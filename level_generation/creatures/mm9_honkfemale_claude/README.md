# MM9 Honk female (mm9_honkf) — 3D actor, 2026-10-31

Monster rows Honk (`MONSTERS.txt` 186, `MM9 Honk Female A`, skin HONKF1) and Elder Honk (217, `MM9 Honk Female B`, HONKF3), `HONKFEMALE.abc`. HONKF2 is on no
monster row. Built on the approved MM9 humanoid route ([brief](../claude_shared/MM9_HUMANOID_BRIEF.md)): MM9 skeleton and clips, never Mixamo.
Sister body and shared notes: [`../mm9_honkmale_claude/`](../mm9_honkmale_claude/README.md). History of the day session: `HANDOFF.md`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_honkf.glb`, sha256 `e804475195d0fc...`, identical to `v2/export/mm9_honkf.glb` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `../mm9_honkmale_claude/scripts/honk_binding.yml`: scale 100, stride 1.0 / 3.2, impacts 0.35 / 0.3 / 0.4, release socket `Socket_Beak` (MM9's `RangeAttack` socket sits in front of the hat) |
| Triangles LOD0/1/2/3 | 9,655 / 4,826 / 1,736 / 576 |
| Skeleton | MM9's with `Ponytail*` braids and `Y*` veil chains, plus 15 finger bones per side on MPFB hands; robe on MM9's `X*` chains |
| Clips | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `Hattack2`, AttackRanged `Rattack1`, Cast `Hattack1`, Hit `wince1`, Death `die1`, Dead. AttackRanged and Cast have identical gate numbers: they look like one motion with different events |
| Textures | body 2K colour, normal and ORM 1K; head + hands set the same; one head base colour per tier |
| Meshy credits | **35** on this body: 25 day (Smart Topology 5, body retexture 10, head retexture 10) + **10 night** (Elder head retexture). Pair total 70, of the 75 allowed. Second pass 0. Backup account, no retries |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_honkfemale_claude/review/viewer/ revision `v23-20261031`, tiers `honkf_a`, `honkf_b` |

## Route

Same as the male. Master chain `v2/scripts/master_v3.sh`: `sleeves_v2` -> `robe_lining.py` -> `robe_v3` -> `medallion.py` -> `medal_v3` -> `braid_fix.py` -> `braid_v3`. Runtime: `BLEND=v2/work/braid_v3.blend v2/scripts/build_runtime_v2.sh honkf HonkF v2/scripts/roles_honkf.json`; `arm_pulses.py apply` before the floor pass (`v2/scripts/arm_pulses_honkf.json`, rotations stored), `clip_relax.py` after it, `mirror_glb.py` last.

**Never rerun `texpass_uv.py` or `texpass_head_uv.py`**: the paid paints belong to `work/uv_tp.blend` and `v2/work/head_uv.blend`.

## Night pass 2026-10-30: what was wrong and what changed

| Found | Cause | Fix |
|---|---|---|
| Robe one-sided: from below and from a corpse's feet the far wall vanished and the legs hung in the air | Meshy cloth, back faces culled | Dark lining, rim at the hem, cap at 0.74 m (`robe_lining.py`). MM9 closes the tube with a dark underside; ours now reads the same in a corpse |
| Boots torn under the robe in Death, dark flaps | Only 25-27 % of the boots' weight was on leg bones; the rest on robe chains | Smooth procedural weights on Calf, Foot, Toe0; shafts cut at 0.28 m (0.54 before) |
| Boots through the robe in Death and Dead, 65 folded robe faces at Death 1.13 s | `floor_fix.py --lift-joints Death Dead` bent the floor-side strips up through the legs | Lift removed for Death and Dead. **Also ended the Death floor failure** (dying sank -3.8, tolerance 2.5; it is OK now). Corpse height unchanged |
| Shoe through a hem running along the floor in Standing | Hem at 3 cm, once the boots follow the legs | Hem raised 4 cm with a smooth falloff |
| Braids flying out like tentacles in Death, across the chest in Dead | Ours are longer than MM9's on the same local rotations | `Ponytail*` 55 % and `Y*` 50 % towards Standing in Death and Dead (`clip_relax.py`) |
| **Elder head was tier A recoloured** | Codex repaints would not project | **Meshy head retexture** (10 credits) on the paid UVs with the three repaints as views (`compose_elder.py`). Her own face, dark hair, blue collar, as HONKF3 |
| Blue strokes on the Elder's chest | Ramp mask was a hue test on the old paint | Mask refit to the cleaned paint, closed and smoothed |
| Gap at the throat with the background showing | Head shell's lower ring and the robe's neck ring did not meet | Neck skirt: the ring extruded 5 cm down and in, hidden under the robe (`medallion.py`) |
| Medallion: black and white flecks, moved with the braids | Meshy | Clean disc rigid on Spine2, art from the head master (`medallion_paint.py`); the old one painted on the chest went too |
| Flesh blotches on the collar | Meshy | Back to linen with real weave |

A smooth hand push for Death and Dead was tried and removed: Dead went from 3.1 to 4.4 cm (`hand_rest.py` casts horizontally, and on a corpse the belly faces up).

Feet turn 12 deg along the leg in the fall, not the male's 40: MM9's are already at 43-55 deg from the leg in the corpse, and 40 straightened them into a lump.

**Handedness:** `mirror_glb.py` last, same convention as the male (`L Hand` at x -21.3 in the raw ABC). Inferred, not compared with MM9 footage. `v2/work/mm9_honkf_floor1.glb` is the unmirrored build, and the arm offset's sign in `arm_offset.py` is for it.

## Second pass 2026-10-31 (coordinator's review)

**1. Hand through the robe (the point of the pass).** The "torn gap" was the wide sleeve's cuff buried in the belly (forearm 7.8 cm, hand 3.1), not a tear: nothing in the skinning was open. The gate's Death peak was a separate contact: at 0.46-0.67 s her bells cross and the right hand runs up to 11.8 cm into the left sleeve. Two slow leans, `v2/scripts/arm_pulses.py`, solved for the least turn, each one constant rotation with one ramp, never per key:
- `right_lean`: upper arm 14.5 deg, 0.05-1.0 s, holding through the corpse;
- `left_stoop`: upper arm 11 deg, 0-0.58 s, holding through the corpse.
A pulse that rose and fell, and one split across both arms, failed the jitter gate (up to 1.82 deg/f excess) and were dropped.

**2. Braid tips.** Two different things, and neither was what it looked like.
- The orange shards on the trim are **paint**: Meshy painted the braid tips onto the robe. They are in the same place in every pose and on both tiers, orange beside the Elder's dark braids. 5,363 texels painted out (`medallion_paint.py shards=`).
- Separately `scripts/hair_gate.py` (male project; edge against body cloth triangle, 48 fps) found the strands crossing the robe in **every frame of every clip**, 243 edges at rest: they ran through the chest from 1.53 m. `v2/scripts/braid_fix.py`: bands of each strand slide out over the chest 1-2 cm, and below 1.44 m the strand takes the weights of the cloth under it. A single chest bone failed: when she bows the tips swing back into the belly (220 edges).

| Clip | Frames crossing, before | After | Worst edges before -> after |
|---|---|---|---|
| Standing | 73/73 | **0** | 243 -> 0 |
| Walking | 49/49 | **0** | 291 -> 0 |
| Running | 25/25 | 5/25 | 218 -> 1 |
| Fidget | 193/193 | 43/193 | 311 -> 5 |
| AttackMelee | 34/34 | **0** | 259 -> 0 |
| AttackRanged, Cast | 29/29 | 7/29 | 263 -> 38 |
| Hit | 44/44 | 11/44 | 253 -> 9 |
| Death | 73/73 | 26/73 | 272 -> 22 |
| Dead | 49/49 | **0** | 208 -> 0 |

The "before" column counted the hidden neck skirt as cloth, the "after" column does not: compare with that in mind. What remains is mid-strand (rest height 1.33 m) against the moving sleeve and the fold when she bends. **Cost:** the strand is pinned to the chest, so it folds in the bow: 27 faces in AttackRanged, reported under `waist` below, and it kinks in `sheet_joints.png` j8.

**3. Neckline.** Meshy's ragged skin patch replaced by one smooth curve: skin inside an ellipse, linen with real weave outside, a thin soft shadow along it (`medallion_paint.py neckline=`). The Elder's blue follows the same curve. The cleaned zone is a little smoother than the weave beyond it (`sheet_joints.png` j7, j9).

**4. Dark cap.** One plain dark patch, a planar cap joined to the lining by a strip. Plain in j3 and j5.

**Egg release.** At the event (AttackRanged 0.3 s) `Socket_Beak` is 3.8 cm from the goose beak's tip, which the bow has swung level and forward (`review/sheet_impact.png`): the egg comes from the goose on her hat. Not caught in flight in game.

Also: `floor_ops.txt` unchanged at `--smooth Death 0.09`, because tighter smoothing fails jitter; a 2 mm Gaussian lift at 1.0 s (`clip_relax.py --lift`) keeps the dying floor inside tolerance with the arms leaning. `shrink_shadow_lods.py` turns a flattened braid in the lowest shadow LOD right way out. `arm_hand_gate.py --outer-only` skips faces with no UV area.

## Checks (final GLB)

| Gate | Result |
|---|---|
| `check_winding.py` | 0 inverted closed parts |
| `flat_shading_check.py` | 0.02 / 0.00 |
| `../mm9_honkmale_claude/scripts/robe_gate.py` (48 fps, edge against triangle) | **Boots through the robe: 0 frames in all ten clips**, including Walking, Running, Death, Dead; inner shell 0 |
| `sleeve_gate.py` (24 fps, four views) | Forearm poke 0 frames; see-through worst 21 px (Death R above34), 17 Death L, 15 AttackMelee, 14 Hit, of 160 x 160 |
| `arm_hand_gate.py --outer-only --exact` | **Death R 0 (was 5.3 cm, 18 frames over 1 cm), Dead R 0 (was 3.1, 49)**, Hit L 2.2 (6), Fidget R 1.2 (3), others under 1. Before the no-UV filter: Death R 3.1 cm for 3 frames, the fingertips against the left sleeve's lining. Finger stretch max 4.97 (Death L) |
| `jitter_gate.py` against `v2/work/mm9_honkf_armout.glb` (MM9's clips + the constant 8.5 deg arm offset) | 0 fails |
| `detached_parts_audit.py` | **2 flagged: both boots**, by design: they hang free inside the tube, as MM9's foot mesh does. Bind gap 3.8 to 4.1 cm |
| `floor_audit.py` | OK on both: stand 0, walk -0.3..+0.2, living -2.4, dead 0 |
| `mm9_actor_models_build_every_binding` | 101 descriptors on 44 models, 0 failed |
| `run_creature_review.py check` | 20 switches, 0 failed, 0 console errors |

`texture_quality.py`: body atlas 57.1 %, fragments 0.0 %, stretch p90 1.13. Head + hands atlas 41.1 % (59.5 % on the head square), spread 1.1, fragments 0.6 %, stretch p90 1.44. Body spread prints a meaningless value because linings sit on one texel. Median density 1,475 px/m body.

### Collapse gate (`scripts/collapse_gate.py` in the male project, 30 fps, worst single frame per region)

| Clip | armpit L/R | elbow L/R | hand L/R | hair | waist | robe | leg L/R | groin |
|---|---|---|---|---|---|---|---|---|
| Standing | 3 / 1 | 0 / 2 | 1 / 1 | 1 | 1 | 0 | 0 | 0 |
| Walking | 3 / 1 | 9 / 3 | 5 / 1 | 0 | 2 | 0 | 0 | 1 |
| Running | 20 / 8 | 10 / 13 | 6 / 4 | 2 | 4 | 7 | 2 / 7 | 0 |
| Fidget | 8 / 3 | 16 / 11 | 9 / 4 | 2 | 3 | 0 | 0 | 0 |
| AttackMelee | 7 / 2 | 2 / 15 | 5 / 5 | 6 | 4 | 0 | 0 | 0 |
| AttackRanged, Cast | 5 / 3 | 4 / 10 | 5 / 3 | 1 | 27 | 0 | 0 | 8 |
| Hit | 11 / 5 | 24 / 20 | 5 / 4 | 8 | 16 | 0 | 0 | 0 |
| Death | 17 / 5 | 28 / 10 | 8 / 2 | 4 | 20 | 0 | 13 / 15 | 3 |
| Dead | 0 / 3 | 3 / 10 | 3 / 2 | 0 | 7 | 0 | 1 / 10 | 0 |

Non-zero, and many are exposed (`review/gates/collapse_gate.txt`). Worst: Death elbow L 28, AttackRanged and Cast waist 27 (the pinned braids, see second pass), Hit elbows 24 and 20. Robe in Death fell from 76 to 0. Looked at in `review/sheet_joints.png`: creases of a wide sleeve, with no tear or flap. An observation, not a pass; no target was set for these bodies.

## Hide and pattern against MM9

MM9's linen is soft with a fine weave. Ours keeps the colour but its weave is **coarser, burlap-like at close range** (`sheet_close_honkf_a.png`), coarser than the male's, and the knot bands are bolder than MM9's. At game distance it reads as linen. Skins are fully opaque; no glow.

## Sheets (viewer shots, all read)

`review/sheet_compare.png` (MM9 vs ours), `sheet_tiers.png`, `sheet_close_honkf_a/b.png`, `sheet_joints.png`, `sheet_cuffs.png`, `sheet_impact.png` (egg release), `strips_left.png` and `strips_front_b.png` (every clip, 7 frames), `strips_left_before.png`, `close_before.png`. In game: `review/ingame_sheet_v3.png`, `ingame_sheet_v3_eggs.png`. Numbers: `review/gates/`.

## Deviations and open points

- **Symmetry not met:** MM9's bind pose is symmetric to 2.9 mm. Ours median 5.0 mm, p95 16.5, max 68.6 (skirt). Mirroring under the paid paint needs a repaint.
- **Elder chest:** the blue now follows the clean neckline ellipse, but it reads as a separate shape round the neck plate. The short strand tips show as brown flecks beside the collar now that they lie outside the robe (`sheet_close_honkf_b.png` t1, t2).
- **Goose hat:** the brim's front centre is a plain gold patch where Meshy painted the skull. MM9's brim is plain, so left. The brim sits low, at the brows.
- **Paint residue:** faint pale smudges below the trim where the shards were (`sheet_joints.png` j12, j11). The chain ends in a short pale stub by the medallion, which it used to run into.
- **Thin spike** by the left sleeve in Death (`sheet_joints.png` j4), needle thin, not traced.
- Eyes read wide and staring on tier A; the Elder's are better. Her hands and head skin differ slightly in tone.

## What was not checked

- Normal-speed playback was captured (`review/playback/`), but judged from its frames: nobody watched the videos.
- Egg release in game: eggs fly and one was seen beside an Elder's head, but the release frame was not caught. `Socket_Beak` is confirmed on the viewer pose only.
- Foot sliding in game (walk stride 1.0 is an estimate: `stride.py` read 0.5 m), LOD1-3 and shadow meshes by eye, outdoor light.
- Symmetry on the final mesh: measured on `work/label_v1.blend`, before the graft.

User artistic acceptance: "honk female - good" (2026-10-31)


## Third pass, hands (2026-10-31)

User feedback: the hands looked grafted (`review/user_feedback_hands_20261031.png`, female).

Cause: not the pass-2 leans, which touch only Death and Dead while the fault shows in Standing. The graft itself was short and bent at bind, the forearm tube was thin and only 5-8 cm long, and the cuff sat off the forearm line. All of it predates pass 2.

Changes: `v2/scripts/hand_fix.py` scales the hand and its finger bones about the wrist and centres the sleeve on the forearm; `v2/scripts/wrist_fix.py` adds one constant Hand rotation to every clip to reach MM9's wrist line; thicker, shorter forearm tube in `sleeve_lining`; lining clamp in `robe_lining.py`. `v2/scripts/master_v3.sh` holds the third-pass chain. 0 credits spent.

Numbers: Hand 12.7 -> 16.5 cm (scale 1.30; MM9 16.8). Standing wrist bend L/R 22.4/20.8 -> 4.7/9.1 deg (MM9 5.0/9.3); Walking 32.5/26.0 -> 14.0/10.7 (13.6/10.8); Running 19.4/18.2 -> 15.5/21.8 (16.6/22.1); AttackRanged 27.5/27.9 -> 10.0/14.5 (10.5/15.5); Hit 33.3/28.4 -> 17.8/12.1 (18.5/13.1). Cuff centre to forearm line in Standing 9.7/10.2 -> 4.1/4.3 cm. Forearm skin radius 2.2-3.6 cm (was thin tube, end radius 1.2 cm). Sleeve slid 2.9/4.6 cm; hand constant rotation 24.7/22.4 deg.

Measurements: `review/hands/measure_before.txt`, `measure_after.txt`. Acceptance sheets, full size, Standing, Running 0.08 (raised), Walking 0.25 (low), front, left and quarter: `review/hands/accept_*.png`.

Export hash `65ec9bb2890d`, viewer revision `v26-20261031`.

Gates on this build (one run): jitter 0, robe gate 0 in every clip, regression `mm9_actor_models_build_every_binding` passed, winding 0 inverted. Arm gate: hands in the body 0 in every clip but Fidget L 0.9 cm (0 frames over 1 cm); Death and Dead R 0, so the pass-2 gain holds. Sleeve worst 29 px (Death R above34), was 21 px; poke max 15.

Open: a small brown spot on the raised sleeve (Running 0.08, front); short dark lines on the robe in Running, lining edges crossing the outer wall. Not rerun: floor audit, hair gate, collapse close-ups, standard sheets, in-game check, forearm/hand join close-ups.

## Sleeve poke fix (2026-10-31)

User feedback: forearm skin came through the outer right sleeve near the cuff (`review/user_feedback_sleeve_poke_20261031.png`).

Cause: the stump of the hand graft, hand-flagged, stood 7.4 cm off the forearm axis on the right and 6.0 cm on the left, where the arm is under 3 cm. `hand_fix.py` had also scaled it, and centring the sleeve moved the wall past it.

Change: `v2/scripts/forearm_tuck.py`, the last step of `master_v3.sh`, puts skin and stump vertices between t 0.35 and 0.92 back on a 3.0-3.2 cm limit around the forearm axis (L 38, R 55 vertices). Hand size, wrist line, weights, UVs and the sleeve do not change. `scripts/forearm_poke.py` lists the vertices outside the cloth per clip. 0 credits.

Sleeve gate, poke frames: right arm 13-97 per clip, poke max 15 -> 0 in all ten clips; left arm stays 0. See-through worst 29 px (Death R), unchanged. Regression `mm9_actor_models_build_every_binding` passed, winding 0 inverted. Export hash `0bc065912f51`, viewer revision `v27-20261031`. Shots: `review/hands/poke_fixed_arms.png`, Standing, both arms, front and inner quarter.

Open, seen in those shots: a skin-coloured sliver on the far inner edge of the right cuff, on the cloth and not skin geometry (no skin vertex lies past 3.3 cm there), so likely texture; the forearm reads as a pointed tip inside the right cuff from below; a thin cloth spike at the left cuff, seen front on. Not rerun on this build: jitter, arm, robe, hair, collapse and floor gates, acceptance sheets for all tiers, in-game check. Only forearm rest geometry changed, not clips. The brown spot on the raised sleeve was not rechecked.

## Dropped-clip pass, 2026-10-31 (run 2, 0 credits)

`v2/scripts/extra_clips.sh honkf source/mm9/honkf1.glb`: the same 12 clips (arm_offset 8.5, `hand_rest_honkf_extra.txt`, wrist_fix, floor, `clip_relax_honkf_extra.txt`, mirror), grafted with `claude_shared/graft_clips.py`. Bound as script clips. Robe gate 0 in all 12; Cower hands at the face 5.1 cm. Numbers, strips: `review/clips_restore/`; summary `devdocs/mm9_rework/overnight/status/clips_groupA.md`.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_honkf_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_honkf_reduce_claude/before/`.


**2026-11-04 later: the reduction was rolled back** (installed source = `mm9_honkf_reduce_claude/before/`): the UV audit (`claude_shared/reduction_uv_audit.py`) found reduced faces whose UVs left the painted charts, visible in close-up. A fixed reduction may be reinstalled later; see the ledger.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_honkf_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_honkf_reduce_claude/before/`.

## MM9 sockets (2026-11-10)

The installed model carries MM9's attach points as `Socket_<name>` nodes for held items (scene `held_items`, MM9's AttachProp), added after this project's install by [`mm9_held_items_claude/scripts/add_sockets.py`](../../props/mm9_held_items_claude/scripts/add_sockets.py) (`Socket_pamphlet`). A rebuild installed from here drops them: run that script again and install its export (`tools/install_model.py --world mm9`).
