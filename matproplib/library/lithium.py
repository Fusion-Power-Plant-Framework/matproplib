# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Lithium materials"""

from matproplib.converters.neutronics import OpenMCNeutronicConfig
from matproplib.library.references import FOKKENS_2003
from matproplib.material import dependentphysicalproperty, material
from matproplib.properties.dependent import (
    CoefficientThermalExpansion,
    Density,
    SpecificHeatCapacity,
)
from matproplib.properties.group import props
from matproplib.tools.tools import From1DData

PbLi_eutectic = material(
    "PbLi_eutectic",
    elements={
        "Pb": 0.99283,
        "Li": 0.0062,
        "Ag": 0.00001,
        "Cu": 0.00001,
        "Nb": 0.00001,
        "Pd": 0.00001,
        "Zn": 0.00001,
        "Fe": 0.00005,
        "Cr": 0.00005,
        "Mn": 0.00005,
        "Mo": 0.00005,
        "Ni": 0.00005,
        "V": 0.00005,
        "Si": 0.0001,
        "Al": 0.0001,
        "Bi": 0.0002,
        "Sn": 0.0002,
        "W": 0.00002,
    },
    properties=props(as_field=True, density=10000, poissons_ratio=0.33),
)

# fmt: off
Li4SO4_SHC = From1DData(
    [
        0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800,
        850, 900, 950, 1000
    ],
    [
        1392.4, 1450, 1513.4, 1580, 1648.5, 1718.2, 1788.8, 1859.9, 1931.4,
        2003.3, 2075.3, 2147.5, 2219.8, 2292.3, 2364.8, 2437.4, 2510.1, 2582.8, 2655.5,
        2728.3, 2801.1
    ],
    "temperature",
)


# fmt: on
@dependentphysicalproperty(
    dpp=SpecificHeatCapacity,
    op_cond_config={"temperature": ("degC", 0, 1000)},
    reference=FOKKENS_2003,
)
def Li4SiO4_specific_heat_capacity(op_cond):
    """Specific heat capacity of LiSiO4"""  # noqa: DOC201
    return Li4SO4_SHC(op_cond)


Li4SiO4 = material(
    "Li4SiO4",
    elements="Li4SiO4",
    properties=props(
        as_field=True,
        specific_heat_capacity=Li4SiO4_specific_heat_capacity,
        coefficient_thermal_expansion=CoefficientThermalExpansion(
            value=lambda oc: 0.768 + 4.96e-4 * oc.temperature + 0.045 * oc.strain,
            unit="1e-6/K",
            op_cond_config={"temperature": ("degC", 25, 800)},
            reference={
                "id": "liso4_cte",
                "type": "article",
                "doi": "10.1016/S0920-3796(02)00165-5",
            },
        ),
        density=Density.from_unit_cell(),
    ),
    converters=OpenMCNeutronicConfig(
        volume_of_unit_cell=1.1543e-27,
        atoms_per_unit_cell=14,
        enrichment_target="Li6",
        enrichment_type="atomic",
    ),
)

Li2SiO3 = material(
    "Li2SiO3",
    elements="Li2SiO3",
    converters=OpenMCNeutronicConfig(
        volume_of_unit_cell=0.23632e-27,
        atoms_per_unit_cell=4,
        enrichment_target="Li6",
        enrichment_type="atomic",
    ),
    density=Density.from_unit_cell(),
    reference={
        "id": "liso3_cell",
        "type": "article",
        "doi": "10.1016/j.ssi.2019.02.019",
    },
)

Li2ZrO3 = material(
    "Li2ZrO3",
    elements="Li2ZrO3",
    converters=OpenMCNeutronicConfig(
        volume_of_unit_cell=0.24479e-27,
        atoms_per_unit_cell=4,
        enrichment_target="Li6",
        enrichment_type="atomic",
    ),
    density=Density.from_unit_cell(),
)

Li2TiO3 = material(
    "Li2TiO3",
    elements="Li2TiO3",
    converters=OpenMCNeutronicConfig(
        volume_of_unit_cell=0.42701e-27,
        atoms_per_unit_cell=8,
        enrichment_target="Li6",
        enrichment_type="atomic",
    ),
    density=Density.from_unit_cell(),
)
