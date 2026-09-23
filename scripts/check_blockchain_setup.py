# scripts/check_blockchain_setup.py

from web3 import Web3

from blockchain.client import get_web3
from blockchain.contracts import (
    get_project_nft_contract,
    get_carbon_credit_contract,
)
from config.settings import settings

# AccessControl:
# DEFAULT_ADMIN_ROLE 永远是 bytes32(0)
DEFAULT_ADMIN_ROLE = bytes(32)


def print_title(title: str):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def print_check(
    name: str,
    success: bool,
    value=None,
):
    status = "OK" if success else "FAIL"

    if value is None:
        print(f"[{status}] {name}")
    else:
        print(f"[{status}] " f"{name}: {value}")


def has_function(
    contract,
    function_name: str,
) -> bool:
    """
    Check whether a function exists in the loaded ABI.
    """

    return any(
        item.get("type") == "function" and item.get("name") == function_name
        for item in contract.abi
    )


def check_contract_code(
    web3: Web3,
    name: str,
    address: str,
):
    """
    Verify that EVM bytecode exists at the contract address.
    """

    code = web3.eth.get_code(address)

    exists = len(code) > 0

    print_check(
        f"{name} bytecode",
        exists,
        (f"{len(code)} bytes" if exists else "No bytecode"),
    )

    return exists


def check_role(
    contract,
    role: bytes,
    account: str,
    label: str,
):
    """
    Call AccessControl.hasRole(bytes32,address).

    This is a read-only eth_call.
    """

    if not has_function(
        contract,
        "hasRole",
    ):
        print_check(
            label,
            False,
            "hasRole() not found in ABI",
        )
        return False

    try:
        result = contract.functions.hasRole(
            role,
            account,
        ).call()

        print_check(
            label,
            result,
            result,
        )

        return result

    except Exception as e:
        print_check(
            label,
            False,
            str(e),
        )

        return False


def read_role_constant(
    contract,
    function_name: str,
):
    """
    Read role constants exposed as public Solidity values.

    Example:

        bytes32 public constant ISSUER_ROLE =
            keccak256("ISSUER_ROLE");

    Solidity automatically generates:

        ISSUER_ROLE() -> bytes32
    """

    if not has_function(
        contract,
        function_name,
    ):
        return None

    try:
        return getattr(
            contract.functions,
            function_name,
        )().call()

    except Exception:
        return None


def print_business_function_check(
    contract,
    function_name: str,
):
    exists = has_function(
        contract,
        function_name,
    )

    print_check(
        f"ABI function {function_name}()",
        exists,
    )


def main():

    print_title("CarbonAI Blockchain Setup Check")

    # --------------------------------------------------
    # 1. Web3 / Network
    # --------------------------------------------------

    web3 = get_web3()

    connected = web3.is_connected()

    print_check(
        "RPC connected",
        connected,
    )

    if not connected:
        raise RuntimeError("Unable to connect to " "Avalanche Fuji RPC")

    chain_id = web3.eth.chain_id

    expected_chain_id = settings.AVALANCHE_CHAIN_ID

    print_check(
        "Chain ID",
        chain_id == expected_chain_id,
        chain_id,
    )

    print(
        "Expected Chain ID:",
        expected_chain_id,
    )

    print(
        "Latest block:",
        web3.eth.block_number,
    )

    # --------------------------------------------------
    # 2. Operator Wallet
    # --------------------------------------------------

    print_title("Operator Wallet")

    operator_raw = settings.BLOCKCHAIN_OPERATOR_ADDRESS

    if not operator_raw:
        raise RuntimeError("BLOCKCHAIN_OPERATOR_ADDRESS " "is not configured")

    operator = Web3.to_checksum_address(operator_raw)

    print(
        "Operator:",
        operator,
    )

    balance_wei = web3.eth.get_balance(operator)

    balance_avax = web3.from_wei(
        balance_wei,
        "ether",
    )

    print(
        "Balance:",
        balance_avax,
        "AVAX",
    )

    print_check(
        "Operator has AVAX",
        balance_wei > 0,
        f"{balance_avax} AVAX",
    )

    # --------------------------------------------------
    # 3. Load Contracts
    # --------------------------------------------------

    print_title("Contract Addresses")

    project_contract = get_project_nft_contract()

    credit_contract = get_carbon_credit_contract()

    print(
        "CarbonProjectNFT:",
        project_contract.address,
    )

    print(
        "CarbonCredit:",
        credit_contract.address,
    )

    # --------------------------------------------------
    # 4. Verify bytecode
    # --------------------------------------------------

    print_title("Contract Bytecode")

    check_contract_code(
        web3,
        "CarbonProjectNFT",
        project_contract.address,
    )

    check_contract_code(
        web3,
        "CarbonCredit",
        credit_contract.address,
    )

    # --------------------------------------------------
    # 5. DEFAULT_ADMIN_ROLE
    # --------------------------------------------------

    print_title("AccessControl")

    check_role(
        project_contract,
        DEFAULT_ADMIN_ROLE,
        operator,
        ("CarbonProjectNFT " "DEFAULT_ADMIN_ROLE"),
    )

    check_role(
        credit_contract,
        DEFAULT_ADMIN_ROLE,
        operator,
        ("CarbonCredit " "DEFAULT_ADMIN_ROLE"),
    )

    # --------------------------------------------------
    # 6. CarbonCredit ISSUER_ROLE
    # --------------------------------------------------

    issuer_role = read_role_constant(
        credit_contract,
        "ISSUER_ROLE",
    )

    if issuer_role is not None:

        print(
            "CarbonCredit ISSUER_ROLE:",
            Web3.to_hex(issuer_role),
        )

        check_role(
            credit_contract,
            issuer_role,
            operator,
            ("CarbonCredit " "ISSUER_ROLE"),
        )

    else:

        print_check(
            "CarbonCredit ISSUER_ROLE",
            False,
            ("ISSUER_ROLE() " "not found in ABI"),
        )

    # --------------------------------------------------
    # 7. CarbonProjectNFT mint role
    # --------------------------------------------------

    # Different versions may call this:
    #
    # MINTER_ROLE
    # ISSUER_ROLE
    #
    # Check the actual deployed ABI.

    project_role = None
    project_role_name = None

    for candidate in [
        "MINTER_ROLE",
        "ISSUER_ROLE",
    ]:

        role = read_role_constant(
            project_contract,
            candidate,
        )

        if role is not None:
            project_role = role
            project_role_name = candidate
            break

    if project_role is not None:

        print(
            ("CarbonProjectNFT " f"{project_role_name}:"),
            Web3.to_hex(project_role),
        )

        check_role(
            project_contract,
            project_role,
            operator,
            ("CarbonProjectNFT " f"{project_role_name}"),
        )

    else:

        print(
            "[WARN] No MINTER_ROLE() " "or ISSUER_ROLE() found " "on CarbonProjectNFT"
        )

    # --------------------------------------------------
    # 8. CarbonProjectNFT business ABI
    # --------------------------------------------------

    print_title("CarbonProjectNFT ABI")

    # These checks don't call the contract.
    # They only check whether functions exist
    # in the loaded ABI.
    #
    # If your actual function names differ,
    # replace these names with the deployed
    # contract's functions.

    for function_name in [
        "ownerOf",
        "balanceOf",
        "supportsInterface",
    ]:
        print_business_function_check(
            project_contract,
            function_name,
        )

    # --------------------------------------------------
    # 9. CarbonCredit business ABI
    # --------------------------------------------------

    print_title("CarbonCredit ABI")

    for function_name in [
        "balanceOf",
        "supportsInterface",
        "hasRole",
        "ISSUER_ROLE",
        "getBatch",
        "mintCredit",
    ]:
        print_business_function_check(
            credit_contract,
            function_name,
        )

    # --------------------------------------------------
    # 10. ERC interface checks
    # --------------------------------------------------

    print_title("ERC Interface Checks")

    # ERC721 interface id
    ERC721_INTERFACE_ID = bytes.fromhex("80ac58cd")

    # ERC1155 interface id
    ERC1155_INTERFACE_ID = bytes.fromhex("d9b67a26")

    try:

        is_erc721 = project_contract.functions.supportsInterface(
            ERC721_INTERFACE_ID
        ).call()

        print_check(
            "CarbonProjectNFT is ERC721",
            is_erc721,
            is_erc721,
        )

    except Exception as e:

        print_check(
            "CarbonProjectNFT ERC721 check",
            False,
            str(e),
        )

    try:

        is_erc1155 = credit_contract.functions.supportsInterface(
            ERC1155_INTERFACE_ID
        ).call()

        print_check(
            "CarbonCredit is ERC1155",
            is_erc1155,
            is_erc1155,
        )

    except Exception as e:

        print_check(
            "CarbonCredit ERC1155 check",
            False,
            str(e),
        )

    # --------------------------------------------------
    # Finish
    # --------------------------------------------------

    print_title("Check Finished")

    print("Blockchain integration " "read-only checks completed.")


if __name__ == "__main__":
    main()
