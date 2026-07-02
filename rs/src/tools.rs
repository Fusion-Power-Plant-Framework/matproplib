use numpy::PyArray1;
use pyo3::exceptions::PyTypeError;
use pyo3::{
    prelude::*,
    types::{PyAny, PySequence},
};

#[pyclass(skip_from_py_object)]
#[derive(Clone)]
pub enum SupportedArray {
    Float(f64),
    Sequence(Vec<f64>),
    NumpyArray(Vec<f64>),
}

impl FromPyObject<'_, '_> for SupportedArray {
    type Error = PyErr;

    fn extract(obj: Borrowed<'_, '_, PyAny>) -> Result<Self, Self::Error> {
        if let Ok(py_float) = obj.extract::<f64>() {
            Ok(SupportedArray::Float(py_float))
        } else if let Ok(py_seq) = obj.cast::<PySequence>() {
            let mut vec = Vec::with_capacity(py_seq.len()?);
            for i in 0..py_seq.len()? {
                if let Ok(item) = py_seq.get_item(i)?.extract::<f64>() {
                    vec.push(item);
                } else {
                    return Err(PyErr::new::<PyTypeError, _>(
                        "Sequence elements must be floats",
                    ));
                }
            }
            Ok(SupportedArray::Sequence(vec))
        } else if let Ok(py_array) = obj.extract::<&PyArray1<f64>>() {
            Ok(SupportedArray::NumpyArray(py_array.to_vec()))
        } else {
            Err(PyErr::new::<PyTypeError, _>(
                "Unsupported type for conversion to SupportedArray",
            ))
        }
    }
}
