# Co-op multiplayer: the event sweep

A static audit of what every event command does when two or more players are in a co-op world. It is the reading
half of open item CO-47 ("the event sweep per world") and gives CO-50 its first facts. It was made on 2026-11-20 from
the working tree. Nothing was built, run or played for it.

The design it is measured against is [the architecture](MULTIPLAYER_LISTEN_SERVER_ARCHITECTURE.md), sections
"Scripts, quests and dialogue", "Map travel", "A downed player" and "Two players as built". The gaps it finds are not
yet rows in [the open items](MULTIPLAYER_OPEN_ITEMS.md); the list under "Engine changes" says which rows they would be.

The raw counts are in [multiplayer_event_sweep_counts.csv](multiplayer_event_sweep_counts.csv).

## The result in short

- **Player-triggered events are mostly right.** A click, a step on a trigger face, a dialogue topic and a house visit
  run for the player who did it. Quest bits, the journal, NPC and map state are the world's. Experience, gold and
  awards an event gives reach every player. Quest items lie in the world's pouch. Existing scenarios prove these
  commands.
- **Events with no acting player are the host's.** A timer, an on-load or on-leave event and a kill's hook run for
  the host's party at the host's place. MM6 to MM8 use this little. MM9's maps are written almost wholly as timers
  that ask where "the party" stands, so in MM9 a guest sets off no trigger box, no approach talk and no trap, and
  takes no damage from a hazard zone. This is the largest finding.
- **Six kinds of request land in the wrong game or in nobody's:** a typed or chosen answer to a question (a guest
  gets no prompt), a launch pad and a push (the host is thrown), the Dimension Door overlay (opens for the host),
  movies and cinematics (the host's only, known as CO-31), the return to the main menu, and the follower list.
- **"Quest item" is decided by price and kind, not by use.** 68 of the 302 items that scripts check or take are gear
  or have a price, so they stay in one player's bags: only that player passes the check, and a guest who leaves takes
  the item out of the world.
- **No co-op scenario runs in MM6 or MM9.** All 44 are MM8 but one (MM7).

## How the audit was done

1. **The engine side was read.** Every `evt.*` function is registered in `registerEventBindings`
   (`game/events/EventRuntime.cpp:10402`): 227 names. For each one the C++ handler was read for what it does to a
   party, to the map's state or to the campaign. The four variable commands (`Cmp`, `Add`, `Subtract`, `Set`) were
   read kind by kind in `getVariableValue`, `setVariableValue`, `addVariableValue` and `subtractVariableValue`
   (`EventRuntime.cpp:2367`, `2862`, `3653`, `4261`). The callers were read for which party an event is run for.
2. **The scripts were counted** with two small Python scripts (in the session's scratch folder, not kept): every
   `evt.Name(` call, every helper of `assets_dev/engine/scripts/common/event_support.lua` that wraps one
   (`IsQBitSet`, `AddValue`, `HasItem` ...), the variable kind of each variable command, and each world library's
   calls (`MM9.giveKey`, `MM7.CompletePromotion` ...). Text inside string literals and comment lines is not counted.
3. **Events were grouped by how they start:** legacy timers (`timers = {...}` in a map's metadata), native timers
   (`RegisterMapTimerEvent`), on-load and on-leave lists, hooks. For those, the calls that touch a party were listed.
4. **Item checks were matched against the item tables** with the engine's own rule for a quest item
   (`ItemRules::questItem`, `game/rules/ItemRules.cpp:351`).
5. **Hazards were confirmed by reading the scripts** named in the examples below. MMExtension's decompiled scripts
   were not needed for any of them.

**Worlds in the counts:** `G` is the shared `assets_dev/engine/events/Global*.lua` (the global events of MM6, MM7
and MM8 in one file), `6`, `7`, `8`, `9` are the worlds' own scripts (maps, `common/`, their global supplements),
`X` is Xeen and `M` is the MAW ruleset's scripts. Xeen is counted because it is mounted; it was not asked for and has
no play order here.

**What the audit can show:** which party, which place and which screen a command uses, from the code; how often
each command is used and where.

**What it cannot show:**

- **Whether a quest still works end to end.** A quest is many events; only single commands and single events were
  read. The play order below says where to look first.
- **What a guest's game shows.** The replica side (`game/coop/`) was read only where an event's outcome is sent.
- **Anything about balance.**
- **House services written in C++** (bank, training, temple, tavern, bounties, Arcomage) beyond the point where an
  event opens them. CO-30 already lists the house screens a guest cannot use.
- **Timing.** A hazard that needs two players to act in the same frame cannot be seen by reading.

**Line numbers** are those of the working tree on 2026-11-20. Other sessions were editing `GameApplication.cpp` and
`CoopSession.cpp` while this was written, so function names are given beside the numbers that matter.

**Read or inferred:** every statement under "What the engine does today" is read from the code at the place cited.
Statements about what a player then sees ("the guest is stuck", "the host is thrown") are inferences from that code
and are marked "inferred" where they carry a hazard. Nothing here was observed in a running game.

## Which party an event runs for

These rules were read from the code and decide most rows of the tables.

- **An event has one party.** The handlers take it from the execution context (`writableParty`,
  `EventRuntime.cpp:4964`). The scene passes the world's party (`OutdoorSceneRuntime::eventParty`,
  `game/scene/OutdoorSceneRuntime.cpp:239`; the same indoors, `IndoorSceneRuntime.cpp:1531`).
- **Inside another player's command the world's party is that player's** (`ActingPartyScope`,
  `game/gameplay/PlayerCommands.cpp:26`; `OutdoorWorldRuntime::swapActingParty`,
  `game/outdoor/OutdoorWorldRuntime.cpp:13339`). The party's place is then that player's body
  (`partyX`, `OutdoorWorldRuntime.cpp:23181`), and the conversation, messages, granted items and prompts of the
  event state are that player's (`swapTransientEventRuntimeState`, `EventRuntime.cpp:11114`).
- **A guest's click, step on a trigger face, dialogue choice and house action are such commands**
  (`PlayerCommands::activateWorldHit`, `touchPositionTrigger`, `dialogueAction`, `houseStockAction`). A guest's game
  reports three kinds of place trigger: an outdoor face, an indoor face, an indoor touch face
  (`ReplicaPositionTrigger`, `game/gameplay/GameplayRuntimeInterfaces.h:802`).
- **Everything else runs for the host.** Timers pass the host's party (`OutdoorWorldRuntime.cpp:17131-17141`,
  `IndoorSceneRuntime.cpp:1461-1470`); so do on-load and on-leave events and the hooks raised outside a command
  (a kill, `OutdoorSceneRuntime::processMonsterKilledEvents`, `:771`). The architecture says so too: "Map timers and
  load events have no acting player." What it does not say is what "the party" then means: today, the host.
- **`ForPlayer(All)` and `ForPlayer(Current)` are the one character** of that party. `Member1` to `Member4` select
  nobody (`resolveTargetMemberIndices`, `EventRuntime.cpp:543`).
- **Three things an event gives go to every player:** experience, gold and an award that is added
  (`EventRuntimeState::coopParties`, filled in `GameSession.cpp:894-907`; used at `EventRuntime.cpp:3768`, `3866`,
  `3949`). Nothing else does.
- **A move to another map** is a vote when the event asks first, and takes everyone at once when it does not
  (`luaMoveToMap` sets `forced`, `EventRuntime.cpp:7570`; `GameApplication::processPendingMapMove`,
  `GameApplication.cpp:17106`). A move inside the map moves the player whose command asked, and the host when
  nobody's did (`GameApplication.cpp:17282`).
- **Quest items** (worth nothing, and not gear, a bottle, a reagent or gold) lie in the campaign's quest pouch,
  which every party's item checks and removals read (`Party::inventoryItemCount`, `game/party/Party.cpp:6019`;
  `Party::removeItemFromMember`, `Party.cpp:6276`).

## The classes

- **a** shared world or campaign state, right for co-op.
- **b** the acting player's (the event's party's), by design and right. From a timer, an on-load event or a kill's
  hook this is the host; where scripts use the command that way the risk column says so.
- **c** applied to every player, right.
- **d** a hazard: wrong or surprising with several players.
- **e** not determined from the code.

| Class | Functions (of 227) | Used in scripts (of 184) | Variable rows (of 46) |
| --- | --- | --- | --- |
| a | 140 | 106 | 13 |
| b | 60 | 52 | 29 |
| c | 0 | 0 | 3 |
| d | 20 | 19 | 1 |
| e | 3 | 3 | 0 |
| by kind (`Cmp`, `Add`, `Subtract`, `Set`) | 4 | 4 | |

A class-b row with a risk is a command that is right when a player triggers it and a hazard when a timer does. Those
are counted as b; the ranked list below is the full count of what goes wrong.

## Variable kinds

Uses are calls of `evt.Cmp`, `Add`, `Subtract` and `Set` and of the helpers that wrap them, plus MM9's library
(`MM9.giveGold` and the like). Citations are in `game/events/EventRuntime.cpp` unless a file is named.

| Variable kind | Operation | G | 6 | 7 | 8 | 9 | X | M | Class | What the engine does today | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| QBits | Cmp, Add, Subtract | 1621 | 626 | 852 | 535 | 0 | 1384 | 131 | a | The campaign's quest bits (`EventRuntime.cpp:2741`, :4215, :4683). | none |
| AutoNote | Cmp, Add, Subtract | 316 | 79 | 70 | 36 | 0 | 89 | 2 | a | The campaign's autonotes (`EventRuntime.cpp:3793`). | none |
| History | Cmp, Add | 31 | 0 | 21 | 6 | 0 | 0 | 1 | a | The campaign's history entries (`EventRuntime.cpp:3814`). | none |
| Counter | Cmp, Set | 23 | 0 | 24 | 17 | 0 | 0 | 1 | a | The campaign's event variables: the game minute a counter was started (`EventRuntime.cpp:4166`, :3510). | none |
| MapVar | Cmp, Add, Subtract, Set | 30 | 1318 | 1218 | 529 | 0 | 880 | 10 | a | The map's variables (`EventRuntime.cpp:4061`, :3424). | none |
| Reputation | Add, Subtract | 56 | 3 | 1 | 0 | 0 | 0 | 0 | a | The map's reputation (`currentLocationReputation`, :4197). | none |
| NumBounties | Cmp | 1 | 0 | 1 | 0 | 0 | 0 | 0 | a | The campaign's event variables (`EventRuntime.cpp:2820`-2828), as are NumDeaths, PrisonTerms and the arena wins. | NumDeaths per world, not per character, is CO-34 |
| ArenaWins | Cmp | 1 | 0 | 1 | 0 | 0 | 0 | 0 | a | The campaign's event variables (`EventRuntime.cpp:2824`). | none |
| Unknown1 | Cmp | 0 | 0 | 2 | 0 | 0 | 0 | 0 | a | The campaign's event variables. | none |
| DayOfYear | Cmp | 0 | 592 | 0 | 0 | 0 | 0 | 0 | a | The calendar. | none |
| DayOfWeek | Cmp | 84 | 0 | 0 | 0 | 0 | 0 | 0 | a | The calendar. | none |
| Hour | Cmp, Add | 0 | 7 | 1 | 0 | 0 | 0 | 0 | a | The calendar. | none |
| MonthIs | Cmp | 0 | 13 | 0 | 0 | 0 | 0 | 0 | a | The calendar. | none |
| Experience | Add | 251 | 23 | 1 | 15 | 84 | 157 | 16 | c | The selected members of the event's party, and every member of every other player's party the same amount (`EventRuntime.cpp:3846`-3874). Subtract and Set touch the event's party only (`EventRuntime.cpp:4402`, :3062). | low: given again per player where the gate is a character's own (H11) |
| Gold | Add | 206 | 107 | 16 | 11 | 42 | 50 | 4 | c | A positive amount goes to every party (`EventRuntime.cpp:3941`-3956). | none (scenario) |
| Gold | Cmp, Subtract, Set | 69 | 55 | 21 | 7 | 18 | 28 | 2 | b | The event's party's gold (`EventRuntime.cpp:2523`, :4461, :3142). | none (scenario): the acting player pays |
| Awards | Add | 94 | 4 | 0 | 4 | 0 | 29 | 1 | c | The selected members, and every member of every other party (`EventRuntime.cpp:3740`-3779). | cosmetic: a promotion's award lands on characters it did not promote |
| Awards | Cmp | 84 | 16 | 5 | 2 | 0 | 8 | 0 | b | The event's party's members (`EventRuntime.cpp:2426`). | none |
| Inventory | Cmp | 269 | 97 | 31 | 70 | 0 | 103 | 8 | b | The event's party's bags, worn gear and cursor, plus the world's quest pouch (`EventRuntime.cpp:12029`; Party.cpp:6019). | medium (H2): 262 of 974 literal item checks name an item that is not a quest item |
| Inventory | Add | 253 | 110 | 284 | 55 | 0 | 120 | 9 | b | An item on the event's player's cursor (`EventRuntime.cpp:3666`). | low |
| Inventory | Subtract | 223 | 76 | 15 | 40 | 56 | 109 | 8 | b | Taken from the event's party or the world's quest pouch (`EventRuntime.cpp:4273`-4287). | medium (H2) |
| Food | Cmp, Add, Subtract, Set | 16 | 33 | 2 | 0 | 0 | 9 | 2 | b | The event's party's food (`EventRuntime.cpp:3720`). Food an event gives is not passed to the other players. | low: unlike gold, a food reward is the acting player's alone |
| GoldInBank | Cmp, Add, Set | 8 | 0 | 15 | 8 | 0 | 0 | 0 | b | The event's party's bank (`EventRuntime.cpp:3974`). | low: MM7's on-load `SetValue(BankGold, 0)` empties the host's bank only |
| Players(roster) | Cmp | 2 | 0 | 0 | 10 | 0 | 0 | 0 | b | Whether the event's party holds that roster member (`EventRuntime.cpp:2382`). | inherits the solo run: nobody joins a party (H12) |
| ClassId | Cmp, Set | 145 | 3 | 0 | 1 | 0 | 0 | 0 | b | The event's party's members (`EventRuntime.cpp:2459`, :3022). | low (H6): promotions reach the acting player only |
| SkillPoints | Add | 56 | 1 | 2 | 3 | 0 | 0 | 0 | b | The selected members of the event's party (`EventRuntime.cpp:4172`). | low (H6): a quest's skill points are the acting player's alone |
| BaseStat | Cmp, Add | 21 | 67 | 17 | 20 | 5 | 64 | 14 | b | The selected members of the event's party (`EventRuntime.cpp:3997`). | medium for one-time gifts to 'the party' (H6) |
| BaseResistance | Cmp, Add | 13 | 42 | 11 | 8 | 0 | 21 | 10 | b | As BaseStat. | as BaseStat |
| StatBonus | Cmp, Add, Subtract, Set | 2 | 35 | 25 | 6 | 1 | 29 | 0 | b | The selected members of the event's party (temporary bonuses). | none |
| ResistanceBonus | Cmp, Add, Set | 0 | 15 | 26 | 2 | 0 | 7 | 0 | b | As StatBonus. | none |
| ActualStat | Cmp | 86 | 12 | 0 | 0 | 2 | 7 | 0 | b | The selected member (`EventRuntime.cpp:2578`). | none: contests are per character |
| ArmorClassBonus | Cmp, Add, Subtract, Set | 0 | 4 | 2 | 0 | 0 | 4 | 0 | b | The selected members. | none |
| LevelBonus | Cmp, Set | 0 | 6 | 0 | 0 | 0 | 0 | 0 | b | The selected members. | none |
| BaseLevel | Cmp | 1 | 1 | 0 | 0 | 1 | 0 | 1 | b | The selected member. | none |
| Age | Add, Set | 0 | 10 | 1 | 0 | 0 | 2 | 0 | b | The selected members. | none |
| Skill | Cmp, Set | 42 | 3 | 2 | 11 | 0 | 4 | 0 | b | The selected member; a party-wide utility skill reads the event's party's best member (`EventRuntime.cpp:2666`). | low: a skill gate passes for its owner only |
| Condition | Cmp, Add, Subtract, Set | 37 | 35 | 37 | 4 | 9 | 20 | 0 | b | The selected members of the event's party (`EventRuntime.cpp:3675`, :3358). | medium from timers and on-load events: the host's only (H9) |
| MajorCondition | Set | 0 | 5 | 1 | 0 | 0 | 0 | 0 | b | Clears every condition of the selected members (`EventRuntime.cpp:3403`). | none |
| CurrentHealth | Cmp, Add, Subtract, Set | 0 | 23 | 4 | 2 | 2 | 9 | 0 | b | The selected members (`EventRuntime.cpp:3898`). | none |
| CurrentSpellPoints | Add | 0 | 7 | 2 | 2 | 1 | 4 | 0 | b | The selected members. | none |
| MaxHealth | Cmp, Add | 0 | 3 | 2 | 2 | 0 | 0 | 0 | b | The selected members. | none |
| MaxSpellPoints | Cmp, Add | 0 | 4 | 1 | 2 | 0 | 0 | 0 | b | The selected members. | none |
| PlayerBits | Cmp, Add, Subtract | 112 | 26 | 78 | 0 | 0 | 114 | 0 | b | The selected member's own bits (`EventRuntime.cpp:4097`). | low (H11) where a player bit gates experience or gold, which every player gets |
| Invisible | Cmp | 0 | 0 | 15 | 8 | 0 | 0 | 0 | b | The event's party's Invisibility buff (`EventRuntime.cpp:2830`). | none |
| IsFlying | Cmp | 0 | 6 | 1 | 0 | 0 | 0 | 0 | d | The event's party's Fly buff, then the host's own flight state (`partyIsFlyingForEventChecks`, OutdoorWorldRuntime.cpp:23285). | low: a guest's check reads whether the host is in the air |
| CircusPrises | Cmp | 2 | 0 | 0 | 0 | 0 | 0 | 0 | b | Counts three items in the event's party's bags (`EventRuntime.cpp:2449`). | low |

Not in the table: 43 calls with a raw selector of tag `0xEB` (MM6's reputation number, `AddValue(131307, 2)` and
the like, mostly in `Global.lua`). The engine has no kind for it: the value goes to the selected member's own event
variables or, with several members selected, to the map's (`EventRuntime.cpp:4237-4258`). It gates nothing that was
found. Eight more calls build their selector at run time and were not classified.

## Event functions used by the scripts

Uses include the helper that wraps the function and MM9's library call that ends in it. Sorted by total uses.

| Function | G | 6 | 7 | 8 | 9 | X | M | Class | What the engine does today | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `evt.SetDoorState` | 0 | 1139 | 1067 | 3474 | 1150 | 623 | 4 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:9783` | none |
| `evt.Cmp` | 1455 | 1771 | 1333 | 707 | 5 | 1514 | 96 | by kind | See the variable table. `EventRuntime.cpp:5126` | see the variable table |
| `evt.Add` | 1918 | 914 | 814 | 408 | 14 | 1167 | 107 | by kind | See the variable table. `EventRuntime.cpp:9127` | see the variable table |
| `evt.OpenChest` | 0 | 384 | 1614 | 1201 | 167 | 215 | 0 | b | The acting player's chest view; one player at a time per chest (`WaitingPlayerViews`). `EventRuntime.cpp:9592` | none for chests (two scenarios); MM9 loot props were not traced for a guest |
| `evt.SetMessage` | 2001 | 107 | 0 | 13 | 0 | 708 | 53 | b | The acting player's screen (PlayerCommands.cpp:109-124); the host's from a timer or an on-load event. `EventRuntime.cpp:10267` | low: narration from timers (MM9, Xeen, MAW) reaches the host only |
| `evt.StatusText` | 254 | 755 | 289 | 166 | 162 | 1026 | 49 | b | The acting player's screen (PlayerCommands.cpp:109-124); the host's from a timer or an on-load event. `EventRuntime.cpp:9570` | low: narration from timers (MM9, Xeen, MAW) reaches the host only |
| `evt.EnterHouse` | 0 | 1111 | 391 | 398 | 0 | 298 | 1 | b | Opens a conversation for the event's player (`pendingDialogueContext`, swapped per player by `swapTransientEventRuntimeState`, :11114). From a timer or an on-load event it opens for the host. `EventRuntime.cpp:7349` | medium in MM9, where approach talks come from timers (H1); house screens a guest cannot use are CO-30 |
| `evt.Set` | 134 | 605 | 504 | 191 | 4 | 405 | 1 | by kind | See the variable table. `EventRuntime.cpp:9157` | see the variable table |
| `evt.Subtract` | 683 | 186 | 156 | 109 | 8 | 167 | 16 | by kind | See the variable table. `EventRuntime.cpp:9141` | see the variable table |
| `evt.NPCText` | 2 | 0 | 0 | 0 | 0 | 1272 | 0 | a | Reads the map, the calendar or a table. `EventRuntime.cpp:9039` | none |
| `evt.ForPlayer` | 553 | 139 | 99 | 81 | 17 | 190 | 51 | b | Selects members of the event's party (`resolveTargetMemberIndices`, :543). All and Current are the one character; Member1 to Member4 select nobody in a party of one. `EventRuntime.cpp:5114` | low: rewards written for Member1-4 reach nobody (47 uses of Member0, 4 of the others) |
| `evt.SetFacetBit` | 0 | 43 | 92 | 245 | 57 | 458 | 1 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:10135` | none |
| `evt.SimpleMessage` | 0 | 20 | 7 | 0 | 79 | 734 | 10 | b | The acting player's screen (PlayerCommands.cpp:109-124); the host's from a timer or an on-load event. `EventRuntime.cpp:10300` | low: narration from timers (MM9, Xeen, MAW) reaches the host only |
| `evt.SetNPCTopic` | 622 | 25 | 68 | 74 | 0 | 0 | 14 | a | Changes or reads the campaign's state (`Party::campaign()`), one for all players. `EventRuntime.cpp:10234` | none |
| `evt.MoveToMap` | 3 | 219 | 291 | 156 | 11 | 97 | 4 | d | Three cases (`GameApplication::processPendingMapMove`, GameApplication.cpp:17106). To another map with a text or picture, or out of a dungeon to an outdoor map: a dialogue, then the players' vote. To another map with neither: `forced`, everyone is moved at once. Inside the map: only the player whose command ran the event; with no acting player, the host. `EventRuntime.cpp:7448` | medium (H5): many ordinary doors are forced moves; a same-map move from a timer, hook or on-load event moves the host alone |
| `evt.SetMonGroupBit` | 4 | 8 | 457 | 165 | 49 | 86 | 6 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:10200` | none |
| `evt.SetTexture` | 0 | 249 | 112 | 178 | 0 | 164 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:10020` | none |
| `evt.SetLight` | 0 | 316 | 8 | 146 | 23 | 179 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:10064` | none |
| `evt.SetSprite` | 0 | 136 | 272 | 11 | 81 | 18 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7322` | none |
| `evt.PlaySoundName` | 0 | 0 | 0 | 0 | 501 | 0 | 0 | a | A sound placed in the world is everyone's; a plain one is the acting player's (PlayerCommands.cpp:134-139). `EventRuntime.cpp:6626` | cosmetic |
| `evt.CastSpell` | 24 | 137 | 131 | 167 | 0 | 4 | 1 | b | A buff goes to the event's party alone (`tryApplyEventSpellBuffs`, OutdoorWorldRuntime.cpp:23722); a missile is the world's, and one aimed at (0,0,0) flies at the acting player's place, the host's from a timer. `EventRuntime.cpp:7577` | low: a pedestal buffs the player who touched it; trap spells from timers aim at the host |
| `evt.SummonMonsters` | 0 | 295 | 31 | 96 | 0 | 3 | 1 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:9173` | none |
| `evt.GiveItem` | 77 | 45 | 23 | 76 | 46 | 61 | 2 | b | The event's party's cursor or bags (`grantedItemIds`, handed over by `applyGrantedEventItemsToHeldInventory`, GameplayHeldItemController.cpp:145). A quest item goes to the world's pouch when it is put into a bag. `EventRuntime.cpp:9696` | low: an item given by an on-load event or a timer is the host's |
| `evt._RandomJump` | 55 | 49 | 155 | 65 | 0 | 0 | 4 | a | Script flow only; the random jump is the map state's sequence. `EventRuntime.cpp:6802` | none |
| `evt.OpenMm9Rude` | 0 | 0 | 0 | 0 | 274 | 0 | 0 | b | Opens a conversation for the event's player (`pendingDialogueContext`, swapped per player by `swapTransientEventRuntimeState`, :11114). From a timer or an on-load event it opens for the host. `EventRuntime.cpp:7378` | medium in MM9, where approach talks come from timers (H1); house screens a guest cannot use are CO-30 |
| `evt.SetMonsterRelation` | 0 | 0 | 2 | 0 | 48 | 209 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:9095` | none |
| `evt.SetQuestBit` | 0 | 0 | 0 | 0 | 255 | 0 | 0 | a | Changes or reads the campaign's state (`Party::campaign()`), one for all players. `EventRuntime.cpp:5168` | none |
| `evt.SetMapVar` | 0 | 4 | 6 | 2 | 118 | 56 | 20 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5955` | none |
| `evt.HasQuestBit` | 0 | 0 | 0 | 0 | 182 | 0 | 1 | a | Changes or reads the campaign's state (`Party::campaign()`), one for all players. `EventRuntime.cpp:5160` | none |
| `evt.GetMapVar` | 0 | 4 | 4 | 3 | 121 | 30 | 21 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5932` | none |
| `evt.DamagePlayer` | 0 | 121 | 21 | 0 | 20 | 17 | 0 | b | Hurts the event's party (:6889). From a timer that is the host's. `EventRuntime.cpp:6889` | medium (H9): timed hazards hurt the host alone |
| `evt.MoveNPC` | 58 | 19 | 44 | 39 | 0 | 11 | 4 | a | Changes or reads the campaign's state (`Party::campaign()`), one for all players. `EventRuntime.cpp:6786` | none |
| `evt.FaceAnimation` | 2 | 2 | 55 | 106 | 0 | 0 | 0 | b | Portrait and speech of the event's party. `EventRuntime.cpp:8113` | cosmetic |
| `evt.StartTimer` | 0 | 0 | 0 | 0 | 162 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7611` | none |
| `evt._BeginCanShowTopic` | 157 | 0 | 0 | 0 | 0 | 0 | 0 | a | Script flow only; the random jump is the map state's sequence. `EventRuntime.cpp:5044` | none |
| `evt.CheckMonstersKilled` | 3 | 0 | 25 | 67 | 19 | 36 | 4 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:8995` | none |
| `evt.SpeakNPC` | 0 | 23 | 76 | 27 | 0 | 17 | 0 | b | Opens a conversation for the event's player (`pendingDialogueContext`, swapped per player by `swapTransientEventRuntimeState`, :11114). From a timer or an on-load event it opens for the host. `EventRuntime.cpp:7366` | medium in MM9, where approach talks come from timers (H1); house screens a guest cannot use are CO-30 |
| `evt.SetNPCGroupNews` | 48 | 0 | 0 | 93 | 0 | 0 | 0 | a | Changes or reads the campaign's state (`Party::campaign()`), one for all players. `EventRuntime.cpp:10251` | none |
| `evt.SetNPCGreeting` | 78 | 0 | 37 | 24 | 0 | 0 | 1 | a | Changes or reads the campaign's state (`Party::campaign()`), one for all players. `EventRuntime.cpp:7977` | none |
| `evt.PlaySound` | 0 | 11 | 13 | 98 | 0 | 10 | 0 | a | A sound placed in the world is everyone's; a plain one is the acting player's (PlayerCommands.cpp:134-139). `EventRuntime.cpp:6606` | cosmetic |
| `evt.CheckSeason` | 0 | 0 | 130 | 0 | 0 | 0 | 0 | a | Reads the map, the calendar or a table. `EventRuntime.cpp:8160` | none |
| `evt.DestroyDestructible` | 0 | 0 | 0 | 0 | 26 | 96 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7287` | none |
| `evt.GetPartyMemberCount` | 65 | 15 | 6 | 2 | 4 | 6 | 2 | b | The event's party: one member in co-op. `EventRuntime.cpp:6129` | low: a loop over 'the party' never reaches the other players (promotions, H6) |
| `evt.DamageDestructible` | 0 | 0 | 0 | 0 | 64 | 33 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7278` | none |
| `evt.ChangeEvent` | 86 | 1 | 0 | 0 | 0 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:9461` | none |
| `evt.AskQuestion` | 3 | 27 | 0 | 0 | 0 | 55 | 0 | d | The prompt is kept in the acting player's part of the event state on the host (`pendingInputPrompt`, :11114); the message a guest's game is sent carries the conversation but no prompt (`CoopSession::hostSendOutcome`, CoopSession.cpp:2278), and no command carries a typed answer (CoopProtocol.h:96-116). `EventRuntime.cpp:8751` | high for a guest (H3): no way to answer |
| `evt.GetPartyPosition` | 0 | 0 | 5 | 0 | 70 | 2 | 7 | b | The acting player's place inside a command, else the host's (`partyX`, OutdoorWorldRuntime.cpp:23181). `EventRuntime.cpp:5224` | high in MM9 and MAW map scripts, which poll it from timers (H1) |
| `evt._PressAnyKey` | 1 | 78 | 0 | 0 | 0 | 0 | 0 | b | The acting player's screen (PlayerCommands.cpp:109-124); the host's from a timer or an on-load event. `EventRuntime.cpp:8914` | low: narration from timers (MM9, Xeen, MAW) reaches the host only |
| `evt.ClearQuestBit` | 0 | 0 | 0 | 0 | 77 | 0 | 0 | a | Changes or reads the campaign's state (`Party::campaign()`), one for all players. `EventRuntime.cpp:5210` | none |
| `evt.SearchLootProp` | 0 | 0 | 0 | 0 | 77 | 0 | 0 | b | The acting player's chest view; one player at a time per chest (`WaitingPlayerViews`). `EventRuntime.cpp:9620` | none for chests (two scenarios); MM9 loot props were not traced for a guest |
| `evt.StopTimer` | 0 | 0 | 0 | 0 | 71 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7601` | none |
| `evt.PlayActorClip` | 0 | 0 | 0 | 0 | 68 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7148` | none |
| `evt.CurrentGameMinutes` | 0 | 4 | 7 | 3 | 41 | 1 | 8 | a | Reads the map, the calendar or a table. `EventRuntime.cpp:8387` | none |
| `evt.HasItemAnywhere` | 0 | 1 | 5 | 0 | 53 | 0 | 0 | b | The event's party's bags and worn gear, the cursor, and the world's quest pouch (Party.cpp:6019-6100). `EventRuntime.cpp:5152` | medium for items that are not quest items (H2) |
| `evt.CheckSkill` | 0 | 22 | 3 | 0 | 34 | 0 | 0 | b | The event's party's members (:7807). `EventRuntime.cpp:7807` | low: a skill gate passes only for the player who has the skill |
| `evt.FaceExpression` | 0 | 51 | 0 | 0 | 0 | 0 | 0 | b | Portrait and speech of the event's party. `EventRuntime.cpp:7733` | cosmetic |
| `evt.SummonObject` | 0 | 45 | 0 | 0 | 0 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7949` | none |
| `evt.PlayCinematic` | 0 | 0 | 0 | 0 | 44 | 0 | 0 | d | Kept with the map's state and played by the host's game (PlayerCommands.cpp:126-161). `EventRuntime.cpp:7098` | known: CO-31, movies and cinematics play for the host only |
| `evt.SummonItem` | 5 | 0 | 0 | 38 | 0 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7857` | none |
| `evt.ShowMovie` | 6 | 10 | 11 | 10 | 2 | 0 | 1 | d | Kept with the map's state and played by the host's game (PlayerCommands.cpp:126-161). `EventRuntime.cpp:7085` | known: CO-31, movies and cinematics play for the host only |
| `evt.SetMonsterBit` | 0 | 0 | 0 | 1 | 39 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:10166` | none |
| `evt.SetMapActorPosition` | 0 | 0 | 0 | 0 | 34 | 1 | 1 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5274` | none |
| `evt.GetMapActorPosition` | 0 | 0 | 0 | 0 | 35 | 0 | 1 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5595` | none |
| `evt.SummonMonstersById` | 0 | 0 | 0 | 0 | 33 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:9292` | none |
| `evt.SpawnWorldEffect` | 0 | 0 | 0 | 0 | 32 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:6642` | none |
| `evt.FaceActorTo` | 0 | 0 | 0 | 0 | 32 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7187` | none |
| `evt.MoveActorTo` | 0 | 0 | 0 | 0 | 31 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5294` | none |
| `evt.PlayDecorationClip` | 0 | 0 | 0 | 0 | 28 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7658` | none |
| `evt.SetGlobalVar` | 0 | 1 | 2 | 2 | 2 | 0 | 20 | a | Changes or reads the campaign's state (`Party::campaign()`), one for all players. `EventRuntime.cpp:6002` | none |
| `evt.AddFollowerNpc` | 0 | 10 | 14 | 0 | 0 | 0 | 2 | d | The follower list is the map's event state (`hiredNpcFollowers`) plus the event's party's own list (:8287-8347). The map's list is rebuilt from the host's party at every map load (`Party::applyGlobalNpcStateTo`, Party.cpp:5244). `EventRuntime.cpp:8287` | medium (H8): an escort a guest took on is forgotten at the next map; one the host took on is not cleared by a guest's turn-in |
| `evt.CameraShake` | 0 | 0 | 0 | 0 | 4 | 21 | 0 | e | The request lies in the per-player part of the event state; whether a guest's game is told was not traced. `EventRuntime.cpp:7228` | cosmetic |
| `evt.RandomBetween` | 1 | 0 | 0 | 0 | 17 | 5 | 0 | a | Script flow only; the random jump is the map state's sequence. `EventRuntime.cpp:6837` | none |
| `evt.StopActorMove` | 0 | 0 | 0 | 0 | 22 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5341` | none |
| `evt.SpawnLootContainer` | 0 | 0 | 0 | 0 | 22 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:9631` | none |
| `evt.RemoveItems` | 18 | 0 | 0 | 2 | 0 | 0 | 1 | b | Takes from the event's party's bags and from the world's quest pouch (Party.cpp:6276, 4343). `EventRuntime.cpp:9759` | medium for items that are not quest items (H2) |
| `evt.SetActorImmobile` | 0 | 0 | 0 | 0 | 20 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5392` | none |
| `evt.CheckItemsCount` | 18 | 0 | 0 | 2 | 0 | 0 | 0 | b | The event's party's bags and worn gear, the cursor, and the world's quest pouch (Party.cpp:6019-6100). `EventRuntime.cpp:7767` | medium for items that are not quest items (H2) |
| `evt.ClearActorPresentation` | 0 | 0 | 0 | 0 | 19 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7216` | none |
| `evt.ActorSeesParty` | 0 | 0 | 0 | 0 | 16 | 0 | 0 | d | Measured to the host's place when called from a timer (the only way the scripts call them). `EventRuntime.cpp:5542` | high in MM9 (H1) |
| `evt.FireMissile` | 0 | 0 | 0 | 0 | 16 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7701` | none |
| `evt.SummonRandomItem` | 0 | 0 | 0 | 16 | 0 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7880` | none |
| `evt.RemoveFollowerNpc` | 0 | 4 | 11 | 0 | 0 | 0 | 1 | d | The follower list is the map's event state (`hiredNpcFollowers`) plus the event's party's own list (:8287-8347). The map's list is rebuilt from the host's party at every map load (`Party::applyGlobalNpcStateTo`, Party.cpp:5244). `EventRuntime.cpp:8349` | medium (H8): an escort a guest took on is forgotten at the next map; one the host took on is not cleared by a guest's turn-in |
| `evt.SetPlayerClass` | 0 | 1 | 1 | 0 | 13 | 1 | 0 | b | The event's party's member (`Party::setMemberClassName`). `EventRuntime.cpp:8552` | low: a promotion reaches the acting player only; the plan says every connected character that qualifies (H6) |
| `evt.Beam` | 0 | 0 | 0 | 0 | 15 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:6696` | none |
| `evt.WakeActor` | 0 | 0 | 0 | 0 | 14 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5574` | none |
| `evt.GetCurrentPlayerIndex` | 0 | 3 | 0 | 0 | 10 | 0 | 0 | b | The event's party: one member in co-op. `EventRuntime.cpp:6136` | low: a loop over 'the party' never reaches the other players (promotions, H6) |
| `evt.RulesetInfo` | 0 | 0 | 0 | 0 | 0 | 0 | 12 | a | Reads the map, the calendar or a table. `EventRuntime.cpp:9492` | none |
| `evt.GetGlobalVar` | 0 | 1 | 2 | 2 | 1 | 0 | 5 | a | Changes or reads the campaign's state (`Party::campaign()`), one for all players. `EventRuntime.cpp:5979` | none |
| `evt.ApplyPartyPrimaryStatBuff` | 0 | 0 | 0 | 0 | 11 | 0 | 0 | b | The event's party's member. `EventRuntime.cpp:9683` | none |
| `evt.GivePartyMemberItem` | 0 | 1 | 0 | 0 | 9 | 0 | 0 | b | The event's party's cursor or bags (`grantedItemIds`, handed over by `applyGrantedEventItemsToHeldInventory`, GameplayHeldItemController.cpp:145). A quest item goes to the world's pouch when it is put into a bag. `EventRuntime.cpp:6213` | low: an item given by an on-load event or a timer is the host's |
| `evt.SkipCinematic` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | d | Kept with the map's state and played by the host's game (PlayerCommands.cpp:126-161). `EventRuntime.cpp:7115` | known: CO-31, movies and cinematics play for the host only |
| `evt.GetPlayerClass` | 0 | 5 | 3 | 2 | 0 | 0 | 0 | b | The event's party's member. `EventRuntime.cpp:8526` | none |
| `evt.SpinMover` | 0 | 0 | 0 | 0 | 9 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:9843` | none |
| `evt.SetChestBit` | 0 | 0 | 9 | 0 | 0 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:8169` | none |
| `evt.AskChoiceWithAnswerSteps` | 0 | 0 | 0 | 0 | 0 | 8 | 0 | d | The prompt is kept in the acting player's part of the event state on the host (`pendingInputPrompt`, :11114); the message a guest's game is sent carries the conversation but no prompt (`CoopSession::hostSendOutcome`, CoopSession.cpp:2278), and no command carries a typed answer (CoopProtocol.h:96-116). `EventRuntime.cpp:8908` | high for a guest (H3): no way to answer |
| `evt._SpecialJump` | 0 | 0 | 0 | 8 | 0 | 0 | 0 | d | Always the host's own body: `m_pPartyRuntime->requestSpecialJump` and `requestDash` with no check for an acting player (OutdoorWorldRuntime.cpp:23331, 7876; IndoorWorldRuntime.cpp:16215, 15446). `EventRuntime.cpp:8928` | medium (H4): a guest on a launch pad launches the host |
| `evt.IsDestructibleDestroyed` | 0 | 0 | 0 | 0 | 8 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7306` | none |
| `evt.HasFollowerNpc` | 0 | 4 | 1 | 0 | 0 | 0 | 3 | d | The follower list is the map's event state (`hiredNpcFollowers`) plus the event's party's own list (:8287-8347). The map's list is rebuilt from the host's party at every map load (`Party::applyGlobalNpcStateTo`, Party.cpp:5244). `EventRuntime.cpp:8264` | medium (H8): an escort a guest took on is forgotten at the next map; one the host took on is not cleared by a guest's turn-in |
| `evt._IsNpcInParty` | 0 | 0 | 0 | 7 | 0 | 0 | 0 | b | The event's party's roster members (:1666). `EventRuntime.cpp:8987` | inherits the solo run's roster gates (H12) |
| `evt.OpenDimensionDoor` | 0 | 2 | 2 | 2 | 1 | 0 | 0 | d | Sets `pendingDimensionDoorOverlay`, which is not among the per-player requests (:11114) and is taken by the host's game (`GameApplication::processPendingDimensionDoorOverlay`, GameApplication.cpp:17845). `EventRuntime.cpp:7055` | medium (H4): a guest's click opens the overlay on the host's screen |
| `evt.SetMonsterItem` | 0 | 0 | 6 | 0 | 1 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:8074` | none |
| `evt.SetActorTarget` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | a | The actor's target; "party" hands it to the AI, which picks the nearest party at every step (`assignActorPartyPlayers`). `EventRuntime.cpp:5363` | none |
| `evt.SetActorRoutine` | 0 | 0 | 0 | 0 | 5 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5408` | none |
| `evt.SetHeldItem` | 0 | 0 | 2 | 0 | 0 | 3 | 0 | b | The event's party's cursor or bags (`grantedItemIds`, handed over by `applyGrantedEventItemsToHeldInventory`, GameplayHeldItemController.cpp:145). A quest item goes to the world's pouch when it is put into a bag. `EventRuntime.cpp:6043` | low: an item given by an on-load event or a timer is the host's |
| `evt.PartyMemberHasItem` | 1 | 0 | 2 | 1 | 1 | 0 | 0 | b | The event's party's bags and worn gear, the cursor, and the world's quest pouch (Party.cpp:6019-6100). `EventRuntime.cpp:6179` | medium for items that are not quest items (H2) |
| `evt.RemovePartyMemberItem` | 1 | 0 | 1 | 1 | 1 | 1 | 0 | b | Takes from the event's party's bags and from the world's quest pouch (Party.cpp:6276, 4343). `EventRuntime.cpp:6333` | medium for items that are not quest items (H2) |
| `evt.SetNPCItem` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | a | Changes or reads the campaign's state (`Party::campaign()`), one for all players. `EventRuntime.cpp:8057` | none |
| `evt.SetPartyVariable` | 0 | 5 | 0 | 0 | 0 | 0 | 0 | a | Changes or reads the campaign's state (`Party::campaign()`), one for all players. `EventRuntime.cpp:8495` | none |
| `evt.StopDoor` | 0 | 0 | 0 | 4 | 1 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:9987` | none |
| `evt.WakeGroup` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5579` | none |
| `evt.IsMapActorWithinPartyDistance` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | d | Measured to the host's place when called from a timer (the only way the scripts call them). `EventRuntime.cpp:5674` | high in MM9 (H1) |
| `evt.PartyMemberItemCount` | 0 | 0 | 1 | 0 | 0 | 3 | 0 | b | The event's party's bags and worn gear, the cursor, and the world's quest pouch (Party.cpp:6019-6100). `EventRuntime.cpp:6203` | medium for items that are not quest items (H2) |
| `evt.SetHookBlocked` | 0 | 0 | 4 | 0 | 0 | 0 | 0 | a | Answers the hook that is running. A hook runs for the world's party at that moment: the acting player's inside a command, the host's for kills and damage, which are dispatched after the fight step (`OutdoorSceneRuntime::executeEventHooks`, `processMonsterKilledEvents`, OutdoorSceneRuntime.cpp:753, 771). `EventRuntime.cpp:6543` | low: a kill's hook reads the host's bags whoever made the kill |
| `evt.SetHookDamage` | 0 | 1 | 0 | 0 | 3 | 0 | 0 | a | Answers the hook that is running. A hook runs for the world's party at that moment: the acting player's inside a command, the host's for kills and damage, which are dispatched after the fight step (`OutdoorSceneRuntime::executeEventHooks`, `processMonsterKilledEvents`, OutdoorSceneRuntime.cpp:753, 771). `EventRuntime.cpp:6530` | low: a kill's hook reads the host's bags whoever made the kill |
| `evt.SetSnow` | 0 | 4 | 0 | 0 | 0 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:6922` | none |
| `evt.CountItems` | 0 | 0 | 0 | 0 | 0 | 0 | 4 | b | The event's party's bags and worn gear, the cursor, and the world's quest pouch (Party.cpp:6019-6100). `EventRuntime.cpp:7796` | medium for items that are not quest items (H2) |
| `evt.AskQuestionWithAnswerSteps` | 0 | 2 | 0 | 0 | 0 | 0 | 1 | d | The prompt is kept in the acting player's part of the event state on the host (`pendingInputPrompt`, :11114); the message a guest's game is sent carries the conversation but no prompt (`CoopSession::hostSendOutcome`, CoopSession.cpp:2278), and no command carries a typed answer (CoopProtocol.h:96-116). `EventRuntime.cpp:8902` | high for a guest (H3): no way to answer |
| `evt.IsActorMoving` | 0 | 0 | 0 | 0 | 3 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5351` | none |
| `evt.AttachActorItem` | 0 | 0 | 0 | 0 | 3 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5422` | none |
| `evt.DetachActorItem` | 0 | 0 | 0 | 0 | 3 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5436` | none |
| `evt.IsMapActorHostile` | 0 | 0 | 0 | 0 | 2 | 1 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5650` | none |
| `evt.IsMapActorDead` | 0 | 0 | 0 | 0 | 1 | 1 | 1 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5663` | none |
| `evt.SetOutdoorSky` | 0 | 1 | 0 | 0 | 0 | 2 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:6946` | none |
| `evt.MoveDecoration` | 0 | 0 | 0 | 0 | 3 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7128` | none |
| `evt.SetMist` | 0 | 0 | 0 | 0 | 0 | 3 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7037` | none |
| `evt.AimDecoration` | 0 | 0 | 0 | 0 | 3 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7623` | none |
| `evt.AddMm9Hireling` | 0 | 0 | 0 | 0 | 3 | 0 | 0 | b | The event's party's hirelings (each player's own by the co-op rules). `EventRuntime.cpp:7428` | low: a story hireling joins or leaves the acting player's party only, while its keys are the world's |
| `evt.RemoveMm9Hireling` | 0 | 0 | 0 | 0 | 3 | 0 | 0 | b | The event's party's hirelings (each player's own by the co-op rules). `EventRuntime.cpp:7438` | low: a story hireling joins or leaves the acting player's party only, while its keys are the world's |
| `evt.RulesTopic` | 0 | 0 | 0 | 0 | 0 | 0 | 3 | b | The rules of the event's party (MAW). `EventRuntime.cpp:9529` | not determined for MAW's rifts and arena waves (see 'Not determined') |
| `evt.GetPartyVariable` | 0 | 3 | 0 | 0 | 0 | 0 | 0 | a | Changes or reads the campaign's state (`Party::campaign()`), one for all players. `EventRuntime.cpp:8487` | none |
| `evt.GetPlayerClassName` | 0 | 0 | 0 | 0 | 2 | 1 | 0 | b | The event's party's member. `EventRuntime.cpp:8543` | none |
| `evt.IsTotalBountyInRange` | 3 | 0 | 0 | 0 | 0 | 0 | 0 | a | Changes or reads the campaign's state (`Party::campaign()`), one for all players. `EventRuntime.cpp:8975` | none |
| `evt.Debug` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | a | Script flow only; the random jump is the map state's sequence. `EventRuntime.cpp:5076` | none |
| `evt.HasEverOwnedItem` | 0 | 2 | 0 | 0 | 0 | 0 | 0 | b | The event's party's own memory of items it held (`Party::hasEverOwnedItem`, Party.cpp:6130). `EventRuntime.cpp:5144` | low: a lost-item topic says 'You never had it' to the player who never held it (H13) |
| `evt.GetEnemyDetectorState` | 0 | 0 | 2 | 0 | 0 | 0 | 0 | e | Reads each monster's state toward 'the party' (`hostileToParty`, `hasDetectedParty`); which party those flags mean with several players was not traced. `EventRuntime.cpp:5236` | low (2 uses, MM7) |
| `evt.KillMapActor` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5450` | none |
| `evt.TriggerActor` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5636` | none |
| `evt.GetCurrentScreen` | 0 | 0 | 2 | 0 | 0 | 0 | 0 | e | Reads the screen that is open; whose screen (the acting player's or the host's) was not traced. `EventRuntime.cpp:5687` | low (2 uses, MM7 Shoals) |
| `evt.SetTransportRouteOverride` | 0 | 0 | 2 | 0 | 0 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5880` | none |
| `evt.GetHeldItemId` | 0 | 0 | 1 | 0 | 0 | 1 | 0 | b | The event's party's cursor or bags (`grantedItemIds`, handed over by `applyGrantedEventItemsToHeldInventory`, GameplayHeldItemController.cpp:145). A quest item goes to the world's pouch when it is put into a bag. `EventRuntime.cpp:6026` | low: an item given by an on-load event or a timer is the host's |
| `evt.ApplyLichTransformation` | 0 | 0 | 1 | 0 | 1 | 0 | 0 | b | The event's party's member. `EventRuntime.cpp:6346` | none |
| `evt.GetHookContext` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | a | Reads the map, the calendar or a table. `EventRuntime.cpp:6470` | none |
| `evt.SetOutdoorModelFacetTexture` | 0 | 2 | 0 | 0 | 0 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:10038` | none |
| `evt.SetUnscaledExperience` | 0 | 0 | 0 | 0 | 0 | 0 | 2 | a | A flag on the map's event state for the next experience grants (MAW). `EventRuntime.cpp:9563` | none |
| `evt.SetNPCName` | 0 | 0 | 1 | 0 | 0 | 0 | 1 | a | Changes or reads the campaign's state (`Party::campaign()`), one for all players. `EventRuntime.cpp:7994` | none |
| `evt.ChangeGroupAlly` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:8152` | none |
| `evt.RemoveFollowerProfession` | 0 | 2 | 0 | 0 | 0 | 0 | 0 | d | The follower list is the map's event state (`hiredNpcFollowers`) plus the event's party's own list (:8287-8347). The map's list is rebuilt from the host's party at every map load (`Party::applyGlobalNpcStateTo`, Party.cpp:5244). `EventRuntime.cpp:8224` | medium (H8): an escort a guest took on is forgotten at the next map; one the host took on is not cleared by a guest's turn-in |
| `evt.AdvanceGameMinutes` | 0 | 0 | 1 | 0 | 1 | 0 | 0 | d | The calendar moves once; only the event's party's timed states are aged (:8398-8421). `EventRuntime.cpp:8398` | low (2 uses): the other players' buffs do not run out with the jump |
| `evt.GetPlayerSkill` | 0 | 2 | 0 | 0 | 0 | 0 | 0 | b | The event's party's member. `EventRuntime.cpp:8626` | none |
| `evt.SetPlayerSkill` | 0 | 2 | 0 | 0 | 0 | 0 | 0 | b | The event's party's member. `EventRuntime.cpp:8639` | none |
| `evt.QuestCompleteFeedback` | 0 | 0 | 0 | 1 | 0 | 0 | 0 | b | Portrait and speech of the event's party. `EventRuntime.cpp:5188` | cosmetic |
| `evt.SetMapActorHp` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5463` | none |
| `evt.SetRestAlarm` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | a | The map's rest alarm; resting is a vote. `EventRuntime.cpp:5328` | none |
| `evt.SetMm9ActorCanReceiveDamage` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5478` | none |
| `evt.GetCurrentContinent` | 0 | 0 | 0 | 1 | 0 | 0 | 0 | a | Reads the map, the calendar or a table. `EventRuntime.cpp:5707` | none |
| `evt.MoveToSavedLocation` | 0 | 0 | 1 | 0 | 0 | 0 | 0 | a | A named place in the map's event state; the save stores the acting player's place, the return is a map move that is not forced (a vote). `EventRuntime.cpp:5825` | low (1 use, MM7) |
| `evt.ClearHeldItem` | 0 | 0 | 1 | 0 | 0 | 0 | 0 | b | The event's party's cursor or bags (`grantedItemIds`, handed over by `applyGrantedEventItemsToHeldInventory`, GameplayHeldItemController.cpp:145). A quest item goes to the world's pouch when it is put into a bag. `EventRuntime.cpp:6111` | low: an item given by an on-load event or a timer is the host's |
| `evt.SetPartyMemberPortraitId` | 0 | 0 | 1 | 0 | 0 | 0 | 0 | b | The event's party's member. `EventRuntime.cpp:6159` | cosmetic (MM7 Shoals portraits, set on load: the host's only) |
| `evt.PartyMemberKnowsSpell` | 0 | 0 | 0 | 1 | 0 | 0 | 0 | b | The event's party's member. `EventRuntime.cpp:6313` | none |
| `evt.ForgetPartyMemberSpell` | 0 | 1 | 0 | 0 | 0 | 0 | 0 | b | The event's party's member. `EventRuntime.cpp:6323` | none |
| `evt.SkillResetCost` | 0 | 0 | 0 | 0 | 0 | 0 | 1 | b | The event's party's member. `EventRuntime.cpp:6356` | none |
| `evt.ResetSkills` | 0 | 0 | 0 | 0 | 0 | 0 | 1 | b | The event's party's member. `EventRuntime.cpp:6365` | none |
| `evt.PartyMemberHasEquippedItem` | 0 | 0 | 1 | 0 | 0 | 0 | 0 | b | The event's party's member. `EventRuntime.cpp:6412` | none |
| `evt.PartyMemberCanWearArmor` | 0 | 0 | 1 | 0 | 0 | 0 | 0 | b | The event's party's member. `EventRuntime.cpp:6462` | none |
| `evt.SetHookRestFoodCost` | 0 | 0 | 1 | 0 | 0 | 0 | 0 | a | Answers the hook that is running. A hook runs for the world's party at that moment: the acting player's inside a command, the host's for kills and damage, which are dispatched after the fight step (`OutdoorSceneRuntime::executeEventHooks`, `processMonsterKilledEvents`, OutdoorSceneRuntime.cpp:753, 771). `EventRuntime.cpp:6560` | low: a kill's hook reads the host's bags whoever made the kill |
| `evt.SetHookHouseTopics` | 0 | 0 | 1 | 0 | 0 | 0 | 0 | a | Answers the hook that is running. A hook runs for the world's party at that moment: the acting player's inside a command, the host's for kills and damage, which are dispatched after the fight step (`OutdoorSceneRuntime::executeEventHooks`, `processMonsterKilledEvents`, OutdoorSceneRuntime.cpp:753, 771). `EventRuntime.cpp:6573` | low: a kill's hook reads the host's bags whoever made the kill |
| `evt.PlaySoundOnce` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | a | A sound placed in the world is everyone's; a plain one is the acting player's (PlayerCommands.cpp:134-139). `EventRuntime.cpp:6616` | cosmetic |
| `evt.SpawnWorldModel` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:6764` | none |
| `evt.SetRain` | 0 | 1 | 0 | 0 | 0 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:6934` | none |
| `evt.SetOutdoorFog` | 0 | 1 | 0 | 0 | 0 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:6962` | none |
| `evt.ReturnToMainMenu` | 0 | 1 | 0 | 0 | 0 | 0 | 0 | d | `pendingReturnToMainMenu`, taken by the host's game (GameApplication.cpp:17833). `EventRuntime.cpp:7256` | medium (H10): the MM6 bad ending sends the host to the menu; what the guests see was not traced |
| `evt.SetFog` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:6986` | none |
| `evt.ClearFog` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7019` | none |
| `evt.ArenaMonster` | 0 | 0 | 0 | 0 | 0 | 0 | 1 | b | The rules of the event's party (MAW). `EventRuntime.cpp:9513` | not determined for MAW's rifts and arena waves (see 'Not determined') |
| `evt.SpawnActorEffect` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:6718` | none |
| `evt.StopActorEffect` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:6743` | none |
| `evt.IsHouseOpen` | 0 | 1 | 0 | 0 | 0 | 0 | 0 | a | Reads the map, the calendar or a table. `EventRuntime.cpp:9015` | none |
| `evt.GetNPCTopic` | 0 | 0 | 0 | 0 | 0 | 0 | 1 | a | Reads the map, the calendar or a table. `EventRuntime.cpp:9065` | none |
| `evt.EnsureChestItem` | 0 | 1 | 0 | 0 | 0 | 0 | 0 | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:8201` | none |
| `evt.RestAndHealParty` | 0 | 0 | 1 | 0 | 0 | 0 | 0 | d | Rests the event's party alone (:8426). `EventRuntime.cpp:8426` | low (1 use, MM7): the plan says a scripted rest is for everyone |
| `evt.GetActiveEventSpellId` | 0 | 0 | 0 | 1 | 0 | 0 | 0 | a | Reads the map, the calendar or a table. `EventRuntime.cpp:8480` | none |
| `evt.GetClassName` | 0 | 1 | 0 | 0 | 0 | 0 | 0 | a | Reads the map, the calendar or a table. `EventRuntime.cpp:8518` | none |
| `evt.CanPlayerLearnSkill` | 0 | 0 | 1 | 0 | 0 | 0 | 0 | b | The event's party's member. `EventRuntime.cpp:8605` | none |
| `evt.PushParty` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | d | Always the host's own body: `m_pPartyRuntime->requestSpecialJump` and `requestDash` with no check for an acting player (OutdoorWorldRuntime.cpp:23331, 7876; IndoorWorldRuntime.cpp:16215, 15446). `EventRuntime.cpp:8952` | medium (H4): a guest on a launch pad launches the host |

## Event functions no script uses

| Function | Class | What the engine does today | Risk |
| --- | --- | --- | --- |
| `evt.ApplyPartyBuff` | b | Gives the event's party a party buff by name (Hesper's Ember Skin: LavaWalk). Added 2026-11-25 (lane KI). | low: the other players' parties get none (as a party potion) |
| `evt.HasPartyBuff` | b | Reads the event's party's party buff by name. Added 2026-11-25 (lane KI). | none |
| `evt.BeamToParty` | b | A beam to the party's place: the acting player's, the host's from a timer. `EventRuntime.cpp:6701` | cosmetic (not used) |
| `evt.CanClassLearnSkill` | a | Reads the map, the calendar or a table. `EventRuntime.cpp:8587` | none |
| `evt.CanFitWorkshopMod` | b | The event's party's member. `EventRuntime.cpp:6394` | none |
| `evt.CanPlayerAct` | b | The event's party: one member in co-op. `EventRuntime.cpp:10316` | low: a loop over 'the party' never reaches the other players (promotions, H6) |
| `evt.ChangeGroupToGroup` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:8144` | none |
| `evt.ClearSavedLocation` | a | A named place in the map's event state; the save stores the acting player's place, the return is a map move that is not forced (a vote). `EventRuntime.cpp:5867` | low (1 use, MM7) |
| `evt.ClearTransportRouteOverride` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5918` | none |
| `evt.ConsumeWorldItem` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:9642` | none |
| `evt.DecorationAim` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7683` | none |
| `evt.FitWorkshopMod` | b | The event's party's member. `EventRuntime.cpp:6403` | none |
| `evt.GetClassId` | a | Reads the map, the calendar or a table. `EventRuntime.cpp:8509` | none |
| `evt.GetClassSkillCap` | a | Reads the map, the calendar or a table. `EventRuntime.cpp:8568` | none |
| `evt.GetCurrentMapName` | a | Reads the map, the calendar or a table. `EventRuntime.cpp:5698` | none |
| `evt.GetPartyMemberPortraitId` | b | The event's party's member. `EventRuntime.cpp:6150` | cosmetic (MM7 Shoals portraits, set on load: the host's only) |
| `evt.GetRuntimeVariable` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:8443` | none |
| `evt.HasSavedLocation` | a | A named place in the map's event state; the save stores the acting player's place, the return is a map move that is not forced (a vote). `EventRuntime.cpp:5815` | low (1 use, MM7) |
| `evt.Jump` | d | Always the host's own body: `m_pPartyRuntime->requestSpecialJump` and `requestDash` with no check for an acting player (OutdoorWorldRuntime.cpp:23331, 7876; IndoorWorldRuntime.cpp:16215, 15446). `EventRuntime.cpp:8943` | medium (H4): a guest on a launch pad launches the host |
| `evt.LineOfSight` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5524` | none |
| `evt.Question` | b | The acting player's screen (PlayerCommands.cpp:109-124); the host's from a timer or an on-load event. `EventRuntime.cpp:10347` | low: narration from timers (MM9, Xeen, MAW) reaches the host only |
| `evt.RecoilDecoration` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7641` | none |
| `evt.RefundChestArtifacts` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:10341` | none |
| `evt.RegisterOutdoorModelMechanism` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:9897` | none |
| `evt.ReplacePartyInventoryItems` | b | Takes from the event's party's bags and from the world's quest pouch (Party.cpp:6276, 4343). `EventRuntime.cpp:6244` | medium for items that are not quest items (H2) |
| `evt.SaveCurrentLocation` | a | A named place in the map's event state; the save stores the acting player's place, the return is a map move that is not forced (a vote). `EventRuntime.cpp:5793` | low (1 use, MM7) |
| `evt.SetActorBehavior` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5620` | none |
| `evt.SetDestructibleDamage` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7295` | none |
| `evt.SetFacetBitOutdoors` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:10135` | none |
| `evt.SetLocalMonsterRelation` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:9095` | none |
| `evt.SetMonsterGroup` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7969` | none |
| `evt.SetNPCPicture` | a | Changes or reads the campaign's state (`Party::campaign()`), one for all players. `EventRuntime.cpp:8015` | none |
| `evt.SetNPCProfession` | a | Changes or reads the campaign's state (`Party::campaign()`), one for all players. `EventRuntime.cpp:8036` | none |
| `evt.SetOutdoorModelMechanismState` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:9927` | none |
| `evt.SetPersistentItemMechanismState` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:9653` | none |
| `evt.SetPersistentItemMechanismVariant` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:9669` | none |
| `evt.SetRuntimeVariable` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:8459` | none |
| `evt.SetSectorAmbient` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:10104` | none |
| `evt.SetTextureOutdoors` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:10020` | none |
| `evt.SpendAction` | b | The event's party's member. `EventRuntime.cpp:7725` | none |
| `evt.StopBeam` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:6706` | none |
| `evt.SummonGold` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:7933` | none |
| `evt.TurnActor` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5584` | none |
| `evt.TurnGroup` | a | Changes or reads the map's state (the host's one world). `EventRuntime.cpp:5589` | none |
| `evt._BeginEvent` | a | Script flow only; the random jump is the map state's sequence. `EventRuntime.cpp:5022` | none |

## The worlds' own libraries

The hand-written libraries call the functions above; what matters is how.

| Library call | Uses | Ends in | Class | Note |
| --- | --- | --- | --- | --- |
| `MM9.hasKey`, `giveKey`, `takeKey` | 181, 253, 75 | quest bits 90000 + key | a | MM9's keys are the world's |
| `MM9.hasItem`, `giveItem`, `takeItem` | 51, 44, 54 | `HasItemAnywhere`, `GiveItem`, `RemoveItem` | b | MM9's raw item ids are mapped at load and were not matched against the quest item rule |
| `MM9.giveExperience`, `giveGold` | 82, 40 | `AddValue(Experience)`, `AddValue(Gold)` | c | every player |
| `MM9.hasGold`, `takeGold` | 7, 7 | the acting player's gold | b | |
| `MM9.openRude` | 272 | `evt.OpenMm9Rude` | b | from a click: the clicker's talk; from a poll: the host's (H1) |
| `MM9.promoteParty`, service event 49990 | 10 | `SetPlayerClass` over `PartyMembers()` | b | the acting player only; the promoter keeps "Promote our eligible characters." for the others (`mm9_common.lua:305-325`) |
| `MM9.useWell`, `useCauldron`, `useCookpot`, `useClover` | 9, 11, 7, 15 | attribute, resistance, item | d | a permanent well and a cauldron are spent by the first player and give to that player only (H6) |
| `MM9.addHireling`, `removeHireling` | 1, 1 | the acting player's hirelings | b | |
| `MM7.CompletePromotion` | 28 | `PromotePlayers` | b | later promotion of other players works and pays experience again (H11) |
| `MM7.AllPartyMembersHaveWetsuit`, `KillUnsuitedShoalsPartyMembers`, `LeaveShoalsIfAboveWater` | 2, 1, 1 | checks, death and the exit of the Shoals | d | the host's party and the host's depth (H7) |
| `MM6.AddQuestFollower`, `RemoveQuestFollower`, Nicolai's functions | 4, 3, 20 | `AddFollowerNpc`, `HasFollowerNpc` | d | H8 |

The counts are one less than the CSV's where the CSV also counts the function's own definition line.

## The hazards, ranked

Ranked by how likely an ordinary co-op play-through is to meet them, then by how bad the result is. "Read" is what
the code does; "inferred" is what follows for the players.

### H1. Events with no acting player see only the host (MM9 above all)

- **Read:** a timer event runs for the host's party (`OutdoorWorldRuntime.cpp:17131-17141`,
  `IndoorSceneRuntime.cpp:1461-1470`). `evt.GetPartyPosition`, `evt.ActorSeesParty` and
  `evt.IsMapActorWithinPartyDistance` measure to `partyX()`, which is another player's place only inside that
  player's command (`OutdoorWorldRuntime.cpp:23181`). `evt.DamagePlayer` hurts the event's party
  (`EventRuntime.cpp:6889`). MM9's own map exits are tested against the host's place only
  (`m_mm9PositionedTransitionRuntime.update`, `OutdoorSceneRuntime.cpp:502`, `IndoorSceneRuntime.cpp:712`).
- **How much:** MM9 has 250 `RegisterMapTimerEvent`, 70 `evt.GetPartyPosition` in 31 of its 44 maps, 16
  `evt.ActorSeesParty` and 20 `evt.DamagePlayer`, nearly all inside polls. MAW's map scripts poll the same way in
  five places (`7d24_maw.lua:6`, `7out02_maw.lua:6` and `:30`, `7out05_maw.lua:42`, `drangheimprison_maw.lua:28`).
- **Examples:**
  - Sturmford City, `sturmfordcity.lua:297-363`: the barks' boxes and the approach talks (`t.talk()` opens a
    dialogue) test the host's place every quarter second. A guest who walks up to the speaker gets no talk; when the
    host walks up, the talk opens for the host.
  - Chasm of the Dead, `chasmofthedead.lua:520-534`: the spike pit and the acid test the host's place, hurt the
    host's party and lift the host out (`evt.MoveToMap` inside the map). A guest in the acid is not hurt and is not
    lifted out.
  - Yanmir's Fort, `yanmirsfort.lua:392-395`: the fall through `EndOfWorld` moves everyone to Frosgard City, and
    only the host's fall triggers it.
  - Dark Passageway, `darkpassageway.lua:413-430`: the shaft exit and the flame damage, the same way.
- **With two players (inferred):** in MM9 only the host advances scripted places. A guest alone can be stuck in
  front of a trigger. Hazards do not hurt guests. The story still completes if the host walks everywhere.
- **Should be:** a box, a sight test and a hazard zone are tested for every player; the talk opens for the player
  who came near; the damage is that player's.

### H2. A quest item that is gear or has a price belongs to one player

- **Read:** only what `ItemRules::questItem` accepts goes to the world's pouch: value 0 and not a weapon, armour,
  ring, amulet, bottle, reagent or gold (`ItemRules.cpp:351-360`). Everything else an event gives lands on the
  acting player's cursor and stays in that player's bags.
- **How much:** scripts name 302 different items in `HasItem`, `RemoveItem` and `HasItemAnywhere`. 68 of them are
  not quest items by that rule: 262 of 974 call sites (shared global events 189, MM8 37, MM7 8, MM6 3, MAW 12,
  Xeen 13). The full list is easy to rebuild from the item table.
- **Examples:**
  - Lord Kilburn's Shield (2119, a shield): `Global.lua:13083-13088`, event 1324.
  - Cloak of Baa (2105, a cloak): Kriegspire, `mm6/events/maps/outb1.lua:202`, event 90; `Global.lua:13983`.
  - Ebonest (539, a spear): "Promotion to Champion", `Global.lua` event 58, `HasItem(539)` under
    `ForPlayer(Players.All)`.
  - Axe of Balthazar (541): `Global.lua` event 71; Dark Dwarf Compound, `mm8/events/maps/d41.lua:119`.
  - Lich Jar (628 and 1417, price 1800): `Global.lua` events 89 and 738.
  - Knight and Eagle Statuette (1419, 1420, priced): Avlee, `mm7/events/maps/out14.lua:639-641`, event 452.
  - The Perfect Bow (1344), Golden Pyramid (2092), Snergle's Axe (2118), the blasters (1666, 1667), the Wetsuit
    (1406).
- **With two players (inferred):** player A carries the shield, player B talks to the quest giver and is told the
  party does not have it. That is a slip, not a lock: A can hand it in or drop it for B. The lock is a guest who
  leaves the session with such an item in the bags: the character file takes it home, and the architecture's rule
  "a player who leaves cannot carry a key out of the world" does not hold for these 68.
- **Should be:** an item a script checks or takes is the world's, whatever it costs and whatever slot it fits.

### H3. A guest cannot answer a question

- **Read:** `evt.AskQuestion` and its two variants put the prompt into `pendingInputPrompt`
  (`EventRuntime.cpp:8751`, `8827`), one of the per-player fields. What the host sends a guest's game after a
  command is the conversation's context, its state and its messages (`CoopSession::hostSendOutcome`,
  `CoopSession.cpp:2278`); the prompt is not among them. No command carries a typed answer
  (`Coop::Command`, `game/coop/CoopProtocol.h:96`). The buttons of a choice prompt are built from the prompt too
  (`EventDialogContent.cpp:1111`).
- **How much:** `AskQuestion` 27 in MM6, 3 in the shared global events, 55 in Xeen; the two variants 3 and 8.
- **Examples:** the Shadow Guild's four riddles, `mm6/events/maps/6d08.lua:422-464` (events 61 to 64); Castle
  Alamos's password, `cd1.lua:313-324` (event 69); "Steal (Yes/No)?" in Castle Darkmoor, `cd2.lua:545-561`.
- **With two players (inferred, not run):** the guest sees the question's text and has nowhere to type. The host
  can answer the same door, so nothing locks. One played riddle as a guest settles it.
- **Should be:** the prompt travels with the outcome and the answer comes back as a dialogue command.

### H4. Requests that land in the host's game instead of the acting player's

- **A launch pad and a push throw the host.** Read: `specialJump` and `dashParty` call the host's own party runtime
  with no test for an acting player (`OutdoorWorldRuntime.cpp:23331`, `7876`; `IndoorWorldRuntime.cpp:16215`,
  `15446`), while a jump from a spell does test it (`requestPartyJump`, `OutdoorWorldRuntime.cpp:23320`). Examples:
  Ravenshore, `mm8/events/maps/out02.lua:1231-1239`; Plane of Fire, `elemf.lua:230-238`; Regna, `out13.lua:459`
  (from a timer, event 452); MM9's Dungeon of Secrets current, `dungeonofsecrets.lua:689`. Inferred: a guest steps
  on the pad and the host flies; over the Plane of Fire's lava that can kill the host.
- **The Dimension Door opens for the host.** Read: `evt.OpenDimensionDoor` sets `pendingDimensionDoorOverlay`
  (`EventRuntime.cpp:7058`), which `swapTransientEventRuntimeState` does not exchange, and the host's game takes it
  (`GameApplication::processPendingDimensionDoorOverlay`, `GameApplication.cpp:17845`). Seven uses: New Sorpigal
  (`oute3_mmmerge.lua:26`, `:42`), Harmondale and its castle (`7out02_mmmerge.lua:23`, `7d29_mmmerge.lua:6`),
  Ravenshore (`out02_mmmerge.lua:17`, `:37`), Sturmford City (`sturmfordcity.lua:80`). Inferred: a guest clicks the
  door and the continent list appears on the host's screen.
- **Movies and cinematics** are kept with the map's state and played by the host (`PlayerCommands.cpp:126-161`).
  Known as CO-31. MM9 has 44 `evt.PlayCinematic`; the other scripts have 40 `evt.ShowMovie`.

### H5. Moves: every unasked door takes everyone, and a move from a timer or a hook takes only the host

- **Read:** `evt.MoveToMap` to another map is a vote only when it has a text or a picture, or leaves a dungeon for
  an outdoor map; otherwise it is `forced` and takes all players at once (`EventRuntime.cpp:7527-7572`). The
  architecture means this for "a trap, a story event".
- **How much** (literal calls in map scripts):

  | World | Inside the map | Asks first (vote) | To an outdoor map, no text (asks from a dungeon, else forced) | No text or picture (forced) |
  | --- | --- | --- | --- | --- |
  | MM6 | 124 | 34 | 49 | 11 |
  | MM7 | 77 | 55 | 68 | 87 |
  | MM8 | 21 | 131 | 1 | 2 |
  | MM9 | 5 | 1 | 0 | 5 |
  | Xeen | 6 | 0 | 41 | 44 |

  MM8 asks nearly everywhere. MM7 and MM6 have many ordinary doors and teleporters among the forced moves.
- **With two players (inferred):** one player uses a teleporter and the other is pulled out of a shop, a chest or
  a fight with no question. By the letter of the design this is right; with this many of them it will surprise.
- **The reverse, read:** a move inside the map from an event with no acting player moves the host alone
  (`GameApplication.cpp:17282` finds no guest for `LocalPlayer`). Example: the Hive's ending,
  `mm6/events/maps/hive_mmmerge.lua:86-98`: the kill of the reactor runs a kill hook, which teleports "the party"
  out of the reactor room. Inferred: the host is taken out and the guests stay inside.
- **Should be:** an unasked move to another map from a player's own action is a vote like any other, or at least
  warns; a move inside the map from a hook or timer moves every player it was meant for.

### H6. A one-time gift for "the party" reaches the acting player only

- **Read:** only experience, gold and an added award are passed to the other players. Permanent attributes and
  resistances (`EventRuntime.cpp:3997`), skill points (`:4172`), food (`:3720`), a class (`:3022`,
  `luaSetPlayerClass` `:8552`) and an award that is `Set` rather than added (`:2912`) are the event's party's.
- **Examples:**
  - MM9's permanent wells and cauldrons: `mm9_common.lua:410-415` (`ForPlayer(Players.All)`, `AddValue(Base...)`,
    then `Spent = 1` in a map variable) and `:431-438`. The first player to drink gets the bonus; the well is then
    spent for everyone. MM9's maps call `MM9.useWell` 9 times and `MM9.useCauldron` 11 times; every cauldron and
    every well that gives an attribute for good is of this kind.
  - Promotions: `Global.lua` event 58 (loops `Member0` to `Member4`), `Global_mm6_mmmerge.lua:316-325`
    (`PartyMembers()`), `MM7.CompletePromotion`, `MM9.promoteParty`. Each promotes the acting player's character.
    The architecture says "every connected character that qualifies". None locks: every world keeps a way to be
    promoted later (MM8's eight "Promote ..." topics, MM6's and MM7's re-entrant events, MM9's service event 49990).
  - The Arena: the fight is sized by the level of the party that talks to the Arena Master and the winnings and the
    award go to that party (`game/gameplay/ArenaRuntime.cpp:70-80`, `203-205`).
- **With two players (inferred):** permanent bonuses are lost for the slower player. This is the same gap as CO-36
  (MAW's stat barrels), found here for MM9's wells and cauldrons.

### H7. The Shoals and the Lincoln (MM7)

- **Read:** the wetsuit rule is checked for the event's party (`MM7.AllPartyMembersHaveWetsuit`,
  `mm7/events/common/mm7_common.lua:482-492`; the edge travel hook `:494-514`; The Lincoln,
  `maps/7d23.lua:852`). On the Shoals a timer kills unsuited members of the host's party and reads the host's depth
  (`:546-565`), and the way out fires when the host surfaces (`:567-580`, `7out15_mmmerge.lua:16`).
- **With two players (inferred):** one player in a wetsuit passes the gate and the vote takes everyone under water.
  A guest without a wetsuit lives. A guest who surfaces does not leave; the host who surfaces asks for the move.

### H8. Followers are the host's

- **Read:** `AddFollowerNpc` adds to the map's list and to the event's party (`EventRuntime.cpp:8287-8347`).
  `HasFollowerNpc` reads the map's list (`:8264`). At every map load that list is rebuilt from the host's party and
  followers the host's party does not have are dropped (`Party::applyGlobalNpcStateTo`, `Party.cpp:5244-5268`,
  called from `OutdoorWorldRuntime.cpp:5168` and `IndoorWorldRuntime.cpp:4138`).
- **Examples:** Prince Nicolai, `mm6/events/common/mm6_common.lua:61-166` (the circus and the return test
  `HasFollowerNpc`); NPC 396 in `Global_mm7_mmmerge.lua:74-84`; Loren Steel, `7d08_mmmerge.lua:10-31`; the rescued
  dwarves, `7d34_mmmerge.lua:21`. 26 `AddFollowerNpc` and 8 `HasFollowerNpc` in all.
- **With two players (inferred):** a guest takes Nicolai along; after the next map change the map no longer lists
  him and the hand-in fails, while the campaign still marks him as away from his house. The other way round, a
  guest's hand-in removes him from the map's list but not from the host's party, which brings him back at the next
  load. Most MMMerge escorts key their progress on quest bits and only show the follower, so they should pass;
  Nicolai is the one that tests the list.

### H9. Timed hazards hurt the host alone (MM6 to MM8)

- **Read:** as H1. The uses outside MM9 are few.
- **Examples:** Tomb of VARN's radiation, `mm6/events/maps/pyramid.lua:155-175` (event 12, six
  `evt.DamagePlayer(Players.All, ...)`); the Hive's flush, `hive.lua:241-249` (event 54); Gharik's Forge,
  `6d18.lua:374` (event 54); Temple of Tsantsa, `6t3.lua:176` (event 28); Castle Harmondale's on-load
  `SetValue(BankGold, 0)`, `mm7/events/maps/7d29.lua:452-468`. Trap spells cast from timers at no target aim at the
  host (`castEventSpell`, `OutdoorWorldRuntime.cpp:23709`); most of the 170 timer casts in MM6 to MM8 fly between
  fixed points and are the world's.

### H10. Endings

- **Read:** `evt.ReturnToMainMenu` is taken by the host's game (`GameApplication.cpp:17833`). MM6's bad ending is
  `hive_mmmerge.lua:20-24` (a movie, then the menu).
- **Not determined:** what the guests' games do when the host goes to the menu.

### H11. Rewards given once per character are paid to everyone each time

- **Read:** experience is passed to every player, a player bit and a class are not.
- **Examples:** "Follow Baa! +50,000 Experience", `mm6/events/maps/6t7.lua:439-443`, gated by `PlayerBit(69)`:
  each player who touches it gives every player 50,000. A later promotion in MM6 pays `stage.xp` again
  (`Global_mm6_mmmerge.lua:316-320`), as does `MM7.CompletePromotion` (`promotedRewards`). One such event was found
  in MM6 and one in Xeen; the promotions add one grant per extra player of the class.

### H12. Roster gates (inherited from the solo run)

- **Read:** `HasPlayer` and `evt._IsNpcInParty` test the event's party's roster members (`EventRuntime.cpp:2382`,
  `1666`), and a solo run takes nobody in (`GameplayDialogController.cpp:3950`).
- **Examples:** Dyson Leyland, `mm8/events/maps/d19.lua:215-223`, `d22.lua:125-170`; Overdune Snapfinger,
  `Global.lua:473`, `out03.lua:576`. MAW replaces these gates (`rulesets/maw/events/maps/d19_maw.lua`). Under
  Standard co-op (CO-48) nobody can pass them. Not a co-op fault; listed so that a Standard play-test expects it.

### H13. Small ones

- **`HasEverOwnedItem` is each party's own** (`Party.cpp:6130`): a lost-item keeper gives a lost quest item back
  only to the player who once held it (`event_support.lua:714-752`; MM9's Hjordisa,
  `GameplayDialogController.cpp`, the block that reads `MM9.HandedIn.`).
- **A promotion's award lands on every character** (`EventRuntime.cpp:3768`), promoted or not, and goes home with
  a guest.
- **`IsFlying` reads the host's flight** (`OutdoorWorldRuntime.cpp:23285`); six checks in MM6's outdoor maps.
- **A boss's scripted distance and bearing are to the host** (`ActorBehaviorRuntime.cpp:1510`), while its target
  is the nearest party.
- **`AdvanceGameMinutes` and `RestAndHealParty`** age and rest the acting party only (`EventRuntime.cpp:8398`,
  `8426`); three uses.
- **Food an event gives** is the acting player's; gold is everyone's.

## What of a character is tied to a world (for CO-50)

Read while doing the above; not a full answer to CO-50.

- **Player bits, the character's own event variables and `npcs2`** are on the character
  (`EventRuntime.cpp:4097`, `4237`, `3486`) and so travel with a guest. A guest who won the "Game of Might" at home
  (`Global.lua` event 543, `PlayerBit(31)`) cannot win it in the host's world, and one who drank from a
  once-per-character well at home finds it used.
- **Awards** travel with the character and are also handed to every player by the host's events, so a guest takes
  home the awards of quests the host's world finished.
- **The class** travels (a promotion in the host's world is kept).
- **"Ever owned" items, chosen MM9 dialogue rows and teacher ledgers** are the party's own (`Party.cpp:6130-6152`).
- **Followers and MM9 hirelings** are the host's copy when a character's two versions are merged
  (`game/coop/CoopCharacter.cpp:235-236`).

## What to play first

A family is "covered" when an existing scenario proves the command it rests on; its single uses need no play-test.

**Covered families**

| Family | Uses | Proven by |
| --- | --- | --- |
| Experience, gold and awards an event gives; quest bits | about 1,100 grants, 5,600 quest bit calls | `event_rewards_for_every_player.yml` |
| Quest items in the world's pouch | 712 item checks on quest items | `quest_items_are_the_worlds.yml`, `net_quest_items.yml` |
| Chests | 3,581 `evt.OpenChest` | `one_chest_two_players.yml`, `net_guest_chest.yml` |
| A map move that asks; coaches and boats | 221 `evt.MoveToMap` that ask | `travel_vote.yml`, `net_travel.yml`, `fares_wait_for_the_vote.yml` |
| A forced move (the command, not the wish for each use) | about 150 certain, up to 315 | `forced_move_takes_everyone.yml` |
| Houses, shops and talk a player starts | 2,199 `evt.EnterHouse`, 143 `evt.SpeakNPC`, 803 `evt.SetNPCTopic` | `net_guest_shops.yml`, `net_guest_talks.yml`, `world_under_dialogue_*.yml` |
| Map state: doors, faces, textures, lights, monsters (the 106 class-a functions in use) | more than 12,000 | `net_join.yml`, `net_replica_monsters.yml` (the state travels as a whole) |
| Rest | | `rest_vote.yml`, `net_rest.yml` |

Not covered by any scenario: an event from a timer, an on-load event or a hook with a guest in the world; a
question; a launch pad; a follower; the Dimension Door; any MM6 or MM9 content.

**MM9** (riskiest: its map scripts are polls)

1. A trigger box with the host standing still and a guest walking in: Sturmford City's approach talks and barks
   (`sturmfordcity.lua:297-363`).
2. A map exit a guest walks into (MM9's exits are positioned transitions, not events).
3. Hazard zones with both players inside: Chasm of the Dead (`chasmofthedead.lua:520-534`), Dark Passageway
   (`darkpassageway.lua:430`).
4. Yanmir's Fort to Frosgard City (`yanmirsfort.lua:392-395`): who can trigger the fall, who arrives.
5. One permanent well and one cauldron, used by one player and then by the other.
6. A promotion quest handed in with two eligible players; then the promoter's "Promote our eligible characters."
7. One cinematic (CO-31), and one boss fight with the guest as the boss's target (Dragon Stadium).
8. Tamur Leng joining and Forad leaving, with a guest doing the talking.

**MM6** (no scenario exists)

1. A typed answer as a guest: the Shadow Guild's riddles (`6d08.lua:422-464`), Castle Alamos's password
   (`cd1.lua:313-324`).
2. A gear quest item held by the other player, then by a guest who leaves: Lord Kilburn's Shield (`Global.lua`
   event 1324), the Cloak of Baa at Kriegspire (`outb1.lua:202`).
3. Prince Nicolai's escort with the guest taking him, across a map change (`mm6_common.lua:61-166`).
4. The Hive: the flush (`hive.lua` event 54), the reactor's kill by a guest and both endings
   (`hive_mmmerge.lua:86-108`).
5. Tomb of VARN without the Crystal Skull (`pyramid.lua` event 12): who is hurt.
6. New Sorpigal's Dimension Door clicked by a guest (`oute3_mmmerge.lua:26`).
7. One promotion with two players of the class (`Global_mm6_mmmerge.lua:303-340`), and "Follow Baa"
   (`6t7.lua:439-443`).
8. One teleporter that does not ask, with the other player in a shop.

**MM7**

1. The Shoals and The Lincoln with one wetsuit between two players (`mm7_common.lua:473-580`, `7d23.lua:852`).
2. Teleporters and doors that do not ask (87 certain): one with the other player in a house, one in a fight.
3. Harmondale's arrival and Castle Harmondale's on-load events (`7out02.lua` event 50, `7d29.lua` event 377):
   who gets the messenger's letter, whose bank is emptied.
4. An escort taken by the guest: Loren Steel (`7d08_mmmerge.lua`), the dwarves (`7d34_mmmerge.lua`).
5. The Arena (`7d05.lua`): who is measured, who is paid.
6. Priced quest items held by the other player: the statuettes (`out14.lua` event 452), the Lich Jar
   (`Global.lua` events 89, 738), the Perfect Bow (events 816, 820).
7. One promotion with two players of the class (`MM7.CompletePromotion`).
8. The Dimension Door in Harmondale (`7out02_mmmerge.lua:23`).

**MM8** (best covered: every scenario but one runs here)

1. The launch pads as a guest: Ravenshore (`out02.lua:1231-1239`), Plane of Fire (`elemf.lua:230-238`).
2. The Necromancers' Guild and the Temple of the Sun under MAW and under Standard (`d19.lua`, `d22.lua`: the roster
   gates).
3. A promotion whose item is a weapon, held by the other player: Ebonest (`Global.lua` event 58), the Axe of
   Balthazar (event 71).
4. Leaving a plane with its heart as the guest who proposes the trip (`d27.lua` event 6 and its like): the on-leave
   event runs for the host.
5. Ravenshore's on-load story steps (`out02.lua` event 3).
6. Ravenshore's Dimension Door (`out02_mmmerge.lua:17`).

## Engine changes that would remove whole classes

Each would be a row of the open items; none is started.

1. **Give an event with no acting player every player.** A timer, on-load or hook event that asks for the party's
   place, damages the party or opens a talk runs once per player with that player acting, or the scripts get a
   plain "for each player" (MM9's converters would use it in `mm9r_common`). Removes H1, H9 and H7's timer half.
2. **Test MM9's positioned exits for every player's place,** as trigger faces already are.
3. **Decide "quest item" by use.** An item any script checks or takes is the world's; or a guest leaving the
   session leaves such items in the world's pouch. Removes H2.
4. **Send the prompt and take the answer.** `pendingInputPrompt` with the outcome, a typed answer as a dialogue
   command. Removes H3.
5. **Route a body's requests to the acting body.** `specialJump`, `dashParty` and the flight test follow the acting
   player as a same-map move already does (`takeActingBodyOrder`). Removes the jump half of H4.
6. **Make `pendingDimensionDoorOverlay` a per-player request,** with the other fields of
   `swapTransientEventRuntimeState`. One line and a message to the guest's game.
7. **One rule for what an event gives.** Either pass skill points, food, permanent attributes under
   `ForPlayer(All)` and a class change to every player as experience is, or say in the architecture that they are
   the acting player's. Today the code and the plan differ on promotions. Removes H6 and, with a "once per
   character" bit kept per player, H11.
8. **Keep followers per world.** The map's follower list is the union of every party's, or quest escorts are the
   campaign's. Removes H8.
9. **Ask before an unasked move a player's own action caused,** and move every player for a same-map move from a
   hook or timer. Softens H5.
10. **Endings, movies and the return to the menu for everyone** (CO-31 widened by `ReturnToMainMenu`).

## Not determined

- **What a guest's game does with an MM9 exit it walks into.** The host tests its own place only; the guest's side
  was not traced. Settle: walk a guest through an MM9 exit.
- **Which party a map-transition, rest-food or gameplay-action hook runs for** when a guest causes it. Settle: read
  where each hook is raised, or play MM7's wetsuit gate as a guest.
- **`evt.GetEnemyDetectorState`, `evt.GetCurrentScreen`, `evt.CameraShake`** with a guest (2, 2 and 25 uses).
- **MAW's rifts, Dimensional Maps and arena waves** (`evt.RulesTopic`, `evt.ArenaMonster`, map instances) with
  several players. Settle: one rift entered by a guest.
- **MM9's loot props** (`evt.SearchLootProp`, 77 uses) searched by a guest.
- **MM9's items against the quest item rule.** `MM9.hasItem` and `takeItem` take MM9's raw ids (about 105 calls).
  Settle: run the same match through `MM9.ItemIds`.
- **What the guests see when the host returns to the main menu.**
- **House services in C++.** Outside this audit; CO-30 has the known part.
- **Whether every escort and every promotion passes.** The follower and promotion rules were read; the quests were
  not followed bit by bit.
