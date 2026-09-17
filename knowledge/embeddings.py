from functools import lru_cache

from langchain_huggingface import (
    HuggingFaceEmbeddings,
)

from config.settings import settings


@lru_cache(maxsize=1)
def get_embeddings():

    print(
        "[Embedding] Loading model:",
        settings.EMBEDDING_MODEL,
    )

    return HuggingFaceEmbeddings(model_name=(settings.EMBEDDING_MODEL))
