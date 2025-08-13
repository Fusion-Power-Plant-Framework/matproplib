# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
import numpy as np
import pytest
from pydantic_core import ValidationError


def _np_and_value_test(thing, inp):
    if isinstance(inp, np.ndarray):
        np.testing.assert_allclose(thing.value, inp)
        assert thing.value.size == inp.size
    else:
        assert np.isclose(thing.value, inp)

    with pytest.raises(ValidationError, match="1 valid"):
        thing.value = 5
