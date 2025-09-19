# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""matproplib matml converter"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

import numpy as np

from matproplib.base import ureg
from matproplib.converters.base import Converter
from matproplib.material import material, mixture
from matproplib.properties.group import props
from matproplib.tools.matml import MatMLXML
from matproplib.tools.matml.utilities import process_units, to_data_type

if TYPE_CHECKING:
    from pint import Unit

    from matproplib.conditions import OperationalConditions
    from matproplib.material import Material
    from matproplib.properties.dependent import DependentPhysicalPropertyTD
    from matproplib.tools.matml.matml import (
        ParameterDetails,
        ParameterValue,
        PropertyData,
    )

__all__ = ["MatML"]

import re

name_pattern = re.compile(r"( )+(?<!^)+(?=[A-Za-z])")

ANSYS_SKIPPED = [
    "Color",
    "Magnetic Flux Density",
    "Magnetic Field Intensity",
    "Strain-Life Parameters",
    "Alternating Stress",
]

NAME_TRANSLATIONS = {
    "specific_heat": "specific_heat_capacity",
    "tensile_ultimate_strength": "average_ultimate_tensile_stress",
    "tensile_yield_strength": "average_yield_stress",
    "coefficient_of_thermal_expansion": "coefficient_thermal_expansion",
    "resistivity": "electrical_resistivity",
    "yield_strength": "average_yield_stress",
}


def to_data(pa_v: ParameterValue, prop: PropertyData) -> list:
    """Convert parametervalue to list of data"""  # noqa: DOC201
    return to_data_type(
        pa_v.data.format,
        pa_v.data.value,
        prop.delimiter,
        prop.quote,
    )


def to_unit(pd: ParameterDetails) -> Unit:
    """Convert parameter details unit to pint unit"""  # noqa: DOC201
    return process_units(pd.units) if pd.unitless is None else ureg.Unit("dimensionless")


def rename(name: str) -> str:
    """Rename unit to snake case"""  # noqa: DOC201
    return name_pattern.sub("_", name).lower().replace("'", "").replace("-", "_")


def convert_to_properties(prop_in) -> DependentPhysicalPropertyTD:
    """Convert data to dependent property dictionary"""  # noqa: DOC201
    properties = {}
    for v in prop_in.values():
        if v:
            for k, _pa in v.items():
                if len(_pa["value"]) == 1:
                    _pa["value"] = _pa["value"][0]
                elif isinstance(_pa["value"][0], float):
                    _pa["value"] = np.array(_pa["value"])
                properties[NAME_TRANSLATIONS.get(k, k)] = _pa
    return properties


def extract_data(xml_model: MatMLXML) -> tuple[dict, dict, dict]:
    materials = {}
    for xml_mat in xml_model.material:
        elements = []

        if (char := xml_mat.bulk_details.characterisation) is not None and (
            comp := char.chemical_composition
        ) is not None:
            # TODO process elements
            # elements = (comp.compound or []) + (comp.element or [])
            pass

        properties = {}
        for p in xml_mat.bulk_details.property_data:
            if p.property in properties:
                properties[p.property]["value"].append(p)
            else:
                properties[p.property] = {"value": [p]}

        materials[xml_mat.id] = {
            "name": xml_mat.bulk_details.name.value,
            "elements": elements,
            "properties": properties,
        }

    property_details = {det.id: det for det in xml_model.metadata.property_details}
    parameter_details = {det.id: det for det in xml_model.metadata.parameter_details}
    return materials, property_details, parameter_details


class MatML(Converter):
    """Converter to and from MatML xml v3.1

    Notes
    -----
    Only considers bulk material properties and elemental contribution
    """

    name: ClassVar[Literal["matml"]] = "matml"

    xml_model: MatMLXML | None = None

    def convert(self, material: Material, op_cond: OperationalConditions) -> MatMLXML:
        """Convert material to matml object"""
        for prop_name in material.list_properties():
            prop = getattr(material, prop_name)
            prop_data = prop(op_cond)
            raise NotImplementedError

    @classmethod
    def get_model(cls, filename: str):
        """Get xml model from file"""  # noqa: DOC201
        return cls(xml_model=MatMLXML.from_file(filename))

    @classmethod
    def import_from(cls, filename, *, skip_properties=ANSYS_SKIPPED) -> Material:
        """Import material from file

        Returns
        -------
        :
            Material object
        """
        self = cls.get_model(filename)

        materials, property_details, parameter_details = extract_data(self.xml_model)

        for mat in materials.values():
            properties = {}

            for p_id, prop in mat["properties"].items():
                if (_name := property_details[p_id].name.value) in skip_properties:
                    continue
                if (name := rename(_name)) not in properties:
                    properties[name] = {}

                data = properties[name]
                for pr_v in prop["value"]:
                    for pa_v in pr_v.parameter_value:
                        pd = parameter_details[pa_v.parameter]
                        if (_name := pd.name.value) in skip_properties:
                            continue
                        pa_name = rename(_name)
                        if "Dependent" in pa_v.qualifier:
                            data[pa_name] = {
                                "value": to_data(pa_v, pr_v),
                                "unit": to_unit(pd),
                            }
                        elif "Independent" in pa_v.qualifier:
                            # TODO include limits on dependent properties
                            pass
                        # Dont currently deal with other types

            mat["properties"] = convert_to_properties(properties)

        materials = [
            material(
                name=mat["name"],
                elements=mat["elements"],
                properties=props(**mat["properties"]),
                **({"converters": self} if len(materials) == 1 else {}),
            )
            for m_id, mat in materials.items()
        ]

        if len(materials) == 1:
            return materials[0]
        # TODO fix name, fix fractions
        return mixture("My mixture", materials=materials, converters=self)
