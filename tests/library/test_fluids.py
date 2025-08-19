# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
import pytest
from CoolProp.CoolProp import PropsSI

from matproplib.conditions import OperationalConditions
from matproplib.library.fluids import Water


class TestWater:
    @pytest.mark.parametrize(
        ("t", "p"),
        [
            (300, 1e5),
            (350, 1e5),
            (400, 1e5),
            (500, 1e5),
            (600, 1e6),
            (700, 1e6),
            (100, 1e3),
        ],
    )
    def test_density(self, t, p):
        water = Water()
        op_cond = OperationalConditions(temperature=t, pressure=p)
        assert water.density(op_cond) == PropsSI(
            "DMASS", "T", op_cond.temperature.value, "P", op_cond.pressure.value, "Water"
        )

    def test_specific_heat_capacity(self):
        water = Water()
        op_cond = OperationalConditions(temperature=300, pressure=1e5)
        assert water.specific_heat_capacity(op_cond) == PropsSI(
            "CPMASS",
            "T",
            op_cond.temperature.value,
            "P",
            float(op_cond.pressure.value),
            "Water",
        )

    def test_thermal_conductivity(self):
        water = Water()
        op_cond = OperationalConditions(temperature=300, pressure=1e5)
        assert water.thermal_conductivity(op_cond) == PropsSI(
            "CONDUCTIVITY",
            "T",
            op_cond.temperature.value,
            "P",
            op_cond.pressure.value,
            "Water",
        )
