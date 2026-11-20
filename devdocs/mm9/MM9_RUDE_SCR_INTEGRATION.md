# MM9 RUDE And NPC SCR Integration Contract

## Purpose

This document defines the desired end state for MM9 dialogue in OpenYAMM. It covers RUDE graphs, the dialogue-linked
subset of SCR behavior, quest state, items, rewards, promotions, skills, services, and save state.

`MM9_RUDE_DIALOGUE.md` remains the presentation and RUDE-format reference. This document is the gameplay integration
contract.

MM9 support remains desktop-only until that restriction is explicitly changed.

## Completion Standard

The target is fully functional dialogue, not a text-only RUDE viewer. Every reachable choice must:

- use the original prompt, response, ordering, conditions, and destination;
- execute its state changes and dialogue-linked SCR callback exactly once and in source order;
- preserve the affected party, object, and dialogue state across save/load;
- enter a working shared OpenYAMM service when the row requests one; or
- be visibly unavailable with a specific reason while an intentionally deferred dependency is missing.

No imported condition, command, item, promotion, skill operation, or service may silently succeed as a no-op.
Importer and test reports must identify every unsupported reachable operation by source file and line or RUDE row.

## RUDE Ownership

The original `.rude` files are authoritative. Import must preserve every source row, column, identifier, prompt,
response, condition, action, and unknown field. Generated indexes or typed caches must be lossless and reproducible.

Raw MM9 quest keys map to global party QBits as:

```text
qbit = 90000 + raw_mm9_key
```

Raw key `0` is invalid, QBit `90000` is reserved, and the MM9 range is `90000-99999`.
Generated MM9 Lua must use the full-width quest-bit event API for this range. The legacy packed EVT selector stores a
16-bit index and therefore cannot represent MM9 QBits above `65535` without truncation.

MM9 current quests remain world-owned content. `NPC997.rude` generates the world's optional
`data_tables/english/quests_overlay.txt` whose rows declare required and forbidden full-width QBits. The shared journal
loader merges every mounted world's overlay with the base quest table, whichever world the game started in (until
2026-11-12 only the starting world's: a game started in MM6-MM8 showed an empty quest log in Chedian), and evaluates
the conditions generically. A newly satisfied quest row uses
the normal OpenYAMM portrait effect, `QuestGot` reaction, and `SoundId::Quest`; explicit MM9 `QUEST.wav` calls map to the
same deduplicated shared cue.

The runtime must evaluate all validated RUDE conditions, including QBits, inventory, class/promotion state, skills,
and other decoded state. Selecting a row must perform its validated action or service and must invoke the correct
dialogue exit behavior when the conversation closes.

## SCR Conversion Boundary

Do not port or recreate OpenMM9's general SCR virtual machine/runtime. Extend the existing MM9 importer into a strict,
build-time SCR-to-Lua compiler for dialogue-linked behavior.

Select source scripts through imported map objects with both `DoRude` and `ScriptName`. Do not select scripts only by
an `NPC*.scr` filename pattern because shops, retainers, named characters, and other dialogue actors use shared or
descriptive script names.

Compile only the routines transitively required by dialogue and its quest consequences, principally:

- `Use` and `DoRude` entry paths;
- `OnRudeExit` and routines called by it;
- `OnFoundPlayer` when it starts dialogue;
- map/object callbacks that are required to maintain dialogue or quest state; and
- scalar declarations, parameters, conditions, assignments, calls, and exits needed by those routines.

The generated Lua should call a small MM9 compatibility surface backed by shared OpenYAMM systems. It must not expose
or duplicate a second party, inventory, class, skill, audio, map, or save runtime.

Do not compile general actor AI from `NPCBASE.inc`, `BASEWANDER.inc`, `FOLLOWPLAYER.inc`, door-navigation includes,
combat scripts, socializing, or unrelated animation machinery as part of dialogue support. Use shared OpenYAMM actor
behavior or explicit authored overlays for those cases. Standard conversation interaction should make the actor face
the party through the shared interaction path.

Unsupported syntax or commands in a required routine are generation failures for that binding. Do not emit a generic
runtime `unimplemented()` fallback. Keep source provenance in generated Lua and reports.

Generic scripts may be attached to multiple actors with different parameters. Bind generated state and callbacks by
map source-object identity, not only by RUDE id or script filename. Persist source-equivalent object/script variables
that affect later dialogue outcomes.

Generated MM9 Lua must remain generated. Fix the importer or add an explicit authored map overlay instead of editing
generated output.

## Shared Party Rewards

Dialogue-linked commands use the existing OpenYAMM party state:

- `HasKey`, `GiveKey`, and `TakeKey` use the MM9 QBit mapping above;
- `GiveGold`, `TakeGold`, and gold checks use shared carried gold;
- `GiveExp` adds the original amount to shared party/character experience according to recovered source behavior;
- item commands use the canonical MM9-to-global item mapping; and
- promotion and skill commands use the compatibility rules below.

Preserve source order and original idempotence. Do not add hidden anti-duplication around rewards; the original key and
item checks are responsible for preventing repeated rewards.

## MM9 Items

MM9 items used by dialogue will ultimately be real MM9 items imported from authoritative MM9 item data, initially
`MASTERITEMLIST.csv`. They are not aliases for unrelated MM6-MM8 items.

Import the dialogue-referenced item subset first and expand it as content is enabled. Each imported item must have a
canonical MM9 identity and an explicit mapping to its global runtime item id; raw MM9 ids must not be used directly in
the merged item namespace.

Original MM9 item visuals will later be converted into inventory-compatible 2D sprites from their source icons. Item
statistics and gameplay properties may be deliberately retuned for OpenYAMM, but the source identity and provenance
must remain available and such changes must be explicit data overrides.

Until a referenced MM9 item is imported, that individual item operation must fail visibly and emit a runtime diagnostic
with source provenance. The generated SCR routine continues with later independent operations, so a missing item cannot
prevent subsequent quest keys, gold, experience, or other state from being applied. An unavailable item still tests as
absent and must never grant, remove, or test an unrelated item with a colliding raw id.

MM9 spellbooks and spell scrolls are excluded. Their dialogue/content references must use the existing OpenYAMM spell,
spellbook, and spell-scroll set. Do not add MM9 spells as part of this work.

The items MM9 placed in its maps for a script to give (givetake.scr, bootgive.scr, skillbook.scr, orb.scr and the quest
pickups' scripts) are the scenes' world items, picked up as any ground item; the script's other effects run as the
item's pickup event ([MM9 placed items](../mm9_rework/PLACED_ITEMS_PLAN.md)). A party that lost a quest item gets it
back from Hjordisa the Hag (RUDE 132): `worlds/mm9/dialogue/lost_items.yml` names her and the items, and her first page
offers "We've lost something." (`Mm9RudeDialogueTable::isLostItemKeeper`). An item a script takes (`MM9.takeItem`) is
handed in and never given back.

## Promotions And Classes

**User decision, 2026-11-05: own line, by tier** (replaces the fixed table below). MM9's tree has two tiers: Fighter ->
Mercenary (-> Gladiator, Assassin) or Crusader (-> Paladin, Ranger); Initiate -> Scholar (-> Mage, Lich) or Healer (->
Priest, Druid) (mm9/extracted/DATA/DATA/GAMETEXT.txt). An MM9 first-tier promotion (Mercenary, Crusader, Scholar,
Healer) gives an eligible character its own MMerge class's first promotion; a second-tier one (Gladiator, Assassin,
Paladin, Ranger, Mage, Lich, Priest, Druid) its second. Might quests (the Mercenary and Crusader lines) promote might
class lines, magic quests (the Scholar and Healer lines) magic class lines; a character already at or past the tier, or
of the other kind, is not promoted. The mapping (approved by the user, 2026-11-05: "lets us play any classes"): each MM9 quest promotes the MMerge lines
of its theme, so every line can be promoted fully in the MM9 world. Character creation is unchanged (MMerge races and
base classes in every world; no MM9 Fighter or Initiate).
MM9 is deliberately a wildcard world (user, 2026-11-05, asked again after the comparison): the MM6-MM8 worlds
promote only their native classes (Global_mm6_mmmerge.lua, Global_mm7_mmmerge.lua, Global_mm8_promotions.lua: a Troll
travels to Jadame), MM9 promotes every line, Jadame's racial classes included.

| MM9 quest | Tier | Promotes (from -> to) |
| --- | --- | --- |
| Mercenary | 1 | Knight -> Cavalier, Thief -> Rogue, Archer -> WarriorMage |
| Crusader | 1 | Paladin -> Crusader, Ranger -> Hunter, Monk -> Initiate |
| Scholar | 1 | Sorcerer -> Wizard |
| Healer | 1 | Cleric -> Priest, Druid -> GreatDruid |
| Gladiator | 2 | Cavalier -> Champion, Initiate -> Master, Minotaur -> MinotaurLord, Troll -> WarTroll, Dragon -> GreatWyrm |
| Assassin | 2 | Rogue -> Assassin, Vampire -> Nosferatu |
| Paladin | 2 | Crusader -> Hero |
| Ranger | 2 | Hunter -> RangerLord, WarriorMage -> MasterArcher |
| Mage | 2 | Wizard -> ArchMage |
| Lich | 2 | Wizard -> Lich |
| Priest | 2 | Priest -> PriestLight |
| Druid | 2 | GreatDruid -> ArchDruid, DarkElf -> Patriarch |

User corrections (2026-11-05): Jadame's racial classes have no first promotion (class_extra.txt: they start at step
1), so their one promotion comes from a second-tier quest: Minotaur, Troll and Dragon from the champion's (Gladiator),
Vampire from the Assassin's, Dark Elf from the Druid's. The Necromancer cannot start in MM9 (as in MM6/MM7): no row
(an MM8 Necromancer is promoted in Jadame).

Rules: completing a quest promotes every party member whose class is a "from" of its row, at once (MMerge's way);
MM9's per-character keys 401-448 are not used. Classes promoted in another world simply continue (an MM7 Cavalier goes
to Gladiator).

Any order (the user, 2026-11-08; `worlds/mm9/dialogue/promotions.yml`): every promotion quest is offered to any party
at any time, and pays its experience and gold whoever it promotes. The map converters give the quest keys without an
eligibility check (Tjolnir's 206, Gray Slemnir's 250-252, Tymon's 201). The second tier's accept rows that MM9 opened
only after the first tier's promotion lose that required key at load (`waived_required_keys`: Gladiator and Assassin
on 127, Ranger and Paladin on 137, Mage on 205, Priest and Druid on 213). `added_rows` adds rows MM9's dialogue lacks,
in its CSV form after the original rows: Fridleif's "We've completed all the labors." on his first page, since MM9 had
it only on the page a labour's hand-in leads to and a "Thanks." after the last hand-in lost the Gladiator promotion
for good (`tests/scenarios/mm9/gladiator_labours_completion.yml`). Lich Lab's engine pays its reward on the
first working strike, whoever it changes. Once a quest is done (its `done_key`), its promoter's first page keeps
"Promote our eligible characters." (engine: `Mm9PromotionService`, the shared Lua event `Mm9PromotionServiceEventId`
in `mm9_common.lua`): the members eligible now are promoted, with no experience or gold, and the dialogue names them.
So a party of Knights can do the Gladiator labours first (rewards only), become Cavaliers later, and come back to
Fridleif to be made Champions (`tests/scenarios/mm9/promotion_any_order.yml`). The Mercenary topic stays with
Thorfinn of Thronheim, since Atli Sigmundssen leaves Guberland when the quest is done; the Lich has no topic (the
engine works at any time).
Light/dark: MM9 has none; Mage and Lich are the Sorcerer line's two, Assassin the Thief line's dark one, the rest take
the light promotion (the other dark promotions stay in MM6-MM8). One data table (`MM9.Promotions`) serves the quests'
promotions and the promoters' standing topic; the maps' promotion handlers call it without the per-character keys.


Do not create a separate MM9 party/class runtime. Initially, MM9 `GivePromo` operations map into the existing shared
OpenYAMM class set through an explicit data-owned compatibility table. Preserve the raw MM9 promotion token in
provenance and diagnostics.

The initial nearest-mechanics mapping is:

| MM9 promotion | OpenYAMM class result |
| --- | --- |
| Mercenary | Cavalier |
| Gladiator | Champion |
| Crusader | Crusader |
| Assassin | Assassin |
| Ranger | Ranger Lord |
| Paladin | Hero |
| Scholar | Wizard |
| Mage | Arch Mage |
| Lich | Lich |
| Healer | Priest |
| Priest | High Priest |
| Druid | Arch Druid |

Promotion eligibility must use the same compatibility data as reward application. An ineligible promotion must not
overwrite a character class silently.

This mapping may be refined when testing exposes a better correspondence. If authentic MM9 character creation or
class progression is implemented later, additional canonical MM9 class entries may be added deliberately to the
shared class registry. Do not introduce them implicitly as a side effect of dialogue import.

## Skills And Mastery

Use only the existing OpenYAMM skill set and mastery levels. Do not add MM9-only skills.

**User decision, 2026-11-05: no composite skills.** The MM9 world teaches the MM6-MM8 skills separately, as the other
worlds do: Sword, Dagger, Axe, Mace, Staff, Spear, Shield, Bow, Throwing, Leather, Chain and Plate Armor, and the seven
schools Fire, Air, Water, Earth, Spirit, Mind and Body (MM9 has no Mind or Body: they are taught too). An MM9 trainer
teaches the separate skills its MM9 skill covers (Blade: Sword, Dagger, Axe; Cudgel: Mace, Staff; Spear: Spear; Armor:
Leather, Chain, Plate; Elemental: Fire, Air, Water, Earth), each as its own topic with the shared mastery training;
skills or masteries MM9 never offered (Mind, Body, any missing Expert/Master/Grandmaster tier of a split skill) get
added MM9-world trainer NPCs (the user: "we might add more teachers npcs"). MM9 items already carry the separate skills
(tools/mm9_import_discovery/import_mm9_items.py `normalized_skill`: Blade -> Dagger/Axe/Sword, Cudgel -> Staff/Mace,
Armor -> Leather/Chain/Plate by subtype).

**Implemented (2026-11-05, D2 in [the final rebuild work](../mm9_rework/FINAL_REBUILD_WORK.md)).**
`tools/mm9_import_discovery/generate_mm9_skill_trainers.py` writes `worlds/mm9/data_tables/skill_trainers.txt` (115
services, one per RUDE `-4` row) whose `SharedSkills` lists the separate skills of the row; the generator's
`SKILL_GROUPS` holds the MM9 split and `ADDED_SKILLS` the MM6-MM8 skills given to the closest MM9 trainers. The row's
MM9 sentence ("We'd like to become Experts in Blade.") stays the topic. Since 2026-11-06 (the talk hides the party)
its answer lists the trainer's skills ("Expert Axe", with how many members can learn it), then one row per party member
for the chosen skill ("Aslaug: Become Expert in Axe for 2000 gold", or that member's reason, muted); a single-skill
trainer goes straight to the member rows. Each lesson goes through the shared single-skill training
(`evaluateSkillMasteryTraining`, `applySkillMasteryTraining`, given the member): its own price, rank requirement and
class/race cap from the shared tables, charged alone. The composite group transaction
and the hard-coded RUDE payload mapping in the runtime are gone: the trainer table is the only owner, and its loader
rejects unknown or repeated skill names.

| MM9 trainers (E/M in two towns, GM in a third) | Separate skills taught |
| --- | --- |
| Blade | Sword, Dagger, Axe |
| Cudgel | Mace, Staff |
| Armor | Leather Armor, Chain Armor, Plate Armor |
| Elemental | Fire, Air, Water, Earth Magic |
| Spirit | Spirit Magic, **Mind Magic, Body Magic** (MM9's Spirit is MM6-MM8's self magic) |
| Disarm Trap | Disarm Traps, **Stealing** |
| Body Building | Bodybuilding, **Regeneration** |
| Identify Item | Identify Item, **Alchemy** |
| the other 15 MM9 skills | their one skill each (Spear, Bow, Throwing, Shield, Light, Merchant, Learning...) |

Every MM9 skill has an Expert, a Master and a Grandmaster trainer, so every skill above is taught at all three
masteries. The generator's audit (`worlds/mm9/import/skill_trainer_audit.yml` `coverage`) lists the trainers of every
MM6-MM8 skill and mastery, and generation fails when a trainable skill mastery has no trainer and no reviewed reason.

**Racial abilities (the user, 2026-11-09).** The MM8 racial abilities (**Dark Elf, Vampire, Dragon**) are taught by
racial trainers, listed in `worlds/mm9/dialogue/racial_trainers.yml`: every training hall's keeper up to Master, and
Arslegard's hall (The Pummeled Fist) and Jenn Harrise in Yorwick (which has no hall) up to Grandmaster. Their first
page keeps "We want to train our racial abilities.", which lists one row per member: the racial ability that member
knows at their next mastery, capped at the trainer's, through the shared single-skill mastery training (its price,
rank and class/race caps); a member at the trainer's cap whose class can go further is sent to a grandmaster
(`GameplayDialogController.cpp` `mm9RacialLesson`). A Vampire, Dark Elf or Dragon by race starts with the ability.

Not taught in the MM9 world (no MM9 trainer fits; a proposal, nothing placed): **Blaster**, Expert to Grandmaster. The
proposal is a trainer NPC in Thjorgard, the town of MM9's weapon Grandmasters, at MMerge's 2000/5000/10000 gold
(teacher topics 971-973). It needs a placed actor (before the rebuild) and a world-owned dialogue with `-4` rows outside
MM9's RUDE ids, so its services stay table rows with a RUDE owner.

**Normal: the venues teach (user decision, 2026-11-06).** MM9's venues offer the shared MM6-MM8 "Learn Skills" menu,
so every skill the MM9 world trains has a Normal source there. `generate_mm9_vendors.py` writes each venue's list into
the `learn_skills` column of `vendors.txt` and `service_venues.txt` (canonical skill names separated by `|`; the
temples' and training halls' `can_learn_skills` is 1 exactly when the list is not empty); `HouseTable` loads it into
`offeredSkills` and rejects unknown, composite or repeated names, and a world vendor with skills shows "Learn Skills"
beside its Buy options. The price is the shared one (merchant base × 500 gold).

| Venue | Teaches at Normal |
| --- | --- |
| Weapon shops | Sword, Dagger, Axe, Mace, Staff, Spear, Bow, Throwing |
| Armor shops | Leather, Chain, Plate Armor, Shield |
| Magic shops, by MM9 school | Elemental: Fire, Air, Water, Earth; Spirit: Spirit, Mind, Body; Light; Dark; All: all nine; each also Meditation, Learning |
| Temples | Regeneration, Meditation, Unarmed, Dodging |
| Training halls | Armsmaster, Bodybuilding, Unarmed, Dodging |
| Apothecaries | Alchemy, Identify Monster |
| General stores | Merchant, Repair Item, Perception, Disarm Traps, Stealing |
| Libraries | Learning, Identify Item, Identify Monster |

MM9's skill books stay as they are (`import_mm9_items.py` `SKILL_BOOK_TARGETS`: composite groups at Normal, Blade ->
Sword and Dagger, Cudgel -> Mace, Armor -> all three, Elemental -> all four), sold in the libraries and found as loot.
The inns teach what the general stores do (Merchant, Repair Item, Perception, Disarm Traps, Stealing; the user,
2026-11-06; "Services" below). The racial abilities' Expert to Grandmaster come from the racial trainers above; Blaster
stays untaught.

MM9 spell identities are not imported. Spell learning, spellbooks, and spell scrolls continue to use the OpenYAMM
spell catalogue.

## Services

The final dialogue path includes all observed RUDE service operations through shared OpenYAMM gameplay systems:

- shops and training;
- skill/mastery training;
- travel and town portal;
- bank, inn, healer, and donation;
- hire and dismiss;
- item combination; and
- quest handoff.

Services may be delivered incrementally, but a service opcode is not complete merely because its name is displayed.
It must perform the transaction, update state, and return to or close dialogue according to recovered behavior.

**State (2026-11-06).** A RUDE service row of a venue opens that venue as a shared house (`GameplayDialogController`:
the RUDE dialogue is suspended and restored when the house closes); the venues are rows of `service_venues.txt` and
`vendors.txt`, written by `tools/mm9_import_discovery/generate_mm9_vendors.py` from MMIXSHOPS and the RUDE rows that
reach them.

| Opcode | Service | State |
| --- | --- | --- |
| -2 | shop | the 48 vendors: buy, sell, identify, repair, Learn Skills |
| -3 | training | the 8 training halls: the shared level training (no level cap), Learn Skills |
| -4 | skill training | the 115 trainer rows (`skill_trainers.txt`), "Skills And Mastery" |
| -5 | travel | the boat and coach routes (`transport_routes.txt`) |
| -6 | bank | the 7 banks (Bank of Thjorgaard ... Bank of Arslegaard): the shared bank |
| -7 | inn | the 7 inns: the MM6-MM8 tavern (rent a room: rest to dawn; fill the packs; Learn Skills). An inn's tavern value is its MMIXSHOPS merchant base × 10 (12 Sturmford, Drangheim; 20 Guberland; 25 Thronheim; 30 Thjorgard; 35 Frosgard; 40 Arslegard, within MM6-MM8's 6-60): food to that many days, a room value²/10 and the food value³/100 gold before the merchant discount; its skills keep the merchant base. The Stumbling Hero's innkeeper is NPC339 (MMIXSHOPS: 338) |
| -8, -16 | healer, donation | the 7 temples and the Thronheim midwife (healing only) |
| -14 | quest handoff | closes the dialogue; the hooks give the quest |
| -10, -11 | hire, dismiss | the 15 hirelings' rows (`hirelings.txt`): fee, hire key, limits; [MM9 hirelings plan](MM9_HIRELINGS_PLAN.md) phase 7 |
| -13 | item combine | **open**: NPC418 |
| -15 | hireling service | the hireling's own service, once a day: NPC179 Town Portal, NPC238 heal, NPC308 heal and cure (hirelings plan phase 7) |

## Verification Gates

Completion requires focused automated coverage proving at least:

- all 436 normal RUDE graphs load without losing source rows or fields;
- visibility reacts to mapped QBits, items, promotions, and skills;
- node navigation, close rows, and paging preserve source ordering;
- each dialogue actor resolves the correct source-object-specific script and parameters;
- `OnRudeExit` executes exactly once on every close path;
- item, gold, experience, promotion, and skill rewards survive save/load;
- every trainer service teaches each of its separate skills through the shared single-skill mastery training;
- every reachable service opcode has implemented behavior or a specific visible unavailable result; and
- the generated dialogue/SCR coverage report contains no silently ignored reachable operation.
