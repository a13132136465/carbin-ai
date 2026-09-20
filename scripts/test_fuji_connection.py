from web3 import Web3

from blockchain.client import get_web3
from config.settings import settings


def main():

    web3 = get_web3()

    address = Web3.to_checksum_address(settings.BLOCKCHAIN_OPERATOR_ADDRESS)

    balance_wei = web3.eth.get_balance(address)

    balance_avax = web3.from_wei(
        balance_wei,
        "ether",
    )

    print(
        "Address:",
        address,
    )

    print(
        "Balance Wei:",
        balance_wei,
    )

    print(
        "Balance AVAX:",
        balance_avax,
    )

if __name__ == "__main__":
    main()