# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""
The physical-materials package provides an interface for material properties.

The main aim of this package is to unite structural, thermal, electro-magnetic
and neutronics properties under one interface.
"""

import logging

from physical_materials.conditions import OperationalConditions, STPConditions
from physical_materials.material import Material, material
from physical_materials.properties.group import props
from physical_materials.properties.independent import pp

__all__ = [
    "Material",
    "OperationalConditions",
    "STPConditions",
    "material",
    "pp",
    "props",
]

logging.basicConfig()
logger = logging.getLogger("physical_materials")
logger.setLevel(logging.INFO)
