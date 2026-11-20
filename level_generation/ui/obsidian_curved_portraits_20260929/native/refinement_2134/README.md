# 2134 — larger selection diamond

Applied the user's final scope correction: enlarge only the active-character diamond. Portrait size and HP/mana
arc widths are unchanged. All five gameplay `Selection` elements now measure 20 × 20 logical pixels (previously 16),
a 25% increase, centred above the portrait at x=39. Their y offset is -5.5 so the larger symbol clears the basebar.
Fullscreen overlay diamonds keep their prior layout.

[First character selected](images/diamond-first.png) · [Fourth character selected](images/diamond-fourth.png)

The existing layout-clearance test passed: one case, 711 assertions, covering all 1–5 party widths. A native desktop
run at 1600×900 checked visibility, border clearance and click selection. It used OpenGL 3.3 on NVIDIA via SDL Wayland
and exited successfully. Only YAML geometry changed; the existing development executable loads it without rebuilding.
The YAML comparison confirmed that only the size/position fields of the five selection diamonds changed.

`validation.json`, `runs/wide.json`, `tours/wide.yml` and `tests.log` retain the verification record.
