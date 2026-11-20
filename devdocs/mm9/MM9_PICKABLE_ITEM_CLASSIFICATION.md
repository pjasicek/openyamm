# MM9 Pickable Item And Item-Source Classification

Status: complete shipped-map census and OpenYAMM representation decision.

## Result

MM9 does not define ordinary ground loot through a map-level item list. The original DAT object record defines the
world object and stores `ScriptName` plus `ScriptParams`; the bound SCR usually supplies the item id and the interaction
logic. Native object class behavior supplies chests, bone piles, and the exceptional `PickupItem` class.

The shipped data contains:

- 45 DAT maps and 32,288 DAT objects;
- 94 `Prop`/`PickupItem` objects bound to a script containing `GiveItem`;
- 36 parameterized, disappearing `GiveTake.scr`/`BootGive.scr` objects;
- 68 fixed one-shot world-item instances in total: the 36 generic objects plus 32 custom quest/item pickups;
- 24 stateful or reusable item-producing props, including 20 staged Ta'Sar textbook positions;
- two non-pickup false positives among the 94: Verhoffin's capstone placement socket and `WinMan`;
- 163 native `TreasureChest` objects on 31 maps;
- 77 `BonePile` objects with `TreasureLevel` and disease properties on 14 maps;
- four authored `TreasureBag` objects, plus 22 more produced by destructible objects' DAT `SpawnObject` property;
- 1,911 authored actors with `GiveTreasure=true` (dynamically spawned actors may add more death-loot rolls); and
- exactly one native `PickupItem`: the Golden Honk. Its DAT `ItemId` is `0`; `Honk.scr`, not the DAT field, grants
  item 369.

There are no shipped SCR commands that spawn a `PickupItem`, item-bearing `Prop`, weapon object, or other ground item.
Every audited `Spawn`/`Spawn2` path creates an actor, monster, or encounter helper. SCR can award inventory items with
`GiveItem`, but that is a direct award, not a spawned world pickup. DAT/native behavior *can* create ground loot:
21 Bathhouse destructibles and one Beethoven destructible spawn a random `TreasureBag`. Monster death treasure,
chests, treasure bags, and bone piles are therefore separate native/procedural loot families.

The complete non-empty DAT `SpawnObject` audit is 23 objects: those 22 treasure-bag producers plus Ta'Sar Academy
destructible 806, which spawns a scaled `Dagrell` world prop and no inventory item.

The registered ObjectDLL class `PickupItemSpawn` has no shipped DAT instance and no SCR reference. Its name alone is
not evidence of another authored pickup source; keep it as an unresolved native runtime helper until its constructor
and callers are recovered.

## OpenYAMM Representation

Use these categories throughout the map inventory:

| Code | Representation | Required behavior |
| --- | --- | --- |
| `WI` | MM6-MM8-style `WorldItem` billboard | Fixed item id, source object index and position, use/pickup, persistent removal. Preserve the MM9 model/skin only as provenance. |
| `QWI` | Quest-gated `WorldItem` billboard | `WI` plus declarative QBit/item availability and pickup actions. Re-evaluate availability on load; do not hand-write a whole-map Lua initialization loop. |
| `IP` | Interactive producer/decoration | Retain a persistent world interaction and run a small event handler. Use for cooking, conversion, random dispensers, placement sockets, and staged book positions. |
| `DA` | Direct award | NPC/dialogue, minigame, controller, or event grants an item directly. Do not create a world object. |
| `TC` | Treasure container | Native/shared chest UI, lock/open state, one-shot generated payload, and save state. Not a `WorldItem`. |
| `BP` | Searchable bone pile | Small one-shot loot source using `TreasureLevel`, disease chance/power, and save state. Not a `WorldItem`. |
| `TB` | Ground treasure bag | Billboard loot-pile/container backed by gold and up to five items or a random tier. It may be authored or spawned when a destructible breaks. Materializing its payload as MM6-MM8 `WorldItem`s is also valid, but generate them at drop time, not map load. |
| `DT` | Actor death treasure | Actor-owned procedural reward controlled by `GiveTreasure`; keep this on actor state/loot data. The map count is an audit signal, not authored ground-item placement. |

`OnLoad` should only ask the shared world-item/state system to recompute availability. A `QWI` record should own fields
such as `required_qbits`, `forbidden_qbits`, `required_items`, `grant_items`, `set_qbits`, `take_items`,
`on_pickup_event`, and `remove_when_complete`. Lua is appropriate for the genuinely stateful `IP` cases, not for
reconstructing every static pickup by scanning the map.

The source `Barrel`, `Cauldron`, `Cookpot`, and `Clover` classes were also checked. They are stat/resistance/buff
interactables, not inventory-item sources, and must not be imported as pickups. Actor `GiveTreasure` is death loot and
should stay on actor/loot definitions rather than being expanded into each map's authored-world-item list.

## Per-Map Inventory

Object numbers below are original DAT `object_index` values. `TC`, `BP`, and authored `TB` entries list every native
loot object; `DT` gives the count of authored actors with death treasure enabled. Dynamically spawned actors are noted
but cannot have fixed DAT indices.

### 1000 Terrors

- `WI`: 2037, Note (598), `BootGive.scr`.
- `IP`: 1953, genie lamp. Each use selects one of six effects; its item branch uses the fixed 61-entry pool in
  `GiveRandom.scr`. Quantity parameter `0` makes it reusable.
- `DA`: 1733 `WinMan` is an endgame controller, not loot; its finale can grant Writ of Fate (394).
- `TC` fixed payloads: 1855 contains Scrap of Paper (593) and Stairs Key (600); 1866 contains Maze Key (599).
- `TC`: 14 — 1854-1867. `BP`: none. `DT`: 178 authored actors.

### Afterworld

- `WI`: 124 Kira's Sword (567), 125 Sigmund's Sword (565), 126 Tryygva's Sword (566), 127 Bjarni's Sword (564), and
  128 Sven's Sword (563). All are `GiveTake` one-shots.
- `TC`/`BP`: none. `DT`: none authored.

### Anskram Keep

- No fixed world item or direct item award.
- `TC`: 37, 1109, 1111, 1124-1127. `BP`: 1238-1240, 1245. `DT`: 55 authored actors.

### Arslegard City

- `WI`: 449, Njam's Struggle (575), `GiveTake` one-shot.
- `TC`/`BP`: none. `DT`: 36 authored actors.

### Bathhouse

- No fixed world item or direct item award.
- `TB`: destructibles 224-244 spawn 21 random bags: level 3 at 225, 229, 232-233, 237, 239, 242; level 5 at the
  other 14 indices. This is DAT `SpawnObject` behavior, not SCR spawning.
- `TC`: 220-223. `BP`: none. `DT`: 16 authored actors.

### Beethoven

- `QWI`: 778, Ludwig's Manuscript (248). Alternate quest paths use QBits 14/16 and 110; remove after either completed
  pickup path.
- `TB`: destructible 1185 spawns one random level-1 bag when destroyed.
- `TC`: 1037-1047. `BP`: 852-857. `DT`: 84 authored actors.

### Boot Camp

- `WI`: 205 Classes (583), 206 Notes (584), 212 Shopkeepers (585), 213 Movement I (586), 214 Movement II (587),
  215 Combat (588), 218 Scroll of Spell Reaving (548), 219 Scroll of Leggib (523), 220 Scroll of Lightning (511),
  221 Spells (581), 222 Skills (582), 223 Scroll of Mines (532), 224 Scroll of the Bugs (555), and 225 Scroll of
  Sparks (547).
- The six MM9 spell scroll definitions are unsupported, so the world-item importer preserves those six objects and
  positions while substituting shared scrolls: 548 -> Dispel Magic (379), 523 -> Wizard Eye (311), 511 -> Lightning
  Bolt (317), 532 -> Fire Spike (306), 555 -> Slow (334), and 547 -> Sparks (314).
- `DA`: NPC436 can grant Disarm Trap Skill (298), Identify Item Skill (302), Interface I/II (579/580), and Strategy
  Tips (589).
- `TC`: none. `BP`: 362. `DT`: 27 authored actors.

### Chasm of the Dead

- `QWI`: 1313 Lich Instructions (447), one-shot with QBit 296; 1314 Crona Kiga (390), alternate QBit 48/169 quest
  paths.
- `TC`: 1191, 1664-1678. `BP`: none. `DT`: 173 authored actors.

### Connecting Tunnels

- No fixed world item or direct item award.
- `TC` fixed payload: 565 contains Spencer's Obedience (198).
- `TC`: 565, 670. `BP`: 513-521. `DT`: 38 authored actors.

### Dark Passageway

- `WI`: 576, Scrap of Book (483), `GiveTake` one-shot.
- `TC`: 22-24, 603-606. `BP`: none. `DT`: 43 authored actors.

### Dook's Castle

- No fixed world item or direct item award.
- `TC` fixed payload: 385 contains Everstrike (184).
- `TC`: 304-308, 385, 458. `BP`: none. `DT`: 47 authored actors.

### Dragon Stadium

- No fixed world item or direct item award.
- `TC`: 43-44. `BP`: 45-47. `DT`: none authored; stadium encounters spawn the actors dynamically.

### Drangheim

- `QWI`: 25 Midwife's Bag of Herbs (372), 26 Farmer's Plow (371), and 27 Dolly (370). These are the same flow:
  require QBit 128, hide and disable solidity/gravity otherwise, forbid completion QBit 131/130/132 respectively,
  grant the item, set that completion QBit, and remove the object.
- `QWI`: 28, the real Verhoffin book interaction. It requires Book Key (244), then grants Eye of the Storm (347) and
  Verhoffin's Book (560), sets QBits 283/290, and removes itself.
- `TC`: 19, 51, 112-113. `BP`: 190-192. `DT`: 39 authored actors.

### Drangheim City

- `DA`: NPC87 can grant Trap Key (596).
- `TC`/`BP`: none. `DT`: 39 authored actors.

### Drangheim Prison

- `DA`: the `GuardRude` interaction can grant Visitor's Pass (446). It is dialogue/guard state, not ground loot.
- `TC`: 497-502. `BP`: 495-496, 503-513. `DT`: none authored; encounters use spawners.

### Dungeon of Secrets

- No fixed world item, direct item award, chest, or bone pile. `DT`: one authored actor (636).

### Frosgard

- `DA`: NPC221 can grant The Green Man amulet (213).
- `TC`: 13-14. `BP`: none. `DT`: 38 authored actors.

### Frosgard City

- `DA`: NPC183 Lich Instructions (245), NPC184 Keg of Strange Brew (249), NPC188 Ritual of Consecration (430), and
  NPC209 Fjordor's Boat Schedule (562).
- `TC`/`BP`: none. `DT`: 50 authored actors.

### Great Gate

- No fixed world item, direct item award, chest, bone pile, or authored death-treasure actor.

### Guberland

- `WI`: 229, Lock of Hair (240), `GiveTake` one-shot.
- `DA`: NPC130 Victory Certificate (400), NPC132 Lock of Hair (240), and NPC133 Capstone of Order (396).
- `DA/IP`: the Gathering game service sells Game Tickets (557), supplies Game Instructions (594), and its all-games
  prize selects one of items 362-367. This is minigame inventory logic, not a pickup.
- `TC`/`BP`: none. `DT`: 64 authored actors.

### Guberland City

- `DA`: NPC142 can grant Nurtigan's Potion (558).
- `TC`/`BP`: none. `DT`: none authored.

### Hall of the Gods

- `DA`: NPC335 grants Njam's Key (576); the endgame `WinMan` controller can grant Writ of Fate (394).
- `TC`/`BP`: none. `DT`: none authored.

### Inventa Storca

- `WI`: 413-419, seven Orb of Linking objects. Every object grants item 252 and removes itself. Parameters
  325/323/324/326/327/328/329 are read but unused by `Orb.scr`; QBit 337 removes any remaining orbs.
- `TB`: 394-395, two authored random level-4 treasure bags.
- `TC` fixed payload: 392 contains Gungnir (189).
- `TC`: 391-393. `BP`: 725-727. `DT`: 39 authored actors.

### Isle of Ashes

- `DA`: Yrsa can grant Turret Key (568).
- `TC`: 475-476, 772. `BP`: none. `DT`: 51 authored actors.

### Kluso's House

- `QWI`: 247, Blackheart. Grants Elite Dagger (29), sets QBit 223, sounds the alarm, and removes itself.
- `TC` fixed payload: 392 contains Black's Heart (180) and Chedian Chain (102).
- `TC`: 392. `BP`: none. `DT`: 20 authored actors.

### Lich Lab

- `WI`: 1500-1505 and 1514, Elixir Ingredients (378); 1509-1512, empty Jar (358). All are `GiveTake` one-shots.
- `IP`: 1507 cookpot consumes Ingredients (378) and grants Elixir Fluid (561). 1506 burner consumes Jar (358) plus
  Elixir Fluid (561) and grants Elixir of Defedation (246). Neither mechanism is a ground item.
- `TC`: 1516-1523. `BP`: 1551-1553. `DT`: 147 authored actors.

### Lindisfarne

- No fixed world item or direct item award.
- `TC`: 333. `BP`: none. `DT`: 63 authored actors.

### Lindisfarne Monastery

- `QWI`: 407, Thjorad (197), with alternate QBit 31/162 acquisition paths.
- `DA`: NPC282 can grant Letter (419).
- `TC`/`BP`: none. `DT`: 27 authored actors.

### Mountain Pass

- No fixed world item or direct item award.
- `TC`: 128. `BP`: 263-267. `DT`: 76 authored actors.

### Ruined Temple

- `QWI`: 5, Tree of Life (241), sets QBit 256 and removes itself.
- `DA`: the Colloidal Genie can choose a random item from 234-238 as one wish outcome; no world item is spawned.
- `TC`: 429-431. `BP`: 391-395. `DT`: 15 authored actors.

### Sturmford

- No fixed world item or direct item award.
- `TC`: 104, 138-140. `BP`: 181-182, 255-259. `DT`: 57 authored actors.

### Sturmford City

- `DA`: Bjarni can grant Love Letter (247).
- `TB`: 1392-1393, two authored random gold-only bags.
- `TC`/`BP`: none. `DT`: 48 authored actors.

### Ta'Sar Academy

- `WI`: 692-695 and 700-701 are disappearing skill books. Object 695 is Blade Skill (285); the other five select a
  random id from 285-306. Raw item 285 is referenced and named in `SkillBook.scr`, but is missing from
  `MASTERITEMLIST.csv`; this must be repaired in authoritative MM9 item data before import.
- `QWI`: 697, Book of Rules (391), with alternate QBit 59/166 paths.
- `IP`: 714-733 are not 20 independent books. They are four textbooks (435-438) represented at five staged locations:
  Start, Offense, Defense, Strategy, and Intelligence. Import four inventory items plus location/state nodes and the
  table place/take flow.
- `TC`: 765-766, 808-809. `BP`: none. `DT`: none authored; enemies are spawned.

### Temple of Honk

- `QWI`: 61, Accountant's Key (445). The prop sets QBit 7000, unlocks the target door, may notify the accountant, and
  removes itself.
- `QWI`: 453, Golden Honk (369). This is the sole native `PickupItem`, but `Honk.scr` grants the actual item. QBit 343
  controls the quest branch; QBits 344/345 prevent repeat pickup; pickup also removes the friendly Honk actor.
- `TC`: 58, 552-555. `BP`: none. `DT`: 26 authored actors.

### The Arena

- No fixed world item, direct item award, chest, bone pile, or authored death-treasure actor. Arena scripts spawn
  combatants, not item objects; their actor loot settings still apply.

### Thjorad Mine

- `IP/QWI`: 1464, slag extractor. First use grants Broken Slag Extractor (398), sets QBit 9512, and hides the object.
  A later `show` interaction consumes repaired Slag Extractor (399), sets QBit 37, changes the visual to the whole
  machine, and reveals it. Model swapping is world state; only item 398 should be a billboard while carried.
- `TC` fixed payloads: 1486 contains ore 361/360/359/359; 1487-1499 each contain ore 359; 1500 contains
  361/360/360/359. These are Elemental Thjorad lode/chunk/lump items.
- `TC`: 1486-1500. `BP`: 551-561. `DT`: 73 authored actors.

### Thjorgard

- `DA/IP`: the Gathering game service sells Game Tickets (557), supplies Game Instructions (594), and grants Stuffed
  Dragon (395) for the all-games prize. Do not materialize these as ground loot.
- `TC`: 89, 410. `BP`: none. `DT`: 54 authored actors.

### Thjorgard City

- `QWI`: 1094, Great Book Key interaction. Its QBit 375 controls visibility. The main branch grants Verhoffin's Book
  (560), Book Key (244), and Eye of the Storm (347), sets QBit 374, and removes the object; its alternate branch grants
  only Book Key (244).
- `DA`: NPC4 can also grant Book Key (244); NPC5 converts Broken Slag Extractor (398) to repaired Slag Extractor (399).
- `TC`/`BP`: none. `DT`: 60 authored actors.

### Thronheim

- No fixed world item. NPC quest logic consumes the Stuffed Dragon (395), but does not source a map pickup.
- `TC`: 45, 91-92. `BP`: none. `DT`: none authored.

### Thronheim City

- `QWI`: 55, Kira's Shield (375), requires QBit 214, sets QBit 216, and removes itself.
- `DA`: Kira/NPC239 can grant Peace Treaty (401); NPC242 can grant Scroll of Bad News (251).
- `TC`: 53. `BP`: none. `DT`: 49 authored actors.

### Training Hall

- No fixed world item or direct item award.
- `TC`: 377-381. `BP`: none. `DT`: none authored.

### Verhoffin Ruins

- `QWI`: 229, fake Verhoffin's Book (242), sets QBits 281/290 and removes itself.
- `QWI`: 232, Writ of Fate (392), visible only with QBit 99 and absent after QBit 100; pickup sets QBit 100 and
  removes it.
- `WI`: 651, Key to Study (559), `GiveTake` one-shot.
- `IP`: 650 is the capstone placement socket, not a pickup. It consumes Capstone of Order (396), sets QBit 99, reveals
  the placed capstone, and enables the Writ. Its dormant `GiveItem` branches are unreachable on this DAT binding because
  only the `place` trigger is registered.
- `TC`: 637-642. `BP`: none. `DT`: 30 authored actors.

### Wizard's Lab

- `WI`: 592 requests raw item 386 through `GiveTake`. Item 386 is absent from `MASTERITEMLIST.csv`; preserve the
  broken source reference and do not guess an identity. Its reviewed unsupported disposition retains the original
  skeleton prop as baked geometry and does not emit an invalid pickup.
- `QWI`: 877, Saint's Relic (368), alternate QBit 339/340 quest paths.
- `DA`: NPC55 can grant Black Orb of Knowledge (250).
- `TC`: 878-880. `BP`: 217-220. `DT`: none authored.

### Yanmir's Fort

- `QWI`: 617, Yanmir's Key (570), sets QBit 7001, unlocks the cage targets, and removes itself.
- Object 702 is a teleport door that reuses patched `Writ.scr`; its overloaded `Init` only pairs the doors. It is not
  another Writ pickup.
- `TC` fixed payload: 568 contains Sage Diary (595).
- `TC`: 62, 560-569. `BP`: none. `DT`: 73 authored actors.

### Yorwick

- No fixed world item or direct item award.
- `TC`: 160-161. `BP`: none. `DT`: 75 authored actors.

## Quest-Item Definition Coverage

`MASTERITEMLIST.csv` contains 529 item definitions, of which 167 have `Quest Item` in either the type or tier field.
The DAT/SCR/native-container audit finds an authored source or item operation for 84 of those 167. This includes fixed
world pickups, direct NPC or event awards, staged producers, fixed chest payloads, and constant-based operations such
as Accountant's Key (445) and Game Instructions (594).

The following 83 quest-classified ids have no fixed DAT pickup/chest binding and no `GiveItem`, `TakeItem`, or
`HasItem` reference in the shipped SCR corpus:

`373, 379, 393, 397, 424-429, 431-434, 439-444, 448-482, 484-503, 569, 571-574, 578, 592, 597`

Most of the large 424-503 block is duplicate letter/post/invoice/lore data. Some numbers also appear as QBits, which is
not an item reference. These definitions are accounted for as **data-only/unreferenced**, not as missing world objects.
Do not invent pickups for them. Promote one only when another authoritative source proves an acquisition path.

Three pickup-like scripts have no shipped DAT binding and are not referenced by an item-spawn path:

- `Everstrike.scr` — item 184 is instead a fixed reward in Dook's Castle chest 385;
- `Gungnir.scr` — item 189 is instead a fixed reward in Inventa Storca chest 392; and
- `Integris.scr` — no source for item 181 was found.

Treat the SCR files as unbound/stale pickup implementations, not implicit map pickups. This does not invalidate a
separate native-container source for the first two items.

Two live item-producing paths expose source-data integrity errors outside that 167-row quest classification:

- Ta'Sar's skill-book range includes raw item 285, called Blade Skill by `SkillBook.scr`, but row 285 is absent; and
- Wizard's Lab object 592 explicitly requests raw item 386, but row 386 is absent.

Both must remain visible import errors. Neither may silently map to another item.

## Evidence And Validation Rules

Primary local evidence used for this census:

- original-DAT-derived objects: `../OpenMM9/assets_dev/maps/*.raw_objects.yml`;
- extracted scripts: `../OpenMM9/reference/extracted/SCRIPTS/SCRIPTS/`;
- item definitions: `../OpenMM9/assets_dev/source/data/MASTERITEMLIST.csv`;
- generated whole-DAT class census: `../OpenMM9/docs/dat_object_class_inventory.md`; and
- native treasure behavior findings: `../OpenMM9/docs/object_native_re_method_findings.md`.

The raw sidecars currently expose `TreasureBase.Item1`-`Item5` values as their 32-bit integer bit patterns. The fixed
chest ids in this document are the exact whole-number IEEE-754 values represented by those bits (for example,
`1142177792` decodes to `593.0`), cross-checked against `MASTERITEMLIST.csv`.

The extracted SCR set contains explicit TELP patch comments in a few scripts, notably `Writ.scr` and `Capstone.scr`.
This document therefore describes the installed reference game's shipped/patched behavior, not an asserted pristine
1.0 executable state.

Validation for an importer should fail if:

- any of the 45 maps is absent from the generated inventory;
- the `Prop`/`PickupItem` script-binding count changes from 94 without an reviewed inventory update;
- a new item-producing `Spawn` path appears;
- any `QWI` loses its original source object index, QBit gates, or completion action;
- native chest, bone-pile, or authored treasure-bag counts differ from 163/77/4;
- the 22 `DestructableProp.SpawnObject -> TreasureBag` bindings are not represented;
- the authored `GiveTreasure=true` count differs from 1,911; or
- a referenced raw item id, currently including 285 and 386, lacks an authoritative item definition/mapping.
