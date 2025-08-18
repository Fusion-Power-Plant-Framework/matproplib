# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from matproplib import OperationalConditions
from matproplib.library.tungsten import PlanseeTungsten

W = PlanseeTungsten()


class TestPlanseeTungsten:
    def test_density(self):
        op_cond = OperationalConditions(temperature=293.15)
        assert W.density(op_cond) == 19250
