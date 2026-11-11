# MM9 Monk body (mm9_monk) — 3D actor, 2026-10-31

MM9 `MONK.abc` (81 nodes, 35 clips, 582 triangles), rows 123 Initiate L25 (`MM9 Monk A`, MONK1), 124 Monk L35 (`B`, MONK2), 125 Reverend Monk L50 (`C`, MONK3).
Decided from the ABC: a two-armed Biped (`Bip01`, Finger0 and Finger1 per hand), so the humanoid route: MM9 skeleton and MM9 clips, never Mixamo. No thigh bones: `Bip01 L/R Calf` hang straight off `Bip01 Spine` with keyed translations, and eight cloth chains (`XF`, `XFR`, `XR`, `XBR`, `XB`, the side ones paired) carry the robe. Two cord chains (`Ytass*`), and `Bip01 Ponytail*` carries the hood's point.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_monk.glb` (`tools/install_model.py --world mm9`), variants `mk_a`, `mk_b`, `mk_c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_monk_claude` (`scripts/bind_actors.py`), scale 100 (MONSTERS Scale 1), `yaw_offset` -1.570796327, stride walk 1.30 (planted foot) / run 2.05 (MM9's RunVelocity × clip; the feet are mostly hidden), `cast: AttackRanged3`, sockets `palm_left` = `LHand1`, `palm_right` = `RHand1` |
| Triangles LOD0/1/2/3 | 14,285 / 7,127 / 2,564 / 853. LOD0: robe 6,959 (shell with hood lining, cuff cups, hem cap), head 3,800, hands 1,600, shoes 620, knots 520, belt 378, cords 328, shins 80 |
| Skeleton | 116 joints: MM9's 81 + 30 finger bones (15 per side) + 5 half-joint helpers (`XhalfUpperArm`, `XhalfForearm`, `XhalfHead`) |
| Clips (30 fps) | All 34 of MM9's + Dead. Bound: Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `Hattack1`, AttackRanged `castspell1`, Hit `wince1`, Death `die1`, Dead; `cast` plays AttackRanged3 `castspell3`. Script clips: Fidget2, Aware, Taunt, Pray, CowerStart/Cower/CowerEnd, AttackRanged2, Hit2, Death2, Backpedal, BackpedalRun, Play, Hoe*, Sweep*, Hammer*, Wash* |
| Events (MM9's) | `attack_melee` impact 0.214 s (`Rattack`; `Hattack1` has four hits, 0.214, 0.428, 0.643, 0.965 s, the engine takes one); `attack_ranged` 0.5 s (`castspell1` CastSpell), `cast` 0.882 s (`castspell3`), both glow on both palms, release `palm_left`. Lunge, DoFX and sounds not carried |
| Textures | Body colour 2K, normal and ORM 1K, region mask 1K (4 regions: cloth, shoes, rope, hands); head colour 1K per tier (3), shared normal and ORM 1K. 9 images |
| GPU memory | about 17.7 MB for all tiers (BC7/BC5 estimate with mips); the three head colours are 4.2 MB of it. No per-tier body image |
| Meshy credits | **20 / 40**: body Smart Topology 5, head Smart Topology 5, body retexture A 10 (backup account), no retries |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_monk_claude/review/viewer/ revision `r13-20261031`, tiers `mk_a`, `mk_b`, `mk_c` |

## Route (`scripts/`)

0. **Sources**: `convert_abc_model.py --scale 0.0256`, `source/mk1..3`, raw ABC space (L at -x). `mm9_dump.py` dumps the mesh. The bind is an A pose and exactly symmetric, but the raw route with `mirror_glb.py` last was kept anyway.
1. **Masters**: Codex, tier A geometry (`references_hd/`, MM9's own arm pose, sleeves coaxial with the arm), then a clay head sculpt (`references_head/00_geometry.png`).
2. **Meshy Smart Topology** body and head. The body came back as a closed shell with a real hood lining, real cuff cups and a shallow cap inside the hem: no linings to build.
3. `step1_clean.py` -> `assemble.py`: robe bisected and mirrored; MPFB left hand (`hand_mpfb.py`, posed open, 800 tris) with a forearm stub into the sleeve, wrist at MM9's 0.523 m from the shoulder; head + eyeballs joined through a 1.1 mm voxel remesh (that closed Meshy's cracks at brow, lips and chin), pressed inside the hood lining, the part behind the ears removed (the hood hides it), one half decimated and mirrored (symmetric decimation flipped midline faces). `refine.py`: rows every 11 cm on the lower robe, four rings at each elbow.
4. `inner_faces.py`, `uv_mk.py` (never re-run): `uv_atlas.py`, body one 2K-layout square at 4K paint, head its own square.
5. **Paint**: Codex paints on our exact clay (`paint_clay.py`, `references_paint/`), one Meshy retexture at 4K, tier A. Heads: Codex paints per tier on the head clay, projected for free (`project_head.py`, from the Thrall's; front, left, right only).
6. `compose_mk.py`, `deghost.py`, `finish_mk.py`, `tiers_mk.py`, `head_finish.py`.
7. `rebuild.sh [--install]`: `tweak.py` -> `fit_rig.py` -> `weights.py` -> `build_glb.py` -> `clips_mk.py` -> `finger_rest.py` -> `arm_out.py` -> arm corrections -> `half_keys.py` -> `cloth_keys.py` -> prepare -> LODs -> shadow fix -> ramps -> tier images -> winding -> floor -> sockets -> `mirror_glb.py` -> install. `tail.sh` reruns from the ramps. `viewer_update.sh`, `gates.sh`, `closeups.sh`, `strips.sh`, `final_sheets.sh` review it.

## Findings worth keeping

- **A robe on MM9's chains wants analytic weights, not transferred ones.** Weights copied from MM9's low-poly mesh by nearest triangle gave a lumpy robe with dark pits. Weights by azimuth (two neighbouring chains) and height (two neighbouring joints of each) are exactly four influences and smooth. **Any smoothing after that** gave more than four influences, and the cut to four tore triangular patches into the robe (robe faces 354 -> 72 in Pray once removed).
- **The chains' translations are real.** `XBc` runs from 11 to 36 cm across the clips. All X and Y bones and the Calves stay at MM9's bind position and are in `root_nodes`, so MM9's keyed translations apply. Moving them onto our mesh would not.
- **Pivots:** the elbow hinge moved forward and up (0, -3.5, +2 cm), the shoulder down 3 cm, cut elbows from 26 to 7 and armpits from 17 to 4 in Standing. The first guess at "outside of the bend" went the wrong way (elbow 46). Try both signs and measure.
- **Meshy paints rope onto the cloth under it.** With the cords moved the ghost showed. `deghost.py` replaces pale strokes on cloth charts with the chart's own weave.
- **Region masks must reach the gutter.** A mask soft at the chart's edge left the brown base as pale stitches along every seam on the navy tier. Labels are spread into the gutters first.
- **`arm_hand_gate.py` needs the body's real waist.** Meshy's waist was 12 cm wider than MM9's narrow, deep one, and MM9's stand rests the hands there: a constant 12 deg arm offset cleared it but read as a gunslinger. Narrowing the waist 20 % and dropping the belt 6.5 cm to MM9's height (`tweak.py`, UVs unchanged) needed only 3 deg.
- A `sed` on `os.environ.get(...)` missed `__import__('os').environ.get(...)` and left an old default in the rig through two full gate runs; the gate's identical face-frames gave it away.

## Tiers

MM9's three skins are the same weave recoloured, and the same rope and hands. **One body paint**, tier A, with ramps fitted to MM9's own texels: cloth, shoes, rope, hands. Inner faces (hood lining, cuffs, hem cap, shins) are darkened in the base and take the bottom of the cloth ramp. Tier A's ramp is shifted 7 % off red, tier C's cloth is 1.2x (the MM9 navy reads brighter than its texels under flat light).
**Heads**: one 1K colour per tier, because the men differ (stern man with goatee, smiling bearded man, weathered old man with ginger beard). This is the only per-tier image. Bound per tier on every LOD through `KHR_materials_variants`.

## Deviations

- **Handedness:** `L Hand` +x, `R Hand` -x on a figure facing +Z in the final GLB (true-handed), by `mirror_glb.py`. Inferred from coordinates and names, as on the other bodies.
- **Arm offset:** 3 deg outward in every clip (`arm_out.py`), constant, plus small key-solved turns (`arm_jobs.txt`: Fidget, AttackRanged2, AttackRanged3, Hit, Hit2, CowerStart, CowerEnd).
- **Waist 20 % narrower than Meshy's, belt 6.5 cm lower, sleeves 20 % slimmer between shoulder and cuff**, moved after the paint: the UVs are unchanged, the paint moved with the mesh.
- **Hands:** MPFB, not Meshy's lumpy ones; no weld, the stub ends in the sleeve. Fingers bind open and take a constant relaxed curl (`finger_rest.py`), since MM9's mitten is flat; MM9's curl then applies at 0.6/0.5/0.35 per joint (thumb 0.7/0.4/0.2).
- **Legs:** shoes and a short plain shin only. MM9 has no thighs either; the shin stops at -0.62 so it stays in the robe.
- **Head:** no jaw bone in MM9, mouth closed, tier B's smile is paint. The back of the skull is not there (3,800 tris on what the hood shows).
- **Hood tip:** `Ponytail11/12` moved onto the hood's crest; `Ponytail1` is unweighted.
- **Props:** MM9's Hoe, Broom, Hammer and Cloth sockets on `R Hand` and the prop models are built since 2026-11-10 (below, "MM9 sockets"); the placements hold them through scene `held_items`.

## Checks (rig and clips of r9; r10 to r13 changed only ramps, one image and the head paint)

| Gate | Result |
|---|---|
| Legs through the robe (`robe_gate.py`, signed distance to the posed outer robe; 48 fps on Walking, Running, Backpedal, BackpedalRun, 24 elsewhere) | **0 frames in all 35 clips** |
| Cords under the robe, over 1.2 cm, below the belt | 0 frames, except script clips Pray 5/37 at 4.3 cm, Cower 3/22 and CowerEnd 2/25 at 2.6 cm (the lap in the kneel and bend), and Dead 25/25 at 1.3 cm. Before `cloth_keys.py`: Running 20/20 at 3.9 cm, Death2 at 3.6 cm |
| `arm_hand_gate.py --outer-only` (48 fps) | Hand depth 0 in Walking, Running, Backpedal, BackpedalRun, Dead. Bound clips are a resting hand at about 1 cm: Standing L 1.1 cm 5 frames, Fidget L 1.1 cm 4, AttackMelee L 1.1 cm 3, AttackRanged L 1.2 cm 6, R 1.2 cm 2, Hit R 1.5 cm 3, L 1.1 cm 2, Death L 1.1 cm 1. **Over that:** AttackRanged3 (the `cast`) L 2.2 cm 3 frames, Pray L 2.0, R 1.9 cm, all 73 frames (the palms pressed together: hand into the other hand), Fidget2 L 1.5 cm 10. Forearm 0 except Hoe and HoeFidget R 6.0 cm (script clips, MM9's own pose with a tool in the hand) |
| Finger stretch | max 3.63 in AttackMelee's fist and the Hoe clips (high: the Thrall has 1.84, the Lich 2.98). Looked at close in the fist, read clean |
| `jitter_gate.py` against the same clips without corrections | **0 fails** |
| `detached_parts_audit.py` | **Not 0:** 2 parts flagged, the two shoe soles, 7.9 cm in 9 and 6.4 cm in 3 of 1,543 poses (Death2, Death). The legs have no thigh and hang free inside the robe, as MM9's do; the gap is between hem and shoe in the fall. Everything else attached |
| `orient_gate.py` against MM9 | Head mean under 3 deg, max 12.6 (Fidget2 ease), 8.7 in the deaths; soles max 7.4 (BackpedalRun, floor raise) |
| `bone_length_audit.py` | 2 flagged: `L/R Calf` 0.37-0.51 m, Death2. That is MM9's keyed distance from Spine to knee (no thigh bone). Arms and everything else constant. Calf to Foot constant 0.402 |
| `check_winding.py` | 0 inverted closed parts |
| `flat_shading_check.py` | 0.00 body, 0.04 head |
| `floor_audit.py` | 3 bindings ok: stand +0.3, walk -1.9..-0.7, living -1.9, dead 0 |
| `texture_quality.py` | Body atlas 61.8 %, stretch 1.25 p90, fragments 0.3 %, spread 2.79 (hands 1.5x, inner faces 0.4x by design); head atlas 61.6 %, spread 1.68, stretch 1.24, fragments 0.0 % |
| Symmetry | Robe, belt and head mirrored exactly at assembly; MM9's mesh is exactly symmetric |
| Regression `--world mm9 --headless-run-regression-suite actors` | `mm9_actor_models_build_every_binding` PASS, 125 descriptors on 52 models, 0 failed; suite 192 passed, 1 failed: `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data", the failure other bodies report. Run at r9, before the texture-only changes |
| Viewer `run_creature_review.py check` | 105 switches, 0 failed, 0 console errors |
| In game (`bootcamp.odm`, review root, isolated) | `review/sheet_ingame.png`: three tiers bound per variant; Standing, Fidget, Running seen |

### Collapse (`scripts/collapse_gate.py` from the Evil Sorcerer's, all LOD0 primitives, 30 fps, worst single frame per region)

| Clip | face-frames | elbow L/R | armpit L/R | waist | torso | neck | head | hood tip | robe | rope | finger | ankle L/R | seen at worst frame |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Standing | 1694 | 7/6 | 4/3 | 0 | 0 | 8 | 5 | 0 | 2 | 0 | 4 | 0/0 | 30 |
| Walking | 498 | 1/1 | 2/2 | 0 | 4 | 6 | 4 | 0 | 15 | 2 | 4 | 0/0 | 28 |
| Running | 481 | 4/4 | 3/3 | 0 | 1 | 10 | 10 | 0 | 11 | 2 | 4 | 1/1 | 27 |
| Backpedal | 502 | 1/1 | 2/2 | 0 | 4 | 6 | 4 | 0 | 15 | 2 | 4 | 0/0 | 27 |
| BackpedalRun | 319 | 1/1 | 2/2 | 0 | 4 | 6 | 4 | 0 | 15 | 1 | 4 | 0/0 | 27 |
| Fidget | 3105 | 7/7 | 4/5 | 0 | 0 | 14 | 13 | 0 | 0 | 0 | 4 | 0/0 | 34 |
| Fidget2 | 3705 | 7/6 | 4/3 | 0 | 2 | 14 | 21 | 1 | 1 | 0 | 5 | 1/0 | 32 |
| Pray | 3959 | 7/7 | 4/4 | 0 | 0 | 12 | 8 | 0 | 28 | 4 | 1 | 6/6 | 47 |
| Aware | 1146 | 7/7 | 4/4 | 0 | 0 | 15 | 12 | 0 | 0 | 0 | 4 | 0/0 | 18 |
| Taunt | 1032 | 7/7 | 4/4 | 0 | 0 | 15 | 12 | 0 | 0 | 0 | 4 | 0/0 | 18 |
| CowerStart | 949 | 8/6 | 4/3 | 0 | 3 | 17 | 13 | 1 | 2 | 0 | 4 | 1/1 | 35 |
| Cower | 1532 | 8/6 | 4/3 | 0 | 4 | 17 | 12 | 1 | 2 | 0 | 2 | 1/1 | 35 |
| CowerEnd | 1407 | 8/8 | 4/4 | 0 | 3 | 17 | 13 | 1 | 2 | 0 | 4 | 1/1 | 35 |
| AttackMelee | 1743 | 7/7 | 5/7 | 0 | 5 | 22 | 14 | 1 | 0 | 0 | 12 | 0/0 | 35 |
| AttackRanged | 1312 | 7/6 | 4/5 | 0 | 4 | 21 | 23 | 3 | 0 | 0 | 6 | 0/0 | 42 |
| AttackRanged2 | 1159 | 7/11 | 4/4 | 0 | 2 | 17 | 21 | 0 | 0 | 1 | 4 | 0/0 | 37 |
| AttackRanged3 | 2359 | 7/7 | 4/4 | 0 | 0 | 28 | 16 | 0 | 0 | 0 | 4 | 0/0 | 27 |
| Hit | 1316 | 7/7 | 4/4 | 0 | 2 | 11 | 14 | 0 | 3 | 0 | 4 | 1/0 | 35 |
| Hit2 | 1184 | 7/7 | 4/4 | 0 | 5 | 13 | 14 | 1 | 2 | 0 | 5 | 0/0 | 33 |
| Death | 2331 | 7/6 | 9/5 | 0 | 10 | 18 | 19 | 0 | 35 | 6 | 4 | 3/3 | 45 |
| Death2 | 2123 | 7/6 | 4/3 | 0 | 8 | 42 | 25 | 0 | 12 | 3 | 4 | 4/3 | 55 |
| Play | 2083 | 7/6 | 3/3 | 0 | 0 | 10 | 8 | 0 | 2 | 0 | 2 | 0/0 | 29 |
| HoeWait | 1689 | 2/7 | 2/4 | 0 | 0 | 6 | 9 | 0 | 4 | 0 | 3 | 0/0 | 21 |
| Hoe | 2977 | 7/8 | 4/6 | 20 | 2 | 16 | 17 | 0 | 13 | 0 | 4 | 1/0 | 62 |
| HoeFidget | 6075 | 7/13 | 13/6 | 17 | 3 | 15 | 12 | 0 | 12 | 0 | 4 | 0/1 | 62 |
| SweepWait | 1817 | 1/6 | 2/3 | 0 | 1 | 14 | 10 | 0 | 0 | 0 | 3 | 0/0 | 21 |
| Sweep | 1290 | 7/6 | 4/3 | 0 | 0 | 8 | 8 | 1 | 0 | 0 | 4 | 0/0 | 27 |
| SweepFidget | 3096 | 7/7 | 7/4 | 0 | 0 | 62 | 25 | 1 | 0 | 0 | 5 | 0/0 | 24 |
| HammerWait | 1174 | 6/5 | 3/3 | 0 | 0 | 3 | 3 | 0 | 2 | 0 | 5 | 1/0 | 25 |
| Hammer | 625 | 1/7 | 3/4 | 4 | 0 | 10 | 8 | 0 | 8 | 0 | 2 | 0/0 | 32 |
| HammerFidget | 4034 | 7/7 | 4/4 | 4 | 0 | 13 | 14 | 0 | 8 | 0 | 4 | 1/0 | 33 |
| WashWait | 1557 | 8/4 | 4/3 | 0 | 0 | 8 | 6 | 0 | 0 | 0 | 2 | 0/0 | 28 |
| Wash | 679 | 6/6 | 3/3 | 0 | 0 | 12 | 7 | 0 | 2 | 0 | 2 | 0/0 | 25 |
| WashFidget | 4193 | 8/5 | 4/3 | 0 | 0 | 17 | 11 | 0 | 0 | 0 | 3 | 0/0 | 27 |
| Dead | 2790 | 1/0 | 3/2 | 0 | 0 | 18 | 19 | 0 | 35 | 5 | 4 | 1/2 | 44 |

Regions: the robe has no knee, hip or groin to measure; its chains are `robe`. Not zero. Largest: `neck` 62 in SweepFidget (script), 42 in Death2, 28 in AttackRanged3, mostly small faces at the neck hole and the skin at the back of the neck inside the hood; `head` up to 25, the same band. Neck and head together, faces a camera can see at the clip's worst frame: 17 at most on bound clips (AttackRanged), 41 in Death2. `elbow` reaches 13 and `armpit` 13 in script clips (HoeFidget), 7 on bound clips; `robe` 35 in Death and Dead, the hem cap crushed under the corpse; `finger` 12 in the fist. Elbow 7 and armpit 4 are the usual worst. First rig: elbow 47, armpit 29, robe 354 in Pray.

## Sheets (viewer shots, read by me)

`review/sheet_mm9_vs_ours.png` (rest and head tier by tier), `review/sheet_mm9_vs_ours_clips.png` (twelve clip moments, tier A; MM9 is a Blender render with its own light), `sheet_tiers.png`, `sheet_joints_a/b/c.png` (armpits, elbows, neck, waist, kneeling cloth, hem, feet, head, hands in Pray, Cower, Running, AttackRanged3, Death, Dead, Standing, framed on the joint; the body has no visible knees or groin), `strips_a/b/c_1..3.png` (every clip, six frames, every tier), `sheet_ingame.png`, `sheet_chin.png` (under the jaw in the corpse, every tier, after the fix: the band was the front paint's chin shadow; the jaw's own tone at 0.72 now, with a soft blend). Numbers: `review/gates/`. Motion: `review/playback/`.

## Seen and left

- **Mantle corners** stand off as thin points when the arm is raised (AttackRanged3, also the corpse). A stiff cape corner, but it could read as a shard. Not fixed.
- **Shoulders read broad** with the arms bent in Standing: the sleeve is solid, it has no drape.
- **Tier C's beard** is thinner than MM9's full beard; the hood hides the jaw's sides. Faces are harder and more detailed than MM9's soft ones, tier A's brows are heavy.
- **Fingers** in Standing stay rather spread: the hands do not rest on the belt the way MM9's mitten does.
- Robe shading has faint rectangular patches at the chains' joints under grazing light, in Blender more than in the viewer.
- Knots are lumpy gourds: Meshy's shape.
- A small notch at the V under the chin, darkened by the neck shade.
- Hands have some pale mottling left after the low-pass.

## What was not checked

- **Motion by eye at normal speed**: `review/playback/` holds every clip; judged from frames and numbers, nobody watched the videos.
- **Attacks in game**: two tours with spawned hostile monks; they stood, walked and ran, but no attack came into frame. Melee impact, the Sparks release at `palm_left`, the Stone Skin and Heal casts, hit and death in game were not seen. The corpse in game not seen. Which of `castspell1/2/3` MM9 plays for which spell is unread: my binding is a judgement.
- LOD1-3 close up, shadow meshes by eye. Maps where the rows are placed (Lindisfarne), indoor light.
- Sounds, footsteps, DoFX, lunge, `WorkingMonk.scr` behaviour, props.
- Strips and joint sheets are from r11 for the body and clips; the under-jaw paint fix (r13) was checked in `sheet_chin.png` only. The regression ran at r9.
- Android, saves.

User artistic acceptance: "monk OK" (2026-10-31)


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_monk_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_monk_reduce_claude/before/`.


**2026-11-04 later: the reduction was rolled back** (installed source = `mm9_monk_reduce_claude/before/`): the UV audit (`claude_shared/reduction_uv_audit.py`) found reduced faces whose UVs left the painted charts, visible in close-up. A fixed reduction may be reinstalled later; see the ledger.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_monk_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_monk_reduce_claude/before/`.

## MM9 sockets (2026-11-10)

The installed model carries MM9's attach points as `Socket_<name>` nodes for held items (scene `held_items`, MM9's AttachProp), added after this project's install by [`mm9_held_items_claude/scripts/add_sockets.py`](../../props/mm9_held_items_claude/scripts/add_sockets.py) (`Socket_Hoe`, `Socket_Broom`, `Socket_Hammer`, `Socket_Cloth`). A rebuild installed from here drops them: run that script again and install its export (`tools/install_model.py --world mm9`).
