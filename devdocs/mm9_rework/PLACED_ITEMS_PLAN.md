# MM9 placed items as world items (plan)

Status: **implemented** (2026-11-08; approved by the user the same day). Engine: `game/maps/MapItemSourceYml.cpp`,
`IndoorWorldRuntime::onPlacedWorldItemTaken`, `MapDeltaData::takenWorldItems` (save version 165). Converter:
`level_generation/projects/mm9r_common/dungeon/pickups.py`. Lost items: `game/mm9/Mm9RudeDialogue.cpp`,
`tools/mm9_import_discovery/generate_mm9_lost_items.py`, `tests/scenarios/mm9/lost_items_hjordisa.yml`.

MM9 placed its pickable items as ordinary `Prop`s: the prop's script gives the item and removes the prop (`givetake.scr`,
`bootgive.scr`, `skillbook.scr`, `orb.scr` and one script per quest item). Only the Golden Honk is a real `PickupItem`.
Until now the converters built each of them as a decoration with a click event that put the item straight into the
packs, so there was no 3D item model, no sparkle and no right-click inspect. This plan makes them real world items,
picked up as any MM6–MM8 ground item, with the prop's side effects in a map Lua pickup handler. It also gives the party
a way back to a lost quest item: Hjordisa the Hag (Guberland, RUDE 132) returns it.

## 1. What MM9 placed (measured)

From the objects of all 45 MM9 worlds (`mm9/extracted/WORLDS`):

| Group | Objects | Where |
| --- | --- | --- |
| Simple gives (`givetake.scr`, `bootgive.scr`, `orb.scr`, `skillbook.scr`) | about 50 | Boot Camp 14 scrolls, Lich Lab 7 herb bags and 4 jars, Inventastorca 7 orbs, Ta'Sar Academy 6 skill books, Afterworld 5 Jarls' swords, single scrolls, notes, a hairbrush and a key elsewhere |
| Quest pickups (one script each) | about 18 | Drangheim's herbs, plow and dolly, Kira's Shield, the Saint's Relic, the Tree of Life, the Writ of Fate, Crona Kiga, the Lich Instructions, Ludwig's Manuscript, the Book of Rules, the Golden Honk, the Honk key, Yanmir's key, the Blackheart dirk |
| Interactions (stay scripted props) | about 8 | the slag extractor (takes 399, gives 398), the great book and the book key (the item depends on what the party holds), the Capstone, the fake book, Thjorad (usable only at one point; the monks turn hostile), the Wizard's Lab skeleton (its item 386 does not exist) |
| Set dressing (stay decorations) | about 75 | the battlefield swords, scrolls on shop counters, helmets on racks, the prizes, the animated pickaxes, the readable books and letters (`BookLetter.scr` gives nothing) |

Every converted item has a ground model in `worlds/mm9/world_items/items.yml`. Quest items have value 0, so they
sparkle red (`worldItemSparkle`, Quest); skill books (value 50) do not sparkle.

## 2. Engine (shared code, used only by scenes that declare `world_items`)

The scene's `world_items` list (`game/maps/MapItemSourceYml.cpp`) existed but no map used it. It becomes:

```yaml
world_items:
  - source_id: inventastorca:Prop2       # unique per map, the saved "taken" key
    source_object_index: 413             # the DAT object
    source_name: Prop2
    position: {x: ..., y: ..., z: ...}
    item_id: 10252                       # or 0 with random_item_pool
    random_item_pool: []                 # one item drawn per session from the pool (a random skill book)
    required_qbits: []                   # shown only while all are set
    forbidden_qbits: [90337]             # hidden while any is set
    pickup_qbits: []                     # optional: shown, but taken only with all of these; no sparkle before
    pose: {yaw: 0, pitch: -75, roll: 0} # optional, degrees: drawn and picked turned so (yaw about up, then pitch
                                         # about its across axis, then roll about its long axis), its lowest point on
                                         # its position, instead of lying flat on what is under it
    set_qbits: []                        # set when the party picks it up
    pickup_event: 30413                  # map event run after the pickup; 0 for none
```

1. **Picked up as any world item.** A click takes it into the active member's pack (or the cursor), with the usual
   sound, speech and status text. The runtime then records the source as taken, sets `set_qbits` and runs
   `pickup_event`, the map Lua's handler for the prop's side effects (XP, sound, other keys, a triggered event). The
   old policy fields (`grant_items`, `take_items`, `clear_qbits`, `consume_on_success`, a pickup that ran an event
   instead of the pickup) are removed: a world item is the item it shows.
2. **Taken stays taken.** The map state keeps the source ids of the items taken (`MapDeltaData::takenWorldItems`,
   saved), and loading the map skips them; a refill keeps the list. Without it the item came back on every entry,
   and the skill books and spell scrolls would be unlimited.
3. **Visibility only when quest bits change.** The gates were evaluated every frame. Now a map without `world_items`
   does nothing, and one with them re-evaluates only when the party's quest bits change (its revision counter) and
   after a pickup.
4. **Resting where placed.** Most items lie on tables and shelves, which are decorations, not floor faces. Placed
   items are not dropped to the floor below on load.

MM6–MM8 scenes have no `world_items`; their maps, saves and frames are unchanged apart from an empty saved list.

## 3. Converter (`level_generation/projects/mm9r_common/pickups.py`)

One shared table maps each pickup script to its item, gates, set keys and side effects, from the script's own
`:Init` and `:OnUse`:

- **Gates**: the keys the script's Init removes or hides the object on become `forbidden_qbits`; the keys it shows the
  object on become `required_qbits` (raw MM9 key + 90000, `world.yml qbits.mapping`). Example: Drangheim's herbs
  show with key 128 and never after key 131. An object MM9 always shows but lets the party take only on its quest
  takes `pickup_qbits` instead: Kira's Shield lies in Thronheim City from the start and is taken only with key 214
  (the user, 2026-11-08); until then a click does nothing and it does not sparkle.
- **Set keys**: the keys OnUse gives become `set_qbits`.
- **Side effects** (XP, sound, a trigger, the alarm bell, a branch on another key) go in the map Lua handler at the
  prop's own event id (`30000 + DAT index`, `objects.py OBJECT_EVENT_BASE`), written by the same module.

An item MM9 stood or leaned is posed by the map's `overrides.yml`:
`pickups: {<DAT name>: {pose: [yaw, pitch, roll], offset: [x, y, z]}}` (degrees, native units): Thronheim City's Kira's
Shield leans on its wall (`pose: [180, -75, 0]`, `offset: [0, -14, 0]`).

Each map's converter replaces its own pickup code (the decoration, its click event, its `Taken…` variable and
`SetSprite` lines) with the module's `world_items` and handlers. Interactions and set dressing are untouched.

**Old saves**: the quest pickups' gates are MM9's own keys, so an item already taken stays gone. A simple give
(an orb, a herb bag, a skill book) taken under the old scheme may show once more; the user accepted that (a second
quest item does nothing).

## 4. Lost items at Hjordisa (RUDE 132, Guberland)

- `worlds/mm9/dialogue/lost_items.yml` gives RUDE 132 a standing topic, "I've lost something.", the mechanism
  `promotions.yml` uses for the promoters (`game/mm9/Mm9RudeDialogue.cpp`). It runs a shared MM9 Lua event.
- `MM9.RecoverLostItem()` (`mm9_common.lua`) returns one item per ask, from `MM9.LostItems`: every item an MM9 script
  checks or takes (generated). An item qualifies when the party has owned it, holds none now and has not handed it
  in; `MM9.takeItem` records the hand-in. Otherwise she says the party never had it. Free, as MM6–MM8's seers.
- MM6–MM8's seers (`support.tryRecoverLostItem`) are unchanged.

## 5. Rollout

1. Engine changes with unit tests (schema, taken list save/load, refill).
2. Pilot: Inventastorca (orbs), Lich Lab (herbs and jars on shelves), Drangheim (quest-gated herbs, plow, dolly);
   an engine screenshot per item (model in place, sparkle) and a scenario (pickup, re-entry).
3. All maps; the scenarios that clicked these props pick up the world items instead. Install by the MM9 rules
   (scratch build, `check_mm9_map_lua.py`, both review roots, promotion).
4. Hjordisa's topic with a scenario: lose the herbs, ask for them.

## 6. Results (2026-11-08)

- 61 world items in 19 maps (promotion R11). Interactions and set dressing stayed props.
- A region's props.json names its props `obj_<DAT name>`: the scene's `source_name` is that name; `REVEALED_BY` and
  the gates use the DAT object's own Name.
- Hjordisa's list: 62 items (the generator reads the installed map scripts, so a give-once check removed with its
  prop drops its item: the tutorial notes and Njam's Struggle, none needed to go on).
- Known issue: Ta'Sar's Book of Rules lies flat on its tilted lectern and clips into it.

