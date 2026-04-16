# Shelter Network Platform

A multi-agent AI platform that simulates a network of animal shelters. Built as a portfolio project demonstrating local LLM orchestration, containerized microservices, and edge-deployed frontends.

**Live dashboard:** https://thestrad031487.github.io/shelter-platform  
**API:** https://shelter-api.cybergrind.org

---

## What it does

- Simulates 5 animal shelters across the US with realistic animal intake and adoption activity
- Uses local LLM agents (Ollama) to generate animal adoption profiles and manage shelter state
- Exposes a REST API serving live metrics, animal listings, and event history
- Renders a public dashboard on GitHub Pages pulling from the live API

---

## Architecture
GitHub Pages (dashboard)
|
| HTTPS
v
Cloudflare Tunnel
|
v
FastAPI (shelter-api) ←── Agents (shelter-agents)
|                        |
v                        v
PostgreSQL (shelter-db)     Ollama (shared, ai-stack)
- No ports exposed on the home network — all ingress via Cloudflare Tunnel
- Agents communicate with the API over Docker internal networking
- Ollama runs on a shared Docker network (`ai-shared`) alongside a separate AI stack
- Dashboard is fully static — no server-side rendering, no build step

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla HTML/JS, GitHub Pages |
| API | FastAPI, Python 3.11 |
| Database | PostgreSQL 16 |
| Agents | Python, Ollama (Mistral, LLaMA 3.2) |
| Inference | Ollama + NVIDIA RTX 3060 (local GPU) |
| Networking | Cloudflare Tunnel, Docker Compose |
| Orchestration | Docker Compose (isolated stack) |

---

## Agents

### Generator agent
Seeds the database with shelter profiles and animals. Calls Ollama (Mistral) to write a unique adoption bio for each animal. Run once to initialize.

### Updater agent
Simulates shelter activity — processes adoptions (~10% of available animals) and adds new intakes (1–3 animals) per run. Each new intake gets an Ollama-generated bio.

---

## API endpoints

| Endpoint | Description |
|---|---|
| `GET /shelters` | All shelters with capacity data |
| `GET /animals` | All animals, filterable by `status` and `shelter_id` |
| `GET /metrics` | Adoption rate, counts, capacity utilization |
| `GET /events` | Recent intake and adoption events |
| `GET /health` | Health check |

---

## Running locally

### Prerequisites
- Docker + Docker Compose
- Ollama running and accessible (local or networked)
- A shared Docker network: `docker network create ai-shared`

### Start the stack
```bash
cp .env.example .env  # add your values
docker compose up -d
```

### Seed initial data
```bash
docker compose run --rm shelter-agents python main.py generate
```

### Run an update cycle
```bash
docker compose run --rm shelter-agents python main.py update
```

---

## Environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `OLLAMA_URL` | Ollama API base URL |
| `API_URL` | Internal API URL for agents |
| `CLOUDFLARE_TUNNEL_TOKEN` | Cloudflare tunnel token |

---

## Project structure
shelter-platform/
├── docker-compose.yml
├── shelter-api/          # FastAPI application
│   ├── main.py           # Routes and endpoints
│   ├── models.py         # SQLAlchemy models
│   ├── database.py       # DB connection
│   └── Dockerfile
├── shelter-agents/       # AI agent pipeline
│   ├── main.py           # Entry point (generate / update)
│   ├── agents/
│   │   ├── generator.py  # Seed shelters and animals
│   │   └── updater.py    # Simulate adoptions and intakes
│   └── Dockerfile
└── shelter-dashboard/    # Static frontend
└── index.html
---

## Related projects

This platform shares infrastructure with a self-hosted AI stack documented on [CyberGrind](https://cybergrind.org), including:
- [Self-Hosted AI Stack (OpenClaw + Ollama + GPU + Tailscale)](https://cybergrind.org/orange-book/self-hosted-ai-stack/)
- [Building Cybersecurity Agents](https://cybergrind.org/orange-book/cybersecurity-agents-pipeline/)
