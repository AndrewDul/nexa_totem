This folder is reserved for Godot-side hardware bridge helpers.

The current hardware polling is still in `scripts/main.gd` because the app router and API callbacks live there. Keep shared helper scripts here only when they are small and useful across screens.

Do not put Wi-Fi setup, network commands, logs, config files, or secrets in this folder.
