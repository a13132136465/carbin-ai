from enum import Enum


class BlockchainTxType(str, Enum):

    MINT_PROJECT_NFT = "MINT_PROJECT_NFT"

    MINT_CREDIT = "MINT_CREDIT"

    RETIRE_CREDIT = "RETIRE_CREDIT"
