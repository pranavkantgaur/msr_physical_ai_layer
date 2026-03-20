# MSR Physical AI Layer — Architecture

## Overview

The physical-AI layer is a **thin coordination server** that sits between
LLM agents and the robot fleet inside an MSR facility.  It is intentionally
stateless (besides in-memory stub data) and side-effect-free on the data path;
all physical actuation happens in the downstream robot-control system.

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM Agent (Claude, GPT-5, etc.)          │
│   (running inside msr-gstack multi-agent orchestrator)      │
└──────────────────────────┬──────────────────────────────────┘
                           │ MCP JSON-RPC 2.0 (stdio / HTTP)
┌──────────────────────────▼──────────────────────────────────┐
│           msr_physical_ai_mcp_server.py  (this repo)        │
│                                                             │
│  Tools:  get_robot_fleet_status  get_robot_status           │
│          get_active_operations   get_task_status            │
│          get_task_log            get_operational_areas      │
│          get_data_source_info                               │
│          dispatch_robot_task     abort_robot_task           │
└──────────┬───────────────────────┬──────────────────────────┘
           │ (stub, in-process)    │ HTTP GET/POST
           │                       │ MSR_ROBOT_CONTROL_URL
┌──────────▼──────────┐  ┌────────▼────────────────────────┐
│  msr_robot_state.py │  │  External Robot-Control REST API │
│  (development stub) │  │  (ROS 2 bridge, SCADA adapter,  │
│  12 robot platforms │  │   or hardware-in-the-loop sim)  │
└─────────────────────┘  └─────────────────────────────────┘
```

## Data flow

### Read path (monitoring)

```
Agent calls get_robot_fleet_status
    → handle_message() dispatches to get_robot_fleet_status()
    → _get_current_fleet() checks MSR_ROBOT_CONTROL_URL
        ├── if set:  HTTP GET <URL>/fleet → parse JSON → return
        └── if unset: msr_robot_state.get_fleet_state() → deep-copy of stub
    → JSON-RPC result returned to agent
```

### Write path (task dispatch)

```
Agent calls dispatch_robot_task(robot_id, task_type, description, parameters)
    → validate inputs (non-empty strings)
    → msr_robot_state.create_task()
        ├── check robot exists
        ├── check robot not FAULT / OFFLINE / already ACTIVE
        ├── allocate task_id (TASK-<robot_id>-<counter>)
        ├── set robot status = ACTIVE, current_task = task dict
        └── append to _TASK_LOG
    → return task dict to agent
```

### Abort path (safety)

```
Agent calls abort_robot_task(robot_id)
    → msr_robot_state.abort_task()
        ├── find robot
        ├── find active task in _TASK_LOG → set status = ABORTED, completed_at = now
        ├── set robot status = IDLE, current_task = None
        └── return {success, aborted_task_id, timestamp}
    → result returned to agent immediately (no retries)
```

## Module responsibilities

### `msr_physical_ai_mcp_server.py`
- JSON-RPC 2.0 message dispatch (`handle_message`)
- MCP protocol surface: `initialize`, `tools/list`, `tools/call`
- Tool handler functions (pure Python, no side effects on reads)
- External API bridge (`_get_current_fleet`, `_get_fleet_from_external`)
- `TOOLS` list + `TOOL_MAP` registry

### `msr_robot_state.py`
- `OPERATIONAL_AREAS` — static registry of 12 MSR operational areas
- `AREA_MAP` — dict keyed by `area_id`
- `_STUB_ROBOT_FLEET` — in-memory mutable robot state (status, sensors, task)
- `_TASK_LOG` — append-only list of all task records
- State accessor / mutator functions:
  - `get_fleet_state()`, `get_robot()`, `get_task_log()`, `get_task_by_id()`
  - `create_task()`, `abort_task()`

## 12 Operational areas (priority order)

| Rank | Area ID | Robot | Primary sensors |
|------|---------|-------|-----------------|
| 1 | `primary_loop_maintenance` | PLMR-01 | loop_temp_c, neutron_dose_rate_msv_h |
| 2 | `hot_cell_chemical_processing` | HCPR-01 | redox_potential_mv, cell_gamma_dose_rate_msv_h |
| 3 | `salt_sampling_analysis` | SSR-01 | fissile_conc_g_l, corrosion_product_ppm |
| 4 | `radiation_mapping_inspection` | RMR-01 | gamma_dose_rate_msv_h, neutron_flux_n_cm2_s |
| 5 | `freeze_plug_monitoring` | FPMR-01 | plug_temp_c, drain_tank_level_pct |
| 6 | `fuel_salt_transport` | FSTR-01 | transfer_line_temp_c, leak_detection_ok |
| 7 | `graphite_moderator_inspection` | GIR-01 | crack_count, swelling_mm |
| 8 | `tritium_management` | TMR-01 | tritium_conc_bq_m3, cold_trap_temp_c |
| 9 | `off_gas_system` | OGSR-01 | xenon_activity_bq_m3, filter_dp_bar |
| 10 | `waste_salt_handling` | WSHR-01 | container_dose_rate_msv_h, solidification_pct |
| 11 | `structural_inspection` | SIR-01 | crack_width_mm, ambient_dose_rate_msv_h |
| 12 | `security_safeguards` | SPR-01 | intrusion_detected, material_inventory_ok |

## Integration with other MSR repos

### msr_data_layer
The data layer provides plant sensor readings (core temperature, neutron flux,
salt chemistry) via its own MCP server.  Agents can query both servers in
parallel — robot state from this server, plant state from the data layer —
to make fused maintenance decisions.

### msr-gstack
The multi-agent orchestration repo provides the LLM agent infrastructure that
calls into this MCP server.  Typical pattern: a `MaintenancePlannerAgent`
queries the data layer for anomalies and then dispatches robot tasks via this
physical-AI layer.

## Extension points

- **External robot-control API**: Set `MSR_ROBOT_CONTROL_URL` to integrate with
  a ROS 2 bridge or SCADA adapter without changing any Python code.
- **New operational areas**: Add to `OPERATIONAL_AREAS` and `_STUB_ROBOT_FLEET`
  in `msr_robot_state.py`; the MCP server picks them up automatically.
- **Persistent state**: Replace `_STUB_ROBOT_FLEET` and `_TASK_LOG` with a
  time-series DB adapter (InfluxDB, TimescaleDB) behind the existing state
  accessor functions.

## Physical AI ecosystem integration (GTC 2026)

The diagram below shows how current-generation physical-AI platforms from GTC 2026
slot into the architecture via the `MSR_ROBOT_CONTROL_URL` extension point:

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM Agent (Claude, GPT-5, etc.)          │
└──────────────────────────┬──────────────────────────────────┘
                           │ MCP JSON-RPC 2.0 (stdio)
┌──────────────────────────▼──────────────────────────────────┐
│           msr_physical_ai_mcp_server.py  (this repo)        │
│   dispatch_robot_task / abort_robot_task / monitoring tools │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP  MSR_ROBOT_CONTROL_URL
             ┌─────────────┼──────────────────┐
             │             │                  │
   ┌─────────▼──────┐ ┌────▼──────────┐ ┌────▼──────────────────┐
   │ Opentrons Flex │ │ NVIDIA Isaac  │ │ TMSR-LF1 Omniverse    │
   │ REST adapter   │ │ ROS 2 bridge  │ │ Digital Twin (USD)     │
   │ (HCPR / SSR)   │ │ (all 12 bots) │ │ + Isaac Lab policies  │
   └────────────────┘ └───────────────┘ └───────────────────────┘
```

Priority integrations (from GTC 2026 analysis):

| Priority | Platform | Sessions | Robots served |
|----------|----------|----------|---------------|
| 1 | Opentrons Flex — Python Protocol API | EX82361 | HCPR-01, SSR-01 |
| 2 | NVIDIA Isaac ROS 2 bridge | S82100 | All 12 |
| 3 | NVIDIA HALOS safety framework | CWES81819 | All 12 (abort path) |
| 4 | TMSR-LF1 Omniverse digital twin | S81875, CWES81472 | All 12 |
| 5 | Isaac Lab + Newton policy training | S81613, DLIT81700 | PLMR-01, GIR-01, WSHR-01 |

Full analysis: see [`.ai/gtc2026-physical-ai.md`](gtc2026-physical-ai.md).
