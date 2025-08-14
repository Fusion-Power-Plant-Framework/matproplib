# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""
The matproplib package provides an interface for material properties.

The main aim of this package is to unite structural, thermal, electro-magnetic
and neutronics properties under one interface.
"""

import logging

from matproplib.conditions import OperationalConditions, STPConditions
from matproplib.material import Material, material
from matproplib.properties.group import props
from matproplib.properties.independent import pp

__all__ = [
    "Material",
    "OperationalConditions",
    "STPConditions",
    "material",
    "pp",
    "props",
]

logging.basicConfig()
logger = logging.getLogger("matproplib")
logger.setLevel(logging.INFO)
