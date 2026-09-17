from dotenv import load_dotenv

from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage, ToolMessage
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


# 第一次调用 LLM
response = model_with_tools.invoke(messages)

print("First AI response:")
print(response.content)

print("\nTool calls:")
print(response.tool_calls)

messages.append(response)
tool_call = response.tool_calls[0]

tool_result = calculate_carbon_reduction.invoke(
    tool_call["args"]
)
print("\nTool result:")
print(tool_result)

tool_message = ToolMessage(
    content = str(tool_result),
    tool_call_id = tool_call["id"]
)

messages.append(tool_message)

print("\nMessages:")
for message in messages:
    print(type(message).__name__, ":", message.content)

final_response = model_with_tools.invoke(messages)

print("\nFinal answer:")
print(final_response.content)