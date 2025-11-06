# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
import warnings

import matplotlib as mpl
import numpy as np
import pytest


@pytest.fixture
def test_material():
    from matproplib.converters.neutronics import (
        FispactNeutronicConfig,
    )
    from matproplib.material import material
    from matproplib.properties.group import props
    from matproplib.superconduction import (
        Nb3SnBotturaParameterisation,
    )

    return material(
        "TestMat",
        elements="C1Fe12",
        properties=props(
            density=5,
            specific_heat_capacity={
                "value": lambda properties, oc: properties.density(oc) * oc.temperature,
                "unit": "J/g/K",
                "op_cond_config": {"temperature": ("K", 100, 300)},
            },
            superconducting_parameterisation=Nb3SnBotturaParameterisation(
                constant=1,
                p=2,
                q=3,
                c_a1=4,
                c_a2=5,
                eps_0a=6,
                eps_m=7,
                b_c20m=8,
                t_c0max=9,
                reference=None,
            ),
        ),
        converters=FispactNeutronicConfig(volume=3),
    )()


@pytest.fixture
def test_condition():
    from matproplib.conditions import OperationalConditions

    return OperationalConditions(temperature=np.array([298, 200]), pressure=(1, "atm"))


@pytest.fixture
def condition():
    from matproplib.conditions import OperationalConditions

    return OperationalConditions(temperature=298, pressure=(1, "atm"))


def pytest_addoption(parser):
    """
    Adds a custom command line option to pytest to control plotting.
    """
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="only run integration tests",
    )
    parser.addoption(
        "--plotting-on",
        action="store_true",
        default=False,
        help="switch on interactive plotting in tests",
    )


def pytest_configure(config):
    """
    Configures pytest with the plotting command line options.
    """
    options = {"integration": config.option.integration}

    if not config.option.plotting_on:
        # We're not displaying plots so use a display-less backend
        mpl.use("Agg")
    config.option.markexpr = config.getoption(
        "markexpr",
        " and ".join([
            name if value else f"not {name}" for name, value in options.items()
        ]),
    )
    if not config.option.markexpr:
        config.option.markexpr = " and ".join([
            name if value else f"not {name}" for name, value in options.items()
        ])


@pytest.fixture(autouse=True)
def _plot_show_and_close(request):
    """Fixture to show and close plots

    Notes
    -----
    Does not do anything if testclass marked with 'classplot'
    """
    import matplotlib.pyplot as plt

    cls = request.node.getparent(pytest.Class)

    if cls and "classplot" in cls.keywords:
        yield
    else:
        yield
        clstitle = "" if cls is None else cls.name
        for fig in list(map(plt.figure, plt.get_fignums())):
            fig.suptitle(
                f"{fig.get_suptitle()} {clstitle}::"
                f"{request.node.getparent(pytest.Function).name}"
            )
        supress_warning_show(plt)
        plt.close()


def supress_warning_show(plt):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.show()


@pytest.fixture(scope="class", autouse=True)
def _plot_show_and_close_class(request):
    """Fixture to show and close plots for marked classes

    Notes
    -----
    Only shows and closes figures on classes marked with 'classplot'
    """
    import matplotlib.pyplot as plt

    if "classplot" in request.keywords:
        yield
        clstitle = request.node.getparent(pytest.Class).name

        for fig in list(map(plt.figure, plt.get_fignums())):
            fig.suptitle(f"{fig.get_suptitle()} {clstitle}")
        supress_warning_show(plt)
        plt.close()
    else:
        yield
