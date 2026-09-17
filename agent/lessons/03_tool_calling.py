from dotenv import load_dotenv

from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool


load_dotenv()


@tool
def calculate_carbon_reduction(
    annual_generation_mwh: float,
    grid_emission_factor: float
) -> float:
    """
    Calculate the estimated annual carbon emission reduction
    for a renewable energy project.

    Args:
        annual_generation_mwh:
            Annual renewable electricity generation in MWh.

        grid_emission_factor:
            Grid emission factor in tCO2/MWh.

    Returns:
        Estimated annual carbon emission reduction in tCO2.
    """

    return annual_generation_mwh * grid_emission_factor


model = ChatDeepSeek(
    model="deepseek-chat"
)

model_with_tools = model.bind_tools(
    [calculate_carbon_reduction]
)

messages = [
    HumanMessage(
        content="""
        A solar energy project generates 5000 MWh
        of renewable electricity annually.

        The grid emission factor is 0.58 tCO2/MWh.

        Calculate the estimated annual carbon emission reduction.
        """
    )
]


response = model_with_tools.invoke(messages)

print("AI content:")
print(response.content)

print("\nTool calls:")
print(response.tool_calls)

tool_call = response.tool_calls[0]

print("\nTool name:")
print(tool_call["name"])

print("\nTool arguments:")
print(tool_call["args"])

tool_result = calculate_carbon_reduction.invoke(
    tool_call["args"]
)

print("\nTool result:")
print(tool_result)