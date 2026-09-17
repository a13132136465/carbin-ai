from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

model = ChatDeepSeek(
    model="deepseek-chat"
)

messages = [
    SystemMessage(
        content="You are a carbon credit project auditor."
    ),
    HumanMessage(
        content="""
        Project: Tianjin Solar Farm
        Type: Solar Energy
        Annual generation: 5000 MWh

        Please briefly analyze this project.
        """
    )
]

response = model.invoke(messages)

print(response.content)
print(type(response))