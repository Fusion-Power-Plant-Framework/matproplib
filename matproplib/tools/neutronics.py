# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Materials neutronics tools"""

from __future__ import annotations

import json
import warnings
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


def import_nmm():
    """Don't hack my json, among other annoyances.

    Returns
    -------
    :
        The modified nmm module reference
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        import neutronics_material_maker as nmm  # noqa: PLC0415

        # Really....
        json.JSONEncoder.default = nmm.material._default.default  # noqa: SLF001

    # hard coded value is out of date after 2019 redefinition
    nmm.material.atomic_mass_unit_in_g = ureg.Quantity(1, "amu").to("g").magnitude

    return nmm


@contextmanager
def patch_nmm_openmc():
    """Avoid creating openmc material until necessary

    Yields
    ------
    :
        NeutronicsMaterialMaker package
    """
    nmm = import_nmm()
    if value := nmm.material.OPENMC_AVAILABLE:
        nmm.material.OPENMC_AVAILABLE = False
    try:
        yield nmm
    finally:
        if value:
            nmm.material.OPENMC_AVAILABLE = True


NMM_FRACTION_TYPE_MAPPING = {
    "atomic": "ao",
    "mass": "wo",
    "volume": "vo",
}


def to_openmc_material(
    name: str | None = None,
    packing_fraction: float = 1.0,
    enrichment: float | None = None,
    enrichment_target: str | None = None,
    temperature: float | None = None,
    elements: dict[str, float] | None = None,
    isotopes: dict[str, float] | None = None,
    percent_type: str | None = None,
    density: float | None = None,
    density_unit: str | None = None,
    atoms_per_unit_cell: int | None = None,
    volume_of_unit_cell: float | None = None,
    enrichment_type: str | None = None,
    zaid_suffix: str | None = None,
    material_id: int | None = None,
    decimal_places: int = 8,
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
    if density is None and None in {atoms_per_unit_cell, volume_of_unit_cell}:
        raise ValueError(
            "density calculation requires 'atoms_per_unit_cell' and "
            "'volume_per_unit_cell' to be set when density is unset"
        )
    if temperature_to_neutronics_code and temperature is not None:
        if isinstance(temperature, np.ndarray) and temperature.size != 1:
            raise ValueError(
                "Only singular temperature value can be passed into neutronics material"
            )
    elif not temperature_to_neutronics_code:
        temperature = None
    with patch_nmm_openmc() as nmm:
        return nmm.Material(
            name=name,
            packing_fraction=packing_fraction,
            elements=elements,
            isotopes=isotopes,
            enrichment_type=NMM_FRACTION_TYPE_MAPPING.get(enrichment_type),
            enrichment_target=enrichment_target,
            enrichment=enrichment,
            percent_type=NMM_FRACTION_TYPE_MAPPING[percent_type],
            density=density,
            density_unit=density_unit.replace("^", ""),
            temperature=temperature,
            temperature_to_neutronics_code=temperature_to_neutronics_code,
            # fallback for density calculation
            atoms_per_unit_cell=atoms_per_unit_cell,
            volume_of_unit_cell_cm3=None
            if volume_of_unit_cell is None
            else ureg.Quantity(volume_of_unit_cell, "m^3").to("cm^3").magnitude,
            zaid_suffix=zaid_suffix,
            material_id=material_id,
            decimal_places=decimal_places,
        ).openmc_material


def to_openmc_material_mixture(
    materials: list[openmc.Material],
    fracs: list[float],
    name: str | None = None,
    material_id: int | None = None,
    temperature: float | None = None,
    percent_type: str = "volume",
    packing_fraction: float = 1.0,
    pressure: float | None = None,
    comment: str | None = None,
    zaid_suffix: str | None = None,
    decimal_places: int = 8,
    additional_end_lines: dict[str, list[str]] | None = None,
    *,
    temperature_to_neutronics_code: bool = True,
) -> openmc.Material:
    """Convert material mixture to OpenMC material mixture

    Returns
    -------
    :
        The openmc mixture
    """
    with patch_nmm_openmc() as nmm:
        return nmm.Material.from_mixture(
            name=name,
            material_id=material_id,
            materials=materials,
            fracs=fracs,
            percent_type=NMM_FRACTION_TYPE_MAPPING[percent_type],
            packing_fraction=packing_fraction,
            temperature=temperature,
            temperature_to_neutronics_code=temperature_to_neutronics_code,
            pressure=pressure,
            comment=comment,
            zaid_suffix=zaid_suffix,
            decimal_places=decimal_places,
            additional_end_lines=additional_end_lines,
        ).openmc_material


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
        mat_card[0] += f" tmp {temperature}"

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
