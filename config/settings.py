import os

from dotenv import load_dotenv

load_dotenv()


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

    BLOCKCHAIN_OPERATOR_ADDRESS = os.getenv("BLOCKCHAIN_OPERATOR_ADDRESS")

    CARBON_CREDIT_CONTRACT_ADDRESS = os.getenv("CARBON_CREDIT_CONTRACT_ADDRESS")


settings = Settings()
