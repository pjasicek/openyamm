# Townsfolk PeasantHOF1/HOF2 (half-orc women) — status, owner hof-agent

- Project `level_generation/creatures/mm9_peasanthof_claude/`, lease mm9:peasanthof (claimed 2026-11-02 17:00 UTC). Budget 70 credits, floor 1740.
- Rows (MONSTERS.txt): 61 Commoner HOF1a, 62 Town HOF1a, 63 Shopkeeper HOF1b (PeasantHOF1.ABC); 64 Prisoner HOF1c on PeasantHOF2.ABC.
  DAT: CommonerHalfOrcFemaleA 5 (row 61), ShopKeeperHalfOrcFemaleA 4 (row 63); scripts NPCbase/none, shopkeeper.scr, NPC141.scr (no anims).
- Skeleton: HOF1 and HOF2 the SAME 86-node half-orc female skeleton (identical rest except Ponytail1 < 1 deg); clip library
  PEASANTHOFEMALE.abc (13 clips: stand walk run conv1 conv2 cower cowerloop fidget1-3 hattack1 wince1 die1), same local offsets.
- MM9 side by side (`review/mm9_all.png`, `review/mm9_heads_all.png`): HOF1 knee skirt + apron, short sleeves, front braids;
  HOF2 floor-length dress, long sleeves (paint on the same arm mesh), cream kerchief to the shoulders instead of braids.
  Plan: ONE Meshy body (HOF1, design A), B = tier (ramps + own head paint: older woman), HOF2 = variant GLB of the same body
  (skirt lengthened, braids replaced by a kerchief shell, sleeves painted), own paint.
- 17:10 UTC Codex master run 1 (design A three-quarter) running.
- Credits: 0 / 70.
- 18:10-19:00 UTC design A masters (Codex, 2 runs) gated; Smart Topology 5 cr (backup 2665 before). Fit on the 86-node skeleton,
  MPFB hands 0.205 m, level neck cut 0.65, procedural pointed ears (Meshy hid them under the hair), eye cups and a loose mouth
  plate dropped. UVs body 66.9 %, head 54.2 %. Body 4K retexture A 10 cr (backup 2660), head 4K A and B 10 + 10 (2630 / 2620).
  Clay clip check: MM9 library plays on the rig (all 11 roles). HOF2 variant mesh built (skirt to the ankles, apron to mid-shin,
  braids/knot dropped, procedural kerchief to the shoulders), refit on phof2c, own UV pass running. Credits so far 35 / 70.
- 19:00-20:30 UTC HOF1 paint chain (compose, head_fix: ears to cheek tone, grey scalp/neck; seam_tone; face_paint: under-eye
  lift, corner specks), mouth slit closed (mouth_close.py), leftover eye cup dropped; tier B: own head paint against the
  B-recoloured body (skin region ramp), A's painted tusks copied in. First runtime build export/mm9_peasanthof1.glb (LOD0 9,977).
  Gates r3: arm/hand 0 frames > 1 cm in all clips (Fidget/Fidget3 via arm_clear + smooth_correction), jitter 0 fails,
  detached 0, flat 0.00, winding 0, bones 0, body atlas 66.9 %. Viewer r1 24 switches 0 errors. See-through gate running.
  HOF2: Codex views on the variant's clay silhouettes, body 4K 10 cr (backup 2540 before), head turnaround, head 4K 10 cr
  (2530 before). Credits 55 / 70.
- Final (2026-11-02 ~22:00 CET): installed `mm9_peasanthof1.glb` (tiers phof1_a rows 61/62, phof1_b row 63; sha 9594fa82c1aa5918)
  and `mm9_peasanthof2.glb` (tier phof2_c row 64; sha de2c3f11795bfc7e). Bound `MM9 61 Commoner`, `MM9 62 Town`, `MM9 63 Shopkeeper`,
  `MM9 64 Prisoner` under the flock; rows 61-64 in mm9_npc_actor_rows.tsv (stand-ins 430/433/436/438); tables regenerated (9061-9064,
  height 195 / radius 38 by MM9's rule = our 1.97 m model; the brief's ~215 is the half-orc man).
  `mm9_actor_models_build_every_binding` PASS (246 on 109), mm6-8 PASS. Floor 4/4 ok. Viewer r4 36 switches 0 errors.
  Gates: arm/hand 0 frames > 1 cm and jitter 0 fails on both; HOF1 sleeve poke 0 mm, see-through living <= 24 px (Hit 66);
  **HOF2 FAILS sleeve poke** (right wrist flap of the grafted hand over the cuff in Running 27 mm / Death 25 mm) and shows a
  41-87 px see-through at the left wrist ring in every clip; HOF2 detached: hidden legs under the dress, apron 1.5 cm in one frame.
  Credits 55 / 70 (backup 2705 -> 2530 before the last job). README is the record. Lease released.

## Finishing round (FINISH_BRIEF_20261104 job 1), owner hof-finish-20261104, lease mm9:peasanthof claimed 2026-11-04 06:11 UTC
- State found: the cut-off round (2026-11-02 r2) had done a fresh tier-A head paint (Meshy head_retexture_a2, SUCCEEDED, 10 cr:
  body total 65/70), hair taper + copper strands, skirt_leg_blend (HOF1 Death), HOF2 wrist weights v21-v23; exports
  `export/mm9_peasanthof1.glb` (00:05 CET) and `mm9_peasanthof2.glb` (23:46) not installed (installed = 21:46 builds).
  No Meshy job pending (all 7 SUCCEEDED). Backup balance 2370 at start.
- Gates on the uninstalled exports (review/gates/fin4_1, fin4_2): HOF2 sleeve poke 0 mm every clip (was 27.1/25.2 mm);
  HOF1 robe Death 0 (was 5.6 cm), HOF1 sleeve 0; arm/hand 0 frames > 1 cm and jitter 0 on both; HOF2 bone audit: L thigh
  offset stretched 11 % (also in the installed GLB) -> scripts/thigh_length_fix.py in the HOF2 build. HOF2 see-through running.
- Fixes (r6): neck strip under the jaw toned to each tier's body neck (`neck_even.py`, A and B: the body showed between jagged
  orange polygons); tier B fresh 4K head paint `head_retexture_b2` (10 cr, backup 2285 before; old B paint had a pale mask
  panel already in the raw Meshy paint) + warmer skin + own tusks; HOF2 thigh offsets kept at rest length
  (`thigh_length_fix.py`, bone audit 1 -> 0). Hair: copper strands from r2 kept; overlay vs MM9 measured, not reshaped.
- Installed 2026-11-04 ~09:40 CET: `mm9_peasanthof1.glb` sha 9b049f40f1258ff6, `mm9_peasanthof2.glb` sha 511267d32822ed0d
  (bindings unchanged: MM9 61-64). Regression mm9 PASS (251 on 113), mm6-8 PASS. Floor 4/4 ok. Viewer r6 36 switches 0 errors.
- Gates after: arm/hand 0 frames > 1 cm and jitter 0 on both; sleeve poke 0 mm both; HOF1 robe 0 (Death was 5.6 cm);
  HOF2 left-wrist see-through 2-4 px in living clips (was 41-87). Open: HOF2 Death see-through sleeve R 113 px (1 frame,
  level camera), L 58, torso 43; HOF2 heel/calf pokes through the back of the dress in Walking/Running (also in the
  installed build; a skirt weight blend was tried and rejected). Credits 75 (job 10). README is the record. Lease released.

## Pre-screen round r7 (orchestrator notes on r6, 2026-11-04), owner hof-finish-20261104, lease re-claimed 08:42 UTC
- HOF2 dress: knee/thigh-driven leg tuck (dress_clips.py: Walking, Running always, Cower, Hit), skirt joints damped toward
  Standing (Running 0.85, Death/Dead 0.6), legs_hide.py in Death/Dead after the floor passes; dress streaks healed
  (streak_heal.py), kerchief smear refilled (kerchief_smear_fix.py). Before/after: review/sheet_hof2_legs_before_after_r7.png.
- HOF1: ears toned to the cheek (ear_tone.py), cheek-side seams blended (skin_seam_blend.py), the pale wedge beside the jaw (head
  shell nape strip) pulled in (nape_strip_in.py -> master_v6). No credits (75 total).
- Gates r7: arm/hand 0 frames > 1 cm, jitter 0, sleeve poke 0 mm, bones 0 on both; HOF1 robe 0 every clip; HOF2 robe_diag (legs
  visible through the dress) Running 0 (was 8 frames), Walking 2 frames/5 verts (feet under the front hem), Cower 0 (was 37),
  Hit 45 frames/19 verts (feet under the hem, render clean), Death horizontal-ray count not meaningful (renders closed).
  See-through running (step 6).
- Installed 2026-11-04 (r7): mm9_peasanthof1.glb sha e4ec961dde85c755, mm9_peasanthof2.glb sha e415315c3d7fc068. Regression mm9 PASS
  (252 on 114), mm6-8 PASS; floor 4/4 ok; viewer r7 36 switches 0 errors. See-through (step 6): HOF2 living <= 4 px, Death sleeve R
  33 px (r6 113), L 2 (58), torso 39 (43); HOF1 unchanged from r6 (Death/Dead torso 84-94, sleeves 84/104, hair 182; Hit skirt 67).
  Open: B's faint left-cheek line (weaker); HOF2 feet do not plant in Running (legs pulled up under the dress by design). Lease released.

## User review round r8 (jaw asymmetry, 2026-11-04), owner hof-finish-20261104
- r7's nape-strip pull undone (it pinched the jaw corner); HOF1 now master_v5 + 2 head-shell faces deleted beside the jaw
  (strip_delete.py -> master_v8b). Jaw-band mirror asymmetry max/p95: r6 23.7/13.5 mm, r7 20.5/13.5 (both sides 20.5), r8 15.5/12.1.
- Cheek/chin lines: gutters re-padded after the paint steps (pad_gutters.py, A/B/C) + head normals averaged across UV seams with a
  Gaussian under-chin normal turn (normal_seams.py, every build). Fringe-top strip: fringe_edge.py (A, B). Jaw darkening off.
- Installed: mm9_peasanthof1.glb 6d0acf8ac5a0aa20, mm9_peasanthof2.glb 3737f0f580b7919b. Regression PASS (252 on 114), floor ok,
  viewer 36/0, all gates as r7. Open: HOF2's chin shows a diagonal light line in the three.js viewer only (also in r7; not in
  Blender renders); a small pale strip at A's left temple hairline. No credits. Lease released.

## Pre-screen round r9 (2026-11-04), owner hof-finish-20261104
- Ears toned to the skin beside each ear (ear_tone.py rewritten, x1.12), all tiers; HOF2 ears one tone. Normal/ORM gutters re-padded;
  normal grouping by KD-tree; HOF2 nose-underside normal turn (nostrils softer). HOF2 chin line diagnosed as a mesh crease (viewer
  only): not fixed. Installed HOF1 02016ad8a2d3a3e5, HOF2 9529ff1936dadabb; regression PASS, floor ok, viewer 36/0. No credits.

## User review round r10 (jaw asymmetry r9, 2026-11-04), owner hof-finish-20261104
- Cause measured: the head shell's neck seam sat 12-13 mm higher at her right jaw corner (body neck showing, straight diagonal) and
  her right jaw carried 13-21 % R Clavicle + up to 77 % Neck, so the Standing pose bent the sides differently (head-local p95 17.8 mm).
- HOF1 master_v9e: right lower face subdivided once, seam moved to the left side's heights, right shell projected radially onto the
  mirrored left surface (jaw_mirror3.py), weights mirrored + jaw tied to the head (jaw_weights.py), body neck follows the seam
  (neck_relax.py follow). Jaw surface mirror asymmetry max/p95 8.7/2.7 -> 3.1/1.7 mm; posed Standing p95 17.8 -> 4.8 mm.
  HOF2's head is a separate, already-symmetric mesh (p95 2.9 mm): unchanged.
- Fresh 4K head paints A3 and B3 (20 credits; backup 2210 -> 2190; 95 in total), chains + chin_speck (A, B) + cheek_line_heal (B).
- Gates (fin10_1): arm/hand 0, jitter 0, bones 0, sleeve 0, robe 0, detached/see-through identical to r8, winding 0. Installed HOF1
  bb2ae72942e4ed5b (HOF2 unchanged). Regression mm9 PASS (252 on 114), mm6-8 PASS; floor 4/4 ok; viewer r10 36/0.
  Sheets: review/sheet_faces_r10.png, review/sheet_viewer_heads_r9_vs_r10.png. Open: faint soft edge on B's right cheek side,
  coarse body neck under her right jaw. Lease released.
- 2026-11-04: user approved ("half orc ok"), r10.
