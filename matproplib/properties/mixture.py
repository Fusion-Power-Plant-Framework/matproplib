# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Mixtures of properties"""

import logging
from typing import Generic, TypeVar

import numpy as np
from numpydantic import NDArray, Shape
from numpydantic.dtype import Number
from pint import Unit
from pydantic import Field, field_validator, model_validator

from matproplib.base import PMBaseModel
from matproplib.conditions import (
    OperationalConditions,
)
from matproplib.properties.dependent import DependentPhysicalProperty

DependentPhysicalPropertyT = TypeVar(
    "DependentPhysicalPropertyT", bound=DependentPhysicalProperty
)

log = logging.getLogger(__name__)


class Mixture(PMBaseModel, Generic[DependentPhysicalPropertyT]):
    """
    Mixture of properties

    Mixes using atomic fractions
    """

    dpp: list[DependentPhysicalPropertyT]
    fractions: NDArray[Shape["* x"], Number] = Field(default=[1])  # noqa: F722
    unit: Unit | str
    _unit_warn: bool = False

    @staticmethod
    def _fix_sizes(out: list[np.ndarray | float]):
        if any(isinstance(o, np.ndarray) for o in out):
            sizes = np.unique([o.size if isinstance(o, np.ndarray) else 1 for o in out])
            if sizes.size > 2:  # noqa: PLR2004
                raise NotImplementedError("Cannot mix independently sized arrays")
            if sizes.size == 2 and 1 in sizes:  # noqa: PLR2004
                size = max(sizes)
                for no, o in enumerate(out):
                    if not isinstance(o, np.ndarray):
                        out[no] = np.full(size, o)
        return np.asarray(out)

    @model_validator(mode="after")
    def _warn_on_unit_difference(self):
        units = [dp.unit != self.unit for dp in self.dpp[1:]]
        if any(units) and not self._unit_warn:
            log.warning(
                f"Output units for {type(self.dpp[0]).__name__} "
                f"are not the same across mixture. Outputting in {self.unit:~P}."
            )
            self._unit_warn = True
            self.__call__ = lambda *args, unit=self.unit, **kwargs: self.value_as(
                *args, unit=unit, **kwargs
            )

        return self

    @field_validator("fractions", mode="after")
    @classmethod
    def _fraction_array(cls, value):
        return np.asarray(value)

    def _fractional_calc(self, out: list[float | np.ndarray]):
        return np.einsum(
            "i..., i",
            self._fix_sizes(out),
            self.fractions,
        )

    def value_as(
        self,
        op_cond: OperationalConditions,
        unit: str | Unit,
        *args,
        **kwargs,
    ) -> float:
        """
        Returns
        -------
        :
            value in another unit

        Raises
        ------
        ValueError
            Failed unit conversion
        """
        return self._fractional_calc([
            d.value_as(op_cond, unit, *args, **kwargs) for d in self.dpp
        ])

    def __call__(
        self,
        op_cond: OperationalConditions,
        *args,
        **kwargs,
    ) -> float:
        """Helper to inject and modify conditions as required

        Returns
        -------
        :
            Property value at conditons
        """
        return self._fractional_calc([d(op_cond, *args, **kwargs) for d in self.dpp])

    # def __str__
