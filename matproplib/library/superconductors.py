# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Superconducting materials"""

from typing import Final

from matproplib.conditions import OpCondT
from matproplib.library.references import CORATO_2016, FERRACIN_2022
from matproplib.material import dependentphysicalproperty, material
from matproplib.properties.dependent import SpecificHeatCapacity
from matproplib.properties.group import props
from matproplib.superconduction import (
    Nb3SnBotturaParameterisation,
    NbTiBotturaParameterisation,
    SummersParameterisation,
)

NBS3N_WST_TF_STRAND = Nb3SnBotturaParameterisation(
    constant=83075.0e6,
    p=0.593,
    q=2.156,
    c_a1=50.06,
    c_a2=0.0,
    eps_0a=0.00312,
    eps_m=-0.00059,
    b_c20m=33.24,
    t_c0max=16.34,
    name="Nb3Sn WST TF Strand",
    reference=CORATO_2016,
)

NB3SN_EUTF4_STRAND = Nb3SnBotturaParameterisation(
    constant=76189.0e6,
    p=0.63,
    q=2.1,
    c_a1=44.48,
    c_a2=0.0,
    eps_0a=0.00256,
    eps_m=-0.00110,
    b_c20m=32.97,
    t_c0max=16.06,
    name="Nb3Sn EUTF4 Strand",
    reference=CORATO_2016,
)

NB3SN_CSJA6_STRAND = Nb3SnBotturaParameterisation(
    constant=79560.0e6,
    p=0.556,
    q=1.698,
    c_a1=45.74,
    c_a2=4.431,
    eps_0a=0.00232,
    eps_m=-0.00061,
    b_c20m=29.39,
    t_c0max=16.48,
    name="Nb3Sn CSJA6 Strand",
    reference=CORATO_2016,
)

NBTI_ITER_STRAND = NbTiBotturaParameterisation(
    constant=168512.0e6,
    alpha=1.0,
    beta=1.54,
    gamma=2.1,
    b_c20=14.61,
    t_c0=9.03,
    name="NbTi ITER Strand",
    reference=CORATO_2016,
)

NB3SN_CERN_STRAND = SummersParameterisation(
    constant=4.31e10,
    alpha=900.0,
    t_c0m=18.0,
    b_c20m=27.6,
    name="Nb3Sn CERN Strand",
    reference=FERRACIN_2022,
)


@dependentphysicalproperty(
    SpecificHeatCapacity,
    op_cond_config={"temperature": ("degK", 4, 300)},
    reference={
        "id": "nb3sn_cp",
        "type": "report",
        "title": (
            "EFDA Material Data Compilation for Superconductor Simulation, "
            "P. Bauer, H. Rajainmaki, E. Salpietro, EFDA CSU, Garching, 04/18/07"
        ),
    },
)
def nbti_specific_heat_capacity(op_cond: OpCondT) -> float:
    """
    Calculates the specific heat capacity of NbTi as a function of temperature.
    Provides the temperature-dependent specific heat capacity [J/(kg·K)] of the A15
    superconductor NbTi.

    Notes
    -----
    The superconducting part is ignored, which is typical in thermal quench calculations.

    - EFDA Material Data Compilation for Superconductor Simulation, P. Bauer,
      H. Rajainmaki, E. Salpietro, EFDA CSU, Garching, 04/18/07.
    - Elrod S.A. Miller J.R., Dresner L.,
     “The specific heat of NbTi from 0-7T between 4.2 and 20K”, Advances in Cryogenic Engineering Materials,
      Vol. 28, 1981
      .. doi:: 10.1007/978-1-4613-3542-9_60
    """  # noqa: DOC201, E501
    gamma: Final[float] = 0.145  # [J/K²/kg] (Grueneisen)
    beta: Final[float] = 0.0023  # [J/K⁴/kg] (Debye)
    cp_300: Final[float] = 400.0  # [J/K/kg] Room-temperature specific heat

    # Normally conducting specific heat capacity (i.e. ignoring transition from
    # superconducting state)
    cp_low = beta * op_cond.temperature**3 + gamma * op_cond.temperature
    return 1.0 / (1.0 / cp_300 + 1.0 / cp_low)


NbTi = material(
    "NbTi",
    elements="NbTi",
    properties=props(
        as_field=True,
        # Large variations in the literature, depending on the alloying elements
        density=6000.0,
        poissons_ratio=0.33,
        specific_heat_capacity=nbti_specific_heat_capacity,
        superconducting_parameterisation=NBTI_ITER_STRAND,
    ),
)


@dependentphysicalproperty(
    SpecificHeatCapacity,
    op_cond_config={"temperature": ("degK", 2, 300)},
    reference={
        "id": "nb3sn_cp",
        "type": "report",
        "title": (
            "EFDA Material Data Compilation for Superconductor Simulation, P. Bauer,"
            " H. Rajainmaki, E. Salpietro, EFDA CSU, Garching, 04/18/07"
        ),
    },
)
def nb3sn_specific_heat_capacity(op_cond: OpCondT) -> float:
    """
    Calculates the specific heat capacity of Nb₃Sn as a function of temperature.
    Provides the temperature-dependent specific heat capacity [J/(kg·K)] of the A15
    superconductor Nb₃Sn.

    Notes
    -----
    The superconducting part is ignored, which is typical in thermal quench calculations.


    - EFDA Material Data Compilation for Superconductor Simulation,
      P. Bauer, H. Rajainmaki, E. Salpietro, EFDA CSU, Garching, 04/18/07.
    - ITER DRG1 Annex, Superconducting Material Database,
      Article 5, N 11 FDR 42 01-07-05 R 0.1.
    - V.D. Arp, Stability and Thermal Quenches in Force-Cooled Superconducting Cables,
      Superconducting MHD Magnet Design Conf., MIT, pp 142-157, 1980.
    - G.S. Knapp, S.D. Bader, Z. Fisk,
      Phonon properties of A-15 superconductors obtained from heat capacity measurements,
      Phys. Rev. B, 13(9), pp 3783-3789, 1976.
      .. doi:: 10.1103/PhysRevB.13.3783
    """  # noqa: DOC201
    gamma: Final[float] = 0.1  # [J/K²/kg] (Grueneisen)
    beta: Final[float] = 0.001  # [J/K⁴/kg] (Debye)
    cp_300: Final[float] = 210.0  # [J/K/kg] Room-temperature specific heat

    # Normally conducting specific heat capacity (i.e. ignoring transition from
    # superconducting state)
    cp_low = beta * op_cond.temperature**3 + gamma * op_cond.temperature
    return 1.0 / (1.0 / cp_300 + 1.0 / cp_low)


Nb3Sn = material(
    "Nb3Sn",
    elements="Nb3Sn",
    properties=props(
        as_field=True,
        # Large variations in the literature,
        # depending on the whether or not Bronze is included
        density=8040.0,
        poissons_ratio=0.33,
        specific_heat_capacity=nb3sn_specific_heat_capacity,
        superconducting_parameterisation=NBS3N_WST_TF_STRAND,
    ),
)
