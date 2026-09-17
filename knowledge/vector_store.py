from functools import lru_cache

from langchain_community.vectorstores import (
    FAISS,
)

from config.settings import settings
from knowledge.embeddings import (
    get_embeddings,
)


@lru_cache(maxsize=1)
def get_vector_store():

    print(
        "[VectorStore] Loading FAISS index:",
        settings.FAISS_INDEX_PATH,
    )

    embeddings = get_embeddings()

    return FAISS.load_local(
        settings.FAISS_INDEX_PATH,
        embeddings,
        allow_dangerous_deserialization=True,
    )
