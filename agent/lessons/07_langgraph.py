from dotenv import load_dotenv

from langchain_deepseek import ChatDeepSeek
from langchain_core.tools import tool
from langgraph.graph import MessagesState,StateGraph,START
from langgraph.prebuilt import ToolNode,tools_condition
from langchain_core.messages import HumanMessage

load_dotenv()


@tool
def calculate_carbon_reduction(
    annual_generation_mwh: float,
    grid_emission_factor: float
) -> float:
    """
    Calculate the estimated annual carbon emission reduction
    for a renewable energy project.
    """

    return annual_generation_mwh * grid_emission_factor


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

model = ChatDeepSeek(
    model="deepseek-chat"
)

tools = [
    calculate_carbon_reduction,
    validate_project_data
]

model_with_tools = model.bind_tools(tools)

def agent_node(state: MessagesState):
    response = model_with_tools.invoke(
        state["messages"]
    )

    return {
        "messages":[response]
    }
tool_node = ToolNode(tools)
builder = StateGraph(MessagesState)

builder.add_node(
    "agent",
    agent_node
)

builder.add_node(
    "tools",
    tool_node
)

builder.add_edge(
    START,
    "agent"
)

builder.add_conditional_edges(
    "agent",
    tools_condition
)

builder.add_edge(
    "tools",
    "agent"
)

graph = builder.compile()

result = graph.invoke(
    {
        "messages": [
            HumanMessage(
                content="""
                Please perform a preliminary audit.

                Project name: Tianjin Solar Farm
                Project type: solar
                Annual electricity generation: 5000 MWh
                Grid emission factor: 0.58 tCO2/MWh

                Please validate the project data,
                calculate the estimated annual carbon reduction,
                and give a short conclusion.

                Use the available tools when appropriate.
                """
            )
        ]
    }
)

print("\n========== Message History ==========")

for message in result["messages"]:
    print(f"\n{type(message).__name__}:")
    print(message.content)

    if hasattr(message, "tool_calls") and message.tool_calls:
        print("Tool calls:")
        print(message.tool_calls)