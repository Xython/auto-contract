import ast
import abc


def check_decorator(node: ast.AST, contract_name: str):
    if isinstance(node, ast.Attribute) and isinstance(
            node.value, ast.Name) and node.value.id == 'contract':

        return node.attr == contract_name
    return False


class Contract(abc.ABC):
    def __new__(cls, f):
        """作为装饰器被调用，但在运行模块中无实际语义"""
        return f

    @classmethod
    def predicate(cls, node: ast.AST) -> bool:
        cls_name = cls.__name__
        if hasattr(node, 'decorator_list'):
            if any(
                    check_decorator(each, cls_name)
                    for each in node.decorator_list):
                return True

        return False

    @classmethod
    @abc.abstractmethod
    def make(cls, node: ast.AST) -> ast.AST:
        raise NotImplementedError
