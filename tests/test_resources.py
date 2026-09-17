from knowledge.embeddings import (
    get_embeddings,
)

from knowledge.vector_store import (
    get_vector_store,
)


e1 = get_embeddings()
e2 = get_embeddings()

print(
    "Same embedding object:",
    e1 is e2,
)


v1 = get_vector_store()
v2 = get_vector_store()

print(
    "Same vector store object:",
    v1 is v2,
)