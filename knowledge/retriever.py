from dataclasses import dataclass
from typing import Optional

from config.settings import settings
from knowledge.vector_store import (
    get_vector_store,
)

REGION_MAPPING = {
    "天津": "Tianjin",
    "北京": "Beijing",
    "上海": "Shanghai",
    "广东": "Guangdong",
    "四川": "Sichuan",
}


@dataclass
class RetrievalResult:
    found: bool
    score: Optional[float]
    content: str
    source: Optional[str]


def search(
    query: str,
    k: int = 1,
) -> list[RetrievalResult]:
    vector_store = get_vector_store()
    results = vector_store.similarity_search_with_score(
        query,
        k=k,
    )

    output = []

    for document, score in results:

        output.append(
            RetrievalResult(
                found=True,
                score=float(score),
                content=document.page_content,
                source=document.metadata.get("source"),
            )
        )

    return output


def search_best(
    query: str,
) -> RetrievalResult:

    results = search(
        query=query,
        k=1,
    )

    print("\n[search_best]")
    print("Query:", query)

    if not results:
        print("No FAISS results")

        return RetrievalResult(
            found=False,
            score=None,
            content="",
            source=None,
        )

    result = results[0]

    print("Raw score:", result.score)
    print(
        "Threshold:",
        settings.RETRIEVAL_DISTANCE_THRESHOLD,
    )
    print("Content:")
    print(result.content)

    if (
        result.score is None
        or result.score > settings.RETRIEVAL_DISTANCE_THRESHOLD
    ):
        print("Retrieval rejected by threshold")

        return RetrievalResult(
            found=False,
            score=result.score,
            content=result.content,
            source=result.source,
        )

    print("Retrieval accepted")

    return result


def normalize_region(region: str) -> str:
    return REGION_MAPPING.get(region, region)
