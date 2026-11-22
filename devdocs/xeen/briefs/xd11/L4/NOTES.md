# XD-11 Tower of High Magic, L4: notes

A new M dungeon (no original), story step **M13** (the Skeleton Key to Darzog's Tower), built with the Map Studio
from its graph (`devdocs/xeen/mockups/act2_graphs/xd11.graph.yml`) and decider D-4
(`devdocs/xeen/mockups/act2_dungeon_decisions.md`, which wins where they differ) by lane A8's sub-agent
`agent:xeen-a8-xd11`, 2026-11-20. Key `xd11`, project `xeen_xd11`, stem `xeen_xd11.blv`, map_stats 9127, world `xeen`.

**State.** L1-L4 `oymap validate` no issues, `fmt --check` clean. Installed in the Xeen world
(`assets_dev/worlds/xeen/maps/xeen_xd11.{blv,scene.yml,studio.yml}`, `events/maps/xeen_xd11.lua`; the world's
data_tables untouched). `oymap audit --reach --solve` on the installed map: **0 faces in one plane**, 25 of 25 sectors
reached, solve 25 of 25 in five steps (the Librarian's Key carried by the Head Sorceress, reached), no stranded
monster, no dressing finding. Playtests **4 of 4** each (`playtest.yml` 190 steps, `playtest_hostility.yml` 20), but
with a test mount for the map_stats row that A2 has not written yet (below, "Blocked").

**Scratch** `output/studio_cal/xd11/`: `tools/gen.py` (plan, project, diagram; `python3 gen.py L1 L2 L3 L4`),
`tools/geo.py` (rooms, openings), `tools/dress.py` (objects, wiring, atmosphere), `tools/tour.py`, `tools/xsheet.py`,
`tools/texsheet.py`; `go.sh` (generate L4, fmt, validate, build, install into assets_dev, record), `four.sh` (the
playtests N times, one game at a time, exact PIDs); `mount/` (the test mount: copies of the world's `map_stats.txt` and
`bolster_maps.txt` with row 9127); `shots/` (tours, contact sheets); `run/` (logs; `run/probe/` monster counts);
`audit_final.txt`, `solve_final.txt`, `metrics.json`, `scale_bands.txt`, `dress_check.txt`, `xexport.json`.
**Every project file of L1-L4 except the playtests and these notes is written by the generator**; each run recorded
with `oymap record --author agent:xeen-a8-xd11`. The generator stays the source until someone edits the project by
hand; then retire it (note it here).

## The tower

A square tower 4,096 across inside (-2048..2048), four floors 640 apart and a roof terrace under the open sky.
Rooms 544 high (slabs 96); walls between rooms 128. The stairs are two-storey halls with one flight of 20 steps of 32
along the outer wall and a gallery at the upper floor, alternating **east (0-640), west (640-1280), east (1280-1920)**,
so every floor is crossed; the Stairway to Heaven climbs from the top floor's north-west corner into the open sky.

| Floor | Rooms | What |
|---|---|---|
| Ground (0) | enchanted door (arrival), foyer (4 pillars), athanor (iron stack over a hearth of live coals, braziers), lightning coils (4 iron coils with crackling lights), lift core, east stair | Fire Brew, Electric Brew; Flying Feet |
| First (640) | east landing (gate 1 lever), cold still (frosted tank), reagent store (steam valve, Pandorian Box, barrels and sacks), poison garden (4 nightshade beds), lift core, frost-sealed west stair | Cold Brew, Poison Brew, the frost seal; Flying Feet |
| Second (1280) | west landing, energy lab (crystals), magic lab (dais; the Head Sorceress), Sorceresses' quarters (beds, chest, gate 2 lever, the Librarian's door), lift core, library stair | Energy Brew, Magic Brew; Guardians, Sorceresses |
| Top (1920) | top landing (gate 3 lever), Library of High Magic (bookcases, The Art of Magic, the cabinet of Mysteries of Light), Archmage's study (the chest: Skeleton Key), observatory (painted sky, orrery, Pandorian Box), lift core, Stairway to Heaven | M13's goal; Sorceresses, Guardians |
| Roof (2560) | roof terrace, rubble parapet, open sky; the stair of cloud | X8; Guardians |

**Measured** (`metrics.json`, `scale_bands.txt`): 25 sectors (M 20-45), **59.8 M units² floor** (M 30-90), 10 doors
(23 door records with the lifts and switches), 5 chests, 15 spawn points + 11 placed monsters. Scale bands: upper-quarter
room 2.97 M (shipped median 1.64 M, percentile 78), largest 15.3 M (the roof), typical ceiling 544 (median 521,
percentile 71), upper-quarter height 640 (median 570), doorways 320 (median 256). Lights: 23 lights (6 brew glows, the
hearth and 4 coil crowns pulse), 33 wall torches and sconces. Light sources 0.64 per M.

## Monsters (Xeen rows, A2)

| Who | Row | Level | How | At load (6 boots) |
|---|---|---|---|---|
| Flying Feet | 11600 | 18 | slot 1 `Xeen Construct`, 9 markers tier **a**, [2, 3]: foyer 2, athanor 2, coils, east landing, reagent store, still, poison garden | 23.3 |
| Guardian | 11601 | 24 | slot 1, 6 markers tier **b**: west landing, energy lab, magic lab, top landing, library, roof | 15.3 |
| Sorceress | 11180 | 30 | placed, group 1, two each: magic lab, quarters, library, study, observatory | 10 |
| **Head Sorceress** | 11185 | 32 | placed by the Magic Brew's dais, group 2, `carries: librarian_key` (12260) | 1 |

**49 at load on average** (counts 47-51; MAPS §0 50), groups of 2-3 (the placed sorceresses in pairs). **Kill XP**
(monster_data: 504, 816, 1200, 1344): 23.3 x 504 + 15.3 x 816 + 10 x 1200 + 1344 = about 37,600 for the party,
**9.4k per member against MAPS §0's 8.9k (+5.7 %)**. A2's `balance.py --detail` shows 3.3k for now: it counts only
the placed monsters while map_stats has no slot row for 9127 (blocked on A2). Carnage Hands and the source's fire
dragon left out (D-4). Hostility: the world's `relations.yml` (constructs and sorceresses long toward the party, no
feud) is enough; the project sets no relations. Sorceresses show the stand-in Druidess look, constructs a Plane
Guardian-like stand-in (S lane's bindings).

## Mechanisms (two states each)

- **The frost seal.** `door:frost` (poison garden to the west stair) is a leaf of Icewind Keep's pale blue ice
  (`orair32`). Clicked before the valve: a message window, "The door is frozen shut: a sheet of blue ice covers it
  from lintel to sill ... A steam pipe runs cold along the wall to its frame, back toward the reagent store."
  `switch:valve` (a lever on the reagent store's north wall, title "Steam valve") opens it and sets `frost_thawed`,
  with a window ("The pipes knock and hiss along the walls ... the frozen door of the west stair stands open."); a
  second pull says the valve is open as far as it goes. The steam pipe (riveted iron, A6's `xwiron`, blocks 32 thick
  hung at 288-320) runs from the valve along the store's east wall, the still's south and west walls and the garden's
  west wall to the door's frame.
- **The Librarian's Key.** The Head Sorceress carries 12260; her corpse holds it (played). `door:librarian` (the
  quarters' south-east door, Celeste's carved door, title "Librarian's door") opens to the key for good; without it:
  "The door is locked. Its keyhole is cut in the shape of an open book: the Librarian's Key, which the Head Sorceress
  keeps about her in the magic lab."
- **The lift core** (D-4 item 4; A1 has no multi-stop lift, so three stacked short lifts): one shaft 768 by 640 in the
  same place on every floor (x 256..1024, y -896..-256). Lift a (0-640) in the west half, lift b (640-1280) in the east
  half, lift c (1280-1920) in the west half again; each is a 256 plank deck (`thickness: 32`, speed 192, `state: up`:
  it starts flush with the upper floor) that rises through a hole in the floor above (`in: floor`, rubble sides).
  Each runs only once its upper floor's **gate lever** is pulled: gate 1 (east landing), gate 2 (quarters), gate 3
  (top landing), each a brass grille (A6's `xngrille`) sliding aside, bolted until then ("The lift gate is bolted.
  The lever beside it on the wall works the bolt."). Clicking a deck, or the call button beside it at either stop,
  toggles it; before its gate: "The brass cage will not move. Its gate on the first floor is still bolted ..." / "The
  cage hangs at the first floor above and will not come down while its gate up there is bolted." So each opened gate
  is a shortcut: from the top landing the cages go straight down to the coils and the door (played: c, b, a).
  The coils' door to the shaft's foot is an ordinary door.
- **The six brews** (D-4 item 1): a cauldron (`cauld00`, clicked) in each lab under a pulsing glow of its colour:
  Fire (athanor, red), Electric (coils, blue), Cold (still, white), Poison (garden, green), Energy (energy lab,
  yellow), Magic (magic lab's dais, violet). Each adds **+5 to FireResistance, AirResistance, WaterResistance,
  BodyResistance, EarthResistance, MindResistance** to the clicking character once (condition `{not: {player_bit:
  n}}`, player bits **11246-11251** in that order), with a message window ("FIRE BREW. A red brew that smokes ...
  +5 Fire resistance (permanent)."); a second drink: "You have drunk the Fire Brew already. It does nothing more for
  you." (played for the Fire Brew).
- **Library.** The Art of Magic: a lectern (`platform:art_of_magic`), a message window of lore only (D-4 item 2). The
  Prismatic Light spellbook (engine item 483, a Learning Book tagged `World:mm8`, which only limits random rolls and
  shop stock) lies in the cabinet of Mysteries of Light (`chest:mysteries`, Clanker's Laboratory's cabinet `7t1cabs`,
  title "Cabinet", status "MYSTERIES OF LIGHT, says the brass plate on the cabinet's door."). Played: the party has 483
  after looting it. **Not played: learning the spell** (needs a Light caster; no scenario step reads a spellbook).
- **Study.** The Archmage's chest runs `XeenQuests.hook("m13.skeleton_key")` (A3's: once, the Skeleton Key 12100,
  qbit 111260, 6,000 experience, "You found a skeleton key in the chest. ..."); the chest holds 600 gold and two
  rolls, no key. Played: one key, the qbit, and a second opening gives no second key.
- **Pandorian Boxes.** Two `7gt002` chests titled "Pandorian Box": the observatory's trapped (trap level 3, three
  rolls, 450 gold), the reagent store's empty with "The box is empty." (played). The build warns that "Pandorian Box"
  does not say it opens; kept for the original line.
- **Beds** in the quarters: "There is nothing on, in, or under the bed." (played).

## Exits (both linked)

The arrival is just inside the enchanted door (`start`: (-1408, -1792, 0) facing north); X3's door and the way back from
X8 both arrive there.

- **`exit:x3_door` to `xeen_x3.odm`** (linked in session 3, X3 installed by A5): the enchanted door is an `exits`
  object `exit:enchanted_door` on the door room's south wall (Celeste's carved door `hwm2d`, 192 by 384) with an `exit`
  preset event (`evt:enchanted_door`, event 13). The game's window asks to leave; OK lands the party on X3's islet at
  **(256, -1674, 992) facing north (512)**, 400 north of the tower door (`briefs/x3/DOORS.md`, `thing:high_magic`).
  X3's door needs the Enchanted Key 12306 (A3's `m13.tower_door`: "The tower door has no lock you can see, only a
  faint shimmer where a key would go."). The door was first linked as the old question ("Leave the Tower of High
  Magic?", aaze0055:6) with a `leave` effect, as the cloud stair does; in a scenario its Yes step was selected but the
  party never left for the ODM (the same shape reaches X8, a BLV). The exit preset reaches ODMs (XD-06, XD-09, XD-27),
  so the door uses it, and the original line is now the window's sense rather than its words. ~~A request to A1.~~
  Closed by D-24 (DECISIONS.md, merge point 10): a plain "Leave X?" is never a map question, such exits use the `exit`
  preset and the game's window, so the door's preset is the rule, not a workaround; `leave` moves at once.
- **`exit:x8_clouds` to `xeen_x8.blv`.** On the roof, five steps of cloud (`xwcloudst`) climb north-east; the top step
  (`platform:cloud_top`) runs `evt:cloud_stair`: "Stairway to Heaven.  Climb?" (aaze0058:6), "Climb (Yes/No)?", and
  on Yes leaves for X8's High Magic clouds at (-10752, -4337, 0) facing north.

## Say why the party is here

`evt:arrive` (a one-shot timer, message window): "THE TOWER OF HIGH MAGIC. The Enchanted Key from the Cave of
Illusion turns, and the door shuts again behind you with a sound like a held breath. Artemus was plain about it: the
Skeleton Key that opens Darzog's Tower lies with the Archmage who built this place, in his study at the very top. Six
laboratories climb the floors between, and their keepers will not welcome you. The stairs go up the east and west sides
in turn." M13 has no arrival hook; if A3 adds one, it replaces this message.

## Original lines

"Fire Brew", "Electric Brew", "Cold Brew" (aaze0055:1-3) and "Poison Brew", "Energy Brew", "Magic Brew"
(aaze0057:1-3) as the cauldrons' hover names; "Pandorian Box", "The box is empty." (aaze0055:4, 5); "Leave the Tower
of High Magic?" (aaze0055:6); "The Art of Magic", "Mysteries of Light" (aaze0058:1, 2); "Stairway to Heaven.
Climb?" (aaze0058:6); "You found a skeleton key in the chest." (aaze0058:7, A3's hook text); "There is nothing on, in,
or under the bed." (the graph's quarters).

## Ids

- Quest bit: M13's `done` 111260 (set by A3's hook; project.yml `skeleton_key_found`). **No map qbits** of
  110680-110719: every two-state mechanism is a map variable (`frost_thawed`, `gate1_open`, `gate2_open`,
  `gate3_open`); after a refill the doors and gates close with their variables and are opened again the same way.
- **Player bits 11246-11251** (A3 to register in m13.yml): 11246 Fire Brew, 11247 Electric Brew, 11248 Cold Brew,
  11249 Poison Brew, 11250 Energy Brew, 11251 Magic Brew.
- Items: Librarian's Key 12260, Skeleton Key 12100 (hook), Enchanted Key 12306 (the X3 door's condition), Prismatic
  Light 483 (engine).

## Textures (one family per area)

**32 distinct of the M cap 45, 0 new** (`python3 tools/xeen/texture_budget.py`). `texture_use.py --project`: 24 face
textures of 10 main maps.

- **Celeste (MM7 7d25), A6's "towers" family, everywhere:** rubble `hwm2wall` (ground floor, stair halls, lift core,
  parapet), plaster `hwp1bwall` with the marble skirting `7tws1fa` (labs and landings), planks `hwr1wall` (quarters,
  library, study), marble floors `7tws1f` and `t2s1fl`, beams `hwm2rf` (every ceiling, the lift decks), the painted sky
  `7plansky1` (observatory ceiling), frieze `t3s2b` and plaster `hwp1b` in the doorways, doors `hwm2d` (carved blue)
  and `hwp1d` (the alchemist's sigil), pillars `hwm2el`.
- **Clanker's Laboratory (MM7 7d12, Bracada's other wizard house, Celeste's sibling):** bookcases `7t1books`, desks
  `7t1books1`, the cabinet `7t1cabs`, the garden's soil `hhp2b2`; bed sheets `t2bedsht`.
- **Where Celeste has nothing:** the athanor's coals `lava` (Castle Gloaming's, with the liquid bit and a flow), the
  frozen door's ice `orair32` (MM6 Icewind Keep), the world's riveted iron `xwiron` (coils, the athanor's stack, the
  still, the steam pipe), the grille `xngrille` (lift gates), the sky `xwsky` and cloud steps `xwcloudst` (A6's).

## Dressing (D-7)

22 floor props, 4 of them containers (two barrels and two sacks along the reagent store's walls). A7's
`check_dressing.py` on the installed map's export: **0 findings** (`dress_check.txt`). `oymap audit --world xeen` on
the installed map (the studio's dressing checks as they stand on build-xeen; A1's D-7 recalibration may not have
landed): **0 dressing findings** (it found one error in the first L4, the orrery on the observatory's walking line,
moved off it). The cauldrons stand in corners or against walls, off every line between openings.
**Dressing exceptions:** none.

## Playtests (4 of 4)

Run by `output/studio_cal/xd11/four.sh` (one game at a time, exact PIDs) with `build-xeen/game/openyamm --asset-root
assets_dev --extra-mount output/studio_cal/xd11/mount --world xeen --map xeen_xd11.blv`; logs `run/four_144220/`.

- `playtest.yml` (190 steps, level-20 party, immortal): the arrival window by its text; the enchanted door's question
  and its sealed answer; the Fire Brew and its refusal; the Electric Brew; lift a's call button refuses before gate 1;
  the east stair; gate 1 bolted, its lever, `gate1_open`; lift a down to 0 and back up; lift b's call refuses; the Cold
  Brew; the frozen door's window; the reagent store's door, the valve (window, the door opens, `frost_thawed`), the
  empty Pandorian Box's line; the Poison Brew; the west stair; the Energy Brew; the Head Sorceress dead, the Librarian's
  Key from her corpse; the Magic Brew on the dais; a bed's line; the quarters' chest; gate 2; the Librarian's door; the
  library stair; gate 3; The Art of Magic (window); the Prismatic Light spellbook from the cabinet; the Archmage's
  chest (the Skeleton Key once, qbit 111260, no second key); the observatory's Pandorian Box; the Stairway to Heaven;
  the cloud stair's question and its sealed answer; then the cages c, b, a straight down to the ground floor and out to
  the coils.
- `playtest_hostility.yml` (20 steps, as XD-27's): 11600, 11601, 11180, 11185 none peaceful and each hostile; 30-60
  actors at load; a Flying Feet, a Guardian and a Sorceress spawned side by side do not take each other on, the last
  goes for the party.

## Pictures (looked at)

`output/studio_cal/xd11/shots/` (contact sheets kept, the PNG folders deleted for the disk; `tour_*.yml` remake them):
`tour_before` (46 poses on a fresh map, sheets `before_s_1..6.jpg`), `tour_after` (the same poses from
`after.oysav`, saved at the end of the playtest: gates open, the frozen door open, the cages down, chests looted;
`after_s_1..6.jpg`), `tour_fix` (`fix_s_1.jpg`), and the tops of the three lifts in play (`decks.jpg`: `--position`
on each deck at the start; the gate and the core's rubble seen, the arrival window over the lower half).
What I changed after looking: the lights washed the plaster white (room lights cooler and shorter, the brew glows
softer); the enchanted door's picture tiled (now at scale 1.5 on a 192 by 384 panel); the braziers stood inside the
athanor's crucible benches; the orrery stood on the observatory's walking line.
Still weak: the rooms are bare beside MM7's furnished labs (a few tables and shelves would help); the frozen door's ice
reads as blue glass tiles (`orair32` is a small tiling picture); the lift decks are plain planks, not a cage; the cloud
steps show `xwcloudst` cut into blue and white patches (as XD-12's); the levers are small on the plaster.

## Words needed

1. **A sealed exit**: a neighbour that exists only on paper (an exit face that asks its "Leave ...?" and answers with
   a line, until the target map is installed), so that unsealing is not a rewrite of the event and the object.
   Workaround: a panel with a question event.
2. **A lift with more than two stops** (D-4 item 4's preference): three stacked lifts instead.
3. **A cage** on a lift: bars that ride with the deck (XD-08 asks the same).

## Tool defects

1. **Tours over a floor hole**: a screenshot tour's pose above a lift deck that fills a floor hole is drawn from the
   room below (the picture is sky and the deck's top); the same place in play (the party set there by `--position`)
   draws right. Pictures of lift tops need `--position` runs.
2. A wall panel's `surface.size` does not stretch its picture (it tiles at the texture's own size); `scale` works.
3. The question events get `click.silent` infos ("when answered ... a click shows nothing") though the answer shows a
   message window (played).
4. As XD-12: `oymap build` warns of chests not titled Chest/Cabinet (the original "Pandorian Box").

## Blocked, and requests

- **A2:** map_stats row 9127 (and bolster) for XD-11 in `source/map_rows.yml`: lock 6, trap 3, perception 6, music 34,
  STONEROOM, one slot `{family: magic_constructs, tier: 0, count: [2, 3], weight: 100}` (markers carry fixed tiers a
  and b). Without it the game cannot activate the map from assets_dev ("could not activate scenario map") and
  `balance.py` counts only the placed monsters. The playtests ran with the test mount `output/studio_cal/xd11/mount`
  (copies of the world's map_stats.txt and bolster_maps.txt plus that row); when A2's row lands, run `MOUNT=0
  ./four.sh` and delete the mount.
- **A3:** register player bits 11246-11251 (above) in m13.yml; M13 has no arrival hook (the map keeps its own).
- **A6:** none (no new textures).

## What the user should look at when playing

- The first room: the enchanted door asks to leave and stays shut; the arrival window says why the party came.
- Each lab's cauldron in its own glow; drink each, then try again with the same character.
- The frozen door before and after the steam valve; the pipe from the store along the walls.
- The magic lab: the Head Sorceress, and the key on her corpse; the Librarian's door.
- The gate levers and the cages: from the top landing straight down to the coils.
- The library (The Art of Magic, the cabinet), the study's chest (the Skeleton Key), the roof and the stair of cloud.
- Whether the bare rooms and the bright plaster read as a wizard's tower.

## X8 linked (lane A8, 2026-11-20)

X8 Cloudreach is installed (A6, `xeen_x8.blv`, an open-air BLV), so the Stairway to Heaven is no longer sealed.

- `tools/gen.py`: `exit:x8_clouds` now goes to `xeen_x8.blv` at **-10752, -4337, 0 facing north** (90 degrees; the
  orchestrator's explicit arrival; the built Lua reads `evt.MoveToMap(-10752, -4337, 0, 512, ...)`).
  `tools/dress.py`: `evt:cloud_stair` keeps "Stairway to Heaven.  Climb?" and on Yes runs `{leave: exit:x8_clouds}`.
- `playtest.yml`: the cloud stair's question left out of the main walk (it would now leave the map); the walk still
  climbs to the roof and rides the cages down. New `playtest_exit.yml` (12 steps): set_pose on the roof by the cloud
  stair, Yes, asserts `xeen_x8.blv` within 128 of the arrival.
- Rebuilt and reinstalled with `go.sh` (label "X8 exit unsealed"): validate no issues; 25 rooms, 1,589 faces, 23
  doors, 40 events, 5 chests; `fmt --check` clean; `audit --world xeen --reach --solve` (`audit_x8.txt`): 0 errors,
  0 faces in one plane, 25 of 25 sectors, no dressing finding.
- The enchanted door to X3 stays sealed (X3 not installed).
- A2 has since written map_stats row 9127 **without slots**; the playtests still need `MOUNT=1` (the mount's row has
  the slot) until A2 adds the slot to `source/map_rows.yml`.
- Runs after the link (`four_x8b.out`, `MOUNT=0`, from assets_dev with A2's slot-less row 9127):
  `playtest_exit.yml` 13 of 13 **4 of 4**, `playtest.yml` 185 of 185 **4 of 4**; `playtest_hostility.yml` fails 4 of
  4 at step 8 ("0 living actors of monster 11600"): with no slot in the row the spawn points make no Flying Feet. It
  passes again once A2 adds `{family: magic_constructs, tier: 0, count: [2, 3], weight: 100}` to XD-11 in
  `source/map_rows.yml`. The old test mount (`output/studio_cal/xd11/mount`, copies of map_stats.txt and
  bolster_maps.txt) is now stale and makes the game fail to load ("could not load headless gameplay data"): run with
  `MOUNT=0`, or refresh its copies from the current `data_tables/` with the slot added, until A2's slot lands; then
  delete the mount.

## Session 3 (2026-11-20): A2's slot, hostility 4 of 4, mount deleted

Lane A8. A2 wrote row 9127 with its slot (`Xeen Construct`, Dif 0, 2-3, 100 %). From assets_dev with no mount
(`MOUNT=0 four.sh`, logs `output/studio_cal/xd11/run/four_152823/`): `playtest.yml` 185, `playtest_hostility.yml` 20,
`playtest_exit.yml` 13 steps, **each 4 of 4**. The test mount `output/studio_cal/xd11/mount` is deleted and `four.sh`
now runs without it by default. The X3 door was still sealed then; it is linked later in this session (below). A3 has registered the six brews' player bits 11246-11251 in m13.yml.

**Later in session 3: the door onto X3 linked, the arrival once.** Generator copies before: `tools/gen_before_x3.py`,
`dress_before_x3.py`, `geo_before_x3.py`; `go.sh` built, installed and recorded. See "Exits" above.
- The arrival window is first-arrival-only: `evt:arrive` has `condition: {not: {qbit: arrived_once}}` and sets
  `arrived_once` **110680** (XD-11's range 110680-110719). **For A3:** register it in m13.yml (`quests.py` errors on it).
- New playtests: `playtest_exit_x3.yml` (out by the enchanted door, OK, on X3 within 128 of (256, -1674), walk north on
  the islet) and `playtest_in.yml` (a new game on X3 before the door: refused without the Enchanted Key with the
  hook's text, in with it to the start, the arrival window once with 110680, out to X3, in again, no window). The main
  `playtest.yml` cancels the exit window at the door and asserts 110680 after the arrival window. `four.sh` runs all
  five (`playtest_in` without `--map`).
- Checks: `validate` clean, `fmt --check` clean, build 25 rooms, 1,587 faces, 23 doors, 40 events, 5 chests;
  `audit --reach --solve` (`output/studio_cal/xd11/audit_x3.txt`): no error or warning, 25 of 25 sectors with the doors
  out of the way.
- **4 of 4** (`four.sh`, logs `output/studio_cal/xd11/run/four_155244/`): every run passed every step: `playtest.yml`
  185, `playtest_hostility.yml` 20, `playtest_exit.yml` 13, `playtest_exit_x3.yml` 14, `playtest_in.yml` 33. The game
  binary was replaced by A1's merge point 8 at 15:52 during the run. Round 1's first three tests ran on the old binary
  and exited 0. Every later run, on the new binary, dumped core (exit 139) after its last step passed. XD-06's unchanged
  `playtest_exit.yml` does the same on the new binary, so it is the binary's shutdown, not this map (reported for A1).
- **Rerun on A1's fixed binary** (16:33; logs `output/studio_cal/xd11/run/four_163342/`): all five tests 4 of 4, every
  run exit 0 (185, 20, 13, 14, 33 steps).

## Merge point 10 (2026-11-20, lane A8 session 5): D-24

- **Rebuilt** with `openyamm-studio/build-xeen/oymap` (merge point 10), installed into assets_dev by temp file and
  rename (`output/studio_cal/a8_s5/rebuild.sh xd11`; build `output/studio_cal/xd11/b_172244`). Wiring unchanged: the
  enchanted door stays the `exit` preset (D-24's rule for a plain exit, so no longer a workaround: the request to A1
  in "Exits" is closed with a pointer to D-24); the cloud stair keeps its question (a real choice) and its `leave`
  now moves at once (`evt.MoveToMap(..., "xeen_x8.blv", {direct = true})`). Only the door event's note in
  `tools/dress.py` changed (copy before `dress_before_mp10.py`).
- `playtest_exit.yml` asserts no dialog open on X8 after the climb (14 steps).
- **4 of 4** from assets_dev (`four.sh`; logs `output/studio_cal/xd11/run/four_172404/`, `four_mp10.out`, and the
  exit test again `run/four_172521/`, `four_mp10_exit.out`): `playtest.yml` 185, `playtest_hostility.yml` 20,
  `playtest_exit.yml` 14, `playtest_exit_x3.yml` 14, `playtest_in.yml` 33 steps, each 4 of 4, exit 0.
- `oymap record --label "merge point 10: rebuilt, the enchanted door's note points to D-24"` (revision 1014f4d4...).
- Merge point 11 (oymap 17:26:09): rebuilt; the four files are byte for byte the installed ones, nothing reinstalled; the 4-of-4 runs above were on the merge point 11 game (17:10:53).

## Light audit (merge point 14)

By `agent:xeen-a8-lights` (lane A8), 2026-11-20, on A1's light-fixture audit (`devdocs/xeen/formats/LIGHTS.md`,
`output/xeen_a1/lights_xeen.txt`). Changed in the generator (`output/studio_cal/xd11/tools/dress.py`, copy before the
change `dress_before_lights.py`; the generator reproduced the project byte for byte first), L4 regenerated, `oymap fmt`,
`oymap record --author agent:xeen-a8-lights --label "lights audit (merge point 14)"`.

- The athanor's two braziers (`brzier00`, chained) stood on the floor: they hang from the ceiling (544 clear; height
  396, `hangs: true`), their tops 2 into it.

- **Audit** (`oymap audit --reach --solve` on the installed map, `output/studio_cal/xd11/audit_lights.txt`): lights
  errors/warnings before **2/0 (ceiling_on_floor)**, after **0/0**; no dressing finding. **Light exceptions:** none.
- **Installed** by `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh xd11` (build `output/studio_cal/xd11/b_192404`), baked
  (`output/studio_cal/a8_s5/bake.sh xd11 assets_dev`, profile `tools/lighting/baked_indoors/profiles/xeen_xd11.yml`
  (new: XD-08's values)), `tools/lighting/stale_bakes.py --check` lists none of the lane's maps. **Playtests from
  assets_dev, each 4 of 4** (four.sh; record `output/studio_cal/xd11/lights_post.out`): playtest 4/4 (185 steps);
  playtest_hostility 4/4 (20 steps); playtest_exit 4/4 (14 steps); playtest_exit_x3 4/4 (14 steps); playtest_in 4/4 (33
  steps).
- **Pictures** `output/studio_cal/xd11/shots/lights_mp14/` (sheet `lights_mp14_sheet_1.jpg`), looked at: both braziers
  hang on their chains under the ceiling by the stack.

## Session 7 batch (texture fit: cloud steps, lab doorways, bookcase posts; the tower's sound bed)

By `agent:xeen-a8-xd11` (lane A8 session 7), 2026-11-20. The generators reproduced the installed L4 byte for byte
first (`output/studio_cal/a8_s7/snap/xd11/`); copies before the change `tools/geo_before_s7.py`,
`tools/dress_before_s7.py`. Changed in the generators only, L4 regenerated, `oymap fmt`, `oymap record --label
"session 7: cloud steps of xccloud/xccloudsd, lab doorways hwp1b, bookcase posts, tower bed"` (revision 4467ba80...),
installed (`INSTALL=1 a8_s5/rebuild.sh xd11`, build `output/studio_cal/xd11/b_210748`: 25 rooms, 1,607 faces).

- **Cloud stair** (23 errors): the five steps of the Stairway to Heaven (four steps and `platform:cloud_top`) laid
  `xwcloudst`, a picture of a whole stairway of clouds against blue sky, cut over every top and riser. They are now
  made of cloud: X8's walkable cloud tops `xccloud` on the treads and its cloud sides `xccloudsd` on the risers (both
  256 x 256, seamless, one declared size each). `xwcloudst` is dropped: the roof's walls are open sky (`xwsky`), so
  a painted stairway hung there would be a poster in the sky. **Textures 33 of the M cap 45** (32 + `xccloud` +
  `xccloudsd` - `xwcloudst`; `tools/xeen/texture_budget.py` on the installed map).
- **`t3s2b`** (10 errors): the labs' doorway reveals (the theme's `reveal`) laid the carved frieze band up jambs 320
  and 352 high, the band shown 1.25 and 1.4 times. The lab theme's reveal is now Celeste's doorway plaster `hwp1b`
  (pale plaster with a dark rail at foot and head), as the other themes' doorways already are. `t3s2b` stays only on
  the magic lab's dais edge (32 high, along its length: the band once).
- **`family_switch`** (2 warnings): the library's and the study's walls of bookcases (`7t1books` panels 512 high)
  stand in the planked walls (`hwr1wall`). Each run of cases now has a wooden post at each end (64 x 64, 512 high, the
  cabinets' wood `7t1cabs`, platforms: a pillar may not touch a wall), so the cases read as built-in furniture. The
  check still sees the two textures meet behind the posts: kept below.
- **Sound:** `sound:tower_bed`, AU's `xeen_amb_tower` (62802), volume 0.35, one source in the middle of the tower
  ([0, 0] over the first floor's centre at z 1120, half-way between the ground and the top floor), inner radius 1,000,
  outer 3,300: every floor's middle at full level, the corner rooms (arrival, study) about 0.3-0.4 of it, the roof
  under its wind fainter; one source, so no two beds stack. The lab sounds and the roof's wind are unchanged. No
  playtest step (a sound line cannot be asserted).
- **Audit** (`oymap audit --reach --solve`, before `output/studio_cal/a8_s7/audit0/xd11.txt`, after
  `output/studio_cal/xd11/s7_audit1.txt`): errors **33 → 0**, warnings **28 → 28** (26 `tile_seams` on `xwiron`, 2
  `family_switch`, all kept below); 0 faces in one plane; 25 of 25 sectors with the doors out of the way; no dressing
  or lights finding.
- **Baked and tested** (`output/studio_cal/xd11/s7_post.out`; the A8 post: bake 21:26, `stale_bakes.py --check` does
  not list XD-11; logs `output/studio_cal/xd11/run/four_212730/`): from assets_dev, `playtest.yml` 185,
  `playtest_hostility.yml` 20, `playtest_exit.yml` 14, `playtest_exit_x3.yml` 14, `playtest_in.yml` 33 steps, **each
  4 of 4**, every run exit 0.
- **Pictures** `output/studio_cal/xd11/shots/s7/` (`tour2.yml`, sheets `s7_sheet_1..3.jpg`, taken from the installed
  map before its bake), looked at: the cloud stair from its foot, its side and its top step (white cloud treads,
  grey-violet cloud risers, no cut picture); the library's and an arch's doorway jambs in `hwp1b` (a plain frame, no
  band halfway up); the bookcase posts in the study and at the library's south end; the coils' iron columns and the
  still's pipe (`xwiron` plates repeat without a visible line). The source pictures are beside them
  (`clouds_src.png`, `lab_src.png`, `xwiron_2x2.png`).

## Texture fit exceptions

- `xwiron` `tile_seams` (26 warnings: the athanor's stack and crucible benches, the four coils' columns, the steam
  pipe): A6's riveted plates repeat up a face; the wrap falls on a plate joint with its rivet row, so the repeat reads
  as the next plate (looked at: coils and pipe in session 7's pictures). Kept.
- `hwr1wall` beside `7t1books` `family_switch` (2 warnings, the library's west wall and the study's south wall): a
  wall of bookcases set in the planked wall, framed by a wooden post at each end (platforms, which the check does not
  count as a pillar between). Kept.

## Session 21 (A8): AU's sounds

The room-filling beds `sound:tower_bed` take `pan: false` (D-48); the point sounds keep panning. Through the generator; installed 10:05, rebaked, tests 4 of 4 from assets_dev, audit 0 errors (lane log `A8.md`, "21st session").

## Session 26 (A8, 2026-11-22)

- D-89 (A3 34th asked for a lock on the study door): the study door would also have shut the study's two sorceresses,
  the observatory, the stairway, the roof's spawn and the Stairway to Heaven behind the Enchanted Key (`reach.stranded`
  on all of them), against D-89's "fully clearable" and its premise that the study holds no monsters. The lock is on the
  Skeleton Key's chest instead (`evt:study_chest`: `m13.study_door` first, its refusal line as a window; then
  `m13.skeleton_key`); the study door is a plain door. DECIDE raised in the A8 report; one line to move it back.
- F16: the Stairway to Heaven (event 11) is the `exit:` effect's standard entrance window (OK/Close), no Yes/No.
- F13: the six brews' lines are status lines (`text:`, held by length), no window.
- F12d: the Art of Magic lectern shows the open book (`xnpbook` 128 x 128, `fit`).
- F14: the athanor's hearth (lava) is 48 down, not 64: the party steps back out (`check_drops` 0).
- Tests: playtest (brews by `status()`, the chest refused then opened with 12306), playtest_in (X3's door is open since
  D-89), playtest_exit (OK). Installed 00:31, baked, 20/20 from assets_dev; audit 0 errors / 28 warnings (as before).

## Session 29 (A8, 2026-11-22): D-89 identity

- **Octagonal tower** (DESIGN_GATING_AND_IDENTITY 2.2/2.3 "Towers are towers"): geo.py's "D-89 identity" block cuts
  the square's four corners at 45 degrees, 512 along each side, on every floor and the roof (`octo()`); the corner
  rooms (door room, athanor, east/west/library stairs and their galleries, reagent store, magic lab, study, Stairway
  to Heaven, roof) get a slanted outer wall. The lift cores are octagons too (96 cuts). Fitted to the cuts: the
  athanor's crucible benches at x ±1344, the library stair's flight 320 wide at x 1728, the reagent store's barrels
  and sacks, the Archmage's books now the whole slanted wall of the study (posts gone), the exit kept at x -1408
  (`at`), the roof opening's wall index computed.
- **Windows to the sky** on every outer wall (sky panels 128 x 256, bottom 176; in the two-storey stair halls one row at
  the gallery's height), clear of torches, the exit and furniture: about 40 windows on four floors.
- **Crenellated roof**: 32 rubble merlons (192 long, 256 high, every 384) along the octagon (`parapets`).
- **Laboratories**: benches of Clanker's cabinets' wood in the coils, still, energy and magic labs, glass (dec35),
  goblets (7dec46, 7dec48), candles (cndlab0) and memory crystals (mcryst01) on them and on the athanor's benches; each
  lab's room light half its brew's colour. Reagent store `store: true`. `identity: {shape: tower, family: 7d25}`.
- Playtests: `playtest` step at the library gallery x 1792 -> 1700 (by the cut corner); `playtest_in` answers X3's
  entrance window (OK) at both entries (F16, A5's X3 rebuild; it failed before this change too).
- Installed, baked, audit 0 errors / 27 warnings (26 xwiron tile seams, 1 books/planks switch; was 28), check_exits 0,
  drops 0, tests 20/20 from assets_dev (`output/studio_cal/a8_s26/run/xd11/t023137`). Build warning "Pandorian Box"
  (MP42 chest naming) kept: the original Xeen name.
- Captures: `output/studio_cal/a8_s29/shots/xd11_before.jpg`, `xd11_after.jpg` (tour `a8_s29/tours/xd11.yml`).
