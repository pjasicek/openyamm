# Analysis harness

Throwaway scripts from the 2026-10-22 MAW analysis, kept so the golden values in `../data/*.csv` and the numbers in
the spec documents can be regenerated when MAW changes. They are not part of the build and not maintained code.

- Lua scripts load MAW's own source files (commit `ef23ee17`; `mawmon/lua/harness.lua` follows `8967ae88`) with small shims for LuaJIT 5.1 and MMExtension
  globals. They were run with a plain Lua 5.4 interpreter built from `build/_deps/lua-src/src` (`make linux-noreadline`).
- Python scripts extract LOD contents, diff tables and assemble the YAML drafts.
- Some scripts still contain absolute paths from the analysis session (`/tmp/claude-1000/.../scratchpad/...`). Replace
  them with a local working folder before running.

| Folder | Produced |
|---|---|
| `maw_combat_spec/` | `COMBAT_SPEC.md` worked examples |
| `mawmon/` | `BALANCE_MODEL.md`, `MONSTER_TABLE_DIFF.md`, `data/balance_golden.csv`, map-level and difficulty drafts |
| `randoms/` | `RANDOMS.md`, `data/rarity_golden.csv` |
| `crafting/` | `CRAFTING.md` tables, `CRAFTING_BENCH_DESIGN.md` mockups |
| `lua_spells/`, `lua_classes/`, `lua_alchemy/`, `spells/` | `CLASSES_SPELLS_SPEC.md` and its data drafts |
| `itemsdata/` | `ITEMS_DATA.md` and the item data drafts |
| `maw_maps/` | `MAPS_CONTENT.md` map diffs |
| `tr/` | `TRAINERS_SKILLS.md` table diffs |
