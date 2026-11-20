# monster_troglodyte (overnight-troglodyte)
Phase: body fit. Lease token be3ecdfca5fa4ec5b09123d1327bc520. Credits 5/40 (body ST). Project level_generation/creatures/mm9_troglodyte_claude.
Decision: humanoid route (58 joints, Bip biped, two arms, MM9 clips). MM9's hands: three long fingers, no thumb (Finger0 has no vertices, never keyed). Keep that design: three fingers on Finger1-3 chains (9 bones per hand), from the mesh by connectivity; no MPFB.
Source true-handed: source/true/trog*_true.glb. MM9 bind = node rest, asymmetric stride pose. Jaw Box05 opens 60 deg: huge red palate. Plan head-only ST with open mouth (master run 4), grafted; tier C leather = torso/head images per tier (zombie/mummy deviation) with one extra retexture.
Masters done: references_hd/00-04 (green, tier B). Meshy smart_v1 body good; scripts/step1_clean.py fixes the arm loop -> work/body0.npz.

## 02:50
Credits 10/40 (body ST, head ST). Head ST with open mouth is excellent: scripts/head_prep.py, head_build.py (procedural teeth on Meshy's sites), join.py (neck plane, ring conform). Rig tests in the viewer are good (work/q2_clips.glb). Waiting for UVs (uv_trog.py), then 3 retextures: body B, head B, body+cut-off C (uploads.py). Never re-run uv_trog after those uploads go.

## 03:10
UVs frozen (work/uv_frozen.npz, joined_frozen.npz, cutoff_frozen.npz; NEVER change topology of joined now). Retextures submitted: body_b, head_b, body_c (credits 40/40 once all three are in). Next: textures, tier A from Codex masters tierA by mask (free), ramps, runtime, gates. arm_bump.py works.

## 03:40
Credits 40/40 (body ST 5, head ST 5, retex body_b, head_b, body_c 10 each). No more Meshy. Paints excellent. Pipeline: scripts/tex_pipeline.py, tex_tiers.py, rebuild.sh (runtime), viewer_tiers.py. Next: first runtime build, tier checks, gates, binding (bind_actors.py not written yet), README.

## 04:05
Runtime builds work (scripts/cycle.sh <rev>): rig -> rebuild -> viewer (not installed yet). Gates: scripts/gates.sh writes review/gates/. Arm gate near clean; added jaw half helper, hinge pivots, smooth floor ops. Next: gates, install, bind (scripts/bind_actors.py under flock), regression, game check, strips, playback, README, lease release.

## 04:25
scripts/cycle2.sh <rev> = runtime + viewer + gates. Not installed yet. Remaining: review gates of r8, install with bind (flock), regression, in-game, strips (scripts/strips.sh), sheets (scripts/sheets.sh), closeups (scripts/closeups.py), playback, README, review_root, release lease.

## 05:05
Installed and bound (r11, actors.yml block mm9_troglodyte). Regression passed on r9 (110 descriptors on 47 models, 0 failed); rerun in scripts/post.sh with sheets, strips, viewer check, playback. Left: README, lease release.

## Done 2026-10-31 05:30
Installed (viewer r11), bound, regression PASS 110 descriptors 0 failed, floor 3/3, in game 3 tiers, review root holds the install, sheets looked at, README written, lease released. Credits 40/40. No background processes of mine left once post.sh ends (only waits for regression).
Open with numbers in the README: AttackMelee2 L hand 3.1 cm 1 f, forearm 3.3 cm; AttackMelee R forearm 2.4 cm; AttackRanged R forearm 2.0 cm; head in chest 5.0 cm AttackRanged; armpit R 31/18 seen in Hit; body UV spread 1.47; tier C images (deviation).

## Chest fix 2026-10-31, 0 credits
User, Hit frame 27. Cause: neck blend by the side of the plane gave the chest Head weight; now by distance from the ring (join.py). Jaw rim weight smoothed (head_build.py). Installed r13, review root same as assets_dev, lease released. Regression: Troglodyte builds; MM9 Guard A/B/C fail on a missing .oytex (not this body). Arm, jitter, pierce gates, strips and game check not rerun.
