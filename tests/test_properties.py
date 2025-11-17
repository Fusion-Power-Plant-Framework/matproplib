# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
import copy

import numpy as np
import pytest
from pint import Unit
from pydantic_core import ValidationError

from matproplib.base import rebuild, ureg
from matproplib.conditions import (
    DependentPropertyConditionConfig,
    OperationalConditions,
    PropertyConfig,
    STPConditions,
)
from matproplib.material import dependentphysicalproperty, material
from matproplib.properties.dependent import (
    CoefficientThermalExpansion,
    CoerciveField,
    Density,
    DependentPhysicalProperty,
    ElectricalResistivity,
    MagneticSaturation,
    PoissonsRatio,
    SpecificHeatCapacity,
    Stress,
    ThermalConductivity,
    UndefinedProperty,
    ViscousRemanentMagnetism,
    YoungsModulus,
)
from matproplib.properties.group import Properties, props
from matproplib.properties.independent import (
    MagneticField,
    NeutronDamage,
    PhysicalProperty,
    Pressure,
    Strain,
    Temperature,
)
from tests import _np_and_value_test


class TestDensity:
    @pytest.mark.parametrize(
        ("unit", "result"),
        [("atom/cm^3", 1.67e-21), ("atom/b-cm", 1673.823), ("atom/m^3", 1.67e-27)],
    )
    def test_value_from_nuclear_units(self, unit, result, test_condition):
        den = Density.from_nuclear_units(elements={"H": 1}, value=1, unit=unit)
        assert den(test_condition) == pytest.approx(result)


class TestIndependentPhysicalProperty:
    props = pytest.mark.parametrize(
        "prop", [Temperature, Pressure, MagneticField, Strain, NeutronDamage]
    )

    @props
    @pytest.mark.parametrize("inp", [np.ones(5), 1])
    def test_property_values(self, prop, inp):
        _np_and_value_test(prop(value=inp), inp)

    @props
    @pytest.mark.parametrize("unit", ["K", "Pa", "T"])
    def test_bad_property_units(self, prop, unit):
        if prop.model_fields["unit"].default != ureg.Unit(unit):
            with pytest.raises(ValueError, match="1 valid"):
                prop(value=1, unit=unit)

    @pytest.mark.parametrize(
        ("prop", "unit", "result"),
        list(zip((Temperature, Pressure), ("degC", "bar"), (274.15, 1e5), strict=False)),
    )
    def test_good_property_units(self, prop, unit, result):
        assert prop(value=1, unit=unit).value == result

    def test_bad_new_property(self):
        class NewProperty(PhysicalProperty):
            pass

        with pytest.raises(ValueError, match="validation"):
            NewProperty()

    def test_weird_unit_new_property(self):
        class NewProperty(PhysicalProperty):
            unit: Unit | str = "1e6g"

        assert NewProperty(value=1).value == pytest.approx(1e6)

    @pytest.mark.parametrize(("unit", "result"), [("1e19K", 1e19)])
    def test_units_with_prefix(self, unit, result):
        temp = Temperature(value=1, unit=unit)

        assert temp.value == pytest.approx(result)

    def test_value_as(self):
        temp = Temperature(value=1)
        assert temp.value_as("degC") == pytest.approx(-272.15)

        with pytest.raises(ValueError, match="Cannot convert"):
            temp.value_as("T")

    def test_direct_init_raises_NotImplemented(self):
        with pytest.raises(NotImplementedError):
            PhysicalProperty(value=5, unit="")

    def test_arithmetic(self):
        assert Pressure(value=5) - Pressure(value=6) == -1
        assert Pressure(value=5) + Pressure(value=6) == 11
        assert Pressure(value=5) * Pressure(value=6) == 30
        assert Pressure(value=6) / Pressure(value=5) == 1.2

        assert 5 - Pressure(value=6) == -1
        assert 5 + Pressure(value=6) == 11
        assert 5 * Pressure(value=6) == 30
        assert 6 / Pressure(value=5) == 1.2

        assert Pressure(value=5) - 6 == -1
        assert Pressure(value=5) + 6 == 11
        assert Pressure(value=5) * 6 == 30
        assert Pressure(value=6) / 5 == 1.2

        assert Pressure(value=5) == Pressure(value=5)
        assert Pressure(value=5) != Pressure(value=5, unit="GPa")
        assert Pressure(value=5000, unit="MPa") == Pressure(value=5, unit="GPa")

    def test_unit_conversion(self):
        k = Temperature(value=278.15, unit="K")
        dc = Temperature(value=5, unit="degC")

        assert k.value == dc.value
        assert k.unit == dc.unit

    def test_range_validator(self):
        with pytest.raises(ValidationError):
            Temperature(value=-5, unit="K")
        Temperature(value=-5, unit="degC")


class TestDependentPhysicalProperties:
    @pytest.mark.parametrize(
        "prop",
        [
            PoissonsRatio,
            ThermalConductivity,
            YoungsModulus,
            SpecificHeatCapacity,
            CoefficientThermalExpansion,
            ElectricalResistivity,
            MagneticSaturation,
            ViscousRemanentMagnetism,
            CoerciveField,
            Stress,
        ],
    )
    @pytest.mark.parametrize(
        "value",
        [
            5,
            np.array([5, 5]),
            lambda oc: oc.temperature.value,
            lambda oc: np.full(5, oc.temperature.value),
        ],
    )
    @pytest.mark.parametrize(
        "op_cond_config",
        [
            None,
            {"temperature": ("degC", -1, 2)},
            {"temperature": (200, 300)},
            {"temperature": ("degC", -1)},
            {"temperature": "degC"},
            {"temperature": ureg.Unit("degC")},
        ],
    )
    @pytest.mark.parametrize(
        "op_cond_type", [None, PropertyConfig, DependentPropertyConditionConfig]
    )
    def test_init_with_value(self, prop, value, op_cond_config, op_cond_type):
        # avoid mutating state
        op_cond_config = copy.deepcopy(op_cond_config)
        if op_cond_config is not None:
            if op_cond_type is PropertyConfig:
                if isinstance(op_cond_config["temperature"], str | Unit):
                    conf = {"unit": op_cond_config["temperature"]}
                else:
                    conf = dict(
                        zip(
                            ["unit", "lower", "upper"],
                            op_cond_config["temperature"],
                            strict=False,
                        )
                    )
                if not isinstance(conf["unit"], str | Unit):
                    conf["upper"] = conf["lower"]
                    conf["lower"] = conf["unit"]
                    del conf["unit"]
                op_cond_config["temperature"] = PropertyConfig(**conf)
            elif op_cond_type is DependentPropertyConditionConfig:
                op_cond_config = DependentPropertyConditionConfig(**op_cond_config)

        inited_prop = prop(value=value, op_cond_config=op_cond_config)

        conds = STPConditions()

        if callable(value):
            # temperature dependent calls
            assert np.allclose(inited_prop.value(conds), value(conds))

            if (
                op_cond_config is not None
                and inited_prop.op_cond_config.temperature.unit != ureg.Unit("K")
            ):
                assert np.allclose(
                    inited_prop(conds),
                    ureg.Quantity(value(conds), "K")
                    .to(inited_prop.op_cond_config.temperature.unit)
                    .magnitude,
                )
            else:
                assert np.allclose(inited_prop(conds), value(conds))
        else:
            assert np.allclose(inited_prop.value(conds), value)
            assert np.allclose(inited_prop(conds), value)

    def test_unit_conversion(self):
        k = YoungsModulus(value=5000, unit="Pa")
        dc = YoungsModulus(value=5, unit="kPa")
        dc2 = YoungsModulus(value=5, unit="1e3Pa")
        conds = STPConditions()

        assert k(conds) == dc(conds) == dc2(conds)
        assert k.unit == dc.unit == dc2.unit

    def test_new_dependent_property(self):
        with pytest.raises(ValueError, match="default unit"):

            class Wow(DependentPhysicalProperty): ...

        class Wow(DependentPhysicalProperty):
            unit: str | Unit = "ton"

        assert np.isclose(Wow(value=5, unit="g")(STPConditions()), 5.51155655462194e-06)

    def test_bad_unit(self):
        with pytest.raises(ValueError, match="Cannot convert"):
            YoungsModulus(value=5, unit="W")

    def test_wrapped_unit_callable(self, test_condition):
        assert YoungsModulus(value=lambda oc: 5, unit="GPa")(test_condition) == 5e9  # noqa: ARG005

    def test_value_as(self, test_condition):
        prop = YoungsModulus(value=lambda oc: 5, unit="GPa")  # noqa: ARG005
        assert np.isclose(prop.value_as(test_condition, unit="GPa"), 5)
        with pytest.raises(ValueError, match="Cannot convert"):
            prop.value_as(test_condition, "W")

    def test_check_and_modify_conditions(self, test_condition):
        prop = YoungsModulus(
            value=lambda oc: oc.temperature * 5,
            unit="GPa",
            op_cond_config={"temperature": "degC"},
        )
        assert np.allclose(
            prop.value_as(test_condition, unit="GPa"),
            5 * test_condition.temperature.value_as("degC"),
        )

    def test_undefined_property(self, test_condition):
        with pytest.raises(ValidationError, match="2 validation"):
            UndefinedProperty(value=5, unit="hello")

        with pytest.raises(NotImplementedError):
            UndefinedProperty()(test_condition)

    def test_array_access(self, test_condition):
        assert np.sum([
            test_condition.temperature,
            test_condition.pressure,
        ]) == pytest.approx(np.array([101623.0, 101525]))

        arr = (
            np.asarray([-3, -2.5, -2, -1.3, 0.7, 2, 3])[:, None]
            + test_condition.temperature
        ).ravel()
        assert np.interp(test_condition.temperature, arr, arr[::-1]) == pytest.approx(
            np.array([295, 203])
        )

    def test_initialisation_from_data(self, condition):
        den = Density.from_data(
            {"temperature": [10, 20, 30, 40, 50], "pressure": [20, 50, 100]},
            np.arange(15).reshape(5, 3),
        )

        # extrapolation
        assert den(condition) == pytest.approx(2112.9)

        # exact value on grid
        cond2 = OperationalConditions(temperature=20, pressure=20)
        assert den(cond2) == pytest.approx(3)

        # value interpolation
        cond3 = OperationalConditions(temperature=15, pressure=20)
        assert den(cond3) == pytest.approx(1.5)


class TestGroupingProperties:
    def test_props_as_field(self, test_condition):
        Test = material(
            "test",
            properties=props(
                as_field=True,
                density=5,
                poissons_ratio=True,
                thermal_conductivity=3.4,
                youngs_modulus={
                    "value": lambda properties, oc: properties.density(oc)
                    * oc.temperature
                },
                coefficient_thermal_expansion={"value": 6, "unit": "1/mK"},
                extra_prop={"value": 5, "unit": "Btu"},
            ),
        )

        test = Test()

        assert test.extra_prop(test_condition) == pytest.approx(5)
        assert test.thermal_conductivity(test_condition) == pytest.approx(3.4)
        assert test.youngs_modulus(test_condition) == pytest.approx(
            5 * test_condition.temperature
        )
        assert test.coefficient_thermal_expansion(test_condition) == pytest.approx(6e3)
        with pytest.raises(NotImplementedError):
            assert test.poissons_ratio(test_condition)

    def test_props_standalone(self, test_condition):
        my_props = props(
            as_field=False,
            density=5,
            poissons_ratio=True,
            thermal_conductivity=3.4,
            youngs_modulus={
                "value": lambda properties, oc: properties.density(oc) * oc.temperature
            },
            coefficient_thermal_expansion={"value": 6, "unit": "1/mK"},
            extra_prop={"value": 5, "unit": "Btu"},
        )

        assert my_props.extra_prop(test_condition) == pytest.approx(5)
        assert my_props.thermal_conductivity(test_condition) == pytest.approx(3.4)
        assert my_props.youngs_modulus(test_condition) == pytest.approx(
            5 * test_condition.temperature
        )
        assert my_props.coefficient_thermal_expansion(test_condition) == pytest.approx(
            6e3
        )
        with pytest.raises(NotImplementedError):
            assert my_props.poissons_ratio(test_condition)

        assert repr(my_props) == (
            "DynamicProperties("
            "defined_properties=['density', 'thermal_conductivity', "
            "'youngs_modulus', 'coefficient_thermal_expansion', 'extra_prop'], "
            "undefined_properties=['poissons_ratio'])"
        )

    def test_Properties(self, test_condition):
        @rebuild
        class MyProperties(Properties):
            density: Density
            specific_heat_capacity: SpecificHeatCapacity

            @dependentphysicalproperty(unit="")
            def residual_resistance_ratio(self, op_cond):
                return self.density(op_cond) * op_cond.temperature

        props = MyProperties(density=5, specific_heat_capacity=6)
        assert props.density(test_condition) == 5
        assert props.specific_heat_capacity(test_condition) == 6
        assert props.residual_resistance_ratio(test_condition) == pytest.approx(
            5 * test_condition.temperature
        )

        props = MyProperties(
            density=5, specific_heat_capacity=6, residual_resistance_ratio=7
        )

        assert props.density(test_condition) == 5
        assert props.specific_heat_capacity(test_condition) == 6
        assert props.residual_resistance_ratio(test_condition) == 7
