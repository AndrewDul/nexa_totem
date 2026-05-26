# Troubleshooting

## Godot Drawing Helper Runtime Errors

Godot helper calls failed because drawing helpers were not callable at runtime from the theme script.

Fixed by using local callable drawing helpers in `main.gd`.

`Rect2.translated()` was not available in this Godot runtime.

Use `Rect2(rect.position + offset, rect.size)` instead.

Repeated script errors can cause visible lag, so runtime logs must be clean before judging performance.
