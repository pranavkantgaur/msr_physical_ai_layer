"""Unit tests for the MSR Physical AI Layer MCP Server."""

import json
import pytest
from msr_physical_ai_mcp_server import (
    handle_message,
    get_robot_fleet_status,
    get_robot_status,
    get_active_operations,
    get_task_status,
    get_task_log,
    get_operational_areas,
    get_data_source_info,
    dispatch_robot_task,
    abort_robot_task,
    TOOLS,
    TOOL_MAP,
)
import msr_robot_state as _state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _call(method, params=None, req_id=1):
    raw = json.dumps({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}})
    return json.loads(handle_message(raw))


def _reset_robot(robot_id: str) -> None:
    """Reset a robot in the stub fleet back to IDLE with no current task."""
    robot = _state._STUB_ROBOT_FLEET.get(robot_id)
    if robot:
        robot["status"] = "IDLE"
        robot["current_task"] = None


# ---------------------------------------------------------------------------
# handle_message – JSON-RPC dispatcher
# ---------------------------------------------------------------------------

class TestHandleMessage:
    def test_initialize(self):
        resp = _call("initialize")
        assert resp["result"]["protocolVersion"] == "2024-11-05"
        assert resp["result"]["serverInfo"]["name"] == "msr-physical-ai-layer"

    def test_tools_list_contains_expected_tools(self):
        resp = _call("tools/list")
        names = {t["name"] for t in resp["result"]["tools"]}
        expected = {
            "get_robot_fleet_status",
            "get_robot_status",
            "get_active_operations",
            "get_task_status",
            "get_task_log",
            "get_operational_areas",
            "get_data_source_info",
            "dispatch_robot_task",
            "abort_robot_task",
        }
        assert expected == names

    def test_tools_call_get_fleet_status(self):
        resp = _call("tools/call", {"name": "get_robot_fleet_status", "arguments": {}})
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "fleet_size" in content
        assert content["fleet_size"] == 12

    def test_tools_call_unknown_tool(self):
        resp = _call("tools/call", {"name": "nonexistent_tool", "arguments": {}})
        assert "error" in resp
        assert resp["error"]["code"] == -32601

    def test_unknown_method_returns_error(self):
        resp = _call("rpc.discover")
        assert "error" in resp
        assert resp["error"]["code"] == -32601

    def test_parse_error(self):
        resp = json.loads(handle_message("not json {{{"))
        assert "error" in resp
        assert resp["error"]["code"] == -32700

    def test_notification_returns_empty(self):
        raw = json.dumps({"jsonrpc": "2.0", "method": "some/notification", "params": {}})
        assert handle_message(raw) == ""

    def test_tools_call_missing_required_param(self):
        resp = _call("tools/call", {"name": "get_robot_status", "arguments": {}})
        assert "error" in resp
        assert resp["error"]["code"] == -32602


# ---------------------------------------------------------------------------
# get_robot_fleet_status
# ---------------------------------------------------------------------------

class TestGetRobotFleetStatus:
    def test_returns_all_12_robots(self):
        result = get_robot_fleet_status()
        assert result["fleet_size"] == 12

    def test_required_fields_per_robot(self):
        result = get_robot_fleet_status()
        for robot in result["robots"]:
            assert "robot_id" in robot
            assert "robot_type" in robot
            assert "area_id" in robot
            assert "status" in robot
            assert "battery_pct" in robot
            assert "radiation_dose_accumulated_msv" in robot

    def test_stub_data_source(self, monkeypatch):
        monkeypatch.delenv("MSR_ROBOT_CONTROL_URL", raising=False)
        result = get_robot_fleet_status()
        assert result["data_source"] == "development-stub"

    def test_has_timestamp(self):
        result = get_robot_fleet_status()
        assert "timestamp" in result


# ---------------------------------------------------------------------------
# get_robot_status
# ---------------------------------------------------------------------------

class TestGetRobotStatus:
    def test_known_robot(self):
        result = get_robot_status("PLMR-01")
        assert "robot" in result
        assert result["robot"]["robot_id"] == "PLMR-01"
        assert result["robot"]["area_id"] == "primary_loop_maintenance"

    def test_unknown_robot(self):
        result = get_robot_status("NONEXISTENT-99")
        assert "error" in result
        assert "available_robots" in result

    def test_sensors_present(self):
        result = get_robot_status("PLMR-01")
        sensors = result["robot"]["sensors"]
        assert "loop_temp_c" in sensors
        assert "neutron_dose_rate_msv_h" in sensors

    def test_all_robots_retrievable(self):
        robot_ids = [
            "PLMR-01", "HCPR-01", "SSR-01", "RMR-01", "FPMR-01",
            "FSTR-01", "GIR-01", "TMR-01", "OGSR-01", "WSHR-01",
            "SIR-01", "SPR-01",
        ]
        for rid in robot_ids:
            result = get_robot_status(rid)
            assert "robot" in result, f"Robot {rid} not retrievable"


# ---------------------------------------------------------------------------
# get_active_operations
# ---------------------------------------------------------------------------

class TestGetActiveOperations:
    def test_returns_active_count(self):
        result = get_active_operations()
        assert "active_count" in result
        assert isinstance(result["active_count"], int)

    def test_active_count_matches_operations_list(self):
        result = get_active_operations()
        assert result["active_count"] == len(result["operations"])

    def test_stub_has_known_active_robots(self):
        """RMR-01, FPMR-01, and SPR-01 start ACTIVE in the stub."""
        result = get_active_operations()
        active_ids = {op["robot_id"] for op in result["operations"]}
        assert "RMR-01" in active_ids
        assert "FPMR-01" in active_ids
        assert "SPR-01" in active_ids

    def test_operations_have_task_details(self):
        result = get_active_operations()
        for op in result["operations"]:
            assert "robot_id" in op
            assert "current_task" in op
            assert op["current_task"] is not None


# ---------------------------------------------------------------------------
# dispatch_robot_task / abort_robot_task
# ---------------------------------------------------------------------------

class TestDispatchAndAbortTask:
    def setup_method(self):
        _reset_robot("PLMR-01")
        _reset_robot("FSTR-01")
        _reset_robot("TMR-01")

    def teardown_method(self):
        _reset_robot("PLMR-01")
        _reset_robot("FSTR-01")
        _reset_robot("TMR-01")

    def test_dispatch_to_idle_robot(self):
        result = dispatch_robot_task(
            robot_id="PLMR-01",
            task_type="valve_replacement",
            description="Replace primary loop inlet valve V-101",
        )
        assert result["success"] is True
        assert "task" in result
        assert result["task"]["robot_id"] == "PLMR-01"
        assert result["task"]["task_type"] == "valve_replacement"

    def test_dispatched_robot_becomes_active(self):
        dispatch_robot_task(
            robot_id="FSTR-01",
            task_type="salt_transfer",
            description="Transfer fresh FLiBe batch to primary loop",
        )
        status = get_robot_status("FSTR-01")
        assert status["robot"]["status"] == "ACTIVE"

    def test_dispatch_to_already_active_robot_fails(self):
        dispatch_robot_task(
            robot_id="TMR-01",
            task_type="cold_trap_maintenance",
            description="Inspect cold trap T-201",
        )
        result = dispatch_robot_task(
            robot_id="TMR-01",
            task_type="barrier_check",
            description="Check permeation barrier B-101",
        )
        assert result["success"] is False
        assert "already ACTIVE" in result["error"]

    def test_dispatch_unknown_robot_fails(self):
        result = dispatch_robot_task(
            robot_id="UNKNOWN-99",
            task_type="inspection",
            description="Test task",
        )
        assert result["success"] is False
        assert "Unknown robot" in result["error"]

    def test_dispatch_empty_robot_id_fails(self):
        result = dispatch_robot_task(
            robot_id="",
            task_type="inspection",
            description="Test task",
        )
        assert result["success"] is False

    def test_dispatch_empty_task_type_fails(self):
        result = dispatch_robot_task(
            robot_id="PLMR-01",
            task_type="",
            description="Test task",
        )
        assert result["success"] is False

    def test_dispatch_empty_description_fails(self):
        result = dispatch_robot_task(
            robot_id="PLMR-01",
            task_type="valve_replacement",
            description="",
        )
        assert result["success"] is False

    def test_dispatch_with_parameters(self):
        result = dispatch_robot_task(
            robot_id="SSR-01",
            task_type="withdraw_sample",
            description="Withdraw fuel salt sample from port 2",
            parameters={"port_id": "SP-02", "volume_ml": 5.0},
        )
        assert result["success"] is True
        assert result["task"]["parameters"]["port_id"] == "SP-02"

    def test_abort_active_task(self):
        dispatch_robot_task(
            robot_id="PLMR-01",
            task_type="pipe_inspection",
            description="Inspect primary loop bypass pipe",
        )
        result = abort_robot_task("PLMR-01")
        assert result["success"] is True
        assert "aborted_task_id" in result

    def test_abort_returns_robot_to_idle(self):
        dispatch_robot_task(
            robot_id="FSTR-01",
            task_type="valve_actuation_check",
            description="Verify valve actuator on V-302",
        )
        abort_robot_task("FSTR-01")
        status = get_robot_status("FSTR-01")
        assert status["robot"]["status"] == "IDLE"

    def test_abort_idle_robot_fails(self):
        result = abort_robot_task("PLMR-01")
        assert result["success"] is False
        assert "no active task" in result["error"].lower()

    def test_abort_unknown_robot_fails(self):
        result = abort_robot_task("UNKNOWN-99")
        assert result["success"] is False
        assert "Unknown robot" in result["error"]

    def test_abort_empty_robot_id_fails(self):
        result = abort_robot_task("")
        assert result["success"] is False


# ---------------------------------------------------------------------------
# get_task_status / get_task_log
# ---------------------------------------------------------------------------

class TestTaskLog:
    def setup_method(self):
        _reset_robot("WSHR-01")

    def teardown_method(self):
        _reset_robot("WSHR-01")

    def test_task_status_after_dispatch(self):
        dispatch_result = dispatch_robot_task(
            robot_id="WSHR-01",
            task_type="container_handling",
            description="Move radioactive salt container C-05 to storage",
        )
        task_id = dispatch_result["task"]["task_id"]
        status = get_task_status(task_id)
        assert "task" in status
        assert status["task"]["task_id"] == task_id
        assert status["task"]["status"] == "ACTIVE"

    def test_task_status_unknown_id(self):
        result = get_task_status("TASK-NONEXISTENT-9999")
        assert "error" in result

    def test_task_log_returns_list(self):
        result = get_task_log()
        assert "tasks" in result
        assert isinstance(result["tasks"], list)

    def test_task_log_last_n_respected(self):
        result = get_task_log(last_n=3)
        assert len(result["tasks"]) <= 3

    def test_task_log_last_n_clamped_to_100(self):
        result = get_task_log(last_n=9999)
        assert result["returned"] <= 100

    def test_aborted_task_reflected_in_log(self):
        dispatch_result = dispatch_robot_task(
            robot_id="WSHR-01",
            task_type="solidification_check",
            description="Verify solidification of waste batch WB-12",
        )
        task_id = dispatch_result["task"]["task_id"]
        abort_robot_task("WSHR-01")
        status = get_task_status(task_id)
        assert status["task"]["status"] == "ABORTED"
        assert status["task"]["completed_at"] is not None


# ---------------------------------------------------------------------------
# get_operational_areas
# ---------------------------------------------------------------------------

class TestGetOperationalAreas:
    def test_returns_12_areas(self):
        result = get_operational_areas()
        assert result["total"] == 12
        assert len(result["areas"]) == 12

    def test_areas_sorted_by_rank(self):
        result = get_operational_areas()
        ranks = [a["rank"] for a in result["areas"]]
        assert ranks == sorted(ranks)

    def test_all_areas_have_required_fields(self):
        result = get_operational_areas()
        for area in result["areas"]:
            assert "rank" in area
            assert "area_id" in area
            assert "label" in area
            assert "description" in area
            assert "assigned_robot" in area
            assert "robot_type" in area
            assert "key_sensors" in area

    def test_highest_priority_area_is_primary_loop(self):
        result = get_operational_areas()
        top = result["areas"][0]
        assert top["rank"] == 1
        assert top["area_id"] == "primary_loop_maintenance"

    def test_lowest_priority_area_is_security(self):
        result = get_operational_areas()
        bottom = result["areas"][-1]
        assert bottom["rank"] == 12
        assert bottom["area_id"] == "security_safeguards"


# ---------------------------------------------------------------------------
# get_data_source_info
# ---------------------------------------------------------------------------

class TestGetDataSourceInfo:
    def test_stub_mode(self, monkeypatch):
        monkeypatch.delenv("MSR_ROBOT_CONTROL_URL", raising=False)
        info = get_data_source_info()
        assert info["mode"] == "development-stub"
        assert info["robot_control_url"] is None
        assert info["connected"] is True
        assert "development stub" in info["message"].lower()

    def test_external_url_unreachable(self, monkeypatch):
        monkeypatch.setenv("MSR_ROBOT_CONTROL_URL", "http://127.0.0.1:19998/robot")
        info = get_data_source_info()
        assert info["mode"] == "external"
        assert info["connected"] is False
        assert "unreachable" in info["message"].lower()

    def test_external_url_reachable(self, monkeypatch):
        from unittest.mock import MagicMock, patch
        monkeypatch.setenv("MSR_ROBOT_CONTROL_URL", "http://mock-robot.example.com")
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read.return_value = b'{"PLMR-01": {}}'
        with patch("urllib.request.urlopen", return_value=mock_resp):
            info = get_data_source_info()
        assert info["mode"] == "external"
        assert info["connected"] is True


# ---------------------------------------------------------------------------
# Tool registry consistency
# ---------------------------------------------------------------------------

class TestToolRegistry:
    def test_all_tools_have_callable_handler(self):
        for tool in TOOLS:
            assert callable(tool["handler"]), f"Tool '{tool['name']}' has no callable handler"

    def test_tool_map_matches_tools_list(self):
        assert set(TOOL_MAP.keys()) == {t["name"] for t in TOOLS}

    def test_all_tools_have_input_schema(self):
        for tool in TOOLS:
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"
