import json
from functools import lru_cache
from pathlib import Path

from web3 import Web3

from blockchain.client import get_web3
from config.settings import settings

ABI_DIR = Path("blockchain/abi")


def load_foundry_abi(
    artifact_path: Path,
) -> list:

    with artifact_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        artifact = json.load(file)

    return artifact["abi"]


def build_contract(
    address: str,
    artifact_path: Path,
):

    web3 = get_web3()

    checksum_address = Web3.to_checksum_address(address)

    code = web3.eth.get_code(checksum_address)

    if not code:
        raise RuntimeError(f"No contract found at " f"{checksum_address}")

    abi = load_foundry_abi(artifact_path)

    return web3.eth.contract(
        address=checksum_address,
        abi=abi,
    )


def get_project_nft_contract():

    artifact = (
        Path(settings.BLOCKCHAIN_CONTRACTS_DIR)
        / "out"
        / "CarbonProjectNFT.sol"
        / "CarbonProjectNFT.json"
    )

    return build_contract(
        settings.CARBON_PROJECT_NFT_ADDRESS,
        artifact,
    )


def get_carbon_credit_contract():

    artifact = (
        Path(settings.BLOCKCHAIN_CONTRACTS_DIR)
        / "out"
        / "CarbonCredit.sol"
        / "CarbonCredit.json"
    )

    return build_contract(
        settings.CARBON_CREDIT_ADDRESS,
        artifact,
    )
