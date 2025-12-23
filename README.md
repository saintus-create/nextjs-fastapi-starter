# Cline Agent v0.8.0

Terminal-first autonomous coding agent with safety guardrails, self-reflection, and MCP/shadcn integration.

## Features

- **A - Safety Guardrail**: Static regex + LLM audit blocking dangerous commands
- **B - Self-Reflection Loop**: Auto-retry on failure with critique
- **C - MCP/shadcn Integration**: HTTP client for external tool servers

## Project Structure

```
├── api/                    # Vercel Python serverless
│   └── index.py            # FastAPI entry point
├── backend/                # Python package
│   ├── cline_agent/        # Agent source code
│   │   ├── agent/core.py   # Main Agent class
│   │   ├── tools/          # File system, Git, MCP, Safety
│   │   ├── llm/            # Multi-provider LLM router
│   │   └── cli.py          # Typer CLI
│   ├── pyproject.toml
│   └── requirements.txt
├── src/                    # Next.js frontend (optional)
│   └── app/chat/           # Chat UI
├── components/             # shadcn/ui components
├── .github/workflows/      # CI/CD
├── vercel.json             # Vercel config
└── install.sh              # One-liner installer
```

## Quick Start

### Option 1: Local Development

```bash
# 1. Clone
git clone https://github.com/saintus-create/nextjs-fastapi-starter.git
cd nextjs-fastapi-starter

# 2. Install Python deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# 3. Install Node deps
pnpm install

# 4. Set API key
echo "OPENAI_API_KEY=sk-your-key" > .env.local

# 5. Run (two terminals)
# Terminal A - FastAPI
python3 -m uvicorn api.index:app --reload --port 8000

# Terminal B - Next.js
pnpm dev
```

### Chat Interface

The Next.js frontend now provides a seamless chat interface to interact with the autonomous coding agent:

- **Conversational AI Experience**: Chat naturally with the agent using plain English
- **Safety Guardrails**: All requests are audited for dangerous operations
- **Self-Reflection**: Agent automatically retries failed tasks with improved approaches
- **Structured Execution**: Tasks are broken down into safe, atomic operations

**Example chat interactions:**
- "Create a hello.py file that prints 'Hello, World!'"
- "List all files in the current directory"
- "Add a new function to utils.py"
- "Check the git status and commit any changes"

### Option 2: CLI Only

```bash
cd backend
pip install -e .
cline-agent --help
cline-agent task "Create a hello.py file" --mode autonomous
```

### Option 3: One-liner Install

```bash
curl -sSL https://get.cline-agent.com | bash
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/run-task` | POST | Execute a task (direct agent API) |
| `/api/chat` | POST | Chat interface for conversational agent interaction |
| `/api/config` | GET | Get config (masked) |

### Example

```bash
curl -X POST http://localhost:8000/api/run-task \
  -H "Content-Type: application/json" \
  -d '{"task": "list files", "mode": "plan_act"}'
```

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional providers
GROQ_API_KEY=gsk-...
ANTHROPIC_API_KEY=sk-ant-...
SAMBANOVA_API_KEY=...
CODESTRAL_API_KEY=...  # Mistral's Codestral

# Phase-specific models
LLM_PLAN_MODEL=openai
LLM_EXECUTE_MODEL=openai
LLM_FALLBACK_MODEL=groq
```

## Deploy to Vercel

1. Push to GitHub
2. Import to Vercel
3. Add environment variables in Vercel dashboard
4. Deploy!

Or via CLI:
```bash
vercel deploy
```

## License

MIT
