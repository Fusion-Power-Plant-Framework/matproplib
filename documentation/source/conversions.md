# Format Conversions


Materials are often needed in specific formats for a given code.
We aim to offer a variety of converters to different formats where direct interfacing cannot easily be achieved.

We currently offer coverters to a few different formats, this will be expanded as the `matproplib` matures.


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

## Finite Element Converters

Finite Element codes and platforms, such as ANSYS, can be interfaced with using the following converters.

### MatML

The MatML 3.1 xml format can be imported and exported by simulation suites such as ANSYS. We can read from these xml files and write to them. This interface has been generated from the MatML 3.1 specification, a copy is available [here](https://github.com/Fusion-Power-Plant-Framework/matproplib/tree/main/matproplib/tools/matml/matml31.xsd)
The interface is limited to bulk material properties at this time.

#### Usage

To use this functionality you will need to install the extra required dependencies:

```bash
pip install matproplib[matml]
```

##### Import

To import a material from a MatML 3.1 xml file. If the importer is unable to process a specific property you specifiy it in `skip_properties`
to ignore it. Please bare with us while we enable importing for different property types.

```python
from matproplib.converters.matml import MatML, ANSYS_SKIPPED

MyMaterial = MatML.import_from('my_material.xml')

# skipping properties
my_skips = ANSYS_SKIPPED + ['my property']
MyMaterial = MatML.import_from('my_material.xml', skip_properties=my_skips)

my_material = MyMaterial()
```

##### Export

As with all converters they can be added during or after initialisation of the material.

```python
from matproplib.converters.matml import MatML
from matproplib.properties.group import props
from matproplib.material import material

Steel = material(
    "Steel",
    elements="C1Fe12",
    properties=props(
        density=5,
        specific_heat_capacity=6
    ),
    converters=MatML(), # alternatively a list of converters
)

my_steel = Steel()

# alternatively
# my_steel.converters.add(MatML())
```

To convert a material to a given format use the `convert` function on the material. The converter name is defined as a variable on the converter class:

```python
from matproplib.conditions import OperationalConditions
from matproplib.converters.matml import MatML

op_cond = OperationalConditions(temperature=298)

# converter name equivalent to 'matml'
matml_mat = my_steel.convert(MatML.name, op_cond)

# to write the xml file
mat_ml.export('my_material.xml')
```
