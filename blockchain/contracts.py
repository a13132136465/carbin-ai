import json
from functools import lru_cache
from pathlib import Path

from web3 import Web3

from blockchain.client import get_web3
from config.settings import settings

ABI_DIR = Path("blockchain/abi")


def load_abi(
    filename: str,
) -> list:

    path = ABI_DIR / filename

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        artifact = json.load(file)

    return artifact["abi"]


@lru_cache(maxsize=1)
def get_carbon_credit_contract():

    web3 = get_web3()

    address = Web3.to_checksum_address(settings.CARBON_CREDIT_CONTRACT_ADDRESS)

    code = web3.eth.get_code(address)

    if len(code) == 0:
        raise RuntimeError("No contract deployed " f"at address {address}")

    abi = load_abi("CarbonCredit.json")

    return web3.eth.contract(
        address=address,
        abi=abi,
    )
