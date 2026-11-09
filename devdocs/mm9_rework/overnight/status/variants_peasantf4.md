# variants: PeasantF4 (rows 30 Commoner F4a, 37 Commoner F4a, 42 Prisoner F4b) — owner peasantf4-agent

Project `level_generation/creatures/mm9_peasantf4_claude/` (lease mm9:peasantf4, claimed 2026-11-02 14:26 UTC).

## State
- MM9 F4 vs F1 (`mm9_meshcmp.py`): same skeleton (73 nodes, identical binds); head p90 2.8 / max 5.7 cm. Looked at side by side
  (`review/mm9/bodies_f1_f3_f4.png`, `heads_f1_f4.png`, `arms_f1_f4.png`, `review/sections.png`): F4 differs from F1 by
  (1) a rounder, lower hood (top 3.8 cm lower) that falls to the shoulders and upper back (MM9 weights: Head, the front lappets
  on xpony/xpony_a, the back tip on Ponytail11); (2) LONG BELL SLEEVES (sleeve radius 3.8 cm at the elbow widening to ~5.5 cm,
  open end ~3 cm above the wrist) where F1 has bare forearms; (3) the paint: A olive-green long-sleeved dress with an embroidered
  keyhole placket, cream apron, dark skirt, dark-haired woman ~45; B brown dress, dirty torn apron, older thin woman.
- Plan: F1's frozen mesh, rig, weights and clips; new outer hood over F1's hood (kept, shrunk inside as the skull), cape lining;
  sleeve tubes over the MPFB arms with a bell and a lining; new UVs; body 4K + head 4K retexture (20 credits); faces by Codex
  repaint by landmarks; tier B by ramps + its own head colour.
- F1 hashes taken before any work: `work/f1_sha_before.txt`, `work/f1_actors_block_before.yml`.
- Codex HD masters (body 4 + head 4, skin A) running.
- 16:0x Geometry v2 frozen (`scripts/add_parts_pf4.py` -> `work/asm_frozen.npz`): new hood over F1's (old hood kept as the hidden skull,
  its crown triangles deleted), sleeve tubes with bells + linings, arm under the tight sleeve deleted, F1 skirt lining decimated 45 %.
  LOD0 14,926. Weights: F1's exact weights on every F1 vertex (`merge_weights_pf4.py`), MM9 F4's hood weights on the hood.
  Geometry gate (half.glb): sleeve <= 0.8 cm beyond rest, 0 frames > 1 cm; hood 0.1-2.9 cm (head turns, as F3's veil).
- UVs `uv_pf4.py` (never re-run): body atlas 69.7 %, head 61.5 %. Codex masters selected (body 4 + head 4).
- Meshy: body 4K retexture (backup 2845 before) and head 4K retexture (2835 before) submitted: 20 credits.
- Meshy both SUCCEEDED and downloaded (20 credits; backup 2815 seen after). Paint: body raw composed (green dress, embroidered placket
  and arm bands, cream apron, dark skirt); head raw sym + head_fix + hood tone; old hood shards pushed under the new hood
  (`fix_shards_pf4.py`); chin sculpt from F3 pass 3 (`chin_pf4.py`). Tiers: R dress (MM9 A olive / B rust), G apron (B dirty beige).
- r1 built (not installed). Gates r1: arm/hand 0 frames > 1 cm (hand <= 0.2 cm; Cower forearm 2.4 cm = the bell on the bust),
  jitter 0, robe 0, sleeve poke 0 mm, bone length 0, flat 0.00/0.01, winding 0, detached = the 2 legs (as F1).
  Hood/sleeve gate after easing the cape onto the bodice: hood <= 0.9 cm, 0 frames > 1 cm; arm under the tube <= 0.8 cm beyond rest.
- Codex face repaint (both tiers) running (API reconnects after the usage-limit reset).
- 17:40 r6 (not installed): hood lining relined after the paint (`reline_pf4.py`: 4 rings where the hood stands off the head, dropped where
  it hugs the face; LOD0 14,979); F1's old hood follows the new hood's weights (no lappet / crown poke); old hood painted shaded hood colour.
  See-through r4 (Standing/Hit/Talk/Walking): head 36 px (was 451), collar 11, sleeves 13/22, torso 99 (Hit from behind).
  Codex face repaint: first run stuck in API reconnects (killed, literal PID), second and third runs reconnecting; fallback ready
  (`f1_face_transfer_pf4.py`: F1's approved face carried over by shared asm triangles) if Codex stays down.
- 17:55 r6 installed as an interim (sha d13aaaed..., Meshy face paint, no Codex face yet) so the binding can be tested: `MM9 30 Commoner`,
  `MM9 37 Commoner` (pf4_a), `MM9 42 Prisoner` (pf4_b) bound under the flock, rows in mm9_npc_actor_rows.tsv (fallback visuals
  350 / 377 / 384), tables regenerated (229 rows), `mm9_actor_models_build_every_binding` PASS (229 descriptors on 100 models, 0 failed),
  floor audit rows 30/37/42 ok. Gates r6: arm/hand 0 frames > 1 cm (hand <= 0.2 cm; Cower forearm 2.4 cm = bell on the bust), jitter 0,
  robe 0, short-sleeve poke 0 mm, hood <= 0.9 cm / tube <= 0.8 cm (0 frames > 1 cm), flat 0.00/0.01, bone length 0, winding 0.
- 19:20 FINAL r15 installed (sha 85f3c2a3...a64f = export). Faces: Codex per-woman runs succeeded (A ~45 dark hair, B ~60 grey-streaked),
  lids and nose from F1's approved geometry-fitted paint (luminance detail), under-chin and skin matched, gutters re-padded. Old-hood
  lappets dropped, cape lining 5 rings; LOD0 14,994. Gates r15: arm/hand 0 frames > 1 cm (Cower forearm 2.4 cm: bell on the bust), jitter 0,
  robe 0, sleeve poke 0, hood <= 0.9 cm / tube <= 0.8 cm (0 frames > 1 cm), flat 0.00/0.01, bone length 0, detached = 2 legs, winding 0,
  texture body 69.6 % / head 61.3 %. Binding PASS (229 on 100 models), floor rows 30/37/42 ok, viewer r15 22 switches 0 errors.
  F1: 1,050 files + installed GLBs + actors block identical to the start (work/f1_sha_before.txt vs _after.txt). Meshy 20 credits.
  Sheets: review/sheet_face_r15.png, review/sheet_face2_r15.png, review/sheet_mm9_vs_ours_r15.png. See-through r15 running.
- See-through r15 (all clips): head 146/156 px (Death fall: slivers at the face/hood edge), torso 1559, sleeve L 2000, collar 907 (corpse from
  the feet up the skirt, F1's hollow dress), sleeve R 23, boots 0. README complete. Lease released.
- 2026-11-02 review pass (coordinator: faces worried/pale/staring, F1 sleeves and laced bust, clean cream apron); lease re-claimed.
  r16-r31: plain sleeves and bodice (lace bands and bust lacing repainted, lacing column smoothed, its AO/normal relief flattened, upper
  puff squeezed to the arm tube), apron graded to dirty grey linen with grime (B: torn dark hem, teal underskirt darkened); Codex v2
  warm faces (tan, rosy, relaxed, A closed smile) projected in texture space, lids painted on the eyeballs and rotated (Wyrde route),
  upper-lid and nose-underside normals relaxed (the zigzag lash line and the dark nostril blob from the front), skin tanned, rosy cheeks.
  No Meshy credits spent in this pass (total 20). Gates/see-through/install running on r31.
- FINAL r31 installed (sha 9c054aca...24a5 = export). Gates r31 = r15 (arm/hand 0 frames > 1 cm, Cower forearm 2.4 cm; jitter 0; robe 0;
  sleeve poke 0; hood/tube <= 0.8 cm; detached = 2 legs; flat 0.00/0.01; bone 0; winding 0; texture 69.6 % / 61.3 %; see-through as r15).
  Binding PASS (240 descriptors on 105 models), floor 30/37/42 ok, viewer 22 switches 0 failed. F1 re-proved unchanged (1,050 files +
  actors block). Sheets: review/sheet_face_r31.png, sheet_face2_r31.png, sheet_mm9_vs_ours_r31.png, face_before_after_r31.png. Lease released.
- 2026-11-04 job 8 (user review: forearm sleeve "transparent parts / holes", hem spikes, chest holes; `review/user_20261104/6-8.png`), lease
  re-claimed by f4-sleeves-20261104. Causes found (`review/diag/`, back faces magenta): (1) the sleeve tube's upper five rings (inside the
  short sleeve to the elbow) were built in the upper-arm frame, whose ring order runs the other way round: 216 of 576 outer tube faces wound
  inward (culled: the "transparent" patches) and the elbow band twisted through the tube (the olive jagged fragments);
  (2) F1's bodice has open eyelet holes where its lacing sat (7 loops, 4-14 edges) and two beside the belt: the hollow dress shows background;
  (3) F1's sawtooth peplum (tips 2.5 cm). Fixes: `sleeve_rings_pf4.py` (positions permuted round the ring, asm backup
  `work/asm_frozen_prej8.npz`; 0 faces inward), `bodice_fix_pf4.py` (holes filled, lacing chevrons dropped, spike faces cut, side hem
  straightened), `sleeve_paint_pf4.py` (upper tube bands re-painted from band 6 in tone/normal/ORM/mask/classes; r31 maps in `work/j8_*`).
- FINAL r40 installed 2026-11-04 (sha 833b8a14...2c49 = export; r31 rollback `work/j8_rollback_r31_mm9_peasantf4.glb`). Also fixed on
  the way: the olive blot on the wrist skin inside the bell (`region_paint_pf4.py wrist`), the side hem's sawtooth (notches down to the
  tips' line, one-face tips dropped) and the skirt/lining sawtooth top under it (down to z 0.098 at the sides). LOD0 14,948.
  Gates r40 vs r31: tube faces inward 216 -> 0; see-through sleeve "inside" px per living clip 620-990 -> 0-148, sleeve holes 8-28 -> 0-2,
  torso holes 61-108 -> 36-77 (F1's back slit, 0-6 px at 20 deg), Death/Dead maxima unchanged (torso 1596, sleeve L 2003: corpse from the
  feet); sleeve poke 0 mm; tube <= 1.0 cm (Cower), 0 frames > 1 cm; arm/hand identical; jitter 0; robe 0; collapse Cower elbows 14/8 ->
  20/13; flat/bone/winding/detached unchanged. Head LOD0 geometry and all head maps byte-identical to r31. Binding regression PASS
  (250 descriptors on 112 models, 0 failed); viewer r40 check 22 switches, 0 failed. No Meshy credits. F1 untouched (installed sha
  e07f87e9 as recorded, no F1 file newer than f1_sha_after.txt). Sheets: review/arms/sheet_arms_r31_vs_r40_{a,b}{1,2}.png,
  review/arms/sheet_r40_walking.png, review/sheet_mm9_vs_ours_r40.png, review/diag/. Lease released.
- 2026-11-04 follow-up (user's back view 13_back_elbows_r40.png; lease re-claimed): the shot shows r31's artefacts (stale browser cache of
  manifest.json + GLB; r31 GLB rendered from the same angle reproduces them, r40 has none: posed back-face renders review/diag_posed/,
  viewer back views 5 clips both tiers review/back/). review.js now fetches the manifest no-store. r41: tube repaint v2 (arc length +
  angle, mirrored at ring 6: no mid-forearm step) + gutter re-pad; geometry byte-identical to r40, so all gates hold. Installed r41
  (sha bccd88d7...), binding PASS 250 on 112, viewer 22/0. Sheet review/back/sheet_back_before_after_r41.png. Lease released.
- 2026-11-04: user approved ("ok peasantf4 is good now"), r41.
