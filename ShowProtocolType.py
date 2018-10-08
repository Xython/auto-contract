import typing as t

T = t.TypeVar('T')
G = t.TypeVar('G')


class ICopy(t.Protocol[T]):
    def copy(self) -> 't.Protocol[T]':
        return self


class MyAPI:
    @t.overload
    def apply(self, arg1: ICopy[T], arg2: ICopy[G]):
        ...

    @t.overload
    def apply(self, arg1: int, arg2: int):
        ...

    def apply(self, *args, **kwargs):
        # implementation
        pass


s = MyAPI()
s.apply(1.0)  # get warning
s.apply([])  # get warning
s.apply(1, 2)
s.apply({}, {})
s.apply([], {})
