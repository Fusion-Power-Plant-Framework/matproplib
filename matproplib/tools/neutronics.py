# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Materials neutronics tools"""

from __future__ import annotations

import os
import re
from contextlib import contextmanager
from typing import TYPE_CHECKING, Literal

import numpy as np

from matproplib.base import ureg

if TYPE_CHECKING:
    import openmc

    from matproplib.nucleides import ElementFraction


__all__ = [
    "to_fispact_material",
    "to_mcnp_material",
    "to_openmc_material",
    "to_serpent_material",
]


NM_FRACTION_TYPE_MAPPING = {
    "atomic": "ao",
    "mass": "wo",
    "volume": "vo",
}


def _enrichment_check(
    enrichment: float | None, enrichment_target: str | None, enrichment_type: str | None
) -> str | None:
    if enrichment is None:
        return None

    if None not in {enrichment_type, enrichment_target}:
        return re.split(r"(\d+)", enrichment_target)[0]

    raise ValueError("enrichment_target and enrichment_type need to be set")


@contextmanager
def _get_openmc():
    import openmc  # noqa: PLC0415

    cs = os.environ.get("OPENMC_CROSS_SECTIONS")
    if cs is not None:
        del os.environ["OPENMC_CROSS_SECTIONS"]
    yield openmc
    if cs is not None:
        os.environ["OPENMC_CROSS_SECTIONS"] = cs


def to_openmc_material(
    name: str,
    density_unit: str,
    percent_type: Literal["atomic", "mass"],
    density: float,
    packing_fraction: float = 1.0,
    enrichment: float | None = None,
    enrichment_target: str | None = None,
    temperature: float | None = None,
    elements: dict[str, float] | None = None,
    isotopes: dict[str, float] | None = None,
    enrichment_type: str | None = None,
    material_id: int | None = None,
    *,
    temperature_to_neutronics_code: bool = True,
) -> openmc.Material:
    """
    Convert material to OpenMC material

    Returns
    -------
    :
        The openmc material

    Raises
    ------
    ValueError
        neither density or atoms and volume per unit cell specified
    ValueError
        Arrays used in temperature specification
    """
    nm_percent_type = NM_FRACTION_TYPE_MAPPING[percent_type]
    enrichment_type = NM_FRACTION_TYPE_MAPPING.get(enrichment_type)
    en_el = _enrichment_check(enrichment, enrichment_target, enrichment_type)

    with _get_openmc() as openmc:
        material = openmc.Material(name=name, material_id=material_id)

        if isotopes:
            for is_name, frac in isotopes.items():
                material.add_nuclide(is_name, frac, nm_percent_type)

        if elements:
            for el_name, frac in elements.items():
                extra = (
                    {
                        "enrichment": enrichment,
                        "enrichment_target": enrichment_target,
                        "enrichment_type": enrichment_type,
                    }
                    if el_name == en_el
                    else {}
                )
                material.add_element(
                    el_name, frac, percent_type=nm_percent_type, **extra
                )

        # Ordering of nucleide can effect results
        material._nuclides = sorted(material._nuclides)  # noqa: SLF001
        material.set_density(density_unit.replace("^", ""), density * packing_fraction)
        if temperature_to_neutronics_code:
            material.temperature = temperature
    return material


def density_from_unit_cell(
    atoms_in_sample: int,
    atoms_per_unit_cell: int,
    average_molar_mass: float,
    volume_of_unit_cell: float,
) -> float:
    """Density from a unit cell"""  # noqa: DOC201
    molar_mass = atoms_in_sample * average_molar_mass
    mass = atoms_per_unit_cell * molar_mass * ureg.Quantity("amu").to("kg").magnitude
    return mass / volume_of_unit_cell


def to_fispact_material(
    volume_in_cm3: float,
    mass_density: float,
    nucleide_atom_per_cm3: dict[str, float],
    decimal_places: int = 8,
    additional_end_lines: list[str] | None = None,
) -> str:
    """Fispact material card using the DENSITY and FUEL keywords

    Returns
    -------
    :
        Material card as string

    Notes
    -----
    See https://fispact.ukaea.uk/wiki/Keyword:FUEL and
    https://fispact.ukaea.uk/wiki/Keyword:DENSITY

    """
    mat_card = [
        f"DENSITY {mass_density:.{decimal_places}E}",
        f"FUEL {len(nucleide_atom_per_cm3)}",
    ]
    mat_card.extend(
        f"{isotope}  {volume_in_cm3 * atoms_cm3:.{decimal_places}E}"
        for isotope, atoms_cm3 in nucleide_atom_per_cm3.items()
    )
    return _general_end(mat_card, additional_end_lines)


def to_serpent_material(
    name: str,
    mass_density: float,
    nucleides: list[tuple[ElementFraction, Literal["mass", "atomic"]]],
    temperature: float | None = None,
    decimal_places: int = 8,
    zaid_suffix: str = "",
    additional_end_lines: list[str] | None = None,
    *,
    temperature_to_neutronics_code: bool = False,
) -> str:
    """Serpent material card

    Returns
    -------
    :
        Material card as a string

    Raises
    ------
    ValueError
        Use of arrays for temperature

    Notes
    -----
    https://serpent.vtt.fi/mediawiki/index.php/Input_syntax_manual#mat_(material_definition)
    Assumes density is in g/cm^3
    """
    mat_card = [f"mat {name} -{abs(mass_density):.{decimal_places}e}"]
    if temperature_to_neutronics_code and temperature is not None:
        if isinstance(temperature, np.ndarray) and temperature.size != 1:
            raise ValueError(
                "Only singular temperature value can be passed into neutronics material"
            )
        mat_card[0] += f" tmp {temperature:.2f}"

    return _mcnp_serpert_ending(
        mat_card, nucleides, zaid_suffix, decimal_places, additional_end_lines
    )


def to_mcnp_material(
    material_id: int,
    mass_density: float,
    nucleides: list[tuple[ElementFraction, Literal["mass", "atomic"]]],
    name: str = "",
    zaid_suffix: str = "",
    decimal_places: int = 8,
    additional_end_lines: list[str] | None = None,
) -> str:
    """MCNP6 Material card

    Returns
    -------
    :
        Material card as a string

    Notes
    -----
    mcnp.lanl.gov/pdf_files/Book_MonteCarlo_2024_ShultisBahadori_AnMCNPPrimer.pdf
    """
    mat_card = [
        "c     " + name + " density " + f"{mass_density:.{decimal_places}e}" + " g/cm3",
        f"M{material_id: <5}"
        + _mcnp_serpert_extras(nucleides[0], zaid_suffix, decimal_places),
    ]

    return _mcnp_serpert_ending(
        mat_card, nucleides[1:], zaid_suffix, decimal_places, additional_end_lines
    )


def _mcnp_serpert_ending(
    mat_card: list[str],
    nucleides: list[tuple[ElementFraction, Literal["mass", "atomic"]]],
    zaid_suffix: str = "",
    decimal_places: int = 8,
    additional_end_lines: list[str] | None = None,
):
    mat_card.extend(
        f"      {_mcnp_serpert_extras(isotope, zaid_suffix, decimal_places)}"
        for isotope in nucleides
    )
    return _general_end(mat_card, additional_end_lines)


def _mcnp_serpert_extras(
    isotope: tuple[ElementFraction, Literal["mass", "atomic"]],
    zaid_suffix: str = "",
    decimal_places: int = 8,
) -> str:
    return (
        f"{isotope[0].element.zaid}{zaid_suffix}{_percent_prefix(isotope[1])}"
        f"{isotope[0].fraction:.{decimal_places}e}"
    )


def _percent_prefix(
    isotope_percent_type: Literal["mass", "atomic"],
) -> Literal["  ", " -"]:
    if isotope_percent_type == "atomic":
        return "  "
    if isotope_percent_type == "mass":
        return " -"
    raise ValueError


def _general_end(mat_card: list[str], additional_end_lines: list[str] | None = None):
    mat_card += additional_end_lines or []
    return "\n".join(mat_card) + "\n"
