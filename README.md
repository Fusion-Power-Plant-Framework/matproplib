# matproplib: Materials Property Library

`matproplib` is an engineering materials property library. It can be used to create material objects with associated material property parameterisations dependent on operational conditions (e.g. temperature) for use in engineering analyses, including neutronics and finite element analyses.


## Installation

The latest stable release is available through `pip`:

`pip install matproplib`

If you want to work on more recent versions:

`pip install matproplib@git+https://github.com/Fusion-Power-Plant-Framework/matproplib@main`

## Library

A few materials with some publicly available material property parameterisations are included for convenience. These will be progressively added to.

Sadly, many material property parameterisations are not publicly available. For such cases, we recommend you construct your own `Material`s in your own repositories.


## Conventions

`matproplib` uses SI units, which includes the use of K for temperature.

Phase transitions are generally not handled, although properties are available for some fluids through the `CoolProp` library.

By default, material compositions are specified by atomic fractions. When used in neutronics, isotopes of elements default to natural abundances, unless otherwise specified.
