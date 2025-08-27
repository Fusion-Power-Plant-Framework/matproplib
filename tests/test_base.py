# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
from matproplib.base import References


class TestReferences:
    def test_multiple_references(self):
        ref = References(
            one={"id": "one", "type": "article"}, two={"id": "two", "type": "article"}
        )

        assert ref.root["one"].id == "one"
        assert ref.root["two"].id == "two"


def test_ci_fail():
    import pytest

    pytest.fail("CI test")
