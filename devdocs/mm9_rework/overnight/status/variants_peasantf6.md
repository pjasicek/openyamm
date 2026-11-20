# variants: PeasantF6 (rows 17 Town PeasantF6a, 19 Shopkeeper PeasantF6b; elf woman) — owner peasantf6-agent

Project `level_generation/creatures/mm9_peasantf6_claude/` (lease mm9:peasantf6, claimed 2026-11-02 13:00 UTC).

## State
- MM9 F6 vs F5: identical skeleton (all 73 bind matrices equal), body within 0.5-2 cm (legs a rigid 0.5 cm shift); the differences
  are the head (no coif: a bob of hair, a braid on Ponytail11, elf ears, bare neck) and the paint (long sleeves with cream chemise
  cuffs, F6a brown dress + laced dark vest, F6b orange dress + pendant). Sheets `references_hd/mm9_body_f5_vs_f6.png`,
  `references_hd/mm9_head_f5_vs_f6.png`.
- Decision: **variant route on PeasantF5** (frozen): F5's final geometry, rig, weights and clips; coif and brooches removed; new hair
  shell (MM9 F6's hair volume), braid and elf ears (numpy, `scripts/make_f6_geom.py`); human ears pressed; new UVs; body 4K retexture
  (F6a design) + head 4K retexture (F6a face) = 20 credits; tier B (F6b) by ramps + a Codex face repaint projected (0 credits).
- Placements: TownElfFemaleA 7 (row 17), ShopkeeperElfFemaleA 5 (row 19). Scripts: NPCbase, shopkeeper, retainer, Pledge, NPC50 (no
  animation params) -> F5's clip set.
- Now: geometry v1 done (clay `review/clay/f6v5_sheet.png`); next UVs + Codex masters.
- Codex: body masters (2 runs; aligned onto F5's masters, arms rotated 7-10 deg to F5's arm angle: `scripts/align_masters.py`,
  `scripts/arm_rotate.py`), head turnaround A, face repaint (A fixed: no lipstick; B: auburn ~45 y.o.) projected.
- Meshy: head 4K retexture A 10 (backup 2950 before), body 4K retexture 10 (2940 before) = **20 / 20, no further paid jobs**.
- Geometry v2 frozen (`work/asm_f6.npz`, UVs `work/uv.npz`, never re-run uv_pf.py). Linings: neck cap, arm-top caps, hand-stub caps,
  collar lining (`scripts/line_rims.py`); braid root blended to the head.
- 15:05 PC reboot: Meshy jobs had both finished and downloaded; lease intact; resumed. Coordinator lesson applied: Meshy's head normal
  map is no longer flattened over the face (project_face_pf6.py --normal dropped).
- Now: r5 build (not installed), face sheets, see-through gate running.
- 15:25 second kill (OOM, orchestrator): lease intact, no Meshy resubmission needed (both jobs SUCCEEDED earlier); my leftover
  see-through Blender (PID 38022, 0.75 GB) stopped and rerun capped; all heavy jobs now under systemd-run MemoryMax=12G, one Blender.
- r8 **installed** `assets_source/worlds/mm9/models/mm9_peasantf6.glb` (sha256 b6a12e5d...); bound `MM9 17 Town` (pf6_a), `MM9 19
  Shopkeeper` (pf6_b); rows 17/19 in mm9_npc_actor_rows.tsv (stand-ins 334/337), tables regenerated (216 rows);
  `mm9_actor_models_build_every_binding` PASS (216 descriptors on 93 models); floor audit ok; viewer check 22 switches 0 failed.
- Gates r7/r8 geometry: arm/hand 0 frames > 1 cm (hands), Cower R forearm 1.0 cm frame 0; jitter 0 fails; skin poke 0.0 mm; robe 0;
  winding 0; bones 0 stretching; texture body atlas 63.3 % / head 55.7 %. See-through gate (step 3) running.
- F5 unchanged: `work/f5_unchanged.txt`.
- r10 final: waist cap inside the skirt (see-through Death torso 1168 -> 57 px, sleeve L 2201 -> 24, collar 731 -> 9), B jaw-hair block
  removed. Reinstalled sha256 b5a735ff...; binding regression PASS (216/93); floor ok; viewer 22/0. F5 sha256 cc15d105... unchanged.
- Done; lease released. Details: project README.
- r13 hair reshape (coordinator review): close cap pulled back (thin, rim tucked under, no nape gap), ears clear and skin-painted, forehead
  arc removed, nostrils softer; 0 credits. Installed sha256 2374f7aa...; binding PASS (216/93); floor ok; viewer 22/0; see-through head 13,
  collar 10 px. F5 unchanged (cc15d105...). Lease released.
- r15 (coordinator re-review): hair fitted to MM9 F6's outline (rounded bob, edge curled under, no nape gap/arc), ears 7.7 cm at the temple
  in front of the hair, lip-slit specks fixed with a mouth backing plate, chin V lifted; 0 credits. Installed sha256 1297f605...; binding PASS
  (217/94); floor ok; viewer 22/0; see-through head 2, collar 10 px. F5 unchanged. Lease released.
- r17 (user "double nose"): painted nose replaced by plain skin over the geometry's nose + soft nostrils on the real openings, lip slit
  re-UV'd (gold line gone), lip specks and chin V cleaned; 0 credits. Installed sha256 cd121970...; binding PASS (229/100); floor ok;
  viewer 22/0. F5 unchanged. Lease released.
