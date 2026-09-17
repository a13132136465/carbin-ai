from typing import Optional

from pydantic import (
    BaseModel,
    Field,
)


class ProjectInput(BaseModel):

    project_name: Optional[str] = Field(
        default=None
    )

    project_type: Optional[str] = Field(
        default=None
    )

    project_region: Optional[str] = Field(
        default=None
    )

    annual_generation_value: Optional[float] = Field(
        default=None
    )

    annual_generation_unit: Optional[str] = Field(
        default=None
    )

    grid_emission_factor_value: Optional[float] = Field(
        default=None
    )

    grid_emission_factor_unit: Optional[str] = Field(
        default=None
    )


class EmissionFactorResult(BaseModel):

    found: bool

    region: Optional[str] = None

    value: Optional[float] = None

    unit: Optional[str] = None