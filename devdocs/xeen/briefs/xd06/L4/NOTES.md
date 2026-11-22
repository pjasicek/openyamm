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

## Rebase, phase 0 (lane A8, 2026-11-20): the design part

What the move into the Xeen world (ROADMAP §6 phase 0, A8 step 3) applies, decided now; only the placed sounds are
built yet (below). The rest waits on A1's world install (W5), A2's rows and A3's hook table.

**Monsters (MAPS §0: 14–28, Yak Master 35, 50 monsters, 6.4k kill XP per member; MONSTERS_AND_ITEMS §2).** The
source's Yak Liches go: the Liches family starts at 35, above the band, and MONSTERS_AND_ITEMS gives the temple
Cultists and Skeletons. The lich crypt keeps its coffins and holds Grave Ghouls (Rotting dead C 18); its id stays.

| Slot (map card) | Family, tier, level | Spawn points (per marker) | Expected |
|---|---|---|---|
| 1 | Cultists A, Cleric of Yak 14 | chapel_w, chapel_e, dormitory, refectory, library ([2, 3]) | 12.5 |
| 1 | Cultists B, Yak Priest 20 | nave_s, nave_m, nave_n, vestry | 10 |
| 1 | Cultists C, Yak Elder 28 | sanctum, plus the three placed Elders (sanctum 2, vestry 1) | 5.5 |
| 2 | Skeletons B 12 | crypt_s, crypt_n, ossuary_w ([2, 3]) | 7.5 |
| 2 | Skeletons C 16 | ossuary_e, near_bank, far_bank_s, far_bank_n | 10 |
| 3 | Rotting dead C, Grave Ghoul 18 | lich_w, lich_e ([1, 2]) | 3 |
| placed | **Yak Master 35, boss row** (×3 hit points, about 680), carries the sixth King's Megacredit | sanctum | 1 |

49.5 monsters, kill experience 25,300 for the party, **6.3k per member (−1 %)**; groups 2–3. The Elders keep their
placed names ("Yak Elder"); the boss row carries the Master's name and hit points (scene `hp` goes).

**Treasure** stays: map Tres 2, chests at 2, the Master's hoard at 3; lock 2, trap 2 (MONSTERS_AND_ITEMS §4.1).

**Items and bits for A2 and A3** (provisional numbers kept): the Elixir of Restoration 12191 (stand-in MM7 1431), the
King's Megacredit 12192 (stand-in 1438, "Floor Tile"); qbits `elixir_found` 110400, `yak_master_slain` 110401,
`treasury_opened` 110402; X2's door reads `yak_stone` 110101 (Q-C12, Mirabeth).

**Original lines** (for A3's ledger `devdocs/xeen/ORIGINAL_LINES.md`; aaze0079): "There is nothing on, in, or under the
bed." (:1), "There is nothing in the crate." (:2), "There is nothing in the coffin." (:3), "Yak Pool" (:7),
"+ 5 Endurance (permanent)" (:14, as +2), "You are not strong enough to open the coffin." (:18), "The pool makes you
ill." (:25), "King's Megacredit!" (:26), "You have found the Elixir of Restoration!" (:0), "Leave the Temple of Yak?"
(:17). Quest text in the arrival message (M10, Q-C12) is A3's to replace with its hook text.

**Studio words since the build.** Bolster `LowerToEqual` was already used (row 9139). Placed engine sounds are new
(built, below). `no_spells`, a doorway's `floor` and a model's `turn` do not apply (the last two are outdoor words).

**Exit** checked against `briefs/x2/DOORS.md`: `door:x2_woods` → `xeen_x2.odm` (-1024, -17840, 1053) facing north,
unchanged. X2's `door:xd06` arrives at this map's start (0, 384, 0) facing north.

**Textures:** 24 distinct face textures in the build (M cap 45), none new.

### Built: placed sounds

`tools/gen.py` gained `objects['sounds']`: the pool's bubbling (`bubbling cauldron01`, loop, radius 2,400, heard on
both banks), drips in the crypt (`drip02`) and the ossuary (`drip03`), each a looping sound with a wait (3–9 and 4–11 s: the game
applies a wait only to a looping sound; `loop: false` plays once per arrival), the sanctum's
torches by the altar (`torch loop`). The regenerated L4 differs from the old one only by these four lines (checked
against a regeneration of the old generator). `validate` no issues; `fmt --check` clean; build warnings as before
(the idol placeholder, the placed names); `audit --reach` 25 of 25 sectors, 0 faces in one plane;
`solve` (`solve_rebase.txt`) opens all 25 in four steps, exit to X2 as above. The scene carries the four
`ambient_sounds`.

Playtests on the final build (drips looping): `playtest.yml` 121 of 121 **4 of 4**, `playtest_exit.yml` 12 of 12
**4 of 4**, `playtest_hostility.yml` 29 of 29 **4 of 4** (`rb2_four.out`, `run/rb2_*.log`; the first build's runs in
`rbA_four.out`). **Run against `--asset-root assets_dev`** (read only) with the scratch mounts: the game binary
`build/game/openyamm` was rebuilt on 2026-11-20 and no longer loads with `output/studio_play/xeen_root` ("Failed to load
engine/data_tables/solo_shop_stock.yml"); the old root is from 2026-11-16. Pictures not retaken: the change is sound
only, geometry and objects are unchanged.

## Into the world (lane A8, 2026-11-20)

Phase 0 step 3, by XD-21's recipe: the map moved off the MM7 stand-ins onto the Xeen world's rows, wired to A3's hooks,
re-dressed under the props rule and installed in the world.

**What changed** (all in `output/studio_cal/xd06/tools/gen.py`; L4 regenerated, `oymap fmt`, `oymap record --author
agent:xeen-a8-xd06`, labels "into the world", "... dressing moves", "... A3's hooks wired"; last revision
`8dc41a1afbc4e4753d1f64a8412390a2`):

- project.yml `world: xeen`; notes without the stand-in wording. Map card slots as A2's map_stats row 9139 (`source/
  map_rows.yml` XD-06): `Xeen Cultist` Dif 2, `Xeen Skeleton` Dif 4, `Xeen Zombie` Dif 5, [2, 3], [2, 3], [1, 2],
  weights 45/45/10. The world's row is what the game reads (install writes no map_stats row).
- Marker tiers as "Rebase, phase 0": Cleric of Yak **11210** (a) at chapel_w, chapel_e, dormitory, refectory,
  library; Yak Priest **11211** (b) at nave_s, nave_m, nave_n, vestry; Yak Elder **11212** (c) at sanctum; Spirit
  Bones **11241** (b) at crypt_s, crypt_n, ossuary_w; Skeleton Lord **11242** (c) at ossuary_e, near_bank,
  far_bank_s, far_bank_n; Grave Ghoul **11252** (slot 3 tier c) at lich_w, lich_e (ids kept).
- Placed: the three Yak Elders → **11212** (placement kept, scene name dropped: the row is "Yak Elder"); the Yak Master
  → boss row **11213** (level 35, 684 hit points from the row, no scene `hp`/`name`; "Yak Master 684/684" over him in
  the pictures), still carrying the sixth Megacredit.
- Items: Elixir of Restoration **12191**, King's Megacredit **12192** (were MM7 1431/1438). Qbits unchanged and named
  as M10/Q-C12: `elixir_found` 110400, `yak_master_slain` 110401, `treasury_opened` 110402.
- `relations` dropped: the world's `relations.yml` makes `xeen_cultists` (11210-11213), `xeen_skeletons`
  (11240-11242) and `xeen_rotting_dead` (11250-11252) the party's foes (`long`) with no feud among them; the build's
  `evt:studio_relations` is gone (40 handlers).
- Exit unchanged: `door:x2_woods` → `xeen_x2.odm` (-1024, -17840, 1053) facing north. Placed sounds unchanged.

**Quest hooks** (A3's `data_tables/quest_hooks.yml`, wired in this move):

| Hook | Event | Wiring |
|---|---|---|
| `m10.yak_arrival` | `evt:arrive` (one-shot timer) | `lua: XeenQuests.hook("m10.yak_arrival")` in place of the map's arrival message |
| `m10.yak_treasury` (once) | `evt:chest_treasury` | the hook sets `treasury_opened`, the experience and the text; the strongbox still holds exactly five 12192 (its `map_gives`) |
| `m10.yak_master` (no call) | `evt:master_dead` | the map sets `yak_master_slain` (and opens the reliquary) as before; the Master carries one 12192 |
| `q-c12.reliquary` (once) | `evt:chest_reliquary` | the hook sets `elixir_found` and gives the one Elixir 12191; the casket holds nothing (no second Elixir) |

Six Megacredits and one Elixir in all. `evt:reliquary` (the slab's message) and `evt:master_dead`'s text stay the map's.

**Props and dressing** (the user's rule, `devdocs/xeen/formats/DRESSING.md`). Checked every room's free-standing props
(decorations not on a wall, furniture platforms, chests) against the openings of the installed blv and the walking lines
between them: A7's `check_dressing.py` (decorations), `measure.py` (run unedited on a copy of the export whose entities
carry their decoration names, `tools/named_export.py`: the export names them by scene id, so measure.py saw none), and
`tools/props_check.py` (platforms and chests too). Files in `output/studio_cal/xd06/dressing/` (`*_before.txt`,
`*_after.txt`). Before: 11 findings (a clump of three casks in the refectory, two of them 192-202 from the chapel's
doorway; the chapels' side altars and statues 112 in front of the refectory and vestry doorways; skulls and bones on
lines).
Moved:

- chapels: the side altars and their statues from before the side doorways to the middle of the south walls (torch
  above moved to the wall's end);
- dormitory: the cots off the hidden cell's secret door (two had stood either side of it) and off the passage doorway:
  two on the west wall south of the door, four on the east wall;
- refectory: table and benches 224 west, off the line from the dormitory door to the stair; casks as a pair in the
  south-east corner and a cask with the crate in the north-east corner (centres 96-128 from the walls, 329-373 from the
  doorways; no clump);
- library: the south wall's bookcases (which stood 112 in front of the passage doorway) now run east of it; the left
  free-standing case moved to the west wall's north half, the other shortened off the ways to the button;
- crypt braziers off the stair-to-ossuary line (to the east wall); ossuary bones, far-bank bones and brazier, the lich
  crypt's brazier (from the Master's stair's foot) and the near bank's rim bones (from the pool steps' landing) off
  their lines; the sanctum's braziers to the dais's back corners, its east skull pile off the Master's cell door's axis;
  the Master's table and candle to the south wall off the door's axis, his barrel to the north-east corner; the stair's
  skull pile to the wall.

After: `check_dressing.py` 2 findings, both kept: the idol and the dais's west skull pile lie on the straight line from
the east chapel's arch to the treasury gate, which crosses the dais itself (the nave's centrepiece; the way goes round
its south edge). Containers: measure.py walls 64-128, portals 329-982, doors 1,006-1,781, groups 2+1 and a single
barrel.
Also kept on purpose: the sanctum's altar before the reliquary slab (the set piece; 304 clear in front of the slab, the
party walks round it on the dais), the near bank's kerb and basin, the chests in the dead-end rooms (hidden cell,
reliquary, Master's cell).

**Checks** (files in `output/studio_cal/xd06/`; `v.sh`, `go.sh`, `world_play.sh`, `world_four.sh`, `world_tour.sh`
copied from XD-21's and adapted):

- `oymap validate` no issues (with `--mount worldtables`, the composed tables of `tools/worldtables.py`); `fmt --check`
  clean.
- `oymap build` (`build_world.txt`): 25 rooms, 1,328 faces, 19 doors, 19 spawns, 40 events, 6 chests. Warnings: the
  idol placeholder; three hostility warnings that are the studio's (it reads `hostile.txt`, not `relations.yml`); and a
  new one, "nothing tells the player on arrival why he is here", because the studio does not see a hook call as an
  arrival message.
- Installed with `--root assets_dev`: `worlds/xeen/maps/xeen_xd06.{blv,scene.yml,studio.yml}` and `worlds/xeen/events/
  maps/xeen_xd06.lua`, nothing else.
- `oymap audit <installed blv> --world xeen --reach --solve` (`audit_world.txt`): 0 faces in one plane, 25 of 25
  sectors with the doors out of the way; known `ride.no_switch` warnings and squashed-texture info. `solve`
  (`solve_world.txt`): 25 of 25 in four steps, none stranded, exit `xeen_x2.odm` at -1024, -17840, 1053.
- Playtests in the **Xeen world** (`--world xeen --map xeen_xd06.blv`, as XD-27 found: the `--map` start makes a
  `world: xeen` scenario start without X1, so `xeen_common.lua`/`xeen_quests.lua` and the hooks run), one game at a
  time (`world_four.out`, logs `run/world/`): `playtest.yml` 125 of 125 **4 of 4** (asserts five 12192 from the
  strongbox, the sixth from the Master's corpse (actor 3, "Yak Master"), exactly one 12191, and all three bits),
  `playtest_hostility.yml` 32 of 32 **4 of 4**, `playtest_exit.yml` 8 of 8 **4 of 4**. Changes: Xeen ids and rows,
  `world: xeen`, a `clear_hostiles` at the causeway's kerb (the Xeen Skeleton Lords reach the party there and one
  blocked the walk back: the first runs failed 4 of 4 at step 82), the crate's step moved with the crate.
- Pictures `world_shots/` (21, `world_shots_sheet.jpg`, `world_tour.sh world_tour.py world_shots`): every monster
  stands as a Xeen row with a 3D model (A2's stand-in bindings): Clerics of Yak green-robed, Yak Priests grey, the
  Elders and "Yak Master 684/684" red-cloaked at the altar, Spirit Bones and Skeleton Lords as skeletons, "Grave Ghoul
  86/86" in the lich crypt; the moved altars, cots, table, casks, bookcases and the Master's cell read clear of their
  doorways; no missing texture, decoration or model in the log.

**Not tested, and why:** the exit onto X2 (not installed; the run ends at the leave dialog, OK offered; the
destination is checked by the Lua's `evt.MoveToMap` and solve's exit line; the steps to add back are in
`playtest_exit.yml`'s header).

**Defects found** (for A1 and A3):

1. build-xeen's oymap indoor build still reads only engine tables (XD-21's defect 1; `--mount worldtables` used).
2. The studio's hostility warnings read `hostile.txt` only; its arrival-message warning does not count a hook call.
3. A7's `measure.py` keys on the entity name, which a studio-built blv sets to the scene id: it finds no props on
   studio maps without `tools/named_export.py`.
4. A3: `m10.yak_treasury`'s `else_text` is "There is nothing in the crate." for the strongbox (a chest); and
   `m10.yak_arrival`'s text no longer says why the party is here (the Elixir for Mirabeth, the Megacredits for
   Emerson), which the map's own message did.

## Exit onto X2 and merge point 3 (lane A8, 2026-11-20)

X2 is in the world (A5) and build-xeen's binaries are A1's merge point 3. This replaces "Not tested" above and defects 1
and the hostility half of 2.

- **Doors:** A5's rebased X2 build (`output/studio_cal/x2/build_w`, `tools/doors.py`) still puts door:xd06's face at
  -1024, -18240, 1088 and the outside arrival at **-1024, -17840, 1053** facing north, as DOORS.md. The map's exit
  needed no change.
- **Studio against assets_dev** (no `--mount`): `validate` no issues (`validate_assets.txt`); `build` (`build_assets.txt`)
  25 rooms, 1,328 faces, 19 doors, 19 spawns, 40 events, 6 chests; the three hostility warnings are gone (the world's
  `relations.yml` read); left: the idol placeholder and the arrival-message warning (the hook call, defect 2). The
  blv, scene, Lua, walk and source came out byte-identical to the build with the composed tables, so nothing was
  reinstalled. `audit --world xeen --reach --solve` on the installed blv (`audit_mp3.txt`) as `audit_world.txt`;
  `solve`: 0 never reached, exit `xeen_x2.odm at -1024, -17840, 1053` (512). `fmt --check` clean.
- **Check root dropped:** `v.sh` and `go.sh` use `--assets assets_dev` only; `output/studio_cal/xd06/worldtables`
  deleted (`tools/worldtables.py` is no longer called).
- **Exit:** `playtest_exit.yml` (14 steps) now takes the leave dialog's OK, asserts `map: xeen_x2.odm` and the party
  within 128 of (-1024, -17840) at z 970-1130, and walks 540 north into the woods.
- **Way in:** `playtest_in.yml` (17 steps, new; `world_play.sh`'s fourth argument `xeen_x2.odm`): a new game on X2
  300 in front of the temple door; without qbit 110101 the door's message ("... the Yak Stone") and the party stays on
  X2; with the bit set, the door leads to `xeen_xd06.blv` at its start (asserted within 128 of 0, 384).
- **Runs** (`world_four.sh`, `world_four_mp3.out`, logs `run/world/{main,host,exit,in}_N.log`), one game at a time,
  `build-xeen/game/openyamm --asset-root assets_dev --world xeen`: `playtest.yml` 125 of 125 **4 of 4**,
  `playtest_hostility.yml` 32 of 32 **4 of 4**, `playtest_exit.yml` 14 of 14 **4 of 4**, `playtest_in.yml` 17 of 17
  **4 of 4**.

## Hooks and dressing, D-7 (2026-11-20)

Touch-up by `agent:xeen-a8-touchup` (lane A8). Only the arrival window changed; XD-06 was already clean under D-7's
dressing audit (`oymap audit --world xeen`: no dressing finding, before and after). The change is in `output/studio_cal/xd06/tools/gen.py` (copy before:
`gen_before_d7.py`). The generator reproduced L4 byte for byte before the change. `v.sh`, `oymap record --author
agent:xeen-a8-touchup --label "first-arrival window"` (revision `a70584cf38bd13cb9cd8aa4909e660e2`). Built to
`output/studio_cal/xd06/build_d7` and installed with `--root assets_dev` (the map's four files).

- **First arrival only:** `evt:arrive` (`m10.yak_arrival`, which has no `once`) opened its window on every entry. It now
  has `condition: {not: {qbit: arrived_once}}` and sets `arrived_once` **110403** (free in 110400-110469). **For A3:** register
  it in m10.yml (`tools/xeen/quests.py` reports "XD-06: built qbit arrived_once (110403) is in no quest file").
- **Checks** (`output/studio_cal/xd06/`): `validate` no issues; `fmt --check` clean; `build`: 25 rooms, 1,328 faces, 19
  doors, 19 spawns, 40 events, 6 chests. The build now warns "nothing tells the player on arrival" (the studio skips a conditioned timer;
  a defect for A1, see XD-12's notes). `audit --reach --solve` (`audit_d7.txt`): 0 faces in one plane, 25 of 25 sectors, the
  two `ride.no_switch` as before. `solve_d7.txt` is identical to `solve_world.txt`.
- **Playtests** (unchanged files; from assets_dev in the Xeen world, one game at a time, `/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/f070ad2b-085f-4ea8-986a-1b63e2657a52/scratchpad/d7/play_once.sh`, logs
  `/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/f070ad2b-085f-4ea8-986a-1b63e2657a52/scratchpad/d7/run/`): `playtest.yml` 125 of 125, `playtest_hostility.yml` 32 of 32, `playtest_exit.yml` 14 of 14,
  `playtest_in.yml` 17 of 17, **each 1 of 1** (the orchestrator's handover stopped the work before the 4 of 4).

**Still open, next steps:** (1) `output/studio_cal/xd06/world_four.sh` for **4 of 4**. (2) A re-entry step showing the
window only once: in `playtest_in.yml`, after entering, leave by the woods door (OK, `follow_map_move`), enter again,
`advance_runtime: {seconds: 3, present_dialogs: true}` and `assert: {dialog: {active: false}}`. (3) A3: register 110403.

## Session 3 (2026-11-20): 4 of 4 and the re-entry step

Lane A8. `oymap audit <stem> --world xeen --assets assets_dev` (studio merge point 7) on the installed map: no dressing finding. The D-7 touch-up's next steps (1) and (2) are done; A3 has registered `arrived_once` 110403 in m10.yml.

- **Re-entry step** in `playtest_in.yml`: after the way in from X2, the arrival window shows once ("The Temple of Yak.")
  and sets 110403; the party leaves by the porch door (event 20, OK), comes back through X2's door, and after 3 seconds
  no window is open. 33 steps.
- **4 of 4** from assets_dev in the Xeen world (`world_four.sh`, logs `output/studio_cal/xd06/run/world/`):
  `playtest.yml` 125, `playtest_hostility.yml` 32, `playtest_exit.yml` 14, `playtest_in.yml` 33 steps, each 4 of 4.
- No prop was moved by D-7 on this map, so no new pictures.

## Light audit (merge point 14)

By `agent:xeen-a8-lights` (lane A8), 2026-11-20, on A1's light-fixture audit (`devdocs/xeen/formats/LIGHTS.md`,
`output/xeen_a1/lights_xeen.txt`). Changed in the generator (`output/studio_cal/xd06/tools/gen.py`, copy before the
change `gen_before_lights.py`; the generator reproduced the project byte for byte first), L4 regenerated, `oymap fmt`,
`oymap record --author agent:xeen-a8-lights --label "lights audit (merge point 14)"`.

- The eight MM6 braziers (`brazir2f`, which hangs on chains) stood on the floor: each now hangs from the ceiling over
  its old place, its top 2 into it (`height` = the ceiling there - the floor - 148, `hangs: true`): the crypt's two
  (556), the far bank's two (648, 644; the cave's ceiling rises to the dome), the near bank's (581), the lich crypt's
  (492), the sanctum's two over the dais (780).
- Dormitory: the south torch from 0.75 (in the west passage's mouth) to 0.4. Vestry: the south torch from 0.5 (in the
  library doorway) to 0.2.
- Master's stair: the stair falls 768 northward and a torch's height is over the room's top floor, so three of its five
  torches stood above the sloped ceiling, in the rock (no wall within 512). All five now hang 176 over their own step
  (heights -515 to 100).

- **Audit** (`oymap audit --reach --solve` on the installed map, `output/studio_cal/xd06/audit_lights.txt`): lights
  errors/warnings before **15/0 (8 ceiling_on_floor, 5 wall_missing, 2 in_doorway)**, after **0/0**; no dressing
  finding. **Light exceptions:** none.
- **Installed** by `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh xd06` (build `output/studio_cal/xd06/b_193202`), baked
  (`output/studio_cal/a8_s5/bake.sh xd06 assets_dev`, profile `tools/lighting/baked_indoors/profiles/xeen_xd06.yml`
  (new: XD-08's values)), `tools/lighting/stale_bakes.py --check` lists none of the lane's maps. **Playtests from
  assets_dev, each 4 of 4** (`world_four.sh`; record `output/studio_cal/xd06/lights_post.out`): main 4/4 (125 steps);
  host 4/4 (32 steps); exit 4/4 (14 steps); in 4/4 (33 steps) (main = playtest, host = playtest_hostility, exit =
  playtest_exit, in = playtest_in from X2).
- **Pictures** `output/studio_cal/xd06/shots/lights_mp14/` (sheets `lights_mp14_sheet_1.jpg`, `_2.jpg`) and
  `lights_mp14_b/` (the crypt again: the first camera stood in a pillar), looked at: every brazier hangs on its chains
  under its ceiling (unlit, as before: `brazir2f` gives no light); the dormitory's and vestry's torches on solid wall
  beside their doorways; the Master's stair torches over their steps.

## Session 24 (A8): merge point 35 tests

`playtest.yml`: after `loot_chest(19)` (the strongbox) and `loot_chest(18)` the chest window was still open on merge
point 35 (an event window over it took loot_chest's close), so the next walk stuck with world input blocked: each step
now calls `close()` and asserts `chest_view: {open: false}`. Rebuilt under oymap 12:46:47 for A1's room step tops
(`evt:sanctum_seen` on the dais; only the .blv changed), installed 17:15, baked, every test 4 of 4 from assets_dev on
merge point 35; audit 0 / 2 (as before).

## Session 26 (A8, 2026-11-22)

- The crypt's heavy coffin tests `ActualMight 25` (a Might potion or spell helps, as the other stat chests; A3).
- F13: the Yak Pool basin's line is a status line (`text:`), no window.
- The Master's one-way slab keeps its plain t4s1fl face (a slab without ring or handle, by design: F12(b)'s list);
  its stair-side title is "Stone door" as its vestry side.
- Drop pockets: `check_drops` lists the Yak Pool's floor (step out 128); the pool's own five steps lead out onto the
  near bank (`oymap probe` from (-768, 9696, -928) to the bank: route found), so no ladder.
- Lua and studio file only (no bake). Tests 16/16 from assets_dev; audit 0 / 2.
