extends RefCounted
class_name DiagnosticsData

# Later this will read from a Python backend API or saved JSON reports.
# The UI must not run hardware checks directly.

const REPORT_TYPES := [
	"system_status",
	"pi_health",
	"audio_output",
	"camera_status",
	"camera_capture",
	"unit_tests",
	"nexa_resources",
	"resource_benchmark"
]

func load_panel_data() -> Dictionary:
	var reports := {}
	for report_type in REPORT_TYPES:
		reports[report_type] = _load_latest_report(report_type)
	return {
		"status": _status_from_reports(reports),
		"message": "Latest saved reports are shown when available.",
		"latest_reports": reports,
		"source": "godot_diagnostics_data"
	}

func _load_latest_report(report_type: String) -> Dictionary:
	var path := "res://data/" + report_type + "_latest.json"
	if FileAccess.file_exists(path):
		var text := FileAccess.get_file_as_string(path)
		var parsed = JSON.parse_string(text)
		if typeof(parsed) == TYPE_DICTIONARY:
			parsed["view_label"] = "Latest saved report"
			return parsed
	return {
		"report": report_type,
		"status": "not_checked",
		"message": "No report saved yet.",
		"view_label": "No report saved yet."
	}

func _status_from_reports(reports: Dictionary) -> String:
	for report in reports.values():
		if report.get("status", "not_checked") in ["ok", "warning", "missing", "error"]:
			return "ok"
	return "not_checked"

func sample_process_rows() -> Array:
	return [
		{"name": "Python backend", "status": "not running", "cpu": "0.0", "ram": "0.0"},
		{"name": "Godot LCD UI", "status": "prototype", "cpu": "--", "ram": "--"},
		{"name": "Web panel", "status": "planned", "cpu": "0.0", "ram": "0.0"},
		{"name": "Camera service", "status": "not checked", "cpu": "0.0", "ram": "0.0"},
		{"name": "Sensor service", "status": "planned", "cpu": "0.0", "ram": "0.0"},
		{"name": "Remote link", "status": "planned", "cpu": "0.0", "ram": "0.0"},
		{"name": "Diagnostics runner", "status": "not checked", "cpu": "0.0", "ram": "0.0"}
	]
