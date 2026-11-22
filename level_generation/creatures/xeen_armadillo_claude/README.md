# Xeen Armadillo, 2026-11-20/21

Lane S project (identity `xeen:armadillo`). HD masters, Smart Topology, clean and rig by the sub-agent
`xeen-s6-armadillo` (parent `xeen-s6`); everything from the UV gate on by `xeen-s7-armadillo` (parent `xeen-s7`).
Row (read-only): 11441 Armadillo (`Xeen Sand Worm B`, level 38, Brkweapon, descriptor height 175, radius 140), ground
walker, melee only. Native art: Darkside image 5 (`sprites/dark/005.mon`, `005.att`). Built with the
[quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md) main route (Meshy model, own rig with automatic weights,
procedural clips with floor rules), [HD masters](../CLAUDE_HD_MASTER_REFERENCES.md),
[creature textures](../CLAUDE_CREATURE_TEXTURES.md), the [texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md)
and the [LOD playbook](../LOD_PLAYBOOK.md); scripts and structure follow `../xeen_mole_claude/`.

**State: installed** (`tools/install_model.py --world xeen`), checked in the review viewer and in game (static model
spawns in XD-21). The binding is **not** merged (the parent owns `actors.yml`): the ready block for `Xeen Sand Worm B`
is [integration/actors.yml](integration/actors.yml). Not accepted by the user. **Meshy: 20 of 30 credits.**

## Deliverables

| File | What |
|---|---|
| `assets_source/worlds/xeen/models/xeen_armadillo.glb` (sha256 `cd4b20f5…`) | installed source = `export/xeen_armadillo.glb`; cooked runtime copy in `assets_dev/worlds/xeen/models/` (`206210f0…`) |
| `integration/actors.yml` | the binding for `Xeen Sand Worm B` (skin `armadillo_a`, scale 220, impact 0.733 s) |
| `work/anim_v1.blend` | keyed master (rig `Dillo_Rig`, mesh `Dillo`); `work/anim_base.blend` is the locked UV layout (claw weights fixed in place by `fix_weights.py`), `work/rig_v2.blend` the PartUV-valid rig before UVs, `work/rig_v1.blend` the first rig |
| `references_hd/` | the five Codex masters, `00b_three_quarter_high.png` (the Smart Topology input that worked), `CODEX_BRIEF.md`, `generation_runs.json`, logs, `selected_views_review.png` |
| `native/` | original frames `mon_0000..0007`, `att_0000..0003` with `*_frames.json`; `sheet_codex.png` (Codex input) |
| `texturing/dillo_upload.glb` | the static upload the paint belongs to (do not re-run `uv_dillo.py`) |
| `textures/` | `dillo_basecolor_graded.png` (2K), `dillo_normal_1k`, `dillo_mr_1k` (R AO, G roughness, B 0), `dillo_region_mask.png` (R red armour/hide incl. ball and spikes, G pale skin, B claws, A eyes + tongue), `dillo_ramps.json`, `dillo_material_classes.png` (1 hide, 4 claw/spike, 6 eye, 7 tongue), `dillo_ao_2k.png` |
| `review/` | `textured_sheet.png` (EEVEE at party eye height: front, quarter, side, wind-up, blow, blow from the front, hunch, walk, hit, corpse, tongue flick, fidget, back), `clips_quarter.png`, `clips_side.png` (clay clip sheets), `region_classes.png`, `uv_quality_upload.json`, `texture_quality.json`, `viewer_shots.png`, `shots/`, `ingame/`; earlier rig/mesh sheets (`stress_sheet.png`, `weights_sheet.png`, `raw*_sheet.png`, `masters_gate.png`) |
| `review/viewer/` | review viewer: `xeen_armadillo_a.glb` (ramps baked for three.js), every clip |

## Mesh

Meshy Smart Topology v2 (meshy-t2, 15k, from `00b_three_quarter_high.png`; v1 came back flat and pear-shaped).
`scripts/clean.py` (xeen-s6): body kept, holes filled, shell widened x1.25 (Xeen draws the beast broader than tall),
body ahead of the tail decimated to 55 %, procedural tail-ball spikes and forked tongue added. `scripts/fix_mesh.py`
(xeen-s7) made it PartUV-valid: the hole fill had left duplicate faces, 6 degenerate triangles and 17 non-manifold edges
in the mouth and under the rump (deleted, coincident vertices merged, holes refilled; 20 small boundary edges remain
inside the mouth), the eye/nostril caps (1,205 triangles for 0.5 % of the surface) decimated to 25 %, and the 15 spikes
rebuilt as 8-sided open cones (their bases sit inside the ball), one developable chart each.
**9,387 triangles**: part 0 body 8,904, 1 face caps 300, 2 spikes 120, 3 tongue 63. Rest: forward -Y, 0.50 m tall,
0.76 m wide, 2.2 m snout to tail ball.

## Rig (`scripts/rig_dillo.py`, `scripts/fix_weights.py`)

28 bones: `Body` (root at the hips) > `Spine` > `Chest` > `Neck` > `Head` > `Tongue`; `Tail1..8` > `TailBall` >
`Spikes` from Body; per side `UpperArm` > `ForeArm` > `Hand` (from Chest) and `Thigh` > `Shin` > `HindFoot` (from Body).
Heat weights on trunk and limbs, shell kept on the trunk bones, feet wholly on Hand/HindFoot below the wrist/ankle,
tail by arc position, ball rigid on TailBall, spikes on Spikes, tongue on Tongue, face caps on Head; 0 unweighted.
`fix_weights.py` (on `anim_base.blend`, weights only): the foot rule skipped |x| < 0.10, where each front foot's inner
claw sits, so those claw tips stayed on Spine and stretched into thin spikes from the chin to the floor whenever the
body moved; every vertex below 7 cm connected (below 7 cm) to a foot vertex within 0.22 m (front) / 0.13 m (hind) of
that foot now goes wholly on the foot (Hand_L 58, Hand_R 65, HindFoot_L 15, HindFoot_R 12 vertices).
Spikes hide at Spikes scale 0.4 (inside the ball), the tongue at Tongue scale 0.05.

## Clips (`scripts/anim_dillo.py`, 30 fps, procedural)

Every frame: the core is lifted if it sinks; a foot whose vertices dip under the floor gets its IK target raised; tail
segments bend up (about tail direction x Z, positive = up; the first version bent them down and hung the tail through
the floor in Walking and Death) until they clear.

| Clip | Length | What | Event |
|---|---|---|---|
| Standing | 2.4 s loop | breathing heave, two forked-tongue flicks (native mon 4-7), head drift, slow tail sway | |
| Walking | 1.0 s loop | heavy waddle on short sprawled legs (LF+RH / RF+LH, duty 0.65), shell roll and yaw, tail swinging low; 0.45 m per cycle | |
| Running | 0.6 s loop | the same, longer, faster, lower; 0.80 m per cycle | |
| Attack | 1.5 s | forelegs up with the claws out, tail lifts (att 0); the tail arcs over the back as the spikes pop out and the ball swells x1.3 (att 1); the spiked mace comes down over the front of the shell at the party while both claws slam forward (att 2); hunch, spikes back in, recover (att 3) | **impact 0.733 s** (frame 22: the ball furthest forward, at y -0.53 m, 0.72 m up, above the head from the party's view) |
| Hit | 0.5 s | flinches into the shell: head ducked, body dropped, tail tucked a little | |
| Death | 1.6 s | rears in pain (spikes half out), rolls onto its right side, legs curl, tail falls limp | |
| Dead | 1.0 s | Death's last pose: on its right side on the floor | |
| Fidget | 2.4 s | curls partly into a ball (head tucked, back arched, tail round) and uncurls; long tongue flick | |

No cast and no missile on the row: `cast: Attack`, `attack_ranged: Attack`.

### Gates

`scripts/clip_gates.py export/xeen_armadillo.glb 220` (largest per-frame vertex step, second difference, loop seam,
lowest point in world units at scale 220):

| Clip | Step cm | Accel cm/f² | Seam cm | Lowest units |
|---|---|---|---|---|
| Standing | 4.29 | 3.37 | 0.00 | -0.01 |
| Walking | 4.69 | 3.95 | 0.00 | -0.01 |
| Running | 8.99 | 8.14 | 0.00 | -0.01 |
| Attack | 26.76 | 13.70 | (one-shot) | -0.62 |
| Hit | 15.45 | 14.36 | | -0.01 |
| Death | 18.84 | 12.09 | | -0.13 |
| Dead | 0.00 | 0.00 | 0.00 | +0.44 |
| Fidget | 12.34 | 3.74 | | -0.48 |

The Attack's 26.8 cm step is the mace whip (frames 18-21, the ball 1 m out on the tail), intended. Hit was 32 cm per
frame with a 4/5-degree tail curl and coil per segment; halved and the onset moved to 0.11 s (15.5 cm).
`scripts/stretch_probe.py <clip> <frame>` lists the most stretched edges: after `fix_weights.py` the largest are 4-10 cm
at the inner edge of the hind feet in the death roll (underside, out of view).

Floor audit (`floor_audit.audit` with this binding block on the installed GLB; the world's `actors.yml` still binds the
mm7_m162 stand-in): **Xeen Sand Worm B: ground, standing -0.01, walking -0.01..+0.40, living lowest -0.62, corpse
+0.44 world units, no problems** (tolerance 2.5).

## Textures

UVs (`scripts/uv_dillo.py`, `uv_atlas.unwrap`, head 1.6x denser). PartUV first failed on the raw mesh ("Invalid mesh");
on the fixed mesh it ran but cut the banded shell into 159 charts under 8 triangles, the merges flipped and were
reverted, and the layout missed the gate (atlas 75.5 %, **fragments 6.5 %**, stretch 1.19; kept in
`work/uv_partuv_try/`). The installed layout is **xatlas charts + seam pass (6 rounds) + sparrow** (`charts='xatlas'`):
gate on the upload **atlas 70.6 %, density p10/p50/p90 2147/2258/2437 (spread 1.14), 181 islands, fragments 2.8 %,
stretch p90 1.20**. Meshy `retexture_v1` (meshy-7, 4K, PBR, original UVs; views 01, 03, 02, 04) returned the same
layout; the export measures the same (`review/texture_quality.json`).

`scripts/compose_dillo.py`: colour 4K -> 2K once (Lanczos), normal and ORM to 1K. Meshy painted the spikes and the
tongue as pale specks: the spikes are painted with the ball's own red, darker toward the tip, the tongue green (darker
than the iris so one channel-A ramp holds black pupil -> green -> orange), both with a flat normal. Regions: pale skin
where most of a texel's neighbourhood (sigma 4) is pale pink (the belly bands, not the paint's pale speckles), claws
= grey texels on the foot bones, eyes = orange-yellow texels on the head plus their dark pupils, the dark mouth and
nostrils in no region, everything else red armour. Gentle grade (`--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast
1.06 --saturation 1.15`), `gutter_fill.py` last on every map. Roughness: hide 0.55-0.92, claws and spikes 0.35-0.7,
eyes 0.25, tongue 0.35; specular 0, metallic 0 (binding extras).

Skin (`scripts/tier_ramps.py`, `textures/dillo_ramps.json`): one skin `armadillo_a`, Darkside image 5's native
colours. The paint already matches the sprite (red median 200,56,50 against 204,48,48; pale 236,160,160 in both), so
the regions keep the paint's hue; claws trimmed to the sprite's mid grey, eyes toward its orange (236,128,14). Fit error
mean / p95 in 8-bit levels: **armour 8.1 / 26.0** (the feathered edges of the pale bands), **pale 3.3 / 9.5, claws
2.0 / 6.6, eyes + tongue 7.4 / 32.0** (1,000 core texels). Later tiers on this model add rows to `DESIGN`.

## LODs

**9,387 / 4,692 / 2,342 / 1,149** (LOD1 `tools/build_actor_lods.py` through `scripts/lods_wrap.py`; LOD2/3 the
`repair.py` ladder in the project copy `lodrepair/` (the mole's, `audit.sh` pointed at this project and the lane lock),
first step **r25_12** accepted: LOD2 outline 4.0 % colour 8.5, LOD3 2.9 % / 6.0; LOD1 1.5 % / 6.0); `verify_far_only`
OK; far maps 512 / 256 px with 91 % / 85 % UV correspondence. Shadow LODs tucked up to 15 mm. Shadow check
(`audit_mm678_20261111/lod_audit/shadow_check.py 220`): 4.0 % of the LOD3 shadow more than 1 unit outside LOD0 (0.7 %
more than 2), below the 5 % look-in-game threshold. `lodrepair/work/dillo/xeen_armadillo/` keeps `r25_12.built.glb`
and `bake_r25_12/` for map-only reruns.

## Binding (integration/actors.yml)

Scale **220** world units per model metre: the front silhouette of `mon_0000` without the tail (7,887 px at the Xeen
bindings' 1.34 units/px = 14,170 units²) against the model's front silhouette (0.293 m²) gives 220. The model then
stands 110 units (sprite 74 px = 99) and is 166 units wide (sprite body 140 px = 188 units; the sprite's 181 px include
the curled tail), 484 units snout to ball (the descriptor radius is 140). For comparison the sand worm binds its own
model at 110 (A) / 126.5 (C); the stand-in entry's `scale_reference: Xeen Sand Worm A` belonged to the stand-in and is
dropped (this is its own model, Xeen draws one size). `yaw_offset -pi/2`, `cast: Attack`, `run: Running`,
`stride_length 0.45`, `run_stride_length 0.8`, look on `Head` (30/20 degrees), `sockets: {}`,
`events.attack_melee.impact 0.733`. **No `upper_body_root`**: the weapon is the tail (a child of Body), so the
follow-through plays on the whole body; with Chest as upper-body root the tail would snap back to the gait while the
armadillo walks. No `worlds/mm9/` path anywhere (D-44).

## Checks

- Winding: 0 inverted closed parts. Installed with `tools/install_model.py --world xeen` (cooked runtime copy).
- Viewer: `python3 tools/run_creature_review.py --project level_generation/creatures/xeen_armadillo_claude check`:
  8 clip switches, no console errors (served by `python3 -m http.server 8912 --bind 127.0.0.1` from the repo root);
  shots in `review/shots/`, sheet `review/viewer_shots.png` (the viewer's auto-framing crops the long body a little).
- Renders: `review/textured_sheet.png` (EEVEE, party eye height 176 units = 0.80 model m, 1.9-3.4 m away).
- In game: `review/ingame/` (XD-21, `build-xeen/game/openyamm`, `model spawn` of the installed GLB at scale 220, yaw
  pi: Standing, the blow, Dead; wind-up, hunch; forced LOD 2 and 3; `sheet.png`); `review/ingame/tour.yml` has the
  command. Exit 0, no model load errors.

## Meshy credits: 20 of 30

| Job | Kind | Credits | Task |
|---|---|---|---|
| `smart_topology_v1` | image-to-3d, meshy-t2 smart-topology 15k, no texture, from `references_hd/00_three_quarter.png` | 5 | `01a1faf6-2dea-715b-9dde-bf10c9c65287` (primary) |
| `smart_topology_v2` | image-to-3d, meshy-t2 smart-topology 15k, no texture, from `references_hd/00b_three_quarter_high.png` (v1 came back flat and pear-shaped with the tail fused sideways) | 5 | `01a1faf9-6184-76a5-bc91-890388589e46` (primary) |
| `retexture_v1` | retexture, meshy-7, 4K, PBR, original UVs (`texturing/dillo_upload.glb`, layout gated: atlas 70.6 %), views 01, 03, 02, 04 | 10 | `01a1fb1f-5bc2-7269-ad08-024cb4b0f026` (primary) |

## Rebuild

```sh
TOK=<lease>; cd level_generation/creatures/xeen_armadillo_claude
TOK=$TOK scripts/step.sh clean.py; TOK=$TOK scripts/step.sh rig_dillo.py; TOK=$TOK scripts/step.sh fix_mesh.py
# uv_dillo.py refuses to run once texturing/dillo_upload.glb exists (the paint belongs to that layout)
TOK=$TOK scripts/step.sh fix_weights.py          # weights only, on work/anim_base.blend, from rig_v2's weights
TOK=$TOK scripts/step.sh anim_dillo.py           # [clip ...] reruns only those clips on work/anim_v1.blend
TOK=$TOK scripts/step.sh dump_uv3d.py; TOK=$TOK scripts/step.sh bake_ao.py     # dump after weight changes, AO after a layout change
TOK=$TOK scripts/build_runtime.sh [--install]    # compose, grade, gutter fill, ramps, export, LODs, skin, far LODs, winding
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
python3 scripts/clip_gates.py export/xeen_armadillo.glb 220
python3 ../claude_shared/tier_textures.py textures/dillo_basecolor_graded.png textures/dillo_region_mask.png \
  textures/dillo_ramps.json work/tier_dillo && TOK=$TOK scripts/step.sh render_textured.py
TOK=$TOK scripts/step.sh clip_sheet.py 7 quarter && python3 scripts/sheet_join.py clips_quarter.png
```

Diagnostics: `diag_mesh.py <blend>` (pieces, degenerate and non-manifold edges, UV fragments per part), `diag_nm.py`,
`raster_probe.py` (paint classes by bone), `stretch_probe.py <clip> <frame>`. `anim_mole.py`, `compose_mole.py` and
`rig_mole.py` are the mole templates the project started from (not used).

## Known limits

- The hind claws are painted red by Meshy (the masters and the sprite have grey claws on all four feet); only the
  front claws are grey.
- The tail is a straight 1 m tube behind the body (the masters'); the sprite's idle curls it beside the body. The
  mace cannot reach over the head on a tail rooted behind the rump: at the blow the ball is above the front half of the
  shell, which from the party's view reads as above the head (the sprite's att 2).
- During the recovery (about 1.0-1.2 s) the tail passes through vertical before it settles; the hunch of att 3 is a
  head tuck with a half coil, not a full defensive ball.
- The corpse lies on its side and is taller (0.76 m) than the living beast (0.50 m).
- In the dim XD-21 room the red reads darker and less saturated than the bright sprite.
- 20 small boundary edges remain inside the mouth after the mesh repair (not visible).
- Seen in game only as debug-spawned models (no binding merged yet); not accepted by the user.
