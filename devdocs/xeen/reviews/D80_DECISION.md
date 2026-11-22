> Orchestrator note (2026-11-21): the Newcastle deed costs 12,000 gold (QUESTS, `m8.yml`), not 50,000 as quoted below (A2's check).

# Xeen's loot and shops after merge point 33: decisions (D-80)

## Q1: the setting "MM9 loot in MM6-MM8" and Xeen

**DECISION:** Xeen stays fixed to MM6–MM8 items whatever the setting says. The setting applies only to worlds whose own pool is the merged base (`lootPoolForWorld(world) == "engine"`), which today means MM6, MM7 and MM8. A world that borrows the base through its world.yml `dependencies` (Xeen, and any later world built the same way) always rolls its declared pools: `xeen` and `engine`. Shops are unchanged, because the setting never touched shops: MM6–MM8 shops and Xeen's shops always keep to their pools.

**WHY:**
- **The setting does not name Xeen.** Its tooltip says "Drops and chests in Enroth, Antagarich and Jadame can hold Might and Magic IX's weapons, armour and jewellery." Xeen is neither of those continents, and the setting dates from 2026-11-13, before Xeen existed. Bringing it into Xeen would stretch it past what its text and its purpose say. Its purpose (LOOT_POOL.md) is to keep MM6–MM8 playing as they did before MM9 unless the player opts in.
- **U-1 is a world design decision, and the user made it.** "No new equipment items … loot uses MM6–MM8 items." D-44 also keeps every Xeen binding off `worlds/mm9/...`. The user decides how a world is designed. A player's preference that is labelled for other worlds should not override that.
- **Balance and presentation.** A2's progression model and the item tiers that A2 and S worked out are calibrated on MM6–MM8 equipment. MM9 bases carry MM9's import balance and their own art style. Xeen presents itself as MM4+MM5 on the MM6–MM8 base, marked Experimental (U-3). An Experimental world should have one loot identity to test, not two.
- **It is symmetric.** Since merge point 33, MM9 no longer rolls Xeen's equipment.
- **No translation work.** The tooltip already names the three continents, so the seven translated catalogues need no change.

**WHO ACTS:**
- **A1:**
  - In `ItemGenerator::generateRandomInventoryItem`, gate the setting on the world's own pool being `engine`, not on `engine` appearing anywhere in its pools. Fix the comment there and in `ItemTable.h`.
  - Rewrite the Xeen bullet in `devdocs/LOOT_POOL.md`: "Xeen never rolls MM9 equipment; the setting is MM6–MM8's."
  - Extend the unit test "a world that depends on MM6-MM8 ...": with the setting on, Xeen still rolls no `mm9` item and MM7 does.
- **A1, verify first. This is my reading of the code, I did not run it, and it affects both questions:** in `HouseServiceRuntime.cpp`, `generateStockItems` builds its candidates without `shopPoolAllows`. It does filter on `availableInWorld`, `NoShop`, family and treasure weight. When `generateRandomInventoryItem` refuses a candidate from outside the pool, the slot falls back to `makeInventoryItem(itemId, …)`, which gives a plain copy of that item.
  - This is very likely how Xeen's shops gave "unenchanted base items only" before merge point 33.
  - It may still put plain MM9 equipment into Xeen's and MM6–MM8's shops. MM9's 155 equipment rows have neither `NoShop` nor `World:mm9`, and they have random weights. That would contradict both U-1 and LOOT_POOL's "MM6–MM8 shops already sell only the base's equipment".
  - If confirmed, the fix belongs in shared code: filter the candidates with `ItemGenerator::shopPoolAllows(entry, itemTable.lootPoolsForWorld(houseEntry.worldId))`.
  - Add a test of the house-stock path: stock for Xeen and MM7 holds no `mm9`-package equipment, and stock for MM9 holds no `engine` or `xeen` equipment.
- **G:** one line on the guide's shop page or FAQ: "Xeen's shops and treasure are MM6–MM8 items; the MM9 loot setting does not apply to Xeen."
- A2, A4: nothing.

**REVERSIBLE:** Yes, cheaply. It is one condition and one test case. No save data is involved: the setting is read live and items already found stay. If the user later wants MM9 items in Xeen, the right form is an explicit choice per world (a world.yml flag or a reworded setting), not this setting.

## Q2: Xeen's shops now stock enchanted MM6–MM8 equipment

**DECISION:** Enchanted stock is intended. The plain stock before merge point 33 was a bug: items refused by the pool fell back to plain copies. A4's stock levels stay as they are. A2 runs one check and does not change the model.

**WHY:**
- **Xeen's shops are meant to work like MM6–MM8's.** TOWNS_FORMAT gives each shop "an engine `house_rules` row of that quality". On MM6–MM8 maps, that row's quality is the treasure level `generateRandomInventoryItem(Shop)` rolls at, enchantments included, just as on MM6–MM8 maps.
- **A4's levels already climb town by town:**
  - quality 1 in Vertigo and 2 in Rivercity;
  - 3 in Castleview and the middle towns;
  - 4 in Sandcaster, Crossroads, Lakeside, Bosco's Forge and The Grave Market;
  - 5 only at Arm and Hammer (Shangri-La), The Queen's Forge (opens at `m26.stage4`) and The Forge of the Gods (Olympus).

  This matches MM4/MM5, where the late towns sold the "+" and elemental gear. All of them are rows that exist (A4 item 70 fixed the missing ones).
- **Low-level shops barely change.** MM7's enchantment rates at treasure levels 1–2 are low, so Vertigo and Rivercity stay mostly plain. Enchantment matters from quality 3 up, and that is where MM6–MM8 have it too.
- **The campaign was already calibrated on enchanted shops.** COMBAT_AND_PROGRESSION and the Act budgets take MM7's progression as the baseline, and MM7's shops sell enchanted stock. Plain stock was the exception. The fix brings Xeen into line with its model rather than away from it.
- **Prices take care of themselves.** Enchanted items cost their enchanted value, so the change mostly adds a gold sink. It does not hand out free power.

**WHO ACTS:**
- **A2:** a one-off check of about an hour, written up in the A2 log. `balance.py` does not model shop stock and should not start to.
  - For each Act, list the highest shop quality open at that Act (respecting `opens:` gates) against the party level the Act expects. Compare it with the MM6–MM8 town of the same level: the best shop in reach should not be above what MM7 offers at that party level.
  - Compare the price of one top-row item in each Act's best shop with the Act's earned gold. This matters most in Act II, next to the Newcastle deed (50,000 gold, about 60 % of Act II's gold).
  - Raise a decider question only if a quality-5 shop opens before the Act its party level supports, or if quality-4 shops in the early Darkside towns undercut the D3/D4 fights.
- **A4:** nothing unless A2 raises something. The quality numbers stay authoritative.
- **A1:** only the stock-candidate check under Q1.
- **G:** on the guide's shop page, say the stock is enchanted and rises from town to town (Vertigo plain, the late towns with magic gear), and remove any wording about plain stock.

**REVERSIBLE:** Yes. Shop stock is generated when a shop is visited and refreshed on its timer, so a change to a quality number reaches every save at the next refresh. Items already bought stay.

## SUMMARY ROW

| D-80 | 2026-11-21 | Xeen's loot after merge point 33 | (1) Xeen ignores "MM9 loot in MM6-MM8": the setting applies only to worlds whose own pool is `engine`; Xeen always rolls xeen+engine (U-1). (2) Enchanted shop stock is intended (MM6–MM8 behaviour); A4's qualities stand; A2 checks the best shop and its prices per Act once. | A1 (setting gate, LOOT_POOL.md, test; verify the stock candidates' pool filter), A2 (check), G (shop page) |
