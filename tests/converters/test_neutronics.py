# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import Any

import numpy as np
import pytest

from matproplib.conditions import OperationalConditions
from matproplib.converters.neutronics import (
    FispactNeutronicConfig,
    MCNPNeutronicConfig,
    OpenMCNeutronicConfig,
    SerpentNeutronicConfig,
    global_id,
)
from matproplib.material import material
from matproplib.tools.neutronics import NMM_FRACTION_TYPE_MAPPING


def empty_filter(lst: list[Any]) -> list[Any]:
    return list(filter(None, lst))


class TestOpenMCNeutronics:
    @pytest.mark.parametrize("percent_type", ["atomic", "mass"])
    def test_material_file_generation(self, percent_type, test_condition):
        pytest.importorskip("openmc")
        Simple = material(
            "Simple",
            "H2O",
            properties={"density": 1},
            converters=OpenMCNeutronicConfig(
                zaid_suffix=".80c", percent_type=percent_type
            ),
        )

        simple = Simple()

        out = simple.convert("openmc", test_condition)

        assert out.density == pytest.approx(0.001)

        assert len(out.nuclides) == 5
        assert [a.name for a in out.nuclides[:2]] == ["H1", "H2"]
        assert np.sum([a.percent for a in out.nuclides[:2]]) == pytest.approx(
            6.66666667e-01 if percent_type == "atomic" else 0.11190, abs=1e-4
        )
        assert [a.name for a in out.nuclides[2:]] == ["O16", "O17", "O18"]
        assert np.sum([a.percent for a in out.nuclides[2:]]) == pytest.approx(
            3.33333333e-01 if percent_type == "atomic" else 0.88810, abs=1e-4
        )
        assert out.temperature is None
        assert all(
            np.array([a.percent_type for a in out.nuclides])
            == NMM_FRACTION_TYPE_MAPPING[percent_type]
        )

    def test_material_with_bad_temperature(self, test_condition):
        with pytest.raises(ValueError, match="Only singular"):
            material(
                "Simple",
                "H2O",
                properties={"density": 1},
                converters=OpenMCNeutronicConfig(),
            )().convert("openmc", test_condition, temperature_to_neutronics_code=True)

    def test_material_with_bad_density(self, test_condition):
        with pytest.raises(ValueError, match="density"):
            material(
                "Simple",
                "H2O",
                converters=OpenMCNeutronicConfig(),
            )().convert("openmc", test_condition, temperature_to_neutronics_code=True)

    def test_material_with_temperature(self):
        pytest.importorskip("openmc")
        out = material(
            "Simple",
            "H2O",
            properties={"density": 1},
            converters=OpenMCNeutronicConfig(),
        )().convert(
            "openmc",
            OperationalConditions(temperature=10, pressure=1),
            temperature_to_neutronics_code=True,
        )
        assert out.temperature == pytest.approx(10)


class TestMCNPNeutronics:
    # mcnp.lanl.gov/pdf_files/Book_MonteCarlo_2024_ShultisBahadori_AnMCNPPrimer.pdf
    MCNP6_MASS_MAT = (
        "M21   001001.80c -1.11868983e-01\n      001002.80c -3.24217864e-05\n"
        "      008016.80c -8.85693561e-01\n      008017.80c -3.61868091e-04\n"
        "      008018.80c -2.04316632e-03"
    )
    MCNP6_ATOMIC_MAT = (
        "M21   001001.80c  6.66570000e-01\n      001002.80c  9.66666667e-05\n"
        "      008016.80c  3.32523832e-01\n      008017.80c  1.27833525e-04\n"
        "      008018.80c  6.81667689e-04"
    )

    @pytest.mark.parametrize("percent_type", ["atomic", "mass"])
    def test_material_file_generation(self, percent_type, test_condition):
        Simple = material(
            "Simple",
            "H2O",
            properties={"density": 1},
            converters=MCNPNeutronicConfig(
                material_id=21, zaid_suffix=".80c", percent_type=percent_type
            ),
        )

        simple = Simple()
        out = simple.convert("mcnp", test_condition)

        _comment, h1, _h2, o1, _o2, _o3 = out.split("\n")[:-1]

        assert h1.startswith("M21   001001")
        assert o1.startswith("      008016")

        res_h1, _res_h2, res_o1, _res_o2, _res_o3 = getattr(
            self, f"MCNP6_{percent_type.upper()}_MAT"
        ).split("\n")

        r_m_id, r_atom, r_fraction = empty_filter(res_h1.split(" "))
        m_id, atom, fraction = empty_filter(h1.split(" "))
        assert m_id == r_m_id
        assert atom == r_atom
        assert float(fraction) == pytest.approx(float(r_fraction), abs=1e-4)

        r_atom, r_fraction = empty_filter(res_o1.split(" "))
        atom, fraction = empty_filter(o1.split(" "))
        assert atom == r_atom
        assert float(fraction) == pytest.approx(float(r_fraction), abs=1e-4)

        out = simple.convert(
            "mcnp", test_condition, additional_end_lines=["hello", "hi"]
        )
        assert out.split("\n")[-3] == "hello"
        assert out.split("\n")[-2] == "hi"

    def test_unused_material_id(self, test_condition):
        # Probably not threadsafe etc
        start = global_id["mcnp"]

        assert start > 0

        Simple = material(
            "Simple",
            "H2O",
            properties={"density": 1},
            converters=MCNPNeutronicConfig(),
        )

        simple = Simple()
        for i in range(10):
            out = simple.convert("mcnp", test_condition)
            assert out.split("\n")[1].startswith(f"M{start + i}")

        assert global_id["mcnp"] == start + 10


class TestSerpentNeutronics:
    # merlin.polymtl.ca/Serpent_Dragon/Serpent_manual_2013.pdf
    SERPENT_MASS_MAT = (
        "mat water -7.20700000e-01\n      001001.06c -1.11868983e-01\n"
        "      001002.06c -3.24217864e-05\n"
        "      008016.06c -8.85693561e-01\n"
        "      008017.06c -3.61868091e-04\n"
        "      008018.06c -2.04316632e-03"
    )
    SERPENT_ATOMIC_MAT = (
        "mat water -7.20700000e-01\n      001001.06c  6.66570000e-01\n"
        "      001002.06c  9.66666667e-05\n"
        "      008016.06c  3.32523832e-01\n"
        "      008017.06c  1.27833525e-04\n"
        "      008018.06c  6.81667689e-04"
    )

    @pytest.mark.parametrize("percent_type", ["atomic", "mass"])
    def test_material_file_generation(self, percent_type, test_condition):
        Simple = material(
            "water",
            "H2O",
            properties={"density": (0.7207, "g/cm^3")},
            converters=SerpentNeutronicConfig(
                zaid_suffix=".06c", percent_type=percent_type
            ),
        )
        simple = Simple()
        out = simple.convert("serpent", test_condition)

        _comment, h1, _h2, o1, _o2, _o3 = out.split("\n")[:-1]

        assert h1.startswith("      001001")
        assert o1.startswith("      008016")

        _comment, res_h1, _res_h2, res_o1, _res_o2, _res_o3 = getattr(
            self, f"SERPENT_{percent_type.upper()}_MAT"
        ).split("\n")

        r_atom, r_fraction = empty_filter(res_h1.split(" "))
        atom, fraction = empty_filter(h1.split(" "))
        assert atom == r_atom
        assert float(fraction) == pytest.approx(float(r_fraction), abs=1e-4)

        r_atom, r_fraction = empty_filter(res_o1.split(" "))
        atom, fraction = empty_filter(o1.split(" "))
        assert atom == r_atom
        assert float(fraction) == pytest.approx(float(r_fraction), abs=1e-4)

    def test_material_with_bad_temperature(self, test_condition):
        with pytest.raises(ValueError, match="Only singular"):
            material(
                "Simple",
                "H2O",
                properties={"density": 1},
                converters=SerpentNeutronicConfig(),
            )().convert("serpent", test_condition, temperature_to_neutronics_code=True)

    def test_material_with_temperature(self):
        assert (
            material(
                "Simple",
                "H2O",
                properties={"density": 1},
                converters=SerpentNeutronicConfig(),
            )()
            .convert(
                "serpent",
                OperationalConditions(temperature=10, pressure=1),
                temperature_to_neutronics_code=True,
            )
            .split("\n")[0]
            .endswith("tmp 10.0")
        )


class TestFispactNeutronics:
    # https://fispact.ukaea.uk/wp-content/uploads/2021/05/user_manual-4.pdf
    # https://fispact.ukaea.uk/wiki/Keyword:FUEL
    FISPACT_MAT = "DENSITY 1.0000E+01\nFUEL 2\nLi6  8.0093E+24\nLi7  1.7167E+24\n"

    def test_material_file_generation(self, test_condition):
        Simple = material(
            "Simple",
            {"Li6": 0.80, "Li7": 0.2},
            properties={"density": (10, "g/cm^3")},
            converters=FispactNeutronicConfig(volume=(10, "cm^3"), decimal_places=4),
        )

        simple = Simple()
        out = simple.convert("fispact", test_condition)

        den, fuel, li6, li7 = out.split("\n")[:-1]
        res_den, res_fuel, res_li6, res_li7 = self.FISPACT_MAT.split("\n")[:-1]

        assert float(den.split(" ")[1]) == pytest.approx(float(res_den.split(" ")[1]))
        assert int(fuel.split(" ")[1]) == pytest.approx(int(res_fuel.split(" ")[1]))
        n, v = empty_filter(li7.split(" "))
        res_n, res_v = empty_filter(res_li7.split(" "))
        assert n == res_n
        assert float(v) == pytest.approx(float(res_v))
        n, v = empty_filter(li6.split(" "))
        res_n, res_v = empty_filter(res_li6.split(" "))
        assert n == res_n
        assert float(v) == pytest.approx(float(res_v))


def test_change_converters():
    Simple = material(
        "Simple",
        {"Li6": 0.80, "Li7": 0.2},
        properties={"density": (10, "g/cm^3")},
        converters=FispactNeutronicConfig(volume=(10, "cm^3"), decimal_places=4),
    )

    simple = Simple(converters=MCNPNeutronicConfig())

    assert simple.converters.root.keys() == {"mcnp"}

    Simple = material(
        "Simple",
        {"Li6": 0.80, "Li7": 0.2},
        properties={"density": (10, "g/cm^3")},
        converters=FispactNeutronicConfig(volume=(10, "cm^3"), decimal_places=4),
    )

    simple = Simple()
    simple.converters.add(MCNPNeutronicConfig())

    assert simple.converters.root.keys() == {"fispact", "mcnp"}
