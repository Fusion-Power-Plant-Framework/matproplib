# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Concrete materials"""

from matproplib.converters.neutronics import OpenMCNeutronicConfig
from matproplib.material import material
from matproplib.properties.group import props

__all__ = ["Concrete", "HeavyConcrete", "OrdinaryConcrete"]

Concrete = material(
    "Concrete",
    elements={
        "H": 0.00453,
        "O": 0.5126,
        "Na": 0.01527,
        "Al": 0.03555,
        "Si": 0.36036,
        "Ca": 0.05791,
        "Fe": 0.01378,
    },
    properties=props(as_field=True, density=2250, poissons_ratio=0.33),
    converters=OpenMCNeutronicConfig(),
)

OrdinaryConcrete = material(
    "OrdinaryConcrete",
    elements={
        "H": 0.0055,
        "O": 0.4975,
        "Si": 0.3147,
        "Ca": 0.0828,
        "Mg": 0.0026,
        "Al": 0.0469,
        "S": 0.0013,
        "Fe": 0.0124,
        "Na": 0.0171,
        "K": 0.0192,
    },
    properties=props(as_field=True, density=2200, poissons_ratio=0.33),
    converters=OpenMCNeutronicConfig(),
)
HeavyConcrete = material(
    "HeavyConcrete",
    elements={
        "H": 0.0052,
        "O": 0.3273,
        "C": 0.004,
        "Si": 0.0224,
        "Ca": 0.0657,
        "Mg": 0.0021,
        "Al": 0.0038,
        "Fe": 0.568,
        "P": 0.0015,
    },
    properties=props(as_field=True, density=3600, poissons_ratio=0.33),
    converters=OpenMCNeutronicConfig(),
)
