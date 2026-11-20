# Townsfolk PeasantM1d (elf man) — status: installed and bound, 2026-11-01 ~22:30

Project `level_generation/creatures/mm9_peasantm1d_claude/` (README has route, rebuild, gates, deviations, binding plan).
Rows 22 Commoner (PeasantM1c) and 28 Prisoner (PeasantM1d); skeleton = PeasantM6/PeasantMale (45 joints, Annud's).

- Installed `assets_source/worlds/mm9/models/mm9_pm1d.glb` (sha256 c75b7898b02face4...), LOD0 7,995 tris; tiers `pm1d_c`, `pm1d_d`
  by region masks + ramps on body (tunic, shirt panel, breeches, hem trim) and head set (hair, collar).
- Descriptors `MM9 22 Commoner` / `MM9 28 Prisoner` (rows added to `mm9_npc_actor_rows.tsv`, tables regenerated, actors.yml bound under the flock).
  Map placements still use stand-ins 340/342: binding plan in the README (shared transcoder + map regeneration, not done).
- Clips: MM9 roles + Cower, Conv1, Conv4, Conv5 (the scripts' clips); Talk/Conv* hands rested with hand_rest.py.
- Gates: arm/hand 0 except Conv1 L 3.1 cm (hand at chin, MM9 gesture) and Conv5 L 1.8 cm; jitter 0 fails; floor OK; winding 0;
  bones 0; detached 0; flat 0; body atlas 56.4 % / spread 1.09 / fragments 0.1 %; head set 43.5 % / 1.5 %; viewer 0 errors;
  `mm9_actor_models_build_every_binding` PASS (168 on 69 models); full actors suite 192 pass, 1 known out05 fail.
- Meshy: 25 credits (Smart Topology 5, body 4K 10, head 4K 10). Codex: 3 runs (masters 1, 2, head).
- Viewer: http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm1d_claude/review/viewer/ (v7-20261101).
- Not checked: playback at speed, in game, LODs by eye, tier D clips beyond Standing.
- Lease released.
2026-11-02 ear-sweep check (owner ear-sweep-fix): the "pale grey triangle under the jaw" (both tiers) was a see-through hole,
not a lace: a 6-edge boundary loop (bow-tie of two missing triangles) in the neck skin under the right jaw, left by geo_fix.py's
sliver deletion. `scripts/neck_hole.py` fills it (fix_v1 -> fix_v2.blend, the new master; positions/faces only, HeadUV continued).
Clips identical, images identical. Installed sha 9e4828dd48e16b85, rollback work/installed_preear.glb. Viewer v8-20261102,
check 26 switches 0 failed. Sheet review/sheet_ear_before_after.png.
