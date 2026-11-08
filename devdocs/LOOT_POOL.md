# One random loot pool

Random loot (monster drops, random chest contents, random map treasure) rolls from one pool of every mounted world's
items: in MM9 an MM6–MM8 sword may drop, in MM7 an MM9 one. Artifacts and relics are the exception: each drops only in
its own world (below). The user chose this on 2026-11-08 in place of the earlier "Random loot from other worlds" setting (own world,
own artifacts, all worlds), which is gone; an old `[gameplay] loot_source` line is ignored. It is part of the MM9
balance plan ([BALANCE_PLAN.md](mm9_rework/BALANCE_PLAN.md) section 3.5).

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
- Tests: `tests/LootPoolTests.cpp`; MM9's mix in `tests/Mm9RudeDialogueTests.cpp`.

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
