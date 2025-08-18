# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Tungsten materials"""

import numpy as np
from pydantic import Field

from matproplib.base import References, rebuild
from matproplib.conditions import (
    OperationalConditions,
)
from matproplib.library.references import PLANSEE_2025
from matproplib.material import (
    FullMaterial,
    PropertiesT_co,
    dependentphysicalproperty,
)
from matproplib.nucleides import Elements
from matproplib.properties.dependent import (
    CoefficientThermalExpansion,
    ElectricalResistivity,
    SpecificHeatCapacity,
    ThermalConductivity,
    YoungsModulus,
)
from matproplib.properties.group import props


@dependentphysicalproperty(
    CoefficientThermalExpansion,
    op_cond_config={"temperature": ("degC", 200, 1400)},
    reference=PLANSEE_2025,
)
def _w_coefficient_thermal_expansion(op_cond: OperationalConditions) -> float:
    temperature_c = [200, 400, 600, 800, 1000, 1200, 1400]
    cte = [4.38, 4.41, 4.54, 4.68, 4.83, 4.96, 5.10]
    return np.interp(op_cond.temperature, temperature_c, cte) * 1e-6


@dependentphysicalproperty(
    SpecificHeatCapacity,
    op_cond_config={"temperature": ("degC", 0, 1100)},
    reference=PLANSEE_2025,
)
def _w_specific_heat_capacity(op_cond: OperationalConditions) -> float:
    temperature_c = [0, 100, 300, 500, 700, 900, 1100]
    c_p = [0.131, 0.135, 0.140, 0.144, 0.149, 0.154, 0.159]
    return np.interp(op_cond.temperature, temperature_c, c_p) * 1e3


@dependentphysicalproperty(
    ThermalConductivity,
    op_cond_config={"temperature": ("degC", 25.4, 801)},
    reference=PLANSEE_2025,
)
def _w_thermal_conductivity(op_cond: OperationalConditions) -> float:
    temperature_c = [25.4, 101, 201, 401, 601, 801]
    k = [174.11, 164.18, 153.67, 136.21, 125.78, 119.77]
    return np.interp(op_cond.temperature, temperature_c, k)


@dependentphysicalproperty(
    ElectricalResistivity,
    op_cond_config={"temperature": ("degC", 0, 3369.33)},
    reference=PLANSEE_2025,
)
def _w_electrical_resistivity(op_cond: OperationalConditions) -> float:
    # fmt: off
    temperature_c = [
        0.0, 12.6468, 38.6373, 68.1125, 97.5877, 127.063, 156.538, 186.013,
        215.488, 244.964, 274.439, 303.914, 333.389, 362.864, 392.34, 421.815, 451.29,
        480.765, 510.24, 539.715, 569.191, 598.666, 628.141, 657.616, 687.091, 716.567,
        746.042, 775.517, 804.992, 834.467, 863.943, 893.418, 922.893, 952.368, 981.843,
        1011.32, 1040.79, 1070.27, 1099.74, 1129.22, 1158.69, 1188.17, 1217.64, 1247.12,
        1276.6, 1306.07, 1335.55, 1365.02, 1394.5, 1423.97, 1453.45, 1482.92, 1512.4,
        1541.87, 1571.35, 1600.82, 1630.3, 1659.77, 1689.25, 1718.72, 1748.2, 1777.67,
        1807.15, 1836.62, 1866.1, 1895.57, 1925.05, 1954.52, 1984.0, 2013.47, 2042.95,
        2072.43, 2101.9, 2131.38, 2160.85, 2190.33, 2219.8, 2249.28, 2278.75, 2308.23,
        2337.7, 2367.18, 2426.13, 2455.6, 2485.08, 2514.55, 2544.03, 2573.5, 2602.98,
        2632.45, 2396.65, 2661.93, 2691.4, 2720.88, 2750.35, 2779.83, 2809.3, 2838.78,
        2868.26, 2897.73, 2927.21, 2956.68, 2986.16, 3015.63, 3045.11, 3074.58, 3104.06,
        3133.53, 3163.01, 3192.48, 3221.96, 3251.43, 3280.91, 3310.38, 3339.86, 3369.33
    ]
    nu = [
        0.04, 0.04, 0.05, 0.06, 0.07, 0.08, 0.08, 0.09, 0.1, 0.11, 0.12, 0.12, 0.13,
        0.14, 0.15, 0.16, 0.16, 0.17, 0.18, 0.19, 0.2, 0.21, 0.21, 0.22, 0.23, 0.24,
        0.25, 0.26, 0.27, 0.28, 0.28, 0.29, 0.3, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36,
        0.36, 0.37, 0.38, 0.39, 0.4, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48,
        0.49, 0.5, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.6, 0.61,
        0.62, 0.63, 0.64, 0.65, 0.66, 0.67, 0.68, 0.69, 0.7, 0.71, 0.72, 0.73, 0.74,
        0.76, 0.77, 0.78, 0.79, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.89, 0.8,
        0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.99, 1.0, 1.01, 1.02, 1.03,
        1.04, 1.05, 1.06, 1.08, 1.09, 1.1, 1.11, 1.12, 1.13, 1.15, 1.16, 1.17
    ]
    # fmt: on
    return np.interp(op_cond.temperature, temperature_c, nu) * 1e-6


@dependentphysicalproperty(
    YoungsModulus,
    op_cond_config={"temperature": ("degC", 0, 2190.33)},
    reference=PLANSEE_2025,
)
def _w_youngs_modulus(op_cond: OperationalConditions) -> float:
    # fmt: off
    temperature_c = [
        56.423, 194.1, 291.33, 388.57, 485.8, 583.04, 680.27, 777.51, 874.75, 971.98,
        1069.2, 1166.5, 1263.7, 1360.9, 1458.2, 1555.4, 1652.6, 1749.9, 1847.1,
        1944.3, 2002.1
    ]
    y_m = [
        407.78, 401.38, 397.45, 393.16, 388.75, 384.29, 379.47, 374.6, 369.61, 366.14,
        362.85, 359.5, 354.51, 348.41, 342.3, 336.2, 326.59, 313.7, 300.87, 287.81,
        280.27
    ]
    # fmt: on
    return np.interp(op_cond.temperature, temperature_c, y_m) * 1e9


@rebuild
class PlanseeTungsten(FullMaterial):
    """
    Plansee ultra-high purity Tungsten, stress-relieved sheet.
    Properties from publicly available Plansee data.
    """

    name: str = Field(
        default="Plansee ultra-high purity Tungsten (W-UHP), stress-relieved sheet"
    )
    elements: Elements = Field(
        default={
            "W": 0.999966,
            "Al": 1e-6,
            "Cr": 3e-6,
            "Cu": 1e-6,
            "Fe": 8e-6,
            "K": 1e-6,
            "Mo": 12e-6,
            "Ni": 2e-6,
            "Si": 1e-6,
            "N": 1e-6,
            "O": 2e-6,
            "Cd": 1e-6,
            "Pb": 1e-6,
            "fraction_type": "mass",
        }
    )
    reference: References = PLANSEE_2025
    properties: PropertiesT_co = props(
        as_field=True,
        density=19250.0,
        poissons_ratio=0.28,
        youngs_modulus=_w_youngs_modulus,
        coefficient_thermal_expansion=_w_coefficient_thermal_expansion,
        thermal_conductivity=_w_thermal_conductivity,
        specific_heat_capacity=_w_specific_heat_capacity,
        electrical_resistivity=_w_electrical_resistivity,
    )
