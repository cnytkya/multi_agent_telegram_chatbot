# Multi-Agent Telegram AI Chatbot

A production-style multi-agent AI chatbot with a Next.js web UI and Telegram integration. Built with LangGraph orchestration, FastAPI backend, and support for local LLMs via Ollama.

## Architecture

```
Browser ──────────────────────────────────────────────►
                                                        Next.js (port 3000)
Telegram ──webhook──► FastAPI (port 8001) ◄────────────
                            │
                     LangGraph Orchestrator
                            │
              ┌─────────────┼─────────────┐
              │             │             │
          Research       Writing        Task
           Agent          Agent         Agent
              │             │             │
              └─────────────┴─────────────┘
                            │
                     Ollama / Claude / Gemini
                            │
                       PostgreSQL
```

## Stack

| Layer | Technology |
|-------|-----------|
| Web UI | Next.js 15, TypeScript, Tailwind CSS |
| API | FastAPI + uvicorn (async) |
| Orchestration | LangGraph StateGraph |
| LLM | Ollama (local) · Anthropic Claude · Google Gemini |
| Database | PostgreSQL 16 + SQLAlchemy async + asyncpg |
| Migrations | Alembic |
| Logging | structlog (JSON) |
| Containerization | Docker Compose |

## Quick Start

### 1. Clone & configure

```bash
git clone https://github.com/cnytkya/multi_agent_telegram_chatbot
cd multi_agent_telegram_chatbot
cp .env.example .env
# .env dosyasını düzenle — LICENSE_KEY zorunlu (aşağıya bak)
```

### 2. Start services

```bash
docker compose up -d
```

Starts: `db` · `migrate` · `ollama` · `app` (port 8001) · `frontend` (port 3000)

### 3. Pull a model

```bash
docker compose exec ollama ollama pull llama3.2
```

### 4. Open

| URL | Description |
|-----|-------------|
| http://localhost:3000 | Web chat UI |
| http://localhost:8001/docs | FastAPI Swagger UI |
| http://localhost:8001/health | Health check |

---

## Web UI

Next.js 15 + TypeScript chat interface:

- **Agent badges** — color-coded per agent (Research / Writing / Tasks)
- **Typing indicator** — animated dots while waiting
- **Suggestion chips** — quick-start prompts on empty chat
- `Enter` to send · `Shift+Enter` for newline
- User ID persisted in `localStorage`

## Agents

| Agent | Triggered by | Behavior |
|-------|-------------|---------|
| **Research** | Factual questions, "what is", "how does" | Answers concisely, flags uncertainty |
| **Writing** | "write", "draft", "compose", "edit" | Drafts text, asks one clarifying question if underspecified |
| **Task** | "add task", "list tasks", "/task" | LLM parses intent → deterministic CRUD on PostgreSQL |
| **Router** | Every message | Keyword heuristics first, then LLM classification (temp=0) |

**Task commands:**
```
add task buy milk      → adds to list
list tasks             → shows all tasks
done 1                 → marks #1 complete
delete 2               → removes #2
```

## Telegram Integration

1. Create a bot via [@BotFather](https://t.me/botfather) — get your `TELEGRAM_BOT_TOKEN`
2. Expose local port with ngrok: `ngrok http 8001`
3. Set in `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_WEBHOOK_SECRET=any_random_string
   TELEGRAM_WEBHOOK_URL=https://your-ngrok-url.ngrok.io/webhook
   ```
4. Register webhook:
   ```bash
   curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
     -d "url=https://your-ngrok-url.ngrok.io/webhook" \
     -d "secret_token=<TELEGRAM_WEBHOOK_SECRET>"
   ```
5. `docker compose restart app`

## LLM Providers

Set `LLM_PROVIDER` in `.env`:

| Provider | Config |
|----------|--------|
| `ollama` (default) | `LLM_MODEL=llama3.2` · `OLLAMA_BASE_URL=http://ollama:11434` |
| `anthropic` | `LLM_MODEL=claude-sonnet-4-6` · `ANTHROPIC_API_KEY=...` |
| `gemini` | `LLM_MODEL=gemini-1.5-flash` · `GEMINI_API_KEY=...` |

## License

This project requires a license key to run.
Contact **[@cnytkya](https://github.com/cnytkya)** to obtain one.

```env
LICENSE_KEY=your_key_here
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Liveness check |
| POST | `/chat` | Direct chat (no Telegram needed) |
| POST | `/webhook` | Telegram webhook receiver |

**POST /chat example:**
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"telegram_id": 12345, "message": "What is quantum computing?"}'
```

## Project Layout

```
├── frontend/                  # Next.js 15 web UI
│   ├── app/                   # App Router pages
│   ├── components/            # ChatWindow, MessageBubble, AgentBadge
│   └── types/                 # TypeScript types
├── src/
│   ├── main.py                # FastAPI app, /health, /webhook, /chat
│   ├── config.py              # Pydantic Settings
│   ├── license.py             # License key validation
│   ├── agents/
│   │   ├── graph.py           # LangGraph StateGraph
│   │   ├── router.py          # Intent classification
│   │   ├── research.py        # Research agent
│   │   ├── writing.py         # Writing agent
│   │   └── tasks.py           # Task CRUD agent
│   ├── llm/
│   │   ├── base.py            # LLMProvider interface
│   │   ├── anthropic.py       # Claude
│   │   ├── gemini.py          # Gemini
│   │   ├── ollama.py          # Ollama (local)
│   │   └── factory.py         # Provider factory
│   ├── db/
│   │   ├── models.py          # SQLAlchemy ORM
│   │   ├── session.py         # Async session
│   │   ├── repository.py      # DB access layer
│   │   └── migrations/        # Alembic
│   ├── telegram/
│   │   ├── client.py          # sendMessage, setWebhook
│   │   └── webhook.py         # Update handler
│   └── observability/
│       └── logging.py         # structlog JSON
└── tests/                     # pytest test suite
```

## Extending

- **Add an agent** — new file in `src/agents/`, add node to `graph.py`, update router prompt
- **Swap LLM** — implement `LLMProvider`, set `LLM_PROVIDER` env var
- **Add a channel** — new route + handler alongside `src/telegram/`
