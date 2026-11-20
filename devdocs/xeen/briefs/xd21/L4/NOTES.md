# XD-21 Rivercity Robbers' Den, L4: notes

A new S dungeon built from its brief (L1 to L3 here; MAPS.md §0 and the dungeon row; QUESTS.md Q-C3 and T1-E) with
the Map Studio by one agent, 2026-11-15/16, under `devdocs/xeen/ACT2_BUILD.md` and REBUILD_PROCEDURE.md. MM7 world as
stand-in (`world: mm7`), as XD-01 to XD-05 and X1. Key `xd21`, map `xeen_xd21.blv`, map_stats 9137, qbits
110300-110303 used (110300-110339 reserved), items 12150-12151 (reserved 12150-12169).

State: `oymap validate` no issues (L1, L2, L3, L4); `audit --strict`: 0 faces in one plane; build warnings: one
placeholder (dice on the table) and the boss's name (below). `solve`: 11 of 11 sectors in 5 steps, nothing waits.
Playtest `playtest.yml` (99 steps) passes **4 of 4** on the final build (`output/studio_cal/xd21/four.out`,
`run/four/run_1..4.log`), ending on X2's quay at DOORS.md's arrival (see "The exit").

Scratch: `output/studio_cal/xd21/`. **The project files are generated:** `tools/plan.py` writes L1-L4 `plan.yml`,
`diagram.txt` and L1-L3 `project.yml`; `tools/gen.py` writes L4 `rooms.yml`, `objects.yml`, `wiring.yml`,
`project.yml` (`gen.py --l3` writes L3's `rooms.yml`). Edit them and run `v.sh` (generate, fmt, validate), `go.sh`
(build, install into `mount/`, optionally one playtest), `four.sh` (four runs against `mount_exit/`), `tour.sh <list>
<name>` (screenshots). Validate, build and install use `output/studio_play/xeen_root` directly; `root/` (a private hard-link copy with engine sounds linked in, before merge 38) is no longer used.

## Layout

The den is the hollow of the great bridge's south abutment, behind Rivercity's south quay. Frame: x east, y north, the
quay door at y 0, heights from the cellar floor. 11 rooms = 11 sectors, floor area 19.7 M units² as `metrics` counts
it (platform tops and the race's floor included; walkable 15.6 M).

| Room | Size | What |
|---|---|---|
| Quay cellar | 1,280 × 1,024, vault 448-576 | Arrival and the X2 exit (the quay door, plank leaf). A drain basin with a stone kerb, the river lapping in through a round culvert grate. Looks like a dead end; stepping to the north wall: "Wet footprints lead from the drain to the north wall and stop dead at the stones..." |
| Robbers' crawl | 320 × 2,300 | The hidden way: a secret sliding block of the cellar's own stone (`door:secret`, secret flag; quest bit `robbers_den_found`), then a brick passage with a tripwire (secret plate, once: a bolt, 12 damage to one member) |
| Dicing room | 1,536 × 1,280, vault 448-576 | Plank dicing table, benches, kegs; the dues box ("WHAT DID YOU EXPECT, MONEY?"); the scratched "NOW THIS IS A WILD TOWN." First fight. An arch east onto the race's west bank, a door north |
| Bunk room | 1,536 × 1,024 | Four plank bunks ("There is nothing on, in, or under the bed."), a loose brick (secret panel) with a 150-gold purse, once |
| **Undercroft of the great bridge** (set piece) | 2,816 × 1,792, arch 640-1,088 | One tall arch east-west, four pier buttresses; **the race** (a mill race off the river, 512 wide, 224 down, slime water flowing) cuts it north-south between two round grates; seven water stairs up onto the west bank at its south end (for anyone who falls in); the robbers' **plank bridge** drawn back onto the east bank, its **winch** (lever on a post) beside it |
| Sluice chamber | 2,176 × 1,024, vault 512-704 | The race pours in through a big round river grate (daylight, the river's roar); the old sluice wall across it planked over as a **catwalk** with rails: the way across. Doors to the bunks (west bank) and the fence (east bank, locked); an arch south into the undercroft's east half |
| Fence's store | 1,024 × 1,024 | Optional: crates, sacks, counting table, the fence's trapped chest. Locked: the boss's keys or a thief (Disarm Traps 3) |
| Boss's stair | 1,280 × 512 | Eight steps up 256 east; overheard: "...a royal tiara won't fence in Rivercity, boss. Too hot." |
| Robber Boss's quarters | 1,408 × 1,280 at 256, vault to 960 | Desk with the **ledger** (a message window: the tiara "not to be fenced", and "throw the catch by the hearth BEFORE you walk the passage"), bed, supper table, hearth, chandelier, the boss's trapped chest, the **catch** lever |
| Strongroom passage | 320 × 1,280 | Three grey slabs (secret plates): each fires darts at the whole party (10 each) every time until the catch is thrown |
| Vault | 896 × 768 | Behind the **iron door with three locks** (the boss's Ring of Keys): the strongbox on a plinth with **Princess Roxanne's tiara** (quest bit `tiara_recovered` on opening, a message once the tiara is in the packs) |

Loop: west bank → bunks → sluice catwalk → east bank → winch → plank bridge back west (the short way home).
Order of play (`solve.txt`): block → crawl/dicing/bunks/undercroft west → sluice, winch, the boss's stair → boss,
fence (skill) → (Ring of Keys) catch and iron door.

## Monsters (MM7 stand-ins), loot

| Xeen (MAPS/MONSTERS) | Built as | Count |
|---|---|---|
| Outlaws: Rogue 12 | MM7 Thief family tier b, Rogue (407, level 12), slot 1 | 6 markers × 2-3 ≈ 15 (dicing ×2, east bank, bunks ×2, fence) |
| Xeen Robbers (brawlers, 14) | MM7 Fighter Leather tier b, Raider (257, 14), slot 2 | 3 markers ≈ 7.5 (west bank, catwalk, foot of the stair) + 2 placed bodyguards |
| Outlaws: Thief 18 | MM7 Master Thief (408, 18), slot 1 tier c | 1 marker ≈ 2.5 (the boss's lieutenants) |
| Robber Boss | Master Thief 408, named "Robber Boss", carries the Ring of Keys, group 2 | 1 |

About 28 monsters, levels 12-18 (band 10-18), groups of 2-3; kill XP ≈ 8,900, 2.2k per member (MAPS 1.9k).
MM7's Thief family is the Erathian Sewers' own thieves' guild (3D models). Actor indices: 0, 1 bodyguards, 2 the boss
(the scene lists placed monsters by id).

Loot (Tres 2): fence's chest (level 2, 2 items, 350 gold, trap 2), boss's chest (level 2, 2 items, 400 gold, trap 2),
the vault's strongbox = the map's hoard one level up (level 3, 2 items, 800 gold, the tiara, trap 3), the purse (150).
map_stats lock 5 / trap 3 / perception 5 (MM7 Zokarr's Tomb's, a Tres 2 S dungeon). Items: `roxannes_tiara` 12150 →
MM7 Noble Crown 900 (a wearable helm, as the design's tiara is); `ring_of_keys` 12151 → Ring of Keys 629.

## Q-C3 and T1-E

Q-C3: Princess Roxanne (Castle Burlock, XD-07, not built) asks for her diamond tiara; the robbers under Rivercity's
bridge took it. Here: on first entry a message gives her errand (her own words from `aaze0066` #0, shortened); the
boss carries the vault's keys; the tiara lies in the strongbox; `tiara_recovered` (110300) and `robber_boss_slain`
(110301) are set; the message on taking it says to bring it back to her at Castle Burlock. Other bits: 110302
`robbers_den_found`, 110303 `robbers_vault_opened`.
T1-E (Thief → Rogue) is Roxanne's reward when the tiara comes back, given in XD-07 (MM9-style composite promotion); it
needs that map. In the den the thief's part is the fence's lock (Disarm Traps 3 picks it) and the trapped chests.

Original lines (decision of 2026-11-14): "Now THIS is a wild town." (Rivercity, `aaze0030` #23) scratched over the
dicing table; "There is nothing on, in, or under the bed." (#24) on the bunks; "What did you expect, money?" (#33) by
the dues box; Roxanne's "My servants have informed me that my diamond tiara has been stolen ... robbers that dwell in
Rivercity. They are led by a devious and cunning boss." (`aaze0066` #0) paraphrased in the arrival message.

## Measurements against shipped S dungeons

Shipped (`output/xeen_review/scale/dungeons.txt`, p25 / median / p75; MAPS S: ≤ 15 sectors, ≤ 20 M, 15-30 monsters):

| Figure | XD-21 | MM7 S | MM8 S | Zokarr's Tomb | Wine Cellar |
|---|---|---|---|---|---|
| Sectors | 11 | 6 / 8 / 18 | 5 / 9 / 13 | 12 | 10 |
| Floor (M units²) | 19.7 (walkable 15.6) | 6 / 12 / 19 | 11 / 17 / 20 | 7.0 | 7.0 |
| Monsters | ≈ 28 | 10 / 22 / 30 | 16 / 26 / 30 | 18 | 23 |
| Chests | 3 | 0 / 2 / 5 | 0 / 1 / 4 | 0 | 4 |
| Doors (metrics' door records) | 10 (7 doors, the bridge, 2 levers) | 4 / 6 / 10 | 0 / 4 / 6 | 6 | 8 |
| Loops | 1 | 0 / 0 / 1 | 0 / 0 / 1 | 0 | 0 |
| Secret faces | 9 (block, tripwire, 3 slabs, loose brick) | 0 / 1 / 3 | 0 / 1 / 4 | 0 | 1 |

`scale_bands.py`: bigger rooms 2.31 M (percentile 71, median 1.64), largest 5.63 M (47), typical ceiling 576 (72),
taller rooms 704 (62), doorway 256 (= the shipped median; percentile 9 because many shipped maps are wider). Monsters per
sector 2.5 (MM7 S Wine Cellar 2.3). Lights 13 points + 18 torches, 56 decorations.

## Textures

One family: **MM7 The Erathian Sewers** (`d01.blv`, "Thief guild and sewers"): `wall` (dark stone, the robbers'
rooms and their vaults), `twb2` (the bridge's dressed stone), `cfb1` (wet rough floor), `tfb07` (brown flagstones in
the robbers' rooms), `7slimywtr` (the race and the drain, liquid shader, flowing), `7trim9_32` (door edges, lever).
Furniture and doors from its MM7 cousins that share its walls: the Tidewater Caverns' (`7d17`, Thief map) and Wine
Cellar's (`7d16`) weathered planks `7trimda` (tables, bunks, crates, plank doors, the bridge, the catwalk), the Wine
Cellar's `7t1books1` (table tops), `7t1beds2` (blankets), `7tfb11` (the dart slabs). Outside the family, with reason:
`d1lggrt` (MM6 Free Haven Sewer's round culvert grate: bars over darkness; MM7 has no grate picture; XD-01 uses it too),
`xwiron` (XD-04's generated studded iron, the vault door). The generated cut-out `xngrille` was tried for the grates and
dropped (a 48-deep block shows both its faces through the bars, with magenta fringes).

Textures to generate (stand-ins meanwhile): a plank door picture for the den's doors and the quay door (now stretched
or tiled planks); a robbers' chalk mark for the worn block; a dues box (now an MM7 chest end, `7gt002c`); a ledger
book on the desk.

## Pictures (looked at)

`output/studio_cal/xd21/shots/` (30, `shots_sheet.jpg`), `shots_catch/` (the catch before and after), first looks
`look1/`, `look2/` (before and after darkening and the grate change), `cmp1314.jpg` (the bridge drawn back and out).
Judged: the grates and the race read well (18-20, 11-14); the bridge visibly runs out (13/14); the damp stone and
candlelight read as a den; the strongbox, the iron door and the lever (moves down when thrown) read. Weak: the worn
block and the dart slabs glow bright red for the new-game party (its Perception sees secrets: the engine's pulse; a
party without the skill finds the block by the footprints' clue); the winch post reads as a crate; the undercroft's
arch is two planes (a pitched roof), not round; rooms are plain rectangles.

## The exit

`door:xd21` → `xeen_x2.odm` at DOORS.md's **final** arrival (1280, 4172, 640, facing north; the door itself at 1280,
3772, 640 in the south quay's wall), relinked 2026-11-16 after X2 was finished (it was the provisional 1152, 4250).
The playtest walks onto X2's final build: `tools/exitmount.py` composes `mount_exit/` (this map's mount +
`output/studio_cal/x2/mount`, X2's map_stats with this map's row added) and the run ends on X2 at (1280, 4172, 631.5),
4 of 4. Re-run exitmount.py (after removing `mount_exit/`) after every install. With X2 absent the last 4 steps fail; a
map transition cannot be checked otherwise (Words needed 6).

## Words needed (workarounds used)

1. **A boss row**: `monsters[].hp` is ignored and the name shows only on the corpse (no `place_mon.txt` row), so the
   Robber Boss is an ordinary Master Thief (86 hp) named on death. Needs his own monster_data row (CHANGES A1).
2. **Engine sounds**: resolved in the studio's merge 38 (S8g: `engine/audio` counts). Since 2026-11-16 the project validates, builds and installs against `output/studio_play/xeen_root` directly; the private root `output/studio_cal/xd21/root` is no longer used (kept).
3. **A sunken level wall to wall**: a `levels` region must stay clear of the room's walls, so a race that runs into
   the walls can't be drawn. Built inset 48 at each end (a stone sill too narrow to walk) with the grate panel above.
4. **Panels below the floor**: `panels[].bottom` must be ≥ 0, so a grate at water level is impossible; the grates
   start at the bank's floor.
5. **Hinged doors are one stretched picture** (`tile` refused): the den's doors slide up (MM6-8 style) with tiled planks.
6. **Exit checks**: `evt.MoveToMap` from a map event writes no `map_transition_requested` trace (only house and
   boundary exits do), so "the transition is requested" can't be asserted; the run follows it onto X2's build.
7. **Bolster row**: resolved (merge 38): project.yml `map_stats.bolster: LowerToEqual`; install writes row 9137 of `bolster_maps.txt` (CHANGES A4).
8. Hidden decoration art: none needed. A real winch (a drum and crank) has no decoration; a post with a lever stands in.

## What the user should look at when playing

```
./tools/run_game.sh --isolated xd21 --world mm7 --map xeen_xd21.blv --assets "$PWD/output/studio_play/xeen_root" --extra-mount "$PWD/output/studio_cal/xd21/mount" --visible --seconds 0
```
(until the lead installs it in `xeen_root`). Look at: whether the hidden way in is findable without Perception (the
footprints line, then clicking the north wall's worn block); the race and the plank bridge (the winch on the east bank,
reached round by the bunks and the catwalk); whether the darts are fair with the ledger's warning; the boss fight (a
plain Master Thief until he has a boss row); the grates and the river sound; whether the den is too bright or too dark.

## Files

Created: `devdocs/xeen/briefs/xd21/L1/` (`plan.yml`, `diagram.txt`, `project.yml`), `L2/` (same), `L3/` (same +
`rooms.yml`), `L4/` (`plan.yml`, `diagram.txt`, `project.yml`, `rooms.yml`, `objects.yml`, `wiring.yml`,
`ids.lock.yml`, `playtest.yml`, `NOTES.md`; `.oymap/` history), `output/studio_cal/xd21/` (tools, root, build, mount,
mount_exit, runs, pictures). Nothing else changed (MAPS.md rows stand).

## Hostility pass (2026-11-16)

The user found monsters peaceful to the party beside hostile ones of their kind and monsters fighting each other
(devdocs/xeen/ACT2_BUILD.md, "Hostility pass"). MMerge's `hostile.txt` decides a slot monster's relation to the party
and two kinds' to each other; the studio now warns of both (`oymap build`) and the map says its relations in objects.yml
`relations` (the build's load event `evt:studio_relations`). Written by `output/studio_cal/xd21/tools/gen.py`: the
Fighter Leather family (256-258, the slot's Raiders) the party's foes. `playtest_hostility.yml` (written by
`output/studio_cal/hostility/gen_hostility_tests.py`) checks the slot and placed foes hostile, the peaceful ones
peaceful and the map's kinds, spawned side by side near the party, not taking each other on; it passes twice, as do the
map's other playtests.
