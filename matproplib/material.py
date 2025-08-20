# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""The main material objects"""

from __future__ import annotations

import copy
import logging
import operator
from abc import ABC
from collections.abc import Callable, Iterable, Sequence
from functools import partial, reduce
from typing import Any, Generic, Literal, Protocol, TypedDict, Union, get_args

import numpy as np
from pint import Unit
from pydantic import (
    AliasChoices,
    AliasPath,
    ConfigDict,
    Field,
    SerializeAsAny,
    create_model,
    field_validator,
    model_validator,
)
from pydantic.fields import FieldInfo
from pydantic.types import NonNegativeFloat  # noqa: TC002
from pydantic_core import ValidationError
from typing_extensions import TypeVar

from matproplib.base import (
    BaseGroup,
    PMBaseModel,
    References,
    SuperconductingParameterisationT_co,
    _Wrapped,
)
from matproplib.conditions import (
    DependentPropertyConditionConfig,
    DependentPropertyConditionConfigTD,
    OperationalConditions,
    STPConditions,
)
from matproplib.converters.base import Converter, ConverterK, Converters
from matproplib.nucleides import (
    ElementFraction,
    Elements,
    ElementsTD,
    atomic_fraction_to_mass_fraction,
    atomic_fraction_to_volume_fraction,
    volume_fraction_to_atomic_fraction,
)
from matproplib.properties.dependent import (
    AttributeErrorProperty,
    BulkModulus,
    CoefficientThermalExpansion,
    CoerciveField,
    Density,
    DependentPhysicalProperty,
    ElectricalResistivity,
    MagneticSaturation,
    MagneticSusceptibility,
    PoissonsRatio,
    ResidualResistanceRatio,
    ShearModulus,
    SpecificHeatCapacity,
    TensileStress,
    ThermalConductivity,
    UndefinedProperty,
    ViscousRemanentMagnetism,
    YieldStress,
    YoungsModulus,
)
from matproplib.properties.group import (
    Ldefine,
    Properties,
    UndefinedSuperconductingParameterisation,
    _superconduction_validation,
    props,
)
from matproplib.properties.mixture import Mixture

BaseGroupT_co = TypeVar("BaseGroupT_co", bound=BaseGroup, covariant=True)
PropertiesT_co = TypeVar("PropertiesT_co", bound=Properties, covariant=True)

log = logging.getLogger(__name__)


class MaterialFraction(PMBaseModel, Generic[ConverterK]):
    """Material fraction object"""

    material: Material[ConverterK]
    fraction: NonNegativeFloat

    @model_validator(mode="before")
    def _input_variation(self):
        if isinstance(self, tuple):
            return {"material": self[0], "fraction": self[1]}
        return self


class Material(PMBaseModel, ABC, Generic[ConverterK]):
    """The Material Class, container for all attributes of a material"""

    model_config = ConfigDict(
        arbitrary_types_allowed=True, validate_assignment=True, validate_default=True
    )
    name: str
    elements: Elements = Field(
        default=[], validation_alias=AliasChoices("elements", "chemical_equation")
    )
    converters: Converters[ConverterK] = Field(default_factory=Converters)
    reference: References | None = None
    mixture_fraction: list[MaterialFraction[ConverterK]] | None = Field(
        default=None, frozen=True
    )

    def __init__(self, **kwargs):
        if type(self) is Material:
            raise NotImplementedError(
                "Cannot initialise Material directly please use the 'material' function"
            )
        super().__init__(**kwargs)

    @model_validator(mode="after")
    def _mixture_validation(self):
        if self.mixture_fraction is None:
            return self

        def_props = set(self.mixture_fraction[0].material.list_properties())
        for mf in self.mixture_fraction[1:]:
            if diff := def_props.symmetric_difference(mf.material.list_properties()):
                for dp in diff:
                    if (
                        hasattr(self, dp)
                        and isinstance(
                            getattr(self, dp),
                            UndefinedProperty | UndefinedSuperconductingParameterisation,
                        )
                    ) or not hasattr(self, dp):
                        material = (
                            self.mixture_fraction[0].material
                            if dp not in def_props
                            else mf.material
                        )
                        msg = f"{dp} is undefined on {material}"
                        log.debug(msg)
                        object.__setattr__(self, dp, AttributeErrorProperty(msg=msg))  # noqa: PLC2801

        return self

    def convert(self, name: ConverterK, op_cond: OperationalConditions, *args, **kwargs):
        """Convert material to another format"""  # noqa: DOC201
        return self.converters[name].convert(self, op_cond, *args, **kwargs)

    def __getattr__(self, value: str) -> Any:
        """Override attribute access for shorthand to nested attributes"""  # noqa: DOC201
        try:
            if value != "superconducting_parameterisation" and hasattr(
                self.superconducting_parameterisation, value
            ):
                return getattr(self.superconducting_parameterisation, value)
        except AttributeError:
            pass
        return super().__getattr__(value)

    def __str__(self) -> str:  # noqa: D105
        undefined = (
            f", undefined_properties={ulp}"
            if (ulp := self.list_properties(include_undefined=None))
            else ""
        )
        p = f", properties={lp}{undefined})" if (lp := self.list_properties()) else ""
        c = f", {self.converters.__repr__()}" if len(self.converters.root) > 0 else ""
        return f"{type(self).__name__}(elements={self.elements.__repr__()}{p}{c})"

    def __repr__(self) -> str:
        """Avoid nested reproduction for partial values"""  # noqa: DOC201
        p = ""
        for k in self.list_properties(include_undefined=True):
            v = getattr(self, k)
            if isinstance(v.value, partial):
                start, end_ = repr(v).split("value", 1)
                end = end_.rsplit("unit", 1)[-1]
                out = repr(v.value)

                if out != "...":
                    out = f"{out.split('>')[0]}>)"
                p += f", {k}={type(v).__name__}({start}value={out}, unit{end})"
            else:
                p += f", {k}={type(v).__name__}({v})"
        return (
            f"{type(self).__name__}(reference={self.reference},"
            f" elements={self.elements.__repr__()}, {self.converters.__repr__()}{p})"
        )

    def list_properties(self, *, include_undefined: bool | None = False) -> list[str]:
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
        return [
            k
            for k, v in self
            if statement(v) and isinstance(v, DependentPhysicalProperty)
        ]


def field_alias_path(name, *alias_path, default=None):
    """Helper to create alias field for properties"""  # noqa: DOC201
    return Field(
        default=default or UndefinedProperty(),
        validation_alias=AliasChoices(name, AliasPath(*alias_path, name)),
    )


class FullMaterial(
    Material[ConverterK], Generic[ConverterK, SuperconductingParameterisationT_co]
):
    """Fully specified material with all default properties"""

    density: UndefinedProperty | Density = field_alias_path("density", "properties")

    poissons_ratio: UndefinedProperty | PoissonsRatio = field_alias_path(
        "poissons_ratio", "properties"
    )
    residual_resistance_ratio: UndefinedProperty | ResidualResistanceRatio = (
        field_alias_path("residual_resistance_ratio", "properties")
    )
    thermal_conductivity: UndefinedProperty | ThermalConductivity = field_alias_path(
        "thermal_conductivity", "properties"
    )
    youngs_modulus: UndefinedProperty | YoungsModulus = field_alias_path(
        "youngs_modulus", "properties"
    )
    shear_modulus: UndefinedProperty | ShearModulus = field_alias_path(
        "shear_modulus", "properties"
    )
    bulk_modulus: UndefinedProperty | BulkModulus = field_alias_path(
        "bulk_modulus", "properties"
    )
    coefficient_thermal_expansion: UndefinedProperty | CoefficientThermalExpansion = (
        field_alias_path("coefficient_thermal_expansion", "properties")
    )
    specific_heat_capacity: UndefinedProperty | SpecificHeatCapacity = field_alias_path(
        "specific_heat_capacity", "properties"
    )
    electrical_resistivity: UndefinedProperty | ElectricalResistivity = field_alias_path(
        "electrical_resistivity", "properties"
    )
    magnetic_saturation: UndefinedProperty | MagneticSaturation = field_alias_path(
        "magnetic_saturation", "properties"
    )
    magnetic_susceptibility: UndefinedProperty | MagneticSusceptibility = (
        field_alias_path("magnetic_susceptibility", "properties")
    )
    viscous_remanent_magnetisation: UndefinedProperty | ViscousRemanentMagnetism = (
        field_alias_path("viscous_remanent_magnetisation", "properties")
    )
    coercive_field: UndefinedProperty | CoerciveField = field_alias_path(
        "coercive_field", "properties"
    )
    minimum_yield_stress: UndefinedProperty | YieldStress = field_alias_path(
        "minimum_yield_stress", "properties"
    )
    average_yield_stress: UndefinedProperty | YieldStress = field_alias_path(
        "average_yield_stress", "properties"
    )
    minimum_ultimate_tensile_stress: UndefinedProperty | TensileStress = (
        field_alias_path("minimum_ultimate_tensile_stress", "properties")
    )
    average_ultimate_tensile_stress: UndefinedProperty | TensileStress = (
        field_alias_path("average_ultimate_tensile_stress", "properties")
    )
    superconducting_parameterisation: SerializeAsAny[
        SuperconductingParameterisationT_co
    ] = field_alias_path(
        "superconducting_parameterisation",
        "properties",
        default=UndefinedSuperconductingParameterisation(),
    )

    field_validator("superconducting_parameterisation", mode="before")(
        _superconduction_validation
    )

    @model_validator(mode="before")
    def _properties_validation(self):
        if "properties" in self and isinstance(self["properties"], dict):
            self["properties"] = props(**self["properties"])
        return self


def material(  # noqa: C901
    name: str,
    elements: Elements
    | str
    | list[str | ElementFraction]
    | list[str]
    | dict[str, float]
    | None = None,
    properties: Properties
    | dict[str, Ldefine | DependentPhysicalProperty]
    | None = None,
    converters: Converter | Iterable[Converter] | Converters[ConverterK] | None = None,
    reference: References | None = None,
    **custom_properties: DependentPhysicalProperty,
) -> type[Material[ConverterK]]:
    """Functional material definition

    Returns
    -------
    :
        New material class
    """
    from matproplib.properties.dependent import (  # noqa: PLC0415
        DependentPhysicalProperty,
    )

    def combine_refs(ref1: References | None, ref2: FieldInfo) -> References | None:
        if ref2.default is not None:
            if ref1 is not None:
                return References.model_validate(ref1).combine(ref2.default)
            return ref2.default
        return None

    if properties is None:
        properties: Properties = Properties()

    if type(properties) is Properties:
        props_ = {}
    elif isinstance(properties, dict):
        props_ = props(as_field=properties.pop("as_field", True), **properties)
    elif isinstance(properties, FieldInfo):
        props_ = properties
    elif isinstance(properties, Properties):
        props_ = copy.deepcopy(type(properties).model_fields)
        vals = properties.list()
        for k in vals:
            props_[k].default = getattr(properties, k)
        if properties.reference is not None:
            props_["reference"].default = properties.reference
        reference = combine_refs(reference, props_.pop("reference"))
    else:
        raise NotImplementedError

    if isinstance(props_, FieldInfo):
        props_ = copy.deepcopy(props_.default_factory.model_fields)
        reference = combine_refs(reference, props_.pop("reference"))

    if "superconducting_parameterisation" in props_:
        p = props_["superconducting_parameterisation"].annotation
        props_["superconducting_parameterisation"].annotation = SerializeAsAny[p]

    return create_model(
        name,
        __base__=Material[ConverterK],
        name=(str, name),
        elements=(
            Elements,
            [] if elements is None else elements,
        ),
        converters=(Converters, converters or {}),
        reference=(References | None, reference),
        **{
            c: (
                DependentPhysicalProperty,
                Field(default_factory=lambda v=v: v),
            )
            for c, v in custom_properties.items()
        },
        **{
            k: (
                v.annotation,
                Field(default_factory=lambda v=v.default: v),
            )
            for k, v in props_.items()
        },
    )


class _PropertyInfo(TypedDict):
    dpp: list[DependentPhysicalProperty]
    fractions: list[float]


def _get_properties_from_materials(
    property_: str,
    materials: Sequence[MaterialFraction[ConverterK]],
) -> _PropertyInfo:
    dpp, fractions = [], []
    for mf in materials:
        fractions.append(mf.fraction)
        # fail later if property isnt defined so property overrides can be used
        dpp.append(getattr(mf.material, property_, UndefinedProperty()))
    return {"dpp": dpp, "fractions": fractions}


def _ignore_undefined(ann):
    types = tuple(
        a
        for a in get_args(ann) or (ann,)
        if a not in {UndefinedProperty, UndefinedSuperconductingParameterisation}
    )

    if len(types) > 1:
        return Union[types]  # noqa: UP007
    return types[0]


def _get_indexes(dpp: list[DependentPhysicalProperty], value=None):
    return [i for i in range(len(dpp)) if dpp[i] == value]


def _atomic_to_inp_converter(
    m_el: list[Elements],
    input_frac: Sequence[float],
    conversion: Callable[[ElementsTD], ElementsTD],
) -> ElementsTD:
    elements = {}
    for el, f in zip(m_el, input_frac, strict=False):
        for k, elf in conversion(copy.deepcopy(el.root)).items():
            if k in elements:
                elements[k].fraction += elf.fraction * f
            else:
                elf.fraction *= f
                elements[k] = elf
    ttl = sum(e.fraction for e in elements.values())
    for el in elements.values():
        el.fraction /= ttl
    return elements


def _atomic_to_volume_converter(
    m_el: list[Elements], input_frac: Sequence[float], densities: list[float]
) -> tuple[ElementsTD, dict[str, float]]:
    elements = {}
    vf_den = {}
    for el, f, d in zip(m_el, input_frac, densities, strict=False):
        for k, elf in atomic_fraction_to_volume_fraction(
            copy.deepcopy(el.root), dict.fromkeys(el.root, d)
        ).items():
            if k in elements:
                vf_den[k] += d * elf.fraction
                elements[k].fraction += elf.fraction * f
            else:
                vf_den[k] = d * elf.fraction
                elf.fraction *= f
                elements[k] = elf

    ttl = sum(e.fraction for e in elements.values())
    for el in elements.values():
        el.fraction /= ttl

    return elements, vf_den


def _void_check(
    materials: Sequence[MaterialFraction[ConverterK]], fraction_type: str
) -> Sequence[float]:
    inp_frac = np.asarray([mf.fraction for mf in materials])

    if not np.isclose(np.sum(inp_frac), 1):
        if fraction_type in {"mass", "atomic"}:
            log.warning(
                "Normalising input fraction, "
                f"Voids are not possible for {fraction_type=}"
            )
            sum_frac = np.sum(inp_frac)

            inp_frac /= sum_frac
            for mf in materials:
                mf.fraction /= sum_frac
        else:
            log.info(
                "Material fractions do not sum to 1. "
                f"Void fraction of {1 - np.sum(inp_frac):.2f}"
            )

    return inp_frac


def mixture(
    name: str,
    materials: Sequence[
        MaterialFraction[ConverterK] | tuple[Material[ConverterK], float]
    ],
    fraction_type: Literal["atomic", "mass", "volume"] = "atomic",
    converters: Converters[ConverterK] | None = None,
    reference: References | None = None,
    *,
    volume_conditions: OperationalConditions | None = None,
    **property_overrides: DependentPhysicalProperty,
) -> Material[ConverterK]:
    """
    Create a mixture from a set of materials

    Parameters
    ----------
    name:
        Mixture name
    materials:
        list of materials with their fractions
    fraction_type:
        the type of fractional mixing to perform
    converters:
        Conversion to other formats, these are not transferred from constituent materials
    reference:
        Any reference for the material data
    volume_conditions:
        if the fraction type is 'volume' what conditions to mix under.
        These are used to calculate the density of the materials. Defaults to IUPAC STP
    **properties_overrides:
        any replacement properties for the mixture eg density

    Returns
    -------
    :
        Mixed material

    Raises
    ------
    AttributeError
        If one material has a property the others dont and there is no override provided
    """
    materials: list[MaterialFraction[ConverterK]] = [
        MaterialFraction.model_validate(m) for m in materials
    ]
    all_fields = reduce(
        operator.or_,
        [type(m.material).model_fields for m in materials],
        {},
    )
    prop_ann, prop_val = {}, {}
    for prp in all_fields.keys() - Material.model_fields.keys():
        mix_properties = _get_properties_from_materials(prp, materials)
        mix_type = _ignore_undefined(all_fields[prp].annotation)
        prop_ann[prp] = all_fields[prp].annotation | Mixture[mix_type]
        if prp in property_overrides:
            prop_val[prp] = property_overrides[prp]
            continue
        for dpp in mix_properties["dpp"]:
            if isinstance(
                dpp, UndefinedProperty | UndefinedSuperconductingParameterisation
            ):
                prop_val[prp] = dpp
                break
        else:
            try:
                prop_val[prp] = Mixture[mix_type](
                    **mix_properties, unit=mix_properties["dpp"][0].unit
                )
            except ValidationError:
                ind = _get_indexes(mix_properties["dpp"])
                miss_materials = [materials[i] for i in ind]
                mats = "".join(
                    f"{i}: {mat.material.name}"
                    for i, mat in zip(ind, miss_materials, strict=True)
                )
                msg = (
                    f"Material property '{prp}' not defined and not overidden at {mats} "
                )
                prop_val[prp] = AttributeErrorProperty(msg=msg)
                log.debug(msg)

    model = create_model(
        name,
        __base__=(Material[ConverterK], Generic[ConverterK]),
        name=(str, name),
        **prop_ann,
    )

    mat_elements = [mf.material.elements for mf in materials]

    inp_frac = _void_check(materials, fraction_type)

    if fraction_type == "atomic":
        elements = _atomic_to_inp_converter(mat_elements, inp_frac, lambda inp: inp)
    elif fraction_type == "mass":
        elements = {}
        elements = _atomic_to_inp_converter(
            mat_elements, inp_frac, atomic_fraction_to_mass_fraction
        )
        elements["fraction_type"] = "mass"
    elif fraction_type == "volume":
        volume_conditions = volume_conditions or STPConditions()
        densities = [mf.material.density(volume_conditions) for mf in materials]
        elements, vf_den = _atomic_to_volume_converter(mat_elements, inp_frac, densities)
        elements = volume_fraction_to_atomic_fraction(elements, vf_den)
    else:
        raise NotImplementedError(f"{fraction_type=} not a valid option")

    return model[ConverterK](
        **prop_val,
        elements=elements,
        reference=reference,
        converters=converters or Converters(),
        mixture_fraction=materials,
    )


Owner = TypeVar("Owner")
DPPT = TypeVar("DPPT", bound=DependentPhysicalProperty)
_T = TypeVar("_T", bound=DependentPhysicalProperty)


class DPPWrap(Protocol, Generic[Owner]):
    """Dependent Property wrapper protocol"""

    def __get__(  # noqa: D105, PLE0302
        _self,  # noqa: N805
        inst: object,
        owner: type[Owner],
        name: str,
    ) -> DependentPhysicalProperty: ...


def dependentphysicalproperty(
    dpp: type[DPPT] = DependentPhysicalProperty,
    *,
    unit: Unit | str | None = None,
    op_cond_config: DependentPropertyConditionConfig
    | DependentPropertyConditionConfigTD
    | None = None,
    reference: References | None = None,
) -> type[DPPWrap[DPPT]]:
    """Decorator to create DependentPhysicalProperty for a method

    Returns
    -------
    :
        Wrapped method of a class

    Raises
    ------
    ValueError
        if unit is not specified and dpp is not the base DependentPhysicalPropery
    """
    dunit = (
        dpp.model_fields["unit"].default
        if (
            issubclass(dpp, DependentPhysicalProperty)
            and dpp is not DependentPhysicalProperty
        )
        else None
    )

    if unit is None and dunit is None:
        raise ValueError("Unit must be specified for function output")

    class Wrap(_Wrapped, Generic[_T]):
        """Wrap a function to make a DependentPhysicalProperty

        Returns
        -------
        :
            Wrapped function

        Notes
        -----
        Pydantic special cases functools entries
        """

        def __init__(
            self,
            func: Callable[[Material, OperationalConditions], float]
            | Callable[[OperationalConditions], float],
        ):
            self.__create_model(func)

        def __create_model(self, func):
            self.__model = create_model(
                func.__name__,
                __base__=dpp,
                value=(
                    Callable[[Material, OperationalConditions], float],
                    Field(default=func, validate_default=True),
                ),
                unit=(
                    Unit | str,
                    Field(
                        default=dunit if dunit is not None else unit,
                        validate_default=True,
                    ),
                ),
                op_cond_config=(
                    DependentPropertyConditionConfig | None,
                    Field(default=op_cond_config, validate_default=True),
                ),
                reference=(
                    References | None,
                    Field(default=reference, validate_default=True),
                ),
            )(unit=unit if unit is not None else dunit)

        def __get__(self, owner: type[Owner], name: str) -> DependentPhysicalProperty:
            return self.__model

        def __set_name__(self, _, name: str):
            """Set the attribute name from a dataclass"""
            self._name = "_" + name

    # Bypass some pydantic checks,
    Wrap.__module__ = "functools"

    return Wrap
