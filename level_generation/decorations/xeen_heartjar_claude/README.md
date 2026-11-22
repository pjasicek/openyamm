# Sandro's heart jar (D-62, DD-21), 2026-11-21

Lane S, session 9. No Meshy. This is MM7's shipped vase (`engine/models/mm7_deco_dec97.glb`, the same `dec97` that A8
placed as a stand-in), recast as green glass that glows from inside. `scripts/build.py` edits the GLB directly:
- the base colour is a luminance-mapped bottle green;
- the metallic-roughness map is glossy (roughness 0.18);
- an emissive green map is brightest in the belly;
- the mesh and LODs are untouched.

It has 0 inverted closed parts.

| Row / sprite | Decoration | Model | Binding (`worlds/xeen/models/indoor_decorations.yml`) |
|---|---|---|---|
| 4047 / 27047 | `xeen_heartjar` "jar of green glass" | `worlds/xeen/models/xeen_deco_heartjar.glb` | height 66 (as A8's dec97), radius 20, origin at its foot |

A8 swaps `deco:jar`'s `dec97` for `xeen_heartjar` and keeps the green light (`light:heart_culvert_2`). It was seen as a
debug spawn in DD-21's heart culvert beside A8's dec97 (`review/ingame/sheet.jpg`). That spawn's z was above the
ledge, so it is not a placement check.

## Session 13 (2026-11-21): translucent glass and a heart inside (installed in session 14)

Stopped at a checkpoint (usage limits). Done: `scripts/build.py` rewritten: a fresh GLB from MM7's vase; the glass is
alpha BLEND (bottle green, alpha 0.36 in the belly, up to about 0.62 at the foot, shoulder and lip; roughness 0.07;
green emission brightest in the belly), each LOD's glass primitive an inner wall (inset 0.006, reversed) drawn before
the outer shell; an opaque dark red-brown anatomical heart (378 triangles, `openyamm_pulse` [0.7, 0.9]) shared by all
three LODs. Triangles: glass 4,608 / 1,296 / 200 (inner + outer) per LOD, plus the heart. Height 0.808 model units
(66 at the binding), unchanged; row and binding unchanged. Built to `work/s13/xeen_deco_heartjar.glb`; winding 0
inverted. Before shots: `review/s13/before/` (tour `scripts/ingame_tour.py <tag>` -> `work/s13/<tag>.yml`, the
placed jar in DD-21).
Left: look at it in game (does it read as glass? is the heart visible?), then
`python3 tools/install_model.py level_generation/decorations/xeen_heartjar_claude/work/s13/xeen_deco_heartjar.glb
--world xeen --name xeen_deco_heartjar.glb`, `./build-xeen/game/openyamm --headless-validate-actor-models --world xeen`,
after shots (`scripts/ingame_tour.py after`) and a before/after sheet in `review/s13/`.

### Session 14 (2026-11-21): installed

Seen in game on DD-21's ledge (`review/s13/after/`, sheet `review/s13/before_after.jpg`): it reads as glass and the
heart shows, but the green belly glow washed the heart to tan. `scripts/build.py` then lowered the belly glow peak
(0.75 -> 0.4), made the heart redder (base ramp and emission 150/14/10 x 0.9). Rebuilt, winding 0, installed
(`--world xeen --name xeen_deco_heartjar.glb`); after shots `review/s13/after2/`, close-ups v1 vs v2
`review/s13/heart_v1_v2_crops.jpg` (middle column = installed). Validate: 335 descriptors on 84 models, 0 refused;
`stale_bakes.py --check` 0 (DD-21 needs no rebake). Row, binding and placement unchanged. The previously installed
source is kept as `work/s13/installed_s9_heartjar.glb` (rollback: install that file with the same command).
