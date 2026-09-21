from typing import Optional

from pydantic import BaseModel


class AuditRequest(BaseModel):
    message: str



class AuditResponse(BaseModel):
    status: str
    
    audit_id: str
    
    thread_id: str
    
    project_id: str | None = None
    
    question: str | None = None

    project_name: Optional[str] = None

    project_type: Optional[str] = None

    project_region: Optional[str] = None

    annual_generation_mwh: Optional[float] = None

    grid_emission_factor: Optional[float] = None

    carbon_estimate: Optional[float] = None

    audit_report: Optional[str] = None

    missing_fields: list[str] = []
    
class AuditResumeRequest(BaseModel):
    message: str
    
class AuditDetailResponse(BaseModel):
    audit_id: str
    status: str
    project_id: str | None = None

    project_name: str | None = None
    project_type: str | None = None
    project_region: str | None = None

    annual_generation_mwh: float | None = None
    grid_emission_factor: float | None = None
    carbon_estimate: float | None = None

    audit_report: str | None = None
