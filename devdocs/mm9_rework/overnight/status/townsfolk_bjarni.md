# Unique Bjarni Thorvaldssen — status

- Project `level_generation/creatures/mm9_bjarni_claude/`, lease `mm9:bjarni` (owner claude-townsfolk-bjarni), budget 60.
- Row: MONSTERS.txt 246 "Bjarni Thorvaldssen" (BJARNI.abc, skin BJARNI, NPCbase.scr, BaseName PeasantMale); stand-in today legacy 586.

## Log
- 23:07 UTC lease claimed; sources converted (BJARNI.abc = the 45-joint PeasantMale skeleton + 11 own clips). Credits 0.
- 23:20 UTC HD masters 00-04 accepted (Codex 2 runs; halo removed by clean_alpha.py). Smart Topology body_smart_v1 done (5 cr, backup 3430 before). Fit (spine span fix for the yoke's back panel), reduce 14,596 -> 7,791, MPFB hands, head split (cut 0.64, r 0.19, necklace beads in the body set), sleeve_tuck. Body UVs running; head turnaround in Codex. Credits 5.
- 23:40 UTC UVs (body atlas 59.9 %), body + head 4K retextures (10 + 10; backup 3425 -> 3405). Credits 25.
- 00:20 UTC face defects found in close-ups and fixed: Meshy eyeball cups through the lower lids (dropped by position), a flipped
  nostril triangle (fix_flips.py), a grey smudge in the moustache (moustache_fix.py); two loose chips (remove_specks.py).
  sleeve_paint_fix.py rejected (it took the cuffs' rust trim; no skin wedges were painted). Seated scene clips: floor_fix
  `--seat-like Sit` (new opt-in option) instead of per-key grounding (shoulder-skin jitter 6-11 mm/f2 -> 0 fails).
- 00:21 UTC installed `assets_source/worlds/mm9/models/mm9_bjarni.glb`; bound under the flock (row 246 -> 586 in
  mm9_npc_actor_rows.tsv, tables regenerated: 9246 `MM9 246 Bjarni Thorvaldssen`, actors.yml block `mm9_bjarni_claude`).
  `mm9_actor_models_build_every_binding` PASS (183 on 76 models). Floor audit: walk all-feet lift 2.6 (tol 2.5) -> walk smoothing
  0.08, reinstall pending after the full regression run.
- 00:55 UTC final: walk smoothing 0.08, eye lid rims softened (eye_rim_fix.py); reinstalled (sha256 e51870d1339e4c39...).
  Gates: arm/hand 0 cm except Fidget R 2.9 cm (MM9 hand over the mouth into the beard) and Applause 1.9/2.0 cm (hands meet);
  sleeve poke 0 mm except ArgumentShot1A R 28.5 mm on 2 back-of-hand vertices folded beside the cuff at a 70 deg wrist (outside
  the cloth; renders show no skin through the sleeve); jitter 0 fails; floor ok (walk -0.5..+2.2); winding 0; detached 0; flat
  0.0/0.1 %; bones: thigh slide 0.105-0.127 (MM9's own); texture body 59.9 % / spread 1.09 / fragments 0.1 %, head set 44.7 %.
  Regression actors --world mm9: passed 192, failed 1 (known out05); after the final reinstall
  `mm9_actor_models_build_every_binding` PASS (184 on 77 models). Viewer r4-20261102, check 18 switches 0 errors.
- Credits: **25 / 60** (ST 5, body 4K 10, head 4K 10; backup 3430 -> 3405). Codex: 3 runs.
- Map placement left to the orchestrator (README "Binding plan": DAT class BjarniThorvaldssen -> 9246). Props (Sturmford/Thronheim
  RUDEProps = decoration mm9_bjarnisitting; corpse props "Kira0" in Afterworld/Yorwick are bjarni.abc + bjarni.dtx) not changed.
- Lease released. Background: none. Chromes: none.
