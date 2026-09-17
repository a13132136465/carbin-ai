from typing import (
    TypedDict,
    Optional,
    Annotated,
)

from langgraph.graph.message import add_messages


class CarbonAuditState(TypedDict):

    user_input: str

    messages: Annotated[
        list,
        add_messages,
    ]

    project_name: Optional[str]
    project_type: Optional[str]
    project_region: Optional[str]

    annual_generation_value: Optional[float]
    annual_generation_unit: Optional[str]

    grid_emission_factor_value: Optional[float]
    grid_emission_factor_unit: Optional[str]

    annual_generation_mwh: Optional[float]
    grid_emission_factor: Optional[float]

    validation_status: str
    validation_result: str
    missing_fields: list[str]

    retrieval_status: str
    retrieval_score: Optional[float]
    retrieved_context: str
    retrieval_sources: list[str]

    carbon_estimate: float
    audit_report: str
