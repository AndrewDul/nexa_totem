# Home Behaviors

This folder describes face behavior presets such as startup greetings, idle blinking, focused states, warning states, LED placeholders, and sound cue placeholders.

Add lightweight behavior definitions here. Do not add hardware control, audio playback, or per-frame logging in this folder.

`main.gd` applies a small runtime subset of these behavior names while keeping the existing custom drawing pipeline. Startup animation timing stays in Home runtime code; behavior files only describe reusable expression and cue names.
