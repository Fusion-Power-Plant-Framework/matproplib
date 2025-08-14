# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Serialisation methods for materials"""

import ast
import base64
import inspect
import pickle  # noqa: S403
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from textwrap import dedent
from types import FunctionType
from typing import Any

import asttokens


def pickle_base64(obj):
    return base64.b64encode(pickle.dumps(obj))


def stringify_function(obj):
    src = inspect.getsource(obj)
    psrc = ast.parse(dedent(src))

    decs: list[ast.Call] = psrc.body[0].decorator_list
    for ind in range(len(decs)):
        if decs[ind].func.id == "dependentphysicalproperty":
            del decs[ind]
    return ast.unparse(psrc)


def deserialise(obj: str) -> Callable:
    raise NotImplementedError("Deserialising raw functions is not currently implemented")


# Lambda collection serialisation inspired by MIT licenced https://github.com/Parquery/icontract


@dataclass
class LambdaInspection:
    """Represent the inspection of the callable given as a lambda."""

    atok: asttokens.ASTTokens
    node: ast.Lambda
    text: str = field(init=False)

    def __post_init__(self):
        self.text = ast.unparse(
            ast.parse(self.atok.get_text(self.node).replace("\n", ""))
        )


def is_lambda(func: FunctionType | Callable[..., Any]) -> bool:
    """
    Check whether the callable is a lambda function.

    Parameters
    ----------
    func:
        callable function

    Returns
    -------
    :
        if func is defined as lambda function
    """
    return callable(func) and getattr(func, "__name__", "") == "<lambda>"


def _walk_with_parent(node: ast.AST) -> Iterable[tuple[ast.AST, ast.AST | None]]:
    """Walk the abstract syntax tree by (node, parent).

    Yields
    ------
    :
        ast node
    :
        ast parent node
    """
    stack: list[tuple[ast.AST, ast.AST | None]] = [(node, None)]
    while stack:
        node, parent = stack.pop()

        stack.extend((child, node) for child in ast.iter_child_nodes(node))

        yield node, parent


def inspect_lambda(func: Callable[..., Any]) -> LambdaInspection:  # noqa: C901, PLR0912
    """
    Parse the file in which func resides and figure out the corresponding lambda AST node

    Parameters
    ----------
    func:
        The lambda function

    Returns
    -------
    :
        Inspected lambda function

    Raises
    ------
    ValueError
        Lambda AST node not found
    """
    # Parse the whole file and find the AST node of the func lambda.
    # This is necessary func.__code__ or getsource gives us only a line number which is
    # too vague to find the lambda node.
    lines, func_lineno = inspect.findsource(func)
    atok = asttokens.ASTTokens("".join(lines), parse=True)
    parent_of = dict(_walk_with_parent(atok.tree))

    # node of the lambda wrapping layer
    call_node = None

    for node in ast.walk(atok.tree):
        if isinstance(node, ast.Lambda) and node.lineno - 1 == func_lineno:
            # Go up to the parent node
            ancestor = parent_of[node]
            if ancestor is None:
                raise ValueError(
                    "Expected a parent of the func's lambda AST node, but got None"
                )

            while ancestor is not None and not isinstance(ancestor, ast.Call):
                ancestor = parent_of[ancestor]

            if ancestor is None:
                raise ValueError(
                    "Expected to find a Call AST node above the the func's lambda AST "
                    "node, but found none"
                )

            if not isinstance(ancestor, ast.Call):
                raise ValueError
            call_node = ancestor
            break

    if call_node is None:
        raise ValueError("Expected call_node to be set in the previous execution.")

    if len(call_node.args) > 0 and isinstance(call_node.args[0], ast.Lambda):
        return LambdaInspection(atok, call_node.args[0])
    if len(call_node.keywords) > 0:  # noqa: PLR1702
        for keyword in call_node.keywords:
            # functional definition
            if keyword.arg == "value" and isinstance(keyword.value, ast.Lambda):
                return LambdaInspection(atok, keyword.value)
            # inline lambda
            if keyword.lineno - 1 == func_lineno and isinstance(
                keyword.value, ast.Lambda
            ):
                return LambdaInspection(atok, keyword.value)
            # dictionary definition
            if keyword.lineno == func_lineno:
                if isinstance(keyword.value, ast.Dict):
                    for no, key in enumerate(keyword.value.keys):
                        if key.value == "value" and isinstance(
                            keyword.value.values[no], ast.Lambda
                        ):
                            return LambdaInspection(atok, keyword.value.values[no])
                    raise NotImplementedError(f"No lambda: {keyword.value}")
                raise NotImplementedError(f"Unknown type: {keyword.value}")
        raise NotImplementedError(f"line number not found: {call_node.keywords}")
    raise NotImplementedError(f"No keyword found: {call_node}")
