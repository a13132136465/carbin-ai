from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

texts = [
    "Tianjin grid emission factor",
    "Beijing grid carbon emission factor",
    "How to cook Italian pasta",
]

vectors = embeddings.embed_documents(texts)

for text, vector in zip(texts, vectors):
    print("\nText:")
    print(text)

    print("Dimension:")
    print(len(vector))

    print("First 10 values:")
    print(vector[:10])
    
import numpy as np


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)

    return np.dot(a, b) / (
        np.linalg.norm(a)
        * np.linalg.norm(b)
    )
    
print("\n========== Similarity ==========")

print(
    "Tianjin vs Beijing:",
    cosine_similarity(
        vectors[0],
        vectors[1]
    )
)

print(
    "Tianjin vs Pasta:",
    cosine_similarity(
        vectors[0],
        vectors[2]
    )
)