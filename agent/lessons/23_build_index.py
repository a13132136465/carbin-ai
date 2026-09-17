from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


# ============================================================
# 1. Load documents
# ============================================================

loader = TextLoader(
    "docs/carbon-standards/demo_emission_factors.txt"
)

documents = loader.load()

print(
    f"Loaded documents: {len(documents)}"
)


# ============================================================
# 2. Split documents
# ============================================================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
)

chunks = splitter.split_documents(
    documents
)

print(
    f"Created chunks: {len(chunks)}"
)


# ============================================================
# 3. Embedding model
# ============================================================

embeddings = HuggingFaceEmbeddings(
    model_name=(
        "sentence-transformers/"
        "all-MiniLM-L6-v2"
    )
)


# ============================================================
# 4. Build FAISS index
# ============================================================

vector_store = FAISS.from_documents(
    chunks,
    embeddings,
)


# ============================================================
# 5. Save index
# ============================================================

INDEX_PATH = "data/faiss/carbon_knowledge"

vector_store.save_local(
    INDEX_PATH
)

print(
    f"FAISS index saved to: {INDEX_PATH}"
)