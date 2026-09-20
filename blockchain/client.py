from functools import lru_cache

from web3 import Web3

from config.settings import settings


@lru_cache(maxsize=1)
def get_web3() -> Web3:

    web3 = Web3(Web3.HTTPProvider(settings.AVALANCHE_FUJI_RPC_URL))

    return web3


def verify_network(
    web3: Web3,
):

    chain_id = web3.eth.chain_id

    if chain_id != settings.AVALANCHE_CHAIN_ID:
        raise RuntimeError(
            "Unexpected chain ID. "
            f"Expected "
            f"{settings.AVALANCHE_CHAIN_ID}, "
            f"got {chain_id}"
        )


@lru_cache(maxsize=1)
def get_web3() -> Web3:

    web3 = Web3(Web3.HTTPProvider(settings.AVALANCHE_FUJI_RPC_URL))

    if not web3.is_connected():
        raise RuntimeError("Unable to connect " "to Avalanche RPC")

    verify_network(web3)

    return web3


def get_chain_id() -> int:

    web3 = get_web3()

    return web3.eth.chain_id


def get_native_balance(
    address: str,
):

    web3 = get_web3()

    checksum_address = Web3.to_checksum_address(address)

    balance_wei = web3.eth.get_balance(checksum_address)

    return web3.from_wei(
        balance_wei,
        "ether",
    )
