from dotenv import load_dotenv

from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool


load_dotenv()
step = 0

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


tools = [
    calculate_carbon_reduction
]


model_with_tools = model.bind_tools(tools)

tool_map = {
    tool.name: tool
    for tool in tools
}

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

while True:
    step += 1
    print(f"\n========== Step {step} ==========")
    response = model_with_tools.invoke(messages)

    messages.append(response)

    print("\nAI:")
    print(response.content)
    if not response.tool_calls:
        print("\nFinal answer:")
        print(response.content)
        break
    for tool_call in response.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        selected_tool = tool_map[tool_name]
        print(f"\nCalling tool: {tool_name}")
        tool_result = selected_tool.invoke(tool_args)
        print(f"Tool result: {tool_result}")
        tool_message = ToolMessage(
            content=str(tool_result),
            tool_call_id=tool_call["id"]
        )
        messages.append(tool_message)