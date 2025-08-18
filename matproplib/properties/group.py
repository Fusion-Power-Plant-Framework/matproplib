# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Dependent properties of matproplib"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Literal, Union

from pint import Unit
from pydantic import ConfigDict, Field, SerializeAsAny, create_model, field_validator
from pydantic_core import PydanticUndefined

from matproplib.base import (
    ArrayFloat,
    BaseGroup,
    References,
    SuperconductingParameterisation,
    SuperconductingParameterisationT_co,
    UndefinedSuperconductingParameterisation,
    all_subclasses,
)
from matproplib.properties.dependent import (
    BulkModulus,
    CoefficientThermalExpansion,
    CoerciveField,
    Density,
    DependentPhysicalProperty,
    DependentPhysicalPropertyTD,
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

if TYPE_CHECKING:
    from matproplib.material import PropertiesT_co


class Properties(BaseGroup):
    """Base property model"""

    model_config = ConfigDict(validate_default=True)

    def __repr__(self) -> str:  # noqa: D105
        undefined = self.list(include_undefined=None)
        undefined = f", undefined_properties={undefined}" if undefined else ""
        return f"{type(self).__name__}(defined_properties={self.list()}{undefined})"

    def __getitem__(self, value):  # noqa: D105
        # Required until https://github.com/pydantic/pydantic/issues/10851
        return getattr(self, value)

    __str__ = __repr__


def _superconduction_validation(cls, value):
    if isinstance(value, dict):
        field = cls.model_fields["superconducting_parameterisation"]
        if field.default is not PydanticUndefined:
            return type(field.default).model_validate(value)
        if field.default_factory is not PydanticUndefined:
            return type(field.default_factory()).model_validate(value)
    return value


class DefaultProperties(Properties, Generic[SuperconductingParameterisationT_co]):
    """Default properties model"""

    density: UndefinedProperty | Density = UndefinedProperty()
    poissons_ratio: UndefinedProperty | PoissonsRatio = UndefinedProperty()
    residual_resistance_ratio: UndefinedProperty | ResidualResistanceRatio = (
        UndefinedProperty()
    )
    thermal_conductivity: UndefinedProperty | ThermalConductivity = UndefinedProperty()
    youngs_modulus: UndefinedProperty | YoungsModulus = UndefinedProperty()
    shear_modulus: UndefinedProperty | ShearModulus = UndefinedProperty()
    bulk_modulus: UndefinedProperty | BulkModulus = UndefinedProperty()
    coefficient_thermal_expansion: UndefinedProperty | CoefficientThermalExpansion = (
        UndefinedProperty()
    )
    specific_heat_capacity: UndefinedProperty | SpecificHeatCapacity = (
        UndefinedProperty()
    )
    electrical_resistivity: UndefinedProperty | ElectricalResistivity = (
        UndefinedProperty()
    )
    magnetic_saturation: UndefinedProperty | MagneticSaturation = UndefinedProperty()
    magnetic_susceptibility: UndefinedProperty | MagneticSusceptibility = (
        UndefinedProperty()
    )
    viscous_remanent_magnetisation: UndefinedProperty | ViscousRemanentMagnetism = (
        UndefinedProperty()
    )
    coercive_field: UndefinedProperty | CoerciveField = UndefinedProperty()
    minimum_yield_stress: UndefinedProperty | YieldStress = UndefinedProperty()
    average_yield_stress: UndefinedProperty | YieldStress = UndefinedProperty()
    minimum_ultimate_tensile_stress: UndefinedProperty | TensileStress = (
        UndefinedProperty()
    )
    average_ultimate_tensile_stress: UndefinedProperty | TensileStress = (
        UndefinedProperty()
    )
    superconducting_parameterisation: SerializeAsAny[
        SuperconductingParameterisationT_co
    ] = UndefinedSuperconductingParameterisation()

    field_validator("superconducting_parameterisation", mode="before")(
        _superconduction_validation
    )


Ldefine = UndefinedProperty | DependentPhysicalPropertyTD | ArrayFloat


def props(  # noqa: PLR0913
    *,
    density: Density | Ldefine = False,
    poissons_ratio: PoissonsRatio | Ldefine = False,
    residual_resistance_ratio: ResidualResistanceRatio | Ldefine = False,
    thermal_conductivity: ThermalConductivity | Ldefine = False,
    youngs_modulus: YoungsModulus | Ldefine = False,
    shear_modulus: ShearModulus | Ldefine = False,
    bulk_modulus: BulkModulus | Ldefine = False,
    coefficient_thermal_expansion: CoefficientThermalExpansion | Ldefine = False,
    specific_heat_capacity: SpecificHeatCapacity | Ldefine = False,
    electrical_resistivity: ElectricalResistivity | Ldefine = False,
    magnetic_saturation: MagneticSaturation | Ldefine = False,
    magnetic_susceptibility: MagneticSusceptibility | Ldefine = False,
    viscous_remanent_magnetisation: ViscousRemanentMagnetism | Ldefine = False,
    coercive_field: CoerciveField | Ldefine = False,
    minimum_yield_stress: YieldStress | Ldefine = False,
    average_yield_stress: YieldStress | Ldefine = False,
    minimum_ultimate_tensile_stress: TensileStress | Ldefine = False,
    average_ultimate_tensile_stress: TensileStress | Ldefine = False,
    superconducting_parameterisation: SuperconductingParameterisationT_co
    | Literal[True]
    | None = None,
    property_group: type[PropertiesT_co] = DefaultProperties,
    reference: References | None = None,
    as_field: bool = False,
    **extra_values: dict[str, DependentPhysicalProperty | DependentPhysicalPropertyTD],
) -> PropertiesT_co:
    """Property group generator

    Returns
    -------
    :
        The initialised property model

    Notes
    -----
    By default this function will create an empty property model.
    Each property can be initialised with an empty model by specifying True
    or an empty model or by any of the possible initialisation objects of
    a given property.
    """
    data = {
        "density": density,
        "poissons_ratio": poissons_ratio,
        "residual_resistance_ratio": residual_resistance_ratio,
        "thermal_conductivity": thermal_conductivity,
        "youngs_modulus": youngs_modulus,
        "shear_modulus": shear_modulus,
        "bulk_modulus": bulk_modulus,
        "coefficient_thermal_expansion": coefficient_thermal_expansion,
        "specific_heat_capacity": specific_heat_capacity,
        "electrical_resistivity": electrical_resistivity,
        "magnetic_saturation": magnetic_saturation,
        "magnetic_susceptibility": magnetic_susceptibility,
        "viscous_remanent_magnetisation": viscous_remanent_magnetisation,
        "coercive_field": coercive_field,
        "minimum_yield_stress": minimum_yield_stress,
        "average_yield_stress": average_yield_stress,
        "minimum_ultimate_tensile_stress": minimum_ultimate_tensile_stress,
        "average_ultimate_tensile_stress": average_ultimate_tensile_stress,
        **extra_values,
    }

    if superconducting_parameterisation is None:
        validators = {}
        sc = {}
    else:
        scp_n = "superconducting_parameterisation"
        scp = superconducting_parameterisation
        field = Field(
            default=UndefinedSuperconductingParameterisation() if scp is True else scp,
            validate_default=True,
        )
        sc = {scp_n: (SerializeAsAny[SuperconductingParameterisationT_co], field)}
        validators = {
            "_superconduction_validation": field_validator(scp_n, mode="before")(
                _superconduction_validation
            )
        }
    model = create_model(
        "DynamicProperties",
        __base__=(Properties, Generic[SuperconductingParameterisationT_co]),
        __validators__=validators,
        reference=(References | None, reference),
        **{
            name: (
                property_group.model_fields[name].annotation
                if name in property_group.model_fields
                else _get_dpp_type(name, value),
                Field(
                    default=UndefinedProperty() if value is True else value,
                    validate_default=True,
                ),
            )
            for name, value in data.items()
            if value is not False
        },
        **sc,
    )
    if superconducting_parameterisation is not None:
        model = model[
            Union[  # noqa: UP007
                tuple(
                    sc
                    for sc in all_subclasses(SuperconductingParameterisation)
                    if not sc.__name__.startswith("_Dyn")
                )
            ]
        ]

    if as_field:
        return Field(validate_default=True, default_factory=model)
    return model()


def _get_dpp_type(
    name: str, value: DependentPhysicalProperty | DependentPhysicalPropertyTD
):
    if isinstance(value, DependentPhysicalProperty):
        return type(value)
    if isinstance(value, dict) and "unit" in value:  # is a dict
        if "value" not in value:
            raise ValueError("No default value specified in extra property")
        return type(
            name,
            (DependentPhysicalProperty,),
            {"unit": value.pop("unit"), "__annotations__": {"unit": str | Unit}},
        )
    raise ValueError(f"No unit provided for extra property '{name}'")
