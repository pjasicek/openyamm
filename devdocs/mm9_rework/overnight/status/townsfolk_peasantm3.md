# Townsfolk PeasantM3 (human man) — status

- Project `level_generation/creatures/mm9_peasantm3_claude/`, lease `mm9:peasantm3` (owner peasantm3-agent), budget 50 credits.
- Rows naming PEASANTM3.abc: 45 Town (Peasant Human1 MaleB A, PEASANTM3B, DAT `TownHumanMaleA`, 4 placed) and 52 Town
  (Peasant Human2 MaleB A, PEASANTM3A, DAT `TownHuman2MaleA`, 12 placed). Two different men (A blond beard, B dark goatee);
  tunic recoloured (A red velvet, B brown knit + jewelled chain), breeches and boots the same.
- Mesh comparison (meshcmp.py): different from every built male body (torso p90 3.9-5.7 cm, arms 3.0-20 cm); head close to
  PeasantM7 (p90 0.8 cm). New body on the PeasantMale route.
- Scripts on the 16 objects: none plays a clip (NPC183/186/195, Pledge, retainer, HucksterMod, BoatJudge, shopkeeper) except
  NPCbase -> BaseRun `LoopAnim Cower`; no marker animations.

## Log
- 11:29 UTC lease claimed (backup 3050). Sources converted, MM9 reference renders, Codex master 00 running (skin A design).
- ~12:45 UTC master 00 accepted; Smart Topology body_smart_v1 done (5 cr; backup 3050 before). Fit (Head joint move pinned to
  1.6 cm: the front measure put it at the back of the skull), reduce 14,759 -> 7,926, MPFB hands (0.199/0.193 m), head split,
  eye cups filled and dropped. Masters 01-04 accepted. UV pass running; head turnaround A running. Credits 5.
- ~13:50 UTC paints: body 4K (10 cr), head A 4K (10), head B 4K (10, Codex head turnaround B on A's silhouette). Credits 35
  (backup 3050 -> 2985 seen before the last job; other agents spend in parallel). No further Meshy planned.
- Fixes: face rigid on the Head (face_rigid_pm3.py), neck/collar/bead-line repaint of both heads (fix_neck_pm3.py), B hair rim
  (fringe_fix.py RIM_K 2.4), hands one skin tone, finger_pose.py (two-joint mitten, unsigned flexion), AttackMelee hattack1
  (hattack2's elbow went 5-6 cm into the tunic), linings at waist and boots (linings_pm3.sh), LOD3 lining drop.
- Installed assets_source/worlds/mm9/models/mm9_peasantm3.glb; bound under the flock: rows 45 -> 361, 52 -> 370 in
  mm9_npc_actor_rows.tsv, tables regenerated (208 rows), `MM9 45 Town` (pm3_b), `MM9 52 Town` (pm3_a). Binding regression PASS
  (208 descriptors / 92 models). Floor ok both. See-through gate r1 (lined) running; sheets next.
- ~14:40 UTC see-through r0 (unlined) -> linings (waist, boots) r1 -> own-paint inner twin of the tunic shell (twin_shell.py) r2;
  breeches region (dark brown as MM9), nape strip tone per tier, AttackMelee = hattack1. Final installed (sha256 f0e56cbb5e32...),
  LOD0 10,104. Gates: arm/hand 0 frames > 1 cm every clip, jitter 0, poke rest 0 (bent-wrist flags checked with markers),
  floor ok, winding 0, detached 0, flat 0. Full actors regression and see-through r2 running. README written.
- ~15:30 UTC DONE. Skirt twin (see-through r3: torso 9 px, collar 1, sleeves 0-1, boots 0, trousers 1-3, head 4), breeches
  region by UV island + tone (dark brown as MM9 on both tiers). Final install sha256 006f55c95d88... (LOD0 10,650).
  Binding regression PASS (214 descriptors / 92 models); full actors suite passed 192, failed 1 (known out05). Floor ok both;
  viewer r14 check 20 switches 0 failed. Credits 35 / 50 (no retries). README is the record. Lease released.
  Map placement switch (361 -> 9045, 370 -> 9052) left to the orchestrator.
- Face pass r2 (orchestrator review of tier A; 0 credits; resumed after the reboot and the OOM kill, memory-capped jobs):
  loose 40-vertex lip piece deleted, mouth openings capped in place with one-texel fans (no lip/pocket vertex moved), pocket
  walls painted as a lip shadow; A's eyes opened/brows lifted and lightened in paint; beard-to-neck 3D gradient, darker neck,
  smooth collar line over the jagged seam; ears repainted skin on both tiers (they were hair-coloured lumps). Installed sha256
  d77da6883f22...; binding PASS (216 / 93), floor ok, viewer 0 failed. Sheet review/sheet_faces_r2.png. README "Face pass r2".
  Lease released.
- Head repaint r3 (tier A, orchestrator rule after two patch passes): Codex head masters from viewer renders of the current head,
  Meshy 4K head retexture head_a_retexture_r3 (10 cr, backup 2835 before; total 45/50), paint fixes on the geometry (nose
  underside/rims, lids, recess walls, ears), mouth opening closed in positions (PeasantM2d route; lips' front untouched; B's
  mouth closes too). Installed sha256 09b78ef27b11...; binding PASS (216/93); floor ok; viewer 0 failed. Sheet
  review/sheet_faces_r3.png. Remaining: narrow eye slits in the mesh (both tiers) read slightly intent close up. Lease released.
- Lip fix r4 (user note "part of lip missing?", 0 credits): cause = r3's mouth close misclassified half the lower lip as pocket;
  redone from mouth_v7 with the lip front at the same height, interior brought to a 1.5 mm groove (no rim moves): both lip
  halves back, closed line; paint: beard under the lip, nostrils lifted, under-eye facets toned. Installed sha256
  187426f182f8...; binding PASS (230/101); floor ok; viewer 0 failed. Sheet review/sheet_faces_r4.png. Lease released.
- r5 (orchestrator: geometry first, then fresh paints; cap 70): mouth geometry finalised (lip_edge.py -> mouth_v14: one smooth
  symmetric closed line, clay-checked), Codex head masters A and B from the current head, Meshy 4K head retextures A and B
  (20 cr; backup 2560 / 2550 before; total 65/70), post-paint fixes re-applied, no geometry moved after the paint. Installed
  sha256 9a8426a489e8...; binding PASS (230/101); floor ok; viewer 0 failed. Sheet review/sheet_faces_r5.png. Lease released.
- r6 neck/collar (user note "some artifacts here?", 0 credits): head-set chest apron under the body collar (z-fight) painted as a
  gold remap -> tucked under the collar to a tube just inside its rim (neck_tuck.py -> work/neck_v1.blend), throat in the
  collar's V painted neck skin, flaps gone. See-through collar 2 px; arm/hand 0; installed sha256 9b98c069e4ea...; binding PASS
  (244/107); floor ok; viewer 0 failed. Sheet review/sheet_neck_r6.png. Lease released.
- r7 throat/neckline (0 credits): head edges snapped onto a smooth round neckline curve (neck_line.py -> work/neck_v2.blend),
  throat one skin tone, below the curve body-collar gold, normal map flattened evenly with padded gutters. Trim of the apron
  tried and dropped (opened the throat). Remaining: plain streaky gold under the neckline instead of brocade. See-through collar
  6 px; installed sha256 7bff04c93774...; binding PASS (246/109); floor ok; viewer 0 failed. Sheet review/sheet_neck_r7.png.
  Lease released.
- r8 collar faces (0 credits): the head faces below the neckline curve moved to the body material (head_to_body.py MODE=panel):
  a closed velvet shirt front mapped affinely into a chest tunic island (nearest-point brocade transfer tried, stretched).
  See-through all clips collar 6 px; installed sha256 52fcf7133249...; binding PASS (246/109); floor ok; viewer 0 failed.
  Sheet review/sheet_neck_r8.png. Lease released.
