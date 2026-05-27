# Home Scripts

This folder holds Home-specific UI foundations for the NeXa face, Home startup sequence, Home Message Mode, and future Home communication features.

Put small Home helpers and documentation here. Do not move the whole LCD app or unrelated screens into this folder yet.

`main.gd` remains the current router. It bridges to these concepts while the Home system is introduced gradually, including the current 5-second NeXa ToTem DevDul startup animation, personalized startup greeting, and the face-LEFT/text-RIGHT Home message layout.

**Home Message Mode layout (face-left/text-right):**
- Face sits on the LEFT side: message-mode center x=160, scale 0.52. Idle center x=320, scale 0.86.
- Text sits on the RIGHT side: x=342, width=264 (x=342..606).
- On enter: text slides from y=-180 to 0 while fading in; face lerps from idle center (320, 245) to message center (160, 245).
- On exit: text slides back to y=-180 while fading out; face lerps back to idle center.
- Close X sits at Rect2(584, 58, 26, 26) — top-right of the text area.
- Action buttons start at x=342, bottom of the text area.
- Auto-dismiss timer counts only while the message is fully visible (4 seconds), not during enter or exit animation.
- Messages Center rows support swipe-to-dismiss: left or right 60px swipe removes the row (abs(dx)>abs(dy) guard).
- Face animates offscreen during screen transitions (left for Menu, right for Clock, down for Control Center, up for Quick Shelf).
