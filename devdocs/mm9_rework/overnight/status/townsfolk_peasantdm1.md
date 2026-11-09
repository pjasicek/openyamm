# Townsfolk PeasantDM1 (dwarf man) — status

- Project `level_generation/creatures/mm9_peasantdm1_claude/`, lease `mm9:peasantdm1` (owner claude-townsfolk-peasantdm1), budget 60.
- Rows naming PeasantDM1.abc: 8 Commoner (Peasant Dwarf MaleA A, PeasantDM1a), 13 and 14 Shopkeeper (Peasant Dwarf MaleC B, PeasantDM1b).

## Log
- 21:50 UTC lease claimed; reading references. Credits 0 (backup 3555).
- 21:55 UTC sources converted (PEASANTDM1 skins A/B, library PEASANTMALEDWARF 21 clips; no existing retarget of this
  skeleton: mm9_dwarf_claude is the DWARF.abc monster rig). Skins A/B are different men -> per-tier head colour planned.
  Codex master 00 run 1: arms 30 deg down (MM9 bind 20 deg) + halo; rerun with the arm angle stated.
- 22:03 UTC master 00 accepted (retry correction; halo removed by clean_alpha.py). Smart Topology body_smart_v1 done
  (5 credits, backup 3550 before). Fit to the dwarf skeleton (fit_rig.py + `follow` Bone22 -> Spine), reduce 15,704 -> 8,302,
  MPFB hands grafted, head split (neck cut 0.33). Library retarget test on the clay rig: all 14 roles play (clips_mm9.py,
  root nodes Spine + Scene Root + Bone22). UV pass and Codex views 01-04 running. Credits 5.
- 22:45 UTC HD masters 01-04 and head turnarounds A and B accepted; UVs (body atlas 54.2 %, head 59.0 %); body 4K
  retexture, head A and head B 4K retextures done (10 + 10 + 10; backup 3500 -> 3460). Credits 35. Library clips needed a
  source offset (the dwarf clips hold the pelvis 0.2214 m above bind: clips_mm9.py `source_offset`). First test build ok.
- 23:00 UTC built and installed (worlds/mm9/models/mm9_peasantdm1.glb, variants pdm1_a / pdm1_b; tier B own head
  colour). Head fixes without paint: eye cups dropped (eye_fill), neck under the beard, tunic collar rim, forearm skin,
  leather wrist bands over the graft seam. Bound under the flock: rows 8/13/14 in mm9_npc_actor_rows.tsv (322/329/329),
  tables regenerated (9008/9013/9014), actors.yml block mm9_peasantdm1_claude. Gates: arm/hand 0 frames > 1 cm except Talk L
  1.4 cm 3 frames; jitter 0 fails; floor ok x3; winding 0; bones 0; detached 0; flat 0.00; body atlas 54.1 %. Viewer 30
  switches 0 errors. First regression: binding FAIL on "MM9 57 Commoner" (PeasantHOM1's block landed in actors.yml before its
  tables during my run; now consistent), rerunning. Credits 35. Map placement left to the orchestrator (README "Binding plan").
- 23:42 UTC wave-1 lessons applied (orchestrator note): wrists rebuilt (cuff_trim.py: the forearm bisected 3 cm
  before the hand joint, the toothed remnant over the MPFB hand deleted; sleeve_tuck.py tried and dropped, it shrank the
  bare wrist), wrist band repainted over the ring, hand_clean.py on both head sets, eyes/brows checked from 20 deg above
  (review/sheet_eyes_high.png). sleeve_poke_gate: rest 0 mm (was 21.9 / 45.6), 0 in 7 clips; residual 1.9-68 mm on 1-10
  vertices in bent-wrist frames (L AttackMelee 68.2, RubBeard 43.0, Fidget 37.0; R Fidget2 28.0, Running 27.9, Rock 13.5,
  Dump 8.9), renders clean. Reinstalled (sha256 df992d69796e...), floor ok x3, viewer r2-20261102 30 switches 0 errors.
  Final regression: passed 192, failed 1 (known out05); mm9_actor_models_build_every_binding PASS.
- 2026-11-02 06:00-07:40 UTC ear fix (lease owner dm1-ear-fix, 0 credits, no Codex). User note "on his ear some leaked
  wrong textures": both head turnarounds wear a silver braid bead where the ear sits; Meshy's tier A head retexture painted
  that bead (white metal, black engraving; also in its normal and ORM) onto the ear islands. Tier B's ears were skin.
  New step `scripts/fix_ear_pdm1.py` (after wrist_band): the three ear-only UV islands take tier B's ear paint x the cheek
  skin gain A/B, plus B's normal/ORM there; it also removes Meshy's dark net along the beard's lower/back edge on the neck
  (thin crossing strands on skin, no UV seam) with a soft beard fringe. Rebuilt (mesh and clips identical, 3 head images
  changed), winding 0, installed r3 (sha256 366854191073...; r2 rollback in work/), viewer r3-20261102 30 switches 0
  errors, regression passed 192 failed 1 (known out05), mm9_actor_models_build_every_binding PASS. Sheet
  review/sheet_ear_before_after.png. Sweep of 15 installed bodies (report only):
  claude_shared/mm9_overview/ear_sweep_20261102.png; findings in the fix report (PeasantDM2 braid ties on both tiers'
  ears, Tryggva dark hair texels on the ears, PeasantM2 white net behind the ears, PeasantHOM1 dark hairline outline).
- Phase: **done**. Credits **35 / 60**. README is the record. Lease released.
