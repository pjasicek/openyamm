# Xeen moles (Tiger Mole, Rock Mole, Tunnel Mole), 2026-11-20

Lane S project (parent session `xeen-s3`; HD masters by `xeen-s3`, everything after them by the sub-agent
`xeen-s3-mole`; identity `xeen:mole`). Rows: the `burrowers` family in `assets_dev/worlds/xeen/source/monsters.yml`
(block 11430): A Tiger Mole (level 6), B Rock Mole (9, earth +20), C Tunnel Mole (12, BrkArmor, earth +20). Ground
walkers (no fly). Xeen draws one sprite (image 11, `sprites/xeen/011.mon`, `011.att`) for all three. Built with the
[quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md) main route (Meshy model, own rig with automatic weights,
procedural clips with floor rules), [HD masters](../CLAUDE_HD_MASTER_REFERENCES.md),
[creature textures](../CLAUDE_CREATURE_TEXTURES.md), the [texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md)
and the [LOD playbook](../LOD_PLAYBOOK.md).

**State: installed** (`tools/install_model.py --world xeen`), checked in the review viewer and in game (static model
spawns in XD-21). The binding is **not** merged (the parent owns `actors.yml`): the ready block for `Xeen Mole A/B/C`
is [integration/actors.yml](integration/actors.yml). Not accepted by the user. **Meshy: 15 of 30 credits.**

## Deliverables

| File | What |
|---|---|
| `assets_source/worlds/xeen/models/xeen_mole.glb` (sha256 `b015ad68…`) | installed source = `export/xeen_mole.glb`; cooked runtime copy in `assets_dev/worlds/xeen/models/` (`be77bf66…`) |
| `integration/actors.yml` | the bindings for `Xeen Mole A/B/C` (skins `mole_a/b/c`, scale 145, impact 0.47 s) |
| `work/anim_v1.blend` | keyed master (rig `Mole_Rig`, mesh `Mole`); `work/anim_base.blend` is the locked UV layout, `work/rig_v1.blend` the rig before UVs |
| `references_hd/` | the five Codex masters (1536x1024), `CODEX_BRIEF.md`, `generation_runs.json`, `codex_run1/2.log`, `selected_views_review.png` |
| `native/` | original frames `mon_0000..0007`, `att_0000..0003` with `*_frames.json`; `sheet_codex.png` (Codex input) |
| `textures/` | `mole_basecolor_graded.png` (2K), `mole_normal_1k`, `mole_mr_1k` (R AO, G roughness, B 0), `mole_region_mask.png` (R fur, G skin, B claws, A tail), `mole_ramps.json`, `mole_material_classes.png` (1 skin, 2 fur, 4 claw, 6 eye), `mole_ao_2k.png` |
| `review/` | `textured_sheet.png` (EEVEE at party eye height: front, quarter, side, wind-up, blow, dig, walk, hit, corpse, face, tiers B/C, back), `clips_quarter.png`, `clips_side.png` (clay clip sheets), `tiers_abc.png`, `stress_sheet.png`, `weights_sheet.png`, `curl_sheet.png`, `raw_sheet.png`, `pieces_sheet.png`, `region_classes.png`, `texture_quality.json`, `uv_quality_upload.json`, `lod_scores_r25_12.tsv`, `viewer_shots.png`, `ingame/` |
| `review/viewer/` | review viewer: three tier GLBs (ramps baked for three.js), every clip |

## Mesh

Meshy Smart Topology v1 (meshy-t2, 15k, from `00_three_quarter.png`): 14,706 triangles in **449 pieces**. Piece 0 is
a clean closed body with head, snout and both five-clawed hands (9 boundary edges); piece 1 a hidden inner shell; about
430 loose fur shingle plates laid over the body; two side tails (Meshy mirrored the master's single curved tail);
two eyeballs with front caps; eight tiny hind toe claws. `scripts/clean.py` keeps the body (hole filled), the eyes and
the hind claws (decimated to 45 %), drops the inner shell, the shingles (the fur is paint) and both tails, and adds
one centred procedural tail (8-sided tapered tube on a Catmull-Rom centreline rising behind the rump, as in
`02_back`). **7,812 triangles**, no further reduction (most of them are in the claws). Face attribute `part`: 0 body,
1 eyes, 2 hind claws, 3 tail. Rest: forward -Y, 1.40 m snout to rump, 1.27 m hand to hand, 0.63 m to the top of the
back once grounded.

## Rig (`scripts/rig_mole.py`)

`Body` (root at the hips) > `Spine` > `Chest` > `Head` > `Snout`; `Tail1..4` (from Body); per side `UpperArm` >
`ForeArm` > `Hand` > `Claws` (from Chest) and `Thigh` > `HindFoot` (from Body). Joints from mesh numbers
(`scripts/dump_mesh.py` slices, `zoom_views.py`). Blender heat weights on the trunk and limbs, then: each hand
(everything past the wrist plane at |x| > 0.24 below z 0.30) is **wholly on Hand/Claws** (Claws ramps in over the
knuckles, so all five claws curl together and never take a head or forearm weight; blended into the heat weights over
4 cm at the wrist); eyes rigid on Head; hind toe claws rigid on HindFoot; the tail on Tail1..4 by arc position.
0 unweighted vertices; stress poses (`review/stress_sheet.png`: swipe, paddle, rear, roll, turn) show no tearing.
Claw curl: negative local X curls the claws down into a grip (`review/curl_sheet.png`); positive bends them back and
shears the knuckles, so splays stay above -12 degrees.

## Clips (`scripts/anim_mole.py`, 30 fps, procedural)

Every frame: the core (trunk, head, snout, thighs) is lifted if it sinks; a hand or hind foot whose vertices dip under
the floor gets its IK target raised; the tail bends up segment by segment until it clears. The bind pose stands 3.4 cm
high on its claw tips (the dropped shingles reached lower), so every clip lowers the root by that amount.

| Clip | Length | What | Event |
|---|---|---|---|
| Standing | 2.0 s loop | breathing heave, snout twitches, head drift, tail sway (native idle) | |
| Walking | 0.8 s loop | paddle gait (LF+RH / RF+LH): the spade hands reach, stroke back and out like a swimmer, swing forward close to the body; hind feet short steps; 0.60 m per cycle | |
| Running | 0.5 s loop | the same, longer, lower and faster, 4 degrees nose-down; 0.95 m per cycle | |
| Attack | 1.0 s | rears, both claws raised and splayed back (native att 1, the left leading), thrown forward and down at the party (att 2), dig in (att 3), recover | **impact 0.47 s** (frame 14: the claw tips land, furthest forward) |
| Hit | 0.5 s | jolts back, head and snout up, hands flinch | |
| Death | 1.5 s | rears in pain, rolls onto its right side, upper arm folds against the chest, claws curl | |
| Dead | 1.0 s | Death's last pose: on its right side on the floor | |
| Fidget | 2.0 s | digs: left then right hand scrape the ground, snout sniffs | |

No cast and no missile on the rows: `cast: Attack`, `attack_ranged: Attack`.

### Gates

`scripts/clip_gates.py export/xeen_mole.glb 145` (largest per-frame vertex step, second difference, loop seam, lowest
point in world units at scale 145):

| Clip | Step cm | Accel cm/f² | Seam cm | Lowest units |
|---|---|---|---|---|
| Standing | 1.13 | 0.76 | 0.00 | +0.30 |
| Walking | 9.76 | 9.88 | 0.00 | -0.56 |
| Running | 11.78 | 10.48 | 0.00 | +0.15 |
| Attack | 24.68 | 17.15 | (one-shot) | -0.62 |
| Hit | 12.91 | 11.72 | | -0.25 |
| Death | 10.35 | 12.59 | | -0.75 |
| Dead | 0.00 | 0.00 | 0.00 | -0.14 |
| Fidget | 9.82 | 5.39 | | -0.35 |

The Attack's 24.7 cm step is the claw lash over frames 11-13 (wind-up peak frame 10, landing frame 14), intended. A
first version had a 32 cm one-frame drop of the left hand in the wind-up: `keyed()` read a per-side key (`l_up`)
missing from the neighbouring key as 0 instead of the shared `up`; fixed (missing per-side keys take the shared value).

Floor audit (`floor_audit.audit` with this binding block on the export; the world's `actors.yml` still binds the
stand-in): **Xeen Mole A, B, C: ground, standing +0.30..+0.98, walking -0.56..+1.84, living lowest -0.62, corpse
-0.14 world units, no problems** (tolerance 2.5).

## Textures

UVs (`scripts/uv_mole.py`, `uv_atlas.unwrap` defaults, head and snout 1.6x denser): PartUV charts, seam pass, sparrow
packing, **no fallback**. Meshy `retexture_v1` (meshy-7, 4K, PBR, original UVs; views 01, 03, 02, 04) returned the same
layout. Quality (`texture_quality.py export/xeen_mole.glb`): **atlas 74.7 %, density p10/p50/p90 1456/1547/1683
(spread 1.16), 43 islands, fragments 0.0 %, stretch p90 1.20**.

`scripts/compose_mole.py`: colour 4K -> 2K once (Lanczos), normal and ORM to 1K, region classes from the paint's hue
limited by geometry (teal fur; yellow-olive claws only on the hand/claw bones and the hind claw pieces; pale
pink-grey skin; red irises only on the eyeball pieces and the head; the tail piece wholly A). Hair highlights are pale,
so a texel counts as fur where most of its neighbourhood is (sigma 3 texels). The eyeballs and the pink nose tip are in
no region and keep their paint in every tier. Gentle grade (`--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06
--saturation 1.15`), `gutter_fill.py` last on every map. Roughness: fur and skin 0.6-0.95, claws 0.4-0.75, eyes 0.25;
specular 0, metallic 0 (binding extras).

Tiers (`scripts/tier_ramps.py`, `textures/mole_ramps.json`): only A is native (one Xeen sprite); B and C are design
recolours that read apart at combat distance (D-10), HSV per region with the texel's value detail kept, then the
shader's ramp fitted. Fit error mean / p95 in 8-bit levels:

| Skin | Monster | Fur | Skin | Claws | Tail | Fit (fur / skin / claws / tail) |
|---|---|---|---|---|---|---|
| `mole_a` | Tiger Mole | native teal-blue, x1.3 toward the sprite's albedo (native fur median 32,80,88, paint 24,71,75) | pale pink-grey x1.15 | yellow-olive | grey-blue | 3.3/11.9, 3.0/8.8, 2.9/10.3, 1.5/4.7 |
| `mole_b` | Rock Mole | stone grey-brown (hue 34, sat x0.42, value x1.65) | greyer | dull ochre | grey | 2.9/7.6, 2.6/7.9, 2.0/5.1, 1.0/2.7 |
| `mole_c` | Tunnel Mole | dark earth-brown (hue 27, sat x0.72) | dusky | dark horn-brown | dark grey-brown | 2.4/6.9, 2.9/7.5, 1.5/4.2, 0.8/1.9 |

## LODs

**7,812 / 3,906 / 1,944 / 975** (LOD1 `tools/build_actor_lods.py` through `scripts/lods_wrap.py`; LOD2/3 the
`repair.py` ladder in the project copy `lodrepair/` (the guardian's adapted copy), first step **r25_12** accepted:
LOD2 outline 1.7 % colour 5.1, LOD3 3.3 % / 4.1, `review/lod_scores_r25_12.tsv`); `verify_far_only` OK; shadow LODs
tucked 9-15 mm. Shadow check (`audit_mm678_20261111/lod_audit/shadow_check.py 145`): at most 0.35 % of the LOD3
shadow more than 1 unit outside any colour level. `lodrepair/work/mole/xeen_mole/` keeps `r25_12.built.glb` and
`bake_r25_12/` for map-only reruns.

## Binding (integration/actors.yml)

Scale **145** world units per model metre: the front silhouette area of `mon_0000` without the dirt mound (5,763 px at
the Xeen bindings' 1.34 units/px) against the model's front silhouette (0.458 m²) gives 150, the height 160, the hand
span 113 (the model's hands splay wider than the sprite's); 0.63 m -> 92 units tall, 203 units long. `yaw_offset
-pi/2`, `cast: Attack`, `run: Running`, `stride_length 0.6`, `run_stride_length 0.95`, `upper_body_root: Chest`, look
on `Head` (30/20 degrees), `sockets: {}`, `events.attack_melee.impact 0.47`. **No `scale_reference`**: Xeen draws all
three moles at one size, and the descriptors' standing sprites are still the rat stand-in's (`ratsta` 0.8, `rbtsta`
0.9, `rctsta` 1.0), which would make B 1.125x and C 1.25x. Add `scale_reference: Xeen Mole A` if growing tiers are
wanted. The descriptor collision rows (Height 77/107/59, Radius 40) are the rat's too.

## Checks

- Winding: 0 inverted closed parts. Installed with `tools/install_model.py --world xeen` (cooked runtime copy).
- Viewer: `python3 tools/run_creature_review.py --project level_generation/creatures/xeen_mole_claude check`: 24
  switches (3 tiers x 8 clips), no console errors (served by `python3 -m http.server 8912 --bind 127.0.0.1` from the
  repo root); shots in `review/shots/`, sheet `review/viewer_shots.png`.
- Renders: `review/textured_sheet.png` (EEVEE, party eye height 1.21 model m = 176 units, 2.6 m away).
- In game: `review/ingame/` (XD-21, `build-xeen/game/openyamm` of 2026-11-20 17:10, `model spawn` of the installed
  GLB at scale 145 yaw pi: Standing, the blow, the wind-up, Dead, forced LOD 2 and 3; tier A only, the default
  variant); `review/ingame/tour.yml` has the command. Exit 0.

## Meshy credits: 15 of 30

| Job | Kind | Credits | Task |
|---|---|---|---|
| `smart_topology_v1` | image-to-3d, meshy-t2 smart-topology 15k, no texture | 5 | `01a1f9aa-e1e5-7050-9afb-4243b1ac5a27` (primary) |
| `retexture_v1` | retexture, meshy-7, 4K, PBR, original UVs | 10 | `01a1f9b6-0ee2-7416-8afc-b402277abddf` (primary) |

## Rebuild

```sh
TOK=<lease>; cd level_generation/creatures/xeen_mole_claude
TOK=$TOK scripts/step.sh inspect_raw.py; TOK=$TOK scripts/step.sh prep.py; TOK=$TOK scripts/step.sh clean.py
TOK=$TOK scripts/step.sh dump_mesh.py clean_v2.blend mesh_v2; TOK=$TOK scripts/step.sh rig_mole.py
# uv_mole.py refuses to run once texturing/mole_upload.glb exists (the paint belongs to that layout)
TOK=$TOK scripts/step.sh anim_mole.py            # [clip ...] reruns only those clips on work/anim_v1.blend
TOK=$TOK scripts/step.sh dump_uv3d.py; TOK=$TOK scripts/step.sh bake_ao.py     # only after a layout change
TOK=$TOK scripts/build_runtime.sh [--install]    # compose, grade, gutter fill, ramps, export, LODs, skins, far LODs
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
python3 scripts/clip_gates.py export/xeen_mole.glb 145
python3 ../claude_shared/tier_textures.py textures/mole_basecolor_graded.png textures/mole_region_mask.png \
  textures/mole_ramps.json work/tier_mole && TOK=$TOK scripts/step.sh tier_views.py && TOK=$TOK scripts/step.sh render_textured.py
```

Mesh and rig sheets: `piece_views.py`, `grid_views.py`, `zoom_views.py`, `weight_views.py`, `stress.py`,
`curl_test.py`, `clip_sheet.py 7 quarter|side` + `sheet_join.py`.

## Known limits

- The fur is paint on a smooth body: the silhouette lacks the sprite's shaggy outline (Meshy's fur shingles were
  loose plates; the creature edge darkening gives the dark rim).
- Hind legs are short stubs under the rump: in Walking/Running the hind toe claws slide a little (leg reach about 7 cm
  against a 0.6 m stride); mostly hidden under the body.
- The front arms are short: at the far end of the stroke the wrist targets are beyond reach and the hands trail a
  few centimetres (IK clamps).
- B and C are design colours (Xeen has one mole palette); the B skin reads light in the bright viewer, stone grey-brown
  in EEVEE and dim rooms.
- Seen in game only as debug-spawned models of tier A (no binding merged yet); not accepted by the user.
