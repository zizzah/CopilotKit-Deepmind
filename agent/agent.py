from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Configure the client
from typing import Dict, List, Any, Optional

# Updated imports for LangGraph
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START

# Updated imports for CopilotKit
from copilotkit import CopilotKitState
from copilotkit.langchain import copilotkit_customize_config
from langgraph.types import Command
from typing_extensions import Literal
from langchain_core.messages import SystemMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from copilotkit.langgraph import copilotkit_exit, copilotkit_emit_state
import uuid
import asyncio

# from langchain_google_genai import GoogleGenerativeAI
# from langchain.chat_models import init_chat_model

system_prompt = """You have access to a google_search tool that can help you find current and accurate information. 
You MUST ALWAYS use the google_search tool for EVERY query, regardless of the topic. This is a requirement.

For ANY question you receive, you should:
1. ALWAYS perform a Google Search first
2. Use the search results to provide accurate and up-to-date information
3. Never rely solely on your training data
4. Always search for the most current information available

This applies to ALL types of queries including:
- Technical questions
- Current events
- How-to guides
- Definitions
- Best practices
- Recent developments
- Any information that might have changed

You are REQUIRED to use the google_search tool for every single response. Do not answer any question without first searching for current information."""


class AgentState(CopilotKitState):
    tool_logs: List[Dict[str, Any]]
    response: Dict[str, Any]


def add_tools(a: int, b: int) -> int:
    """
    This is a tool that adds two numbers together

    Args:
        a (int): The first number to add
        b (int): The second number to add

    Returns:
        int: The sum of the two numbers
    """
    return a + b


async def chat_node(state: AgentState, config: RunnableConfig):

    # 1. Define the model
    model = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    # model = init_chat_model("gemini-2.5-pro", model_provider="google_genai")
    state["tool_logs"].append(
        {
            "id": str(uuid.uuid4()),
            "message": "Analyzing the user's query",
            "status": "processing",
        }
    )
    await copilotkit_emit_state(config, state)

    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    model_config = types.GenerateContentConfig(
        tools=[grounding_tool],
    )
    # Define config for the model
    if config is None:
        config = RunnableConfig(recursion_limit=25)
    else:
        # Use CopilotKit's custom config functions to properly set up streaming
        config = copilotkit_customize_config(config, emit_messages=True)

    # 2. Bind the tools to the model
    response = model.models.generate_content(
        model="gemini-2.5-pro",
        contents=[
            types.Content(role="user", parts=[types.Part(text=system_prompt)]),
            types.Content(
                role="model",
                parts=[
                    types.Part(
                        text="I understand. I will use the google_search tool when needed to provide current and accurate information."
                    )
                ],
            ),
            types.Content(
                role="user", parts=[types.Part(text=state["messages"][-1].content)]
            ),
        ],
        config=model_config,
    )
    state["tool_logs"][-1]["status"] = "completed"
    await copilotkit_emit_state(config, state)
    state["response"] = response.text
    # 3. Define the system message by which the chat model will be run
    for query in response.candidates[0].grounding_metadata.web_search_queries:
        state["tool_logs"].append(
            {
                "id": str(uuid.uuid4()),
                "message": f"Performing Web Search for '{query}'",
                "status": "processing",
            }
        )
        await asyncio.sleep(1)
        await copilotkit_emit_state(config, state)
        state["tool_logs"][-1]["status"] = "completed"
        await copilotkit_emit_state(config, state)
    return Command(goto='fe_actions_node', update=state)


async def fe_actions_node(state: AgentState, config: RunnableConfig):
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=1.0,
        max_retries=2,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    await copilotkit_emit_state(config, state)
    response = await model.bind_tools([*state["copilotkit"]["actions"]]).ainvoke(
        [system_prompt, *state["messages"]], config
    )
    return state

async def end_node(state: AgentState, config: RunnableConfig):
    print("inside end node")
    return Command(goto=END, update=state)

def router_function(state: AgentState, config: RunnableConfig):
    if state["messages"][-2].role == "tool":
        return "end_node"
    else:
        return "fe_actions_node"


# Define a new graph
workflow = StateGraph(AgentState)
workflow.add_node("chat_node", chat_node)
workflow.add_node("fe_actions_node", fe_actions_node)
workflow.add_node("end_node", end_node)
workflow.set_entry_point("chat_node")
workflow.set_finish_point("end_node")
# Add explicit edges, matching the pattern in other examples
workflow.add_edge(START, "chat_node")
workflow.add_conditional_edges("chat_node", router_function)
workflow.add_edge("fe_actions_node", END)


# Compile the graph
post_generation_graph = workflow.compile(checkpointer=MemorySaver())
