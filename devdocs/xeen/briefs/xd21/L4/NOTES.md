# XD-21 Rivercity Robbers' Den, L4: notes

A new S dungeon built from its brief (L1 to L3 here; MAPS.md §0 and the dungeon row; QUESTS.md Q-C3 and T1-E) with
the Map Studio by one agent, 2026-11-15/16, under `devdocs/xeen/ACT2_BUILD.md` and REBUILD_PROCEDURE.md. **Since
2026-11-20 a `world: xeen` map installed in `assets_dev/worlds/xeen/maps/` on the world's rows (last section, "Into
the world"); the sections before it describe the MM7 build.** Built first in the MM7 world as
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
./tools/run_game.sh --isolated xd21 --binary "$PWD/build-xeen/game/openyamm" --world xeen --map xeen_xd21.blv --assets "$PWD/assets_dev" --visible --seconds 0
```
(installed in the Xeen world since 2026-11-20). Look at: whether the hidden way in is findable without Perception (the
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

## Rebase, phase 0 (lane A8, 2026-11-20): the design part

What the move into the Xeen world (ROADMAP §6 phase 0, A8 step 3) applies, decided now. Nothing is rebuilt yet: the
map already has its placed engine sounds and bolster row, and every remaining change needs A1's world install (W5),
A2's rows or A3's hook table.

**Monsters (MAPS §0: 10–18, 28 monsters, 1.9k kill XP per member; MONSTERS_AND_ITEMS §2 Outlaws 12/18/30 and Evil
rangers 8/12/18).** MONSTERS_AND_ITEMS has no "Robbers" family: the brawlers become the robbers' crossbowmen, the Evil
rangers family's B tier, placed where they shoot across the race (the west bank, the catwalk, the stair's foot). One
of the dicing room's two markers goes, to keep the experience inside 15 %.

| Slot | Family, tier, level | Where (per marker [2, 3]) | Expected |
|---|---|---|---|
| 1 | Outlaws A, Rogue 12 | dicing (one marker), east bank, bunks ×2, fence | 12.5 |
| 2 | Evil rangers B 12 (crossbows) | west bank, catwalk, foot of the boss's stair | 7.5 |
| 1 | Outlaws B, Thief 18 | the lieutenants' marker by the boss, plus the two placed bodyguards | 4.5 |
| placed | **Robber Boss 22, boss row** (×3 hit points, about 340), carries the Ring of Keys | his quarters | 1 |

25.5 monsters, kill experience 8,300 for the party, **2.1k per member (+9 %)**; groups 2–3. The relations row
(`relations` in objects.yml) then names the Outlaws' and the rangers' rows hostile to the party, from A2's world
relations if they cover it.

**Treasure** stays: Tres 2; the fence's and the boss's chests at 2, the vault's strongbox (the hoard) at 3; lock 5,
trap 3, perception 5.

**Items and bits for A2 and A3:** Princess Roxanne's diamond tiara 12150 (a wearable helm; stand-in MM7 Noble Crown
900), the Ring of Keys 12151 (the robbers', stand-in MM8 629); qbits `tiara_recovered` 110300, `robber_boss_slain`
110301, `robbers_den_found` 110302, `robbers_vault_opened` 110303. Q-C3's errand in the arrival message and the
tiara's message are quest text: A3's hook text replaces them. T1-E (Thief → Rogue) is given at Castle Burlock (XD-07).

**Original lines** (for A3's ledger): "Now THIS is a wild town." (aaze0030 #23, scratched over the dicing table),
"There is nothing on, in, or under the bed." (aaze0030 #24, the bunks), "What did you expect, money?" (aaze0030 #33,
the dues box), Roxanne's "My servants have informed me that my diamond tiara has been stolen ..." (aaze0066 #0, the
arrival message; quest text).

**Studio words since the build:** placed engine sounds (four, already in), bolster `LowerToEqual` (row 9137, already
in). `no_spells`, doorway `floor`, model `turn` do not apply.

**Exit** checked against `briefs/x2/DOORS.md`: `door:xd21` → `xeen_x2.odm` (1280, 4172, 640) facing north, unchanged.

**Textures:** 18 distinct face textures in the build (S cap 30), none new (`xwiron` is XD-04's).

### Built: the drips loop

The two drips (`sound:crawl_drip`, `sound:vault_drip`) said `loop: false` with a wait; the game applies a wait only to
a looping sound (`game/audio/WorldAmbientSounds.cpp`), so each dripped once per arrival. `tools/gen.py` now leaves
`loop` out (looping, with their waits); the regenerated L4 differs only in those two lines. `validate` no issues,
`fmt --check` clean, `audit --reach` 11 of 11 sectors, 0 faces in one plane, `solve` all 11 (`audit_rebase.txt`,
`solve_rebase.txt`), exit to X2 (1280, 4172, 640). `mount_exit` recomposed (`tools/exitmount.py`). Playtests
`playtest.yml` 99 of 99 **4 of 4** (onto X2), `playtest_hostility.yml` 21 of 21 **4 of 4**
(`output/studio_cal/xd06/rb2_four.out`, logs `output/studio_cal/xd21/run/rb2_*.log`), run with `--asset-root
assets_dev` (the 2026-11-20 game no longer loads with `output/studio_play/xeen_root`).

## Into the world (lane A8, 2026-11-20)

Phase 0 step 3: the map moved off the MM7 stand-ins onto the Xeen world's rows and is installed in the world.

**What changed** (all in `output/studio_cal/xd21/tools/gen.py`; L4 regenerated, `oymap fmt`, `oymap record --author
agent:xeen-a8-xd21 --label "into the world"`, revision `a8f6ccc77ac0c5bb9c0dfed528508454`):

- project.yml `world: xeen`; notes without the stand-in wording.
- Map card slots: slot 1 `Xeen Outlaw` Dif 1, slot 2 `Xeen Ranger` Dif 2, [2, 3] per marker, weights 60/40: the slot
  name is the `Picture` column of the world's monster_data without the tier letter (`Xeen Outlaw A` → `Xeen Outlaw`),
  as A2's generated map_stats row 9137 has it (`source/map_rows.yml` XD-21). The world's row is what the game reads;
  install writes no map_stats row for a world that owns its map ids.
- Markers carry tiers: Rogue 11110 (slot 1 tier a) in the dicing room, on the east bank, the bunks ×2 and the fence's
  store; Evil Ranger 11131 (slot 2 tier b) on the west bank, the catwalk and the stair's foot; Thief 11111 (slot 1
  tier b) at the lieutenants' marker. `spawn:dicing_2` removed (9 markers).
- Placed: the Robber Boss → boss row **11113** (level 22, 342 hit points from the row; the scene's `hp` and `name`
  dropped: the row is named "Robber Boss", which shows while he lives, "Robber Boss 342/342" in the pictures);
  bodyguards → Thieves **11111**. He still carries the ring of keys.
- Items: `roxannes_tiara` **12150** (the world's "Princess Roxanne's Tiara"), `ring_of_keys` **12151** ("Robbers'
  Ring of Keys"). Qbits unchanged and named as `source/quests/q-c3.yml`: 110300-110303.
- `relations` dropped: the world's `relations.yml` (A2) makes `xeen_outlaws` (11110-11113) and `xeen_evil_rangers`
  (11130-11132) the party's foes (`long`) and sets no feud between them; the game reads it for every mounted world
  (`GameDataLoader`, devdocs/ENERGY_SHIELDS_AND_RELATIONS.md). The build's `evt:studio_relations` is gone (30 handlers).
- Exit unchanged: `door:xd21` → `xeen_x2.odm` (1280, 4172, 640) facing north.
- Q-C3 hooks: `data_tables/quest_hooks.yml` has no `q-c3.*` entry yet and `xeen_quests.lua` no hook (A3 makes Q-C3
  full later), and build-xeen's oymap has no `hook:` word. The map keeps its own messages. **To wire when Q-C3 is
  full:** `evt:arrive` → `q-c3.arrival` (text), `evt:secret_door` → `q-c3.secret_door`, `evt:boss_dead` →
  `q-c3.boss` (text), `evt:vault_door` → `q-c3.vault_door`, `evt:chest_vault` → `q-c3.vault` (text, else_text); each
  hook's qbits and items are the ones the map already sets.

**Checks** (files in `output/studio_cal/xd21/`):

- `oymap validate` no issues; `oymap fmt --check` clean.
- `oymap build`: 11 rooms, 601 faces, 10 doors, 9 spawns, 30 events, 3 chests. Warnings: the known placeholder
  (dice), and two hostility warnings that are the studio's, not the map's: it reads `engine/data_tables/hostile.txt`
  only and not the world's `relations.yml`, so it calls 11110, 11111 and 11131 friendly to the party (the game makes
  them hostile: `playtest_hostility.yml` below).
- Installed with `oymap install <L4> --build output/studio_cal/xd21/build --root assets_dev`: `worlds/xeen/maps/
  xeen_xd21.{blv,scene.yml,studio.yml}` and `worlds/xeen/events/maps/xeen_xd21.lua`, nothing else.
- `oymap audit <installed blv> --world xeen --assets assets_dev --reach --solve` (`audit_world.txt`): 0 faces in one
  plane, 11 of 11 sectors with every door out of the way, the known `thing.in_doorway` warning (fence_barrel) and
  squashed-plank info, as before. `oymap solve` (`solve_world.txt`): 11 of 11 in 5 steps, never reached 0, the last
  step needs item 12151, carried by the boss; exit xeen_x2.odm at 1280, 4172, 640.
- Playtests from `assets_dev` (`world_play.sh`, `build-xeen/game/openyamm --asset-root assets_dev --world xeen`, one
  game at a time): `playtest.yml` 95 of 95 **4 of 4**, `playtest_hostility.yml` 24 of 24 **4 of 4**
  (`world_four.out`, logs `run/world/main_1..4.log`, `host_1..4.log`).
- Pictures `world_shots/` (15, `world_shots_sheet.jpg`, `world_tour.sh world_tour.py world_shots`): every robber
  stands as a Xeen row with a 3D model (A2's stand-in bindings: Rogues green-cloaked, Thieves purple, the boss brown,
  the Evil Rangers red archers); "Robber Boss 342/342" and "Evil Ranger 50/50" over them; no missing texture or
  decoration. As before: the worn block glows red for a party with Perception, the winch reads as a crate.

**Not tested, and why:**

- **A `world: xeen` scenario.** A headless run loads the active world's first map_stats map before its first step
  (`GameDataLoader::loadInitialMap`, called by the runner's `ensureGameDataLoaded`; scenarios have no start-map
  override), and Xeen's first is `xeen_x1.odm`, not installed (A5): `new_game_flow` fails with "Failed to load initial
  map asset for xeen_x1.odm". Both playtests therefore say `world: mm7` (header comment): the map, its monster and item
  rows and the world's relations are the Xeen world's (rows and relations.yml apply whatever the world), but the Xeen
  world's own common scripts (`xeen_common.lua`, `xeen_quests.lua`) do not run. Change both to `world: xeen` once X1 is
  installed. The tour (`--world xeen --map xeen_xd21.blv`) did run in the Xeen world.
- **The exit onto X2.** X2 is not installed; the quay door's OK loads `xeen_x2.odm` and fails ("Failed to load
  initial map asset for xeen_x2.odm"). The playtest ends at the leave dialog (OK offered); its last comment says what
  to add back once X2 is installed. The destination is checked statically (the Lua's `evt.MoveToMap`, solve's exit).

**Tool and world defects found** (for A1 and A2):

1. build-xeen's oymap, indoor projects: `validate`/`build` with `--assets assets_dev` refuse the world's monster rows
   ("there is no monster number 11111 in monster_data.txt"): `IndoorBuild.cpp` `loweringOptionsOf`/`dataTable` read
   only `engine/data_tables`; W5's `readWorldTable` is used by the outdoor build only. Shown by
   `openyamm-studio/build-xeen/oymap validate devdocs/xeen/briefs/xd21/L4 --assets assets_dev`. Worked round without
   stand-ins: `tools/worldtables.py` composes engine + world rows of monster_data, monster_descriptors, items and
   map_stats exactly as `readWorldTable` does into `worldtables/`, passed as `--mount`.
2. The studio's hostility warnings read `hostile.txt` only, not the world's `relations.yml` (build output above).
3. `oymap solve <installed blv> --world xeen` names the ring's carrier with an empty name ("carried by the monster  in
   sector 1"): it takes the scene's actor name and does not fall back to the row's name.
4. Headless scenarios cannot start in the Xeen world until X1 is installed (above).
5. A2's tiara row 12150 is `Misc` with no equip stat; the design (above) had it as a wearable helm. Data, A2's call.

**Recipe for XD-06 and XD-12** (and XD-27): what to repeat and what to avoid.

1. In gen.py: `world: xeen`; slots named `Xeen <Family>` (the Picture column without the tier letter; check with
   `grep -P "^<id>\t" assets_dev/worlds/xeen/data_tables/monster_data.txt | cut -f1-3`) with A2's Dif from
   `map_rows.yml` and the generated `map_stats.txt` row; every marker `tier` a/b/c as the design; placed bosses by row
   id with no `hp` and no `name` when the row has the name; items by the world's ids; drop `relations` when the world's
   `relations.yml` covers the families (check its `relations:` and that no feud sets two of the map's families on each
   other); clear the stand-in wording.
2. Copy `tools/worldtables.py`, `v.sh`, `go.sh`, `world_play.sh`, `world_tour.sh` from this folder (change the key).
   Compose the world tables before every validate/build (`v.sh` and `go.sh` do), and pass `--mount <work>/worldtables`
   until the indoor build reads world tables; never write the composed tables into assets_dev.
3. Build with `--out output/studio_cal/<key>/build`, install with `--root assets_dev` (writes only the map's four
   files), then audit/solve the installed blv with `--world xeen --assets assets_dev`, `fmt --check`, `record`.
4. Expect the two studio hostility warnings per family that hostile.txt lacks; prove hostility in the game instead.
5. Playtests: `world: mm7` (until X1 is installed), item ids and monster ids replaced, the exit ended at the leave
   dialog when the destination map is not in the world. Run with `--asset-root assets_dev --world xeen`, one game at a
   time; `world_play.sh` makes a fresh user-data folder per run (no `rm` needed).
6. A tour: `--binary build-xeen/game/openyamm --world xeen --map <stem>.blv --assets assets_dev`, shots from the
   doorways towards each marker without `actor kill`, so the rows stand where they spawn.
7. Q-C hooks: look for `<quest>.<hook>` in `data_tables/quest_hooks.yml`; where a hook has a `call`, call it from a
   `lua:` effect in place of the map's own message; where not, keep the message and list it as "to wire".


## World playtests, hooks and dressing (lane A8, 2026-11-20)

The three things the move into the world left, done as XD-27 and XD-06 did them. All map changes in
`output/studio_cal/xd21/tools/gen.py`; L4 regenerated, `oymap fmt`, `oymap record --author agent:xeen-a8-xd21 --label
"world playtests, hooks, dressing"` (last revision `650823cdf3400a5b402a835e0f1f5c53`), installed again.

**Playtests in the Xeen world.** `playtest.yml` and `playtest_hostility.yml` say `world: xeen`; `world_play.sh` runs
`build-xeen/game/openyamm --asset-root assets_dev --world xeen --map xeen_xd21.blv` (the `--map` start makes the den the
initial map, so X1 need not be installed), and `xeen_common.lua`/`xeen_quests.lua` run with the hooks. X2 is still not
installed: the main test ends at the quay door's leave dialog (its last comment says what to add back).

**A3's Q-C3 hooks** (`assets_dev/worlds/xeen/data_tables/quest_hooks.yml`, all five present now):

| Hook | Event | Wiring |
|---|---|---|
| `q-c3.arrival` | `evt:arrive` (one-shot timer) | `lua: XeenQuests.hook("q-c3.arrival")` in place of the map's errand message |
| `q-c3.boss` | `evt:boss_dead` (death timer) | the hook sets `robber_boss_slain` 110301 and shows "The Robber Boss falls ..." (was the map's bit and status text) |
| `q-c3.vault` (once) | `evt:chest_vault` | the hook sets `tiara_recovered` 110300, gives the tiara 12150 and says so; a later opening its else text "What did you expect, money?". The strongbox no longer holds the tiara itself (one tiara), and `evt:tiara_found` (the map's second window for the same moment) is gone |
| `q-c3.secret_door` | `evt:secret_door` | no `call`: the map sets `robbers_den_found` 110302 as before |
| `q-c3.vault_door` | `evt:vault_door` | no `call`: the map sets `robbers_vault_opened` 110303 as before |

The chest's event calls the hook on every click (no condition), so no `else_effects` are needed: the hook's own `once`
gives the else text. The strongbox's trap goes off on the first click and leaves it shut, and the hook runs on the
click that opens it.

**Dressing** (`devdocs/xeen/formats/DRESSING.md`). Every room's props measured on the installed blv before and after
(files in `output/studio_cal/xd21/dressing/`): A7's `check_dressing.py` on the export (`check_*.txt`), A7's `measure.py`
unedited on a renamed export (`tools/named_export.py`, XD-06's, `measure_*.txt`), and `tools/walk_lines.py` (after
XD-27's, `walk_*.txt`): furniture platforms as rectangles (edge at least 64 from a line), decorations as circles
(decoration_data's radius + 64), chests, against the lines between each room's openings (the export's portals), the
start and what the party walks to (worn block, bridge landings, winch, catwalk ends, desk, catch, chests, dues box);
architecture (sills, pier buttresses, catwalk, plinth, the winch post the lines end at) is skipped. `gen_before.py`
is the generator before the moves.

- Before: `check_dressing` 8 findings (the supper table's goblet and fruit on the line from the boss's door to the
  strongroom passage, the crawl's bones 40 and the strongroom's corpse 76 from their passages' centre lines; the bunk
  room's sack 130 from its doorway, the fence's barrel 126 (standing in front of his door; the audit's known
  `thing.in_doorway`), his flour sack 298 and the vault's barrel 268); `walk_lines` 8 of 46 (the dicing table and both
  benches in the middle of the room, across all three lines between its doors; the boss's hearth, with its fire, right
  in front of the strongroom passage though its note said "west of" it; the supper table; the bones, the fence's barrel,
  the corpse). The fence's crate stack stood 258 from his doorway. Measure: barrels to wall median 148 (max 188), to a
  portal min 126; sacks to a portal min 130; barrels 7 singles and 1 pair.
- Moved (nothing removed): the dicing table (448 → 384 long) and its benches (384 → 320) to the south-west, with the
  dice, candle, goblets, plate and the table's light; the dues box up the west wall to y 4480 (offset 336), clear north
  of the table; the kegs as a pair into the north-west corner, the cask with the barrel as a pair against the north
  wall in the north-east corner; the bunk room's sack and bowl from before its door to beside bunk 1; the fence's barrel
  and flour sack into the store's north-west corner with the other sack (a storeroom clump, 328-360 from the doorway),
  his crates 80 east and 48 south (342 from the doorway); the vault's barrel to the east wall (364 from the door);
  the hearth (384 → 320 long) to the north wall's west end, the catch between it and the passage (as the ledger says,
  "by the hearth"), the supper table to the south-east, the boss's chest from beside his door to beside his bed; the
  crawl's bones and the strongroom's corpse to their walls.
- After: `check_dressing` 0 findings, `walk_lines` 0 of 46. Measure: barrels to wall median 82 (max 188), to a portal
  min 328; sacks to wall max 124, to a portal min 347; barrels 5 singles and 2 pairs; 2-4 containers per room; the one
  clump (barrel and two sacks) in the fence's store. The audit no longer reports `thing.in_doorway`.
- Pictures (`output/studio_cal/xd21/dress_shots/`, sheet `dress_shots_sheet.jpg`, `world_tour.sh dress_tour.py
  dress_shots`, looked at): the dicing room from the den door and from the arch (table and benches in the south-west,
  lanes to the three doors clear, the dues box free on the west wall), its north-east pair, the bunk room and the fence's
  store from their doors (the clump in the corner beside the door, the crates on the south wall), the boss's room from
  its door (hearth west of the passage, the catch between) and towards the south-east (supper table, chest by the bed),
  the vault, the crawl's bones and the corpse against their walls. No missing texture or decoration in the log.

**Checks** (files in `output/studio_cal/xd21/`):

- `oymap validate` (with `--mount worldtables`): no issues. `oymap fmt --check`: clean.
- `oymap build` (`build_world.txt`): 11 rooms, 601 faces, 10 doors, 9 spawns, 29 events, 3 chests; the known dice
  placeholder, the two studio hostility warnings (hostile.txt, not relations.yml) and, new, "nothing tells the player
  on arrival why he is here" (the studio does not see the hook call, as XD-06 and XD-27).
- Installed with `--root assets_dev`: `worlds/xeen/maps/xeen_xd21.{blv,scene.yml,studio.yml}` and
  `worlds/xeen/events/maps/xeen_xd21.lua` only.
- `oymap audit <installed blv> --world xeen --reach --solve` (`audit_world.txt`): 0 faces in one plane, 11 of 11
  sectors with every door out of the way, only the squashed-plank info. `solve` (`solve_world.txt`): 11 of 11 in 5
  steps, never reached 0, the last step needs 12151 (carried by the boss); exit `xeen_x2.odm` at 1280, 4172, 640.
- Playtests in the Xeen world, one game at a time (`world_four.sh`, `world_four.out`, logs `run/world/main_1..4.log`,
  `host_1..4.log`): `playtest.yml` 101 of 101 **4 of 4**, `playtest_hostility.yml` 24 of 24 **4 of 4**. The main test
  now asserts the three hook windows by text (arrival with `present_dialogs`; the boss's window right after he falls,
  before a walk closes it), exactly one tiara 12150 after the strongbox and still one after a second opening (the
  else text), the Ring of Keys 12151 from the boss's corpse, and all four bits at the quay door; the dues box and the
  catch are walked to at their new places.

**For A3:** `q-c3.arrival`'s text ("The robbers' den, under the great bridge ...") no longer says why the party is here
(Roxanne's tiara), which the map's message did, and `q-c3.vault`'s does not say where the tiara goes (the map's removed
`evt:tiara_found` said "Take it back to her at Castle Burlock"). XD-06 reported the same for `m10.yak_arrival`.

## Exit onto X2 and merge point 3 (lane A8, 2026-11-20)

**Studio checks against assets_dev** (A1's merge point 3, `openyamm-studio/build-xeen/oymap`): `oymap validate <L4>
--assets assets_dev` no issues; `oymap build <L4> --assets assets_dev --out output/studio_cal/xd21/build`
(`build_assets_dev.txt`): 11 rooms, 601 faces, 10 doors, 9 spawns, 29 events, 3 chests, byte for byte the build with
the `worldtables/` mount (blv, scene, Lua and build.json identical), and the same as the installed files, so no
re-install. The two hostility warnings are gone (the studio reads `relations.yml`); left: the dice placeholder and
"nothing tells the player on arrival" (the hook call, as before). The map had no `relations` rows left to drop.
`v.sh` and `go.sh` now use assets_dev alone; the check root `output/studio_cal/xd21/worldtables/` is deleted
(`tools/worldtables.py` kept, unused). `oymap audit <installed blv> --world xeen --assets assets_dev --reach --solve`
(`audit_mp3.txt`): 0 faces in one plane, 11 of 11 sectors with every door out of the way, the squashed-plank info.
`fmt --check` clean.

**The way out.** X2 (A5) is in the world; its door is where DOORS.md says (unchanged in A5's rebase: `door:xd21` in
`x2/L4/project.yml`, X2's event 114 "Enter the Robbers' Den", face hit at 1280, 3772). `playtest.yml` now walks out:
the quay door's OK, `follow_map_move`, `assert: {map: xeen_x2.odm}` and the party at **(1280, 4172), z 631.5**
(radius 160), the tiara and the keys still carried. The exit's arrival needed no change.

**The way in** (`playtest_way_in.yml`, new): a new party on X2 at the arrival, set facing the door 222 in front of it,
`press_interact` hits X2's event 114 and the party lands at the den's start (-2560, 320, 0) with q-c3.arrival's window.

**Playtests 4 of 4** (`world_four.sh` → `world_four_mp3.out`; `build-xeen/game/openyamm --asset-root assets_dev
--world xeen`, `--map xeen_xd21.blv` except the way in; one game at a time, exact PIDs; logs `run/world/main_1..4.log`,
`host_1..4.log`, `wayin_1..4.log`): `playtest.yml` 106 of 106, `playtest_hostility.yml` 24 of 24,
`playtest_way_in.yml` 14 of 14, each **4 of 4**.

## Hooks and dressing, D-7 (2026-11-20)

Touch-up by `agent:xeen-a8-touchup` (lane A8). Changes in `output/studio_cal/xd21/tools/gen.py` (copy before:
`gen_before_d7.py`). The generator reproduced L4 byte for byte before the change. `v.sh`, `oymap record --author
agent:xeen-a8-touchup --label "first-arrival window, D-7 dressing"` (revision `31175aba6d4d5ec797d4867532168eff`). Built to
`output/studio_cal/xd21/build_d7` and installed with `--root assets_dev` (the map's four files).

- **First arrival only** (from S, via the orchestrator): `evt:arrive`'s window (`q-c3.arrival`) opened on every entry and
  paused the spawned monsters until it was closed. It now has `condition: {not: {qbit: arrived_once}}` and sets `arrived_once`
  **110304** (free in 110300-110339; project.yml `qbits`). **For A3:** register it in q-c3.yml (`tools/xeen/quests.py`
  reports "XD-21: built qbit arrived_once (110304) is in no quest file").
- **Dressing:** `oymap audit --world xeen` before **0 errors / 2 warnings**: `cellar_bucket` 480 from the nearest wall,
  and a clump of 3 containers in the fence's store (sector 6). Fixes: the bucket went from the middle of the quay cellar to the east wall
  by the drain basin's kerb, (-2016, 504). The fence's store is a real storeroom (stolen goods, crates, sacks), so
  `room:fence_store` has `store: true`. After: **0 / 0**. No "Dressing exceptions" are needed.
- **Checks** (`output/studio_cal/xd21/`): `validate` no issues; `fmt --check` clean; `build`: 11 rooms, 601 faces, 10
  doors, 9 spawns, 29 events, 3 chests. It warns about the dice placeholder, and again "nothing tells the player on arrival"
  (the studio skips a conditioned timer; a defect for A1, see XD-12's notes). `audit --reach --solve` (`audit_d7.txt`): 0 faces in
  one plane, 11 of 11 sectors, no findings. `solve_d7.txt` is identical to `solve_world.txt`.
- **Playtests** (unchanged files; from assets_dev in the Xeen world, one game at a time, `/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/f070ad2b-085f-4ea8-986a-1b63e2657a52/scratchpad/d7/play_once.sh`, logs
  `/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/f070ad2b-085f-4ea8-986a-1b63e2657a52/scratchpad/d7/run/`): `playtest.yml` 106 of 106, `playtest_hostility.yml` 24 of 24, `playtest_way_in.yml` 14 of 14, **each 1 of 1**
  (the orchestrator's handover stopped the work before the 4 of 4).

**Still open, next steps:** (1) `output/studio_cal/xd21/world_four.sh` for **4 of 4**. (2) A re-entry step showing the
window only once: in `playtest_way_in.yml`, after the arrival window, leave by the quay door (OK, `follow_map_move`),
enter again from X2 (event 114), then `advance_runtime: {seconds: 3, present_dialogs: true}` and
`assert: {dialog: {active: false}}`. (3) A picture of the bucket by the basin (not taken). (4) A3: register 110304.

## Session 3 (2026-11-20): 4 of 4, re-entry, picture

Lane A8. `oymap audit <stem> --world xeen --assets assets_dev` (studio merge point 7) on the installed map: no dressing finding. A3 has registered `arrived_once` 110304 in q-c3.yml. Next steps (1)-(3) of the D-7 section are done.

- **Re-entry step** in `playtest_way_in.yml`: the window ("The robbers' den, under the great bridge.") shows once and
  sets 110304; the party leaves by the quay door (event 17, OK), comes back through X2's door, and no window opens.
  28 steps.
- **4 of 4** from assets_dev (`world_four.sh`, logs `output/studio_cal/xd21/run/world/`): `playtest.yml` 106,
  `playtest_hostility.yml` 24, `playtest_way_in.yml` 28 steps, each 4 of 4.
- **Picture** (`/home/pjasicek/github/OpenYAMM/output/studio_cal/a8_s3/props/xd21_sheet.jpg`): the bucket stands against the east wall by the drain basin's kerb, out of
  the way.

## The vault strongbox's gold (lane A8 session 5, 2026-11-20)

A3's playthrough chain found the strongbox (event 12, `chest:vault`, 800 gold) gave 0 gold on Take All. The gold is
there: the hook's window (A3's `q-c3.vault`, shown by the same event that opened the chest) closes the chest with it,
so Take All after closing the window takes from nothing (probe `output/studio_cal/xd21/vaultgold/`: Take All with the
window still open gives +1,090; the hook first and the chest after behaves the same). **Fix in the map**
(`tools/gen.py`, copy before `gen_before_vaultgold.py`): `evt:chest_vault` has `condition: {qbit: tiara_recovered}`
with the hook as `else_effects`, so the first use is the hook alone (the tiara and its window) and the strongbox opens
on the gang's takings from the next use on (its trap goes off then). The hook's else text ("What did you expect,
money?") is no longer reached. Rebuilt and installed (`b_174157`); `playtest.yml` asserts the hook's window, then
`loot_chest(12)` gives at least 800 gold (+2,067, +976, +1,412, +1,433 in the four runs) and no second tiara.
**4 of 4** (`world_four.sh`, `four_vaultgold.out`): main 104, hostility 24, way in 28 steps.
For A3: the chain's segment 17 must loot after the window (`close()`, then `loot_chest(12)`); `else_text` may go.
For A1: a window from an event that also opens a chest closes the chest when dismissed (engine; the map now avoids it).

## Light audit (merge point 14)

By `agent:xeen-a8-lights` (lane A8), 2026-11-20, on A1's light-fixture audit (`devdocs/xeen/formats/LIGHTS.md`,
`output/xeen_a1/lights_xeen.txt`). Changed in the generator (`output/studio_cal/xd21/tools/gen.py`, copy before the
change `gen_before_lights.py`; the generator reproduced the project byte for byte first), L4 regenerated, `oymap fmt`,
`oymap record --author agent:xeen-a8-lights --label "lights audit (merge point 14)"`.

- The boss's chandelier hung from the barrel vault's springing (832), 126 under the crown: it now hangs from the crown
  (960; height 618), its top 2 into it.

- **Audit** (`oymap audit --reach --solve` on the installed map, `output/studio_cal/xd21/audit_lights.txt`): lights
  errors/warnings before **0/1 (ceiling_gap)**, after **0/0**; no dressing finding. **Light exceptions:** none.
- **Installed** by `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh xd21` (build `output/studio_cal/xd21/b_192745`), baked
  (`output/studio_cal/a8_s5/bake.sh xd21 assets_dev`, profile `tools/lighting/baked_indoors/profiles/xeen_xd21.yml`
  (new: XD-08's values)), `tools/lighting/stale_bakes.py --check` lists none of the lane's maps. **Playtests from
  assets_dev, each 4 of 4** (world_four.sh; record `output/studio_cal/xd21/lights_post.out`): main 4/4 (104 steps); host
  4/4 (24 steps); wayin 4/4 (28 steps).
- **Pictures** `output/studio_cal/xd21/shots/lights_mp14/`, looked at: the chandelier hangs from the vault's crown.

## Session 7 batch (winch sound, A8 session 7, 2026-11-20)

- AU's `xeen_winch` (62510) plays at the winch post (576, 3712, 192) when the winch runs the plank bridge out
  (`evt:winch` `effects`, `tools/gen.py`; copy before: `gen_before_s7.py`).
- Audit (oymap 20:45:55, texture fit): 0 errors; 2 warnings, kept (below). Recorded, installed, baked; tests from
  assets_dev 4 of 4 (104, 24, 28 steps; `output/studio_cal/xd21/s7_post.out`).

**Texture fit exceptions:**
- `xwiron` `tile_seams` on the strongroom's iron door (faces 570, 571, 256 x 256, 2 x 2 plates): XD-04's studded
  plates meet in a line top and bottom, which reads as four riveted plates on a vault door.

## Session 24 (A8): merge point 35 tests

Rebuilt under oymap 12:46:47 for A1's room step tops (`evt:dicing_seen`, `evt:sluice_seen`, `evt:undercroft_seen`;
only the .blv changed), installed 17:15, baked, every test 4 of 4 from assets_dev on merge point 35; audit 0 / 2 (as
before).

## Session 26 (A8): plank door pictures (F12)

- The den's five plank doors (door ids 1 boss, 2 bunks, 3 den, 4 fence, 6 sluice; events 3, 8, 14, 18, 23) showed the
  plank strip `7trimda` laid across a folding slide_up leaf. Each is now a sliding pair (`kind: slide_left, leaves: 2`)
  of MM7's weathered Z-braced plank wings `hhm1d | hhm1d2` (the den's grey planks), one 128 x 256 wing per leaf of the
  256 x 256 opening (`tools/gen.py` `PLANKPAIR`; before: `output/studio_cal/a8_s26/before/xd21/gen.py`). The fence
  door was not on the reported list but had the same strip. A hinged pair was tried first: its open leaves lay their
  edges flat on the walls (8 `geometry.coplanar` warnings), the sliding pair none. The pairs' second leaves are door
  records 11-15 (each event opens both).
- Installed 00:54, baked, tests 12 of 12 from assets_dev (`output/studio_cal/a8_s26/run/xd21/c005349`); audit 0 / 2
  (the vault door's `xwiron` seams, as before); check_exits 0, check_drops 0.

## D-104 dungeon campfires (2026-11-26, agent:xeen-fb5-dungeon2)

`deco:boss_fire`: the outdoor campfire's event (food 1-3 once, a small ring for a character with Perception), `once: true`, added by `level_generation/projects/xeen/common/campfires.py` (regen.py runs it after gen.py). Rebuilt, audit 0 errors, every playtest passing from the stage, installed and baked, MAW reserve rerun.
