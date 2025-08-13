# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
import pytest
from csl_reference import Reference
from pint import Unit

from physical_materials.base import rebuild, ureg
from physical_materials.conditions import (
    DependentPropertyConditionConfig,
    OperationalConditions,
    STPConditions,
)
from physical_materials.converters.base import Converters
from physical_materials.converters.neutronics import OpenMCNeutronicConfig
from physical_materials.library.copper import CryogenicCopper
from physical_materials.library.fluids import H2O, DDPlasma, DTPlasma
from physical_materials.material import (
    FullMaterial,
    Material,
    MaterialFraction,
    dependentphysicalproperty,
    material,
    mixture,
)
from physical_materials.nucleides import ElementFraction, Elements
from physical_materials.properties.dependent import (
    Density,
    PoissonsRatio,
    UndefinedProperty,
    YoungsModulus,
)
from physical_materials.properties.group import DefaultProperties, props
from physical_materials.superconduction import Nb3SnBotturaParameterisation


class TestMaterialFunctionalInit:
    def test_simple(self):
        Simple = material("Simple")
        simple = Simple()
        assert not simple.elements
        assert type(simple).model_fields.keys() == {
            "reference",
            "name",
            "elements",
            "converters",
            "mixture_fraction",
        }
        assert simple.converters.root == {}

    @pytest.mark.parametrize(
        "ref",
        [
            {"id": 1, "type": "article"},
            Reference(id=1, type="article"),
            [{"id": 1, "type": "article"}, {"id": 2, "type": "article"}],
            [Reference(id=1, type="article"), Reference(id=2, type="article")],
        ],
    )
    def test_simple_reference(self, ref):
        Simple = material("Simple")
        simple = Simple(reference=ref)
        assert not simple.elements
        assert type(simple).model_fields.keys() == {
            "reference",
            "name",
            "elements",
            "converters",
            "mixture_fraction",
        }
        assert simple.converters.root == {}

        assert (
            simple.reference.root.keys() == {1.0, 2.0}
            if isinstance(ref, list)
            else {1.0}
        )

    def test_references_on_properties_group(self):
        raise NotImplementedError

    def test_element(self):
        Element = material("Element", elements=["H"])
        element = Element()
        assert element.elements == Elements(H=ElementFraction(element="H", fraction=1))

    def test_elements(self):
        ElementsMat = material("ElementsMat", elements={"H": 0.1, "He": 0.9})
        elements = ElementsMat()
        assert elements.elements == Elements(
            H=ElementFraction(element="H", fraction=0.1),
            He=ElementFraction(element="He", fraction=0.9),
        )

    def test_bad_elements(self):
        Elements2 = material("Elements2", elements={"H": 1.1})

        with pytest.raises(ValueError, match="greater than 1"):
            Elements2()

    def test_properties(self):
        Struct1 = material(
            "Struct1",
            properties={
                "density": 5,
                "poissons_ratio": lambda oc: oc.temperature**2,
                "youngs_modulus": True,
            },
        )
        Struct2 = material(
            "Struct2",
            properties=props(
                density=5,
                poissons_ratio=lambda oc: oc.temperature**2,
                youngs_modulus=True,
            ),
        )

        struct1 = Struct1()
        struct2 = Struct2()
        cond = STPConditions()
        assert struct1.density(cond) == struct2.density(cond)
        assert struct1.poissons_ratio(cond) == struct2.poissons_ratio(cond)

        assert struct1.youngs_modulus == UndefinedProperty()
        assert struct2.youngs_modulus == UndefinedProperty()
        struct1.youngs_modulus = 5
        assert struct1.youngs_modulus(cond) == 5
        assert type(struct1.youngs_modulus) is YoungsModulus

        assert (
            type(struct1).model_fields.keys()
            == type(struct2).model_fields.keys()
            == {
                "reference",
                "name",
                "elements",
                "converters",
                "mixture_fraction",
                "density",
                "poissons_ratio",
                "youngs_modulus",
            }
        )

    def test_default_properties(self):
        Struct3 = material("Struct3", properties=DefaultProperties())

        struct3 = Struct3()
        assert {"name", "elements", "converters", "mixture_fraction"} ^ type(
            struct3
        ).model_fields.keys() == DefaultProperties.model_fields.keys()

    @pytest.mark.parametrize(
        "prop",
        [
            DefaultProperties(reference={"id": 1, "type": "article"}),
            props(reference={"id": 1, "type": "article"}),
        ],
    )
    def test_reference_combining(self, prop):
        struct = material("Struct", properties=prop)()

        assert struct.reference[1] == Reference(id=1, type="article")

    def test_combining_properties(self):
        raise NotImplementedError


class TestMaterialClassInit:
    def test_self_init(self):
        with pytest.raises(NotImplementedError):
            Material(name="mat")

    def test_simple(self):
        class SimpleClass(Material):
            name: str = "SimpleClass"

        simple = SimpleClass()
        assert not simple.elements
        assert simple.converters.root == {}

    def test_properties_accessed_on_init(self):
        struct = {
            "density": 5,
            "poissons_ratio": lambda oc: oc.temperature,
            "thermal_conductivity": True,
        }
        struct2 = props(**struct)

        struct3 = DefaultProperties(
            density=5,
            poissons_ratio=lambda oc: oc.temperature,
            thermal_conductivity=UndefinedProperty(),
        )

        class Complex(FullMaterial):
            name: str = "Complex"

        c1 = Complex(properties=struct)
        c2 = Complex(properties=struct2)
        c3 = Complex(properties=struct3)

        assert (
            type(c1).model_fields.keys()
            == type(c2).model_fields.keys()
            == type(c3).model_fields.keys()
        )
        assert {"name", "elements", "converters", "mixture_fraction"} ^ type(
            c3
        ).model_fields.keys() == DefaultProperties.model_fields.keys()

    def test_properties_from_defaults_on_material(self):
        raise NotImplementedError

    @pytest.mark.parametrize("op_cond_config", [None, {"temperature": {"unit": "degC"}}])
    def test_dependentphysicalproperty_decorator(self, op_cond_config):
        @rebuild
        class DepMat(FullMaterial):
            name: str = "DepMat"

            density: Density = 5
            converters: Converters = OpenMCNeutronicConfig()

            @dependentphysicalproperty(unit="", op_cond_config=op_cond_config)
            def thing(self, op_cond: OperationalConditions) -> float:
                return self.density(op_cond) * self.converters.openmc.packing_fraction

        dep_mat = DepMat()

        assert dep_mat.thing(STPConditions()) == 5
        if op_cond_config is not None:
            op_cond_config = DependentPropertyConditionConfig(**op_cond_config)

        assert dep_mat.thing.op_cond_config == op_cond_config

    def test_bad_dependentphysicalproperty_decorator(self):
        with pytest.raises(ValueError, match="specified"):

            @rebuild
            class DepMat(FullMaterial):
                name: str = "DepMat"

                density: Density = 5

                @dependentphysicalproperty()
                def thing(self, op_cond: OperationalConditions) -> float:
                    return self.density(op_cond) * op_cond.temperature

    def test_inheritance_dependentphysicalproperty_decorator(self):
        @rebuild
        class DepMat2(FullMaterial):
            name: str = "DepMat2"

            poissons_ratio: PoissonsRatio = 5

            @dependentphysicalproperty(Density)
            def thing(self, op_cond: OperationalConditions) -> float:
                return self.density(op_cond) * op_cond.temperature

        assert not hasattr(DepMat2, "thing")
        assert issubclass(type(DepMat2.model_fields["thing"].default), Density)
        assert DepMat2.model_fields["thing"].default.unit == ureg.Unit(
            Density.model_fields["unit"].default
        )

    def test_simple_serialisation(self, test_material):
        mat_dict = test_material.model_dump()

        empty_dict_keys = {}.keys()
        assert mat_dict["name"] == test_material.name
        assert mat_dict["elements"] == test_material.elements.model_dump() != {}
        assert (
            mat_dict.keys() == type(test_material).model_fields.keys() != empty_dict_keys
        )
        assert (
            mat_dict["converters"].keys()
            == test_material.converters.root.keys()
            != empty_dict_keys
        )


class TestMixtures:
    @pytest.mark.parametrize(
        "mats",
        [
            [
                MaterialFraction(material=CryogenicCopper(), fraction=0.5),
                MaterialFraction(material=CryogenicCopper(), fraction=0.5),
            ],
            [(CryogenicCopper(), 0.5), (CryogenicCopper(), 0.5)],
        ],
    )
    def test_simple_combination(self, mats):
        mix = mixture("special", mats)

        assert mix.elements == mix.mixture_fraction[0].material.elements

    def test_complex_combination(self, test_condition):
        test_condition.temperature = [289, 459]
        mix = mixture(
            "PlasmaWater", [(DDPlasma(), 0.4), (DTPlasma(), 0.4), (H2O(), 0.2)]
        )

        constit = [m.material.density(test_condition) for m in mix.mixture_fraction]
        md = mix.density(test_condition)

        assert md[0] == pytest.approx(
            (constit[0] * 0.4) + (constit[1] * 0.4) + (constit[2][0] * 0.2)
        )
        assert md[1] == pytest.approx(
            (constit[0] * 0.4) + (constit[1] * 0.4) + (constit[2][1] * 0.2)
        )

    def test_overridden_properties_function(self, test_condition):
        mix = mixture(
            "PlasmaWater",
            [(DDPlasma(), 0.4), (DTPlasma(), 0.4), (H2O(), 0.2)],
            density=6,
        )
        assert mix.density(test_condition) == pytest.approx(6)

    def test_undefined_properties_on_one_material_raises(self):
        raise NotImplementedError

    @pytest.mark.parametrize(
        ("fraction", "elements"),
        [
            ("atomic", {"H": 0.1, "O": 0.74, "C": 0.16}),
            ("mass", {"H": 0.1544374, "O": 0.707337, "C": 0.138225}),
            ("volume", {"H": 0.15443743, "O": 0.707337, "C": 0.138225}),
        ],
    )
    def test_fractional_types(self, fraction, elements):
        m1 = material(
            "m1",
            elements={"H": 0.5, "O": 0.5},
            properties=props(density=lambda op_cond: op_cond.temperature**2),
        )
        m2 = material(
            "m2",
            elements={"C": 0.2, "O": 0.8},
            properties=props(density=lambda op_cond: op_cond.pressure**2),
        )

        mix = mixture("special", [(m1(), 0.2), (m2(), 0.8)], fraction_type=fraction)

        assert mix.elements.model_dump() == pytest.approx(
            Elements.model_validate(elements).model_dump()
        )
        if fraction == "volume":
            raise ValueError("This is the same as mass?!")

    def test_different_units_in_properties(self, test_condition, caplog):
        m1 = material(
            "m1",
            elements={"H": 0.5, "O": 0.5},
            properties=props(density=lambda op_cond: op_cond.temperature**2),
        )

        class MyDensity(Density):
            unit: Unit | str = "g/cm^3"

        m2 = material(
            "m2",
            elements={"C": 0.2, "O": 0.8},
            properties=props(
                density=MyDensity(value=lambda op_cond: 1 / op_cond.pressure**2)
            ),
        )

        mix = mixture("special", [(m1(), 0.2), (m2(), 0.8)])

        assert len(caplog.records) == 1
        assert "not the same" in caplog.records[0].msg
        assert mix.density(test_condition) == pytest.approx([
            17760.8,
            8000,
        ])
        assert len(caplog.records) == 1


class TestSerialisation:
    def test_numerical_serialisation_deserialisation(self, test_condition):
        Simple = material(
            "Simple",
            elements="H2O",
            properties=props(
                as_field=True,
                density=(5, "g/cm^3"),
                poissons_ratio=4,
                superconducting_parameterisation=Nb3SnBotturaParameterisation(
                    constant=1,
                    p=2,
                    q=3,
                    c_a1=4,
                    c_a2=5,
                    eps_0a=6,
                    eps_m=7,
                    b_c20m=8,
                    t_c0max=9,
                    reference=None,
                ),
            ),
            converters=OpenMCNeutronicConfig(),
        )
        simple = Simple()
        out = Simple.model_validate_json(simple.model_dump_json())

        assert simple.name == out.name
        assert simple.elements == out.elements
        assert simple.converters == out.converters
        assert (
            simple.density(test_condition)
            == simple.density(test_condition)
            == pytest.approx(5000)
        )
        assert (
            simple.poissons_ratio(test_condition)
            == simple.poissons_ratio(test_condition)
            == pytest.approx(4)
        )
        ssp = simple.superconducting_parameterisation
        osp = out.superconducting_parameterisation
        assert ssp.constant == osp.constant == 1
        assert ssp.p == osp.p == 2
        assert ssp.q == osp.q == 3
        assert ssp.c_a1 == osp.c_a1 == 4
