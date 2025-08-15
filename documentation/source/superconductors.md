# Superconductors

## Superconducting parameterisations

Superconductors are often characterised by their critical surface in terms of the current density as a function of applied temperature, magnetic field, and strain: $J_c(T,B,\varepsilon)$.

Superconducting parameterisations take many forms. At present, three formulations are provided:
 - [Summers parameterisation](https://scispace.com/pdf/a-model-for-the-prediction-of-nb-sub-3-sn-critical-current-xoujezlpxh.pdf)
 - [Bottura-Bordini Nb<sub>3</sub>Sn parameterisation](https://doi.org/10.1109/TASC.2009.2018278)
 - [Bottura NbTi parameterisation](https://doi.org/10.1109/77.828413)

 Each parameterisation takes a range of free parameters. For example, one can instantiate a superconducting parameterisation:

```python
from matproplib.superconduction import Nb3SnBotturaParameterisation

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
)
```
Values above from [Corato et al.](https://scipub.euro-fusion.org/wp-content/uploads/eurofusion/WPMAGREP16_16565_submitted.pdf).

## Superconducting materials

A superconducting material can be specified by assigning it a `superconducting_parameterisation`. Doing so will endow it with an additional material property: `critical_current_density` [A/m<sup>2</sup>]

```python
from matproplib.material import material
from matproplib.properties.group import props
from matproplib.conditions import OperationalConditions
Nb3Sn = material(
    "Nb3Sn",
    elements="Nb3Sn",
    properties=props(
        as_field=True,
        density=8040.0,
        superconducting_parameterisation=NBS3N_WST_TF_STRAND,
    )
)
myNb3Sn = Nb3Sn()
op_cond = OperationalConditions(temperature=4.7, magnetic_field=13, strain=-0.0055)
print(f"J_c = {myNb3Sn.critical_current_density(op_cond)/1e6} A/mm^2")
```

N.B.: The formulations of these superconducting parameterisations is invariably such that negative or NaN results can be obtained if the operational conditions would drive the superconductor to no longer be superconducting. A variety of numerical fudges are employed here to ensure that the results are always positive or 0.0. These fudges will affect the critical current density around the transition region (at very low current densities). Results at very low current densities (< 20 A/m<sup>2</sup>) should not be trusted.
