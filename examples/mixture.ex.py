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
from matproplib.library.fluids import H2O
from matproplib.library.steel import Steel
from matproplib.material import Mixture
