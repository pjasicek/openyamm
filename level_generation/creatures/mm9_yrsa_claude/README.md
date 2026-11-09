# MM9 Yrsa the Troll (mm9_yrsa) — 3D actor, 2026-10-29

## Hit floor sink fixed (2026-10-30, later) - current

`floor_audit.py --world mm9` flagged "Hit sinks to -5.4" (the open point of the section below, not a new regression of
the boots or sleeves). **Cause**: the jitter smoothing, `--ground-loop Hit` with `--smooth Hit 0.08 --smooth-hold 0`. The raw
MM9 Hit (wince3) puts the flying skirt hem 12-19 cm under the floor for most of the clip; the earlier per-key solve held
it at 0 by chasing the hem with the whole body (the jitter), and the smoothed offsets, pinned back to the first key's
offset over the first 4 sigma (0.32 s), cannot follow the 0.07-0.17 s dip, so the hem sinks 5.4 cm. Smoothing the body harder or less (sigma 0.03-0.10, hold 0-2, shorter end tails, `--raise`) either failed `jitter_gate.py`
(shoulder-skin excess over MM9 2.3-8.9 mm/f2 against 2.0) or left the sink; the clip start cannot take a 10 cm body lift.
**Fix** (smallest): a second `floor_fix.py` call on the first one's result, `scripts/floor_ops_hit.txt`
(`--lift-joints Hit --lift-only x* --tolerance 0.02`): the skirt strips bend just enough to stay within 2 cm of the
floor, in the keys where they are under it (strips `xbk1`, `xbk_rt_a`, `xrt`). Bending to the full depth doubled the hem
acceleration over MM9's (max 0.40 vs 0.19, the earlier snapped skirt); within 2 cm it is 0.27. Wired into
`v2/scripts/build_runtime_v2.sh`. Only Hit's strip rotations change: every other clip is identical (0 difference of
all joint matrices at all keys), meshes, textures and LODs untouched.

| Check | Before | After |
|---|---|---|
| `floor_audit.py --world mm9` Yrsa living / corpse | -5.4 / 0.0 | **-1.9 / 0.0 ok** (tolerance 2.5) |
| `jitter_gate.py`, fails | 0 | 0 |
| `check_winding.py` inverted | 0 | 0 |
| viewer `v2.2-hitfloor-20261030`, `run_creature_review.py check` | | 7 clips, 0 errors |

Shots of Hit at 0.07, 0.10, 0.15, 0.23, 0.37, 0.67 s, front and side: `v2/review/hit_floor_sheet.png`
(single frames in `review/shots/`): hem on the floor, skirt not snapped, no pop at either end. Installed with
`tools/install_model.py --world mm9`.

## Sleeves, forearms and smooth clips (2026-10-30)

User on the boots build: "hands - cut off, floating?". Then approved one addition: smooth the jitter in her clips.
Boots and textures stay; the mesh gains only the lining and forearms below.

- **Cause**: the sleeves are single-sided (back faces culled), so a view into a cuff went through the far wall to the
  background, and `graft_hands.py` ends the hand in an open 2.3 cm stub at the cuff, with nothing behind it.
- **Lining, not a two-sided material**: `v2/scripts/sleeve_lining.py` (shared; `v2/work/shoes_v2.blend` ->
  `sleeves_v2.blend`). An inner copy of the sleeve faces 3 mm in, flipped, same weights (the `mm6_cle_claude`
  technique), on one dark rough texel of the sleeve's own paint, with a rim strip closing the open cuff edge. Why not two-sided:
  back faces would show the outer paint, bright cuff trim included, lit from the wrong side, and the wrist would
  still be a cut end. Meshy's own inner layer (33-34 faces per sleeve, an arm painted on it, pale slivers at the cuff)
  takes the same dark texel. 154 + 158 lining faces, 32 + 2 rim faces.
- **Forearm**: each stub ring continues up the sleeve to 6 cm from the elbow in four rings, from the stub's tilted
  shape to true circles (radius up to 3 cm), capped; weights reach the forearm alone halfway; each column repeats the
  stub's rim texels, so the skin continues. A first version with one flat skin texel on a straight line read as a
  pink box in the viewer. 135 + 144 faces. LOD0 8,676 triangles (was 8,051).
- **Arm correction**: `arm_clear.py` is gone (`v2/scripts/hand_rest_yrsa.txt` replaces it). Its depth test samples four
  points per face, and on the large skirt faces it read clear hands as up to 6 cm inside, so most of its turns chased
  nothing. New `arm_hand_gate.py --exact` (signed distance to the nearest triangle) shows MM9's own hands clear of the
  dress in every clip but Fidget's left hand (2.7 cm deep, 20 frames over 1 cm). That hand alone gets `hand_rest.py`,
  capped at 3.3 cm (new `--max-push`: the horizontal cast reads 9.7 cm on the flared skirt) with a slow push (0.24 s)
  on a smoothed direction (new `--sigma-dir`). Walking, Running, Standing, Hit and Death arms are MM9's.
- **Floor offsets**: the remaining jitter fails were the root, not the arms: `floor_fix.py` solved each key alone, and
  in Hit and Death the lowest point is the flying skirt hem, so the whole body chased it (one 16 cm jump in Death).
  New `--smooth` / `--smooth-loop` / `--smooth-hold` low-pass those offsets and keep each one-shot's first and last keys
  (`scripts/floor_ops.txt`: Walking and Running 0.04 s, Hit 0.08 s, Death 0.07 s). In Death and Dead the skirt strips also
  bend clear of the floor (`--lift-joints Death Dead --lift-only x*`), so the body no longer rides the hem: she falls
  to MM9's height and the corpse lies 6 cm lower. Not in Hit: there the bends snapped the skirt (hem acceleration 3 x
  MM9's).
- **What now reads differently**: Fidget's left arm. The approved build swung it out by up to 32 deg to clear the skirt
  (`arm_clear.py`); it now stays near MM9's pose, the hand low in front of the skirt (`v2/review/jitter_strips_compare.png`).
  Also the fall in Death, as above. **Open**: in Hit the hem sinks up to 5.4 cm under the floor for about 0.1 s (it was
  held at 0 by the body chasing it), so `floor_audit.py` flags it; Death stays within 1.8 cm. Walking and Running within
  0.3 / 0.4 cm of the floor when grounded.

| Check | Before | After |
|---|---|---|
| `jitter_gate.py`, fails over all clips and sides | 10 | **0** (`v2/review/jitter_gate_final.txt`) |
| Fidget hand acceleration L / R, mm/f2 (MM9 26.9 / 5.5) | 57.3 / 38.1 | 26.8 / 5.5 |
| Walking right hand, mm/f2 (MM9 9.6) | 15.1 | 9.6 |
| `sleeve_gate.py` see-through, worst px of 160 x 160 near the sleeve, front / above / below / 3/4, left | 482 / 457 / 443 / 404 | 19 / 21 / 55 / 20 |
| same, right | 55 / 90 / 44 / 48 | 2 / 2 / 8 / 28 |
| Forearm poking out of the sleeve, frames | - | 0 |
| `arm_hand_gate.py --outer-only --exact` hand over 1 cm, frames | 0 (MM9 raw: Fidget 20) | 0 (Fidget worst 0.6 cm, was 0; Death 1.0 cm, unchanged) |
| `detached_parts_audit.py --fps 48` | 0 | 0 |

The residual see-through pixels sit at the neck and hair (`v2/review/sleeve_gate_after/`, green), not in the sleeves.
Flat shading 0.00 (`flat_shading_check.py`), winding 0. Sheets: `v2/review/sleeves_compare.png` (user framings),
`v2/review/viewer_sleeves_sheet.png` (viewer shots, four clips, front, 3/4 from above, below, both cuffs),
`v2/review/jitter_strips_compare.png` (Fidget and Walking before/after).

Rebuild: `BLEND=v2/work/sleeves_v2.blend v2/scripts/build_runtime_v2.sh yrsa Yrsa v2/scripts/roles_yrsa_v2.json --install`
(no graft any more). `PYGLTF_PYTHON` is `claude_shared/gltf_venv/bin/python`, by that path, not resolved through
`realpath` (that drops the venv); setup: `python3 -m venv claude_shared/gltf_venv &&
claude_shared/gltf_venv/bin/pip install pygltflib numpy scipy pillow`. Meshy: 0 credits.
The boots section below still holds; its clip graft is replaced by this section.

## Boots rooted (2026-10-30) - current base

Coordinator request after `../claude_shared/detached_parts_mm9.md`: both boots were separate pieces, the right one
5.1 cm from anything at bind, the left one parting by 6.2 cm in Hit (2 detached parts). Only the boots changed: no
retexture, no clip change.

- **Cause**: the Meshy dress is a hollow shell (skirt and bodice, no hips or thighs inside), and each boot is an open
  tube ending at the knee inside the skirt, its top weighted to the back skirt chains. There was no leg to root it in.
- **Fix** (`v2/scripts/root_shoes.py`, as `mm9_eye_claude/scripts/root_limbs.py` stretches a leg into the body):
  each boot's top band (13-14 vertices) is stretched 0.56 m up to a hip point under the waist (x +/-6.5 cm, 10 cm
  above the pelvis), where the skirt narrows. Top-ring vertices cast towards the skirt land 2 mm inside it (4-5 per
  boot) and take the skirt's weights at that point (`xbk_rt*` 0.67-0.69, `FHP Spine2` 0.13-0.15, `XCOM_skirt`
  0.10-0.13); the others (inner side) sit at 5 cm and take their mean; band vertices blend by smoothstep. No vertices
  added; UVs and textures unchanged (the boot band's leather stretches over the thigh, which shows only under the
  skirt). `v2/work/head_v1.blend` -> `v2/work/shoes_v2.blend`, report `v2/work/root_shoes.json`.
- **Clips kept**: the rebuild's `arm_clear.py` sees the new thighs and turned Fidget's left upper arm differently
  around 1.8 s (51 mm at the hand), so the approved clips were grafted back (`../claude_shared/graft_clips.py --replace`,
  all seven, from `v2/work/before_texpass/mm9_yrsa_installed.glb`). Rebuild: `BLEND=v2/work/shoes_v2.blend
  v2/scripts/build_runtime_v2.sh yrsa Yrsa v2/scripts/roles_yrsa_v2.json`, then that graft onto `v2/export/mm9_yrsa.glb`,
  then `tools/install_model.py --world mm9`. (A baseline rebuild from `head_v1.blend` reproduces the installed GLB
  exactly, 0.000 mm.)

**Checks**: `detached_parts_audit.py --fps 48` **0 detached in any pose** (was 2; the boots touch the skirt at 2 mm,
listed as shallow; `v2/review/detached_parts_texpass.json`); `glb_diff.py` against the installed GLB: every other vertex
0.000 mm in every clip at 48 fps, same clips; winding 0 inverted; LOD0 8,051 triangles; `arm_hand_gate.py` and
`jitter_gate.py` output identical before and after (`v2/review/*_texpass_{before,after}.txt`; Fidget's known jitter
fail unchanged); viewer `v2.1-boots-20261030`, `check` 7 clips, 0 errors; `mm9_actor_models_build_every_binding`
(`--world mm9`): 49 descriptors on 20 models, 0 failed. `v2/scripts/poke_gate.py` (rays from the thigh band, every
clip at 48 fps, `v2/review/poke_gate_*.json`): with rays from 15 deg up nothing shows while standing, walking, running
or in Fidget; in Hit up to 7 sample points show through the neckline gap from steeply above (`Dead`/`Death`: through
the skirt opening while lying, as the old boot tops did, 108-165 points before against 27-52 now).
`texture_quality.py` (textures untouched): body 29.5 % atlas, 335 islands as before; the stretched thigh band (hidden)
lowers body density p10 678 -> 377 and raises stretch p90 1.36 -> 3.43; head set unchanged.
Sheets: `v2/review/texpass_shoes_compare_tex.png` and `..._xray.png` (bind, Hit 8 and Hit 27 at 48 fps: both sides,
front, from below; before/after at identical cameras). Before state: `v2/work/before_texpass/`. Meshy: 0 credits.

New shared v2 scripts from this pass (identical in the three projects' `v2/scripts/`): `texpass_uv.py`, `texpass_head_uv.py`,
`bake_ao_texpass.py`, `compose_texpass.py`, `compose_head_texpass.py`, `uv_pairs.py` + `match_skin.py`, `texpass_shots.py`
(identical-camera stills), `part_views.py` (close-ups around joints, also see-through), `glb_diff.py` (what changed
between two runtime GLBs: images, meshes, clips, posed vertices).
Yrsa only: `root_shoes.py`, `poke_gate.py`.

## v2 rework (2026-10-30, after the user's review) - current base (boots changed above)

User review of v1: four-finger hands, a pasted-on face patch (skin colour leaking into the white hair, a hard seam
at the jaw), fidget frame 72 hand into the body; the animations otherwise approved, so the MM9 skeleton and clips stay.

- **Hands**: five-finger MPFB hands (old female) grafted inside the sleeve ends, with 15 new finger bones per side
  (`FHP <S> Thumb1..Pinky3`) that copy the rest frame of the MM9 mitten bones, so `clips_mm9.py` `finger_alias`
  drives them from MM9's own Finger0/Finger1 curl (MCP copied, distal joints a share of it). Weights from MPFB.
- **Head**: head set from a Codex head turnaround + a Meshy head-only retexture (10 credits): head shell, hood with
  its tail, white hair, both braids and the bead band are their own parts in the head set (no skin texels in them);
  the face is painted with the hair in one pass, so there is no patch outline.
- **Fidget**: `arm_clear.py` (two passes) turns the upper arm the least where a hand enters the body; the gate
  now shows 1 interpolated frame > 1 cm in Fidget (3.8 cm at 48 fps frame 87), none elsewhere; the wide sleeves
  still brush the dress (forearm cloth 5-6 cm, cloth on cloth).
- In game (remade isle review root, minimized): `v2/review/ingame_sheet.png` in mm9_forad_claude (all three).
- **User acceptance (2026-10-30):** "yrsa the troll - good, this one is good, including the animations". This is the
  reference for MM9 humanoids: MM9 skeleton and clips, grafted five-finger hands, separate head set.
- Runtime `v2/scripts/build_runtime_v2.sh yrsa Yrsa v2/scripts/roles_yrsa_v2.json --install`; LOD0 8,051 triangles.
- 2026-10-30 face check after Annud's face fix (shared scripts synced, Yrsa not rebuilt: approved): no neck hole
  and clean eyes; a 3-edge hole in the head shell sits under the hood; the mouth shows a faint jagged teeth line like
  Annud's, milder (`v2/review/face_check_20261030.png`). `build_export_v2.py`'s `export_fix` (not set in
  `head_yrsa.json`) would remove it on a future rebuild.
- Jitter gate (2026-10-30, report only, not rebuilt; `v2/review/jitter_gate.json`): Fidget fails (hand acceleration
  57.3 / 38.1 mm/f2 against MM9's 26.9 / 5.5: the per-key `arm_clear.py` turns), Walking right hand marginal (15.1
  against 9.6). Detached-parts audit: both shoes are separate pieces (right 5 cm under the dress at bind, left
  opens in Hit). A rebuild would use `hand_rest.py` instead of arm_clear for Fidget.

Shared v2 scripts (identical in the three projects' `v2/scripts/`): `graft_hands.py` (posed MPFB/MakeHuman CC0
hands grafted at the bracer or sleeve: old skin past the cuff deleted by the class map, stub conformed inside the
cuff, MPFB weights kept), `head_split.py` (head faces + `HeadUV`, head upload), `bake_hands.py` +
`compose_headhand.py` (head + hands set: Meshy head retexture resampled into the lower-left 0.8 square, MakeHuman
hand skin graded to the character's own skin in the freed squares; base colour 2K like the body, normal/ORM 1K),
`arm_hand_gate.py` (every clip at 48 fps: hand/forearm depth inside the rest of the body, finger edge stretch,
wrist), `arm_clear.py` (least upper-arm turn that takes a hand out of the body), `glb_frames.py` (textured renders); since the 2026-10-30 face fix also `build_export_v2.py`'s `export_fix` (head cleanup), `head_closeups.py`
(head/neck close-ups), `head_topology.py` (holes, flipped faces), `compare_rows.py` (before/after sheets) and
`shading_check.py` (flat-shading check).

## v1 (MM9 rig-reuse route, superseded where v2 says so)


Isle of Ashes NPC for the MM9 world: MONSTERS.txt 254, `Yrsa.abc` + `YRSA.dtx`; isle object `YrsatheTroll` (46), RUDE 1. Built by the **MM9 rig-reuse route for humanoid NPCs**: a Meshy HD
body fitted to the ORIGINAL MM9 skeleton, playing the original MM9 clips (see "Deviations"). Progress, hashes and
Meshy receipts: `creature_3d_progress.json`. Shared scripts are identical in `mm9_forad_claude/`,
`mm9_yrsa_claude/` and `mm9_annud_claude/` (only the configs differ).

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_yrsa.glb` (installed with `tools/install_model.py --world mm9`; cooked copy in `assets_dev`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, descriptor `MM9 254 Yrsa the Troll` (new MM9 NPC row, see below), `scale: 100` (GLB = LithTech units x 0.0256, MM9 world x 2.56), `yaw_offset: -1.570796327`, look `FHP Neck, FHP Head`, stride walk/run 1.5 / 1.5 |
| Triangles LOD0/1/2/3 | 7,628 / 3,805 / 1,351 / 436; LOD0 7628 (head+neck 3001, hands 874, rest 3753; from Smart Topology 14688) |
| Skeleton | Yrsa / PeasantFemale, 73 joints (`FHP *` biped without thigh joints, skirt chains `XCOM_skirt`/`xbk*`/`xfr*`/`xrt*`, hood tail `FHP Ponytail1..12`, braids `xpony*`); names and rest rotations unchanged, joints translated onto the HD body |
| Clips (30 fps, from her own clips in `YRSA.abc` (static, stand, fidget1, walk, Wince3, Die3)) | Standing `stand` 2.0 s, Walking `walk` 1.3 s, Running `walk` x1.45 0.9 s, Fidget `fidget1` 3.2 s (also script clip `talk`), Hit `Wince3` 1.03 s (her spin; skirt chains damped 60 % toward Standing), Death `Die3` 1.03 s, Dead; attack_melee/attack_ranged map to Fidget (she never attacks; no MM9 attack clip for her body) |
| Textures | one set, no tiers: base colour 2K (head and neck UV islands 3x denser), normal 1K, ORM 1K (R baked AO, G roughness, B 0), `openyamm_specular 0`, metallic 0; class map `textures/yrsa_material_classes.png` (1 skin, 8 cloth/leather, 9 metal) |
| Meshy credits | **15** (Smart Topology 5, retexture 10; backup account), no retries |

## Route (scripts/)

0. **HD masters** (`references_hd/`, Codex, two runs, brief `CODEX_BRIEF.md`, records `generation_runs.json`,
   `selected_views_review.png`): inputs are renders of the MM9 model with its skin (`mm9_views.png` five views,
   `mm9_head_views.png`, `mm9_skin_x4.png` surface only). Pose = the MM9 bind pose (arms out ~17 deg below horizontal),
   so the Meshy mesh needs no posing to sit on the MM9 skeleton. Canvas 1536x1024 (spread arms).
1. **Meshy** Smart Topology 15k from `00_three_quarter.png` (`requests/smart_topology_v1.json`).
2. **Fit + weights** (`fit_rig.py`, `fit_config.json`; X-ray `review/xray_v1.png`): body scaled to the MM9 height,
   centre chain by torso depth (neck/head by the face line), arms by slices along the MM9 arm axis (each joint keeps
   its fraction of the arm and its offset from the centreline; wide sleeves: along the axis only), hips by hip width,
   knees/ankles by leg slices (a dress: legs follow the shoes), every other joint (fingers, hip ring, skirt, braids,
   hood) with its nearest fitted ancestor. Weights: the rigid MM9 skin carried onto the fitted joints, nearest-surface
   bone label, 8 diffusion passes, then **arm bands** (clavicle -> upper arm -> forearm -> hand by the position on the
   arm axis, so vest caps and sleeves follow the arm), 4 influences.
3. **Reduce after weighting + UVs** (`reduce_uv.py`, `reduce_config.json`): head/neck 0.75, hands 0.6, rest 0.42;
   Smart UV, head islands x3; upload `texturing/yrsa_body_upload.glb`; **retexture** with our UVs from 01/03/02/04
   (`requests/retexture_v1.json`).
4. **Textures** (`bake_ao.py`, `compose.py`, `../claude_shared/grade_basecolor.py --ao`).
5. **Clips** (`clips_mm9.py`, `roles_yrsa.json`): MM9 local rotations copied unchanged (the rest rotations are the MM9
   ones), translations = our rest + the source's pelvis offset x leg-length ratio; LithTech keys resampled as monotone
   cubic curves at 30 fps; loop seams spread; one-shots eased from/to Standing (0.15 / 0.2 s; Death in only).
6. **Runtime** (`build_runtime.sh yrsa Yrsa [--install]`): textured export (armature lifted so model y = 0 is
   the floor) -> clips -> `prepare_actor_glb.py` -> `build_actor_lods.py` -> `shrink_shadow_lods.py` -> material
   extras -> `floor_fix.py` (`floor_ops.txt`: ground loops/idles, raise run, corpse grounded) -> winding check (0).

Rebuild: `PYGLTF_PYTHON=<python with pygltflib> scripts/rebuild_rig.sh source/mm9/yrsa.glb scripts/roles_yrsa.json`
(fit + quick clip test), then `reduce_uv.py` (only with a new retexture: the UVs feed the paid job), `bake_ao.py`,
`compose.py`, `grade_basecolor.py`, `build_runtime.sh yrsa Yrsa --install`. MM9 sources:
`tools/mm9_import_discovery/convert_abc_model.py <abc> source/mm9 --id <id> --texture 0=<dtx> --scale 0.0256`.

## Checks (2026-10-29)

`scripts/gates.py` (`review/gates.json`), every clip at 30 fps (lowest point cm, edge stretch, wrist rotation
relative to the forearm vs rest, largest per-frame world rotation step of head/hands/feet):

| Clip | lowest cm | stretch p99 / max | hand p99 / max | wrist deg | jerk deg/frame |
|---|---|---|---|---|---|
| Standing | -0.0..0.0 | 1.38 / 2.86 | 1.36 / 2.19 | 34.8 | 0.5 |
| Walking | -0.1..0.0 | 1.7 / 4.48 | 1.39 / 2.35 | 30.7 | 10.1 |
| Running | -0.1..1.7 | 1.7 / 4.48 | 1.39 / 2.35 | 30.7 | 13.5 |
| Fidget | -0.0..0.0 | 1.79 / 5.01 | 1.35 / 2.19 | 36.6 | 11.7 |
| Hit | -0.0..0.0 | 2.21 / 7.22 | 1.36 / 2.19 | 34.8 | 61.3 |
| Death | -0.1..1.6 | 1.65 / 5.16 | 1.36 / 2.19 | 34.8 | 40.8 |
| Dead | -0.0..-0.0 | 1.7 / 4.32 | 1.36 / 2.19 | 34.8 | 0.0 |

- Loop seams 0; floor: `floor_audit.py --world mm9` ok (stand 0, walk never below, corpse on the floor).
- Wrist angles above 60 deg and the fast steps (attack, hit) are the MM9 authored motion (fidget scratch, bow, limp
  death hand), checked in textured close-ups (`review/tex_clips.png`, `review/tex_close.png`): no wrist collapse.
- Viewer: `review/viewer/index.html` (port 8912 serves the repo root:
  `http://127.0.0.1:8912/level_generation/creatures/mm9_yrsa_claude/review/viewer/index.html`), `check_viewer.mjs` exit 0.
- Regression `mm9_actor_models_build_every_binding` (`--world mm9`): 6 descriptors on 4 models, 0 failed.
- In game: `../mm9_forad_claude/review/ingame_sheet.png` (all three NPCs spawned on the remade isle: idles, walk/run, a hostile Forad fighting, Yrsa killed and lying on the floor) (remade isle review root, minimized, private `--user-data`, tour
  `mm9_forad_claude/review/ingame_tour.yml`).

## Deviations and open points

- **Clips are MM9's own, on the MM9 skeleton** (the dragonfly rig-reuse route), not the humanoid set/Mixamo with a
  Mixamo-frame rig: the MM9 libraries are the authored clips of these exact bodies and cover every role (including
  Forad's bow and the shopkeeper's talk), with MM9's contact events. The playbook gates were run on them. MM9's
  `stand1` is sparse (5 keys / 3 s), so Standing is quiet; MM9 hands are mittens (thumb + one four-finger chain),
  so fingers do not curl individually.
- No separate 1K head set (budget 15 credits: one retexture); the face gets 3x texel density in the 2K atlas instead.
- No tiers: unique NPCs with one MM9 skin each (no region mask/ramps).
- Descriptor: MM9 NPC rows (IsMonster 0) had no MM9 world descriptor, so `tools/mm9_import_discovery/
  generate_mm9_monster_tables.py` gained `--npc-actors` (`mm9_npc_actor_rows.tsv`: 54, 252, 254 with the legacy
  visual actor the isle already used) and the MM9 tables were regenerated (137 rows; the 134 monster rows unchanged).
  The isle's actors still use the old stand-in monster ids until the story session switches them.
- User artistic acceptance: v1 not recorded; v2 accepted (see the v2 section).
