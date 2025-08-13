# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
import pytest

from physical_materials.base import References
from physical_materials.nucleides import (
    ElementFraction,
    Elements,
    mass_fraction_to_volume_fraction,
    volume_fraction_to_mass_fraction,
)


class TestElements:
    inp_types = pytest.mark.parametrize(
        "inp",
        [
            "CH3",
            {"C": 0.25, "H": 0.75, "reference": References(id="test", type="article")},
            {"C": 0.7988693049551047, "H": 0.20113069504489525, "fraction_type": "mass"},
            [{"element": "C", "fraction": 0.25}, {"element": "H", "fraction": 0.75}],
        ],
    )

    @inp_types
    def test_setup_types(self, inp):
        el = Elements.model_validate(inp)
        assert el.root.keys() == {"C", "H"}
        assert el["C"].fraction == pytest.approx(0.25)
        assert el["H"].fraction == pytest.approx(0.75)

    @inp_types
    def test_referencing(self, inp):
        el = Elements.model_validate(inp)

        if not isinstance(inp, list | str):
            assert el.reference == inp.get("reference")
        else:
            assert el.reference is None

    def test_direct_setup(self):
        el = Elements.model_validate(ElementFraction(element="H", fraction=1))
        assert el.root.keys() == {"H"}
        assert el["H"].fraction == 1

    def test_iteration(self):
        el = Elements.model_validate("CH3")

        for (_en, e), frac in zip(el, [0.25, 0.75], strict=False):
            assert e.fraction == frac

    def test_repr(self):
        el = Elements.model_validate("CH3")

        assert repr(el) == "Elements({'C': 0.25, 'H': 0.75})"

    def test_mass_number(self):
        el = Elements.model_validate({"C": 0.25, "H3": 0.75})
        assert el["H3"].element.mass_number == 3
        assert el["C"].element.mass_number == 12

    @pytest.mark.parametrize(
        ("formula", "res"),
        [
            ("CH3", {"C": 1, "H": 3}),
            ("CFe12", {"C": 1, "Fe": 12}),
            ("C(Fe12)H1", {"C": 1, "Fe": 12, "H": 1}),
            ("C(H12(BeU2)2)", {"C": 1, "H": 12, "Be": 2, "U": 4}),
            ("C(H3(Be2HO4)2)3C2", {"C": 3, "H": 15, "Be": 12, "O": 24}),
        ],
    )
    def test_chemical_formula(self, formula, res):
        el = Elements.model_validate(formula)

        ttl = sum(res.values())
        for k, v in el.model_dump().items():
            assert v == pytest.approx(res[k] / ttl)

    def test_bad_chemical_formula(self):
        with pytest.raises(ValueError, match=r"Unparsed.*'-nn\)'"):
            Elements.model_validate("C(H3-n(Be2HO4n)2)3C2)")


def test_weight_volume_fraction_conversion():
    densities = {"H": 5.1, "C": 6}
    vf = mass_fraction_to_volume_fraction(
        {
            "H": ElementFraction(element="H", fraction=0.201131),
            "C": ElementFraction(element="C", fraction=0.798869),
        },
        densities,
    )

    wf = volume_fraction_to_mass_fraction(vf, densities)

    assert wf["H"].fraction == pytest.approx(0.201131)
    assert wf["C"].fraction == pytest.approx(0.798869)
