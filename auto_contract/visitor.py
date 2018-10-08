import ast
from .base import Contract
from .sym_ana import Tag, AnalyzedSymTable
from typing import Type

class ContractPerformer(ast.NodeTransformer):
    def __init__(self, *contracts: Type[Contract]):
        self.contracts = contracts
        self.syms = []

    @property
    def current_sym_tb(self) -> AnalyzedSymTable:

        return self.syms[-1]

    def visit_tag(self, node: Tag):

        self.syms.append(node.tag.analyzed)
        node = self.visit(node.it)
        self.syms.pop()
        return node

    visit_Tag = visit_tag

    def visit(self, node):
        """Visit a node."""
        is_tag = isinstance(node, Tag)
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        node = visitor(node)
        if not is_tag:
            sym_tb = self.current_sym_tb
            if all('contract' not in each for each in sym_tb):
                for contract in self.contracts:
                    if contract.predicate(node):
                        node = contract.make(node)

        return node
