from web3 import Web3

from blockchain.contracts import (
    get_carbon_credit_contract,
)


def get_token_name() -> str:

    contract = get_carbon_credit_contract()

    return contract.functions.name().call()


def get_total_supply() -> int:

    contract = get_carbon_credit_contract()

    return contract.functions.totalSupply().call()


def get_balance(
    address: str,
) -> int:

    contract = get_carbon_credit_contract()

    checksum_address = Web3.to_checksum_address(address)

    return contract.functions.balanceOf(checksum_address).call()
