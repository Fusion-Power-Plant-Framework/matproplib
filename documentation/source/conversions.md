# Format Conversions


Materials are often needed in specific formats for a given code.
We aim to offer a variety of converter to different formats where direct interfacing cannot easily be achieved.

We currently offer coverters to a few select neutronics packages but this area will be expanded as the `matproplib` matures.


## Neutronics Converters

We offer converters to OpenMC, Serpent, Fispact and MCNP6.
The OpenMC converter requires OpenMC installed as it produces an OpenMC python material.
All of the other converters output a text string and can be run without any extra dependencies.

### Usage
To use any converter they need to be added to a material, this can be done at definition or during use.
The individual converters have some configuration options if required.

```python
from matproplib.converters.neutronics import MCNPNeutronicConfig, OpenMCNeutronicConfig
from matproplib.properties.group import props
from matproplib.material import material

Steel = material(
    "Steel",
    elements="C1Fe12",
    properties=props(
        density=5,
        specific_heat_capacity=6
    ),
    converters=MCNPNeutronicConfig(), # alternatively a list of converters
)

my_steel = Steel()
my_steel.converters.add(OpenMCNeutronicConfig())

```

To convert a material to a given format use the `convert` function on the material. The converter name is defined as a variable on the converter class:

```python
from matproplib.conditions import OperationalConditions
from matproplib.converters.neutronics import MCNPNeutronicConfig

op_cond = OperationalConditions(temperature=298)

# converter name equivalent to 'mcnp'
mcnp_mat = my_steel.convert(MCNPNeutronicConfig.name, op_cond)
```

All neutronics converters translate elements to thier natural nucleide abundances. The nucleides are then combined with any other isotopes on the material.
