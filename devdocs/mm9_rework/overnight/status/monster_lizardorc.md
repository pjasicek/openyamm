# monster_lizardorc (overnight-lizardorc)
Phase: masters. Lease token a9af93ce99d7405d8307fce8e8a79451. Credits 0/40. Project level_generation/creatures/mm9_lizardorc_claude.
Decision: humanoid route (42 nodes, Bip01 biped, two arms, MM9 clips, no child model: ChildModels count 1 = self). One skin LIZARDORC.dtx + LIZORCCUTLASS.dtx for all three rows, Scale 1.
Jaw Box01 (opens up to 35 deg), tongue Bone02-05 (flick in fidget1), Box02 static (helm), tail Box03-05. Cutlass rigid on Bone07 (R hand). Finger0 thumb, Finger1 all three fingers.
Source true-handed: source/true/lizardorc_true.glb (mirror_glb.py). Plan: body ST + head ST (open mouth), one retex each = 30 credits.

## 09:00
Credits 10/40 (body ST, head ST). Masters excellent (references_hd/, references_head/). scripts: clean_body, reduce (work/half0r), fit_liz, head_prep/head_build (headfr.py = head frame), join_liz, rig.sh, weights_liz, build_glb, quick.sh. First clay rig plays all 16 clips well (review/sheet_strips_r0.png). UVs running (uv_liz.py, work/joined_frozen.npz: never change topology of joined after this). Next: uploads, 2 retextures (20 credits), textures, fist, cutlass, tiers, gates.

## 09:10
Credits 30/40 (+ body and head retexture, both excellent, no more Meshy planned). UVs frozen: work/uv.npz, work/joined_frozen.npz (never change topology; the paints belong to them). scripts/rebuild.sh, viewer_update.sh <rev>, gates.sh. Fist solved (fist.py, hand_poses.json), cutlass procedural (make_cutlass.py). Next: neck seam, region mask + ramps (liz_ramps.json), gate review, bind, install, in-game, sheets, README.

## 09:25
Installed and bound (actors.yml block mm9_lizardorc, strides 1.7/2.5). Credits 30/40. scripts/deliver.sh running (gates, regression, strips, close-ups, sheets). Coordinator: finish fast, no polish. Left: in-game, README, lease release.

## Done 2026-10-31 10:00
Installed r7, bound, validator 143 descriptors 0 refused, review root refreshed, three tiers in game, README written, lease released. Credits 30/40. Open with numbers in the README: plates in legs up to 7 cm (cap), floor AttackMelee -9.5, neck-ring sliver. No background processes left.

## Second pass done 2026-10-31 12:10 (user feedback 19-24)
Installed r13, regression PASS 147 descriptors 0 failed, lease released, 0 new credits (30/40). Neck rejoined, body density 693 -> 1386 texels/m (mirror UVs, two 2K pages, 1:1 from the 4K paint), grip in the palm, hip plates rigid on thighs. Open in README: flap 1.5/3.3, tasset 1.7/1.6 cm Walking/Running; Fidget R fist 5.5 cm in its tasset; floor -9.0 is the cutlass tip.

## Third pass 2026-10-31 (user feedback 32, skin on breastplate)
Lease claimed. scripts/plate_fix.py inside tex_pages.py: chest plate zone reflected from the plate's own paint, torso beside the neck from lower chest. 0 credits. Rebuild running, candidate viewer in review/viewer_next (manifest held until read).
Done: installed r15 (same build as the shots), review root refreshed, binding regression PASS, validator 147 descriptors 0 refused, viewer published, lease released. 0 new credits (30/40). Open items in README, third pass.

## Run 2 (finishing job) started 2026-10-31
Lease token 1d6906ab193845058a4284c0364c9c7d (owner run2-lizardorc). Credits 30/40 before; at most 20 more for a paid retexture, only after a balance check. Job: close r15's open gates (MONSTERS_HANDOFF.md section 2), carry every MM9 clip, fresh strips and in-game from the final build.
### Run 2 progress
- clips_mm9.py: soft offset line. New: scripts/flap_solve.py (replaces flap_keys in rebuild), scripts/tip_lift.py (AttackMelee cutlass tip/blade), scripts/chin_crease (normals in build_glb.py), plate_fix.py trim on the shell top + armpit mail flecks, tex_pages.py throat slivers, arm_bump.py excludes the cutlass from "body" (R jobs were stuck at 7.5 cm), bumps R caps 27, floor_ops --smooth Death. scripts/mid.sh = rebuild up to work/final_clips.glb.
- Candidate builds go to review/viewer_next (VIEWER=viewer_next scripts/viewer_update.sh); review/viewer still r15 until final.
- r16 installed 14:2x (tools/install_model.py --world mm9), floor audit 0 flagged, validator 147/0 refused, regression mm9_actor_models_build_every_binding PASS (suite stopped after it, my PID), review root refreshed, in-game bootcamp tours review/ingame_sheet_r16.png and _r16b.png. Gates in README "Run 2". Sheets via scripts/deliver_r16.sh running (publishes review/viewer r16). Lease still held until sheets are read.

## Run 2 done 2026-10-31 ~14:45
Installed r16, review/viewer published r16 (check: 0 failed), review root refreshed, floor audit 0 flagged, regression PASS (147/58, 0 failed), validator 0 refused, in-game bootcamp sheets review/ingame_sheet_r16.png and review/ingame_sheet_r16b.png. Strips (3 tiers), close-ups, tiers, MM9 vs ours regenerated from r16 and read. 0 credits (30/40). Lease released. Open (README "Run 2"): plates (Walking 1.5/1.7, Running 3.3, AttackMelee flap 3.4 inner 3.9 tasset 2.5, AttackMelee2 5.2, AttackRanged tasset 5.2), Death2 L hand 3.6 cm 1 frame, AttackRanged L forearm 2.0, AttackMelee2 blade 1.3 cm 1 frame, jaw-corner pale slivers. No background processes of mine left; the http.server on 8912 (PID 511324) was started by me and left up because other agents' viewer shots use it.

## Run 2, second request done 2026-10-31 ~16:30
Installed r17 (neck band weights wider, hip smoothing 40 passes over 22 cm, throat/chin paint, Hit L bump 6 deg), viewer r17 (check 0 failed), floor 0 flagged, validator 149/59 0 refused, regression PASS, review root refreshed, in game review/ingame_sheet_r17.png. Close-ups now from outside the body (scripts/closeups2.py). Collapse before/after in README "Run 2, second request" and work/collapse_r16_r17.md. 0 credits. Lease released. No processes of mine left except the shared http.server 8912.

## Run 2, third request (jaw underside and throat), started
Lease token da36bd8415a348a380345bd05452be21. scripts/throat_paint.py: strip and chin faces get UV cells in free head atlas space (assemble.py), one below view (references_head/throat/throat_below.png) repainted by Codex (scripts/codex_throat.sh), projected back in tex_pages.py. 0 credits.
Done ~18:00: installed r18 (throat from one Codex-repainted below view + a front view for the ring band, strip zipped flat, chin fans and strip on real UV cells), viewer r18, floor 0 flagged, validator 150/60 0 refused, regression PASS, review root refreshed. Sheets review/run2/sheet_throat_a/b/c.png. 0 credits. Lease released. Open: Hit2 lower-throat stretch streaks (body faces stretched 3x).
