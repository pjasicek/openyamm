# XD-09 Golem Dungeon, L4: notes

A new dungeon (no original) built with the Map Studio from its MU-6 graph (`devdocs/xeen/mockups/act2_graphs/
xd09.graph.yml`) and decider D-4 (`mockups/act2_dungeon_decisions.md`, "XD-09"), through briefs L1 to L4 in this
folder's siblings, by lane A8's sub-agent `agent:xeen-a8-xd09`, 2026-11-20. Class M, Act II, party 16 to 18, story step
M10 (the last five King's Megacredits for Newcastle) and the title Master of Golems. Installed in the Xeen world
(`assets_dev/worlds/xeen/maps/xeen_xd09.{blv,scene.yml,studio.yml}`, `events/maps/xeen_xd09.lua`).

**The project files are generated**: `output/studio_cal/xd09/tools/gen.py` writes L1 to L3 (plan, project, diagram,
the L3 shell) and L4's rooms.yml, objects.yml, wiring.yml, project.yml and plan.yml; the playtests are hand-written.
Edit the generator and rerun it (then `oymap fmt`, `build`, `install`, `oymap record --author agent:xeen-a8-xd09`),
not the YAML. Scratch: `output/studio_cal/xd09/` (`play.sh <playtest> <name> [n]`, `four.sh`, `tour.sh <list> <name>`,
`tools/props_check.py`, `tools/texsheet.py`, the tours `look1/`, `look2/`, `look3/`, `look3b/` with contact sheets).

**A2's rows are live** (session 3, 2026-11-20): `data_tables/map_stats.txt` row 9125 has the `material_golems` slot
(Xeen Golem, Dif 2, 1-2, 100 %) and `items.txt` the Iron Key 12261. Every game run plays from `assets_dev` with
`--world xeen` and no `--extra-mount`; the session-2 scratch mount `output/studio_cal/xd09/mount` is deleted (see
"Session 3").

Row 9125 as tested in session 2 (A2's row now carries the same slot): lock 6, trap 4, perception 6, refill 672 days, music 43,
environment STONEROOM, bolster LowerToEqual, encounter 10 %; slot 1 `material_golems` (Xeen Golem) tier/Dif 2, count
[1, 2], weight 100 (the markers carry fixed tiers a/b/c; slots 2 and 3 unused, repeated in the test row).

## Layout (27 rooms, 27 sectors with a floor, 52.8 M units²)

```
                         [Masons' store $]
                                |door
 [W gallery]==rail==[ THE BLOCK FIELD: 9 blocks, 6 rocks ]==rail==[E gallery]
      \_________________[South gallery]___________________/
                      |                 |
               [Lamp gallery]      [Stone stair +512]
          window into the hub           |
 [High N]-canopy-[Low N]                | (Stone door)                [N tumbler: lever 1]--slot--
 [CROWN]--[ TRUNK ]--Wood door--[ HALL OF THE PLAQUE ]--Iron door--[ FORGE $ key ]--[furnace]
 [Heart $]     |                 statue, six lamps        |door                [ HALL OF THE GREAT LOCK ]--[E tumbler: 3]
 [High S]-canopy-[Low S]          |                                   lever 2, the lid over the diamond stair
                            [Entry stair]==Diamond door (from below)==[Vault stair]
                            X5 door (out)                                 |
                                                [VAULT $ Megacredits]--door--[ DIAMOND HALL: Diamond Golem ]
```

- **Hub, the Hall of the Plaque** (2,560 square, 1,152 high): four pillars, the golem-maker's statue on a plinth and
  dais (the plaque, `m10.golem_plaque`), the Wood door west, the Stone door north, the Iron door east with six dark
  lamps over it, the entry south; a window high in the north wall from the lamp gallery.
- **Entry stair**: the landing inside the tundra door (out to X5), six steps down, the hub through an arch, the Diamond
  door in its east wall (opens only from the vault stair).
- **Home of the Wood** (floor 0 and 256): the trunk (3,520 by 1,280, six root-posts), two low branches off its sides,
  the crown at its west end with steps up to two high branches (+256), the heartwood (seed chest); two canopy walks
  climb from each low branch to its high branch (two loops). Each branch-end has a living bough grown out of its
  outer wall.
- **Home of the Stone** (256 to 512): the Stone stair (16 steps, +512) to the south gallery; the lamp gallery runs back
  south from it to the window over the hub; the west and east galleries; the block field 256 below the galleries and
  open to them over rails (2,560 by 2,048, 1,024 high), reached by steps up to doorways at the galleries' north ends
  (the loop round the field); the masons' store (chest) off the east gallery.
- **Home of the Iron** (floor 0): the forge (hearth, two anvils, a cooling trough, the forge chest with the Iron Key),
  the furnace passage (a furnace mouth in its wall) to the north tumbler, the Hall of the Great Lock (2,048 by 2,304,
  the lock in its floor), the east tumbler; the loop round the forge (forge, furnace, north tumbler, lock hall).
- **Home of the Diamond** (-640): the diamond stair (19 steps) down from under the great lock, the Diamond hall (four
  crystal pillars, the Diamond Golem on its dais), the vault (vault chest), the vault stair (20 steps) up to the
  Diamond door by the entry: the way out.

Rooms added to the graph: the south gallery (the stair's landing over the field), the lamp gallery (the window onto
the lamps, D-4's "visible from the galleries"), two canopy walks (the graph's canopy links), the vault stair. The
graph's iron loop order (forge, north tumbler, furnace) became forge, furnace, north tumbler, so that the north
tumbler sits against the lock hall and sees its bolt through a slot.

## Measurements

| | XD-09 | M band |
|---|---|---|
| Sectors | 27 | 20-45 |
| Floor area | 52.8 M units² | 30-90 |
| Monsters at load (expected) | 45.5 | 45-75 (MAPS §0: 45) |
| Chests | 4 | 3-7 |
| Doors (real) | 7 doors, plus the great lock's lid and the tundra door out to X5 | 6-16 |
| Loops | 4 (two canopies, round the field, round the forge) | |

`scale_bands.py` (`scale_bands.txt`): bigger rooms 3.40 M (shipped median 1.64, percentile 83), largest room 6.80 M
(6.13, 52), typical ceiling 640 (521, 74), taller rooms 896 (570, 79), doorway 320 (256, 57): all at or above the
shipped median.

## Monsters (MAPS §0: 18-40, Diamond Golem 50, 45 in groups of 1-2, 9.6k kill XP per member; D-4 item 2)

Map card (row 9125, requested from A2): slot 1 `Xeen Golem` (Material golems), Dif 2, 1-2 per marker, weight 100
(slots 2 and 3 repeat it in the test row). Markers carry fixed tiers:

| Row | Tier | Where | Markers | Expected |
|---|---|---|---|---|
| Wood Golem 11580 (18, 504 XP) | a | hub 1, trunk 2, each branch 2 (8), crown 2, heartwood 1, north canopy 1 | 15 | 22.5 |
| Stone Golem 11581 (26, 936 XP) | b | stone stair 1, south gallery 1, west gallery 2, east gallery 2, field 3, masons' store 2 | 11 | 16.5 |
| Iron Golem 11582 (40, 2,000 XP) | c | forge, furnace, lock hall | 3 | 4.5 |
| Iron Golem 11582, placed | | Diamond hall, by the vault door | 1 | 1 |
| **Diamond Golem 11583** (boss row, 50, 1,200 HP, 3,000 XP), placed | | Diamond hall, on its dais | 1 | 1 |

45.5 monsters expected; kill experience 11,340 + 15,444 + 11,000 + 3,000 = 40,784 for the party, 10.2k per member
(+6 %). **Counted at load** in four runs (`actor count`, `run/countb1-4.log`): 47, 48, 49, 47 (wood 22-26, stone 16-19,
iron 5-6, the Diamond Golem 1); at the mean (23.5, 17.5, 5.75, 1) **10.7k per member (+11 %)**, inside the 15 % rule
(D-4 said about 7 % over). A2's `balance.py --detail` shows XD-09 as "spawn on empty slot 1"
(1.2k) until the map row exists. Every golem stands where a golem (radius 94, height 215) can come out to the party:
passages 320 or wider, rooms 512 high or more, the field's blocks 256 apart. The world's `relations.yml` makes
`xeen_material_golems` (11580-11584) the party's foes; no map relations.

## Loot and story (M10)

Treasure level 3 (map card; chests at 3), the vault a level-4 hoard. Four chests: the seed chest in the heartwood
(three rolls), the masons' chest (three rolls, 600 gold), the **forge chest** (the Iron Key 12261 and two rolls), the
**vault chest** (five King's Megacredits 12192 as `m10.golem_vault`'s `map_gives`, 3,000 gold, four rolls of level 4).
Chest kinds: MM6's `ch3` in the wood and the forge, MM7's `7gt002` in the masons' store and the vault (the diamond
family has no chest of its own; MM8's `gt002` is the same picture, and one kind fewer kept the textures in budget).

**Quest hooks** (`data_tables/quest_hooks.yml`):

| Hook | Event | Wiring |
|---|---|---|
| `m10.golem_plaque` | `evt:statue` (the statue, `deco:statue`), else-branch | `XeenQuests.hook("m10.golem_plaque")`: the rhyme in a window, then the map's count of boughs left |
| `m10.golem_vault` (once) | `evt:chest_vault` | `XeenQuests.hook("m10.golem_vault")`: sets `golem_credits` 111202, the award "Master of Golems" (404) and 3,000 XP, the plaque's lines and "King's Megacredit!"; the chest holds exactly five 12192 |
| `m10.golem_door` | X5's (A6) | not this map's |

The arrival is the map's own (no arrival hook exists for XD-09): "The Golem Stone turns in the door, and the door
grinds shut behind you. Emerson's King's Megacredits for Newcastle lie somewhere below, the golems' hoard; the golems
that keep this place were never told to stop." (a one-shot timer, `evt:arrive`), on the first arrival only (session 3:
`condition: {not: {qbit: arrived_once}}`, sets `arrived_once` 110601).

**Bits**: qbits `golem_credits` 111202 (M10's, set by the hook), **`diamond_slain` 110600** (the map's, set when
the Diamond Golem dies) and **`arrived_once` 110601** (the map's, the first-arrival window; session 3); A3 to register
both in m10.yml. Map variables for everything else (`boughs`, `cut_ln/ls/hn/hs`,
`stone_open`, `rocks`, `block_11..33`, `bolt_n/e/s`, `lid_open`, `diamond_open`). No player bits.
Items: King's Megacredit 12192, **Iron Key 12261** (A2's row, live since session 3), Golem Stone 12305 (X5's door).

## Mechanisms (two-state only, D-4 items 3 and 4)

- **Wood: four boughs.** Each branch-end has a living bough: a block of dark wood (`bemdk4`) 512 or 640 long, 128 thick,
  grown out of the outer wall from 96 to 224 above the floor; an **indoor destructible** (objects.yml `destructibles`,
  30 hp, wood, `Events/shatterwood02.wav`). Clicking it cuts it (`evt:bough_*`: counts and breaks it: "You hack through
  the living bough, and it falls. Three branches remain."); a blow or missile breaks it too, and its `on_destroyed`
  (`evt:bough_*_cut`) counts it then (a per-bough variable keeps a cut from counting twice). The plaque says the count
  ("Four branches remain." until cut). With four cut, touching the statue opens the **Stone door** ("Deep in the north
  wall a bar draws back, and the Stone door grinds open.").
- **Stone: nine blocks.** Each block (256 square, 192 high, Stone City's `cwb`) is a mover clicked on itself
  ("Stone Block"): it slides 256 east into its own empty recess and **stays pushed** (chosen over toggling: no
  progress can be undone; a second click says "The block sits in its recess."). Six hide a glowing rock (a plate of
  veined rock `vlcwl1` under the block, lit by its own pulsing orange light when bared): blocks 11, 12, 21, 23, 32, 33
  (row from the south, column from the west). Each bared rock says "Stone Block - Glowing Rock! Far off, a lamp kindles
  over the Iron door (n of six)." (aaze0081:12), switches on its lamp's light (`lights_on`, the lamps start dark) and
  turns its lamp panel over the Iron door from dark iron to lava-bright (`set_texture` to `orfyrlga`). The three bare
  blocks say "Bare stone beneath it." Six rocks open the **Iron door** (a timer: "Six rocks glow. Far below, the Iron
  door grinds open."). The lamps are seen from the hub and from the lamp gallery's window (D-4: "visible from the
  galleries"); the Iron door, clicked, says how many burn.
- **Iron: the Iron Key and three tumblers.** The great lock is a lid of dark iron 384 by 1,168 lying over a hole in the
  lock hall's floor (an `in: floor` opening over the upper half of the diamond stair), a mover that slides 512 west
  when opened. Three bolts (A6's dark riveted iron `xwiron`, 96 by 160, 72 high) stand shot against its north, east and south edges; three
  **two-way levers** (the shipped lever, on a plate of veined rock with a small light) draw a bolt back 128 or shoot it
  home again, the lever and the bolt moving together: the north tumbler's lever (its bolt seen through a low slot in
  the wall beside it), the lock hall's lever on its south wall (its bolt in view), the east tumbler's lever (through
  its slot). The lid: without the key "Its keyhole is cut for a great iron key."; with it and bolts shot "The Iron
  Key will not turn: n of the three bolts still hold the lock. Their levers are in this hall and in the rooms north and
  east."; with all three drawn "The Iron Key turns. All is set: the great lock slides aside ..." The key is not taken.
- **Diamond.** The Diamond Golem's death (a kill test on a timer) sets `diamond_slain` and raises the vault door ("The
  Diamond Golem shatters, and the vault door grinds up."); clicked before, the vault door says it will not move while
  the Golem stands. The **Diamond door** by the entry opens from the vault stair only (`side`); from the entry it says
  it has no ring or keyhole on this side.
- Plaques over the four hall doors: each door's hover name and text is "Home of the Wood / Stone / Iron / Diamond"
  ("A plaque over the door reads: ...", aaze0081:2-5).

How the build's own checks see it: `oymap solve` opens all 27 sectors in five steps (Wood door; the statue; the
blocks and the Iron door; the levers, the forge door, needs item 12261; the lid and the vault on the kill), one exit,
`xeen_x5.odm` at 18688, -3457, 960, direction 512 (north).

## Exit to X5 (linked in session 3)

The tundra door is the exit `exit:x5` (Stone City's door `hdr1dl` fitted, 224 by 384, on the entry's south wall above
the landing), event 28 `evt:exit_x5`, an `exit` preset with the hint "Exit Golem Dungeon" (aaze0081:10); the game's
window asks "Do you wish to leave Golem Dungeon?" (OK / Close). `neighbours` `door:x5` → `xeen_x5.odm`, arrival
**18688, -3457, 960, direction 90** (MoveToMap 512: north, the convention of XD-06's X2 arrival and XD-11's X8 link),
120 north of X5's slab door `thing:xd09_door` and facing away from it. X5's door (event 92, `m10.golem_door`, needs
the Golem Stone 12305) brings the party to this map's start, **384, -2176, 192**, on the landing facing north.

## Textures (37 distinct of 45, none new)

One shipped family per area:

- Hub, entry, stone level: **MM7 Stone City (7d24)**, the dwarves' city cut in the mountain: block brick `cwb`, rough
  rock `cwb1`, rough floor `cfb1`, tan flags `7tfb1`, the door `hdr1dl`.
- Wood: **MM6 Warlord's Fortress (6d16)**, its timber: wood grain `cbeam5` on the walls, dark wood `bemdk4` (posts,
  boughs, reveals), beam planks `bemstrt1`, the earth ceiling `d8ceild`, the plank door `d2smldor`.
- Iron: **MM6 Gharik's Forge (6d18)**: soot brick `d2wlactr`, dark iron rock `vlcwl3a`, volcanic tile `6voltyl`, the
  beam ceiling `d2ceil1`, the iron-bound door `cvdor1`, lava `orfyrlga` (hearth, furnace mouth, lit lamps), veined rock
  `vlcwl1` (the glowing rocks and the lever plates), A6's dark riveted iron `xwiron` (XD-04's, registered for XD-09) on the great lock's lid and bolts (session 4; `cvdor1` there in session 3, the grating `gset05` before). XD-03 took this map's lava and soot
  brick for its deep mine; here it is a forge, Gharik's own purpose.
- Diamond: **MM8 Prison of the Lord of Fire (d37)**: pale ice marble `gtempw3`/`gtempw1`, blue brick `gtempflr`, the gold
  mosaic ceiling `gtemprf`, the rune door `gtempdor1`, cyan crystal `gcrysc3` (the pillars).
- Others: the chests' own (`ch3*`, `7gt002*`), the lever's default.

`tools/xeen/texture_budget.py`: XD-09 M 37/45, 0/8 new (session 4). For A6's `dungeon_families.yml`: XD-09: 7d24 (hub, stone),
6d16 (wood), 6d18 (iron), d37 (diamond). Nothing generated; a bark texture for the trunk would read better than the
fortress's planed grain (wanted, not made).

## Original lines (aaze0081)

The plaque rhyme (:0, through `m10.golem_plaque`); "Home of the Wood / Stone / Iron / Diamond" (:2-5, the four doors);
"Stone Block - Glowing Rock" (:12, each bared rock); "All is set, it is plain to see / Master of Golems I now dub thee."
(:1) and "King's Megacredit!" (:11) in `m10.golem_vault`; "Exit Golem Dungeon" (:10, the tundra door's hint). "All is set"
also in the lock's opening line.

## Light and sound

Torches (MM6's `torch01`) on the walls of the hub, wood, stone and iron rooms; the hub's statue in a cold light; the
forge's hearth and the furnace in pulsing red; lights over the great lock, by each bolt and each lever; two lights over
the block field; six dark lamp lights over the Iron door and six dark rock lights in the field (lit by the blocks); the
diamond level cold blue, no torches. Ambient 20-28. Placed sounds (engine audio): `raging fire loop` at the hearth and
the furnace, drips (`drip02`, `drip03`) in the field and the heartwood. Music 43 (map card).

## Playtests (from assets_dev, `--world xeen --map xeen_xd09.blv`; session 2 with the test-only scratch mount)

- `playtest.yml` (156 steps, level-17 party of four, immortal): arrival message; the tundra door asks to leave (Close: the party stays); the Diamond
  door refuses from the entry; the plaque (rhyme, "Four branches remain"); the Iron door's lamp count; Wood door; three
  boughs cut by click (counts asserted, a cut bough says so), one broken as a blow does (`destructible 1 destroy`,
  its on_destroyed counts it); the seed chest; the statue opens the Stone door; the south and lamp galleries (step
  texts); the nine blocks (texts, six rocks, the Iron door opens); the masons' chest; the Iron Key from the forge
  chest; the lock refuses ("3 of the three bolts"); the south lever, the east lever thrown three times (the bolt
  follows both ways), the north lever; the key turns, the lid slides aside; down the stair (the golems meet the party
  there); the Diamond Golem's death (`diamond_slain`, the vault opens); the vault chest (five Megacredits,
  `golem_credits`); up the vault stair, the Diamond door from below, back to the entry.
- `playtest_hostility.yml` (25 steps): the four golem rows hostile, none peaceful; the four kinds spawned side by side
  in the entry do not take each other on and go for the party.
- Runs in session 2 (`four.sh`, one game at a time; session 3: "Session 3" below): `playtest.yml` 156 of 156 **4 of 4**, `playtest_hostility.yml` 25 of 25
  **4 of 4** without the bolster row (`four.out`), and again **4 of 4** each with the world's current tables and the
  bolster row 9125 (`four2.out`); logs `run/world/main_N.log`, `host_N.log`.

Clearing in the playtest stays under 1,800 near the forge and 1,000 in the lock hall: the Diamond hall lies within
2,400 below them and must keep its golems for the kill test.

## Pictures (looked at)

`look1/` (first look, every room), `look2/` (mechanisms before and after: bough cut, blocks pushed, rocks lit, lamps lit
seen from the hub and the window, bolts drawn, lid open, the stair from the top), `look3/`, `look3b/` (levers and
bolts after the fixes). Fixed after looking: the hub, field, forge and lock hall too dark (ambient 26-28, more torches,
lights over the field and the lock); the boughs read as benches on the floor (now hanging from the wall at 96-224);
the bolts dark on the dark floor (now grated iron with a light each); the levers lost on the brick (plates of veined
rock behind them, a small light each). Best: the lamps lit over the Iron door (look2 13), the lid open over the
stair (21, 22), the Diamond hall (23). Weakest: the wood hall's planed grain (no bark), the levers' small arms, the
golems' stand-in model (A2's binding).

## Dressing (DRESSING.md, D-7)

Audit used: the current `oymap audit --world xeen` (A1's recalibrated audit had not landed) plus A7's
`check_dressing.py` and `tools/props_check.py` (platforms and chests too). Files in `output/studio_cal/xd09/dressing/`.

- First build: the audit's `dressing.walking_line` error on the statue (the entry-to-Stone-door line crossed the hub's
  middle): the entry and the Stone stair moved to x 384, the lamp gallery to x -448; the error is gone.
- `props_check.py` before: 12 flagged (the hearth over the furnace doorway, an anvil and the trough on the line from
  the Iron door to the lock hall door, the two low boughs and the field rocks near openings, the masons' and the
  vault's rock and crystal by their doorways); moved: hearth 384 long west of the furnace doorway, anvils and the
  trough to the forge's south half, the low boughs shortened and moved east, the field rocks and the vault crystal
  dropped, the masons' rock to the east wall. After: 3 (below).
- `check_dressing.py`: 0 findings (no containers on the map); `measure.py`: no containers.
- `oymap audit --world xeen` on the installed map: no dressing findings, 0 faces in one plane.

### Dressing exceptions

- The statue, its plinth and dais in the middle of the hub (`props_check.py` only, which counts the lamp gallery's
  window high in the north wall as an opening): the set piece the hall is built round; every walking line between the
  hub's doorways passes at least 190 from it (the audit's check passes).

## Departures from the graph and the brief

- The Diamond door stands in the entry's east wall (the hub's antechamber) rather than in the hub itself: the vault
  stair has to come up somewhere near the entry and the hub's south wall carries the entry arch.
- The lamps are seen from a lamp gallery's window, not from the field's galleries themselves (they are 1,800 apart).
- The great lock is a lid over a hole (a mover), not a door: the studio has no door in a floor opening.
- Blocks stay pushed: decided by D-18 (DECISIONS.md; a search, not a sliding puzzle, since no order or wrong move exists under D-4).

## Words needed (gaps), most harmful first

1. **A two-way switch with a state**: a lever that sets its variable and moves its parts both ways. `toggles` moves the
   parts but keeps no state the lock can test; a `condition` branch has no `closes`. Workaround: the else branch sets
   the variable to 0 and closes the bolt by its door number from ids.lock.yml in Lua (`evt.SetDoorState(n,
   DoorAction.Close)`, read by gen.py from the lock).
2. **A door in a floor opening** (a hatch): workaround, a mover lid sliding aside over an `in: floor` hole.
3. **A count shown in text** ("Three branches remain", "n of six"): Lua in the effects.
4. **A destructible clicked to break it** (MM9's converter has `click`): a separate click event on the same platform
   that destroys it and counts, with the `on_destroyed` event guarded against counting twice.

## Tool defects

1. `oymap solve` never runs an event whose else branch's Lua contains `Xeen.itemCount(12261) < 1` (it stopped at the
   lock with every condition met); with `not HasItem(12261)` it does. Shown by `output/studio_cal/xd09/tmp_l4`.
2. `oymap build` warns "a click does nothing the player sees" for events whose else branch is Lua that shows a message
   (`evt:great_lock`, `evt:statue`).
3. `oymap solve` / `audit --reach` do not follow a destructible's `on_destroyed` (and say the variable it counts is
   never set); the count had to live in the click event.
4. The game cannot load a world map with no map_stats row ("cannot resolve map world"), so a new map cannot be played
   before A2's generator adds it.
5. Scenario `play_lua`: `mapvar(name)` does not see the studio's numbered map variables (always 0); `status()` does not
   carry lines over from an earlier `play_lua` step. Indexed `state_dump_map_var` asserts used instead.
6. `tools/xeen/balance.py` shows XD-09 at 1.2k ("spawn on empty slot 1") until the map row exists.

## What the user should look at when playing

The plaque and the four homes in order; whether clicking a bough to cut it reads right (blows also break it); the nine
blocks and the six lamps kindling over the Iron door (seen through the lamp gallery's window); whether the three levers
and their bolts read (small levers on veined plates, bolts through slots); the lid sliding off the stairwell; the
Diamond Golem's fight on the stair; the wood hall's look (planed grain, no bark); the golems' stand-in model. Since session 3: whether the riveted lid and bolts (dark iron `xwiron` since session 4) read as iron, the golem forge in the lock hall's
south-east corner, and the way out to X5 and back in by the Golem Rocks' slab door.

## Session 3 (2026-11-20): exit to X5, iron bolts, forge

By `agent:xeen-a8-xd09` (lane A8, session 3). All changes are in `output/studio_cal/xd09/tools/gen.py` (the session-2
generator is kept as `tools/gen_s2.py`). They were rebuilt with `v.sh` (gen, `fmt` L1-L4, `validate`) and `go.sh`
(`build`, `audit --reach --solve` on the build, `install --root assets_dev`, the same audit on the installed map,
`solve`), then recorded with `oymap record --author agent:xeen-a8-xd09` (revision `f7ccc8edefd50aa97013821263d48419`).

- **Exit linked to X5**: `exit:x5` and `evt:exit_x5` (event 28) as an `exit` preset, and the neighbour's arrival
  18688, -3457, 960, direction 90. The sealed panel `panel:x5_door` is gone. Details are under "Exit to X5" above.
  `solve` lists one exit: `xeen_x5.odm` at 18688, -3457, 960, direction 512.
- **First arrival only**: `evt:arrive` has `condition: {not: {qbit: arrived_once}}` and sets **`arrived_once` 110601**.
  **For A3:** register it, with `diamond_slain` 110600, in m10.yml.
- **Iron bolts and lid**: the bolts were the grating `gset05` (read as stacks of planks) and the lid was `vlcwl3a`
  (read as a gravel slab). Gharik's Forge has no plain iron plate or bar. In a tour I tried its dark cast rock
  `vlcgnrc2` (it read as rock blocks and merged with the floor), its iron-strapped door `d2lgdor` (the bolts read as
  skull chests), and the world's rusted iron `xnrustirn` (flat tan, read as clay). I kept the forge's iron-bound
  plate **`cvdor1`**, which is already the Iron door's picture. The lid's top is a grid of two by three bossed plates
  (`size [192, 389]`), each bolt's top is one plate (`fit`), and the low sides use it at its own size. They read as
  machined plates, not planks. They are pale grey under the warm light, not dark iron.
- **The golem forge** in the lock hall's south-east corner, off every walking line (`props_check.py`: hearth 622 from
  an opening and 760 from a line; pot 798 and 936; brazier 538 and 573):
  - `platform:lock_hearth`: a casting hearth against the east wall, 224 by 448, 96 high, in iron rock with lava coals.
    It is clicked as "Golem forge" (event 51: "An iron pot simmers on the coals. Here the golem-makers poured the
    iron limbs of their golems.").
  - MM6's bubbling cauldron `cauld00` on the coals.
  - A lit brazier `brzier00` at the hearth's north end.
  - A pulsing red light `light:lock_forge` (radius 1,300) and the sound `raging fire loop`.
  - The east wall's torch over the hearth was dropped.
- **Numbers**: 28 sectors (27 rooms), 1,398 faces, 23 doors, 51 events (44 bound), 0 faces in one plane, 0 sectors
  never reached. Textures: **36 distinct of 45, 0 new** (`gset05` dropped). The monsters, chests and layout are
  unchanged.
- **Audit** (`oymap audit xeen_xd09.blv --world xeen --assets assets_dev --reach --solve`; `--dressing` gives the
  same): no dressing findings. Infos: `texture.squashed` on 6 `vlcwl3a` faces (hearth sides), and `event.unbound`
  for events 13 and 15. The build warns that nothing tells the player why he is here on arrival; that is a tool
  defect (below).
- **A2's rows are live**: map_stats 9125 (golem slot) and item 12261. Every playtest and tour ran from `assets_dev`
  with no `--extra-mount`. The scratch mount `output/studio_cal/xd09/mount` was deleted after the 4-of-4 runs.
  `play.sh` takes a fourth argument (`none` for no `--map`); `four.sh` runs all four tests.
- **Playtests** (`four.sh`, `four3.out`, logs `run/world/{main,host,exit,in}_N.log`):

  | Test | Steps | Runs |
  |---|---|---|
  | `playtest.yml` | 160 | **4 of 4** |
  | `playtest_hostility.yml` | 25 | **4 of 4** |
  | `playtest_exit.yml` | 22 | **4 of 4** |
  | `playtest_in.yml` | 36 | **4 of 4** |

  - `playtest.yml`: the tundra door now asks to leave (Close: the party stays), and it asserts `arrived_once`.
  - `playtest_exit.yml` (new): walk to the door, use it, OK, arrive on `xeen_x5.odm` at (18688, -3457, 961). Turned
    south on the same spot, the party reaches the slab door, which refuses without the stone. The scenario cannot
    assert a yaw. A press facing the arrival yaw picked nothing (the door is behind), and 512 is north by the
    convention XD-06 verified.
  - `playtest_in.yml` (new, a new game on X5, no `--map`):
    - X5's event 92 refuses without the Golem Stone ("... waits for a stone tablet.").
    - With 12305 the party arrives at (384, -2176, 192).
    - The arrival window shows once; out by event 28 to X5, in again by X5's door, and no window opens.
- **Pictures** (`look4f/`, `look4f_sheet.jpg`; trials `look4_sheet.jpg`, `look4b-e_sheet.jpg`, `tex/look4*_4.jpg`):
  - The lock hall before and after the bolts are drawn, and with the lid open.
  - A close view of the north bolt through its slot, the south bolt and its lever, and the golem forge.
  - The exit door from the entry floor and from the landing.
  - Fixed: four texture trials for the bolts and lid (above).
  - Seen and kept: the forge corner is still dim beyond its light; the lid and bolts are pale.
  - A note on the test: X5 was reinstalled by A6 during this session (a stale lighting bake at 15:31 stopped one
    exit run from loading X5); after A6's re-bake (15:38) every run passed.
- **Tool defect**: `oymap build` warns "nothing tells the player on arrival why he is here" when the arrival timer has
  a `condition` (first arrival only), although the message is there.
- **Wanted (A6)**: a plain dark iron plate or bar texture for forge and iron areas. Gharik's Forge has none, so the
  bolts and lid use the pale iron-bound stone plate `cvdor1`.

## Session 4: xwiron on the bolts and lid

By `agent:xeen-a8-xd09` (lane A8, session 4, 2026-11-20), at A6's offer. All changes are in
`output/studio_cal/xd09/tools/gen.py` (the session-3 generator is kept as `tools/gen_s3.py`); rebuilt with `v.sh` and
`go.sh`, recorded as revision `f787212b64f566753640c97330ab227a`.

- **What changed**: the great lock's lid and its three bolts use A6's dark riveted iron **`xwiron`** (128 square;
  riveted bands every 64 texels) instead of `cvdor1`. The surface offsets place the bands:
  - each bolt: `surface` offset [-8, 42] gives a band round it 48 up (the middle of what shows over the 24-high lid)
    and an upright strap 12 from its lock end on both long sides. The new `end_surface` offset [4, 42] gives the band
    **across each end face**, between two upright straps 16 in from its edges.
  - each bolt's top (its own offset: north [52, 14], east [8, 90], south [52, 38]): straps across it 12 in from the
    lock end and every 64 back, and two along it 16 in from its sides, in line with the end face's straps.
  - the lid: top offset [52, 26] gives bands 32 in from its long sides and 40 from its short ones; its edge
    (offset [0, 54]) has a band at half height.
  - The Iron door and the forge's lock-hall door keep `cvdor1`.
- **Numbers**: 28 sectors, 1,398 faces, 23 doors, 51 events (44 bound); no geometry, event or id changed. Textures
  **37 distinct of 45, 0/8 new** (`texture_budget.py`; `xwiron` is registered for XD-09 in `source/textures.yml`).
- **Audit** of the installed map (`--reach --solve`, and `--dressing`): no dressing findings, 0 faces in one plane, 0
  sectors never reached, one exit (X5). Infos as before (`texture.squashed` on the hearth's six `vlcwl3a` sides,
  events 13 and 15 unbound).
- **Bake**: XD-09 has no lighting sidecar (indoor bakes are opt-in, and no Xeen dungeon has one), so there was
  nothing to re-bake. `stale_bakes.py --check` lists nothing for `xeen_xd09`; it lists one other map's bake,
  `xeen_x2.lighting` (its scene changed; not this lane's).
- **Playtests** (`four.sh`, `four5.out`, from `assets_dev`, no mount):

  | Test | Steps | Runs |
  |---|---|---|
  | `playtest.yml` | 160 | **4 of 4** |
  | `playtest_hostility.yml` | 25 | **4 of 4** |
  | `playtest_exit.yml` | 22 | **4 of 4** |
  | `playtest_in.yml` | 36 | **4 of 4** |

- **Pictures** (`output/studio_cal/xd09/look5/`, `look5_sheet.jpg`, HUD off; looked at): the lock hall before, the lock
  end of the north and east bolts over the lid, each bolt close, the east bolt's far end, the bolts drawn, and the lid
  open.
  - Fixed after the first look: the band across the end faces sat low, just over the lid (36 up). It is now at 48,
    the middle of what shows.
  - Seen and kept: the plates read as riveted iron. Under the warm bolt lights they are dark brown-grey, darker than
    `cvdor1` but not black. In the wide views the lid is low in contrast against the dark `6voltyl` floor. The lid's
    top reads as a grid of 64-unit riveted plates.

## Light audit (merge point 14)

By `agent:xeen-a8-lights` (lane A8), 2026-11-20, on A1's light-fixture audit (`devdocs/xeen/formats/LIGHTS.md`,
`output/xeen_a1/lights_xeen.txt`). Changed in the generator (`output/studio_cal/xd09/tools/gen.py`, copy before the
change `gen_before_lights.py`; the generator reproduced the project byte for byte first), L4 regenerated, `oymap fmt`,
`oymap record --author agent:xeen-a8-lights --label "lights audit (merge point 14)"`.

- The forge's brazier (`brzier00`, chained) hangs from the Hall of the Great Lock's ceiling (height 748), its top 2 into
  it.
- The low branches' west torches (in the canopy paths' mouths) to 0.85 (north) and 0.15 (south); the high branches' east
  torches likewise to 0.75 and 0.25; the south gallery's torch out of the lamp gallery's mouth (0.4 to 0.25).
- The entry's east torch was on the diamond door's leaf and in its doorway: now on the landing's east wall (0.25, height
  320: 128 over the landing's floor 192).
- The stone stair's two torches stood under its sloped floor (height 128 over the bottom step at a point where the floor
  is 358): height 486, 128 over their step.

- **Audit** (`oymap audit --reach --solve` on the installed map, `output/studio_cal/xd09/audit_lights.txt`): lights
  errors/warnings before **11/0 (5 wall_missing, 4 in_doorway, 1 on_moving_face, 1 ceiling_on_floor)**, after **0/0**;
  no dressing finding. **Light exceptions:** none.
- **Installed** by `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh xd09` (build `output/studio_cal/xd09/b_193320`), baked
  (`output/studio_cal/a8_s5/bake.sh xd09 assets_dev`, profile `tools/lighting/baked_indoors/profiles/xeen_xd09.yml`
  (new: XD-08's values)), `tools/lighting/stale_bakes.py --check` lists none of the lane's maps. **Playtests from
  assets_dev, each 4 of 4** (`four.sh 4`; record `output/studio_cal/xd09/lights_post.out`): main 4/4 (160 steps); host
  4/4 (25 steps); exit 4/4 (22 steps); in 4/4 (36 steps) (main = playtest, host = playtest_hostility, exit =
  playtest_exit, in = playtest_in).
- **Pictures** `output/studio_cal/xd09/shots/lights_mp14/` (sheet `lights_mp14_sheet_1.jpg`), looked at: the forge
  brazier hangs under the hall's ceiling; the branches' torches on solid wall beside the canopy paths; the stone stair's
  torches over their steps; the entry's on the landing wall beside the diamond door; the south gallery's beside the lamp
  gallery's mouth.

## Double doors (merge point 15, A8 session 6, 2026-11-20)

A1's door check (oymap 20:03:53, `devdocs/xeen/formats/DOORS.md`) found Stone City's door `hdr1dl` (one wing) laid 1.8
times across the 256-wide doors `door:stone` and `door:mason`. Both are hinged pairs now (`kind: hinged, leaves: 2`,
`pictures` and `back_pictures` `hdr1dl` | `hdr1dr`) in `tools/gen.py` (copy before: `gen_before_doors.py`). The exit
door's `hdr1dl` was declared 224 x 384 with `fit` while the doors declared 128 x 256: the studio keeps one size per
texture for the whole map, so the pair's left leaves still measured 1.75 across until the exit door said 128 x 256 too
(it still fits its 224-wide face; a word for A1). Audit `--reach --solve`: no error, no warning, 27 of 27 sectors with
the doors out of the way. Recorded, installed, baked; tests 4 of 4 from assets_dev (160, 25, 22, 36;
`output/studio_cal/xd09/doors_post.out`). Pictures `output/studio_cal/xd09/shots/doors_mp15_sheet.jpg` (looked at:
the arch reads whole across both leaves from both sides).

## Session 7 (one size per texture, A8 session 7, 2026-11-20)

- Merge point 17's build warns where one texture is given two sizes in a map. `tools/gen.py` (copy before:
  `gen_before_s7.py`) now gives each its own size and enlarges by `scale`: the six Iron-door lamps `vlcwl3a` at 128 x
  256 scale 0.75 (were [96, 96]), the forge's lava panel `orfyrlga` 256 at scale 0.5 (was [128, 128]), the veined plates
  `vlcwl1` 128 x 256 (were [128, 128]) and the glowing rocks under the blocks at scale 1.5 (were [192, 192]). Build
  warnings 13 → 0; audit 0 errors, 2 warnings (below). Only L4 regenerated (L1–L3 kept as they were). Recorded,
  installed, baked; tests from assets_dev 4 of 4 (160, 25, 22, 36; `output/studio_cal/xd09/s7_post17.out`). No new
  pictures: the panels are tiles, now at one density.

**Texture fit exceptions:**
- `xwiron` `tile_seams` (2 faces): XD-04's studded iron plates meet in a line top and bottom; it reads as riveted plates.

## Session 24 (A8): merge point 35 tests

Rebuilt under oymap 12:46:47 for A1's room step tops (`evt:diamond_seen` on the dais; only the .blv changed),
installed 17:15, baked, every test 4 of 4 from assets_dev on merge point 35; audit 0 / 2 (as before).

## Session 26 (A8): the open door (D-89)

- X5's slab door (`m10.golem_door`) is open since D-89 (no Golem Stone). The arrival window no longer says "The Golem
  Stone turns in the door": now "The slab door grinds open at a push, and shut again behind you. ..." (`tools/gen.py`,
  also the plan's pitch and three notes that named the stone; before: `output/studio_cal/a8_s26/before/xd09/gen.py`).
  Only the .lua and studio.yml changed (no bake).
- `playtest_in.yml`: the refusal and the stone grant are gone; the first press goes in. `playtest_exit.yml`: the door
  from X5 leads back in (was: refuses). Both take X5's standard entrance window (OK) before the move (X5 rebuilt with
  merge point 40). Installed 00:43, tests 16 of 16 from assets_dev (`output/studio_cal/a8_s26/run/xd09/c004302`); audit
  0 / 2 (as before); check_exits 0.

### Drop pockets

- `check_drops` reports the hub, the quarry and the homes (z -640..512; the stone blocks 3-11, levers 36-38) as one
  pocket. Not a trap: the landing's six steps and the homes' flights stand over their rooms' continuous floors, so
  their treads share no edge with them and the check misses them (the landing's floor at 192 against the hub's at 0 is
  the only edge it sees). The playtests walk the whole map and back to the landing.

## Session 29 (A8, 2026-11-22): D-89 identity

- **Wood:** the trunk is round-ended (`rounded()`, radius 256 in three pieces a corner) under a barrel vault of grain
  from 576 at the walls to 1,024 along its middle (`ceiling_points`), crossed by five bough beams of 6d16's bark-red
  wood (bemdk4) at 448; the crown arch 640 wide (was 768: it fits the round end's straight stretch).
- **Iron:** anvils with a waist and a wide face, a pair of bellows (a tapering wedge) beside the hearth, an iron hood
  over it, the fire on the coals (ckfyr00) and the forge's red glow over the room.
- **Diamond:** hexagonal crystal pillars (gcrysc3) and eight clusters of four tapering shards at the walls and the
  pillars' feet.
- `identity: {shape: hall, family: 7d24}`. Family share 35 % by `check_identity.py`: by design, the map is four
  families, one per home (7d24 stone, 6d16 wood, 6d18 iron, d37 diamond; together 64 %); recorded as an exception.
- Installed, baked, audit 0 / 2 (the lid's xwiron seams, as before), check_exits 0, drops 0, tests 16/16 from
  assets_dev (`output/studio_cal/a8_s26/run/xd09/c023733`). Captures `output/studio_cal/a8_s29/shots/xd09_before.jpg`,
  `xd09_after.jpg`, both stacked in `xd09_before_after.jpg` (tour `a8_s29/tours/xd09.yml`).
- Left: the trunk reads dark at its ambient 22 (the vault shows best by torchlight); the golem tiers' bodies are S's.
