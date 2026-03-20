# MSR Physical AI Layer — Technology Stack

> AI agents: **do not introduce technologies outside this list** without
> discussion.  Adding new dependencies requires updating `requirements.txt`
> and this file.

## Core language

| Technology | Version | Role |
|------------|---------|------|
| Python | 3.11+ | Only language in this repo |

## Standard-library modules used

| Module | Purpose |
|--------|---------|
| `json` | JSON serialisation / deserialisation |
| `os` | Environment variable access |
| `urllib.request` | HTTP calls to external robot-control API (no extra deps) |
| `datetime` | Timestamps for tasks and sensor readings |
| `typing` | Type annotations |
| `copy` | Deep-copy of mutable state |
| `sys` | Stderr logging |

## Third-party dependencies

| Package | Version constraint | Purpose |
|---------|--------------------|---------|
| `numpy` | >=1.24.0 | Dense vector support (future sensor-fusion / RAG integration) |
| `pytest` | >=8.0.0 | Unit testing framework |
| `ruff` | *(dev only)* | Linting and formatting (PEP 8 + isort) |

## Protocols

| Protocol | Version | Use |
|----------|---------|-----|
| MCP (Model Context Protocol) | 2024-11-05 | Wire protocol between LLM agents and this server |
| JSON-RPC | 2.0 | Transport for MCP messages |

## What is deliberately NOT used

| Technology | Reason for exclusion |
|------------|----------------------|
| FastAPI / Flask / aiohttp | Adds complexity; stdio transport is sufficient for MCP |
| SQLAlchemy / any ORM | No persistent DB in this layer |
| Pydantic | Would be appropriate but kept out to minimise deps |
| asyncio | Synchronous server keeps the code simple and testable |
| Docker | Left to the deployment layer (msr-gstack) |
| Redis / RabbitMQ | Message queuing not needed at this layer |

## Approved future additions (pre-approved, no discussion needed)

| Package | When to add |
|---------|-------------|
| `httpx` | Only if async HTTP to external robot API is needed |
| `influxdb-client` | Only if persistent time-series state storage is added |
| `openai` | Only if local LLM inference is added to this layer |
| `mcp` (official SDK) | If official Anthropic MCP Python SDK support is needed |
