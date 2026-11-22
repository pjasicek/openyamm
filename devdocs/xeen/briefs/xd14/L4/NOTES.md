# XD-14 Castle Basenji, L4 notes (lane A7, agent:xeen-a7-xd14, 2026-11-20)

Written by `output/studio_cal/xd14/tools/gen.py` (L1-L4; `--levels` writes L1-L3). Never hand-edit the project
files: change the generator and run `output/studio_cal/xd14/cycle.sh` (generate, fmt, validate, build, install into
the scratch root `output/studio_cal/xd14/root`, audit). Built from the graph `mockups/act4_graphs/xd14.graph.yml`
with decider D-39 (`mockups/act4_a7_decisions.md`), which wins over the graph.

## What was built

The cult's keep on X6's north-rim crag, one BLV of four floors (x east, y north, the gate south):

- **L1 (0):** the gatehouse (the arrival; the gate's two wings in its south wall are the way out), the great hall
  behind wolf-headed double doors (beamed ceiling 960 up, four stone posts, a hearth, long tables, two chandeliers), the
  lower scriptorium (rack of six scrolls) and the kitchen and stores (a storeroom, chest) west, the kennels east (the
  set piece: three iron pens with open gates along the north wall, a straw bed in each, a sunken feeding pit), the two
  tower feet and their straight stairs (20 steps of 32), the dungeon stair (16 steps down east from the kennels).
- **Dungeon (-512):** the jailers' room (the cell lever), the werewolf den (rough rock, two straw beds, a brazier),
  the cell row (iron doors of empty cells, the peasant's barred cell), the peasant's cell, the bone pit (chest, two
  scrolls on a ledge). Loop: jailers' room, den, cell row.
- **L2 (640):** the west and east landings, the battlement walk over the gate between them (open sky), the cult's
  wing over the gatehouse: the hall of scrolls (five lecterns) behind the password door, the wizards' dormitory (chest,
  the barred door to the east landing, the keep stair north).
- **L3 (1280):** the keep landing, the Cult Leader's study (desk with the Scroll of Insight, chest, hearth,
  bookcases), the roof walk and the moon tower (open sky; rack of six scrolls, a brazier). Loop round the keep's top.

Loops (4): towers (up one tower, over the battlements, down the other; open from the start), wing (password door,
hall of scrolls, dormitory, its barred door, battlements), dungeon, keep top.

## Measurements

- 26 rooms = 26 sectors; floor area 31.1 M units² (M band 20-45 sectors, 30-90 M units²; footprint about 10,500 by
  5,100 with the dungeon). 1,293 faces. Doors 12 records (14 leaves: the great hall's pair), band 6-16. Chests 4 (T4).
- Monsters 45 placed (Cult Acolyte 11197 ×16 at 24, Werewolf 11421 ×18 at 30, Greater Werewolf 11422 ×2 at 40,
  Wizard 11190 ×6 at 36, Sorcerer 11191 ×2 at 45, Basenji Cult Leader 11198 at 45 in the study), groups 10-25 by
  room; kill XP 56,017 = 14.00k per member (D-39 row 1). The Trapped Peasant 11233 (group 30, immobile, peaceful,
  not counted) in the cell.
- Distinct textures 30 (cap 45), 0 new: d1wcntr, d1smbw, ctwl5, d2wlcctr, d2ceil3, d2flor5, d2flor1, d1ceil1, bemv,
  BemH16a (the lever), cddl/cddr, ckdl/ckdr, beemdorc, d8dorb, ctdor4, d2lgdor, xwcage, scroll, bookcas1, bookcas2,
  straw and the chest family ch1.
- **Arrival** `entrance:x6_gate` (and the map's start): room:gatehouse (0, -1280, 0), facing north, 256 inside the
  gate's wings (the gatehouse's south wall at y -1536).
- **Exit's measured landing:** either gate wing (evt:exit_left 56, evt:exit_right 57; the game's leave window, D-24)
  to X6 (-13312, 15104, 2592) facing south; measured 2 s after landing at (-13312, 15104, **2593**)
  (`playtest_exit.yml`, `output/studio_cal/xd14/a7_xrun/playtest_exit_*.log`).
- Map card (test row 9129 in the scratch root's own `map_stats.txt`/`bolster_maps.txt`): encounter 10 %, treasure
  4, trap 4, perception 8, lock 8, music 42, slots Xeen Werewolf Dif 5 (1-2, 60) and Xeen Wizard Dif 0 (1-2, 40).

## Wiring

- Password door (state:password): from the west landing `evt:password` asks "STOP!  What is the password?"
  (aaze0069:10); "There wolf"/"therewolf" runs A3's `q-c8.l2_door` (password 112161) and opens the door for good; any
  other answer `q-c8.l2_wrong`, and the next click asks again. From the hall of scrolls the door simply opens.
- Dormitory's door (D-39 Q5): from the east landing "The door is barred from the other side." until `dorm_bar`
  118000; from the dormitory it opens, sets the bit and stays open.
- Jailers' lever (`cell_lever` 118001): raises the cell's bars for good (one-way, decided, D-43; a second click: "The lever is down. The shut cell stands open."). The bars talk:
  `q-c8.peasant` at any time. Once the bars are up, a click on his chain post frees him (`q-c8.peasant_freed`,
  500 experience, peasant_freed 112164) and hides group 30, also on every later load.
- Desk: `q-c8.scroll` (the Scroll of Insight 12316, scroll_found 112162; later "The desk is bare.").
- Scrolls (names on hover, A3's hooks decide for the reading member): scriptorium Fire, Electricity, Depression,
  Confusion, Insanity, Weakness; hall of scrolls Intellect, Personality, Speed, Magic, Aging; moon tower Energy,
  Magic (`q-c8.scroll_faded`), Depression, Confusion, Death, Insanity; bone pit Death, Insanity.
- Beds (5): "Werewolf Bed" ×4, "Straw Bed" ×1: a gold find once, then "Nothing here." (aaze0067:0-1, :10).
- Load stages re-open the password door, the dormitory door and the bars from their bits.

## Original lines

"STOP!  What is the password?" (aaze0069:10) and its answers (:8, :16); "Wrong!" (:9, A3's l2_wrong keeps it as its
first word); "Werewolf Bed", "Straw Bed", "Nothing here." (aaze0067:0-1, :10; aaze0068:0-1); the scroll names
(aaze0068:2-7, aaze0069:0-4, aaze0070:0-6); "Leave Castle Basenji?" (aaze0068:14) as the leave window's meaning.

## Checks

- `oymap validate`, `build` (0 warnings), `fmt --check`, `audit --reach --solve` on the installed map: 0 errors;
  `lights.*` 0, `doors.*` 0, `textures.*` 0, `dressing.*` 0. Three warnings `question.answer` (the password is given
  by Arie's note, autonote 4220, and the peasant's hook text, which the audit does not read): kept on purpose.
- Solve: all 26 sectors reached. The solver does not model a door event's `side`: it counts the dormitory's
  doorway slab as reached from the east landing and lets the dormitory-side event lift the bar from there; the game
  does not (`playtest.yml` clicks the landing side first: "The door is barred from the other side.", door shut).
- Playtests 4 of 4 each from the scratch root with `--world xeen`: `playtest.yml` (113 steps), `playtest_hostility.yml`
  (32), `playtest_exit.yml` (15); logs `output/studio_cal/xd14/a7_xrun/`.
- Pictures: `output/studio_cal/xd14/sheet1.jpg` - `sheet3.jpg` (unbaked: the lane lead bakes).

## Words needed

- A click on a placed peaceful monster cannot run a map event (DD-09's note, "an indoor monster with an npc id"): the
  peasant talks through his bars (the bars' door faces carry `q-c8.peasant`) and is freed by a click on his chain post.

## Dressing exceptions

None.

## Texture fit exceptions

None.

## What the user should look at

- The kennels' pens and pit, the gate's two wings from inside, the password door's prompt, the battlement walk and the
  moon tower under X6's sky (once baked).
- The rooms are larger than X6's shell (D-39 Q6).

## Decided

1. The jailers' lever is one-way (decided, D-43): lowering the bars again would only shut the peasant back in; D-4's
   two-state rule is for mechanisms where going back does something.
2. Rest encounters (D-43): Xeen Werewolf at Dif 5 and Xeen Wizard at Dif 0 (Wizard 36 only: Dif 1+ could roll a
   Master Wizard 60). See "Rest encounter exceptions".
3. The battlement walk runs over the gate between the two towers, not over the great hall (whose beamed ceiling
   stands 960 high); the cult's wing stands over the gatehouse.
4. No wolf's-head banners (no shipped texture; 0 new textures planned).

## Rest encounter exceptions

- Wolfmen 20 in about 6 % of the rest encounters (Xeen Werewolf at Dif 5), under the 24 floor: accepted, D-43 (the
  engine has no tier range per slot; a zero weight would drop the werewolves from rests).
