# MM9 ghoul body (mm9_ghoul) — 3D actor, 2026-10-31

Rows 174 Ghast L20 (`MM9 Ghoul A`, GHOUL1), 175 Ghoul L27 (`B`, GHOUL2), 176 Revenant L38 (`C`, GHOUL3), `GHOUL.abc`, 54 nodes, 16 clips. The inventory row lists Ghast (1), Ghoul (8), Revenant (1).
**Humanoid** by the ABC: `Bip01` skeleton, two arms, two legs, five real finger chains per hand, plus `Bone01` and `Bone03`, which are the loincloth's front and back flaps. Built on the approved MM9 humanoid route ([brief](../claude_shared/MM9_HUMANOID_BRIEF.md)): MM9 skeleton and clips, Meshy body and head, sharp textures. Progress, hashes, Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_ghoul.glb` (`tools/install_model.py --world mm9`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, `MM9 Ghoul A/B/C`, skins `ghoul_a/b/c`, `scale: 100`, `yaw_offset: -1.570796327`, stride 1.85 / 2.75 (measured, `stride.py`), look `Bip01 Neck, Bip01 Head`, `cast: AttackRanged`, melee impact 0.426 s (Hattack1 `Rattack`), ranged and cast 0.8 s (rAttack1 `RangeAttack`) released at `throw_hand` = `Bip01 R Finger11` (MM9's RangeAttack node is the right hand) |
| Triangles LOD0/1/2/3 | 9,988 / 4,983 / 1,774 / 813; LOD0 body set 5,304, head set 4,684 |
| Skeleton | MM9's nodes, names and rest rotations; the hands were laid onto MM9's own finger joints, so no new finger bones. Added: 10 half-rotation helpers (`*_h`: hips, knees, elbows, shoulders, neck, head), keyed by `half_keys.py`. Hinge pivots moved: knee 3 cm back, elbow 1.5 cm back, hip 2.5 cm forward |
| Clips | 30 fps: Standing `stand`, Walking `walk`, Running `run` (MM9 has one here), Fidget `fidget1`, AttackMelee `Hattack1`, AttackRanged `rAttack1`, Hit `wince1`, Death `die1`, Dead; script clips Fidget2, Taunt, Hit2, Death2, ResurrectSpell, Backpedal, BackpedalRun |
| Textures | body 2K / 1K normal + ORM; head set 2K / 1K; region masks 1K. One shared set, no per-tier images |
| Meshy credits | **30 / 40**: body Smart Topology 5, head-only Smart Topology 5, body paint 10, head paint 10 (backup account, no retries) |

## Route (`scripts/`)
0. **Sources**: `convert_abc_model.py` per skin, `mirror_glb.py` on the raw ABC output: `source/g*/ghoul*_true.glb`, true handedness from the start. `bone_length_audit.py` is clean on the raw and true sources.
1. **Masters** (Codex): `references_hd/` five views, `references_head/` five busts, from MM9 renders. Very close to MM9; `clean_alpha.py` removes the soft halo.
2. **Meshy**: a clean closed body, separate teeth, eyes, studs, a sheet of hair and two open flap sheets. The head-only model is a doubled shell with hair strips over a real neck, and a real mouth pocket.
3. **`step_a.sh`** = `fit_ghoul.py` (limb segments mapped joint for joint, arms stretched 1.42 / 1.27; the palm swung and twisted onto MM9's palm, each digit laid along MM9's own chain; the near half mirrored, MM9 being symmetric), `head_ghoul.py` (outer faces by rays, near half mirrored, ears brought in to MM9's span, hair voxel-closed), `graft_ghoul.py` (trapezius lowered 8.5 cm, body voxel-remeshed for Meshy's specks and folds with the hands kept as fitted, a clean neck tube, flaps rebuilt as low grids through Meshy's sheets).
4. **`quick.sh`** = `reduce_ghoul.py` (budgets, then the right half mirrored), `rig_ghoul.py` (bone heat, rules by part, digits by a level-set tree, `digits2.py`), clips and gates.
5. **UVs** `uv_ghoul.py`. **Never re-run**: the paints belong to these layouts. `repack.py` then splits the long limb charts and packs again without new flattening, and `repack_maps.py` warps Meshy's 4K maps straight into the new layout (one resample). `textures/old_layout/`, `work/faces_oldlayout.npz` keep the first layout.
6. **Textures** `textures.sh`, then `finish_tex.py` (detail band cut, belt front projected from the master, claws), `tier_ghoul.py`, `veins.py`.
7. **Runtime** `TOKEN=<lease> REV=<rev> scripts/rv.sh --install` (`rebuild.sh`): `reweight_ghoul.py` (applies the split UVs, flap weights, thumb roots, flap tops tucked under the belt, belt lumps out), `export_ghoul.py` (flap lining and rim, skull plug), `clips_mm9.py`, `flap_keys.py`, `half_keys.py`, `clip_fix.sh` (`lower_clip.py`, `arm_bump.py`), prepare, LODs, shadow fix, ramps, floor, `smooth_lift.py`, winding, bone length audit, viewer.
`scripts/final_run.sh` runs gates, close-ups, strips and playback in order.

## Checks (final GLB, revision r16)
| Gate | Result |
|---|---|
| Flaps, `flap_gate.py` (48 fps; flap vertex under the thigh, hip or belly skin, over 3 mm past its rest depth) | **Walking 0/53, Running 0/33, both flaps.** Bound clips: Death 1.1 cm 13/73, Fidget 1.1 cm 60/194; script Death2 1.1 cm 3/73; all others 0 |
| Collapse, `collapse_gate.py` (both LOD0 primitives, 9,988 of 9,988 triangles: `prim_cover.py`) | table below; knees 0 to 2, elbows 1 to 5 |
| `bone_length_audit.py` | **0 stretching**, 12 joints. The hips first read 19 %: our own bug, see Decisions |
| `arm_hand_gate.py --outer-only --exact` | **0 frames over 1 cm in every bound clip** but Death L 1.0 cm 1 frame. Script Death2: L hand 4.9 cm 2 frames, forearm 5.3 cm; R 1.2 cm 1 frame |
| Finger stretch | p99 at most 1.47, max 3.11 on one 4 mm edge at the thumb root (under a centimetre of movement) |
| `jitter_gate.py` against MM9 + helpers | **3 flags in 2 clips**: Death L, Death2 L and R, see below. Every other clip clean, Standing, Walking, Running, attacks and hits included |
| `floor_audit.py --world mm9` | **ok, 0 problems**: stand +1.3..+1.8, walk -1.2..+1.2, living -1.2, dead 0 (world units) |
| `detached_parts_audit.py` (24 fps) | 39 components, **0 detached** |
| `flat_shading_check.py` | 0.01 body, 0.00 head |
| `check_winding.py` | 0 inverted |
| `texture_quality.py` | **body atlas 58.6 %, spread 1.15, fragments 0.2 %, stretch 1.11, 1,568 px equivalent**. Head 61.0 %, spread 1.66 and fragments 2.9 % (read from the Meshy upload: the skull plug's zero-size UV inflates the figure on the runtime GLB), stretch 1.18 |
| `--headless-validate-actor-models` | 119 descriptors on 50 models, 0 refused (the world at the time of the last run) |
| `--world mm9 --headless-run-regression-suite actors` | `mm9_actor_models_build_every_binding` **PASS** |
| `run_creature_review.py check` | 48 switches, 0 console errors |
| In game (review root, `bootcamp.odm`) | `review/ingame_sheet.png` (Ghast, Revenant, attacks, run, hit, corpse poses), `review/ingame_tier_b.png` (Ghoul) |

Collapse, worst frame (`review/gates/collapse.txt`), and who owns those faces (`review/gates/collapse_parts.txt`, by weight):

| Clip | knee | groin | elbow | armpit | ankle | neck/head | body | exposed body | face-frames | Mostly |
|---|---|---|---|---|---|---|---|---|---|---|
| Standing | 0 | 0 | 4 | 1 | 0 | 0 | 5 | 5 | 647 | wrist, thumb root |
| Walking | 0 | 2 | 0 | 1 | 1 | 0 | 5 | 4 | 139 | |
| Running | 1 | 4 | 5 | 1 | 7 | 0 | 47 | 37 | 862 | back flap 24, thumb roots 20 |
| Fidget | 0 | 5 | 3 | 12 | 0 | 5 | 10 | 5 | 2651 | armpits, hidden |
| AttackMelee | 0 | 4 | 3 | 15 | 2 | 7 | 17 | 11 | 413 | armpit in the swing, hair 11 |
| AttackRanged | 0 | 2 | 3 | 1 | 0 | 3 | 5 | 5 | 370 | |
| Hit | 0 | 2 | 3 | 8 | 2 | 0 | 16 | 6 | 479 | |
| Death | 1 | 7 | 3 | 4 | 1 | 9 | 70 | 1 | 514 | hair 71, hidden under the head |
| Dead | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 62 | |
| Script: Death2 | 2 | 16 | 3 | 14 | 0 | 1 | 144 | 35 | 2595 | back flap 100, front flap 36 |

**Not zero, with why (second attempts done):**
- **Collapse is not zero.** Skin joints are low: knees at most 2, elbows at most 5. Armpit 15 at the top of AttackMelee, a few exposed. The larger counts are cloth and hair, not joints: the back flap folds where it meets the buttock when the thigh swings behind it (Running 24 faces, script Death2 100), the hair mass folds against the back in Death (71, under the head). Widening the flap's weight band took Walking's body count from 23 to 5.
- **Jitter, 3 flags**, the two falls only. Death L upper arm 1.65 deg/f, shoulder skin 5.6 mm/f2; Death2 upper arm 1.4 deg/f (R), skin 3.7 mm/f2 (L). Causes: the hand-clearing bump (the hand goes 8.1 cm into the body without it, in a brief contact) and the corpse's rise off the floor, MM9's fall goes 13 cm under it. `smooth_lift.py` took the rise's own acceleration from 116 to 6 mm/f2. Trading the bump away would put the hand back in the body, so it stays.
- **Script clip Death2** carries the worst numbers: hand 4.9 cm, flaps. Nothing binds it as the dying clip.
- **Cloth 1.1 cm** in Death and Fidget: front flap into the raised thigh at the end of its travel.

## Tiers
One shared body and head set; every tier is ramps, so no per-tier images and no deviation. Regions: body R hide, G veins; head R hide, G nose hollow.
Ramps come by luminance rank from the hide texels of MM9's own three skins, at tone 0.80 / 0.78 / 0.74.
- **Ghoul veins**: MM9's GHOUL2 has glossy pale veins that GHOUL3 lacks. `veins.py` takes that difference from MM9's own surface (ours is fitted onto its bind pose) into a region, 1.2 x lighter on tier B. They read as a soft mottle, not MM9's crisp lines: GHOUL2 is 256 px.
- **Revenant's nose**: MM9's C skin rots the nose to a hollow. Same mesh, a head region that goes near black on C only. It is paint: no real cavity.

## Decisions and deviations
- **Handedness**: raw ABC space with `mirror_glb.py` last, not `mirror_source.py`. `Bip01 R Hand` at x -0.798 of the true GLB. No held weapon.
- **Hands**: five digits with long claws, as MM9. Meshy's fingers, laid onto MM9's chains so its curl reads as authored; no MPFB graft, and no finger aliases. Claws are painted black to the tip in `finish_tex.py`, because Meshy painted skin over our longer fingers.
- **Mouth**: MM9 has no jaw bone and no clip opens the mouth: a fixed snarl, slightly more open than MM9's, with Meshy's real cavity. A dark plug in the skull stops back-face culling from showing the sky through it.
- **Head**: colour 2K as Yrsa's approved route, not 1K. Ears brought in 18 % past 12.5 cm to MM9's span.
- **Neck**: Meshy's neck under the hair could not be saved, so a clean tube runs from the shoulders up into the skull and the jaw lies over it, as on the Mummy. A faint line shows where they meet (`review/close_a/Death2_7.png`).
- **Hair**: a closed voxel mass, narrowed and lengthened to MM9's wedge, Head to Spine3 weights.
- **Flaps**: rebuilt as low grids, since Meshy's sheets mirrored into a crease. The front flap drapes (top and sides ride the skin under them, centre and tip on `Bone01`, keyed by `flap_keys.py`, up to 73 deg in Running). MM9's own flaps hang still and the thighs pass through them. The back flap rides the skin at the top and hangs from `Bone03`.
- **Belt**: Meshy scattered white blobs and lumps over the front, so the mesh studs and plate were dropped and the master's front (skull disc, woven plate, studs, brass) is projected flat, as MM9's is. Its back and sides are Meshy's paint.
- **Hip orbit bug (ours)**: MM9's thigh node orbits its parent at constant length. Adding the clip's offset to our moved hip pivot stretched the hip 19 %, found by `bone_length_audit.py`. `clips_mm9.py` `ORBIT` now turns our rest offset by the same rotation. **`clips_mm9.py` in other projects with a moved hip pivot may carry the same bug.**
- **Region order bug (ours)**: regions mix in order, in the shader too, so a later region must lie over the full first one. Subtracting it bled the tan base through as smudges.
- **Running** is lowered 11 cm against the corrected root, because MM9's run floats. `root_lift` corrected once for all clips: they all sat 6.3 cm low.
- Skins are opaque. FX `bluedots`, `greenyeldots`, `redyeldots`, `DoFX`, `playanimsound`: not wired, as on the other bodies.
- **In game, corpses vanish**: a killed spawned ghoul goes shortly after falling and leaves a bag. The Zombie, run beside it as a control, does the same, so this is not this body. The Dead pose was checked in the viewer and with `model play`.
- **Lighter than MM9**: every tier reads lighter and cleaner than MM9, partly the viewer's bright light (`review/sheet_mm9_vs_ours.png`). Tier A is olive in game, yellower in the viewer. The feet run pale on B and C, the palest paint meeting the top of the ramp.
- **Pebbles**: the hide is less pebbled after the band cut and with normals at 0.3, but the body still reads a little pebbled up close, more than the face.
- **Rows at their sprite height**: the health bar floats as on other MM9 bodies.

## Sheets (viewer shots unless noted)
`review/sheet_mm9_vs_ours.png` (MM9 is a Blender render with its own light), `review/sheet_tiers.png`, `review/sheet_closeups_a.png`, `_b.png`, `_c.png` (knees, groin, armpits, elbow, neck, mouth in the crouch, the attack, Death, Death2), `review/sheet_closeups_death_a.png`, `review/strip_a_1.png`, `_2.png`, `strip_b_*.png`, `strip_c_*.png` (every clip, every tier, eight frames), `review/masters.png`, `review/front_map.png` (belt, atlas projected), `review/ingame_sheet.png`, `review/ingame_tier_b.png`. Numbers: `review/gates/`.

## Not checked
LOD1-3 and shadow meshes by eye; any real map (`bootcamp.odm` only: no Ghoul placement was visited); the projectile's flight from `throw_hand` and the green cast effect's origin; bloom; fullbrite in the skins; the Android cook. Tone by eye is approximate: the viewer's light is much brighter than MM9's Blender render, and both differ from the game's. Playback: `run_creature_review.py playback` recorded 32 runs (`review/playback/`) with no errors, but I read frames, not motion: smoothness rests on the gates and strips. All clips of all tiers were read on the eight-frame strips, at contact-sheet size.

User artistic acceptance: "ghoul OK" (2026-10-31).


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_ghoul_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_ghoul_reduce_claude/before/`.
