from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage
from typing import Optional
from langchain_core.messages import SystemMessage

load_dotenv()

model = ChatDeepSeek(model="deepseek-chat")


class ProjectInput(BaseModel):

    project_name: Optional[str] = Field(
        default=None, description="Name of the carbon project. None if not provided."
    )

    project_type: Optional[str] = Field(
        default=None, description="Type of carbon project. None if not provided."
    )

    annual_generation_mwh: Optional[float] = Field(
        default=None,
        description="Annual renewable electricity generation in MWh. None if not provided.",
    )

    grid_emission_factor: Optional[float] = Field(
        default=None,
        description="Grid emission factor in tCO2/MWh. None if not provided.",
    )


structured_model = model.with_structured_output(ProjectInput)

messages = [HumanMessage(content="""
        我在天津有一个光伏项目，
        项目叫 Tianjin Solar Farm。

        这个项目一年大约可以产生
        5000 MWh 的清洁电力。

        电网排放因子按照
        0.58 tCO2/MWh 计算。
        """)]

result = structured_model.invoke(messages)

print(result)
print(type(result))

carbon = result.annual_generation_mwh * result.grid_emission_factor

print(carbon)
