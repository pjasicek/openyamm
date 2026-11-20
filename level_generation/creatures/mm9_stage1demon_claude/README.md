# MM9 Lesser Demon (mm9_lesserdemon) — 3D actor, 2026-10-31

MM9 `STAGE1DEMON.abc` (97 nodes, 18 clips, skin LESSERDEMON.dtx): MONSTERS.txt row 241 Lesser Demon L70 (`MM9 Demon A`,
family `demon` A/B with the accepted Greater Demon B, `../mm9_greaterdemon_claude/`). 16 placed (Thousand Terrors).
**Humanoid route** by the ABC: a `Bip01` biped with two arms and real three-joint finger chains (thumb + three fingers),
three toe chains per foot, a tail chain, jaw and tongue bones. MM9 skeleton and MM9 clips, never Mixamo.
Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_lesserdemon.glb` (`tools/install_model.py --world mm9`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `mm9_stage1demon_claude` (`scripts/bind_actor.py`, under the flock): `MM9 Demon A`, scale 100 (MONSTERS Scale 1), `yaw_offset` -1.570796327, stride walk 2.39 / run 2.17 (toe joints, `stride.py`), upper body `Bip01 Spine1`, no `look` (MONSTERS HeadTurn 0), melee impact 0.341 s (Hattack1 `Rattack`), ranged impact 0.488 s (rattack1 `RangeAttack`) released at `mouth` = `Xtong` (MM9's RangeAttack node is the jaw pivot) |
| Triangles LOD0/1/2/3 | 12,429 / 6,148 / 2,140 / 940. LOD0: body set 7,653 (skin 3,400, armour shells 1,000, spikes and skirt shards 1,700, tail 400, talons 1,248), head set 4,776 (shell 3,600, teeth 800, eyes 120, tongue 250) |
| Skeleton | MM9's nodes, names and rest rotations; joints unchanged except `Xjawpiv` (moved 13 cm to our mouth corners, children kept in place) and hinge pivots (knee 3 cm back, elbow 1.5 cm back, hip 2.5 cm forward); + 8 half-rotation helpers `*_h` (thighs, calves, upper arms, forearms) keyed by `half_keys.py` |
| Clips (30 fps) | all 18 MM9 clips + Dead. Bound: Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `Hattack1`, AttackRanged `rattack1`, Hit `wince1`, Death `die1`, Dead (die1's last pose). `script_clips`: fidget2, taunt, block, attack_melee2 `Hattack2`, dodge_left, dodge_right, hit2 `wince2`, backpedal, backpedal_run, clop_setup `clopsetup` (MM9's 2-key setup pose). None left out |
| Textures | body 2K colour + 1K normal + 1K ORM; head set 2K colour + 1K normal + 1K ORM. One row, one skin: no tiers; the pass-2 tone is a region mask (`textures/ldemon_region_mask.png`: R hide, G dark armour, B steel) and one grade per region on the shared set (`scripts/grade_regions.py`) |
| Meshy credits | **30 / 30**: body Smart Topology 5, head-only Smart Topology 5, body retexture (4K) 10, head retexture (4K) 10; backup account, balance checked before each (3960 -> 3920), no retries |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_stage1demon_claude/review/viewer/ (revision `r10_ldemon_20261031`, with MM9's own model as a second entry for same-light comparison; the manifest's `focuses` override the six focus names for close-up batches, `scripts/set_focus.py`) |

## Pass 2 (coordinator review, 2026-10-31, 0 credits) - current

Asked: darker MM9 tone, 0 pieces parting, walk floor, knee smudges, Death left hand, an in-game full-body frame, horns.

- **Tone** (`grade_regions.py`, region mask + grade on the shared set, no tiers): hide value compressed above 0.32 (the bright orange speckles) x0.75, saturation x0.8; steel x0.55, saturation x0.5 (gunmetal); gauntlets, greaves and knee cops (dark-armour region, rasterised from bind positions) x0.38. Compared under the SAME light by loading MM9's own GLB in the viewer (`work/mm9_view.glb`, `review/sheet_mm9_vs_ours_samelight.png`): MM9's skin is red with orange highlights and silver plates under the viewer light; ours now reads darker maroon with dark gunmetal and near-black bracers. The earlier MM9 sheet compared a dark Blender render with the bright viewer, which overstated the gap.
- **Detached pieces** (`reweight.py`, rewritten). Why the first reweight changed nothing: it copied the nearest SKIN vertex, but most pieces rest on another piece (shards on the skirt shell, talons in the gauntlet flange, the arrowhead on the shaft, the tongue on the jaw floor), so their roots moved with a different blend than their holder. Now every piece's vertices in or within 3 cm of a holder (all larger components; tail pieces only on the tail and the body above the knees; head pieces on the head) take the barycentric weights of the holder point (LBS is linear in the weights, so they move with that point), faded out to 8 cm; pieces under 30 triangles go wholly onto the holder; pieces under 60 triangles sit 8 mm into the holder (4-influence rounding left 5-10 mm gaps); palms and talons keep their own limb weights; the crotch shards under 30 triangles on the centre line (they stand across the gap the thighs open, lifted 1.3-5 cm whatever the weighting) are removed. Not a merge by distance: the pieces overlap, they share no vertices. Result below.
- **Floor**: the +7.9 cm walk lift came from the smoothed ground-loop grounding the lowest point, which in those frames was the tail tip or a toe claw sinking where MM9's own toes sink (MM9's walk dips -0.5 to -6.3 cm, its run -15 cm at push-off). Fix without moving the root: toe chains (and the tail) bent out of the floor per key (`floor_fix.py --lift-joints ... --lift-only 'Xtail*,Bip01 ? Toe*'`), then only uniform raises. Walk and run keep MM9's root motion (including MM9's own run hop), so the jitter gate sees no added root acceleration.
- **Knees**: the grey-beige smudges are Meshy paint on the knee cops and knee pits (texel density there 411 texels/m against 414 body median: not stretch, not an empty chart, not a region bleed). They get the dark-armour grade now, read as dark knee plates continuing the greaves (`review/sheet_knees_p2.png`, `review/sheet_close_p2.png`).
- **Horns** (`horns.py`): horn vertices of the head shell scaled up to 1.4x about their root (positions only, texels stretch 1.4x): span about +-0.44 m against MM9's +-0.5.
- **Death left hand**: tried longer bump ramps and the palm keeping its own weights; it got worse (see the table), not better.
- **In game**: Isle of Ashes open grass (`isleofashes.odm`, review root, `debug.menu_input_tour_path=review/ingame_tour2.yml`, `tp -12000 0 2500`, one friendly and one hostile `actor spawn 9241`): **full-body frames** `review/ingame4/d01_friendly.png`, `d06.png`, `d07.png` (the demon walking on the grass, feet on the ground, the ranged release in `d05.png`), sheet `review/ingame_sheet_p2.png`. A first try failed while another session was rewriting Guberland (transport routes unresolved), then passed.

| Gate | Pass 1 (r4/r5) | Pass 2 (r10) |
|---|---|---|
| Detached (24 fps) | 32 of 144 | **11 of 132**: the tail's distal piece (119 tris) reads 4.0 cm off XtailD in 293 poses, but its contact vertices carry the same weights as the shaft and no gap shows in the tail close-ups (`review/shots/tl_*.png`); 5 central groin shards of 4-8 tris (lifted 0.9-3.6 cm in DodgeRight, Block, Death); both talon sets float 5.6 mm off the gauntlet flange (left on their own limb weights: holder weights stretched the finger roots to 10x); two chest shards 4-5 mm. **Target 0 not met** |
| Floor audit | walk lifts +7.9 cm | **ok**: stand, walk, living -0.1, dead 0 |
| Arm and hand | Death L 3.0 cm 9 f | **Death L 5.9 cm 51 f (worse)**, Dead L 2.6 cm (corpse, hand under the chest), DodgeRight R 4.6 cm 1 f, Block R 1.3 cm 1 f |
| Jitter | 3 fails (AttackMelee2 L, DodgeLeft L, Death L) | 3 fails: Fidget L (0.98 deg/f, 3.7 mm/f2), AttackMelee2 L (10 mm/f2), DodgeLeft R; all bump corrections |
| Collapse face-frames | Standing 715, Death 8,116 | Standing 838, Walking 1,090, attacks 1,521-3,286, Death 9,063 (worst regions as before: mouth and jaw when it opens, throat in Death) |
| Flat / winding / bones | 0.00 / 0 / 0 | 0.00 / 0 / 0 |
| Texture quality | body 60.0 %, head 56.7 % | body 59.5 %, head 56.7 % (head stretch p90 1.34 from the scaled horns) |
| Regression | PASS 155/63 | **PASS**, 158 descriptors on 65 models, 0 failed (on the installed r10) |

Sheets (pass 2, read): `review/sheet_mm9_vs_ours_samelight.png`, `review/strip_p2_1.png`-`strip_p2_3.png`, `review/sheet_close_p2.png`, `review/sheet_knees_p2.png`, `review/ingame_sheet_p2.png`.

## Route (`scripts/`)
0. **Source**: `convert_abc_model.py --scale 0.0256`, then `mirror_glb.py` on the raw ABC output: `source/tier1/ldemon_true.glb`, true handedness from the start. `bone_length_audit.py` 0 stretching on it. `mm9_data.py` dumps its joints and mesh for the Blender scripts.
1. **Masters** (Codex via `codex_slot.sh`, `scripts/codex_masters.sh`, `codex_head.sh`): inputs are renders of the MM9 model (`ref_renders.py`): `references_hd/` five body views (one correction run: the first 00 had four toes per foot), `references_head/` five head views (open mouth, ram horns). `clean_alpha.py` on all.
2. **Meshy**: body Smart Topology 15k from the body 00, head-only Smart Topology 15k from the head 00.
3. **`step_a.sh`** = `fit_demon.py` (global fit by height without Meshy's 2 m tail; torso Kabsch; each limb segment mapped from estimated joints onto MM9's, rotation + stretch, blended labels; the tail laid along MM9's chain by arc length with the arrowhead rigid at 0.35x; Meshy's fingers were fused, three geodesic tips for four digits, so they and the palm past MM9's knuckle line are deleted, the palm capped, and four talons per hand built as tubes on MM9's own finger chains; the -x half kept and mirrored; Meshy's head pieces dropped), `place_head.py` (head-only model fitted to MM9's head by a similarity ICP with pitch only, x 0, scale x1.2, mirrored; Meshy's own head skin removed in a box and the hole capped; the head's open neck ring capped), `reduce_demon.py` (budgets per part, mirrored again).
4. **Rig** `rig_demon.py`: bone heat on the skin with a clean segment rig (spine, neck chain, arms, legs, toes, tail), armour shells per vertex from the nearest skin (palm to the hand), tail and talons by projection onto MM9's chains, head split by the half-gape plane through the hinge (skull `Xhead`, lower jaw `Xjaw`), tongue `Xtongpiv`/`Xtong`, teeth rigid with the shell under them, the head blended into the neck skin behind the hinge; helpers and pivots. `reweight.py` (in `rebuild.sh`): small pieces per vertex from the nearest skin, the tail's separate arrowhead rigid with the shaft.
5. **UVs** `uv_demon.py` (`claude_shared/uv_atlas.py`, body and head sets, talons and palms denser; **never re-run**: the paints belong to this layout). `geo_fix.py`: soles compressed onto MM9's floor (Meshy's claws reached 9.8 cm under it), positions only.
6. **Textures** `textures.sh` (AO, 4K -> 2K once, gentle grade), `tone.py` (hide toward MM9's maroon: value 0.68, saturation 0.8 on red texels; steel plates -25 % value on the body).
7. **Runtime** `TOKEN=<lease> scripts/rebuild.sh [--install]`: reweight, export (`LIFT` 1.368 = MM9's floor), `clips_mm9.py` (soft joint-offset line, ORBIT hips; `roles_demon.json`), `half_keys.py`, `clip_fix.sh` (`arm_bump.py`, hands out of the body by one smooth bump per contact: Fidget L, AttackMelee2 L, AttackRanged R, DodgeLeft L/R, DodgeRight L, Death L/R), prepare, LODs, shadow shrink, material extras (specular 0, metallic 0), floor (tail bent up from its own joints first, MM9 drags it through the floor; then `floor_ops.txt`: uniform raises, smoothed ground-loop on the gaits, ground-death), `fix_winding.py`, winding check, bone audit, install. Gates: `scripts/gates.sh` -> `review/gates/` (gate numbers below are from r4; r5 changed only the floor smoothing of Walking, Running and Backpedal).

## Checks (final GLB, r4)
| Gate | Result |
|---|---|
| `bone_length_audit.py` | **0 stretching** (12 joints) on source and runtime |
| `check_winding.py` | **0** inverted closed parts |
| `flat_shading_check.py` | **0.00** body, **0.00** head |
| `arm_hand_gate.py --outer-only --exact` (48 fps) | 0 frames over 1 cm in every clip but **Death L hand 3.0 cm, 9 frames** (was 11.5 before the bump; the hand lies under the falling chest), Death R 1.1 cm 1 frame. Forearm (gauntlet) brushes: Fidget2 L 4.4 / R 3.3 cm, Taunt R 4.1, DodgeLeft R 4.2, Hit R 3.0 cm (gauntlet against the chest plates) |
| `jitter_gate.py` against MM9 + helpers | **3 fails**, all from bump corrections: AttackMelee2 L (upper arm 0.89 deg/f, shoulder skin 2.3 mm/f2 over MM9), DodgeLeft L (skin), Death L (upper arm 1.07 deg/f). Gaits and the floor pass are clean after the smoothed ground-loop (the first per-key floor pass failed 23) |
| Collapse (`collapse_gate.py`, every LOD0 primitive, 30 fps) | face-frames: Standing 715, Walking 880, Running 397, attacks 1,434-3,083, Death 8,116, Dead 8,029. Worst frame per region: knees 0-5, hips 0-2, elbows 5-10 (inside the gauntlets; exposed 2-8), wrists up to 19 (AttackRanged R), **head 26-79 and jaw 12-81 in clips that open the mouth** (exposed 8-18), head 172-188 in Death/Dead (the throat and cranium dome fold into the neck with the head thrown back; exposed 0). `review/gates/collapse.txt` |
| `detached_parts_audit.py` (24 fps) | **32 of 144 components part in some pose**: skirt shards of 4-24 triangles up to 7.2 cm (Death), 6 cm (Walking, Running); tongue 2.2 cm in Hit; tail pieces up to 4 cm. Not fixed (see below) |
| `texture_quality.py` | body atlas 60.0 %, spread 1.16, fragments 9.6 %, stretch p90 1.19; head 56.7 %, spread 1.6, fragments 2.2 %, stretch 1.18 (4K source) |
| Regression `--world mm9 --headless-run-regression-suite actors` | `mm9_actor_models_build_every_binding` **PASS**, 155 descriptors on 63 models, 0 failed (r4 and again on the installed r5) |
| `floor_audit.py --world mm9 --match 'MM9 Demon A'` | **flagged**: stand +0.0..+0.2, living -1.3, dead 0, but **walk lifts every foot by +7.9 cm** at one point of the cycle (the smoothed ground-loop grounds the lowest visible point, which in that frame is not a foot: tail or talon). Three floor-pass variants tried (per-key, smoothed 0.3 s: +10.7; 0.1 s: +6.8 with Running -3.7) |

## Sheets (viewer shots unless noted; all read)
`review/sheet_mm9_vs_ours.png` (MM9 is a Blender render of the true-handed source at the same clip times), `review/strip_1.png`-`strip_3.png` (every clip, six frames, 3/4), `review/sheet_close_mouth.png` (mouth open in AttackRanged/Hit/Taunt, Standing head front and side, Death), `review/sheet_close_joints.png` (hips, knees and groin in Walking/Running/DodgeLeft/Death/Taunt from the front and back, shoulders and armpits in attacks, the corpse), `review/sheet_first.png` (bind, head close-ups), `references_hd/selected_views_review.png`, `references_head/selected_views_review.png`, `review/ingame_sheet.png`.

## Decisions and deviations
- **Talons rebuilt**: Meshy fused the three fingers (three geodesic tips). Four tapered tubes per hand on MM9's own chains (thumb + three fingers), as MM9's talon hands; painted by the body retexture. They read plain next to the scaled forearm.
- **Head**: head-only Meshy model (open mouth with tongue, teeth and a closed cavity) placed on MM9's head; the jaw pivot moved to our mouth corners. MM9's jaw opens up to 61 deg past its bind; ours follows MM9 unchanged (the maw gapes wide in AttackRanged and Taunt). Our ram horns are smaller than MM9's wide horns.
- **Tone**: lighter and redder than MM9 even after `tone.py` (MM9 maroon 82/28/22, ours 95/22/10 median on red texels); steel lighter than MM9's gunmetal.
- **Tail**: Meshy's 2 m tail laid on MM9's 1.16 m chain; MM9 drags it through the floor, so the floor pass bends it up from its own joints.
- **Head set colour 2K** as the approved Yrsa route, not 1K.
- One row, one skin: no tiers, no region mask, no ramps (as the Greater Demon).
- FX (`DoFX`, `EndFX`, `lunge`, sounds) not wired, as on the other bodies.

## Not finished / not checked
- Pass 2: detached 11 pieces (not 0; see the pass-2 table), Death L hand 5.9 cm 51 frames and Dead L 2.6 cm (worse than pass 1's 3.0 cm), jitter 3 fails (bump corrections), collapse at the mouth and throat as before. The knee paint is darkened, not repainted.
- Not watched at normal speed; LOD1-3 and shadow meshes not looked at; the projectile's flight from `Xtong` seen only as a release streak in game (`review/ingame4/d05.png`).
- Pass 1 notes below are kept for the record; the pass-2 table supersedes their numbers.

- Floor: Walking lifts the feet by up to 7.9 cm in one part of the cycle (audit tolerance 2.5).
- Gates that fail: Death L hand 3.0 cm (9 frames); jitter 3 clips; 32 detachable small pieces (skirt shards up to 7.2 cm); collapse at the mouth corners and the throat in Death/Dead.
- **Pale patches behind both knees** (Meshy paint), seen in the back views, not fixed.
- **In game**: the Thousand Terrors (`1000terrors.blv`) loads with the review root, but my tour positions from the scene's placements landed in empty corridors: **no frame of the demon in game** (`review/ingame_sheet.png`). Not run on a wide map.
- LOD1-3 and shadow meshes not looked at by eye; playback at normal speed not watched (frames and gates only); the projectile release from `Xtong` not seen.

User artistic acceptance: not recorded


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_lesserdemon_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_lesserdemon_reduce_claude/before/`.
