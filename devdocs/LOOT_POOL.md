# One random loot pool

Random loot (monster drops, random chest contents, random map treasure) rolls from one pool of every mounted world's
items, with one default exception: MM6–MM8 maps roll no MM9 equipment unless the Gameplay setting "MM9 loot in
MM6-MM8" is on (below). So in MM9 an MM6–MM8 sword may drop; in MM7 an MM9 one only with that setting. Artifacts and
relics drop only in their own world (below). The user chose one pool on 2026-11-08 in place of the earlier "Random loot
from other worlds" setting (own world, own artifacts, all worlds), which is gone; an old `[gameplay] loot_source` line
is ignored. It is part of the MM9 balance plan ([BALANCE_PLAN.md](mm9_rework/BALANCE_PLAN.md) section 3.5).

- **Shops** keep their world's own equipment (`ItemGenerationMode::Shop`, `ItemGenerator::shopPoolAllows`): weapons,
  armour, jewellery, artifacts and relics of the world's own package pool (`package_id`; MM6–MM8's merged base is
  `engine`; `ItemTable::lootPoolForWorld`), everything else from anywhere. Authored stock is untouched.
- **Artifacts and relics drop only in their own world** (user, 2026-11-08): each carries its world's `World:<id>`
  content flag (`ItemDefinition::availableInWorld`, which random loot and shops check), so MM6's relics roll only in
  MM6, MM7's only in MM7, MM8's only in MM8 and MM9's only in MM9. The engine's merged table has them by id range
  (MM8 500–537, MM7 1302–1338, MM6 2020–2049); `import_mm9_items.py` flags MM9's. A world with `chestArtifactsOnly`
  (MM9) still rolls none at level 6, items with `NoRandom` never roll, and a found artifact does not roll again. The
  unique "Special" items (Mace of the Sun, Clanker's Amulet and the like) are not artifacts and stay in the pool.
- **Spellbooks** are world-flagged the same way: every world has its own book of each spell (MM6, MM7 and MM8 in the
  merged table, MM9's from `tools/mm9_import_discovery/mm9_spellbooks.py`), so a book drops only in its world.
- **Setting: "MM9 loot in MM6-MM8"** (user, 2026-11-13; Settings → Gameplay → Loot, `[gameplay]
  mm9_loot_in_older_worlds`, off by default; it changes at any time, existing saves included). Off, random loot on
  maps of the merged base's pool (`engine`: MM6–MM8) keeps to the base's equipment as their shops do
  (`shopPoolAllows`), so MM6–MM8 play as before MM9; MM9's maps always roll every world's items, a mix of MM6–MM9.
  On, MM6–MM8 maps roll every world's too. Shops need nothing more: MM6–MM8 shops already sell only the base's
  equipment, and MM9's books are world-flagged. The party carries it (`Party::mm9LootInOlderWorlds`, set from the
  settings in `GameApplication::bindPartyDependencies` and `applyCurrentSettingsToActiveRuntime`). Items already
  found stay.
- **The per-game "Loot from other worlds" is retired** (user, 2026-11-13). The new-game Rules panel offered it from
  2026-11-09 (`RulesetOptions::otherWorldsLoot`, fixed for the adventure; off, every world kept to its own pool, MM9
  too). The setting above replaced it; saves 172 to 177 hold its byte, which loading skips
  (`SaveVersionOtherWorldsLootRetired` = 178), and the scenario key `other_worlds_loot` is gone.
- Tests: `tests/LootPoolTests.cpp`; MM9's mix in `tests/Mm9RudeDialogueTests.cpp`; the retired choice's saves in `tests/RulesetTests.cpp`.

## World random-treasure weights

A world weights its own items for random treasure with a `random_items` table contribution, rows in the engine's
`random_items.txt` format (item id, picture, weights for treasure levels 1–6), composed after the engine rows. The ids
must lie in the world's item id range and may not repeat another package's rows:

```yaml
tableContributions:
  - table: random_items
    idDomain: items
    mode: append
    path: data_tables/random_items.txt
```

Without it a world's items carry no weights and never roll as random loot. Items with the `NoRandom` content flag never
roll, whatever their weights.

All weights compete in the one pool, so a world's item should weigh what an MM6–MM8 item of its family and tier
weighs; MM9's take those weights at import (`mm9_item_balance.EngineReference.weights`). With MM9 mounted, MM9's items
are about a fifth to a third of the equipment that drops (more at low levels, where MM9 has an item of every family),
and an untyped drop is equipment a little more often than in MM6–MM8 alone (68–81% against 58–78%: MM9 brings
equipment but no consumables). The balance report's "Random loot pool" section measures both.
