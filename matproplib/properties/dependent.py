# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Dependent properties of matproplib"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable  # noqa: TC003
from functools import partial
from typing import (
    Literal,
    Protocol,
    TypedDict,
)

import numpy as np
import periodictable as pt
from numpydantic import NDArray, Shape
from numpydantic.dtype import Number
from pint import Unit  # noqa: TC002
from pint.errors import DimensionalityError
from pydantic import Field, field_serializer, model_validator
from pydantic_core import PydanticUndefinedType
from typing_extensions import NotRequired

from matproplib.base import (
    BasePhysicalProperty,
    References,
    unit_conversion,
    ureg,
)
from matproplib.conditions import (
    DependentPropertyConditionConfig,
    OperationalConditions,
    check_conditions,
    modify_conditions,
)
from matproplib.tools.serialisation import (
    deserialise,
    inspect_lambda,
    is_lambda,
    stringify_function,
)

log = logging.getLogger("matproplib.base")


class _NoDependence: ...


ArrayFloat = float | int | NDArray[Shape["* x"], Number]


class _WrapCallable:
    def __init__(self, value, unit_val, default):
        self.value = value
        self.unit_val = unit_val
        self.default = default
        # for pickling
        self.__name__ = self.value.__name__

    def __call__(self, *args, **kwargs):
        return unit_conversion(self.value(*args, **kwargs) * self.unit_val, self.default)


def _no_dependence(value: float) -> Callable[[OperationalConditions], float]:
    class NoDependence(_NoDependence):
        """Invariant physical property

        Returns
        -------
        :
            The setup value at all operational conditions
        """

        def __call__(self, op_cond, *args, **kwargs) -> float:  # noqa: ARG002
            return value

        def __repr__(self) -> str:
            return f"<function Invariant of {value:.2g}>"

    return NoDependence()


class DependentCallable(Protocol):
    """DependentPhysicalProperty callable typing"""

    def __call__(  # noqa: D102
        self,
        op_cond: OperationalConditions,
        *args,
        **kwargs,
    ) -> float: ...


class DependentPhysicalPropertyTD(TypedDict):
    """DependentPhysicalProperty typing"""

    value: Callable[[OperationalConditions], ArrayFloat] | ArrayFloat
    unit: NotRequired[Unit | str]
    op_cond_config: NotRequired[
        DependentPropertyConditionConfig
        | dict[str, tuple[str, float, float] | tuple[str, float] | tuple[float, float]]
        | None
    ]
    reference: NotRequired[References | None]


class DependentPhysicalProperty(BasePhysicalProperty):
    """A property that is dependent on operating conditions"""

    value: Callable[[OperationalConditions], ArrayFloat]
    op_cond_config: DependentPropertyConditionConfig | None = None

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):  # noqa: PLW3201
        """Ensure default units are set for a property

        Raises
        ------
        ValueError
            Default unit not set on class
        """
        super().__pydantic_init_subclass__(**kwargs)
        if isinstance(cls.model_fields["unit"].default, PydanticUndefinedType):
            raise ValueError(  # noqa: TRY004
                f"No default unit set on {cls}."
                " Please set a default unit attribute 'unit: Unit | str = \"myunit\"'"
            )

    @field_serializer("value")
    @classmethod
    def _serialise_value(
        cls,
        value: Callable[[OperationalConditions], ArrayFloat] | None,
    ) -> ArrayFloat | bool | dict[str, float | bool] | None:
        """
        Returns
        -------
        :
            Serialised value
        """
        if isinstance(value, partial):
            value = value.func

        if isinstance(value, _NoDependence):
            return value(None)

        if isinstance(value, _WrapCallable):
            return {
                "conv_unit": value.unit_val.units,
                "func": cls._serialise_value(value.value),
            }

        if is_lambda(value):
            lam = inspect_lambda(value)
            return lam.text

        if inspect.isfunction(value):
            log.debug("function")
            return stringify_function(value)

        if value is None:
            return None

        raise NotImplementedError

    @model_validator(mode="before")
    def _from_static_value(self):
        """Static value validation"""  # noqa: DOC201
        if not isinstance(self, DependentPhysicalProperty):
            if not isinstance(self, dict):
                # Single number or a function not wrapped in a dictionary
                if isinstance(self, tuple):
                    v = self[0]
                    u = self[1]
                else:
                    v = self
                    u = None

                return {
                    "value": _no_dependence(v)
                    if isinstance(v, float | int | complex)
                    else v,
                    **({} if u is None else {"unit": u}),
                }
            if self.get("value", None) is not None and not callable(self["value"]):
                val = self["value"]
                # function or single number
                self["value"] = (
                    deserialise(val)
                    if isinstance(val, str) and ("def" in val or "lambda" in val)
                    else _no_dependence(val)
                )
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
        unit_val, default = super()._unitify()

        if unit_val.units != default or not np.isclose(unit_val.magnitude, 1):
            log.debug("Non default unit used, wrapping value")
            if type(self.value).__name__ == "NoDependence":
                wrap_callable = _no_dependence(
                    unit_conversion(unit_val * self.value(None), default)
                )
            else:
                wrap_callable = _WrapCallable(self.value, unit_val, default)
            object.__setattr__(self, "value", wrap_callable)  # noqa: PLC2801
        object.__setattr__(self, "unit", default)  # noqa: PLC2801
        return self

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
        if self.op_cond_config is not None:
            op_cond = modify_conditions(op_cond, self.op_cond_config)
            check_conditions(op_cond, self.op_cond_config)

        try:
            return (
                ureg.Quantity(
                    self.value(op_cond, *args, **kwargs),
                    self.unit,
                )
                .to(unit)
                .magnitude
            )
        except DimensionalityError as de:
            raise ValueError(
                f"Cannot convert from '{de.args[0]}' "
                f"({de.args[2]}) to '{de.args[1]}' ({de.args[3]})"
            ) from None

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
        if self.op_cond_config is not None:
            op_cond = modify_conditions(op_cond, self.op_cond_config)
            check_conditions(op_cond, self.op_cond_config)
        return self.value(op_cond, *args, **kwargs)

    def __str__(self) -> str:
        return (
            f"{type(self).__name__}(value={self.value}, "
            f"unit={self.unit:~P}, "
            f"op_cond_config={self.op_cond_config}, "
            f"reference={self.reference.__str__()})"
        )


class UndefinedProperty(DependentPhysicalProperty):
    """Undefined property"""

    value: None = Field(default=None, frozen=True)
    unit: Literal[""] = Field(default="", frozen=True)

    def __call__(self, op_cond: OperationalConditions, *args, **kwargs):
        """Call for Undefined property is undefined"""
        raise NotImplementedError("")


class Density(DependentPhysicalProperty):
    """Density of a material"""

    unit: Unit | str = "kg/m^3"

    @classmethod
    def from_nuclear_units(
        cls,
        elements: dict[str, float],
        value: float,
        unit: str = "atom/cm^3",
    ) -> Density:
        """Set density from nuclear units

        Returns
        -------
        :
            Initialised density object
        """
        tval = 0

        if "atom" in unit:
            for e_n, e_f in elements.items():
                e = getattr(pt, e_n)
                tval += (
                    ureg.Quantity(e.mass * e_f * value, e.mass_units).to("amu").magnitude
                )

        if "b-cm" in unit:
            unit = unit.replace("b-cm", "(b.cm)")

        return cls(value=tval, unit=unit.replace("atom", "amu"))


class PoissonsRatio(DependentPhysicalProperty):
    """Poisson's ratio"""

    unit: Unit | str = ""


class ThermalConductivity(DependentPhysicalProperty):
    """Thermal conductivity"""

    unit: Unit | str = "W.m/K"


class YoungsModulus(DependentPhysicalProperty):
    """Youngs Modulus"""

    unit: Unit | str = "Pa"


class ShearModulus(DependentPhysicalProperty):
    """Shear Modulus"""

    unit: Unit | str = "Pa"


class BulkModulus(DependentPhysicalProperty):
    """Bulk Modulus"""

    unit: Unit | str = "Pa"


class SpecificHeatCapacity(DependentPhysicalProperty):
    """Specific Heat Capacity"""

    unit: Unit | str = "J/kg/K"


class ThermalExpansionCoefficient(DependentPhysicalProperty):
    """Coefficient of thermal expansion (CTE)"""

    unit: Unit | str = "K^-1"


class ElectricalResistivity(DependentPhysicalProperty):
    """Electrical resistivity"""

    unit: Unit | str = "ohm.m"


class MagneticSaturation(DependentPhysicalProperty):
    """Magnetic Saturation"""

    unit: Unit | str = "A.m^2/kg"


class MagneticSusceptibility(DependentPhysicalProperty):
    """Magnetic Susceptibility"""

    unit: Unit | str = ""


class ViscousRemanentMagnetism(DependentPhysicalProperty):
    """Viscous remanent magnetism"""

    unit: Unit | str = "A.m^2/kg"


class CoerciveField(DependentPhysicalProperty):
    """Coercive Field"""

    unit: Unit | str = "A/m"


class Stress(DependentPhysicalProperty):
    """Stress"""

    unit: Unit | str = "Pa"


class DependentTemperature(DependentPhysicalProperty):
    """Dependent Temperature"""

    unit: Unit | str = "K"


class ResidualResistanceRatio(DependentPhysicalProperty):
    """Residual Resistance Ratio"""

    unit: Unit | str = ""
