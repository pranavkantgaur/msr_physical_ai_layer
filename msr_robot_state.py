"""
MSR Physical AI Layer – Robot Fleet State Management

Defines the robot platforms, operational areas, and stub state used by the
MSR physical-AI MCP server when no external robot-control system is configured.

The 12 operational areas (in priority order) are:

  1.  Primary loop maintenance         (PLMR – Primary Loop Maintenance Robot)
  2.  Hot-cell chemical processing     (HCPR – Hot-Cell Processing Robot)
  3.  Salt sampling & analysis         (SSR  – Salt Sampling Robot)
  4.  Radiation mapping & inspection   (RMR  – Radiation Mapping Robot)
  5.  Freeze plug safety monitoring    (FPMR – Freeze Plug Monitor Robot)
  6.  Fuel salt transport & refilling  (FSTR – Fuel Salt Transport Robot)
  7.  Graphite moderator inspection    (GIR  – Graphite Inspection Robot)
  8.  Tritium management systems       (TMR  – Tritium Management Robot)
  9.  Off-gas system handling          (OGSR – Off-Gas System Robot)
  10. Waste salt handling              (WSHR – Waste Salt Handling Robot)
  11. External structural inspection   (SIR  – Structural Inspection Robot)
  12. Security & safeguards monitoring (SPR  – Security Patrol Robot)

Each robot has:
  - A unique robot_id
  - An operational area label
  - A status (IDLE | ACTIVE | FAULT | OFFLINE | CHARGING)
  - A battery_pct
  - A radiation_dose_msv (accumulated dose in mSv)
  - A current_task (None or task dict)
  - A location string
  - Sensor readings relevant to its area
"""

from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Operational area registry
# ---------------------------------------------------------------------------

OPERATIONAL_AREAS: list[dict[str, Any]] = [
    {
        "area_id": "primary_loop_maintenance",
        "rank": 1,
        "label": "Primary Loop Maintenance",
        "description": (
            "Bolt removal, valve replacement, pipe cutting/welding, pump-impeller "
            "inspection, and heat-exchanger tube replacement in the high-radiation "
            "primary salt loop."
        ),
        "robot_id": "PLMR-01",
        "robot_type": "Primary Loop Maintenance Robot",
        "key_sensors": ["loop_temp_c", "loop_pressure_bar", "neutron_dose_rate_msv_h",
                        "pump_vibration_mm_s"],
    },
    {
        "area_id": "hot_cell_chemical_processing",
        "rank": 2,
        "label": "Hot-Cell Chemical Processing",
        "description": (
            "Sample transfer, reagent injection, salt batch transfer, and equipment "
            "maintenance inside shielded chemical hot cells for online fuel-salt "
            "chemistry control."
        ),
        "robot_id": "HCPR-01",
        "robot_type": "Hot-Cell Processing Robot",
        "key_sensors": ["redox_potential_mv", "noble_metal_ppm", "tritium_activity_bq_m3",
                        "cell_gamma_dose_rate_msv_h"],
    },
    {
        "area_id": "salt_sampling_analysis",
        "rank": 3,
        "label": "Salt Sampling & Analysis",
        "description": (
            "Withdraw molten-salt samples, transport capsules, and load spectrometry "
            "instruments to measure fissile concentration, corrosion products, fission "
            "products, and redox chemistry."
        ),
        "robot_id": "SSR-01",
        "robot_type": "Salt Sampling Robot",
        "key_sensors": ["sample_temp_c", "fissile_conc_g_l", "corrosion_product_ppm",
                        "sample_gamma_dose_rate_msv_h"],
    },
    {
        "area_id": "radiation_mapping_inspection",
        "rank": 4,
        "label": "Radiation Mapping & Inspection",
        "description": (
            "Continuous radiation mapping, neutron flux monitoring, leak detection, "
            "and pipe surface inspection using gamma spectrometers, neutron detectors, "
            "and thermal cameras."
        ),
        "robot_id": "RMR-01",
        "robot_type": "Radiation Mapping Robot",
        "key_sensors": ["gamma_dose_rate_msv_h", "neutron_flux_n_cm2_s",
                        "surface_temp_c", "leakage_indicator"],
    },
    {
        "area_id": "freeze_plug_monitoring",
        "rank": 5,
        "label": "Freeze Plug Safety Monitoring",
        "description": (
            "Thermal inspection of the freeze plug, drain tank monitoring, and "
            "emergency post-drain inspection to verify passive-safety system readiness."
        ),
        "robot_id": "FPMR-01",
        "robot_type": "Freeze Plug Monitor Robot",
        "key_sensors": ["plug_temp_c", "drain_tank_level_pct", "plug_integrity_ok",
                        "coolant_flow_l_min"],
    },
    {
        "area_id": "fuel_salt_transport",
        "rank": 6,
        "label": "Fuel Salt Transport & Refilling",
        "description": (
            "Handling heated transfer lines, monitoring valve actuation, autonomous "
            "procedure execution for filling fresh salt, transferring salt between "
            "loops, and draining for maintenance."
        ),
        "robot_id": "FSTR-01",
        "robot_type": "Fuel Salt Transport Robot",
        "key_sensors": ["transfer_line_temp_c", "salt_flow_kg_min", "valve_position_pct",
                        "leak_detection_ok"],
    },
    {
        "area_id": "graphite_moderator_inspection",
        "rank": 7,
        "label": "Graphite Moderator Inspection",
        "description": (
            "Visual inspection inside core channels, ultrasonic integrity checks, and "
            "replacement operations for graphite moderator elements experiencing "
            "neutron damage, swelling, and cracking."
        ),
        "robot_id": "GIR-01",
        "robot_type": "Graphite Inspection Robot",
        "key_sensors": ["graphite_surface_temp_c", "crack_count", "swelling_mm",
                        "channel_dose_rate_msv_h"],
    },
    {
        "area_id": "tritium_management",
        "rank": 8,
        "label": "Tritium Management Systems",
        "description": (
            "Maintenance of tritium capture modules (permeation barriers, cold traps, "
            "gas stripping), sensor replacement, and leak detection."
        ),
        "robot_id": "TMR-01",
        "robot_type": "Tritium Management Robot",
        "key_sensors": ["tritium_conc_bq_m3", "cold_trap_temp_c", "permeation_barrier_ok",
                        "tritium_dose_rate_msv_h"],
    },
    {
        "area_id": "off_gas_system",
        "rank": 9,
        "label": "Off-Gas System Handling",
        "description": (
            "Filter replacement, gas sampling, and pressure vessel inspection for "
            "the off-gas system that captures fission-product gases (xenon, krypton)."
        ),
        "robot_id": "OGSR-01",
        "robot_type": "Off-Gas System Robot",
        "key_sensors": ["xenon_activity_bq_m3", "krypton_activity_bq_m3",
                        "filter_dp_bar", "vessel_pressure_bar"],
    },
    {
        "area_id": "waste_salt_handling",
        "rank": 10,
        "label": "Waste Salt Handling & Solidification",
        "description": (
            "Handling radioactive salt containers, controlling solidification processes, "
            "and packaging for storage of contaminated salt and chemical waste streams."
        ),
        "robot_id": "WSHR-01",
        "robot_type": "Waste Salt Handling Robot",
        "key_sensors": ["container_temp_c", "container_dose_rate_msv_h",
                        "solidification_pct", "storage_capacity_pct"],
    },
    {
        "area_id": "structural_inspection",
        "rank": 11,
        "label": "External Structural Inspection",
        "description": (
            "Drone and mobile robot inspection of containment, cooling towers, and "
            "structural integrity checks in lower-radiation external areas."
        ),
        "robot_id": "SIR-01",
        "robot_type": "Structural Inspection Robot",
        "key_sensors": ["structure_surface_temp_c", "crack_width_mm",
                        "vibration_mm_s", "ambient_dose_rate_msv_h"],
    },
    {
        "area_id": "security_safeguards",
        "rank": 12,
        "label": "Security & Safeguards Monitoring",
        "description": (
            "Facility patrol for radiation verification and nuclear material inventory "
            "tracking to support safeguards obligations."
        ),
        "robot_id": "SPR-01",
        "robot_type": "Security Patrol Robot",
        "key_sensors": ["patrol_zone", "area_dose_rate_msv_h",
                        "material_inventory_ok", "intrusion_detected"],
    },
]

# Quick lookup by area_id
AREA_MAP: dict[str, dict[str, Any]] = {a["area_id"]: a for a in OPERATIONAL_AREAS}

# ---------------------------------------------------------------------------
# Stub robot fleet state
# (used when MSR_ROBOT_CONTROL_URL is not configured)
# ---------------------------------------------------------------------------

_STUB_ROBOT_FLEET: dict[str, dict[str, Any]] = {
    "PLMR-01": {
        "robot_id": "PLMR-01",
        "robot_type": "Primary Loop Maintenance Robot",
        "area_id": "primary_loop_maintenance",
        "status": "IDLE",
        "battery_pct": 92.0,
        "radiation_dose_accumulated_msv": 4.2,
        "location": "maintenance_bay_1",
        "current_task": None,
        "sensors": {
            "loop_temp_c": 695.0,
            "loop_pressure_bar": 1.1,
            "neutron_dose_rate_msv_h": 12.5,
            "pump_vibration_mm_s": 0.8,
        },
    },
    "HCPR-01": {
        "robot_id": "HCPR-01",
        "robot_type": "Hot-Cell Processing Robot",
        "area_id": "hot_cell_chemical_processing",
        "status": "IDLE",
        "battery_pct": 78.5,
        "radiation_dose_accumulated_msv": 8.1,
        "location": "hot_cell_A",
        "current_task": None,
        "sensors": {
            "redox_potential_mv": -350.0,
            "noble_metal_ppm": 0.05,
            "tritium_activity_bq_m3": 1.2e6,
            "cell_gamma_dose_rate_msv_h": 25.0,
        },
    },
    "SSR-01": {
        "robot_id": "SSR-01",
        "robot_type": "Salt Sampling Robot",
        "area_id": "salt_sampling_analysis",
        "status": "IDLE",
        "battery_pct": 85.0,
        "radiation_dose_accumulated_msv": 3.6,
        "location": "sampling_port_2",
        "current_task": None,
        "sensors": {
            "sample_temp_c": 650.0,
            "fissile_conc_g_l": 2.8,
            "corrosion_product_ppm": 12.4,
            "sample_gamma_dose_rate_msv_h": 18.0,
        },
    },
    "RMR-01": {
        "robot_id": "RMR-01",
        "robot_type": "Radiation Mapping Robot",
        "area_id": "radiation_mapping_inspection",
        "status": "ACTIVE",
        "battery_pct": 61.0,
        "radiation_dose_accumulated_msv": 6.7,
        "location": "primary_loop_corridor",
        "current_task": {
            "task_id": "TASK-RMR-0001",
            "task_type": "radiation_survey",
            "description": "Routine radiation survey of primary loop corridor",
            "started_at": "2026-03-16T08:00:00Z",
            "progress_pct": 45,
        },
        "sensors": {
            "gamma_dose_rate_msv_h": 8.3,
            "neutron_flux_n_cm2_s": 1.4e12,
            "surface_temp_c": 45.0,
            "leakage_indicator": False,
        },
    },
    "FPMR-01": {
        "robot_id": "FPMR-01",
        "robot_type": "Freeze Plug Monitor Robot",
        "area_id": "freeze_plug_monitoring",
        "status": "ACTIVE",
        "battery_pct": 95.0,
        "radiation_dose_accumulated_msv": 1.1,
        "location": "freeze_plug_station",
        "current_task": {
            "task_id": "TASK-FPMR-0001",
            "task_type": "continuous_monitoring",
            "description": "Continuous thermal monitoring of freeze plug",
            "started_at": "2026-03-16T00:00:00Z",
            "progress_pct": None,
        },
        "sensors": {
            "plug_temp_c": 395.0,
            "drain_tank_level_pct": 0.0,
            "plug_integrity_ok": True,
            "coolant_flow_l_min": 12.5,
        },
    },
    "FSTR-01": {
        "robot_id": "FSTR-01",
        "robot_type": "Fuel Salt Transport Robot",
        "area_id": "fuel_salt_transport",
        "status": "IDLE",
        "battery_pct": 88.0,
        "radiation_dose_accumulated_msv": 2.9,
        "location": "salt_storage_bay",
        "current_task": None,
        "sensors": {
            "transfer_line_temp_c": 580.0,
            "salt_flow_kg_min": 0.0,
            "valve_position_pct": 0.0,
            "leak_detection_ok": True,
        },
    },
    "GIR-01": {
        "robot_id": "GIR-01",
        "robot_type": "Graphite Inspection Robot",
        "area_id": "graphite_moderator_inspection",
        "status": "CHARGING",
        "battery_pct": 35.0,
        "radiation_dose_accumulated_msv": 15.3,
        "location": "charging_station_B",
        "current_task": None,
        "sensors": {
            "graphite_surface_temp_c": 620.0,
            "crack_count": 0,
            "swelling_mm": 0.12,
            "channel_dose_rate_msv_h": 32.0,
        },
    },
    "TMR-01": {
        "robot_id": "TMR-01",
        "robot_type": "Tritium Management Robot",
        "area_id": "tritium_management",
        "status": "IDLE",
        "battery_pct": 74.0,
        "radiation_dose_accumulated_msv": 5.5,
        "location": "tritium_capture_bay",
        "current_task": None,
        "sensors": {
            "tritium_conc_bq_m3": 8.5e4,
            "cold_trap_temp_c": -196.0,
            "permeation_barrier_ok": True,
            "tritium_dose_rate_msv_h": 0.4,
        },
    },
    "OGSR-01": {
        "robot_id": "OGSR-01",
        "robot_type": "Off-Gas System Robot",
        "area_id": "off_gas_system",
        "status": "IDLE",
        "battery_pct": 82.0,
        "radiation_dose_accumulated_msv": 7.2,
        "location": "off_gas_building",
        "current_task": None,
        "sensors": {
            "xenon_activity_bq_m3": 2.1e7,
            "krypton_activity_bq_m3": 4.5e6,
            "filter_dp_bar": 0.08,
            "vessel_pressure_bar": 0.5,
        },
    },
    "WSHR-01": {
        "robot_id": "WSHR-01",
        "robot_type": "Waste Salt Handling Robot",
        "area_id": "waste_salt_handling",
        "status": "IDLE",
        "battery_pct": 91.0,
        "radiation_dose_accumulated_msv": 11.8,
        "location": "waste_storage_cell",
        "current_task": None,
        "sensors": {
            "container_temp_c": 55.0,
            "container_dose_rate_msv_h": 42.0,
            "solidification_pct": 100.0,
            "storage_capacity_pct": 28.0,
        },
    },
    "SIR-01": {
        "robot_id": "SIR-01",
        "robot_type": "Structural Inspection Robot",
        "area_id": "structural_inspection",
        "status": "IDLE",
        "battery_pct": 97.0,
        "radiation_dose_accumulated_msv": 0.3,
        "location": "containment_exterior",
        "current_task": None,
        "sensors": {
            "structure_surface_temp_c": 22.0,
            "crack_width_mm": 0.0,
            "vibration_mm_s": 0.1,
            "ambient_dose_rate_msv_h": 0.05,
        },
    },
    "SPR-01": {
        "robot_id": "SPR-01",
        "robot_type": "Security Patrol Robot",
        "area_id": "security_safeguards",
        "status": "ACTIVE",
        "battery_pct": 68.0,
        "radiation_dose_accumulated_msv": 0.8,
        "location": "perimeter_zone_3",
        "current_task": {
            "task_id": "TASK-SPR-0001",
            "task_type": "perimeter_patrol",
            "description": "Scheduled perimeter patrol – zone 3",
            "started_at": "2026-03-16T11:00:00Z",
            "progress_pct": 60,
        },
        "sensors": {
            "patrol_zone": "zone_3",
            "area_dose_rate_msv_h": 0.05,
            "material_inventory_ok": True,
            "intrusion_detected": False,
        },
    },
}

# Task log (in-memory, writable at runtime)
_TASK_LOG: list[dict[str, Any]] = []

# Task ID counter
_task_counter: int = 100


# ---------------------------------------------------------------------------
# State accessors used by the MCP server
# ---------------------------------------------------------------------------

def get_fleet_state() -> dict[str, dict[str, Any]]:
    """Return a copy of the current robot fleet state."""
    import copy
    return copy.deepcopy(_STUB_ROBOT_FLEET)


def get_robot(robot_id: str) -> dict[str, Any] | None:
    """Return state for a single robot, or None if not found."""
    robot = _STUB_ROBOT_FLEET.get(robot_id)
    if robot is None:
        return None
    import copy
    return copy.deepcopy(robot)


def get_task_log() -> list[dict[str, Any]]:
    """Return the current in-memory task log."""
    import copy
    return copy.deepcopy(_TASK_LOG)


def create_task(
    robot_id: str,
    task_type: str,
    description: str,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create and register a new robotic task.

    Sets the robot status to ACTIVE and records the task in the task log.
    Returns the created task dict, or an error dict if the robot is unknown
    or already busy.
    """
    global _task_counter  # noqa: PLW0603

    robot = _STUB_ROBOT_FLEET.get(robot_id)
    if robot is None:
        return {"error": f"Unknown robot '{robot_id}'."}

    if robot["status"] == "FAULT":
        return {"error": f"Robot '{robot_id}' is in FAULT state and cannot accept tasks."}
    if robot["status"] == "OFFLINE":
        return {"error": f"Robot '{robot_id}' is OFFLINE."}
    if robot["status"] == "CHARGING" and robot["battery_pct"] < 20.0:
        return {"error": f"Robot '{robot_id}' is charging with low battery ({robot['battery_pct']:.0f}%)."}
    if robot["status"] == "ACTIVE":
        return {
            "error": (
                f"Robot '{robot_id}' is already ACTIVE on task "
                f"'{robot['current_task']['task_id']}'."
            )
        }

    _task_counter += 1
    task_id = f"TASK-{robot_id}-{_task_counter:04d}"
    now = datetime.now(timezone.utc).isoformat()
    task: dict[str, Any] = {
        "task_id": task_id,
        "robot_id": robot_id,
        "task_type": task_type,
        "description": description,
        "parameters": parameters or {},
        "status": "ACTIVE",
        "started_at": now,
        "completed_at": None,
        "progress_pct": 0,
        "result": None,
    }
    robot["status"] = "ACTIVE"
    robot["current_task"] = {
        "task_id": task_id,
        "task_type": task_type,
        "description": description,
        "started_at": now,
        "progress_pct": 0,
    }
    _TASK_LOG.append(task)
    return task


def abort_task(robot_id: str) -> dict[str, Any]:
    """
    Abort the current task on a robot and set it back to IDLE.

    Returns a result dict with ``success`` and ``aborted_task_id`` fields.
    """
    robot = _STUB_ROBOT_FLEET.get(robot_id)
    if robot is None:
        return {"success": False, "error": f"Unknown robot '{robot_id}'."}

    if robot["status"] != "ACTIVE" or robot["current_task"] is None:
        return {"success": False, "error": f"Robot '{robot_id}' has no active task to abort."}

    task_id = robot["current_task"]["task_id"]
    now = datetime.now(timezone.utc).isoformat()

    # Update task log entry
    for task in _TASK_LOG:
        if task["task_id"] == task_id:
            task["status"] = "ABORTED"
            task["completed_at"] = now
            break

    robot["status"] = "IDLE"
    robot["current_task"] = None
    return {"success": True, "aborted_task_id": task_id, "timestamp": now}


def get_task_by_id(task_id: str) -> dict[str, Any] | None:
    """Return the task log entry for a given task_id, or None."""
    for task in _TASK_LOG:
        if task["task_id"] == task_id:
            import copy
            return copy.deepcopy(task)
    return None
