# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""matproplib matml converter"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from matproplib.converters.base import Converter
from matproplib.tools.matml import MatMLXML

if TYPE_CHECKING:
    from matproplib.conditions import OperationalConditions
    from matproplib.material import Material


class MatML(Converter):
    name: ClassVar[Literal["matml"]] = "matml"

    _xml_model: MatMLXML | None = None

    def convert(
        self, material: Material, op_cond: OperationalConditions
    ) -> MatMLXML: ...

    @classmethod
    def import_from(cls, filename: str, *, material_cls: type[Material]) -> Material:
        matmlxml = MatMLXML.from_file(filename)
        # ChemicalComposition element -> Elements
        #                     Compounds -> mixtures
        # BulkDetails PropertyData -> dpp
        # Metadata PropertyDetails (units) -> dpp
