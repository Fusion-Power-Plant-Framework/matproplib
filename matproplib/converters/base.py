# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Dependent properties of matproplib"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING, Generic, TypeVar

from pydantic import Field, RootModel, SerializeAsAny, model_validator

from matproplib.base import PMBaseModel, all_subclasses

if TYPE_CHECKING:
    from matproplib.conditions import OpCondT
    from matproplib.material import Material


ConverterK = TypeVar("ConverterK", bound=str)


class Converters(RootModel[ConverterK], Generic[ConverterK]):
    """
    Converter grouping object

    Collects all objects to convert materials into other formats
    """

    root: SerializeAsAny[dict[ConverterK, Converter]] = Field(default_factory=dict)

    def add(self, converter: Converter):
        """Add a converter to the group"""
        self.root[converter.name] = converter

    @model_validator(mode="before")
    def _validation(self):
        if not isinstance(self, dict | Converter) and isinstance(self, Iterable):
            return {conv.name: conv for conv in self}
        if isinstance(self, Converter):
            return {self.name: self}
        if isinstance(self, dict):
            return {
                k: conv_cls.model_validate(self)
                for k in self
                for conv_cls in all_subclasses(Converter)
                if hasattr(conv_cls, "name") and conv_cls.name == k
            }
        return self

    def __iter__(self):  # noqa: D105
        return iter(self.root.items())

    def __getitem__(self, item):  # noqa: D105
        return self.root[item]

    def __getattr__(self, name: str):  # noqa: D105
        if name == "root":
            return super().__getattr__(name)
        return self.__getitem__(name)

    def __setattr__(self, name: str, value):  # noqa: D105
        if name == "root":
            super().__setattr__(name, value)
        self.root[name] = value

    def __repr__(self) -> str:  # noqa: D105
        converters = ", ".join(v.__repr__() for v in self.root.values())
        return f"{type(self).__name__}({converters})"


class Converter(PMBaseModel, ABC):
    """Base converter object for material format converters"""

    name: str

    @abstractmethod
    def convert(self, material: Material, op_cond: OpCondT):
        """Function to convert material to secondary format"""
