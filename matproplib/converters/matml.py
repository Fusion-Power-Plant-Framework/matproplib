# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""matproplib matml converter"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from matproplib.base import ureg
from matproplib.converters.base import Converter
from matproplib.material import material, mixture
from matproplib.properties.group import props
from matproplib.tools.matml import MatMLXML
from matproplib.tools.matml.utilities import process_units, to_data_type

if TYPE_CHECKING:
    from matproplib.conditions import OperationalConditions
    from matproplib.material import Material

__all__ = ["MatML"]


class MatML(Converter):
    """Converter to and from MatML xml v3.1

    Notes
    -----
    Only considers bulk material properties and elemental contribution
    """

    name: ClassVar[Literal["matml"]] = "matml"

    xml_model: MatMLXML | None = None

    def convert(
        self, material: Material, op_cond: OperationalConditions
    ) -> MatMLXML: ...

    @classmethod
    def get_model(cls, filename: str):
        return cls(xml_model=MatMLXML.from_file(filename))

    def import_from(self, *, material_cls: type[Material]) -> Material:
        metadata = self.xml_model.metadata

        materials = {}
        for xml_mat in self.xml_model.material:
            elements = []

            if (char := xml_mat.bulk_details.characterisation) is not None:
                elements = char.compound or [] + char.element or []

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

        for det in self.xml_model.metadata.property_details:
            for m_id, mat in materials.items():
                for p_id, prop in mat["properties"].items():
                    if det.id == p_id:
                        prop["unit"] = (
                            process_units(det.units)
                            if det.unitless is None
                            else ureg.Unit("dimensionless")
                        )
                        prop["value"] = sum(
                            [
                                to_data_type(
                                    d.data.format,
                                    d.data.value,
                                    d.delimiter,
                                    d.quote,
                                )
                                for d in prop["value"]
                            ],
                            [],
                        )
                        if len(prop["value"]) == 1:
                            prop["value"] = prop["value"][0]

        # TODO fix elements
        materials = [
            material(
                name=mat["name"],
                elements=mat["elements"],
                properties=props(**mat["properties"]),
            )
            for m_id, mat in materials.items()
        ]

        if len(materials) == 1:
            return materials[0]
        # TODO fix name, fix fractions
        return mixture("My mixture", materials=materials, converters=self)
