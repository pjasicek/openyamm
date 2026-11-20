# Townsfolk PeasantF8 (elf woman) — status

- Project: `level_generation/creatures/mm9_peasantf8_claude/` (README is the record), lease `mm9:peasantf8`, owner claude-townsfolk-peasantf8.
- Rows: MONSTERS.txt 15 (Commoner, F8b, DAT CommonerElfFemaleA, 19 placed), 16 (Commoner, F8a, CommonerElfFemaleB, 12 placed), 21 (Prisoner, F8b, none placed).
- Phase: **done** (installed, bound, gates run, sheets read, README written).
- Credits: **35 / 60** (Smart Topology 5, body retexture 4K 10, head retextures 4K faces B and A 10 + 10; backup account).
- Installed: `assets_source/worlds/mm9/models/mm9_peasantf8.glb` (sha256 72983df1fdc6...), variants `pf8_b` (rows 15, 21), `pf8_a` (row 16).
- Binding: rows 15, 16, 21 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visuals 331/332/331), tables regenerated (ids 9015, 9016,
  9021), `actors.yml` block `mm9_peasantf8_claude` (`MM9 15 Commoner`, `MM9 16 Commoner`, `MM9 21 Prisoner`). Map placement left to the
  orchestrator (rebuilt maps still place 331/332).
- Clips: PeasantFemale library, the set the scripts play (stand1, Walk, run, Fidget4, Conv1-3, Wince1, Die1, Dead, cower); `scripts/pf_roles.py ALL=1`
  writes all 20 for F1/F5.
- Gates: arm/hand 0 frames > 1 cm; legs through skirt 0 in all clips; jitter 0 fails; floor ok x3; winding 0; flat 0.00; bones 0 stretching;
  texture body 65.9 % / head 59.0 %; detached 2 (the free legs inside the skirt, by design); collapse worst Hit armpit R 41, waist 36, neck 33-35.
  Regression: mm9 binding PASS (168 descriptors on 69 models, 0 failed), suite 192 passed, 1 known out05 failure.
- Viewer `r13-20261101`, check 0 errors. In-game spawn tour on bootcamp: `review/sheet_ingame.png`.
- No background processes, no Chrome left. Lease released 2026-11-01.
