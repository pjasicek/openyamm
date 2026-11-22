# Xeen giant scorpion (Scorpion, Xeen Crawler A), 2026-11-20

Lane S project (parent session `xeen-s5`, everything by the sub-agent `xeen-s5-scorpion`; identity `xeen:scorpion`).
Row (`assets_dev/worlds/xeen/source/monsters.yml`): `giant_crawlers` block 11360, tier A Scorpion (11360, level 16,
Poison2). Walker, melee only. Xeen draws it as Clouds image 19 (`sprites/xeen/019.mon`, `019.att`): a large dark
glossy brown scorpion seen from the front, pincers forward, eight legs splayed, the tail curled high over the back with
a lighter bulbous stinger. Tiers B (Electrapede) and C (Lava Roach) are other models. Built with the
[quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md) (segmented creatures: exoskeleton rig, tetrapod gait, floor
rules), [HD masters](../CLAUDE_HD_MASTER_REFERENCES.md), [creature textures](../CLAUDE_CREATURE_TEXTURES.md), the
[texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [LOD playbook](../LOD_PLAYBOOK.md).

**State: installed** (`tools/install_model.py --world xeen`), checked in the review viewer and in game (static model
spawns in XD-21). The binding is **not** merged (the parent owns `actors.yml`): the ready block for `Xeen Crawler A`
is [integration/actors.yml](integration/actors.yml). Not accepted by the user. **Meshy: 15 of 30 credits.**

## Deliverables

| File | What |
|---|---|
| `assets_source/worlds/xeen/models/xeen_scorpion.glb` (sha256 `30c4db74…`) | installed source = `export/xeen_scorpion.glb`; cooked runtime copy in `assets_dev/worlds/xeen/models/` (`f96bdd84…`) |
| `integration/actors.yml` | the binding for `Xeen Crawler A` (skin `scorpion_a`, scale 143, impact 0.467 s) |
| `work/anim_v1.blend` | keyed master (rig `Scorpion_Rig`, mesh `Scorpion`); `work/anim_base.blend` the locked UV layout, `work/rig_v1.blend` the rig before reduction, `work/reduced_v1.blend` after |
| `references_hd/` | the five Codex masters (1536x1024), `CODEX_BRIEF.md`, `generation_runs*.json` (one per run), `codex_run*.log`, `selected_views_review.png` (with the native sheet) |
| `native/` | original frames `mon_0000..0007`, `att_0000..0003` with `*_frames.json`; `sheet_codex.png` (Codex input) |
| `textures/` | `scorpion_basecolor_graded.png` (2K), `scorpion_normal_1k`, `scorpion_mr_1k` (R AO, G roughness, B 0), `scorpion_region_mask.png` (R carapace, G legs and pincers, B stinger, A eyes), `scorpion_ramps.json`, `scorpion_material_classes.png` (4 chitin, 6 eye), `scorpion_ao_2k.png` |
| `review/` | `textured_sheet.png` (EEVEE at party eye height: front, quarter, side, wind-up, blow, blow side, walk, hit, corpse, face, claw, back), `clips_quarter.png`, `clips_side.png` (clay clip sheets), `frames_death.png`, `frames_dead.png`, `raw_sheet.png`, `pieces_sheet.png`, `rig_sheet.png` (bones and weights), `reduced_sheet.png`, `region_classes.png`, `clip_gates.txt`, `floor_audit.json`, `texture_quality.json`, `uv_quality_upload.json`, `lod_scores_r25_12.tsv`, `shadow_check.json`, `viewer_shots.png`, `ingame/` |
| `review/viewer/` | review viewer: `xeen_scorpion_a.glb` (ramps baked for three.js), every clip |

## Mesh

Meshy Smart Topology v1 (meshy-t2, 15k, from `00_three_quarter.png`): 16,399 triangles in **17 closed pieces**
(`scripts/prep.py`, `review/pieces_sheet.png`): 0 body + tail (one piece), 1/2 the left/right pedipalp with its claw,
3-10 the eight walking legs (one piece each, no segment breaks), 11/12/13/16 four chelicerae, 14/15 the eyes. All eight
legs came back although the primary master hides one far leg. Scaled to 1.60 m wide (leg tip to leg tip), 1.60 m long
(claw tips to the rear plate), 0.83 m to the top of the tail, forward -Y. No cleanup needed. `scripts/reduce_scorpion.py`
(after rigging, edit-mode collapse per piece class: chelicerae 0.40, legs 0.45, body + tail 0.50, pedipalps 0.55,
eyes 0.60): **7,921 triangles** (`review/reduced_sheet.png`: claws, face, tail segments and legs kept).

## Rig (`scripts/joints.py`, `scripts/rig_scorpion.py`)

Exoskeleton rig of 40 bones: `Body` (root, carapace, face, eyes, chelicerae) > `Abdomen` (rear plates) > `Tail1..5` >
`Stinger`; per leg `Femur_k` > `Tibia_k` > `Tarsus_k` (k = L1..L4, R1..R4, L = +X, 1 = front); per side `Arm1_s` >
`Arm2_s` > `Chela_s` > `Finger_s`. Joints from the mesh (`scripts/geo.py`: geodesic distance on the pieces): legs and
pedipalps from geodesic-bin centrelines away from their junction with the body (knee = the leg's highest point, ankle =
the strongest downward turn after it; elbow and wrist at the arm's constrictions); the tail joints at the constrictions
between its five segments and the bulb (`review/zoom_tail_side.png` on the 5 cm grid); the movable claw finger is the
front finger: vertices nearer its tip than the back finger's tip along the surface, within 0.32 m of geodesic distance
(6 cm ramp at its base), hinged about the normal of the two fingers' plane. Weights: each vertex only uses its piece's
bones, `exp(-(d_i - d_min) / 8 mm)` over the distances to the bone segments, two influences, so rigid plates with
~1 cm blends at the joints of the continuous leg, pedipalp and tail tubes; the trunk splits Body/Abdomen over y
0.30-0.42 m. 0 unweighted vertices. `review/rig_sheet.png` (bones; dominant-bone colours).

## Clips (`scripts/anim_scorpion.py`, 30 fps, procedural)

Legs on two-bone IK (Femur + Tibia, knees up and out), the tarsus keeps its rest direction; pedipalps on two-bone IK
to a wrist target in the body frame, the chela orientation and the finger opening keyed; the tail curls per joint
about the body's X axis (strike and cocked shapes solved in the tail plane for the sting tip) and sways about Z with a
lag along the chain. Floor rules every frame: the body (with the limb roots) is lifted when it sinks, a leg or claw
dipping under the floor gets its target raised; lying poses put the lowest body point on the floor and settle the
tail segment by segment onto it (eased in over the fall).

| Clip | Length | What | Event |
|---|---|---|---|
| Standing | 2.0 s loop | breathing, tail sway, claws shift and twitch open (native idle) | |
| Walking | 0.8 s loop | alternating tetrapod (L1 R2 L3 R4 / R1 L2 R3 L4, small back-to-front lead), 0.50 m per cycle | |
| Running | 0.5 s loop | the same, lower, 0.80 m per cycle | |
| Attack | 1.0 s | rears, claws up and open, tail cocked back and up (0.32 s, native att 1); the right claw lunges at the party and snaps, the tail whips forward over the head (att 2); holds; recovers | **impact 0.467 s** (frame 14: the sting at its furthest reach, 0.44 m ahead of the body centre, 0.43 m high, just in front of the face) |
| Hit | 0.5 s | jolts back, claws flinch up and open, tail flinches back | |
| Death | 1.5 s | rears in pain with claws open, the tail lashes up, collapses on its belly tilted a little, legs splay, the tail falls onto the floor behind | |
| Dead | 1.0 s | Death's last pose: on its belly, the tail flat behind | |
| Fidget | 2.0 s | the tail curls and sways, the left then the right claw snaps twice | |

No cast and no missile on the row: `cast: Attack`, `attack_ranged: Attack`.

### Gates

`scripts/clip_gates.py export/xeen_scorpion.glb 143` (largest per-frame vertex step, second difference, loop seam,
lowest point in world units):

| Clip | Step cm | Accel cm/f² | Seam cm | Lowest units |
|---|---|---|---|---|
| Standing | 1.81 | 0.90 | 0.00 | -0.49 |
| Walking | 6.36 | 4.65 | 0.00 | -0.77 |
| Running | 7.73 | 7.77 | 0.00 | -0.63 |
| Attack | 36.48 | 23.59 | (one-shot) | -0.34 |
| Hit | 23.48 | 18.27 | | 0.00 |
| Death | 29.25 | 23.44 | | -0.85 |
| Dead | 0.00 | 0.00 | 0.00 | -0.60 |
| Fidget | 10.75 | 4.41 | (one-shot) | 0.00 |

The Attack's 36 cm step is the sting tip whipping forward over frames 10-13 (cocked peak frame 10, reach frame 14),
as the mantis's scythe strike. Death's 29 cm is the tail tip falling to the floor. A first Death had a 104 cm one-frame
jump where the corpse's tail settle switched on at once and an upward-arcing tail (the floor rule bent every segment up
for a later segment's contact); fixed (segment-by-segment rule, settle eased in over 0.6-1.2 s).

Floor audit (`floor_audit.audit('xeen', ..., actors=integration/actors.yml)` on the export, `review/floor_audit.json`):
**Xeen Crawler A: ground, standing -0.49..0, walking -0.77..0, living lowest -0.77, corpse -0.60 world units, no
problems** (tolerance 2.5).

## Textures

UVs (`scripts/uv_scorpion.py`, `uv_atlas.unwrap` defaults, `cut_closed`, the front-facing parts (Body = carapace, face,
eyes, chelicerae; the claws) 1.25x denser): PartUV charts, seam pass, sparrow packing, **no fallback**. Meshy
`retexture_v1` (meshy-7, 4K, PBR, original UVs; views 01, 03, 02, 04) returned the same layout. Quality
(`texture_quality.py export/xeen_scorpion.glb`, LOD0): **atlas 66.2 %, density p10/p50/p90 1161/1429/1596 (spread
1.38 with the front 1.25x denser by design), 35 islands, fragments 0.0 %, stretch p90 1.19**.

`scripts/compose_scorpion.py`: colour 4K -> 2K once (Lanczos), normal and ORM to 1K; classes from the Smart Topology
piece and each triangle's dominant bone: eyes = the two eye pieces (A), legs and pincers = pieces 1-10 (G), stinger =
the Stinger bone's triangles of the body piece (B), everything else carapace (R, chelicerae included). Gentle grade
(`--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15`), `gutter_fill.py` last on every map.
Roughness 0.3-0.75 (glossy chitin), eyes 0.15; specular 0, metallic 0 (binding extras).

## Skins (`scripts/tier_ramps.py`, `textures/scorpion_ramps.json`)

| Skin | Monster | Carapace / legs and pincers / stinger / eyes | Fit mean / p95 (8-bit) |
|---|---|---|---|
| `scorpion_a` | Scorpion (Xeen Crawler A) | native dark glossy brown at ~1.35x the sprite's medians: 103,65,38 / 90,59,37 / tan 156,99,52 / the paint kept | 0.12/0.17, 0.11/0.11, 0.06/0.15, 4.2/15.6 |

Native medians measured on `mon_0000`: body 76,48,28, legs and claws 64,44,28, stinger bulb 120,76,40. The paint came
back more copper than the sprite; the 'mid' ramps set the shown average and keep each texel's luminance (gloss and
plate seams survive). The four regions let later tiers recolour the whole body by numbers only.

## LODs

**7,921 / 3,960 / 1,980 / 984** (LOD1 `tools/build_actor_lods.py` through `scripts/lods_wrap.py`; LOD2/3 the
`repair.py` ladder in the project copy `lodrepair/` (the mantis's copy, its `audit.sh` pointed here), first step
**r25_12** accepted: LOD2 outline 5.7 %, colour 8.7; LOD3 6.1 % / 7.5 (`review/lod_scores_r25_12.tsv`);
`verify_far_only` OK; shadow LODs tucked (max 15 mm). Shadow check (`shadow_check.py 143`): at most 1.2 % of the LOD3
shadow more than 1 unit outside any colour level. `lodrepair/work/scorpion/xeen_scorpion/` keeps `r25_12.built.glb`
and `bake_r25_12/` for map-only reruns (the audit renders were deleted for disk space).

## Binding (integration/actors.yml)

Scale **143** world units per model metre: the image 19 standing frame (`mon_0000`, 159 x 99 px without the painted
ground shadow, 4,751 px of body silhouette without the dark outline) at the Xeen bindings' 1.34 units/px against the
model's rest front silhouette (1.60 x 0.83 m, 0.461 m²): width 133, area 136 (outline excluded, so low), height 160
(the sprite is drawn from a little above, which raises the tail) -> 143: **229 units wide, 229 long, the raised tail
119 units high** (descriptor collision radius 127, height 132). `yaw_offset -pi/2`, `cast: Attack`, `run: Running`,
`stride_length 0.5`, `run_stride_length 0.8`, `upper_body_root: Abdomen` (the tail strike plays over the gait while it
walks; the claws sit on the Body root with the legs), no head look (the head is fused into the carapace),
`sockets: {}`, `events.attack_melee.impact 0.467`.

## Checks

- Winding: 0 inverted closed parts. Installed with `tools/install_model.py --world xeen` (cooked runtime copy).
- Viewer: `python3 tools/run_creature_review.py --project level_generation/creatures/xeen_scorpion_claude check`:
  **8 switches (1 skin x 8 clips), no console errors** (repo HTTP server on 8912); shots in `review/shots/`, sheet
  `review/viewer_shots.png`.
- Renders: `review/textured_sheet.png` (EEVEE, party eye height 1.23 model m = 176 units, 2.6 m away).
- In game: `review/ingame/` (XD-21, `build-xeen/game/openyamm` of 2026-11-20 21:33, `model spawn` of the installed GLB
  at 143: the wind-up, Standing, the blow, Dead; forced LOD 2 and 3 in `lods.png`); `review/ingame/tour.yml` has the
  command. Exit 0, no model load errors.

## Meshy credits: 15 of 30

| Job | Kind | Credits | Task |
|---|---|---|---|
| `smart_topology_v1` | image-to-3d, meshy-t2 smart-topology 15k, no texture, from `references_hd/00_three_quarter.png` | 5 (consumed 5) | `01a1fa91-00ed-731d-b767-02850c8abcb7` (primary) |
| `retexture_v1` | retexture, meshy-7, 4K, PBR, original UVs (`texturing/scorpion_upload.glb`), views 01, 03, 02, 04 | 10 (consumed 10) | `01a1faa2-184d-7062-8515-2aaa954f2d27` (primary) |

## Rebuild

```sh
TOK=<lease>; cd level_generation/creatures/xeen_scorpion_claude
TOK=$TOK scripts/step.sh inspect_raw.py; TOK=$TOK scripts/step.sh prep.py && python3 scripts/label_pieces.py
python3 scripts/joints.py; TOK=$TOK scripts/step.sh rig_scorpion.py; TOK=$TOK scripts/step.sh reduce_scorpion.py
# uv_scorpion.py refuses to run once texturing/scorpion_upload.glb exists (the paint belongs to that layout)
TOK=$TOK scripts/step.sh anim_scorpion.py          # [clip ...] reruns only those clips on work/anim_v1.blend
TOK=$TOK scripts/step.sh dump_uv3d.py; TOK=$TOK scripts/step.sh bake_ao.py     # only after a layout change
TOK=$TOK scripts/build_runtime.sh [--install]      # compose, grade, gutter fill, ramps, export, LODs, skin, far LODs
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
python3 scripts/clip_gates.py export/xeen_scorpion.glb 143
python3 ../claude_shared/tier_textures.py textures/scorpion_basecolor_graded.png textures/scorpion_region_mask.png \
  textures/scorpion_ramps.json work/tier_scorpion && TOK=$TOK scripts/step.sh render_textured.py
```

`scripts/step.sh` takes the lane's Blender lock (`xeen_tiers_claude/bin/.blender.lock`). Frame renders:
`frames.py <out.png> <clip:frame:view> ...` + `join_frames.py`; clip sheets `clip_sheet.py 7 quarter|side` +
`sheet_join.py`; `zoom_views.py <name> x y z size`; `probe_pose.py <clip> <frame>` (per-bone heights).

## Known limits

- The paint is more matte and granular than the sprite's glossy shell (specular is off for creature skins); the
  ramps bring the colour to the sprite's dark brown.
- The legs are continuous tubes (no separate segment pieces), bent at blended joints; up close the knee shows a soft
  bend rather than a hinge.
- The claw finger is part of the claw's mesh: its opening (up to 30 degrees) stretches the 6 cm at its base a little.
- Death has a tail lash straight up at about 0.5 s before it falls (a death throe); the corpse lies on its belly, not
  on its back.
- `upper_body_root: Abdomen` layers only the tail strike over the gait when it attacks while walking; the claws then
  keep the gait's swing.
- Seen in game only as debug-spawned models (no binding merged yet); `level_generation/update_gitignore.py` was not
  run (it writes `level_generation/.gitignore`, outside this project; no file here over 256 KB is admitted by the
  rules). Not accepted by the user.
