# System UI Scripts

This folder stores cross-screen UI foundations such as design tokens and input routing notes.

Use it for shared constants and small policies that affect multiple screens, including the fixed 640x480 layout, equal Home message split, 5-second startup timing, 4-second message preview timing, and inactivity timeout. Do not place backend code, database code, or hardware commands here.

The current app still routes through `main.gd`; these files document and stabilize the shared concepts used there.
