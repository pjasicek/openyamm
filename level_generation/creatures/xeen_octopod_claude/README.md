# Xeen octopods (Octopod, Great Octopod, Kraken), 2026-11-21

Lane S project (parent session `xeen-s7`, sub-agent `xeen-s7-octopod`, identity `xeen:octopod`). Rows (read-only):
11470 Octopod (`Xeen Octopod A`, level 50), 11471 Great Octopod (`B`, 60), 11472 Kraken (`C`, 70): MM9 swimmers in
D4's lake (`modifiers.yml`: `mm9_ai archetype swimmer, movement swim`, Fly Y), melee only (Water); 11473 Octopod
(`D`, D-52): A's look, stationary (`stand`), no swimmer AI, in DD-14's cistern. Descriptors: height 120, radius 50.
Native art: Darkside image 41 (`sprites/dark/041.mon` 8 frames: red domed head, blue eyes under a stern brow, tentacles
with yellow suckers rising out of the lake; `041.att` 4 frames: a purple ink burst from under the face, then the head
ducks under its tentacles). Built with the [quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md) (water creatures;
segmented creatures), [HD masters](../CLAUDE_HD_MASTER_REFERENCES.md), [creature textures](../CLAUDE_CREATURE_TEXTURES.md),
the [texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [LOD playbook](../LOD_PLAYBOOK.md);
scripts adapted from `xeen_sandworm_claude/` (and its `lodrepair/` copy), the foam ring from `mm6_seas_claude/`.

**State: installed** (`tools/install_model.py --world xeen`), checked in the review viewer, EEVEE renders and in game
(D4's lake and DD-14's cistern, with the bindings through a private extra mount). The binding is **not** merged (the
parent owns `actors.yml`): the ready block for `Xeen Octopod A/B/C/D` is [integration/actors.yml](integration/actors.yml).
Not accepted by the user. **Meshy: 15 of 30 credits.**

## Deliverables

| File | What |
|---|---|
| `assets_source/worlds/xeen/models/xeen_octopod.glb` (sha256 `7551e04e…`) | installed source = `export/xeen_octopod.glb`; cooked runtime copy in `assets_dev/worlds/xeen/models/` (`f26640bb…`) |
| `integration/actors.yml` | bindings `Xeen Octopod A` (skin `octopod_a`, scale 135), `B` (`octopod_b`, 155.25), `C` (`octopod_c`, 175.5), `D` (`octopod_a`, 135, same model and origin); impact 0.533 s; purple melee glow at `Socket_Siphon` |
| `work/anim_v1.blend` | keyed master (rig `Octopod_Rig`, mesh `Octopod` + foam ring in material slot 1); `work/anim_base.blend` the locked UV layout + foam; `work/rig_v1.blend` (rig, no UVs), `work/clean_v1.blend` (cleaned mesh); `work/rig_v1.json` (joints, weights) |
| `references_hd/` | the five Codex masters (1536x1024; `00` from run 1b, the run-1 primary and rejected drafts in `raw/`), `CODEX_BRIEF.md`, `generation_runs*.json`, `codex_run*.log`, `selected_views_review.png` (with the native sheet) |
| `native/` | original frames `mon_0000..0007`, `att_0000..0003`, `*_frames.json`; `sheet_codex.png` (Codex input), `contact_3x.png` |
| `textures/` | `octopod_basecolor_graded.png` (2K), `octopod_normal_1k`, `octopod_mr_1k` (R AO, G roughness, B 0), `octopod_region_mask.png` (R skin, G suckers, B irises), `octopod_ramps.json`, `octopod_material_classes.png` (1 skin, 4 sucker, 6 eye), `octopod_ao_2k.png`, `foam.png` (512, the MM6 sea serpent's Codex foam ring) |
| `review/` | `textured_sheet.png` (EEVEE over a dark lake plane: front, quarter, side, wind-up, blow, walk, run, hit, death, dead, face close-up, back, fidget, tier B and C), `clips_fq.png`, `clips_front.png` (clay clip sheets with a water plane), `raw_sheet.png`, `pieces_sheet.png`, `clean_sheet.png`, `region_classes.png`, `clip_gates.txt`, `floor_audit.json/.txt`, `texture_quality.json`, `uv_quality_upload.json`, `lod_scores_r25_12.tsv`, `shadow_check.txt`, `ingame/` |
| `review/viewer/` | review viewer: three tier GLBs (ramps baked for three.js), every clip |

## Mesh

Meshy Smart Topology v1 (meshy-t2, 15k, from `00_three_quarter.png`): 14,821 triangles in 133 pieces: the body (head
dome and eight tentacles in a flat star, one tentacle under the face, the face looking along -Y within 0.5 degrees),
two eyeballs of different sizes, 130 sucker blobs and a five-face sliver strip. `scripts/clean.py` (rules, not
indices): sliver faces (an edge over 0.06 raw units, median 0.012) removed and their holes filled; both eyeballs
replaced by one mirrored pair of UV spheres set into the head surface; the tentacles lengthened 1.35x along their own
axes beyond the head (smooth ramp; Meshy's star spans 3.1 head widths tip to tip, the sprite's 4.8), each sucker moving
rigidly with the body point under it; suckers decimated to about a third; scaled to a 0.60 m head; **z 0 = the
waterline**, 0.33 head widths under the eye centres as in the native frames. **9,587 triangles** (body 5,848, suckers
3,167, eyes 576) + the foam ring 384. Face attribute `part`: 0 body, 1 sucker, 2 eye, 3 foam. Rest: forward -Y, head
0.47 m above the waterline, star 2.24 m across.

## Rig (`scripts/joints.py`, `scripts/rig.py`)

69 bones. `Root` (the waterline; Death sinks it) > `Body` (hub at the head base: bob, pitch, roll) > `Head` (dome,
eyes, brow, beard) > `Socket_Siphon` (non-deform, in front of the beard: the ink glow); `Body` > `Arm<k>_1..8` for the
eight tentacles k = 0..7 (azimuth 45k degrees from the front, + toward +X = the creature's left; every bone's local X its
tentacle's plane normal); `FoamRoot` unparented at the origin. Joints (`joints.py`, no Blender): per tentacle its
vertices (nearest axis, beyond 0.27 m along it), a geodesic distance over its own surface from a seed ring 0.30 m out,
binned into cross-section rings whose centroids trace the centreline round the hooked tip; J0 inside the head base,
then 8 bones by equal arc length (1.25-1.30 m per tentacle). Weights: tentacle vertices on their chain by arc position
(hat functions peaking at bone midpoints, two influences), eased into Body/Head over the web (0.20-0.36 m along); body
vertices off the tentacles on Head (dome, smoothstep 0.12-0.26 m high) and Body; suckers rigid on the weights of the
body vertex nearest their centre; eyes on Head; the foam ring on FoamRoot. 0 unweighted vertices.

## Clips (`scripts/anim.py`, 30 fps, procedural)

Each tentacle bone keeps its rest length and is turned from rest by a pitch change in its tentacle's plane and a yaw
about the vertical, from target profiles: ARCH (the root bones dip under the water, the middle rises in a tall arch,
the tip hooks over outward and down, as the native tentacles rise out of the lake), LOW (streaming along the surface),
SUNK (under the water), plus a wave travelling to the tip; per-tentacle height, phase and curl. The front tentacle (under
the face) stays under the water except in the attack. No floor rules (water): the measured rule is what shows above
z 0.

| Clip | Length | What | Event |
|---|---|---|---|
| Standing | 3.0 s loop | head bobbing on the water, every tentacle arching out of the water and weaving with its own phase, tips curling (native 041.mon 0-7) | |
| Walking | 1.6 s loop | swimming on the surface: the star swept back (azimuths compressed toward the rear), lower arches streaming behind, a stroke pulse per cycle, head pitched forward | |
| Running | 1.0 s loop | the same, swept further back, lower and faster | |
| Attack | 1.2 s | the front pair and the front tentacle rear up tall and back (0.30-0.42 s), lash forward and down onto the party with the head lunging, recover | **impact 0.533 s** (frame 16: the front tentacle tips furthest forward, 1.39 m out) |
| Hit | 0.5 s | the head jerks back and ducks, the tentacles flinch up and curl | |
| Death | 1.6 s | the tentacles flail, the head tips back, the whole body sinks 1.15 m under the waterline while the tentacles go limp; the foam ring shrinks away (0.6-1.3 s) | |
| Dead | 1.0 s | Death's last pose: sunk (top 0.68 m below z 0; no corpse, as the sprite) | |
| Fidget | 2.4 s | the left side tentacle rises tall and curls and uncurls its tip twice, the head turning toward it | |

No cast and no missile: `cast: Attack`, `attack_ranged: Attack`. The foam ring sways (±4-6 degrees) and pulses in every
clip (a sway, not a spin, so the loops close).

### Gates

`scripts/clip_gates.py export/xeen_octopod.glb 135` (largest per-frame vertex step, second difference, loop seam,
lowest point in world units; review/clip_gates.txt):

| Clip | Step cm | Accel cm/f² | Seam cm | Lowest units |
|---|---|---|---|---|
| Standing | 0.89 | 0.22 | 0.00 | -36.0 |
| Walking | 2.39 | 0.32 | 0.00 | -61.4 |
| Running | 4.66 | 0.97 | 0.00 | -55.6 |
| Attack | 42.43 | 25.28 | (one-shot) | -39.6 |
| Hit | 15.64 | 10.09 | (one-shot) | -47.5 |
| Death | 13.09 | 3.12 | (one-shot) | -246.9 |
| Dead | 0.00 | 0.00 | 0.00 | -246.9 |
| Fidget | 8.00 | 3.08 | (one-shot) | -35.9 |

The Attack's 42 cm step is the lash (the tentacle tips 1.3 m out sweep from the reared pose to the strike in about
four frames), intended. The negative lows are the tentacle roots and dips under the water (and the sunk corpse), by
design. Floor audit (`floor_audit.audit` on this binding block, `review/floor_audit.json`): it has no kind for these
rows (A-C have Fly Y and are judged as fliers, D as a ground walker; its swimmer kind is MM9's S cell), so it reports
"living lowest at -61 (suggested hover 0.455)", "corpse at -247" for A (B, C scaled) and "standing at -29", "sinks"
for D. **These are the waterline origin working as intended and must not be "fixed"** with `--hover`/`--ground-*`:
the origin is the water surface (below). Above the water: the head's lowest point stays 7-14 cm under the waterline in
every living clip; the front tentacle's outer joints stay 6-10 cm under it.

## Origin (D-36) and DD-14 (D-52): findings

- **Outdoors** (`game/outdoor/OutdoorWorldRuntime.cpp`): an outdoor swimmer (`isOutdoorSwimmer`: the actor's MM9 profile
  is `swimmer`) with `canFly` (the rows' Fly Y) steers its vertical move to `sampleOutdoorTerrainHeight` at its position
  every step; outdoor water is a terrain tile drawn at the terrain height, so the actor's `preciseZ` (its feet) is
  the water surface. `outdoorBodyInWater` (`Mm9ActorRules.cpp`, `OutdoorSwimDepth` 48) only decides whether a body
  counts as in water (feet within 48 above the surface over a water tile). D4's placed octopods sit at z 1056, and the
  height map there is 1056 at all four corners. The renderer draws model y 0 at `preciseZ + z_offset`
  (`WorldFxSystem`), so **root at the waterline, no `z_offset`** is right.
- **DD-14** (`xeen_dd14.blv`, room `room:cistern`, level `level:pool`): there is no water volume; the pool is a sunken
  floor at z -736 whose face *is* the water (`7wtrtyl`, the fluid attribute 0x10, `liquids.yml` `water_mm7`, opacity
  1 = opaque), 96 under the ledges (-640). The five cistern actors stand on that face (z -736). The swimmer origin
  therefore puts the waterline on the drawn surface there too; parts under it are hidden by the opaque face, and the
  sunk corpse vanishes into it. **No grounded copy and no `z_offset` are needed: `Xeen Octopod D` binds the same model,
  scale and skin as A.** (Had the pool been a water volume over a separate bed, a grounded copy raised by the depth
  would have been needed; it is not.)
- In game (below) both look right: the octopods sit in the lake and on the cistern's water with the foam on the
  surface.

## Textures

UVs (`scripts/uv.py`, `uv_atlas.unwrap` defaults, Head 1.5x denser): PartUV charts, seam pass, sparrow packing, **no
fallback**. Meshy `retexture_v1` (meshy-7, 4K, PBR, original UVs; views 01, 03, 02, 04) returned the same layout.
Quality (`texture_quality.py export/xeen_octopod.glb`): **atlas 74.1 %, density p10/p50/p90 1548/1653/1796 (spread
1.16), 185 islands, fragments 0.8 %, stretch p90 1.29** (the upload gated the same before the paint). Far LODs: LOD2
512 px, LOD3 256 px own maps.

`scripts/compose.py`: colour 4K -> 2K once (Lanczos), normal and ORM to 1K; classes from the face attribute (body,
sucker pieces, eyeballs) and the paint (the yellow sucker rings Meshy also painted on the tentacles' undersides join the
sucker region; blue irises; dark pupils out of every region; the flesh painted round the irises joins the skin). Gentle
grade (`--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15`), `gutter_fill.py` last on every map.
Roughness: skin 0.35-0.62 (wet), suckers 0.4-0.65, eyes 0.1-0.25; specular 0, metallic 0 (binding extras). The foam
ring is its own mesh node `Foam` (alpha cut-out MASK, no region, no LODs, not in the merged shadow).

Skins (`scripts/tier_ramps.py`, `textures/octopod_ramps.json`; whole-body tiers, D-10), fit error mean / p95 in 8-bit
levels:

| Skin | Monster | Skin | Suckers | Irises | Fit (skin / suckers / iris) |
|---|---|---|---|---|---|
| `octopod_a` | Octopod (A, D) | native red (041.mon pixels, median 148,0,0; x1.11) | native yellow-olive (112,104,0) | native blue (0,132,228) | 0.28/1.06, 0.07/0.23, 0.27/1.07 |
| `octopod_b` | Great Octopod | deep violet-purple (hue 285, sat x0.9, value x0.82) | pale gold (hue 46, sat x0.62) | amber (hue 40) | 0.19/0.58, 0.16/0.61, 0.50/1.67 |
| `octopod_c` | Kraken | dark sea-green slate (hue 165, sat x0.45, value x0.6) | pale bone (hue 50, sat x0.28) | red-orange (hue 10) | 0.12/0.28, 0.15/0.44, 0.68/2.73 |

Xeen draws all three with one sprite (the descriptors only tint it), so B and C are design recolours: violet for the
bigger Great Octopod, a dark sea-green old Kraken with bone suckers and red eyes; all three read apart at lake distance
(`review/ingame/d4_actors_*.png`).

## LODs

**9,587 / 4,792 / 1,689 / 462** body triangles (+ the 384-triangle foam ring on its own node, no LODs). LOD1
`tools/build_actor_lods.py` (via `scripts/lods_wrap.py`); LOD2/3 the `repair.py` ladder in the project copy `lodrepair/`,
first step **r25_12** accepted (LOD2 outline 4.6 % colour 9.5, LOD3 5.5 % / 8.1; `review/lod_scores_r25_12.tsv`).
`verify_far_only` OK; shadow LODs tucked up to 15 mm. Shadow check (`shadow_check.py 175.5`, the Kraken): at most 4.5 %
of the LOD3 shadow more than 1 unit outside LOD0 (under the 5 % line). `lodrepair/work/octopod/xeen_octopod/` keeps
`r25_12.built.glb`, `bake_r25_12/` and `result.json` for map-only reruns. Winding: 0 inverted closed parts.

## Binding (integration/actors.yml)

Scale **135** for the Octopod (A, D): the native front silhouette above the water (041.mon 0/4/5, the lake's teal and
everything below it left out, 1.34 units/px) against the model's Standing silhouette above z 0 (`scripts/scale_measure.py`):
area 133, width 141, height 161 (Meshy's tentacles are thicker and arch lower than the sprite's). Great Octopod **155.25**
(1.15x, a design choice for "Great"), Kraken **175.5** (1.3x, as asked); no `scale_reference`. Sizes (A / B / C): head
81 / 93 / 105 units wide; out of the water 70-74 / 81-85 / 91-97 units; tentacle span 256 / 294 / 333 units; Attack reach
of the tentacle tips 1.39 m = 188 / 216 / 244 units (the modifiers' `attack_reach` is 192). `yaw_offset -pi/2`,
`cast: Attack`, `run: Running`, `stride_length 3.0` / `run_stride_length 1.9` (no feet: the swim speed 256 units/s x the
1.6 s / 1.0 s cycle over the scale), `gait_rate [0.7, 1.5]`, `upper_body_root: Body` (the whole creature but the foam),
look on `Head` (25/10 degrees), `sockets: {siphon: Socket_Siphon}`, `events.attack_melee: {impact 0.533, glow [siphon],
color [170, 60, 255], glow_scale 1.0}` (the sprite's purple ink burst as the melee charge glow).

**Recommended collision** (the descriptors' 120 / 50 are generic): A and D height 80, radius 60; B 92 / 70; C 104 / 80
(the body out of the water, the head plus the tentacle roots; the swimmer's height only matters for aim and the box;
aim falls at 60 % of the model, on the head, either way).

## Checks

- Viewer: `python3 tools/run_creature_review.py --project level_generation/creatures/xeen_octopod_claude check`: 24
  switches (3 skins x 8 clips), no console errors (server `python3 -m http.server 8912 --bind 127.0.0.1` from the
  repo root). The viewer has no water: below z 0 is under the lake in game.
- Renders: `review/textured_sheet.png` (EEVEE, camera 1.6 model m above the water = 216 units, 3.2 m out; all three
  skins), clay clip sheets with a water plane.
- In game (`build-xeen/game/openyamm`, isolated runs, `--extra-mount work/mount`: a copy of the world's `actors.yml`
  with these four bindings in place of the stand-in, so live actors use them; nothing in `assets_dev` was edited):
  - D4 (`review/ingame/tour_d4.yml`, `sheet_d4.png`): static model spawns on the lake from the west shore (Standing,
    the blow, the wind-up, the death mid-sink, the Kraken at 175.5 swimming, forced LOD 2 and 3), then live hostile
    swimmers 11470/11471/11472: they sit on the water and swim off the shore party (the MM9 rule: a swimmer flees a
    target out of the water), all three skins distinct; the map's own placed octopod shows in the distance.
  - DD-14 (`review/ingame/tour_dd14.yml`, `sheet_dd14.png`): the five placed cistern octopods on the water face with
    the foam, plus a static model at the blow, the wind-up and Dead (gone under the surface).
  Exit 0, no load errors.

## Meshy credits: 15 of 30

| Job | Kind | Credits | Task |
|---|---|---|---|
| `smart_topology_v1` | image-to-3d, meshy-t2 smart-topology 15k, no texture, from `references_hd/00_three_quarter.png` | 5 | `01a1fb92-402a-71cc-a0aa-96dc2f9939bc` (primary) |
| `retexture_v1` | retexture, meshy-7, 4K, PBR, original UVs (`texturing/octopod_upload.glb`), views 01, 03, 02, 04 | 10 | `01a1fb9e-01c0-717e-a6cb-f3202923040b` (primary) |

## Rebuild

```sh
TOK=<lease>; cd level_generation/creatures/xeen_octopod_claude
TOK=$TOK scripts/step.sh inspect_raw.py; TOK=$TOK scripts/step.sh dump_glb.py; python3 scripts/pieces.py raw
TOK=$TOK scripts/step.sh clean.py; TOK=$TOK scripts/step.sh dump_raw.py clean_v1.blend clean
python3 scripts/joints.py; TOK=$TOK scripts/step.sh rig.py
# uv.py refuses to run once texturing/octopod_upload.glb exists (the paint belongs to that layout)
TOK=$TOK scripts/step.sh add_foam.py            # once, on anim_base.blend after uv.py
TOK=$TOK scripts/step.sh anim.py                # [clip ...] reruns only those clips on work/anim_v1.blend
TOK=$TOK scripts/step.sh dump_uv3d.py; TOK=$TOK scripts/step.sh bake_ao.py     # only after a layout change
TOK=$TOK scripts/build_runtime.sh [--install]   # compose, grade, gutter fill, ramps, export, LODs, skins, far LODs
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
python3 scripts/clip_gates.py export/xeen_octopod.glb 135; python3 scripts/scale_measure.py export/xeen_octopod.glb
TOK=$TOK scripts/step.sh render_textured.py; TOK=$TOK scripts/step.sh clip_sheet.py 6 fq all && python3 scripts/sheet_join.py clips_fq.png
```

`scripts/step.sh` takes the lane's Blender lock (`xeen_tiers_claude/bin/.blender.lock`). The in-game mount is rebuilt by
copying `assets_dev/worlds/xeen/models/actors.yml` with the four Octopod entries replaced from `integration/actors.yml`.

## Known limits

- Meshy's tentacles are thicker and shorter than the sprite's slender arms (lengthened 1.35x in `clean.py`); the
  arches rise to about head height, the sprite's a little higher.
- The sucker blobs are low-poly (decimated to a third) and the sucker pieces take about a fifth of the atlas.
- Near D4's shore the outdoor water is partly see-through, so the submerged front tentacle and the tentacle roots show
  faintly under the surface; in deep water and in DD-14's opaque cistern they are hidden.
- The ink spray is the engine's melee charge glow at `Socket_Siphon` (purple, then sparks at the blow), not a
  particle burst like the sprite's.
- The floor audit has no kind for Xeen's swimmer rows (Fly Y + the MM9 swimmer modifier, or D's stand): its problems are
  the intended waterline origin (above). A1 may want the audit to read `modifiers.yml`'s `movement: swim` and treat
  Xeen Octopod D like a swimmer.
- In-game skins B and C were seen only as live actors through the private mount (the console cannot pick a skin for a
  static model); the parent's binding validation runs after the merge.
- `level_generation/update_gitignore.py` was run; it lists nothing of this project.
- Not accepted by the user.

## Deep-water variant for P4 (lane S session 8, 2026-11-21)

P4's five Great Octopods (row 11471, A6's two swimmer groups with `above_floor` 512 over the bed at -1,024, surface
-64) swim mid-sea inside the water volumes and keep their height there (MM9 swimmer: Gravity 0). Seen in game
(`../xeen_tiers_claude/ingame_s8/p4oct2/sheet.jpg`): the bodies hover about -500 and read as swimmers, but the
surface **foam ring** draws with them mid-water. `scripts/deep_variant.py` writes the same GLB with the `Foam` node's
mesh and skin removed (nothing else changes); installed as `worlds/xeen/models/xeen_octopod_deep.glb`. Through an
overlay of the binding (`Xeen Octopod B` on the deep model, `../xeen_tiers_claude/ingame_s8/p4oct3/sheet.jpg`) the
octopods swim clean. Row 11471 also swims on D4's lake (surface, foam wanted), so the deep model needs its own row and
descriptor for P4 (asked of A2: a copy of 11471, `Xeen Octopod E`); bind it as Octopod B with this model (skin
`octopod_b`, scale 155.25) once the row exists. Seen: the underwater view itself is untinted (A1/A6's, not the model's).
