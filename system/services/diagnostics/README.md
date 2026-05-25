# Diagnostics Service

This folder contains the shared status format for NeXa ToTem components.

It is the foundation for future LCD and web diagnostic views.

The report helper can save and read simple JSON reports under `var/reports/diagnostics/`.

Reports are only saved when a script asks for them, such as with `--save-report`.
