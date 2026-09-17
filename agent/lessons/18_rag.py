from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
)

load_dotenv()

model = ChatDeepSeek(model="deepseek-chat")

# ============================================================
# 1. Load document
# ============================================================

loader = TextLoader("docs/carbon-standards/demo_emission_factors.txt")

documents = loader.load()


print("\n========== Documents ==========")

print(documents)


# ============================================================
# 2. Split document
# ============================================================

splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)

chunks = splitter.split_documents(documents)


print("\n========== Chunks ==========")

for index, chunk in enumerate(chunks):

    print(f"\n--- Chunk {index} ---")

    print(chunk.page_content)


# ============================================================
# 3. Create embedding model
# ============================================================

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


# ============================================================
# 4. Create vector store
# ============================================================

vector_store = FAISS.from_documents(chunks, embeddings)


# ============================================================
# 5. Search
# ============================================================

query = input("\nAsk Carbon Knowledge Base: ")


results = vector_store.similarity_search(query, k=1)

context = "\n\n".join(document.page_content for document in results)


messages = [
    SystemMessage(content="""
        You are a carbon accounting assistant.

        Answer the user's question using only
        the provided context.

        Do not use outside knowledge.

        If the answer cannot be found in the
        context, say that the information is
        not available in the provided documents.
        """),
    HumanMessage(content=f"""
        Context:

        {context}

        Question:

        {query}
        """),
]
response = model.invoke(messages)
print("\n========== CarbonAI Answer ==========")

print(response.content)

print("\n========== Sources ==========")

for document in results:

    print(document.metadata.get("source", "Unknown source"))
