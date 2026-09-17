from pathlib import Path

from langchain_community.document_loaders import (
    TextLoader,
)
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from langchain_community.vectorstores import (
    FAISS,
)

from knowledge.embeddings import (
    get_embeddings,
)

# ============================================================
# 1. Paths
# ============================================================


DOCUMENT_PATH = Path("docs/carbon-standards/" "demo_emission_factors.txt")


INDEX_PATH = Path("data/faiss/carbon_knowledge")


# ============================================================
# 2. Load Documents
# ============================================================


def load_documents():

    print("\n[load_documents]")

    if not DOCUMENT_PATH.exists():

        raise FileNotFoundError(
            "Knowledge document does " "not exist: " f"{DOCUMENT_PATH}"
        )

    loader = TextLoader(
        str(DOCUMENT_PATH),
        encoding="utf-8",
    )

    documents = loader.load()

    print(
        "Loaded documents:",
        len(documents),
    )

    return documents


# ============================================================
# 3. Split Documents
# ============================================================


def split_documents(
    documents,
):

    print("\n[split_documents]")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
    )

    chunks = splitter.split_documents(documents)

    print(
        "Created chunks:",
        len(chunks),
    )

    for index, chunk in enumerate(chunks):

        print(f"\n--- Chunk {index} ---")

        print(chunk.page_content)

        print(
            "Metadata:",
            chunk.metadata,
        )

    return chunks


# ============================================================
# 4. Build FAISS Index
# ============================================================


def build_index(
    chunks,
):

    print("\n[build_index]")

    embeddings = get_embeddings()

    vector_store = FAISS.from_documents(
        chunks,
        embeddings,
    )

    print("FAISS index created")

    return vector_store


# ============================================================
# 5. Save Index
# ============================================================


def save_index(
    vector_store,
):

    print("\n[save_index]")

    INDEX_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    vector_store.save_local(str(INDEX_PATH))

    print("FAISS index saved to:")

    print(INDEX_PATH)


# ============================================================
# 6. Main
# ============================================================


def main():

    print("\n========== " "CarbonAI Knowledge Index Builder " "==========")

    documents = load_documents()

    chunks = split_documents(documents)

    vector_store = build_index(chunks)

    save_index(vector_store)

    print("\n========== " "Index Build Completed " "==========")


if __name__ == "__main__":
    main()
