# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import re
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
from matproplib.material import Material, material, mixture
from matproplib.properties.group import props
from matproplib.tools.neutronics import NM_FRACTION_TYPE_MAPPING


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
            == NM_FRACTION_TYPE_MAPPING[percent_type]
        )

    def test_material_with_bad_temperature(self, test_condition):
        with pytest.raises(ValueError, match="Only singular"):
            material(
                "Simple",
                "H2O",
                properties={"density": 1},
                converters=OpenMCNeutronicConfig(),
            )().convert("openmc", test_condition, temperature_to_neutronics_code=True)

    def test_material_with_bad_density(self, condition):
        with pytest.raises(ValueError, match="Density"):
            material(
                "Simple",
                "H2O",
                converters=OpenMCNeutronicConfig(),
            )().convert("openmc", condition, temperature_to_neutronics_code=True)

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
            .endswith("tmp 10.00")
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


TRUE_OPENMC_MAT_CARD_0_15_2 = """
    Material
        ID             =	102
        Name           =	inb_breeder_zone
        Temperature    =	None
        Density        =	2.2730677516373854 [g/cm3]
        Volume         =	None [cm^3]
        Depletable     =	False
        S(a,b) Tables
        Nuclides
        Be9            =	0.6998631398987395 [ao]
        Cr50           =	0.0006047907018436486 [ao]
        Cr52           =	0.011662786678199647 [ao]
        Cr53           =	0.0013224663885423491 [ao]
        Cr54           =	0.00032918987568704926 [ao]
        Fe54           =	0.007699874949531171 [ao]
        Fe56           =	0.12087156990920157 [ao]
        Fe57           =	0.0027914516711816176 [ao]
        Fe58           =	0.0003714909727575347 [ao]
        He4            =	5.015408434749479e-06 [ao]
        Li6            =	0.023828836409492994 [ao]
        Li7            =	0.015885890939662 [ao]
        O16            =	0.043926895401338095 [ao]
        Si28           =	0.007822597811197195 [ao]
        Ti46           =	0.005159062951108941 [ao]
        Ti47           =	0.004652536770454609 [ao]
        Ti48           =	0.04610013584918195 [ao]
        Ti49           =	0.003383094613999924 [ao]
        Ti50           =	0.0032392661923326444 [ao]
        W182           =	0.00012897639723287904 [ao]
        W183           =	6.895717680765254e-05 [ao]
        W184           =	0.00014723557673232383 [ao]
        W186           =	0.0001347374563400298 [ao]
    """

EUROFER_MAT = material(
    name="eurofer",
    elements={
        "Fe": 0.9006,
        "Cr": 0.0886,
        "W182": 0.0108 * 0.266,
        "W183": 0.0108 * 0.143,
        "W184": 0.0108 * 0.307,
        "W186": 0.0108 * 0.284,
        "fraction_type": "mass",
    },
    properties=props(density=(7.78, "g/cm^3")),
    converters=OpenMCNeutronicConfig(),
)()

TUNGSTEN_MAT = material(
    name="tungsten",
    elements={
        "W182": 0.266,
        "W183": 0.143,
        "W184": 0.307,
        "W186": 0.284,
        "fraction_type": "atomic",
    },
    properties=props(density=(19.3, "g/cm^3")),
    converters=OpenMCNeutronicConfig(),
)()

Be12Ti = material(
    "Be12Ti",
    elements={"Be": 12.0 / 13, "Ti": 1.0 / 13, "fraction_type": "atomic"},
    converters=OpenMCNeutronicConfig(),
    properties=props(density=2250.0),
)

HELIUM_MAT = material(
    "He",
    elements={"He4": 1.0},
    converters=OpenMCNeutronicConfig(),
    properties=props(density=0.008867),
)()


def make_Li4SiO4_mat(li_enrich_ao, packing_fraction=0.642) -> Material:
    """
    Making enriched Li4SiO4 from elements with enrichment of Li6 enrichment

    Parameters
    ----------
    li_enrich_ao:
        The fraction of enrichment of the lithium-6.

    Returns
    -------
    :
        Li4SiO4 material with the specified Li-6 enrichment.

    Notes
    -----
    packing_fraction=0.642 Fusion Eng. Des., 164, 112171. See issue #3657
    """
    return material(
        name="lithium_orthosilicate",
        elements={"Li": 4 / 9, "Si28": 1 / 9, "O16": 4 / 9},
        properties=props(
            density=(packing_fraction * (2.247 + 0.078 * (1.0 - li_enrich_ao)), "g/cm^3")
        ),
        converters=OpenMCNeutronicConfig(
            enrichment=li_enrich_ao * 100,
            enrichment_target="Li6",
            enrichment_type="atomic",
        ),
    )()


def make_Li2TiO3_mat(li_enrich_ao, packing_fraction=0.642) -> Material:
    """
    Make Li2TiO3 according to the enrichment fraction inputted.

    Parameters
    ----------
    li_enrich_ao:
        The fraction of enrichment of the lithium-6.

    Returns
    -------
    :
        Li2TiO3 material with the specified Li-6 enrichment.

    Notes
    -----
    packing_fraction=0.642 Fusion Eng. Des., 164, 112171. See issue #3657
    """
    return material(
        name="lithium_titanate",
        elements={"Li": 2 / 6, "Ti": 1 / 6, "O16": 3 / 6},
        properties=props(
            density=(
                packing_fraction * (3.28 + 0.06 * (1.0 - li_enrich_ao)),
                "g/cm^3",
            )
        ),
        converters=OpenMCNeutronicConfig(
            enrichment=li_enrich_ao * 100,
            enrichment_target="Li6",
            enrichment_type="atomic",
        ),
    )()


# Lithium-containing material that is also a mixture of existing materials
def make_KALOS_ACB_mat(li_enrich_ao) -> Material:
    """
    Parameters
    ----------
    li_enrich_ao:
        The fraction of enrichment of the lithium-6.

    Returns
    -------
    :
        the KALOS_ACB material with the specified Li-6 enrichment.

    Notes
    -----
    Ref: Current status and future perspectives of EU ceramic breeder development
    (Fusion Eng. Des., 164, 112171)
    """
    return mixture(
        name="kalos_acb",  # optional name of homogeneous material
        materials=[  # molar combination adjusted to atom fractions
            (make_Li4SiO4_mat(li_enrich_ao), 9 * 0.65 / (9 * 0.65 + 6 * 0.35)),
            (make_Li2TiO3_mat(li_enrich_ao), 6 * 0.35 / (9 * 0.65 + 6 * 0.35)),
        ],
        fraction_type="atomic",
        converters=OpenMCNeutronicConfig(
            # packing_fraction=0.642,  # Fusion Eng. Des., 164, 112171. See issue #3657
            enrichment=li_enrich_ao * 100,
            enrichment_target="Li6",
            enrichment_type="atomic",
        ),
    )  # combination fraction type is by atom fraction
    # KALOS_ACB_mat.set_density("g/cm^3", 2.52 * 0.642)  # applying packing fraction
    # 3657


def compare_openmc_mat_cards(str1: str, str2: str, tol: float = 1e-8):
    """
    Compare two OpenMC material definition strings, using str1 as the reference.
    Shows absolute and relative (to str1) differences.
    """  # noqa: DOC201

    def parse_material(s: str):
        pattern = re.compile(r"(\w+)\s*=\s*([^\s]+)")
        data = {}
        for key, value in pattern.findall(repr(s)):
            v = re.sub(r"\[.*?\]", "", value).encode().decode("unicode_escape").strip()
            try:
                data[key] = float(v)
            except ValueError:
                data[key] = v
        return data

    ref = parse_material(str1)
    new = parse_material(str2)

    ref_keys, new_keys = set(ref), set(new)

    only_in_ref = sorted(ref_keys - new_keys)
    only_in_new = sorted(new_keys - ref_keys)
    both = sorted(ref_keys & new_keys)

    diffs = []

    for key in both:
        v1, v2 = ref[key], new[key]
        if isinstance(v1, float) and isinstance(v2, float):
            if not np.isclose(v1, v2, rtol=tol, atol=tol):
                rel_diff = (v2 - v1) / v1 if v1 != 0 else float("inf")
                diffs.append((key, v1, v2, v2 - v1, rel_diff))
        elif v1 != v2:
            diffs.append((key, v1, v2, None, None))

    # --- Print summary ---
    in_ref = ["🔹 Only in reference (missing in second):"]
    in_ref.extend(f"  {k} = {ref[k]}" for k in only_in_ref)

    out_ref = ["\n🔹 Only in second (not in reference):"]
    out_ref.extend(f"  {k} = {new[k]}" for k in only_in_new)

    diff_ref = ["\n🔹 Differences beyond tolerance (relative to reference):"]
    for key, v1, v2, delta, rel in diffs:
        if rel is None:
            diff_ref.append(f"  {key}: '{v1}' != '{v2}'")
        else:
            diff_ref.append(
                f"  {key}: {v1:.6g} → {v2:.6g}  (Δ={delta:.3g}, rel={rel * 100:.3f}%)"
            )

    return {
        "only_in_ref": [only_in_ref, "\n ".join(in_ref)],
        "only_in_new": [only_in_new, "\n ".join(out_ref)],
        "diffs": [diffs, "\n ".join(diff_ref)],
    }


def test_nmm_regression_complex_mixture():
    li_enrich_ao = 0.6
    KALOS_ACB_MAT = make_KALOS_ACB_mat(li_enrich_ao)

    structural_fraction_vo = 0.128
    multiplier_fraction_vo = 0.493  # 0.647
    breeder_fraction_vo = 0.103  # 0.163
    helium_fraction_vo = 0.276  # 0.062

    mat = mixture(
        name="inb_breeder_zone",
        materials=[
            (EUROFER_MAT, structural_fraction_vo),
            (Be12Ti(), multiplier_fraction_vo),
            (KALOS_ACB_MAT, breeder_fraction_vo),
            (HELIUM_MAT, helium_fraction_vo),
        ],
        fraction_type="volume",
        volume_conditions=OperationalConditions(temperature=300, pressure=8e6),
        converters=OpenMCNeutronicConfig(
            material_id=102,
            enrichment=li_enrich_ao * 100,
            enrichment_target="Li6",
            enrichment_type="atomic",
        ),
    )
    mat_card = mat.convert("openmc", {"temperature": 300, "pressure": 1.01325e5})

    comparison = compare_openmc_mat_cards(
        TRUE_OPENMC_MAT_CARD_0_15_2, mat_card, tol=5e-4
    )

    assert len(comparison["only_in_ref"][0]) == 0, comparison["only_in_ref"][1]
    assert len(comparison["only_in_new"][0]) == 0, comparison["only_in_new"][1]
    assert len(comparison["diffs"][0]) == 0, comparison["diffs"][1]
