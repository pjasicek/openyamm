# Townsfolk PeasantDM2 (old dwarf man) — status

- Project `level_generation/creatures/mm9_peasantdm2_claude/`, lease `mm9:peasantdm2` (owner claude-townsfolk-peasantdm2), budget 60.
- Rows naming PeasantDM2.abc: only **9 Commoner** (Peasant Dwarf MaleA B, PeasantDM2a), DAT class `CommonerDwarfMaleB`,
  6 placed objects (legacy stand-in 323: sturmfordcity 1, thjoradmine 5). Skin PEASANTDM2B is used by no row; kept as tier B.

## Log
- 23:45 UTC lease claimed (backup 3400). Sources converted; PEASANTDM2 skeleton = PEASANTDM1's exactly (41 joints, every
  translation/rotation equal) and = the `peasantmaledwarf` library bind. Skin A: elderly balding dwarf, white hair and
  braids, white beard, charcoal knit tunic with full sleeves to the wrist; skin B: another man (studded headband), laced
  leather tunic -> per-tier head planned. Scripts: DM1's chain. Codex master 00 running. Credits 0.
- 00:50 UTC master 00 accepted (Codex run 1, first return; alpha clean). Smart Topology body_smart_v1 (5; backup 3400 before).
  Fit, reduce 15,458 -> 8,865, MPFB hands at 0.234 m (Meshy's 0.277/0.265, MM9 0.21: new graft option hand_len), stray piece
  dropped, head split, eye cups filled and removed before the UV pass. Masters 01-04 and head turnarounds A/B accepted.
- 01:10 UTC UVs (body 62.8 %, head 59.7 %); body, head A 4K retextures (10 + 10); head B 4K retexture later (10). Credits 35.
- 01:15-02:10 UTC fixes: sleeves tucked + clean sleeve ring (cuff_trim 1 cm past the wrist: DM2 has real sleeves), cheek
  see-through gap patched and beard sheet flushed, eye_relax 0.4 (eyes visible from party height), neck base knit -> skin,
  collar leopard rim -> dark knit (first try painted a dark yoke on the chest: fixed by distance to the neck opening), hands
  warm skin (HAND_REF), tiers (R tunic, G trousers, B boots, A belt; belt/boots matched to MM9 A), hand rest Talk/Death/RubBeard.
- 02:15 UTC installed (assets_source/worlds/mm9/models/mm9_peasantdm2.glb, sha256 c208b01ea6d9...). Bound under the flock:
  row 9 -> 323 in mm9_npc_actor_rows.tsv, tables regenerated (186 rows, descriptor 9009), actors.yml block
  mm9_peasantdm2_claude (MM9 9 Commoner, pdm2_a). Gates: arm/hand 0 frames > 1 cm in all 15 clips; jitter 0 fails; floor ok;
  winding 0; bones 0; detached 0; flat 0.00; texture body 62.4 %; sleeve poke rest 0 mm, 1-6 flagged vertices in bent-wrist
  frames checked with markers (review/poke_check.png): on visible wrist skin past the cuff or under cloth. Viewer 30 switches
  0 errors. Regression running. Map placement left to the orchestrator (README "Binding plan").
- 02:45 UTC regression actors --world mm9: passed 192, failed 1 (known out05); mm9_actor_models_build_every_binding PASS
  (186 descriptors on 79 models, 0 failed).
- Phase: **done**. Credits **35 / 60** (backup 3400 -> 3295 shared balance over the session). README is the record. Lease released.
- 02:50-04:10 UTC **face pass** (orchestrator review; lease re-claimed; 0 Meshy credits, one Codex run): one skin tone over face,
  forehead, scalp and ears (skin_unify.py), knit on the neck sides removed, Codex eye/brow/mouth repaint by landmarks (open smiling
  eyes with light blue irises on both tiers, relaxed brows, gentle smile, cheek patches gone; warp_face.py with measured anchors,
  project_face.py with overlapping windows), cheek gaps closed (bridge, patch-face UV islands, backing plates), hands to the face
  tone (texel medians hand 208/120/81 vs cheek 220/123/86). Rollback r4 in work/rollback_r4/. Reinstalled (sha256 6edaaf7e61b0...).
  Gates unchanged (arm/hand 0, jitter 0, floor ok, winding/bones/detached 0, flat 0.00); viewer r6 30 switches 0 errors;
  regression passed 192, failed 1 (known out05), mm9_actor_models_build_every_binding PASS. Residual: ~1 cm shading facet beside
  the nose on one cheek (geometry). Sheets: review/sheet_faces_before_after.png, review/sheet_hands_vs_face.png.
- Phase: **done** (face pass). Credits **35 / 60**. Lease released.
- 06:20-11:30 UTC **see-through openings and ears (r7)** (user note "holes in sleeves + some in knees (e.g. running anim 12)",
  `review/user_notes/sleeve_knee_holes_running12.png`; orchestrator ear sweep rows 17-18). Lease re-claimed (owner dm2-holes-fix),
  0 Meshy credits. Causes: single-sided cloth with open rims: the cuff ring over the tucked stub, the boot's turned-down cuff
  (end of the trouser piece) lifting off the shaft at a bent knee, the belt-level tunic rims, the collar, the head's open
  neck bottom. Fix `scripts/linings.sh` (step 7b -> work/linings_v1.blend, the build default): neck cap + `rim_lining.py`
  linings (collar 30 cm, belt 12 cm, boots + trousers 30 cm, sleeves 55 cm to the shoulder; dark texel per region, rim strips,
  collision-capped offsets, inner-layer faces skipped in the sleeves / own-paint 0.5 mm twins elsewhere); shadow meshes drop
  the linings. New gate `scripts/see_through_gate.py` (every 2nd frame of all clips, 16 views, 3 mm px): worst background px
  r6 -> r7 sleeves 431/391 -> 4/4, boots 241/181 -> 0/0, collar 129 -> 2, torso 109 -> 6, trousers 61 -> 0; Running cloth 0
  in every frame. Ears: `fix_ear_pdm2.py` in head_paint.sh (synthesised temple-skin ears, ties/smudges around them removed,
  both tiers). Gates: arm/hand 0 frames > 1 cm in 15/15 clips; jitter 0; poke as r6; floor ok; winding 0; bones 0; flat 0.00;
  detached lists the boots (lining artifact; 0 without the lining triangles). LOD0 8,650 -> 11,942. Installed sha256
  dec7348e99ad...; viewer r7-20261102 30 switches 0 errors; regression passed 192, failed 1 (known out05), mm9_actor_models_build_every_binding PASS. Rollback work/rollback_r6/. Sheets:
  review/sheet_holes_before_after.png, review/sheet_ear_before_after.png. Sibling sweep (render only):
  level_generation/creatures/claude_shared/mm9_overview/holes_sweep_20261102.png.
- Phase: **done** (r7 linings + ears). Credits **35 / 60**. Lease released.
