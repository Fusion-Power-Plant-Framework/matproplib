use crate::chemical_formula;
use mendeleev as pt;
use pyo3::prelude::*;
use regex::Regex;
use std::any::Any;
use std::collections::HashMap;

#[pyclass(module = "matproplib.nucleides")]
#[derive(Clone)]
struct ElementFraction {
    element: Element,
    fraction: f64,
}

enum ElementOrIsotope {
    Element(pt::Element),
    Isotope(pt::Isotope),
}

impl ElementFraction {
    fn from_element_symbol(symbol: &str) -> Self {
        ElementFraction {
            element: Element::new {
                element: symbol.to_string(),
            },
            fraction: 1.0,
        }
    }
}

#[pyclass(module = "matproplib.nucleides")]
#[derive(Clone)]
pub struct Element {
    element: ElementOrIsotope,
    metastable: i32,
}

#[pyclass(module = "matproplib.nucleides")]
pub struct Elements {
    root: HashMap<String, ElementFraction>,
    _no_atoms: Option<i32>,
    // _reference: Option<Json<References>>, //todo add references everywhere
}

#[derive(FromPyObject)]
enum ElementTypes<'py> {
    FORM(String),
    ELEM(Bound<'py, ElementFraction>),
    // ELEMS(Vec<(ElementFraction)>),  // todo from list of dictionary
    // ELEM_DICT(HashMap<String, String | f64>) // todo from dictionary
}

#[pymethods]
impl Elements {
    #[new]
    fn new(input: &PyAny, fraction_type: Option<String>) -> Self {
        let mut root = HashMap::new();
        let no_atoms = None;

        match input {
            s if s.is::<String>() => {
                let equation = s.downcast_ref::<String>().unwrap();
                let (root, no_atoms) = convert_chemical_equation_to_elements(equation);
            }
            e if e.is::<ElementFraction>() => {
                let el = e.downcast_ref::<ElementFraction>().unwrap();
                root.insert(el.element.symbol.clone(), el.clone());
            }
            list if list.is::<Vec<&dyn Any>>() => {
                let list = list.downcast_ref::<Vec<&dyn Any>>().unwrap();
                if list.len() == 1 && list[0].is::<String>() {
                    let symbol = list[0].downcast_ref::<String>().unwrap();
                    root.insert(symbol.clone(), ElementFraction::from_element_symbol(symbol));
                } else {
                    for e in list {
                        let el = ElementFraction::from_element_symbol(e.to_string().as_str());
                        root.insert(el.element.symbol.clone(), el);
                    }
                }
            }
            _ => {
                for (k, v) in input.downcast_ref::<HashMap<String, f64>>().unwrap() {
                    root.insert(k.clone(), ElementFraction::from_element_symbol(k));
                }
            }
        }

        let fraction_type = match fraction_type {
            Some(frac) => frac,
            None => String::from("atomic"),
        };

        let root = _from_fraction_type_conversion(fraction_type, root);

        let ret = Self {
            root,
            _no_atoms: no_atoms,
        };
        ret.check_elements();
        ret
    }

    fn check_elements(&self) {
        let mut e_sum: f64 = 0.0;
        for e in self.root.elements.values() {
            e_sum += e.fraction;
        }

        if e_sum.abs() >= 1e-5 && self.root.elements.len() > 0 {
            println!("Fraction does not sum to 1, total: {:.5}", e_sum);
        }

        if e_sum > 1.0 && e_sum.abs() >= 1e-5 {
            panic!("The fraction of elements is greater than 1: {:.5}", e_sum);
        }
    }

    fn nucleides(&self) -> Elements {
        // todo deconstruct into nucleides
        Elements {
            root: (),
            _no_atoms: None,
        }
    }

    fn average_molar_mass(&self) -> f64 {
        let mut mass = 0.0;
        let mut moles = 0.0;

        for ef in self.root.values() {
            // todo fix when periodic table crate chosen
            mass += ef.fraction * ef.element.element.mass;
            moles += ef.fraction;
        }

        return mass / moles;
    }
}

#[pymethods]
impl Element {
    // todo allow periodic table element to be passed in
    #[new]
    fn new(element: &str, metastable: Option<i32>) -> Self {
        // DOI: 10.1787/5f05e3db-en.
        // 12.1.4 Particle property type: metaStable
        let gnds_meta_stable = Regex::new(r"([A-Zn][a-z]*)(\d+)*((?:_[em]\d+)?)").unwrap();
        if let Some(caps) = gnds_meta_stable.captures(element) {
            let symbol = caps.get(1).map_or("", |m| m.as_str()).to_string();
            let a_n = caps.get(2).map_or(None, |m| Some(m.as_str().to_string()));
            let state = caps.get(3).map_or(None, |m| Some(m.as_str().to_string()));

            let metastable = match state {
                Some(s) => match s.get(2..) {
                    Some(substring) => substring.parse::<i32>().unwrap_or(0),
                    None => 0,
                },
                None => 0,
            };

            let new_element = pt::Element::iter()
                .find(|e| e.symbol() == element)
                .map(ElementOrIsotope::Element)
                .or_else(|| {
                    pt::Isotope::iter()
                        .find(|i| i.symbol() == element)
                        .map(ElementOrIsotope::Isotope)
                })
                .ok_or(format!("Element '{}' not found", element))?;

            Element {
                element: new_element,
                metastable,
            }
        } else {
            panic!("No Elements found");
        }
    }

    fn zaid(&self) -> String {
        format!("{:03}{:03}", self.atomic_number(), self.mass_number())
    }

    pub fn nucleides(&self) -> Vec<Element> {
        let mut result = vec![];
        if let Some(isotope) = self.element.Isotope() {
            result.push(Element::new(
                Box::new(Isotope {
                    isotope,
                    abundance: 1.0,
                }),
                Some(self.metastable),
            ));
        } else {
            let isos = self.element.Isotope();
            for iso in isos {
                result.push(Element::new(iso, Some(self.metastable)));
            }
        }
        result
    }

    fn atomic_number(&self) -> i32 {
        self.element.number()
    }

    fn mass_number(&self) -> i32 {
        if let Some(isotope) = self.element.Isotope() {
            isotope
        } else {
            most_abundant_isotope(&self.element).isotope
        }
    }
}

#[pyfunction]
fn convert_chemical_equation_to_elements(formula: &str) -> (HashMap<String, ElementFraction>, i32) {
    fn add_fraction(
        el1: &HashMap<String, ElementFraction>,
        el2: &HashMap<String, ElementFraction>,
    ) -> HashMap<String, ElementFraction> {
        let mut new_elements = el2.clone();
        for (k, v) in el1 {
            if new_elements.contains_key(k) {
                new_elements.get_mut(k).unwrap().fraction += v.fraction;
            } else {
                new_elements.insert(k.clone(), v.clone());
            }
        }
        new_elements
    }

    fn parse(
        tokens: &chemical_formula::ParsedFormula,
        elements: &HashMap<String, ElementFraction>,
    ) -> HashMap<String, ElementFraction> {
        let mut new_elements: HashMap<String, ElementFraction> = HashMap::new();
        for tok in tokens {
            match tok {
                chemical_formula::ParsedFormulaItem::Element(
                    chemical_formula::ParsedElement::Element(element, count),
                ) => {
                    if new_elements.contains_key(element) {
                        new_elements.get_mut(element).unwrap().fraction += *count as f64;
                    } else {
                        new_elements.insert(
                            element.clone(),
                            ElementFraction {
                                element: element.clone(),
                                fraction: *count as f64,
                            },
                        );
                    }
                }
                chemical_formula::ParsedFormulaItem::Group(
                    chemical_formula::ParsedGroup::Group(group),
                ) => {
                    let group_elements = parse(group, &HashMap::new());
                    new_elements = add_fraction(&new_elements, &group_elements);
                }
                chemical_formula::ParsedFormulaItem::Count(
                    chemical_formula::ParsedCount::Count(count),
                ) => {
                    for v in new_elements.values_mut() {
                        v.fraction *= *count as f64;
                    }
                }
            }
        }
        add_fraction(elements, &new_elements)
    }

    let mut elements = parse(
        &chemical_formula::parse_chemical_formula(formula),
        &HashMap::new(),
    );
    let ttl_fraction: f64 = elements.values().map(|e| e.fraction).sum();
    let mut result = HashMap::new();
    let mut no_atoms: i32 = 0;
    for v in elements.values_mut() {
        no_atoms += v.fraction as i32;
        v.fraction /= ttl_fraction;
    }
    for (k, v) in elements {
        result.insert(k, v);
    }
    (result, no_atoms)
}

#[pyfunction]
fn most_abundant_isotope(el: &Element) -> pt::Isotope {
    // Implement the most abundant isotope logic here
    el.element.isotopes[0]
}

#[pyfunction]
fn mass_fraction_to_atomic_fraction(
    ef_dict: HashMap<String, ElementFraction>,
) -> HashMap<String, ElementFraction> {
    // Implement the mass to atomic fraction conversion logic here
    HashMap::new()
}

#[pyfunction]
fn atomic_fraction_to_mass_fraction(
    ef_dict: HashMap<String, ElementFraction>,
) -> HashMap<String, ElementFraction> {
    // Implement the atomic to mass fraction conversion logic here
    HashMap::new()
}

#[pyfunction]
fn mass_fraction_to_volume_fraction(
    ef_dict: HashMap<String, ElementFraction>,
    densities: HashMap<String, f64>,
) -> HashMap<String, ElementFraction> {
    // Implement the mass to volume fraction conversion logic here
    HashMap::new()
}

#[pyfunction]
fn volume_fraction_to_mass_fraction(
    ef_dict: HashMap<String, ElementFraction>,
    densities: HashMap<String, f64>,
) -> HashMap<String, ElementFraction> {
    // Implement the volume to mass fraction conversion logic here
    HashMap::new()
}

#[pyfunction]
fn atomic_fraction_to_volume_fraction(
    ef_dict: HashMap<String, ElementFraction>,
    densities: HashMap<String, f64>,
) -> HashMap<String, ElementFraction> {
    // Implement the atomic to volume fraction conversion logic here
    HashMap::new()
}

#[pyfunction]
fn volume_fraction_to_atomic_fraction(
    ef_dict: HashMap<String, ElementFraction>,
    densities: HashMap<String, f64>,
) -> HashMap<String, ElementFraction> {
    // Implement the volume to atomic fraction conversion logic here
    HashMap::new()
}

#[pyfunction]
fn nucleides(el: &Element) -> Vec<Element> {
    // Implement the nucleides logic here
    Vec::new()
}

#[pyfunction]
fn average_molar_mass(elements: &Elements) -> f64 {
    // Implement the average molar mass logic here
    0.0
}

#[pymodule(name = "nucleides")]
pub mod nucleides_mod {
    #[pymodule_export]
    use super::{
        Element, ElementFraction, Elements, atomic_fraction_to_mass_fraction,
        atomic_fraction_to_volume_fraction, average_molar_mass,
        convert_chemical_equation_to_elements, mass_fraction_to_atomic_fraction,
        mass_fraction_to_volume_fraction, most_abundant_isoptope, nucleides,
        volume_fraction_to_atomic_fraction, volume_fraction_to_mass_fraction,
    };
}
