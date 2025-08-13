# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
import copy

import numpy as np
import pytest
from pint import Quantity

from physical_materials.conditions import (
    DependentPropertyConditionConfig,
    OperationalConditions,
    Pressure,
    STPConditions,
    Temperature,
    check_conditions,
    modify_conditions,
)
from physical_materials.properties.independent import Volume
from tests import _np_and_value_test


class TestOperationalConditions:
    @pytest.mark.parametrize("inp", [np.ones(5), 1])
    def test_operational_condition_values(self, inp):
        for cond in [
            OperationalConditions(temperature=inp, pressure=inp),
            OperationalConditions(temperature={"value": inp}, pressure={"value": inp}),
        ]:
            _np_and_value_test(cond.temperature, inp)
            _np_and_value_test(cond.pressure, inp)

    @pytest.mark.parametrize(
        ("inp", "out"), [((1, "degC"), 274.15), (Quantity(1, "degR"), 0.555555)]
    )
    def test_operational_condition_val_and_unit(self, inp, out):
        for cond in [
            OperationalConditions(temperature=inp, pressure=1),
            OperationalConditions(temperature={"value": inp}, pressure=1),
        ]:
            _np_and_value_test(cond.temperature, out)

    @pytest.mark.parametrize(
        "temp",
        [
            (1, "degC"),
            Quantity(1, "degC"),
            {"value": 1, "unit": "degC"},
            274.15,
            {"value": Quantity(1, "degC")},
            {"value": (1, "degC")},
        ],
    )
    def test_setting_properties_on_operational_conditions(self, temp):
        a = OperationalConditions(temperature=1, pressure=1)
        a.temperature = temp
        assert a.temperature.value == 274.15

    def test_operational_condition_of_different_lengths(self):
        a_ok = OperationalConditions(temperature=np.ones(3), pressure=1)
        assert a_ok.pressure.value.size == 3
        a_ok = OperationalConditions(temperature=1, pressure=np.ones(3))
        assert a_ok.temperature.value.size == 3
        a_ok = OperationalConditions(temperature=np.ones(1), pressure=np.ones(3))
        assert a_ok.temperature.value.size == 3

        with pytest.raises(ValueError, match="1 valid"):
            OperationalConditions(temperature=np.ones(2), pressure=np.ones(3))

    def test_good_operation_condition_type(self):
        class ExtensionCondition(OperationalConditions):
            b: Temperature | None = None

        ext = ExtensionCondition(temperature=1, pressure=2)
        assert ext.b is None
        ext = ExtensionCondition(temperature=2, pressure=2, b=1)
        assert ext.b.value == 1

    def test_bad_operation_condition_type(self):
        with pytest.raises(TypeError, match="field types must be"):

            class ExtensionCondition(OperationalConditions):
                b: int = 4

    def test_stp_conditions(self):
        stp = STPConditions()
        assert stp.temperature.value == 273.15
        assert stp.pressure.value == 1e5

        with pytest.raises(ValueError, match="cannot be modified"):
            STPConditions(pressure=5)

        with pytest.raises(ValueError, match="cannot be modified"):
            STPConditions(temperature=5)

    @pytest.mark.filterwarnings("error::pydantic.json_schema.PydanticJsonSchemaWarning")
    def test_serialisation_for_defaults(self):
        class ExtensionCondition(OperationalConditions):
            temperature: Temperature = Temperature(value=[1, 2.5, 3])
            pressure: Pressure = Pressure(value=np.array([4, 5, 6]))

        temp = ExtensionCondition()
        json_temp_schema = temp.model_json_schema()["properties"]
        assert json_temp_schema["temperature"]["default"]["unit"] == "K"
        assert json_temp_schema["pressure"]["default"]["value"] == [4, 5, 6]


class TestConditionModification:
    @classmethod
    def setup_class(cls):
        class sSTP(STPConditions):
            volume: Volume

        cls.sSTP = sSTP

    @pytest.mark.parametrize(
        ("op_cond_config", "prop", "value"),
        [
            (DependentPropertyConditionConfig(temperature=("degC")), "temperature", 0),
            (DependentPropertyConditionConfig(volume=("cm^3")), "volume", 3e6),
        ],
    )
    def test_modify_conditions(self, op_cond_config, prop, value):
        op_cond = self.sSTP(volume=3)

        mod_op_cond = modify_conditions(op_cond, op_cond_config)

        for name, moc in mod_op_cond:
            if name == prop:
                assert moc.unit == getattr(op_cond_config, name).unit
                assert moc.value == pytest.approx(value)
                assert moc != getattr(op_cond, name)
            else:
                assert moc == getattr(op_cond, name)

    @pytest.mark.parametrize(
        ("op_cond_config", "does_raise", "does_match"),
        [
            (DependentPropertyConditionConfig(), False, None),
            (
                DependentPropertyConditionConfig(temperature=("degC", -5, -3)),
                True,
                "upper",
            ),
            (DependentPropertyConditionConfig(temperature=("degC", -2, 2)), False, None),
            (DependentPropertyConditionConfig(volume=("cm^3")), False, None),
            (DependentPropertyConditionConfig(volume=("cm^3", 4e6, 5e6)), True, "lower"),
            (DependentPropertyConditionConfig(volume=("cm^3", 1e6, 3e6)), False, None),
        ],
    )
    def test_check_conditions_raises_ValueError(
        self, op_cond_config, does_raise, does_match
    ):
        op_cond = self.sSTP(volume=3)
        mod_op_cond = modify_conditions(op_cond, op_cond_config)

        if does_raise:
            with pytest.raises(ValueError, match=does_match):
                check_conditions(mod_op_cond, op_cond_config)
        else:
            check_conditions(mod_op_cond, op_cond_config)

    def test_dependentpropertyconfig_repr(self):
        assert repr(DependentPropertyConditionConfig(temperature=("degC", -2, 2))) == (
            "DependentPropertyConditionConfig(temperature=PropertyConfig(reference=None "
            "unit=<Unit('degree_Celsius')> lower=-2.0 upper=2.0))"
        )
        assert repr(DependentPropertyConditionConfig(volume=("cm^3"))) == (
            "DependentPropertyConditionConfig(volume=PropertyConfig(reference=None "
            "unit=<Unit('centimeter ** 3')> lower=None upper=None))"
        )

    def test_op_cond_config_raises_ValueError_on_unknown_config(self):
        with pytest.raises(ValueError, match="unknown"):
            DependentPropertyConditionConfig(volume=(1e6, 3e6))

    def modification_of_STP(self):
        stp = STPConditions()

        not_stp = copy.copy(stp)
        not_stp.temperature = 10

        assert not isinstance(not_stp, STPConditions)
        assert isinstance(not_stp, OperationalConditions)
        assert not_stp.temperature == pytest.approx(10)
