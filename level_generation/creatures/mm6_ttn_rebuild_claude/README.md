# MM6 Titan: five-finger hands and the Cast recovery (rebuild stream, 2026-11-11)

Audit fix ([audit](../audit_mm678_20261111/README.md) finding 5, brief
[REBUILD.md](../audit_mm678_20261111/fixes/REBUILD.md) row 2, Discord OY-27 "hands look messy in the attack"), agent
`rebuild-2`. Scope: the hands and the Cast shoulder only. Body, textures outside the hand rectangles, rig, and every
other clip channel are the installed ones (`mm6_ttn1_claude`, reduced in `mm6_ttn_reduce_claude`, far LODs from
`lod_repair_claude`, WalkHeavy and the melee-plays-Cast decision of 2026-10-21). Meshy: 0 credits.

## What changed

- **Hands**: the rigid open Meshy hands (no finger bones) are replaced by posed MPFB (MakeHuman, CC0) male hands
  grafted inside the bracers (`scripts/graft_ttn.py`, copied from `mm9_yrsa_claude/v2/scripts/graft_hands.py`; config
  `scripts/graft_ttn.json`). Titan changes to the route: the body is the installed GLB (glTF import); skin/cuff classes
  come from connectivity (the hand's own shell vs the bracer pieces), not a class map; the MPFB hand is widened 1.15x
  across the fingers (`girth`) and 1.05x longer for the giant's hands; the decimated, conformed wrist stub is relaxed
  (8 Laplacian passes, hidden in the bracer) because it left needle triangles poking out of the left bracer.
  15 finger bones per side (`LeftHandThumb1..Pinky3`, `RightHand...`), built along the fingers (Y along the segment,
  Z the palm normal, X the flex axis), MPFB weights.
- **Hand texels**: the hands get a free 197 x 197 px square of the existing 2080 x 1024 atlas (two 98 x 197 rectangles,
  `rects`; found by `scripts/free_squares.py`), MakeHuman skin baked through the MakeHuman UVs (`bake_hands_ttn.py`)
  and graded to the old hand texels' grey stone skin, plus the granite grain of a clean forearm-skin swatch of the same
  atlas on colour and normal (`compose_ttn.py`). Metal/rough and region mask = the old hand texels' medians (skin is in
  no tier region, so tiers A/B/C keep the hand colour). Hand density 599 texels/m (body p50 634).
- **Finger keys** in every clip (`scripts/finger_poses.json`, `splice_ttn.py`): Standing relaxed; Walking/WalkHeavy/
  Running loose fists; Cast (= melee) relaxed -> claw while gathering (0.3-0.74 s) -> fingers spread open on the
  push (0.86 s, the impact 0.87) -> relaxed from 1.5 s; Ranged right fist on the wind-up, open on the thrust (0.78 s);
  Hit cupped round the helmet; Fidget clenches both fists (0.26-0.42 s, as the native fidget); Death/Dead limp curl.
  The thumb's fist pose was solved numerically (tip within 1.5 cm of the index/middle middle phalanges).
- **Cast recovery** (`cast_fix`): from 1.55 s to the end (2.25 s) both arms' Arm/ForeArm/Hand rotations ease
  (smoothstep slerp) from the 1.55 s pose to Standing frame 0. The source swung the left hand across the belly at
  1.9-2.05 s (hand 3.8 cm across the midline, elbow 113 deg) and crushed the left armpit; now the hand stays 28-33 cm
  to the side all the way down. The lat stretch under the raised arms during the push hold (1.0-1.8 s) is the
  installed Meshy weights and was not changed (same before and after).
- LODs rebuilt from the new LOD0: `tools/build_actor_lods.py` (LOD1), variants copied, shadows tucked
  (`../mm6_ttn1_claude/scripts/shrink_shadow_lods.py`), LOD2/3 by the far-LOD repair steps at the installed choice
  r25_12 (`build_lods.py`, `unwrap_lods.py`, `transfer_textures.py`, `apply_bake.py`).

## Build

`TOKEN=<lease> scripts/build_runtime.sh --graft [--install]` (Blender 5.3 needs `BLENDER_USER_EXTENSIONS=
~/.config/blender/5.2/extensions` for MPFB; the script sets it; the far-LOD steps use `work/lodrep_venv` with pymeshlab,
xatlas, numpy, scipy, pillow). Without `--graft` it replays from the splice (finger poses, Cast fix). Review:
`scripts/review_shots.sh [shot names]` (viewer GLBs per tier, manifest, identical-camera shots from `shot_specs.py`).
`scripts/diff_ttn.py work/before_rebuild/mm6_ttn.glb export/mm6_ttn.glb` checks that nothing else changed.

## Checks (installed 2026-11-11)

| Check | Before | After |
|---|---|---|
| LOD triangles | 7,666 / 3,832 / 1,916 / 958 | 9,126 / 4,562 / 2,281 / 1,115 (hands 2 x 1,100) |
| `diff_ttn.py` | | only intended: +30 finger nodes and channels per clip, 6 Cast arm channels, pixels inside the hand rectangles; 0 non-hand vertices with other weights or normals |
| `texture_quality.py` Titan_A | atlas 49.4 %, fragments 7.6 %, spread 3.6 | atlas 49.2 %, fragments 6.4 %, spread 3.48 |
| Attack (Cast) motion ratio vs MM9 biped (`rebuild_measure.py`) | 0.83 | 0.83 |
| Cast left hand across the belly 1.9-2.05 s | 3.8 cm past the midline | none (28-33 cm out) |
| Hand inside the body (motion_audit), every clip | 0 | 0 |
| Hand region bad, worst clip (finger knuckles in fists) | 3.0 % | 10.4 % (Fidget fist), under the brief's 12 % |
| Worst region beyond Standing | Hit spine 17.0 % (existing) | unchanged |
| `check_winding.py` | 0 | 0 |
| `floor_audit.py --match 'BTitan*'` | ok | ok (stand -0.3, corpse 0.42) |
| `mm6_mm7_mm8_actor_models_build_every_binding`, `mm6_titan_...` | pass | pass (647 descriptors, 0 failed) |
| viewer `run_creature_review.py check` | | 60 switches, 0 console errors |

Sheets (viewer shots, identical cameras): `review/sheet_tiers.png` (A/B/C: full body, Cast push, left hand at rest),
`review/sheet_hands_1.png`, `review/sheet_hands_2.png` (first pass), `review/sheet_hands_v2.png`, `review/sheet_fist_v5.png`
(final fists), `review/graft/cast_left_before_after.png` (flat, deformation red, Cast 1.6-2.15 s). In game:
`review/ingame/crop_out.png` (New Sorpigal, Titans fighting with Cast), `review/ingame/ingame_indoor.png` (Agar's Lab).

Known: the right fist's thumb tip shows at the bottom edge of the fist from the front-right; the Ranged clip ends with
an 8 m/s hand snap at 1.42 s (installed, not in scope); the hands are smooth MakeHuman hands with the body's stone grain,
not Meshy paint.

Revert: `python3 tools/install_model.py level_generation/creatures/mm6_ttn_rebuild_claude/work/before_rebuild/mm6_ttn.glb
--world mm6` (actors.yml was not changed; its backup is `work/before_rebuild/actors_mm6.yml`).

## Follow-up 2026-11-11: clean fists (agent `followup-wwf-ttn`)

`review/sheet_fist_v5.png` showed lumpy fists: fingers half-fused, the thumb poking out of the right fist, a dark notch
at the left bracer, a faceted hand surface. Hands only; body, rig, other channels and the texels outside the hand
rectangles are the installed ones (`followup/diff_followup.py`). Meshy: 0 credits.

- **Fist solve** (`followup/fist_solve.py`, no Blender): finger and thumb angles found numerically on the spliced GLB
  with the splice's own rotation rule. Cost: distal finger/thumb vertices inside another finger or the palm (signed
  distance to the nearest triangle interior, as `arm_hand_gate.py --exact`), each fingertip within 1.5 cm of the palm
  point a fist puts it on (under the wrist-to-knuckle line, 0.5-0.65 of the way; the old pose only touched the palm next
  to the knuckles and sank 1.2-1.8 cm into it), the thumb tip resting 0.1-0.5 cm outside the index/middle middle
  phalanges and not past the fist's extent, a weak prior, human-range bounds. Solved per side (`fist@Left`,
  `fist@Right` in `scripts/finger_poses.json`; `splice_ttn.py` now reads `<pose>@<side>` overrides).
- **Thumb path**: `fistopen` (fist fingers, loose thumb) and `fistlift` (thumb lifted off the fingers) are keyed between
  relax and fist in Fidget and the Ranged right fist, so the thumb wraps after the fingers close and leaves first
  instead of sliding through the index. **Loose** carry fists (walk, run, death, left Ranged): `followup/loose_solve.py`,
  fingers 0.55 of the way to the fist, thumb solved against the index (`loose@<side>`; the old pose kept as `loose_old`).
- **Hand mesh**: `graft_ttn.json` `hand_tris` 1100 -> 1900 per hand (smoother knuckles and finger shading), re-grafted
  with `followup/graft_only.sh` (graft, bake, compose, splice). Hand texels: `ao_strength` 0.45 -> 0.25 (the AO is baked
  with open fingers and blotched the fist), granite `grain` 1.0 -> 0.6 and `grain_normal` 0.8 -> 0.25 (mirror-tiled
  across the many small UV islands, it lit each island differently: the faceted look).
- **Bracer notch**: the graft's bracer-rim rules had also deleted 9 bright gold faces of the left bracer rim (a hole
  showing the dark inside). `splice_ttn.py` (`restore_bracer` in finger_poses.json) puts back the installed LOD0 faces the
  graft dropped that are forearm-weighted and textured bracer gold, with their installed vertices, weights and UVs.
- Build: `TOKEN=<lease> followup/graft_only.sh` then `TOKEN=<lease> scripts/build_runtime.sh` (splice, LODs, far LODs).
  Installed 2026-11-11 22:40.

| Check | Before follow-up | After |
|---|---|---|
| LOD triangles | 9,126 / 4,562 / 2,281 / 1,115 | 10,736 / 5,368 / 2,682 / 1,321 (hands 2 x 1,900) |
| Fidget fist (0.34 s), L / R: worst finger-in-finger | 0.86 / 0.90 cm | 0.14 / 0 cm |
| fingertips into the palm (I, M, R, P) | 1.2-1.8 cm | 0-0.54 cm |
| thumb tip: gap to index/middle, past the fist | 1.5 / 1.4 cm off, 1.4 / 1.1 cm out | 0.6 / 0.8 cm, inside (-0.42 / -0.04) |
| `followup/hand_gate.py`, every clip at 48 fps, worst finger-in-finger | 1.09 cm (Ranged R), 0.5-0.67 in walk/run/death | 0.24 cm (Ranged R), 0.05 elsewhere |
| thumb pad into the palm in the fist | 0.6-0.9 cm | 1.2-1.4 cm (hidden inside the fist) |
| `diff_followup.py` vs installed | | body vertices 6,464: 0 missing, 0 changed; non-finger channels identical; finger channels changed in Fidget, Ranged, Walking, WalkHeavy, Running, Death; pixels outside the hand rectangles 0 |
| motion_audit hand region worst | Fidget 10.4 % | Fidget 11.4 % (knuckle skin over the tighter fist) |
| Cast (= melee) motion ratio | 0.83 | 0.83 |
| texture_quality Titan_A | atlas 49.2 %, fragments 6.4 % | 49.2 %, 6.3 % |
| winding, floor (`BTitan*`) | 0, ok | 0, ok |
| `mm6_mm7_mm8_actor_models_build_every_binding`, `mm6_titan_...` | pass | pass (647 descriptors, 0 failed) |
| viewer check (`followup/viewer_manifest.py export/mm6_ttn.glb fu cur before`) | | 90 switches, 0 console errors |

Sheets (viewer shots, identical cameras, `followup/shot_specs.py`): `review/followup/sheet_followup_fists.png` (tier A:
both fists from the front, outside and below, walk fists, Ranged fist), `review/followup/sheet_followup_tiers.png`
(A/B/C), `review/followup/sheet_followup_open.png` (stand, Cast claw and push, Ranged thrust, Hit).

Still open: `arm_hand_gate.py` reads 3-5 cm "hand inside the body" in every frame of every clip, before and after alike
(a structural reading of the Titan's skirt/bracer, not a contact); the hands keep the body's stone grain at 98 x 197 px
per hand; finger edge stretch peaks 4.9x at the thumb web in the fist (was 3.6x).

Revert: `python3 tools/install_model.py level_generation/creatures/mm6_ttn_rebuild_claude/work/before_followup/mm6_ttn.glb --world mm6`
(actors.yml unchanged). The follow-up's inputs before it are in `work/before_followup/` (graft config, finger poses,
splice/compose scripts, graft outputs, textures).
