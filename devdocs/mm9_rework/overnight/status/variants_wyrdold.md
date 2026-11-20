# MM9 Igrid, Wyrde of the Known (wyrd_old row 263) — owner igrid-scholar-agent

Project `level_generation/creatures/mm9_wyrdold_claude/`, lease `mm9:wyrdold` claimed 2026-11-02 18:56 UTC.

- 18:56 lease claimed. meshcmp: vs wyrd_young same 73-node skeleton but bind max diff 26 cm, torso 10.8 cm (shifted); vs Hag/Yrsa bind 8 cm,
  torso 6.9 cm, arms 1.1 cm, head 2.6 cm. Deciding route (Wyrde variant vs new body).
- Credits: 0 / 50.
- 19:20 Route decided: NEW BODY. wyrd_old shares the 73 joint names with the Wyrde but its bind is stooped (bind max diff 26 cm, torso
  10.8 cm after a rigid shift); its skeleton and five clips (stand, walk, fidget1, Wince3, Die3) are Yrsa's/Hag's (bind diff 8 cm, braid
  chains). Design = Wyrde-like hood + full-length open brown robe with sleeves over a navy gown. Plan: Wyrde mesh pipeline (seg/assemble/
  weights with skirt chains) on wyrd_old's own skeleton and own clips (Yrsa's role set). Codex 00 master gated (stoop milder than MM9).
- 19:25 Smart Topology 5 cr submitted (backup 2480 before). Codex run 2 (four views) running.
- 20:30 Smart Topology back (one fused robe/hood/bodice shell, face shell, gown skirt, braids as thin cords, a loose lip shell over a parted
  pursed mouth, flat hair plates on the forehead). Assembled (`assemble_wo.py`); face geometry finalised BEFORE paint (`face_geo_wo.py`:
  loose lip shell and plates deleted, mouth rebuilt closed with subtle lips, lids opened 12/7 deg: Meshy's eyes were a 3 mm slit).
  Rig/clip smoke test on MM9's own wyrd_old clips OK. UVs (`uv_wo.py`, never re-run): body 60.1 %, head 62.2 %. Codex head turnaround OK.
- 20:40 Retextures 4K body 10 cr (backup 2470 before) + head 10 cr (2460 before) submitted. Credits 25 / 50.
- 21:00 Paints composed (`compose_wo.py`, gentle grade). Face pre-screen in the viewer (r1-r6, `review/face_r*_sheet.png`): braids recoloured grey
  with a plait pattern (Meshy painted them hood brown), the maroon cap Meshy painted over the scalp -> grey hair in the hood's shade, the forehead
  swag -> skin, the dark wrinkle net softened 65 %, nostrils and lip dimple lifted, lips desaturated, gold circlet band + small ruby gem
  (gem geometry halved after the paint: jewel piece, not face), the cream neckline -> dark collar. Face geometry untouched after the paint.
  See-through gate r1 running.
- 21:20 Gates round: linings (rest + posed back faces, robe/gown hem bands, a hood box behind the neck; LOD0 14.5k); see-through r1 -> r2
  torso Death 14728 -> 1358 px, Dead 11773 -> 173, Hit 10162 -> 128, collar Death 2000 -> 319. Hands: walk/run arm_clear, Fidget a smooth
  per-clip arm offset (abd 20 / flex 20 deg, eased) -> 0 frames > 1 cm, jitter 0; hand_rest's 13 cm push jittered (dropped). Robe gate: Hit
  damp removed, Death/Dead robe chains lifted only to 10 cm of the floor, shins shortened. Gates r3 + see-through r3 running.
- 21:35 INSTALLED `mm9_wyrdold.glb` (r9, sha fe1eb529f983), bound `MM9 263 Wyrde of the Known (Igrid)` under the flock, row 263 in
  mm9_npc_actor_rows.tsv (fallback 376), body overrides + tables regenerated (9263: height 174, radius 31). Binding regression PASS (245 on
  108). Floor ok. Viewer r9 check 0 errors. Credits 25 / 50. Open: Death hand under robe (23 f), Death/Dead shoes out under the hem 7.8 cm,
  Death mid-fall see-through 1079 px, Fidget R wrist 24 mm through the cuff (MM9's own bend). README has the gates. Starting the Scholar.
- 22:45 Lease mm9:wyrdold released.
- 23:50 Coordinator review round: lease re-claimed (coif, wrinkle net, Death gates).
- 2026-11-04 06:11 UTC Finishing job (owner igrid-scholar-finish-20261104): lease mm9:wyrdold claimed. Installed `mm9_wyrdold.glb` = export
  (sha 50096212c87c, r12, 2026-11-03 00:02 CET); gates after it: arm/hand, robe, bone length, see-through r5, regression PASS; jitter/flat/
  texture/detached ran on the build before the last legs_hide change (re-run). Meshy: no pending job, backup 2370. Face r11 read zoomed:
  coif reads as a white cap without folds, the skin blotchy from the net closing, orange/white bands under the eyes, faint wrinkles only:
  more than two patch passes -> fresh head paint (Codex head turnaround v2 with a linen coif, soft creases, gentle smile; then Meshy 4K).
- 06:22 UTC Codex head turnaround v2 (`references_head_v2/`: ivory linen coif with folds under the hood, circlet on its edge, soft natural
  creases, gentle closed smile, warm skin) read and accepted. Meshy head retexture 4K `wo_head_v2` on the final head mesh (`uv_tw.npz`,
  same UVs) submitted, 10 cr (backup 2365 before). Lease re-claimed with budget 45 (25 spent before + this job's 20 cap).
  Death arm trials (`work/armtry/`): right arm abd 10 deg eased 0.15-0.42 s in, 0.6-1.4 s out -> Death R 4.1 -> 2.1 cm (1 f), jitter 0.
- 06:40 UTC Head paint v2 composed (`compose_wo.py wo_head_v2 head`; v1 maps kept in `work/head_v1_backup/`). Meshy painted the scalp as a dark
  hair fringe down to the brows (the hood is not in the head upload) and no coif: new `scripts/head_fix_wo2.py`: braids/gem/band as v1; the
  coif from the Codex v2 front view projected from the front (eyes + gem anchors) over a procedural linen; the forehead and brows from the
  Codex view, toned to Meshy's skin; net and lifts off. A dark moustache-like band above the upper lip was SHADING of the rebuilt mouth
  patch's upper rim (unlit raster `work/hv2/raster.png`): normals of that band relaxed in `build_glb_wo.py` (ULRELAX, positions unchanged)
  + paint x1.12. Face sheets r13-r15 read; r15 is the candidate. Gates on r15 running.
- 07:58 UTC r15 INSTALLED (`mm9_wyrdold.glb` sha f893bcb2b8ea, r12 kept in `work/head_v1_backup/`). Gates r15: robe 0 every clip; sleeve
  poke 0 except Fidget R 24 mm (unchanged, MM9's wrist bend); see-through r6 torso Death 370 / Dead 219 px, all one-pixel hem slivers
  (0 after a 1-px erosion); arm/hand Death R 4.0 cm 1 f (hand brushes the hood at 0.48 s; 2.1 cm on the unmirrored build), Death L 1.4 cm
  4 f (hood), Dead L 1.4 cm 4 f (resting on the right sleeve); jitter 0; flat 0.00/0.00; texture body 60.1 % / head 62.2 %; floor ok;
  viewer check 7 clips 0 errors. Credits 35 / 45 (this round 10). README updated. Regression after the Scholar install (one run for both).
- 08:10 UTC Regression with both installs PASS (248 descriptors on 110 models). Backup 2275 at the end. Lease released.
- 08:15 UTC Orchestrator pre-screen of r15: one more pass (nose blot, age, coif edge at the temples). Lease re-claimed.
- 08:45 UTC Pre-screen pass (paint + normals only, no positions moved): (1) nose blot = shading of the large downward nose underside
  (unlit raster `work/hv2/raster_low.png` shows clean paint): underside normals tilted toward the front in `build_glb_wo.py` (NOSETILT),
  small soft nostril shadows painted (NOSTRILK); (2) age: Codex v2 creases transferred multiplicatively with a landmark height map
  (eyes/nose base/mouth), warmer ruddier skin, cheek flush; lips excluded (no second lip line); (3) coif edge: fold shadow on the coif
  and cast shade on the skin by 3D distance. Builds r16-r20; r20 is the candidate (no credits). Gates running.
- 09:00 UTC r20 INSTALLED (sha 16fe15cf6d31). Positions and clips unchanged: arm/hand Death R 4.0 cm 1 f, L 1.4 cm 4 f, Dead L 1.4 cm 4 f
  (as r15), robe 0, jitter 0, flat 0.00/0.00, texture 60.1 / 62.2 %; viewer check 7 clips 0 errors; floor ok; regression PASS 248 on 110.
  No credits this pass (35 / 45 total). Backup 2270. README updated. Lease released.
- 09:10 UTC User review r20: hands out of the sleeves. Lease re-claimed.
- 09:25 UTC r22 INSTALLED (sha 77cde78e5c89): hands into the sleeves (cause: wide bell cuffs + MM9's wrist bent 34-59 deg down, the hand
  left through the cuff's lower edge and the opening showed its empty inside). Cuffs tapered to 45 % radius at the rim, cuff rim 35 % Hand
  weight, wrist bend clamped to 30 deg (34 in Death/Dead). Sleeve poke 0 in every clip (was Fidget R 24 mm); see-through sleeves worst
  32 -> 28 px; arm/hand Death R 3.7 cm 1 f, Death L 1.6 cm 4 f, Dead L 1.8 cm 6 f (was 1.4 / 4 f). Regression PASS 250 on 112 (rerun;
  first run caught another agent's PeasantF4 install mid-way). No credits. Backup 2250. Lease released.
- 09:35 UTC Pre-screen r22: jagged cuff rims. Lease re-claimed.
- 11:30 UTC r42 INSTALLED (sha 597705e92727): cuff rims. The teeth were mostly the MPFB stub (sparse spiky cone, dark paint) seen through the
  gathered opening, plus the crumpled rim and an inner sleeve layer folded toward the wrist. Kept: taper over 14 cm, rim end stretched to 1 cm
  behind the wrist, rim >= 3.4 cm off the axis, inner layer at 2.4 cm, stub rebuilt as a clean tube (flip repair), cuff ends lined (6.5 cm).
  Dropped: rim relaxation (see-through sleeves 79-85 px), longer stub, wrist-ring reweighting. Gates: sleeve poke 0, see-through sleeves worst
  28 px, robe 0, jitter 0, arm/hand Death R 3.6 cm 1 f / L 1.6 cm 4 f, Dead L 1.8 cm 6 f; LOD0 15,067 (67 over 15k). Regression PASS 252 on
  114; floor ok; viewer 0 errors. One small dark V notch remains on top of each wrist in close views. No credits. Backup 2210. Lease released.
- 11:40 UTC Pre-screen r42: dark V on top of each wrist; third pass (diagnose with flat part colours, close the junction, undersleeve band). Lease re-claimed.
- 12:50 UTC r43 INSTALLED (sha c787513947e1): navy undersleeve bands. Diagnosis (part_raster.py, flat part colours, back faces magenta): the V
  was the hand/stub junction's long thin triangles lying edge-on (dark), the stub tube standing out of the gathered cuff on top; no open end,
  no gap. A 10-segment navy band per wrist (2.5 cm off the axis, 4.5 cm long, hem folded 3 mm in, 100 % Forearm) hides it. Cuff linings off
  again, LOD0 14,982. Gates: sleeve poke 0, see-through sleeves worst 16 px (was 28), robe 0, jitter 0, regression PASS 252 on 114, floor ok,
  viewer 0 errors. No credits. Backup 2210. Lease released.
- 13:00 UTC User review r43: hands still out of the sleeves; full navy undersleeve to the elbow. Lease re-claimed.
- 13:55 UTC r45 INSTALLED (sha 4f382ac9030c): fitted navy undersleeve (8-segment tube wrist -> elbow -> 4 cm up the upper arm, Forearm /
  UpperArm weights, band as its cuff) + the bell's last 20 cm recentred on the forearm axis (Meshy's bell hung 4.4 cm in front of it, so
  the forearm left through its back wall). Gates: sleeve poke 0, see-through sleeves worst 13 px, robe 0, jitter 0; LOD0 15,101 (101 over
  15k). Regression PASS 252 on 114, floor ok, viewer 0 errors. Sheet review/undersleeve_r43_vs_r45.png. No credits. Backup 2210. Lease released.
- 2026-11-04: user approved ("igrid ok"), r45.
