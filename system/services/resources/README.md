# Resource Service

This folder contains the first NeXa resource monitoring foundation.

It monitors NeXa-owned processes only. It does not show the whole Linux process table in user-facing reports.

The process registry lists planned and current NeXa components such as the backend, Godot LCD UI, web panel, camera service, sensor service, remote link, diagnostics runner, and test runner.

The process monitor reads quick CPU and RAM snapshots from `/proc` when Linux provides it. The reports are prepared for the future diagnostic panel.

GPU usage percent may be unavailable on Raspberry Pi. Godot GPU usage is reported as unknown unless there is a reliable measurement source.

Godot can later provide FPS and frame timing from its own runtime. Until then, those values stay empty instead of being guessed.

