# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
import numpy as np
import pytest


@pytest.fixture
def test_material():
    from physical_materials.converters.neutronics import (
        FispactNeutronicConfig,
    )
    from physical_materials.material import material
    from physical_materials.properties.group import props
    from physical_materials.superconduction import (
        Nb3SnBotturaParameterisation,
    )

    return material(
        "TestMat",
        elements="C1Fe12",
        properties=props(
            density=5,
            specific_heat_capacity={
                "value": lambda properties, oc: properties.density(oc) * oc.temperature,
                "unit": "J/g/K",
                "op_cond_config": {"temperature": ("K", 100, 300)},
            },
            superconducting_parameterisation=Nb3SnBotturaParameterisation(
                constant=1,
                p=2,
                q=3,
                c_a1=4,
                c_a2=5,
                eps_0a=6,
                eps_m=7,
                b_c20m=8,
                t_c0max=9,
                reference=None,
            ),
        ),
        converters=FispactNeutronicConfig(volume=3),
    )()


@pytest.fixture
def test_condition():
    from physical_materials.conditions import OperationalConditions

    return OperationalConditions(temperature=np.array([298, 200]), pressure=(1, "atm"))
