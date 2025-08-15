# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Dependent properties of matproplib"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from matproplib.base import (
    SuperconductingParameterisation,
    rebuild,
)
from matproplib.material import dependentphysicalproperty
from matproplib.properties.independent import (
    MagneticField,  # noqa: TC001
    Strain,  # noqa: TC001
    Temperature,  # noqa: TC001
)
from matproplib.tools.tools import kludge_linear_spline

if TYPE_CHECKING:
    from matproplib.conditions import OperationalConditions


@rebuild
class Nb3SnBotturaParameterisation(SuperconductingParameterisation):
    """
    ITER-like Bottura-Bordini parameterisation of the critical surface of
    a Nb3Sn Superconducting strand.

    .. doi:: 10.1109/TASC.2009.2018278
        :title: L. Bottura and B. Bordini, "JC(B,T,ε) Parameterization for the ITER Nb3Sn Production,"
        in IEEE Transactions on Applied Superconductivity, vol. 19, no. 3, pp. 1521-1524, June 2009
    """  # noqa: E501

    constant: float  # Current density scaling constant
    p: float  # Low field exponent of the pinning force
    q: float  # High field exponent of the pinning force
    c_a1: float  # Strain fitting constant
    c_a2: float  # Strain fitting constant
    eps_0a: Strain  # Residual strain component
    eps_m: Strain  # Tensile strain at which the maximum critical properties are reached
    b_c20m: MagneticField  # Upper critical field at zero temperature and strain
    t_c0max: Temperature  # Critical temperature at zero field and strain

    @dependentphysicalproperty(unit="A/m^2")
    def critical_current_density(self, op_cond: OperationalConditions) -> float:
        """
        Calculate the critical current density as a function of temperature,
        magnetic field, and strain.
        """  # noqa: DOC201
        temperature = op_cond.temperature
        field = np.maximum(0.001, op_cond.magnetic_field)  # Avoid division by zero
        strain = op_cond.strain

        s = _nb3sn_strain_twente(strain, self.c_a1, self.c_a2, self.eps_0a)

        t_zero = self.t_c0max * s ** (1.0 / 3.0)
        reduced_t = temperature / t_zero
        t_152 = np.where(reduced_t > 0, reduced_t**1.52, reduced_t)

        b_crit = self.b_c20m * s * (1.0 - t_152)
        reduced_b = field / b_crit

        result = self.constant / field * s * (1.0 - t_152) * (1.0 - reduced_t**2)

        j_crit = np.zeros_like(reduced_b)
        ind = np.where((reduced_b < 1.0) & (reduced_b > 0), True, False)
        inv_ind = ~ind
        reduced_b_ind = reduced_b[ind]
        reduced_b_not_ind = reduced_b[inv_ind]

        # Apply kludging to avoid negative values and NaNs.
        j_crit[ind] = (
            result[ind] * reduced_b_ind**self.p * (1.0 - reduced_b_ind) ** self.q
        )
        j_crit[inv_ind] = result[inv_ind] * reduced_b_not_ind * (1.0 - reduced_b_not_ind)

        return kludge_linear_spline(j_crit, 10.0, 1.0)


def _nb3sn_strain_twente(
    strain: float, c_a1: float, c_a2: float, eps_0a: float
) -> float:
    """
    Strain function \n
    :math:`s({\\epsilon}) = 1+ \\frac{1}{1-C_{a1}{\\epsilon}_{0,a}}[C_{a1}
    (\\sqrt{{\\epsilon}_{sk}^{2}+{\\epsilon}_{0,a}^{2}}-\\sqrt{({\\epsilon}-
    {\\epsilon}_{sk})^{2}+{\\epsilon}_{0,a}^{2}})-C_{a2}{\\epsilon}]`
    """  # noqa: DOC201
    eps_sh = c_a2 * eps_0a / np.sqrt(c_a1**2 - c_a2**2)
    s1 = 1.0 / (1.0 - c_a1 * eps_0a)
    s2 = np.sqrt(eps_sh**2 + eps_0a**2) - np.sqrt((strain - eps_sh) ** 2 + eps_0a**2)
    return 1.0 + s1 * (c_a1 * s2 - c_a2 * strain)


@rebuild
class NbTiBotturaParameterisation(SuperconductingParameterisation):
    """
    ITER-like Bottura parameterisation of the critical surface of
    a NbTi Superconducting strand. (strain-independent)

    ..doi:: 10.1109/77.828413
        :title: L. Bottura, "A practical fit for the critical surface of NbTi,"
        in IEEE Transactions on Applied Superconductivity, vol. 10, no. 1, pp. 1054-1057, March 2000,
    """  # noqa: E501

    constant: float  # Current density scaling constant
    alpha: float  # Low field exponent of the pinning force
    beta: float  # High field exponent of the pinning force
    gamma: float  # High temperature exponent (?)
    t_c0: Temperature  # Critical temperature at zero field
    b_c20: MagneticField  # Upper critical flux density at zero temperature

    @dependentphysicalproperty(unit="A/m^2")
    def critical_current_density(self, op_cond: OperationalConditions) -> float:
        """
        Calculate the critical current density as a function of temperature
        and magnetic field.
        """  # noqa: DOC201
        field = np.maximum(0.001, op_cond.magnetic_field)  # Avoid division by zero
        temperature = op_cond.temperature

        reduced_t = temperature / self.t_c0
        temp_term = np.where(reduced_t > 0, 1 - reduced_t**1.7, 1 - reduced_t)

        b_c2 = self.b_c20 * temp_term
        reduced_b = field / b_c2

        result = self.constant / field * temp_term**self.gamma
        # Apply kludging to avoid negative values and NaNs.
        j_crit = np.where(
            (reduced_b < 1.0) & (reduced_b > 0),
            result * (reduced_b**self.alpha) * (1 - reduced_b) ** self.beta,
            result * reduced_b * (1 - reduced_b),
        )

        return kludge_linear_spline(j_crit, 20.0, 10.0)


@rebuild
class SummersParameterisation(SuperconductingParameterisation):
    """
    Summers' parameterisation of the critical surface of
    an A-15 type superconducting strand.

    https://scispace.com/pdf/a-model-for-the-prediction-of-nb-sub-3-sn-critical-current-xoujezlpxh.pdf
    see e.g. https://conferences.lbl.gov/event/979/contributions/5985/attachments/4069/3482/U9-U10_final.pdf, slide 25

    """  # noqa: E501

    constant: float  # Current density scaling constant
    alpha: float  # Strain function exponent (Ekin-like)
    t_c0m: Temperature  # Critical temperature at zero field and max strain
    b_c20m: (
        MagneticField  # Upper critical flux density at zero temperature and max strain
    )

    @dependentphysicalproperty(unit="A/m^2")
    def critical_current_density(self, op_cond: OperationalConditions) -> float:
        """
        Calculate the critical current density as a function of temperature,
        magnetic field, and strain.
        """  # noqa: DOC201
        field = np.maximum(0.001, op_cond.magnetic_field)  # Avoid division by zero
        temperature = op_cond.temperature
        f_strain = 1.0 - self.alpha * abs(op_cond.strain) ** 1.7

        constant = self.constant * np.sqrt(f_strain) / np.sqrt(field)

        b_c20 = self.b_c20m * f_strain
        t_c0 = self.t_c0m * f_strain ** (1.0 / 3.0)
        r_temp = temperature / t_c0
        r_temp_sq = r_temp**2
        b_c2 = (
            b_c20
            * (1 - r_temp_sq)
            * (1 - 0.31 * r_temp_sq * (1 - 1.77 * np.log(r_temp)))
        )
        reduced_b = field / b_c2
        result = np.where(
            (reduced_b < 1.0) & (reduced_b > 0),
            constant * (1 - reduced_b) ** 2 * (1 - r_temp_sq) ** 2,
            constant * (1 - reduced_b) * (1 - r_temp_sq) ** 2,
        )
        return kludge_linear_spline(result, 10.0, 1.0)
