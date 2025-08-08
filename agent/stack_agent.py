import os
import re
import base64
import json
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from copilotkit import CopilotKitState
from copilotkit.langgraph import copilotkit_emit_state
from copilotkit.langchain import copilotkit_customize_config

from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


class StackAgentState(CopilotKitState):
    tool_logs: List[Dict[str, Any]]
    analysis: Dict[str, Any]


def _parse_github_url(url: str) -> Optional[Tuple[str, str]]:
    """Extract owner and repo from a GitHub URL, even if surrounded by other text."""
    pattern = r"https?://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)"
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


def _fetch_manifest_contents(owner: str, repo: str, default_branch: Optional[str], root_items: List[Dict[str, Any]]) -> Dict[str, str]:
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
        "README content (truncated to first 8000 chars):\n" + context.get("readme", "")[:8000] + "\n\n"
        "Infer the stack with specific frameworks and libraries when possible (e.g., Next.js, Express, FastAPI, Prisma, Postgres)."
    )


async def gather_context_node(state: StackAgentState, config: RunnableConfig):
    # Determine URL from the latest user message
    last_user_content = state["messages"][-1].content if state["messages"] else ""
    parsed = _parse_github_url(last_user_content)

    state.setdefault("tool_logs", [])
    state["tool_logs"].append({"message": "Parsing GitHub URL", "status": "processing"})
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
    state["tool_logs"].append({"message": "Fetching repository metadata", "status": "processing"})
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
    context = state.get("analysis", {}).get("context", {})

    state.setdefault("tool_logs", [])
    state["tool_logs"].append({"message": "Analyzing stack with Gemini", "status": "processing"})
    # Ensure CopilotKit streaming config is applied
    config = copilotkit_customize_config(config, emit_messages=True, emit_tool_calls=False)

    prompt = _build_analysis_prompt(context)

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0.4,
        max_retries=2,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

    response = await model.ainvoke(prompt, config)

    state["tool_logs"][-1]["status"] = "completed"
    await copilotkit_emit_state(config, state)

    # Try to coerce to JSON for downstream consumers; if invalid, pass as text
    text = response.content if isinstance(response, AIMessage) else str(response)
    parsed_json: Optional[Dict[str, Any]] = None
    try:
        parsed_json = json.loads(text)
    except Exception:
        parsed_json = None

    if parsed_json:
        pretty = json.dumps(parsed_json, indent=2)
    else:
        pretty = text

    # Return a message containing the analysis
    return {
        "messages": [
            AIMessage(content=f"High-level stack analysis for {context.get('owner')}/{context.get('repo')}:\n\n" + pretty)
        ]
    }


async def end_node(state: StackAgentState, config: RunnableConfig):
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
