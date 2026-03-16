# msr_physical_ai_layer

Physical AI layer for robotic operations in Molten Salt Reactor (MSR) systems
such as TMSR‑LF1.  Provides a Model Context Protocol (MCP) server that allows
LLM agents to monitor and coordinate a robot fleet performing maintenance,
inspection, sampling, and safety tasks in high-radiation MSR environments.

## Architecture

```
msr_robot_state.py               – Robot fleet state management & stub data
msr_physical_ai_mcp_server.py    – MCP server (JSON-RPC 2.0 over stdio/HTTP)
test_msr_physical_ai_mcp_server.py – Unit tests
requirements.txt                 – Python dependencies
```

The server integrates with the
[MSR data layer](https://github.com/pranavkantgaur/msr_data_layer) (plant
sensor data / knowledge base) and the
[MSR multi-agent system](https://github.com/pranavkantgaur/msr-gstack) for
end-to-end AI-driven reactor operations.

## Operational Areas (priority order)

| Rank | Area | Robot |
|------|------|-------|
| 1 | Primary loop maintenance & repair | PLMR-01 |
| 2 | Hot-cell chemical processing automation | HCPR-01 |
| 3 | Salt sampling & analysis | SSR-01 |
| 4 | Radiation mapping & autonomous inspection | RMR-01 |
| 5 | Freeze plug safety monitoring | FPMR-01 |
| 6 | Fuel salt transport & refilling | FSTR-01 |
| 7 | Graphite moderator inspection & replacement | GIR-01 |
| 8 | Tritium management systems | TMR-01 |
| 9 | Off-gas system handling | OGSR-01 |
| 10 | Waste salt handling & solidification | WSHR-01 |
| 11 | External structural inspection | SIR-01 |
| 12 | Security & safeguards monitoring | SPR-01 |

## MCP Tools

### Read tools
| Tool | Description |
|------|-------------|
| `get_robot_fleet_status` | Summary of all 12 robots (status, battery, dose) |
| `get_robot_status` | Detailed state for a single robot |
| `get_active_operations` | All currently running robotic operations |
| `get_task_status` | Status of a specific task by `task_id` |
| `get_task_log` | Recent task history |
| `get_operational_areas` | All 12 operational areas with descriptions |
| `get_data_source_info` | Data-source connectivity information |

### Command tools
| Tool | Description |
|------|-------------|
| `dispatch_robot_task` | Dispatch a robot to perform a named task |
| `abort_robot_task` | Abort the current task and return the robot to IDLE |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the MCP server (reads JSON-RPC messages from stdin, writes to stdout)
python msr_physical_ai_mcp_server.py

# Run tests
pytest test_msr_physical_ai_mcp_server.py -v
```

## Configuration

| Variable | Description |
|----------|-------------|
| `MSR_ROBOT_CONTROL_URL` | Base URL of an external robot-control REST API.<br>When unset, a representative development stub is used. |

The external API must respond to `GET <MSR_ROBOT_CONTROL_URL>/fleet` with a
JSON object mapping robot IDs to robot state dictionaries.
