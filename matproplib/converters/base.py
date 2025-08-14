# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Dependent properties of physical materials"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING, Generic, TypeVar

from pydantic import Field, RootModel, model_validator

from matproplib.base import PMBaseModel

if TYPE_CHECKING:
    from matproplib.conditions import OperationalConditions
    from matproplib.materials import Material


ConverterK = TypeVar("ConverterK", bound=str)


class Converters(RootModel[ConverterK], Generic[ConverterK]):
    root: dict[ConverterK, Converter] = Field(default_factory=dict)

    def add(self, converter: Converter):
        self.root[converter.name] = converter

    @model_validator(mode="before")
    def _validation(self):
        if not isinstance(self, dict | Converter) and isinstance(self, Iterable):
            return {conv.name: conv for conv in self}
        if isinstance(self, Converter):
            return {self.name: self}
        return self

    def __iter__(self):  # noqa: D105
        return iter(self.root.items())

    def __getitem__(self, item):  # noqa: D105
        return self.root[item]

    def __getattr__(self, name: str):
        if name == "root":
            return super().__getattr__(name)
        return self.__getitem__(name)

    def __setattr__(self, name: str, value):
        if name == "root":
            super().__setattr__(name, value)
        self.root[name] = value
        # TODO fix for subclass validation
        # Converter.model_validate(value)

    def __repr__(self) -> str:
        converters = ", ".join(v.__repr__() for v in self.root.values())
        return f"{type(self).__name__}({converters})"


class Converter(PMBaseModel, ABC):
    name: str

    @abstractmethod
    def convert(self, material: Material, op_cond: OperationalConditions):
        """Function to convert material to secondary format"""
