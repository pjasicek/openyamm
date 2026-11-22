# D-90: finds, touch sites, death lines, entrance texts, quest-item bits (2026-11-22, fourth orchestrator's decider)

I checked how MM6–MM8 handle this in `assets_dev/worlds/mm6|mm7|mm8/events/maps/` and in the engine code, and three things decide the answers:

- **Finds never open a window in MM6–MM8.** A find puts the item straight into the packs (`AddValue(InventoryItem(id))`), sets its quest bit, often swaps the sprite (MM6's Memory Crystal Delta, the Sacred Chalice cabinet, the Oracle crystal), and at most shows a status line. Next to these finds the maps call `evt.StatusText` 70 times and `evt.SimpleMessage` none.
- **The entrance window already has a place for a flavour line.** The engine's `trans.txt` holds MM6–MM8's own entrance texts ("A burial mound. Though obviously centuries old…"), and `EventDialogContent.cpp:1298` shows such a text in place of "Do you wish to enter X?". The table is read from the engine only (`GameDataLoader::loadTransitionTable`); worlds cannot add rows to it yet.
- **The engine already remembers every item the party has ever held.** Every way an item can be gained calls `Party::recordEverOwnedItem` (19 calls: chest, corpse, ground, script, the item held on the mouse). The record is saved, and Lua can already ask it with `HasEverOwnedItem(id)`.

**1. 47 spot finds**
- **DECISION:** no window on any find. Pick by the kind of spot:
  - **(a) Something the party clicks** (nest, rubble pile, gem, crystal on an altar, booth, kettle): a status-line find, the MM6–MM8 way. The item goes into the packs, the bit is set, the sprite or state changes where the map has one, and a short status line says what was found.
  - **(b) A real container** (desk, rack, strongbox, crate, coffin): the container becomes a chest holding the item (`objects.yml items:` + `map_gives`). This is the F15 rule already adopted.
  - **(c) An item lying in the open with nothing else happening** (a bare alcove or ledge): a placed 3D ground item. It is safe because of decision 5.
  - **(d) A find behind a question** (password, riddle): the question stays because it is a choice. The answer is a status-line find, with no second window.
  - **Only exception:** a note meant to be read keeps its window (Joe's invoice).
- **WHY:** this is the user's "loot like MM6–MM8", and the exported MM6–MM8 Lua shows exactly this pattern.
- **WHO ACTS:** A3 sets the default in `gen_quests` (a `gives:` hook writes a status line). `quests.py` refuses a `gives:` hook that shows a window unless it says `window: "<why>"`; this closes the "no automatic refusal yet". A3 also splits the 47 into a/b/c/d. The map lanes A5/A6/A7/A8 do the chest and ground-item conversions, plus X2's strongbox (A5).
- **REVERSIBLE:** yes, it is generator and data work only.

**2. Touch sites that only give experience (Soul Waters, Shangri-La's well, the Tome, the Manual)**
- **DECISION:** status line, with `status: true` and the "again" line also on the status line. A site keeps a window only if its source text is long lore meant to be read (over about 200 characters), recorded as `window: "<why>"`.
- **WHY:** these are F13's touch effects; experience is a party effect like a stat.
- **WHO ACTS:** A3 (hooks; `check_touch_sites` should treat an experience award as a party effect). Map lanes only for sites wired in their own map `lua:`.
- **REVERSIBLE:** yes.

**3. Eleven monster-death lines**
- **DECISION:** status line by default (Rooka, Blackfang, Darzog, Draco and the rest), held by the existing length rule.
  - A death keeps a window only if its hook plays a cinematic or a voiced line, or carries a long story text that is the point of the moment. That is likely just Lord Xeen's end and any death that ends an act.
  - The quest item a boss holds stays corpse loot (`carries:`), never handed over by the death script.
- **WHY:** MM6–MM8 bosses mostly die silently (a monster group's bit is set). A window in the middle of a fight is exactly the interruption the user objected to (12.png).
- **WHO ACTS:** A3 (death hooks `status: true`; `quests.py` applies the same `window:` rule to death hooks).
- **REVERSIBLE:** yes.

**4. Entrance flavour lines**
- **DECISION:** keep them through a world `trans.txt` contribution. The line then shows inside the standard entrance window, exactly where MM6–MM8 put their own `trans.txt` lines. Do not drop them, and do not use a status line on arrival.
  - **C++ (A1):** let worlds add rows to `trans.txt` through `appendWorldTableRows` in a declared id range. The studio writes a text id into `MoveToMap` for both `screen` and `leave` (fold this into the F16 spec already with A1). The lines go through the localization pipeline.
  - **Data:** A3/data writes Xeen's rows from the MM4/5 source lines.
  - **After merge:** the map lanes rebuild Lua-only and drop the 44 Yes/No prompts. Entrances without a source line fall back to "Do you wish to enter X?".
- **WHY:** this is what MM6–MM8 do, so it costs the player no extra window and keeps the source flavour.
- **WHO ACTS:** A1 (C++ and studio), then A3 (rows), then map lanes A5–A8 (rebuild, prompts removed, tests' `answer_input: Yes` changed to `OK`).
- **REVERSIBLE:** yes. Rows can be emptied, and the fallback text is automatic.

**5. Quest-item bits on pickup**
- **DECISION:** no new C++ table. Quest conditions about an item read `HasEverOwnedItem(id)`:
  - `gen_quests` gets a `found: <item>` condition (or `requires`) that compiles to that call.
  - The bit "set when the chest opens" goes away wherever its only job was to mean "the item was found", because it is wrong when a chest is opened and left full.
  - An experience or gold award "on finding" moves to the hand-in or the find event. Only add a C++ "on first acquisition" table later if a case truly needs a side effect at pickup that no event can provide.
- **WHY:** the engine already records every item gained and saves the record. A new table would just repeat it, against the rule against adding duplicated ownership. It also makes the chest and ground-item finds in decision 1 correct for free.
- **WHO ACTS:** A3 (the `gen_quests` condition, the audit counts `found:` as read, hooks moved off chest-open bits). Map lanes rebuild Lua-only.
- **REVERSIBLE:** yes.

**SUMMARY ROW**

| D-90 | 2026-11-22 | Finds, touch sites, death lines, entrance texts, quest-item bits (F13/F15/F16 follow-ups) | No window on finds, experience touches or monster deaths: status-line finds (item into packs, sprite or state change), real containers become chests, bare-floor items become 3D ground items, a window only with `window: "<why>"` (a note, long lore, a cinematic or voiced line, a choice's answer); quest conditions about an item read the existing `HasEverOwnedItem` instead of chest-open bits. Entrance flavour lines are kept as a world `trans.txt` contribution shown inside the standard MM6–MM8 entrance window, replacing the 44 Yes/No prompts. | A3 (gen_quests/quests.py rules, sorting the 47, `found:`, trans rows); A1 (world `trans.txt` rows + studio text id on `screen`/`leave`, with the F16 spec); map lanes A5–A8 (chest/ground-item conversions, X2 strongbox, Lua-only rebuilds, tests) |
