from services.blockchain_service import (
    mint_project_for_audit,
)


def main():

    result = mint_project_for_audit(
        audit_id="AUD-8C48CE65EA8C",
        metadata_uri=("ipfs://demo/" "carbon-project.json"),
    )
    print(result)
    print()
    print("Mint success")
    print(
        "Project ID:",
        result["project_id"],
    )
    print(
        "Token ID:",
        result["token_id"],
    )
    print(
        "Owner:",
        result["owner"],
    )
    print(
        "Contract:",
        result["contract_address"],
    )
    print(
        "Transaction:",
        result["tx_hash"],
    )


if __name__ == "__main__":
    main()
