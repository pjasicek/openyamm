# Variants PeasantDF1-4 (dwarf women) — status

- Project `level_generation/creatures/mm9_peasantdf_claude/`, lease `mm9:peasantdf` (owner peasantdf-agent), budget 80 for the family.
- Rows: 1 Commoner DF1a, 5 Shopkeeper DF1b, 2 Commoner DF2b, 4 Town DF3a, 7 Prisoner DF3b, 3 Town DF4b, 6 Shopkeeper DF4a.
  DAT objects: CommonerDwarfFemaleA 6 (row 1), CommonerDwarfFemaleB 2 (row 2), ShopKeeperDwarfFemaleB 2 (row 6),
  TownDwarfFemaleB 1 (row 4); rows 3, 5, 7 unplaced.

## Log
- 14:26 UTC lease claimed (backup 2930). Sources converted (8 skins, library PEASANTFEMALEDWARF 10 clips, 53-node skeleton:
  Scene Root -> Spine1 / Bone22 skirt ring (8 two-bone hem chains) / thighs; LF_tail/RF_tail hair-side chains). meshcmp re-run:
  worst-region p90 1.9-3.3 cm between any two. MM9 views of all eight skins: one mesh, the differences are paint (hair vs
  hood, sleeve length, apron) -> ONE Meshy body (design 1 = DF1a, the most placed), four paint designs. Codex master 00 (d1) running.
- 14:35-16:50 UTC design-1 master 00 (Codex, attempt 1 of 2 chosen: truer 3/4, MM9's centre-parted bob) -> Smart Topology
  body_smart_v1 (5; backup 2930 before). The Meshy hair came out as one rounded hood-like shell (the MM9 hair/hood volume all
  four models share). Fit to the 53-node dwarf female skeleton (Spine2 interpolated), necklace/brooch/bracelet pieces dropped
  (paint in every design), reduce 13.4k -> 8.6k, MPFB female hands 0.135 m, level neck cut, eyes filled, ears tucked under
  the hair, wrist rings trimmed. UVs: body 62.7 %, head 61.6 %. One GLB per MM9 model (the engine uploads every
  material's images when a model loads, so 4 designs in one GLB would load all 4 paints for any one woman); one mesh, rig
  and clip set for all four. Design views d1 (DF1a), d2 (DF2b), d3 (DF3a), d4 (DF4a) on design 1's silhouette (Codex).
  Paid: body d1, head d1, body d3, body d4 (10 each). Credits 45 (backup 2930 -> 2815 shared balance).
  d1 runtime built (export/mm9_peasantdf1.glb, LOD0 10,015 incl. 1,502 back-side twin faces); gates running.
- 16:50-17:40 UTC paint chains (compose -> gentle grade -> head/hands -> paint_clean: hair underside / scalp / pale neck band
  -> seam_tone: head neck band takes the body paint below the cut, normals flattened at the seam, gutters re-padded ->
  wrist_fix: hands to the cheek tone, met half way with the forearm, one wrist band per design). Back-side twins
  (twin_faces.py: hair, skirt+apron, stockings, sleeves, wrist rings, boot tops): see-through worst pixels v1 -> v3: hair 41 -> 0,
  head 60 -> 0, skirt 167 -> 42, sleeves 66 -> 38, boots 56 -> 12. Paid: head d4, combined body+head d2 (10 each); credits 65.
  d2's own head paint had a doubled lip line: its head set is design 4's head paint, recoloured (cream kerchief, fringe).
  d3 head turnaround Codex run stalled on "Reconnecting" (killed my PIDs 224778/224767, restarted, done 17:35).
  Building + installing d1, d2, d4.
- 17:40-19:10 UTC d3 head retexture (10; backup 2765 before). Credits **75 / 80**. Face sheet r1 -> fixes: seam meets at the
  mean skin tone (no lighter collar), d2 kerchief recoloured to MM9's own cream (gain 1.3), d3 hair rule dropped (it took the
  lower face), d3 lips toned down from lipstick red. Sleeve poke: left stub 20 mm out of the ring at rest -> stub ring cap
  (positions only) -> 0 mm in every clip. All four installed (sha256 df1 5bd92a5c9df1..., df2 7c4127e735c5..., df3
  ae37fcf325e6..., df4 1d142d7b9522...). Bound rows 1-7 under the flock (MM9 1..7 <role>), rows in mm9_npc_actor_rows.tsv,
  tables regenerated; heights: rows were 61/33 until `mm9_monster_bodies.py --write-overrides` (MM9 rule 118/31; it also
  filled the missing overrides of rows 10, 17, 19 by the same rule). Regression (filter actor_models_build_every_binding):
  mm9 PASS (226 descriptors on 99 models, 0 failed), mm6-8 PASS. Viewer r3-20261102: 77 switches, 0 failed, 0 console errors.
  Floor audit 7/7 ok. Final gates running.
- 19:30 UTC final gates (README "Checks"): arm/hand 0 frames > 1 cm in 11/11 clips; jitter 0; sleeve poke 0 mm; see-through
  worst skirt 43 / sleeves 46 / boots 15 / torso 19 / collar 15 px (hair and face gap 0); robe_gate numeric fail (renders clean);
  floor 7/7 ok; winding 0; detached 0; flat 0.00; body atlas 61.2 %, head 42.9 %; LOD0 11,681; viewer 77 switches 0 errors;
  binding regression PASS. Ears under the hair/hood in every tier. Sheets: review/sheet_faces_r2.png, sheet_faces_d3.png,
  sheet_ears.png, sheet_mm9_vs_ours.png.
- Phase: **done**. Credits **75 / 80** (backup 2930 -> 2765 before the last job, shared). README is the record. Lease released.
- r4 (coordinator review of sheet_mm9_vs_ours / sheet_faces_r2): lease re-claimed (owner peasantdf-agent-r4; backup 2705).
  To do: face areas out of every hair/hood ramp, per-design headwear geometry (MM9 silhouettes, DF3 braids), warmer faces
  with a gentle smile, B-tier ramps to MM9's B colours; rerun gates, reinstall, rebind test. Cap now 110 credits.
- r4 done (0 Meshy credits; README "Review r4"): face kept out of every head ramp; per-design headwear (headwear.py: MM9
  hood/hair outline, hem to the shoulders, hood points; DF3a plaited braids on the hair chains; DF2 kerchief hem band);
  gentle smile + rounder cheeks (smile.py) and warmer faces with lifted eye sockets (face_warm.py); B tiers to MM9's B
  colours (DF1b red, DF3b navy/red). All four reinstalled (bc68e5e1f210 / 76d62d7ddc84 / e70eb358550a / 8124ddd71cf6);
  gates: arm/hand 0, jitter 0, sleeve poke 0, see-through hair/head 0 (cloth slivers <= 46 px), floor 7/7, winding 0,
  binding test PASS, viewer 0 errors. Sheets review/sheet_faces_r4.png, sheet_mm9_vs_ours_r4.png, sheet_headwear_clay.png.
- Phase: **done (r4)**. Credits 75 / 110 (backup 2530 now, shared). Lease released.
- r5 done (0 credits; README "Review r5"): DF3b braids and fringe dark brown-black with plait detail (explicit hair ramp
  over our own luminance), DF3/DF4 hoods narrowed at the temples (14 %) and at the back bulge (18 %) with clearer points.
  Reinstalled df3 e4ada034c61c, df4 fe6f75a3d03f. Gates: see-through head/hair 0 on DF3 and DF4, DF3 arm/hand 0, jitter 0,
  winding 0, floor 7/7, viewer 0 errors, binding test PASS (rerun; first run hit another agent's MM9 46 Town race).
  Sheets review/sheet_faces_r5_d34.png, sheet_faces_r5_before_after.png, sheet_headwear_r5.png. Lease released.
- r6 done (user note via coordinator; 0 credits; README "Review r6"): head/body seam moved up under the jaw (necklace and
  chest now from the body paint, tones met at the seam, DF2/DF4 neck collar paint replaced by skin); temples and cheeks
  widened in geometry toward MM9 (temples 5.2-5.4 -> 5.6-6.1 cm half-width, MM9 6.2; cheeks 5.6 -> 6.2-6.3, MM9 6.4),
  hair/hood shells kept 4 mm outside. All four reinstalled (096baccbe9d6 / 531ac166353c / 8abc575f24c4 / 4df20ee724b9).
  Gates: arm/hand 0, jitter 0, sleeve poke 0, see-through head/hair 0 (cloth slivers <= 49 px), floor 7/7, winding 0,
  binding test PASS, viewer 0 errors. Sheets review/sheet_face_widen_clay.png, sheet_faces_r6.png, r6_zoom_a/b/d24.png.
  Lease released.
- 2026-11-04 06:24 UTC Job 7 (user review: ears, neck seam, cheek crack lines; FINISH_BRIEF_20261104): lease re-claimed
  (owner df-ears-20261104). Investigating.
- 2026-11-04 ~08:30 UTC job 7 in progress: modelled ears (scripts/add_ears_pdf.py -> work/master_v3_d*.blend, the build
  default now), ear/neck/crack paint pass (scripts/ear_paint.py, from *_prejob7 texture copies), shadow LODs drop thin
  inverted parts (the ears), new ear poke gate (scripts/ear_poke_gate.py); first gate run found hair swaying into the ears
  (9 mm AttackMelee) -> hair over the ears now rigid on the head. Viewer regenerated (job7-20261104), r6 viewer GLBs kept in
  review/ears_job7/viewer_r6_glbs/. Not installed yet. 0 Meshy credits.
- 2026-11-04 ~10:30 UTC job 7 done (0 Meshy credits; README "Job 7"): modelled ears on all four (tucked under the
  hair/hood, hair lifted and made head-rigid over them), ear islands painted to the cheek tone, painted outline removed,
  island-border crack lines healed, neck tone made one 3D-smooth field across both seam lines (necklace untouched).
  Installed df1 427a0e944504 / df2 14931a12370d / df3 c59945aa9daf / df4 60c6bcd2dd83. Gates: ear poke 0 mm all clips,
  arm/hand 0, jitter 0, sleeve poke 0, detached 0, winding 0, see-through = r6, floor 7/7, regression PASS, viewer 0
  errors. Sheets review/ears_job7/sheet_before.png, sheet_after.png, sheet_neck_before_after.png. Lease released.
- 2026-11-04: user approved ("ok dwarf female fine"), job 7 build.
