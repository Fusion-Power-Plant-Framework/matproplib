# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Concrete materials"""

from matproplib.converters.neutronics import OpenMCNeutronicConfig
from matproplib.library.references import PNNL_COMPENDIUM
from matproplib.material import material
from matproplib.properties.group import props

__all__ = ["Concrete", "HeavyConcrete", "OrdinaryConcrete"]

Concrete = material(
    "Concrete [Los Alamos (MCNP) Mix]",
    elements={
        "H": 0.004530,
        "O": 0.512600,
        "Si": 0.360360,
        "Al": 0.035550,
        "Na": 0.015270,
        "Ca": 0.057910,
        "Fe": 0.013780,
    },
    properties=props(as_field=True, density=2250),
    converters=OpenMCNeutronicConfig(),
    reference=PNNL_COMPENDIUM,
)

OrdinaryConcrete = material(
    "Concrete, Ordinary (NBS 03)",
    elements={
        "H": 0.008485,
        "C": 0.050064,
        "O": 0.473483,
        "Mg": 0.024183,
        "Al": 0.036063,
        "Si": 0.145100,
        "S": 0.002970,
        "K": 0.001697,
        "Ca": 0.246924,
        "Fe": 0.011031,
    },
    properties=props(as_field=True, density=2350),
    converters=OpenMCNeutronicConfig(),
    reference=PNNL_COMPENDIUM,
)
HeavyConcrete = material(
    "Concrete, Magnetite",
    elements={
        "H": 0.003113,
        "O": 0.330504,
        "Mg": 0.009338,
        "Al": 0.023486,
        "Si": 0.025750,
        "S": 0.001415,
        "Ca": 0.071024,
        "Ti": 0.054329,
        "V": 0.003113,
        "Cr": 0.001698,
        "Mn": 0.001981,
        "Fe": 0.474250,
    },
    properties=props(as_field=True, density=3530),
    converters=OpenMCNeutronicConfig(),
    reference=PNNL_COMPENDIUM,
)
