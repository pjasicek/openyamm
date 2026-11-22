# Xeen sand worms (Sand Worm, Great Worm), 2026-11-20

Lane S project (parent session `xeen-s6`, sub-agent `xeen-s6-sandworm`, identity `xeen:sandworm`). Rows (read-only):
11440 Sand Worm (`Xeen Sand Worm A`, level 30, descriptor height 160, radius 140) and 11442 Great Worm
(`Xeen Sand Worm C`, level 45, height 190, radius 140); `Xeen Sand Worm B` is the Armadillo, another model. Ground
walkers, melee only. Native art: Clouds image 56 (`sprites/xeen/056.mon`: the worm rising out of a sand mound,
`056.att`: bent forward, the round maw toward the viewer). Built with the [quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md)
main route (snakes and segmented-creature sections), [HD masters](../CLAUDE_HD_MASTER_REFERENCES.md),
[creature textures](../CLAUDE_CREATURE_TEXTURES.md), the [texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md)
and the [LOD playbook](../LOD_PLAYBOOK.md); scripts adapted from `xeen_electrapede_claude/` and `xeen_mole_claude/`.

**State: installed** (`tools/install_model.py --world xeen`), checked in the review viewer and in game (static model
spawns in XD-21). The binding is **not** merged (the parent owns `actors.yml`): the ready block for `Xeen Sand Worm A`
and `C` is [integration/actors.yml](integration/actors.yml). Not accepted by the user. **Meshy: 15 of 30 credits.**

## Deliverables

| File | What |
|---|---|
| `assets_source/worlds/xeen/models/xeen_sandworm.glb` | installed source = `export/xeen_sandworm.glb`; cooked runtime copy in `assets_dev/worlds/xeen/models/` |
| `integration/actors.yml` | bindings for `Xeen Sand Worm A` (skin `sandworm_a`, scale 110) and `Xeen Sand Worm C` (skin `sandworm_c`, scale 126.5), impact 0.567 s |
| `work/anim_v1.blend` | keyed master (rig `Worm_Rig`, mesh `Worm`); `work/anim_base.blend` the locked UV layout; `work/rig_v1.blend`, `work/clean_v2.blend` before |
| `references_hd/` | the five Codex masters (1024x1536 portrait; `00` the worm alone for Smart Topology, `01`-`04` with the sand mound for the retexture), `CODEX_BRIEF.md`, `generation_runs.json`, `codex_run*.log`, `selected_views_review.png` |
| `native/` | original frames `mon_0000..0007`, `att_0000..0003` with `*_frames.json`; `sheet_codex.png` (Codex input) |
| `textures/` | `worm_basecolor_graded.png` (2K), `worm_normal_1k`, `worm_mr_1k` (R AO, G roughness, B 0), `worm_region_mask.png` (R skin, G spikes, B gums, A sand mound), `worm_ramps.json`, `worm_material_classes.png` (1 skin, 4 spike, 5 fang, 7 gums and gullet, 11 sand and rock = other), `worm_ao_2k.png` |
| `review/` | `textured_sheet.png` (EEVEE at party eye height, both skins), `clips_fq.png`, `clips_side.png` (clay clip sheets), `raw_sheet.png`, `prep_sheet.png`, `clean_sheet.png`, `region_classes.png`, `texture_quality.json`, `uv_quality_upload.json`, `lod_scores_r25_12.tsv`, `viewer_shots.png`, `shots/`, `ingame/` |
| `review/viewer/` | review viewer: two tier GLBs (ramps baked for three.js), every clip |

## Mesh

Meshy Smart Topology v1 (meshy-t2, 15k, from `00_three_quarter.png`): 15,635 triangles in 50 pieces, the maw turned to
-Y and scaled to 1.15 m (`scripts/prep.py`): **six separate ring shells** (the top one the head with an open maw
funnel), 33 thorn spikes and 11 fangs, all separate pieces. `scripts/clean.py` (rules, not indices): the rings' small
holes filled; decimation per class (rings 0.45, head 0.55, spikes 0.40, fangs 0.50); then the **procedural sand
mound** (`scripts/mound.py`): an open lumpy heap 1.85x the worm's base radius (0.48 m), 0.10 m high at the axis and
0.08 m where it meets the lowest ring, no bottom (the floor hides it), and eleven angular rock slabs (convex hulls)
on its slope and rim. **8,396 triangles** (rings 3,114, head 1,002, spikes 2,060, fangs 824, mound 1,104, rocks 292).
Face attributes `part` (0 ring, 1 head, 2 spike, 3 fang, 4 mound, 5 rock) and `seg` (ring index). Rest: forward -Y,
1.157 m from the floor to the top spike, ring diameter 0.52 m, the maw tilted 35 degrees forward (rim radius 0.126 m).

## Rig (`scripts/rig.py`)

`Root` > `Ring0` > `Ring1` > `Ring2` > `Ring3` > `Ring4` > `Head` (on the axis through the creases between the shells);
`Head` > `Lip0..Lip5` (six points on the maw rim, Y along the maw normal, Z radial); `Root` > `Lobe0..Lobe5` (six mound
lobes, 60 degrees apart, Lobe0 in front). 19 bones. Weights: shells by piece, blended with the neighbouring shell
where they touch (smoothstep over 3.5 cm of distance to it, 50/50 at contact), so bends keep the creases closed;
spikes rigid on their ring; the maw region of the head shared among the lips by angle (cos^2) with a radial influence
(0 in the gullet, 1 at the rim, 0 at 1.7 rims), fangs rigid on their nearest lip; the mound by angle among the lobes
with a radial influence (1 inside the worm's base, 0 at 0.92 of the rim, the rest on Root, so the rim never leaves the
floor), each rock rigid with the mound weights under it. 0 unweighted vertices. The maw opens by moving the lips out
3 cm and tilting them out 28 degrees (the fangs flare); the worm sinks by **uniform scale** of the lower ring bones
(joints carry uniform scale only), which telescopes them inside the mound; the mound grows and ripples by lobe
translation only.

## Clips (`scripts/anim.py`, 30 fps, procedural)

Every frame: the chain is laid out from the floor joint (each ring its rest length times its scale, pitch/side/twist
accumulated up the chain); floor rule on the evaluated mesh (the body is lifted when it sinks); the corpse is solved
down onto the floor (its droop grows until the lying rings touch).

| Clip | Length | What | Event |
|---|---|---|---|
| Standing | 2.4 s loop | upright out of its mound, slow sway travelling up the rings, maw slowly opening and closing, mound breathing (native mon 4-5) | |
| Walking | 1.0 s loop | sunk into a travelling mound (rings 0-2 shrunk to 0.32/0.42/0.58 inside it, the mound centre raised 11 cm), upper rings and maw above, the hump ploughing (front higher) and rippling front to back, body undulating | |
| Running | 0.6 s loop | sunk deeper (rings 0-3), mound 15 cm, leaning 12 degrees forward, faster ripple | |
| Attack | 1.2 s | rears back (maw up and opening), lunges forward-down bent over toward the party with the maw wide open facing forward (att 1-2), snaps shut, recovers | **impact 0.567 s** (frame 17: the maw furthest forward, wide open) |
| Hit | 0.5 s | recoils back and aside, maw clenched | |
| Death | 1.6 s | writhes with the maw gaping, the lower rings sink into the mound, topples forward-left onto the floor | |
| Dead | 1.0 s | Death's last pose: slumped half out of the mound, head and upper rings on the floor | |
| Fidget | 2.0 s | sinks partly into the mound and rises again, maw flexing wide then snapping | |

No cast and no missile on the rows: `cast: Attack`, `attack_ranged: Attack`.

### Gates

`scripts/clip_gates.py export/xeen_sandworm.glb 110` (largest per-frame vertex step, second difference, loop seam,
lowest point in world units at scale 110):

| Clip | Step cm | Accel cm/f² | Seam cm | Lowest units |
|---|---|---|---|---|
| Standing | 0.64 | 0.62 | 0.00 | -0.33 |
| Walking | 1.31 | 0.35 | 0.00 | -0.16 |
| Running | 2.11 | 0.93 | 0.00 | -0.17 |
| Attack | 28.96 | 16.02 | 0.00 | -0.04 |
| Hit | 16.76 | 11.88 | 0.00 | -0.04 |
| Death | 10.98 | 6.44 | (one-shot) | -0.15 |
| Dead | 0.00 | 0.00 | 0.00 | +0.11 |
| Fidget | 3.56 | 1.61 | 0.00 | -0.33 |

The Attack's 29 cm step is the lunge (the maw 1 m up the chain swings from the rear-up to the strike in 0.16 s),
intended. Floor audit (`floor_audit.audit` with this binding block on the export): **Xeen Sand Worm A: ground,
standing -0.33..0.00, walking -0.16..-0.04, living lowest -0.33, corpse +0.11 world units; C: -0.38..0.00,
-0.18..-0.05, -0.38, +0.13; no problems** (tolerance 2.5). The mound rests on the floor in every clip (lowest mound
vertex +1 mm).

## Textures

UVs (`scripts/uv.py`, `uv_atlas.unwrap` defaults, Head and the lips 1.5x denser): PartUV charts, seam pass, sparrow
packing, **no fallback**. Meshy `retexture_v1` (meshy-7, 4K, PBR, original UVs; views 01, 03, 02, 04, the mound shown
in the views) returned the same layout. Quality (`texture_quality.py export/xeen_sandworm.glb`): **atlas 76.5 %,
density p10/p50/p90 796/902/1297 (spread 1.63: the head ring and maw are meant to be 1.5x denser), 95 islands,
fragments 0.0 %, stretch p90 1.14**.

`scripts/compose.py`: colour 4K -> 2K once (Lanczos), normal and ORM to 1K; classes from geometry (rings, head,
spikes, fangs, mound, rocks) and inside the maw (the rig's maw frame) from the paint (red gums; dark texels deep in the
funnel = gullet). Gentle grade (`--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15`),
`gutter_fill.py` last on every map. Roughness: skin 0.6-0.92, spikes 0.35-0.6, fangs 0.35-0.55, gums 0.35-0.6, sand
0.8-0.98; specular 0, metallic 0 (binding extras).

Skins (`scripts/tier_ramps.py`, `textures/worm_ramps.json`), fit error mean / p95 in 8-bit levels:

| Skin | Monster | Skin region | Spikes | Gums | Sand mound | Fit (skin / spikes / gums / sand) |
|---|---|---|---|---|---|---|
| `sandworm_a` | Sand Worm | native orange-ochre (056 pixels hue 28-40, median 132,68,0; texel luminance x1.2 of the native mean) | native grey steel | native red | the paint (identity) | 1.69/7.8, 0.04/0.02, 1.90/8.4, 4.3/16.1 |
| `sandworm_c` | Great Worm | deep rust-red / umber (A's target at hue 9, saturation x0.95, value x0.62) | near-black steel (value x0.32) | darker crimson (hue 352, value x0.62) | the same paint | 1.52/5.8, 0.26/1.05, 0.94/3.3, 4.3/16.1 |

Xeen draws both worms with one sprite, so C is a design recolour (D-10: the whole body tiers): the bigger, higher-level
worm reads as an older, darker, blood-rust animal next to the bright orange Sand Worm at combat distance, without
leaving the desert family. The fangs, the black gullet and the rock slabs are in no region and keep their paint on
both skins (one luminance ramp turned the pink-brown rocks tan: they were taken out of the sand region, whose fit then
fell from 7.1/26.6 to 4.3/16.1).

## LODs

**8,396 / 4,197 / 2,096 / 1,030** (LOD1 `tools/build_actor_lods.py` through `scripts/lods_wrap.py`; LOD2/3 the
`repair.py` ladder in the project copy `lodrepair/`, first step **r25_12** accepted: LOD2 outline 2.7 % colour 7.1,
LOD3 4.2 % / 6.5, `review/lod_scores_r25_12.tsv`). `verify_far_only` OK; shadow LODs tucked up to 15 mm. Shadow check
(`audit_mm678_20261111/lod_audit/shadow_check.py 126.5`, the larger tier): at most 4.1 % of the LOD3 shadow more than
1 unit outside LOD0 (under the 5 % look-in-game line). `lodrepair/work/worm/xeen_sandworm/` keeps `r25_12.built.glb`
and `bake_r25_12/` for map-only reruns.

## Binding (integration/actors.yml)

Scale **110** for the Sand Worm: the native standing frame (056.mon frame 5, worm with its mound, flying shards left
out) is 94 px = 126 units tall at the Xeen bindings' 1.34 units/px, against the model's 1.157 m (109); the silhouette
area gives 133 and the width 97 (`scripts/scale_measure.py`: the model's mound is broader than the sprite's), so the
height decides. **Great Worm 126.5** (1.15x, no `scale_reference`). Standing heights (floor to the top spike):
**Sand Worm 127 units, Great Worm 146 units** (maw centre 112 / 129); walking (sunk) maw centre 81 / 93 units; the
mound 1.18 m wide = 130 / 149 units. `yaw_offset -pi/2`, `cast: Attack`, `run: Running`, `stride_length 1.0`,
`run_stride_length 1.5` (no feet: the rates only pace the ripple), `upper_body_root: Ring3`, look on `Head` (30/20
degrees), `sockets: {}`, `events.attack_melee.impact 0.567`.

## Checks

- Winding: 0 inverted closed parts. Installed with `tools/install_model.py --world xeen` (cooked runtime copy).
- Viewer: `python3 tools/run_creature_review.py --project level_generation/creatures/xeen_sandworm_claude check`:
  16 switches (2 skins x 8 clips), no console errors (served by `python3 -m http.server 8912 --bind 127.0.0.1` from
  the repo root); shots in `review/shots/`, sheet `review/viewer_shots.png`.
- Renders: `review/textured_sheet.png` (EEVEE, party eye height 1.60 model m = 176 units, 3.0 m away; both skins).
- In game: `review/ingame/` (XD-21, `build-xeen/game/openyamm` of 2026-11-20 22:38, `model spawn` of the installed GLB
  at scale 110 yaw pi: Standing, the blow at 0.567 s, Walking, the wind-up, Dead, forced LOD 2 and 3; tier A only:
  the console cannot pick a skin and the descriptors still bind the stand-in, so C is seen in the viewer and EEVEE
  renders); `review/ingame/tour.yml` has the command. Exit 0, no load errors.

## Meshy credits: 15 of 30

| Job | Kind | Credits | Task |
|---|---|---|---|
| `smart_topology_v1` | image-to-3d, meshy-t2 smart-topology 15k, no texture, from `references_hd/00_three_quarter.png` | 5 | `01a1fac6-94d3-7294-93d3-e8ae6ba5243c` (primary) |
| `retexture_v1` | retexture, meshy-7, 4K, PBR, original UVs (`texturing/worm_upload.glb`), views 01, 03, 02, 04 | 10 | `01a1fad6-8119-7497-bcf1-bb23ed386756` (primary) |

## Rebuild

```sh
TOK=<lease>; cd level_generation/creatures/xeen_sandworm_claude
TOK=$TOK scripts/step.sh inspect_raw.py; TOK=$TOK scripts/step.sh prep.py; TOK=$TOK scripts/step.sh clean.py
TOK=$TOK scripts/step.sh rig.py
# uv.py refuses to run once texturing/worm_upload.glb exists (the paint belongs to that layout)
TOK=$TOK scripts/step.sh anim.py                 # [clip ...] reruns only those clips on work/anim_v1.blend;
                                                 # anim.py rig_v1.blend preview.blend keys a preview on the rig
TOK=$TOK scripts/step.sh dump_uv3d.py; TOK=$TOK scripts/step.sh bake_ao.py     # only after a layout change
TOK=$TOK scripts/build_runtime.sh [--install]    # compose, grade, gutter fill, ramps, export, LODs, skins, far LODs
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
python3 scripts/clip_gates.py export/xeen_sandworm.glb 110; python3 scripts/scale_measure.py export/xeen_sandworm.glb
python3 ../claude_shared/tier_textures.py textures/worm_basecolor_graded.png textures/worm_region_mask.png \
  textures/worm_ramps.json work/tier_worm && TOK=$TOK scripts/step.sh render_textured.py
```

`scripts/step.sh` takes the lane's Blender lock (`xeen_tiers_claude/bin/.blender.lock`). Clay sheets:
`clip_sheet.py <n> fq|side|quarter all [blend]` + `sheet_join.py <out.png>`; `dump_raw.py` + `pieces.py` list pieces.

## Known limits

- The mound is procedural geometry painted by Meshy's retexture (from the masters' mound); its rocks are rigid slabs
  that ride the mound lobes. No flying rock shards (the native emerge frames throw some).
- Burrowing is faked: Walking/Running shrink the lower rings uniformly inside a raised mound; from very low cameras a
  narrower neck may show between the mound and the first full-size ring during the walk ripple.
- Hidden geometry costs atlas: the interpenetrating ring caps and the inside of the lowest ring take a share of the
  layout (Meshy's shells overlap).
- In a dim dungeon (XD-21) the orange reads brownish; outdoors (X6 desert) it should read as the sprite's orange.
  The Great Worm skin is not seen in game yet (binding not merged).
- `level_generation/update_gitignore.py` was run as AGENTS.md asks; its only listing is another project's file
  (`/sounds/xeen_20261120/picks.yml`, already noted by the electrapede run); nothing of this project needed listing.
- Not accepted by the user.
