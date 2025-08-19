# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
import pytest
from CoolProp.CoolProp import PropsSI

from matproplib.conditions import OperationalConditions
from matproplib.library.fluids import Air, Helium, Hydrogen, Water

# (fluid_class, fluid_name, prop_func, coolprop_key)
fluids_and_props = [
    (Water, "Water", "density", "DMASS"),
    (Water, "Water", "specific_heat_capacity", "CPMASS"),
    (Water, "Water", "thermal_conductivity", "CONDUCTIVITY"),
    (Air, "Air", "density", "DMASS"),
    (Air, "Air", "specific_heat_capacity", "CPMASS"),
    (Air, "Air", "thermal_conductivity", "CONDUCTIVITY"),
    (Helium, "Helium", "density", "DMASS"),
    (Helium, "Helium", "specific_heat_capacity", "CPMASS"),
    (Helium, "Helium", "thermal_conductivity", "CONDUCTIVITY"),
    (Hydrogen, "Hydrogen", "density", "DMASS"),
    (Hydrogen, "Hydrogen", "specific_heat_capacity", "CPMASS"),
    (Hydrogen, "Hydrogen", "thermal_conductivity", "CONDUCTIVITY"),
]

# operating conditions to test
conditions = [
    (300, 1e5),
    (350, 1e5),
    (400, 1e5),
    (500, 1e5),
    (600, 1e6),
    (700, 1e6),
    (300, 1e3),
]


@pytest.mark.parametrize(
    ("fluid_class", "fluid_name", "prop_func", "coolprop_key"), fluids_and_props
)
@pytest.mark.parametrize(("t", "p"), conditions)
def test_fluid_properties(fluid_class, fluid_name, prop_func, coolprop_key, t, p):
    fluid = fluid_class()
    op_cond = OperationalConditions(temperature=t, pressure=p)

    # call the method dynamically
    method = getattr(fluid, prop_func)
    result = method(op_cond)

    expected = PropsSI(
        coolprop_key,
        "T",
        float(op_cond.temperature.value),
        "P",
        float(op_cond.pressure.value),
        fluid_name,
    )

    assert result == expected
