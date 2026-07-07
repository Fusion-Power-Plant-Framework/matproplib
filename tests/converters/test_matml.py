# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from matproplib.converters.matml import MatML
from matproplib.material import material

simple_xml = """<?xml version="1.0" encoding="UTF-8"?>
<MatMLXML>
  <Material id="1">
    <BulkDetails>
      <Name>Simple</Name>
      <Characterization>
        <Formula>H2O</Formula>
        <ChemicalComposition>
          <Element>
            <Symbol subscript="2">H</Symbol>
          </Element>
          <Element>
            <Symbol subscript="1">O</Symbol>
          </Element>
        </ChemicalComposition>
      </Characterization>
      <PropertyData property="pr01" delimiter=",">
        <Data format="string">-</Data>
        <ParameterValue parameter="pa01" format="float">
          <Data>1</Data>
          <Qualifier>Dependent</Qualifier>
        </ParameterValue>
      </PropertyData>
      <PropertyData property="pr02" delimiter=",">
        <Data format="string">-</Data>
        <ParameterValue parameter="pa02" format="float">
          <Data>0.3</Data>
          <Qualifier>Dependent</Qualifier>
        </ParameterValue>
      </PropertyData>
    </BulkDetails>
  </Material>
  <Metadata>
    <ParameterDetails id="pa01">
      <Name>density</Name>
      <Units system="SI">
        <Unit power="1.0">
          <Name>kg</Name>
        </Unit>
        <Unit power="-3.0">
          <Name>m</Name>
        </Unit>
      </Units>
    </ParameterDetails>
    <ParameterDetails id="pa02">
      <Name>poissons_ratio</Name>
      <Unitless/>
    </ParameterDetails>
    <PropertyDetails id="pr01">
      <Name>density</Name>
      <Unitless/>
    </PropertyDetails>
    <PropertyDetails id="pr02">
      <Name>poissons_ratio</Name>
      <Unitless/>
    </PropertyDetails>
  </Metadata>
</MatMLXML>
"""


class TestMatML:
    def test_material_export(self, condition):
        Simple = material(
            "Simple",
            "H2O",
            properties={"density": 1, "poissons_ratio": 0.3},
            converters=MatML(),
        )

        simple = Simple()

        with patch("matproplib.tools.matml.matml.material_id", return_value="1"):
            matmlxml = simple.convert("matml", condition)

        with patch("builtins.open", new_callable=mock_open) as mo:
            matmlxml.export("filename.xml")

        assert "".join(c[1][0] for c in mo.mock_calls[2:-1]) == simple_xml

    @pytest.mark.parametrize(
        ("file", "quantities"),
        [(Path(Path(__file__), "../../../water.xml").resolve(), [("density", 998.2)])],
    )
    def test_full_material_import(self, file, quantities, condition):
        NewMaterial = MatML.import_from(file)

        mat = NewMaterial()

        for q_n, qv in quantities:
            assert getattr(mat, q_n)(condition) == pytest.approx(qv)
