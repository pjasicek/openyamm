# Variant PeasantM4 (row 49 Prisoner, skin PeasantM4a) — owner m45-agent, 2026-11-02

Project `level_generation/creatures/mm9_peasantm4_claude/` (lease mm9:peasantm4, claimed 15:43 UTC, backup 2815).

## Log
- 15:43 lease claimed. meshcmp re-run: M4 has PeasantM8's / Forad's exact binds (bind diff 0.00 cm); vs Forad head 0.5,
  arms 0.1, legs 1.5, torso 4.9 cm p90; vs PM8 torso 4.1. Next: side-by-side MM9 renders, route decision.
- 17:10 Decision: **variant route on PeasantM8** (= Forad's body; M4 has PM8's/Forad's exact binds, bind diff 0.00 cm, not M1's).
  MM9 side by side (`mm9_peasantm4_claude/references_hd/mm9_m4_vs_forad_pm8_body.png`, `review/sil_mm9_pm8_red_mm9_m4_green.png`):
  M4 = PM8's mesh with a fuller belly, waist, hips and thighs (3-5 cm); head, arms, boots the same. Paint: old balding man, white
  side/back hair, white walrus moustache; olive-green open jerkin with chevron braid and torn hem over a cream long-sleeved
  shirt, no belt, ribbed trousers torn at the knees, cuffed boots. Clips: PM8's set without Conv2/Conv3 + Fidget3
  (DrangheimPrisoner.scr PlayAnim Fidget3/cower; NPC90.scr none). Row 49 = DAT PrisonerHumanMaleA (7 placed).
- Geometry: `scripts/reshape_m4.py` (spatial MM9 PM8->M4 offset field, gain 1.5) + `scripts/belt_smooth.py` (PM8's waistband lip
  smoothed away: no belt) on a copy of PM8's `master_v2.blend` -> `work/reshape_v4.blend`; self-overlaps 133 = PM8's 133.
  Body upload = PM8's upload with the same moves (`move_upload.py`, UVs unchanged). PM8/Forad sha256 baseline taken (1465 files).
- Codex body master run 1 running (Codex reconnecting). Credits 0.
- 16:43 Codex head turnaround selected (references_head/selected_views_review.png read: calm smiling old man, white walrus moustache, bald top, white side/back hair). Moustache volume sculpt tried and dropped (read as a pouting upper lip in clay, review/clay/face_moustache_v1.png): paint only. Meshy head 4K retexture submitted (backup 2730 before), 10 cr.
- 17:50 Head retexture done (10 cr, SUCCEEDED; backup 2730 before). Composed (`compose_head_texpass.py forad_tp pm4`), hands toned to
  the new face (`hand_tone.py`). First close-ups `review/head/r0.png` + flat `review/head/hd_sheet.png`: bald crown, white side/back
  hair, white walrus moustache, closed smiling mouth. Clips/test builds: PM8's gates reproduced (Talk L 3.4 cm = PM8's 3.3), Fidget3
  hands 6 cm into the fuller hips -> one eased 14 deg abduction (`clap_spread.py`; hand_rest jittered 1.5-2 deg/f); jitter 5 = PM8's.
  Body Codex run 2 still reconnecting. See-through gate running on the test build.
- 19:00 Body masters selected (references_hd/selected_views_review.png, review/body_clean_check.png read); Meshy 4K body retexture
  (backup 2685 before) SUCCEEDED: **M4 total 20 credits, no further jobs**. Composed + gentle grade; `trim_calm.py` (the chevron
  braid came out as a stark leopard print: calmed to a woven brown band on the upper torso), `collar_match.py` (head-set collar to the
  body tone), lining texel to the cream cuffs (`lining_texel.py`), `head_pm4.json` (the 5-edge back hole filled at export: it was the
  only torso see-through). Build r2 = `work/r2_final.glb`. Sheets read: `review/sheet_mm9_vs_ours_r1.png`, `review/r2/upper.png`,
  `review/sheet_face_viewer_r2.png` (viewer lighting: front, 3/4, both profiles, low 3/4, party view, 128 px).
- Gates r2: arm/hand = PM8's (Talk L 3.4 cm 38 f; Fidget R forearm 2.3 cm, PM8 1.2); jitter 5 = PM8's accepted 5; sleeve poke =
  PM8's (hard wrist bends, Forad's bracer); detached 0; flat 0.1/0.0 %; winding 0; bones 0 stretching; texture body atlas 53.3 %
  (PM8 53.3), spread 1.14, stretch p90 1.42, head 44.0 %. See-through full run in progress.
- 19:55 **Installed** `assets_source/worlds/mm9/models/mm9_peasantm4.glb` (sha256 647521a7d859...), bound `MM9 49 Prisoner` (row 49 ->
  366 in mm9_npc_actor_rows.tsv, tables regenerated 230 rows) under the flock; binding regression PASS (230 descriptors / 101 models);
  floor ok; viewer r3 check 11/0 failed. See-through final: head/torso/collar/boots/trousers 0, sleeves R 12 px (4 f) / L 4 px (3 f)
  cuff-rim slivers (PM8 22/4). Ears sheet read (clean). PM8 + Forad sha256 (1461 files + 4 GLBs) identical before/after.
  README written. 20 credits total.
- Lease mm9:peasantm4 released.
