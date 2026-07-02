use pyo3::prelude::*;

mod chemical_formula;
mod conditions;
mod custom_units;
mod materials;
mod nucleides;
mod physicalproperties;
mod tools;

#[pymodule(name = "matproplib")]
mod matproplib {
    #[pymodule_export]
    use super::conditions::{OperationalConditions, conditions_mod};
    #[pymodule_export]
    use super::materials::{Material, materials_mod};
    #[pymodule_export]
    use super::nucleides::{Element, Elements, nucleides_mod};
    #[pymodule_export]
    use super::physicalproperties::pp_mod;
}
