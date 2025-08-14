# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import numpy as np
import pytest

from matproplib.conditions import OperationalConditions
from matproplib.library.copper import CryogenicCopper


def cryo_copper(rrr: float):
    return CryogenicCopper(residual_resistance_ratio=rrr)


class TestCryogenicCopper:
    @pytest.mark.parametrize(
        "rrr,temperature,expected",
        [
            (30, 1, 46),
            (30, 2, 91),
            (30, 4, 183),
            (30, 20, 843),
            (30, 100, 421),
            (30, 300, 386),
            (100, 1, 156),
            (100, 2, 312),
            (100, 4, 624),
            (100, 30, 2119),
            (100, 150, 419),
            (100, 300, 397),
            (300, 1, 471),
            (300, 2, 942),
            (300, 4, 1880),
            (300, 30, 3245),
            (300, 100, 475),
            (300, 300, 400),
            (1000, 1, 1574),
            (1000, 2, 3147),
            (1000, 5, 7715),
            (1000, 30, 4151),
            (1000, 100, 480),
            (1000, 300, 401),
        ],
    )
    def test_thermal_conductivity(self, rrr, temperature, expected):
        """
        Values from Hust and Lankford paper, not NIST! Different values...
        """
        op_cond = OperationalConditions(temperature=temperature)

        copper = cryo_copper(rrr)
        assert copper.residual_resistance_ratio(op_cond) == rrr
        actual = round(copper.thermal_conductivity(op_cond), 0)

        assert np.isclose(actual, expected, rtol=2e-3, atol=1.0)

    @pytest.mark.parametrize(
        "temperature,expected",
        [
            (4, 0.112),
            (7, 0.309),
            (13, 1.97),
            (20, 7.88),
            (30, 26.3),
            (40, 55.3),
            (50, 90.6),
            # Honestly, not sure how I can be getting this wrong...
            pytest.param(100, 253, marks=pytest.mark.xfail),
            pytest.param(210, 364, marks=pytest.mark.xfail),
            pytest.param(250, 372, marks=pytest.mark.xfail),
            pytest.param(300, 377, marks=pytest.mark.xfail),
        ],
    )
    def test_specific_heat(self, temperature, expected):
        """
        Values from NIST, table 7.3 (terrible data, be careful of T!)
        """
        op_cond = OperationalConditions(temperature=temperature)

        copper = cryo_copper(100.0)

        actual = copper.specific_heat_capacity(op_cond)

        assert np.isclose(actual, expected, rtol=2e-3, atol=2.0)

    @pytest.mark.xfail
    @pytest.mark.parametrize(
        "temperature,expected",
        [
            (4, 0.00239e6),
            (11, 0.0408e6),
            (20, 0.276e6),
            (40, 2.22e6),
            (100, 10.6e6),
            (300, 16.8e6),
        ],
    )
    def test_thermal_expansion(self, temperature, expected):
        """
        Values from NIST, table 7.6 (again, terrible)
        """
        op_cond = OperationalConditions(temperature=temperature)

        copper = cryo_copper(100.0)

        actual = copper.coefficient_thermal_expansion(op_cond)

        assert np.isclose(actual, expected, rtol=2e-3, atol=0.0)
