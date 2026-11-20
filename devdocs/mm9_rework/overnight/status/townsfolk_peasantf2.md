# Townsfolk PeasantF2 (human townswoman, long sleeves with bell cuffs, braid) — status, owner f27-agent

- Project `level_generation/creatures/mm9_peasantf2_claude/`, lease mm9:peasantf2 (claimed 2026-11-02 16:05 UTC).
- Rows (MONSTERS.txt): 31 Town F2a (TownHumanFemaleA, 1 placed), 38 Town F2a (TownHuman2FemaleA, 2), 32 Town F2b (TownHumanFemaleB, 0),
  39 Town F2b (TownHuman2FemaleB, 3). All NPCbase.scr, PeasantFemale library.
- Comparison (`mm9_meshcmp.py`): same 73-node skeleton but bind differs up to 16.7 cm from F1/F5/F8/Yrsa; shifted arms p90 10-12 cm,
  torso 3-7 cm, head 7-10 cm: a NEW body. F7 vs F2: arms p90 12.3, torso 7.6 cm: F7 is a new body too.
- Route: F5's new-body route (Codex masters skin A, Smart Topology, MM9 skeleton + peasantfemale clips, MPFB hands, 4K body + head retextures).
- Now: MM9 refs rendered (`references_hd/mm9_*`), Codex run 1 (three-quarter master) running.
- Credits: 0 / 50.
- 18:20 Codex masters done (run 1 retried after a stuck session); Smart Topology 5 + body 4K 10 = 15 / 50 (backup 2675 before the body job).
  Geometry frozen: fused-shell split with clean neck and waist plane cuts, sleeves pulled/turned onto MM9's arm, bell cuffs kept on the
  sleeve with their closing disc pressed into a funnel, MPFB hands with stubs in the cuffs, ears smoothed into the skull under the hair
  (a modelled side-hair panel was tried and dropped: it read as cheek guards), hair cap fitted to MM9, bead necklace, skirt lining.
  LOD0 14,676. Rig/clips done; arm/hand 0 frames > 1 cm. Tiers: R dress (rust/teal), G necklace (copper/green-blue). Head turnarounds
  running (retried after a stuck session).
- 19:45 Credits **35 / 50** (Smart Topology 5, body 4K 10, head A 4K 10, head B 4K 10; backup 2650 before head A, 2610 before head B).
  Hair cap stretched over the ears to the jaw (positions only, `tweak_pf2.py`) after the modelled side panel failed; Codex face repaint projected.
  r6 gates: arm/hand 0 frames > 1 cm (Conv3 L forearm 1.0 cm one frame); jitter 0; flat 0.00; bones 0; atlas 64.2 / 61.0 %; robe Death 0.4 /
  Cower 0.7 / Dead 0.9 cm -> shins slimmed 15 % inside the skirt (r7 pending). See-through gate running.
- 20:20 r7 **installed** `assets_source/worlds/mm9/models/mm9_peasantf2.glb` (sha256 72806032434649de...), bound `MM9 31 Town`, `MM9 38 Town`
  (pf2_a), `MM9 32 Town`, `MM9 39 Town` (pf2_b) under the flock (rows 31/32/38/39, stand-ins 352/353/379/380, ids 9031/9032/9038/9039; tables
  238 rows). Binding regression PASS (238 descriptors on 104 models, 0 failed); floor audit ok x4; viewer check 22 switches 0 failed.
  r7 gates: robe 0 in all 11 clips (shins slimmed); hand stub poke 0.0 mm all clips; arm/hand 0 frames > 1 cm; jitter 0; flat 0.00; LOD0 14,984.
  See-through: sleeves 0 (bell funnels), collar 2 px, but head 212 / torso 256 px in every frame at the lower sides of the hair: investigating.
- 21:50 **FINAL r8** installed (sha256 b1de5bbbca41...): hair rim lining + head-set materials doubleSided (engine flips back-face normals,
  fs_model.sc) so the hair cap's inside no longer shows background. Gates r8: arm/hand 0 frames > 1 cm; hand-stub poke 0.0 mm; robe 0 all clips;
  jitter 0; flat 0.00/0.00; bones 0; winding 0; LOD0 14,984; atlas 64.2 / 61.0 %; see-through (double=1) head 0, torso 9 px (Death), sleeves 0,
  collar 2. Binding regression PASS (240 descriptors on 105 models); floor ok x4; viewer 22/0. Faces review/sheet_r8a_face.png, r8b.
  Open: the cap's inside now shows as a light flap behind the ear at the braid top (3/4 and low views). Credits 35/50. Lease released.
- 22:40 FACE PASS 2 (coordinator review): r12 installed (sha256 bbfe93f93876...). Geometry first: Meshy's nose/lips kept (my F5-derived nose
  smoothing removed), slit closed, eyes back + lids 2 mm down, hair-cap rim smoothed and tucked onto the skin (no inside flap, no side flaps),
  midline cracks welded; frozen (hash dc19914f, unchanged since). Fresh Meshy 4K heads A+B on it (20 cr: backup 2420/2410 before) -> credits
  **55**. Codex projection retired; paint finish only (lips rose, specks, nostril lift, lid shade); forehead midline normals relaxed.
  Gates r12: arm/hand 0; stub poke 0.0; robe 0; jitter 0; flat 0.00; bones 0; winding 0; LOD0 15,000; atlas 64.2/61.1 %. Regression PASS
  (246/109); floor ok x4; viewer 22/0. Sheet review/sheet_faces_pass2_before_after.png. Remaining: lips read slightly apart from below,
  small notch in the cap's back edge in profile, eyes a little round, dark under-chin from below.
- 23:10 see-through r12 (double=1): head 0, torso 9 px (Death), collar 2, sleeves 0/1. Lease released.
- pass 3 (0 cr): nostrils on the real openings, lightened; r15 installed (sha256 6a0ea69d6b91...), binding PASS 248/110, floor ok, viewer 22/0. Lease released.
- 2026-11-04 NECK GRAFT PASS (owner f2f7-neck-20261104, user review "soldered on", 0 credits): r19 installed (sha256 956a91f002e3...).
  Dark band = the head's neck cap summed into the seam normals (seam normal z -0.93 -> +0.45/+0.65): outer-only normals; the cap dropped
  (its rim z-fought into a dotted line; LOD0 15,000 -> 14,936); dress midline crack closed (5 verts <= 0.33 mm). "Orange chest" = the chest
  skin inside the neckline was in the dress ramp region: now its own region (mask B) with per-tier ramps onto each tier's neck skin;
  tier B's painted choker cloned over with neck skin; neck paint feathered to one tone; midline line (normals + paint), tier A forehead band
  equalised. Nostrils: paint lift had no visible effect (geometry shading) - open. Gates: winding 0; flat 0.00/0.00; arm/hand 0 frames > 1 cm;
  robe 0; jitter 0; bones 0; texture quality unchanged (64.2 / 61.1 %); see-through (double=1) torso 9, collar 2, sleeves 0, head 1 px
  (Conv3 side view, at the left bell cuff, not the neck). Validate-actor-models 250/112, 0 refused; floor ok x4; viewer check 0 failed.
  `mm9_actor_models_build_every_binding` PASS on the final rerun (252/114; an earlier run failed on another job's `MM9 256 Fre`). Sheet
  review/sheet_neck_r15_r19.png, review/sheet_mm9_vs_ours_r19.png. Rollback work/pre_neck/.
- Lease mm9:peasantf2 released (f2f7-neck-20261104).
- 2026-11-04 PRE-SCREEN PASS (f2f7-neck-20261104, 0 credits): r20 installed (sha256 97177d5e7ed9...). Nose-underside and under-chin
  normals tilted (Igrid's method), nostril paint soft; mouth fold (24 backward faces) unfolded <= 1.44 mm + groove normals + lip paint
  (tier B's painted teeth) - a post-paint patch, no repaint credits. Gates unchanged; binding test 251/252 (failure: MM9 266 Green Man,
  another job). Sheets review/sheet_mouth_nose_prescreen.png, review/sheet_face_r15_r20.png. Lease released.
- 2026-11-04 SECOND PRE-SCREEN PASS (f2f7-neck-20261104): r24 installed (sha256 1834cf18534990cd). Mouth (MOUTH2) and columella (NOSE2)
  rebuilt before a fresh Meshy 4K head paint A+B (20 credits, backup 2230 -> 2210; F2 total 75); v2-only face fixes off; nose/chin/groove
  normals as F7 r37. Gates unchanged; binding test PASS 252/114. Sheets review/sheet_mouth_nose_v3.png, review/sheet_face_r19_r24.png.
  Lease released.
- 2026-11-04: user approved ("peasantf2 ok"), r24.
