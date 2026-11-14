# XD-03 Deep Mine, L4: notes

A new dungeon built from the written brief (L1 to L3 here, `devdocs/xeen/MAPS.md` row XD-03, QUESTS.md Story M3,
MONSTERS_AND_ITEMS.md) with the Map Studio, by one agent, 2026-11-13, after XD-01's two passes and XD-02. No original
exists; shipped maps were measured and looked at for scale, light and texture families only (below).

State after the second pass (below; its figures replace the first pass's where they differ): `oymap validate` no
issues, `fmt --check` clean, `audit` clean (no faces in one plane), playtests 179 and 46 steps four of four, installed
in `output/studio_play/xeen_root`. First pass: `oymap validate` no issues, `fmt --check` clean. The build's warnings are the two placed monsters' names
(`Clan King`, `Gong Sentry`, gap 6) and the four placeholders (racks, gong model, cart model). 24 rooms, 24 sectors,
all reached on foot (`metrics --reach`: 24 of 24 with the doors open). Two playtests (175 and 46 steps) pass four runs
of four (`output/studio_cal/xd03/run/four.out`, logs `final_playtest_1..4.log`, `final_playtest_alarm_1..4.log`).

Scratch: `output/studio_cal/xd03/` (`go.sh` builds, installs into `mount/` and plays one test; `four.sh` the four runs
of both; `look.sh <tour>` builds, installs into the scratch root `root/` and takes a tour; `tour.yml` the pictures;
`ref/` the shipped maps looked at; `repro/`; `look1`-`look3`, `shots_take1`, `shots_take2` the earlier takes;
`tex/` texture sheets; `metrics.json`, `solve.txt`). Pictures: `output/studio_cal/xd03/shots/` (35 in the game, HUD off,
`captions.yml`, `plan.png`, `iso.png`).

**What was scripted.** The first shell, objects and wiring were written by two generators in my scratch folder,
`output/studio_cal/xd03/tools/gen_rooms.py` and `gen_objects.py` (the dome rings, the slag channel's lines, the gem
clusters, the cart's and cage's parts are computed), changed by the small `edit*.py` steps beside them and rerun after
each change; `regen.sh` runs them, `fmt` and `validate`. No hand edit has been made to rooms.yml, objects.yml or
wiring.yml that a rerun would lose; plan.yml, project.yml and the playtests are hand-written. Once the project is
edited by hand the generators must not be rerun.

## Second pass: the user's lessons (2026-11-13)

The user has not played this map; this pass applies what he found in XD-01 and XD-04 (REBUILD_PROCEDURE.md: room
sizes, can a player read it, no riddles, puzzles a player can solve, no silent clicks, nothing in its stand-in) and the
ninth merge's checks, and answers the lead's request to remove every pair of faces in one plane. The project before it
is `output/studio_cal/xd03/pass2_backup/`; scratch in `output/studio_cal/xd03/pass2/` (`go.sh` validates and builds
against the play root's assets and installs into `root/`, a hard-link copy of `output/studio_play/xeen_root`;
`root_before/` is the play root as it stood; `test.sh` runs both playtests; `tour.sh` a picture tour).

**Scripted** (each kept there, each diff read; not to be rerun): `edit_p2.py` (rooms, doors, levers, chests, the gong,
piers, pilasters, monsters, wiring), `fix1_p2.py` to `fix5_p2.py` (after validate, after the build's warnings, after
the first look in the game, the cart) and `fix6_p2.py` (torches that hung in doorways, the statues' line; then by
hand the warren's rock that stood on the walk to the prospector, `fix6_p2.py.note`). `level_generation/update_gitignore.py`
run after the new texture.
The generators of the first pass (`tools/gen_*.py`) are retired: the files are the source now.

### Room sizes (`scale_bands.py`, measured on the private root: see tool defect 4 below)

| Figure | Before | After | Shipped p25 / median |
|---|---|---|---|
| Bigger rooms: upper-quarter room floor area | 0.76 M (11th percentile, below p25) | **1.69 M (51st)** | 1.06 M / 1.64 M |
| Largest room | 7.35 M | 7.51 M | 3.68 M / 6.13 M |
| Typical ceiling height | 640 | 640 | 394 / 521 |
| Taller rooms: upper-quarter height | 952 | 960 | 522 / 570 |
| Typical doorway width | 224 (5th, below p25) | **256 (9th)** | 256 / 256 |
| Floor area (`metrics`) | 24.9 M | 28.9 M (inside the S band, 20-35) | |

Per room (sector floor area with platform tops; `pass2/sectors_before.txt`, `sectors_after.txt`). The upper quarter is
the 7th largest of 24 sectors, so seven rooms had to reach the median:

| Room | Before | After | What changed |
|---|---|---|---|
| Furnace Hall | 7.35 M | 7.51 M | plan unchanged; pilasters, piers (below) |
| The Clan King's hall | 5.05 M | 5.07 M | unchanged in plan |
| Mole warren | 1.13 M, roof 400 over the floor | 2.25 M, roof about 550 | grown south, east and west (2944..5312 x -512..896), four rock cores (two new), a second dim light, more bones and spoil |
| Geode grotto | 1.42 M | 2.09 M | grown west to x -320 and north to 2624, crown 1024 over the floor; crystals, a stalagmite, a fifth glow and light in the new part |
| Deep landing | 1.65 M | 2.05 M | 256 longer to the south (1536 x 1152); a rock, a barrel, a light |
| Barracks | 2.00 M, 448 high | 2.01 M, **576 high** | ceiling and beams raised 128 |
| Geode lower terrace | 0.68 M | 1.69 M | grown south and east (128..1664 x -640..704), roof to 832, a crystal column, crystals, stalagmites, a second glow and light |
| Antechamber | 0.65 M | 0.86 M | 1280 wide at the hall, 768 at the gate (the gate's two leaves are now 256 each) |
| Lookout, cut, tower stair, descent, warren mouth, Deep Line head | | a little wider | 320 wide so their doorways are 256 |
| Hoard, vault, tower, armoury, alcove, back stair, shaft | | unchanged | small on purpose (the brief's closets and vaults) |

The plan and order are the brief's: the same rooms joined the same way; `oymap solve` opens it in the same six steps
(`pass2/solve_after.txt`), all 24 sectors reached; the critical path is unchanged.

### Each rule, and how it is met

- **Faces in one plane** (the lead: none): 32 pairs before, **0 after** (`audit` and the build). Causes: the trestle's
  and the cut's posts ran through their caps at the caps' own width (18 + 2 pairs; posts now end under caps a little
  wider than they are); the gallery's parapet stood with its outer faces in the gallery level's edges (2; now 8 inside
  it); the throne's plinth and the forge braziers' stands crossed each other (2; the stands moved apart); the cage's
  hanger bar ended in the top ring's sides (6; shortened to meet them); the gate's lower bar, lifted, met the leaves'
  tops (2; new gate and bar heights); and, found on the way, the lifted upper bar's top met the bar brackets' tops
  (brackets raised).
- **Levers as levers.** The three plates (`t1swdd`, MM6's red plate) are now `kind: lever`, the post and arm that sink
  when pulled, with Gharik's Forge's own arm `BemH16a` (the hold's family: 26 of the Forge's door records are such
  levers); 12 x 48 with a reach of 56 so they read across a room, above the brick's footing band (they lay over two
  wall faces). The two cage "bell-pulls" are levers too ("Cage lever"; the foot's on the shaft's west wall with a reach
  of 24, clear of the cage that passes 32 from the wall). Pictures `pass2/shots_after2/17-lever-alcove`,
  `41-lever-a-close`, `42-lever-b-close`, `43-shaft-lever`.
- **No silent clicks.** The levers had `once` and said nothing the second time: each now says so ("The lever is down;
  the King's Gate's lower bar stays up.") and its arm stays down (the bar stays up). The King's Gate before both bars
  are up opens a **message window**: "The King's Gate is barred from within: two iron bars lie across its leaves in
  their brackets. The clan lifts them with levers, one for each bar: one hangs in the barracks behind the bunks, the
  other in the furnace tower beyond the far bank." (also the clue to the levers). The hoard door without the key: a
  message window saying the Clan King carries its key. The cage, its levers and the shaft head's hatch say that the
  counterweight is chained and that its lever is in the hoard. The shaft lever's second pull says the cage runs free.
  `audit`'s remaining `click.silent` are the step events (bats, gutters, the sentry's step, the hum below) and the
  gem clusters after use (hidden and passable then: nothing left to click).
- **Puzzles a player can solve; no riddles.** No typed answer anywhere. The two levers: the gate's message says where
  they are, on the way (the gate is met before the tower and, by the playtest's route, after the barracks). The hoard
  key: the door's message says the King carries it; it is in his corpse. The secret crystal wall (optional): coming down
  the terrace steps the party hears it ("A faint hum, like a bell struck long ago, comes from the crystal in the west
  wall."), and it shows the crystal cavity picture, unlike the walls round it.
- **Every lootable thing reads as one; nothing that looks like a chest is not one.** The chests take the shipped
  families' kinds and the hover name **Chest** (they were "Weapon chest", "The King's chest", "Red Dwarf chest",
  "Prospector's pack": the build's check): the armoury's MM6 `ch2` (Gharik's Forge), the King's two `ch3` with the
  Forge's carved gold lid (`lid: v`), the Red Dwarf vault's `7gt002` (Stone City's), the prospector's pack, a
  stretched plank box, is now a small `7gt002` chest beside his bones. **The hoard reads as a hoard**: three heaps of
  gold coins (platforms tapering to their tops, the new generated `xncoins`), each clicked once ("Heap of gold": 150,
  100, 100 gold, then gone), two urns and plates beside the two chests. Gold-pile items were tried first and dropped:
  picked up they give no gold (tool defect 7).
- **Hover names and reasons to click.** Every clicked thing has one (`pass2/things_after.txt`: the six without are the
  step events: bats, cart, gutters, sentry, hum). The gong's eight slabs are all clicked (eight events, as a clicked
  event has one source); before only one slab of six rang.
- **Signs and long texts in message windows:** the lectern, the gate, the hoard door (the build makes a window of any
  clicked text over 65 characters).
- **Nothing floats or hangs from nothing.** The gong hung 64 under its frame's beam: two short chains now join them
  (`38-gong-close`); the beam ends on its posts. The bridges "rested on nothing": stone abutments under both ends and a
  pier under the south bridge's middle, standing in the slag (`48-bridges-piers`). The barracks' third torch hung in
  the lever alcove's open mouth (a wall decoration's `at` is not read when it has `wall`: tool defect 2); the gallery's
  two torches and the shaft head's lamp were inside their levels' blocks (tool defect 1): all now on their walls.
  `audit`: no `thing.floating`.
- **Torches in doorways** (found in the pictures of every thing): the barracks' east torch and the armoury's torch hung
  in the armoury's doorway, a gallery torch in the sentry doorway (each a wall's default middle): moved along their
  walls. The two "hacked statues" are 7d34's dwarf statue models, whose faces are whole: their line now says axe marks
  scar the plinth instead of a hacked face.
- **Nothing stands inside something else.** Three sleeping sergeants stood in their bunks, the King in his throne,
  the gate guards in their flambeaux, a crystal in a glow, the hall's bucket in the smelter's base: all moved.
- **No stretched pictures.** The doors now show whole pictures: the King's Gate is two leaves of 256 x 256 with
  `d2lgdor` (the Forge's skull door, as the Forge lays it once at 256 x 256; they were 208 x 384), the barracks' double
  door two leaves of the Forge's own slab door `cvdor1` at its 128 x 256 (the Forge's 26 door leaves are `cvdor1`;
  hinged leaves cannot tile, so `d2lgdor` could not be halved), the hoard's door `cvdor1`, the plank doors (sentry,
  armoury, tower) two halves of `bemvwal` at its size that fold to the jambs (256 wide), the back stair's one plank leaf
  128 x 256, the crystal wall 256 x 256. The King's hall's corner pilasters (`ctwl5le`) are laid at size, not stretched
  to 960. Small end faces (the furnace mouth, the crest, the gong slabs' rims) take pictures of their shape.
- **Doors and switches of the area's family:** the Forge's levers, slab doors, skull door and plank doors in the hold
  (above). The family texture rule holds: `xncoins` is the only new texture (generated, below).
- **Every named thing recognisable.** The gong: one `xngong` picture at scale 1.5 over eight slabs of 24, each showing
  its own window by `offset` (the six cut strips `xngong1`-`6` are no longer used), round, on two chains from the frame
  (`38-gong-close`). The throne, unchanged in form, with the King now standing in front of its seat. The hoard: heaps of
  gold. The cart: XD-02's riveted iron ore cart (`xnrustirn`) with sides 64 high, not a plank pallet
  (`02-cart-on-the-ledge`, `03-cart-riding-down`). The cage: unchanged (iron frame, hanger bar, chain).
- **The King** (known weak): the game ignores `hp`, so he is now the Dwarf family's top rank, the **Dwarven
  Commander** (231: level 30, 180 hit points, armour-breaking blows, never flees, a colour of his own among his
  Soldiers) instead of a 100-hit-point Lieutenant; `hp: 300` and his name stay for when the game reads them. Level 30
  is above the brief's 18: the nearest dwarf row with boss hit points (the Lieutenant has 100).
- **The furnace hall's large plain walls:** eight pilasters of dressed granite (`vlcwl3a`) 128 wide stand against the
  south, west and north walls up to the roof timbers, two of which now rest on them; three more wall torches between
  them (`39-hall-south-wall`, `40-hall-west-wall`, `53-hall-from-ante-opening`).
- **The dome** is `xnquartz` (checked: `24-dome`, blue quartz in four rings, the cavity at its crown).
- **Sound** (known weak): the gong now booms (`evt.PlaySound` of MM6's `6gong` at the gong, from the party's click and
  the sentry's ring) and the crystal wall chimes as it sinks. The ambient sounds (slag bubbling, the wind in the shaft)
  still wait: placed sounds of an MM7 project are refused for want of the world's own audio files (gap 7).

### Playtests

On the final build in the private root (`pass2/run/final/result.out`, build `pass2/build3/`): `playtest.yml` (179 steps) **four runs of
four**, `playtest_alarm.yml` (46 steps) **four of four**. New in the walk: the barred gate's message window, lever A's
second pull (says so, bar stays up), the gong rung from another slab (event 50), a heap of gold (150 gold, once); the
barracks' doorway coordinates. Then installed into `output/studio_play/xeen_root` (map, scene, Lua and `map_stats.txt`
byte-identical to the tested root, with `xncoins`) and both played once more there (`pass2/run/playroot/`, passed).
Event numbers are the project's `ids.lock.yml` (copied back from the build: `build
--out` does not write it, and new events took numbers between builds until it was).

### Pictures

Before (the play root as it stood): `pass2/shots_before/` (37), `pass2/things_before/contact.png`. After:
`pass2/shots_after2/` (the same 37 cameras and 16 more), `pass2/things_final/contact.png` (every interactive thing
before and after use). Best pairs: `07-gallery-overlook` and `08-gong` / `38-gong-close`, `30-hoard` / `51-hoard-heaps`,
`17-lever-alcove` / `41-lever-a-close`, `20-antechamber-barred` and `22-gate-opens-on-the-throne`, `02-cart-on-the-ledge`.

### Generated texture

| Name | What | Size | Family | Where |
|---|---|---|---|---|
| `xncoins` | A heap of worn gold coins, some stamped with a hammer (tiles) | 128 x 128 | MM6 Forge chest gold (`ch3tpbv`), MM7 `c1gold` | the hoard's three heaps |

Made by `level_generation/textures_xeen/xtex.py` (spec added to `specs.yml`; check `sheets/check_xncoins.png`),
installed in `output/studio_play/xeen_root` and the pass's root.

### Tool defects found in this pass

1. **A wall decoration's `floor_height` is not read**: its height counts from the room's floor, so the gallery's
   torches (gallery 384 up) and the shaft head's lamp (1536 up) were built inside the levels' solid blocks
   (`[5108, 2799, -336]`); the build said "stands inside LEVEL". Worked round with heights from the room's floor.
2. **A wall decoration's `at` is ignored when `wall` is given**: it goes to `along` 0.5; the barracks' third torch hung
   in the alcove's open mouth and both gallery torches stood at one point. `along` used.
3. The squashed-picture warning suggests `uneven: true`, which the schema refuses (unknown key); a platform's
   `end_surface` is stretched whatever `fit` says, so small end faces need a picture of their own proportions.
4. **`scale_bands.py` (`oymap metrics <file> --assets <root>`) reads the map of that name from the root**, not the file
   given: the new build measured 0.76 M against the play root until measured against the private root it was in.
5. `build --out` leaves `ids.lock.yml` in the build folder: new events' numbers moved between builds until the lock was
   copied back (documented, but a trap for playtests that click by number).
6. Hinged leaves cannot `tile` (no two halves of one picture on a double door); `sources` only for step events (a
   thing of several blocks clicked as one needs an event per block).
7. A gold-pile item placed with `items` (1001, "A large pile of gold coins") gives 0 gold when picked up.

### What waits on the studio and the game

- **The King's own hit points, level and frenzy, and his name while alive** (gaps 3 and 6): the Commander is a
  stand-in; `immobile` cannot be lifted by an event, so he still fights from the dais.
- **Ambient sound** for an MM7 project (gap 7).
- **Weapons on the armoury's racks** (no decoration; the placeholders stay) and **models** for the gong and the cart.
- The decorations above are placed by working round defects 1 and 2: rebuild after they are fixed.

### What looks worse

- The bigger warren, grotto and lower terrace keep about the same number of lights: their far corners are dark
  (`46-warren-wide`, `45-lower-terrace-south`).
- The barracks' double door is grey stone slabs (the Forge's door) where it was the red skull door; the skull door
  stays on the King's Gate alone.
- The levers are the Forge's thin handles: correct for the family, small next to the old red plates.

## Shipped maps looked at first

`output/studio_cal/xd03/ref/`: MM7's Stone City `7d24` (the dwarves' city: plan, iso, metrics, 7 game pictures) and
MM6's Gharik's Forge `6d18` (lava forge: plan, iso, metrics, 7 pictures), plus the metrics of Snergle's Caverns `6d05`
(a dwarf king's caverns). What they taught, nothing of theirs copied:

- `7d24`: an octagonal great hall with dressed walls and timber frontages, dark floor, warm light high on the walls
  and a dark roof; tunnels of red rock between; 48.7 M units², 40 sectors, 3 loops, 3.86 light sources per M.
- `6d18`: the forge is one tall space over bright lava floors with dark rock and soot brick above; dressed tan halls
  (ctwl2/ctwl5, ctflor1) beside it; 56.6 M, 47 sectors, 2.93 light sources per M.
So: lava reads by its own light and should be the brightest thing in the hold; dark rock and soot above it; the dressed
stone of the King's own rooms warm and lit high; a hall wants its light in pools, not flat.

## Texture families (the lead's rule of 2026-11-13)

Every area takes its textures from one shipped map whose purpose fits; every texture was checked against
`output/studio_lead/blv_texture_use.json` (`output/studio_cal/xd03/tools/tex_report.py` lists each with the shipped
dungeons that use it; all 39 are used by at least one shipped dungeon, and by the family's own map):

| Area | Family (shipped map) | Textures |
|---|---|---|
| The mine: Deep Line head, landing, trestle, cart, sentry cut, lookout, breach, descent, escape shaft, the King's hoard, mole warren | MM7 `7d34` The Red Dwarf Mines (as XD-02, whose Deep Line this continues) | c2b, cfb1, c1gold (the hoard's gold-veined rock), tfb2, 7trimd, 7trimda, trim9_32a, trim11_32, ch004i (iron) |
| The clan's forge and hold: furnace hall, slag channel, bridges, gong gallery, back stair, barracks, lever alcove, armoury, furnace tower, antechamber, the King's hall | MM6 `6d18` Gharik's Forge | d2wlactr, vlcwl1lg, vlcwl1, vlcwl3a, vlcflorc, vlcflora, vlcflore, d2ceil1, d2ceil3, vlctrm3, ctwl5, ctwl5le, ctwl2, ctflor1, ctflor5, ctceil3, orfyrlga (the slag), vlcgnrc2, vlcgnrc3, bemh16a, bemv16a, bemvwal, d2lgdor |
| The geode grotto, its lower terrace, the crystal wall, the King's dome (the same geode, over the hall) | MM6 `6d05` Snergle's Caverns (a dwarf king's crystal caverns) | crstont, crdrf1, crflr3, d3ystlwl |
| The Red Dwarf vault (the old dwarves' work) | MM7 `7d24` Stone City | cwb, 7cdb, 7tfb1 |

Looked at as whole walls in the game (pictures in `shots/`): nothing shows a window, sign or emblem of another place.
Two stand-ins carry a motif chosen on purpose: the gong's face is `ctflor5` (gold scrollwork from the Forge's own
floor) and the throne's crest `ctceil3` (the Forge's red carved panel). The first take used textures from other
places (MM6 temple and hive crystal `orwtrlga` and `hvceila`, MM8 cave rock, an unshipped copper, rune and skull
texture); all were replaced. The geode's crystal-cavity panels (`d3ystlwl` on `crstont`) showed their brown frame as
pasted squares and were taken out; the cavity picture stays only on the singing crystal wall, where standing out is
the point.

Textures to generate (none shipped fits; the stand-in in use meanwhile):

| What it shows | Size | Where | Stand-in |
|---|---|---|---|
| A cold blue quartz lining: dark rock thick with pale blue crystal points | 256 x 256, tiling | geode walls and crown, the King's dome | `crstont` (blue-grey layered rock) |
| The same crystal cavity as `d3ystlwl` but in blue-grey rock (no brown border), for crystal faces in the geode walls | 256 x 256, single | geode wall panels, the singing wall | `d3ystlwl` on the door only |
| A bronze gong face: hammered bronze, a boss in the middle | 128 x 128 | the gong (six slabs) | `ctflor5` |
| The Mad Dwarf Clan's crest: a skull over an anvil, carved in red stone | 128 x 128 | the throne's crest | `ctceil3` |
| Glowing slag: dark cooled crust broken by orange-red seams | 256 x 256 | the channel and the gutters (brighter than the Forge's flat lava) | `orfyrlga` |

### Generated textures (2026-11-13)

The five above, made by Codex image generation with the families' shipped masters as references and installed in
`output/studio_play/xeen_root` only (sources, prompts, raw returns, checks: `level_generation/textures_xeen/`, its
README). Every texture is x4 art (master 4x the size below). The stand-ins are gone from the project.

| Name | What | Size | Family | Where used |
|---|---|---|---|---|
| `xnquartz` | Dark blue-grey rock thick with pale blue quartz points (tiles) | 256 x 256 | MM6 Snergle's Caverns `crstont` / `d3ystlwl` | every former `crstont` here: geode walls and crown (theme), the two crystal columns, the King's dome rings |
| `xnquartzcv` | Crystal cavity of blue and violet quartz in blue-grey rock, no brown | 256 x 256 | `d3ystlwl` on `crstont` | `door:crystal_wall`, the dome's cap |
| `xngong` | Hammered bronze gong: rings, a ring of dwarf runes, a polished boss | 128 x 128 | MM6 Gharik's Forge bronze and gold (`ctflor5`, `d2lgdor`) | the gong slabs' ends and tops (scale 1.5) |
| `xngong1`-`xngong6` | The gong picture cut into its six slabs' windows, top to bottom | 128 x 32 each | the same | the six gong slabs' faces (`fit`) |
| `xncrest` | Skull over an anvil with crossed hammers, carved in a red stone panel | 128 x 128 | Forge `ctceil3` | the throne's crest (`fit`, art at its 224 x 192 face) |
| `xnslag` | Dark cooled slag crust, its cracks glowing orange and yellow (tiles) | 256 x 256 | Forge `orfyrlga`, `vlcflorc`, `vlcwl1lg` | the slag channel, the furnace mouth, the gutters at the King's wrath (wiring `set_texture`) |

The gong is six slabs: one 192 x 192 picture needs each slab to show its own part. The studio build in use
(`openyamm-studio/build/oymap`) refuses a surface `offset` ("unknown key"), so `strips.py` cuts the one gong picture
into the six slabs' windows, each stretched once over its slab; in the game they meet as one disc with the boss in
the middle (`09-gong-close`). With `offset` in the build, one `xngong` at scale 1.5 with an offset per slab would do.

Pictures: `output/studio_cal/xd03/textures_gen/before/` and `after/` (same cameras; `pairs.jpg`): the geode and the
King's dome now read as blue crystal; the crystal wall is a blue-violet cavity in blue-grey rock (with the secret
pulse's red tint, as before); the gong a bronze disc; the crest the clan's skull and anvil; the slag dark crust with
glowing seams. The quartz repeats visibly on the widest geode walls (a 256 period of evenly spread clusters).

Playtests on the play root after the change: `playtest.yml` 4 of 4 (175 steps), `playtest_alarm.yml` 4 of 4
(`output/studio_cal/textures_gen_tests/four.out`).

## The world it is built in

As XD-01 and XD-02: `world: xeen` validates but render, solve and the game refuse it, so L4 says `world: mm7`.

| Brief | Built as | Why |
|---|---|---|
| Slot 1 Mad Dwarves (Mad Dwarf 7, Clan Sergeant 12) | MM7 Dwarf family, tier 1 (Dwarven Soldier 10) | XD-02's stand-in; the only hostile-looking dwarf with an MM7 model. MM7 makes Dwarves the party's ally: a load event makes the three rows hostile (gap 2) |
| Slot 2 Spiders (10 / 14) | Spider family, tier 3 (Venomous Spider 8, Widowmaker 12); the spawns say `tier: b` and `c` | the same family |
| Slot 3 Burrowers (Tiger Mole 9) | Troglodyte family, tier 1 (Troglodyte Drone 9) | a level-9 burrower with a model (XD-02 placed the same) |
| Clan Sergeants (placed) | Dwarven Soldiers (229) | the Lieutenant (20) is far over 12 |
| The Clan King (18, three times the hit points) | Dwarven Lieutenant (230, level 20) with `hp: 300`, `name`, `immobile`, `carries` the key | the nearest dwarf in level; the game ignores the `hp` (100/100 in picture 27) |
| Bat Queens (10) | Inferno Bats (207, level 9), placed `hidden` | the Bat family's top rank |
| clan_king_key 12021 | Key to Snergle's Chambers (2108) | a dwarf king's key by name |
| qbits 110030-110031 | kept | the game sets and reads both (playtest) |
| music `cave_deep` | MM7 track 18 | the game refuses a name |
| XD-02 and X1 | Emerald Island `7out01.odm` at XD-01's point | neither is mounted with this map |

With a real Xeen world: `world: xeen`; the slots to Mad Dwarf 7 / Spider 10 / Tiger Mole 9, the sergeants and the
King to their own rows (the load event that makes the clan hostile goes; the King's hit points and his frenzy come
from his row and the world's `modifiers.yml`), the bats to Bat Queen 10, the key to 12021, music by name, the cart's
exit to XD-02's Deep Line station (XD-02 L4 about [4600, 4450, -1216]) and XD-02's `exit:deep_mine` arrival to this
map's Deep Line head ([8192, 1088, 384], facing west), the shaft to X1's shaft head, sounds from the Xeen audio
folder. The textures are the shared MM6-MM8 library and stay (with the five above generated).

## What the brief asks, and how each thing was built

L3's plan and coordinates are kept wherever they worked (the caves, the vault, the tower, the antechamber, the
barracks and armoury, the hoard and the shaft stand where L3 drew them); the departures are listed below.

- **The arrival by mine cart (a real ride).** The Deep Line comes in high in the landing's east wall: the party
  starts in the Deep Line head (a short rock-cut stretch with its rails, two timber sets and a torch) facing the mouth.
  On the mouth's ledge (a level 384 up) the cart waits at the top of the line's last pitch, a timber trestle of three
  bents under two stringers and iron rails falling 384 west to the floor. **Stepping onto the cart sends it down with
  the party on it** (a mover travelling [-768, 0, -384], a step event on its top) to the buffer stop, a baulk of timber
  on a stone, with a lantern over it; stepping onto it again at the bottom rides it back up, and the Deep Line's east
  end is the exit back to XD-02 ("always works from this end"). The cart is a plank wagon of parts (bed, front and side
  boards, four iron wheels). Pictures 01-04.
- **Sentry cut.** One path room with heights at its points: north, a jog, the long run past the lookout niche, then
  west and down 128 to the gallery door; three timber sets of dark posts and caps; torches in the niche and at the
  ramp's head. Pictures 05, 06.
- **The Furnace Hall** is one room now (L3: seven). 2560 x 2240, a rough rock roof 832 to 1216 over the floor on two
  soot-black timbers; dressed granite footing and soot brick to 448, raw dark volcanic rock above. The **slag channel**
  is a sunken level 128 deep and 384 wide at 45 degrees, its floor the Forge's lava (`floors: lava`: it burns), its
  sides glowing seamed rock. The **north span** (a slab 270 wide at the far bank, 611 at the near) covers its head; the
  **south bridge** (192 wide) crosses near its foot; both are hanging slabs flush with the banks, with a low iron kerb
  and no rail. The **slag steps** (four steps of 32, 352 wide) climb out of the main reach beside the south bridge; the
  **drain steps** (four, 224 wide) climb out of the south reach by the breach. The **ruined smelter** is an octagonal
  stack from floor to roof on a stone furnace base, its glowing mouth on the north face under an iron lintel; spoil
  heaps, buckets, slag lumps; four flambeaux with their own flickering light; six slag lights low over the channel
  pulsing out of step. Pictures 07, 10-14.
- **The gong gallery** is a balcony inside the hall, 384 up along its east wall behind a stone parapet (L3: a room
  beside the hall with two windows): its stair of twelve steps with side walls along the east wall at its south end,
  the gong at its north end, the sentry door from the cut in the middle, the back-stair head beside it. **The gong** is
  a round disc of six bronze slabs in a timber frame on a plinth (clicked). Picture 08.
- **The gong alarm (set:gong_alarm).** Coming onto the gallery marks the party as seen; a timer counts every two
  seconds while the sentry lives and the alarm is quiet, and at the third count (about six seconds) the sentry rings
  the gong. Killing him first keeps the barracks shut; the party can ring the gong itself. Either way the barracks'
  double door and the back-stair door fly open, the barracks' three torches light (switched lights over unlit torch
  models), a small camera shake (Lua). Both paths are played (`playtest_alarm.yml` lets the sentry ring).
- **Barracks**: plank ceiling on three beams, three bunk benches, a trestle table with benches, bowls and a goblet,
  barrels, unlit torches; five placed sergeants and dwarves asleep in the dark behind the doors; the lever alcove in
  the north wall (lever A, a torch). **Armoury** one step up through a plank door, its east wall folded into two bays
  with two weapon racks (rails on posts; the weapons are a placeholder), the clan's chest, an axe by the rack, a cask
  and a barrel. Pictures 15-18.
- **The King's Gate (set:kings_gate).** Two skull-studded leaves side by side with a mullion, each a hinged door; two
  iron bars across both (movers): lever A lifts the lower, lever B (in the furnace tower) the upper, each with a clank
  and visible from the antechamber; clicking the gate before both are up says "The gate is barred from within." and
  stays shut. The antechamber: a wedge under a pointed vault, the two hacked statues (clicked: "The clan has hacked his
  face away."), two flambeaux, two gate guards at their posts. Pictures 20-22.
- **Furnace tower**: L3's octagon with its roof drawing in to a sooty flue, a hearth of heat-cracked stone round the
  cold crucible (a cauldron with a slow red glow), two sconces, lever B on the west wall; stair of eight steps and a
  door. Picture 19.
- **The Clan King's hall.** L3's six-sided coffin shape widened to take its gutters, 2688 x 1792, 960 high: dressed
  tan blocks over a dark granite footing, a frieze of carved rune stone, carved pilasters in all six corners, four squat
  dressed pillars in a ring; a **dome of geode rock** in four rings rising to 1664 over the floor with the crystal
  cavity at its crown and a pale pulsing light in it; **the stepped dais** (six steps 1024 wide of granite risers and
  red inlay treads) to the throne floor along the north wall; **the anvil throne** (an anvil block that flares, on a
  plinth, with a high back and the clan's crest); the two forge braziers either side on stands, a skull pile and
  goblets; the hoard door behind it; six braziers round the walls; **two gutters** 32 deep along the east and west
  walls. Pictures 23-29.
- **The Clan King (set:clan_king).** Phase one: he stands on the throne floor (`immobile`) while his guard of four
  holds the foot of the dais. Phase two, when his guard has fallen (the brief: at half his health, gap 1): the forge
  braziers' fire lights go dark, a red light fills the hall, the gutters' beds turn to slag (`set_texture` on two
  platforms lying in the gutters) and burn whoever stands in them (step events that note the party in a gutter and a
  one-second timer that burns while the wrath holds, since a floor's lava flag cannot be set by an event), a camera
  shake. His death sets `clan_king_slain`; his key is in his corpse (`carries`).
- **The King's hoard**: gold-veined rock, a lantern, two trapped chests (450 gold, a ruby and three rolls of level 4;
  350 gold and four rolls), goblets, a fruit bowl; the shaft lever on its back wall beside the shaft. Picture 30.
- **The escape shaft (one way out until its lever is thrown).** A shaft 512 square going up 1856 beside a rock block
  whose top is the shaft head's landing (a level 1536 up), with the exit to the X1 hills on its east wall. **The
  counterweight cage is a mover that carries the party** up 1536 in ten seconds (iron frame, posts, a hanger bar and
  its chain as parts). Before the shaft lever the cage refuses ("its counterweight is chained fast") and so does the
  exit; the lever sets `escape_shaft_open`. Bell-pulls at the foot and at the head call the cage. Pictures 31, 32.
- **Geode grotto**: L3's breach, descent, upper terrace, steps and lower terrace; walls, crown and two columns of
  cold blue-grey crystal rock with rough walls and a roof rising to a crown 960 over the floor, a floor of dark crystal
  gravel, glowing crystals and crystal clusters (decorations) with slow blue pulsing lights, stalagmites, a skeleton
  and bones. **The bat queens hang hidden** in the crown and appear (`show_actors`) when the party steps onto the
  descent. **Four gem clusters** are tapering crystal points (platforms with ids): clicking one gives one low gem (zircon,
  iolite, citrine or amber) once, and its points are hidden and made passable. **The singing crystal wall** in the lower
  terrace's west wall is a secret door (`secret: true`) showing a crystal cavity; clicking it hums and sinks it.
  Pictures 33, 35.
- **Red Dwarf vault**: an octagon of Stone City's dressed stone over a footing of old blocks under a low dome, the
  memory crystal over a ring in the floor (a platform), the stone lectern (clicked: the mine's history as a message,
  noted in a map variable), the chest (amber, iolite, 150 gold, two rolls). Picture 36.
- **Mole warren**: the burrow mouth ramp and L3's knot of burrows round two rock cores, now with an uneven floor and a
  low uneven roof and rough walls, dark; tiger moles (two slot-3 spawns), the prospector's skeleton and bones, his pack
  (a chest: a potion, 100 gold, a roll) and a potion beside him. Picture 37.

Objects and wiring (every mechanism a preset with conditions and effects; Lua only for the clan's hostility on load
and the camera shakes):

| Brief | Built |
|---|---|
| Arrival and the cart back | `start` in the Deep Line head; `mover:deep_cart` with a step event (`toggles`); `exit:deep_cart` on the line's east end |
| Gong alarm | `evt:sentry_seen` (step on the gallery level), `evt:sentry_count` / `evt:sentry_rings` (timers, `kills` and `map_var` counts), `evt:gong` (the gong platform, `not alarm_rung`, `else_effects`) |
| King's Gate | `evt:lever_a` / `evt:lever_b` (switch, once, `opens` a bar, `sets`), `evt:gate_e` / `evt:gate_w` (door, `condition: all`, `action: open`, opens the other leaf) |
| Clan King | `evt:kings_wrath` (timer, once, `kills: group 4` and not the King), `evt:gutter_in` / `evt:gutter_out` (steps), `evt:gutter_burn` (timer), `evt:king_dead` (timer, once, `kills: monster`, qbit) |
| Hoard and shaft | `evt:door_hoard` (item, kept), `evt:shaft_lever` (switch, once, qbit), `evt:cage` / `evt:cage_call` / `evt:cage_call_top` (qbit), `evt:exit_x1` (qbit) |
| Geode | `evt:bats_drop` (step, once, `show_actors`), `evt:cluster_1..4` (script, once, `give_item one_of`, `hide`, `passable`), `evt:crystal_wall` (secret door), `evt:lectern` (message) |
| Doors | sentry (plank, hinged), barracks double door (two hinged leaves that open together), back stair, armoury, tower, gate, hoard, crystal wall: 10 doors and 4 movers |
| Chests | armoury (a field hammer, 60 gold, two rolls of 3), prospector's pack, Red Dwarf chest, the King's two (trapped, level 4) |
| Population | 9 monster spawn points (5 dwarf, 2 spider, 2 tiger mole) and 3 item spawn points; 18 placed: the King, his guard of 4, the gong sentry, 5 in the barracks, 3 on the far bank, 2 gate guards, 2 bat queens (hidden) |
| Lying items | a dwarven axe by the armoury's rack, a zircon in the geode, a potion by the prospector |
| Lights | 44 lights in objects.yml (26 pulsing: slag, flambeaux, the smelter's mouth, crucible, forge braziers, dome, geode, vault; 4 switched dark at the start: the barracks' three and the wrath's three) and 21 decorations that carry light |
| Decorations | 82: torches, lanterns, flambeaux, braziers, statues, barrels, cask, bowls, goblets, spoil heaps, buckets, rocks, crystals, stalagmites, skeletons, bones, the memory crystal |

## Scale against the bands

`oymap metrics <L4> --reach` (`output/studio_cal/xd03/metrics.json`); bands from
`devdocs/xeen/research/MAP_CRAFT_CALIBRATION.md` 3.1, 3.3 and 6.3.

| Figure | XD-03 L4 | Band |
|---|---|---|
| Floor area | 24.9 M units² (walkable 18.4) | S 20-35 (the brief's class); L3 measured 21.6 |
| Sectors | 24 | S 10-20, M 20-35; one sector per room (the hall, its channel, bridges and gallery are one) |
| Floor levels | -800 (warren) to +1216 (shaft head) walked; the hold at -512 and -128, the arrival +384 and 0, the caves -640 to -800 | 2-4; height range MM7 1,050-2,860, here 2,016 |
| Loops | 2: the barracks ring (gallery, back stair, barracks, hall) and the bridges inside the hall (metrics counts sector loops: 1) | at least 1 for M |
| Doors | 10 doors and 4 movers (14 door records); 17 door events | M 8-16, 5-14 door events |
| Monsters | about 35 (9 markers of 1-3 and 18 placed): 1.5 per sector | S 20-35; the brief about 34 |
| Chests | 5 (with the prospector's pack) | S 2-4, 3-7 |
| Secret faces | 2 (the crystal wall) | 1-6 per M dungeon |
| Plates, traps | no plates; 71 "pressure-plate" faces are the step events' floors (gallery, gutters, the hall's floor, the descent, the cart); harmful floors: the channel and the gutters | 1-15 plates |
| Boss | the Clan King (named, hit points ignored) | about 1 dungeon in 5 |
| Light sources | 39 counted by metrics (18 records, 21 decoration lights; the 26 pulsing lights are not counted): 1.57, really 2.6 per M units² | 7d24 3.86, 6d18 2.93, XD-02 2.0 |
| Decorations | 82, 3.3 per M | 7d24 2.77, 6d18 1.68 |
| Doorways | median 224 wide, 320 high | 256 x 256 |
| Sector height | median 640 (256 to 1856) | 464-592 mid rooms |
| Non-orthogonal rooms | 12 of 24 (the hall, the King's hall, landing, antechamber, armoury, tower, geode rooms, vault, warren, hoard); 13 with sloped, stepped, uneven or vaulted floors or roofs | at least 40 %, 25 % |
| Main wall texture | c2b 20 %, vlcwl3a 11 %, crstont 8 %, d2wlactr 8 % | one texture 45-85 % (here four families, one per area) |
| Clickable faces | 172 | 50-170 |

## Order of play (`oymap solve`, `output/studio_cal/xd03/solve.txt`)

```
step 0: 4 sectors   the Deep Line head and its ledge (the arrival)
step 1: 12 sectors  the cart (event 17) -> the landing; the gallery door (event 23) -> the cut, the hall and all open off it
step 2: 4 sectors   the barracks doors, the back stair, the geode (gem clusters, crystal wall)
step 3: 2 sectors   the armoury door; lever A (event 36) and lever B (event 37) -> the King's Gate (event 27) -> the King's hall
step 4: 2 sectors   needs item 2108 (the King's key): the hoard door -> the hoard and the shaft
step 5: needs qbit 110031 (the shaft lever): the cage -> the shaft head and the X1 exit
never reached: 0 sectors
```

That is the brief's critical path (landing, cut, gallery, hall, barracks, hall, tower, hall, antechamber, King's hall)
and return path (hall, hoard, shaft). `solve` does not see that the King carries the key (defect 2).

## Playtests

`playtest.yml` (175 steps): a level-9 party rides the cart down, walks the cut (lookouts), opens the gallery door and
kills the gong sentry at once (the alarm stays quiet ten seconds later), rings the gong itself (both barracks leaves
and the back-stair door open, the torches light, the gong refuses to ring twice), fights the sergeants, walks down the
gallery stair, through the barracks to lever A (the lower bar lifts), opens the armoury, loots its chest (the field
hammer) and picks up the axe; crosses the north span, fights the far bank's guard, finds the gate barred with one bar
up, climbs to the tower and throws lever B; walks into the slag of the main reach and out by the slag steps, over the
south bridge, into the south reach and out by the drain steps; through the breach and down the descent (the bat queens
appear), prises a gem cluster (one gem, once), sinks the crystal wall, reads the lectern and loots the Red Dwarf chest
(its amber and iolite); walks down to the mole warren and loots the prospector's pack (100 gold); opens the King's Gate,
kills the King's guard (the wrath: `kings_wrath` set), stands in the west gutter (it burns) and steps out (`in_gutter`
cleared), kills the King (`clan_king_slain`), takes the key from his corpse, opens the hoard (the key kept), loots the
King's first chest (its ruby), throws the shaft lever (`escape_shaft_open`), rides the cage to the shaft head and
leaves for the stand-in with both bits, the key and the ruby.

`playtest_alarm.yml` (46 steps): rides the cart down, steps off and on (it rides back up), off and on again (down);
walks the cut, opens the gallery door by its click and lets the sentry live: he rings the gong (`alarm_rung`, both
doors and the back-stair door open, the torches light); back through the cut, up on the cart, and out by the Deep Line.

Nothing depends on chance: only chests with fixed items are checked by those items; the gem is counted, not named;
the walks clear hostiles round the party, with small radii near the King. Two traps found while writing them:
`open_door` kills monsters near a door (it killed the sentry in the alarm test; that test clicks the door instead), and
`clear_hostiles` kills through walls (the hall's walks kept under the gallery's distance).

## Departures from the brief

1. **The gong gallery is a balcony inside the furnace hall** (the handoff's "the gallery over the hall"), not a room
   beside it with two windows; the overlook is the whole hall. Its stair runs inside the hall; L3's gallery stair and
   stair foot rooms are gone.
2. **The slag channel is one sunken level in one hall room** with hanging bridges (L3: seven rooms). A level must stay
   clear of the walls, so 32 of bank remain between the channel and the north and west walls; the channel's foot ends
   at the west wall instead of running under it.
3. **The drain is a flight of four steps** out of the south reach onto the bank by the breach, not a tunnel into the
   breach (an opening cannot sit below the hall's floor).
4. **The stepped dais and the throne floor are inside the King's hall** (a flight and a level along its north wall),
   not beyond a broad opening; the hall is widened to take the gutters (2688 x 1792, L3: 2304 x 1728).
5. **The King's second phase starts when his guard has fallen**, not at half his health (gap 1). The braziers' fire
   goes out by their lights; the brazier models cannot be swapped or tipped (gap 4). He leaves the dais only as far as
   `immobile` allows: the word cannot be lifted by an event, so he stays on the throne floor and fights from there.
6. **A door at the back stair's foot**, opened by the alarm: without it the sleeping sergeants would wander up the open
   stair long before any alarm.
7. **The arrival is the Deep Line's head** in the landing's east wall, 384 up, and the cart is a ride down a trestle
   (L3: the cart standing at the buffer stop on the landing's floor). The landing is 1536 x 896 (L3: 1024 x 768).
8. The north span and the south bridge have a low iron kerb (16) to read as bridges; still no rails.
9. **Texture families** instead of the brief's mixed picks (the lead's rule): the brief's `7tfb11` floors, `7cdb`
   hold, `d2flor`, `cwb1`/`cwb1gold`, `orwtrlga` geode, `vlcflord`, `MM7 lava` are replaced as the table above says.
10. The barracks has no bunk at its south-east corner (the back stair lands there); the armoury's racks are rails on
   posts with a placeholder for the weapons.

## Gaps (what I wanted to say and could not), most harmful first

1. **A condition on a monster's health** (set:clan_king, "phase two at half health"): `condition: {kills: {monster:
   monster:clan_king, hp_below: 0.5}}` or an actor script word (`monsters[].behaviour`). Used: the guard has fallen.
2. **A map's own monster relations** (XD-02's gap 1, unchanged): MM7's Dwarf rows are the party's allies; a load event's
   Lua `evt.SetMonsterRelation` makes them hostile. `project.yml relations` or `map_stats.slots[].hostile`.
3. **A placed monster's hit points, level and modifiers reach the game** (XD-01's gap, unchanged): the King has 100 hit
   points in the game (picture 27, `hp: 300` in the scene), no frenzy (`monsters[].modifiers: [frenzy]`), and
   `immobile` cannot be lifted by an event (an effect `mobile: monster:clan_king`).
4. **A decoration cannot be hidden, swapped or switched by an event**: the forge braziers cannot be kicked over
   (`brzier00` to `brazir2f`), the gem clusters had to be built of platforms to be hidden. `effects: {hide: deco:id}`,
   `{set_decoration: {of, to}}`.
5. **A floor's kind cannot be changed by an event**: the gutters burn by step events and a timer. `effects:
   {floor: {of: platform:gutter_w, kind: lava}}`.
6. **A placed monster's name shows only on its corpse** (`Clan King` shows as "Dwarven Lieutenant"): a project names
   table (XD-01's gap 2).
7. **Placed sounds of an MM7 project are refused** even for the engine's own sounds: `sounds[0].sound: the world mm7
   has no sound file lava loop` though `engine/audio/lava loop.wav` exists. The brief's slag bubbling, gong boom, crystal
   hum and wind in the shaft are missing. Repro `output/studio_cal/xd03/repro/sound_mm7/` (`validate.txt`).
8. **Exits only on walls**: the cart and the cage cannot be the way out; the party clicks the Deep Line's end and the
   shaft head's wall. `exits[]` on a mover or an effect `exit: <neighbour>`.
9. **No camera shake word** (the gong, the wrath, the shaft lever): Lua `evt.CameraShake`.
10. **No rotating lever**: the three levers are switch plates on walls.
11. **Things riding a mover**: the cart cannot carry a lantern or a decoration (`decorations[].rides`).
12. **Arrival points for the other entrances** (from X1 down the shaft) cannot be said in this project; only one `start`.

## Tool defects (repros under `output/studio_cal/xd03/repro/`)

1. **A platform on a raised level is measured from the room's floor, without a word.** A platform with `base` whose
   middle lies in a sunken level is measured from that level's floor (and the build says so); one on a raised level
   (a gallery, a dais) is measured from the room's floor and is built inside the level's solid block. The gong, its
   plinth and frame on the gallery and the whole throne on the dais were invisible in the first take; they now carry
   the level's height in their `base`. Repro `repro/platform_on_raised_level/` (`project/`, `result.txt`: the platform
   on the gallery at 384 has its top at 96, the one in the pit at -32).
2. **`solve` does not count an item a placed monster carries**: "item 2108 ... is not given or held in a chest on this
   map: it comes from elsewhere", though `monster:clan_king` `carries` it. Repro `repro/solve_carries/`.
3. **Placed sounds**: the refusal above names the world's audio folder only; the example it gives (`waterdrip.wav`) is
   not in that folder for MM7 (XD-01/XD-02's defect, unchanged). Repro `repro/sound_mm7/`.
4. **`oymap assets` hints mislead for some decorations**: `7dec11` ("dirt") draws as a dead tree, `Corpse` and
   `Corpse07` ("corpse") as standing living people in the game (first take, `shots_take1/37-mole-warren.png`); the
   skeleton is `dec05`, not `7dec05` (a cage) as the brief and the first lookup suggested.
5. The movers' schema text still says a level slide does not carry the party (XD-02's defect 3); the cart and cage
   here travel with a vertical part and carry.
6. Test harness: `open_door` kills monsters near the door (the gong sentry died to it); a light assertion on a pulsing
   light reads `unset`; in a screenshot tour the map's timers do not run (the wrath never fired however long a shot
   settled) and neither `actor kill <radius>` nor `lua evt.KillMapActor(...)` killed the King's guard, so pictures 28
   and 29 come from a scratch copy whose wrath event has no condition (`output/studio_cal/xd03/wrath_copy/`), run by
   the console's `event 34` (the playtest proves the real chain); a `walk_to` that ends while the party is still on a stair's steps reports a height
   between steps.
7. Minor: `plan.yml level` takes only L0-L3, so this L4's plan says `level: L3`.

## What in the brief was unclear

- "Phase two at half health" and "he comes down off the dais" have no words; the brief's state also lists him
  "frenzied" as a modifier the studio cannot give.
- The gutters are "dry until the second phase" but L3 draws them in the slag theme; a texture swap by event exists
  only for doors, platforms and panels (built so).
- The back stair is an open link; with sleeping sergeants behind closed hall doors it needs a door (built).
- The geode is "cold blue crystal" and the King's dome is "the geode's crystal": no shipped crystal texture is blue
  and coherent with a cave set; the nearest is Snergle's Caverns' blue-grey rock.
- "The bars are seen lifting from the antechamber" with bars across a gate whose leaves swing: built as bars in front
  of the leaves on the antechamber side, so the leaves swing into the hall.

## Pictures

Best: `shots/03-cart-riding-down.png` (the cart halfway down the trestle), `shots/07-gallery-overlook.png` (the hall
from the gong gallery: the smelter, the slag channel and the far bank), `shots/22-gate-opens-on-the-throne.png` (the
gate's leaves open on the throne at the far end), `shots/11-slag-channel.png` (the channel running across the hall
with the gong over it), `shots/16-barracks-alarm.png` with `15-barracks-asleep.png` (before and after the gong).
Also good: `08-gong.png`, `21-bars-lifted.png`, `23-king-hall-from-gate.png`, `29-gutter-burning.png` (from the picture copy), `33-geode.png`.
Weakest: `shots/24-dome.png` (the dome is a grey stone cupola with a small cavity at its crown, not the glittering
crystal the brief wants: the crystal texture to generate) and `shots/37-mole-warren.png` (a dark plain burrow).

Fixed after looking (takes `look1`-`look3`, `shots_take1`, `shots_take2`): the hall and the King's hall were flat and
bright (base darkness raised to 21-24, the light in pools); the gallery parapet hid the hall (lowered); the gong, its
frame and the whole throne were buried in their levels (defect 1); the dome and geode read as water and sky (other
families' crystal, replaced); the gate bars were pale (dark iron); the lanterns in the Deep Line head filled the
arrival picture (small torches); a dead tree and standing "corpses" in the warren and geode (skeletons and bones);
the armoury racks looked like doors (rails on posts); a tie beam in the tower drew as a spike up the flue (removed);
the geode's crystal-cavity panels looked pasted (removed); textures from the wrong places (the lead's rule).

## Judgement

As a dungeon it has what the brief promises and all of it works: you arrive on a real cart ride down the Deep Line's
last pitch, walk a timbered cut to a gallery where a sentry will ring the gong if you are slow, look down on a hall cut
by a glowing slag channel with two bridges and a ruined smelter, wake (or surprise) a barracks of sergeants, throw two
levers in two corners of the hold and watch the bars lift off the King's Gate, which opens on the throne at the far end
of a six-sided hall under a dome; the King's guard falls, the slag pours into the gutters, the King dies and leaves his
key, his hoard pays, and a counterweight cage carries you up a 1500-foot shaft to the hills. The optional geode has
bats that drop out of its crown, gems to prise out, a singing wall and an old vault. It is short and dense, as the
brief wants, and the alarm and the two-lever gate give the middle a plan to make.

Its weaknesses: the King's fight is an ordinary Dwarven Lieutenant with an ordinary 100 hit points who never leaves his
dais, and his second phase is a light change and two burning gutters, not a frenzied king; the dome does not glitter;
the furnace hall's walls are large plain planes of brick and granite under a dark roof; the geode is blue-grey rock
with crystal models rather than a crystal lining; the mole warren is a dark empty knot; there is no sound at all; the
clan are MM7's friendly dwarves made hostile by a line of Lua, all one model, so sergeants, guards and dwarves look
the same. A player would enjoy the cart, the gong, the two levers and the gate opening on the throne; the King himself
wants a Xeen row, an actor script and sounds before he is the climax the brief asks for.

## Exits to Vertigo (2026-11-13)

`exit:x1_shaft` (the hatch, evt:exit_x1 26) now leads to X1 (`xeen_x1.odm`): arrival [-1024, 17565, 1500], facing 270
(south), on the hilltop in front of X1's shaft head (`thing:shaft_head`, face at y 17965; ground about 1469 on a
slope, so the party drops a few units). Unchanged: `exit:deep_cart` still goes to Emerald Island (XD-02's station is
its place). `playtest.yml` checks map and position on X1 after the hatch and walks off down the hill.
The map installed in `xeen_root` before this change was older than the current studio (status-line durations and one
face differ in a build of the unchanged backup); this install carries those too.

Backup before the change: `output/studio_cal/xd03/exits_backup/`. Build `output/studio_cal/xd03/exits_build/` (against
`output/studio_play/xeen_root`); only the exit's `evt.MoveToMap` line changed in the built Lua (the .blv and scene are
byte-equal to the build of the backup). Installed in `xeen_root`. Arrival points were read from X1's build
(`output/studio_cal/x1/build/export.json`: the doorway models' faces; ground from its height map), 400 units in front of
the door face, clear of the doorway model, on open ground; the playtest walks off from there. Pictures of every arrival,
facing out and turned back to the door: `output/studio_cal/x1/exits_pics/sheet.jpg`. On first arrival on X1 from a
dungeon Mayor Gunther's errand window opens (X1's one-shot timer), as on a new game there.
