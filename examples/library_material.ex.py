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

"""An example to show the use of a matproplib material"""

# %%
import matplotlib.pyplot as plt
import numpy as np

from matproplib.conditions import OperationalConditions
from matproplib.library.copper import CryogenicCopper

# %% [markdown]
# # Library Materials
# We can import an existing material from the `matproplib` library. Here we use the
# `CryogenicCopper` material, which is a collection of some material property
# parameterisations, largely from NIST.

# %%
copper = CryogenicCopper()

# %% [markdown]
# We can then set up some conditions at which we want to evaluate some material property.
# Here we take a look at the electrical resistivity of Copper in cryogenic conditions,
# which is senstive to temperature, magnetic field, and neutron fluence.

# %%
temperatures = np.linspace(4, 100, 50)  # Temperatures from 4 K to 100 K

zero_fluence_conditions = [
    OperationalConditions(temperature=t, magnetic_field=10.0, neutron_fluence=0.0)
    for t in temperatures
]
resistivity_zero_fluence = [
    copper.electrical_resistivity(c) for c in zero_fluence_conditions
]

fluence = 1e22
fluence_conditions = [
    OperationalConditions(temperature=t, magnetic_field=10.0, neutron_fluence=fluence)
    for t in temperatures
]
resistivity_fluence = [copper.electrical_resistivity(c) for c in fluence_conditions]

# %% [markdown]
# And simply plot the results.
# %%
f, ax = plt.subplots()

ax.plot(temperatures, resistivity_zero_fluence, label="fluence=0.0")
ax.plot(temperatures, resistivity_fluence, label=f"fluence={fluence:.1e}")
ax.legend()
ax.set_xlabel("Temperature (K)")
ax.set_ylabel("Electrical Resistivity (Ohm m)")
plt.show()
