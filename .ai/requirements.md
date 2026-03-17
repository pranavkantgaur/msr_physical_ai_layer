# MSR Physical AI Layer — Requirements

## Project goals

This repository provides the **physical-AI layer** for robotic operations at
Molten Salt Reactor (MSR) facilities.  The primary target is TMSR-LF1, a
10 MWth fluoride-salt-cooled thorium reactor developed by the Shanghai
Institute of Applied Physics (SINAP) under the Chinese Academy of Sciences.

### In scope

1. **MCP server** — expose robotic fleet status, task dispatch, and abort via
   Model Context Protocol (JSON-RPC 2.0 over stdio).
2. **Robot fleet state management** — 12 robot platforms covering every major
   MSR operational area (primary loop maintenance, hot-cell chemistry, salt
   sampling, radiation mapping, freeze-plug monitoring, fuel transport,
   graphite inspection, tritium management, off-gas handling, waste salt,
   structural inspection, security patrol).
3. **Development stub** — representative sensor and status data so the server
   can be exercised without a live robot-control system.
4. **External API bridge** — forward fleet queries to a live robot-control REST
   API when `MSR_ROBOT_CONTROL_URL` is configured.
5. **Integration hooks** — compatibility with the MSR data layer
   (`msr_data_layer`) and multi-agent orchestration (`msr-gstack`).

### Out of scope

- Real-time hardware control loops (this server is a **coordination layer**,
  not a PLC replacement).
- Reactor physics simulation or safety-system actuation.
- Authentication / authorisation (assumed to be handled by the network
  perimeter around the robot-control API).
- Persistent storage — all state is in-memory; production deployments should
  add a time-series database behind `MSR_ROBOT_CONTROL_URL`.

## Safety notes

> ⚠️ **Nuclear environment — special constraints apply.**

1. **Fail-safe abort**: The `abort_robot_task` tool must always succeed or
   return a clear error.  No silent swallowing.  No auto-retry.
2. **Radiation dose tracking**: Every robot accumulates `radiation_dose_accumulated_msv`.
   Agents must monitor this and recommend robot rotation when thresholds are
   approached (occupational limit: 20 mSv/year whole-body; ALARA applies).
3. **Temperature constraints**: Primary loop robots operate near 700 °C molten
   salt.  Task parameters that include physical contact must specify
   thermal-standoff distances.
4. **No autonomous hardware actuation without human-in-the-loop confirmation**
   for safety-critical tasks (valve actuation, drain operations, freeze-plug
   interference).  The MCP server dispatches tasks but does not bypass any
   hardware interlock.
5. **Tritium handling**: TMR-01 operates in tritium-bearing environments.
   Alert thresholds (`tritium_conc_bq_m3 > 1e5`) should trigger immediate
   notification before any maintenance dispatch.

## Non-functional requirements

| Requirement | Target |
|-------------|--------|
| Startup time | < 2 s (no I/O on import) |
| Tool response latency | < 100 ms (stub) / < 5 s (external API with timeout) |
| Test coverage | ≥ 70 % line coverage on core modules |
| Python version | 3.11+ |
| External dependencies | Minimal; `numpy` and `pytest` only |

## Relationship to other repos

```
msr_data_layer          → plant sensor data, RAG knowledge base
msr_physical_ai_layer   → robot fleet coordination (this repo)
msr-gstack              → multi-agent org / LLM orchestration
```
