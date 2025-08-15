# matproplib: Materials Property Library

`matproplib` is an engineering materials property library. It can be used to create material objects with associated material property parameterisations dependent on operational conditions (e.g. temperature) for use in engineering analyses, including neutronics and finite element analyses.


## Installation

The latest stable release is available through `pip`:

`pip install matproplib`

If you want to work on more recent versions, git clone the repository and run:

`pip install .`

in the destination folder.

## Library

A few materials with some publicly available material property parameterisations are included for convenience. These will be progressively added to.

Sadly, many material property parameterisations are not publicly available. For such cases, we recommend you construct your own `Material`s in your own repositories.


## Conventions

`matproplib` uses SI units...