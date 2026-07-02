use std::hash::DefaultHasher;
use std::hash::Hash;
use std::collections::hash_map::DefaultHasher;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::wrap_pyfunction;
use serde::{Deserialize, Serialize};
use std::cmp::Ordering;
use std::ops::{Add, Div, Mul, Neg, Sub};
use std::str::FromStr;
use uom::Conversion;
use uom::fmt::DisplayStyle::Abbreviation;
use uom::si::Unit;
use uom::si::{
    areal_number_density::per_square_meter, electric_current_density::ampere_per_square_meter,
    magnetic_flux_density::tesla, pressure::pascal, ratio::ratio,
    thermodynamic_temperature::kelvin, volume::cubic_meter,
};

use crate::tools::SupportedArray;

use pyo3::prelude::*;
use std::fmt;

// --- Mock Setup (Must be defined for the macro to use) ---
// pub trait Unit: std::fmt::Debug + 'static {}
// pub trait Conversion<U>: Unit {}

// Mocking the specific unit types we want to support
#[derive(Debug, Clone, Copy)] pub struct Kelvin; impl Unit for Kelvin {}
#[derive(Debug, Clone, Copy)] pub struct Meter; impl Unit for Meter {}

// Mocking the raw data input
pub enum SupportedArray {
    Float(f64),
    Sequence(Vec<f64>),
    NumpyArray(Vec<f64>),
}

// --- Trait Definition (The common API) ---
pub trait PhysicalPropertyTrait: Send + Sync {
    fn value_as(&self, _unit: &dyn Unit) -> PyResult<f64>;
    fn __str__(&self) -> String;

    // For arithmetic, the return must be a Box<dyn PhysicalPropertyTrait>
    // because the result's unit might change, or we might return a placeholder.
    fn __sub__(&self, other: &dyn PhysicalPropertyTrait) -> PyResult<Box<dyn PhysicalPropertyTrait>>;
    fn __mul__(&self, other: &dyn PhysicalPropertyTrait) -> PyResult<Box<dyn PhysicalPropertyTrait>>;
}

// --- Macro Helper: Generates the Concrete Storage Property ---
macro_rules! impl_concrete_property {
    (
        $unit_type:ty,
        $struct_name:ident
    ) => {
        // 1. The concrete property struct, owning the base unit.
        pub struct $struct_name {
            value: f64,
            // The base unit is fixed for this struct's lifetime.
            _base_unit: $unit_type,
        }

        impl PhysicalPropertyTrait for $struct_name {
            fn value_as(&self, _unit: &dyn Unit) -> PyResult<f64> {
                println!("-> Executing base logic for {}", stringify!($struct_name));
                Ok(self.value)
            }
            fn __str__(&self) -> String { format!("{}: {:.2}", stringify!($struct_name), self.value) }

            // Implement arithmetic for the concrete type
            fn __sub__(&self, other: &dyn PhysicalPropertyTrait) -> PyResult<Box<dyn PhysicalPropertyTrait>> {
                println!("-> Subtraction logic for {}", stringify!($struct_name));
                // Return a new instance of the same concrete type (simplification)
                Ok(Box::new($struct_name { value: self.value - 1.0, _base_unit: unsafe { std::mem::transmute(()) } }))
            }
            fn __mul__(&self, other: &dyn PhysicalPropertyTrait) -> PyResult<Box<dyn PhysicalPropertyTrait>> {
                println!("-> Multiplication logic for {}", stringify!($struct_name));
                Ok(Box::new($struct_name { value: self.value * 2.0, _base_unit: unsafe { std::mem::transmute(()) } }))
            }
        }
    };
}


// --- The Main Macro ---
/// Defines a full physical property wrapper for a given unit type.
/// Usage: define_property!(UnitType, WrapperStructName, UnitTypeBaseUnit, ...)
macro_rules! define_property {
    (
        $unit_type:ty,
        $wrapper_struct_name:ident,
        $unit_type_base_unit:ty,
        // List of concrete units to support, e.g., (UnitType, StructName)
        $(
            $concrete_unit_type:ty,
            $concrete_struct_name:ident
        ),*
    ) => {
        // 1. Generate all the concrete property storage structs
        $(
            impl_concrete_property!($concrete_unit_type, $concrete_struct_name)
        )*

        // 2. Define the Wrapper struct that owns the concrete property
        pub struct $wrapper_struct_name {
            property: Box<dyn PhysicalPropertyTrait>,
        }

        impl $wrapper_struct_name {
            // Constructor: Takes raw data and initializes the concrete property.
            pub fn new(value: SupportedArray) -> Self {
                // Factory logic: This must select the correct concrete type based on context/unit.
                // For simplicity here, we assume we are always creating the base unit type.
                let base_property = $crate::TemperatureProperty::new(value); // Assuming TemperatureProperty is the base one
                Self { property: Box::new(base_property) }
            }
        }

        // 3. Implement the API methods on the Wrapper
        impl $wrapper_struct_name {
            // Implementation of the trait methods on the wrapper itself
            pub fn value_as(&self, unit: &dyn Unit) -> PyResult<f64> {
                self.property.value_as(unit)
            }
            pub fn __str__(&self) -> String {
                self.property.__str__()
            }
            // Arithmetic delegation
            pub fn __sub__(&self, other: &dyn PhysicalPropertyTrait) -> PyResult<Box<dyn PhysicalPropertyTrait>> {
                self.property.__sub__(other)
            }
            pub fn __mul__(&self, other: &dyn PhysicalPropertyTrait) -> PyResult<Box<dyn PhysicalPropertyTrait>> {
                self.property.__mul__(other)
            }
        }
    };
}

// --- Macro Invocation ---
// We define the system for Temperature:
define_property!(
    // UnitType, WrapperName, BaseUnitType,
    Kelvin,
    Temperature,
    Kelvin,
    // Concrete Units Supported (UnitType, StructName)
    (Kelvin, TemperatureProperty)
);

// NOTE: For this example to compile, you would need to manually implement
// the boilerplate for Meter, Length, etc., following the same pattern.

#[pyclass(module = "matproplib.physicalproperties")]
#[derive(Debug, Clone, PartialEq, Eq, Hash, Ord, PartialOrd)]
pub struct Temperature(PhysicalProperty<Temperature>);

#[pymethods]
impl Temperature {
    #[new]
    pub fn new(value: SupportedArray) -> Self {
        Temperature(PhysicalProperty::new(value, kelvin))
    }

    pub fn value_as(&self, unit: Conversion<kelvin>) -> PyResult<f64> {
        self.0.value_as(unit)
    }
}

#[pyclass(module = "matproplib.physicalproperties")]
#[derive(Debug, Clone, PartialEq, Eq, Hash, Ord, PartialOrd)]
pub struct Pressure(PhysicalProperty<pascal>);

#[pymethods]
impl Pressure {
    #[new]
    pub fn new(value: SupportedArray) -> Self {
        Pressure(PhysicalProperty::new(value, pascal))
    }

    pub fn value_as(&self, unit: Conversion<pascal>) -> PyResult<f64> {
        self.0.value_as(unit)
    }
}

#[pyclass(module = "matproplib.physicalproperties")]
#[derive(Debug, Clone, PartialEq, Eq, Hash, Ord, PartialOrd)]
pub struct MagneticField(PhysicalProperty<tesla>);

#[pymethods]
impl MagneticField {
    #[new]
    pub fn new(value: SupportedArray) -> Self {
        MagneticField(PhysicalProperty::new(value, tesla))
    }

    pub fn value_as(&self, unit: Conversion<tesla>) -> PyResult<f64> {
        self.0.value_as(unit)
    }
}

#[pyclass(module = "matproplib.physicalproperties")]
#[derive(Debug, Clone, PartialEq, Eq, Hash, Ord, PartialOrd)]
pub struct Strain(PhysicalProperty<ratio>);

#[pymethods]
impl Strain {
    #[new]
    pub fn new(value: SupportedArray) -> Self {
        Strain(PhysicalProperty::new(value, ratio))
    }

    pub fn value_as(&self, unit: Conversion<ratio>) -> PyResult<f64> {
        self.0.value_as(unit)
    }
}

#[pyclass(module = "matproplib.physicalproperties")]
#[derive(Debug, Clone, PartialEq, Eq, Hash, Ord, PartialOrd)]
pub struct NeutronDamage(PhysicalProperty<ratio>);

#[pymethods]
impl NeutronDamage {
    #[new]
    pub fn new(value: SupportedArray) -> Self {
        NeutronDamage(PhysicalProperty::new(value, ratio))
    }

    pub fn value_as(&self, unit: Conversion<ratio>) -> PyResult<f64> {
        self.0.value_as(unit)
    }
}

#[pyclass(module = "matproplib.physicalproperties")]
#[derive(Debug, Clone, PartialEq, Eq, Hash, Ord, PartialOrd)]
pub struct NeutronFluence(PhysicalProperty<per_square_meter>);

#[pymethods]
impl NeutronFluence {
    #[new]
    pub fn new(value: SupportedArray) -> Self {
        NeutronFluence(PhysicalProperty::new(value, per_square_meter))
    }

    pub fn value_as(&self, unit: Conversion<per_square_meter>) -> PyResult<f64> {
        self.0.value_as(unit)
    }
}

#[pyclass(module = "matproplib.physicalproperties")]
#[derive(Debug, Clone, PartialEq, Eq, Hash, Ord, PartialOrd)]
pub struct CurrentDensity(PhysicalProperty<ampere_per_square_meter>);

#[pymethods]
impl CurrentDensity {
    #[new]
    pub fn new(value: SupportedArray) -> Self {
        CurrentDensity(PhysicalProperty::new(value, ampere_per_square_meter))
    }

    pub fn value_as(&self, unit: Conversion<ampere_per_square_meter>) -> PyResult<f64> {
        self.0.value_as(unit)
    }
}

#[pyclass(module = "matproplib.physicalproperties")]
#[derive(Debug, Clone, PartialEq, Eq, Hash, Ord, PartialOrd)]
pub struct Volume(PhysicalProperty<cubic_meter>);

#[pymethods]
impl Volume {
    #[new]
    pub fn new(value: SupportedArray) -> Self {
        Volume(PhysicalProperty::new(value, cubic_meter))
    }

    pub fn value_as(&self, unit: Conversion<cubic_meter>) -> PyResult<f64> {
        self.0.value_as(unit)
    }
}

#[pymodule(name = "physicalproperties")]
pub mod pp_mod {
    #[pymodule_export]
    use super::{
        CurrentDensity, MagneticField, NeutronDamage, NeutronFluence, Pressure, Strain,
        Temperature, Volume,
    };
}
