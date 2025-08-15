# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Polymer materials"""

from pydantic import Field

from matproplib.base import rebuild
from matproplib.material import FullMaterial, PropertiesT_co
from matproplib.nucleides import Elements
from matproplib.properties.group import props


@rebuild
class EpoxyResin(FullMaterial):
    """Epoxy resin"""

    name: str = Field(default="EpoxyResin")
    elements: Elements = Field(
        default={
            "Al": 0.0007074,
            "C": 0.0034056,
            "H": 0.0038934,
            "Mg": 0.0002142004,
            "N": 0.0003708,
            "O": 0.0048708,
            "S": 9.179996e-5,
            "Si": 0.0058552,
        },
    )
    properties: PropertiesT_co = props(
        as_field=True,
        density=1207,
        youngs_modulus={
            "value": 7.5,
            "unit": "GPa",
            "reference": {
                "id": "ym_epoxy",
                "type": "webpage",
                "doi": "10.1109/20.511486",
                "url": r"https://ncsx.pppl.gov/NCSX_Engineering/ModCoil_TF-Coil_VVSA_Fab/TF%20Coil%20Fabrication/Insulation%20Systems/Coil%20Papers%20from%20Neumeyer/Mech_Prop_Solenoids.pdf",
            },
        },
        poissons_ratio=0.33,
    )
