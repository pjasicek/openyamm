# XD-04 Witch Tower, L4: notes

A new dungeon built from its written brief (L1 to L3 here, QUESTS.md story M4 and promotion T1-A) with the Map Studio, by
one agent, 2026-11-13, after XD-01 to XD-03 and their texture passes, under the texture rule and the user's rules of
"What the measure does not see" and "Can a player read it?" (REBUILD_PROCEDURE.md). No original exists.

State: `oymap validate` no issues, `fmt` clean; the build's only warnings are the seven placeholders and the three placed
monsters' names (`Goblin Warden`, `Schoolmistress`, `Head Witch`: shown on the corpse only). No faces in one plane
(`audit`, `things`). 33 rooms, 33 sectors, all reached (`metrics --reach`: 19 at the start, 33 with the doors open).
Two playtests pass four runs of four each (`output/studio_cal/xd04/run/four.out`: `playtest.yml` 164 steps,
`playtest_m4.yml` 58 steps; logs `final_playtest_1..4.log`, `final_playtest_m4_1..4.log`).

**After the second pass** (the user's walk, section below): playtests 175 and 77 steps, four of four each
(`output/studio_cal/xd04/pass2/run9b.out`); installed in `output/studio_play/xeen_root`. The figures above are the
first pass's.

Scratch: `output/studio_cal/xd04/` (`go.sh` builds, installs into `mount/` and plays one test; `four.sh` the four runs of
both; `look.sh <tour> <log>` builds, installs into the scratch root `root/` and takes a tour; `tour.yml` the final
pictures, written by `tools/tour.py`; `look1`-`look3` the earlier takes; `things1/` (first build), `things3/` (final) the pictures of
every interactive thing by `things_shots.py`; `ref/` the shipped maps looked at; `tex/` texture sheets; `repro/`;
`metrics.json`, `solve.txt`, `texuse.txt`). Pictures: `output/studio_cal/xd04/shots/` (40 in the game, HUD off,
`captions.yml`, `plan.png`, `iso.png`).

**What was scripted.** rooms.yml, objects.yml and wiring.yml are written by three generators in my scratch folder,
`output/studio_cal/xd04/tools/gen_rooms.py` (from L3's rooms.yml: L3's geometry kept, themes, bands, furniture, ceilings,
the bridge and the cupboard added), `gen_objects.py` and `gen_wiring.py`; `tools/regen.sh` runs them, `fmt` and
`validate`. No hand edit has been made to those three files that a rerun would lose; project.yml, plan.yml (L3's, kept),
the playtests and these notes are hand-written. Once the project is edited by hand the generators must not be rerun.
**Since the second pass the project files are the source**: the pass edited rooms.yml, objects.yml and wiring.yml
directly (scripted text edits, each checked), so `output/studio_cal/xd04/tools/gen_*.py` and `regen.sh` are retired and
must not be run again (they would undo the pass).

## Second pass: the user's walk (2026-11-13)

The user played the first build from `output/studio_play/xeen_root` and sent eight findings, then a decision: "MM6-MM8
had almost no riddles and nobody minded; it should be more like combat + mechanisms + loot". Scratch:
`output/studio_cal/xd04/pass2/` (`pass2_backup/` beside it is the project before the pass). Pictures: `before/` (the
first build, taken from the play root itself), `after1/` and `after2/` (this build), `pairs/` (before | after, one
sheet per finding), `things/` (every interactive thing, `things_shots.py`); tours written by `tour2.py`, `tour3.py`.

| His finding | What was done | Picture |
|---|---|---|
| 1. Hanging braziers "suspended in the air" beside the cauldron and in the vat hall | The four shaft braziers (`brzier00`, a bowl on a 146-high chain) hang from two new black crossbeams over the stoking floor (`beams`, bottom 448, y = +-560, wall to wall, clear of the cauldron's rim); each at height 300, its chain top 1.5 into the beam. The vat hall's three were hanging braziers standing on the floor as fires under the vats: gone; the bubbling vat is now MM6's cauldron on its tripod fire (`ckfyr00`). Also fixed by the same rule: the shaft's three hanging cages ended 86 under the roof (now 2 into it), the bedchamber's 52 under its ridge (now at the ridge) | `pairs/braziers.jpg`, `pairs/brazier-chain.jpg`, `pairs/vat-hall-fires.jpg` |
| 2. "The slate": a plain stone-flag panel | The generated slate `xwslate`: a slate board in a dark wooden frame with a chalk ledge and chalk, the lesson in chalk and "Rosebud" scratched small in the corner; 384 x 192 on the east wall, its foot 64 above the floor (a child's reading height); click: the lesson as a message window | `pairs/slate.jpg` |
| 3. A skeleton inside a cage with the child | The bone cage model (`bonecage`) has a skeleton in it. The children's cages are now cages of the map: each a mover of four bar panels (generated see-through cut-out `xwcage`, cut from the cauldron's iron) under an iron lid on a chain to the roof, round the child. The warden's ring hoists the cage up its chain (192 to 260 up) and the child is free. One bone cage with its skeleton stays, alone, as dressing in the goblin pens | `pairs/cage-2.jpg`, `pairs/cage-2-opened.jpg`, `pairs/cage-1.jpg`, `pairs/cage-3.jpg` |
| 4. "How am I supposed to know the answer?" at the Rosebud door; then the user's decision: no riddles | **The password is gone (the user's decision; a change against the brief).** The face door opens to a key: the coven's key (MM7's High Cleric's Key, 2187: the Head Witch is a cleric of the Moon here) in the witches' stores, the herb loft's chest, on the critical path before the door. Clues below. No typed answer is left in the map; the skulls' Yes/No offers stay | `pairs/rosebud-door.jpg` |
| 5. (-1434, -185, 1920) "torch in the air" | The pier's two green torches hung in the sanctum's opening onto the pier; now on the pier's own north and south walls. A check over every wall-mounted decoration (`pass2/wall_check.py` on the built map: a solid wall face within 40 behind it, covering its point) found one more: a balcony sconce in an opening, moved. Now 0 of 28 in the air | `pairs/u1-torch-in-the-air.jpg` |
| 6. (-3828, 454, 1920) "imo wrong tiling of the door" | The ward: a 128 x 256 sigil slab laid at its own size on a 192 x 320 leaf (cut and repeated). Every door now shows whole pictures: the two-leaf plank doors are 256 x 256 (one 128 x 256 plank picture per leaf; they were 192 x 288), the stone slabs (bedchamber, hatch), the bookcase and the upper hoist gate 256 x 256 with two whole pictures side by side, the cupboard panel 128 x 256 (its wainscot picture); the ward is the generated `xwward` laid as a 192 x 320 window of a 256 x 512 picture made for it; the lower hoist gate stays 192 x 256 (its wall is 224 long; the plank picture repeats across, reads as planks) | `pairs/u2-ward-door-tiling.jpg`, `pairs/bedchamber-door.jpg`, `after2/18-schoolroom-doors.png` |
| 7. (-817, -480, 0) the hoist's lower gate and call button: "what should this do?" | Hover names "Hoist call" (both buttons), "Hoist cage", "Hoist gate" (the lower plank gate, which now calls the cage like its button). While the brake holds, each says why in a message window: below, "nothing moves: the hoist's rope is held fast somewhere above (the hoist's brake must be in the hoist room, by the coven's sanctum)"; above, "held fast by its brake. The brake lever is on this room's north wall" | `before/03-u3-hoist-cage-and-call.png` (the look is unchanged; the messages are asserted by both playtests) |
| 8. The ward's line "keyed to an oath you have not sworn": "no idea what I should do here" | A message window: a web of witch-light, "ONLY THOSE SWORN AS CRUSADERS MAY PASS. You are not sworn. Old Valia in Toad Meadow names Crusaders: bring her the Alacorn first, and come back when she has named you." The cloud stair's line says the same | `pairs/u2-ward-door-tiling.jpg`, `after2/12-ward-close.png` |

**Where the cage ring is** (his question "where is the key to the cages?"): on the warden's table in his lodge, in plain
sight beside his candle (`items`, the Ring of Keys has a ground model), no longer on his corpse; entering the lodge
shows "In a cage by the west wall, a boy rattles the bars. On the warden's table glints a big ring of keys."; every
locked cage's first click opens a message saying the warden's ring opens it and where it is (the boy: "The big ring, on
his table there").

**The clues to the face door, as a player meets them on the way up:**

1. Ground floor, the warden's lodge: the cue line and cage 1's message lead to the ring (above).
2. Second floor, the schoolroom: coming in, the caged girl calls "Psst! Let me out and I'll tell you a secret!"; the
   cage's hover is "Locked cage"; freed, she says in a message window: "I'm Rosebud. The door at the top of the north
   stair has a witch's face on it, and it only opens to the coven's key. They keep it in their stores in the herb loft,
   past the vats." The slate beside her bears her name (the lesson and "Rosebud" in the corner, its message says it is
   her own name): flavour now, not a password.
3. Third floor, the herb loft: the witches' stores (a chest, hover "Chest") hold the High Cleric's Key with the potions.
4. Fourth floor, the face door (hover "The sleeping face"): without the key a message window: "A face of an old witch is
   carved in the door, fast asleep and smiling in her sleep. The door will not move. Under her chin, in a carved
   rosebud, is a keyhole: the coven's own key would fit it." With it: "The coven's key turns in the carved rosebud ..."
   and the leaves part.

The children's own hover name stays "Peasant" (MM7's Goblin peasants): the studio writes a monster's `name` only for its
corpse, and a living name needs a row in the engine's `place_mon.txt` (outside the project); none of its rows fits a
child. The cage's hover ("Locked cage") is what a player points at: the bars stand in front of the child. The title does
not change once the cage is hoisted (one title per event).

**The M4 order** (QUESTS.md M4 and T1-A): Old Valia in Toad Meadow (X1) gives the quest and the Crystal Key to the
tower's door; the party climbs the tower, frees the children on the way, takes the Alacorn on its bridge and leaves
(by the hoist and the tower door); Valia takes the Alacorn and names the party Crusaders (qbit `m4_crusaders`, the
first promotion T1-A, set on X1); on a later visit the ward on the roof stair falls for Crusaders and the roof's cloud
stair leads to X8 (Cloudreach). The ward and the cloud stair are the only things in the map gated by the world outside,
and both now say so.

**Generated textures** (`level_generation/textures_xeen/`, specs `xw*` in `specs.yml`, made by `xtex.py` like the
earlier ones: Codex image generation with 7d12's and 7d06's masters as references, brightness matched; derived ones by
`xd04_derive.py`; checks in `sheets/check_xw*.png`; installed into `output/studio_play/xeen_root` and the scratch root
as `worlds/mm7/textures_x4/<name>.oytex` and `textures_x2/<name>.png`):

| Texture | Size | What | Where |
|---|---|---|---|
| `xwface1`-`4` (from `xwface`) | 4 x 256 x 256 | the carved face of a sleeping old witch in dark wood, a rosebud under her chin; the face fills the middle 320 of a 512 picture, cut in four quarters | the Rosebud door's two leaves (was the Moon seal `t1d1a`-`d`) |
| `xwward` | 256 x 512 (a 192 x 320 window) | a web of glowing violet and green witch-light with the coven's moon-eye sigil, cut out (see-through) | the ward (was `tws1a`) |
| `xwiron` | 128 x 128 | black riveted iron plates | the cauldron's sides (was `trim11_32`), the cages' lids and chains |
| `xwcage` (from `xwiron`) | 128 x 256 | iron bars every 32 with riveted straps, cut out | the four cages |
| `xwbrew` | 128 x 128 | bright bubbling green brew | the cauldron's top, the larder and pen troughs (was `7slimywtr`) |
| `xwslate` | 256 x 128 (at 1.5) | a framed slate with the chalked lesson and "Rosebud" in the corner | the schoolroom's slate (was `7tfb11`) |
| `xwrecipe` | 64 x 128 (at 1.25) | a nailed parchment: STRENGTH BREW, a toad on a barrel lid, three lines, a crossed-out pot | the herb loft's recipe card (was `t2bedsht` at 0.5) |
| `xwsky` | 512 x 512 (at 2) | open day sky with fair-weather clouds | the roof's walls and ceiling (was `sky_clo1`) |
| `xwcloudst` | 512 x 512 | a stair of white cloud climbing into a blue sky | the cloud stair's exit and its panel (was `sky_clo1`) |

**Checks after the pass** (built with the ninth-merge `oymap`, against `output/studio_play/xeen_root`; the scratch
build in `pass2/build9/` is byte for byte what was installed): `validate` no issues; the build's warnings are the
seven placeholders, the three placed names and two notes that the lodge's and the hidden cage's movers end within 200
of their ceilings (nobody rides a cage). The ninth merge's new checks found, and the pass fixed: the bedchamber's
hanging cage on the ridge line (moved off it, height left to the build), two familiars straddling two circle
platforms, the schoolmistress inside her desk, a sister inside a roof post, four shelf candles inside the talking
skulls (two floor candlesticks at the shelf's ends instead), the cupboard's candle inside the hoard cabinet (removed),
the two cabinets' squashed side pictures (now 128 deep, sides of 7d12's planks `7trimd` at their shape), the hoist
brake's silent second pull (now a message). `audit` is then clean except four `thing.floating` findings for the
braziers: the build accepts them (`hangs: true`, their chains reach the crossbeam: `after2/08-brazier-chain-at-beam.png`)
but the audit, reading the built map, does not know a decoration hangs from a beam (tool gap). `solve`: every sector
(step 1 needs the coven's key 2187, from the loft chest; the closet now reads as a niche too small to stand in: the
hoard cabinet fills it and is used from its doorway). Wall check (`pass2/wall_check.py`): 0 of 28 wall decorations in
the air. Room sizes (`pass2/scale_bands.txt`): bigger rooms 1.71 M (shipped median 1.64 M, percentile 51), largest
4.35 M (35), ceilings 640 (74), taller rooms 704 (62), doorways 256 (9): unchanged. Things: `oymap things`
(`pass2/things9.txt`) and the pictures of every interactive thing before and after use (`pass2/things9b/`,
`contact.png`); the first pass's are `output/studio_cal/xd04/things3/`. Playtests four of four each on the final
build (`pass2/run9b.out`: `playtest.yml` 175 steps, `playtest_m4.yml` 77 steps). Installed into `output/studio_play/xeen_root`
(map, scene, Lua and `map_stats.txt` byte-identical to the tested scratch root) and both played once more there
(`pass2/run_playroot/`, passed).

**Looks worse or still weak:** the hoisted cages keep the hover "Locked cage"; the cages are square boxes of bars
(the bone cages were round 3D models); the sky on the roof is busier than `sky_clo1` (small clouds even at scale 2) and the roof is still a room with painted
walls (gap 1); the hidden cage's closet was raised from 384 to 512 so the child stands under the hoisted cage.

## Texture families (the lead's rule)

Looked at first, in the game and as sheets (`ref/shots7d12/`, `ref/sheet7d12.jpg`, `tex/set_*.png` for Clanker's
Laboratory, the Temple of the Moon, Lord Markham's Manor, the Haunted Mansion, the Temple of the Dark, the Wine Cellar,
Castle Gloaming and the Pit; `tools/roles.py` gives each texture's share as wall, floor and ceiling in a map's export).
The brief's own picks (hhm3b, hdp2b, hhm2rf, hhm3d are in no shipped dungeon; the rest from eight maps) were not used.

| Area | Family | Why, and how it is laid |
|---|---|---|
| The tower: ground, second and third floors, the stairs, the shaft and cauldron chamber, the bridge, the roof's parapet | MM7 **Clanker's Laboratory** `7d12` (a wizard's tower laboratory: rubble stone, black-beamed roofs, wooden laboratory rooms, books) | As 7d12 lays them: rubble walls `hwm2wall` under its carved timber frieze `hwm2b` (a band hung in the top 256 of each wall, so the black timbers run round every room: the brief's "black-timbered tower"), black-beamed plank ceilings `hwm2rf`, cobbles `hhp2b2` (ground floor, stairs), its laboratory's flags `7tfb1` (third floor), plank walls `hwm1bwall` and the carved wainscot `hwm1b` (second and third floors), planks `7trimd` (floors of the nursery, doors), plaster `twb1a` above the wainscot, bookcases `7t1books`, furniture wood `7t1books1`, sheets `t2bedsht`, marble `7tws1f` (the Alacorn's pedestal), posts `trim11_32`, `trim9_32`, its carved front door `hwm2d`, its cabinets `7t1cab`, its liquid `7slimywtr` (the brew), its buttons `7t1butt`/`7t1butts`. The shaft wears the frieze at each storey's height (640, 1280, 1920, 2688): from the cauldron the floors are counted by black timber rings. |
| The coven's fourth floor: Rosebud landing, sanctum, pier, bedchamber, hoist room, the roof stair | MM7 **Temple of the Moon** `7d06` (the Moon cult's temple; the witches are Moon clerics here) | Dressed stone under its frieze `7tws2`, the ram-skull frieze `tws2b` in the sanctum, dark flags `7tfb11`, block ceilings `twb2`, its stone door slabs `twb1` folding up into the lintel, its reveals `tfb2`, its dark brick `wall` (roof stair), red rock `cwb1` (the altar), the carved sigil `tws1a` (the ward), and its Moon seal `t1d1a`-`d`: as the seal door (the Rosebud door) and laid in the floor as the witch-mark circle. |

`texture_use.py --project` (`texuse.txt`): 33 textures. Every one is used by its area's family map except `sky_clo1`
(in no shipped dungeon but MM6's arena and a test map): the sky over the roof, which a BLV cannot open (XD-02 used it
for daylight the same way). The tool's "main source" names each texture's biggest user (Celeste for `hwm2wall`, the
Strange Temple for `twb2` ...), not the family it was taken from. Looked at as whole walls in the game: no window,
porthole or emblem of another place; `hwm2d` (the front door) carries carved runes, 7d12's own.

### Textures to generate (nothing shipped fits; the stand-in in use meanwhile)

All seven were generated in the second pass (the sky as two: the open sky and the cloud stair); see "Second pass".

| What it shows | Size | Where | Stand-in |
|---|---|---|---|
| A carved door face of a sleeping old woman, eyes shut, in dark wood | 256 x 256 in four quarters (or 320 x 320 whole) | `door:rosebud` | the Moon seal `t1d1a`-`d` |
| A translucent, shimmering witch-ward with a sigil (or a liquid of its own) | 128 x 256 | `door:ward` | the carved sigil `tws1a` |
| Black iron, riveted, with a rolled rim: the great cauldron's sides | 128 x 128 | `platform:cauldron` sides | `trim11_32` (black wood) |
| A bubbling green brew, bright and opaque (a liquid colour; the slime water is teal) | liquid | the cauldron, troughs | `7slimywtr` |
| A chalk slate: the lesson in chalk, "Rosebud" scratched small in a corner | 256 x 128 | `panel:slate` | dark slate flags `7tfb11` |
| A recipe card pinned to a beam, a toad drawn on it | 64 x 128 | `panel:recipe` | the sheet `t2bedsht` at scale 0.5 |
| Open sky over meadows for walls and ceiling, and a stair of cloud | 512 x 512 | the roof's walls and ceiling, the cloud-stair exit | `sky_clo1` |

## The world it is built in

As XD-01 to XD-03: `world: xeen` validates but render, solve and the game refuse it, so L4 says `world: mm7`.

| Brief | Built as | Why |
|---|---|---|
| Slot 1 Goblins (Goblin 4 / Gremlin 6 / Gremlin Guard 10) | MM7 Goblin family (Goblin 4, Hobgoblin 6, Goblin Lord 10), spawns `tier: a` / `b` / `c` | the same levels, a 3D model in MM7 |
| Slot 2 Witches (Wicked Witch 14) | Moon clerics (Acolyte of the Moon 10, in green robes) | robed women casters with a model; MM6-8 have no witch |
| Slot 3 Swamp Things (Giant Toad 11) | Bat family tier 3 (Inferno Bat 9) | no toad or frog exists; a witch's familiar that flies the shaft |
| Head Witch (Wicked Witch 14, boss hit points) | Cleric of the Moon (215, level 20) with `hp: 300` and a name | the game ignores `hp` (XD-01's gap) |
| Schoolmistress, the Head Witch's sisters | Acolytes of the Moon (214), placed | |
| Goblin Warden (Gremlin Guard 10) | Goblin Lord (273), placed, `immobile`, `carries` the ring | |
| The four children | Goblin peasants (439, 430, 433, 442), peaceful, `immobile`, one group each, inside the cages | no child model exists; half-turned children as goblins fits the story |
| Alacorn of Falista 12033 | Unicorn Horn (214) | an alicorn is a unicorn's horn; it shows as a horn on the pedestal |
| warden_ring 12032 | Ring of Keys (629) | |
| crystal_key 12031 | Key (2110), declared only | X1's door, not this map's |
| qbits 110040-110047 | kept | |
| music tower_dark | MM7 track 28 (the Temple of the Moon's) | the game refuses a name |
| X1, X8 | Emerald Island `7out01.odm` at XD-01's point | |

With a real Xeen world: `world: xeen`, the three slots and the placed rows to the Xeen families, items 12031-12033,
music by name, the neighbours to X1 and X8 with their arrival points, sounds. The textures stay (with the list above).

## What the brief asks, and how each thing was built

L3's crooked tower is kept room for room and coordinate for coordinate (each storey a quarter turn round the shaft):
ground floor south, second east, third north, fourth west, roof furthest west.

- **The shaft and the cauldron (set:shaft_view, landmark:cauldron).** One room 2048 across and 2688 high. The cauldron
  is an octagonal tub 768 across and 96 high (black sides, the green brew on top), with four stoking pots on their
  fires, four braziers, sacks, a cask, bowls; three hanging cages on chains from the roof beams. Green lights in the
  brew, on the walls and up the shaft's axis, the Witches' Finger (the west notch) climbing to the pier. From the rim
  the whole spiral is seen: the gallery's two arches south, the balcony rail east at 640, the broken balcony and its
  gap north at 1280, the sanctum's window and the bridge west at 1920 (pictures 06-08, 12, 25, 32).
- **The Alacorn on a bridge over the shaft** (the task's and L1's bridge; L3 had only the pier). From the pier on the
  Witches' Finger a plank walk 192 wide with low kerbs hangs 400 out over the shaft at 1920 to an octagonal landing over
  the middle of the cauldron; the Alacorn lies on a marble pedestal there, under its own white light (30, 31). Taking it
  sets `alacorn_taken` (a timer notices the item in the packs).
- **The boil-over (set:boil_over).** On taking it: a camera shake, the shaft and pier fill with pulsing green light,
  the steam scalds anyone on the pier, the bridge or the landing every two seconds for about a minute (step events note
  the party on them), the Alacorn's light goes out, and two Hobgoblins come up behind at the Rosebud landing.
- **Ground floor**: the gate hall with the tower door (7d12's carved door, the exit), the gallery under a pitched plank
  roof with four torches and the two arches, the warden's lodge (his table with candle and plates, his strongbox, cage
  1), the toad larder (a raised trough of green water, mushrooms, a cask, bats), the goblin pens (the trough, trash,
  bones, sacks, the densest goblins), the east stair's two flights and turn.
- **Second floor (the nursery)**: the balcony along the rail, the dormitory (six small beds with pillows, turned
  children, and **the loose panel**: a secret leaf in the wainscot that slides up on a cupboard with a cabinet, the
  goblin's hoard), the schoolroom (three bench rows, the slate on the east wall with its lesson as a message, the
  teacher's desk and two candlesticks, the schoolmistress, cage 2), the skull niche (three talking skulls on a shelf
  before the bookcase wall), the west stair. The second floor is a ring: landing, dormitory, the mistress's door,
  schoolroom, the double door, balcony.
- **Third floor (the brewery)**: the vat hall under a pitched roof (three vats on plinths over fires: the toad-lid
  barrel, the bubbling cauldron, the green barrel; its west wall all bookcase with **the secret bookcase door** to the
  hidden cage; a step in front of it makes the crying heard), the herb loft up six steps (the recipe card as a message,
  the witches' stores), the broken balcony with **the gap** (a 1280 fall to the cauldron floor, played), the long dark
  north stair.
- **Fourth floor (the coven)**: **the Rosebud door** (the Moon seal door, two leaves that part; it asks for the word:
  'Rosebud' opens it for good, any other word shows a line), the sanctum under a pitched roof (the witch-mark circle of
  the Moon seal with six candlesticks and a violet light, the altar with skull, goblet and a small cauldron, two carved
  posts, green-flame torches by the pier, the window over the shaft), the bedchamber (three beds, candlesticks, a
  hanging cage, cage 4, the coven's cabinet), the hoist room, **the ward** over the roof stair (a carved sigil slab that
  sinks for Crusaders), the roof stair, the hatch and **the roof** (a parapet, the chimney stack, the cloud-stair exit).
- **The hoist (link:hoist)**: a plank cage of posts and rails filling the slot, standing at the top. The brake lever
  sends it down (`hoist_released`); after that the cage is ridden by clicking it and called by a button at either door.
  A plank gate shuts the upper door while the cage is down and a second one the lower door while it is up (L4: nobody
  stands under it when it comes down). Pictures 34-36.
- **Cages and children (poi:cages)**: four bone cages, a child in each. The warden's ring opens them: children 2-4
  vanish home (500 experience, their bit); child 2 whispers the word in a message window and sets `rosebud_heard`;
  child 1 steps out but stays until the cage is clicked again with the Alacorn in the packs (set:cure_the_boy).
- **The vats (set:vats)**: the toad-lid vat gives +2 to a stat drawn at random, once per character (player bit 11041);
  the bubbling one poisons, the green one makes the drinker Weak. **The talking skulls** each sell a scroll (Mind Blast,
  Heal, Sparks) for one gem of any kind, after a question.
- **The Head Witch (set:head_witch)**: at the window with her two sisters and a guard of Goblin Lords; her two
  familiars come out of the floor when her sisters have fallen or the party treads on the circle; her death sets
  `head_witch_slain`.

Objects and wiring: 14 doors (25 door records with the second leaves, the hoist and the switches), 48 events, 4 chests,
24 spawn points (21 monster, 3 item), 11 placed monsters, 44 lights (9 pulsing), 110 decorations, 7 placeholders.
Every mechanism is a preset with conditions and effects; Lua only for the cages' branches and experience, the vats'
per-character bits and random stat, the skulls' payment, and the camera shake.

## Interactive things, as the player meets them (REBUILD_PROCEDURE "What the measure does not see", "Can a player read it?")

Every kind was looked at in the game before and after use (`things3/` from `things_shots.py`, and pictures 03/04,
13/14, 17/18, 22/23, 27/28, 34-36, 37/38):

| Kind | The family's form | Built |
|---|---|---|
| Tower doors | 7d12's doors are two plank leaves (`7trimd`) that fold into the jambs | `slide_left, leaves: 2, fold: true` with `7trimd` at its own size: warden, larder, pens, dormitory, mistress's door, schoolroom (one 256 doorway) |
| Coven doors | 7d06's plain door is a stone slab (`twb1`) folding up into the lintel | bedchamber and hatch so |
| The Rosebud door | 7d06's seal door: two leaves parting sideways, the four seal quarters | so; the question on it |
| Secret doors | 7d12's wall slabs that rise | the bookcase (`7t1books`, the wall's own picture) and the loose panel (`hwm1b`, the wainscot's) rise, secret-flagged (they pulse red for a party that spots secrets) |
| Chests | 7d12's chests are MM7's `7gt002`; both families have cabinets (`7t1cab`) | warden and loft `kind: 7gt002` (hover "Chest"); the coven's chest and the hoard are cabinets of `7t1cab` at their own size (hover "Cabinet") |
| Buttons | 7d12 and 7d06 use MM7's `7t1butt`/`7t1butts` | the two call buttons `kind: button` with those |
| Lever | 7d12 has none of the Forge's kind; a dark wood post and arm | `kind: lever`, post `trim11_32`, arm `trim9_32` (both 7d12's) |
| Plates | none visible | the crying plate wears the floor |
| Exits | | the tower door is 7d12's carved door `hwm2d` at its own size (128 x 256), on a panel of the same picture so it lies on one face; the cloud stair a 512 sky panel |

The user's checks: every chest looks like a chest or is a cabinet that says "Cabinet"; nothing else looks like a chest
(the tables, desk and beds are low furniture; the winch drum, a dark block, has the hover "Winch drum" and a line);
every clicked thing has a hover name (Cage, Talking skull, the vats, The slate, A recipe card, Hoist brake, Call the
hoist, The sleeping face, A shimmering ward ...) and a reason to click (a child in each cage, skulls that the niche
shows, a card on the wall, a slate before the benches); the slate, the recipe card, child 2's whisper and the skulls'
offers open message windows; no prop floats (candles, plates, skulls and goblets stand on their table, shelf or altar by
`floor_height`; the hanging cages hang from the roof beams on their chains, the shaft's at 2400-2440 under 2688, the
bedchamber's under its ridge); no picture is stretched (doors at their own size, the seal and the circle at a uniform
1.25, the card at a uniform 0.5, the cabinets 128 x 256 as their picture); doors, buttons and the lever come from the
two families. Not recognisable enough: the slate (a dark stone panel) and the winch (a block): both textures/models to
make.

## Scale against the bands

`oymap metrics <L4> --reach` (`metrics.json`); bands from `devdocs/xeen/research/MAP_CRAFT_CALIBRATION.md` 3.1-3.3, 6.3.

| Figure | XD-04 L4 | Band / brief |
|---|---|---|
| Floor area | 38.8 M units² (walkable 32.6) | M 40-70; S 20-35; the brief 34.9 |
| Sectors | 33 | M 20-35; the brief 32 |
| Floor levels | 0, 320, 640, 960, 1280, 1472, 1920, 2560 (height range 2560) | 2-4 floors; MM7 height range 1,050-2,860 |
| Loops | the hoist ring, the second-floor ring, the two arches (metrics counts 6 sector loops: rails and windows are portals) | ≥ 1 for M; the brief 3 |
| Doors | 14 doors (16 door events) | M 8-16 doors, 5-14 door events |
| Monsters | about 50: 21 monster spawn points (13 goblin of 2-3, 2 witch of 1, 6 bat of 1-2) and 7 hostile placed; 1.5 per sector | M 35-65; the brief about 52 |
| Chests | 4 | 3-7; the brief 4 |
| Secret faces | 6 (two secret doors) | 1-6; the brief 2 doors |
| Plates, traps | 1 plate (crying); harmful: the cauldron and the boil-over's steam (2 trap events) | 1-15 plates |
| Boss | the Head Witch (named, hit points ignored) | 1 in 5 |
| Light sources | 75 (35 light records, 40 decoration lights; 9 pulsing lights not counted): 1.9 per M | 7d24 3.9, 6d18 2.9, XD-03 2.6 |
| Decorations | 110, 2.8 per M | the brief 110 |
| Doorways | median 256 x 320 | 256 x 256 |
| Sector height | median 640 (256 to 2688) | 464-592 mid rooms |
| Non-orthogonal rooms | 8 of 33 (shaft, cauldron, gate hall, lodge, dormitory, skull niche, vat hall, roof); 13 with stepped floors or pitched ceilings (8 pitched roofs added at L4) | ≥ 40 %, 25 % sloped: under on the first, met on the second |
| Main wall texture | `hwm2wall` 19 % of all area (walls about 30 %), two families | one texture 45-85 % (two families) |
| Clickable faces | 201 | 50-170: a little over (the hoist cage alone is 62 faces) |

### Room sizes (`scale_bands.py`, the user's finding on XD-01; `output/studio_cal/xd04/scale_bands.txt`)

L3's rooms gave the bigger rooms (upper quarter by floor area) 1.27 M units², at the shipped dungeons' 36th percentile
(median 1.64 M). Sized up at L4, each outward where nothing of another storey lies under or over it: the gate hall south
to 1.82 M (two more torches, a cask and sacks), the goblin pens south to 2.29 M, the toad larder south to 1.06 M, the
warden's lodge west and south to 1.67 M (cage 1 against its new west wall), the dormitory east to 1.95 M (its cupboard
moved with the wall). Now:

| Figure | XD-04 | Shipped p25 / median | Percentile |
|---|---|---|---|
| Bigger rooms (upper-quarter floor area) | 1.71 M | 1.06 / 1.64 M | 51 |
| Largest room | 4.35 M (the shaft) | 3.68 / 6.13 M | 35 |
| Typical ceiling | 640 | 394 / 521 | 74 |
| Taller rooms (upper-quarter height) | 704 | 522 / 570 | 62 |
| Typical doorway width | 256 | 256 / 256 | 9 |

The largest room stays under the median: it is the shaft, 2048 across and 2688 high, whose size fixes every storey round
it (widening it moves the whole crooked tower); the sanctum (3.66 M) and the vat hall (2.8 M) follow. Small on purpose:
the cupboard, the hidden cage, the hoist slot, the landings and the stair flights.

## Order of play (`oymap solve`, `solve.txt`)

```
step 0: 19 sectors  the ground floor, the shaft, the stairs, the balconies, the vat hall, the landings
step 1: 10 sectors  the plank doors (lodge, larder, pens, dormitory, schoolroom), the bookcase, the cupboard, the Rosebud door
step 2: 3 sectors   the hoist brake (event 6) and the calls; the ward needs qbit 110047 (m4_crusaders)
step 3: 1 sector    the roof hatch -> the roof
never reached: 0 sectors
```

That is the brief's critical path (gate hall, gallery, lodge, east stair, balcony, schoolroom, west stair, vat hall,
broken balcony, north stair, Rosebud door, sanctum, pier) and return path (sanctum, hoist room, slot, cauldron chamber,
gallery, gate hall). `solve` takes the Rosebud question as passable; it does not count the ring the warden carries
(XD-03's defect 2) nor the Alacorn lying on its pedestal (defect 1 below).

## Playtests

**Since the second pass** (175 and 77 steps): `playtest.yml` takes the player's route: the lodge's cue runs (its
once-variable), cage 1 refuses without the ring and its message names the table (asserted), the ring is picked up off
the table, cage 1 is hoisted (door record 26 open) and the boy's two lines are message windows; the schoolroom's cue
runs, the slate's message (with Rosebud's name) and Rosebud's message naming the herb loft's stores are asserted before
the door, the loft chest gives the coven's key, the face opens to it; the ward's and the hoist call's messages are
asserted. `playtest_m4.yml` meets the dead call button and the hoist gate (their messages), climbs to the face door
without key or Rosebud (its keyhole message asserted, the door stays shut), goes back down for the key and opens it.
The first-pass descriptions below are kept as the record.

`playtest.yml` (164 steps, the critical path and the way back): a level-9 party enters, kills the Goblin Warden behind
his folding door and takes the Ring of Keys from his corpse; cage 1 (the boy steps out, will not go, twice), the
strongbox (zircon, potion); the east stair; the dormitory door, the loose panel (rises) and the hoard (amber); the
mistress's door, the schoolmistress, the slate, cage 2 (both bits); the double door; the Body skull sells Heal for one
gem (one gem fewer); the west stair, the vat hall, the loft steps, the recipe card, the stores (two potions); the
toad-lid vat (works once, not twice); the crying at the bookcase (its once-variable), the bookcase rises, cage 3; the
broken balcony, the north stair; the face refuses a wrong word (door shut, variable 0) and opens for Rosebud; the
sanctum (sisters and Head Witch dead, the familiars appear, `head_witch_slain`); the ward hums shut; the bedchamber door,
cage 4, the cabinet (amethyst, citrine); over the bridge (on the pier noted), takes the Alacorn (`alacorn_taken`, the
steam scalds); back off the bridge (noted); the call button refuses before the brake; the brake sends the cage down and
moves both gates; the button calls it back; the party rides it down (z 0); out by the west arch; the Alacorn cures the
boy (`child_rescued_1`, the boy gone, the Alacorn kept); out by the tower door to the X1 stand-in with all seven bits.

`playtest_m4.yml` (58 steps, the second way): a level-10 party already Crusaders climbs to the broken balcony and drops
through the gap to the cauldron floor (asserted at z 0); the lower call button refuses while the brake holds; climbs
again, speaks 'rosebud' without child 2 (`rosebud_heard` asserted unset); the ward sinks for the Crusaders; the roof
stair, the hatch, the roof (its once-variable), the cloud stair to the X8 stand-in with `m4_crusaders`.

Nothing depends on chance: chests are checked only by their fixed items, the gem by a count, every walk clears hostiles
round it, every count is near its place. Four of four each.

## Departures from the brief

1. **The Alacorn on a bridge over the shaft** (L1's and the task's), not on the pier's tip (L3): a hanging plank walk
   and landing in the shaft room; the pier's tip is the bridge's mouth (L3: a 64 lip).
2. **Interactive things in the families' forms** (the rule): every "hinged" door of the brief is a folding plank pair
   (7d12) or a stone slab (7d06); the Rosebud door is the Moon seal, not a carved face; the ward a carved slab, not
   translucent.
3. **Textures**: two shipped families instead of the brief's picks from eight maps (table above).
4. **Pitched ceilings** over eight long rooms (gallery, pens, schoolroom, dormitory, vat hall, herb loft, sanctum,
   bedchamber): L3 had none because R3-K5 had no sloped ceilings; the studio has them now, and 7d12 roofs its rooms so.
5. **The secret cupboard is a closet** behind a secret leaf with a cabinet in it (no secret flag on a chest), a room of
   128 x 160 east of the dormitory.
6. **A lower hoist gate** besides the brief's upper one; a call button at each door (the brief's call switches).
7. **The Head Witch's familiars** come when her sisters fall or the party treads on the circle, not at half her health
   (no word); her sisters are placed monsters (group 6), not spawns.
8. **Children are Goblin peasants**, the familiars bats, the witches Moon clerics (stand-ins, above). A child's
   "running home" is the child vanishing (hidden); the boy cannot be seen to step out.
9. **Skulls sell for one gem** of any kind (the brief: 5 to 10): the chests hold five gems in all.
10. **The roof** is a room whose walls above a 112 parapet and whose ceiling wear the sky; the chimney a 448 block.
11. The cauldron is an octagon (L3: a 768 square turned 45 degrees), with black sides.
12. **No password (second pass, the user's decision of 2026-11-13: "MM6-MM8 had almost no riddles ... it should be
    more like combat + mechanisms + loot").** The brief's Rosebud password (L1 `condition: {password: rosebud}`, child
    2 whispering the word, the half-rubbed slate) is replaced by a key: the coven's key in the witches' stores in the
    herb loft opens the face door; child 2 (Rosebud) tells where it is; the slate carries her name as flavour. The
    brief's jinx on a wrong word goes with it (gap 2 is moot).
13. **The cage ring lies on the warden's table** (second pass), not on his corpse; the cages are cages of bars built in
    the map that are hoisted up their chains when opened, not the bone cage decoration (which has a skeleton in it).

## Gaps (what I wanted to say and could not), most harmful first

1. **A room open to the sky** (the roof, the vista over Toad Meadow, the cloud stair climbing above): painted walls and a
   painted ceiling. `rooms[].sky: true` (no ceiling, the outdoor sky drawn), or a vista backdrop.
2. **A wrong answer that does something** (the Rosebud jinx: a curse until rest): `question.wrong_effects`.
3. **A condition on a monster's health** (the Head Witch at half health): XD-03's gap 1, unchanged.
4. **A placed monster's hit points and name reach the game** (XD-01/03, unchanged): the Head Witch has 100.
5. **A monster that walks out of a cage** (the boy steps out and waits): `effects: {move_actor: {group, to}}`; the
   cages cannot open either (a decoration cannot be changed by an event: XD-03's gap 4).
6. **Using an item on a monster** (the Alacorn on the boy): the cage is clicked again instead; `monsters[].event`.
7. **Indoor fog or steam** for the shaft and the boil-over (`atmosphere.yml` fog for a BLV room).
8. **Placed sounds in an MM7 project** (bubbling, winch, dripping, crying, wind): refused (XD-03's defect 3); the crying
   is a status line on a plate.
9. **Per-character state** (the vat): Lua player bits (XD-02's gap 3, unchanged).
10. **An exit on a mover or an effect** (XD-03's gap 8): the cloud stair is a sky panel on a wall.
11. **A summon of slot monsters that walk up from below** (the goblins coming up the stairs): they appear at the landing.

## Tool defects (repros under `output/studio_cal/xd04/repro/`)

1. **`solve` does not count an item lying in the map** (`objects.yml items`): "item 2110 ... is not given or held in a
   chest on this map: it comes from elsewhere" for a key on the floor beside its door. Repro `repro/solve_floor_item/`
   (`project/`, `solve.txt`, `result.txt`). Here the Alacorn; the warden's ring is XD-03's `carries` defect, unchanged.
2. **`things` puts a cabinet's stand point outside the map**: `chest:hoard` (128 x 16 x 256 against its closet's east
   wall) is "used from [4512, 416]", 160 behind the wall, and `things_shots.py` takes its picture from inside the wall.
   Repro `repro/things_stand_point/things.txt`.
3. **Playtest harness**: `mapvar(name)` reads only named map variables, so a project's numbered variable that changes
   (the boil counter) cannot be read in `play_lua`, only asserted at an exact value; a light assertion on a pulsing light
   reads `unset` (XD-03); a tour's console `lua evt.SetLight(40001, 1)` on a pulsing light changed nothing visible.
4. **`oymap build --out` writes `ids.lock.yml` into the project** (known).
5. Minor: `oymap assets dec02` lists `7dec02` (a campfire) first for the brief's tall candlestick `dec02`; a name match
   that is not exact should come after the exact one. Python's YAML reads the objects' key `on` as a boolean (a reader
   of the files by script should know).

Found in the second pass (ninth-merge `oymap`):

6. **`audit` flags a decoration that hangs from a beam as floating** (`thing.floating` for the four braziers): the
   build accepts them with `hangs: true` (their chains reach the crossbeam), but the audit reads the built map, which
   does not carry `hangs`, and looks only under the thing. `oymap audit devdocs/xeen/briefs/xd04/L4 --assets
   output/studio_play/xeen_root`.
7. **`oymap things` lists no "changes" for a script preset's `opens`** (the four cages, events 7-10, hoist their movers
   26-29, which the playtests see), and `things_shots.py` runs a locked event without its item, so a locked thing's
   "used" picture shows nothing happening (`pass2/things9b/contact.png`, the cages). It also stands a room step
   event's camera behind a wall (the schoolroom cue's pictures show the slate from behind, mirrored).
8. **Playtest harness:** `status()` does not keep a step event's line through a walk (the lodge's cue ran, its
   once-variable is set, `status()` came back empty); the playtests assert the cue's once-variable instead.
9. Minor: `chests[].end_surface` refuses `uneven` (the squashed-picture warning names `uneven: true` as the way to
   say it is meant); a hanging decoration placed exactly on a pitched roof's ridge line is measured against the
   room's lower ceiling (the bedchamber's cage, moved 28 off the ridge).

## What in the brief was unclear

- "The cauldron ... a ledge, not stepped onto; harmful to anyone who climbs or falls in": only a fall from the bridge
  reaches it; built as a step event on its top.
- The hoist "starts at the top, held by the brake": with the cage up, the lower slot is open under it; a lower gate
  was added.
- L3's mechanisms say "hinged" doors everywhere; the rule says the family's form, which here slides.
- "Goblins left alive below come up the stairs": no word walks them; two are summoned at the landing.

## Pictures

Best: `shots/27-rosebud-door-shut.png` with `28-rosebud-door-open.png` (the Moon seal in green light, parted on the
sanctum), `shots/07-shaft-up-from-the-cauldron-rim.png` (the whole spiral of storeys, rails, window and bridge up the
green shaft), `shots/29-sanctum-witch-mark-circle.png` (the circle, candles, altar and ram-skull walls under the pitched
roof), `shots/31-bridge-the-alacorn.png` (the horn on its pedestal over the drop), `shots/23-bookcase-open-cage-3.png`
(the risen bookcase on a caged child). Also good: `14-dormitory-loose-panel-open.png`, `19-talking-skulls.png`,
`12-balcony-over-the-shaft.png`, `34`/`35` (the hoist gate).
Weakest: `shots/40-roof-and-cloud-stair.png` (a room with sky painted on its walls and a stone block: not a roof
terrace under the sky; gap 1) and `shots/11-east-stair-turn.png` / `20-west-stair.png` (plain rubble shafts; the
stairs are honest but dull).

Fixed after looking (`look1`-`look3`, `things1`): flat bright rooms (base darkness raised to 18-28 by floor); a dark
shaft (green light on the walls, darkness 12); the bookcase drawn only in the frieze band (a whole-wall panel); the
skulls on the floor (a shelf); furniture in a pink plaster-like wood (`7t1books1`); beds as blank slabs (pillows); the
roof's walls of rubble 2048 high (a parapet under the sky); a chimney pillar to the ceiling (a stack); stretched pictures
(the front door, the cabinets, the card, the cloud stair at their own size); hanging cages in mid-air (hung from the
beams); exit faces over two wall faces (panels behind them); balcony pictures blocked by the rail's sill.

## Judgement

As a dungeon it has what the brief promises, and all of it works and is played: you come in at the bottom of a
green-lit shaft and see the goal at once, high on its bridge; the tower is climbed floor by floor round it, each floor
its own place (stone and timber below, the wooden nursery with its beds, slate and talking skulls, the brewery with its
vats and books, the Moon temple on top), and each floor shows the shaft again from a quarter turn further round. The
plan to make is real: the warden's ring opens the cages, a child gives the word, the face asks for it, the Alacorn is
taken on a bridge over the drop while the cauldron boils over, the hoist is the quick way down, and the boy at the bottom
wants the Alacorn before he goes home. The second way (the drop through the broken rail, the ward that falls only for
Crusaders, the roof) is there too.

Its weaknesses: the witch theme leans on stand-ins (Moon clerics, bats for toads, goblin peasants for children with a
billhook through the bars); the Head Witch is an ordinary 100-hit-point cleric whose second phase is her familiars
crawling out; there is no sound and no steam; the boil-over is light and damage, not a column of steam; the roof is a
painted room; the stairs and the gate hall are plain; the cauldron reads as a green pool with a black rim rather than a
cauldron. A player would enjoy the shaft, the seal door, the bookcase and the bridge; the boss and the roof want game-side
words (health conditions, an open sky) and a few textures and models before they are the climax and vista the brief
asks for.

## Exits to Vertigo (2026-11-13)

`exit:toad_meadow` (the tower door, evt:exit_door 25) now leads to X1 (`xeen_x1.odm`): arrival [12288, -11619, 864],
facing 270 (south), in Toad Meadow in front of X1's tower door (`thing:witch_tower_door`, face at y -11219), facing
away from it. Unchanged: `exit:cloudreach` still goes to Emerald Island (X8). `playtest.yml` checks map and position
on X1 after the door and walks off south.

Backup before the change: `output/studio_cal/xd04/exits_backup/`. Build `output/studio_cal/xd04/exits_build/` (against
`output/studio_play/xeen_root`); only the exit's `evt.MoveToMap` line changed in the built Lua (the .blv and scene are
byte-equal to the build of the backup). Installed in `xeen_root`. Arrival points were read from X1's build
(`output/studio_cal/x1/build/export.json`: the doorway models' faces; ground from its height map), 400 units in front of
the door face, clear of the doorway model, on open ground; the playtest walks off from there. Pictures of every arrival,
facing out and turned back to the door: `output/studio_cal/x1/exits_pics/sheet.jpg`. On first arrival on X1 from a
dungeon Mayor Gunther's errand window opens (X1's one-shot timer), as on a new game there.

## X1 pass five: the tower door moved (2026-11-14)

X1's Witch Tower door now stands on the tower's north side (face y -9387). `exit:toad_meadow` arrives at
[12288, -8987, 850], 400 north of it, `direction: 90`; `playtest.yml` asserts that and walks off north. Rebuilt
(`--out output/studio_cal/xd04/build`), installed in `output/studio_play/xeen_root`; both playtests four of four
there (`output/studio_cal/xd04/run/p5_four.out`). Backup: `output/studio_cal/xd04/pass5_backup/`.
