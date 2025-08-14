# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Conditions of a Material"""

from __future__ import annotations

from typing import get_args

import numpy as np
from numpydantic import NDArray, Shape
from numpydantic.dtype import Number
from pint import Unit
from pydantic import (
    ConfigDict,
    Field,
    create_model,
    field_serializer,
    field_validator,
    model_serializer,
    model_validator,
)

from matproplib.base import PMBaseModel, ureg
from matproplib.properties.independent import (
    MagneticField,
    NeutronDamage,
    NeutronFluence,
    PhysicalProperty,
    Pressure,
    Strain,
    Temperature,
)

__all__ = [
    "DependentPropertyConditionConfig",
    "OperationalConditions",
    "PropertyConfig",
    "STPConditions",
    "check_conditions",
    "modify_conditions",
]


class OperationalConditions(PMBaseModel):
    """Operating conditions of a given material"""

    temperature: Temperature
    pressure: Pressure | None = None
    magnetic_field: MagneticField | None = None
    strain: Strain | None = None
    neutron_damage: NeutronDamage | None = None
    neutron_fluence: NeutronFluence | None = None
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    def __str__(self) -> str:  # noqa: D105
        return f"{type(self).__name__}({super().__str__()})"

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):  # noqa: PLW3201
        """Ensure all attributes are Physical Properties

        Raises
        ------
        TypeError
            If the attribute is not a physical property
        """
        super().__pydantic_init_subclass__(**kwargs)

        pm_fields = PMBaseModel.model_fields.keys()
        for f_name, field in cls.model_fields.items():
            if f_name not in pm_fields and not issubclass(
                field.annotation, PhysicalProperty
            ):
                for ann_type in get_args(field.annotation):
                    if issubclass(ann_type, PhysicalProperty):
                        break
                else:
                    raise TypeError(
                        "OperationalCondition field types must be"
                        " PhysicalProperty types or None"
                    )

    @model_validator(mode="before")
    def _value_only(self):
        """Allow value setting with default units

        Returns
        -------
        :
            the operating conditions instance
        """
        for k, v in self.items():
            if (
                v is not None
                and not isinstance(v, dict)
                and not isinstance(v, PhysicalProperty)
            ):
                self[k] = {"value": v}
        return self

    @model_validator(mode="after")
    def _all_values_same_length(self):
        """Validate ther are the same number of conditions

        Returns
        -------
        :
            the operating conditions instance

        Raises
        ------
        ValueError
            If value sizes are not compatible
        """
        fields = dict(iter(self))
        values = list(fields.values())
        old_length = length = (
            values[0].value.size if isinstance(values[0].value, np.ndarray) else 1
        )
        for v in values[1:]:
            if v is not None and isinstance(v.value, np.ndarray):
                if length == 1:
                    length = v.value.size
                elif v.value.size != length:
                    raise ValueError(
                        "All values must be of equal size or a singular value"
                    )
            else:
                old_length = 0

        if old_length != length:
            for k, v in fields.items():
                if v is not None and (
                    not isinstance(v.value, np.ndarray) or v.value.size == 1
                ):
                    v_dat = v.model_dump()
                    val = v_dat.pop("value")
                    value = np.full(
                        length, val.magnitude if isinstance(val, ureg.Quantity) else val
                    )
                    object.__setattr__(  # noqa: PLC2801
                        self, k, type(v)(value=value, **v_dat)
                    )
        return self


class PropertyConfig(PMBaseModel):
    """Configuration model found bounding properties in a given unit"""

    unit: Unit | str | None = None
    lower: float | None = None
    upper: float | None = None

    @model_validator(mode="before")
    def _convert_to_structure(self):
        if isinstance(self, str | Unit):
            return {"unit": self}
        if isinstance(self, tuple):
            if not isinstance(self[0], str) and len(self) == 2:  # noqa: PLR2004
                return {"lower": self[0], "upper": self[1]}
            if len(self) == 2:  # noqa: PLR2004
                return {"unit": self[0], "lower": self[1]}
            if len(self) == 3:  # noqa: PLR2004
                return {"unit": self[0], "lower": self[1], "upper": self[2]}
        return self

    @field_validator("unit", mode="after")
    @staticmethod
    def _unit_valid(unit):
        return ureg.Unit(unit)

    @field_serializer("unit")
    @staticmethod
    def _serialise_unit(unit: Unit) -> str:
        """
        Returns
        -------
        :
            Serialised a unit
        """
        return f"{unit:~P}"


DependentPropertyConditionConfigTD = dict[
    str, tuple[str, float, float] | str | Unit | tuple[str, float] | tuple[float, float]
]


class DependentPropertyConditionConfig(PMBaseModel):
    """Configuration of limits of a dependent property for its operational conditions"""

    temperature: PropertyConfig = Field(default_factory=lambda: PropertyConfig(unit="K"))
    pressure: PropertyConfig = Field(default_factory=lambda: PropertyConfig(unit="Pa"))
    magnetic_field: PropertyConfig = Field(
        default_factory=lambda: PropertyConfig(unit="T")
    )
    strain: PropertyConfig = Field(default_factory=lambda: PropertyConfig(unit=""))
    neutron_damage: PropertyConfig = Field(
        default_factory=lambda: PropertyConfig(unit="dpa")
    )
    model_config = ConfigDict(extra="allow")

    def __repr__(self) -> str:
        """
        Returns
        -------
        :
            String representation
        """
        cls = type(self)
        cells = "".join([
            f"{k}={type(v).__name__}({v})"
            for k, v in self
            if k not in cls.model_fields or v != cls.model_fields[k].default_factory()
        ])
        return f"{cls.__name__}({cells})"

    __str__ = __repr__

    @model_validator(mode="after")
    def _pass_int_default_unit(self):
        for n, v in self:
            if not isinstance(v, PropertyConfig):
                v = PropertyConfig.model_validate(v)  # noqa: PLW2901
                setattr(self, n, v)
            if v.unit is None:
                field = type(self).model_fields.get(n, None)
                if field is None:
                    raise ValueError("Unit required for unknown condition configuration")
                v.unit = field.default_factory().unit
        return self

    @model_serializer
    def _serialise_op_cond_config(self) -> dict[str, PropertyConfig]:
        cls = type(self)
        return {k: v for k, v in self if v != cls.model_fields[k].default_factory()}


def modify_conditions(
    op_cond: OperationalConditions, op_cond_config: DependentPropertyConditionConfig
) -> OperationalConditions:
    """
    Modify conditions to fit unit of condition configuration

    Returns
    -------
    :
        Modified conditions
    """
    models = {}

    cond_unit_names = [c[0] for c in op_cond_config]
    for cond_n, cond_v in op_cond:
        if cond_v is not None:
            entry = getattr(op_cond, cond_n)
            if cond_n in cond_unit_names:
                new_unit = getattr(op_cond_config, cond_n).unit
                if new_unit != cond_v.unit:
                    models[cond_n] = create_model(
                        f"Modified_{type(cond_v).__name__}",
                        __base__=PhysicalProperty,
                        value=(
                            NDArray[Shape["* x"], Number] | float,
                            ureg.Quantity(cond_v.value, cond_v.unit).to(new_unit),
                        ),
                        unit=(Unit | str, new_unit),
                    )()

                else:
                    models[cond_n] = entry
            else:
                models[cond_n] = entry
    return create_model(
        "ModifiedOperationalConditions",
        __base__=OperationalConditions,
        **{name: (type(model), model) for name, model in models.items()},
    )()


def _format_value(cond: PhysicalProperty | float, unit: Unit | None = None) -> str:
    if unit is None and isinstance(cond, PhysicalProperty):
        val = cond.value
        unit = cond.unit
    else:
        val = cond

    fmt = ".2g" if val > 1e4 else ".2f"  # noqa: PLR2004

    return f"{val:{fmt}} {unit:~P}"


def check_conditions(
    op_cond: OperationalConditions, op_cond_config: DependentPropertyConditionConfig
):
    """Check condtions are within range of condition configuration

    Raises
    ------
    ValueError
        Out of bounds
    """
    empty = PropertyConfig()
    for name, cond in op_cond:
        cond_conf = getattr(op_cond_config, name, empty)
        if cond_conf.lower is not None and np.less(cond, cond_conf.lower).all():
            raise ValueError(
                f"Operating condition '{name}' ({_format_value(cond)}) lower"
                f" than lower bound {_format_value(cond_conf.lower, cond_conf.unit)}"
            )
        if cond_conf.upper is not None and np.greater(cond, cond_conf.upper).all():
            raise ValueError(
                f"Operating condition '{name} ({_format_value(cond)})' higher"
                f" than upper bound {_format_value(cond_conf.upper, cond_conf.unit)}"
            )


class STPConditions(OperationalConditions):
    """IUPAC standard temperature and pressure"""

    temperature: Temperature = Field(default=Temperature(value=273.15), frozen=True)
    pressure: Pressure = Field(default=Pressure(value=100, unit="kPa"), frozen=True)

    @model_validator(mode="after")
    def _enforce_frozen_stp(self) -> STPConditions:
        if any(
            getattr(self, k).value != type(self).model_fields[k].default.value
            for k in ("temperature", "pressure")
        ):
            raise ValueError(
                "Standard temperature and pressure conditions cannot be modified"
            )
        return self

    def __copy__(self) -> OperationalConditions:
        """
        Copy a standard condition object to allow modification

        Returns
        -------
        :
            OperationalConditions not STPConditions
        """
        md = self.model_dump()

        return OperationalConditions(
            temperature=md.pop("temperature"), pressure=md.pop("pressure"), **md
        )
