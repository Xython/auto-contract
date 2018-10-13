from wisepy.talking import Talking
from importlib import util
from contract.base import Contract
from contract import perform

cli = Talking()


def _check_contract(it):
    if it is Contract:
        return False
    if isinstance(it, type):
        return issubclass(it, Contract)
    return isinstance(it, Contract)


@cli.alias('gen')
def contract_gen(c: 'files to define contracts', i: 'input filename'):
    """
    perform static contracts and generate python stub files.
    """
    with open(i, 'r') as fr:
        source = fr.read()

    spec = util.spec_from_file_location('<contract definition>', c)
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    concrete_contracts = [
        value for value in getattr(mod, '__dict__').values()
        if _check_contract(value)
    ]
    perform(i, *concrete_contracts)


def main():
    cli.on()
