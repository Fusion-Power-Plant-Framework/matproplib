# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: tags,-all
#     notebook_metadata_filter: -jupytext.text_representation.jupytext_version
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% tags=["remove-cell"]
# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""An example to show the basic usage of matproplib"""

# %%
from typing import Literal

from pint import Unit

from matproplib.base import rebuild
from matproplib.conditions import OperationalConditions
from matproplib.converters.neutronics import (
    FispactNeutronicConfig,
    MCNPNeutronicConfig,
    OpenMCNeutronicConfig,
)
from matproplib.material import FullMaterial, dependentphysicalproperty, material
from matproplib.properties.dependent import Density, SpecificHeatCapacity
from matproplib.properties.group import DefaultProperties, Properties, props
from matproplib.properties.independent import PhysicalProperty, pp
from matproplib.superconduction import NbTiBotturaParameterisation

# %% [markdown]
# # Usage Overview
# ## Basics
#
# <div class="alert alert-block alert-info">
# ⚠️ All material and property definitions are for example purposes
# they dont necessarily represent actual quantities or materials.
# </div>
#
# ### Conditions
# All materials are affected by the conditions they are in.
# For properties of a material that are dependent on conditions `OperationConditions`
# should be passed as an argument to the property.
# By default `OperationalConditions` contains:
#
#  - Temperature
#  - Pressure
#  - Magnetic Field
#  - Stress
#  - Neutron Fluence
#  - Neutron Damage
#
# The only conditions required is temperature
#
# %%
op_cond = OperationalConditions(temperature=298, pressure=(1, "atm"))
print(op_cond)

# %% [markdown]
# More complex conditions can be created adding a new independent physical property.
# This can be achieve via inheriting from PhysicalProperty or
# using the `pp` helper function
#
#
# %%
# class CurrentDensity(PhysicalProperty):
#     unit: Unit | str = "A/m^2"

CurrentDensity = pp("CurrentDensity", "A/m^2")


class SpecialConditions(OperationalConditions):
    """Example conditions object"""

    current_density: CurrentDensity


sp_op_cond = SpecialConditions(temperature=5, pressure=(1, "atm"), current_density=3)
print(sp_op_cond)

# %% [markdown]
# ### Material
# You can create a material either with the `material` function or
# via inheriting from `Material`. When creating a material via inheritance all fields
# need full typing specification and is therefore considered a more advanced usecase.
# The `material` function handles this internally allowing for
# straightforward material creation.
#
#
# %%
# class MyMaterial(Material):
#     name: str = "MyMaterial"

MyMaterial = material("MyMaterial")


# %%
my_material_inst = MyMaterial()
print(my_material_inst)

# %% [markdown]
# #### Elements
# You can specify elements in a material like so

# %%
Unobtainium = material(
    "Unobtainium", elements={"H": 0.1, "He": 0.2, "Li": 0.3, "Be": 0.4}
)
unob = Unobtainium()
print(unob)

# %% [markdown]
# Or from a chemical formula

# %%
Unobtainium = material("Unobtainium", elements="HHe(Be5(Li2He)2)3")
unob = Unobtainium()
print(unob)

# %% [markdown]
# Isotopes cannot be specified from a formula but can be achieved like so

# %%
Unobtainium = material(
    "Unobtainium", elements={"H2": 0.1, "H3": 0.2, "He4": 0.3, "Li6": 0.4}
)
unob = Unobtainium()
print(unob)

# %% [markdown]
# #### Properties
# Properties come in two forms dependent and independent.
#
# ##### Independent
# Independent properties have already been shown and are just a number with a unit.
# These are generally used for conditions.
#
# Notice the created property is converted to the default units.

# %%
CurrentDensity = pp("CurrentDensity", "A/m^2")
cd = CurrentDensity(value=(5, "MA/m^2"))
print(cd)

# %% [markdown]
# ##### Dependent
# Dependent properties are dependent on any operational condition,
# they can also be singular values.

# %%
shc = SpecificHeatCapacity(value=lambda op_cond: 5 * op_cond.temperature)
print(shc(op_cond), f"{shc.unit:~P}")

# %%
# With convertable units
den = Density(value=5, unit="pound/ft^3")
print(f"{den(op_cond):.2f}", f"{den.unit:~P}")

# %% [markdown]
# A parameterisation may only valid within a range of operating conditions or
# use a specific condition unit for calculation.

# %%
den = Density(
    value=lambda op_cond: op_cond.pressure**2,
    op_cond_config={"pressure": ("millibar", 1, 100)},
)

try:
    den(op_cond)
except ValueError as ve:
    print(ve)

# %% [markdown]
# The default set of dependent properties can be created using the `props` function.
# Only properties specifed will be created.
# Alternatively all are defined when using the `DefaultProperties` class.
#
# When grouped dependent properties can also depend on each other.

# %%
myprops = props(
    specific_heat_capacity={
        "value": lambda properties, op_cond: properties.density(op_cond)
        * op_cond.temperature
    },
    density=lambda oc: oc.pressure * 5,
    superconducting_parameterisation=NbTiBotturaParameterisation(
        alpha=1,
        beta=2,
        gamma=3,
        constant=4,
        t_c0=5,
        b_c20=6,
        critical_current_density=7,  # overriding default
    ),
)
print(myprops)
print(myprops.specific_heat_capacity(op_cond))

# %%
my_def_props = DefaultProperties(density=5)
print(my_def_props)

# %% [markdown]
# You can add properties to a material when you define it

# %%
Unobtainium = material(
    "Unobtainium",
    elements={"H2": 0.1, "H3": 0.2, "He4": 0.3, "Li6": 0.4},
    properties=myprops,
)
unob = Unobtainium()
print(unob)

# %% [markdown]
# #### Superconducting Parameterisations
#
# Superconducting information can be provided as part of the properties as seen above.
# This enables the calculation of critical current density
#
# %%
m_op_cond = OperationalConditions(temperature=1, pressure=2, magnetic_field=3)
print(
    unob.superconducting_parameterisation.critical_current_density(m_op_cond),
    f"{unob.superconducting_parameterisation.critical_current_density.unit:~P}",
)

# %% [markdown]
# #### Neutronics Properties and Code Material Conversion
# When using materials as part of neutronics calculations some finer details
# about the material can be required.
# These details are usually code specific

# %%
n_props_openmc = OpenMCNeutronicConfig(enrichment_target="Li6")

n_props = FispactNeutronicConfig(volume=(3, "cm^3"))

# %%
n_unob = Unobtainium(properties=myprops, converters=n_props)
n_unob.convert("fispact", op_cond)

# %% [markdown]
# ### Full functional material

# %%
Steel = material(
    "Steel",
    elements="C1Fe12",
    properties=props(
        density=5,
        specific_heat_capacity={
            "value": lambda properties, oc: properties.density(oc) * oc.temperature,
            "unit": "J/g/K",
            "op_cond_config": {"temperature": ("K", 100, 300)},
        },
        superconducting_parameterisation=NbTiBotturaParameterisation(
            alpha=1,
            beta=2,
            gamma=3,
            constant=4,
            t_c0=5,
            b_c20=6,
        ),
    ),
    converters=FispactNeutronicConfig(volume=3),
)
op_cond = OperationalConditions(temperature=298, pressure=(1, "atm"), magnetic_field=5)
steel = Steel()  # Initialised using defaults
print(steel.critical_current_density(op_cond))
print(steel.specific_heat_capacity(op_cond))
print()
print(steel.convert("fispact", op_cond))


# %% [markdown]
# ## Advanced Usage
#
# ### Complete specification using a classes
# Defaults can be added to the class specification if required. They
# can still be overwritten.


# %%


class Steel(FullMaterial[Literal["mcnp"], NbTiBotturaParameterisation]):
    """Custom material through inheritance"""

    name: str = "Steel"


steel = Steel(
    elements="CFe12",
    density=5,
    specific_heat_capacity=6,
    superconducting_parameterisation=NbTiBotturaParameterisation(
        alpha=1,
        beta=2,
        gamma=3,
        constant=4,
        t_c0=5,
        b_c20=6,
    ),
    converters=MCNPNeutronicConfig(),
)

print(steel)

# Steel being statically typed means that this will work but isnt recognised in typing
steel.converters.add(FispactNeutronicConfig(volume=5))
steel.convert("fispact", op_cond)

# %% [markdown]
# Alternatively you can create a material using an existing properties object


# %%
@rebuild  # required when using the dependentphysicalproperty decorator
class MyProperties(Properties):
    """Custom property class"""

    density: Density = 6
    specific_heat_capacity: SpecificHeatCapacity = 7
    superconducting_parameterisation: NbTiBotturaParameterisation | None = None

    @dependentphysicalproperty(unit="")
    def residual_resistance_ratio(self, op_cond):
        """Default residual_resistance_ratio dependent property"""
        return self.density(op_cond) * op_cond.temperature


properties = MyProperties(
    density=5,
    specific_heat_capacity=6,
    superconducting_parameterisation=NbTiBotturaParameterisation(
        alpha=1,
        beta=2,
        gamma=3,
        constant=4,
        t_c0=5,
        b_c20=6,
    ),
)

steel = Steel(
    elements="CFe12",
    properties=properties,
    converters=MCNPNeutronicConfig(),
)

print(steel)
