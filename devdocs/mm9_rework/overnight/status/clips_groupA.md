# Dropped MM9 clips, group A (run 2, 2026-10-31)

Agent: run2-clips-groupA. Bodies: honkmale, honkfemale, clansoldier, mummy, banshee, skeleton; verify thrall, evilsorcerer,
ghoul, monk. Meshy 0 credits, Codex 0. No background processes left (regression run: see below).

## Leases (released)
mm9:honkmale, mm9:honkfemale, mm9:clansoldier, mm9:mummy, mm9:banshee, mm9:skeleton (owner run2-clips-groupA).

## Exact counts (ABC read with `convert_abc_model.read_abc`; bind/setup pose and the added Dead excluded)
| Body | ABC clips | Installed before | After | Missing before |
|---|---|---|---|---|
| honkmale | 20 (+ malsetup) | 9 | 20 | Backpedal, Backpedalrun, cowerstart, cower, cowerend, die2, fidget2, prop-fidget1, prop-fidget2, prop-stand, wince2 |
| honkfemale | 20 (+ femsetup) | 9 | 20 | same 11 |
| clansoldier | 22 (+ clansetup02) | 20 (cower set stitched as one Cower) | 22 | static_die1, static_die2 |
| mummy | 21 (+ static_model) | 17 | 21 | BackPedal, BackPedalRun, Coffin2, die2 |
| banshee | 16 (+ bansetup) | 15 (DieAir1+Fall1+FallDown1 stitched as Death) | 16 | Fly (keys identical to WalkAir) |
| skeleton | 16 (+ static_model) | 14 | 16 | Backpedal, BackpedalRun |
| thrall | 14 | 14 | 14 | none |
| evilsorcerer | 17 (+ static_model) | 17 | 17 | none |
| ghoul | 15 (+ static_model) | 15 | 15 | none |
| monk | 34 (+ static_model) | 34 | 34 | none |

## What was done
Per body: an `*_extra.json` roles file (soft joint-offset line via the new opt-in `soft_offsets`, `hold` for static poses), the
body's own clip steps in the accepted order, then `claude_shared/graft_clips.py` onto the installed export (rest check passed on
every body: no mirror/rerest mismatch). Old export kept as `<project>/work|v2/work/mm9_<x>_pre_clips.glb`. Byte check: every
pre-existing accessor, mesh, skin, material, node and accepted clip identical (0 differences on all five). `check_winding` 0,
`install_model.py --world mm9`, `script_clips` added to every descriptor using the model (actors.yml under the flock), and the
project's binder template updated.

| Body | New clips (role -> clip) | Steps |
|---|---|---|
| clansoldier | dead_static -> DeadStatic (static_die1), dead2 -> Dead2 (static_die2); 4 descriptors incl. MM9 110 Town Guard | clips_mm9, finger_keys, half_keys, skirt_keys (2-key clips not eased), floor ground-loop |
| skeleton | backpedal, backpedal_run; 5 descriptors | clips_mm9, finger_keys, arm_clear, floor (Backpedal as Walking, BackpedalRun raised + 0.04 s loop smoothing) |
| mummy | backpedal, backpedal_run, coffin2, death2, dead2; 3 descriptors | clips_mummy, arm_clear on Coffin2 (22 deg cap), copy_anim, band_sim (Backpedal* loops, Dead2 = Death2's end, Coffin2 band settled then held), half_keys, floor (ground-death Death2/Dead2, Coffin2 grounded), mirror |
| banshee | fly -> Walking (A anchor, shared by B/C) | none: MM9's Fly has WalkAir's keys exactly |
| honkmale | fidget2, hit2, death2, dead2, cower_start, cower, cower_end, backpedal, backpedal_run, prop_stand, prop_fidget, prop_fidget2; 3 descriptors | `v2/scripts/extra_clips.sh`: clips_mm9, hand_rest (Fidget2 at 10 cm max push), wrist_fix (constant matches the installed 14.9/22.2 deg), floor (`scripts/floor_ops_extra.txt`), clip_relax (head damp on Hit2/Death2/Dead2, 2 mm lift at 0.867 s), mirror |
| honkfemale | same 12 roles; 2 descriptors | same script: arm_offset 8.5, hand_rest Fidget2 (10 cm), wrist_fix (24.7/22.4 deg = installed), floor, clip_relax (braid damp on Death2/Dead2, 5 mm lift at 0.733 s), mirror |

## Measured (new clips only; `claude_shared/new_clip_measure.py`, project arm/jitter/robe/band gates). Files: `<project>/review/clips_restore/`
- Floor (cm, lowest visible point): all living clips within -1.3..+1.8; deaths: honkm Death2 -2.39, honkf Death2 -2.26, corpses 0.
- Bones: no stretch over 10 % except Honk calves (MM9's own: the raw source stretches the same; legs are inside the robe), honkm Death2 1.25, Cower set 1.12.
- Hands in body (arm_hand_gate --outer-only --exact): clean on the walks, deaths and corpses. Over 1 cm: honkm Fidget2 2.5 cm (fists on hips),
  Cower 4.0 cm R (hands over the face), Cower set start/end 2.3-3.4; honkf Cower 5.1 cm R, CowerStart L 3.2 (hand 5.7 forearm), PropFidget2 R 3.1;
  Honk frame-0 values of 2.7-2.9 cm are the accepted Standing's. Mummy Coffin2 6.0 -> 0.7 cm after arm_clear.
- Jitter vs MM9's raw clips: fails only on the pushed Fidget2 (honkm upper arm +1.27/+1.83 deg/f, honkf +1.43 deg/f), the price of clearing the hips.
  Skeleton Backpedal/BackpedalRun and mummy Death2 shoulder-skin excess 2.0-4.6 mm/f2 from the floor root move (accepted Walking/Death show the same).
- Robe (Honks): 0 boot-through frames in all 12 new clips, both bodies. Mummy band: 0 through legs; torso 0 except Death2 2.1 cm, 18/66 frames.
- Clansoldier corpses: hands 0.4 cm max, sword 0, shield 0.5 cm.
- Frame strips read: `strip_new.png` (clansoldier, skeleton, mummy), `strip_a.png`/`strip_b.png`, `close_cower.png` (Honks).

## Progress
- [x] clansoldier, skeleton, mummy, banshee, honkmale, honkfemale installed and bound
- [x] binding regression after all installs and bindings: `mm9_actor_models_build_every_binding` PASS, 147 descriptors on 58 models, 0 failed (mm6-8: 647 on 185, 0 failed)
- [x] `review_root.py` run, leases released, no Chrome or game process of mine left

## Not checked
- No in-game run and no viewer/textured shots: strips are grey clay renders (Blender Workbench, `claude_shared/clay_strip.py`); playback at normal speed not watched.
- Collapse gate, LOD1-3, hats on the male Honk tiers in the new clips, clansoldier skirt gate on the two corpses, mummy band seam on the Backpedal loops.
- No behaviour drives any of these clips yet (script clips only); the Honk prop clips play without MM9's prop.
