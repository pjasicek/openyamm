# Townsfolk PeasantF7 (elf townswoman, long hair, front braids) — status, owner f27-agent

- Project `level_generation/creatures/mm9_peasantf7_claude/`, lease mm9:peasantf7 (claimed 2026-11-02 16:05 UTC).
- Rows (MONSTERS.txt): 18 Town F7a (TownElfFemaleB, 7 placed), 20 Shopkeeper F7b (ShopkeeperElfFemaleB, 3). NPCbase.scr, PeasantFemale library.
- Comparison: F7 vs F5/F6 bind differs 7.2 cm, shifted head p90 4-5 / torso 3-4 / arms 5.3 cm; vs F2 arms 12.3 / torso 7.6 cm.
  Not within 1.5-2 cm of anything built: a NEW body (budget 50).
- MM9's F7 hides the ears under the hair (no visible elf ears in any view): following MM9.
- Now: MM9 refs rendered, Codex run 1 (three-quarter master) running.
- Credits: 0 / 50.
- 18:20 Codex masters (2 runs) + head turnarounds A/B done; Smart Topology 5, body 4K 10, head A 4K 10, head B 4K 10 = **35 / 50**
  (backup 2755 -> 2715 seen before the last F7 job). Geometry frozen (`work/asm_frozen.npz`, F1-style fused-shell split, MPFB arm+hand,
  procedural bracelets, F3-style braids on MM9's xpony path, hair fitted to MM9's silhouette, Meshy's skirt closed so no lining,
  mouth inserts and eyelash cards dropped), LOD0 14,312. Rig/clips (MM9 peasantfemale lib), ARMDEG 5 + Conv3 arm_clear.
  Gates (pre-face): arm/hand 0 frames > 1 cm all clips; jitter 0; flat 0.00; bones 0; texture body 63.5 % / head 56.4 %; skirt lift 0.14.
  Face: Meshy's paint kept (procedural eye/nostril repaints made it worse, reverted); Codex face repaint by landmarks running.
- 19:45 **installed** r14 `assets_source/worlds/mm9/models/mm9_peasantf7.glb` (sha256 8a111b1f754e...), bound `MM9 18 Town` (pf7_a, 9018) and
  `MM9 20 Shopkeeper` (pf7_b, 9020) under the flock (rows 18/20 in mm9_npc_actor_rows.tsv, stand-ins 335/338, tables regenerated). Floor audit ok.
  Gates r14: arm/hand 0 frames > 1 cm all clips; robe 0 all clips; jitter 0; flat 0.00/0.00; bones 0; detached = 1 free leg (by design);
  winding 0; texture body 63.5 % / head 56.3 %. Faces: Codex repaint by landmarks projected (`project_face_pf7.py`), sheets
  review/sheet_r14a_face.png, sheet_r14b_face.png. Caps over the head's open skull/neck loops, waist, arm stubs (`line_rims_pf7.py`).
  Binding regression and the see-through rerun after the caps: pending (run with F2's).
- 20:20 r15 reinstalled (sha256 1745c7217f4ddd59..., hair rim lining added); regression PASS (238/104); floor ok; viewer 22/0.
  Sleeve poke: Death 2.6 mm / Dead 1.9 mm (MPFB upper arm through the short sleeve in the corpse) -> arm slimmed inside the sleeve (r16 pending).
- 22:15 **FINAL r16** installed (sha256 643d7ed9723c...): upper arm slimmed inside the short sleeves, hair rim lining, head-set materials
  doubleSided. Gates r16: arm/hand 0 frames > 1 cm; sleeve poke 0.0 mm every clip (r15 Death 2.6 mm); robe 0 all clips; jitter 0; flat
  0.00/0.00; bones 0; winding 0; LOD0 14,952; atlas 63.5 / 56.3 %; see-through (double=1) head 0, torso 49 px (Death from behind), sleeves 1-3,
  collar 2. Binding regression PASS (240 descriptors on 105 models); floor ok x2; viewer 22/0. Faces review/sheet_r16a_face.png, r16b.
  Open: ~2 mm pale speck at the columella base (Meshy geometry), eyes a little wide, hair sheet flings up in Wince/Fidget (MM9's keys).
  Credits 35/50. Lease released.
- 22:40 FACE PASS 2 (coordinator review): r21 installed (sha256 d891830cda4e...). Causes: my F5-derived tweak blunted the nose; unwelded
  mirror-seam vertices + dropped needle slivers = open cracks under the nose/chin/forehead/parting; Meshy's columella/nostril shards.
  Geometry: nose/lips kept, slit closed, eyes back + lids 2.6 mm down, cracks welded, pinhole caps, philtrum holes collapsed; frozen and
  painted fresh (Meshy 4K heads A+B, 20 cr: backup 2400/2390 before) -> credits **55**; after the paint only the nose-underside shards were
  smoothed (<= 2.5 mm, 56 positions) and their texels repainted from position. Gates r21: arm/hand 0; sleeve poke 0.0; robe 0; jitter 0;
  flat 0.00; bones 0; winding 0; LOD0 14,942. Regression PASS (246/109); floor ok x2; viewer 22/0. Sheets review/sheet_faces_pass2_before_after.png,
  review/zoom_r21.png. Remaining: pale line on tier A's hair parting, faint pale tick at tier B's forehead top, lighter bridge facet,
  soft dark nose underside from the front, eyes a little round.
- 23:35 see-through r21 (double=1): head 0, torso 48 px (Death, from behind), sleeves 1-3, collar 2. Lease released.
- pass 3 (0 cr): midline paint seam line fixed + seam normals blended (feathered 7 mm), nostrils on the real openings, hair parting cleaned; r25 installed (sha256 10f163a3572f...), binding PASS 248/110, floor ok, viewer 22/0. Lease released.
- 2026-11-04 NECK GRAFT + UPPER LIP PASS (owner f2f7-neck-20261104, user review, 0 credits): r33 installed (sha256 86b89267d675...).
  Dark band/V notches = the two head neck caps summed into the seam normals (seam normal z -0.80 -> +0.45): outer-only normals, caps
  dropped (148 faces; LOD0 14,942 -> 14,794), 9 dress loop verts snapped (<= 0.93 mm). Graft paint (chemise/bead colours on the bottom
  1.2 cm of both heads) cloned over; necks + chest skin feathered to one shared skin (body has no free mask channel); shoulder V / chest M
  paint marks cloned over; neck midline normals. Upper lip: 20 folded front faces at the closed slit (drawn as their back side = black)
  unfolded (<= 1.5 mm, post-paint deviation) + groove normals turned 60 % forward + lip-red underside paint: no black triangle/slit.
  Tier A forehead band equalised. Nostrils: not fixed (geometry shading; normal edits on the nose forbidden) - open.
  Gates: winding 0; flat 0.00/0.00; arm/hand 0 frames > 1 cm; robe 0; jitter 0; bones 0; sleeve poke 0.0 mm all clips; texture 63.5 /
  56.4 %; see-through (double=1) torso 48 (Death, as r21/r25), collar 2, sleeves 1-3, head 0. Floor ok x2; viewer 22/0; validate 252/114 0 refused; `mm9_actor_models_build_every_binding` PASS (252/114).
  Sheets review/sheet_neck_r25_r33.png, review/zoom_mouth_r32.png, review/sheet_mm9_vs_ours_r33.png. Rollback work/pre_neck/.
- Lease mm9:peasantf7 released (f2f7-neck-20261104).
- 2026-11-04 PRE-SCREEN PASS (f2f7-neck-20261104): r37 installed (sha256 43d0cff97cce...). Mouth geometry rebuilt BEFORE paint (MOUTH2:
  3D relax of the slit region + subtle sculpted lips; frozen work/geom_final_v3.npz), fresh Meshy 4K heads A+B on it (pf7_head_a_v3 /
  pf7_head_b_v3, 20 credits, backup 2250 -> 2230; F7 total 75), v2-only paint fixes switched off. Nose-underside and under-chin normals
  tilted (Igrid's method); nostril paint soft. Gates unchanged (see README). Binding test: 251/252, the failure is MM9 266 Green Man
  (another job). Sheets review/sheet_mouth_nose_prescreen.png, review/sheet_face_r25_r37.png. Lease released.
- 2026-11-04: user approved ("peasantf7 ok"), r37.
