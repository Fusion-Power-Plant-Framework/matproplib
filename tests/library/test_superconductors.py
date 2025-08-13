# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import numpy as np
import pytest

from physical_materials.conditions import OperationalConditions
from physical_materials.library.superconductors import (
    NB3SN_CERN_STRAND,
    NB3SN_CSJA6_STRAND,
    NB3SN_EUTF4_STRAND,
    NBS3N_WST_TF_STRAND,
)


class TestParameterisations:
    @classmethod
    def setup_class(cls):
        n_points = 25
        temperatures = np.linspace(4.0, 20.0, n_points)
        magnetic_fields = np.linspace(0.0, 20.0, n_points)
        cls.strain = -0.0055

        cls.xx, cls.yy = np.meshgrid(temperatures, magnetic_fields)
        cls.ind = np.triu_indices(n_points)

    @pytest.mark.parametrize(
        "parameterisation",
        [NBS3N_WST_TF_STRAND, NB3SN_CSJA6_STRAND, NB3SN_CERN_STRAND, NB3SN_EUTF4_STRAND],
    )
    def test_nb3sn_real_positive(self, parameterisation):
        j_crit = np.zeros_like(self.xx)

        op_cond = OperationalConditions(
            temperature=self.xx[self.ind],
            magnetic_field=self.yy[self.ind],
            strain=self.strain,
        )
        j_crit[self.ind] = parameterisation.critical_current_density(op_cond)

        assert np.all(j_crit >= 0.0)
        assert np.all(~np.isnan(j_crit))


def test_summers_cern_strand():
    """
    https://conferences.lbl.gov/event/979/contributions/5985/attachments/4069/3482/U9-U10_final.pdf slide 25
    """
    op_cond = OperationalConditions(temperature=4.2, magnetic_field=12.0, strain=0.0)
    j_crit = NB3SN_CERN_STRAND.critical_current_density(op_cond)
    assert np.isclose(j_crit, 2.9e9, rtol=1e-3, atol=0.0)
