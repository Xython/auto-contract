"""
code from https://github.com/Xython/YAPyPy/blob/master/yapypy/extended_python/symbol_analyzer.py
"""

import ast
import typing

from typing import NamedTuple, List, Optional, Union
from pprint import pformat
from enum import Enum, auto as _auto


class ContextType(Enum):
    """
    Generator
    Coroutine
    """
    Module = _auto()
    Generator = _auto()  # yield
    Coroutine = _auto()  # async
    Annotation = _auto()
    ClassDef = _auto()


class AnalyzedSymTable(NamedTuple):
    bounds: Optional[set]
    freevars: Optional[set]
    cellvars: Optional[set]
    borrowed_cellvars: Optional[set]


class SymTable:
    requires: set
    entered: set
    explicit_nonlocals: set
    explicit_globals: set
    parent: Optional['SymTable']
    children: List['SymTable']
    depth: int  # to test if it is global context
    analyzed: Optional[AnalyzedSymTable]
    cts: typing.Union[typing.Set[ContextType], typing.FrozenSet[ContextType]]

    def __init__(self, requires: set, entered: set, explicit_nonlocals,
                 explicit_globals, parent, children, depth, analyzed, cts):
        self.requires = requires
        self.entered = entered
        self.explicit_nonlocals = explicit_nonlocals
        self.explicit_globals = explicit_globals
        self.parent = parent
        self.depth = depth
        self.children = children
        self.analyzed = analyzed
        self.cts = cts

    @staticmethod
    def global_context():
        return SymTable(
            requires=set(),
            entered=set(),
            explicit_globals=set(),
            explicit_nonlocals=set(),
            parent=None,
            children=[],
            depth=0,
            analyzed=None,
            cts={ContextType.Module},
        )

    def enter_new(self):
        new = SymTable(
            requires=set(),
            entered=set(),
            explicit_globals=set(),
            explicit_nonlocals=set(),
            parent=self,
            children=[],
            depth=self.depth + 1,
            cts=set(),
            analyzed=None)

        self.children.append(new)
        return new

    def can_resolve_by_parents(self, symbol: str):
        return (symbol in self.analyzed.bounds
                or self.parent and self.parent.can_resolve_by_parents(symbol))

    def resolve_bounds(self):
        enters = self.entered
        nonlocals = self.explicit_nonlocals
        globals_ = self.explicit_globals
        # split bounds
        bounds = {
            each
            for each in enters
            if each not in nonlocals and each not in globals_
        }
        self.analyzed = AnalyzedSymTable(bounds, set(), set(), set())
        return bounds

    def resolve_freevars(self):
        enters = self.entered
        requires = self.requires - enters
        nonlocals = self.explicit_nonlocals
        freevars = self.analyzed.freevars
        freevars.update(
            nonlocals.union({
                each
                for each in requires
                if self.parent.can_resolve_by_parents(each)
            }))

        return freevars

    def resolve_cellvars(self):
        def fetched_from_outside(sym_tb: SymTable):
            return sym_tb.analyzed.freevars.union(
                analyzed.borrowed_cellvars,
                *(fetched_from_outside(each.analyze())
                  for each in sym_tb.children),
            )

        analyzed = self.analyzed
        cellvars = analyzed.cellvars
        bounds = analyzed.bounds
        borrowed_cellvars = analyzed.borrowed_cellvars

        requires_from_sub_contexts = fetched_from_outside(self)

        cellvars.update(requires_from_sub_contexts.intersection(bounds))
        borrowed_cellvars.update(requires_from_sub_contexts - cellvars)
        bounds.difference_update(cellvars)
        return cellvars

    def is_global(self):
        return self.depth == 0

    def analyze(self):
        if self.analyzed is not None:
            return self

        if self.is_global():
            # global context
            self.analyzed = AnalyzedSymTable(set(), set(), set(), set())
            for each in self.children:
                each.analyze()
            return self

        # analyze local table.
        self.resolve_bounds()
        self.resolve_freevars()
        self.resolve_cellvars()
        return self

    def show_resolution(self):
        def show_resolution(this):
            return [
                this.analyzed,
                [show_resolution(each) for each in this.children]
            ]

        return pformat(show_resolution(self))


class Tag(ast.AST):
    it: ast.AST
    tag: SymTable

    def __init__(self, it, tag):
        super().__init__()
        self.it = it
        self.tag = tag

    _fields = 'it',


def _visit_name(self, node: ast.Name):
    symtable = self.symtable
    name = node.id
    if isinstance(node.ctx, ast.Store):
        symtable.entered.add(name)
    elif isinstance(node.ctx, ast.Load):
        symtable.requires.add(name)
    return node


def _visit_import(self, node: ast.ImportFrom):
    for each in node.names:
        name = each.asname or each.name
        self.symtable.entered.add(name)

    return node


def _visit_global(self, node: ast.Global):
    self.symtable.explicit_globals.update(node.names)
    return node


def _visit_nonlocal(self, node: ast.Nonlocal):
    self.symtable.explicit_nonlocals.update(node.names)
    return node


def visit_suite(visit_fn, suite: list):
    return [visit_fn(each) for each in suite]


def _visit_cls(self: 'ASTTagger', node: ast.ClassDef):
    bases = visit_suite(self.visit, node.bases)
    keywords = visit_suite(self.visit, node.keywords)
    decorator_list = visit_suite(self.visit, node.decorator_list)

    self.symtable.entered.add(node.name)

    new = self.symtable.enter_new()

    new.entered.add('__module__')
    new.entered.add('__qualname__')  # pep-3155 nested name.

    new_tagger = ASTTagger(new)
    new.cts.add(ContextType.ClassDef)
    body = visit_suite(new_tagger.visit, node.body)

    node.bases = bases
    node.keywords = keywords
    node.decorator_list = decorator_list
    node.body = body

    return Tag(node, new)


def _visit_list_set_gen_comp(self: 'ASTTagger', node: ast.ListComp):
    new = self.symtable.enter_new()
    new.entered.add('.0')
    new_tagger = ASTTagger(new)
    node.elt = new_tagger.visit(node.elt)
    head, *tail = node.generators
    head.iter = self.visit(head.iter)
    head.target = new_tagger.visit(head.target)
    if head.ifs:
        head.ifs = [new_tagger.visit(each) for each in head.ifs]

    if any(each.is_async for each in node.generators):
        new.cts.add(ContextType.Coroutine)

    node.generators = [head, *[new_tagger.visit(each) for each in tail]]
    return Tag(node, new)


def _visit_dict_comp(self: 'ASTTagger', node: ast.DictComp):
    new = self.symtable.enter_new()
    new.entered.add('.0')
    new_tagger = ASTTagger(new)
    node.key = new_tagger.visit(node.key)
    node.value = new_tagger.visit(node.value)

    head, *tail = node.generators
    head.iter = self.visit(head.iter)
    head.target = new_tagger.visit(head.target)
    if head.ifs:
        head.ifs = [new_tagger.visit(each) for each in head.ifs]

    if any(each.is_async for each in node.generators):
        new.cts.add(ContextType.Coroutine)
    node.generators = [head, *[new_tagger.visit(each) for each in tail]]

    return Tag(node, new)


def _visit_yield(self: 'ASTTagger', node: ast.Yield):
    self.symtable.cts.add(ContextType.Generator)
    return node


def _visit_yield_from(self: 'ASTTagger', node: ast.YieldFrom):
    self.symtable.cts.add(ContextType.Generator)
    return node


def _visit_ann_assign(self: 'ASTTagger', node: ast.AnnAssign):
    self.symtable.cts.add(ContextType.Annotation)
    return node


def _visit_fn_def(self: 'ASTTagger',
                  node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
    self.symtable.entered.add(node.name)
    args = node.args
    visit_suite(self.visit, node.decorator_list)
    visit_suite(self.visit, args.defaults)
    visit_suite(self.visit, args.kw_defaults)

    if node.returns:
        node.returns = self.visit(node.returns)

    new = self.symtable.enter_new()

    if isinstance(node, ast.AsyncFunctionDef):
        new.cts.add(ContextType.Coroutine)

    arguments = args.args + args.kwonlyargs
    if args.vararg:
        arguments.append(args.vararg)
    if args.kwarg:
        arguments.append(args.kwarg)
    for arg in arguments:
        annotation = arg.annotation
        if annotation:
            self.visit(annotation)
        new.entered.add(arg.arg)

    new_tagger = ASTTagger(new)
    node.body = [new_tagger.visit(each) for each in node.body]
    return Tag(node, new)


def _visit_lam(self: 'ASTTagger', node: ast.Lambda):
    args = node.args
    new = self.symtable.enter_new()

    arguments = args.args + args.kwonlyargs
    if args.vararg:
        arguments.append(args.vararg)
    if args.kwarg:
        arguments.append(args.kwarg)
    for arg in arguments:

        # lambda might be able to annotated in the future?
        annotation = arg.annotation
        if annotation:
            self.visit(annotation)
        new.entered.add(arg.arg)

    new_tagger = ASTTagger(new)
    node.body = new_tagger.visit(node.body)
    return Tag(node, new)


class ASTTagger(ast.NodeTransformer):
    def __init__(self, symtable: SymTable):
        self.symtable = symtable

    visit_Name = _visit_name
    visit_Import = _visit_import
    visit_ImportFrom = _visit_import

    visit_Global = _visit_global
    visit_Nonlocal = _visit_nonlocal
    visit_FunctionDef = _visit_fn_def
    visit_AsyncFunctionDef = _visit_fn_def
    visit_Lambda = _visit_lam
    visit_ListComp = visit_SetComp = visit_GeneratorExp = _visit_list_set_gen_comp
    visit_DictComp = _visit_dict_comp

    visit_Yield = _visit_yield
    visit_YieldFrom = _visit_yield_from
    visit_AnnAssign = _visit_ann_assign
    visit_ClassDef = _visit_cls


def to_tagged_ast(node: ast.Module):
    global_table = SymTable.global_context()
    # transform ast node to tagged. visit is an proxy method to spec method.
    node = Tag(ASTTagger(global_table).visit(node), global_table)
    global_table.analyze()
    return node


if __name__ == '__main__':
    import ast

    mod = ("""
def f():
    x = 1
    def g(y):
        t + y
        def z():
            # add some borrowed cellvars to g 
            x + d
    d = 2
    """)
    print(mod)
    mod = ast.parse(mod)

    g = SymTable.global_context()
    ASTTagger(g).visit(mod)

    g.analyze()
    print(g.show_resolution())
