# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Steel materials"""

import numpy as np
from pydantic import Field

from matproplib.base import References, rebuild
from matproplib.conditions import (
    OperationalConditions,
)
from matproplib.library.references import CHOONG_1975
from matproplib.material import (
    FullMaterial,
    PropertiesT_co,
    dependentphysicalproperty,
)
from matproplib.nucleides import Elements
from matproplib.properties.dependent import (
    CoefficientThermalExpansion,
    Density,
    SpecificHeatCapacity,
    ThermalConductivity,
)
from matproplib.properties.group import props
from matproplib.tools.tools import annotate_reference


@dependentphysicalproperty(
    SpecificHeatCapacity,
    op_cond_config={"temperature": ("degK", 300, 1170)},
    reference=annotate_reference(CHOONG_1975, "Equation 7"),
)
def _ss316l_specific_heat_capacity(op_cond: OperationalConditions) -> float:
    """Specific heat capacity of SS316L as a function of temperature."""  # noqa: DOC201
    # Orginal formula given in calories
    return 4.184 * (0.1097 + 3.174e-5 * op_cond.temperature)


@dependentphysicalproperty(
    Density,
    op_cond_config={"temperature": ("degK", 300, 1600)},
    reference=annotate_reference(CHOONG_1975, "Equation 18"),
)
def _ss316l_density(op_cond: OperationalConditions) -> float:
    """Density of SS316L as a function of temperature."""  # noqa: DOC201
    return 8084.2 - 4.2086e-1 * op_cond.temperature - 3.8942e-5 * op_cond.temperature**2


@dependentphysicalproperty(
    CoefficientThermalExpansion,
    op_cond_config={"temperature": ("degK", 300, 1600)},
    reference=annotate_reference(CHOONG_1975, "Equation 24"),
)
def _ss316l_thermal_expansion_coefficient(op_cond: OperationalConditions) -> float:
    """Thermal expansion cofficient of SS316L as a function of temperature."""  # noqa: DOC201
    return (
        1.7887e-5 + 2.3977e-9 * op_cond.temperature + 3.2692e-13 * op_cond.temperature**2
    )


@dependentphysicalproperty(
    ThermalConductivity,
    op_cond_config={"temperature": ("degK", 300, 1600)},
    reference=annotate_reference(CHOONG_1975, "Equation 30"),
)
def _ss316l_thermal_conductivity(op_cond: OperationalConditions) -> float:
    """Thermal conductivity of SS316L as a function of temperature."""  # noqa: DOC201
    return 9.248 + 1.571e-2 * op_cond.temperature


@rebuild
class SS316_L(FullMaterial):
    """
    Stainless Steel 316L material. Properties from publicly available Choong 1975 report.
    """

    name: str = Field(default="SS316L")
    elements: Elements = Field(
        default={
            "Fe": 0.70345,
            "C": 0.0003,
            "Cr": 0.17,
            "Ni": 0.105,
            "Mo": 0.02125,
            "fraction_type": "mass",
        }
    )
    reference: References = CHOONG_1975
    properties: PropertiesT_co = props(
        as_field=True,
        density=_ss316l_density,
        specific_heat_capacity=_ss316l_specific_heat_capacity,
        coefficient_thermal_expansion=_ss316l_thermal_expansion_coefficient,
        thermal_conductivity=_ss316l_thermal_conductivity,
    )


@dependentphysicalproperty(
    Density,
    op_cond_config={"temperature": ("degC", 20, 800)},
    reference={
        "id": "ss316_density",
        "type": "report",
        "title": "ITER_D_222RLN v3.3 Table A.S03.2.4-1",
    },
)
def SS316_LN_density(op_cond: OperationalConditions):  # noqa: D103
    # fmt: off
    SS316_LN_density1 = [
        20, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800
    ]
    SS316_LN_density2 = [
        7930, 7919, 7899, 7879, 7858, 7837, 7815, 7793, 7770, 7747, 7724, 7701, 7677,
        7654, 7630, 7606, 7582
    ]
    # fmt: on
    return np.interp(op_cond.temperature, SS316_LN_density1, SS316_LN_density2)
