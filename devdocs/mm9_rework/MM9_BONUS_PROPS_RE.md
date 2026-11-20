# MM9 bonus props: wells, cauldrons, cook pots, clovers (RE, 2026-11-06)

What MM9's `WellMMIX`, `Cauldron`, `Cookpot` and `Clover` props do when the party uses them, read from
`mm9/game/data/object.lto` with Rizin (`aaa`, `pdg`), and how the rework carries it. 44 objects in 23 maps; none has a
script, the behaviour is the class's own.

## Finding the code

Each class registers a LithTech ClassDef in `.data` (name, parent `0x101a2e48` = Prop, constructor, property list):
`WellMMIX` 0x101a2ff8 (ctor 0x10061710), `Cookpot` 0x101a2f98 (0x100609d0), `Cauldron` 0x101a2f38 (0x1005fd00),
`Clover` 0x101a2f08 (0x1005f8d0). The constructors set the vtables (WellMMIX 0x101723fc, Cookpot 0x10171f64, Cauldron
0x10171acc, Clover 0x10171880; the Prop base 0x1017119c). Against the base the classes override slot 95 (ReadProp: the
DAT properties into members) and slot 121 (the use handler): WellMMIX 0x100617f0 / 0x10061860, Cookpot 0x10060ab0 /
0x10060b40, Cauldron 0x1005fdc0 / 0x1005fe00, Clover 0x1005f990 / 0x1005f9b0. The DAT stores the numbers as floats
(1084227584 = 5.0); ReadProp (0x100be260) reads them as integers.

Messages are `GAMETEXT.txt` lines by id (0x100d09b0; ids count the non-empty lines from 1): 0x20d "%s gains +%d %s!",
0x20e "%s gains +%d %s temporarily", 0x20f "Hit Points", 0x210 "Spell Points", 0x211 "Resistance", 0x213 "The party",
attributes 0x16-0x1b (Might, Magic, Endurance, Accuracy, Speed, Luck), resistances 0xe2-0xe6 (Elemental, Dark, Light,
Spirit, Physical). Success plays `sounds\events\quest.wav`; a refusal `sounds\events\error.wav`. Every use first
requires a selected character (game +0x68 in 0..3), else the error sound.

## The classes

| Class | Properties (member) | Use |
| --- | --- | --- |
| WellMMIX | Stat (+0x480), BonusAmt (+0x484), BonusSeconds (+0x488), StatType (+0x48c), DosesPerDay (+0x490); doses taken (+0x494), last use (+0x498) | A day (86 400 s) after the last use the count starts again; every use stamps the time and counts a dose, more than DosesPerDay: error. Stat 0: the selected character heals BonusAmt (vtable +0x34); 1: spell points; 2: attribute StatType: with BonusSeconds 0 every member gains it for good ("The party gains ...") and DosesPerDay becomes 0 (the well is spent), else a timed buff (kind 8) on the selected character; 3: resistance StatType: with BonusSeconds 0 the selected character gains it for good (vtable +0x50), else a timed buff (kind 9) |
| Cauldron | Resistance (+0x480), BonusAmt (+0x484); used (+0x488) | Once: every member gains BonusAmt of the resistance for good |
| Cookpot | PoisonChance (+0x480), PoisonPower (+0x484), Resistance (+0x488), BonusAmt (+0x48c), BonusSeconds (+0x490), DosesPerDay (+0x494); doses (+0x498), last use (+0x49c) | Doses as the well's. With `rand % 100 + 1 < PoisonChance` the selected character takes condition 13 (poisoned) for 3 600 s (kind 10); then a timed resistance buff (kind 9) of BonusAmt for BonusSeconds |
| Clover | none; used (+0x480) | Once: item 590 (Clover, a four-leaf clover) to the party, then the model's "Clover" animation |

The data (DAT values): wells Beethoven +5 Speed (party, once), Drangheim City +10 Physical for an hour (12 a day),
Frosgard City +5 Magic (party, once), Guberland City +5 Speed (once), Lindisfarne +5 Dark (selected character, 4 a
day, for good), Thjorgard City +5 Endurance (once), Thronheim City +5 Might (once), the Isle's Prop1 +5 HP (500 a
day), Wizard's Lab's Cauldron1/2 (class WellMMIX) +5 HP / +5 SP (50 a day). Cauldrons +5 to +15 of a resistance
(Boot Camp's two give +0). Cook pots +10 or +15 of a resistance for 3 600 s (the Isle's 2 700 s), 16 a day, poison
20-50 %. Fifteen clovers.

## In the rework

Shared: `level_generation/projects/mm9r_common/dungeon/content.py` (`BONUS_CLASSES`) gives each placed prop of these
classes without a map event the click event 30000 + its DAT index; `dungeon/objects.py` `bonus_call` /
`bonus_lines` write its handler with the DAT values; Frosgard, Guberland and Thjorgard City keep their wells' own
events and call `bonus_call`. The behaviour is world Lua, `assets_dev/worlds/mm9/events/common/mm9_common.lua`:
`MM9.useWell`, `MM9.useCauldron`, `MM9.useCookpot`, `MM9.useClover` (doses and uses in map variables
`MM9.Bonus.<index>.*`, the day as 1 440 game minutes).

The Clover item itself (MM9 item 590, ours 10590): used on a character it gives one skill point and is consumed
(cshell.dll 0x100249c4 adds 1 to the field the level-up code adds 5 + level/10 to). Ours: the item table's
`use_action` `GrantSkillPoints` with VarA 1 (`tools/mm9_import_discovery/import_mm9_items.py`,
`InventoryItemUseAction::GrantSkillPoints`), since 2026-11-12; before, the item did nothing. All fifteen patches are
placed since the same day: Guberland, Sturmford and Thronheim City's props projects had left the Clover class out
(`tests/scenarios/mm9/city_clovers.yml`).

Deviations: what MM9 gives the selected character goes to the current member; MM9's timed buffs (kinds 8 and 9)
become the MM6-MM8 temporary event bonuses (`<Stat>Bonus`, `<School>ResistanceBonus`), raised to the amount and not
stacked, which last until the party rests rather than BonusSeconds; the poison is the weakest (PoisonedGreen) and has
no hour; MM9's resistances map onto the MM6-MM8 schools as the monster import does (Elemental: fire, air, water,
earth; Spirit: spirit, mind, body; Light, Dark, Physical as they are). The messages name no character.
