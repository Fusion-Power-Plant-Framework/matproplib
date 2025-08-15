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

"""An example to show how to create a mixture in `matproplib`"""

# %%[markdown]
# ### Material Mixture
# In `matproplib`, we can create a mixture of materials using the `Mixture` class. This
# allows us to define a material that is composed of multiple other materials,
# each with its own properties.

# In this example, we will create a mixture of steel and water.

# %%
from matproplib.conditions import OperationalConditions
from matproplib.library.fluids import H2O
from matproplib.library.steel import SS316_L
from matproplib.material import mixture

# %%[markdown]
# Let us create the base materials first.

# %%
steel = SS316_L()
water = H2O()

# %%[markdown]
# Now we can create a mixture of these two materials. We will define the mass fractions
# of steel and water in the mixture. For example, we can create a mixture with
# 70% steel and 30% water.

# %%
my_mixture = mixture(
    "SteelWaterMixture", [(steel, 0.7), (water, 0.3)], fraction_type="mass"
)

# %%[markdown]
# We can now use this mixture material in our simulations. For example, we can evaluate
# the density of the mixture at a given temperature.
# Mixture properties are computed as a weighted average of the underlying material
# properties, assuming a homogenous mixture.

# %%

op_cond = OperationalConditions(temperature=300)

print(f"{my_mixture.density(op_cond)} kg/m^3")


# %%[markdown]
# We can always override the properties of the mixture by defining a new property.


# %%
my_mixture.density = lambda _: 1000.0  # Override density to be 1000 kg/m^3

# %%[markdown]
# We can still access teh underlying materials in the mixture.

# %%
print(f"{my_mixture.materials[0].density(op_cond)} kg/m^3")
print(f"{my_mixture.materials[1].density(op_cond)} kg/m^3")
