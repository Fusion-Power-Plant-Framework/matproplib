# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Copper materials"""

from typing import Final

import numpy as np
from pydantic import Field

from matproplib.base import References, rebuild
from matproplib.conditions import OperationalConditions
from matproplib.library.references import HUST_1984, SIMON_1992
from matproplib.material import (
    FullMaterial,
    Material,
    PropertiesT_co,
    dependentphysicalproperty,
)
from matproplib.nucleides import Elements
from matproplib.properties.dependent import (
    BulkModulus,
    ElectricalResistivity,
    MagneticSusceptibility,
    PoissonsRatio,
    ShearModulus,
    SpecificHeatCapacity,
    ThermalConductivity,
    ThermalExpansionCoefficient,
    YoungsModulus,
)
from matproplib.properties.group import props
from matproplib.tools.tools import annotate_reference


@rebuild
class Bronze(FullMaterial):
    name: str = Field(default="Bronze")
    elements: Elements = Field(default={"Cu": 0.95, "Sn": 0.05})
    properties: PropertiesT_co = props(
        as_field=True, density=8877.5, poissons_ratio=0.33
    )


@dependentphysicalproperty(
    YoungsModulus,
    op_cond_config={"temperature": ("degK", 4, 300)},
    reference=annotate_reference(SIMON_1992, "Equation 6-1"),
)
def _copper_youngs_modulus(op_cond: OperationalConditions) -> float:
    return 1e9 * (137.0 - 1.27e-4 * op_cond.temperature**2)


@dependentphysicalproperty(
    ShearModulus,
    op_cond_config={"temperature": ("degK", 4, 300)},
    reference=annotate_reference(SIMON_1992, "Equation 6-3"),
)
def _copper_shear_modulus(op_cond: OperationalConditions) -> float:
    return 1e9 * (51.0 - 4.63e-5 * op_cond.temperature**2)


@dependentphysicalproperty(
    BulkModulus,
    op_cond_config={"temperature": ("degK", 4, 300)},
    reference=annotate_reference(SIMON_1992, "Equation 6-5"),
)
def _copper_bulk_modulus(op_cond: OperationalConditions) -> float:
    return 1e9 * (142.0 - 5.7e-5 * op_cond.temperature**2)


@dependentphysicalproperty(
    PoissonsRatio,
    op_cond_config={"temperature": ("degK", 4, 300)},
    reference=annotate_reference(SIMON_1992, "Equation 6-6"),
)
def _copper_poisson_ratio(op_cond: OperationalConditions) -> float:
    return 0.339 + 7.03e-6 * op_cond.temperature**2


@dependentphysicalproperty(
    ThermalConductivity,
    op_cond_config={"temperature": ("degK", 1, 300)},
    reference=annotate_reference(HUST_1984, "Equation 1.1.3"),
)
def _copper_thermal_conductivity(
    self: Material, op_cond: OperationalConditions
) -> float:
    p1: Final[float] = 1.754e-8
    p2: Final[float] = 2.763
    p3: Final[float] = 1102.0
    p4: Final[float] = -0.165
    p5: Final[float] = 70.0
    p6: Final[float] = 1.765  # Hust and Lankford, NIST gives 1.756
    l_o: Final[float] = 2.443e-8
    rho_i_273: Final[float] = 1.553e-8

    rho_o = rho_i_273 / (self.residual_resistance_ratio(op_cond) - 1.0)
    beta = rho_o / l_o
    beta_r = beta / 0.0003
    p7 = 0.838 / beta_r**0.1661

    temperature = op_cond.temperature
    w_o = beta / temperature

    # Hust and Lankford shenanigans
    w_c = (
        -0.00012
        * np.log(temperature / 420)
        * np.exp(-((np.log(temperature / 470) / 0.7) ** 2))
    )
    w_c -= (
        0.00016
        * np.log(temperature / 73)
        * np.exp(-((np.log(temperature / 87) / 0.45) ** 2))
    )  # Typo in ref
    w_c -= (
        0.00002
        * np.log(temperature / 18)
        * np.exp(-((np.log(temperature / 21) / 0.5) ** 2))
    )

    w_i = (
        p1
        * temperature**p2
        / (
            1.0
            + p1 * p3 * temperature ** (p2 + p4) * np.exp(-((p5 / temperature) ** p6))
        )
        + w_c
    )
    w_io = p7 * w_i * w_o / (w_i + w_o)

    return 1.0 / (w_o + w_i + w_io)


@dependentphysicalproperty(
    SpecificHeatCapacity,
    op_cond_config={"temperature": ("degK", 4, 300)},
    reference=annotate_reference(SIMON_1992, "Equation 7-1"),
)
def _copper_specific_heat_capacity(op_cond: OperationalConditions) -> float:
    """
    Calculate the specific heat capacity of cryogenic copper (temperature-dependent).

    This function returns the specific heat capacity of high-purity copper
    at the temperature specified by the operational conditions.

    Parameters
    ----------
    op_cond : OperationalConditions
        The operational conditions, including temperature, for which
        the specific heat capacity is to be calculated.

    Returns
    -------
    float
        Specific heat capacity of copper in J/(kg·K).

    Notes
    -----
    Assumes high-purity copper with negligible impurity effects.

    References
    ----------
    J. Simon, E. S. Drexler, and R. P. Reed, *NIST Monograph 177*,
    "Properties of Copper and Copper Alloys at Cryogenic Temperatures",
    U.S. Government Printing Office, February 1992.
    https://nvlpubs.nist.gov/nistpubs/Legacy/MONO/nistmonograph177.pdf
    Equation 7-1
    """
    poly_coeffs: Final[list[float]] = [1.131, -9.454, 12.99, -5.501, 0.7637]
    logt = np.log10(op_cond.temperature)
    logcp = sum(c * logt**i for i, c in enumerate(poly_coeffs))
    return 10**logcp


@dependentphysicalproperty(
    ThermalExpansionCoefficient,
    op_cond_config={"temperature": ("degK", 4, 300)},
    reference=annotate_reference(SIMON_1992, "Equation 7-3"),
)
def _copper_thermal_expansion_coefficient(op_cond: OperationalConditions) -> float:
    poly_coeffs: Final[list[float]] = [
        -11.27,
        37.36,
        -66.59,
        63.49,
        -31.49,
        7.748,
        -0.7504,
    ]
    logt = np.log10(op_cond.temperature)
    log_alpha = sum(c * logt**i for i, c in enumerate(poly_coeffs))
    return 10**log_alpha * 10e6


@dependentphysicalproperty(
    MagneticSusceptibility,
    op_cond_config={"temperature": ("degK", 1.4, 300)},
    reference=annotate_reference(SIMON_1992, "Equation 8-8"),
)
def _copper_magnetic_susceptibility(op_cond: OperationalConditions) -> float:
    return 1e6 * (-9.84 + 3.59 / op_cond.temperature + 6.66e-4 * op_cond.temperature)


def _copper_rrr_resistivity(temperature: float, rrr: float) -> float:
    """
    Calculate the electrical resistivity of cryogenic copper based on temperature and RRR.

    Parameters
    ----------
    temperature : float
        Operating temperature in kelvin [K].

    rrr : float
        Residual resistivity ratio (dimensionless).

    Returns
    -------
    float
        Electrical resistivity of copper in ohm-meters [Ω·m].

    References
    ----------
    J. Simon, E. S. Drexler, and R. P. Reed, *NIST Monograph 177*,
    "Properties of Copper and Copper Alloys at Cryogenic Temperatures",
    U.S. Government Printing Office, February 1992.
    https://nvlpubs.nist.gov/nistpubs/Legacy/MONO/nistmonograph177.pdf
    Equation 8-1

    J. G. Hust, A. B. Lankford, NBSIR 84-3007,
    "Thermal Conductivity of Aluminum, Copper, Iron, and Tungsten for Temperatures from 1 K to the Melting Point", 1984.
    https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nbsir84-3007.pdf
    """
    p1: Final[float] = 1.171e-17
    p2: Final[float] = 4.49
    p3: Final[float] = 3.841e10
    p4: Final[
        float
    ] = -1.14  # Appears to be a typo in the original papers... given as 1.14
    p5: Final[float] = 50.0
    p6: Final[float] = 6.428
    p7: Final[float] = 0.4531
    rho_c: Final[float] = (
        0.0  # Experimentally determined deviation from Matthiessen rule (no data)
    )
    p9: Final[float] = 1.553e-8

    t = temperature

    # Compute rho_o
    rho_o = p9 / rrr
    # Compute rho_i
    numerator = p1 * t**p2
    denominator = 1.0 + p1 * p3 * t ** (p2 + p4) * np.exp(-((p5 / t) ** p6))
    rho_i = numerator / denominator + rho_c
    rho_io = p7 * rho_i * rho_o / (rho_i + rho_o)

    # Compute total resistivity
    return rho_o + rho_i + rho_io


def _copper_irradiation_resistivity(fluence: float) -> float:
    """
    Estimate the radiation-induced increase in copper resistivity due to neutron irradiation.

    Parameters
    ----------
    fluence : float
        Total neutron fluence [n/m²].

    Returns
    -------
    float
        Radiation-induced resistivity increase in ohm-meters [Ω·m].

    Notes
    -----
    - Fit to data at low-temperature conditions (around 4.6 K).
    - Fit to data in fast neutron spectrum (E > 0.1 MeV).
    - Damage and transmutation effects are both included.
    - Transmutation effects may be underestimated.
    - This contribution is additive to the base residual resistivity of copper.

    References
    ----------
    M. Kovari, 09/11/2012, internal notes (Excel / Mathcad), Technology Program, WP12, PEX, Super-X Divertor for DEMO.

    M. Nakagawa et al., "High-dose neutron-irradiation effects in fcc metals at 4.6 K",
    *Phys. Rev. B*, 16, 5285 (1977).
    https://doi.org/10.1103/PhysRevB.16.5285
    Figure 6
    """
    c1: Final[float] = 0.00283
    c2: Final[float] = -0.0711
    c3: Final[float] = 0.77982
    res_scale: Final[float] = 1e-9
    flu_scale: Final[float] = 1e-22

    fluence_norm = flu_scale * fluence

    return res_scale * (c1 * fluence_norm**3 + c2 * fluence_norm**2 + c3 * fluence_norm)


def _copper_magneto_resistivity(resistivity: float, field: float) -> float:
    """
    Calculate the increase in copper resistivity due to magnetoresistive effects.

    Parameters
    ----------
    resistivity : float
        Base electrical resistivity of copper [Ω·m].

    field : float
        Magnetic field strength [T].

    Returns
    -------
    float
        Total resistivity including magnetoresistance [Ω·m].

    Notes
    -----
    Resistivity increases with magnetic field due to magnetoresistance effects.

    References
    ----------
    J. Simon, E. S. Drexler, and R. P. Reed, *NIST Monograph 177*,
    "Properties of Copper and Copper Alloys at Cryogenic Temperatures",
    U.S. Government Printing Office, February 1992.
    https://nvlpubs.nist.gov/nistpubs/Legacy/MONO/nistmonograph177.pdf
    Equation 8-7
    """
    p9: Final[float] = 1.553e-8
    # This is necessary as the function is poorly behaved as field tends to 0
    field_cutoff: Final[float] = 1e-2

    if field > field_cutoff:
        poly_coeffs: Final[list[float]] = [-2.662, 0.3168, 0.6229, -0.1839, 0.01827]
        x = np.log10(p9 * field / resistivity)
        a = sum(c * x**i for i, c in enumerate(poly_coeffs))
        return resistivity * (1.0 + 10**a)

    return resistivity


@dependentphysicalproperty(
    ElectricalResistivity,
    op_cond_config={
        "temperature": ("degK", 4, 300),
        "neutron_fluence": ("1/m^2", 0.0, 1.5e23),
    },
    reference=annotate_reference(SIMON_1992, "Equation 8-1, 8-7"),
)
def _copper_electrical_resistivity(
    self: Material, op_cond: OperationalConditions
) -> float:
    """
    Calculate the electrical resistivity of cryogenic copper with combined effects.

    Combines temperature, residual resistivity ratio (RRR), magnetic field, and neutron
    fluence to estimate the total electrical resistivity.

    Parameters
    ----------
    op_cond : OperationalConditions
        The operational conditions, including temperature, for which
        the electrical resistivity is to be calculated.

    Returns
    -------
    float
        Electrical resistivity of copper [Ω·m].

    Notes
    -----
    Includes additive effects from:
    - Temperature-dependent phonon scattering and impurity scattering.
    - Neutron irradiation-induced damage.
    - Magnetoresistive enhancement.

    References
    ----------
    J. Simon, E. S. Drexler, and R. P. Reed, *NIST Monograph 177*,
    "Properties of Copper and Copper Alloys at Cryogenic Temperatures",
    U.S. Government Printing Office, February 1992.
    https://nvlpubs.nist.gov/nistpubs/Legacy/MONO/nistmonograph177.pdf
    Equation 8-1, 8-7

    J. G. Hust, A. B. Lankford, NBSIR 84-3007,
    "Thermal Conductivity of Aluminum, Copper, Iron, and Tungsten for Temperatures from 1 K to the Melting Point", 1984.
    https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nbsir84-3007.pdf

    M. Kovari, 09/11/2012, internal notes (Excel / Mathcad), Technology Program, WP12, PEX, Super-X Divertor for DEMO.

    M. Nakagawa et al., "High-dose neutron-irradiation effects in fcc metals at 4.6 K",
    *Phys. Rev. B*, 16, 5285 (1977).
    https://doi.org/10.1103/PhysRevB.16.5285
    Figure 6
    """
    rho_rrr = _copper_rrr_resistivity(
        op_cond.temperature, self.residual_resistance_ratio(op_cond)
    )
    rho_irr = _copper_irradiation_resistivity(op_cond.neutron_fluence)
    return _copper_magneto_resistivity(rho_rrr + rho_irr, op_cond.magnetic_field)


@rebuild
class CryogenicCopper(FullMaterial):
    name: str = "High-purity cryogenic copper, NIST properties"
    elements: Elements = Field(
        default={
            "Cu": 0.999964,
            "Ag": 0.000011,
            "Pb": 0.000002,
            "S": 0.000011,
            "Se": 0.000001,
            "Ni": 0.000011,
            "fraction_type": "mass",
        },
    )
    properties: PropertiesT_co = props(
        as_field=True,
        poissons_ratio=_copper_poisson_ratio,
        residual_resistance_ratio=100.0,
        youngs_modulus=_copper_youngs_modulus,
        shear_modulus=_copper_shear_modulus,
        bulk_modulus=_copper_bulk_modulus,
        specific_heat_capacity=_copper_specific_heat_capacity,
        thermal_conductivity=_copper_thermal_conductivity,
        coefficient_thermal_expansion=_copper_thermal_expansion_coefficient,
        electrical_resistivity=_copper_electrical_resistivity,
        magnetic_susceptibility=_copper_magnetic_susceptibility,
    )
    reference: References = SIMON_1992
