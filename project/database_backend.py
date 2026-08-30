from langgraph.prebuilt import tool_node
import os
import sqlite3
import requests
from langgraph.graph import StateGraph
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from langchain_ollama import ChatOllama
from typing import TypedDict
from langgraph.constants import END, START
from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

class Chat(TypedDict):

    messages: Annotated[list[BaseMessage], add_messages]

model = ChatOllama(
    model = "qwen3:1.7b"
)

conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)

def chat_node(state: Chat):

    response = model.invoke(state['messages'])
    return {'messages': [response]}

checkpointer = SqliteSaver(conn=conn)
graph = StateGraph(Chat)

graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer = checkpointer)

def retrieve_all_thread():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])

    return list(all_threads)

def get_thread_messages(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    state = chatbot.get_state(config)
    if state and state.values and "messages" in state.values:
        return state.values["messages"]
    return []