from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


INDEX_PATH = "data/faiss/carbon_knowledge"


# ============================================================
# 1. Load embedding model
# ============================================================

embeddings = HuggingFaceEmbeddings(
    model_name=(
        "sentence-transformers/"
        "all-MiniLM-L6-v2"
    )
)


# ============================================================
# 2. Load existing FAISS index
# ============================================================

vector_store = FAISS.load_local(
    INDEX_PATH,
    embeddings,
    allow_dangerous_deserialization=True,
)


# ============================================================
# 3. Search
# ============================================================

query = input(
    "\nAsk Carbon Knowledge Base: "
)

results = (
    vector_store
    .similarity_search_with_score(
        query,
        k=2,
    )
)


print(
    "\n========== Results =========="
)

for index, (document, score) in enumerate(
    results
):
    print(
        f"\n--- Result {index + 1} ---"
    )

    print(
        "Score:",
        score
    )

    print(
        document.page_content
    )