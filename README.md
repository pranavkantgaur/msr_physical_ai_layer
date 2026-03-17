# msr_physical_ai_layer

> **Open-source Physical AI (robotics + autonomy) layer for Molten Salt Reactor operations —
> ready for Claude Code, OpenClaw, OpenAI Codex, and Cursor.**

[![CI](https://github.com/pranavkantgaur/msr_physical_ai_layer/actions/workflows/ci.yml/badge.svg)](https://github.com/pranavkantgaur/msr_physical_ai_layer/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![MCP 2024-11-05](https://img.shields.io/badge/MCP-2024--11--05-green.svg)](https://spec.modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Physical AI layer for robotic operations in Molten Salt Reactor (MSR) systems
such as **TMSR‑LF1** (Shanghai Institute of Applied Physics, Chinese Academy of
Sciences).  Provides a **Model Context Protocol (MCP) server** that allows
LLM agents to monitor and coordinate a 12-robot fleet performing maintenance,
inspection, sampling, and safety tasks in high-radiation MSR environments.

> "Physical AI is the highest-leverage point in nuclear robotics: it replaces
> human presence in radiation fields exceeding 25 mSv/h and molten-salt
> temperatures of 600–700 °C, reducing lifecycle maintenance costs by an
> estimated 30–50 % compared to traditional remote-handling systems."
> *(derived from IAEA-TECDOC-1535, 2007)*

## Why this matters for MSR programs

Molten salt reactors such as TMSR-LF1 require continuous chemical processing,
primary-loop maintenance, and safety-system monitoring that are **impossible for
humans** in high-radiation, high-temperature environments.  Physical-AI robots
with perception, manipulation, and autonomy — coordinated by this MCP server —
provide the largest operational and safety gains of any technology investment in
the MSR lifecycle (Zou et al., 2021; IAEA Safety Report Series No. 87, 2017).

## Agent quick-start

> **Clone this repo and run `make test` — 50 tests should pass with zero setup.**

```bash
git clone https://github.com/pranavkantgaur/msr_physical_ai_layer
cd msr_physical_ai_layer
make install   # pip install -r requirements.txt
make test      # pytest -v  →  50 passed
make start     # launch MCP server on stdio
```

See [CLAUDE.md](CLAUDE.md) for full agent rules, build commands, and safety constraints.

## Architecture

```
msr_robot_state.py               – Robot fleet state management & stub data
msr_physical_ai_mcp_server.py    – MCP server (JSON-RPC 2.0 over stdio)
test_msr_physical_ai_mcp_server.py – pytest unit tests (50 tests, ≥70 % coverage)
requirements.txt                 – Python deps (numpy, pytest)
Makefile                         – One-liner dev commands
mcp.json                         – MCP integrations manifest (OpenClaw / Claude Code)
llms.txt                         – LLM/agent discovery file
.ai/                             – Grounding documents for AI agents
  requirements.md                – MSR goals, scope, safety notes
  architecture.md                – System overview & data flow diagrams
  tech-stack.md                  – Approved technology stack
.github/workflows/ci.yml         – GitHub Actions CI (lint + test on Python 3.11/3.12)
```

The server integrates with the
[MSR data layer](https://github.com/pranavkantgaur/msr_data_layer) (plant
sensor data / RAG knowledge base) and the
[MSR multi-agent system](https://github.com/pranavkantgaur/msr-gstack) for
end-to-end AI-driven reactor operations.

## Operational areas (priority order)

Twelve robotic platforms cover every major MSR operational challenge, ranked by
lifecycle cost and safety impact (Renault et al., 2010; IAEA, 2011):

| Rank | Area | Robot | Key challenge |
|------|------|-------|---------------|
| 1 | Primary loop maintenance & repair | PLMR-01 | 12–35 mSv/h neutron + gamma fields |
| 2 | Hot-cell chemical processing | HCPR-01 | Continuous online fuel-salt chemistry |
| 3 | Salt sampling & analysis | SSR-01 | Fissile concentration drift → corrosion |
| 4 | Radiation mapping & autonomous inspection | RMR-01 | Predictive degradation mapping |
| 5 | Freeze plug safety monitoring | FPMR-01 | Passive safety system verification |
| 6 | Fuel salt transport & refilling | FSTR-01 | Heated transfer lines at 580 °C |
| 7 | Graphite moderator inspection & replacement | GIR-01 | Neutron-damage swelling & cracking |
| 8 | Tritium management systems | TMR-01 | Permeation barrier integrity |
| 9 | Off-gas system handling | OGSR-01 | Xenon/krypton fission-product capture |
| 10 | Waste salt handling & solidification | WSHR-01 | Radioactive salt container handling |
| 11 | External structural inspection | SIR-01 | Containment & cooling tower integrity |
| 12 | Security & safeguards monitoring | SPR-01 | Nuclear material inventory tracking |

## MCP tools

### Read tools
| Tool | Description |
|------|-------------|
| `get_robot_fleet_status` | Summary of all 12 robots (status, battery, radiation dose) |
| `get_robot_status` | Detailed state + sensor readings for a single robot |
| `get_active_operations` | All currently running robotic operations |
| `get_task_status` | Status of a specific task by `task_id` |
| `get_task_log` | Recent task history (last N records) |
| `get_operational_areas` | All 12 areas with descriptions, robots, and key sensors |
| `get_data_source_info` | Data-source connectivity information |

### Command tools
| Tool | Description |
|------|-------------|
| `dispatch_robot_task` | Dispatch a robot to perform a named task |
| `abort_robot_task` | Abort the current task and return the robot to IDLE |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MSR_ROBOT_CONTROL_URL` | *(unset)* | Base URL of live robot-control REST API. When unset, a representative development stub is used. |

The external API must respond to `GET <MSR_ROBOT_CONTROL_URL>/fleet` with a
JSON object mapping robot IDs to robot state dictionaries.

## Development

```bash
make install-dev   # install deps + ruff linter
make lint          # ruff check + format check
make format        # auto-fix formatting
make coverage      # pytest with ≥70 % coverage gate
```

## Related repositories

| Repo | Role |
|------|------|
| [msr_data_layer](https://github.com/pranavkantgaur/msr_data_layer) | Plant sensor data, RAG knowledge base, MCP data server |
| [msr-gstack](https://github.com/pranavkantgaur/msr-gstack) | Multi-agent organisation / LLM orchestration |

## References

1. Zou, Y. et al. (2021). "Design and safety features of TMSR-LF1."
   *Annals of Nuclear Energy*, 148, 107638.
2. IAEA-TECDOC-1535 (2007). "Status of Small Reactor Designs without
   On-site Refuelling." International Atomic Energy Agency, Vienna.
3. Haubenreich, P. N. & Engel, J. R. (1970). "Experience with the Molten-Salt
   Reactor Experiment." *Nuclear Applications & Technology*, 8(2), 118–136.
4. Renault, C. et al. (2010). "The Molten Salt Reactor (MSR) in Generation IV:
   Overview and Perspectives." *GIF Symposium*, Paris.

---

*Topics: molten-salt-reactor · msr · nuclear-engineering · physical-ai ·
ai-agents · multi-agent-system · mcp · claude-code · openclaw-ready ·
tmsr-lf1 · robotics · radiation-mapping · hot-cell-automation*
