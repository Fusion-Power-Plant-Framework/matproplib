# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Miscellaneous tools for matproplib package"""

from collections.abc import Sequence
from copy import deepcopy
from operator import attrgetter

import numpy as np
import numpy.typing as npt
from scipy.interpolate import RegularGridInterpolator

from matproplib.base import References
from matproplib.conditions import OpCondT


def annotate_reference(reference: References, annotation: str) -> References:
    """
    Returns
    -------
    :
        Annotated a reference object
    """
    reference = deepcopy(reference)
    reference["id"] += annotation
    reference["annote"] = f"{reference.get('annote', '')} {annotation}".strip(" ")
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

    Returns
    -------
    :
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


class From1DData:
    """1-D Data interpolation from condition

    Parameters
    ----------
    x:
        Array of condition
    y:
        Array of resultant quantity
    condition:
        condition name

    Notes
    -----
    Uses numpy.interp under the hood
    """

    def __init__(self, x: Sequence[float], y: Sequence[float], condition: str):
        self.x = np.asarray(x)
        self.y = np.asarray(y)
        self.condition = condition

    def __call__(self, op_cond: OpCondT):
        """Call the interpolator"""  # noqa: DOC201
        return np.interp(getattr(op_cond, self.condition), self.x, self.y)


class FromNDData:
    """N-D Data interpolation from conditions

    Parameters
    ----------
    condition_array:
        Sequence of arrays of condition data
    data_array:
        Array of resultant quantity
    conditions:
        conditions used

    Notes
    -----
    Uses scipy RegularGridInterpolator under the hood
    """

    def __init__(
        self,
        condition_array: Sequence[npt.NDArray] | npt.NDArray,
        data_array: npt.NDArray,
        conditions: Sequence[str],
        method: RegularGridInterpolator._ALL_METHODS = "linear",
        **kwargs,
    ):
        if not isinstance(condition_array, tuple):
            condition_array = tuple(*condition_array)
        self.interpolator = RegularGridInterpolator(
            condition_array,
            data_array,
            method=method,
            bounds_error=kwargs.pop("bounds_error", False),
            fill_value=kwargs.pop("fill_value", None),
            **kwargs,
        )
        self.conditions = attrgetter(*conditions)

    def __call__(self, op_cond: OpCondT):
        """Call the interpolator"""  # noqa: DOC201
        return self.interpolator(self.conditions(op_cond))
