import ast
import abc


def check_decorator(node: ast.AST, contract_name: str) -> bool:
    ret = False
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id == 'contract':
            args = node.args
            if len(args) is 1 and isinstance(args[0], ast.Name):
                name = args[0]
                ret = name.id == contract_name

    return ret


class Contract(abc.ABC):
    @classmethod
    def predicate(cls, node: ast.AST) -> bool:
        cls_name = cls.__name__
        if hasattr(node, 'decorator_list'):
            return any(
                check_decorator(each, cls_name)
                for each in node.decorator_list)
        return False

    @classmethod
    @abc.abstractmethod
    def make(cls, node: ast.AST) -> ast.AST:
        raise NotImplementedError
