# GitHub Copilot Instructions for GPT Researcher

This repository contains the GPT Researcher project. These instructions focus on the "hackathon" workflow: customizing the frontend/backend test harness to demonstrate new research capabilities, while treating the core `gpt_researcher` library as a dependency.

## 🏗 Project Architecture

The project consists of three main parts:
1.  **Frontend**: A static HTML/JS interface (located in `frontend/`) and a Next.js app (in `frontend/nextjs/`). For simple demos, the static frontend is preferred.
2.  **Backend**: A FastAPI server (located in `backend/`) that exposes endpoints and manages WebSocket connections for streaming research results.
3.  **Core Library**: The `gpt_researcher` package, which handles the actual research logic (scraping, summarizing, etc.).

## 🚀 Running the Application (Demo Mode)

To run the application for a demo:

1.  **Start the Backend**:
    ```bash
    python backend/run_server.py
    ```
    This starts the FastAPI server on port 8000 and serves the static frontend.

2.  **Access the Frontend**:
    Open `http://localhost:8000` in your browser.

### ☁️ Running in GitHub Codespaces

If running in a GitHub Codespace:
1.  **Environment Variables**: Create a `.env` file in the root directory with your API keys (OPENAI_API_KEY, TAVILY_API_KEY).
2.  **Start Server**: Run `python backend/run_server.py`.
3.  **Port Forwarding**:
    *   Go to the "Ports" tab in VS Code.
    *   Right-click on port **8000**.
    *   Set **Port Visibility** to **Public** (required for external access or if sharing the link).
    *   Click the "Local Address" (globe icon) to open the app in your browser.
    *   *Note*: The frontend automatically connects to the backend relative to the current window location, so it works seamlessly over the forwarded port.

## 🛠 Customization Workflow

### 1. Adding a New Research Type
To add a custom research type (e.g., "Hackathon Report"):

1.  **Create the Report Class**:
    Add a new directory and file in `backend/report_type/`, e.g., `backend/report_type/hackathon_report/hackathon_report.py`.
    Implement a class that initializes `GPTResearcher` with your desired configuration.
    ```python
    from gpt_researcher import GPTResearcher

    class HackathonReport:
        def __init__(self, query, ...):
            # Initialize GPTResearcher with custom parameters
            self.researcher = GPTResearcher(query=query, report_type="custom_type", ...)
        
        async def run(self):
            return await self.researcher.run()
    ```

2.  **Register the Report Type**:
    Update `backend/server/websocket_manager.py` in the `run_agent` function to handle your new report type string:
    ```python
    # backend/server/websocket_manager.py
    elif report_type == "hackathon_report":
        researcher = HackathonReport(...)
        report = await researcher.run()
    ```

3.  **Update the Frontend**:
    Modify `frontend/index.html` to add the new option to the report type selector.
    Update `frontend/scripts.js` if specific handling is needed for the new type.

### 2. Customizing Prompts
Prompts are located in `gpt_researcher/prompts.py`.
- **Direct Modification**: You can modify the strings in this file to change the agent's persona or instructions.
- **Via Configuration**: `GPTResearcher` accepts `agent` and `role` arguments. You can define new agents/roles and map them to prompts if you extend the prompt system.

## 📂 Key Files & Directories

- **`backend/run_server.py`**: Entry point for the backend server.
- **`backend/server/app.py`**: FastAPI application definition and routes.
- **`backend/server/websocket_manager.py`**: Handles WebSocket connections and orchestrates the research process (`run_agent` function).
- **`backend/report_type/`**: Contains report type implementations (`BasicReport`, `DetailedReport`).
- **`frontend/index.html`**: Main entry point for the static frontend.
- **`frontend/scripts.js`**: Frontend logic for WebSocket communication and UI updates.
- **`gpt_researcher/prompts.py`**: Contains the system prompts used by the agents.

## 🛡️ Security & Environment
- **API Keys**: Never commit `.env` files or hardcode keys. Ensure `OPENAI_API_KEY` and `TAVILY_API_KEY` are set in the `.env` file (which is git-ignored).
- **Codespaces**: When using Port Forwarding, be aware that the "Public" visibility makes the port accessible to anyone with the URL. Do not expose sensitive data on the frontend.

## 🧠 Context & Focus
To maintain focus and prevent errors, treat the following as **Read-Only** or **Ignored**:
- `gpt_researcher/`: Core library logic (treat as a dependency/black box).
- `outputs/`: Generated reports and artifacts.
- `.venv/`, `__pycache__/`: System/Environment files.
- `.github/`: CI/CD workflows (unless specifically modifying the hackathon harness).

## ⚠️ Important Notes
- The backend serves the `frontend/` directory at `/site` and `frontend/index.html` at `/`.
- For the hackathon demo, prefer the **Static Frontend** (`frontend/index.html`) over the Next.js app for simplicity and speed of iteration.
