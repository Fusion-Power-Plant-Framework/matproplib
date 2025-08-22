# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Conditions of a Material"""

from __future__ import annotations

from numbers import Number
from typing import Any

import numpy as np
from pint import Quantity, Unit
from pint.errors import DimensionalityError
from pydantic import Field, create_model, model_validator

from matproplib.base import BasePhysicalProperty, unit_conversion, ureg

__all__ = [
    "MagneticField",
    "NeutronDamage",
    "NeutronFluence",
    "PhysicalProperty",
    "Pressure",
    "Strain",
    "Temperature",
]


class PhysicalProperty(BasePhysicalProperty, np.lib.mixins.NDArrayOperatorsMixin):
    """Independent Physical Property model"""

    @model_validator(mode="before")
    def _value_entry(self):
        """Validate value"""  # noqa: DOC201
        if isinstance(self, float | int | np.ndarray | list):
            return {"value": self}

        if isinstance(self, Quantity):
            return {"value": self.magnitude, "unit": self.units}

        if isinstance(self, tuple) and len(self) == 2:  # noqa: PLR2004
            return {"value": self[0], "unit": self[1]}

        if isinstance(self, dict):
            val = self.get("value", None)
            if isinstance(val, Quantity):
                return {"value": val.magnitude, "unit": val.units}
            if isinstance(val, tuple) and len(val) == 2:  # noqa: PLR2004
                return {"value": val[0], "unit": val[1]}

        return self

    @model_validator(mode="after")
    def _unitify(self):
        """Convert value and unit to default

        Raises
        ------
        ValueError
            Failed unit conversion

        Returns
        -------
        :
            The property instance
        """
        dunit = type(self).model_fields["unit"].default
        if isinstance(dunit, Unit) and self.unit == dunit:
            return self

        unit_val, default = super()._unitify()

        if unit_val.units != default or not np.isclose(unit_val.magnitude, 1):
            object.__setattr__(  # noqa: PLC2801
                self, "value", unit_conversion(unit_val * self.value, default)
            )
        object.__setattr__(self, "unit", default)  # noqa: PLC2801
        return self

    def value_as(self, unit: str | Unit) -> float:
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
        try:
            return ureg.Quantity(self.value, self.unit).to(unit).magnitude
        except DimensionalityError as de:
            raise ValueError(
                f"Cannot convert from '{de.args[0]}' "
                f"({de.args[2]}) to '{de.args[1]}' ({de.args[3]})"
            ) from None

    def __eq__(self, other: PhysicalProperty) -> bool:
        """
        Returns
        -------
        :
            The boolean of equality
        """
        return not (
            type(self) is not type(other)
            or not np.allclose(self.value, other.value)
            or not self.unit == other.unit
        )

    def __hash__(self):
        """
        Returns
        -------
        :
            hash of object
        """
        return hash((self.value, self.unit))

    def __abs__(self):  # noqa: D105
        return np.abs(self.value)

    def __array_ufunc__(  # noqa: PLW3201
        self, ufunc: np.ufunc, method: str, *inputs: Any, **kwargs: Any
    ) -> float | tuple[float, ...]:
        """Array options for physical properties"""  # noqa: DOC201
        out = kwargs.get("out", ())
        for x in inputs + out:
            if not isinstance(x, np.ndarray | Number | PhysicalProperty):
                return NotImplemented

        inputs = tuple(x.value if isinstance(x, PhysicalProperty) else x for x in inputs)
        if out:
            kwargs["out"] = tuple(
                x.value if isinstance(x, PhysicalProperty) else x for x in out
            )

        result = getattr(ufunc, method)(*inputs, **kwargs)

        if isinstance(result, tuple):
            return tuple(
                x.value if isinstance(x, PhysicalProperty) else x for x in result
            )
        if isinstance(result, type(self)):
            return result.value
        return result

    def __array_function__(self, func, types: tuple[type, ...], args, kwargs) -> float:  # noqa: PLW3201
        """Array options for physical properties"""  # noqa: DOC201
        if not all(issubclass(t, PhysicalProperty | Number | np.ndarray) for t in types):
            return NotImplemented

        args = tuple(x.value if isinstance(x, PhysicalProperty) else x for x in args)
        return func(*args, **kwargs)


def pp(name: str, unit: str | Unit) -> PhysicalProperty:
    return create_model(
        name,
        __base__=PhysicalProperty,
        unit=(Unit | str, Field(default=unit, validate_default=True)),
    )


class Temperature(PhysicalProperty):
    """Temperature of a material"""

    unit: Unit | str = ureg.Unit("K")

    @model_validator(mode="after")
    def _k_below_0(self):
        """Validate negative temperature

        Raises
        ------
        ValueError
            Less than 0K
        """  # noqa: DOC201
        value = (
            ureg.Quantity(self.value, self.unit).to("K")
            if self.unit != ureg.Unit("K")
            else self.value
        )
        if any(np.atleast_1d(np.less(value, 0))):
            raise ValueError("Temperature cannot be below 0 K")
        return self


class Pressure(PhysicalProperty):
    """Pressure on a material"""

    unit: Unit | str = ureg.Unit("Pa")


class MagneticField(PhysicalProperty):
    """Magnetic field on a material"""

    unit: Unit | str = ureg.Unit("T")


class Strain(PhysicalProperty):
    """Strain on a material"""

    unit: Unit | str = ""


class NeutronDamage(PhysicalProperty):
    """Neutron damage of a material"""

    unit: Unit | str = "dpa"


class NeutronFluence(PhysicalProperty):
    """Neutron damage of a material"""

    unit: Unit | str = "1/m^2"


class CurrentDensity(PhysicalProperty):
    """Current density of a material"""

    unit: Unit | str = "A/m^2"


class Volume(PhysicalProperty):
    """Volume of a material"""

    unit: Unit | str = "m^3"
