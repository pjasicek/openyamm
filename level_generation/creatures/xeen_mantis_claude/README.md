# Xeen mantis ants (Mantis Ant, Mantis Warrior, Mantis Queen) and the Lava Roach, 2026-11-20

Lane S project (parent session `xeen-s5`, everything by the sub-agent `xeen-s5-mantis`; identity `xeen:mantis`). Rows
(`assets_dev/worlds/xeen/source/monsters.yml`): `mantis_ants` block 11370: A Mantis Ant (level 22, Poison2), B Mantis
Warrior (30), C Mantis Queen (38, Poison3); and `giant_crawlers` C Lava Roach (11362, level 26, Fire, fire immune).
Walkers, melee only. Xeen draws the mantis as Darkside image 10 (`sprites/dark/010.mon`, `010.att`) and the Lava Roach
as image 33 (`033.mon`, `033.att`): the same upright body plan (two raptorial arms, four legs, antennae), so the roach
is a skin of this model. Built with the [quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md) (segmented creatures:
rigid pieces, one bone each), [HD masters](../CLAUDE_HD_MASTER_REFERENCES.md), [creature textures](../CLAUDE_CREATURE_TEXTURES.md),
the [texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [LOD playbook](../LOD_PLAYBOOK.md).

**State: installed** (`tools/install_model.py --world xeen`), checked in the review viewer and in game (static model
spawns in XD-21, default skin). The binding is **not** merged (the parent owns `actors.yml`): the ready block for
`Xeen Mantis A/B/C` and `Xeen Crawler C` is [integration/actors.yml](integration/actors.yml). Not accepted by the user.
**Meshy: 15 of 30 credits.**

## Deliverables

| File | What |
|---|---|
| `assets_source/worlds/xeen/models/xeen_mantis.glb` (sha256 `c15a3f1e…`) | installed source = `export/xeen_mantis.glb`; cooked runtime copy in `assets_dev/worlds/xeen/models/` (`e0e211c3…`) |
| `integration/actors.yml` | bindings for `Xeen Mantis A/B/C` (skins `mantis_a/b/c`) and `Xeen Crawler C` (`mantis_lava`); scale 134 (Queen 160.8), impact 0.50 s |
| `work/anim_v1.blend` | keyed master (rig `Mantis_Rig`, mesh `Mantis`); `work/anim_base.blend` the locked UV layout, `work/rig_v1.blend` the rig before reduction, `work/reduced_v1.blend` after |
| `references_hd/` | the five Codex masters (1536x1024), `CODEX_BRIEF.md`, `generation_runs.json`, `codex_run1/2.log`, `selected_views_review.png`; gate sheet `work/masters_gate.png` |
| `native/` | original frames: mantis `mon_0000..0007`, `att_0000..0003`; roach `roach_mon_*`, `roach_att_*`; `sheet_codex.png` (Codex input) |
| `textures/` | `mantis_basecolor_graded.png` (2K), `mantis_normal_1k`, `mantis_mr_1k` (R AO, G roughness, B 0), `mantis_region_mask.png` (R chitin, G ball joints, B eyes, A underside + mouth), `mantis_ramps.json`, `mantis_emission_mask.png` (lava glow, 1K), `mantis_material_classes.png` (4 chitin, 5 mouth, 6 eye), `mantis_ao_2k.png` |
| `review/` | `textured_sheet.png` (EEVEE at party eye height: front, quarter, side, wind-up, blow, walk, hit, corpse, face, B, C, lava, lava blow, back), `tiers.png`, `clips_quarter.png`, `clips_side.png` (clay clip sheets), `attack_front.png`, `raw_sheet.png`, `pieces_*.png`, `rig_sheet.png`, `reduced_sheet.png`, `region_classes.png`, `clip_gates.txt`, `texture_quality.json`, `uv_quality_upload.json`, `lod_scores_*.tsv`, `shadow_check.json`, `viewer_shots.png`, `ingame/` |
| `review/viewer/` | review viewer: four skin GLBs (ramps baked for three.js, the lava glow as emission), every clip |

## Mesh

Meshy Smart Topology v1 (meshy-t2, 15k, from `00_three_quarter.png`): 15,810 triangles in **56 closed rigid pieces**
(`scripts/prep.py` lists them, `review/pieces_*.png` numbers them): head, two eye spheres and lids, face plate, crown,
radial mouth disc with ten beads, two antennae with knobs, thorax (stacked rib plates, which stand out at the back as
dorsal plates), hip ring, abdomen; per arm a shoulder ball, upper arm, elbow ball, forearm and hook; per leg a hip ball,
femur, knee ball, shin and clawed foot (the left rear shin carries one more ball). Scaled to 1.10 m standing height
(antenna knobs), 1.135 m wide, forward -Y. No geometry cleanup was needed. `scripts/reduce_mantis.py` (after rigging):
edit-mode collapse per piece class (beads and knobs 0.30, ball joints 0.45, feet 0.50, rest 0.60), **8,386
triangles** (`review/reduced_sheet.png`: silhouette, face and claws kept). No purple-only geometry: the Lava Roach
skin uses the same mesh.

## Rig (`scripts/joints.py`, `scripts/rig_mantis.py`)

Exoskeleton rig, every piece 100 % on one bone (0 unweighted vertices): `Body` (hip ring, root) > `Abdomen`,
`Thorax` > `Head` > `Mouth`, `Antenna_L/R`; `Thorax` > `UpperArm_s` > `ForeArm_s` > `Hook_s`; `Body` > `Thigh_k` >
`Shin_k` > `Foot_k` for k = L1, R1 (front), L2, R2 (rear). Joints from the mesh: ball-joint pieces' box centres for
hips, knees, shoulders and elbows (each ball rides on the distal bone and turns about its own centre), closest-point
junctions for neck, wrists, ankles and antennae; abdomen and thorax pivots set under and on the hip ring (their contact
band is wide). `review/rig_sheet.png`.

## Clips (`scripts/anim_mantis.py`, 30 fps, procedural)

Legs on two-bone IK (knees up and out like a crouching frog), feet flat in their rest orientation with a toe pitch in
swing; arms aimed by direction in the thorax frame (upper arm, forearm) plus a hook hinge; the Mouth bone scales to
open the radial mouth. Floor rules every frame: the creature is lifted when anything but the legs sinks, a leg whose
vertices dip under the floor gets its target raised; lying poses put the lowest core point on the floor.

| Clip | Length | What | Event |
|---|---|---|---|
| Standing | 2.0 s loop | breathing, hooks bob, antennae sway, the mouth pulses (native idle) | |
| Walking | 0.8 s loop | diagonal trot L1+R2 / R1+L2, 0.50 m per cycle | |
| Running | 0.5 s loop | the same, lower, leaning 6 degrees, 0.80 m per cycle | |
| Attack | 1.0 s | rears and throws both arms out wide, scythes open (native att 1, peak 0.34 s), lunges and snaps the scythes together forward and down at the party (att 2), holds, folds back (att 3) | **impact 0.50 s** (frame 15: the hook tips meet, 5 cm apart) |
| Hit | 0.5 s | jolts back, arms flinch up, head back | |
| Death | 1.5 s | rears, topples backward onto its back, legs curl up, arms fold over the chest | |
| Dead | 1.0 s | Death's last pose: on its back, legs curled | |
| Fidget | 2.0 s | head tilts, the left hook wipes the mouth, antennae twitch | |

No cast and no missile on the rows: `cast: Attack`, `attack_ranged: Attack`.

### Gates

`scripts/clip_gates.py export/xeen_mantis.glb 134` (largest per-frame vertex step, second difference, loop seam,
lowest point in world units):

| Clip | Step cm | Accel cm/f² | Seam cm | Lowest units |
|---|---|---|---|---|
| Standing | 1.03 | 0.16 | 0.00 | 0.00 |
| Walking | 5.04 | 5.34 | 0.00 | -0.69 |
| Running | 6.96 | 7.28 | 0.00 | -0.73 |
| Attack | 35.77 | 20.93 | (one-shot) | 0.00 |
| Hit | 17.53 | 12.09 | | 0.00 |
| Death | 20.93 | 21.67 | | -1.48 |
| Dead | 0.00 | 0.00 | 0.00 | -1.09 |
| Fidget | 8.27 | 3.79 | 0.00 | 0.00 |

The Attack's 36 cm step is the hook tips sweeping from wide open to the front over frames 12-14 (the strike of a
mantis; the wind-up was lengthened once to 0.34-0.50 s from 0.36-0.46 s). A first loop version had a 6 cm jump in
Standing and Walking at the loop seam (antenna sway at frequencies that did not fit the loop length); fixed (whole cycles
per loop period).

Floor audit (`floor_audit.audit('xeen', ..., actors=integration/actors.yml)` on the installed GLB): **Xeen Mantis A,
B, Crawler C: ground, standing 0..0, walking -0.69..0, living lowest -0.73, corpse -1.09; Mantis C (160.8): walking
-0.82, living -0.87, corpse -1.31 world units; no problems** (tolerance 2.5).

## Textures

UVs (`scripts/uv_mantis.py`, `uv_atlas.unwrap` defaults, `cut_closed`, head and mouth 1.5x denser): PartUV charts, seam
pass, sparrow packing, **no fallback**. Meshy `retexture_v1` (meshy-7, 4K, PBR, original UVs; views 01, 03, 02, 04)
returned the same layout. Quality (`texture_quality.py export/xeen_mantis.glb`, LOD0): **atlas 71.1 %, density
p10/p50/p90 820/879/1309 (spread 1.6 with the head 1.5x denser by design), 132 islands, fragments 0.5 %, stretch p90
1.21**.

`scripts/compose_mantis.py`: colour 4K -> 2K once (Lanczos), normal and ORM to 1K; classes from the Smart Topology
piece and the paint's hue: ball joints are whole pieces (G); eyes the teal texels of the eye pieces (B); the mouth the
yellow-orange texels of the disc and beads plus the charcoal underside (A: luminance keeps them apart in one ramp); the
red abdomen tip and the dark mouth centre are in no region and keep the paint in every skin; everything else is chitin
(R), so stray teal or yellow specks take the chitin ramp. Gentle grade (`--fine 1.0 --local 0.3 --ao-strength 0.5
--contrast 1.06 --saturation 1.15`), `gutter_fill.py` last on every map. Roughness 0.35-0.8, eyes 0.2; specular 0,
metallic 0 (binding extras).

## Skins (`scripts/tier_ramps.py`, `textures/mantis_ramps.json`)

Whole-body tiers (insects tier the body, D-10). Chitin, joints and eyes take a target average colour with each texel's
luminance ratio kept; the underside + mouth region keeps value and sets hue. Ramp fit error mean (8-bit levels):
chitin 0.1-0.2, joints 0.1-0.2, eyes 0.05-0.3, underside + mouth 3.2-4.3 (p95 14-21).

| Skin | Monster | Chitin / joints / eyes / underside + mouth | Why |
|---|---|---|---|
| `mantis_a` | Mantis Ant (Xeen Mantis A) | violet #680EAA / #7012B2 / teal #2C8086 / the paint's charcoal and yellow | native: 1.3x the sprite's purple (median 76,0,128) and teal |
| `mantis_b` | Mantis Warrior (B) | dark bronze-green #525A2A / bronze #A07030 / amber #E89618 / bronze-brown and ochre | a soldier caste in old bronze; reads olive at combat distance, apart from A's violet |
| `mantis_c` | Mantis Queen (C, 1.2x) | black-violet #361E46 / gold #D4A634 / crimson #DC1E34 / dark gold-brown and gold | royalty: the darkest silhouette with bright gold points and red eyes |
| `mantis_lava` | Lava Roach (Xeen Crawler C) | dark grey #4C4848 / dark red #782210 / red #EC2410 / dark red-brown and red | native colours of image 33 (grey chitin, red eyes and joints) |

**Lava glow.** `mantis_lava` alone emits (`claude_shared/emission.py --material Mantis_LAVA`, colour 1.0,0.22,0.04,
pulse 0.2 over 2.6 s): the ball joints (brightest in their crevices, from the AO), the eyes and the cracks of the thorax
front (the sprite's burning chest), about 7 % of the surface. The far LOD copies get their own emission maps from their
own transferred masks (`scripts/far_emission.py`: G x 0.55 + B x 0.9). The other skins have no emission.

## LODs

**8,386 / 4,192 / 2,919 / 1,677** (LOD1 `tools/build_actor_lods.py` through `scripts/lods_wrap.py`; LOD2/3 the
`repair.py` ladder in the project copy `lodrepair/` (the mole's adapted copy, its `audit.sh` pointed at this project):
r25_12 and r30_16 failed the LOD2 outline gate (the thin legs), **r35_20** accepted: LOD2 outline 5.1 %, colour 10.0;
LOD3 7.2 % / 8.1 (`review/lod_scores_r35_20.tsv`); `verify_far_only` OK; shadow LODs tucked (max 15 mm). Shadow check
(`shadow_check.py 160.8`, the Queen's scale): LOD3 shadow 5.9 % outside LOD0 by more than 1 unit (2.9 % against LOD2,
0.2 % against LOD3; the playbook's look-in-game threshold is 5 %), LOD2 shadow at most 1.0 %. `lodrepair/work/mantis/
xeen_mantis/` keeps `r35_20.built.glb` and `bake_r35_20/` for map-only reruns.

## Binding (integration/actors.yml)

Scale **134** world units per model metre: the image 10 standing frame (108 x 110 px, 5,181 px of silhouette) at the
Xeen bindings' 1.34 units/px against the model's front silhouette (0.508 m², 1.135 x 1.10 m): area 135, height 134,
width 128; 147 units tall. The Lava Roach sprite (image 33, 128 x 106 px) gives 122-151 and takes A's scale as the
task asks. **Queen 160.8** (1.2x), no `scale_reference` (the descriptors' standing sprites are still the stand-in's).
`yaw_offset -pi/2`, `cast: Attack`, `run: Running`, `stride_length 0.5`, `run_stride_length 0.8`, `upper_body_root:
Thorax`, look on `Head` (30/20 degrees), `sockets: {}`, `events.attack_melee.impact 0.5`.

## Checks

- Winding: 0 inverted closed parts. Installed with `tools/install_model.py --world xeen` (cooked runtime copy).
- Viewer: `python3 tools/run_creature_review.py --project level_generation/creatures/xeen_mantis_claude check`: **32
  switches (4 skins x 8 clips), no console errors** (served by `python3 -m http.server 8912 --bind 127.0.0.1` from the
  repo root); shots in `review/shots/`, sheet `review/viewer_shots.png`.
- Renders: `review/textured_sheet.png` (EEVEE, party eye height 1.31 model m = 176 units, 2.8 m away), `review/tiers.png`.
- In game: `review/ingame/` (XD-21, `build-xeen/game/openyamm` of 2026-11-20 18:28, `model spawn` of the installed GLB:
  Standing, the blow, the wind-up, Dead at 134 and Standing at 160.8, forced LOD 2 and 3; default skin `mantis_a` only:
  `model spawn` has no skin switch); `review/ingame/tour.yml` has the command. Exit 0.

## Meshy credits: 15 of 30

| Job | Kind | Credits | Task |
|---|---|---|---|
| `smart_topology_v1` | image-to-3d, meshy-t2 smart-topology 15k, no texture, from `references_hd/00_three_quarter.png` | 5 (consumed 5) | `01a1fa4a-6786-73c4-951e-d2a991a56433` (primary) |
| `retexture_v1` | retexture, meshy-7, 4K, PBR, original UVs (`texturing/mantis_upload.glb`), views 01, 03, 02, 04 | 10 (consumed 10) | `01a1fa53-a1b1-745a-94e8-67131eab3f45` (primary) |

## Rebuild

```sh
TOK=<lease>; cd level_generation/creatures/xeen_mantis_claude
TOK=$TOK scripts/step.sh inspect_raw.py; TOK=$TOK scripts/step.sh prep.py && python3 scripts/label_pieces.py
python3 scripts/joints.py; TOK=$TOK scripts/step.sh rig_mantis.py; TOK=$TOK scripts/step.sh reduce_mantis.py
# uv_mantis.py refuses to run once texturing/mantis_upload.glb exists (the paint belongs to that layout)
TOK=$TOK scripts/step.sh anim_mantis.py            # [clip ...] reruns only those clips on work/anim_v1.blend
TOK=$TOK scripts/step.sh dump_uv3d.py; TOK=$TOK scripts/step.sh bake_ao.py     # only after a layout change
TOK=$TOK scripts/build_runtime.sh [--install]      # compose, grade, gutter fill, ramps, export, LODs, skins, glow, far LODs
python3 scripts/viewer_tiers.py && python3 ../claude_shared/emission.py review/viewer/xeen_mantis_lava.glb \
  review/viewer/xeen_mantis_lava.glb --material Mantis_A --mask textures/mantis_emission_mask.png --color 1.0,0.22,0.04 \
  && python3 scripts/update_viewer_manifest.py
python3 scripts/clip_gates.py export/xeen_mantis.glb 134
python3 ../claude_shared/tier_textures.py textures/mantis_basecolor_graded.png textures/mantis_region_mask.png \
  textures/mantis_ramps.json work/tier_mantis && TOK=$TOK scripts/step.sh tier_views.py && TOK=$TOK scripts/step.sh render_textured.py
```

`scripts/step.sh` takes the lane's Blender lock (`xeen_tiers_claude/bin/.blender.lock`). Frame renders:
`frames.py <out.png> <clip:frame:view> ...` + `join_frames.py`; clip sheets `clip_sheet.py 7 quarter|side` + `sheet_join.py`.

## Known limits

- The other skins and the lava glow were seen in the viewer and in EEVEE, not yet in game (static `model spawn` draws
  the default skin only; the parent's bound-actor tour shows them). Check the lava glow by day and in a dark corridor.
- Lava Roach differences are skin-only: its sprite's longer antennae and its burning-ring attack are not modelled (the
  chest cracks glow constantly, with a gentle pulse).
- The red abdomen tip keeps the native red on every skin (in no region).
- The thorax's stacked rib plates stand out at the back as a saw-tooth dorsal ridge (Meshy's reading of the masters).
- The Attack sweep is fast (36 cm per frame at the hook tips); the engine fits the wind-up to the native time.
- LOD3 shadow 5.9 % outside LOD0 at the Queen's scale (above the 5 % look-in-game threshold; the shadow level is usually
  coarser than the colour level, against which it is 0.2-2.9 %).
- Not accepted by the user.
