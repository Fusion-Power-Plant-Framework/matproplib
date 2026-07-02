use pyo3::prelude::*;
// use uom::si::{f64::*, magnetic_flux_density::tesla, thermodynamic_temperature::kelvin};
use serde::{Deserialize, Serialize};

use crate::nucleides::Elements;
use crate::physicalproperties::{PhysicalProperty, PhysicalPropertyPy};

#[pyclass(subclass, module = "matproplib.materials")]
// #[derive(Debug, Serialize, Deserialize)]
pub struct Material {
    #[pyo3(get)]
    pub name: String,
    // #[pyo3(get)]
    pub elements: Elements,
    pub properties: Vec<(String, PhysicalProperty)>,
    pub converters: String, // todo not string
}

#[pymethods]
impl Material {
    #[new]
    fn new(
        name: String,
        elements: Option<Elements>,
        properties: Option<Vec<(String, PhysicalProperty)>>,
        converters: Option<String>,
    ) -> Self {
        Material {
            name,
            elements,
            properties,
            converters,
        }
    }

    fn __str__(&self) -> String {
        format!("Material({}, properties: {:?})", self.name, self.properties)
    }
}

#[pyfunction]
pub fn material(
    name: String,
    elements: Option<Elements>,
    properties: Option<Vec<(String, PhysicalPropertyPy)>>,
    converters: Option<String>,
) -> Material {
    Material::new(name, elements, properties, converters)
}

#[pymodule(name = "materials")]
pub mod materials_mod {
    #[pymodule_export]
    use super::{Material, material};
}
