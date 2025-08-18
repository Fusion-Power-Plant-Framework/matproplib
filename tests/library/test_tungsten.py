# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import numpy as np
import pytest

from matproplib import OperationalConditions
from matproplib.library.tungsten import PlanseeTungsten

W = PlanseeTungsten()


class TestPlanseeTungsten:
    def test_density(self):
        op_cond = OperationalConditions(temperature=293.15)
        assert W.density(op_cond) == 19250

    def test_poissons_ratio(self):
        op_cond = OperationalConditions(temperature=293.15)
        assert W.poissons_ratio(op_cond) == 0.28

    @pytest.mark.parametrize(
        ("t", "expected_cte"), [(200, 4.38), (800, 4.68), (1400, 5.1)]
    )
    def test_cte(self, t, expected_cte):
        op_cond = OperationalConditions(temperature=273.15 + t)
        cte = W.coefficient_thermal_expansion(op_cond) * 1e6
        assert np.isclose(cte, expected_cte)

    @pytest.mark.parametrize(("t", "expected_k"), [(25.401, 174.11), (801, 119.77)])
    def test_k(self, t, expected_k):
        op_cond = OperationalConditions(temperature=273.1499 + t)
        k = W.thermal_conductivity(op_cond)
        assert np.isclose(k, expected_k)

    @pytest.mark.parametrize(
        ("t", "expected_cp"), [(0, 0.131), (500, 0.144), (1100, 0.159)]
    )
    def test_cp(self, t, expected_cp):
        op_cond = OperationalConditions(temperature=273.15 + t)
        cte = W.specific_heat_capacity(op_cond) * 1e-3
        assert np.isclose(cte, expected_cp)

    @pytest.mark.parametrize(
        ("t", "expected_nu"), [(0, 0.04), (12.6468, 0.04), (3369.33, 1.17)]
    )
    def test_nu(self, t, expected_nu):
        op_cond = OperationalConditions(temperature=273.15 + t)
        nu = W.electrical_resistivity(op_cond) * 1e6
        assert np.isclose(nu, expected_nu)

    @pytest.mark.parametrize(("t", "expected_ym"), [(56.423, 407.78), (2002.1, 280.27)])
    def test_ym(self, t, expected_ym):
        op_cond = OperationalConditions(temperature=273.15 + t)
        ym = W.youngs_modulus(op_cond) * 1e-9
        assert np.isclose(ym, expected_ym)
