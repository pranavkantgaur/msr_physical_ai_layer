"""
MSR Physical AI Layer – MCP Server

Exposes MSR (Molten Salt Reactor) physical-AI robotic operations through the
Model Context Protocol (MCP), allowing LLM agents to monitor and coordinate
the robot fleet that performs maintenance, inspection, sampling, and safety
tasks on MSR systems such as TMSR-LF1.

The server covers twelve operational areas (in descending priority):

  1.  Primary loop maintenance & repair
  2.  Hot-cell chemical processing automation
  3.  Salt sampling & analysis
  4.  Radiation mapping & autonomous inspection
  5.  Freeze plug safety monitoring
  6.  Fuel salt transport & refilling
  7.  Graphite moderator inspection & replacement
  8.  Tritium management systems
  9.  Off-gas system handling
  10. Waste salt handling & solidification
  11. External structural inspection
  12. Security & safeguards monitoring

Data Source
-----------
Set ``MSR_ROBOT_CONTROL_URL`` to the base URL of an external robot-control
REST API.  When unset, a development stub with representative robot fleet
data is used so the service can be exercised without a live connection.

The external API is expected to respond to
``GET <MSR_ROBOT_CONTROL_URL>/fleet`` with a JSON object mapping robot IDs
to robot state dictionaries.

MCP Tools provided
------------------
Read tools (always present):
- ``get_robot_fleet_status``  – summary of all robots in the fleet
- ``get_robot_status``        – detailed state for a single robot
- ``get_active_operations``   – all currently active robotic operations
- ``get_task_status``         – status of a specific task by task_id
- ``get_task_log``            – recent task history
- ``get_operational_areas``   – list of all 12 operational areas with descriptions
- ``get_data_source_info``    – robot control connectivity and configuration

Command tools:
- ``dispatch_robot_task``     – dispatch a robot to perform a named task
- ``abort_robot_task``        – abort the current task on a robot

Environment Variables
---------------------
MSR_ROBOT_CONTROL_URL   Base URL of external robot-control REST API (optional).
                        When unset, the development stub is used.
"""

import json
import os
import urllib.request
from datetime import datetime, timezone
from typing import Any

import msr_robot_state as _state

# ---------------------------------------------------------------------------
# External robot-control API helpers
# ---------------------------------------------------------------------------

def _get_fleet_from_external(base_url: str) -> dict[str, Any] | None:
    """
    Try to fetch fleet state from an external robot-control REST API.

    Returns the parsed JSON dict on success, None on any error.
    """
    url = base_url.rstrip("/") + "/fleet"
    try:
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "msr-physical-ai-layer/1.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if isinstance(data, dict):
            return data
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError,
            OSError, TimeoutError, ValueError) as exc:
        import sys
        print(
            f"[PhysicalAI] Could not fetch from MSR_ROBOT_CONTROL_URL ({exc!r}); "
            "using development stub.",
            file=sys.stderr,
        )
    return None


def _get_current_fleet() -> dict[str, Any]:
    """Return the current robot fleet state, from external API or stub."""
    external_url = os.environ.get("MSR_ROBOT_CONTROL_URL", "").strip()
    if external_url:
        data = _get_fleet_from_external(external_url)
        if data is not None:
            return data
    return _state.get_fleet_state()


# ---------------------------------------------------------------------------
# MCP tool handler functions
# ---------------------------------------------------------------------------

def get_robot_fleet_status() -> dict[str, Any]:
    """
    Return a summary of all robots in the MSR physical-AI fleet.

    Provides each robot's ID, type, operational area, status, battery level,
    and accumulated radiation dose.
    """
    fleet = _get_current_fleet()
    summary = []
    for robot_id, robot in fleet.items():
        summary.append({
            "robot_id": robot_id,
            "robot_type": robot.get("robot_type"),
            "area_id": robot.get("area_id"),
            "status": robot.get("status"),
            "battery_pct": robot.get("battery_pct"),
            "radiation_dose_accumulated_msv": robot.get("radiation_dose_accumulated_msv"),
            "location": robot.get("location"),
            "has_active_task": robot.get("current_task") is not None,
        })
    return {
        "fleet_size": len(summary),
        "robots": summary,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data_source": os.environ.get("MSR_ROBOT_CONTROL_URL", "development-stub"),
    }


def get_robot_status(robot_id: str) -> dict[str, Any]:
    """
    Return the detailed state of a single robot.

    Parameters
    ----------
    robot_id : str
        The unique identifier of the robot, e.g. ``"PLMR-01"`` or ``"RMR-01"``.
    """
    fleet = _get_current_fleet()
    robot = fleet.get(robot_id)
    if robot is None:
        available = list(fleet.keys())
        return {"error": f"Unknown robot '{robot_id}'.", "available_robots": available}
    return {
        "robot": robot,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data_source": os.environ.get("MSR_ROBOT_CONTROL_URL", "development-stub"),
    }


def get_active_operations() -> dict[str, Any]:
    """
    Return all currently active robotic operations across the fleet.

    Each entry includes the robot ID, type, location, current task details,
    and operational area.
    """
    fleet = _get_current_fleet()
    active = [
        {
            "robot_id": robot_id,
            "robot_type": robot.get("robot_type"),
            "area_id": robot.get("area_id"),
            "location": robot.get("location"),
            "current_task": robot.get("current_task"),
            "battery_pct": robot.get("battery_pct"),
        }
        for robot_id, robot in fleet.items()
        if robot.get("status") == "ACTIVE"
    ]
    return {
        "active_count": len(active),
        "operations": active,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_task_status(task_id: str) -> dict[str, Any]:
    """
    Return the status of a specific task.

    Parameters
    ----------
    task_id : str
        The task identifier returned by ``dispatch_robot_task``.
    """
    task = _state.get_task_by_id(task_id)
    if task is None:
        return {"error": f"Unknown task '{task_id}'."}
    return {"task": task, "timestamp": datetime.now(timezone.utc).isoformat()}


def get_task_log(last_n: int = 20) -> dict[str, Any]:
    """
    Return recent task history from the task log.

    Parameters
    ----------
    last_n : int
        Number of most recent task records to return (max 100).
    """
    last_n = min(max(1, last_n), 100)
    log = _state.get_task_log()
    return {
        "total_tasks": len(log),
        "returned": min(last_n, len(log)),
        "tasks": log[-last_n:],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_operational_areas() -> dict[str, Any]:
    """
    Return the list of all 12 MSR robotic operational areas in priority order.

    Each entry describes the area, the assigned robot, and the key sensors
    monitored in that area.
    """
    areas = [
        {
            "rank": area["rank"],
            "area_id": area["area_id"],
            "label": area["label"],
            "description": area["description"],
            "assigned_robot": area["robot_id"],
            "robot_type": area["robot_type"],
            "key_sensors": area["key_sensors"],
        }
        for area in _state.OPERATIONAL_AREAS
    ]
    return {"areas": areas, "total": len(areas)}


def get_data_source_info() -> dict[str, Any]:
    """
    Return information about the configured robot-control data source.

    Shows whether the service is connected to a live external robot-control
    API or using the development stub.
    """
    external_url = os.environ.get("MSR_ROBOT_CONTROL_URL", "").strip()
    info: dict[str, Any] = {
        "mode": "external" if external_url else "development-stub",
        "robot_control_url": external_url or None,
    }
    if external_url:
        url = external_url.rstrip("/") + "/fleet"
        try:
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "User-Agent": "msr-physical-ai-layer/1.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
            info["connected"] = True
            info["message"] = "External robot-control API reachable."
        except (urllib.error.URLError, urllib.error.HTTPError,
                OSError, TimeoutError) as exc:
            info["connected"] = False
            info["message"] = f"External robot-control API unreachable: {exc}"
    else:
        info["connected"] = True
        info["message"] = (
            "Using development stub data. "
            "Set MSR_ROBOT_CONTROL_URL to connect to a live robot-control API."
        )
    return info


def dispatch_robot_task(
    robot_id: str,
    task_type: str,
    description: str,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Dispatch a robot to perform a specific task.

    Creates and registers a new task in the task log and sets the robot
    status to ACTIVE.  Returns an error if the robot is unavailable.

    Parameters
    ----------
    robot_id : str
        Target robot identifier, e.g. ``"PLMR-01"``.
    task_type : str
        Type of task to perform.  Examples per operational area:

        * Primary loop:          ``"valve_replacement"``, ``"pipe_inspection"``,
                                 ``"pump_impeller_check"``
        * Hot-cell chemistry:    ``"reagent_injection"``, ``"sample_transfer"``,
                                 ``"equipment_maintenance"``
        * Salt sampling:         ``"withdraw_sample"``, ``"transport_capsule"``,
                                 ``"load_spectrometer"``
        * Radiation mapping:     ``"radiation_survey"``, ``"leak_detection"``,
                                 ``"thermal_imaging"``
        * Freeze plug:           ``"plug_thermal_inspection"``, ``"drain_tank_check"``
        * Fuel transport:        ``"salt_transfer"``, ``"valve_actuation_check"``,
                                 ``"leak_check"``
        * Graphite inspection:   ``"visual_channel_inspection"``, ``"ultrasonic_check"``,
                                 ``"graphite_replacement"``
        * Tritium management:    ``"cold_trap_maintenance"``, ``"barrier_check"``,
                                 ``"tritium_leak_detection"``
        * Off-gas:               ``"filter_replacement"``, ``"gas_sampling"``,
                                 ``"vessel_inspection"``
        * Waste salt:            ``"container_handling"``, ``"solidification_check"``,
                                 ``"storage_packaging"``
        * Structural inspection: ``"containment_inspection"``, ``"crack_survey"``,
                                 ``"drone_perimeter_scan"``
        * Security patrol:       ``"perimeter_patrol"``, ``"inventory_verification"``,
                                 ``"radiation_verification"``
    description : str
        Human-readable task description.
    parameters : dict, optional
        Task-specific parameters (e.g. target valve ID, zone coordinates).
    """
    if not robot_id or not robot_id.strip():
        return {"success": False, "error": "robot_id must not be empty."}
    if not task_type or not task_type.strip():
        return {"success": False, "error": "task_type must not be empty."}
    if not description or not description.strip():
        return {"success": False, "error": "description must not be empty."}

    result = _state.create_task(robot_id, task_type, description, parameters)
    if "error" in result:
        return {"success": False, **result}
    return {"success": True, "task": result}


def abort_robot_task(robot_id: str) -> dict[str, Any]:
    """
    Abort the current task on a robot and return it to IDLE status.

    Parameters
    ----------
    robot_id : str
        Target robot identifier.
    """
    if not robot_id or not robot_id.strip():
        return {"success": False, "error": "robot_id must not be empty."}
    return _state.abort_task(robot_id)


# ---------------------------------------------------------------------------
# MCP tool registry
# ---------------------------------------------------------------------------

TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_robot_fleet_status",
        "description": (
            "Get a summary of all robots in the MSR physical-AI fleet including "
            "their operational area, status, battery level, and radiation dose."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "handler": get_robot_fleet_status,
    },
    {
        "name": "get_robot_status",
        "description": "Get the detailed state of a single robot by its ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "robot_id": {
                    "type": "string",
                    "description": (
                        "Unique robot identifier, e.g. 'PLMR-01', 'RMR-01', 'SSR-01'."
                    ),
                }
            },
            "required": ["robot_id"],
        },
        "handler": get_robot_status,
    },
    {
        "name": "get_active_operations",
        "description": (
            "Return all currently active robotic operations across the fleet, "
            "including task details and robot locations."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "handler": get_active_operations,
    },
    {
        "name": "get_task_status",
        "description": "Return the status and details of a specific task by its task_id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Task identifier returned by dispatch_robot_task.",
                }
            },
            "required": ["task_id"],
        },
        "handler": get_task_status,
    },
    {
        "name": "get_task_log",
        "description": "Return the recent task history from the robot task log.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "last_n": {
                    "type": "integer",
                    "description": "Number of most recent task records to return (1-100).",
                    "default": 20,
                }
            },
            "required": [],
        },
        "handler": get_task_log,
    },
    {
        "name": "get_operational_areas",
        "description": (
            "Return the list of all 12 MSR robotic operational areas in priority order, "
            "with descriptions, assigned robots, and key sensors."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "handler": get_operational_areas,
    },
    {
        "name": "get_data_source_info",
        "description": (
            "Return information about the configured robot-control data source, "
            "including connectivity status and whether a live API URL is configured."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "handler": get_data_source_info,
    },
    {
        "name": "dispatch_robot_task",
        "description": (
            "Dispatch a robot to perform a specific task.  The robot must be IDLE "
            "or CHARGING (with sufficient battery). Returns the created task record."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "robot_id": {
                    "type": "string",
                    "description": "Target robot identifier, e.g. 'PLMR-01'.",
                },
                "task_type": {
                    "type": "string",
                    "description": (
                        "Task type, e.g. 'valve_replacement', 'radiation_survey', "
                        "'withdraw_sample', 'plug_thermal_inspection'."
                    ),
                },
                "description": {
                    "type": "string",
                    "description": "Human-readable description of the task.",
                },
                "parameters": {
                    "type": "object",
                    "description": "Optional task-specific parameters.",
                },
            },
            "required": ["robot_id", "task_type", "description"],
        },
        "handler": dispatch_robot_task,
    },
    {
        "name": "abort_robot_task",
        "description": (
            "Abort the current task on a robot and return it to IDLE status. "
            "Use in emergencies or when a task needs to be cancelled."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "robot_id": {
                    "type": "string",
                    "description": "Target robot identifier.",
                }
            },
            "required": ["robot_id"],
        },
        "handler": abort_robot_task,
    },
]

TOOL_MAP: dict[str, dict[str, Any]] = {t["name"]: t for t in TOOLS}


# ---------------------------------------------------------------------------
# JSON-RPC request / response helpers
# ---------------------------------------------------------------------------

def _jsonrpc_result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _jsonrpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


# ---------------------------------------------------------------------------
# MCP message dispatcher
# ---------------------------------------------------------------------------

def handle_message(raw: str) -> str:
    """
    Process a single JSON-RPC 2.0 message and return the serialised response.

    Implements the minimal MCP 2024-11 surface:
    - ``initialize``
    - ``tools/list``
    - ``tools/call``
    """
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError as exc:
        return json.dumps(_jsonrpc_error(None, -32700, f"Parse error: {exc}"))

    req_id = msg.get("id")
    method = msg.get("method", "")
    params = msg.get("params", {})

    if method == "initialize":
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "msr-physical-ai-layer", "version": "1.0.0"},
        }
        return json.dumps(_jsonrpc_result(req_id, result))

    if method == "tools/list":
        tool_list = [
            {
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["inputSchema"],
            }
            for t in TOOLS
        ]
        return json.dumps(_jsonrpc_result(req_id, {"tools": tool_list}))

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        if tool_name not in TOOL_MAP:
            return json.dumps(
                _jsonrpc_error(req_id, -32601, f"Unknown tool: '{tool_name}'")
            )
        try:
            output = TOOL_MAP[tool_name]["handler"](**arguments)
        except TypeError as exc:
            return json.dumps(_jsonrpc_error(req_id, -32602, f"Invalid params: {exc}"))
        except Exception as exc:  # noqa: BLE001
            return json.dumps(_jsonrpc_error(req_id, -32603, f"Internal error: {exc}"))
        return json.dumps(
            _jsonrpc_result(
                req_id,
                {"content": [{"type": "text", "text": json.dumps(output, indent=2)}]},
            )
        )

    # Notifications (no id) are silently ignored per MCP spec
    if req_id is None:
        return ""

    return json.dumps(_jsonrpc_error(req_id, -32601, f"Method not found: '{method}'"))
