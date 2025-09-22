# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""matproplib matml utilities"""

from __future__ import annotations

import math
from collections.abc import Sequence
from fractions import Fraction
from typing import TYPE_CHECKING, Literal

from matproplib.base import ureg
from matproplib.tools.matml.matml import Unitless
from matproplib.tools.matml.matml_enums import DataFormat

if TYPE_CHECKING:
    from pint import Unit

    from matproplib.nucleides import Elements
    from matproplib.tools.matml.matml import (
        MatMLXML,
        ParameterDetails,
        ParameterValue,
        PropertyData,
        Units,
    )


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


def extract_data(xml_model: MatMLXML) -> tuple[dict, dict, dict]:
    """Extract bulk material data from MatML material"""  # noqa: DOC201
    materials = {}
    for xml_mat in xml_model.material:
        elements = []

        if (char := xml_mat.bulk_details.characterisation) is not None:
            if char.formula:
                elements = char.formula
                continue

            if (comp := char.chemical_composition) is not None:  # noqa: F841
                # TODO @je-cook: Process Elements more thoroughly
                # 1
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

    if xml_model.metadata is not None:
        property_details = {det.id: det for det in xml_model.metadata.property_details}
        parameter_details = {det.id: det for det in xml_model.metadata.parameter_details}
    else:
        property_details, parameter_details = {}, {}
    return materials, property_details, parameter_details


def process_units(units: Units) -> Unit:
    """Convert matml units to pint units"""  # noqa: DOC201
    units_ = []
    for u in units.unit:
        if u.name == "C":
            name = "degC" if u.power is None or u.power > 0 else "K"
        else:
            name = u.name
        units_.append(f"{name}^{u.power or 1}")

    return ureg.parse_units(".".join(units_), as_delta=False)


def to_data_type(d_format: DataFormat, value: str, delimiter: str, quote: str | None):
    """Convert data to specified data type"""  # noqa: DOC201
    new_v = value.split(delimiter) if delimiter else [value]
    if quote is not None:
        new_v = [v.strip(quote) for v in new_v]

    if d_format is DataFormat.EXPONENTIAL:
        new_v = [10 ** float(v) for v in new_v]
    elif d_format is DataFormat.STRING:
        new_v = [str(v) for v in new_v]
    else:
        new_v = [float(v) for v in new_v]

    return new_v


def to_ml_units(unit: Unit):
    """Convert to MatML units"""  # noqa: DOC201
    return {
        "unit": [
            {"name": f"{ureg.Unit(u_n):~P}", "power": power}
            for u_n, power in unit._units.items()  # noqa: SLF001
        ],
        "system": "SI",
    }


def details(name: str, id_: str, units: Unit | Literal[""]):
    """Create details object for MatML"""  # noqa: DOC201
    # pint dimensionless == '' is true
    if units == "":  # noqa: PLC1901
        unitless = Unitless()
        unit = None
    else:
        unitless = None
        unit = to_ml_units(units)

    return {"name": {"value": name}, "id": id_, "units": unit, "unitless": unitless}


def parameter_data(
    pr_id: str,
    pa_id: str,
    name: str,
    prop_data: float | Sequence[float],
    units: Unit | Literal[""],
    delim: str,
) -> tuple[dict, dict, dict]:
    """Convert matproplib property to MatMl parameter data"""  # noqa: DOC201
    if not isinstance(prop_data, Sequence):
        prop_data = [prop_data]

    pa_v = {
        "parameter": pa_id,
        "format": "float",
        "data": {"value": delim.join(str(p) for p in prop_data)},
        "qualifier": ["Dependent"] * len(prop_data),
    }
    # TODO @je-cook: Add independent parameter_value
    # 1
    pa_d = details(name, pa_id, units)

    pr_v = {
        "data": {"value": "-", "format": "string"},
        "property": pr_id,
        "parameter_value": [pa_v],
    }
    pr_d = details(name, pr_id, "")
    return pr_v, pr_d, pa_d


def to_characterisation(elements: Elements):
    """Convert matproplib elements to matml characterisation"""  # noqa: DOC201
    out = {
        sym: Fraction(el).limit_denominator()
        for sym, el in elements.model_dump().items()
    }
    denom = math.gcd(*[o.denominator for o in out.values()])
    elmnt = [
        {
            "symbol": {
                "value": sym,
                "subscript": str((o * denom).limit_denominator().numerator),
            }
        }
        for sym, o in out.items()
    ]
    formula = "".join(
        (
            f"{o['symbol']['value']}"
            f"{o['symbol']['subscript'] if o['symbol']['subscript'] != '1' else ''}"
        )
        for o in elmnt
    )
    return {"formula": formula, "chemical_composition": {"element": elmnt}}
