# Xeen: the quest format

Owner: A3 (`devdocs/xeen/lanes/A3.md`). Written 2026-11-20. How Xeen's quests, NPC topics, journal, autonotes, awards
and map hooks are written (`assets_dev/worlds/xeen/source/quests/`, `source/npcs/`), what
`tools/xeen/gen_quests.py` makes of them, and what the map lanes, A1, A2 and A4 can rely on. `tools/xeen/quests.py`
audits the whole set.

Part 1 is the research answer the other lanes asked for: how MM6–MM8 house dialogue runs quests in OpenYAMM, and how
a world adds its own topic events.

## 1. How house dialogue runs quests in OpenYAMM (MM6–MM8)

### 1.1 The chain

1. **`npc.txt`** (engine table, `game/tables/NpcDialogTable.cpp` `loadNpcRows`): one row per NPC. Column 0 id, 1
   name, 2 portrait, 6 house, 7 profession, 8 greeting id (`npc_greet.txt`), 9 join flag, **10–15 the six topic
   slots A–F** (topic ids; trailing zeros dropped).
2. **`npc_topic.txt`** (`loadTopicsFromRows`): one row per topic id. Column 1 is the **button label**, column 4 the
   text id (`npc_topic_text.txt`), column 6 `teacher hint` marks a text-only topic. A topic id with no row here is
   never shown (`getTopicsForNpc` skips it).
3. When the house dialogue lists an NPC's topics (`game/events/EventDialogContent.cpp`), each slot's topic is shown
   unless the global Lua program has a **`RegisterCanShowTopic(<topic id>, fn)`** that returns false
   (`EventRuntime::canShowTopic`). Lua can replace a slot at run time with `evt.SetNPCTopic(npc, slot, topic)` (saved
   per NPC as `npcTopicOverrides`).
4. Clicking a topic (`GameplayDialogController.cpp`, `EventDialogActionKind::NpcTopic`): built-in topics first
   (teachers, roster joins, guild membership: recognised by id or label), a `teacher hint` row shows its text, and
   **every other topic runs the global event with the same id as the topic**: `EventRuntime::executeNpcTopicEventById`
   looks the id up in the global Lua scope (`RegisterGlobalEvent(<id>, "<title>", fn)`), then the map scope. No handler:
   "That topic does not have an event yet."
5. The event does the quest: `evt.SetMessage(...)` for the reply, `SetQBit(QBit(n))`, `AddValue(InventoryItem(id),
   id)`, `RemoveItem(id)`, `evt.ForPlayer(Players.All)` + `AddValue(Experience, n)`, `SetAward(Award(n))`,
   `SetAutonote(n)`, `evt.SetNPCTopic`, `evt.SetNPCGreeting`, `evt.MoveNPC`. The exported MM6–MM8 events
   (`assets_dev/engine/events/Global.lua`) inline their English text; `NPCText(id, fallback)` reads a row of
   `npc_topic_text.txt` instead (`Global_mmmerge_ore_smiths.lua` uses it).
6. Topic and event ids travel as `uint16_t` (`executeNpcTopicEvent(..., uint16_t(action.id))`), so they must stay
   below 65,536. Xeen's 40000–49999 fits; nothing in the engine, MM6–MM9, the ruleset overlays or MAW uses it
   (checked 2026-11-20; the overlays' hooks sit at 65070–65402, MAW's topics at 10010–10011).
7. The journal (`english/quests.txt`, `game/tables/JournalQuestTable.cpp`): a row with text shows while its qbit is
   set; a row with six or more cells uses its **required** (column 4) and **forbidden** (column 5) qbit lists
   instead, so a step's line can disappear when the next step's bit is set without clearing anything.
8. Street people's one-liners are `npc_news.txt` rows, chosen by the placed actor's **group** through
   `english/npc_group.txt` (group → news id), changeable with `evt.SetNPCGroupNews`
   (`game/gameplay/GenericActorDialog.cpp`).

### 1.2 Where the global events come from

The global program is built in `GameDataLoader::loadMapData` (`game/data/GameDataLoader.cpp`, around line 5140) from:

```text
scripts/common/event_support.lua                      the shared API
+ the active world's common scripts                    buildLuaWorldCommonPathCandidates: events/common/world_common.lua,
                                                       events/common/common.lua, events/common/<world>_common.lua
+ events/Global.lua                                    the exported MM6-MM8 global events
+ events/Global_*.lua overlays                         every Global_<anything>.lua in events/ of every mounted package,
                                                       then the active ruleset's (appendLuaGlobalScriptOverlays)
```

Each map's own program is built the same way from its `events/maps/<stem>.lua` (plus `<stem>_*.lua` overlays), with
the same support and world common prepended. Both programs run in one Lua session.

### 1.3 How a world adds its own topic events

**Answer: in its world common script, `events/common/<world>_common.lua`.** That file is prepended to the global
program (and to every map program) only when the current map belongs to that world, so its
`RegisterGlobalEvent`/`RegisterCanShowTopic` calls register world-scoped global events. MM7 already does this
(`worlds/mm7/events/common/mm7_common.lua` registers global event 889, "I lost it"); MM8 does too (705). Registering
the same id again from the map program's copy is harmless (`requireFreeGlobalEvent` only refuses an id registered
under a different title).

The `events/Global_*.lua` overlays are **not** world-scoped: a development root mounts every world's `events/` folder
at `/events` (`AssetFileSystem::mountMergedWorldPackageRoots` collects all worlds), so MM6's, MM7's and MM8's
`Global_*.lua` load in every world. That is the MMerge design for those three; Xeen does not use it.

MM9 is no model here: its dialogue is the RUDE table (`loadMm9RudeDialogueTable`, MM9 only), not npc topics.

**Xeen therefore uses:**

| File | Owner | What |
| --- | --- | --- |
| `events/common/xeen_common.lua` | A3, hand-written | `Xeen` helpers: promotions, staged maps, gem payment, time of day, mirrors; anything the quest files call by name |
| `events/common/xeen_quests.lua` | generated by `gen_quests.py` | every quest topic as `RegisterGlobalEvent`/`RegisterCanShowTopic`, and the map hooks (`XeenQuests.hook(name)`) |

**Requests to A1 (engine), made 2026-11-20:**

1. **Load every `events/common/<world>_*.lua` of the active world**, `<world>_common.lua` first, the others in name
   order (today only `<world>_common.lua` is read). Until this lands, `xeen_quests.lua` is not loaded; nothing in phase
   0 needs it at run time (the NPC tables wait on W1 anyway). No fallback is wanted: hand-merging generated code into
   `xeen_common.lua` would break the "generated files are never edited by hand" rule.
2. **`events/common/world_common.lua` and `common.lua` should resolve only in the active world's package.** In a
   development root they currently resolve through the merged `/events` mounts, so it appears MM9's generated
   `worlds/mm9/events/common/world_common.lua` (its item-id table) is prepended to MM6, MM7, MM8 and Xeen scripts
   too. Harmless today, but it is a leak; please verify and fix in shared code. Xeen does not create either file.
3. W1's table contributions (landed at merge point 1, `devdocs/xeen/lanes/TABLES.md`) carry what quests need:
   `npc_topic`, `npc_topic_text`, `npc_news`, `quests`, `autonote`, `awards`. `npc_group` (street groups' news) is not
   contributable; Xeen's street people are A4's NPCs with greetings instead, so no request. The NPC rows themselves
   (`npc.txt`, slots filled from `ctx.shared['npc_topics']`) are A4's.

No other engine change is needed for quests: house dialogue, topics, canShow, SetMessage, qbits, awards, autonotes,
`NPCText`, `SetPlayerClass` and the journal's required/forbidden columns all work for a fifth world as they are.

## 2. Files

```text
assets_dev/worlds/xeen/source/
  quests/<id>.yml          one per quest: m1.yml ... m42.yml, q-c1.yml ... q-c28.yml, q-d1.yml ... q-d28.yml,
                           q-f1.yml, q-f2.yml, t1-a.yml ... (promotions), and the built maps' own small quests
                           (x1-tam.yml): A3
  npcs/<map>.yml           topics of A4's NPCs that belong to no quest but touch the story (original lines, the
                           court's plaques) and the street news lines: A3
  npcs/flavour/<map>.yml   flavour topics of NPCs with no quest role (rumours, jokes): A4 (section 5)
assets_dev/worlds/xeen/events/common/
  xeen_common.lua          hand-written helpers: A3
  xeen_quests.lua          generated
assets_dev/worlds/xeen/data_tables/       generated by tools/xeen/build_world.py (gen_quests.py's part):
  npc_topic.txt  npc_topic_text.txt  npc_news.txt  english/quests.txt  english/autonote.txt  english/awards.txt
  quest_hooks.yml          the hook table the map lanes wire by name
```

NPC ids are A4's (`source/towns/<map>.yml`, `npcs:`); quest files key their topics by those numeric ids. Item keys are
A2's (`source/items.yml`, resolved through `ctx.shared['items']`); engine items are written `engine:<id>`.

## 3. Ids

| What | Range | Rule |
| --- | --- | --- |
| Qbits | 110000–119999 | Built maps keep theirs (110010–110599, below). New quest bits by convention: main `111000 + 20·n` (M1 111020), Cloudside side `112000 + 20·n`, Darkside side `113000 + 20·n`, finale `114000 + 20·n`, promotions `114500 + 20·k`, the built maps' own quests `115000 + 20·k`; world systems 119000–119099 (`quests/world.yml`: the twelve town mirrors 119001–119012, each also its town's Town Portal unlock; the Adventurer's Inn roster 119020, set by M1's opening). Every qbit is written in a quest file with its number |
| Topics and topic texts | 40000–49999 | Each file has a **block** b (0–199): its topic ids are `40000 + 50·b + n` (n 1–49, given per topic) and its text ids `40000 + 50·b + i` (i 0–49, counted in file order). Topic ids and text ids are different tables, so they may share numbers. A file with more than 50 texts takes a second block (`blocks: [b1, b2]`). The topic id is also the global event id |
| Blocks | | M1–M42: 1–42; Q-C1–28: 51–78; Q-D1–28: 81–108; Q-F: 111–112; promotions: 115–139; built maps' own quests: 140–148; `world.yml`: 149; A3's `npcs/<map>.yml`: 150–169; A4's `npcs/flavour/<map>.yml`: 170–198; `npcs/books.yml`: 199 |
| Autonotes | 4001–4999 | Given per note |
| Awards | 401–499 | Given per award |
| News | 40000–49999 | `npc_news` rows from `npcs/<map>.yml` (domain `npc_topics`, as TABLES.md says); a placed actor shows one only through `evt.SetNPCGroupNews` |

## 4. A quest file

```yaml
id: M2                       # the QUESTS.md id; the file name is its lower case (m2.yml)
title: Joe the Exterminator
act: I                       # I-VI, opt
kind: main                   # main | side | promotion | ours (a quest the built maps invented)
status: full                 # full: text and logic done; outline: steps and hooks, text to follow
giver: 4003                  # A4's NPC id (Mayor Gunther)
maps: [X1, XD-01]            # source/maps.yml keys
level: 2                     # the party level it is set for
block: 2                     # topic and text id block (§3)
after: [m1.started]          # the qbits that must be set before it can start (the audit's order)
source: "QUESTS M2; xeen/aaze0028:1-27"

qbits:                       # every qbit the quest owns, by name
  started: {id: 111040, journal: "Find out why Joe the Exterminator always arrives just after the pests.",
            until: [done]}   # the journal line shows while started is set and none of `until` is
  # `journal_while: [m36.started]` shows a line while other bits are set instead of its own (a target's line from the
  # task's start until the target's own bit: M37's Reflectors, M38's Sleepers). Every line needs an `until` (the audit
  # refuses one without: Current Quests lists open tasks, and a line leaves when its step is done); a standing line
  # with no end says why in `journal_stays: "<why>"` (Q-D7's gemsmiths). A record of something done is no journal
  # line (an autonote or an award, if anything).
  joe_invoice_found: {id: 110010, map: XD-01}    # a built map's bit: number kept
  done: {id: 111041}

player_bits:                 # per-character bits a map uses (once per character), registered so none is used twice
  book_might: {id: 11230, map: XD-12}

autonotes:
  invoice: {id: 4010, text: "Joe's invoice: Breeder Slimes, 1 mated pair, 287 gold.", category: Misc}

awards:
  citizen: {id: 401, text: "Received Vertigo's Outstanding Citizenship Award", sort: 2}

items:                       # A2's item keys this quest gives, takes or needs (A2 makes the rows)
  warehouse_key: "the key under the rain barrel; opens XD-01"
  joes_invoice: "Joe's invoice, from the crate in XD-01"

npcs:
  4003:                      # Mayor Gunther
    topics:
      - n: 1                 # topic id 40000 + 50*block + 1
        label: Pests
        show: {not: {qbit: m3.done}}            # optional; RegisterCanShowTopic
        states:              # the first state whose `when` holds answers; the last has no `when`
          - when: {qbit: done}
            text: "My favorite citizens, I'm always glad to see you."
          - when: {item: joes_invoice}
            text: "Thank you for cleaning up Vertigo and discovering Joe's treachery. ..."
            do: [{take: joes_invoice}, {set: done}, {xp: 1500}, {gold: 1000}, {award: citizen}, {set: m3.started}]
          - text: "Welcome to Vertigo. ..."
            do: [{set: started}]

hooks:                       # what the map lanes wire (§7)
  invoice_crate:
    map: XD-01
    where: "the crate in Joe's storeroom"
    sets: [joe_invoice_found]
    gives: [joes_invoice]
    text: "Inside the crate you find a piece of paper ..."
    once: true

riddles:                     # every password or riddle and who says the answer (README 2026-11-13)
  - {answer: laboratory, where: "XD-13 vault door", said_by: "Shangri-La, the hint NPC (XD-17)"}

rewards: {xp: 1500, gold: 1000}   # informative; the audit sums the `xp` effects itself
playthrough: "Talk to Gunther (Pests); take the key under the rain barrel; XD-01 crate; Gunther (Pests)."
```

A topic may **ask first** (`ask: {text, declined}`, Cyrano's sale, D-65): its click shows `text` with the buttons Yes
and No (`AskChoiceWithAnswerSteps`, rendered in NPC topics and house dialogue since merge point 28; nothing is shown
before it); Yes runs the states as usual, No shows `declined`. The quest stub's `answer:` step names the button. An NPC id a decision gave that A4's town files do not list yet
goes in the file's `pending_npc_ids: {id: why}`: the audit lists it as open, not an error.
A topic or state may say `repeatable: true` (Myra's roots): the audit then leaves its `xp` out of the act's budget. A hook, or a topic or hook state, that pays the other route of a choice (a party takes one) says
`alternative: true`: the audit counts only the route without it (Q-D16's throne, Q-D17's oath, Q-C26's second skull).
A qbit may say `pending: "<why>"` when its writer or reader is a place not built yet (a town mirror of a later act): the
audit then lists a missing writer or reader as open instead of an error. A4's town files count as writers and readers:
a mirror house's `mirror.qbit` is set by its event (`Xeen.useMirror`) and read by `Xeen.mirrorDestinations`, Town
Portal destinations and roster rows read their `qbit`.

### 4.1 References

A bare name (`done`) is the file's own qbit, autonote, award or hook; `m3.started` is another quest's (file stem, dot,
name). Items are A2's keys, or `engine:<id>`. NPCs are A4's numeric ids.

### 4.2 Conditions (`when`, `show`, a hook's `requires`)

| Form | True when |
| --- | --- |
| `{qbit: ref}` | the qbit is set |
| `{item: key}` | a party member carries the item |
| `{items: [key, n]}` | the party carries at least n of the item (`Xeen.itemCount`; Megacredits) |
| `{found: key}` | the party has ever held the item (`HasEverOwnedItem`, the engine's saved record of every gain; D-90 5). A quest condition about a find reads this, never a bit set when a chest opens (a chest opened and left full) |
| `{award: ref}` | the first member has the award |
| `{gold: n}` | the party has at least n gold |
| `{promotable: key}` | some member can take promotion `key` (`Xeen.Promotions`) |
| `{lua: "expr"}` | the Lua expression is true (an `xeen_common.lua` helper, e.g. `Xeen.isNight()`; `Xeen.onMap("Castle Blackfang")` (the map_stats name) for a person met on two maps, Ambrose's D6 and DD-14 topics, D-52) |
| `{not: c}`, `{all: [c, ...]}`, `{any: [c, ...]}` | as named |

### 4.3 Effects (`do`)

Run in order after the state's text is set.

| Effect | Lua |
| --- | --- |
| `{set: ref}`, `{clear: ref}` | `SetQBit`, `ClearQBit` |
| `{give: key}`, `{give: key, count: n}` | `AddValue(InventoryItem(id), id)` n times |
| `{take: key}`, `{take: key, count: n}` | `RemoveItem(id)` n times |
| `{xp: n}` | every member gains n (`evt.ForPlayer(Players.All)`) |
| `{gold: n}`, `{pay: n}` | party gold up or down |
| `{treasure: level}` | one random item of that treasure level (`evt.GiveItem(level, 0)`: type 0 is any item) |
| `{award: ref}` | every member gets the award |
| `{autonote: ref}` | `SetAutonote` |
| `{promote: key}` | `Xeen.promote(key)`: every eligible member (`xeen_common.lua`) |
| `{stat: personality, value: 5}` | every member's base statistic (might, intellect, personality, endurance, accuracy, speed, luck) |
| `{move_npc: [npc, house]}` | `evt.MoveNPC` (house 0: gone) |
| `{lua: "statement"}` | as written (a call into `xeen_common.lua`) |

## 5. An NPC file

`source/npcs/<map>.yml` (A3) carries the topics that belong to no quest but touch the story (original lines, the
court's plaques) and the street news. Same topic shape as a quest file, with its own block.

**Flavour files (A4, since 2026-11-20):** `source/npcs/flavour/<map>.yml` hold the flavour topics of NPCs with no
quest role (rumours, jokes, trade talk), in the same shape, with a block of 170–198. They only talk: a flavour file
may have `npcs:` topics (with `show:`/`when:` conditions that read qbits) and `news:`, but no `do:` effects, `hooks:`,
`qbits:`, `items:`, `autonotes:`, `awards:` or `books:`; the generator refuses them (any topic that sets, gives, pays,
moves or promotes is a quest topic, A3's). Their stems are `flavour_<map>`, so they never meet A3's `<map>.yml`.
Slots fill after the quest files' topics and A3's NPC files'.


```yaml
map: X1
block: 150
npcs:
  4024:                      # Old Thorne
    topics:
      - {n: 1, label: Money tree, text: "Some fool said money's now growing on trees. Ha!"}
news:                        # street lines: one npc_news row per entry
  - {id: 47550, text: "Sinners must repent.", who: "Plague Cult member", source: "xeen/aaze0028:17"}
```

A one-state topic may write `text:` directly instead of `states:`. `source/npcs/books.yml` (block 199) holds the
readable books and notes whose text is A3's: `books: {<A2 item key>: {title, paragraphs: [...]}}`; gen_quests writes
their `readable_items.txt` rows (A2's table, shared), once A2's item exists. Greetings are A4's (`npc_greet`, in the town
files); `ORIGINAL_LINES.md` lists the original lines A4 may use for them.

**Slots:** each NPC has six topic slots. The generator fills them in this order: the quest files' topics (by file:
main, side, promotion, ours; then `n`), then the NPC file's; `slot: k` pins a topic to slot k (0–5). More than six
topics on one NPC stops the build; topics that never show together can share a slot only through an explicit
`evt.SetNPCTopic` (avoid it: use `show:` instead).

## 6. What the generator writes

`tools/xeen/gen_quests.py` is a module of A2's driver (`build(ctx)`, `tools/xeen/build_world.py`, `xeenlib.py`).
Run `python3 tools/xeen/build_world.py` (`--check` to compare). It:

- reads every `source/quests/*.yml` and `source/npcs/*.yml`;
- resolves item keys through `ctx.shared['items']` (A2) and checks NPC ids against A4's town files;
- **skips a whole quest** (with a warning naming the missing key and its owner) when any of its items is not in
  A2's rows yet: a quest is generated complete or not at all, never with a stand-in;
- writes, with the engine tables' header rows:

| File | Rows |
| --- | --- |
| `npc_topic.txt` | topic id, label, 0, quest id, text id of the first state, NPC name, NPC id (column 6 must never read `teacher hint`) |
| `npc_topic_text.txt` | every state's and hook's text, by text id |
| `english/quests.txt` | one row per qbit with a journal line: id, line, quest id, `Xeen`, required (itself, or its `journal_while`), forbidden (its `until`), `A3` |
| `english/autonote.txt`, `english/awards.txt` | id, text, category or sort |
| `npc_news.txt` | street lines |

Every file is written, header-only when it has no rows (TABLES.md: a listed file that is missing stops the game).
| `events/common/xeen_quests.lua` | per topic a `RegisterGlobalEvent` (states as `if ... return end`, text through `NPCText(id, english)`) and a `RegisterCanShowTopic` for `show:`; the hook functions; `XeenQuests.qbits` (name → number); a `RegisterCanShowTopic` per A4 teacher offer that opens by qbit (`gen_towns.teacher_gates()`, e.g. Kalindra's Grandmaster offers at `m26.stage4`) |
| `data_tables/quest_hooks.yml` | the hook table (§7) |

- publishes `ctx.shared['npc_topics']` = `{npc id: [topic id per slot]}` for A4's `gen_towns.py` (columns 10–15 of
  `npc.txt`). **This needs `gen_quests` to run before `gen_towns`** (request to A2: driver order). Until then
  `gen_quests` warns that the slots were published too late.
- The driver's generated-file note is a `#` line; a `.lua` file needs `--` (request to A2: pick the comment by the
  file's extension). `gen_quests` starts the Lua with its own `--` header as well.

## 7. Hooks: what the map lanes wire

Every place on a map where a quest happens is a named hook, `<quest>.<name>` (`m2.invoice_crate`,
`q-c3.tiara_vault`). The map lane looks it up in `data_tables/quest_hooks.yml`:

```yaml
m2.invoice_crate:
  quest: M2
  map: XD-01
  where: the crate in Joe's storeroom
  sets: {joe_invoice_found: 110010}      # qbits the map's event sets (studio `sets: {qbit: ...}`)
  reads: {}                              # qbits the map's event tests (doors, wards, staged faces)
  gives: {joes_invoice: 12017}           # items the map gives
  needs: {}                              # items the map's event requires (keys)
  call: XeenQuests.hook("m2.invoice_crate")   # every hook (a map may call any; a door without a condition returns true)
  once: true
```

A hook may also say `map_gives: {megacredit: 5}`: items the map's own chest or monster holds, which the map lane
places (the hook gives nothing; the table lists them as `map_gives` with id and count, and the audit counts them as
given). The Megacredits of XD-06, XD-08 and XD-09 are placed this way.

A hook's `question:` is the line the map asks before it calls the hook (Yes calls it), or an `exit` preset's meaning;
the table lists it as `question`, and the map lane copies it (D7's hatches and scarab stalls, the planes' ways up).
Questions with more than Yes, or that a hook's state decides first, are asked by a `xeen_common.lua` helper the map
calls with its event id: `Xeen.genieLamp` (Q-D27's lamps), `Xeen.toll(key, group, ...)` (D7's tolls: a map variable,
the pair's hostility), `Xeen.merchantRiddle` (D7's typed riddles), `Xeen.pyramidNiche` and `Xeen.pharaohSafe` (DD-15's
niches and wall safe: they return true while the vault or safe is open, so the event opens it), `Xeen.vowelessBook` and
`Xeen.vowelessThrone` (DD-08's books and thrones) and `Xeen.tribbleDoor` (DD-26's password door: true while open, so the event opens the leaves), `Xeen.alamarSundial` (DD-17's dials: true when turned, so the event
sets the ring's slab; DD-17's load event calls `Xeen.alamarSundialsSync()` first). Gifts to every member present, once
per character, go through `Xeen.anyMemberLacks(bit)` and `Xeen.giveEachOnce(bit, value, amount)`.

A hook's text shows as a message box; `status: true` shows it on the status line instead, held by its length as the
studio's status lines (over 30 characters 2 seconds and one more per 15, at most 6). **Touch effects answer on the
status line (F13, the user, 2026-11-21):** a hook that gives a party effect itself (`stat:`, a `lua:` AddValue/SetValue
of a member's property, `Xeen.giveEachOnce`) or that a map event giving one calls (a shrine, well, fountain, statue,
throne, brew, scroll) says `status: true` (and `else_status`/`fail_status` for its other lines), as MM6–MM8's shrines
and fountains; `window: "<why>"` keeps a window only for a long text to read or a choice's answer (the Dragon's
visions, the vowelless books' riddles, Wardoz's and the genie's answers). `quests.py` refuses any other.
**Quest items are looted (F15, 2026-11-21):** an item a chest holds is the chest's item (`objects.yml` `items:`, the
sketch's `chest: {items}`) and the hook says `map_gives`; an item a monster carries is its `carries:` (corpse loot).
A hook the map calls after `OpenChest` shows nothing in a window (a window closes the chest) unless it is a note to
read (`m2.invoice_crate`). `else_status: true` shows a once hook's `else_text` on the status line (DD-26's drains: the source's plain "Drain"). A hook a map calls after an
`evt.MoveToMap` must use it: the map change drops a message box opened in the same event (either order), so the line
never appears (`m14.let_out`). `fail_status: true` does the same for the fail line, for a map that leaves the map
after a refusal (`q-c25.inner_door`'s `leave`, D-57 Q2, D-63).

**Sounds and voiced lines (D-38).** A topic state, a hook or a hook state may say `sound: <name>`: the generator plays
the sound by name with the text (`evt.PlaySoundName(name)`, AU's names in `devdocs/xeen/AUDIO.md`); `sound_once: <qbit>`
plays it only while that qbit is clear and sets it (the audit counts it as written and read). A hook's fail or else
path takes `fail_sound`/`fail_sound_once`, `else_sound`/`else_sound_once`. A voiced text carries `voice: {speaker,
line}` (a list when several speak; for a fail path `fail_voice`), the exact words AU records, and `locked: true`: the
voiced words are locked, and an edit to them means AU re-voices (say so in the report). The text always shows; the
voice may read only its opening sentences. Voiced so far: m5 (Burlock), m32 and m33 (Corak, Sheltem), m35 (Burlock, Lord
Xeen), m42 (the Dragon Pharaoh).

**Cinematics (D-56).** A hook may play its map's cinematic: `cinematic: {id: unification, done: ceremony, event: 49}`.
Its run ends with `evt.PlayCinematic("unification", <done event>)`, after its effects and text; the done event is a
global event `40000 + 50·block + event` (a topic number of the file's block that no topic takes; the generator checks)
that runs the file's hook `done` (`XeenQuests.hook("m42.ceremony")`), when the cinematic ends played out or skipped,
or at once on a map without it. The hook table lists `cinematic: {id, done_event, done_hook}` for the map lane's
`<stem>.cinematics.yml`; the done hook counts as wired. A voiced line the cinematic speaks is the cinematic's cue
(`cinematic_sound`, `cinematic_subtitles` in the hook, for the map lane), not the hook's `sound:`.

**Dungeon gating (D-89, the user's F17, 2026-11-22).** Every dungeon can be entered and cleared without a story item,
a quest bit or a conversation.
- A hook at a dungeon's outer door says `entrance: <dungeon key>`. It may carry `requires`/`needs` only when it is on
  `quests.py`'s sealed list (DESIGN_GATING_AND_IDENTITY.md 1.2's KEEP rows; a new seal needs a decider) and says
  `sealed: "<reason>"` and a `fail_text` that names where the key or the way in comes from. A way the dungeon opens from
  inside (a culvert, a shaft, a grate) says `gate: shortcut` and reads only bits that dungeon sets.
- A hook on a dungeon map with `requires`/`needs` says `gate:` `beat` (guards only its own beat: a story room, a
  service, a promotion), `puzzle` (answered in the same map or by a named answer-giver), `order` (after a boss),
  `faction` (one route opens it) or `shortcut`. A `beat` room holds no counted monster group and no chest but the beat's.
- No refusal moves the party: a door that says no leaves the party where it stands (XD-18's throw is gone).
- `quests.py` checks all of it, and scans the map Lua: an event that moves into a dungeon while testing a qbit, an item
  or a conditional hook directly must be on the sealed lists or be a shortcut the dungeon opens; a refusal branch with
  a MoveToMap to another map is an error. `quests.py --open` prints the sealed doors with their refusal lines.

**Finds, experience and deaths answer on the status line (D-90, 2026-11-22).** A hook that hands over an item
(`gives:`) or runs at a container holding one (`map_gives:`) is a find: its lines go to the status line by default (no
`status: true` needed), the MM6–MM8 way; `window: "<why>"` keeps a window only for a note to read (Joe's invoice). An
experience award at a touch site is a party effect (`status: true`, as a stat). A monster's death (a hook a map calls
beside `evt.CheckMonstersKilled`, or whose `where` says "'s death") says `status: true`; a window only with
`window: "<why>"` for a cinematic, a voiced line or a long story text that ends an act. A find behind a question
(a password, a riddle, a Yes) keeps the question; its answer goes on the status line. `quests.py` refuses any other
window. Real containers become chests holding the item (`map_gives`), and a bare item in the open a placed 3D ground
item; both are the map lanes' (`output/a3_s34/d90_finds.md` sorts the session-34 list).

The map lane either uses the numbers in its studio project (`qbits:`/`items:` tables) or calls `call` from a `lua:`
effect; when the studio learns a `hook:` word (A1, W5), it reads this table directly. `XeenQuests.hook(name)` returns
true when it ran, false when its `requires` failed or a `once` hook already ran (it then shows `else_text` if given).
`XeenQuests.can(name)` tests `requires` without running anything (for doors). A hook that a quest needs but no map
has wired is listed by `quests.py` as open.

## 8. Text

- WORLD_DESIGN §1's voice: short lines, deadpan, quest text one or two sentences. Journal lines are one sentence in the
  source's style ("The dwarf mines are still being over-run. Please help them.").
- Original MM4/MM5 lines may be quoted when short (README, 2026-11-14); each quoted line goes in
  `devdocs/xeen/ORIGINAL_LINES.md` with its `aaze` reference. Double spaces after full stops are removed.
- English only, whole sentences (no joined pieces): the Lua passes each text as one literal, so language packs match
  it (`devdocs/LOCALIZATION.md`).
- No riddle or password without an answer-giver in `riddles:`; the audit refuses one.
- Distances in game units.

## 9. The audit (`tools/xeen/quests.py`)

`python3 tools/xeen/quests.py` reads the quest and NPC files, the built maps' projects (`devdocs/xeen/briefs/*/L4/`,
their `qbits:` tables and every `qbit:` they test or set), A4's town files and MAPS §0, and reports:

- every qbit number unique and in range; every reference resolved; every block unique;
- every qbit has a writer (a topic, a hook, a map event, or a `xeen_common.lua` function that names it with
  `Xeen.qbit("...")` and calls `SetQBit`, as `Xeen.alamarSundial` for `m33.sundial_nine`) and a reader (a topic, a journal line, a hook, a map
  condition), and every built map's qbit is registered in some quest file;
- every item given has a use, every item taken or needed is given somewhere;
- an item taken or needed that only a `pending_npcs` topic gives (an NPC without an id yet) is listed as open, not an
  error;
- every hook's map exists in `maps.yml`, and once the map is built, that its project wires it: it calls the hook by name
  (`XeenQuests.hook("<name>")`, `XeenQuests.can`, `hook: <name>`) or names or uses the hook's qbits; a hook whose full
  name a `xeen_common.lua` helper calls (`Xeen.genieLamp`'s lamps and wishes) is wired wherever a map calls the helper;
- the main path solvable in order (`after:` chains from M1 to M42, both orders of Act V);
- quest experience per act against MAPS §0 (I 16.5k, II 83k, III 132k, IV 160k, V 209k, VI 210k, optional 70k per
  member), with each quest's share against the per-quest cap (QUESTS rules);
- riddles without an answer-giver; NPCs with more than six topics; NPC ids not in A4's files; topics of `outline`
  files (listed, not errors).

## 10. The stub run (`tools/xeen/quest_stub.py`)

`python3 tools/xeen/quest_stub.py [scenario.yml ...]` builds the tables in memory (the driver's modules, nothing
written) and plays each scenario in `tools/xeen/quest_stub/` (`act1.yml`, one per act) through the generated topics and
hooks in a stub Lua runtime: click topics by NPC id and label, call hooks, set what map events set, then expect qbits,
items, classes, experience and gold. It needs only a C compiler: Lua 5.4 is compiled once from the engine's own Lua
sources into `output/xeen_tools/lua`. Run it after every change to a quest file, with `quests.py`; the scenario format
is in the tool's docstring (`hour:` sets the time of day for `Xeen.isNight`; Food, Age, resistances and conditions
(`Insane`, `Afraid` ...) count like stats; topics of one
NPC that share a label, shown at different times, are clicked by whichever is shown). It proves the quest logic, not
the game: the playthrough segments do that.
