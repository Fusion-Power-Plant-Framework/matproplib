# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""matproplib matml converter"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

import numpy as np

from matproplib.converters.base import Converter
from matproplib.material import material
from matproplib.properties.group import props
from matproplib.tools.matml import MatMLXML
from matproplib.tools.matml.utilities import (
    extract_data,
    parameter_data,
    to_characterisation,
    to_data,
    to_unit,
)

if TYPE_CHECKING:
    from pint import Unit

    from matproplib.conditions import OperationalConditions
    from matproplib.material import Material
    from matproplib.properties.dependent import DependentPhysicalPropertyTD

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


def rename(name: str) -> str:
    """Rename unit to snake case"""  # noqa: DOC201
    return name_pattern.sub("_", name).lower().replace("'", "").replace("-", "_")


def convert_to_properties(
    prop_in: dict[str, dict[str, dict[str, float | Unit]]],
) -> dict[str, DependentPhysicalPropertyTD]:
    """Convert data to dependent property dictionary"""  # noqa: DOC201
    properties = {}
    for v in prop_in.values():
        for k, _pa in v.items():
            if _pa and _pa["dependent"]:
                if len(_pa["value"]) == 1:
                    _pa["value"] = _pa["value"][0]
                elif isinstance(_pa["value"][0], float):
                    # TODO @je-cook: Create interpolation function
                    # 1
                    _pa["value"] = np.array(_pa["value"])
                properties[NAME_TRANSLATIONS.get(k, k)] = _pa
    return properties


class MatML(Converter):
    """Converter to and from MatML xml v3.1

    Notes
    -----
    Only considers bulk material properties and elemental contribution
    """

    name: ClassVar[Literal["matml"]] = "matml"

    xml_model: MatMLXML | None = None

    @staticmethod
    def convert(material: Material, op_cond: OperationalConditions) -> MatMLXML:
        """Convert material to matml object"""  # noqa: DOC201
        delimiter = ","
        pr_ds, pa_ds, pr_vs = [], [], []

        for id_, prop_name in enumerate(material.list_properties(), start=1):
            prop = getattr(material, prop_name)
            pr_v, pr_d, pa_d = parameter_data(
                f"pr{id_:02}",
                f"pa{id_:02}",
                prop_name,
                prop(op_cond),
                prop.unit,
                delimiter,
            )
            pr_vs.append(pr_v)
            pr_ds.append(pr_d)
            pa_ds.append(pa_d)

        return MatMLXML.model_validate({
            "material": [
                {
                    "bulk_details": {
                        "name": {"value": material.name},
                        "property_data": pr_vs,
                        "delimiter": delimiter,
                        "characterisation": to_characterisation(material.elements),
                    }
                }
            ],
            "metadata": {
                "parameter_details": pa_ds,
                "property_details": pr_ds,
            },
        })

    @classmethod
    def get_model(cls, filename: str):
        """Get xml model from file"""  # noqa: DOC201
        return cls(xml_model=MatMLXML.from_file(filename))

    @classmethod
    def import_from(cls, filename, /, *, skip_properties=ANSYS_SKIPPED) -> Material:
        """Import material from file

        Returns
        -------
        :
            Material object
        """
        self = cls.get_model(filename)

        materials, property_details, parameter_details = extract_data(self.xml_model)

        if len(materials) > 1:
            # When implemented only add converter to mixture.
            raise NotImplementedError("No fractional mixing of materials known")
        mat = next(iter(materials.values()))
        properties = {}
        for p_id, prop in mat["properties"].items():
            if (_name := property_details[p_id].name.value) in skip_properties:
                continue
            if (name := rename(_name)) not in properties:
                properties[name] = {}
            for pr_v in prop["value"]:
                for pa_v in pr_v.parameter_value:
                    pd = parameter_details[pa_v.parameter]
                    if (_name := pd.name.value) in skip_properties:
                        continue
                    data = properties[name][rename(_name)] = {}
                    if "Dependent" in pa_v.qualifier:
                        data |= {
                            "value": to_data(pa_v, pr_v),
                            "unit": to_unit(pd),
                            "dependent": True,
                        }
                    elif "Independent" in pa_v.qualifier:
                        data |= {
                            "value": to_data(pa_v, pr_v),
                            "unit": to_unit(pd),
                            "dependent": False,
                        }
                    # Dont currently deal with other types

        return material(
            name=mat["name"],
            elements=mat["elements"],
            properties=props(**convert_to_properties(properties)),
            converters=self,
        )
