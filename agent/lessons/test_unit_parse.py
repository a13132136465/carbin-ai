from typing import Optional

from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field


load_dotenv()

model = ChatDeepSeek(
    model="deepseek-chat"
)


class ProjectInput(BaseModel):

    annual_generation_value: Optional[float] = Field(
        default=None,
        description=(
            "Numeric value of annual electricity generation. "
            "Only extract the number explicitly provided by the user."
        ),
    )

    annual_generation_unit: Optional[str] = Field(
        default=None,
        description=(
            "Unit explicitly provided by the user for annual "
            "electricity generation. "
            "Do not infer or guess the unit. "
            "None if no unit is explicitly provided."
        ),
    )


structured_model = model.with_structured_output(
    ProjectInput
)


user_input = input("\nYou: ")


result = structured_model.invoke([
    SystemMessage(
        content="""
        Extract information explicitly stated by the user.

        Do not guess missing information.

        In particular, never infer a measurement unit
        when the user did not explicitly provide one.
        """
    ),
    HumanMessage(
        content=user_input
    )
])


print("\nParsed:")
print(result)