# monster_ebora (run2-ebora)
Phase: sources. Lease token b039663e1fb6497db7190e875100dbc0. Credits 0/25 (backup 3900 at start, stop at <= 3785).
Project level_generation/creatures/mm9_ebora_claude. Background: none.
Found: Concubine (row 302) uses ebora.abc with skin siren1.dtx; Ebora (row 301) ebora.dtx. Same model -> tiers.
19:30 Route decided: humanoid (MM9 Bip01, 5 two-bone fingers per hand) + two bat wings on MM9's chains (Bone13-69). Wings are
NOT Meshy: scripts/build_wings.py builds spars + Coons membrane on MM9's bone heads (MM9's wing is rigid per vertex),
harmonic weights, buried root. Masters without wings (references_hd/, Codex run 1 accepted 00, run 2 views running).
Clip roles: Standing stand, Walking walk, Running run, Fidget fidget1, AttackMelee Hattack1 (rattack 0.407), AttackRanged/cast
Castspell, Hit wince1, Death die2, Dead; script clips fidget2 taunt backpedal backpedalrun fly launch land flap WinceAir1 DieAir1 fall1 FallDown1 wince2.
Tiers: Ebora (ebora.dtx), Concubine siren1 (row), siren2-4 = EboraConcubine.scr random skins (extra variants).
Credits 5/25 (eb_smart_v1 submitted 19:20)
20:45 Credits 5/25 (eb_smart_v1 ST). Mesh: work/s1.npz -> assemble (hair cut at shoulder blades) -> work/asm.npz (10,124 tris).
Rig: fit_rig -> heat_weights -> weights -> bind (wing roots kept 7 cm behind the back) -> build_wings -> merge -> build_glb -> clips_mm9 (soft line) -> half_keys. First clay rig work/half0.glb plays every clip (sheet work/pose0.png).
UV FROZEN: work/uv_frozen.npz (TCOST 0.6), never re-run uv_eb.py. Upload texturing/eb_body_upload_v1.glb ready.
Codex running: references_paint ebora + siren paints on our clay, wing paint (wing_template.png). Gates0 on clay rig in review/gates0.
Next: retexture Ebora (10), retexture siren1 (10), wing texture compose, ramps for siren2-4, head set from the upload layout.
19:43 eb_retex_ebora submitted. Credits 15/25.
19:46 eb_retex_ebora done (10). eb_retex_siren submitted. Credits 25/25 (budget used).
20:31 eb_retex_siren downloaded. Credits 25/25 spent; backup 3875. No more paid jobs.
21:00 Built end to end with scripts/rebuild.sh (2 min). LOD0 14,600 tris (face subdiv +2.2k, wings 2.3k). Installed (first install),
bound (scripts/bind_actors.py 1.14 4.0 under the flock; generator run, tables unchanged). Tiers eb/s1 own paints, s2-s4 ramps
(textures/eb_tiers.json via scripts/tiers_eb.py, scripts/tier_glb.py). Viewer r3 with 5 tiers (scripts/viewer_update.sh).
Regression running. Gates (review/gates) running. Next: arm results -> fixes, wing fold look, sheets (compare, joints, strips),
in-game, review_root, README, release lease.
21:40 Installed r8 (sha f72ad1550201): wing pleat (scripts/pleat_keys.py, per panel 0.6/0.6/0.2), inner wing web on Bone48 (no sail),
Land arm group 10 deg / 0.25 s (jitter). Skin slash marks inpainted (tone_eb.py). Regression on the first install PASS (157 on 64).
Sheets: review/sheet_mm9_vs_ours.png, sheet_tiers.png, sheet_joints_1-3.png, strips_eb_1/2.png, sheet_wing_*.png, sheet_ingame.png.
In game (bootcamp map 9021 spot over water): eb + s1 idle, death, hostile cast seen.
Pending: lips fix in tiers_eb (applied to textures, needs rebuild+install), final gates/regression, README, lease release.
22:30 FINAL build installed: sha 5d63ccc8e9df (Death arm group 20/0.25, Land 10/0.25; s2-s4 lips fix). Gates: jitter 0 fails,
detached 0, bones 0, winding 0, flat body 0.00-0.01 / wing 0.21, floor ok, arm hands < 1 cm except AttackRanged R 1.4 (2 f) and
Land L 1.6 (4 f, script clip); forearms on the wing in Death/Dead 4.7-5.9 cm. Collapse: body in the accepted range; wings ~150/wing
when folded (MM9's fold; pleat tried, kept partial). Regression PASS on the previous install (158 on 65); rerun on final running.
Viewer r12, check 110 switches 0 errors. README written. Credits 25/25. Remaining: regression result, strips reshoot, release lease.
23:00 DONE. Final install sha 5d63ccc8e9df; regression mm9_actor_models_build_every_binding PASS (158 on 65, 0 failed); the suite
also printed an unrelated MM8 test fail (out05_event_clearance..., world mismatch under --world mm9). Strips re-shot on the final
build. README written. Lease released. Credits 25/25 (backup 3,875). Background: none. Chromes: none.
Open for a follow-up: wing fold collapse count (~150/wing, MM9's own fold), forearms on the wing in Death/Dead, s2 lips orange,
Concubine skin lighter than MM9, joint close-ups and MM9-vs-ours sheet from r3-r4, in-game from r8, bathhouse map not run.
22:26 PASS 2 started (coordinator): wing tier colour when spread, Death/Dead forearms on the wing, concubine tone + s2 lips, reshoots. 0 credits.
Lease token pass 2: 104d6a21c8eb4720a820628d11700504
PASS 2 DONE: installed sha 8c1fc6165863. Wings: bent membrane normals (build_glb.py) -> tier colour from both sides (sheet_tiers,
in game ingame2/h06). Death/Dead: arm_lay.py L upper arm 18 deg (Dead L 0, Death L 1.3 cm, corpse 0 wing crossings, jitter 0).
Siren tone (tone_sr.sh) and lips (tiers_eb.py). Gates rerun, regression PASS (158 on 65). Reshoots read. Lease released. 0 credits.
14:45 HEAD PASS started (user: 'needs better head texture'). Budget 10, prefer Codex+projection.
HEAD PASS DONE (2026-11-01): installed sha ac7581618509. Codex head paints on our head clay (references_head/), projected by
landmarks (project_head.py), fringe tip lifted (fringe_lift.py), head image 2048, seam gain (Ebora), tier head mask from parts,
hair floor. 0 Meshy credits. Gates unchanged (jitter 0, detached 0, bones 0, winding 0, flat head 0.01, floor ok), regression
PASS (158 on 65). Sheets: review/sheet_head_full.png, sheet_tiers.png. Lease released.
16:02 HEAD FIX 2 (coordinator): hairline stub, nose streak, ear cards. 0 credits.
16:34 HEAD FIXES 3 started (claude-ebora-face-20261101): user review — mouth too thin, nose too tall/thin; ear paint on hair. Lease token 5aa5132c0859485c9f6b825ee3509cea. Budget: 0 Meshy credits. First: baseline gates + regression on the 17:14 install.
18:20 Baseline: regression PASS (158 on 65) on the 17:12 install (sha d0abf59d2ff8); gates on it running (review/gates_base). Causes: mouth/nose = Meshy geometry (paint fitted to it); 'ear on the hair' = the ear cards are 14 cm side locks 1-3 cm off the skin, labelled skin, plus red ear shading accepted on Ebora's hair texels (RGB test). Fixes in progress: scripts/face_shape.py (vertex moves after subdiv), dump_head relabels the cards hair, project_head redness test (eb), ridge tone from the skin beside the nose, tone_eb highlight shoulder. Not installed yet.
18:55 Iterating (dev viewer revisions h16dev*): mouth line found at z 0.832 (midline section), fields recentred; projection samples the paint at the reshape's smooth inverse (work/head_faces_shp.npz); lip pucker folds Taupin-smoothed; lip junction crevice darkened. Next: final rebuild + install, gates, regression, sheets, README.
21:20 HEAD FIXES 3 DONE: installed sha f141099bc209 (rebuild.sh --install). Mouth wider/fuller and nose broader/shorter (scripts/face_shape.py after subdiv, vertex moves; projection samples the paint through the reshape's inverse, lip pucker folds smoothed, lip-junction crevice painted a deep lip tone); 'ear' cards relabelled hair (Meshy side locks), Ebora hair texels refuse red paint; seam-gain highlight shoulder. Gates identical to the 17:12 baseline (jitter 0, detached 0, bones 0, winding 0, flat head 0.01, arm/collapse unchanged); regression PASS 158 on 65 before and after; viewer h16-20261101 check 110/0. Sheets: review/sheet_face_compare.png, sheet_head_sides.png, sheet_head_clips.png. Credits 0 (Meshy 0, Codex 0). Lease released. Background: none. Chromes: none.

## Concubine face and hair (user note 2026-11-01 evening)
23:00 Started (concubine-face-fix). Lease token 44fe9e2694cc4ddeab0060886266a589, budget 15, Meshy 0 so far (backup 3550). Rollback copy work/installed_hf3.glb (sha f141099bc209). Causes found: hair holes = single-sided hair shell/side locks/fringe seen from inside (culled) past the face profile; ugly face = Codex brief asked for "fierce, cold slight smile" (knitted brows, pursed mouth); muddy chin = unlit underside + dark fill; neck seam = torso paint lighter than head (219,159,111 vs 210,129,94). Fixes in progress: scripts/hair_backs.py, Codex calm face on the reshaped clay, neck/jaw blocks in project_head.py (siren only).
00:55 Installed sha 614076182777 (tools/install_model.py --world mm9; rollback work/installed_hf3.glb = f141099bc209). Hair: scripts/hair_backs.py (733 reversed copies of hair/fringe/side-lock faces whose inside is ever in view; LOD0 14,566 -> 15,299). Face: Codex calm repaint on the reshaped clay (references_head/s2_08_face_clean.png, CODEX_BRIEF_HEAD_SIREN_CALM.md, attempt 1 of 2), landmarks clay_face_shp (24 pts incl. brows), ridge softening stops below the eyes. Chin underside lightened (additive), neck seam: head gain + scripts/seam_rim.py sr (torso padding) + seam_rim.py orm (shared AO, neck faces only). Ebora: eb textures not regenerated (project_head a eb reproduces byte for byte); face pixels unchanged except a sliver at the hair edge where the hair backs now fill old holes. Gates: winding 0, bones 0, detached 0 (29 -> 38 components: the copies), flat head 0.01, jitter identical (0 fails), arm/hand identical, collapse identical but neck worst +1 in Death/HitAir/DeathAir (copies of the same squashed nape hair faces; exposed unchanged), texture head atlas/density/spread/stretch/fragments unchanged (islands 58 -> 87, uv sum 60.3 -> 71.5 %: copies on existing texels), floor 2 bindings ok (same numbers). Credits: Meshy 0, Codex 1 run (2 images).
01:40 Reinstalled sha ad8aff4fc94e (same geometry/UVs/weights/normals as the gated candidate; seam AO padding 8 px + torso padding: no visible change on the residual seam zigzag). Regression mm9_actor_models_build_every_binding PASS (182 on 75); only the known out05 world-mismatch FAIL. Viewer cf9-20261102 check 110/0. Floor 2 ok. Sheets: review/sheet_cf_s1_before_after.png, sheet_cf_sirens.png, sheet_cf_hair_sides.png, sheet_cf_ebora_face.png (0 face-skin px changed in 5 views, 854 at the temple hair edge in front), sheet_cf_neck.png. Left: chin underside shaded wedge from below (lighting), faint seam zigzag (cause not found), s2 olive jaw (ramp). Credits: Meshy 0 (backup 3550), Codex 1 run. Lease released. Background: none. Chromes: none.
2026-11-02 ear-sweep check (owner ear-sweep-fix): the heart-shaped wing-coloured patch under the jaw (rneck/lneck, all tiers) is the
wings and background seen past the neck from that low camera, not a hole (proof `review/throat_wings_check.png`: wings deleted ->
magenta background there, the throat is closed). s2's olive throat was the s2 head skin ramp clipping per channel into yellow at the
lightened chin underside; `tiers_eb.py` now scales over-range s2 head-skin targets back with hue kept. Only that ramp changed;
images and clips identical, eb/s1/s3/s4 viewer GLBs byte-identical. Installed sha 5a8a356830dd, rollback work/installed_preear.glb.
Viewer cf10-20261102, check 110 switches 0 failed. Sheet review/sheet_ear_before_after.png.
