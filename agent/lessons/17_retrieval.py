from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


# ============================================================
# 1. Load document
# ============================================================

loader = TextLoader(
    "docs/carbon-standards/demo_emission_factors.txt"
)

documents = loader.load()


print("\n========== Documents ==========")

print(documents)


# ============================================================
# 2. Split document
# ============================================================

splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50
)

chunks = splitter.split_documents(
    documents
)


print("\n========== Chunks ==========")

for index, chunk in enumerate(chunks):

    print(f"\n--- Chunk {index} ---")

    print(chunk.page_content)


# ============================================================
# 3. Create embedding model
# ============================================================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# 4. Create vector store
# ============================================================

vector_store = FAISS.from_documents(
    chunks,
    embeddings
)


# ============================================================
# 5. Search
# ============================================================

query = input(
    "\nAsk Carbon Knowledge Base: "
)


results = vector_store.similarity_search(
    query,
    k=2
)


# ============================================================
# 6. Print retrieved documents
# ============================================================

print(
    "\n========== Retrieved Documents =========="
)


for index, document in enumerate(results):

    print(
        f"\n--- Result {index + 1} ---"
    )

    print(
        document.page_content
    )