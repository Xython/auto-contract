from my_contract_decls import *
from contract import contract
from typing import overload, Union

class Animal:
    pass


class Dog(Animal):
    pass


class Cat(Animal):
    pass


@contract(DispatchByName)
def process_animal(inst, *args, **kwargs):
    raise NotImplementedError


@contract(DispatchByName)
def process_dog(inst, *args, **kwargs):
    return NotImplementedError


@contract(DispatchByName)
def process_cat(inst, *args, **kwargs):
    return NotImplementedError


@contract(AutoOverload)
def fn(x, y, z):
    if isinstance(x, int) and isinstance(y, str):
        ...
    elif isinstance(x, Animal) and isinstance(z, float):
        ...
    ...
