import ast
import copy
from .base import check_decorator, Contract


class Case(Contract):

    @classmethod
    def make(cls, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.ClassDef):
            ann_assigns = [
                each for each in node.body if isinstance(each, ast.AnnAssign)
                and isinstance(each.target, ast.Name)
            ]

            cons = ast.FunctionDef(
                name='__init__',
                args=ast.arguments(
                    args=[
                        ast.arg('self', None), *[
                            ast.arg(each.target.id, each.annotation)
                            for each in ann_assigns
                        ]
                    ],
                    vararg=None,
                    kwonlyargs=[],
                    kwarg=None,
                    defaults=[]),
                body=[ast.Pass()],
                decorator_list=[],
                returns=None,
            )

            node = copy.copy(node)
            lst = node.decorator_list
            lst = [
                each for each in lst
                if not check_decorator(each, cls.__name__)
            ]
            node.body.insert(0, cons)
            node.decorator_list = lst
            return node
        return node
