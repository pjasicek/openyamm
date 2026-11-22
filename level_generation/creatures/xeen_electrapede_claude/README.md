# Xeen Electrapede (Xeen Crawler B), 2026-11-20

Lane S project (parent session `xeen-s5`, sub-agent `xeen-s5-electrapede`, identity `xeen:electrapede`). Row: the
`giant_crawlers` family in `assets_dev/worlds/xeen/source/monsters.yml` (block 11360), tier B Electrapede (11361,
level 20, Air attack, Paralyze, air immune). Ground walker, melee only. Native art: Darkside image 7
(`sprites/dark/007.mon`, `007.att`). Built with the [quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md) main route
(segmented creatures and snakes sections), [HD masters](../CLAUDE_HD_MASTER_REFERENCES.md),
[creature textures](../CLAUDE_CREATURE_TEXTURES.md), the [texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md)
and the [LOD playbook](../LOD_PLAYBOOK.md); scripts adapted from `xeen_mole_claude/`.

**State: installed** (`tools/install_model.py --world xeen`), checked in the review viewer and in game (static model
spawns in XD-21). The binding is **not** merged (the parent owns `actors.yml`): the ready block for `Xeen Crawler B`
is [integration/actors.yml](integration/actors.yml). Not accepted by the user. **Meshy: 15 of 30 credits.**

## Deliverables

| File | What |
|---|---|
| `assets_source/worlds/xeen/models/xeen_electrapede.glb` (sha256 `9763380f…`) | installed source = `export/xeen_electrapede.glb`; cooked runtime copy in `assets_dev/worlds/xeen/models/` (`24b918c4…`) |
| `integration/actors.yml` | the binding for `Xeen Crawler B` (skin `electrapede_a`, scale 140, impact 0.533 s, melee glow at mouth and antenna tips) |
| `work/anim_v1.blend` | keyed master (rig `Pede_Rig`, mesh `Pede`); `work/anim_base.blend` the locked UV layout; `work/rig_v1.blend`, `work/clean_v2.blend` before |
| `references_hd/` | the five Codex masters (00/01/02 1536x1024; the side views 2172x724 as returned), `CODEX_BRIEF.md`, `generation_runs.json`, `codex_run1/2.log`, `selected_views_review.png` |
| `native/` | original frames `mon_0000..0007`, `att_0000..0003` with `*_frames.json`; `sheet_codex.png` (Codex input) |
| `textures/` | `pede_basecolor_graded.png` (2K), `pede_normal_1k`, `pede_mr_1k` (R AO, G roughness, B 0), `pede_region_mask.png` (R green plates and head, G legs/antennae/sockets, B eyes, A slate underside), `pede_ramps.json`, `pede_material_classes.png` (1 chitin, 6 eye, 7 mouth), `pede_ao_2k.png` |
| `review/` | `textured_sheet.png` (EEVEE at party eye height), `clips_quarter.png`, `clips_top.png`, `clips_fq.png` (clay clip sheets), `raw_sheet.png`, `v1_*`/`v2_*` mesh views, `region_classes.png`, `texture_quality.json`, `uv_quality_upload.json`, `lod_scores_c40_25.tsv`, `viewer_shots.png`, `shots/`, `ingame/` |
| `review/viewer/` | review viewer (one skin, every clip) |

## Mesh

Meshy Smart Topology v1 (meshy-t2, 15k, from `00_three_quarter.png`): 16,208 triangles in 102 pieces, scaled to
2.20 m along Y (`scripts/prep.py`): 15 plate shells, 32 leg-socket rings, 30 short straight leg spikes (0.14 m), the
head shell, mouth parts, palps, antennae and six tail cerci. `scripts/clean.py` (rules, not indices):
- two mid-body pieces came back as merged, folded plates (two and three plates in one piece, with holes): each is
  replaced by copies of the nearest good plate, one per leg pair inside it, scaled to the local width, height, pitch;
- Meshy's leg spikes are dropped; every leg becomes a **procedural jointed leg** from the same hip (6-sided tapered
  tubes: femur up and out to a raised knee, a slightly bowed tibia down to a pointed foot on the floor, fanned forward
  at the front and back at the rear, sized by the local plate width), as in the masters and the native sprite;
- the head group is scaled 1.25x about the neck (the native head is wider than the body); Meshy's four small eye
  bumps are replaced by **two compound-eye ellipsoids** on the upper face (ray cast, symmetric; Meshy's head is
  slightly asymmetric), later shrunk to 0.8 (`scripts/eyes_scale.py`: each eye about a quarter of the head width, as
  in the native frame; vertex positions only, the paint stays valid);
- small holes filled, decimation per part (plates 0.55, head 0.85, sockets 0.5, cerci 0.45, legs and antennae kept).

**9,232 triangles** (plates 3,063, head 1,551, eyes 576, antennae 870, legs 2,100, sockets 770, cerci 302). Face
attributes `part`, `seg`, `side`. Rest: forward -Y, 2.25 m long, plates 0.20 m high and 0.23 m wide, head top 0.31 m,
legs reach 0.37 m from the centre line, antenna tips 0.50 m.

## Rig (`scripts/rig.py`, exoskeleton route)

`Root` > `Seg0..Seg14` (one per leg pair, head to tail, joints at the plate boundaries) > `Tail` (the two leg-less
tail plates and the cerci); `Seg0` > `Head` > `Jaw`, `Mandible_L/R`, antennae `Ant0_R1/2`, `Ant1_R1`, `Ant0_L1`,
`Ant1_L1`, `Ant2_L1/2` (two bones for the long ones); `Seg<j>` > `Femur<j>_<side>` > `Tibia<j>_<side>` (30 legs, Z
axis = the leg plane's normal). 91 bones. Weights: plates and sockets by arc position along the spine (rigid inside a
plate, smoothstep over 2.5 cm either side of each boundary, so bending opens no gaps); head, eyes, jaw, mandibles,
antennae rigid; each leg rigid on Femur to its knee ring, Tibia beyond, the knee ring half and half. 0 unweighted
vertices. FX sockets (non-deform bones, exported as nodes, `scripts/add_sockets.py`): `Socket_Mouth` (in front of
the mouth, on Head), `Socket_Antenna_L/R` (the long antennae's tips).

## Clips (`scripts/anim.py`, 30 fps, procedural)

Every frame is built as armature-space bone matrices: the spine from an absolute heading per segment (yaw: S-wave,
pitch: rearing, roll) laid out from an anchor joint so segment lengths never change, gait loops re-centred on the body
axis (in place); every leg a two-bone IK to a foot target with the knee kept up and out; head, jaw, mandibles and
antennae local rotations on top. **Metachronal gait:** each pair runs stance/swing 0.11 of a cycle behind the pair in
front, left and right in antiphase; a stance foot is planted on the floor and slides back at exactly the body speed
(no slip); its lateral foothold follows the hip at mid-stance of the S-wave. Floor rules every frame on the evaluated
mesh: the core (plates, head) is lifted when it sinks, a leg dipping under the floor gets its target raised (never
needed: the body lies on the floor, every foot target is clamped to z >= 0).

| Clip | Length | What | Event |
|---|---|---|---|
| Standing | 2.0 s loop | breathing ripple along the body, head drift, antennae sway, mandibles chew | |
| Walking | 0.8 s loop | S-wave head to tail (10 degrees), metachronal leg waves, duty 0.65; 0.45 m per cycle | |
| Running | 0.5 s loop | S-wave 15 degrees, duty 0.5; 0.70 m per cycle | |
| Attack | 1.0 s | the front six segments rear up to 40 degrees, body draws back, mouth opens, mandibles spread, antennae raised with an electric twitch; lunges forward and down, bites, recovers | **impact 0.533 s** (frame 16: the head furthest forward) |
| Hit | 0.5 s | recoils: the front jerks up and back, the body kinks, head jerk, antennae whip | |
| Death | 1.5 s | thrashes (S-wave, rearing), then curls into a C on the floor (235 degrees), legs folding in against the body (native att 3 shows the curled body) | |
| Dead | 1.0 s | Death's last pose | |
| Fidget | 2.0 s | head turns left then right, the front pair lifts and rubs at the mouth, antennae flick | |

No cast and no missile on the row: `cast: Attack`, `attack_ranged: Attack`.

**Lightning:** the native attack frames crackle with yellow lightning around the head and antennae. The engine
cannot animate emission per clip (pulse is constant), so the binding uses the melee event's **glow sockets**:
`attack_melee: {impact: 0.533, glow: [mouth, antenna_left, antenna_right], color: [255, 225, 70], glow_scale: 0.8}`
charges an electric yellow glow at the mouth and both antenna tips during the wind-up and goes out with sparks as the
bite lands. The model has no emissive material. The glow was not seen in game (it needs the binding merged).

### Gates

`scripts/clip_gates.py export/xeen_electrapede.glb 140` (largest per-frame vertex step, second difference, loop seam,
lowest point in world units at scale 140):

| Clip | Step cm | Accel cm/f² | Seam cm | Lowest units |
|---|---|---|---|---|
| Standing | 1.53 | 0.17 | 0.00 | -0.00 |
| Walking | 6.15 | 6.31 | 0.00 | -0.00 |
| Running | 8.14 | 12.87 | 0.00 | -0.00 |
| Attack | 18.12 | 14.18 | (one-shot) | -0.00 |
| Hit | 13.79 | 12.71 | | -0.00 |
| Death | 19.13 | 20.55 | | -0.00 |
| Dead | 0.00 | 0.00 | 0.00 | +0.28 |
| Fidget | 8.96 | 2.69 | | -0.00 |

The largest steps are the antenna tips in the attack's lunge and the death thrash (0.5 m from the head, fast), and the
swing feet of the run. Floor audit (`floor_audit.audit` with this binding block on the export; the world's
`actors.yml` still binds the stand-in): **Xeen Crawler B: ground, standing -0.00, walking -0.00, living lowest -0.00,
corpse +0.28 world units, no problems** (tolerance 2.5).

## Textures

UVs (`scripts/uv.py`, `uv_atlas.unwrap` defaults, Head/Jaw/Mandibles 1.6x denser): PartUV charts, seam pass, sparrow
packing, **no fallback**. Meshy `retexture_v1` (meshy-7, 4K, PBR, original UVs; views 01, 03, 02, 04) returned the
same layout. Quality (`texture_quality.py export/xeen_electrapede.glb`): **atlas 72.7 %, density p10/p50/p90
1907/2109/3187 (spread 1.67: the head and eyes are meant to be 1.6x denser; every body bone is at 155 with stretch p90
1.12-1.14, `review/texture_quality.json`), 177 islands, fragments 0.1 %, stretch p90 1.22**.

`scripts/compose.py`: colour 4K -> 2K once (Lanczos), normal and ORM to 1K, the procedural legs get dark joint bands
(hip, knee) and a dark foot tip in luminance (native legs: magenta with dark purple joints); classes from geometry
(eyes, legs, antennae) and on the plates and head from the paint's hue (teal-slate belly hue ~157 vs green, magenta
socket rings); dark mouth texels in no region. Gentle grade (`--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast
1.06 --saturation 1.15`), `gutter_fill.py` last on every map. Roughness 0.35-0.75, eyes 0.22; specular 0, metallic 0
(binding extras).

Skin (`scripts/tier_ramps.py`, `textures/pede_ramps.json`): Xeen draws the Electrapede with one palette, so the one
skin `electrapede_a` reproduces the native sprite: per region the colour comes from the native pixels of that region
(band-averaged chroma by luminance percentile, 15th-95th), the texel keeps its own luminance scaled to the native mean
x 1.3 (eyes x 1.0), then the shader ramp is fitted. Meshy painted the eye ellipsoids green and the legs partly green;
the region ramps make them magenta like the sprite. The mask covers body (R), legs/antennae/sockets (G), eyes (B) and
the underside (A), so later crawler tiers are ramp numbers only.

| Region | Native pixels (median sRGB) | Gain | Fit mean / p95 (8-bit) |
|---|---|---|---|
| R green plates, head | 5,982 (28,160,8) | 3.59 | 0.37 / 2.21 |
| G legs, antennae, sockets | 2,159 (88,0,88) | 0.68 | 0.10 / 0.29 |
| B eyes | 1,261 (212,0,216) | 1.24 | 0.75 / 2.89 |
| A slate underside | 1,254 (28,68,76) | 1.21 | 0.08 / 0.15 |

## LODs

**9,232 / 4,616 / 3,693 / 2,299** (LOD1 `tools/build_actor_lods.py` through `scripts/lods_wrap.py`; LOD2/3 the
`repair.py` ladder in the project copy `lodrepair/`, step **c40_25** (curvature-weighted) accepted: LOD2 outline
4.7 % colour 8.2, LOD3 8.2 % / 5.1, `review/lod_scores_c40_25.tsv`; the plain 25-35 % steps lost the thin legs'
outline). `verify_far_only` OK; shadow LODs tucked up to 15 mm. Shadow check
(`audit_mm678_20261111/lod_audit/shadow_check.py 140`): at most 4.0 % of the LOD3 shadow more than 1 unit outside
LOD0 (under the 5 % look-in-game line). `lodrepair/work/pede/xeen_electrapede/` keeps `c40_25.built.glb` and
`bake_c40_25/` for map-only reruns.

## Binding (integration/actors.yml)

Scale **140** world units per model metre, from the native front frame (007.mon frame 0) at the Xeen bindings' 1.34
units/px, judged by the head because the long body recedes behind it in the sprite: eye spacing 15 px against 0.144 m
gives 139, head height to the floor 30 px against 0.30 m gives 134, head width 30 px against 0.25 m gives 160. The
model: **2.25 m -> 315 units long, plates 28 units high, head 43 units, antenna tips 70 units**. `yaw_offset -pi/2`,
`cast: Attack`, `run: Running`, `stride_length 0.45`, `run_stride_length 0.7`, `upper_body_root: Head` (a bite while
moving moves head, jaw and antennae over the gait), look on `Head` (35/25 degrees), sockets `mouth`, `antenna_left`,
`antenna_right`, `events.attack_melee` impact 0.533 with the glow above. No `scale_reference` (Scorpion and Lava Roach
are other models).

## Checks

- Winding: 0 inverted closed parts. Installed with `tools/install_model.py --world xeen` (cooked runtime copy).
- Viewer: `python3 tools/run_creature_review.py --project level_generation/creatures/xeen_electrapede_claude check`:
  8 switches (1 skin x 8 clips), no console errors (served by `python3 -m http.server 8912 --bind 127.0.0.1` from the
  repo root); shots in `review/shots/`, sheet `review/viewer_shots.png`.
- Renders: `review/textured_sheet.png` (EEVEE, party eye height 1.26 model m = 176 units, 3.4 m from the body centre;
  EEVEE's sheen makes the eyes look paler than in game).
- In game: `review/ingame/` (XD-21, `build-xeen/game/openyamm`, `model spawn` of the installed GLB at scale 140 yaw pi:
  Standing, the bite at 0.533 s, the wind-up, Walking, Dead, forced LOD 2 and 3; the default variant); `tour.yml`
  has the command. Exit 0, no load errors.

## Meshy credits: 15 of 30

| Job | Kind | Credits | Task |
|---|---|---|---|
| `smart_topology_v1` | image-to-3d, meshy-t2 smart-topology 15k, no texture | 5 | `01a1fa7c-6c83-708c-9758-8e8d1382d1c8` (primary) |
| `retexture_v1` | retexture, meshy-7, 4K, PBR, original UVs (`texturing/pede_upload.glb`), views 01, 03, 02, 04 | 10 | `01a1fa89-7ffa-7428-952d-3e0a1180d19a` (primary) |

## Rebuild

```sh
TOK=<lease>; cd level_generation/creatures/xeen_electrapede_claude
TOK=$TOK scripts/step.sh inspect_raw.py; TOK=$TOK scripts/step.sh prep.py; TOK=$TOK scripts/step.sh clean.py
TOK=$TOK scripts/step.sh rig.py
# uv.py refuses to run once texturing/pede_upload.glb exists (the paint belongs to that layout)
TOK=$TOK scripts/step.sh add_sockets.py; TOK=$TOK scripts/step.sh eyes_scale.py
TOK=$TOK scripts/step.sh anim.py                 # [clip ...] reruns only those clips on work/anim_v1.blend
TOK=$TOK scripts/step.sh dump_uv3d.py; TOK=$TOK scripts/step.sh bake_ao.py
TOK=$TOK scripts/build_runtime.sh [--install]    # compose, grade, gutter fill, ramps, export, LODs, skin, far LODs
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
python3 scripts/clip_gates.py export/xeen_electrapede.glb 140
python3 ../claude_shared/tier_textures.py textures/pede_basecolor_graded.png textures/pede_region_mask.png \
  textures/pede_ramps.json work/tier_pede && TOK=$TOK scripts/step.sh render_textured.py
```

`scripts/step.sh` takes the lane's Blender lock (`xeen_tiers_claude/bin/.blender.lock`); so does
`lodrepair/scripts/audit.sh`. Mesh views: `views.py`, `closeups.py`, `clip_sheet.py <n> quarter|top|fq [clips]` +
`sheet_join.py`; `pieces.py` lists a dump's pieces (`dump_raw.py`).

## Known limits

- Meshy's head is a rounded shell with a nose-like mouth blob; the mandibles are small palps. The compound eyes are
  our ellipsoids, painted by the region ramp (Meshy painted them green).
- The legs are procedural tubes; their paint is Meshy's projection recoloured by the leg ramp plus procedural joint
  bands (no hand-painted segmentation).
- The lightning is the engine's melee glow at three sockets, not an arc effect; not yet seen in game (binding not
  merged).
- The Dead C-curl lies belly down with the legs folded in, not rolled onto its side.
- `scripts/update_gitignore` was run as AGENTS.md asks: it added one line for another project's file
  (`/sounds/xeen_20261120/picks.yml`) to `level_generation/.gitignore`; nothing of this project needed listing.
- Seen in game only as debug-spawned models; not accepted by the user.
