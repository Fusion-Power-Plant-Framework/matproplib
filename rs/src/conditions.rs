use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use uom::fmt::DisplayStyle::Abbreviation;
use uom::si::{magnetic_flux_density::tesla, thermodynamic_temperature::kelvin};

use super::physicalproperties::{
    MagneticField, NeutronDamage, NeutronFluence, Pressure, Strain, Temperature,
};

use super::tools::SupportedArray;

#[pyclass(subclass, module = "matproplib.conditions")]
// #[derive(Serialize, Deserialize)]
pub struct OperationalConditions {
    #[pyo3(get, set)]
    pub temperature: Temperature,
    #[pyo3(get, set)]
    pub pressure: Option<Pressure>,
    #[pyo3(get, set)]
    pub magnetic_field: Option<MagneticField>,
    #[pyo3(get, set)]
    pub strain: Option<Strain>,
    #[pyo3(get, set)]
    pub neutron_damage: Option<NeutronDamage>,
    #[pyo3(get, set)]
    pub neutron_fluence: Option<NeutronFluence>,
}

#[pymethods]
impl OperationalConditions {
    #[new]
    fn new<'py>(
        temperature: SupportedArray,
        pressure: Option<SupportedArray>,
        magnetic_field: Option<SupportedArray>,
        strain: Option<SupportedArray>,
        neutron_damage: Option<SupportedArray>,
        neutron_fluence: Option<SupportedArray>,
    ) -> Self {
        OperationalConditions {
            temperature: Temperature::new(temperature),
            pressure: pressure.map(|p| Pressure::new(p)),
            magnetic_field: magnetic_field.map(|m| MagneticField::new(m)),
            strain: strain.map(|s| Strain::new(s)),
            neutron_damage: neutron_damage.map(|nd| NeutronDamage::new(nd)),
            neutron_fluence: neutron_fluence.map(|nf| NeutronFluence::new(nf)),
        }
    }

    fn __str__(&self) -> String {
        format!(
            "OperationalConditions(temperature: {}, magnetic_field: {:?}, strain: {})",
            self.temperature.unit.into_format_args(kelvin, Abbreviation),
            self.magnetic_field.unit.into_format_args(tesla, Abbreviation),
            self.strain
        )
    }
}

#[pymodule(name = "conditions")]
pub mod conditions_mod {
    #[pymodule_export]
    use super::OperationalConditions;
}
