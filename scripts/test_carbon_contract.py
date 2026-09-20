from blockchain.contracts import (
    get_carbon_credit_contract,
)


def main():

    contract = get_carbon_credit_contract()

    print(
        "Contract:",
        contract.address,
    )

    name = contract.functions.name().call()

    symbol = contract.functions.symbol().call()

    decimals = contract.functions.decimals().call()

    total_supply = contract.functions.totalSupply().call()

    print("Name:", name)
    print("Symbol:", symbol)
    print(
        "Decimals:",
        decimals,
    )
    print(
        "Total Supply:",
        total_supply,
    )


if __name__ == "__main__":
    main()
