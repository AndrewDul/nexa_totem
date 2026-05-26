extends Node
class_name DiagnosticsApiClient

signal data_received(endpoint: String, payload: Dictionary)
signal api_offline(endpoint: String)
signal frame_received(endpoint: String, body: PackedByteArray)

const BASE_URL := "http://127.0.0.1:8769"

var request := HTTPRequest.new()
var frame_request := HTTPRequest.new()
var in_flight := false
var pending_endpoint := ""
var frame_in_flight := false
var pending_frame_endpoint := ""

func _ready() -> void:
	add_child(request)
	add_child(frame_request)
	request.request_completed.connect(_on_request_completed)
	frame_request.request_completed.connect(_on_frame_request_completed)

func request_get(endpoint: String) -> bool:
	if in_flight:
		return false
	in_flight = true
	pending_endpoint = endpoint
	var error: int = request.request(BASE_URL + endpoint)
	if error != OK:
		in_flight = false
		api_offline.emit(endpoint)
		return false
	return true

func request_frame(endpoint: String) -> bool:
	if frame_in_flight:
		return false
	frame_in_flight = true
	pending_frame_endpoint = endpoint
	var error: int = frame_request.request(BASE_URL + endpoint)
	if error != OK:
		frame_in_flight = false
		api_offline.emit(endpoint)
		return false
	return true

func request_post(endpoint: String, payload: Dictionary = {}) -> bool:
	if in_flight:
		return false
	in_flight = true
	pending_endpoint = endpoint
	var headers := ["Content-Type: application/json"]
	var body := JSON.stringify(payload)
	var error: int = request.request(BASE_URL + endpoint, headers, HTTPClient.METHOD_POST, body)
	if error != OK:
		in_flight = false
		api_offline.emit(endpoint)
		return false
	return true

func _on_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	var endpoint := pending_endpoint
	in_flight = false
	pending_endpoint = ""
	if result != HTTPRequest.RESULT_SUCCESS or response_code < 200 or response_code >= 300:
		api_offline.emit(endpoint)
		return
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		api_offline.emit(endpoint)
		return
	data_received.emit(endpoint, parsed)

func _on_frame_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	var endpoint := pending_frame_endpoint
	frame_in_flight = false
	pending_frame_endpoint = ""
	if result != HTTPRequest.RESULT_SUCCESS or response_code < 200 or response_code >= 300:
		api_offline.emit(endpoint)
		return
	frame_received.emit(endpoint, body)
