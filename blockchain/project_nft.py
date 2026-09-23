from blockchain.contracts import (
    get_project_nft_contract,
)


def build_mint_project_function(
    recipient: str,
    project_id: str,
    metadata_uri: str,
):

    contract = get_project_nft_contract()

    return contract.functions.mintProject(
        recipient,
        project_id,
        metadata_uri,
    )


def parse_project_minted_event(
    receipt,
) -> dict:

    contract = get_project_nft_contract()

    events = contract.events.ProjectMinted().process_receipt(receipt)

    if not events:
        raise RuntimeError("ProjectMinted event " "not found")

    event = events[0]

    return {
        "token_id": (event["args"]["tokenId"]),
        "project_hash": (event["args"]["projectHash"]),
        "project_id": (event["args"]["projectId"]),
        "owner": (event["args"]["owner"]),
    }
