# MM9 Hirelings

Research record (2026-11-06) of Might and Magic IX's hireling ("NPC party member", "retainer") system, so that
OpenYAMM can implement an MM9-only hireling system next to the MM6-MM8 followers. Nothing here is implemented yet.

## OpenYAMM design (user decisions, 2026-11-06)

The research below records MM9; this section records what OpenYAMM will do. Not implemented yet.

- **Two systems, one per world.** In the MM9 world the MM9 hirelings are active and the MM6-MM8 followers are off:
  not shown, not counted, no wages or gold share. In MM6-MM8 worlds the MM9 hirelings do not exist.
- **At most three hirelings, as MM9** (the user, second decision of the day): at most two paid retainers; the third
  slot only for the story companions Forad and Tamur (section 2).
- **Values:** the MM9 rows' values as fixed numbers, buffs and conditions on top, no levelling; they may be revised to
  fit the MM6-MM8 calculations by the MM9 balance work (`devdocs/mm9_rework/BALANCE_PLAN.md`), to be agreed with it.
- **Combat:** full party members; how they act (and how the casters cast, and with what mana) follows MM9's code
  (section 9 when researched).
- **Death:** a dead hireling stays on the rail, greyed, and is raised at a temple (or by PC spells) like a PC.
- **Wages:** MM9's: the hire fee once, the wage every 28 days; an unpaid wage empties the purse and that retainer
  leaves.
- **External party members.** A hireling is computed like a party character (the same damage, armour, resistance,
  condition, buff and debuff rules, the same recovery), but has no inventory, no equipment and no spellbook. Buffs
  and party spells reach it, monsters can target it, it can be inspected (held RMB over its portrait, as a PC), and a
  double click on its portrait opens its dialogue (its -15 service, dismissal). Its values come from its MM9 row
  (section 3): level, HP, AC, attack dice, resistances, recovery, its spells (with the MM9_SPELL_MAPPING.md
  replacements). It takes no experience share (as in MM9).
- **HUD.** The rail of the study `level_generation/ui/mm9_hirelings_20261106/` (revision 1): the basebar's Obsidian
  panel flush with the right edge under the minimap, a slot per hireling with its MM9 portrait (x2 restoration, the
  18 expression frames animated as PC faces), the party's HP arc (no mana), the aggro diamond with its recovery arc
  and the buff medallion. Revision 2: three slots, faces 72 % of a party face, the rail under the row of the
  combat-log and followers buttons. Those buttons are not shown in the MM9 world, nor the combat log in the Standard
  ruleset (the user); the row stays free for a combat log switched on in the settings.

## Sources and notation

| Short form | File |
| --- | --- |
| `NPCn.rude:L` | `mm9/extracted/RUDE/RUDE/NPCn.rude`, line L. `assets_dev/worlds/mm9/dialogue/rude/` holds byte-identical copies (checked with `cmp` for every file cited here). Columns as in `game/mm9/Mm9RudeDialogue.cpp:247-250`: c7/c9/c11/c13/c15 required keys, c16-c20 granted, c21-c25 forbidden, c26-c30 removed. |
| `MONSTERS:L` | `mm9/extracted/DATA/DATA/MONSTERS.txt`, line L (line 1 is the header). |
| `X.scr:L` | `mm9/extracted/SCRIPTS/SCRIPTS/X.scr`, line L. |
| `map#N` | object N of `assets_editor_dev/worlds/mm9/maps/<map>.raw_objects.yml` (decoded `WORLDS/*.dat`). `NPCNbr` and `RUDENPCId` are floats stored as integer bits (1127284736 = 177.0). |
| `GAMETEXT:L` | `mm9/extracted/DATA/DATA/GAMETEXT.txt`, line L. The executable's text id equals the line number (id 522 is line 522). |
| `HUDCOORDS:L` | `mm9/extracted/ART/ART/HUD/HUDCOORDS.txt`, line L. |
| `cshell@0x...` | client game code `mm9/game/data/cshell.dll` (sha256 `678700ff1cc795aeee49fe8427a42e1686d5a20dfdc1617eb46a8ef19f82f7ae`, PE 32-bit, image base 0x10000000, linked 2002-03-21), virtual address, read with Rizin. |
| `object@0x...` | server game code `mm9/game/data/object.lto` (sha256 `b1271f37e5314281035efe6425dd59051bb8a9b0271de0d75a5926a7bc37f162`, linked 2002-03-21), virtual address. |
| `MANUAL p.N` | `mm9/game/MANUAL.PDF`, page N of its `pdftotext -layout` text. |

Binary findings are read from disassembly without running the game; each one names the routine so it can be
rechecked. The scripts were patched by the fan "TELP Patch 1.3" (`RETAINER.scr:7`); the DLLs were not.

## 1. The hirelings

Fifteen RUDE dialogues contain a hire row (`next = -10`). Thirteen are paid retainers, two are story companions,
and one (Huber Carryall) is not hireable in the shipped executable.

### 1.1 Identity, location and price

The executable maps a RUDE id to a `MONSTERS.txt` row in two places with the same switch: the client hire check
`cshell@0x10053690` and the server `AddNPC` routine `object@0x100b6a90` (jump tables at `object@0x100b6c1c/0x100b6c40`
and `0x100b6cc0/0x100b6ce0`). The portrait folder number is `monster row - 278`, and 15 for Forad
(`cshell@0x10053410`). The paid retainers' hire keys and hire fees are parallel tables in `cshell.dll`: RUDE ids at
`0x100d1ce0`, keys at `0x100d1d14`, fees at `0x100d1d48`, read by the hire handler `cshell@0x10028af0`. The monthly
wages are hard-coded in `object@0x100556c0` and the gold shares in `cshell@0x10054100` (both described in section 5).

| RUDE | Name | Portrait | MONSTERS row | Where met (map, object, script) | Hire key | Hire fee | Wage / 28 days | Gold share | RUDE quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 42 | Hrolf Spearmaster | NPC01 | 279 (`MONSTERS:260`) | Thjorgard city, `thjorgardcity#1073`, `retainer.scr "voices\npc\NPC_042.wav 450"` | 450 | 300 | 300 | 2 % | 300 gold per month, plus 2 % (`NPC42.rude:2`) |
| 43 | Tesar Olin | NPC02 | 280 (`MONSTERS:261`) | Sturmford city, `sturmfordcity#843`, `Retainer.scr "... 451"` | 451 | 500 | 500 | 3 % | "500 shinies every moon. 3 part of found shinies" (`NPC43.rude:4`) |
| 44 | Arienh A'Klindor | NPC03 | 281 (`MONSTERS:262`) | Thjorgard city, `thjorgardcity#1076`, `retainer.scr "... 452"` | 452 | 500 | 500 | 5 % | 500 per month plus 4 % (`NPC44.rude:4`; the code takes 5) |
| 85 | Randver Headcrusher | NPC04 | 282 (`MONSTERS:263`) | Thjorgard city, `thjorgardcity#1102`, `randverretainer.scr` (key 453 hard-coded, `RANDVERRETAINER.scr:44`) | 453 | 700 | 700 | 10 % | 700 per month plus 10 % (`NPC85.rude:5`) |
| 86 | Ake the Righteous | NPC05 | 283 (`MONSTERS:264`) | Sturmford city, `sturmfordcity#801` (a `RUDEProp`, `RUDENPCId` 86), `akeretainer.scr` (key 454, `AKERETAINER.scr:27`) | 454 | 1000 | 1000 | 0 % | a 1000 gold monthly donation to his temple (`NPC86.rude:3`) |
| 125 | Beagan A'Ghrie | NPC06 | 284 (`MONSTERS:265`) | Drangheim city, `drangheimcity#333`, `Retainer.scr "... 455"` | 455 | 1000 | 1000 | 5 % | 1000 per month plus 5 % (`NPC125.rude:3`) |
| 126 | Edina A'Mor | NPC07 | 285 (`MONSTERS:266`) | Drangheim city, `drangheimcity#332`, `Retainer.scr "... 456"` | 456 | 700 | 700 | 10 % | 700 per month plus 10 % (`NPC126.rude:2`) |
| 177 | Alberik Gusmundssen | NPC08 | 286 (`MONSTERS:267`) | Guberland city, `guberlandcity#823`, `retainer.scr "... 457"` | 457 | 500 | 500 | 2 % | 500 per month plus 2 % (`NPC177.rude:3`) |
| 178 | Alvar the Clumsy | NPC09 | 287 (`MONSTERS:268`) | Guberland region (outdoor), `guberland#345`, `Retainer.scr "... 458"` | 458 | 600 | 600 | 0 % | 600 per month (`NPC178.rude:3`) |
| 179 | Ehwaz | NPC10 | 288 (`MONSTERS:269`) | Guberland city, `guberlandcity#824`, `retainer.scr "... 459"` | 459 | 1000 | 1000 | 15 % | 1000 per month plus 15 % (`NPC179.rude:4`) |
| 238 | Sowelu Axeldotir | NPC11 | 289 (`MONSTERS:270`) | Frosgard city, `frosgardcity#581`, `retainer.scr` without parameters (the patch sets key 460 for object name `238`, `RETAINER.scr:78-90`) | 460 | 1000 | 1000 | 10 % | 1000 per month plus a 10 % tithe (`NPC238.rude:3`) |
| 281 | Cleirach A'Lyrae | NPC12 | 290 (`MONSTERS:271`) | Thronheim city, `thronheimcity#133`, `retainer.scr "... 461"` | 461 | 1000 | 1000 | 20 % | 1000 per month and 20 % (`NPC281.rude:3`) |
| 308 | Florie de Latharna A'Washadi | NPC13 | 291 (`MONSTERS:272`) | Lindisfarne (outdoor), `lindisfarne#296`, `Retainer.scr "... 462"` | 462 | 2000 | 1000 | 20 % | "2000 gold to start, 1000 gold per month plus 20 %" (`NPC308.rude:2`) |
| 2 | Forad Darre (story) | NPC15 | 252 (`MONSTERS:233`) | Isle of Ashes, `isleofashes#61` (`ForadDarreNPC`, `forad.scr`) | 29 (granted by the RUDE row) | none | none | 0 % | "Climb Aboard!" (`NPC2.rude:4`), "Welcome aboard" (`NPC2.rude:13`, `:36`) |
| 309 | Tamur Leng (story) | NPC14 | 292 (`MONSTERS:273`) | Frosgard city, `frosgardcity#69` (`NPC309.scr`) | 190 (set by the script) | none | none | 0 % | joins by script, not by RUDE (section 1.3) |
| 253 | Huber Carryall (cut) | none | 298 (`MONSTERS:279`, picture `porter`) | Thjorgard city, `thjorgardcity#1075` (`shopkeeper.scr`, object name `Hreidmar0`) | none | none | none | none | "+30 carrying capacity ... 500 gold a month, plus 20 %" (`NPC253.rude:3`) |

Notes:

- The hire fee is charged once, at the moment of hiring, from the fee table (`cshell@0x10028b92-0x10028bc6`). For
  twelve retainers it equals the monthly figure their dialogue quotes; only Florie's 2000 differs, matching her
  "2000 gold to start". The wage is then charged again every 28 days (section 5).
- Huber Carryall has no portrait folder, no `porter` portrait, no hire key, no dismiss row and no entry in either
  RUDE-to-monster switch. His hire row reaches `cshell@0x10053690`, whose default branch fails, so hiring him plays
  `sounds\events\error.wav` and nothing else (`cshell@0x10028b0d`). He is cut content.
- Forad's and Tamur's MONSTERS rows have 3D models (`ForadDarre.abc`, `ClanSoldier.abc`) because they also appear
  as world actors. The 13 retainer rows and Huber's have `ModelName = n/a`: a retainer exists only as a party member.

### 1.2 Hire and dismiss rows; rejoining

| RUDE | Hire row | Dismiss row | Rows hidden while hired |
| --- | --- | --- | --- |
| 42 | `NPC42.rude:1` (node 7) | `NPC42.rude:9` (root node, requires and removes 450) | `NPC42.rude:14` forbids 450 |
| 43 | `NPC43.rude:5` (node 4) | `NPC43.rude:18` (root, requires 451) leads to `NPC43.rude:8` (node 20, `-11`, removes 451) | `NPC43.rude:6`, `:14` forbid 451 |
| 44 | `NPC44.rude:3` | `NPC44.rude:10` (requires and removes 452) | `NPC44.rude:2`, `:5` forbid 452 |
| 85 | `NPC85.rude:3` | `NPC85.rude:14` (453) | `NPC85.rude:2`, `:4`, `:7` forbid 453 |
| 86 | `NPC86.rude:2` | `NPC86.rude:12` (454) | `NPC86.rude:7` forbids 454 |
| 125 | `NPC125.rude:2` | `NPC125.rude:10` (455) | `NPC125.rude:6` forbids 455 |
| 126 | `NPC126.rude:1` | `NPC126.rude:9` (456) | `NPC126.rude:4`, `:5`, `:8` forbid 456 |
| 177 | `NPC177.rude:2` | `NPC177.rude:10` (457) | `NPC177.rude:9` forbids 457 |
| 178 | `NPC178.rude:2` | `NPC178.rude:9` (458) | `NPC178.rude:8` forbids 458 |
| 179 | `NPC179.rude:3` | `NPC179.rude:10` (459) | `NPC179.rude:8` forbids 459 |
| 238 | `NPC238.rude:2` | `NPC238.rude:10` (460) | `NPC238.rude:5` forbids 460 |
| 281 | `NPC281.rude:2` | `NPC281.rude:10` (461) | `NPC281.rude:5`, `:8` forbid 461 |
| 308 | `NPC308.rude:1` | `NPC308.rude:8` (462) | `NPC308.rude:4` forbids 462 |
| 2 | `NPC2.rude:4` (grants 29), `:13` (grants 29 and 371), `:36` (grants 29) | none | many rows require 29 (section 1.3) |
| 253 | `NPC253.rude:2` | none | none |

- The retainers' hire rows grant no key. The hire key is set by the executable after a successful hire, from the
  key table (`cshell@0x10028be8`, `call 0x1004a7d0` on the party's key set). Every dismiss row removes that key in its
  own c26 tail. In OpenYAMM the RUDE hire row therefore cannot be the source of the key: the hireling table must
  give it (`mm9RudeRowAppliesQuestKeys`, `Mm9RudeDialogue.cpp:566-569`, applies the tails of -10/-11 rows, which is
  right for Forad and for the dismiss rows).
- Every retainer's world object runs `Retainer.scr` (or `AkeRetainer.scr`, `RandverRetainer.scr`), whose `:Init`
  hides the object (clears Visible, Solid, Gravity) while the hire key is held and shows it otherwise, on world start,
  mini-save load and save load (`RETAINER.scr:41-56`, `:61-75`; `AKERETAINER.scr:25-56`; `RANDVERRETAINER.scr:37-79`).
  At the moment of hiring, the server also clears the same three flags on the speaking object
  (`object@0x100b6bd3`, mask `0xfffddffe`), so the retainer vanishes at once.
- Rejoining is supported: dismissal removes the key, so on the next load the retainer stands at his post again,
  and his hire row has no forbidden key. The dismiss responses say so ("I'll be around if you need me again!",
  `NPC42.rude:9`; similar in `NPC44.rude:10`, `NPC126.rude:9`, `NPC178.rude:9`). Re-hiring charges the fee again.
- The dismiss handler `cshell@0x10028cc0` looks for the party NPC whose RUDE id matches the open dialogue and
  removes it (`call 0x100538f0`); it refunds nothing. The manual describes the same: "dismiss an NPC ... by pressing
  the key relative to his position to bring up his dialog ... and then click on the topic that says 'we don't need
  you anymore'" (MANUAL p.34).

### 1.3 Story companions

**Forad Darre** (RUDE 2) is Tamur Leng's advisor, sent to betray the party (`BOOK AND SCROLL TEXT.csv:345`).

- Joins on the Isle of Ashes through his `-10` rows, which grant key 29 (in party) and, on one path, 371
  (`NPC2.rude:4`, `:13`, `:36`). `FORAD.scr:46-85` (`:OnRude`) gives 4000 experience once (key 368) and removes the
  world object while key 29 is held. He costs nothing: RUDE 2 is not in the fee table.
- While in the party his dialogue offers region commentary gated on key 29 and the location keys 1024-1033
  (`NPC2.rude:21-33`), which `FORADWORLD.scr:39-98` sets per map (Isle of Ashes 1024 ... Yorwick 1032, elsewhere 1033).
  Those rows are reachable only from his portrait, since his world object is gone.
- Leaves in the clan-council cutscene in Thronheim city: `RemoveNPC 2` in `ARGUMENT.scr:202` (label `:Cam2b`,
  `ARGUMENT.scr:191`; the comment "this is where Forad is removed from the party" is at `ARGUMENT.scr:74`). Key 29 is
  never removed by any script or RUDE row.
- His betrayal sets key 104 (`NPC3.rude:39`, Sven Forkbeard). Afterwards he is an enemy: Frosgard city places him
  hidden with parameter `Hate` (`frosgardcity#48`, `FORAD.scr:178-183`); with key 104 his dialogue turns him hostile
  (`FORAD.scr:50-56`), and his death gives 194000 experience and key 494 (`FORAD.scr:145-158`). The Afterworld fight
  uses MONSTERS row 252 as a monster (`tools/mm9_import_discovery/mm9_monster_legacy_replacements.tsv:136`, runtime id
  9252 in `assets_dev/worlds/mm9/modifiers.yml:283`).

**Tamur Leng** (RUDE 309) joins at the end of the main quest: after the party shows the Writ of Fate
(`NPC309.rude:3` grants 106), `NPC309.scr:39-58` gives key 190 and 412000 experience and calls `AddNPC 309`, then
removes his Frosgard world object. No script removes him again. His row (`MONSTERS:273`) is the strongest companion
(level 60, 720 HP).

`ADDNPC.scr:17-26` is a developer test object that adds and removes Forad on use; no map uses it.

## 2. The party limit

The party has seven members: four PCs and up to three NPCs. "The maximum possible number of characters in the
party at any time is seven ... up to three NPCs that can join or leave the party. Their portraits will always appear
along the right side of the Adventure Screen" (MANUAL p.26). The manual also says "You may hire up to three NPCs"
(MANUAL p.34), but the code is stricter for paid retainers.

Client check before hiring, `cshell@0x10053690` (party object `0x100d9f38`, NPC count at `+0x64`):

1. Three NPCs already: refuse.
2. RUDE id not in the switch (Huber, or anything else): refuse.
3. The same MONSTERS row is already in the party: refuse.
4. Two NPCs already, neither of them Forad (252) or Tamur (292), and the newcomer is not Forad or Tamur either:
   refuse (`cshell@0x1005378d-0x10053794`).

A refusal plays `sounds\events\error.wav` with no message (`cshell@0x10028b0d`). The server's add routine
`object@0x10054700` refuses only a fourth NPC.

So at most **two paid retainers** can be in the party. The third slot is reserved for a story companion: Forad plus
two retainers is possible, three retainers is not. (This differs from the "three without Forad" assumption; the
check is explicit in the code.) `AddNPC` from a script (Tamur) goes straight to the server and only meets rule 1; by
then Forad has left, so Tamur always finds a slot.

Insufficient gold also refuses the hire: the selected PC speaks voice event 23 (`cshell@0x10028bcb-0x10028bdd`),
which is "You don't have enough gold to buy that item." (`DATA/PCVOICES/ANGRYM.txt:25`, event n is line n + 2).

## 3. Combat data

The server builds each hireling as a party entity (0x2d8 bytes, `object@0x10052930`) from its MONSTERS row
(`object@0x10052b00` with the row number). The fields come from `MONSTERS.txt`'s header (`MONSTERS:1`); "Res" is
Elemental/Spirit/Dark/Light/Physical.

| RUDE | Name | Lvl | HP | AC | SPD | Recovery | Attack 1 | Spells | Res E/S/D/L/P | Script | Role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 42 | Hrolf Spearmaster | 34 | 276 | 21 | 13 | 70 | Phys 2d9+17 | none | 0/0/0/0/0 | basemelee | melee spearman |
| 43 | Tesar Olin | 15 | 110 | 9 | 11 | 60 | Phys 4d5+12 | none | 10/10/10/10/20 | basemelee | brawler ("Me bash good") |
| 44 | Arienh A'Klindor | 20 | 120 | 14 | 14 | 75 | Phys 2d4+8, Projectile1 = Spell | 60 %: Elemental Blast (11) Expert 6; Poison Cloud (32) Master 7 | 20/20/20/20/0 | baserange | mage |
| 85 | Randver Headcrusher | 40 | 360 | 21 | 18 | 70 | Phys 5d5+20 | none | 10/10/10/10/30 | basemelee | gladiator, meat shield |
| 86 | Ake the Righteous | 50 | 525 | 26 | 15 | 50 | Phys 7d3+25, Projectile1 = Spell | 60 %: Sparks (40) Normal 3; Elemental Bolt (12) Normal 3 | 10/20/10/10/30 | baserange | holy warrior, caster |
| 125 | Beagan A'Ghrie | 50 | 525 | 21 | 15 | 40 | Phys 2d3+25 | none | 30/30/30/30/30 | basemelee | assassin |
| 126 | Edina A'Mor | 7 | 43 | 10 | 9 | 80 | Phys 2d4+3 | none | 5 all | basemelee | banker (weak) |
| 177 | Alberik Gusmundssen | 8 | 47 | 10 | 9 | 80 | Phys 2d4+4 | none | 5 all | basemelee | merchant (weak) |
| 178 | Alvar the Clumsy | 8 | 66 | 17 | 9 | 80 | Phys 2d4+4 | none | 5 all | basemelee | tinker (weak) |
| 179 | Ehwaz | 11 | 91 | 11 | 9 | 80 | Phys 2d4+5 | none | 5 all | basemelee | gate master (weak) |
| 238 | Sowelu Axeldotir | 13 | 116 | 11 | 9 | 80 | Phys 2d4+6 | none | 10/30/10/10/20 | basemelee | healer |
| 281 | Cleirach A'Lyrae | 9 | 61 | 11 | 10 | 80 | Phys 4d4+8 | none | 20 all | basemelee | illuminate (weak) |
| 308 | Florie de Latharna A'Washadi | 25 | 169 | 16 | 12 | 70 | Phys 4d4+13 | none | 20 all | basemelee | healer, fair fighter |
| 2 | Forad Darre | 50 | 525 | 50 | 13 | 45 | Phys 9d3 | none | 40/40/40/30/30 | basemelee | story, strong melee |
| 309 | Tamur Leng | 60 | 720 | 30 | 18 | 45 | Phys 4D3+30 | none | 0 all | basemelee | story, strongest |

Rows: `MONSTERS:260-273` and `:233`. Every row has `IsMonster = 0`, `Hostility Group = 1`, `Resurrect = 0`,
`TreasureType = None` (retainers) and `Always Wince? = 1` for the retainers. The retainers' second attack (Hrolf,
Tesar, Randver: `Type2` Phys 5d3+10 / 5D3+25) is loaded and used as their ranged attack (section 9.2); the first
`Projectile2` column (`arrow`, column 40) is not loaded (`devdocs/mm9_rework/MM9_SPELL_MAPPING.md:231-232`; the
`monsters.txt` loader `object@0x10042e14` reads `Projectile1` and the second `Projectile2`, column 67). `SpellUse%2`
is never read: the second spell takes the casts the first leaves (`MM9_SPELL_MAPPING.md:51-55`, section 9.2). The two spell rows are listed in `MM9_SPELL_MAPPING.md:104-105`,
`:213` and `:396-397`, with OpenYAMM replacements (Elemental Blast as Fireball, Poison Cloud as Toxic Cloud).

The scripts never mention hirelings except the visibility scripts above, and `HIREDGOON.scr` (a 2001
follow-and-fight prototype, `HIREDGOON.scr:1-46`) is used by no map (no `.dat` contains its name). How hirelings fight
is in the executable and is described in section 9: they are player-controlled party members that take their turn in
the active-member rotation, not autonomous allies.

Server experience award, `object@0x10054c60`: with Cleirach in the party the award is multiplied by 1.1
(constant `0x1016f1b8` = 0.1), then split equally among the members counted by the party's `+0x60` field that are not
incapacitated (entity method `+0x64`, `object@0x100536e0`, tests conditions such as Unconscious, Stunned and Asleep).
NPC add and remove change only the NPC count `+0x64` (`object@0x10054700`, `0x10054740`), so `+0x60` is the PC count
and hirelings take no experience share.

## 4. Abilities

### 4.1 Dialogue services (opcode -15)

Opcode -15 is "the hireling's special service", not "town portal": the client dispatches -15 to
`cshell@0x1002add0`, which branches on the dialogue's RUDE id (179, 238, 308). The rows sit on each hireling's root
node and require the hire key, so they are reachable only from the portrait.

| RUDE | Row | Prompt | Effect (`cshell@0x1002add0`) |
| --- | --- | --- | --- |
| 179 Ehwaz | `NPC179.rude:9` | "We'd like you to cast Town Portal." | Casts MM9 spell 43 Town Portal (`SPELL.txt:44`) for the party: sends message 0x79 with the NPC and spell 43 (`cshell@0x1002aee3`). |
| 238 Sowelu | `NPC238.rude:9` | "We'd like to be healed" | Plays `sounds\spells\heal.wav` and sets every party member's HP (all seven slots, the hirelings too) to its maximum (`cshell@0x1002b03d-0x1002b06c`). No condition is cured, although her offer says "all your injuries and conditions" (`NPC238.rude:3`). |
| 308 Florie | `NPC308.rude:7` | "We'd like to be healed" | Same HP restore, and on every member clears conditions 1, 3, 10 and 13 (`cshell@0x1002b17c-0x1002b1d7`), which `cshell@0x1004b0c0` names Cursed, Diseased, Insane and Poisoned (`GAMETEXT:449`, `:450`, `:453`, `:454`). |

Cooldown: each service is "once per day" per hireling. The NPC entity keeps a timed effect (Ehwaz: spell 43;
Sowelu and Florie: spell 23 Heal, `SPELL.txt:24`) set to the current game time plus 86400 seconds (`0x15180`, 24 game
hours) by `call 0x1004b460`. While it runs, the service shows "%s can cast this but once per day!" (`GAMETEXT:522`)
with the hireling's name and, for the healers, `sounds\events\fizzle.wav`. The services cost nothing beyond the
wage; no gold or mana is taken. The cooldown is 24 hours after use, not a calendar day.

### 4.2 Passive bonuses

| Hireling | Bonus | Source |
| --- | --- | --- |
| Edina A'Mor (285) | Gold the party gains is multiplied by 1.2 ("increase the riches you find by 20 %", `NPC126.rude:2`) | `cshell@0x10053de0` (constant `0x100c5ad0` = 0.2); the same in `object@0x10054d80` (`0x1016f2d8`) |
| Cleirach A'Lyrae (290) | Experience awards multiplied by 1.1 ("add 10 % to your experience", `NPC281.rude:3`) | `object@0x10054c60` |
| Cleirach A'Lyrae (290) | Identify Item never fails for lack of skill ("identify anything") | `cshell@0x10011970`: the failure branch (`call 0x10011b80`) is skipped while Cleirach is present |
| Alvar the Clumsy (287) | Repair Item never fails for lack of skill ("fix all your stuff for free", `NPC178.rude:3`) | `cshell@0x10011aa0`, same pattern |
| Alberik Gusmundssen (177) | +6 to each PC's skill 15 | at hire every PC gets flag `+0x229` (`cshell@0x10028c09-0x10028c3f`, `0x1004dd90`); the skill getter adds 6 to skill 15 (`cshell@0x1004dd68-0x1004dd75`) |
| Beagan A'Ghrie (125) | +4 to each PC's skills 14 and 16 | flag `+0x228`; `cshell@0x1004dd51-0x1004dd65` |

The skill bonus is added only when the PC already has the skill (the getter returns 0 for an untrained skill before
the bonus, `cshell@0x1004dd3c`); dismissal clears both flags (`cshell@0x10028cfe-0x10028d39`). The skill numbers are
the executable's enumeration. Repair is 17 and Identify Item 18 (the skill checks above read them); the skills screen
lists Armsmaster, Disarm Trap, Merchant, Perception, Repair Item, Identify Item in that order
(`ART/INTERFACESCREENS/CHARACTERINFO/CHARACTERSKILLS-COORDS.txt:59-64`), so 14, 15 and 16 are Disarm Trap, Merchant
and Perception. Alberik ("I could help you get better prices", `NPC177.rude:4`) thus gives +6 Merchant and Beagan
the assassin +4 Disarm Trap and +4 Perception (inferred from that order, which the 17/18 reads confirm).

Hrolf, Tesar, Arienh, Randver, Ake, Forad and Tamur have no ability besides fighting. Huber's "+30 carrying
capacity" is never implemented (section 1.1).

## 5. Payment

Three charges, all hard-coded:

1. **Hire fee**, once, when hired (`cshell@0x10028b92-0x10028bc6`): subtracted from party gold
   (`cshell@0x10053e40`, clamps at 0) with `sounds\events\Gold01.wav`. Amounts in the table in section 1.1.
2. **Wage every 28 days.** The server party update (`object@0x10054e76-0x10054e8c`) runs the wage routine
   `object@0x100556c0` when game time passes a party-wide due time, then sets the next due time to now + 2419200
   seconds (`0x24ea00`, 28 days; an MM9 month is 28 days). For each hired retainer in a fixed order (279, 280, 281,
   282, 284, 285, 286, 288, 289, 290, 291, 283, 287) it subtracts the wage when the party has at least that much gold.
   When it has not, the party's gold is set to 0 and that retainer leaves (`object@0x10054840`, remove by MONSTERS row);
   if anyone left, the first PC able to speak says voice event 23 ("You don't have enough gold ...",
   `object@0x100559ad`). The manual's "cost per day" (MANUAL p.34) is wrong.
3. **Share of found gold**, intended: `cshell@0x10054100` (and the server copy at `object@0x100555e0`) adds up the
   percentages of the hirelings present: Hrolf 2, Tesar 3, Arienh 5, Randver 10, Beagan 5, Edina 10, Alberik 2,
   Ehwaz 15, Sowelu 10, Cleirach 20, Florie 20 (Ake, Alvar, Forad and Tamur 0). The gold-gain routines
   (`cshell@0x10053de0`, `object@0x10054d80`) then compute `gold += amount * (1 - share / 100)` in integer arithmetic.
   `share / 100` is 0 for any share below 100, and two retainers can reach at most 40 %, so in the shipped game **the
   share is never deducted**. Only Edina's +20 % has an effect.

Where these routines are called from (chest gold, corpse gold, quest rewards) was not traced.

## 6. Death, travel and party state

What the data shows:

- A hireling is a full party entity with HP, conditions and timed effects; the NPC health bars and HP text
  (`HUDCOORDS:128-130`, `:166-173`) show its HP, and the healers restore NPC slots as well as PCs (section 4.1).
- Hirelings stay in the party across map changes: the party object holds them (server `+0x14` to `+0x1c`, members 4-6),
  and the retainers' world objects stay hidden on every map load while the key is held. Forad's location dialogue
  depends on this (section 1.3).
- MONSTERS `Resurrect` is 0 for every hireling. No script or RUDE row resurrects or removes a hireling on death.

Knocked-out hirelings and the all-PCs-down case are covered in section 9.3. Whether boat or coach travel prices or
travel time count hirelings is still open.

A likely original bug: when a retainer leaves because his wage cannot be paid (section 5), the server removes him,
but nothing removes his hire key, so `Retainer.scr` keeps his world object hidden and he can never be hired again.

## 7. Presentation

### 7.1 HUD

`HUDCOORDS:113-144` and `:166-173` define three NPC slots on the right edge of the 800 × 600 screen, drawn only while
NPCs accompany the party:

| Element | Slot 1 | Slot 2 | Slot 3 | Size |
| --- | --- | --- | --- | --- |
| Frame (`NPCFRAME-NOMANA.pcx`) | 703, 143 | 703, 273 | 703, 403 | 87 × 131 |
| Portrait | 708, 162 | 708, 292 | 708, 422 | 60 × 80 |
| Overlay `NPCOVERLAY.pcx` (border pixels over the portrait) | at the portrait | | | 60 × 3 |
| Health bar `NPCFRAME-HEALTH-{GREEN,YELLOW,RED}.pcx` | 706, 245 | 706, 375 | 706, 505 | 71 × 8 |
| Health text "xxx/yyy" (SmallFont, centred) | 711, 244 | 711, 374 | 711, 504 | 50 × 9 |

The coordinate file also lists mana bars and mana text (`HUDCOORDS:132-134`, `:167-173`) and a frame with a mana well
(`NPCFRAME.pcx`, `NPCFRAME-MANA.pcx`), but the HUD routine loads only `Hud\NPCFrame-NoMana.pcx`
(`cshell@0x1001c2e7`; no other frame or mana image name is in `cshell.dll`). **Hirelings show an HP bar and no mana
bar.** The health bar uses three colour images, as the PCs' bars do (`cshell` strings `0x100d04a8-0x100d04e4`). The
PC frames by comparison are 126 × 150 with a vertical 11 × 82 health bar and a 70 × 11 mana bar (`HUDCOORDS:39-74`).
The frame art is in `mm9/extracted/ART/ART/HUD/` (`NPCFRAME*.pcx`, `NPCOVERLAY.pcx`, `TURNMARKERNPC.pcx`).

### 7.2 Portraits and facial animation

- `mm9/extracted/ART/ART/NPCPORTRAITS/NPC01` to `NPC15`, files `NPC-nn-ff.pcx`, 60 × 80, 8-bit, the same size as PC
  portraits (`PCPORTRAITS/PCnn/PC-nn-ff.pcx`). Folder number = MONSTERS row - 278 (Forad 15), as in section 1.1.
- Each NPC folder has 18 frames: 01, 04, 07, 10, 13, 16, 20, 21, 25, 26, 28, 30, 31, 32, 45, 47, 49, 51 (NPC05 also
  has 29). A PC set has 56 frames (`PCPORTRAITS/PC01`): groups of three (clean, bruised, variant) up to about 18,
  smiles and talking 19-27, collapse 28-29, drunk, sleepy and sick 30-35, yawns 39-40, mouth shapes 41-52 and stone
  53-55 (`level_generation/ui/hud_inventory/mm9_pc_portraits/PLAYBOOK.md:12-15`). The NPC set keeps the first frame
  of each group and a few talking, condition and mouth frames; it has no bruised, yawn or stone frames. As with the
  PCs, the acting at a number varies per character (NPC01's frame 28 is a head tilt, not a collapse).
- **Yes, hirelings are animated like PCs**: the HUD formats `NPCPortraits\NPC%.2d\NPC-%.2d-%.2d.pcx` with a frame
  number (`cshell@0x1001c35b`), the same pattern as `PCPortraits\PC%.2d\PC-%.2d-%.2d.pcx`. The formation screen shows
  frame 01 (`NPCPortraits\NPC%.2d\NPC-%.2d-01.pcx`, `cshell@0x1001911d`, `mmixformation.cpp`), so hirelings also appear
  in the marching-order screen. Frame choice is in section 9.4.

### 7.3 Talking to a hireling

Keys 5, 6 and 7 open the dialogue of the first, second and third NPC (MANUAL p.12, controls table "5-7 converse with
NPC"; MANUAL p.34). The conversation is the hireling's own RUDE graph at its root node, where the hire key unlocks
the dismiss row and the -15 service (section 1.2, 4.1). Clicking a portrait does the same as the key (section 9.1):
the first click makes the hireling the active member, a click on the already active hireling opens its dialogue.

## 8. What OpenYAMM already has

- **MM6-MM8 followers** (shared code): `game/gameplay/NpcFollowerTypes.h` (`HiredNpcFollower`: npcId, professionId,
  weeklyCost, abilityUsedDay, name, pictureId), `game/gameplay/NpcFollowerRuntime.h` (follower views, found-gold share
  `resolveFoundGold`, skill/stat/resistance bonuses, repair, travel and food reductions),
  `Party::addHiredNpcFollower` / `removeHiredNpcFollower` / `setHiredNpcFollowerAbilityUsedDay` (`game/party/Party.h:586-588`),
  limit `MaxNpcFollowerCount = 4` (`game/events/EventDialogContent.cpp:27`, `game/gameplay/GameplayDialogController.cpp:57`),
  the follower panel UI (`game/ui/GameplayOverlayTypes.h:561-569`, `game/ui/GameplayHudLayoutCache.h:25-75`), save data
  (`game/maps/SaveGame.cpp:1756`, `:2909`) and the hireling buff path (`game/party/EventSpellBuffs.h:17-20`). These
  followers are non-combat professions; MM9 hirelings are combat party members with HP, conditions and a HUD slot,
  so they need their own state next to these, not a new profession.
- **MM9 RUDE services**: `mm9RudeServiceName` names -10 hire, -11 dismiss, -15 town portal (`game/mm9/Mm9RudeDialogue.cpp:614-631`,
  `game/gameplay/GameplayDialogController.cpp:2046-2050`); -10, -11 and -15 currently fall through to "service is not
  implemented yet" (`GameplayDialogController.cpp:2599`). The -10/-11 rows already apply their key tails
  (`Mm9RudeDialogue.cpp:566-569`), which covers Forad's key 29 and the dismiss rows' key removal but not the retainers'
  hire keys. `devdocs/mm9/MM9_RUDE_SCR_INTEGRATION.md:296-298` lists both as open; its note that the -15 rows of
  NPC238 and NPC308 are "We'd like to be healed" is explained by section 4.1.
- **Converted maps**: the rebuilt cities already hide each retainer while its key is held, the `Retainer.scr :Init`
  rule: `level_generation/projects/mm9r_thjorgardcity/citylua.py:297-299` (450, 452, 453),
  `mm9r_sturmfordcity/citylua.py:342-348` (451, 454), `mm9r_drangheimcity/citylua.py:270-271` (455, 456),
  `mm9r_guberlandcity/citylua.py:337-338` (457, 459), `mm9r_guberland_blv/regionlua.py:416-424` (458),
  `mm9r_frosgardcity/citylua.py:409` (460), `mm9r_thronheimcity/citylua.py:385` (461) and
  `mm9r_lindisfarne_blv/regionlua.py:20-37` (462). Huber Carryall (Thjorgard, `shopkeeper.scr`) needs nothing.
- **Monsters**: rows 279-291 are not imported as monsters (`MM9_SPELL_MAPPING.md:104-105`); row 252 is imported as
  the hostile Afterworld Forad (9252). `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` lists Forad's world body
  (row 252, `mm9_forad`).

## 9. Combat behaviour (code)

Read from `object.lto` (server) and `cshell.dll` (client) as in the rest of this document. The short answer:
**a hireling fights like a PC that the player commands.** Hirelings do not act on their own: they are members 5-7 of
the party's active-member rotation, attack what the player aims at, with the player's Attack command, from the
party's position, and then pass the turn on.

### 9.1 Being the active member

- The party keeps one active member index (`+0x68`). Both the client setter (`cshell@0x10053d50`) and the server's
  "next ready member" routine (`object@0x10054b00`) accept indices 0-3 for PCs and 4-6 for the hired NPCs
  (`4 + NPC count`). The rotation goes 0 to 6 and skips members that are incapacitated (entity method `+0x64`,
  `object@0x100536e0`) or still recovering (`+0x68` flag, `object@0x1004af40`).
- Selecting a member (`cshell@0x1001eec0`, reached from the HUD controls, `cshell@0x100a5f86`) makes it active
  (`cshell@0x1001ef51`). Selecting the hireling who is already active opens his RUDE dialogue instead
  (`cshell@0x1001ef62-0x1001ef72` → `0x1001f090`, which builds the `npcdialog` screen at `cshell@0x1001f147-0x1001f18c`).
  While a spell waits for a target, selecting a hireling makes him the spell's target (`cshell@0x1001f0bb-0x1001f0f2`,
  message 0x79 with the NPC as target), so PC spells (Heal and the like) can be cast on hirelings.
- **Real time.** The Attack command goes to the server routine `object@0x100c1f50`. It takes the target under the
  crosshair (`object@0x100c6120`, which also reports whether it is in melee reach) and asks
  `object@0x100b3940` what the active member can do. For a hireling (`object@0x100b3b1b-0x100b3b7c`):
  bit 4 if `chooseSpell` (section 9.2) returns a spell, bit 1 if the target is in reach and attack 1 has damage
  (`+0x84`, maximum of attack 1), bit 2 if it is out of reach and attack 2 has damage (`+0x88`), bit 8 if nothing
  reaches. A spell wins: with bit 4 the server casts (`object@0x100c2011-0x100c20a5`); otherwise it makes a weapon
  attack (`object@0x100c2112` → `0x100b3bc0`); with only bit 8 the member is skipped and the next one becomes active
  (`object@0x100c20f2`).
- **Turn-based.** Starting turn-based combat (`object@0x100b5b90`) fills the turn list with the aware monsters, then
  every PC, then every hired NPC (`object@0x100b5cd1-0x100b5d25`), each with an initiative time. When the next turn
  belongs to a hired NPC (entity type 2), the server finds his slot (`+4`) and makes him the active member
  (`object@0x100b37ed-0x100b383c`, `call 0x10054c10`), exactly as for a PC; the player then gives his command. Monster
  turns run their own AI (`object@0x100b388e`). An NPC that has acted in turn-based mode ends his turn
  (`object@0x100b40a1-0x100b40b6`), in real time the next ready member becomes active (`object@0x100b40cc`).
  `Hud\TurnMarkerNPC.pcx` marks the hireling whose turn it is.

### 9.2 How a hireling attacks

- **Target:** the creature under the player's crosshair, the same target a PC would get. There is no own target
  choice, no "nearest hostile" and no defence of the party: an unaimed Attack does nothing for a hireling either.
- **Position and movement:** none. A hireling has no world body (MONSTERS `ModelName = n/a`). His spells start at the
  party (`object@0x1008a124-0x1008a136`: for an entity of type 2 the spell's source object is the player object
  `0x102b8cfc`), and melee reach is the party's reach as reported by the crosshair test.
- **Melee and ranged:** in reach he uses attack 1 (`Type1`/`DmgDie`/`DmgDieType`/`DmgBonus`, entity `+0x1f0`-`+0x1f8`,
  min/max getters `object@0x10053eb0`, `0x10053ee0`); out of reach he uses attack 2 (`Type2` dice, `+0x204`-`+0x20c`,
  getters `object@0x10053ec0`, `0x10053f00`) if it has damage. The weapon attack picks the projectile from
  `Projectile1` (`+0x224`) or the second `Projectile2` (`+0x264`) by attack kind (`object@0x100b4067-0x100b4081`);
  both are `0` for the melee retainers, so what Hrolf, Tesar and Randver's attack 2 looks like in flight was not traced.
  Hirelings without attack 2 (all except Hrolf, Tesar, Randver and the two casters' spells) cannot hit anything out of
  reach and are skipped.
- **Recovery:** after a weapon attack the server sets the hireling's recovery end to now plus his recovery
  (`object@0x100b4049-0x100b4062`), where recovery is the MONSTERS `Recovery` column (loaded to record `+0x144`, entity
  `+0x2a4`, `object@0x10052c71`) plus the modifier of timed effect 13/12 (`object@0x100537c0`; a haste/slow effect,
  not identified further). The units are the game's time units, the same clock as the 30 and 60 added for turn-based
  defaults (`object@0x100b3fda`, `0x100b3d04`); converting them to PC recovery needs a run of the game.
- **Casters (Arienh A'Klindor, Ake the Righteous).** `chooseSpell` (`object@0x10053210`, entity vtable `+0x44`) returns
  `Spl1` if `Spl2` is empty, `Spl2` if `Spl1` is empty, otherwise `Spl1` when `1 + rand % 100 <= SpellUse%1` and `Spl2`
  otherwise. Spell id 50 means "no spell" (MM9's spells are 0-48, `SPELL.txt`). Both casters have two spells, so
  **every attack they make is a spell**: Arienh casts Elemental Blast 60 % and Poison Cloud 40 % of the time, Ake
  Sparks 60 % and Elemental Bolt 40 %. They never melee, although their rows have melee dice. The roll is made again
  when the spell is cast (`object@0x100b4430-0x100b444d`), independently of the roll that decided "spell".
  - When: only when the player orders an attack while the caster is active (9.1). The cast message (`object@0x100c333f`,
    spell 50 = "caster's choice") takes the same path, so a quick-cast command with the caster active also casts his
    chosen spell. There is no autonomous casting and the player cannot pick which of the two spells is cast.
  - Skill and mastery: from the MONSTERS spell cells, parsed by the loader into id, mastery (N, E, M, G = 0-3) and two
    skills (`object@0x10043ec8-0x10044009`), copied to the entity (`object@0x10052cba-0x10052d14`): `Spl1` id `+0x2ac`,
    mastery `+0x2bc`, skills `+0x2c4`/`+0x2cc`; `Spl2` id `+0x2b0`, mastery `+0x2c0`, skills `+0x2c8`/`+0x2d0`. The
    spell takes them from the caster (`object@0x1008a1e4-0x1008a205`). So Arienh casts Elemental Blast at Expert with
    skill 6 (second skill 1) and Poison Cloud at Master with skill 7 (4); Ake casts Sparks at Normal with skill 3 (2)
    and Elemental Bolt at Normal with skill 3 (1).
  - Mana: none. MONSTERS has no spell-point column, the HUD draws no NPC mana bar (7.1), and the NPC cast branch
    (`object@0x100b4430-0x100b44a7`) creates and casts the spell with no spell-point test. Hireling casters cast without
    limit; only their recovery paces them.
- **Kills:** a creature killed by a hireling still gives the party its experience (`object@0x100b50bb-0x100b50d1`,
  `call 0x10054c60`), split among the PCs (section 3).

### 9.3 Monsters hitting the party, knock-out and party death

- **Which member a monster hits** (`object@0x10054ea0`): the party has a 3 × 3 formation grid of member pointers
  (`+0x3c`, slots 0-8; the formation screen places hirelings in it too). A d10 picks a row: 1 the back row, 2-3 the
  middle row, 4-10 the front row, so **70 % front, 20 % middle, 10 % back**; then a d3 picks a slot in that row,
  re-rolled while the slot is empty. An incapacitated pick restarts the whole choice unless all PCs are down. The
  rows follow the attack's direction: for one direction the front row is slots 0-2, for another 6-8, for a third the
  columns 0/3/6 (`object@0x10054ed0-0x10054f91`). Hirelings therefore take hits by their formation place, with the
  same odds as a PC in that place. A hit on a PC or a hireling plays the "was hit" voice events 14/15 by remaining HP
  (`object@0x100b4e8c-0x100b4f54`).
- **Knock-out instead of death.** Damage (`object@0x10053130`, entity vtable `+0x38`) lowers HP (`+0x54`); at 0 or less
  HP is set to 0 and a party NPC gets condition 16, Unconscious, while other entities of this class get 2, Dead
  (`object@0x10053190-0x100531bf`). Hirelings never go below 0 HP and never die from damage.
- **Recovery from knock-out.** Healing (`object@0x10053070`, vtable `+0x34`) adds HP up to the maximum and clears
  Unconscious once HP is above 0 (`object@0x100530bc-0x100530e3`); a Dead entity cannot be healed. Any heal therefore
  revives a hireling: a PC's Heal on his portrait (9.1), Sowelu's or Florie's service (4.1), or presumably rest and
  temples (not traced). Nothing removes a knocked-out hireling from the party: none of the damage, condition or
  party-death routines calls the NPC removal routine `object@0x10054840` (its only callers are the wage routine, section
  5, and the scripts' `RemoveNPC`).
- **Dead and Eradicated.** The condition setter (`object@0x10053460`) still accepts Dead (2) and Eradicated (5) for a
  hireling, so spells or effects that set them directly can kill one; Dead clears the other conditions and timed effects
  (`object@0x10053529-0x100535a0`). How the game cures Dead or Eradicated hirelings was not traced.
- **Party death.** The "everyone down" test (`object@0x10054cf0`) and the last-member-standing reaction
  (`object@0x10055a00`, expression 26 and voice event 33 on the last PC) count only the four PCs (`+0x60`). When all PCs
  are incapacitated, monsters stop choosing targets (`object@0x10055178-0x10055189`) and turn-based combat ends
  (`object@0x100b35d9-0x100b35e6`), even if hirelings are still standing: hirelings cannot keep a defeated party alive.
  What follows (MM9's defeat screen or respawn) and what it does to the hirelings was not traced.

### 9.4 Portrait frames

The server drives the NPC portrait frame (entity `+0x1b4`, changed flag `+0x1b0`), read by the client HUD:

| Situation | Frame | Source |
| --- | --- | --- |
| Normal | 01 | `object@0x100536b7` (when Unconscious is cleared) |
| Idle, every 1-300 time units while able to act | random of 04, 07, 10, 13, 16, 20 | `object@0x100542d0` (vtable `+0x9c`) |
| Unconscious | 28 | `object@0x10053511-0x10053518` |
| Some event (vtable `+0xa8`) | random of 30, 31, 32 | `object@0x10054450` |
| Set by the caller (vtable `+0xac`, used for talking and reactions) | argument | `object@0x100544b0` |

These are exactly the frames the NPC portrait folders contain (7.2); 21, 25, 26 and 45-51 are presumably the talking
and reaction frames chosen through `+0xac` (not traced).

## 10. Formations

MM9's "Party Formation" places all seven party members, PCs and hirelings alike, on a 3 × 3 grid. The formation
decides which member a monster's blow lands on, and nothing else. Code: `mmixformation.cpp` in `cshell.dll`
(`cshell@0x10018c30-0x10019c40`) and the party classes in both DLLs.

### 10.1 The grid and its rules

- **Cells.** Nine cells numbered 0-8, row by row: 0-2 the **front** rank, 3-5 the **middle** rank, 6-8 the **rear**
  rank, columns left to right. The screen draws cell `n` as control `500 + n` at x = 331 / 399 / 467 for the columns
  and y = 176 / 264 / 352 for front, middle and rear (`cshell@0x100191e1-0x10019534`, matching
  `ART/INTERFACESCREENS/FORMATION/PARTYORDERCOORDS.txt:5-15`, whose rank labels "Front Rank", "Middle Rank", "Rear Rank"
  sit at y = 190, 280, 370, `:17-22`). The texts are `GAMETEXT:73-77` ("Party Formation", "Rank", "Front", "Middle",
  "Rear").
- **Storage.** Each party object keeps the member list (`+0x04`, 7 entries: PCs 0-3, NPCs 4-6), one cell index per
  member (`+0x20`, 7 entries, -1 for none) and the grid of member pointers (`+0x3c`, 9 entries) (`cshell@0x10053e90`,
  `0x10053eb0`, `0x10053f00`; server `object@0x100551b0`). The party state reader rebuilds the grid from the seven cell
  indices (`object@0x10055445-0x10055474`), so a formation is saved as one cell number per member.
- **One member per cell.** A portrait can be dropped only on an empty cell; dropping it on an occupied cell cancels
  the drag and the portrait returns (`cshell@0x10019890`: `+0x48` of the target cell is tested at `0x100198c1`). There
  is no swap: with seven members on nine cells there are always two free cells to move through.
- **"Front line must be covered"** (`GAMETEXT:78`, the instruction "Drag and drop, front line must be covered."). On
  Exit the screen writes the arrangement to the party (`cshell@0x10019b00`) and runs the check
  `cshell@0x10053f30`: duplicates are moved to the lowest free cell, and every column is packed towards the front (an
  empty front cell takes the middle member of its column, an empty middle cell the rear member, then front again). If
  anything moved, the screen redraws the corrected formation and stays open (`cshell@0x10019b57-0x10019b72`); otherwise
  it closes. So a column may be empty, but nobody may stand behind an empty cell. There are no per-rank limits beyond
  the three cells. With seven members at least three columns are used, so a full party always has a full front rank.

### 10.2 Effects

- **Monster target choice** is the only reader of the grid on the server: the grid offsets `+0x3c` to `+0x5c` are read
  only in `object@0x10054ea0` (and written by the placement and rebuild routines), with no other use in `object.lto`.
  The choice (section 9.3): d10 = 1 rear rank, 2-3 middle, 4-10 front (`object@0x10054ed0-0x10054edd`,
  `0x10054f99`, `0x1005503b-0x10055050`), so **front 70 %, middle 20 %, rear 10 %**; a d3 then picks a cell of that
  rank, re-rolled while the cell is empty (`0x10054fce-0x10055036` and the two copies below it). If the whole rank is
  empty or the picked member is incapacitated, the whole choice starts again (`0x10055167-0x10055183`) until all PCs are
  down. The effect is that each living member's chance is his rank's weight divided by the number of occupied cells in
  that rank, renormalised over the living members.
- **Columns matter only through the attack's direction.** The selector's first argument rotates the grid: with 3 the
  rear rank is treated as the front (cells 6-8 get 70 %, 0-2 get 10 %), with 2 the columns are the ranks (0/3/6 get
  70 %, 1/4/7 20 %, 2/5/8 10 %) (`object@0x10054ee2-0x10054f91`). Most callers pass 0, the normal front-first order
  (`object@0x100091fa`, `0x1001173f`, `0x100b9450`, `0x100b9791`); two monster-AI callers pass a computed value
  (`object@0x1000f6a3`, `0x1001882f`), presumably the side the blow comes from. The value 1 leaves the rear-rank cells
  uninitialised and looks unused.
- **No other effect was found.** Melee reach, who may attack in melee, ranged attacks and spells use the crosshair
  target and the active member (section 9.1) and never read the grid; turn-based combat uses the same target selector.
  How traps and area spells choose the members they hurt was not traced, but they do not read the grid.

### 10.3 Defaults and changes of membership

- **New members go to the lowest free cell.** Adding a PC (`cshell@0x10053630`, server `object@0x100546a0`) or a hired
  NPC (`object@0x10054700` → `0x100551b0`) gives the member the first cell 0-8 that no member holds. A new party of four
  therefore stands with PCs 1-3 in the front rank and PC 4 in the middle-left cell; the first hireling or story
  companion goes to the middle centre (4), the next to middle right (5), the third to rear left (6), unless the player
  has rearranged the party, in which case the newcomer takes whichever cell has the lowest number among the free ones.
- **Unconscious or dead members keep their cell.** Nothing moves a knocked-out member; the target selector skips him by
  re-rolling (10.2), so his rank keeps its weight as long as another living member stands in it.
- **Removal.** Removing a hireling (`object@0x10054740`) shifts the following NPCs down in the member list together
  with their cell indices; whether the removed member's grid cell is cleared at once was not confirmed (the grid is
  rebuilt from the cell indices when the party state is read, 10.1).

### 10.4 The screen

- **Opening.** The key F ("F party formation screen", MANUAL p.12) or its keyboard-remap entry "Party Formation"
  (`GAMETEXT:136`; command name `PartyFormation`, `cshell` string `0x100d366c`). The game's command switch creates the
  screen (`cshell@0x100a5664-0x100a5697`, in `game.cpp`) and pushes it on the screen stack. No HUD button opens it in
  MM9; the HUD coordinate files have no formation element.
- **Layout and art** (`mm9/extracted/ART/ART/INTERFACESCREENS/FORMATION/`, 8-bit PCX):

| File | Size | Use |
| --- | --- | --- |
| `PARTYORDERBG.pcx` | 800 × 600 | full-screen background (`cshell@0x10018cde`) |
| `PARTYORDERCANCEL-{NORMAL,PRESSED,HIGHLIGHT}.pcx` | 100 × 50 | Cancel, control 510 at 699, 485, also on Escape (`cshell@0x10018cf6-0x10018d21`) |
| `PARTYORDEREXIT-{NORMAL,PRESSED,HIGHLIGHT}.pcx` | 100 × 50 | Exit (apply), control 509 at 699, 549 (`cshell@0x10018d53`) |

  Title "Party Formation" at 307, 76 (260 × 18); the rank labels at x = 174 (120 × 18); the nine 60 × 80 cells; the
  instruction text area at 170, 457 (437 × 82) (`PARTYORDERCOORDS.txt:3-27`). Each member is a draggable 60 × 80
  portrait showing frame 01 of his PC or NPC portrait set (`cshell@0x100190a4-0x100191c3`); pointing at one shows his
  name (`cshell@0x10019bf0`).
- **Interaction.** Drag a portrait to an empty cell (10.1); Exit applies and checks, Cancel or Escape closes without
  applying (`cshell@0x10019820-0x1001985a`: control 509 applies, 510 and 1000 close). Whether the game world pauses
  while the screen is open was not traced; it is pushed like the other full-screen menus.

## Open questions

These need more of the executable's code (or a run of the original game):

1. The units of `Recovery` and of the recovery clock, to convert hireling recovery to OpenYAMM's PC recovery.
2. The projectile and visual of the melee retainers' attack 2 (both projectile columns are `0`), and whether its
   damage type is the row's `Type2`.
3. What follows party defeat (all PCs down) and what it does to hirelings; how Dead or Eradicated hirelings are cured
   (temples, Raise Dead, resting).
4. Whether hirelings change boat and coach prices or travel days, and whether they rest, eat or sleep.
5. The first wage due time after a new game or a hire (the timer is party-wide, so the first charge may come early).
6. Whether the hire key really stays set after a retainer leaves unpaid (section 6), and what the client does with
   the server's removal.
7. Whether the once-per-day timers survive dismissal and re-hiring (the server builds a new entity on every hire).
8. Callers of the gold-gain routines: which gold sources get Edina's bonus.
9. Which reactions use the talking frames (vtable `+0xac`), and what triggers the 30-32 frames (vtable `+0xa8`).
10. How a formation edited on the client reaches the server's grid (the client writes its own party copy; the
    server rebuilds its grid when it reads the party state), and whether the removed hireling's grid cell is cleared.
11. Which attack directions the two monster-AI callers of the target selector pass, i.e. when side and rear attacks
    rotate the formation.
12. How traps and area spells pick the members they hurt, and whether the formation screen pauses the game.

## Proposed OpenYAMM table

One TSV row per hireling, world-owned, for example `assets_dev/worlds/mm9/data_tables/hirelings.txt`. Combat
values stay in the imported MM9 monster rows (the 13 retainer rows would be imported as non-hostile party actors,
not placed in maps), so the table only links to them.

| Column | Example (Ehwaz) | Meaning |
| --- | --- | --- |
| `RudeId` | 179 | dialogue id; key of the row |
| `Name` | Ehwaz | display name (`NPCNAME.rude`) |
| `Kind` | paid | `paid` (counts toward the two-retainer limit) or `story` (Forad, Tamur; may take the third slot) |
| `MonsterRow` | 288 | MM9 `MONSTERS.txt` row with the combat data |
| `PortraitFolder` | NPC10 | portrait set (MONSTERS row - 278; Forad NPC15) |
| `HireKey` | 459 | raw MM9 quest key set on hire, removed by the dismiss row (QBit 90000 + key) |
| `HireFee` | 1000 | gold charged once at hire |
| `Wage` | 1000 | gold charged every `WagePeriodDays` |
| `GoldSharePercent` | 15 | intended share of found gold (0 for no share; see the next column) |
| `ApplyGoldShare` | false | original behaviour (the integer bug never deducts it); a ruleset may switch it on |
| `Service` | town_portal | -15 service: `none`, `town_portal`, `heal`, `heal_cure` |
| `ServiceCooldownHours` | 24 | per-hireling cooldown of the service |
| `CuredConditions` | | `heal_cure` only: Cursed, Diseased, Insane, Poisoned |
| `Passive` | | `gold_bonus:20`, `xp_bonus:10`, `identify_always`, `repair_always`, `skill:Merchant+6`, `skill:DisarmTraps+4,Perception+4` |
| `WorldMap` | guberlandcity | map holding the world object |
| `WorldObject` | ShopkeeperHuman2MaleA13 | DAT object name to hide while `HireKey` is held |
| `Notes` | | free text |

World-wide rules beside the table (for example in `world.yml` or one `hirelings` header row): three NPC slots, at
most two `paid` unless a `story` hireling is present, wage period 28 days, an unpaid wage empties the purse and
dismisses that retainer, the -15 opcode dispatches on `Service`, and hirelings take no experience share. In combat
(section 9) hirelings are members 5-7 of the active-member rotation and of the formation grid, attack the
crosshair target from the party's position on the player's command, cast without mana when their row has spells,
and fall unconscious at 0 HP instead of dying. Huber
Carryall gets no row (the original cannot hire him); adding him would be a design decision.
