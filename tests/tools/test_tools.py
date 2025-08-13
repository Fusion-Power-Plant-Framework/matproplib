# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import numpy as np
import pytest

from physical_materials.tools.tools import kludge_linear_spline


@pytest.mark.parametrize(
    "x,x_expected",
    [
        (1.0e6, 1.0e6),
        (1.0, 1.0),
        (0.5, 0.5),
        (0.1, 0.1),
        (0.01, 0.01),
        (-1e6, 0.0),
    ],
)
def test_kludge_linear_spline_outside_kludge(x, x_expected):
    """Test the kludge linear spline function."""
    y_new = kludge_linear_spline(x, 0.001, 0.0001)
    assert np.isclose(x_expected, y_new)


def test_kludge_linear_spline_inside_kludge():
    x = np.linspace(0.01, -0.01, 100)
    y_new = kludge_linear_spline(x, 0.001, 0.0001)
    assert np.all(y_new >= 0.0)

    for i in range(len(x) - 1):
        assert y_new[i + 1] <= y_new[i]
