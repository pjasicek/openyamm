# Krohn (MM9 row 255, KROHN.abc) — status

- Worker: krohn-20261104 (FINISH_BRIEF_20261104.md, job 3). Lease `mm9:krohn` claimed 2026-11-04 06:11 UTC.
- Project: `level_generation/creatures/mm9_krohn_claude/`.

## Log
- 06:11 lease claimed; reading the MM9 model, its clips and scripts; mesh comparison next.
- 06:20 mesh comparison: KROHN.abc is a 2.78 m giant (108.6 MM9 units) with its own 64-node Bip01 skeleton (hair x3, beard,
  cape x3, front/back flaps, Xspear on the right hand, Xsword on Spine3); raw p90 25-125 cm and height-normalised p90 8-23 cm
  against every built humanoid (`scripts/meshcmp_scaled.py`): no shared body, a NEW body (cap 60 credits).
- Clips: own stand, fidget1-4, walk, stand1, statue, Krohn01-06, Krohn16, Krohnshot25, SC7_22_Krohn; scripts play stand
  (NPC335/WG_NPC335), Krohn01-05, SC7_22_Krohn (WG_NPC335 cutscene), statue (PropAnim statue prop, sculpt skins). No run,
  attack, hit, death: PeasantMale library run/hattack1/wince1/die1 retargeted (BaseName PeasantMale), as Sigmund.
- 06:25 Codex HD primary (00) generated and gated; run 2 (01-04) running.
- 06:45 masters 00-04 and head turnaround gated (review/masters_check.png, review/head_check.png). Meshy Smart Topology 15k
  (5 credits, backup 2355 before): one 15.2k shell + crown/eyes/buckle parts, nearly symmetric (mirror p90 <= 2.8 cm), so no
  symmetrisation (keeps the baldric/medallion geometry). Rig fitted (review/xray_v1.png), reduced to 9.4k, MPFB hands grafted
  (1.86 x scale), cuffs trimmed, head set split (head+hair+beard+crown). Body UVs (uv_atlas) running.
- Weapons: glaive and scabbarded sword built procedurally from MM9's own piece geometry (scripts/make_props.py), rigid on
  Xspear / Xsword (no Codex weapon master: the Guard's weapon prompt was refused).
- 08:05 4K body + head retextures (10 + 10 credits; backup 2325 -> 2315 -> 2305 around the two jobs, other agents spend too).
  Composed, graded gently, MPFB hand skin baked (old caucasian male). Face pre-screen r1 good (eyes open, one brow, one nose,
  closed lips; ears show through the long hair). Runtime build chain scripts/build_runtime_kr.sh (export with the glaive and
  sword joined as a third material, MM9 clips with the cutscene clips' LithTech origin (0,-54,0) removed, constant shoulder
  abduction L 14 / R 9 deg (hands into the fuller scale skirt), right fist solved round the shaft (grip_solve_kr.py, a 22 deg
  wrist turn with the glaive turned back so it stays where MM9 holds it), glaive clearance passes, prepare, LODs, floor, mirror).
- Arm and hand gate: 0 frames > 1 cm in every clip, both hands (before: Standing L 6+ cm / R 4.1 cm every frame). Other gates
  running.
- 09:30 installed `assets_source/worlds/mm9/models/mm9_krohn.glb`, bound `MM9 255 Krohn` (actors.yml block mm9_krohn_claude),
  row 255 -> 565 in mm9_npc_actor_rows.tsv, body override 9255 276/51 (mm9_monster_bodies.py --write-overrides), tables
  regenerated, binding regression PASS (249 descriptors on 111 models). Viewer
  http://127.0.0.1:8912/level_generation/creatures/mm9_krohn_claude/review/viewer/ check 15 switches 0 failed.
- Gates r2 (review/gates_r2/): arm/hand 0 frames > 1 cm (hands) in all 15 clips; sleeve poke 0 mm; sword vs body 0 except Death 3.1 cm
  (5 f, hair); glaive vs body 0 in Standing/Walking/Running/Fidget/Hit/Death/Statue/Krohn02/SC7_22, fails: AttackMelee 6 cm (6 f
  @24, side hair), Krohn01 6 cm (10 f), Krohn04 6 cm (3 f), Krohn05 6 cm (56 of 484 f) (butt behind the right thigh), Krohn03 1.0;
  jitter fails AttackMelee (L upper arm +2.0 deg/f) and Death (forearm +1.1 deg/f, skin 4.0 mm/f2): faded end abduction;
  detached: the glaive guard 2 cm off the fist cluster in 2 AttackMelee poses; winding 0; flat 0.00 (props 0.07, hard blade edges).
- Final rebuild pending: walking floor (ground-loop + smooth 0.06) and L 14 deg at the ends of AttackMelee/Hit/Death.
- 11:00 FINAL (installed sha256 f5516e6e4202..., viewer r7-20261104, README has the full table):
  rim linings added (bracer ends, skirt/tabard hems); glaive/sword faces made outward (the first builds had the glaive inside out);
  sword carried by the cape centre pivot; hair follows Spine3 in the retargeted clips; walking floor ground-loop + 0.06 s smoothing.
  PASS: arm/hand 0 (hands and forearms, all 15 clips); sleeve poke 0 (Dead L 1 mm); winding 0; bones 0; flat 0.00; regression PASS
  (251 descriptors); viewer 15/0.
  FAIL / open: glaive vs body AttackMelee 6 cm (6 f @24, side hair), Krohn01 6 cm (12 f), Krohn04 6 cm (3 f), Krohn05 6 cm (55/484 f),
  Krohn03 1.0 cm; sword vs hair Death 3.1 cm (5 f); jitter AttackMelee (L +2.4 deg/f, skin 15.8 mm/f2) and Death (L forearm +1.4
  deg/f, skin 4.0); floor walk lift +3.8 units (tolerance 2.76); see-through torso 129 px sliver at the cape side (every clip),
  sleeves 75/62 px and collar 73 px in Death.
  Credits 25 (Smart Topology 5, body 4K 10, head 4K 10); backup now 2230 (shared account).
  Map placement not switched (orchestrator's step): the Hall of the Gods still places legacy 565; DAT Scale 1.25 there.
- Lease mm9:krohn released.
- 2026-11-04 motion pass (orchestrator pre-screen of r7; lease re-claimed as krohn-20261104b, no credits). Installed sha256
  7cbdb15c12b6..., viewer r9-20261104 (15/0). Jitter 0 fails in every clip (AttackMelee/Hit/Death ease 0.3 s to the abducted
  Standing instead of carrying an offset; Death floor smoothing 0.15 s); hands/forearms 0 frames > 1 cm (all clips); floor_audit
  ok (walk -2.1..+2.1, walk_floor.py low-pass); glaive vs body AttackMelee 13.8 -> 0.4 cm (spear_window.py), Krohn01 0.2, Krohn04 0.0,
  Krohn03 1.4 cm (1 f), Krohn05 2.2 cm (3 f, left); sword vs hair Death 3.1 -> 0.2 cm (hair_window.py, side strand); regression PASS
  (252 descriptors). See-through as r4. Sheets review/shots/sheet_motion_fix_r8.png. Lease released.
- 2026-11-04: user approved ("krohn ok"), r9.
