import typing as t
from auto_contract import perform
import auto_contract
try:
    from .arg2 import *

except ImportError:
    pass


class NamedListMeta(type):
    def __new__(mcs, name, bases, ns: dict):
        if ns.get('_root'):
            return super().__new__(mcs, name, bases, ns)
        annotations = ns.get('__annotations__')
        if not annotations:

            def __init__(self):
                pass
        else:
            annotations = tuple(annotations)

            def __init__(self: list, *args, **kwargs):
                data = {**dict(zip(annotations, args)), **kwargs}
                try:
                    for attr in annotations:
                        self.append(data[attr])
                except KeyError:
                    raise ValueError(f"Field {attr!r} is not specified!")

        def __repr__(self):
            return '{}[{}]'.format(
                name, ', '.join(f'{attr}={self[idx]}'
                                for idx, attr in enumerate(annotations)))

        bases = tuple(each for each in bases if each is not NamedList)
        if list not in bases:
            bases = (*bases, list)
        cls = type(name, bases, ns)
        cls.__init__ = __init__
        cls.__repr__ = __repr__

        return cls


class NamedList(metaclass=NamedListMeta):
    _root = True


@auto_contract.Case
class MyT(NamedList):
    a: int
    b: int
    c: int
    d: int


if __name__ == '__main__':
    perform(__file__, auto_contract.Case)

auto_contract.Other: t.Callable
