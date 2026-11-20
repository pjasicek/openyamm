# MM9 balance prototypes (2026-11-05)

Read-only measurement scripts behind [BALANCE_PLAN.md](../BALANCE_PLAN.md). The checks that gate the generated MM9 tables are
`tools/mm9_import_discovery/mm9_balance_report.py` (it runs `fit_check.py`, `probe_input.py` and the engine probe). They change no game data and are
to be folded into `tools/mm9_import_discovery/mm9_balance_report.py` (plan section 8). Run from the repository root;
outputs go to `output/mm9_balance/` (create it first).

| Script | Measures |
| --- | --- |
| `cmp.py` | Ordinary items: average damage or armour by skill/slot and tier, MM6–MM8 against MM9 |
| `art.py` | Artifacts, relics and set pieces: base stats and effect score. Needs `output/mm9_balance/rare.txt`, the body of `applyRareItemBonus` without blank and brace lines: `sed -n '797,1453p' game/items/ItemEnchantRuntime.cpp \| grep -v '^\s*$\|^\s*{\|^\s*}\|break;' > output/mm9_balance/rare.txt` (line numbers as of 2026-11-05) |
| `mon.py` | Monster HP, AC, damage, XP, treasure and resistances by level band |
| `dps.py` | Monster damage per second under `monsterAttackHitsArmorClass`, recovery, ranged share, spell use and skill |
| `allmaps.py` | MM6–MM8 monster count and XP per map and per world (uses `inventory_mm9_rework.py`) |
| `density.py` | Floor area, packs, pack size and spacing per map; MM9 dungeons from the rebuilt BLVs in `output/mm9_rework/` |
| `spell_calc.py` | MM9 against MM6–MM8 spell damage by skill rank |
| `threat.py` | One MM9 monster in MM7 monsters of its level (HP × damage per second) and equal-threat pack sizes (2026-11-06) |
| `economy.py` | MM7 kill gold, items and XP by level band; MM9 kill XP, gold and drops by chapter at the planned density (2026-11-06) |
| `quest_xp.py` | MM9 quest XP from the original script IR, content level per award, party level per chapter with and without a cap (2026-11-06) |
| `quest_xp_audit.py` | Every original MM9 GiveExp, including include files: giver, routine, script, keys, quest note, alternatives merged; writes `output/mm9_balance/quest_xp_audit.tsv` |
| `quest_xp_proposal.py` | Superseded by `quest_xp_profile.py` and `fit_check.py`: the first per-award proposal with hand-set content levels |
| `quest_xp_profile.py` | Builds `tools/mm9_import_discovery/mm9_quest_xp_profile.yml` from the audit with the decided cap rule (BALANCE_PLAN.md 3.1) |
| `fit_check.py` | Level-based first model, each MM9 chapter against the matching MM7 stage; kept for the XP curve (party level per chapter). Its party is a stand-in, so its fight numbers are superseded by the balance probe. `--density`, `--quest`, `--profiles 1`, `--quest-profile 1` |
| `probe_input.py` | Writes the pack mixes and party levels for the engine balance probe (`tools/balance_probe_main.cpp`, target `openyamm_balance_probe`). `--density`, `--pack-scale` |
| `probe_compare.py` | Prints the probe's results, each MM9 chapter against its MM7 stage |
| `quest_xp_audit_doc.py` | Writes `QUEST_XP_AUDIT.md` from the audit table and the profile |
| `pack_room_check.py` | Whether the chapter 4–5 pack sizes fit the rebuilt rooms: free space around each pack (rays to the walls) and each map's capacity against the planned count |
