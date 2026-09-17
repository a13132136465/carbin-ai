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

@tool
def validate_project_data(
    project_name: str,
    project_type: str,
    annual_generation_mwh: float,
    grid_emission_factor: float
) -> str:
    """
    Validate whether the basic carbon project data is complete
    and contains reasonable positive values.

    Args:
        project_name:
            Name of the carbon project.

        project_type:
            Type of project, such as solar or wind.

        annual_generation_mwh:
            Annual renewable electricity generation in MWh.

        grid_emission_factor:
            Grid emission factor in tCO2/MWh.

    Returns:
        PASS if the basic project data is valid,
        otherwise returns FAIL with a reason.
    """

    if not project_name.strip():
        return "FAIL: project name is missing"

    if not project_type.strip():
        return "FAIL: project type is missing"

    if annual_generation_mwh <= 0:
        return "FAIL: annual generation must be greater than 0"

    if grid_emission_factor <= 0:
        return "FAIL: grid emission factor must be greater than 0"

    return "PASS: basic project data is valid"


tools = [
    calculate_carbon_reduction,
    validate_project_data
]


model_with_tools = model.bind_tools(tools)

tool_map = {
    tool.name: tool
    for tool in tools
}

messages = [
    HumanMessage(
        content="""
        Please perform a preliminary audit of this carbon project.

        Project name: Tianjin Solar Farm
        Project type: solar
        Annual electricity generation: 5000 MWh
        Grid emission factor: 0.58 tCO2/MWh

        Please:
        1. Validate the basic project data.
        2. Calculate the estimated annual carbon emission reduction.
        3. Give a short preliminary audit conclusion.

        Use the available tools when appropriate.
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