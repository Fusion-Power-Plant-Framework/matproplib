# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Materials plotting tools"""

import matplotlib.pyplot as plt
import numpy as np

from physical_materials.conditions import OperationalConditions


def plot_superconductor(
    sc_parameterisation, t_min, t_max, b_min, b_max, strain, n_points=50
):
    """Plot the critical current density of a superconductor parameterisation.

    Parameters
    ----------
    sc_parameterisation : SuperconductorParameterisation
        The superconductor parameterisation to plot.
    t_min : float
        Minimum temperature in K.
    t_max : float
        Maximum temperature in K.
    b_min : float
        Minimum magnetic field in T.
    b_max : float
        Maximum magnetic field in T.
    strain : float
        Strain value to use for the plot.
    n_points : int, optional
        Number of points to use for the plot, by default 100.
    """
    temperatures = np.linspace(t_min, t_max, n_points)
    magnetic_fields = np.linspace(b_min, b_max, n_points)

    xx, yy = np.meshgrid(temperatures, magnetic_fields)
    j_crit = np.zeros_like(xx)
    for i in range(n_points):
        for j in range(n_points):
            op_cond = OperationalConditions(
                temperature=xx[i, j], magnetic_field=yy[i, j], strain=strain
            )
            j_crit[i, j] = sc_parameterisation.critical_current_density(op_cond)

    f, ax = plt.subplots()
    cm = ax.contourf(xx, yy, j_crit, cmap="viridis")
    f.colorbar(cm, label="Critical current denstiy [A/m^2]")
    ax.set_title(
        f"{sc_parameterisation.name} superconducting parameterisation critical surface"
    )
    ax.set_xlabel("Temperature [K]")
    ax.set_ylabel("Magnetic field [T]")
    return f, ax
