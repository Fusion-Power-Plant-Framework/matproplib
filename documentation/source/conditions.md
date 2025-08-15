# Operational conditions

Material properties depend on the operational conditions to which the material is subjected. Most commonly, material property parameterisations are temperature-dependent. However, parameterisations may exist for a wide variety of other conditions, such as magnetic field and radiation damage.

In `matproplib` all material properties are called with an `OperationalConditions` object. The following fields are available by default:

| Operational Condition Name                      | Units         | Definition                                                        |
|-------------------------------------|--------------|-------------------------------------------------------------------|
| temperature                           | K        | Operational temperature.                                            |
| pressure| Pa | Operational pressure (fluids).
| magnetic_field                     | T             | Operational magnetic field.                                                  |
| strain | — | Operational strain.
| neutron_damage         | dpa             | Operational neutron damage (displacements per atom).                                        |
| neutron_fluence         | 1/m^2             | Operational neutron fluence.                                        |
