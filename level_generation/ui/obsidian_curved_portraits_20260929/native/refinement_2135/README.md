# 2135 — larger, lower gameplay status text

The user requested slightly larger event/status text closer to the basebar, referencing `test_img/2135.png`.

`OutdoorGameplayStatusBar` now uses Lucida scale 0.75 instead of 0.65 (about 15% larger). It is attached directly
above `OutdoorGameplayBasebar` with a six-logical-pixel gap, replacing the previous 24-pixel gap. The shared renderer
retains the resolved bottom edge while sizing the message, so longer content grows upward. Event messages and hover
hints use this same panel. The separate fullscreen status/input rail keeps its existing layout and font size.

The enlarged selection diamond from 2134 is retained. Portrait size, HP/mana widths, basebar and ornaments are unchanged.

Native screenshots: [short message](images/status-short-wide.png), [longer message](images/status-longer-wide.png),
[4:3](images/status-longer-4by3.png). These exercise actual turn-mode and rest-denial events in isolated saves.

The normal development build passed. Existing focused layout/HUD tests passed: six cases, 807 assertions.
Native 1600×900 and 1280×960 checks used OpenGL 3.3 on NVIDIA via SDL Wayland. Both runs exited successfully.
See `validation.json`, `runs/`, `tours/`, `build.log` and `tests.log` for the retained record.
