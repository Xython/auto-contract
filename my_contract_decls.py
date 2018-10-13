import ast

from astpretty import pprint

from contract import Case, Contract
from typing import Dict as _Dict
import copy


class DispatchByName(Contract):
    @classmethod
    def make(cls, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.FunctionDef):
            args = node.args.args
            secs = node.name.split('_')
            if len(secs) is not 2:
                raise ValueError(f"Invalid function name.{node.name}")
            _, typename = secs
            typename = typename.capitalize()
            if args and args[0].annotation is None:
                args[0] = ast.arg(args[0].arg, ast.Name(typename, ast.Load()))
        return node


class AutoOverload(Contract):
    # noinspection PyTypeChecker
    @classmethod
    def make(cls, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.FunctionDef):
            visitor = VarTypeCollector()
            visitor.visit(node)
            cases = visitor.cases
            args: ast.arguments = node.args
            overload_fns = []

            for case in cases:
                new_node = copy.copy(node)
                substitution = AnnotationSubstitution(case)
                new_node.args = substitution.visit(copy.deepcopy(args))
                new_node.body = [ast.Pass()]
                new_node.decorator_list = [ast.Name('overload', ast.Load())]
                overload_fns.append(new_node)
            overload_fns.append(node)
            return overload_fns
        return node


class _VarTypeCollector(ast.NodeVisitor):
    def __init__(self):
        self.args = {}

    def visit_call(self, node: ast.Call):
        func = node.func
        args = node.args
        if isinstance(func, ast.Name) and func.id == 'isinstance':
            assert len(args) is 2
            fst, snd = args
            if isinstance(fst, ast.Name):
                self.args[fst.id] = snd

    visit_Call = visit_call


class VarTypeCollector(ast.NodeVisitor):
    def __init__(self):

        self.cases = []

    def visit_fn(self, node: ast.FunctionDef):
        body = node.body
        for each in body:
            if isinstance(each, ast.If):
                self.visit(each)
                break

    def visit_if(self, node: ast.If):
        visitor = _VarTypeCollector()
        visitor.visit(node.test)
        if visitor.args:
            self.cases.append(visitor.args)
        for each in node.orelse:
            self.visit(each)

    visit_FunctionDef = visit_fn
    visit_If = visit_if


class AnnotationSubstitution(ast.NodeTransformer):
    def __init__(self, case: _Dict[str, ast.AST]):
        self.case = case

    def visit_arg(self, node: ast.arg):
        ident = node.arg
        annotation = self.case.get(ident)
        if annotation:
            if isinstance(annotation, ast.Tuple):
                annotation = ast.Subscript(
                    ast.Name('Union', ast.Load()), ast.Index(annotation),
                    ast.Load())
            return ast.arg(ident, annotation)
        return node
