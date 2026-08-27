from langgraph.graph import StateGraph
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from langchain_ollama import ChatOllama
from typing import TypedDict
from langgraph.constants import END, START
from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

class Chat(TypedDict):

    messages: Annotated[list[BaseMessage], add_messages]

model = ChatOllama(
    model = "qwen3:1.7b"
)

def chat_node(state: Chat):

    response = model.invoke(state['messages'])
    return {'messages': [response]}


checkpointer = MemorySaver()
graph = StateGraph(Chat)

graph.add_node("chat_node", chat_node)

graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer = checkpointer)