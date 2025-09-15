# CopilotKit-Deepmind

https://github.com/user-attachments/assets/1e95c9e1-2d55-4f63-b805-be49fe94a493

# CopilotKit + Google DeepMind (Gemini) + LangGraph Template

This project showcases how to build practical AI agents with **CopilotKit**, **Google DeepMind’s Gemini**, and **LangGraph**.  
It includes two agents, exposed through a **Next.js frontend** and a **FastAPI backend**.

## ✨ Features

- **Post Generator Agent**  
  Generate LinkedIn and Twitter posts from the context you provide.  
  Useful for creating professional, context-aware social content.

- **Stack Analyzer Agent**  
  Provide a URL and get a detailed breakdown of the site’s technology stack.  
  Quickly identify frameworks, libraries, and infrastructure used.

## 🛠️ Tech Stack

- **Frontend**: Next.js  
- **Backend**: FastAPI  
- **Agents**: Powered by CopilotKit + Google Gemini + LangGraph


## 📌 About

This demo illustrates how CopilotKit can be paired with LangGraph and Gemini to create agents that are:
- **Context-aware** (understand the input you provide)
- **Task-focused** (generate content or analyze stacks)
- **UI-integrated** (feels like part of your app, not just a chatbox)


---

## Project Structure

- `frontend/` — Next.js 15 app (UI)
- `agent/` — FastAPI backend agent (Python)

---

## 🚀 Getting Started

### 1. Clone the repository
Clone this repo `git clone <project URL>`


### 2. Environment Configuration

Create a `.env` file in each relevant directory as needed. 

#### Backend (`agent/.env`):
```env
GOOGLE_API_KEY=<<your-gemini-key-here>>
```

#### Frontend (`frontend/.env`):
```env
GOOGLE_API_KEY=<<your-gemini-key-here>>
```

---

### 3. Start the Backend Agent

```bash
cd agent
poetry install
poetry run python main.py
```

---

### 4. Start the Frontend

```bash
cd frontend
pnpm install
pnpm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to view the app.

---

## Notes
- Ensure the backend agent is running before using the frontend.
- Update environment variables as needed for your deployment.

---

### Hosted URL : https://copilot-kit-deepmind.vercel.app/
