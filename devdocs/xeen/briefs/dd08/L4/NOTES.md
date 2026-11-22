# DD-08 Northern Tower, L4: notes

New M dungeon on D5 (the source's dark maze0069-0072: the Voweless Knights' tower), quest Q-D17 The Chalice of
Protection (Black Knight / Villain on the oath route), built with the Map Studio from
`devdocs/xeen/mockups/act5_graphs/dd08.graph.yml` and decider D-61 (`mockups/act5_a8_decisions.md`, which wins) by
`agent:xeen-a8-dd08` (lane A8 session 12), 2026-11-21. Key `dd08`, project `xeen_dd08`, stem `xeen_dd08.blv`,
map_stats 9157 (A2's row), world `xeen`, music 43.

## State and next steps

**Done: ready to install.** Every project file of L1-L4 except the playtests and these notes is written by the
generator (`output/studio_cal/dd08/tools/gen.py`, `geo.py`, `dress.py`); recorded (`agent:xeen-a8-dd08`). Validate
L1-L4: no issues; build: 0 warnings; audit (`--reach --solve`, `output/studio_cal/dd08/audit.txt`): **0 errors, 0
warnings** (info only: the gate's two leaves never move, the thrones' map variables are read by A3's helper); `fmt
--check` clean.

**Scratch root** `output/studio_cal/dd08/root` (`cp -al assets_dev` 05:40; `worlds/xeen/data_tables/` a real copy, A2's
row 9157 already in it; `tools/sync_root.py` refreshes it from assets_dev).

**Next (the lane lead):** `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd08`, then
`flock output/studio_cal/a8_s5/lights/post.lock output/studio_cal/a8_s5/lights/post.sh dd08` (bake, then `four.sh`
from assets_dev), then the baked tour `ASSETS=$PWD/assets_dev output/studio_cal/dd08/shoot.sh things` (and `rooms`),
sheets with `python3 output/studio_cal/dd08/tools/sheet.py output/studio_cal/dd08/shots/things <prefix>`.

**Resume:** `RECORD=1 LABEL="..." output/studio_cal/dd08/cycle.sh` (regenerates L4 from the generator, fmt, validate,
build, install into the root, audit, record; `LEVELS="L1 L2 L3 L4"` for all). Diff the L4 against `.oymap/last` first
if anyone edited it by hand. `four.sh` (`ASSETS=`, `N=`, `TESTS=`; every game inside `a8_s9/slot.sh`), `shoot.sh
<tour>` (`tools/tour.py rooms|things <name>` writes the tour), `tools/texsheet.py`, `tools/sync_root.py`.

## What was built

One BLV of four floors 448 apart in one frame (x east, y north, z up; the tower's centre 0, 0), rooms 384 high (the
chapter hall and the Hall of Thrones 512), 64 of floor between storeys, 128 walls. The split core (D-61 Q29): the core
is two rooms stacked, each two storeys with a hanging head platform (DD-15's way): the great stair L1-L2 and the
Stair of Silence L3-L4; between L2 and L3 the climb goes round through the two wall stairs (two-storey rooms in the
west and east walls), so L2 and L3 are crossed both ways.

- **L1, the gate floor (0):** the porch behind the gate (never entered), the gatehouse (the arrival), the Hall of Arms
  across the south (the founder's statue on its plinth, two banners, two hung pieces: the shield find), the great
  stair's foot in the core (arches south, west and east), the west gallery (the dead mirror) and the west lectern room
  (book 1), the east gallery, the dormitory (four beds, the pillow note, book 2), the refectory (tables, benches, the
  silent reader's pulpit).
- **L2, the armouries (448):** the great stair's head (the graph's core1), the west armoury (helms; the helm find),
  the east armoury (black plate; the cuirass find), the north gallery (arrow slits), the quartermaster's store (chest,
  barrels in a pair, sacks), the wall stairs' landings (book 3 west, book 4 east).
- **L3, the drill floor (896):** the Stair of Silence's foot (arcades west and east), the drill hall's west, south and
  east arms (slits in the yard), the wall stairs' heads (book 7 on the east one by its slit), the west and east studies
  (books 5 and 6, a step plate before the outer wall) and the niches behind their sliding walls (chests).
- **L4, the sanctum (1344):** the Stair of Silence's head (the graph's core3), the chapter hall (dark 7d33 stone,
  `xdvowel` over its two-leaf doors inside, the order's plaque `sign22` on the north wall, banners, four dark niches),
  the antechamber (the voice's mask `xvkmask`, the iron door), the chalice room (the stand, a goblet on it), the Hall
  of Thrones (four Emotion Thrones round the Euphoria Throne on its dais) and the Dunce's alcove, the west cells (three
  beds, Cliff Notes 5-7, the strongbox), the east cells (four beds, notes 1-4) and the ladder loft (the roof trapdoor
  in its ceiling).

## Measurements

`oymap metrics` (`output/studio_cal/dd08/metrics.json`): **31 sectors** (M 20-45; the graph's "about 38" counted the
split halls twice), **38.4 M units² of floor** (M 30-90; geo.py 33.2 by outline, metrics with the stair heads), one
component, 6 loops, **14 doors** (16 door records: two hinged pairs), 4 chests, 2 step plates, **45 placed monsters** +
the four figures. Textures (`python3 tools/xeen/texture_budget.py --root output/studio_cal/dd08/root --map DD-08`):
**36 of 45, 2 new** (`xvkban`, `xvkmask`); the graph planned about 25. Session 17: 35 (`xdthrone` gone with the seat blocks).

| Who | Row | Level | XP | Where | Count |
|---|---|---|---|---|---|
| Slayer Knight | 11150 | 45 | 2,475 | L1 8, L2 9, L3 11, L4 5 | 33 |
| Death Knight | 11151 | 55 | 3,575 | L2 3, L3 4, L4 5 (one in the Hall of Thrones in the Doom Knight's place) | 12 |
| Voweless Knight | 11925 | - | - | the chapter hall's niches, hidden until the oath; peaceful, immobile | 4 (not counted) |

By floor 8, 12, 15, 10 (the graph's). Quiet: the gatehouse, the galleries, the lectern room, the antechamber, the
chalice room, the alcove, the loft, the studies. **Kill XP:** 124,575 for the party, **31.14k per member** (D-61).
The placed knights take A2's faction `xeen_voweless_knights` from their rows (no map relation; the hostility test).

Rest encounters (`project.yml`, = A2's row 9157): `{monster: Xeen Dark Knight, tier: 0, per_marker: [1, 2], weight:
100}`, encounter 10 %, treasure 5, lock 15, trap 8, perception 15, music 43.

## Mechanisms

- **Arrival** (`evt:arrive`, timer once): the first arrival sets 117640 and names the errand in the status line.
- **The gate** (`door:gate`, two hinged leaves `hkm1dl|hkm1dr`, mirrored inside): its click is the exit (`{exit:
  exit:d5_door}`: the game's leave window, D-24) to D5's entrance:dd08_door; the leaves never open.
- **The books** (D-61 Q25): seven lecterns (plank stands with `xnpbook` on top), each `Xeen.vowelessBook("<key>",
  eventId, continueStep)` (A3); a wrong answer plays `closebook` with the hook's slam line. Book 1 sleeping_dogs (L1
  lectern room), 2 laughs_last (dormitory), 3 needs_of_many (west wall stair's landing), 4 love_of_money (east wall
  stair's landing), 5 gift_horse (west study), 6 fool_and_money (east study), 7 wishes_horses (east wall stair's head).
- **The voice** (D-61 Q27): the mask's click asks (one prompt: aaze0072:2 and "Wht d y sk?"): Chlc or aie calls
  `q-d17.voice` (113342), "Chalice" `q-d17.voice_wrong`, anything else `q-d17.voice_other`; after the answer "The mask
  is silent.". `evt:iron_open` (timer) opens the iron door once 113342 is set and on every later load; before it the
  door says "An iron door with no handle and no lock. Beside it, the mask waits.".
- **The Chalice:** the stand's click calls `q-d17.chalice` and hides the goblet on the stand (`evt:chalice_load` keeps
  it hidden once 113345 is set); after it the hook's "An empty stand.".
- **The oath** (D-61 Q28): the plaque's click: without the Chalice the hook's fail text; with it "Swear the Voweless
  oath?" (Yes calls `q-d17.oath` and shows group 40, the four figures; No nothing); after the oath
  `q-d17.oath_again` when a member can still be promoted, else the hook's else text. `evt:figures_load` shows the
  figures on every load once 113344 is set. The knights turn friendly by A2's faction rule.
- **The thrones** (D-61 Q26; D-66 item 7, A8 session 17): six of S's throne models, the click on the decoration
  (`deco:throne_<key>`, events 48-53 unchanged), each `Xeen.vowelessThrone("<key>")` (A3: the lows' conditions, the
  Euphoria Throne after the four, the Dunce's 50 damage); titles Emotion Throne, Euphoria Throne, Throne of the Dunce
  (aaze0072:8-10). The four lows are `xeen_throne` (dark gilded wood, red cushion) by the side walls, their backs 62
  off the wall: (896, 0), (896, 512) facing east, (2176, 0), (2176, 960) facing west, placed clear of the walking lines
  between the hall's four openings (the west arch 800-1120 and the east door 432-592 rule out the old 1088/1984 x
  0/768 square: the audit put three of them 18-102 off a line). The Euphoria Throne is `xeen_throne_gold` (ivory
  cushion) on its 48 dais at (1536, 384) facing south; the Dunce `xeen_throne` at (1600, -576) facing north up its
  alcove. The `xdthrone` seat and back blocks are gone.
- **The sliding walls:** a step plate before each study's outer wall (the source's (3, 8) and (11, 8)) slides it open
  with `stone door0301`'s grind, for good (117652, 117653; `evt:wall_*_open` on later loads).
- **The finds** (117654-117656): the Hall of Arms' shield (a T5 shield, kind 5), the west armoury's helm (kind 6), the
  east armoury's plate (kind 4); then "Nothing here.".
- **Lines:** the founder's statue (aaze0069:2), the dead mirror ("Where to?", "The mirror does not respond.",
  aaze0069:3, :5), the pillow note (aaze0069:15), the beds ("Nothing here."), the Cliff Notes (aaze0072:14-20).
- **The roof** (D-58): the trapdoor in the loft's ceiling: before m30.done the hook's "The trapdoor is shut fast.";
  after it "Climb up through the trapdoor?" (Yes: the hook, then `evt.MoveToMap(5632, 15104, 1158, 512, ...,
  "xeen_d7.blv", {direct = true})`; No: nothing). One way: no arrival in this map.

## Arrivals and exits

| Name | Where | Facing |
|---|---|---|
| entrance:d5_tower (and start) | (0, -1152, 0), gatehouse, 256 inside the gate | 512 (north) |
| exit to D5 (the gate) | measured: D5 (2560, 11776) | 1536 |
| exit to D7 (the roof, after m30.done) | measured: D7 (5632, 15104) | 512 |

D5's door:dd08 (A6) names `entrance:d5_tower` and drops its placeholder effect (D-61 RELAYS).

## Playtests

`output/studio_cal/dd08/four.sh` from the scratch root (`ASSETS=` for assets_dev), `--world xeen --map
xeen_dd08.blv`; logs `output/studio_cal/dd08/run/four_*`, summaries `four_1.txt` (16/16) and `four_2.txt` (the final
build, with the lecterns' posts).

| Test | Checks | What |
|---|---|---|
| `playtest.yml` | 231 | starts on D5, moves in to entrance:d5_tower (position and facing); the arrival line (117640); the statue; the shield find once, then "Nothing here."; the mirror; up the great stair, the west armoury's door, the helm find; book 3: a wrong answer (the slam), the proverb (+1 Might measured), a second read ("You have all taken it to heart."); up the west wall stair, the drill hall, the Stair of Silence, the chapter hall's doors; the iron door shut; the voice: "Chalice" (voice_wrong), "Treasure" (voice_other), "aie" (voice, 113342, the iron door opens, then "The mask is silent."); the Chalice once (12525, 113345), then "An empty stand."; the other six books (vowels, proverb with and without punctuation, upper case); the pillow note, a Cliff Note; the thrones: Euphoria first unworthy, the four lows (the sitter Fear Drunk Weak Insane), Euphoria (+1 Might measured), unworthy again, the Dunce (damage); the plate find; both sliding walls by their plates and the niches' chests; out by the gate to D5 (2560, 11776) facing 1536 |
| `playtest_oath.yml` | 76 | figures hidden, knights hostile; the plaque without the Chalice (fail text); the voice "Chlc"; the Chalice; the plaque: No, then Yes (113344, the Chalice gone, the Energy Disks, the four figures shown, no knight hostile); a reload: the figures still shown, the knights friendly, the plaque's else text |
| `playtest_roof.yml` | 46 | the loft: "The trapdoor is shut fast." before m30.done; with 111600 the question, No stays, Yes lands on D7 at (5632, 15104) facing 512 |
| `playtest_hostility.yml` | 46 | 33 / 12 knights hostile at load, none peaceful, the four figures peaceful; the two kinds side by side do not fight; from the save, the oath bit: all 45 friendly, still after a reload, no infighting |

## Pictures (unbaked, from the scratch root)

`output/studio_cal/dd08/shots/things2_sheet_1..4.jpg` (the tour `shots/things2.yml`, 29 shots: the arrival, the gate,
the Hall of Arms, the mirror, a lectern with its book, the dormitory, the refectory, the great stair, the armouries'
hung pieces, the wall stair's landing and book, the north gallery, the quartermaster's store, the drill yard, the east
stair head's book by its slit, the west study, the Stair of Silence, the chapter hall's doors, plaque, banners and
niches, `xdvowel` over the doors, the mask and iron door, the Chalice, the thrones, the Dunce, the cells, the loft's
trapdoor). The lecterns were first plain blocks (the book unseen); they are now a post and a book-topped slab.
`books_sheet_1.jpg`: the books from above. No bake in the root: the rooms are lit by the generator's lights only.
Tour note: a tour's `commands` are per shot (the first shot carries them: HUD off, doors open); the console's
`SetMonGroupBit` did not show the oath figures in a tour (they show in the game: `playtest_oath.yml`), so they are not
pictured.

## Families and textures

The Towers of Mok family, MM8 Castle of Air d27 (as DD-05): `gston1wl` over a `gstntilev` skirting, `gston1fl`,
`gstn1cl`, `gcstflor` in the core and the wall stairs, `gstn1bot` plinths and the stand, `gcstdoor` doors. The
knights' rooms (chapter hall, Hall of Thrones, the alcove, both cells) in MM7 7d33: `dchb1`, `7tfb1`, `tfb2`, `7trimd`
jambs, `7tfb11` niches, `chb1dl|chb1dr` (the chapter hall's leaves). The gate `hkm1dl|hkm1dr` (D-49), `xkmirror`
(D-37), `xdvowel` once over the chapter hall's doors inside, `xnpbook` the books, `t2bedsht` and
`7trimd` beds, tables and lecterns, `t19b04c` slits, `sign22` the order's plaque, the hung pieces `armormid`,
`armorpor`, `armorrch`, `7sgarm`. New: **`xvkban`** (the lead's, 128 x 256: three in the Hall of Arms and the chapter
hall, two in the Hall of Thrones, once per face) and **`xvkmask`** (128 x 128, once, 192 square).

## Texture fit exceptions

None (audit: 0 texture findings). The dead mirror is `xkmirror` tiled (A6's seamless tile, as DD-05).

## Dressing exceptions

None (audit: 0 dressing findings).

## Lines for A3 (map-local, ORIGINAL_LINES)

- The founder's statue: "A plaque reads:\n\"In honor of the Grand Order of Voweless Knights\"" (aaze0069:2), title
  "Statue" (aaze0069:1).
- The mirror: "Where to?" (aaze0069:3), "The mirror does not respond." (aaze0069:5).
- The beds: "Nothing here." (aaze0069:14); the pillow note (aaze0069:15); the Cliff Notes (aaze0072:14-20), title
  "Bed" (aaze0069:13, aaze0072:13).
- The voice's prompt: "A disembodied voice thunders through your brain, \"What do you seek?\"\nWht d y sk?"
  (aaze0072:2 and the graph's prompt); after the answer "The mask is silent."; the iron door before it "An iron door
  with no handle and no lock. Beside it, the mask waits.".
- The finds: "You lift the shield from its hooks.", "You take the helm from its peg.", "You take the black plate from
  its stand.", then "Nothing here." (aaze0069:17, aaze0070:8); titles "Shield", "Helm", "Armor" (aaze0069:16,
  aaze0070:7, :9).
- The sliding walls: "With a grinding of stone, the wall before you slides aside."
- The arrival: "The Northern Tower of the Voweless Knights. Bosco's Chalice is kept at the top, where a voice asks
  what you seek."
- The pulpit: "The silent reader's pulpit. Nobody reads here: the book is gone."
- The oath's question "Swear the Voweless oath?", the roof's "Climb up through the trapdoor?" (the hook's own).
- Titles: "Exit the Knight's Tower" (aaze0069:0), "Book" (aaze0069:7), "Emotion Throne", "Euphoria Throne", "Throne of
  the Dunce" (aaze0072:8-10).

## Hook notes for A3

No text mismatches with D-61: the voice takes Chlc and aie (`q-d17.voice` text aaze0072:5 + the iron door), the oath
text "before the plaque", the books and thrones as Q25/Q26. One observation: after `q-d17.oath` the two Energy Disks
end up one in a pack and one held on the cursor (`playtest_oath.yml` logs "pack 12334x1, held 12334"); both are given.

## Sounds for AU

The bed `xeen_amb_tower` (one source in the core on L3, `pan: false`, as DD-05); `whistling wind` at the drill yard's
slits and round the trapdoor; the books' slam `closebook`; the sliding walls `stone door0301`. Optional (D-61): a low
rumble under the voice.

## Waiting on

Nothing in the map: A3's hooks and helpers (books, thrones, voice, oath, roof) are in; the two new textures are in.
Outside it: A6's D5 door:dd08 to name `entrance:d5_tower`; the figures' look (11925 on the Slayer look). S's thrones
are in (session 17).

## DECIDE (cheaper to reverse; listed in the report)

1. The founder's statue is MM7's `7dec55` (a stout armoured statue from 7d34) on a plinth: the world has no knight
   statue decoration. S could bind a knight; the event keeps its id.
2. The stair rooms carry both floors (core0 with the graph's core1 as its head, and so on), so the graph's 33 review
   rooms are 31 rooms (the porch and the Dunce's alcove added).
3. The roof asks with the map's own Yes/No and moves to D7 directly (as DD-15's sky door), not through the exit
   preset's window (D7 is a BLV: no leave window either way).
4. The gate never opens: its click is the exit (the porch behind it is a closed sector).
5. The hung finds are random T5 items of the kinds shield 5, helm 6 and armour 4.
6. Textures 36 of 45 (the graph's 25 is not met; in the cap).

## What the user should look at

The gate from inside, the Hall of Arms (banners, statue), a lectern, the great stair from its foot, the chapter hall
(the doors with `xdvowel` over them, the plaque, the niches with the figures after the oath), the antechamber's mask
and iron door, the Hall of Thrones.

## Session 26 (A8, 2026-11-22)

- F16: the roof trapdoor (event 45) is `d7.roof_dd08` then the `exit:` effect's standard entrance window (OK/Close);
  no "Climb up through the trapdoor?". The Voweless oath keeps its Yes/No (a choice, not a move). Audit
  `entrance.question` 1 -> 0 errors. Lua and studio file only (no bake). Tests 16/16 from assets_dev.
- q-d17's stuck walk at (256, 1986, 1344) is a test matter, not the map: the oymap probe walks it; the Slayer
  (actor 46, 11150, hostile, from the chapter hall) wanders into the corridor and A3's walk has no `clear_hostiles`.

## Session 29 (A8): MP42 rebuild

Rebuilt on oymap merge point 42 (2026-11-22 ~02:20). The generator reproduced the L4 unchanged; the build changed
only the four chests: the style world's 7gt002 chest in place of MM6's ch1, same places, none moved. Installed,
baked; audit 0/0, check_exits 0, check_drops 0; tests 4 of 4 (16 of 16, output/studio_cal/a8_s26/run/dd08/c021903).
Chest pictures: output/studio_cal/a8_s29/shots/dd08_chests.jpg (all on the floor against a wall).
