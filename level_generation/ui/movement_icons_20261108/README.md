# Movement indicator frames (Fly, Water Walk, Levitate), 2026-11-08

Seamless 128x128 HD replacements for the HUD's movement indicators (Discord OY-457: the Water Walk icon "moves
strangely"). The x2 frames in `assets_dev/engine/icons_x2` were upscaled one frame at a time, so every frame had its
own details: the Water Walk man stopped turning and twitched, the Fly wings shimmered, Levitate had no frames 07-08.
Here every frame shares the same HD pixels except what really moves in the original.

Installed 2026-11-08 after the owner approved all three (replacing the per-frame x2 upscales in
`assets_dev/engine/icons_x2`); checked in the HUD on the GPU.

| Indicator | Icon group | Frames | How it is built |
|---|---|---|---|
| Fly | `spell21` | `out/fly/sp21a10..80.png` (8) | One HD sandal (x2 frame 1). Each wing is cut from the HD frame where it is widest and warped per frame by an affine fitted to that frame's native wing silhouette (moment matching, then Powell on the soft IoU), so other frames only compress it. Sparkles are drawn procedurally at the native sparkle places, sizes and colours. |
| Water Walk | `spell27` | `out/waterwalk/sp27a10..80.png` (8) | The man is a Blender render of the MM6 peasant (`mm6_pman_v2.glb`, recoloured to a light shirt and charcoal trousers) walking in place at one fixed facing, three-quarter toward the right (yaw 65 degrees, between the native frame 1 profile and frame 2). The 8 frames sample the Walking clip at phases k/8 of its 28 frames, exactly one cycle (frame 28 equals frame 0, no root drift), so 8 flows into 1; the pose change between neighbouring frames is even (1 - IoU 0.31-0.55, the 8 -> 1 step included). The water disc is procedural (`water_disc.py`: caustic water in the disc's plane in the native disc's palette, ragged rim, spray, drip curtain) and turns 45 degrees a frame, so its loop is exact. A fixed contact shadow, a light streak and a reflection made from the render sit under him; sparkles are procedural at the native places (+ or x as in the native). |
| Levitate | `sp109` | `out/levitate/sp109-01..06.png` (6) | One HD figure (x2 frame 01) moved by the first-harmonic fit of the native bob in whole HD pixels (2..7 px, no resampling), over one HD mist that billows through a small warp whose phase turns once over the six frames, so 06 -> 01 has no jump. Native frames 07/08 are not part of the original loop. |

## Regenerate

```
cd level_generation/ui/movement_icons_20261108/scripts
python3 fly.py
# Water Walk: recolour the peasant's base colour (exported from the GLB's material), render, composite
python3 recolour_peasant.py <pman_body_basecolor.png> <recoloured.png>
#   jobs: "yaw phase out.png" per line, yaw = 65, phase = k / 8 (k = 0..7), out = ../out/waterwalk_man/man_<k+1>.png
blender -b --python render_man.py -- ../../../../assets_source/worlds/mm6/models/mm6_pman_v2.glb <recoloured.png> <jobs.txt> 512
python3 waterwalk.py
python3 levitate.py
python3 preview.py fly; python3 preview.py waterwalk; python3 preview.py levitate
```

The base colour texture is the GLB's `pman_body_basecolor_1k_head_atlas` image (save it from Blender, or read it
from the GLB).

## Previews

`preview/<name>_sheet.png`: native (2x nearest), current x2, new. `preview/<name>_{1x,2x,3x}.gif`: the new loop at game
pace (one data unit 8/128 s, slowed by the HUD to 50/128: 0.16 s a frame). `preview/<name>_current_3x.gif`: the
current x2 frames. `preview/<name>_moving.png`: pixels that change anywhere in the loop.

## Install

Copy `out/fly/*`, `out/waterwalk/*` and `out/levitate/*` to `assets_dev/engine/icons_x2/` (lowercase, mode 0644). Frame
counts are unchanged (spell21 and spell27: 8, sp109: 6), so `icon_frame_data.txt` needs no new rows. A 16-frame Water
Walk would need 16 rows for spell27 (`render_man.py` and `water_disc.disc` take any angle); it was not tried.
