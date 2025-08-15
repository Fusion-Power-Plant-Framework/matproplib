# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Dependent properties of matproplib"""

from __future__ import annotations

from abc import ABC
from collections import Counter
from typing import TYPE_CHECKING, Literal

import periodictable as pt

from matproplib.base import N_AVOGADRO
from matproplib.converters.base import Converter
from matproplib.nucleides import (
    atomic_fraction_to_mass_fraction,
    ef_root_model,
)
from matproplib.properties.independent import Volume  # noqa: TC001
from matproplib.tools import (
    to_fispact_material,
    to_mcnp_material,
    to_openmc_material,
    to_serpent_material,
)

if TYPE_CHECKING:
    import openmc

    from matproplib.conditions import OperationalConditions
    from matproplib.material import Material
    from matproplib.nucleides import ElementFraction


class NeutronicConfig(Converter, ABC):
    """Base neutronic property model"""


def _to_fraction_conversion(fraction_type: str, ef_dict: ef_root_model) -> ef_root_model:
    if fraction_type == "atomic":
        return ef_dict

    if fraction_type == "mass":
        return atomic_fraction_to_mass_fraction(ef_dict)
    raise NotImplementedError(f"Conversion to {fraction_type} not implemented")


class OpenMCNeutronicConfig(NeutronicConfig):
    """OpenMC neutronic properties model"""

    name: Literal["openmc"] = "openmc"
    """Name of converter"""
    zaid_suffix: str = ""
    """The nuclear library to apply to the zaid, for example '.31c'"""
    material_id: int | None = None
    """The id number or mat number used in OpenMC materials,
    auto assigned by default within OpenMC."""
    packing_fraction: float = 1.0
    """Amount of unit packed volume of a material"""
    percent_type: Literal["atomic", "mass", "volume"] = "atomic"
    """Percent type of material"""
    enrichment: float | None = None
    """Enrichment percent of the target"""
    enrichment_target: str | None = None
    """Enrichment target for instance Li6"""
    enrichment_type: Literal["atomic", "mass"] | None = None
    """Enrichment percentage type"""
    atoms_per_unit_cell: int | None = None
    """Number of atoms per unit cell, used in combination with volume_of_unit_cell for
    density fallback calculation"""
    volume_of_unit_cell: float | None = None
    """Volume of unit cell, used in combination with atoms_per_unit_cell for
    density fallback calculation"""
    decimal_places: int = 8
    """Precision of the material card"""

    def convert(
        self,
        material: Material,
        op_cond: OperationalConditions,
        *,
        temperature_to_neutronics_code: bool = False,
    ) -> openmc.Material:
        """
        Returns
        -------
        :
            OpenMC material object
        """
        ef_dict = _to_fraction_conversion(self.percent_type, material.elements.root)
        # Isotope-element separation
        isotopes, elements = {}, {}
        for k, v in ef_dict.items():
            if isinstance(v.element, pt.core.Isotope):
                isotopes[k] = v.fraction
            else:
                elements[k] = v.fraction

        # density calculation from unit cell
        density = (
            material.density.value_as(op_cond, "g/cm^3")
            if hasattr(material, "density")
            else None
        )

        return to_openmc_material(
            name=material.name,
            material_id=self.material_id,
            temperature=op_cond.temperature.value,
            density=density,
            density_unit="g/cm^3",
            isotopes=isotopes or None,
            elements=elements or None,
            percent_type=self.percent_type,
            enrichment=self.enrichment,
            enrichment_target=self.enrichment_target,
            enrichment_type=self.enrichment_type,
            zaid_suffix=self.zaid_suffix,
            volume_of_unit_cell=self.volume_of_unit_cell,
            atoms_per_unit_cell=self.atoms_per_unit_cell,
            packing_fraction=self.packing_fraction,
            temperature_to_neutronics_code=temperature_to_neutronics_code,
            decimal_places=8,
        )


def _get_mass_density(material: Material, op_cond: OperationalConditions) -> float:
    if not hasattr(material, "density") or material.density is None:
        raise NotImplementedError
        # TODO from unit cell?
    return material.density.value_as(op_cond, "g/cm^3")


def _atoms(fraction: float, mass_density: float, molar_mass: float):
    return N_AVOGADRO * fraction * mass_density / molar_mass


class FispactNeutronicConfig(NeutronicConfig):
    """Fispact neutronic properties model"""

    name: Literal["fispact"] = "fispact"
    """Name of converter"""
    volume: Volume
    """Volume of material provided"""
    decimal_places: int = 8
    """Precision of the material card"""

    def convert(
        self,
        material: Material,
        op_cond: OperationalConditions,
        *,
        additional_end_lines: list[str] | None = None,
    ) -> str:
        """
        Returns
        -------
        :
            Fispact material card
        """
        mass_density = _get_mass_density(material, op_cond)
        isotopes = {}  # atoms/cm^3
        for k, v in material.elements.nucleides:
            pt_el = v.element.element
            isotopes[k] = _atoms(v.fraction, mass_density, pt_el.mass)

        return to_fispact_material(
            self.volume.value_as("cm^3"),
            mass_density,
            isotopes,
            self.decimal_places,
            additional_end_lines,
        )


global_id = Counter({"mcnp": 1})
"""MCNP requires material ID this counter increments if none provided"""


class MCNPNeutronicConfig(NeutronicConfig):
    """MCNP6 neutronic properties model"""

    name: Literal["mcnp"] = "mcnp"
    """Name of converter"""
    zaid_suffix: str = ""
    """The nuclear library to apply to the zaid, for example ".31c", this is used in
        MCNP and Serpent material cards."""
    material_id: int | None = None
    """The id number or mat number used in the MCNP and OpenMC material cards."""
    decimal_places: int = 8
    percent_type: Literal["atomic", "mass"] = "atomic"

    def convert(
        self,
        material: Material,
        op_cond: OperationalConditions,
        *,
        additional_end_lines: list[str] | None = None,
    ) -> str:
        """
        Returns
        -------
        :
            MCNP material card
        """
        ef_dict = _to_fraction_conversion(
            self.percent_type, material.elements.nucleides.root
        )

        mass_density = _get_mass_density(material, op_cond)
        if self.material_id is None:
            mat_id = global_id["mcnp"]
            global_id["mcnp"] += 1
        else:
            mat_id = self.material_id

        nucleides: list[tuple[ElementFraction, Literal["mass", "atomic"]]] = [
            (v, self.percent_type) for _k, v in ef_dict.items()
        ]

        return to_mcnp_material(
            mat_id,
            mass_density,
            nucleides,
            material.name,
            self.zaid_suffix,
            self.decimal_places,
            additional_end_lines,
        )


class SerpentNeutronicConfig(NeutronicConfig):
    """Serpent neutronic properties model"""

    name: Literal["serpent"] = "serpent"
    """Name of converter"""
    zaid_suffix: str = ""
    """The nuclear library to apply to the zaid, for example ".31c", this is used in
        MCNP and Serpent material cards."""
    decimal_places: int = 8
    percent_type: Literal["atomic", "mass"] = "atomic"

    def convert(
        self,
        material: Material,
        op_cond: OperationalConditions,
        *,
        additional_end_lines: list[str] | None = None,
        temperature_to_neutronics_code: bool = False,
    ) -> str:
        """
        Returns
        -------
        :
            Serpent material card
        """
        ef_dict = _to_fraction_conversion(
            self.percent_type, material.elements.nucleides.root
        )
        mass_density = _get_mass_density(material, op_cond)
        nucleides: list[tuple[ElementFraction, Literal["mass", "atomic"]]] = [
            (v, self.percent_type) for _k, v in ef_dict.items()
        ]

        return to_serpent_material(
            material.name,
            mass_density,
            nucleides,
            op_cond.temperature.value,
            self.decimal_places,
            self.zaid_suffix,
            additional_end_lines,
            temperature_to_neutronics_code=temperature_to_neutronics_code,
        )
