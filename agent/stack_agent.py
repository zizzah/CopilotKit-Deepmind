import os
import re
import base64
import json
from typing import Any, Dict, List, Optional, Tuple
import uuid

import requests
from dotenv import load_dotenv

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from copilotkit import CopilotKitState
from copilotkit.langgraph import copilotkit_emit_state
from copilotkit.langchain import copilotkit_customize_config

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from langchain_core.tools import tool

load_dotenv()


class StackAgentState(CopilotKitState):
    tool_logs: List[Dict[str, Any]]
    analysis: Dict[str, Any]
    show_cards: bool


# -------------------- Structured Output Schema --------------------
class FrontendSpec(BaseModel):
    framework: Optional[str] = None
    language: Optional[str] = None
    package_manager: Optional[str] = None
    styling: Optional[str] = None
    key_libraries: List[str] = Field(default_factory=list)


class BackendSpec(BaseModel):
    framework: Optional[str] = None
    language: Optional[str] = None
    dependency_manager: Optional[str] = None
    key_libraries: List[str] = Field(default_factory=list)
    architecture: Optional[str] = None


class DatabaseSpec(BaseModel):
    type: Optional[str] = None
    notes: Optional[str] = None


class InfrastructureSpec(BaseModel):
    hosting_frontend: Optional[str] = None
    hosting_backend: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)


class CICDSpec(BaseModel):
    setup: Optional[str] = None


class KeyRootFileSpec(BaseModel):
    file: Optional[str] = None
    description: Optional[str] = None


class HowToRunSpec(BaseModel):
    summary: Optional[str] = None
    steps: List[str] = Field(default_factory=list)


class RiskNoteSpec(BaseModel):
    area: Optional[str] = None
    note: Optional[str] = None


class StructuredStackAnalysis(BaseModel):
    purpose: Optional[str] = None
    frontend: Optional[FrontendSpec] = None
    backend: Optional[BackendSpec] = None
    database: Optional[DatabaseSpec] = None
    infrastructure: Optional[InfrastructureSpec] = None
    ci_cd: Optional[CICDSpec] = None
    key_root_files: List[KeyRootFileSpec] = Field(default_factory=list)
    how_to_run: Optional[HowToRunSpec] = None
    risks_notes: List[RiskNoteSpec] = Field(default_factory=list)


# ------------------------------------------------------------------


# OpenAI-style tool for returning the structured stack analysis
@tool("return_stack_analysis", args_schema=StructuredStackAnalysis)
def return_stack_analysis_tool(**kwargs) -> Dict[str, Any]:
    """Return the final stack analysis in a strict JSON structure. Use this tool to output results."""
    try:
        validated = StructuredStackAnalysis(**kwargs)
        return validated.model_dump(exclude_none=True)
    except Exception:
        # In case validation fails unexpectedly, return raw
        return kwargs


def _parse_github_url(url: str) -> Optional[Tuple[str, str]]:
    """Extract owner and repo from a GitHub URL, even if surrounded by other text."""
    pattern = (
        r"https?://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)"
    )
    match = re.search(pattern, url)
    if not match:
        return None
    return match.group("owner"), match.group("repo")


def _github_headers() -> Dict[str, str]:
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _gh_get(url: str) -> Optional[requests.Response]:
    try:
        resp = requests.get(url, headers=_github_headers(), timeout=30)
        if resp.status_code == 200:
            return resp
        return None
    except requests.RequestException:
        return None


def _fetch_repo_info(owner: str, repo: str) -> Dict[str, Any]:
    info = {}
    r = _gh_get(f"https://api.github.com/repos/{owner}/{repo}")
    if r:
        info = r.json()
    return info


def _fetch_languages(owner: str, repo: str) -> Dict[str, int]:
    r = _gh_get(f"https://api.github.com/repos/{owner}/{repo}/languages")
    return r.json() if r else {}


def _fetch_readme(owner: str, repo: str) -> str:
    # Prefer the readme API which returns the default README
    r = _gh_get(f"https://api.github.com/repos/{owner}/{repo}/readme")
    if r:
        data = r.json()
        content = data.get("content")
        if content:
            try:
                return base64.b64decode(content).decode("utf-8", errors="ignore")
            except Exception:
                pass
    # Fallback: try common README names in root contents
    contents = _gh_get(f"https://api.github.com/repos/{owner}/{repo}/contents/")
    if contents:
        for item in contents.json():
            name = item.get("name", "").lower()
            if name in {"readme.md", "readme", "readme.txt", "readme.rst"}:
                file_resp = _gh_get(item.get("download_url", ""))
                if file_resp:
                    return file_resp.text
    return ""


def _list_root(owner: str, repo: str) -> List[Dict[str, Any]]:
    r = _gh_get(f"https://api.github.com/repos/{owner}/{repo}/contents/")
    return r.json() if r else []


ROOT_MANIFEST_CANDIDATES = [
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "requirements.txt",
    "pyproject.toml",
    "Pipfile",
    "Pipfile.lock",
    "setup.py",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Cargo.toml",
    "Gemfile",
    "composer.json",
    "Dockerfile",
    "docker-compose.yml",
    "Procfile",
    "serverless.yml",
    "vercel.json",
    "netlify.toml",
    "next.config.js",
    "next.config.mjs",
    "nuxt.config.js",
    "nuxt.config.ts",
    "angular.json",
    "vite.config.ts",
    "vite.config.js",
]


def _fetch_manifest_contents(
    owner: str,
    repo: str,
    default_branch: Optional[str],
    root_items: List[Dict[str, Any]],
) -> Dict[str, str]:
    manifest_map: Dict[str, str] = {}
    by_name = {item.get("name"): item for item in root_items}

    for name in ROOT_MANIFEST_CANDIDATES:
        item = by_name.get(name)
        if not item:
            continue
        # Use download_url if present, otherwise construct raw URL
        download_url = item.get("download_url")
        text: Optional[str] = None
        if download_url:
            r = _gh_get(download_url)
            if r:
                text = r.text
        elif default_branch:
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/{name}"
            r = _gh_get(raw_url)
            if r:
                text = r.text
        if text is not None:
            manifest_map[name] = text
    return manifest_map


def _summarize_root_files(root_items: List[Dict[str, Any]]) -> List[str]:
    names = []
    for item in root_items:
        names.append(f"{item.get('name')} ({item.get('type')})")
    return names


def _build_analysis_prompt(context: Dict[str, Any]) -> str:
    return (
        "You are a senior software architect. Analyze the following GitHub repository at a high level.\n"
        "Goals: Provide a concise, structured overview of what the project does and the tech stack.\n\n"
        "Return JSON with keys: purpose, frontend, backend, database, infrastructure, ci_cd, key_root_files, how_to_run, risks_notes.\n\n"
        f"Repository metadata:\n{json.dumps(context.get('repo_info', {}), indent=2)}\n\n"
        f"Languages (bytes of code):\n{json.dumps(context.get('languages', {}), indent=2)}\n\n"
        f"Root items:\n{json.dumps(context.get('root_files', []), indent=2)}\n\n"
        f"Manifests (truncated to first 2000 chars each):\n{json.dumps({k: v[:2000] for k, v in context.get('manifests', {}).items()}, indent=2)}\n\n"
        "README content (truncated to first 8000 chars):\n"
        + context.get("readme", "")[:8000]
        + "\n\n"
        "Infer the stack with specific frameworks and libraries when possible (e.g., Next.js, Express, FastAPI, Prisma, Postgres)."
    )


async def gather_context_node(state: StackAgentState, config: RunnableConfig):
    # Ensure streaming is enabled
    config = copilotkit_customize_config(
        config or RunnableConfig(recursion_limit=25),
        emit_messages=True,
        emit_tool_calls=True,
    )

    # Determine URL from the latest user message
    last_user_content = state["messages"][-1].content if state["messages"] else ""
    parsed = _parse_github_url(last_user_content)

    state["tool_logs"] = state.get("tool_logs", [])
    state["tool_logs"].append(
        {
            "id": str(uuid.uuid4()),
            "message": "Getting GitHub URL",
            "status": "processing",
        }
    )
    await copilotkit_emit_state(config, state)

    if not parsed:
        state["tool_logs"][-1]["status"] = "failed"
        await copilotkit_emit_state(config, state)
        analysis = {
            "error": "Could not parse GitHub URL from input. Provide a URL like https://github.com/owner/repo",
        }
        return {"analysis": analysis}

    owner, repo = parsed
    state["tool_logs"][-1]["status"] = "completed"
    await copilotkit_emit_state(config, state)

    state["tool_logs"].append(
        {
            "id": str(uuid.uuid4()),
            "message": "Fetching repository metadata",
            "status": "processing",
        }
    )
    await copilotkit_emit_state(config, state)

    repo_info = _fetch_repo_info(owner, repo)
    default_branch = repo_info.get("default_branch")
    languages = _fetch_languages(owner, repo)
    readme = _fetch_readme(owner, repo)
    root_items = _list_root(owner, repo)
    manifests = _fetch_manifest_contents(owner, repo, default_branch, root_items)

    context: Dict[str, Any] = {
        "owner": owner,
        "repo": repo,
        "repo_info": repo_info,
        "languages": languages,
        "readme": readme,
        "root_files": _summarize_root_files(root_items),
        "manifests": manifests,
    }

    state["tool_logs"][-1]["status"] = "completed"
    await copilotkit_emit_state(config, state)

    return {"analysis": {"context": context}}


async def analyze_with_gemini_node(state: StackAgentState, config: RunnableConfig):
    # Ensure streaming is enabled for this node as well
    # config = copilotkit_customize_config(
    #     config,
    #     emit_intermediate_state=[
    #         {
    #             "state_key": "analysis",
    #             "tool": "return_stack_analysis",
    #             "tool_argument": "purpose",
    #         }
    #     ],
    # )

    context = state.get("analysis", {}).get("context", {})

    state["tool_logs"] = state.get("tool_logs", [])
    state["tool_logs"].append(
        {"id": str(uuid.uuid4()), "message": "Analyzing stack", "status": "processing"}
    )
    await copilotkit_emit_state(config, state)

    prompt = _build_analysis_prompt(context)
    system_instructions = (
        "You are a senior software architect. Analyze the repository context provided by the user. "
        "When responding, do not write free-form text. Always call the tool `return_stack_analysis` "
        "with all applicable fields filled."
    )
    messages = [
        SystemMessage(content=system_instructions),
        HumanMessage(content=prompt),
    ]

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0.4,
        max_retries=2,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

    # Prefer tool calling via bind_tools(); then structured output; then raw JSON parse
    pretty: str
    structured_payload: Optional[Dict[str, Any]] = None

    # 1) Try to get a tool call
    try:
        bound = model.bind_tools([return_stack_analysis_tool])
        tool_msg = await bound.ainvoke(messages, config)
        if isinstance(tool_msg, AIMessage):
            tool_calls = getattr(tool_msg, "tool_calls", None)
            if tool_calls:
                for call in tool_calls:
                    if call.get("name") == "return_stack_analysis":
                        args = call.get("args", {}) or {}
                        state['analysis'] = json.dumps(args)
                        state['show_cards'] = True
                        await copilotkit_emit_state(config, state)
                        try:
                            structured_payload = StructuredStackAnalysis(
                                **args
                            ).model_dump(exclude_none=True)
                        except Exception:
                            # accept the raw args if validation fails
                            structured_payload = dict(args)
                        break
    except Exception:
        pass

    # 2) Fallback: structured output
    if structured_payload is None:
        try:
            structured_model = model.with_structured_output(StructuredStackAnalysis)
            structured_response = await structured_model.ainvoke(messages, config)
            if isinstance(structured_response, StructuredStackAnalysis):
                structured_payload = structured_response.model_dump(exclude_none=True)
            elif isinstance(structured_response, dict):
                structured_payload = structured_response
            else:
                try:
                    structured_payload = structured_response.dict(exclude_none=True)  # type: ignore[attr-defined]
                except Exception:
                    structured_payload = None
        except Exception:
            structured_payload = None

    state["tool_logs"][-1]["status"] = "completed"
    await copilotkit_emit_state(config, state)
    messages.append(AIMessage(tool_calls=tool_calls, id = tool_msg.id, type = "ai", content= ''))
    messages.append(ToolMessage(content= "The GitHub Repository has been analyzed", tool_call_id = tool_calls[0]["id"], type = "tool"))
    messages[0].content = "Generate a summary of the GitHub Repository. It should be in a concise and strictly textual"
    client = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0.4,
        max_retries=2,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    state["tool_logs"].append({"id": str(uuid.uuid4()), "message": "Generating Summary", "status": "processing"})
    await copilotkit_emit_state(config, state)
    model_response = await client.ainvoke(messages, config)
    state["tool_logs"][-1]["status"] = "completed"
    await copilotkit_emit_state(config, state)
    print(model_response, "model_response")
    # if structured_payload:
    #     pretty = json.dumps(structured_payload, indent=2)
    #     # store for downstream consumers if needed
    #     # state.setdefault("analysis", {})["structured"] = structured_payload
    # else:
    #     # Fallback: call the raw model and try to coerce JSON
    #     response = await model.ainvoke(messages, config)
    #     text = response.content if isinstance(response, AIMessage) else str(response)
    #     try:
    #         parsed_json = json.loads(text)
    #         pretty = json.dumps(parsed_json, indent=2)
    #         state.setdefault("analysis", {})["structured"] = parsed_json
    #     except Exception:
    #         pretty = text

    # Return a message containing the analysis
    return {
        "messages": [
            AIMessage(
                content= model_response.content
            )
        ]
    }


async def end_node(state: StackAgentState, config: RunnableConfig):
    # Clear logs and emit once more to update UI
    state["tool_logs"] = []
    await copilotkit_emit_state(config or RunnableConfig(recursion_limit=25), state)
    return {"messages": state["messages"], "tool_logs": []}


workflow = StateGraph(StackAgentState)
workflow.add_node("gather_context", gather_context_node)
workflow.add_node("analyze", analyze_with_gemini_node)
workflow.add_node("end", end_node)
workflow.add_edge(START, "gather_context")
workflow.add_edge("gather_context", "analyze")
workflow.add_edge("analyze", END)
workflow.set_entry_point("gather_context")
workflow.set_finish_point("end")

stack_analysis_graph = workflow.compile(checkpointer=MemorySaver())
