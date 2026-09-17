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


settings = Settings()
