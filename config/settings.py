import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

root_env = BASE_DIR / ".env"
blockchain_env = BASE_DIR / "blockchain-contracts" / ".env"

load_dotenv(root_env)
load_dotenv(blockchain_env)


class Settings:

    # =========================
    # LLM
    # =========================

    DEEPSEEK_MODEL = os.getenv(
        "DEEPSEEK_MODEL",
        "deepseek-chat",
    )

    # =========================
    # Embedding
    # =========================

    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        ("sentence-transformers/" "all-MiniLM-L6-v2"),
    )

    # =========================
    # Vector Store
    # =========================

    FAISS_INDEX_PATH = os.getenv(
        "FAISS_INDEX_PATH",
        "data/faiss/carbon_knowledge",
    )

    # =========================
    # Retrieval
    # =========================

    RETRIEVAL_DISTANCE_THRESHOLD = float(
        os.getenv(
            "RETRIEVAL_DISTANCE_THRESHOLD",
            "0.85",
        )
    )

    # =========================
    # DATABASE
    # =========================
    DATABASE_URL = os.getenv("DATABASE_URL")
    # =========================
    # WEB3
    # =========================
    AVALANCHE_FUJI_RPC_URL = os.getenv(
        "AVALANCHE_FUJI_RPC_URL",
        "https://api.avax-test.network/ext/bc/C/rpc",
    )

    AVALANCHE_CHAIN_ID = int(
        os.getenv(
            "AVALANCHE_CHAIN_ID",
            "43113",
        )
    )

    BLOCKCHAIN_OPERATOR_ADDRESS = os.getenv("ADMIN_ADDRESS")
    BLOCKCHAIN_OPERATOR_PRIVATE_KEY=os.getenv("ADMIN_PRIVATE_KEY")

    CARBON_CREDIT_CONTRACT_ADDRESS = os.getenv("CARBON_CREDIT_CONTRACT_ADDRESS")

    CARBON_PROJECT_NFT_ADDRESS = os.getenv("PROJECT_NFT")
    CARBON_CREDIT_ADDRESS = os.getenv("CARBON_CREDIT")
    
    BLOCKCHAIN_CONTRACTS_DIR="./blockchain-contracts"


settings = Settings()
