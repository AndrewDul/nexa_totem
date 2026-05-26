#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
PROJECT_DIR="$ROOT_DIR/system/ui/godot"
NEXA_GODOT_RENDERING_DRIVER="${NEXA_GODOT_RENDERING_DRIVER:-opengl3}"

if command -v godot4 >/dev/null 2>&1; then
	GODOT_BIN=godot4
elif command -v godot >/dev/null 2>&1; then
	GODOT_BIN=godot
else
	echo "Godot is not installed or not on PATH."
	echo "Install Godot separately, then run this script again."
	exit 0
fi

echo "Starting NeXa Godot LCD UI prototype in a fixed 640x480 window."
echo "Fullscreen LCD mode is not enabled in this sprint."
echo "Using Godot Compatibility/OpenGL renderer for Raspberry Pi stability."
exec "$GODOT_BIN" --rendering-driver "$NEXA_GODOT_RENDERING_DRIVER" --path "$PROJECT_DIR" --windowed --resolution 640x480 -- nexa_godot_lcd_ui
