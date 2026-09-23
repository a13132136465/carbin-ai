from blockchain.contracts import (
    get_carbon_project_nft_contract,
    get_carbon_credit_contract,
)


def main():

    project_contract = get_carbon_project_nft_contract()

    credit_contract = get_carbon_credit_contract()

    print(
        "CarbonProjectNFT:",
        project_contract.address,
    )

    print(
        "CarbonCredit:",
        credit_contract.address,
    )


if __name__ == "__main__":
    main()
