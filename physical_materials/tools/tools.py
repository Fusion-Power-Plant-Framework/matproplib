# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Miscellaneous tools for physical materials package"""

from copy import deepcopy
import numpy as np
from physical_materials.base import References


def annotate_reference(reference: References, annotation: str) -> References:
    """
    Annotate a reference object
    """
    reference = deepcopy(reference)
    reference["id"] += annotation

    if reference.get("annote") is not None:
        reference["annote"] += f" {annotation}"
    else:
        reference["annote"] = annotation
    return reference


@np.vectorize
def _kludge_spline(
    x: float, x0: float, x1: float, y0: float, y1: float, p0: float
) -> float:
    t1 = (x - x1) ** 2
    t2 = (x - x0) ** 2
    t3 = (x1 - x0) ** 3
    t4 = (x1 - x0) ** 2

    term1 = y0 * t1 / t3 * (2.0 * x - 3.0 * x0 + x1)
    term2 = -y1 * t2 / t3 * (2.0 * x + x0 - 3.0 * x1)
    term3 = p0 * t1 / t4 * (x - x0)
    term4 = t2 / t4 * (x - x1)

    return term1 + term2 + term3 + term4


@np.vectorize
def kludge_linear_spline(x: float, x_kludge: float, width: float) -> float:
    """Kludge a value below a certain minimum value with
    linear slope and cubic spline transition.

    For x < x_kludge:
        0.0 < x < x_kludge

    Linear kludge with cubic spline transition.

    Notes
    -----
    This is a kludge to avoid negative values by providing a smooth transition from the
    intended function to a linear function below a certain minimum value.
    The transition is cubic spline based on the minimum value and a width parameter.
    There is still the potential to return negative values if the input is much lower
    than the input which first produces a negative value.
    """
    p0 = 1e-8  # Chosen to give a very shallow slope to 0.0
    x0 = x_kludge - width
    x1 = x_kludge + width
    y0 = x_kludge
    y1 = x_kludge + width

    if x < x0:
        return max(0.0, p0 * x + y0)
    if x < x1:
        return _kludge_spline(x, x0, x1, y0, y1, p0)
    return x
