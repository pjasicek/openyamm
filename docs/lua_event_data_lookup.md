# Lua Event Data Lookup

This document records the repo-local data tables used to annotate authored Lua event scripts with exact comments.

These comments must come from `assets_dev/Data/data_tables`, not from external decompiled sources.

## Rules

- Use exact table text where the text is stable and author-facing.
- Do not paraphrase table text.
- Use ids directly in Lua where that matches the authoring workflow, then add the exact table comment.
- If a reference is not unambiguously backed by a repo-local table, do not invent a comment.

## Autonotes

- File:
  - [autonote.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/data_tables/english/autonote.txt)
- Lookup key:
  - first column, autonote id
- Comment text:
  - second column, exact text

Example:

```lua
SetAutonote(247) -- Well in the village of Blood Drop on Dagger Wound Island gives 1000 gold if Luck is greater than 14 and total gold on party and in the bank is less than 100.
```

## Items

- File:
  - [items.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/data_tables/items.txt)
- Lookup key:
  - first column, item id
- Comment text:
  - third column, item display name

Example:

```lua
RemoveItem(617) -- Power Stone
```

## Spells

- Primary file:
  - [spells.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/data_tables/spells.txt)
- Supplemental file:
  - [spells_supplemental.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/data_tables/spells_supplemental.txt)
- Lookup key:
  - first column, spell id
- Comment text:
  - third column, spell name

Use `spells_supplemental.txt` for event/runtime spell ids that are not part of the base spell table, such as cannonball projectiles.

Examples:

```lua
CastSpellFromTo(6, ...) -- Fireball
CastSpellFromTo(9, ...) -- Meteor Shower
CastSpellFromTo(136, ...) -- Cannonball
```

## Map Destinations

Outdoor and indoor destinations are sourced differently.

### Outdoor / named map files

- File:
  - [map_stats.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/data_tables/map_stats.txt)
- Lookup key:
  - third column, map file name
- Comment text:
  - second column, map name

Examples:

```lua
MoveToMap({...}) -- Dagger Wound Island
MoveToMap({... "\\1ElemE.blv"}) -- Plane of Earth
```

### Dungeon and special entrance ids

- File:
  - [house_data.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/data_tables/house_data.txt)
- Lookup key:
  - first column, house / entrance id
- Comment text:
  - sixth column, entrance name

Examples:

```lua
MoveToMap({... 191, 0, "\\1D05.blv"}) -- Abandoned Temple
MoveToMap({... 192, 0, "\\1D06.blv"}) -- Pirate Outpost
MoveToMap({... 221, 0, "\\1ElemE.blv"}) -- Gateway to the Plane of Earth
```

If the destination comment is derived from the file-name lookup instead of the numeric entrance id, use the file-backed map name and not a guessed local label.

## Awards

- File:
  - [awards.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/data_tables/english/awards.txt)
- Lookup key:
  - first column, award id
- Comment text:
  - second column, exact award text

Example:

```lua
SetAward(2) -- Brought Power Stone to Fredrick Talimere.
```

## History

- File:
  - [history.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/data_tables/english/history.txt)
- Lookup key:
  - first column, history id
- Comment text:
  - fourth column when present as the short title, otherwise the second column body text

Use the short title if it exists and is specific enough. Use the full history body only if a short title is absent and the comment remains readable.

Example:

```lua
AddHistory(2) -- The World Must Know!
```

## NPCs

- File:
  - [npc.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/data_tables/npc.txt)
- Lookup key:
  - first column, npc id
- Comment text:
  - second column, npc name

Example:

```lua
evt.SpeakNPC(31) -- S'ton
```

## NPC Group News

This combines two tables.

- Group file:
  - [npc_group.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/data_tables/english/npc_group.txt)
- News file:
  - [npc_news.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/data_tables/npc_news.txt)

Lookup:

- group id:
  - first column in `npc_group.txt`
- group label:
  - fourth column in `npc_group.txt`
- news id:
  - first column in `npc_news.txt`
- news text:
  - second column in `npc_news.txt`

Recommended comment style:

```lua
-- NPC group 1 "Peasants on Main Island of Dagger Wound" -> news 2
-- "Our thanks for defeating the pirates!  Now if you could only do something about the mountain of fire!"
evt.SetNPCGroupNews(1, 2)
```

## Monster Kinds Used By Event Calls

- File:
  - [monster_data.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/data_tables/monster_data.txt)
- Lookup key:
  - first column, monster id
- Comment text:
  - second column, monster name

Use this for event calls that refer directly to monster ids, for example:

- `evt.CheckMonstersKilled(...)`
- `evt.SummonMonsters(...)`

Example:

```lua
if evt.CheckMonstersKilled(1, 10, 0, true) then -- Regnan Bandit
```

Current verified `Out01` examples:

- `8` -> `Couatl`
- `9` -> `Winged Serpent`
- `10` -> `Regnan Bandit`
- `11` -> `Regnan Pirate`
- `12` -> `Regnan Brigadier`
- `13` -> `Regnan Crossbowman`

## SummonItem Payloads

`evt.SummonItem(...)` does not use a single id namespace.

Known payloads currently split into two verified families:

- legacy object / sprite payloads
- direct item ids

### Legacy object / sprite payloads

- File:
  - [object_list.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/data_tables/object_list.txt)
- Lookup key:
  - third column, object id / sprite payload
- Comment text:
  - first column, object display name

These payloads are resolved through the legacy object-space path first. When they correspond to a pickable item, runtime also attaches the backing inventory item by reverse lookup on `items.txt` sprite index.

Verified examples:

- `35` -> `Phirna Root`
- `36` -> `Widowsweep Berries`
- `37` -> `Mushrooms`
- `38` -> `Poppy Pod`
- `39` -> `Datura`
- `58` -> `White Potion`
- `76` -> `Empty Potion Bottle`
- `139` -> `Power Stone`
- `140` -> `Power Stone`

Example:

```lua
evt.SummonItem(35, ...) -- Phirna Root
```

### Direct item ids

- File:
  - [items.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/data_tables/items.txt)
- Lookup key:
  - first column, item id
- Comment text:
  - third column, item display name

These payloads are resolved directly as item ids when there is no object-space match.

Verified examples:

- `200` -> `Widowsweep Berries`
- `205` -> `Phima Root`
- `210` -> `Poppy Pod`
- `215` -> `Mushroom`
- `220` -> `Potion Bottle`
- `240` -> `Might Boost`
- `241` -> `Intellect Boost`
- `242` -> `Personality Boost`
- `243` -> `Endurance Boost`
- `244` -> `Speed Boost`
- `245` -> `Accuracy Boost`

Example:

```lua
evt.SummonItem(240, ...) -- Might Boost
```

### Unresolved legacy payloads

The following payloads are present in original legacy event content, but do not currently map cleanly through our repo-local `items.txt` or `object_list.txt` tables:

- `2138`
- `2139`
- `2140`
- `2141`

Do not invent names for these. Leave them un-commented or mark them explicitly as unresolved.

## Not Good Auto-Comment Candidates

These should usually stay as authored names or plain numeric ids without table-driven comments unless a better validated source appears:

- QBits
- MapVars
- Counters
- facet ids
- monster group ids
- chest ids

These are usually gameplay semantics rather than direct text-table references.
