# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
import pytest

from matproplib.library.superconductors import (
    NB3SN_CERN_STRAND,
    NB3SN_CSJA6_STRAND,
    NB3SN_EUTF4_STRAND,
    NBS3N_WST_TF_STRAND,
)
from matproplib.tools.plotting import plot_superconductor


@pytest.mark.parametrize(
    "parameterisation",
    [
        NB3SN_CERN_STRAND,
        NB3SN_CSJA6_STRAND,
        NB3SN_EUTF4_STRAND,
        NBS3N_WST_TF_STRAND,
    ],
)
def test_superconductor_plotting(parameterisation):
    # Example usage

    plot_superconductor(parameterisation, 4.0, 20.0, 1.0, 15.0, -0.0055, n_points=10)
