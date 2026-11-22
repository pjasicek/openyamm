# Xeen sabertooth (Sabertooth, Kennel Sabertooth), 2026-11-20

Lane S project (parent session `xeen-s5`, sub-agent `xeen-s5-saber`; identity `xeen:saber`). Rows: the `wolves`
family in `assets_dev/worlds/xeen/source/monsters.yml` (block 11410): B Sabertooth (11411, level 22, recovery 60,
Spd 295) and D Kennel Sabertooth (11413, DD-13's ogre kennel, Sabertooth's numbers). Ground walkers, melee only.
Darkside draws it with image 44 (`sprites/dark/044.mon`, `044.att`), front only. Built with the
[quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md) main route, [HD masters](../CLAUDE_HD_MASTER_REFERENCES.md),
[creature textures](../CLAUDE_CREATURE_TEXTURES.md), the [texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md)
and the [LOD playbook](../LOD_PLAYBOOK.md).

**State: installed** (`tools/install_model.py --world xeen`), checked in the review viewer and in game (static model
spawns in XD-21). The binding is **not** merged (the parent owns `actors.yml`): the ready block for `Xeen Wolf B` and
`Xeen Wolf D` is [integration/actors.yml](integration/actors.yml). Not accepted by the user. **Meshy: 15 of 30 credits.**

## Deliverables

| File | What |
|---|---|
| `assets_source/worlds/xeen/models/xeen_saber.glb` (sha256 `f20b3d18…`) | installed source = `export/xeen_saber.glb`; cooked runtime copy in `assets_dev/worlds/xeen/models/` (`cb9f7d98…`) |
| `integration/actors.yml` | bindings for `Xeen Wolf B` and `Xeen Wolf D` (skin `saber_a`, scale 150, impact 0.5 s) |
| `work/anim_v1.blend` | keyed master (rig `Saber_Rig`, mesh `Saber`); `work/anim_base.blend` the UV master with the mouth cut (`anim_base_premouth.blend` before it), `work/rig_v1.blend` the rig before UVs |
| `references_hd/` | the five Codex masters (1536x1024), `CODEX_BRIEF.md`, `generation_runs.json` (merged from the per-view records), `codex_run*.log`, `selected_views_review.png` |
| `native/` | original frames `mon_0000..0007`, `att_0000..0003` with `*_frames.json`; `sheet_codex.png` (Codex input) |
| `textures/` | `saber_basecolor_graded.png` (2K), `saber_normal_1k`, `saber_mr_1k` (R AO, G roughness, B 0), `saber_region_mask.png` (R tawny fur, G pale fur, B fangs + claws, A irises), `saber_ramps.json`, `saber_material_classes.png` (1 nose, 2 fur, 4 claw, 5 tooth, 6 eye, 7 mouth), `saber_ao_2k.png` |
| `review/` | `raw_sheet.png`, `clean_sheet*.png`, `stress_sheet.png`, `clips_side.png`, `clips_quarter.png`, `gaits_side.png`, `textured_sheet.png` (EEVEE at party eye height), `mouth_check.png`, `mouth_parts.png`, `region_classes.png`, `clip_gates.txt`, `texture_quality.json`, `uv_quality_upload.json`, `shadow_check.json`, `viewer_shots.png`, `ingame/` |
| `review/viewer/` | review viewer (`xeen_saber_a.glb`, ramps baked for three.js), every clip |

## Mesh

Meshy Smart Topology v1 (meshy-t2, 15k, from `00_three_quarter.png`): 15,611 triangles in 50 pieces. The body came
out three-quarter: the trunk's front 6 cm right of its rear and the head yawed 19 degrees to its left; the chest ruff
an overlapping open shell (an 85-edge boundary), holes on the cheek and both flanks, 30 whisker and lip rods, fur
plates. `scripts/clean.py`: straighten (x shear by the trunk midline, head yawed back about the neck with a smooth
falloff and centred); keep the body, the left eyeball, the left fang and the left paws' 8 claw pieces; cut Meshy's
tail; close every hole with a centroid fan (an open loop makes the voxel remesh a thin double wall); voxel remesh
6 mm (fuses ruff and lip slit into one closed surface), light smooth, cut at x = 0 and mirror the left half (the
camera side of the master); `scripts/reduce_voxel.py` (MeshLab quadric; Blender's collapse stalled at 40k) to 8,000;
`scripts/clean_finish.py` softens the fused ruff edge, flank dents and tail stub (Taubin) and joins the mirrored eyes,
fangs and claws and one procedural tail (10-sided tapered tube on a Catmull-Rom centreline hanging behind and curling
up at the tip, as in the masters). `scripts/mouth.py` (after the UVs, paint layout unchanged): the lips cut along the
mouth line (20 edges split), lips wholly Head above / Jaw below, and a mouth bag (flattened sphere 9 x 12 x 4 cm,
upper half Head, lower half Jaw) in a free atlas corner, painted gum red with ivory teeth rows by compose.
**10,133 triangles** (body 8,000, bag 168, eyes 450, fangs 212, claws 764, tail 540). Face attribute `part`: 0 body,
1 eyes, 2 fangs, 3 claws, 4 tail, 5 mouth bag. Rest: forward -Y, 2.25 m nose to tail tip, 1.28 m to the ear tips.

## Motion route (decision)

The quadruped playbook's main route (own rig, procedural clips with floor rules), not an installed animal's clips:
- MM9 cat (`mm9_cat_claude`): a house cat's motion: `stand1` is a sitting idle on folded hind legs, walk 0.4 s and run
  0.2 s loops; its attack, Hit and Death are authored key poses anyway. Retiming a 0.4 s house-cat walk to a big cat's
  1 s stride plays the same quick trot in slow motion, and the route needs the fit/graft/hind-IK machinery whose knee
  folds are still open there.
- MM9/MM8 wolf (`mm9_wolf_claude`, `mm8_wolf.glb`): canine gaits (trot, a wolf's bite) on a wolf's proportions, with the
  voxel rebuild and armpit repairs that route needed.
- `anim_library/`: no quadruped motion (Mixamo and Meshy are biped).

Procedural keys give the big-cat features directly: a slow four-beat lateral-sequence walk with the head carried low,
shoulder blades turning with each foreleg, the spine swaying, and a rotary gallop with spine flexion.

## Rig (`scripts/rig_saber.py`)

`Body` (root at the hips) > `Spine` > `Chest` > `Neck` > `Head` > `Jaw`; `Tail1..8` (from Body) on the tail's
centreline; per side `Scapula` > `UpperArm` > `ForeArm` > `FrontPaw` (from Chest) and `Thigh` > `Shin` > `Hock` >
`HindPaw` (from Body, digitigrade). Joints from mesh slices and grid views (`review/zlegs_side.png`, `zhead_side.png`).
Heat weights on the body (Jaw and tail excluded), then the head region wholly Head ahead of the skull base, the jaw
below the mouth line ahead of the hinge (then the hard lip split of `mouth.py`), eyes and fangs rigid on Head, claws
rigid on the nearest paw, the tail by arc position. 0 unweighted vertices; stress poses (`review/stress_sheet.png`:
stride, crouch, snarl, swipe, roll, turn) without tearing.

## Clips (`scripts/anim_saber.py`, 30 fps, procedural)

Front legs: two-bone IK (UpperArm + ForeArm) to the wrist, elbow pole behind, the paw keeps its rest orientation plus a
pitch (folds back in the swing), the wrist held at least 0.38 m from the shoulder (high swings flipped the elbow over
the shoulder). Hind legs: the Hock keeps its rest direction plus a pitch, Thigh + Shin IK to the hock joint, knee pole
in front. Every frame: the core is lifted when it sinks, a paw under the floor gets its target raised, the tail bends
up until it clears; the death blends from lifting to grounding (no jump when the fall comes to rest).

| Clip | Length | What | Event |
|---|---|---|---|
| Standing | 3.0 s loop | breathing, slow look round, tail-tip swish, mouth breathing a little | |
| Walking | 1.0 s loop | lateral-sequence walk (LH, LF, RH, RF), slightly crouched, head low, shoulder blades turning with the forelegs, spine sway; 1.45 m per cycle | |
| Running | 0.633 s loop | rotary gallop (LH, RH, LF, RF), spine flexing and extending; 2.30 m per cycle | |
| Sprint | 0.6 s loop | the gallop stretched (MAW's faster chase); 3.00 m per cycle | |
| Attack | 1.2 s | crouch and snarl (native att 0), lunge with both forepaws thrown forward, claws out, jaws wide at the party (att 1-2), the paws slam down and the jaws snap shut, recover (att 3) | **impact 0.5 s** (frame 15: paw tips furthest forward, jaw 46 degrees) |
| Hit | 0.5 s | flinches back, head jerks up and aside, snarls | |
| Death | 1.7 s | rears in pain, the hind legs buckle, falls onto its right side, the upper legs sprawl | |
| Dead | 1.0 s | Death's last pose: on its right side, legs out | |
| Fidget | 2.6 s | a great yawn baring the sabres, a head shake, a tail flick | |

No cast and no missile on the rows: `cast: Attack`, `attack_ranged: Attack`.

### Gates

`scripts/clip_gates.py export/xeen_saber.glb 150` (`review/clip_gates.txt`; largest per-frame vertex step, second
difference, loop seam, lowest point in world units at scale 150):

| Clip | Step cm | Accel cm/f² | Seam cm | Lowest units |
|---|---|---|---|---|
| Standing | 0.97 | 0.10 | 0.00 | +0.07 |
| Walking | 12.70 | 14.89 | 0.00 | +0.03 |
| Running | 13.14 | 23.93 | 0.00 | +0.05 |
| Sprint | 20.20 | 20.32 | 0.00 | -0.15 |
| Attack | 23.23 | 20.90 | (one-shot) | -0.78 |
| Hit | 13.61 | 10.54 | | +0.05 |
| Death | 13.31 | 7.90 | | -0.82 |
| Dead | 0.00 | 0.00 | 0.00 | +0.02 |
| Fidget | 6.02 | 5.42 | | +0.07 |

The Attack's 23 cm step is the lunge and jaw snap (`scripts/step_report.py`), the gallops' are the paws' ground speed
(5 m/s in the Sprint is 17 cm per frame) and the foot reversal at lift-off. Fixed on the way: a 57 cm jump in Death (a
switch from lifting to grounding, now blended), a 35 cm elbow flip in the gallops, the hind legs overreaching at the end
of the stance (strides shortened, stance centres moved forward, the scapula turning with the leg), the jaw opening the
wrong way (the Head bone's local X points to -X).

Floor audit (`scripts/floor_check.py`: `floor_audit.audit` on this binding block and the export): **Xeen Wolf B and D:
ground, standing +0.07, walking +0.03..+0.09, living lowest -0.78, corpse +0.02 world units, no problems**
(tolerance 2.5). Strides measured by `stride_audit.measure` (vertices / foot joints): Walking 1.453 / 1.449, Running
2.296 / 2.290, Sprint 2.87 / 2.97 against the bound 1.45, 2.3, 3.0. Playback at scale 150: wander (Spd 295) on the walk
x1.36, chase (590) on the gallop x1.08, MAW's chase (895) on the sprint x1.19 (computed by hand: `gait_gate.py` reports
the Xeen wolf rows as stationary and gives no targets).

## Textures

UVs (`scripts/uv_saber.py`, `uv_atlas.unwrap` defaults, head and jaw 1.6x denser): PartUV charts, seam pass, sparrow
packing, **no fallback**. Gate on the upload: atlas 65.7 %, spread 1.20, 47 islands, fragments 0 %, stretch p90 1.18.
Meshy `retexture_v1` (meshy-7, 4K, PBR, original UVs; views 01, 03, 02, 04) returned the same layout. Installed LOD0
(`texture_quality.py export/xeen_saber.glb`): **atlas 66.2 %, density p10/p50/p90 1629/1744/1974 (spread 1.21), 48
islands, fragments 0.0 %, stretch p90 1.18**.

`scripts/compose_saber.py`: colour 4K -> 2K once (Lanczos), normal and ORM to 1K; regions from the paint's hue and
lightness limited by geometry: tawny fur, pale fur (muzzle, chin, ruff, belly, inner legs) as a soft lightness weight,
fangs and claws (the fang and claw pieces plus golden claw tips painted on the paws), green irises (eyeballs and head);
the dark red nose, pupils, lids, mouth cavity and the mouth bag in no region (they keep their paint). Mouth cavity faces
(inward-facing faces inside the lips) gum red; the bag gum red with ivory teeth rows, put back after the grade
(`scripts/apply_bag.py`: the AO would blacken it). Gentle grade (`--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast
1.06 --saturation 1.15`), `gutter_fill.py` last on every map (islands from `texturing/saber_uvref.glb`, which includes
the bag). Specular 0, metallic 0 (binding extras).

Skin (`scripts/tier_ramps.py`, `textures/saber_ramps.json`): **`saber_a`**, the native tawny ochre (the paint's coat is
already a little lighter than the sprite's, fur median 161,107,60 against 144,92,52, so the coat is lifted only x1.06;
pale fur x1.02). Fit error mean / p95 in 8-bit levels: fur 3.3/10.3, pale 3.1/9.3, fangs+claws 4.4/17.9, irises
5.6/17.4. Later tiers are new rows in `DESIGN` (ramp numbers only; fur + pale cover nearly all of the silhouette).

## LODs

**10,133 / 5,065 / 2,532 / 1,266** (LOD1 `tools/build_actor_lods.py` through `scripts/lods_wrap.py`; LOD2/3 the
`repair.py` ladder in the project copy `lodrepair/`, first step **r25_12** accepted: LOD1 outline 0.4 % colour 3.3,
LOD2 1.5 % / 5.0, LOD3 2.4 % / 4.7); far maps 512 / 256 (atlas 45.3 / 35.7 %); `verify_far_only` OK; shadow LODs
tucked 13.7-15 mm. Shadow check (`audit_mm678_20261111/lod_audit/shadow_check.py 150`): at most 0.72 % of the LOD3
shadow more than 1 unit outside any colour level (`review/shadow_check.json`). `lodrepair/work/saber/xeen_saber/` keeps
`r25_12.built.glb` and `bake_r25_12/` for map-only reruns.

## Binding (integration/actors.yml)

Scale **150** world units per model metre. The native sprite (mon_0000: 100 px tall, 5,043 px of body without the
ground shadow) at the Xeen bindings' 1.34 units/px gives 105 by height and 120 by front silhouette area (model
0.631 m²). Xeen draws the sabertooth at the Dark Wolf's sprite size, but the Dark Wolf binding (`mm8_wolf` at 237.4)
stands 158 units, 1.17x its own sprite, and the sabertooth must read clearly bigger and heavier: 150 gives 191 units to
the ear tips (1.21x the wolf), about 270 nose to rump and 337 to the tail tip (wolf 247 with its tail);
`review/ingame/vs_wolf.png` shows both side-on. `yaw_offset -pi/2`, `cast: Attack`, `run: Running` (2.3),
`sprint: Sprint` (3.0), `stride_length 1.45`, `upper_body_root: Spine` (the lunge rides over the gait), look on
`Neck`, `Head` (30/20 degrees), `sockets: {}`, `events.attack_melee.impact 0.5`. No `scale_reference` (both rows are
the same animal). The descriptor collision rows (Height 160, Radius 100) are the wolf family's; the model stands 191.

## Checks

- Winding: 0 inverted closed parts. Installed with `tools/install_model.py --world xeen` (cooked runtime copy).
- Viewer: `python3 tools/run_creature_review.py --project level_generation/creatures/xeen_saber_claude check`: 9
  switches (1 skin x 9 clips), no console errors (served by `python3 -m http.server 8912 --bind 127.0.0.1` from the repo
  root); shots in `review/shots/`, sheet `review/viewer_shots.png`.
- Renders: `review/textured_sheet.png` (EEVEE, party eye height 1.17 model m = 176 units, 3.6 m away), mouth close-ups
  `review/mouth_check.png`.
- In game: `review/ingame/` (XD-21, `build-xeen/game/openyamm`, `model spawn` of the installed GLB at scale 150 yaw pi:
  Standing, the blow at 0.5, the wind-up at 0.3, Walking, the Fidget yawn, Dead, forced LOD 2 and 3; `tour.yml`;
  sheet `sheet.png`), and `vs_wolf.png` (`tour_vs_wolf.yml`: beside the Dark Wolf's binding). Exit 0, no load errors.

## Meshy credits: 15 of 30

| Job | Kind | Credits | Task |
|---|---|---|---|
| `smart_topology_v1` | image-to-3d, meshy-t2 smart-topology 15k, no texture | 5 | `01a1fa4c-1ddb-7687-b8b8-66e0cb9e9429` (primary) |
| `retexture_v1` | retexture, meshy-7, 4K, PBR, original UVs | 10 | `01a1fa68-0b98-7161-946d-cb50627a3c69` (primary) |

## Rebuild

```sh
TOK=<lease>; cd level_generation/creatures/xeen_saber_claude      # step.sh takes the lane Blender lock
TOK=$TOK scripts/step.sh inspect_raw.py; TOK=$TOK scripts/step.sh prep.py
TOK=$TOK scripts/step.sh clean.py && ../claude_shared/meshlab_venv/bin/python scripts/reduce_voxel.py 8000
TOK=$TOK scripts/step.sh clean_finish.py; TOK=$TOK scripts/step.sh dump_mesh.py clean_v2.blend mesh_v2
TOK=$TOK scripts/step.sh rig_saber.py
# uv_saber.py refuses to run once texturing/saber_upload.glb exists (the paint belongs to that layout)
TOK=$TOK scripts/step.sh mouth.py                # from work/anim_base_premouth.blend -> anim_base.blend + saber_uvref.glb
TOK=$TOK scripts/step.sh anim_saber.py           # [clip ...] reruns only those clips on work/anim_v1.blend
TOK=$TOK scripts/step.sh dump_uv3d.py; TOK=$TOK scripts/step.sh bake_ao.py     # after a mesh change
TOK=$TOK scripts/build_runtime.sh [--install]    # compose, grade, bag, gutter fill, ramps, export, LODs, skin, far LODs
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
python3 scripts/clip_gates.py export/xeen_saber.glb 150; python3 scripts/floor_check.py
python3 ../claude_shared/tier_textures.py textures/saber_basecolor_graded.png textures/saber_region_mask.png \
  textures/saber_ramps.json work/tier_saber && TOK=$TOK scripts/step.sh render_textured.py
```

Sheets: `piece_views.py` (env `BLEND`, `FOCUS`), `part_views.py <blend> <prefix> cx cy cz size [jaw]`, `grid_views.py`,
`zoom_views.py`, `stress.py`, `clip_sheet.py N side|quarter` (env `CLIPS`) + `sheet_join.py`, `render_shots.py` (env
`SHOTS`), `grid_sheet.py`; `step_report.py` locates per-frame step spikes.

## Known limits

- The fur is paint on a smooth voxel body: the chest ruff's lower edge stays a soft ledge where Meshy's ruff shell fused
  with the chest; a shallow dent remains behind each shoulder.
- The body is mirrored from its left half: Meshy's asymmetric stance is gone (both sides stand the same).
- The open mouth is a lip cut plus a gum-red bag with painted teeth rows (no modelled lower teeth); in a wide yawn seen
  up close the bag reads as a smooth cavity.
- Galloping forelegs fold high in the swing (the wrist is held 0.38 m from the shoulder); the run's foot reversal at
  lift-off gives 24 cm/f² peaks.
- One skin: B (Sabertooth) and D (Kennel Sabertooth) look the same, as in Xeen.
- Seen in game only as debug-spawned models (no binding merged yet); not accepted by the user.
