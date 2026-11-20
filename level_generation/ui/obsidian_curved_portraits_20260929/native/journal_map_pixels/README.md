# Journal map pixel dimensions

Fixed on 2026-09-29 after the reported New Sorpigal map displayed water where the party stood south of town.
Compare the [reported screenshot](reference/reported.png) with the [corrected native capture](images/map-mm6.png).

`GameplayUiRuntime::hudTexturePixels` returned physical BGRA pixels with logical HUD dimensions. The journal map
compositor used those smaller dimensions for source coordinates and row stride, reading the wrong pixels from x2
assets. The getter now returns `physicalWidth` and `physicalHeight`; ordinary texture/layout dimensions remain logical.
Map transforms, exploration state, marker placement and art are unchanged.

Verification:

- Normal `openyamm` build passed.
- Focused map presentation, transform and exploration tests: **3 cases / 20 assertions**, all passed (`tests.log`).
- A temporary harness linked against the built game libraries exercised the actual pixel getter with MM6 `oute3`,
  MM7 `out09` and MM8 `out01`. All buffers match their physical dimensions while texture handles retain half-size
  logical dimensions. An unscaled dynamic texture also passed (`pixel-buffer-check.log`).
- Native MM6 desktop tour checked the default map, both zoom levels, dragging and zooming back. Captures retain the
  limited exploration of the isolated save. The default view shows the correct town and grass at the reported
  `x=-9728, y=-11319` position. Renderer: OpenGL 3.3, NVIDIA, SDL Wayland; exit code 0 (`runs/mm6.json`).

The [zoomed and panned capture](images/map-mm6-zoom-back.png) shows the terrain, exploration boundary and player marker
moving together. `tours/mm6.yml` reproduces the interaction using the existing one-member fixture. MM7/MM8 verification
here covers asset loading and buffer dimensions, not additional desktop captures.
