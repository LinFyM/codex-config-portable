"""Python function metrics and version-family normalization for the guard."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable, Optional


@dataclass(frozen=True)
class FunctionMetric:
    qualname: str
    start: int
    end: int
    lines: int
    complexity: int


class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.value = 1

    def visit_If(self, node: ast.If) -> None:
        self.value += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.value += 1
        self.generic_visit(node)

    visit_AsyncFor = visit_For

    def visit_While(self, node: ast.While) -> None:
        self.value += 1
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self.value += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.value += max(0, len(node.values) - 1)
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self.value += len(node.handlers)
        if node.orelse:
            self.value += 1
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:
        self.value += max(0, len(node.cases) - 1)
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        self.value += 1 + len(node.ifs)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_Lambda = visit_FunctionDef


def function_metrics(text: str) -> tuple[list[FunctionMetric], Optional[str]]:
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [], f"syntax error at line {exc.lineno}: {exc.msg}"

    metrics: list[FunctionMetric] = []

    def walk(body: Iterable[ast.stmt], prefix: tuple[str, ...]) -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = getattr(node, "end_lineno", node.lineno)
                visitor = ComplexityVisitor()
                for statement in node.body:
                    visitor.visit(statement)
                metrics.append(
                    FunctionMetric(
                        qualname=".".join((*prefix, node.name)),
                        start=node.lineno,
                        end=end,
                        lines=end - node.lineno + 1,
                        complexity=visitor.value,
                    )
                )
                walk(node.body, (*prefix, node.name))
            elif isinstance(node, ast.ClassDef):
                walk(node.body, (*prefix, node.name))

    walk(tree.body, ())
    return metrics, None


VERSION_TOKEN = re.compile(
    r"(?i)(?:^|[_-])(?:v|ver|version|rev|recovery|attempt|phase)[_-]?\d+(?=$|[_-])"
)
FUNCTION_VERSION_TOKEN = re.compile(
    r"(?i)(?:_(?:v|ver|version|rev|attempt|phase)[_-]?\d+)(?=$|_)"
)


def normalized_version_path(path: str) -> str:
    pure = PurePosixPath(path)
    stem = VERSION_TOKEN.sub("_<variant>", pure.stem)
    return str(pure.with_name(stem + pure.suffix))


def normalized_function_name(name: str) -> str:
    return FUNCTION_VERSION_TOKEN.sub("", name)
