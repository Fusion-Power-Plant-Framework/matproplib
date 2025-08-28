# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Base of matproplib"""

from __future__ import annotations

import inspect
import logging
import operator
from abc import ABC
from functools import partial, reduce
from typing import TYPE_CHECKING, Any, ClassVar, Literal

import numpy as np
from csl_reference import Reference
from numpydantic import NDArray, Shape
from numpydantic.dtype import Number
from pint import Quantity, Unit, UnitRegistry
from pint.errors import DimensionalityError
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    create_model,
    field_serializer,
    field_validator,
    model_validator,
)
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefinedType
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from collections.abc import Generator

__all__ = [
    "BaseGroup",
    "BasePhysicalProperty",
    "PMBaseModel",
    "References",
    "SuperconductingParameterisation",
    "UndefinedSuperconductingParameterisation",
    "rebuild",
    "unit_conversion",
    "ureg",
]


log = logging.getLogger(__name__)


class MaterialUnitRegistry(UnitRegistry):
    """Physical Materials unit registry"""

    def __init__(self):
        super().__init__(fmt_locale="en_gb", autoconvert_offset_to_baseunit=True)
        self.define("displacements_per_atom = count = dpa")


ureg = MaterialUnitRegistry()

N_AVOGADRO = ureg.Quantity("avogadro_number").to_base_units().magnitude

ArrayFloat = float | int | NDArray[Shape["* x"], Number]


class _Wrapped:
    """Class for type checking dpp decorator use"""


def unit_conversion(unitval: str | Quantity | Unit, default: str) -> float:
    """Convertion of a unit wrapping pint

    Returns
    -------
    :
        the converted value

    Raises
    ------
    ValueError
        Failed unit conversion
    """
    try:
        return ureg.Quantity(unitval).to(default).magnitude
    except DimensionalityError as de:
        raise ValueError(
            f"Cannot convert from '{de.args[0]}' "
            f"({de.args[2]}) to '{de.args[1]}' ({de.args[3]})"
        ) from None


class References(RootModel):
    """Reference collection model"""

    root: dict[str | float, Reference]

    @model_validator(mode="before")
    def _list_to_dict(self):
        if isinstance(self, list):
            return {
                r.id if isinstance(r, Reference) else r["id"]: Reference.model_validate(
                    r
                )
                for r in self
            }
        if "id" in self:
            return {self["id"]: self}

        if hasattr(self, "type"):
            return {self.id: self}
        return self

    def __iter__(self):  # noqa: D105
        return iter(self.root.items())

    def __getitem__(self, item):  # noqa: D105
        return self.root[item]

    def __str__(self) -> str:  # noqa: D105
        return " ".join(f"[{k}] {ref.__str__()}" for k, ref in self.root.items())

    def combine(self, reference: References | Reference):
        """Combine references into this reference object"""
        if isinstance(reference, References):
            for k, r in reference:
                self.root[k] = r
        if isinstance(reference, Reference):
            self.root[reference.id] = reference


class PMBaseModel(BaseModel, ABC):
    """Base model for physical_material"""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    reference: References | None = None

    def _fields(self):
        base_field_names = PMBaseModel.model_fields.keys()
        return dict(
            filter(
                lambda pair: pair[0] not in base_field_names, dict(iter(self)).items()
            )
        )

    def __iter__(self) -> Generator[tuple[str, Any], None, None]:
        """Iteration for Base model ignoring 'reference'

        Yields
        ------
        :
            field name
        :
            field value
        """
        yield from [
            (k, v)
            for (k, v) in self.__dict__.items()
            if not k.startswith("_") and k != "reference"
        ]
        extra = self.__pydantic_extra__
        if extra and extra.get("__pydantic_extra__", None) != {}:
            yield from extra.items()

    def __dir__(self) -> set[str]:
        """List methods only if they dont exist in pydantic basemodel

        Returns
        -------
        :
            subset of attributes
        """
        return set(super().__dir__()).difference(dir(BaseModel))


class MaterialBaseModel(PMBaseModel, ABC):
    @model_validator(mode="after")
    def _inject_group(self):
        from matproplib.properties.dependent import (  # noqa: PLC0415
            DependentPhysicalProperty,
            _NoDependence,
            _WrapCallable,
        )

        for prop in filter(
            lambda x: not x.startswith("_"), set(dir(self)).difference(dir(BaseGroup))
        ):
            attr = getattr(self, prop)
            if (
                isinstance(attr, DependentPhysicalProperty)
                and attr.value is not None
                and not isinstance(attr.value, partial)
                and not isinstance(attr.value, _NoDependence)
            ):
                if isinstance(attr.value, _WrapCallable) and _injection_check(
                    attr.value.value
                ):
                    object.__setattr__(  # noqa: PLC2801
                        attr.value, "value", partial(attr.value.value, self)
                    )
                elif _injection_check(attr.value):
                    object.__setattr__(attr, "value", partial(attr.value, self))  # noqa: PLC2801
        return self


class BasePhysicalProperty(PMBaseModel, ABC):
    """Physical properties of a material"""

    value: ArrayFloat
    unit: Unit | str

    model_config = ConfigDict(frozen=True)

    @field_validator("value", mode="before")
    @staticmethod
    def array_validation(value):
        """Flatten extra array dimensions

        Returns
        -------
        :
            modified value
        """
        if isinstance(value, np.ndarray):
            return np.squeeze(value)
        return value

    def _unitify(self) -> Quantity:
        dunit = type(self).model_fields["unit"].default
        if isinstance(dunit, Unit) and self.unit == dunit:
            return ureg.Quantity(1, self.unit), dunit
        if isinstance(dunit, PydanticUndefinedType):
            raise NotImplementedError("default unit must be provided on class")
        if isinstance(dunit, Unit):
            dmag = 1
            default = dunit
        else:
            default = (
                ureg.Quantity(dunit or "dimensionless")
                if isinstance(dunit, str)
                else ureg.Quantity(1, dunit)
            )
            dmag = default.magnitude
            default = default.units
        if not (dmag == 1 or np.isclose(dmag, 1)):
            log.debug(
                f"default unit for {type(self).__name__} has multiplier."
                f" Return value will converted to {default: ~P}"
            )
        if self.unit == "":  # noqa: PLC1901
            return ureg.Quantity(1, self.unit), default
        if isinstance(self.unit, str) and self.unit[0].isdigit():
            return ureg.Quantity(f"{self.unit}"), default
        return ureg.Quantity(1, self.unit), default

    @field_serializer("unit")
    @staticmethod
    def serialise_unit(unit: Unit) -> str:
        """
        Returns
        -------
        :
            Serialised a unit
        """
        return f"{unit:~P}"

    def __hash__(self):
        """
        Returns
        -------
        :
            hash of object
        """
        return hash((type(self).name, self.value, self.unit))


class BaseGroup(MaterialBaseModel):
    """Base properties grouping class"""

    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)

    def list(self, *, include_undefined: bool | None = False) -> list[str]:
        """
        Returns
        -------
        :
            List of defined properties
        """
        from matproplib.properties.dependent import (  # noqa: PLC0415
            UndefinedProperty,
        )

        statement = (
            (lambda _v: True)
            if include_undefined is True
            else (lambda v: not isinstance(v, UndefinedProperty))
            if include_undefined is False
            else (lambda v: isinstance(v, UndefinedProperty))
        )
        return [k for k, v in self if statement(v)]


def _injection_check(func, keys=("properties", "self")):
    sig = inspect.signature(func).parameters
    return any(k in sig for k in keys)


def rebuild(cls):
    """Function to rebuild pydantic model to allow decorated creation of submodels

    Returns
    -------
    :
        modified class
    """
    from matproplib.properties.dependent import (  # noqa: PLC0415
        DependentPhysicalProperty,
    )

    extras = {}
    methods = {"__module__": cls.__module__}
    fields = cls.model_fields
    for prop in set(dir(cls)).difference(
        reduce(operator.iadd, [dir(c) for c in cls.__bases__], [])
    ):
        extra = getattr(cls, prop)
        if isinstance(extra, DependentPhysicalProperty):
            extras[prop] = (type(extra), Field(default=extra, validate_default=True))
        else:
            methods[prop] = extra

    props = fields.pop("properties", None)

    mf = {
        k: (
            v.annotation,
            Field(
                default=v.default,
                default_factory=v.default_factory,
                validate_default=v.validate_default,
            ),
        )
        for k, v in fields.items()
    }

    if props is not None:
        if isinstance(props, FieldInfo):
            for k, v in props.default_factory.model_fields.items():
                if k != "reference":
                    mf[k] = (
                        v.annotation,
                        Field(
                            default=v.default,
                            default_factory=v.default_factory,
                            validate_default=v.validate_default,
                        ),
                    )
        else:
            raise NotImplementedError

    model = create_model(
        cls.__name__,
        __base__=type("_DynamicParent", cls.__bases__, methods),
        **mf,
        **extras,
    )
    return cls_vars(model, cls, methods)


def cls_vars(model, orig_cls, methods):
    classvars = {cv: getattr(orig_cls, cv) for cv in methods.get("__class_vars__", {})}
    for name, val in classvars.items():
        setattr(model, name, val)
    return model


def all_subclasses(cls):
    return set(cls.__subclasses__()).union([
        s for c in cls.__subclasses__() for s in all_subclasses(c)
    ])


class SuperconductingParameterisation(BaseGroup):
    """Superconducting Parameterisation base model"""

    name: ClassVar[Literal["base"]] = "base"


class UndefinedSuperconductingParameterisation(SuperconductingParameterisation):
    """Undefined Superconducting Parameterisation base model"""

    name: ClassVar[Literal["undef"]] = "undef"


SuperconductingParameterisationT_co = TypeVar(
    "SuperconductingParameterisationT_co",
    bound=SuperconductingParameterisation,
    covariant=True,
    default=UndefinedSuperconductingParameterisation,
)
