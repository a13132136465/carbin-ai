from web3 import Web3
from web3.exceptions import (
    TransactionNotFound,
)

from blockchain.client import get_web3
from config.settings import settings


def get_operator_address() -> str:

    address = settings.BLOCKCHAIN_OPERATOR_ADDRESS

    if not address:
        raise RuntimeError("BLOCKCHAIN_OPERATOR_ADDRESS " "is not configured")

    return Web3.to_checksum_address(address)


def get_operator_private_key() -> str:

    private_key = settings.BLOCKCHAIN_OPERATOR_PRIVATE_KEY

    if not private_key:
        raise RuntimeError("BLOCKCHAIN_OPERATOR_PRIVATE_KEY " "is not configured")

    return private_key


def verify_operator_account():

    web3 = get_web3()

    expected_address = get_operator_address()

    private_key = get_operator_private_key()

    account = web3.eth.account.from_key(private_key)

    actual_address = Web3.to_checksum_address(account.address)

    if actual_address != expected_address:
        raise RuntimeError(
            "Operator private key " "does not match " "BLOCKCHAIN_OPERATOR_ADDRESS"
        )


def broadcast_contract_transaction(
    contract_function,
) -> str:

    verify_operator_account()

    web3 = get_web3()

    operator = get_operator_address()

    private_key = get_operator_private_key()

    nonce = web3.eth.get_transaction_count(
        operator,
        "pending",
    )

    gas_estimate = contract_function.estimate_gas(
        {
            "from": operator,
        }
    )

    gas_limit = int(gas_estimate * 1.2)

    transaction = contract_function.build_transaction(
        {
            "from": operator,
            "nonce": nonce,
            "chainId": (web3.eth.chain_id),
            "gas": gas_limit,
            "gasPrice": (web3.eth.gas_price),
        }
    )

    signed = web3.eth.account.sign_transaction(
        transaction,
        private_key=private_key,
    )

    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)

    return tx_hash.hex()


def wait_for_transaction_receipt(
    tx_hash: str,
    timeout: int = 120,
):

    web3 = get_web3()

    return web3.eth.wait_for_transaction_receipt(
        tx_hash,
        timeout=timeout,
    )


def get_transaction_receipt(
    tx_hash: str,
):

    web3 = get_web3()

    try:

        return web3.eth.get_transaction_receipt(tx_hash)

    except TransactionNotFound:

        return None
