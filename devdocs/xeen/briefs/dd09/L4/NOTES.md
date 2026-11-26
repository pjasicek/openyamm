# DD-09 Temple of Bark, L4: notes

The source's Temple of Bark (dark/aaze0073-0077) rebuilt as a new M dungeon inside the great tree of D2 Sprite Forest:
side quest **Q-D10** (Princess Sheewana, held by Shaalth's orcs) and **M18** (two Energy Disks in the root alcoves),
built with the Map Studio from its graph (`devdocs/xeen/mockups/act3_graphs/dd09.graph.yml`) and decider D-27
(`devdocs/xeen/mockups/act3_a8_decisions_b.md`, which wins) by lane A8's sub-agent `agent:xeen-a8-dd09`, 2026-11-20.
Key `dd09`, project `xeen_dd09`, stem `xeen_dd09.blv`, map_stats 9158, world `xeen`, music 12.

**State.** L1-L4 `oymap validate` no issues, `fmt --check` clean, build 0 warnings. Installed in the scratch root
`output/studio_cal/dd09/root` only (the lane lead installs into assets_dev). `oymap audit --world xeen --reach --solve`
(`output/studio_cal/dd09/audit.txt`, `solve.txt`): 0 errors, 0 warnings, 0 faces in one plane, 0 dressing findings;
solve reaches 26 of 26 sectors in three steps (the vault last, on `disciples`). Playtests: see below.

**Scratch** `output/studio_cal/dd09/`: `tools/gen.py` (plan, project, diagram; `python3 gen.py L1 L2 L3 L4`),
`tools/geo.py` (rooms, openings, themes), `tools/dress.py` (objects, wiring), `tools/tour.py` + `tools/sheet.py`
(tours and JPEG sheets), `cycle.sh` (generate, fmt, validate, build, install into the root, audit, record;
`LEVELS="L1 L2 L3 L4"`, `INSTALL=0`, `ROOT=`), `four.sh` (the three playtests N times, one game at a time, exact PIDs;
`ASSETS=` defaults to the root), `shoot.sh <tour>` (one tour run), `run/` (logs), `shots/` (sheets).
**Every project file of L1-L4 except the playtests and these notes is written by the generator** (DD-01's scripts
adapted); each run recorded with `oymap record --author agent:xeen-a8-dd09`.

## The temple

Four floors in one frame (x east, y north, heights from the arrival floor), each in its own part of the plan, joined
by climbing tunnels:

| Floor | Rooms | Monsters |
|---|---|---|
| Trunk base (0) | trunk door (arrival, exit to D2), Hall of the Trunk (dome of bark, four root columns, the voice), orc barracks, guardroom, Chapel of Sap | 6 + 1 Captain, 4, 2 Shamans |
| Roots (-512, west) | root stair (0 to -512), the root cellar (root pillars, rough earth), west and east root alcoves, sap store (two vats of sap, the black barrel and its sign, the ledger, a chest), the pens (Nathan's and Sky's cages, the lever) | 4 Arachnoids, 3 + 3 Elites |
| Upper trunk (640, east) | ring stair (0 to 640, winding round the barracks), ring landing, Shaalth's hall (the dais, Sheewana's cage, the hoard), cell row (Snog's and Alicia's cells; the orcs' back stair from the guardroom arrives here), the shaman's tea room (kettle), the Chapel of Ascension (three dials, lever, Dark and Crystal Water, the Book), the Disciples' vault | Shaalth + 3 Captains + 2 Shamans, 1 Captain, 4 Shamans |
| Limbs (1280, south-east) | limb climb (640 to 1280), limb stair, the limb walk (three limb alcoves), fruit rooms, the crown (grass, a canopy of leaves, four fountains in pools), Barkman's hollow (diary, bound chest; Barkman hidden), treasure room | 4 + 2, 2 + 2, 4 Hunters, Barkman, 2 Shamans |

**Measured** (`oymap metrics`, `output/studio_cal/dd09/metrics.json`): **26 sectors** (M 20-45), **70.8 M units² of
floor** (M 30-90), 8 doors (+ 5 cage gates and 2 levers: 15 door records), 5 chests, **50 placed monsters** (+ Barkman
hidden, 4 prisoners and Sheewana peaceful), 4 loops (base, roots, back stair, limbs), 32 lights, 8 placed sounds,
33 decorations.

## Monsters (all placed, Xeen rows of A2)

| Who | Row | Level | Where | Count |
|---|---|---|---|---|
| Orc Elite | 11040 | 16 | barracks 6, guardroom 4, pens 3, sap store 3 | 16 |
| Orc Shaman | 11041 | 20 | chapel 2, Shaalth's hall 2, tea room 4, treasure room 2 | 10 |
| Orc Captain | 11042 | 26 | barracks 1, Shaalth's hall 3, cells 1 | 5 |
| Shaalth | 11043 | 30 | his dais (`monster:shaalth`, group 5) | 1 |
| Arachnoid | 11330 | 14 | root cellar 4, limb walk 4, fruit rooms 2 | 10 |
| Arachnoid Hunter | 11331 | 18 | limb walk 2, fruit rooms 2, crown 4 | 8 |
| Barkman | 11633 | 60 | his hollow, **hidden** (group 30), shown by the first limb gem | (optional; Act IV, D-1.2) |
| Snog | 11044 | 16 | his cell, peaceful (own faction), immobile, group 20 | talker |
| Nathan, Sky, Alicia the Just | 11902, 11903, 11904 (A2, each its own friendly faction) | 15 | pens and cells, peaceful, immobile, group 20 | talkers |
| Princess Sheewana | 11905 (A2, her own friendly faction) | 10 | her cage, peaceful, immobile, group 21 | talker |

**Kill XP** (rows' XP): 16 × 416 + 10 × 600 + 5 × 936 + 1,200 + 10 × 336 + 8 × 504 = **25,928 for the party, 6.48k per
member** (graph target about 7.1k: −9 %; Barkman's 4,200 not counted, D-1.2).

## Mechanisms

- **The voice** (`evt:voice`, step on the hall's floor): A3's `q-d10.voice` once per visit (`voice_heard`, cleared by
  `evt:voice_reset` on leaving).
- **Root alcoves** (hover "Root alcove", wall panels of sap-veined earth in the two alcove rooms): the studio's question
  "Feed me! Give gem?" / "Give gem (Yes/No)?"; Yes runs A3's once-hook (`q-d10.root_west` / `root_east`: takes one gem,
  its text) and the map gives the Energy Disk 12334 (the hook's map_gives; it lands on the cursor as given items do).
  Fed: the hook's else text "The root is fed." No gem: the hook's fail text.
- **Limb alcoves** (hover "Limb alcove", three panels along the limb walk): the same question; Yes takes one gem
  (`Xeen.payGems(1)`), sets the alcove's variable and `barkman_woken`, A3's `q-d10.limb_alcoves` says the words;
  then "The limb alcove is fed. Something in the trunk is still awake." `evt:barkman_wakes` (timer) shows group 30 the
  first time (`barkman_shown`); his state is kept with the map (save and reload checked).
- **Barkman's chest** (hoard 4): the chest preset with the condition "Barkman dead"; locked text "The life force of the
  BARKMAN binds the lid of the chest shut, making it impossible to open." (aaze0077:21). His diary on a stump
  (aaze0077:19).
- **The black barrel** (sap store, hover "Black barrel"): once per character (condition `player_bit` 11317, else "The
  black sludge has done all it will do to you."); the studio's question with the source's lid note: "The barrel is
  filled with a strange black sludge. A note on the inside of the lid reads, "Danger: Unpredictable Effects." Drink?";
  Yes: `evt.ForPlayer(Players.Current)`, +1 to the seven base stats, `AddValue(Age, 1)` (merge point 12: ages the
  member; an AgingImmunity item, the Jewel of Ages, protects, D-2.4), the bit, "Your statistics have improved, but you
  have suffered a little magical aging." A wall sign above it says "Danger: Unpredictable Effects." Played: all seven
  stats 10 → 11 and the age exactly one year more; a second drink refused.
- **Flasks** (Chapel of Sap, alcove ledges): red +2 Might (bit 11315), blue +2 Personality (bit 11316), once per
  character ("The flask is empty for you."), XD-08's / DD-01's method.
- **The pens' lever** (`switch:pen_lever`): two states, toggles the four prisoners' gates (movers sinking into the
  floor) and `pens_open`; "You hear a rumbling in the distance." (aaze0073:15) both ways; the first opening sets
  **`prisoners_freed` 117121**. Each gate is its prisoner's click (hover "Nathan the Prisoner" etc.): locked "Locked. A
  lever somewhere in the temple works these cages."; open: `evt.SpeakNPC(<npc>)`, A3's topic Thanks (500 XP once,
  `thanks_*` 113212-113215). `evt:prisoners_gone` (load) hides group 20 and sets `prisoners_gone` once
  `prisoners_freed` is set, on a fresh entry only (map variable `in_visit`, session 6 below): on the next entry the
  cages say "The cage is empty."
- **Shaalth** (`monster:shaalth`): a timer runs A3's `q-d10.shaalth` at his death (shaalth_slain 113204).
- **Sheewana's cage** (`mover:cage_sheewana`, hover "Cage"): A3's `q-d10.cage` (fail text while Shaalth lives; sets
  cage_opened 113205); `evt:cage_opens` (timer) lowers the gate; then the cage talks: `evt.SpeakNPC(5107)`, topic Home
  (A3: sheewana_freed 113206, her move home); `evt:sheewana_gone` hides group 21; then the hook's else text "The cage is
  open and empty."
- **The kettle** (tea room): A3's `q-d10.kettle` (the source's invitation, aaze0075:17), then the typed question
  "Drink (Yes/No)?"; Yes: A3's `q-d10.kettle_drunk` and the drinker is poisoned (`PoisonedGreen`); repeatable.
- **The Disciples' chapel**: three dials (panels west, north, east; map variables `dial_west`, `dial_north`, `dial_east`
  0-3 shown as 1-4): "Dial reads N. Turn?" (aaze0076:10-13) and "Turn (Yes/No)?"; turning sets the next number and
  undoes the lever. The lever (`switch:asc_lever`): with west 1, north 2, east 3 it sets `lever_pulled` ("The lever
  clicks home. In the Crystal Water's basin the scum parts and the water runs clear."), else "Nothing happens.". The
  Crystal Water: before the lever "The water is stagnant." (aaze0076:9); after it A3's once-hook
  `q-d10.crystal_water` (disciples 113216, award 418 "Disciple of Bark" for every member; then its else text). The
  Dark Water: A3's `q-d10.dark_water`, the drinker poisoned and a tenth of the drinker's current hit points taken
  (`SubtractValue(CurrentHealth, ...)`, never the last; played: 150 → 135). The Book of Ascension on its lectern: A3's
  `q-d10.book_of_ascension`. The vault's arched door: "Disciples of Bark ONLY!" (aaze0076:0) until `disciples`.
- **The crown's four fountains** (bark spouts over pools): +5 Fire, Air, Water, Body resistance to the drinker, once
  per character (D-37, player bits 11306-11309), "The water is cool, clear and refreshing." (aaze0077:2); a second
  drink "... You have had your fill."
- **Books and ledger**: History of Bark, Book of Sap, Morning Ceremonies (bookcases in the chapel), the orcs' ledger
  (aaze0073:19-30), the tea room's cabinet "Nothing here." (aaze0075:1).
- `evt:arrive`: a one-shot window on the first arrival only (`arrived_once` 117120): "THE TEMPLE OF BARK. The round door
  shuts behind you on the bark glade. ..."

## Exit (live to D2) and arrival

| This map's exit | To | Arrival on D2 | Facing |
|---|---|---|---|
| `exit:trunk_door` (the south wall of the trunk door room; the game's leave window) | `xeen_d2.odm` | A6's return point for D2 event 13: **(-11264, -6656, 992)**, measured headless: (-11264, -6656, **993**) | north (90°, game 512), away from the tree |

D2 checked current in the root at 18:35 (same inodes as assets_dev's 17:53 install). **D2's door into this map (A6,
`door:dd09`, D2 event 13, still the old stub "...comes in a later part of the world.")**: start point **(0, -1920, 0)
facing north (90°, game 512)**, at the foot of the temple's first stair inside the trunk door.

## Original lines

"A voice bellows: 'Feed the roots ...'" (aaze0077:0, A3's voice); "Feed me! Give gem?" (aaze0077:14, the alcoves'
question); Barkman's diary and bound chest (aaze0077:19, 21); "Disciples of Bark ONLY!" (aaze0076:0), "The water is
stagnant." (aaze0076:9), "Dial reads N. Turn?" (aaze0076:10-13); the orcs' tea (aaze0075:17, A3's kettle); "You hear a
rumbling in the distance." (aaze0073:15); the ledger, the Book of Sap, History of Bark, Morning Ceremonies (aaze0073);
the black barrel's lid note and "Your statistics have improved, but you have suffered a little magical aging."
(aaze0074:7, 9); "The water is cool, clear and refreshing." (aaze0077:2); "Nothing here." (aaze0075:1). The prisoners'
lines are A3's topics (aaze0073:3, 5; aaze0075:9, 11, 19).

## Ids

- Map qbits (block 117120-117159, provisional): `arrived_once` **117120**, `prisoners_freed` **117121**,
  (117122-117125, the fountains' old map qbits, retired by D-37: no longer set or read).
- Player bits (provisional, D-27): **11315** red flask, **11316** blue flask, **11317** black barrel; A3's
  **11306-11309** the fire, air, water and body fountains (D-37).
- Quest bits read/set through A3's hooks and topics: 113204-113206, 113210-113216 (q-d10).
- Map variables: `voice_heard`, `limb_1_fed`-`limb_3_fed`, `barkman_woken`, `barkman_shown`, `cage_moved`,
  `sheewana_hidden`, `pens_open`, `prisoners_gone`, `dial_west`, `dial_north`, `dial_east`, `lever_pulled`,
  `in_visit` (16).
- NPCs: 5107 Sheewana, 5111 Nathan, 5112 Sky, 5113 Snog, 5114 Alicia (A3's topics in q-d10.yml). Groups: 1 the
  hostiles, 5 Shaalth, 20 the prisoners, 21 Sheewana, 30 Barkman.
- Item: Energy Disk 12334 (twice, the root alcoves).

## Textures (one family)

**38 distinct of 45 since session 6 (37 before: + `ceb1dr`), 0 new** (`tools/xeen/texture_budget.py --root output/studio_cal/dd09/root --map DD-09`). MM7 The
Hall under the Hill `7d22` (dungeon_families `temples`) with D2's bark: the bark `xdbark` (D-23, D2's trunks) on the
trunk's and the limbs' walls and vaults (34 % of the faces), heartwood planks `7t1books1` underfoot in the trunk and the
limbs; 7d22's root earth `c2b` / `c2b1` / sap-veined `c2bb` (the sap store, the alcove mouths), dark soil `cfb1`,
earthen ceilings `7dirttyl`, trodden dirt `7dirt1`; the old temple's green stone `ceb1sa` (chapels), `ceb2sa` under ivy
(Shaalth's hall, the Disciples' chapel), small brick `ceb3s` (barracks, guardroom), pilaster corners `ceb1el`, flags
`7tfb1`, `7tfb10`, `7tfb11`, rough `t2bs` (tea room, cells), grass `7grastyl` (the crown's floor and canopy), bookcases
`7t1books`, the cabinet `7t1cab`, bed rolls `7t1beds` (the tea room's mats), dials `7gt002c`, the sign `7gt002a`, the
ivy-arched vault door `ceb1dl` / `ceb1dr` (a hinged pair since session 6); plank doors `beemdorc` (MM6, DD-01's); the cage bars
`xwcage` (XD-04's see-through bars, D-22.1; `xngrille` until session 6) under `xwiron` tops;
liquids `7wtrtyl` (Crystal Water, the fountains), `tartyl` (Dark Water), `xjuiceorg` (the sap vats). Chest and lever
pictures add the rest. **No new textures**: the two the brief allowed (heartwood floor, alcove mouth) are served by
7t1books1 and c2bb; a request stays open if the user wants them (A6).

## Dressing (D-7)

`oymap audit --world xeen` on the installed map: **0 dressing findings** (the first L4 had a barrel 86 from the sap
store's walking line, moved to the east wall beside its pair). Props: barrels in a pair and the black barrel by the sap
store's walls, bedrolls and a cookfire in the barracks, sacks in the guardroom and the fruit rooms, bones in the pens,
mushrooms in the root cellar, a skull pole by Shaalth's dais, torches in the orcs' rooms. **Dressing exceptions:** none.

## Playtests

`output/studio_cal/dd09/four.sh` from the scratch root (`ASSETS=` for assets_dev), `--world xeen --map
xeen_dd09.blv`; the root has a test map_stats/bolster row for 9158 (copied from DD-01's with this map's name, stem,
music 12, treasure 3, the slots below) until A2 writes it. Logs `output/studio_cal/dd09/run/four_*`.

| Test | What |
|---|---|
| `playtest.yml` | the critical path through every mechanism (header): roots and disks, barrel (stats and age), pens and lever, flasks, cells, prisoners gone after a reload, Shaalth, cage, Sheewana, kettle, the Disciples' chapel (stagnant, wrong dials, Dark Water, Book, dials, lever, Crystal Water, vault), Barkman absent / shown / kept after a reload, his bound chest, a fountain, the treasure room |
| `playtest_hostility.yml` | 16, 10, 5, 1, 10, 8 hostile at load, none peaceful; Snog and the four peasant bodies peaceful; an Elite, an Arachnoid, a Shaman and a Hunter side by side do not fight each other |
| `playtest_exit.yml` | the trunk door's exit window, OK: D2 within 128 of (-11264, -6656), z 960-1030; walks north |

**Results: all three 4 of 4, exit 0** (`output/studio_cal/dd09/run/four_184347`, summary `four3.out`): playtest 294, hostility 35, exit 23 asserts passed in each run. (An earlier run failed once where a chest had given the party a gem and the limb check counted rubies only; the check now counts every gem before and after.)

## Pictures (looked at)

`output/studio_cal/dd09/shots/rooms1_1..6.jpg` (every room from two corners, every tunnel), `things1_*.jpg` (every
interactive thing; the cages shut and open; Barkman hidden and shown). **No bake in the root** (the lane lead bakes
after install): lighting is the build's own. Sheets kept: `rooms1_1..6.jpg`, `things1_1..4.jpg`, `fix3_1.jpg` (Sheewana's
cage shut and open); PNG folders deleted for the disk (`tools/tour.py rooms|things|fix <name>` and `shoot.sh` remake
them). What I changed after looking: a pillar of Shaalth's hall stood on the sightline to Sheewana's cage (moved north);
the crown's fountains were a decoration that draws nothing in this world (now bark spouts over their pools); the sap
vats and the tea room's mats wore a chest's picture (planks now). Still plain: rooms are boxes (the hall's dome and
the root cellar's rough walls aside), bark on the vaults reads as stripes, the limb and root alcoves are flat dark
panels of sap-veined earth (a recess or the brief's new "alcove mouth" texture would read better), the trunk's door is
MM6's square plank door. Barkman did not show in a tour picture (the tour's console command did not wake him); the
playtest shows him hostile and visible to the engine after the first limb gem and after a reload, but his look in the
Xeen world (row 11633, "reuse MM6 demons") is not checked in a picture.

## Words needed

1. **A talking monster indoors** (objects.yml `monsters` take no `npc`; the build writes `npc_id: 0`). Workaround: each
   prisoner talks through his cage gate and Sheewana through hers (clicked movers running `evt.SpeakNPC(id)`), the
   bodies stand peaceful and immobile behind the bars (DD-01's and DD-04's finding). Checked first: XD-12's Crodo (row
   11900) is a peaceful placed body whose words are a step message, not a talk, and XD-25's townsfolk say their line
   by a step too; neither is a talking actor.
2. **A dynamic question** (the studio's `question` takes a fixed message): the dials' "Dial reads N. Turn?" and the
   kettle's question after A3's hook text are hand Lua in the studio's own compiled form (`evt.SetMessage`,
   `evt.AskQuestion(eventId, 1, 0, 2, ...)`, `continueStep == 2`), which the audit's sandbox follows.

## Waiting on, and requests

- **A2**: map row 9158 (slots below); rows of their own for Nathan, Sky, Alicia (peasant looks) and **Princess
  Sheewana** (a sprite look, her own friendly faction, not the village sprites', who turn hostile on the robbery
  route): they stand on engine peasant bodies 358, 361, 349, 376 now; record the flasks (+2 Might / +2 Personality,
  bits 11315/11316) and the black barrel (+1 all, a year, 11317) as fixed by event.
- **A3**: register map qbits 117120-117125 and the player bits 11315-11317 (as q-d10.yml has them).
- **A6**: D2's `door:dd09` (event 13) to the door preset into `xeen_dd09.blv` at the start above.

## DECIDE

1. **The crown's fountains** (graph: +5 Fire, Air, Water, Body resistance once per character; D-27 is silent; the brief
   gives three player bits): built once for the whole party per fountain (map qbits 117122-117125). The cheaper-to-reverse
   option; four more player bits make them per character.
2. **Sheewana's body**: an engine peasant woman until A2 gives her a row (see requests).

## What the user should look at when playing

- The hall of the trunk under its bark dome; the root alcoves' "Feed me! Give gem?".
- The black barrel: a year older and +1 to everything, once.
- The pens' lever, the prisoners' thanks through their opened cages, and the empty cages next time.
- Shaalth's hall, the cage, Sheewana's goodbye; the tea (poisoned); the Disciples' dials and two waters.
- A limb alcove's gem waking Barkman, who walks out of his hollow.

## Installed (lane lead, A8 session 5, 2026-11-20)

- Rebuilt on the merge point 13 oymap (byte for byte the agent's build), installed into assets_dev by temp file and
  rename (`output/studio_cal/a8_s5/rebuild.sh dd09`), baked (`a8_s5/bake.sh dd09 <scratch root>`, profile
  `tools/lighting/baked_indoors/profiles/xeen_dd09.yml`, XD-08's values; `stale_bakes.py` 0).
- A2's map row landed; **playtests from assets_dev 4 of 4** under D-32's levelRadiusLimit 60
  (`output/studio_cal/a8_s5/assets_dev_dd09_10a.out`, `run/four_1902*`).
- Baked pictures (`output/studio_cal/dd09/shots/baked_a.jpg`, 24 of the 48 rooms shots, looked at by the lead): the
  play works, the look is weak. Still weak (a polish pass, as XD-10's): most rooms are plain boxes with a flat ceiling;
  D2's bark on the ceilings reads as stripes; the green brick halls (7d22) and the bark rooms change family at a
  doorway without a trim; the crown room's grass-green floor with a flat blue block (the fountain) reads as a carpet
  and a crate; the prisoners and Sheewana stand on engine peasant bodies (A2 rows needed). Barkman not seen in the
  tour (hidden until a limb gem).

## Light audit (merge point 14)

By `agent:xeen-a8-lights` (lane A8), 2026-11-20, on A1's light-fixture audit (`devdocs/xeen/formats/LIGHTS.md`,
`output/xeen_a1/lights_xeen.txt`). Changed in the generator (`output/studio_cal/dd09/tools/dress.py`, copy before the
change `dress_before_lights.py`; the generator reproduced the project byte for byte first), L4 regenerated, `oymap fmt`,
`oymap record --author agent:xeen-a8-lights --label "lights audit (merge point 14)"`.

- The treasure room's west torch stood in the doorway from Barkman's room (0.5): now at 0.2.
- The ring stair's ceiling stays level while its floor climbs, and the default light height put its upper light 249 into
  the rock: both ring stair lights now have an explicit height, 256 over the floor.

- **Audit** (`oymap audit --reach --solve` on the installed map, `output/studio_cal/dd09/audit_lights.txt`): lights
  errors/warnings before **3/0 (wall_missing, in_doorway, light_in_solid)**, after **0/0**; no dressing finding. **Light
  exceptions:** none.
- **Installed** by `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd09` (build `output/studio_cal/dd09/b_193022`), baked
  (`output/studio_cal/a8_s5/bake.sh dd09 assets_dev`, profile `tools/lighting/baked_indoors/profiles/xeen_dd09.yml`),
  `tools/lighting/stale_bakes.py --check` lists none of the lane's maps. **Playtests from assets_dev, each 4 of 4**
  (`ASSETS=$PWD/assets_dev four.sh`; record `output/studio_cal/dd09/lights_post.out`): playtest 4/4 (294 steps);
  playtest_hostility 4/4 (35 steps); playtest_exit 4/4 (23 steps).
- **Pictures** `output/studio_cal/dd09/shots/lights_mp14/01-torch_11.png` and `lights_mp14_ring/`, looked at: the
  treasure room's torch on its west wall beside Barkman's doorway; the ring stair lit evenly up and down its east run
  (no light behind its walls).

## Session 6 batch (D-37, rows, doors)

By `agent:xeen-a8-dd09` (lane A8), 2026-11-20, brief `output/studio_cal/a8_s6/brief_dd09_batch.md`. The generators
reproduced the installed L4 byte for byte first (snapshot `output/studio_cal/a8_s6/snap/dd09/`, after `oymap fmt`); the
diff after the change shows only the changes below. Changed in `tools/dress.py`, `tools/geo.py`, `tools/gen.py`
(backups `dress_before_doors.py`, `geo_before_doors.py`; `*_before_fit.py` before the texture-fit item); recorded
"D-37, rows, vault doors, prisoners on re-entry", then "texture fit: ..." (two records).

- **Vault door** (`door:vault`): a hinged pair, `pictures` and `back_pictures` `[[ceb1dl, ceb1dr]]` (each 128 x 256;
  ceb1dl the only other use, none elsewhere). Events and lock unchanged ("Disciples of Bark ONLY!" until `disciples`);
  the second leaf is door record 16 (`door:vault.leaf2`). The doors check: 8 and 16 a wing pair, no `doors.*` finding.
- **Bodies**: Nathan 11902, Sky 11903, Alicia the Just 11904, Princess Sheewana 11905 (A2's rows, each its own friendly
  faction) for the engine peasants 358, 361, 349, 376. Talk (NPCs 5111-5114, 5107) and the pen lever unchanged.
  `playtest_hostility`: each of the four peaceful (1, never hostile).
- **D-37 (3) fountains**: once per character on A3's player bits 11306-11309 (+5 Fire, Air, Water, Body to the clicking
  member, "The water is cool, clear and refreshing. +5 <kind> resistance (permanent)."; again: "The water is cool,
  clear and refreshing. You have had your fill."). Map qbits 117122-117125 retired (no longer in project.yml, set or
  read). `tools/xeen/quests.py`: the four DD-09 errors gone.
- **Prisoners on re-entry only** (A3's bug): `evt:prisoners_gone` (load) hides group 20 only when `in_visit` (map
  variable 16) is clear, then sets it; `evt:visit_end` (leave) clears it. The engine runs the map's leave events before
  it captures the map state on any map move (`GameApplication`: `executeCurrentMapOnLeaveEvents` then
  `captureCurrentSceneState`), so a game saved inside the map keeps `in_visit` 1 and its reload hides no one, while a
  fresh entry finds 0. Played: free them, save and load in the cell row: all four shown (`actor_visible hidden:
  false`), Snog and Alicia thank; out by the trunk door to D2 and back in (D2's own MoveToMap): `prisoners_gone` 1,
  the four hidden, "The cage is empty." (XD-25's `evt:townsfolk_gone` has the same reload fault; not this lane's map
  to change here.)
- **Texture fit** (merge point 16, A1's check): 28 errors, all `xngrille` (a picture meant once, 3 times across each
  384-wide side of bars and gate). The bars and gates now wear XD-04's see-through `xwcage` (a band that repeats
  across; D-22.1 "reuse first for any bars or cages"), and the cage tops' `xwiron` lies at scale 3 (a level face
  ignores `fit`; its edges do not meet up and down): the five `xwiron` seam warnings gone. Distinct textures 38 of 45
  (`ceb1dr` added, `xngrille` swapped for `xwcage`), 0 new.
- **Audit** (`oymap audit devdocs/xeen/briefs/dd09/L4 --assets assets_dev --reach --solve`,
  `output/studio_cal/dd09/audit_fit.txt`): 0 errors; 11 warnings, all `ceb3s` (below); doors, lights, dressing clean;
  reach 19 of 26 with the doors shut, 26 with them open; `oymap solve` 26 of 26 in three steps (the vault last, on
  `disciples`, both leaves).
- **Installed** by `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd09` (`b_204439`, then the fit builds `b_204951`,
  `b_205211`), baked and tested by `post.sh` under its lock: **playtest 4/4 (259 steps, 326 asserts), hostility 4/4
  (38), exit 4/4 (23)** each time (`output/studio_cal/dd09/batch_post.out`, `fit_post.out`; runs `run/four_204708`,
  `run/four_205320`); `stale_bakes.py` lists none of the lane's maps.
- **Pictures** (looked at): `shots/s6_batch/` (`s6_batch_sheet.jpg`): the vault's arched ivy door reads as one double
  door from the chapel and from the vault, both leaves out of the way when open; Nathan (the bedraggled human), Alicia
  and Sheewana (peasant women in green) stand in their cages. `shots/s6_fit/` (`s6_fit_sheet.jpg`): the pens, the cells
  and Sheewana's cage in `xwcage` bars (an even run of bars, the prisoners seen through them; the old grille's magenta
  fringes gone); the barracks' `ceb3s` brick.

### Texture fit exceptions

- `ceb3s` (barracks, guardroom, back stair walls; faces 35, 37, 38, 64-69, 328-335): `textures.storey_stacked` and
  one `tile_seams` (its seam down measures 3.37, just past 3): small brick in even courses, and in the baked and tour
  pictures no line shows where it repeats up the 512- and 1024-high walls; kept.

## Session 25 (A8): warnings checked

`oymap audit` (oymap 12:46:47) on the installed map: 0 errors, 11 warnings, all `ceb3s` (10 `textures.storey_stacked`,
1 `textures.tile_seams` on face 38), every one listed under "Texture fit exceptions" (faces 35, 37, 38, 64-69,
328-335). No map change (`output/studio_cal/a8_s25/audit/dd09.txt`).


## Session 26 (A8): F13 status lines, F12d book tops

- The four fountains (`evt:fountain_air`, `_body`, `_fire`, `_water`; +5 resistance once per character) showed the
  gain with `evt.SimpleMessage`; `tools/dress.py` `fountain_lua()` now writes `evt.StatusText(text, 6)` for the gain
  and for "You have had your fill." (helper `status_line()`, the seconds rule of the studio's `text:`).
- F12d: `platform:lectern` (the Book of Ascension), `platform:diary` (Barkman's stump) and `platform:ledger` (the orcs'
  crate) showed the heartwood plank picture on top; `tools/geo.py` gives them `BOOK_TOP`, `{texture: xnpbook,
  size: [128, 128], fit: true}` (the picture's own size, fitted once over the top). Before:
  `output/studio_cal/a8_s26/before/dd09/` (gen.py, geo.py, dress.py, L4).
- `playtest.yml`: the fire fountain's gain is checked on the status line.
- Installed 00:47 and baked; audit 0 errors / 11 warnings (as before), check_exits 0, check_drops 0; tests from
  assets_dev 4 of 4 (12 of 12, `output/studio_cal/a8_s26/run/dd09/c004703`).

## Session 27 (A8): D-89 identity, a temple grown in a tree

`reviews/DESIGN_GATING_AND_IDENTITY.md` 2.2 called DD-09 "a log cabin, not a temple grown in a tree" (bark on the
flat walls of rectangular rooms, brick barracks, a grass-floored box for the crown). Changed in the generator only
(`tools/geo.py` "D-89 identity" blocks, `tools/gen.py` `IDENTITY` and `ATMOSPHERE`, `tools/dress.py` two props and a
torch); the generator reproduced the installed L4 first (snapshot `output/studio_cal/a8_s27/before/dd09/`).

- **project.yml `identity:`** `{shape: temple, family: 7d22, seen: [the round hall of bark under its dome, the roots'
  sloping earth and hanging roots, the limbs and the crown open to the leaves and the sky]}`.
- **Hall of the Trunk round** (16 sides, `round_hall()`): four straight stretches where its doorways are (trunk door
  and ring stair south, barracks east, Chapel of Sap north, root stair west), three-piece arcs between them; a **bark
  dome** 1,344 high over 896 walls (`ceiling_points` in two rings). **Ring stair** bends rounded (`bend_radius` 512; its
  landing opening is path wall 20 now).
- **Roots in 7d22 earth**: the root cellar, both root alcoves, the pens and the sap store lose their square corners
  (`broken()`: a slanted cut with its middle pushed in, kept clear of doorways and things), sloping floors
  (`floor_points`, up to 64; the pens' cages stand level), earthen vaults (`ceiling_points`), **roots hanging through the
  roof** (six-sided `stalactites` in c2b: four in the cellar, two in the pens).
- **Barracks and guardroom** hollowed in the trunk: bark over a root-earth foot, heartwood roof (were ceb3s small green
  brick: its 11 audit warnings are gone), broken corners.
- **The limb walk** tapers from 640 to 448 and lies **open to the leaves and the sky**: a new theme `theme:branch`
  (the branch's bark to 256, leaves `eswamp` above, the ceiling `sky: true`, 768 up); its panels on outline edges 4
  (north) and 0 (south). The fruit rooms, Barkman's hollow and the limb stair: knotted (`rough`) bark, broken corners.
- **The crown** open to the sky in its middle (`ceiling_levels` 1,536 up, sky faces, leaves round it); bark to 384,
  leaves above; `atmosphere.yml` new: `open_sky` with D2's `xeendark1` (DD-11's pit's way).
- **Bands**: a root-earth foot (64) on every bark room, a dark-flag plinth (48) under the green stone chapels.
- Fruit sacks moved inward (were inside the cut corners and two arachnoids); the sap store's west torch at 0.6 (the cut
  shortened the wall and put it in the pens' doorway).
- Cave shape (`oymap metrics`, not required for a temple): floor uneven 0.077 -> 0.157, rough walls 0.057 -> 0.201,
  ceiling uneven 0.437 -> 0.465. Textures 40 of 45 (ceb3s out, eswamp in), 0 new.
- Installed, baked; audit **0 errors / 0 warnings**, check_exits 0, check_drops 0; tests **12/12** from assets_dev
  (`output/studio_cal/a8_s26/run/dd09/c011451`); stale bakes none for the map.
- **Name test** (things tour): before `output/studio_cal/a8_s27/dd09_before_sheet.jpg`, after (baked)
  `output/studio_cal/a8_s27/dd09_after_sheet.jpg` (unbaked preview `dd09_pre_sheet.jpg`). The arrival opens on bark and
  the round hall; the first fight room (barracks) is a hollow in the trunk; the signature rooms (limb walk, crown) read
  as a tree open to the sky.
- **Still weak:** the five gem alcoves are flat sap-earth panels (the design's "knots in the trunk" not built: a panel
  cannot sit on a rough wall, and a recess needs an opening of its own); the old temple's green-stone rooms upstairs
  (Shaalth's hall, the chapels, the tea room) are still boxes; bark on the dome still reads as stripes.

## Session 29 (A8): MP42 rebuild

Rebuilt on oymap merge point 42 (2026-11-22 ~02:20). The generator reproduced the L4 unchanged; the build changed
only the five chests: the style world's 7gt002 chest in place of MM6's ch1, same places, none moved. The three fitted
lectern tops (xnpbook) stand on the floor, so MP42's fitted underside adds no face here. Installed, baked; audit 0/0,
check_exits 0, check_drops 0; tests 4 of 4 (12 of 12, output/studio_cal/a8_s26/run/dd09/c021929). Chest pictures:
output/studio_cal/a8_s29/shots/dd09_chests.jpg (all four on the floor).

## Session 29 (A8, 2026-11-22): identity family exception

- `check_identity.py` measures 33 % of the map in 7d22: the bark is the world's own xdbark (A6, 35 %), 7d22's earth
  and roots below it (68 % together). Recorded as an exception in the tool (`EXCEPTIONS`), no texture forced.

## D-104 dungeon campfires (2026-11-26, agent:xeen-fb5-dungeon2)

`deco:cookfire`: the outdoor campfire's event (food 1-3 once, a small ring for a character with Perception), `once: true`, added by `level_generation/projects/xeen/common/campfires.py` (regen.py runs it after gen.py). Rebuilt, audit 0 errors, every playtest passing from the stage, installed and baked, MAW reserve rerun.
