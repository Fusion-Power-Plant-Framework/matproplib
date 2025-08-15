# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Fluid materials"""

from CoolProp.CoolProp import PropsSI
from pydantic import Field

from matproplib.converters.base import Converters
from matproplib.converters.neutronics import OpenMCNeutronicConfig
from matproplib.material import FullMaterial, material
from matproplib.nucleides import Elements
from matproplib.properties.dependent import Density
from matproplib.properties.group import props


class Void(FullMaterial):
    """Material for a void, very low hydrogen concentration"""

    name: str = Field(default="Void")
    elements: Elements = Field(default=["H"], frozen=True)
    density: Density = Field(
        default=Density.from_nuclear_units({"H": 1}, 1),
        frozen=True,
    )
    converters: Converters = Field(
        default_factory=lambda: OpenMCNeutronicConfig(
            percent_type="atomic",
        )
    )


DTPlasma = material(
    "DTPlasma",
    elements={"H2": 0.5, "H3": 0.5},
    properties=props(
        as_field=True,
        density=Density(value=1e-6, unit="g/cm^3"),
        youngs_modulus=0,
        poissons_ratio=0,
    ),
    converters=OpenMCNeutronicConfig(),
)

DDPlasma = material(
    "DDPlasma",
    elements={"H2": 1},
    properties=props(
        as_field=True,
        density=Density(value=1e-6, unit="g/cm^3"),
        youngs_modulus=0,
        poissons_ratio=0,
    ),
    converters=OpenMCNeutronicConfig(),
)

H2O = material(
    "H2O",
    elements="H2O",
    properties=props(
        as_field=True,
        density=Density(
            value=lambda oc: PropsSI(
                "D", "T", oc.temperature.value, "P", oc.pressure.value, "Water"
            ),
            op_cond_config={"temperature": ("K", 273.153)},
        ),
        youngs_modulus=0,
        poissons_ratio=0,
    ),
)

He = material(
    "He",
    elements="He",
    properties=props(
        as_field=True,
        density=Density(
            value=lambda oc: PropsSI(
                "D", "T", oc.temperature, "P", oc.pressure, "Helium"
            ),
            op_cond_config={"temperature": ("K", 1.58842)},
        ),
        youngs_modulus=0,
        poissons_ratio=0,
    ),
)
