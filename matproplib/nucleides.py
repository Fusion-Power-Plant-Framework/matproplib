# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Nucleides representation"""

from __future__ import annotations

import copy
import logging
import re
from typing import TYPE_CHECKING, Literal, Union

import numpy as np
import periodictable as pt
from pydantic import ConfigDict, RootModel, model_serializer, model_validator
from pydantic.types import NonNegativeFloat  # noqa: TC002
from typing_extensions import TypedDict

from matproplib.base import PMBaseModel, References

if TYPE_CHECKING:
    from collections.abc import Callable

log = logging.getLogger(__name__)


class ElementFraction(PMBaseModel):
    """Elemental fraction model"""

    element: Element
    fraction: NonNegativeFloat


_ef_root_model = dict[str, ElementFraction | float | int | References | str | None]


class ElementsTD(TypedDict, total=False, extra_items=ElementFraction):
    """Strict typing of Elements.root, not yet supported by pydantic as type"""

    _no_atoms: int
    reference: References | None
    fraction_type: Literal["atomic", "mass"]


class Elements(RootModel):
    """Element grouping model"""

    root: _ef_root_model
    _no_atoms: int | None = None
    _reference: References | None = None
    model_config = ConfigDict(validate_default=True)

    @model_validator(mode="before")
    def _element_pre_validation(self):
        if isinstance(self, str):
            # conversion is always fraction by atom "atomic"
            return convert_chemical_equation_to_elements(self)
        if isinstance(self, ElementFraction):
            return {self.element.element.symbol: self}
        if isinstance(self, list):
            if len(self) == 1 and isinstance(self[0], str):
                return {self[0]: 1}
            ret = {}
            for e in self:
                el = ElementFraction.model_validate(e)
                ret[el.element.element.symbol] = el
            return ret
        return self

    @model_validator(mode="after")
    def _element_post_validation(self):
        self._reference = self.root.pop("reference", None)
        self._no_atoms = self.root.pop("no_atoms", None)
        fraction_type = self.root.pop("fraction_type", "atomic")

        for k, v in self.root.items():
            if not isinstance(v, ElementFraction):
                self.root[k] = ElementFraction(element=k, fraction=v)

        self.root = _from_fraction_type_conversion(fraction_type, self.root)

        e_sum = 0
        for e in self.root.values():
            e_sum += e.fraction

        if not np.isclose(e_sum, 1, atol=1e-5, rtol=1e-5) and len(self) > 0:
            log.info(f"Fraction does not sum to 1, total: {e_sum:.5f}")

        if e_sum > 1 and not np.isclose(e_sum, 1, atol=1e-5, rtol=1e-5):
            raise ValueError(f"The fraction of elements is greater than 1: {e_sum:.5f}")
        return self

    @model_serializer
    def _elements_serialise(self) -> dict[str, float]:
        ref = {} if self._reference is None else {"reference": self._reference}
        return {k: e.fraction for k, e in self.root.items()} | ref

    def __iter__(self):  # noqa: D105
        return iter(self.root.items())

    def __getitem__(self, item):  # noqa: D105
        return self.root[item]

    def __len__(self) -> int:  # noqa: D105
        return len(self.root)

    def __repr__(self):  # noqa: D105
        return f"{type(self).__name__}({self._elements_serialise()})"

    def __getattr__(self, name: str):
        """Gets reference if requested"""  # noqa: DOC201
        if name == "reference":
            return self._reference
        return super().__getattr__(name)

    @property
    def nucleides(self) -> Elements:
        """Get the nucleides for a given element group

        Returns
        -------
        :
            Expanded model only consisting of nucleides

        Notes
        -----
        Natural abundance is used for elements
        """
        return Elements(**{
            f"{iso.element.element.symbol}{iso.element.isotope}": {
                "element": iso,
                "fraction": _modify_fraction(ef, iso),
            }
            for ef in self.root.values()
            for iso in ef.element.nucleides
        })


def _modify_fraction(ef: ElementFraction, iso: Element):
    if isinstance(ef.element.element, pt.core.Element):
        return ef.fraction * iso.element.abundance / 100
    return ef.fraction


# DOI: 10.1787/5f05e3db-en.
# 12.1.4 Particle property type: metaStable
_GNDS_metaStable = re.compile(r"([A-Zn][a-z]*)(\d+)*((?:_[em]\d+)?)")


class Element(PMBaseModel):
    """Element Model

    Notes
    -----
    Verifies against the Generalised Nuclear Database Structure for metastable nucleides
    if provided (eg Am242_m1)

    .. doi:: 10.1787/5f05e3db-en

    """

    element: pt.core.Element | pt.core.Isotope
    metastable: int = 0

    @model_validator(mode="before")
    def _split_into_parts(self):
        if isinstance(self, str):
            self = {"element": self}  # noqa: PLW0642

        if isinstance(self, dict) and not isinstance(
            self.get("element"), pt.core.Isotope | pt.core.Element
        ):
            symbol, a_n, state = _GNDS_metaStable.fullmatch(self["element"]).groups()

            symbol = getattr(pt, symbol)

            self["element"] = symbol if a_n is None else symbol[int(a_n)]
            self["metastable"] = int(state[2:]) if state else self.get("metastable", 0)
        return self

    @property
    def mass_number(self) -> int:
        """Atomic mass number

        Notes
        -----
        Returns highest abundance mass number for elements
        """
        if isinstance(self.element, pt.core.Isotope):
            return self.element.isotope
        return most_abundant_isoptope(self.element).isotope

    @property
    def atomic_number(self) -> int:
        """Atomic number"""
        return self.element.number

    @property
    def zaid(self) -> str:
        """ZAID structure for the element"""
        return f"{self.atomic_number:03}{self.mass_number:03}"

    @property
    def nucleides(self):
        """Nucleides of the element

        Yields
        ------
        :
            The nucleide if its an isotope or the natural abundance nucleides
        """
        if isinstance(self.element, pt.core.Isotope):
            yield self
        else:
            for iso in list(self.element):
                if iso.abundance > 0:
                    yield Element(element=iso, metastable=self.metastable)


def most_abundant_isoptope(el: pt.core.Element) -> pt.core.Isotope:
    """
    Returns
    -------
    :
        The most naturally abundant nucleide
    """
    return max(list(el), key=lambda x: x.abundance)


def _from_fraction_type_conversion(
    fraction_type: Literal["atomic", "mass"], ef_dict: ElementsTD
) -> ElementsTD:
    if fraction_type == "atomic":
        return ef_dict

    if fraction_type == "mass":
        return mass_fraction_to_atomic_fraction(ef_dict)

    raise NotImplementedError(f"Conversion from {fraction_type} not implemented")


def _converter(
    ef_dict: ElementsTD, conversion: Callable[[ElementFraction], float]
) -> ElementsTD:
    ttl = 0
    new = {}
    for n_ef, ef in ef_dict.items():
        new[n_ef] = conversion(ef)
        ttl += new[n_ef]

    # dont modify original elements
    new_ef_dict = copy.deepcopy(ef_dict)
    for n_ef, frac in new.items():
        new_ef_dict[n_ef].fraction = frac / ttl

    return new_ef_dict


def mass_fraction_to_atomic_fraction(ef_dict: ElementsTD) -> ElementsTD:
    """
    Returns
    -------
    :
        Atomic fraction of model
    """
    return _converter(ef_dict, lambda ef: ef.fraction / ef.element.element.mass)


def atomic_fraction_to_mass_fraction(ef_dict: ElementsTD) -> ElementsTD:
    """
    Returns
    -------
    :
        Mass fraction of model
    """
    return _converter(ef_dict, lambda ef: ef.fraction * ef.element.element.mass)


def _get_dn(densities: dict[str, float], el: Element):
    if isinstance(el.element, pt.core.Element):
        return densities[el.element.symbol]

    elm = el.element
    return densities[f"{elm.symbol}{elm.isotope}"]


def mass_fraction_to_volume_fraction(
    ef_dict: ElementsTD, densities: dict[str, float]
) -> ElementsTD:
    """
    Returns
    -------
    :
        Volume fraction of model
    """
    return _converter(ef_dict, lambda ef: ef.fraction * _get_dn(densities, ef.element))


def volume_fraction_to_mass_fraction(
    ef_dict: ElementsTD, densities: dict[str, float]
) -> ElementsTD:
    """
    Returns
    -------
    :
        Mass fraction of model
    """
    return _converter(ef_dict, lambda ef: ef.fraction / _get_dn(densities, ef.element))


def atomic_fraction_to_volume_fraction(
    ef_dict: ElementsTD, densities: dict[str, float]
) -> ElementsTD:
    """
    Returns
    -------
    :
        Volume fraction of model
    """
    return _converter(
        ef_dict,
        lambda ef: ef.fraction
        * ef.element.element.mass
        / _get_dn(densities, ef.element),
    )


def volume_fraction_to_atomic_fraction(
    ef_dict: ElementsTD, densities: dict[str, float]
) -> ElementsTD:
    """
    Returns
    -------
    :
        Atomic fraction of model
    """
    return _converter(
        ef_dict,
        lambda ef: ef.fraction
        * _get_dn(densities, ef.element)
        / ef.element.element.mass,
    )


ParsedElement = tuple[Literal["element"], str, int]
ParsedCount = tuple[Literal["count"], int]
ParsedGroup = tuple[
    Literal["group"], list[Union["ParsedGroup", ParsedElement, ParsedCount]]
]
ParsedFormula = list[ParsedElement | ParsedGroup | ParsedCount]


def parse_chemical_formula(formula: str) -> ParsedFormula:
    """Parse a chemical formula into its constituent elements

    Returns
    -------
    :
        Parsed formula
    """
    el_str = r"[A-Z][a-z]*"
    element_pattern = re.compile(el_str)

    def digits(tokens: list[str]) -> int:
        return int(tokens.pop(0)) if tokens and tokens[0].isdigit() else 1

    def parse(tokens: list[str]) -> ParsedFormula:
        parsed: ParsedFormula = []
        while tokens:
            token = tokens.pop(0)
            if token == "(":  # noqa: S105
                sub_parsed = parse(tokens)
                multiplier = digits(tokens)
                parsed.append(("group", [*sub_parsed, ("count", multiplier)]))
            elif token == ")":  # noqa: S105
                break
            elif element_pattern.match(token):
                element = token
                count = digits(tokens)
                parsed.append(("element", element, count))
        return parsed

    parsed = parse(re.findall(rf"{el_str}|\d+|\(|\)", formula))
    _unparse_check(formula, parsed)
    return parsed


def _unparse_check(formula: str, parsed: ParsedFormula):
    def _remove_digit_check(formula: str, cell: str) -> bool:
        return (
            formula[formula.index(cell) + len(cell)].isdigit()
            if len(formula) > len(cell)
            else False
        )

    def unparse(parse: ParsedFormula, formula: str) -> str:
        for p in parse:
            p: ParsedElement | ParsedGroup | ParsedCount
            if p[0] == "element":
                if _remove_digit_check(formula, p[1]):
                    formula = formula.replace(f"{p[2]}", "", 1)
                formula = formula.replace(p[1], "", 1)
            elif p[0] == "group":
                formula = formula.replace("(", "", 1)
                formula = unparse(p[1], formula)
            elif p[0] == "count":
                if _remove_digit_check(formula, ")"):
                    formula = formula.replace(f"{p[1]}", "", 1)
                formula = formula.replace(")", "", 1)
        return formula

    formula = formula.replace(" ", "")
    if len(out := unparse(parsed, formula)) != 0:
        raise ValueError(f"Unparsed chemical equation symbols '{out}'")


def convert_chemical_equation_to_elements(formula: str) -> dict[str, ElementFraction]:
    """Convert chemical formula into a form ingestable by Elements

    Returns
    -------
    :
        dictionary of ElementFractions
    """

    def add_fraction(
        el1: dict[str, ElementFraction], el2: dict[str, ElementFraction]
    ) -> dict[str, ElementFraction]:
        for k, v in el1.items():
            if k in el2:
                el2[k].fraction += v.fraction
            else:
                el2[k] = v
        return el2

    def parse(
        tokens: ParsedFormula, elements: dict[str, ElementFraction]
    ) -> dict[str, ElementFraction]:
        new_elements: dict[str, ElementFraction] = {}
        for tok in tokens:
            if tok[0] == "element":
                if tok[1] in new_elements:
                    new_elements[tok[1]].fraction += tok[2]
                else:
                    new_elements[tok[1]] = ElementFraction(
                        element=tok[1], fraction=tok[2]
                    )
            elif tok[0] == "group":
                group_elements = parse(tok[1], {})
                new_elements = add_fraction(group_elements, new_elements)
            elif tok[0] == "count":
                for v in new_elements.values():
                    v.fraction *= tok[1]

        return add_fraction(new_elements, elements)

    elements = parse(parse_chemical_formula(formula), {})
    ttl_fraction = sum(e.fraction for e in elements.values())
    no_atoms = 0
    for v in elements.values():
        no_atoms += v.fraction
        v.fraction /= ttl_fraction
    return {"no_atoms": int(no_atoms), **elements}
