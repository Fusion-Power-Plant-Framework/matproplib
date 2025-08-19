# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from matproplib.conditions import OperationalConditions
from matproplib.library.fluids import Water


class TestWater:
    def test_density(self):
        water = Water()
        op_cond = OperationalConditions(temperature=300, pressure=1e5)
        assert water.density(op_cond) == 997.047

    def test_specific_heat_capacity(self):
        water = Water()
        op_cond = OperationalConditions(temperature=300, pressure=1e5)
        assert water.specific_heat_capacity(op_cond) == 4.186

    def test_thermal_conductivity(self):
        water = Water()
        op_cond = OperationalConditions(temperature=300, pressure=1e5)
        assert water.thermal_conductivity(op_cond) == 0.606
