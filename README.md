# Multi-Agent Telegram AI Chatbot

A production-style multi-agent Telegram chatbot demonstrating clean architecture with async Python, LangGraph orchestration, and Anthropic Claude.

## Architecture

```
Telegram ──webhook──► FastAPI ──► LangGraph Orchestrator
                                        │
                              ┌─────────▼──────────┐
                              │   Router Agent      │
                              │ (intent classify)   │
                              └──┬──────┬───────┬───┘
                                 │      │       │
                           Research  Writing  Task
                            Agent    Agent    Agent
                                 │      │       │
                              Claude (Anthropic API)
                                        │
                                   PostgreSQL
```

**Flow:** Telegram → `POST /webhook` → FastAPI (returns 200 immediately) → background task → Router classifies intent → Specialist agent → persist reply → send Telegram message.

## Stack

| Layer | Technology |
|-------|-----------|
| Transport | python-telegram-bot webhook |
| API | FastAPI + uvicorn (async) |
| Orchestration | LangGraph StateGraph |
| LLM | Anthropic Claude (swappable to Gemini) |
| Database | PostgreSQL + SQLAlchemy async + asyncpg |
| Migrations | Alembic |
| Logging | structlog (JSON) |
| Containerization | Docker Compose |

## Quick Start

### 1. Prerequisites

- Docker + Docker Compose
- A Telegram bot token ([BotFather](https://t.me/botfather))
- An Anthropic API key

### 2. Configure

```bash
cp .env.example .env
# Edit .env — set TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, TELEGRAM_WEBHOOK_URL
```

### 3. Run

```bash
docker compose up
```

This starts three services: `db` (Postgres 16), `migrate` (Alembic upgrade head), `app` (FastAPI on port 8000).

### 4. Register the webhook

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://your-domain.com/webhook" \
  -d "secret_token=<TELEGRAM_WEBHOOK_SECRET>"
```

### Local development with ngrok

```bash
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000

# In another terminal:
ngrok http 8000
# Copy the https URL → set as TELEGRAM_WEBHOOK_URL in .env, then register webhook
```

## Agents

| Agent | Trigger | Behavior |
|-------|---------|---------|
| **Research** | Factual questions, "what is", "how does" | Answers concisely, flags uncertainty |
| **Writing** | "write", "draft", "compose", "edit" | Drafts text, asks one clarifying question if underspecified |
| **Task** | "add task", "list tasks", "/task" | LLM parses intent → deterministic CRUD on PostgreSQL |
| **Router** | Every message | Keyword heuristics first, then LLM classification (temp=0) |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness check |
| `POST /webhook` | Telegram update receiver |
| `POST /chat` | Direct chat (for testing without Telegram) |

**POST /chat example:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"telegram_id": 12345, "message": "What is quantum computing?"}'
```

## Switching LLM Provider

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key
LLM_MODEL=gemini-1.5-flash
```

## Running Tests

```bash
pytest -q
```

## Project Layout

```
src/
├── main.py               # FastAPI app, /health, /webhook, /chat
├── config.py             # Pydantic Settings (env vars)
├── agents/
│   ├── graph.py          # LangGraph StateGraph orchestrator
│   ├── router.py         # Intent classification
│   ├── research.py       # Research agent
│   ├── writing.py        # Writing agent
│   └── tasks.py          # Task CRUD agent
├── llm/
│   ├── base.py           # LLMProvider abstract interface
│   ├── anthropic.py      # Claude implementation
│   ├── gemini.py         # Gemini implementation
│   └── factory.py        # Provider factory
├── db/
│   ├── models.py         # SQLAlchemy ORM models
│   ├── session.py        # Async session factory
│   ├── repository.py     # DB access functions
│   └── migrations/       # Alembic
├── telegram/
│   ├── client.py         # sendMessage, setWebhook
│   └── webhook.py        # Update handler
└── observability/
    └── logging.py        # structlog JSON setup
```

## Extending

- **Add an agent:** new file in `src/agents/`, add node to `graph.py`, update router prompt.
- **Swap LLM:** implement `LLMProvider`, set `LLM_PROVIDER` env var.
- **Add a channel:** new route + handler alongside `src/telegram/`.
