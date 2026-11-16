# XD-06 Temple of Yak, L4: notes

A new dungeon (no original) built with the Map Studio from its own briefs L1 to L3 (in this folder's siblings), by one
agent, 2026-11-15/16, under `devdocs/xeen/ACT2_BUILD.md` and every rule of `devdocs/map_studio/REBUILD_PROCEDURE.md`.
MM7 world as stand-in (`world: mm7`), as X1 and XD-01 to XD-05.

State: `oymap validate` no issues; `build` warns only of the idol placeholder and the four placed monsters' names
(shown on the corpse only); `audit --reach` 0 faces in one plane, 25 of 25 sectors reached with the doors out of the
way; `solve` opens all 25 (step 1 the Yak door, step 2 the buttons and the causeway, step 3 the sanctum doors, step 4
the Master's cell and the reliquary on the Master's death), exits to `xeen_x2.odm` at -1024, -17840, 1053.
Playtests: `playtest.yml` 121 steps **4 of 4** (own mount), `playtest_exit.yml` 12 steps **4 of 4** (combined mount
with X2's build) (`output/studio_cal/xd06/four.out`).

Scratch: `output/studio_cal/xd06/`. **The project files are generated**: `tools/gen.py` writes L4's rooms.yml,
objects.yml, wiring.yml and project.yml; `tools/gen_plan.py` writes L1-L3's plan.yml, project.yml and diagram.txt and
L4's plan.yml (L3's plan, kept); L3's rooms.yml is a copy of L4's (the shell). Edit the generators and rerun them (then
`oymap fmt`, `build`, `install`), not the YAML; no hand edits have been made. `play.sh <playtest> <log>` plays one run
on the scratch mount, `play_exit.sh` the exit run on the combined mount (`play_mount.sh` assembles it from X2's mount
and this one), `four.sh` both four times, `tour.sh <shots.py> <name>` takes a screenshot tour. `ref/` holds the
measured kin (MM6 6t1, MM7 d04, MM7 Barrow I) and the decoded source events (`ref/maze0079_events.txt`).

## Layout (25 rooms, 25 sectors with a floor, 50.4 M units²)

```
                         [Reliquary: ELIXIR]   (slab: opens when the Yak Master dies)
     [Master's cell $]--[ SANCTUM: YAK MASTER + 2 elders, altar ]
                          [Sanctum way]
 [Ossuary]--[Near bank: 3 BUTTONS, basin]==(YAK POOL: 3 blocks, sickens)==[Far bank]--[Lich crypt]
 [Crypt $ coffins]                                                          [Master's stair, up]
 [West stair, down]               [Treasury $ MEGACREDITS]  =gate, 2 bars=   (Master's door: from below)
 [Refectory]--[West chapel: BUTTON W]--[ NAVE: pillars, idol ]--[East chapel]--[Vestry: elder]
 [Dormitory]-#-[Hidden cell $]        [Narthex]                               [Library: BUTTON E $]
 [West passage]-----------------------/      \-----------------------------[East passage]
                                   [Porch] -> X2, the fairy woods' dark south end
```

The temple above (floor 0, 13 rooms): porch (arrival), narthex, the **Nave of Yak** (2,560 by 3,584, 1,088 high and
1,344 under its raised middle, eight brick pillars, Yak's idol on a dais), two chapels, two passages, dormitory with a
secret door to a hidden cell, refectory, library, vestry, treasury. Two stairs of 24 steps link it with the undercroft
768 below (12 rooms): crypt, ossuary, the **Yak Pool** between its near and far banks, lich crypt, sanctum way, the
octagonal **sanctum** (2,432 across, 960 high, eight pillars, the altar on a dais), reliquary, Master's cell, and the
**Master's stair** back up to the vestry. Loops: the west wing, the east wing, and the undercroft ring (down the west
stair, up the Master's stair; closed until the Master's door is opened from below).

## The set piece

- **Switch puzzle 1, the treasury's two bars** (the source's switches that open a wall in pairs). Two upright bars of
  riveted, iron-banded timber stand before the treasury gate in the nave's north wall. The west chapel's button sinks
  the west bar, the library's button the east bar. Learnt in the game: the button stands out of a light carved plaque
  and goes in when pressed, the plaque darkens to green-black slab, the text says what it did ("Out in the nave, iron
  grinds on stone: the west bar before the treasury gate sinks into the floor"), the bar is seen gone, and the gate,
  clicked, says which bar still stands and where the buttons are ("one in a chapel, one among their books"). A step text
  on the dais points at the gate.
- **Switch puzzle 2, the causeway** (lights-out in three). Three stone blocks lie in a line in the pool, their tops at
  the water; three stone buttons in a low kerb at the near bank's edge. Button 1 moves blocks 1 and 2, button 2 blocks 2
  and 3, button 3 block 3: each press raises a sunk block and sinks a raised one, and the button stays in until pressed
  again. Learnt in the game: the bank's first step text names the blocks and buttons, and the party presses them
  looking over the kerb at the blocks (pictures 31-36, `buttons/`). Solution: buttons 1 and 3; pressing all three leaves
  only block 1 up; any state can be undone.
- **The pool that sickens** (MM6-8 pool, a condition with a visible tell). The tell: green-teal bubbling water (MM7's
  `7slimywtr`, shader liquid), a slow sick-green pulsing light, bones and a skull at the rim, the bank's step text
  ("bubbling and stinking of rot"). Wading in diseases the whole party ("The pool makes you ill."); five steps lead out
  onto the near bank. The basin "Yak Pool" at the rim: drink for +2 Endurance (permanent, once per character, the
  source's +5 rescaled to an MM6-8 fountain) and disease every time.
- **The Elixir**: the reliquary behind the altar is sealed (a carved slab) while the Yak Master lives; his death raises
  it ("The Yak Master falls, and the slab behind the altar grinds up"). The casket holds the Elixir of Restoration
  ("You have found the Elixir of Restoration!").

## Monsters (MM7 stand-ins; about 50: 19 spawn points and 4 placed)

| Design (MONSTERS_AND_ITEMS) | Stand-in | Where | Count |
|---|---|---|---|
| Slot 1 Cultists: Yak Priest 20 | Cleric of the Moon (215, 20), slot tier b | nave 3, chapels 2, dormitory, refectory, library, vestry, sanctum: 10 points × 2-3 | 20-30 |
| Slot 2 Skeletons (16) | Skeleton Lord (399, 14), tier c | crypt 2, ossuary 2, near bank 1, far bank 2: 7 × 2-3 | 14-21 |
| Slot 3 the source's Yak Liches | Lich (289, 20), tier a | lich crypt: 2 × 1-2 | 2-4 |
| Yak Elder 28 | Necromancer (307, 25), placed, named | sanctum 2, vestry 1 | 3 |
| **Yak Master 35** (boss) | Speaker for the Dead (308, 35), placed, named, `hp: 680` (3 × 227), carries the sixth Megacredit | sanctum | 1 |

Levels 14-35, inside the band (14-28, the boss 35). Kill experience at the expected counts: about 26,900, **6.7k per
member** against MAPS §0's 6.4k. Groups 2-3 per point as §0 asks. The necromancers summon ghosts (their MM7 row).

## Loot and story (M10, Q-C12)

Map treasure level 2 (§0), chests at 2, the boss hoard one step up at 3. Six chests: the **treasury strongbox** (five
King's Megacredits, 1,500 gold, two level-2 rolls; "King's Megacredits!"), the heavy coffin in the crypt (Might 25 or
"You are not strong enough to open the coffin."), the library's scroll chest (two MM7 scrolls and a roll), the hidden
cell's chest, the Master's hoard (level 3, 2,500 gold), the **reliquary casket** (the Elixir). The party comes with
Mirabeth's Yak Stone (X2's door tests qbit 110101; the inside has no second lock) and leaves with **six Megacredits**
(the five Newcastle's walls cost in M9, one spare as the source's 8 left slack; the design's 15 over three dungeons
stands) and **the Elixir of Restoration** for Mirabeth (Q-C12: +5 Personality there). The arrival message says both
plainly. Quest bits: `elixir_found` 110400 (casket opened), `yak_master_slain` 110401, `treasury_opened` 110402.
Items: the Elixir 12191 is MM7's Elixir (1431); the King's Megacredit 12192 MM7's "Floor Tile (w/ moon insignia)"
(1438: a round carved disc, the nearest picture to a minted credit; no MM6-8 item is a coin). The source's spell books
(Light, Sparks, Acid Spray, Hypnotize) are the library chest's scrolls.

## Mechanisms (19 door records)

Doors: the Yak door, two narthex doors, the treasury gate, the Master's door (opens from the stair only; from the
vestry: "A plain slab without ring or handle. It is meant to be opened from the other side."), the sanctum door, the
Master's cell, the reliquary slab, one secret door (dormitory, the wall's own brick, flagged secret). Movers: the two
bars (48 thick, 512 tall, `7gt001a`, standing 32 out from the gate). Lifts: the three causeway blocks. Switches: five
push buttons (`kind: button`, 48 square, 24 deep, the carved `7t1butt` face on `7t1butts` sides: MM7's own switch, as
d04's three vault switches and the Grand Temple of the Moon's are); the two bar buttons sit in carved `t6s1c` plaques
that turn to `t4s1fl` when pressed. Doors are d04's iron-bound `t5d1`, one picture per leaf (doorways 1:2, slide up,
not folding).

## Measured against shipped M dungeons

| | XD-06 | MM7 Temple of Baa (d04) | MM6 Temple of Baa (6t1) | XD-04 | XD-05 | M band |
|---|---|---|---|---|---|---|
| Sectors | 25 | 31 | 49 | 33 | 26 | 20-45 |
| Floor area, M units² | 50.4 | 33.0 | 440 (four open caverns) | 34.9 | 44 | 30-90 |
| Monsters | ~50 (19 points, 4 placed) | ~46 (11 points, 35 placed) | 53 points | ~52 | 40 | 45-75 |
| Doors (real) | 9 | 14 records | 20 records | 29 | - | 6-16 |
| Chests | 6 | 5 | 6 | 4 | 4 | 3-7 |
| Loops | 3 | 4 | 7 | - | 1 | - |

`compare.py` against d04's metrics: 22 in, 7 near, 6 out (out: start reach, fixed actors, lights, light sources per
area 1.0 against d04's 3.0, decorations per area 1.7 against 3.3, floor spread). `scale_bands.py`: bigger rooms 2.16 M
(shipped median 1.64, percentile 68), largest room 9.5 M (median 6.13, 65), typical ceiling 768 (521, 87), taller
rooms 1,024 (570, 83), doorway 384 (256, 61): all above the shipped median. The MM6 temples' feel taken: a pillared
central temple with chapels, the clergy's quarters, a sanctum with pillars and an altar dais below; MM6's temple riddle
doors ("As the winds blow ... Zap!") were not taken (decision of 2026-11-13).

## Textures (two families)

- Temple above, treasury, sanctum: **MM7 Temple of Baa (d04)** as d04 lays it: brick `t6s1bs`, flags `t6s1fl`,
  coffered ceiling `t6s1c`, the skull frieze `t6s1b` in a band 640-896 in the nave and sanctum, green-black slabs
  `t4s1fl`, doors `t5d1`, riveted boards `7gt001a`, beds `7t1beds`/`t2bedsht`, cabinets `7t1cab`, buttons `7t1butt(s)`,
  `t2bs`. Torches: see "Light" below.
- Crypts and pool caves: **MM7 Barrow I (mdt03)** as it lays them: rock walls `t5bs`, floors `t2bs`, roofs `t4bs`,
  plastered crypt walls `hwp1b`, cut stone `7t1s2b`.
- Two from neither, with reasons: bookcases `7t1books` (d04's `7t1books1` is plain wood; `7t1books` is MM7's Temple of
  the Dark's, the same 7t1 kit) and the pool's `7slimywtr` (MM7's slime water; the only sick-coloured MM7 liquid).
- Nothing generated. Wanted (not made): a yak-headed idol (placeholder; MM7's statue `7dec54` stands in), a greener
  liquid (`slime_mm9` is MM9's own).

## Light (the lead's review: the red flooded every room)

Measured: d04 lights its every room with `torch07` (98 of them, decoration light 255, 0, 0 at radius 512) and holds
every sector at minimum ambient 25; in the game it reads red everywhere too (`output/studio_cal/xd06/ref/d04_shots/`).
MM7's other temples and tombs: the Temple of the Dark (t02) 130 `torch05` (violet), the Temple of the Moon 21 and the
Grand Temple 48 `torch05`, Zokarr's Tomb 34 `torch01` (orange, 255, 128, 0, radius 512), the Wine Cellar `torch01`,
Barrow I 25 `torch07`; ambient 22-31. Built: red (`torch07`) only as the cult's accent in the nave (with the idol's
red glow), in the Yak Master's sanctum, sanctum way, reliquary, cell and stair, and in the crypts (Barrow I's own);
MM7's plain `torch01` everywhere else above (porch, narthex, passages, chapels, dormitory, hidden cell, refectory,
library, vestry, treasury). Room ambients unchanged (20-26).

## The Master's quarters (the lead's review: bare)

Measured on d04: its bedchamber (sector 14, 1,226 by 1,034) holds beds of `t2bedsht`/`7t1beds`, three `7t1cab`
cabinets that are its chests, a `7dec32` barrel and four torches; its long stair halls (sectors 7 and 8, about 4,400
long) six torches each (one every ~750), coffered ceilings and the frieze. Built: the Master's cell enlarged to 1,024
by 768 (448 clear → 640), a bed of the same pictures, a row of robe cabinets, his hoard as a `7t1cab` cabinet (hover
"Cabinet", as d04's), a table with a candle, a barrel, a skull pile, four torches; the Master's stair walled in the
sanctum's green-black slabs under d04's coffered ceiling, five torches one every ~740 on alternating walls, a skull
pile at its foot. (Theme bands cannot run on a stepped floor, so the stair has no frieze.)

## Original lines (aaze0079, the Ancient Temple of Yak)

"Leave the Temple of Yak?" (:17; the exit, which shows the game's "Do you wish to leave Temple of Yak?"), "There is
nothing on, in, or under the bed." (:1, seven beds), "There is nothing in the crate." (:2), "There is nothing in the
coffin." (:3, three tombs), "You are not strong enough to open the coffin." (:18), "Yak Pool" (:7, the basin's hover),
"The pool makes you ill." (:25), "King's Megacredit!" (:26, as "King's Megacredits!"), "You have found the Elixir of
Restoration!" (:0), "+ 5 Endurance (permanent)" (:14, as +2). Mirabeth's request is aaze0016:8 (X3).

## Playtests

`playtest.yml` (121 steps, level-15 party of four, immortal, `clear_hostiles` on the way): arrival message; Yak door;
west button (bar sinks); the gate refuses and its message names the standing bar; library button and chest; gate opens;
strongbox (five Megacredits, `treasury_opened`); the crate and a bed say the source's lines; secret door and hidden
chest; the heavy coffin; ossuary; pool's step text; basin (message, disease); into the pool (party diseased); out by
the steps; buttons 1, 2, 3 leave only block 1 up, button 2 then raises all three; across; sanctum; the Master's death
sets `yak_master_slain` and opens the reliquary; the Elixir (`elixir_found`); the Master's cell and hoard; the lich
crypt and the Master's stair; the Master's door from below; back to the porch; the exit's question ("Do you wish to
leave Temple of Yak?") and Close; quest bits and items kept. `playtest_exit.yml` (12 steps): out by the porch door,
OK, arrives on X2 at -1024, -17840 (z 970-1130) and walks off north. Four runs of each pass.

## Pictures (looked at)

`output/studio_cal/xd06/shots/` (54, HUD off, after the second pass; contact sheets `shots_s00.jpg`-`shots_s08.jpg`),
the causeway and library buttons before and after (`buttons/`, `buttons_sheet.jpg`),
earlier takes `look1/` (first look), `lookpool/`, `look2/`, `look3/` (levers and causeway), the X2 arrival
`x2_arrival/` (and `x2_arrival_sheet.jpg`), plan and iso `renders/`. Fixed after looking: the doors' pictures (tiled
3 by 2 at first; now one picture per leaf), the library's plain-wood "bookcases" (now `7t1books`), the levers lost on
brick (now in carved plaques), the pool unseen from its bank (made 160 deep instead of 320 and the levers moved into a
kerb at the edge, so the blocks are watched while pulling), bones lying on the lever post, the green light flooding the
pool cave (toned down), the reliquary slab reading as wall (now carved coffer stone), a cask answering as a crate (a
crate of riveted boards now). Second pass (the lead's review of `shots_s01`/`shots_s07`): the levers that could not be seen nor seen to move are
MM7 push buttons in plaques that darken (09-12, `buttons/`); the bars are timber posts 48 thick standing out from the
gate (08 and 13: one sunk, one standing); the red light only in the nave, the Master's rooms and the crypts (07-18, the
rest orange); the Master's cell (47-49) and stair (50-52) dressed as d04's bedchamber and stair halls. Best: 04 the nave from the arch, 08/11 the gate with its bars, 29-34 the causeway
sequence, 36 the sanctum, 42 the altar and the sealed reliquary. Weakest: the pool caves' flat rock walls (rough walls
barely show), the long Master's stair (bare), the idol (a small stand-in statue).

## Departures from the brief

- Monster stand-ins as above; the Elders' necromancer model and the Master's (MM7's Speaker for the Dead, a woman in
  red) are the nearest MM7 casters at the levels; the source's Yak Master is a lich-like undead.
- The Yak Stone gate is X2's door (qbit 110101); there is no second lock inside.
- The pool is 160 deep, not 320 (to be seen from the buttons).

## Words needed (gaps), most harmful first

1. **Boss rows and placed names**: `monsters[].name` shows only on the corpse (no row in `place_mon.txt`), and the boss
   needs its own monster_data row (CHANGES A1, PRODUCTION E14). Workaround: name and `hp` in the scene.
2. **A dungeon's bolster row** (CHANGES A4): done since the studio's merge 38/39: `map_stats.bolster: LowerToEqual`;
   install writes row 9139 (Temple of Yak, continent 2, LowerToEqual) into the mount's `bolster_maps.txt`, and
   `play_mount.sh` carries it into the combined mount beside X2's 9136.
3. **Sounds from the engine's audio**: `sounds[].sound` must be in `worlds/<world>/audio` of the root; bubbling water
   and chanting exist in no MM7 world folder, and this agent may not write the play root. No placed sounds.
4. **Folding doors with a scaled picture**: a folding leaf takes pictures at one texel a unit only, so a 1:2 door
   picture fits a 128 by 256 doorway. Workaround: non-folding `slide_up` leaves, with the porch, narthex, treasury and
   sanctum way raised so that the wall above holds the leaf.
5. **A lever that reads**: the studio's shipped-size `lever` (an 8 by 32 post, an arm that sinks 16) cannot be seen on a
   brick wall, nor its move. Workaround: MM7's own push button, larger (48), in a carved plaque that changes texture
   on use (`set_texture` on the panel).
6. **One extra mount**: the game takes one `--extra-mount`; following the exit to X2 needs a combined copy
   (`play_mount.sh`).

## Tool defects

- The tour's `actor kill 40000` (console) left the monsters standing in every take (also XD-05's note).
- `assert: {actor_visible: {actor_index: 3, dead: true}}` failed for the Yak Master (index 3 in the built scene's
  actor list) while his kill test (`evt:master_dead`) fired; the playtest checks the quest bit instead. The runtime's
  actor order may differ from the scene file's.
- The tour's per-shot `event N` runs the switch's event, so a pressed button and its plaque show in the tour (used for
  the before/after pictures).
- `scale_bands.py <map.blv>` reads only a root (no `--mount`); the project form works.
- `audit` warns `ride.no_switch` for the causeway blocks (meant: they are worked from the bank, in view).

## The exit link

`door:x2_woods` (`exit:woods`, the porch's south door, event 20) → `xeen_x2.odm` at **-1024, -17840, 1053, facing
north** (DOORS.md's final values from X2's finished map: door at -1024, -18240, 1088, opened by qbit 110101): tested 4 of 4 with X2's build. X2's own
`door:xd06` needs an arrival inside: this map's start, **0, 384, 0, facing north (90)**, inside the porch. For the
lead: install both maps into the play root together (this map's `map_stats` row 9139 is in the mount's copy).

## What the user should look at when playing

The two switch puzzles (is the bars' telling enough; are three buttons too easy or too opaque), the pool's look (teal,
not a sick green) and whether falling in is a fair cost, the red light everywhere above (d04's own torches), the Yak
Master's stand-in model, the long walk back by the Master's stair, and the stand-in item names (a "Floor Tile" as a
Megacredit).

## Hostility pass (2026-11-16)

The user found monsters peaceful to the party beside hostile ones of their kind and monsters fighting each other
(devdocs/xeen/ACT2_BUILD.md, "Hostility pass"). MMerge's `hostile.txt` decides a slot monster's relation to the party
and two kinds' to each other; the studio now warns of both (`oymap build`) and the map says its relations in objects.yml
`relations` (the build's load event `evt:studio_relations`). Written by `output/studio_cal/xd06/tools/gen.py`: the Moon
clerics (214-216, the Cultists) and the Liches (289-291) the party's foes (the slots' were friendly to it).
`playtest_hostility.yml` (written by `output/studio_cal/hostility/gen_hostility_tests.py`) checks the slot and placed
foes hostile, the peaceful ones peaceful and the map's kinds, spawned side by side near the party, not taking each other
on; it passes twice, as do the map's other playtests.
