# MM9 Evil Sorcerer body (mm9_evilsorcerer) — 3D actor, 2026-10-31

MM9 `EVILSORCERER.abc` (31 nodes, 18 clips), rows 156 Evil Apprentice L25 (`MM9 Evil Sorcerer A`, EVILSORCERER1), 157 Evil Sorcerer L35 (`B`, EVILSORCERER2), 158 Evil Grand Sorcerer L50 (`C`, EVILSORCERER3).
Decided from the ABC: a two-armed Biped (`Bip01`, Finger0 and Finger1 per hand), so the humanoid route: MM9 skeleton and MM9 clips, never Mixamo. Not a robe: trousers, two long hanging panels (front, back), hip flaps, plates.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_evilsorcerer.glb` (`tools/install_model.py --world mm9`), variants `es_a`, `es_b`, `es_c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` (`scripts/bind_actors.py`), scale 100 (MONSTERS Scale 1), `yaw_offset` -1.570796327, stride walk 1.25 / run 1.8 (2026-11-04: a planted toe's backward travel over its stance x the clip length; the earlier 0.90 / 1.36 read the jerky keys' median and capped the gait at MM9's speeds, MM9_ANIMATION_AUDIT.md P5; regenerate with `scripts/bind_actors.py 1.25 1.8`), `cast: AttackRanged`, sockets `palm_left` = `LHand1`, `palm_right` = `RHand1` |
| Triangles LOD0/1/2/3 | 13,348 / 6,673 / 2,401 / 798. LOD0: head 2,270, crown 1,194, eyes 118, torso 1,704, legs 1,266, hands 1,198, panels 648 + 822, pauldrons 756, shoes 520, belt 420, boots 420, bracers 420, greaves 340, buckle 296, flaps 480, yokes 476 |
| Skeleton | 78 joints: MM9's 31 + 30 finger bones (15 per side) + 8 panel links (`XPanelF1-4`, `XPanelB1-4`) + 9 half-joint helpers |
| Clips (30 fps) | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget2`, AttackMelee `hAttack1`, AttackRanged `rAttack1`, Hit `wince1`, Death `die1`, Dead; script clips Fidget2 `fidget3`, Fidget3 `fidget4`, Taunt, AttackRanged2 `rAttack1Lame`, ResurrectSpell, Hit2 `wince2`, Death2 `die2`, Backpedal, BackpedalRun |
| Events (MM9's) | `attack_melee` impact 0.36 s (`rattack`); `attack_ranged` and `cast` impact 0.833 s (`rangeAttack`), release `palm_left` (MM9's RangeAttack socket is on LHand1). MM9's `DoFX` hand effects as socket effects on both palms, one hand's emitter on each (2026-11-10, no glow: MM9 has no light there). `DoFX n` plays FX*n*, 0-based (`object.lto` `0x1001af90`; FX0 bluedots, FX1 redyeldots, FX2 greenyeldots): melee `mm9:redyeldots` from 0.36 s, ranged and cast `mm9:greenyeldots` 0.133-1.266 s, `fidget` redyeldots 0.6-1.933 s, `attack_ranged2` redyeldots 0.114-1.657 s, `taunt` greenyeldots 0.141-0.817 s; ResurrectSpell's `DoFX 3` names no column (nothing), and bluedots never plays |
| Textures | Up colour 2048x1024, Low colour 2048x1024 + tier A Low colour 2048x1024, head colour 1K per tier (3), normals and ORM 1024x512 / 1K, region masks 1024x512. 15 images |
| GPU memory | about 20.3 MB for all tiers (BC7/BC5 estimate with mips); three full paints would be 29.4 MB. All variants upload even with one tier on a map (orchestrator's note) |
| Meshy credits | **30 / 40**: body Smart Topology 5, head Smart Topology 5, body retexture B 10, body retexture A 10 (backup account), no retries |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_evilsorcerer_claude/review/viewer/ revision `r11-20261031`, tiers `es_a`, `es_b`, `es_c` |

## Route (`scripts/`)

0. **Sources**: `convert_abc_model.py --scale 0.0256`, `source/es1..3`. **Never `source/true`** (below).
1. **Masters**: Codex, geometry from tier B (`references_hd/`), then a clay head sculpt with crown and flap (`references_head/00_geometry.png`).
2. **Meshy Smart Topology** body and head. Both came back in clean parts (30 and 8 components).
3. `step1_clean.py` -> `assemble.py`: parts labelled, exact mirror symmetry (each pair from its left part, midline parts bisected), head placed by the eyes, back panel straightened and narrowed to MM9's width, back yoke cut to a V, per-part budgets with symmetric decimation. `arm_fit.py`: arms shortened 14 % (Meshy's were 29 % longer than MM9's, the tall crown set the scale). `refine.py`: edge rings at knees, elbows and every 11 cm of the panels.
4. `fit_rig.py`: joints by plane sections, fingers by geodesic merge levels on the hand part, spine heights from MM9.
5. `uv_es.py` (never re-run): `uv_atlas.py`, Up in the top half, Low in the bottom half of one 4K layout, head in its own square.
6. **Paint**: Codex paints on our exact clay renders (`references_paint/`, tier B then tier A), then Meshy retextures at 4K. Heads: Codex paints per tier on the head clay, projected for free (`project_head.py`, from the Thrall's).
7. `compose_es.py`, `finish_es.py` (AO, gentle grade), `tone_es.py` (brass towards MM9's olive gold), `tiers_es.py` (mask + ramps), `head_finish.py`, `tweak.py` (small post-paint moves).
8. `rebuild.sh [--install]`: weights -> GLB (bind in the A pose) -> clips -> arm offset and corrections -> half joints -> panels -> prepare -> LODs -> shadow fix -> ramps -> tier images -> winding fix -> floor -> sockets -> `mirror_glb.py` -> winding -> install. `viewer_update.sh`, `gates.sh`, `closeups.sh`, `strips.sh` review it.

## Findings worth keeping

- **`mirror_source.py` breaks limb lengths on an asymmetric bind.** MM9's bind here is a wide stride. The script applies the partner bone's world motion to this bone's rest, so the clip's bones change length: thigh 0.52 -> 0.32 m, calf 0.39 -> 0.65 in Running; legs read as rubber and feet detached. Raw ABC clips have constant lengths. This body is built in raw space and mirrored last with `mirror_glb.py` (the Lich and Mummy route). Bodies built on `source/true` with an asymmetric bind deserve a length check.
- **`collapse_gate.py` in the Mummy's copy reads only the first primitive.** On a multi-material GLB it silently skips the rest: my first run showed knees and hips at 0. Fixed here (all LOD0 primitives). The numbers below are the fixed gate. Other projects that copied it read only their first material.
- **Panels are not skirts.** Open plates, so `panel_keys.py` keys a four-link chain per clip: MM9's own cloth motion (Box01 > Box14, Box17) as the base, the least extra angle that keeps the plate outside legs, boots, greaves and flaps, a rule that MM9's swing never lifts a link above horizontal (it stood straight up in Death2), a floor limit. Running maximum and Gaussian on the clip's keys.

## Tiers (GPU note from the orchestrator answered with data)

MM9's skins B and C are the same pattern, recoloured (high-pass correlation about 1.0 on filigree, trim, belt, hands). Tier A shares the belt, hands and the chest and pauldron layout, but its panels are plain, thighs green with gold piping, greaves plain steel, bracers tooled leather.
- **One body paint** (tier B). Upper set, four regions: plate field, filigree, sleeves and collar, tunic. Lower set, three regions: field, gems, legs and boots. Ramps map our luminance quantiles to MM9's texels of that region, tier by tier.
- **Tier A's own image only where the pattern truly differs**: its lower set (colour 2.8 MB + normal 0.7 MB). Its upper set is ramps, with tier A's second paint as the ramp target and as the mask that separates filigree from rims.
- **Heads**: one 1K colour per tier, 1.4 MB each (faces differ: young, cruel, old with ritual marks). Normal and ORM shared.
- Deviation from strict shared-set rule: 3 extra colour images and 1 normal, 7.7 MB in all. Bound per tier in the GLB on every LOD (`tier_images.py`); seen in game.

## Deviations

- **Handedness:** `L Hand` +x, `R Hand` -x on a figure facing +Z in the final GLB (true-handed). The cast release is the anatomical left hand as in MM9's data. Inferred from coordinates and names, as on the other bodies.
- **Arm offset:** raw R upper arm 7 deg outward in every clip (`arm_out.py`), one constant offset: MM9's stand rests that hand where our hips are wider. It changes no motion and cleared 3.1 cm in Standing and every clip that starts from it.
- **Limb lengths:** ours, from the mesh; only the Pelvis and Scene Root translate.
- **Hands:** Meshy's five fingers rigged by connectivity (no MPFB graft); finger frames take MM9's Finger1/Finger0 frame, so its curl applies at 0.6/0.5/0.35 per joint (thumb 0.7/0.4/0.2). Full-strength curl stretched fingers to 3.9; now 2.4 at most.
- **Head:** no jaw bone in MM9, mouth closed, head rigid above the jaw line.
- **Tone:** our red is brighter and brass paler than MM9's in the viewer; the gold pass brings it near. Greatest gap: filigree is a larger, cleaner dragon than MM9's blotted knotwork, because Codex drew MM9's blur as dragons. Tier C's dark halos round the gold are stronger than MM9's. Tier A's plate field reads near black where MM9's is navy. Trousers on tiers B and C are lighter and plainer than MM9's near-black mottled wool (the paint's quilting read as stripes through a stronger ramp).

## Checks (final GLB)

| Gate | Result |
|---|---|
| Thighs and legs through panels (`panel_gate.py`, 48 fps, all LOD0 leg vertices) | **Walking 0/58, Running 0/34, Standing, Backpedal, Fidgets, Taunt, attacks, Hit, Hit2, Dead: 0 frames.** Death front 6/58 at 4.2 cm, back 1/58 at 0.2; Death2 back 5/73 at 2.2 (edge of the panel in the fall) |
| `arm_hand_gate.py --outer-only` (48 fps) | Hand depth 0 in Standing, Walking, Running, BackpedalRun, Fidget, Fidget3, Taunt, AttackMelee, Hit, Hit2, Death2, Dead. **Open:** Fidget2 (arms crossed, hand on the other arm) L 4.9 cm 53 frames, R 4.0 cm 47; AttackRanged2 and ResurrectSpell L 4.3 cm 4 frames; Death R hand 2.6 cm 9 frames, forearm 3.4 cm; AttackRanged L 2.0 cm 2 frames; Backpedal L 5.7 cm 1 frame. Finger stretch max 2.36 |
| `jitter_gate.py` against the same clips without corrections | **0 fails** |
| `detached_parts_audit.py` | 1 part flagged 1 cm in 1 of 861 poses (`Death2`, trousers under the belt, hidden). The back panel's 3 cm flag (413 poses) went when its top was tucked under the belt |
| `orient_gate.py` against MM9 | Head mean 0.2-2.0 deg, sole up mean 0-2.4 deg; constant 7.4 deg foot yaw (our toe splay). Max 22.6 deg head in Death (easing), 28 deg foot in AttackRanged (floor raise) |
| `check_winding.py` | 0 inverted closed parts (5 in LOD3 and shadow meshes reversed by `fix_winding.py`) |
| `flat_shading_check.py` | 0.01 / 0.01 / 0.00 |
| `floor_audit.py` | 3 bindings ok: stand 0, walk -1.8..+1.1, living -1.8, dead 0 |
| `texture_quality.py` | Up atlas 58.5 %, spread 1.06, stretch 1.07; Low 55.7 %, 1.08, 1.12; head 60.3 %, stretch 1.16 (spread 3.16: flap is 0.55x and face 1.7x by design). Fragments 0.0 % |
| Symmetry | 0 mm before the rig (exact mirror). MM9's mesh is symmetric, its bind is not |
| Regression `--world mm9 --headless-run-regression-suite actors` | `mm9_actor_models_build_every_binding` PASS, 110 descriptors on 47 models, 0 failed |
| Viewer `run_creature_review.py check` | 54 switches, 0 failed, 0 console errors at r11 |

### Collapse (`scripts/collapse_gate.py`, 30 fps, worst single frame per region, all LOD0 primitives)

| Clip | face-frames | knee L/R | hip L/R | groin | armpit L/R | elbow L/R | neck | head | torso | finger | seen at worst frame (armpit / neck / hip) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Standing | 1513 | 0/0 | 8/5 | 1 | 2/1 | 0/0 | 1 | 0 | 2 | 0 | 2 / 1 / 2 |
| Walking | 1176 | 0/0 | 10/7 | 1 | 11/4 | 0/0 | 1 | 0 | 4 | 8 | 11 / 1 / 1 |
| Running | 680 | 4/0 | 10/11 | 4 | 4/2 | 2/0 | 2 | 0 | 2 | 4 | 4 / 1 / 1 |
| Backpedal | 1187 | 0/0 | 11/7 | 1 | 11/5 | 0/0 | 1 | 0 | 4 | 8 | 11 / 1 / 1 |
| BackpedalRun | 806 | 0/0 | 11/7 | 1 | 11/5 | 0/0 | 1 | 0 | 4 | 8 | 11 / 1 / 1 |
| Fidget | 2397 | 0/0 | 7/5 | 2 | 9/6 | 0/0 | 12 | 0 | 4 | 21 | 6 / 5 / 2 |
| Fidget2 | 1149 | 0/0 | 7/5 | 1 | 11/3 | 0/0 | 1 | 0 | 2 | 0 | 2 / 0 / 1 |
| Fidget3 | 1991 | 0/0 | 13/6 | 3 | 3/2 | 0/0 | 2 | 2 | 2 | 0 | 3 / 1 / 6 |
| Taunt | 982 | 0/0 | 7/5 | 2 | 9/6 | 0/0 | 12 | 0 | 4 | 11 | 9 / 5 / 0 |
| AttackMelee | 648 | 0/0 | 7/5 | 3 | 11/12 | 0/0 | 1 | 0 | 2 | 0 | 5 / 1 / 2 |
| AttackRanged | 1737 | 0/0 | 8/5 | 3 | 28/19 | 0/0 | 9 | 0 | 11 | 27 | 26 / 0 / 9 |
| AttackRanged2 | 2024 | 1/0 | 7/5 | 5 | 18/15 | 0/0 | 15 | 6 | 11 | 6 | 22 / 5 / 0 |
| ResurrectSpell | 2024 | 1/0 | 7/5 | 5 | 18/15 | 0/0 | 15 | 6 | 11 | 6 | 22 / 5 / 0 |
| Hit | 1067 | 0/0 | 11/6 | 3 | 5/2 | 0/0 | 16 | 1 | 3 | 0 | 3 / 3 / 2 |
| Hit2 | 949 | 0/0 | 7/5 | 2 | 5/2 | 0/0 | 4 | 0 | 6 | 0 | 6 / 3 / 5 |
| Death | 1368 | 0/0 | 10/7 | 5 | 30/21 | 0/0 | 16 | 0 | 7 | 0 | 8 / 3 / 2 |
| Death2 | 1583 | 0/0 | 11/8 | 5 | 20/12 | 0/0 | 7 | 1 | 8 | 0 | 23 / 3 / 10 |
| Dead | 465 | 0/0 | 5/5 | 0 | 2/0 | 0/0 | 1 | 0 | 2 | 0 | 1 / 1 / 0 |

Knees and elbows are near 0 after pivots at the outside of the bend and a tight blend. The largest counts are armpits with arms raised or crossed (mostly under the pauldrons) and hips, under flaps and belt. Sheets: `review/gates/`.

## Sheets (viewer shots, read by me)

`review/sheet_mm9_vs_ours.png` (rest and clip extremes, tier by tier), `sheet_tiers.png`, `sheet_close_a/b/c.png` (texture, head), `sheet_joints_b.png`, `sheet_joints_a.png`, `sheet_joints_c.png` (knees, groin, armpits, elbows, neck, head in crouch, running, raised arms, death, corpse), `strips_a/b/c_*.png` (every clip, seven frames, every tier), in game `review/sheet_ingame.png`.

## What was not checked

- **Motion by eye at normal speed**: `review/playback/` holds every clip at normal and half speed; judged from frames, nobody watched the videos.
- LOD1-3 close up, shadow meshes by eye.
- Indoor maps and a map where the rows are placed: the in-game check is `bootcamp.odm`, spawned actors, outdoors. Melee glow on both palms and the lightning release seen in captures. Corpse in game not seen (no console kill).
- MM9's dots recipes have one emitter per hand; the engine spawns the whole recipe on each palm (twice MM9's density per hand). ResurrectSpell has no engine hook (its clip shows its effect when a script plays it).
- Sounds and footsteps, Velocity events of `die1` (MM9 moves the actor while it falls).
- Android, saves.
- Which clip MM9 plays for which tier is unread: `rAttack1Lame` is only a script clip; no script names it.
- Seen and left: a thin dark line under the jaw on the side views (`sheet_close_a.png`, `sheet_close_c.png`, cell 7), the side paints' chin edge; closing the neck band removed the worst of it. A small dark notch at a bracer rim (`cbdd5`), not traced. Underside of the pauldrons has Meshy's mottled paint.

User artistic acceptance: "evil sorcerer - OK" (2026-10-31)


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_evilsorcerer_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_evilsorcerer_reduce_claude/before/`.


**2026-11-04 later: the reduction was rolled back** (installed source = `mm9_evilsorcerer_reduce_claude/before/`): the UV audit (`claude_shared/reduction_uv_audit.py`) found reduced faces whose UVs left the painted charts, visible in close-up. A fixed reduction may be reinstalled later; see the ledger.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_evilsorcerer_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_evilsorcerer_reduce_claude/before/`.
