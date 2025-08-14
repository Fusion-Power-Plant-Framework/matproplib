# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Beryllium materials"""

import numpy as np

from matproplib.conditions import OperationalConditions
from matproplib.converters.neutronics import OpenMCNeutronicConfig
from matproplib.library.references import FOKKENS_2003
from matproplib.material import dependentphysicalproperty, material
from matproplib.properties.dependent import (
    SpecificHeatCapacity,
    ThermalExpansionCoefficient,
)
from matproplib.properties.group import props

Be12Ti = material(
    "Be12Ti",
    elements="Be12Ti",
    converters=OpenMCNeutronicConfig(
        volume_of_unit_cell=0.22724e-27,
        atoms_per_unit_cell=2,
        enrichment_target="Li6",
        enrichment_type="atomic",
    ),
)


@dependentphysicalproperty(
    ThermalExpansionCoefficient,
    unit="1e-6/T",
    op_cond_config={"temperature": ("degC", 25, 800)},
    reference={
        "id": "bepb_cte",
        "type": "article",
        "doi": "10.1016/S0920-3796(02)00165-5",
    },
)
def BePB_CTE(op_cond: OperationalConditions) -> float:  # noqa: N802
    """
    .. doi:: 10.1016/S0920-3796(02)00165-5

    Returns
    -------
    :
        Mean coefficient of thermal expansion
    """
    # NOTE: Effect of inelastic volumetric strains [%] not negligible
    # eps_vol calculated roughly as f(T), as per 2M2BH9
    eps_vol = op_cond.strain
    if eps_vol == 0:

        def calc_eps_vol(temp):
            """
            Returns
            -------
            :
                Inelastic volumetric strains [%] based on T (C)
            """
            if temp >= 600:  # noqa: PLR2004
                return 0.5
            if temp >= 500:  # noqa: PLR2004
                return 0.3
            if temp < 500:  # noqa: PLR2004
                return 0.2
            return None

        eps_vol = np.vectorize(calc_eps_vol)(op_cond.temperature)
    eps_vol *= np.ones_like(op_cond.temperature)
    return (
        1.81
        + 0.0012 * op_cond.temperature
        - 5e-7 * op_cond.temperature**2
        + eps_vol
        * (
            9.03
            - 1.386e-3 * op_cond.temperature
            - 7.6e-6 * op_cond.temperature**2
            + 2.1e-9 * op_cond.temperature**3
        )
    )


@dependentphysicalproperty(
    dpp=SpecificHeatCapacity,
    op_cond_config={"temperature": ("degC", 0, 1000)},
    reference=FOKKENS_2003,
)
def BePB_specific_heat_capacity(op_cond: OperationalConditions):
    # fmt: off
    SHC_BePB1 = [0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000]
    SHC_BePB2 = [1741.8, 1900.97, 2045.53, 2176.44, 2294.66, 2401.14, 2496.83, 2582.71, 2659.71, 2728.79, 2790.93, 2847.05, 2898.14, 2945.13, 2988.99, 3030.68, 3071.14, 3111.34, 3152.22, 3194.76, 3239.9]
    # fmt: on

    return np.interp(op_cond.temperature, SHC_BePB1, SHC_BePB2)


BePebbleBed = material(
    "BePebbleBed",
    elements="Be",
    properties=props(
        as_field=True,
        specific_heat_capacity=BePB_specific_heat_capacity,
        coefficient_thermal_expansion=BePB_CTE,
    ),
    converters=OpenMCNeutronicConfig(
        volume_of_unit_cell=0.01622e-27, atoms_per_unit_cell=8
    ),
)
