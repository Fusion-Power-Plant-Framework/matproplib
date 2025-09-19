# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""matproplib matml model"""

from __future__ import annotations

from collections import Counter
from typing import Literal

from lxml import etree
from pydantic import BaseModel, ConfigDict, model_validator
from xsdata_pydantic.bindings import XmlParser, XmlSerializer
from xsdata_pydantic.fields import field

from matproplib.tools.matml.matml_enums import (
    ChemicalElementSymbol,  # noqa: TC001
    CurrencyCode,  # noqa: TC001
    DataFormat,  # noqa: TC001
    UncertaintyScale,  # noqa: TC001
)


class MatMLBase(BaseModel):
    """MatML base model"""

    model_config = ConfigDict(defer_build=True)


t_attr: dict[Literal["type"], Literal["Attribute"]] = {"type": "Attribute"}
t_element: dict[Literal["type"], Literal["Element"]] = {"type": "Element"}
req: dict[Literal["required"], bool] = {"required": True}
n_name: dict[Literal["name"], Literal["Name"]] = {"name": "Name"}
n_note: dict[Literal["name"], Literal["Notes"]] = {"name": "Notes"}


class AssociationDetails(MatMLBase):
    """
    Description of a relationship of the component to another
    component in a complex material system such as a composite, weld, or
    multilayer material.

    Parameters
    ----------
    associate:
        Name of a component's associate. For example,
        a TiC coating has been placed on AISI 1018 steel coupons. The
        Associate of the steel, then, is the "titanium carbide coating."
    notes:
        additional information concerning the association.
    relationship:
        relationship between acomponent and the associate. For example the relationship
        of a steel to a titanium carbide coating is that the steel is the
        substrate for the coating.

    """

    associate: str | None = field(
        default=None, metadata={"name": "Associate"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)
    relationship: str | None = field(
        default=None, metadata={"name": "Relationship"} | t_element
    )


class Geometry(MatMLBase):
    """
    Description of the geometry of the bulk material, component or
    specimen.

    Parameters
    ----------
    shape:
         The shape of the bulk material or component
    dimensions:
        The dimensions of the bulk material or component
    orientation:
        The orientation of the bulk material or component
    notes:
        additional information concerning the geometry
    """

    shape: str = field(metadata={"name": "Shape"} | req | t_element)
    dimensions: str | None = field(
        default=None, metadata={"name": "Dimensions"} | t_element
    )
    orientation: str | None = field(
        default=None, metadata={"name": "Orientation"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)


class Graphs(MatMLBase):
    """
    Graphs of the material

    Notes
    -----
    Graph uses the W3C's SVGs see: http://www.w3.org/TR/SVG/.
    """

    graph: list[Graphs.Graph] = field(
        default_factory=list, metadata={"name": "Graph", "min_occurs": 1} | t_element
    )

    class Graph(MatMLBase):
        """Graph element"""

        w3_org_2000_svg_element: list[object] = field(
            default_factory=list,
            metadata={"type": "Wildcard", "namespace": "http://www.w3.org/2000/svg"},
        )


class Name(MatMLBase):
    """
    Material name

    Parameters
    ----------
    name:
        the name
    authority:
        for identifying an authoritative source of names in this context
    """

    value: str = field(default="", metadata=req)
    authority: str | None = field(default=None, metadata=t_attr)


class Source(MatMLBase):
    """
    Source of material

    Parameters
    ----------
    source:
        a name representing the source of the bulk material or component
    """

    source: str | None = field(default=None, metadata=t_attr)


class Specification(MatMLBase):
    """
    The specification for the bulk material and its authoritative source.
    """

    value: str = field(default="", metadata=req)
    authority: str | None = field(default=None, metadata=t_attr)


class AuthorityDetails(MatMLBase):
    """
    A description of an authority referenced by other elements.

    An authority is typically an organisation that is the authoritative
    source of information about the element that is referencing it.

    Parameters
    ----------
    id:
        A unique id for the authority
    name:
        authority name
    notes:
        Any additional information about the authority
    """

    name: Name = field(metadata=n_name | req | t_element)
    notes: str | None = field(default=None, metadata=n_note | t_element)
    id: str = field(metadata=t_attr | req)


class Class(MatMLBase):
    """
    Material Class (categorisation)

    Parameters
    ----------
    name:
        class name
    parent_material:
        id reference to another material
    """

    name: Name | None = field(default=None, metadata=n_name | t_element)
    parent_material: list[Class.ParentMaterial] = field(
        default_factory=list, metadata={"name": "ParentMaterial"} | t_element
    )
    parent_sub_class: list[Class] = field(
        default_factory=list, metadata={"name": "ParentSubClass"} | t_element
    )

    class ParentMaterial(MatMLBase):
        """Parent material"""

        id: str = field(metadata=t_attr | req)


class DataSourceDetails(MatMLBase):
    """
    A description of a data source referenced by the PropertyData
    element.

    Parameters
    ----------
    name:
        The name of the data source
    notes:
        Any additional information concerning the data source
    id:
        unique data source id
    type_value:
        for specifying the type of the data source
        (examples include "unpublished report," "journal," "handbook," etc.)
    """

    name: Name = field(metadata=n_name | req | t_element)
    notes: str | None = field(default=None, metadata=n_note | t_element)
    id: str = field(metadata=t_attr | req)
    type_value: str | None = field(default=None, metadata={"name": "type"} | t_attr)


class Form(MatMLBase):
    """
    Form of the material


    Parameters
    ----------
    description:
        description of the form
    geometry:
        Geometry of the form
    notes:
        Any additional information concerning the form
    """

    description: Name = field(metadata={"name": "Description"} | req | t_element)
    geometry: Geometry | None = field(
        default=None, metadata={"name": "Geometry"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)


class GlossaryTerm(MatMLBase):
    """
    Descriptions of material and property terms used in the document

    Parameters
    ----------
    name:
        The name of the term
    definition:
        The term's definition and must occur once and only
    abbreviation:
        Abbreviation of the term
    synonym:
        Synonym of the terms
    notes:
        Any additional information concerning the glossary term
    """

    name: Name = field(metadata=n_name | req | t_element)
    definition: str = field(metadata={"name": "Definition"} | req | t_element)
    abbreviation: list[str] = field(
        default_factory=list, metadata={"name": "Abbreviation"} | t_element
    )
    synonym: list[str] = field(
        default_factory=list, metadata={"name": "Synonym"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)


class MeasurementTechniqueDetails(MatMLBase):
    """
    A description of a measurement technique referenced by
    the PropertyData element.

    Parameters
    ----------
    name:
        The name of the technique
    notes:
        Any additional information concerning the measurement technique
    id:
        A unique ID for the technique
    """

    name: Name = field(metadata=n_name | req | t_element)
    notes: str | None = field(default=None, metadata=n_note | t_element)
    id: str = field(metadata=t_attr | req)


class SourceDetails(MatMLBase):
    """
    Source details

    Parameters
    ----------
    name:
        the name of the source of the component
    notes:
        Any additional information concerning the data source
    id:
        Unique ID of the source
    type_value:
        type of the source
    """

    name: Name = field(metadata=n_name | req | t_element)
    notes: str | None = field(default=None, metadata=n_note | t_element)
    id: str = field(metadata=t_attr | req)
    type_value: str | None = field(default=None, metadata={"name": "type"} | t_attr)


class SpecimenDetails(MatMLBase):
    """
    A description of a specimen referenced by the PropertyData
    element.

    Parameters
    ----------
    name:
        name of the specimen detail
    id:
        Unique ID of the specimen details
    notes:
        Any additional information concerning the specimen
    geometry:
        geometry of the specimen
    type_value:
        type of the specimen (eg
       cylindrical" "rectangular" "full cross-section" "pressed" etc)

    """

    name: Name | None = field(default=None, metadata=n_name | t_element)
    notes: str | None = field(default=None, metadata=n_note | t_element)
    geometry: Geometry | None = field(
        default=None, metadata={"name": "Geometry"} | t_element
    )
    id: str = field(metadata=t_attr | req)
    type_value: str | None = field(default=None, metadata={"name": "type"} | t_attr)


class Value(MatMLBase):
    """
    Value of an object and the value format
    """

    value: str = field(default="", metadata=req)
    format: DataFormat = field(metadata=t_attr | req)


class Glossary(MatMLBase):
    """
    A list of glossary entries
    """

    term: list[GlossaryTerm] = field(
        default_factory=list,
        metadata={"name": "Term", "min_occurs": 1} | t_element,
    )


class Unitless(MatMLBase):
    """
    An empty element used whenever am object value has no units.
    """


class Unit(MatMLBase):
    """
    A matml unit

    Parameters
    ----------
    name:
        unit name
    currency:
        The CurrencyCode for the unit, if it is a unit expressing
        cost in an ISO 4217 recognised currency.
    power:
        The exponent for Unit.
    description:
        unit description
    """

    name: str | None = field(default=None, metadata=n_name | t_element)
    currency: CurrencyCode | None = field(
        default=None, metadata={"name": "Currency"} | t_element
    )
    power: float | None = field(default=None, metadata=t_attr)
    description: str | None = field(default=None, metadata=t_attr)


class Units(MatMLBase):
    """
    Units

    Parameters
    ----------
    unit:
        list of constituent units
    system:
        Units system eg 'SI'
    factor:
        constant multiplier
    name:
        Name of the unit
    description:
        description of the units

    Notes
    -----
    Multiple Unit elements are multiplied together to form the
    units. Division is specified by using setting the power
    attribute of Unit equal to "-1."
    """

    unit: list[Unit] = field(
        default_factory=list,
        metadata={"name": "Unit", "min_occurs": 1} | t_element,
    )
    system: str | None = field(default=None, metadata=t_attr)
    factor: float | None = field(default=None, metadata=t_attr)
    name: str | None = field(default=None, metadata=t_attr)
    description: str | None = field(default=None, metadata=t_attr)


class ParameterDetails(MatMLBase):
    """
    A description of a parameter referenced by the ParameterValue
    element.

    Parameters
    ----------
    id:
        Unique ID for the parameter details
    name:
        name of the parameter
    units:
        units of the parameter
    unitless:
        if there are no units for a paramter this should be set
    notes:
        Any additional information about the parameter
    """

    name: Name = field(metadata=n_name | req | t_element)
    units: Units | None = field(default=None, metadata={"name": "Units"} | t_element)
    unitless: Unitless | None = field(
        default=None, metadata={"name": "Unitless"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)
    id: str = field(metadata=t_attr | req)


class PropertyDetails(MatMLBase):
    """
    A description of a property referenced by the PropertyData
    element.

    Parameters
    ----------
    id:
        Unique ID of the property detail
    type_value:
        Specifying the type of the property (eg  "thermal" "mechanical" "electrical" etc)
    name:
        name of the property
    units:
        units of the property
    unitless:
        if there are no units for a paramter this should be set
    notes:
        Any additional information concerning the property
    """

    name: Name = field(metadata=n_name | req | t_element)
    units: Units | None = field(default=None, metadata={"name": "Units"} | t_element)
    unitless: Unitless | None = field(
        default=None, metadata={"name": "Unitless"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)
    id: str = field(metadata=t_attr | req)
    type_value: str | None = field(default=None, metadata={"name": "type"} | t_attr)


class Uncertainty(MatMLBase):
    """
    A description of the measurement uncertainty of the data.

    Parameters
    ----------
    distribution_type:
        A description of the nature of the uncertainty value, for example
        '6 sigma', 'Gaussian' or '2 std dev.'
    value:
        the value of the uncertainty
    units:
        units of the property
    unitless:
        if there are no units for a paramter this should be set
    percentile:
        the percentage of the data population that have values less than or equal
        to the Uncertainty value.
    num_std_dev:
        An uncertainty of 2 standard deviations below the mean for a
        normally distributed dataset would have a uncertainty percentile of 5%,
        and 2 standard deviations above the mean would be 95%
    notes:
        Any additional information concerning the uncertainty,
    """

    value: Value = field(metadata={"name": "Value"} | req | t_element)
    units: Units | None = field(default=None, metadata={"name": "Units"} | t_element)
    unitless: Unitless | None = field(
        default=None, metadata={"name": "Unitless"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)
    scale: UncertaintyScale | None = field(
        default=None, metadata={"name": "Scale"} | t_element
    )
    distribution_type: str = field(
        default="Normal/Gaussian", metadata={"name": "DistributionType"} | t_attr
    )
    num_std_dev: float = field(default=2.0, metadata={"name": "Num_Std_Dev"} | t_attr)
    percentile: float | None = field(
        default=None, metadata={"name": "Percentile"} | t_attr
    )
    confidence_level: float | None = field(
        default=None, metadata={"name": "ConfidenceLevel"} | t_attr
    )


class Concentration(MatMLBase):
    """
    Model for Concentration

    Parameters
    ----------
    value:
        the concentration value
    units:
        the units for the value of the concentration
    qualifier:
        Any qualifier pertinent to the value of the concentration
        (e.g. "min," "max," etc.)
    uncertainty:
        the measurement uncertainty(ies) of the data
    notes:
        Any additional information concerning the concentration
    """

    value: Value = field(metadata={"name": "Value"} | req | t_element)
    units: Units = field(metadata={"name": "Units"} | req | t_element)
    qualifier: list[str] = field(
        default_factory=list, metadata={"name": "Qualifier"} | t_element
    )
    uncertainty: list[Uncertainty] = field(
        default_factory=list, metadata={"name": "Uncertainty"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)


class DimensionalDetails(MatMLBase):
    """
    A description of a dimensional characteristic (e.g. grain size,
    porosity, precipitate size and distribution, etc.) of the bulk material or
    component.

    Parameters
    ----------
    name:
        name of the characteristic
    value:
        value of the characteristic
    units:
        the units for the value of the concentration
    qualifier:
        Any qualifier pertinent to the value of the dimensional
        characteristic (e.g. "min" "max" etc)
    uncertainty:
        the measurement uncertainty(ies) of the data
    notes:
        Any additional information concerning the dimensional characteristic
    """

    name: Name = field(metadata=n_name | req | t_element)
    value: Value = field(metadata={"name": "Value"} | req | t_element)
    units: Units = field(metadata={"name": "Units"} | req | t_element)
    qualifier: str | None = field(
        default=None, metadata={"name": "Qualifier"} | t_element
    )
    uncertainty: list[Uncertainty] = field(
        default_factory=list, metadata={"name": "Uncertainty"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)


class ParameterValue(MatMLBase):
    """
    The value of a parameter.

    Parameters
    ----------
    parameter:
        A unique ID referenced in the ParameterDetails element
    format:
        The format of the value. If 'mixed' used, then the "format" attribute on each
        "Data" item should be individually set.
    data:
        the property data
    qualifier:
        Any qualifier(s) pertinent to the data in ParameterValue (e.g. "min," "max," etc)
    uncentainty:
        the measurement uncertainty(ies) of the data in ParameterValue
    notes:
        Any additional information concerning the property data
    """

    data: ParameterValue.Data = field(metadata={"name": "Data"} | req | t_element)
    uncertainty: list[Uncertainty] = field(
        default_factory=list, metadata={"name": "Uncertainty"} | t_element
    )
    qualifier: list[str] = field(
        default_factory=list, metadata={"name": "Qualifier"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)
    parameter: str = field(metadata=t_attr | req)
    format: DataFormat = field(metadata=t_attr | req)

    class Data(MatMLBase):
        """Parameter value data"""

        value: str = field(default="", metadata=req)
        format: DataFormat | None = field(default=None, metadata=t_attr)


class Element(MatMLBase):
    """
    Model for Element

    Parameters
    ----------
    symbol:
        element symbol
    concentration:
        Contains the concentration of the element
    notes:
        Any additional information concerning the element
    """

    symbol: Element.Symbol = field(metadata={"name": "Symbol"} | req | t_element)
    concentration: Concentration | None = field(
        default=None, metadata={"name": "Concentration"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)

    class Symbol(MatMLBase):
        """
        Element Symbol with subscript
        """

        value: ChemicalElementSymbol = field(metadata=req)
        subscript: str = field(default="1", metadata=t_attr)


class ProcessingDetails(MatMLBase):
    """
    A description of a processing step for the bulk material or
    component.

    Parameters
    ----------
    name:
        The name of the processing step
    parameter_value:
        the value of the parameter of the processing step
    result:
        description of the processing step results
    notes:
        Any additional information concerning the processing step
    """

    name: Name = field(metadata=n_name | req | t_element)
    parameter_value: list[ParameterValue] = field(
        default_factory=list, metadata={"name": "ParameterValue"} | t_element
    )
    result: str | None = field(default=None, metadata={"name": "Result"} | t_element)
    notes: str | None = field(default=None, metadata=n_note | t_element)


class PropertyData(MatMLBase):
    """
    PropertyData

    Parameters
    ----------
    data:
        the data of the property
    uncertainty:
        the measurement uncertainty(ies) of the data
    qualifier:
        Any qualifier(s) pertinent to the data (e.g. "min," "max," etc.)
    parameter_value:
        The value(s) of a parameter under which the data were determined
    notes:
        Any additional information concerning the property data
    property:
        ID that links PropertyData to PropertyDetails
    technique:
        ID that references the MeasurementTechniqueDetails
    source:
        ID that links the property data to the DataSourceDetails
    specimen:
        ID that links to SpecimenDetails
    test:
        ID that links to TestConditionDetails
    delimiter:
        Separator for multiple values in
        [Data, Qualifier, Uncertainty, and ParameterValue]
    quote:
        Quotes values in [Data, Qualifier, Uncertainty, and ParameterValue]

    Notes
    -----
    Multiple entries in the Data, Qualifier, Uncertainty Value, and
    ParameterValue elements must of equal length.
    """

    data: PropertyData.Data = field(metadata={"name": "Data"} | req | t_element)
    uncertainty: list[Uncertainty] = field(
        default_factory=list, metadata={"name": "Uncertainty"} | t_element
    )
    qualifier: list[str] = field(
        default_factory=list, metadata={"name": "Qualifier"} | t_element
    )
    parameter_value: list[ParameterValue] = field(
        default_factory=list, metadata={"name": "ParameterValue"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)
    property: str = field(metadata=t_attr | req)
    technique: str | None = field(default=None, metadata=t_attr)
    source: str | None = field(default=None, metadata=t_attr)
    specimen: str | None = field(default=None, metadata=t_attr)
    test: str | None = field(default=None, metadata=t_attr)
    delimiter: str = field(
        default=",",
        metadata={"type": "Attribute", "min_length": 1, "white_space": "preserve"},
    )
    quote: str | None = field(default=None, metadata=t_attr)

    class Data(MatMLBase):
        """PropertyData data values"""

        value: str = field(default="", metadata=req)
        format: DataFormat = field(metadata=t_attr | req)

    @model_validator(mode="after")
    def _qualifier_validation(self):
        if len(self.qualifier) == 1:
            self.qualifier = self.qualifier[0].split(self.delimiter)

        for p in self.parameter_value:
            if len(p.qualifier) == 1:
                p.qualifier = p.qualifier[0].split(self.delimiter)
        return self


class ConditionTestDetails(MatMLBase):
    """
    A description of the test conditions referenced by the
    PropertyData element.

    Parameters
    ----------
    id:
        Unique ID of the test condition
    parameter_value:
        the condition tested
    notes:
        Any additional information concerning the test conditions
    """

    parameter_value: list[ParameterValue] = field(
        default_factory=list, metadata={"name": "ParameterValue"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)
    id: str = field(metadata=t_attr | req)


class Compound(MatMLBase):
    """
    Compound details

    Parameters
    ----------
    element:
        a list of chemical elements
    concentration:
        The concentration of the compound
    notes:
        any additional information concerning the compound
    """

    element: list[Element] = field(
        default_factory=list,
        metadata={"name": "Element", "min_occurs": 1} | t_element,
    )
    concentration: Concentration | None = field(
        default=None, metadata={"name": "Concentration"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)


class Metadata(MatMLBase):
    """
    Descriptions of authorities, data sources, measurement techniques,
    parameters, properties, material and component sources, specimens, and
    test conditions.

    Parameters
    ----------
    authority_details
        description of authority
    data_source_details:
        A description of deta source
    measurement_technique_details:
        A description of measurement techniques
    parameter_details:
        A description of a parameter referenced in PropertyData
    property_details:
        A description of a property referenced in PropertyData
    source_details:
        A description of the source of a material or component
    specimen_details:
        A description of a specimen referenced using in PropertyData
    test_condition_details:
        A list of the test condtions referenced using the PropertyData
    """

    authority_details: list[AuthorityDetails] = field(
        default_factory=list, metadata={"name": "AuthorityDetails"} | t_element
    )
    data_source_details: list[DataSourceDetails] = field(
        default_factory=list, metadata={"name": "DataSourceDetails"} | t_element
    )
    measurement_technique_details: list[MeasurementTechniqueDetails] = field(
        default_factory=list,
        metadata={"name": "MeasurementTechniqueDetails"} | t_element,
    )
    parameter_details: list[ParameterDetails] = field(
        default_factory=list, metadata={"name": "ParameterDetails"} | t_element
    )
    property_details: list[PropertyDetails] = field(
        default_factory=list, metadata={"name": "PropertyDetails"} | t_element
    )
    source_details: list[SourceDetails] = field(
        default_factory=list, metadata={"name": "SourceDetails"} | t_element
    )
    specimen_details: list[SpecimenDetails] = field(
        default_factory=list, metadata={"name": "SpecimenDetails"} | t_element
    )
    test_condition_details: list[ConditionTestDetails] = field(
        default_factory=list,
        metadata={"name": "TestConditionDetails"} | t_element,
    )


class PhaseComposition(MatMLBase):
    """
    Phase composition

    Parameters
    ----------
    name:
        Name of the phase
    concentration:
        concentration of the phase
    property_data:
        Property data for the phase
    notes:
        Any additional information concerning the phase
    """

    name: Name = field(metadata=n_name | req | t_element)
    concentration: Concentration | None = field(
        default=None, metadata={"name": "Concentration"} | t_element
    )
    property_data: list[PropertyData] = field(
        default_factory=list, metadata={"name": "PropertyData"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)


class ChemicalComposition(MatMLBase):
    """
    Chemical composition of material.

    Parameters
    ----------
    compound:
        description of a compound
    element:
        description of an element.
    """

    compound: list[Compound] = field(
        default_factory=list, metadata={"name": "Compound"} | t_element
    )
    element: list[Element] = field(
        default_factory=list, metadata={"name": "Element"} | t_element
    )


class Characterisation(MatMLBase):
    """
    A description of the chemical composition of the bulk material
    or component and is composed of the following elements.

    Parameters
    ----------
    formula:
        A string representation of the chemical formula
    chemical_composition:
        A description of the compounds and elements
    phase_composition:
        A description of the phases
    notes:
        Any additional information concerning the characterisation
    dimensional_details:
        Information about dimensional characteristics such as grain size, porosity,
        precipitate size and distribution, etc.,
    """

    formula: str = field(metadata={"name": "Formula"} | req | t_element)
    chemical_composition: ChemicalComposition | None = field(
        default=None, metadata={"name": "ChemicalComposition"} | t_element
    )
    phase_composition: list[PhaseComposition] = field(
        default_factory=list, metadata={"name": "PhaseComposition"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)
    dimensional_details: list[DimensionalDetails] = field(
        default_factory=list, metadata={"name": "DimensionalDetails"} | t_element
    )


class BulkDetails(MatMLBase):
    """
    Material bulk details

    Parameters
    ----------
    name:
        name of the material
    class:
        list of classes of the material
    subclass:
        list of subclasses of the material
    specification:
        list of specifications of the material
    source:
        contains the name of the source of the material
    form:
        The form of the material
    processing_details:
        list of descriptions of processing steps for the material
    characterisation:
        The characterisation of the material, including the formula,
        chemical composition, phase composition, and dimensional details.
    property_data:
        list of property data for the material
    notes:
        Any additional information concerning the bulk material
    """

    name: Name = field(metadata=n_name | req | t_element)
    class_value: list[Class] = field(
        default_factory=list, metadata={"name": "Class"} | t_element
    )
    subclass: list[Class] = field(
        default_factory=list, metadata={"name": "Subclass"} | t_element
    )
    specification: list[Specification] = field(
        default_factory=list, metadata={"name": "Specification"} | t_element
    )
    source: Source | None = field(default=None, metadata={"name": "Source"} | t_element)
    form: Form | None = field(default=None, metadata={"name": "Form"} | t_element)
    processing_details: list[ProcessingDetails] = field(
        default_factory=list, metadata={"name": "ProcessingDetails"} | t_element
    )
    characterisation: Characterisation | None = field(
        default=None, metadata={"name": "Characterization"} | t_element
    )
    property_data: list[PropertyData] = field(
        default_factory=list, metadata={"name": "PropertyData"} | t_element
    )
    notes: str | None = field(default=None, metadata=n_note | t_element)


class ComponentDetails(MatMLBase):
    """
    A Component of the bulk material

    Paramters
    ---------
    name:
        component name
    class:
        list of component classes
    subclass:
        list of component subclasses
    specification:
        list of specifications
    souce:
        source information
    form:
        the form of the component
    processing_details:
        list of processing steps on component
    characterisation:
        The formula, chemical composition, phase composition, and
        dimensional details
    property_data:
        property data for the component
    association_details:
        Description of a relationship to other components
    component_details:
        list of sub component details
    id:
        identifier  useful for complex systems such as composite laminates.
    """

    name: Name = field(metadata=n_name | req | t_element)
    class_value: list[Class] = field(
        default_factory=list, metadata={"name": "Class"} | t_element
    )
    subclass: list[Class] = field(
        default_factory=list, metadata={"name": "Subclass"} | t_element
    )
    specification: list[Specification] = field(
        default_factory=list, metadata={"name": "Specification"} | t_element
    )
    source: Source | None = field(default=None, metadata={"name": "Source"} | t_element)
    form: Form | None = field(default=None, metadata={"name": "Form"} | t_element)
    processing_details: list[ProcessingDetails] = field(
        default_factory=list, metadata={"name": "ProcessingDetails"} | t_element
    )
    characterisation: Characterisation | None = field(
        default=None, metadata={"name": "Characterisation"} | t_element
    )
    property_data: list[PropertyData] = field(
        default_factory=list, metadata={"name": "PropertyData"} | t_element
    )
    association_details: list[AssociationDetails] = field(
        default_factory=list, metadata={"name": "AssociationDetails"} | t_element
    )
    component_details: list[ComponentDetails] = field(
        default_factory=list, metadata={"name": "ComponentDetails"} | t_element
    )
    id: str | None = field(default=None, metadata=t_attr)


mat_id = Counter({"material": 1})


def material_id():
    """Material ID incrementer"""  # noqa: DOC201
    new_id = f"{mat_id['material']}"
    mat_id["material"] += 1
    return new_id


class Material(MatMLBase):
    """
    Material model

    Parameters
    ----------
    bulk_details:
        description of the bulk material
    component_details:
        description of a component within the bulk material
    graphs:
        two dimensional graphics
    glossary:
        descriptions of the material and property terms
    id:
        An identification specifier for the material, useful for complex systems such as
        composite laminates.
    layers:
        The number of layers in complex systems such as composite laminates.
    local_frame_of_reference:
        identification specifier for the local material orientation relative to the
        global frame of reference, useful for complex systems
        such as anisotropic materials.

    Notes
    -----
    In a departure from spec id will be created if not provided and is not optional.
    The default will be an increasing counter
    """

    bulk_details: BulkDetails = field(metadata={"name": "BulkDetails"} | req | t_element)
    component_details: list[ComponentDetails] = field(
        default_factory=list, metadata={"name": "ComponentDetails"} | t_element
    )
    graphs: Graphs | None = field(default=None, metadata={"name": "Graphs"} | t_element)
    glossary: Glossary | None = field(
        default=None, metadata={"name": "Glossary"} | t_element
    )
    id: str = field(default_factory=material_id, metadata=t_attr)
    layers: int | None = field(default=None, metadata=t_attr)
    local_frame_of_reference: str | None = field(default=None, metadata=t_attr)


class MatMLParserError(ValueError):
    """ValueError when xml file is out of spec"""


class MatMLXML(MatMLBase):
    """
    MatML model

    Parameters
    ----------
    material:
        List of materials in mixture
    metadata:
        Descriptions of the data sources, properties,
        measurement techniques, specimens, and parameters which are
        referenced when materials property data are encoded using
        other elements.
    """

    class Meta:
        """Name of model"""

        name = "MatMLXML"

    material: list[Material] = field(
        default_factory=list,
        metadata={"name": "Material", "min_occurs": 1} | t_element,
    )
    metadata: Metadata | None = field(
        default=None, metadata={"name": "Metadata"} | t_element
    )

    @classmethod
    def from_file(cls, filename):
        """Import xml file

        Raises
        ------
        NotImplementedError
            More than one material in xml file
        MatMLParserError
            Out of spec MatML 3.1 xml file
        """  # noqa: DOC201

        def find_xml_node(node, tag_name):
            matches = []
            if node.tag.lower() == tag_name.lower():
                matches.append(node)
                return matches
            for child in node:
                matches.extend(find_xml_node(child, tag_name))
            return matches

        found_nodes = find_xml_node(etree.parse(filename).getroot(), "MatML_Doc")
        if len(found_nodes) > 1:
            raise NotImplementedError("More than one MatML material found in xml file")

        try:
            return XmlParser().parse(found_nodes[0], cls)
        except ValueError as pe:
            raise MatMLParserError(
                f"MatML3.1 xml file not in spec, {pe.args[0]}"
            ) from pe

    def export(self, filename):
        """Export model to xml file"""
        serialiser = XmlSerializer()
        serialiser.config.indent = "  "
        serialiser.config.xml_declaration = False

        with open(filename, "w") as xml_out:
            serialiser.write(xml_out, self)
