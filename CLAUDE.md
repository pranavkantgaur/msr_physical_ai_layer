# CLAUDE.md — MSR Physical AI Layer

> **For AI agents (Claude Code, OpenClaw, GitHub Copilot, Codex, Cursor):**
> This file is your primary reference. Read it fully before touching any code.

## What this repo does

`msr_physical_ai_layer` is a **Python MCP (Model Context Protocol) server** that
lets LLM agents monitor and command a 12-robot fleet operating in high-radiation
Molten Salt Reactor (MSR) environments such as the TMSR-LF1 at SINAP, China.

It is one layer in a four-repo MSR AI stack:

| Repo | Role |
|------|------|
| [msr_data_layer](https://github.com/pranavkantgaur/msr_data_layer) | Plant sensor data, RAG knowledge base, MCP data server |
| **msr_physical_ai_layer** (this repo) | Physical-AI robot fleet MCP server |
| [msr-gstack](https://github.com/pranavkantgaur/msr-gstack) | Multi-agent organisation / company template |

## Repo layout

```
msr_robot_state.py                – Robot fleet state + task lifecycle (no external deps)
msr_physical_ai_mcp_server.py     – MCP JSON-RPC 2.0 server (9 tools)
test_msr_physical_ai_mcp_server.py – pytest unit tests (50 tests)
requirements.txt                  – Python deps (numpy, pytest)
Makefile                          – One-liner dev commands
mcp.json                          – MCP integrations manifest
llms.txt                          – LLM/agent discovery file
.ai/                              – Grounding docs for agents
  requirements.md                 – MSR goals, scope, safety
  architecture.md                 – System overview & data flow
  tech-stack.md                   – Approved technology stack
```

## One-liner commands (memorise these)

```bash
make install    # pip install -r requirements.txt
make test       # pytest -v
make lint       # ruff check + ruff format --check
make start      # run MCP server on stdio
make coverage   # pytest --cov with coverage report
```

## Development rules

### Language & style
- **Python 3.11+** only.
- Follow **PEP 8**; use `ruff` for linting and formatting.
- All public functions must have **Google-style docstrings**.
- No f-strings with side effects; keep expressions in f-strings simple.
- Use `typing.Any` for JSON payloads; avoid `dict` without type params.

### Adding tools to the MCP server
1. Write the handler function in `msr_physical_ai_mcp_server.py`.
2. Add an entry to the `TOOLS` list (name, description, inputSchema, handler).
3. Write at least **two tests** per new tool in `test_msr_physical_ai_mcp_server.py`.
4. Run `make test` to confirm all pass.

### Modifying robot state
- All mutable state lives in `msr_robot_state.py` (`_STUB_ROBOT_FLEET`, `_TASK_LOG`).
- State functions (`create_task`, `abort_task`, etc.) return **copies** — never mutate the caller's dict.
- Do not add external databases or I/O without discussion.

### Adding a new robot / operational area
1. Add an entry to `OPERATIONAL_AREAS` in `msr_robot_state.py`.
2. Add the corresponding entry to `_STUB_ROBOT_FLEET`.
3. Update `AREA_MAP`.
4. Add tests for the new robot in the test file.

### Secrets & environment variables
- **Never hardcode** credentials, URLs, or API keys.
- Use `.env` (excluded from git) and read via `os.environ.get(...)`.
- Document every new env var in both `CLAUDE.md` and `README.md`.

### Safety-critical note
> ⚠️ This server issues commands to robots operating in **nuclear environments**
> with live radiation, molten salt at 600–700 °C, and tritium.
> Never add auto-retry logic for `abort_robot_task` — a single authoritative
> abort is the correct pattern.  Always propagate errors; never silently swallow
> them in command-path code.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MSR_ROBOT_CONTROL_URL` | *(unset)* | Base URL of live robot-control REST API. When unset, development stub is used. |

## Testing strategy

- **All new code must have unit tests** before merging.
- Tests use `pytest` + `monkeypatch` — no live network calls.
- Test file: `test_msr_physical_ai_mcp_server.py`.
- Target: ≥ 70 % line coverage on `msr_physical_ai_mcp_server.py` and `msr_robot_state.py`.
- Run: `make coverage` to check.

## CI

GitHub Actions runs on every push and pull request:
- `make lint` (ruff check + format)
- `make test` (pytest)

See `.github/workflows/ci.yml`.

## How to connect to the MSR data layer

Set `MSR_PLANT_DATA_URL` pointing at the `msr_data_layer` MCP server, then
the data layer's sensor readings become available alongside robot state for
fused LLM queries.

## GTC 2026 Physical AI integration guide

Key innovations from NVIDIA GTC 2026 that are relevant to this repo are analysed
in [`.ai/gtc2026-physical-ai.md`](.ai/gtc2026-physical-ai.md).

TL;DR for agents:
- **Opentrons Flex** (EX82361) can serve as the `MSR_ROBOT_CONTROL_URL` backend
  for HCPR-01 (hot-cell chemistry) and SSR-01 (salt sampling) with a thin REST adapter.
- **NVIDIA Isaac ROS** is the target ROS 2 bridge for all 12 robots.
- **NVIDIA HALOS** formalises the safety constraints already in `.ai/requirements.md`.
- **Newton physics engine** + **Isaac Lab** is the training stack for manipulation tasks.
- **Cosmos-Predict2** generates synthetic MSR environment data for sim-to-real training.

## Relevant papers & references

- Zou, Y. et al. (2021). "Design and safety features of TMSR-LF1." *Ann. Nucl. Energy*, 148, 107638.
- IAEA-TECDOC-1535 (2007). "Status of Small Reactor Designs without On-site Refuelling."
- Haubenreich & Engel (1970). "Experience with the MSRE." *Nucl. Appl. Technol.* 8(2).
- Mittal, M. et al. (2025). "Isaac Lab: A GPU-Accelerated Simulation Framework for Multi-Modal Robot Learning." *arXiv:2511.04831*.
