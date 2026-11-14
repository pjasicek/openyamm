# Map Studio handoff

Kept current by the lead session; the user asked on 2026-11-13 for an update every 30 minutes while work runs. The
block "Status" below is rewritten each time; the rest changes when a fact changes.

Read this first, then `S3.md` from "Round three merged" to "WebAssembly" (the record of what was built and
measured, round by round), `REBUILD_PROCEDURE.md` (dungeons), `OUTDOOR_REBUILD_PROCEDURE.md` (outdoor maps),
`rounds/ROUND_FOUR.md` (how a round's common brief looks) and `openyamm-studio/README.md`. Older: the first part of
`S3.md`, `S2.md`, `S1.md`, `S0.md`, `PLAN.md`.

## Status (2026-11-14, 22:34)

**Merged:** the ninth merge (closed 14:41). **Tenth merge closed (17:19: shapes, slice, rewire pass; every playtest four of four, outdoor two of two; the user's copies reinstalled). It began (16:32):** code batch ten (`output/studio_obj7/`) in
`build/oymap` (before: `output/studio_lead/oymap_before_merge10`); 237 unit cases pass. It holds: `secret` on floor and
ceiling regions and plates, effects `secret`/`clear_secret` (d05's walkway, ceiling trace and sanctum plates pulse as
the original's); a beam `top` (level top over a raking underside) and the build's own cut of raking beams at a
ceiling level's flat top (d05's box: 5 pairs to 0 with no project change); the coplanar check at quarter, half and
three-quarter travel, pairs matched against the original (`--original`, default `map_stats.reference`), `--strict`
failing on new ones, a summary line (Hive 5 new, Lincoln 6 new, the rest 0); `liquid:`/`flow:` on any surface and a
warning for unflowing liquid textures; MM6's `lid: v` laid as the original's; message windows only for things meant
to be read, other texts on the status line held 2 s plus 1 s per 15 characters (at most 6, `seconds:` overrides);
`build --out` keeps the project's lock again; wall decorations' `at` and `floor_height`; `uneven`; `end_surface`
`fit: false`; `items[].gold` (gold heaps paid 0: the studio's fault). Lines applied by the lead: d05's secret regions,
plates and walkway (`output/studio_obj7/d05/d05_lines.diff`; backup `output/studio_cal/mm8_d05/m10_backup/`), XD-04's
three brew tops `liquid: liquid`, XD-01's nest step back to the status line (XD-02's agent told likewise). Checks:
`output/studio_lead/merge10/check.sh`.

**Uncommitted changes for the user to commit:** the 22 decoration bindings lifted by one unit (above); the status-text duration
(`evt.StatusText(text, seconds)`, 1 to 15 s, 2 s without; files under `game/events/`, the views' status loops, a unit
case; checked: unit suite unchanged, release scenarios pass; `output/studio_statustext/`). **Taken out:** the
eye-sector fix (a sweep found four regressions of one cause: floor lookups from the empty sector above an opening;
saved as `output/studio_eyefix/patch/eye_sector_fix_v1.patch`; the game binary rebuilt without it). Asked the user
whether to try a second version.

**Done this afternoon** (S3.md has each): the six dungeons got batch nine's lines (door edges and reveals, offsets,
lids, sprites, secret panels; the Lincoln's locker failure was a droid's corpse on the use key: playtest fixed, ten of
ten); outdoor round five (round halls, huts, porches, shrine, obelisk, signs, railings, the fort pit; buildings up,
totals down a hair from events the right forms add); the Abandoned Temple's round seven (the arrival view fixed in the
map, railings and stair edge); XD-02 and XD-03 second passes (rooms to the shipped median, no flicker, legibility);
XD-04's ring moved into the warden's strongbox. Coplanar pairs now: Forge, Control Center, XD-02, XD-03 0; Lincoln 6
(a studio limit); Hive 17 (12 the original's); d05 5 (batch ten).

**Decoration models flickering on the floor (16:21, the user's picture of XD-02's dirt mound):** 22 of the game's 3D
decoration models have an up-facing flat face at their lowest point (the mound `7dec11`, `plant37`, 20 MM9 props),
lying exactly on the floor. With the user's yes, each binding got `z_offset: 1` (`assets_dev/engine/models/
decorations.yml`, `indoor_decorations.yml`, `assets_dev/worlds/mm9/models/` both; files replaced, not edited in place;
22 added lines, uncommitted; the play roots updated the same way). Proven on the mound
(`output/studio_lead/flatbase/pair.png`). The scan is `output/studio_lead/flatbase/scan.py`; worth running after any
model install (a candidate for `tools/install_model.py`'s checks).
**The user's walk through XD-02's second pass:** "otherwise this dungeon is good"; stuck bats, a chest, unknown wood
things, a lever unreachable from the cart, a brake wheel without purpose, and no sense of why the party is there:
XD-02's third pass is running; lessons in REBUILD_PROCEDURE.md ("Say why the party is here", "Monsters where they can
fight", "Usable from where the party is") and NEXT_CODE_BATCH.md item 20.

**Finished 16:35: XD-02's third pass, the user's walk** (playtest 191 steps four of four on the tenth-merge binary;
installed in `xeen_root`): the bats' spawn out of the ore chute; chests at their kind's size facing the party; the
"wood things" (a pay rack and stool as bright slabs) now plank shelves; a riders' lever at every ride stop; the brake
wheel named, saying what changed and where to go; Mayor Gunther's errand in a window on arrival (a one-shot timer: a
load event's window never shows, a step event does not fire at the start); the Tallymaster a distinct boss. Lessons:
"a chest at its kind's size, front to the party"; "furniture reads as furniture or goes"; "every ride has a lever at
each stop on the rider's side"; "a new dungeon opens with its errand".
**Installed for the user's walks (16:35), `rebuilds_root`:** Warlord's Fortress, Control Center, the Hive, Darkmoor, the
Abandoned Temple, all built with the tenth-merge studio (commands in `output/studio_play/PLAY.md`).

**The user's acceptance walks:** the Forge, Warlord's Fortress ("plays exactly the same", 16:33) and Control Center
("good", 16:39) accepted; the Hive walked with three points, all fixed in its round seven (17:12: the button panel whole, the alcoves' divider and post, the keg room entered up a ramp; coplanar 0 new; 97.7 %; reinstalled); Darkmoor not yet.

**Finished 17:09: the Mad Necromancer's Lab (MM8 d20, held out) in one round:** 99.7 % (shape 99.8, textures 99.6);
playtest 119 steps four of four; every event as the original's but the exit's transition picture; coplanar 0; a wall
that would score higher not built (the original's two stray faces the game ignores); installed in `rebuilds_root`
(`calib_mm8_d20.blv`, map row 9720). Gaps: floor mist (the game has the scene `mist` block: a studio word is
missing), the exit picture, ring kerbs, small furniture, lintel textures. Within the bands: awaits the user's walk.

**Finished 17:14: XD-05 the orcs' drum caves from its brief** (25 rooms; bigger rooms 1.94 M, 60th percentile; walks of 96
and 47 steps four of four; three drums that burn, drum sound layers that fall silent, palisade, Tam in his pit,
the Drum Hall with its scaffold, chimney and ledge; one texture family, MM8's Ogre Fortress, 11 textures generated;
arrival errand; coplanar 0; installed in `xeen_root`). The project is written by `output/studio_cal/xd05/tools/gen.py`
(edit there, run `v.sh`). S3's five Xeen dungeons are built.

**Finished 17:14: the Temple of the Moon's round seven** (95.9 to 97.5 %: within the band with the original's shapes:
cave walls straight on the outlines, the south cavern's roof down to the original's walls in four rooms of one
space, the cave mouth, the stair under its vault; playtest 213 steps four of four; 27 of 27 events; coplanar 0 new;
installed in `rebuilds_root`). Gaps in its NOTES.md (pillar panels, octagonal door frame, leaning walls).

**Finished 17:36: Goblinwatch (MM6 6d01, held out):** 99.2 % (shape 99.2, textures 99.3); playtest 141 steps four of four
from the landing to the exit into New Sorpigal through every mechanism (the console's 16 switches, the gates, the
vault, the shaft); 50 of 53 events as the original's; coplanar 0; installed in `rebuilds_root` (`cal6d01.blv`). Gaps
in its NOTES.md (floor holes need a level upper room, steep cave banks, switches on raking tops, cave point budgets).
**S3's maps are all built and within the bands; acceptance rests on the user's walks.**

**The user's walks (19:10):** the Temple of the Moon "good, authentic" (its arrival faced 90 degrees off: the lead set
`start.facing: 56` from Emerald Island's entrance event (direction 320 of 2048) and reinstalled; arrival picture
beside the original's: `output/studio_cal/mm7_7d06/arrival/pair.png`); Castle Darkmoor "fine I guess" (walked in part:
too big to go through); the Mad Necromancer's Lab good but for a floor that should drop the party and its trap
plates without the secret flag (its round two running); Goblinwatch good but for the console's switches (on the
sloping top in the original) and a light outline round a door (a code-and-project agent running).

**19:15:** the user accepts the Hive on its round-seven fixes without walking it again ("if you fixed it then I'm fine
with it"); the Lab's round two fixed his two points (the well is a way down, the three trap plates secret; reinstalled);
XD-05 walked ("otherwise good": a lamp in the air, stalactites, keyhole blocks and floor torches at the back gate, a
square tunnel turn): its second pass running. S3 now waits on: Goblinwatch's console and door fix, XD-05's pass.

**Eleventh merge (19:44):** the Goblinwatch fix (`output/studio_obj8/`; binary before
`output/studio_lead/oymap_before_merge11`; 239 unit cases): `switches[].side: top` on a block's level or sloping top
(Goblinwatch's 16 console switches on its raking top, as the original's); the reveal strip in front of a shut leaf
standing 2 back now takes the leaf's own picture (the bright line round the Goblinwatch locker doors, and every such
door in every map). The user's copies reinstalled. Closed 20:30: shapes, slice, rewire pass; every playtest four of four (outdoor two of two), 21 walks.

**Twelfth merge (20:58):** outdoor code batch eight (`output/studio_s4i/`; binary before
`output/studio_lead/oymap_before_merge12`; 243 unit cases): `structures[].same_event_as`, `signs[].offset`, `plinth`,
windlass well `frame`s, bay texture names without a digit, a warning for negative `raise`, spawn areas seeded from
their own text, the recess message. Not built: A-frames, cave mouths, square fountains, a hole in a platform, the
Sanctum's roof, arcades, rim peaks. Its project lines (`output/studio_s4i/scripts/proof.py`) sent to Harmondale's
round six; the S4 agents told the new words. Checks closed: shapes, slice, rewire and every playtest pass.

**Finished 21:07: Shadowspire's first rebuild (held out): 80.01 % (79.77 without the rim), outside the band**; walk 221
steps two of two; events 100; coplanar 0; not installed. Ground scores 3 %: the map uses its own tile sets (grey
dust, grey stone, tar) and rows, which the studio cannot lay; with ground scored like the rest about 90.6 %. Mist and
sky theme have no word; the east's sheer columns, roof details and some houses not reached. Outdoor code batch nine
takes the ground sets, mist and sky; Shadowspire's second round follows.

**Finished 21:08: Harmondale's round six:** 89.18 to 89.92 % (86.20 to 86.91 without the rim), 0.08 under the band, with
the original's shapes only (heights in 32s, the spire knoll's rings, the outlet stream, roads, batch eight's lines,
the Mind guild and Kern Residence redrawn); walk 69 steps two of two; installed in `rebuilds_root`. The measure
counts the footbridge's invisible ceiling as its top (about 0.2): sent to outdoor batch nine with the silent building
step events.

**Finished 21:12: New Sorpigal (MM6 oute3, held out): 92.8 % (93.2 without the rim), within the band;** walk 140 steps
three of three (every shop, the hill's temple and guilds, the docks and the Odyssey, Goblinwatch's door, the west
edge); installed in `rebuilds_root` (`calib_newsorpigal.odm`, rows 9603). Gaps: upper storeys on posts, the bridge's
goblin plate, the gate's round pillars and mirrored sign, hanging shop signs, panels with their own events. Road
tiles of MM7 laid at its jogs (sent to outdoor batch nine).

**Finished 21:25: X1 Vertigo Meadows from its design** (`devdocs/xeen/briefs/x1/L4/`, `xeen_x1.odm`, row 9130; generated by
`output/studio_cal/x1/tools/gen.py`): Vertigo walled with 14 services and 18 homes, the creek and south bank, the
meadows, the Witch Tower landmark, devices, orc camps, entrances to XD-01 to XD-05 leading into the built dungeons
(XD-04 with Old Valia's key), edges to X3 and X7; Gunther's errand on arrival; walk 305 steps, two of two; installed
in `xeen_root`. Weak: the dungeon doorways are lone dirt frames on mounds (no cave mouth: outdoor batch nine's cave
mouth word would answer it); buildings bigger and sparser than shipped; the rim is a cliff over water. Next: point
XD-01 to XD-05's exits back at X1.
**New Sorpigal round two** (the user's 21 places) running.

**Thirteenth merge (21:35):** outdoor code batch nine (`output/studio_s4j/`; before `oymap_before_merge13`; 251 unit
cases): `tile_sets` and ground materials naming any of the world's tile sets (12 shipped maps use their own),
liquids in ground sets (tar), `atmosphere.yml` `mist` (checked by the game's parser) and `sky_theme` (install writes
the root's `sky.yml` row by rename), MM6 road jogs as round bends, `compare` ignoring invisible faces as tops and
reading transition corners as the map's plain ground, building triggers refused, height points no longer adding up,
untitled doors. **It also changed `tools/terrain_materials.py`** (a tile without art takes coverage from its
`shape_from` tile): a tracked repository file, for the user to commit. Shadowspire got its lines (backup
`output/studio_cal/mm8_out06/m13_backup/`): 80.0 to 91.2 % on the batch's copy, ground 3.3 to 93.3; installed in
`rebuilds_root` (`calib_shadowspire.odm`, sky theme necrotic). Checks closed: shapes, slice, rewire and every playtest pass.

**Finished 21:54: New Sorpigal round two, the user's 21 places:** 92.8 to 93.5 % (93.8 without the rim); buildings 92.4
to 95.9; every place redrawn from the original's faces (the tavern's porch, smithy, bank, stable, training grounds,
Buccaneers' Lair, the keep's loggia, temple porch, guild, Gharik's house, the Shrine of Luck with its event, the
overhanging west houses, Blades' End, the Town Hall's paved court, the Abandoned Temple's mouth, Goblinwatch's keep
with towers and spire); walk two of two; reinstalled. Missing words in its NOTES.md "Round two" (porch floor from
the land, one-wall eaves, posts on chosen walls, a partial sill, two-width recesses, `doors[].same_event_as`).
**Vertigo's by-eye review** (`output/studio_cal/x1/review/REVIEW.md`, eleven shipped towns) done; its pass running.

**Outdoor installs need their terrain materials:** after `oymap install` of an outdoor map into a play root, run
`python3 openyamm-studio/calibration/outdoor_materials.py <project> --root <root> --build <build>`, or the game
refuses to load it (the lead's Shadowspire install missed it; the user hit "Game exited before loading").

**Finished 22:14: Vertigo pass two** (the user's walk and the by-eye review; generators `output/studio_cal/x1/tools/town.py`
and `dress.py` beside `gen.py`; backup `output/studio_cal/x1/pass2_backup/`): grass town floor, seven house shapes in
mixed materials turned 4-25 degrees around lanes and yards, a path to every door and a check refusing roads under
buildings, trees, flowers, wells, stalls, fences and props, townsfolk 12 to 23, a crenellated wall with 8 round towers
and four gatehouses, a farm belt, whole road joins, monster camps (40 markers in 14 camps, groups of 3-5, gates
clear), the dead forest 90 to 230 trees, a water ramp down the rim; walk 388 steps two of two; installed in
`xeen_root`. Before/after/shipped: `output/studio_cal/x1/pass2/compare_before_after_shipped.jpg`. Missing words: a real
waterfall, spray, a gate arch, a battered wall base, battlements on `kind: wall`, fences, carts, more than three ground
kinds. Still unlike shipped: browner core, one tree kind, no red accent, the waterfall a dark slab.

**Finished 22:21: Shadowspire round two, the user's 10 places:** 91.21 to 91.52 % (91.25 without the rim), buildings
80.3 to 82.3; the shops redrawn from the original's faces; z-fighting pairs 904 to 36 (the original has 7; the rest
are studio drawing defects: railing corners, signs 1 unit off their boards, gable eaves at the ridge); walk two of
two; installed with terrain materials. Defects and words in its NOTES.md "Round two" and code list item 10.

**Outdoor feature survey (22:44, the user's request: "the tool right and capable"):** ten agents survey all 42 shipped
outdoor maps for places the studio cannot say yet (class a: says it today, b: needs a word, defined; c: needs engine
work). The lead merges their words into one catalog on `rounds/NEXT_CODE_BATCH.md`, ranked by how many maps need
each, and the next code batches take it from the top.

**Finished 22:54: Shadowspire round three:** 91.52 to 92.10 % (91.83 without the rim), buildings 82.3 to 86.1; Yaardrake's
Cave (the shell taken whole, the land set at the original's nodes) and the Mad Necromancer's Lab's passage, hall and
approach (the user's two "dragon cave" poses stand there); Caverhill Hall and the Blood Bank without Ravenshore's kit
doors; the Assassin's School's pyramid roof; the pier's ramp and gate frame; walk 233 steps two of two, entering the
cave; installed. Its method is now "Buildings built into the terrain" in OUTDOOR_REBUILD_PROCEDURE.md, and the word
`kind: cave_mouth` code list item 14.

**Survey done (22:58):** all ten surveyors reported (`output/studio_survey/<map>/SURVEY.md`, `rebuilt/SURVEY.md`). Most
common gaps: dungeon entrances built into the terrain (cave mounds and shells, hollows cut into mountains), ruins,
invisible plates and barriers, MM6 fountain basins, portals, domes, arched bridges, tents, battered walls, scatter
groups for season swaps, atmosphere flags (underwater, no terrain). No new engine needs beyond the known outdoor
SetFacetBit click; data to check: outd3 events 90/91 without handlers. Lead's next steps: merge batch ten when it
reports; start the catalog's first code batch; Vertigo pass three after `cave_mouth`.

**Finished 22:59: Xeen exits to Vertigo:** every XD-01..XD-05 exit onto X1 now arrives 400 in front of its X1 door facing
away (XD-01 has two: the street gate and the culvert); exits to maps not built yet (XD-02's deep mine and X4 adit,
XD-03's deep cart, XD-04's Cloudreach, XD-05's X7 slopes) still go to Emerald Island; walks four of four (dungeons),
X1 two of two (391 steps, with a round trip through XD-05); all six reinstalled in `xeen_root`.

**Catalog done (23:07):** `rounds/OUTDOOR_FEATURE_CATALOG.md` ranks the survey's words by maps needing them (outdoor leave
trigger 16, fountain outlines 15, `cave_mouth` 15, arched heads 10, invisible faces 10, arched bridges 10, atmosphere
flags 10, ...) and orders code batches O-A..O-G. Lead's choice: O-B (ways in: `cave_mouth`, hatch, arched heads, door
dressing) goes first after batch ten merges, because the user named the dragon cave as the calibration case and
Vertigo's doorways wait on it; O-A next. Data defect found: 7out04 event 504 bound on `ClL1_W` with no handler
(MMerge's Dimension Door); outd3 events 90/91 are fine (`grep -a`).

**Finished 23:12: Harmondale round seven** (round two after batch nine): 89.92 to **90.23 %, inside the band** (87.22 without
the rim); buildings 87.6 to 89.7, every changed building redrawn from the original's faces (footbridge level at 592 on
no piers: the sag is a missing word; town houses, tavern, bank with its sign, Otto's, temple, guild wings); z-fighting
273 to 50 (the original 65; 43 are batch ten's sign defect); walk two of two; installed. Missing words in its NOTES.md.

**The user's priority (2026-11-13):** an outdoor map is judged by its town's feel: asymmetry, one or two house
styles, natural paths, density, services placed sensibly, monsters guarding chests and entrances, props, a pedestal,
small hills. The town-feel study turns it into measured ranges and a checker that runs before the user walks a map.

**Finished 23:37: town-feel study:** `devdocs/map_studio/TOWN_FEEL.md` (ranges from 13 shipped towns) and
`openyamm-studio/calibration/town_feel.py <map> --world <w> [--assets <root>]` (59 figures, flags those outside).
It corrects the by-eye review: shipped houses face the compass axes (0.77-1.0 of doors); irregularity comes from
placement, setbacks, plot sizes and short road runs with offset junctions, not from turning houses. Vertigo: 7
figures outside (doors on axes 0.27, odd road angles, a 9230 straight street, 43 monster groups) plus a flat town
and the largest, most even groups; New Sorpigal 3, Harmondale 4, Shadowspire 5 outside. Vertigo pass three applies
it after the density round and `cave_mouth`.

**Finished 23:42: Vertigo density round:** trees measured on six shipped maps (even, Clark-Evans R 1.4-1.8, nearest
tree 1.6-2.7 cells, never `clusters`); dead forest 139 trees evenly spread and mixed; wilds given relief (Vertigo read
empty because flat) and small places; the west and north roads and the creek run to the map edge; town core in
the shipped density range, outskirts still sparse. Walk 391 steps two of two; installed. Its measured sections are in
OUTDOOR_REBUILD_PROCEDURE.md; scatter words are code list item 16.

**Overnight plan (the user away until morning, 23:44; his words: "progress with the plan for the studio, deliberately;
you need to gauge when it is good to continue, then continue with the next phases; note what you want from me").**
The lead runs, in order, each step only when the previous one meets its gate:
1. Merge batch ten. Gate: all unit cases, every playtest (merge check), scores unchanged or better, the outdoor
   coplanar check matching the original's counts on the four rebuilds.
2. Catalog batch O-B (ways in: `cave_mouth`, hatch, arched heads, door dressing), then O-A (leave trigger, atmosphere
   flags, `when_flying`, invisible faces, scatter extras and item 16's scatter words, the 7out04 504 data fix), then
   O-C (fountains, arched bridges, liquid faces, culvert). Gate per batch: the same as 1, plus each new word used on a
   shipped place it was defined from, measured against the original by picture and `compare` of that spot.
3. Vertigo pass three after O-B: `cave_mouth` doorways, the town-feel checker's figures inside the shipped ranges,
   a by-eye review against shipped towns. Gate for "good to continue": `town_feel.py` all inside (or argued), the
   reviewer's verdict that it reads like a shipped town, the walk two of two.
4. The rebuilds' town-feel figures (New Sorpigal 3, Harmondale 4, Shadowspire 5 outside) where they differ from their
   originals by the rebuild's fault.
5. The Xeen design reviews: merge their findings into a proposal list for the user (not applied to the design
   documents without him).
For the user in the morning: `devdocs/map_studio/FOR_THE_USER.md`.

**Xeen design reviews done (23:57):** `devdocs/xeen/reviews/{SCALE_AND_DENSITY,STORY_AND_ATMOSPHERE,COMBAT_AND_PROGRESSION}.md`;
their decisions are on `FOR_THE_USER.md` (not applied to the design documents).

**Fourteenth merge (2026-11-14 00:49):** outdoor code batch ten (`output/studio_s4k/`; before `oymap_before_merge14`; 259
unit cases): the outdoor coplanar check in `build` and `audit` (matching `coplanar_odm.py`), the studio's own
z-fighting sources fixed (mitred railings, signs' boards hidden under their pictures, gable beams, stall sills,
stair treads in `top`), `doors[].same_event_as`, `porches[].floor_from: land`, `post_walls`, `kind: fence`,
`kind: waterfall` (FlowDown sheet, no spray). Scores unchanged; Shadowspire's pairs 36 to 1 (the original's boat).
Gate met for the studio's part; the remaining pairs are the projects' own (New Sorpigal 58, Harmondale 231,
Ravenshore 205, X1 31), which the cleanup takes. Checks closed: slice, rewire and every playtest pass; the shapes walk passed but its picture tour failed with "SDL_Init failed: The video driver did not add any displays" (the desktop display is off overnight: desktop runs and screenshots cannot start until it is back; headless walks are unaffected).

**Finished 01:14: rebuild cleanup** (z-fighting and town feel; NOTES.md "Cleanup" sections): fighting pairs New Sorpigal
58 to 2 (original 0), Harmondale 7 to 6 (65), Ravenshore 205 to 46 (7; 23 in the north-west block, which needs
redrawing from the original's faces); town-feel figures outside only by the rebuild's fault fixed (New Sorpigal's
longest street and mirror share, Harmondale's groups in town and wells; Harmondale's flat share 0.58 to 0.70 against
the original's 0.78). Scores 93.52 / 90.23 / 92.18; walks two of two; installed; the desktop load check could not
run (no display). Words: a level terrace area, eaves per wall, a recess under a hanging part.
Next for the lead: Ravenshore's north-west block redraw when pictures are possible again.

**Fifteenth merge (01:35):** catalog batch O-B, ways in (`output/studio_s4l/`; before `oymap_before_merge15`; 267 unit
cases): `kind: cave_mouth` (shell, tunnel to one dark event face, land set to floor and crest; `free`, `mouth.form:
door`), `kind: hatch` (wedge, pit), `arch: round | pointed` on doorways, doors, windows and gates, door dressing
(`leaves: 2`, `hood`, `frame` with portcullis, gabled portico). Gated on shipped places by compare and faces (no
display, so no pictures): Yaardrake's Cave as `cave_mouth` overlap 0.94, heights exact, map 92.10 to 92.07 against
the whole-model import (the project keeps the import); Emerald's dragon cave weaker (0.76: no word for a mouth set
back behind a ledge); Chain of Fire 0.94, Balthazar's pit 1.0. Projects build identical bytes; walks two of two.
Pictures still to take: `output/studio_s4l/` lists them. Checks closed: slice, rewire and every playtest pass; the shapes picture tour failed for want of a display.
Next: O-A (running), then O-C; Vertigo pass three when the display is back (it needs the by-eye review).

**Batch O-A done (02:17), to merge into `build/` together with O-C (the source tree is shared: building `build/` now would take O-C's half-made edits)** (`output/studio_s4m/`; 273 unit cases):
outdoor leave trigger, `atmosphere.flags` with raw bits, outdoor `ceiling`, `footsteps`, `when_flying`, invisible
platforms and step plates, `kind: barrier`, `kerb_invisible`, `ethereal`, scatter `group`/`event`/`on: water`/
`height`/`spacing_group`/`kinds`/`close_share`/`edge_thin` (clusters keep a cell), `heights.terraces[]`. Gated on
shipped places (the Planes' flags exact, Silver Cove's event 209, Emerald's tutorial plates exact, Outbound Pass's
barriers, Erathia's forest window R 1.18 against 1.20). Rebuilds identical bytes; X1's 15 clustered entries moved;
walks two of two. Data fix for the user: `output/studio_s4m/data_fix_7out04_504.md`.

**Sixteenth merge (03:02):** batches O-A and O-C together (before `oymap_before_merge16`; 281 unit cases). O-C
(`output/studio_s4n/`): `fountain.outline` (polygon or `size` rectangle, `sides: 3`, `pillar: 0`, `tiers` with
`tier_shape`, `pillar_shape: box` with `flow: down`), `bridge.arches` (round and segment), sagging decks with rope
rails and towers, liquid faces on any part (`{texture, liquid, flow}`, bits as the originals), `kind: culvert`,
`mouth.setback`/`ledge`, `arch: segment`. Gated: outa1's HF fountain overlap 1.0, oute2's fountain 1.0, the 7out04
viaduct's arches exact, Harmondale's footbridge 0.85, culvert 0.66, Emerald's cave still 0.763 (its rounded shell
outline is the gap). Projects: only the fluid bit now set on well and fountain water; scores unchanged; walks two of
two. Checks closed: slice, rewire and every playtest pass; the shapes picture tour failed for want of a display.

**Seventeenth merge (03:53):** batch O-D (`output/studio_s4o/`; before `oymap_before_merge17`; 288 unit cases):
`roof: dome` with `dome_rings` and mushroom caps, `parts[].batter`/`batter_height`/`batter_walls`, `buttresses`,
wall `batter` and `top: follow`, roofs to the ground with doors cut into the roof, building `steps` and `stair`
(ramps), round and stepped platforms, `ruin` (bays to their own heights, gaps, bare rafters), `eaves_walls`, recess
undersides cut. Gated: the Plane of Fire guard tower's batter tops 1.000, its cone hut's door exact, Dragonsand's
pyramid tops 1.000, Dagger Wound's ramp 0.998, Sweet Water's burnt tavern footprint 0.948; Harmondale's town hall
pairs 4 to 0 with `eaves_walls` on a copy. Only Shadowspire's build changes (the recess fix); scores unchanged;
walks two of two. Not built: non-convex outlines. Checks closed: slice, rewire and every playtest pass; the shapes picture tour failed for want of a display.

**Batch O-E done (04:25), to merge into `build/` together with O-F (the shared source tree holds O-F's edits in progress)** (`output/studio_s4p/`; 296 unit cases):
`heights.spires[]`, `heights.peaks[]`, `heights.cuts[]` with ramps, `terraces[].steps` and `ramps`, `ridges[].closed`,
`against: slope`, `skirt`. Gated: Avlee's Baa spires 43 of 43 nodes exact, Shadowspire east 6 of 6, Blackshire's trench
window 1.000, Free Haven's Moon slot exact, Castle Ironfist's pit 0.995, New Sorpigal's crater 26 of 27, Mount
Nighon's Fire Guild land exact; the Plane of Water peak field statistically close (76 tops against 81). Projects
build identical bytes; walks two of two.

**Eighteenth merge (05:14):** batches O-E and O-F together (before `oymap_before_merge18`; 305 unit cases). O-F
(`output/studio_s4q/`): `kind: portal`, `kind: arch` (beam or ribs to a hub), `stone_ring`/`trilithon`, `walkway`
(heights per point, piers, end frames with steps), `deck` with plots `on:` it, `tent`, `arcade`, porch
`form: portico` and round columns. Gated: all seven planes' portal rings within 3.5 units on average, Barrow Downs'
walkway 99 % within 32, Castle Navan's arcade 99.8 %, Pierpont's deck 0.79, Alvar's tents 0.84, Bracada's arch 0.71,
Avlee's stonehenge 0.50, Kriegspire's portico 0.89. Builds identical; walks two of two. The catalog's batches O-A to
O-F are all in; O-G words are taken when a map needs them. Checks closed: slice, rewire and every playtest pass; the shapes picture tour failed for want of a display.
Pictures of every gate are still to take (lists in each batch's scratch); `FOR_THE_USER.md` item 7.

**Finished 05:55: Vertigo pass three (by the numbers):** `town_feel.py` 7 figures outside to 0 (houses on compass axes,
offset junctions and jogs, longest straight 9230 to 3584, a terrace at 1280 with shops `against: slope`, tavern by
the arrival, groups of 1-3 guarding chests and doors, town clear 4,500 round its doors); dungeon doors as
`cave_mouth` (mine, orc cave, Temple of Yak), `hatch` (shaft), `culvert`, a pointed arch (tower), every click face
where it was; `kind: waterfall`; battered walls with `top: follow`; fences; one scatter entry per stand (dead forest
R 1.45 against Deyja's 1.47); z-fighting 31 to 3; walk 395 steps two of two; installed. The by-eye review and its
pictures wait for the display (list in its NOTES.md "Pass three"). "Good to continue" is met by the numbers; by eye
not yet judged.
Next for the lead when the display is back: the gate pictures of batches O-A..O-F, Vertigo's by-eye review, the
Ravenshore north-west block redraw; until then the user's Xeen decisions (`FOR_THE_USER.md`) gate further Xeen maps.

**Finished 06:06: Ravenshore north-west block:** redrawn from the original's faces (Caori's twelve-sided tower, Keen
Edge's three meeting boxes with its door at the original's place, the upper floor's cut corner); the terrace steps,
eaves at joins (`eaves_walls`), the Dancing Ogre's band, the north-east lean-to and the council ramp fixed; fighting
pairs 46 to 3 (original 7; the 3 shared or as the original); 92.18 to 92.19 %; walk two of two; installed. Words:
eaves along part of a wall, one roof over two parts, `parapet_walls`.
All four outdoor rebuilds now have no more fighting pairs than their originals except New Sorpigal (2 against 0).

**Nineteenth merge (06:37):** concave outline parts under one roof (largest convex pieces, highest roof wins, valleys
and gable meets), `eaves_walls` stretches with their own `eaves`, `parapet_walls` with `parapet_top` (`output/studio_s4r/`;
before `oymap_before_merge19`; 309 unit cases). Gated on copies: Keen Edge's L roof tops 0.670 to 0.929, its parapet
1.000, Ravenshore's wings' undersides 0.749 to 0.889, Blooded Daggers' notch exact, Harmondale's tavern height
difference 8.8 to 2.6. Builds identical; walks two of two. Checks closed: slice, rewire and every playtest pass; the shapes picture tour failed (display off at the time).

**Finished 06:46: roof words in the rebuilds:** Ravenshore 92.20 % (Keen Edge's L roof and parapet, the rich houses'
wings), Shadowspire 92.11 % (Blooded Daggers' notch, Black Company's U roof), Harmondale 90.23 % (the tavern's L gable,
the town hall's eaves: pairs 6 to 2), New Sorpigal 93.53 % (the Knife Shoppe's and Savings House's roofs over their
porches); walks two of two; installed.
**Waiting for the display and the user:** the by-eye checks (gate pictures of batches O-A..O-F and the roof words,
Vertigo's pass three review); the user's Xeen design decisions (`FOR_THE_USER.md`) before more Xeen maps.

**Vertigo pass three by eye (07:10):** "not yet" (`output/studio_cal/x1/review/REVIEW_PASS3.md`): a raw terrace slope
burying the north-row shops, a flat-slab waterfall below a straight canal, a free-standing culvert box, slab stalls
reading as broken buildings, one repeating wall texture with flat gates, identical mossy cave mounds, straight soil
rectangles. Otherwise close to a shipped MM7 town. Pass four takes those seven.

**XD-01 (07:28):** merge 19's playtests failed XD-01 once in four (rats still leaving their pens: six sweeps now), then
once in eight on a keg 68 inside the stash doorway that caught the party one walk in six; the keg moved to the
stash's far corner (map fix), playtest eight of eight; reinstalled in `xeen_root`. Audit check for it: code list 19.

**Finished 07:39: Vertigo pass four** (the by-eye review's seven): a 512 terrace step with a fieldstone retaining wall
and full steps, a fanned waterfall between rock crags with a meandering outflow, the culvert in a quay wall, stalls
with hip roofs, light dressed-stone walls with coursed towers, red cones, round-arched gates and the creek side
open, rock cave mouths dressed with torches, timber, skulls and flags in rising hills, soil only on paths; town_feel
all inside; walk 387 steps two of two; installed. Before/after: `output/studio_cal/x1/review/pass4/compare_*.jpg`.
The lead looked: clearly better; shown to the user. Still: the rim cliff an earth slope, smooth cave shells, brown
street bands (how roads are laid), no foam (missing words in its NOTES.md).

**Indoor batch eleven done (07:55), to merge with the picture fixes** (the shared source tree holds their edits;
`output/studio_s4s/`; 313 unit cases): indoor `mist` (checked by the game's parser; d20's overlay reproduced key for
key), `neighbours[].screen`, effect `leave`, `player_bit` effects and condition, `shake`, `give_item: {level, kind}`,
`objects.yml` `relations`. All 20 projects build identical bytes; every playtest passes. Lines for projects to adopt
the words are in its report (d20/d05 screens, d20/cd2 mist, XD-02/03 relations, the Forge's player bit, the
Fortress's random axe).

**Twentieth merge (08:03):** indoor batch eleven and the picture fixes (`output/studio_s4t/`; before
`oymap_before_merge20`; 313 unit cases). Fixes: cave_mouth keeps the land and has a rounded hood (Emerald wrong to
close), doorway `frame_width`/`frame_height`/`passage` (DunEntC3 wrong to close), tiered roofs' closing top takes
`textures.top` (the Plane of Fire hut matches), bridge `tower` texture (segment span matches); the other wrong gates
were the gate projects' simplifications (pyramid now matches; lava monument, ruin, Fire Guild, Ogre Fortress close).
Shadowspire's teal roof (Supple Leather, building_38) was NOT the roof words' doing: present since the first measured
pass; fixed in the project (92.12 %), reinstalled. Not done: ribbed domes, the arch's ring hub, tent doors and trim,
the HF fountain's island. Checks closed: shapes (with pictures), slice, rewire and, rerun on the game rebuilt at 08:38, all 25 playtests pass.

**Finished 08:06: Castle Ironfist rebuilt fresh** (`mm6_outd3`, `calib_ironfist.odm`, row 9604) as the test of the new
words: 83.4 to **93.5 %** (93.8 without the rim) in about seven rounds; buildings 52.7 to 90.7, events 68.1 to 94.2;
walk 128 steps two of two; no faces in one plane (the original none); installed. The terraces with ramps, spires,
gate arches, the arched bridge, fountain outlines, step plates and the Seer's star deck all did their job. Play gap:
the castle roof (King's Library, two tower doors) is unreachable: no word for an inner stair to a roof. Missing
words with repros: code list item 20.

**Finished 08:11: Erathia rebuilt fresh** (`mm7_7out03`, `calib_erathia.odm`, row 9703): 75.0 to **88.8 %**, short of the
band; buildings 38 to 88, events 53 to 88; heights 78 (43 % of the error beside sheer drops of 1200 or more, which
cliffs, terraces and cuts moved only by tenths); walk 39 steps two of two; 6 coplanar pairs over the original's 3, all
studio defects (diagonal sign arms, a door cut into a gable); installed. Words and defects: code list item 21.

**Batch O-H done (09:03), to merge after merge 20's playtest rerun** (`output/studio_s4u/`; 321 unit cases):
`heights.nodes[]` (node heights given one by one, last), part `stair` with `run` up to a flat roof (Ironfist's library
reached on foot), walls to 4096 thick with gates taller than the wall and `passage_along`, a box part's `court`,
`hint_shared` (and building `hint` now works; tents take a hint), `doors[].recess` and arched porch recesses, platform
`holes` (basins, flush plates), wall signs with `title`/`house`, and the defects (diagonal sign arms, doors on gables,
deck posts, install's way back). On copies Erathia 88.8 to 91.3 % (most from `heights.nodes`: 1505 nodes beside the
sheer drops, 88.8 to 90.7; `hint_shared` +0.6).
**Lead's ruling on `heights.nodes`:** it takes the original's heights node by node, like `kind: model` takes a model
whole; a rebuild using it reports its score with and without it, and NOTES.md names the nodes taken. It answers a
real limit (the grid cannot hold land that changes from one node to the next), measured, not a shortcut.

**Finished 09:17: the per-building shot tool and Castle Ironfist round two:** `openyamm-studio/calibration/building_shots.py`
(every building matched to the original's models, a view per door and per side at eye height and raised, cameras
moved clear of models, decorations and land, one tour per map, side-by-side pairs and contact sheets; about 35
minutes for both maps). Ironfist 93.5 to **94.0 %**, buildings 90.7 to 93.1 (the castle walls' posts, the guilds'
canopy, Eye of Newt's stone, the vaulted temples, HouseR2S, the stables, the south Temple Baa, Corlagon's door, the
Seer's walls and ledge, Snergle's hill, the docks on piers, Fine Blades, inn signs); the user's six places done except
the gate passage (words) and the roof stair (O-H). Walk three of four (the first failed returning from Bootleg Bay,
2000.2 from the assert's point at radius 2000). New words: shorter window bays, sloping beams, recesses running into
the next part, end-sloped vaults.

**Twenty-first merge (09:29):** batch O-H (before `oymap_before_merge21`; 321 unit cases). Checks closed: shapes, slice, rewire and every
playtest pass except XD-04's main playtest (0 of 4 on its X1 arrival assert), which Vertigo pass five was editing
at the same moment; after pass five both XD-04 playtests pass four of four.

**Finished 09:43: Castle Ironfist round three:** the castle roof reached on foot by the inner ramp (King's Library and
both tower doors opened in the walk), the gate block as a thick wall with a segment arch and the passage steps to
the Throne Room, the stables board with its event, flush pad plates; 93.96 to 93.91 % (buildings 93.1 to 92.7: the
honest shapes miss the original's heights: the ramp is inside where the original's runs outside along the north
wall, the gate top 2656 against 2720-2752; kept by the rule); walk 152 steps five of five (the Bootleg Bay return
asserts its real landing line); 0 pairs; installed. Words left: door sills above the floor, an outside ramp along a
wall, several boards with events on one post, recesses into the next part, end-sloped vaults; a defect: a short
outline face ignores its `walls` bays (repro `output/studio_cal/mm6_outd3/repro/recess_outline_bays/`).

**The user walked Vertigo pass four:** "much better"; five points (a dungeon door that does not read as one and looks ugly, the waterfall, the Witch Tower's door on the approach side, dragonflies in the swamp, guards inside the walls) go to pass five, with general rules for the procedure.

**Finished 10:24: Vertigo pass five** (the user's five points): Joe's door now in a timber warehouse's wall with a dark
stone-framed opening, torches and casks (click face unchanged); torches at the other dungeon doors; the waterfall an
upright sheet between rock outcrops (built as a building in the water: `kind: waterfall`'s faults are code list 22);
the Witch Tower's door on its north (approach) side, XD-04's exit arriving 400 north of it (XD-04 playtests four of
four each, reinstalled; merge 21's XD-04 failure was this edit in flight); dragonflies over swamp, creek and pond,
orcs only at camps, skeletons in the dead forest; 13 guards (pairs at the three gates and the bridge, five in the
streets). town_feel all inside; walk 388 steps two of two; installed. Three measured sections added to
OUTDOOR_REBUILD_PROCEDURE.md (dungeon entrances, monsters by habitat, guards in towns).

**The user walked Vertigo pass five (10:58):** few monster packs; the waterfall a water box with a dirt strip between
creek and lip, between blocky rock boxes (studio word: the code batch rebuilds it, then Vertigo gets it); the town
perhaps too stretched beyond the walls (to be measured). Lead's next steps: merge the waterfall batch, put the word
into Vertigo; the user's Xeen decisions (`FOR_THE_USER.md`) gate the next stage.

**Finished 11:03: Vertigo pass six:** `town_feel.py` now counts monsters (it had read spawn indices 4-12 as dice groups:
fixed, shipped ranges recomputed) and town spread, with a `--start` profile for start maps (`TOWN_FEEL.md` 5b).
X1 had been below every start map in monsters (134, 0.08 along roads, no singles or packs of four) and had the most
footprint beyond its core (0.40); now 208 monsters (1.57 per 100 land, 0.25 along roads, groups 1 to 6, road camps,
outposts of 4-6 orcs, loners) and spread 0.24 (the five farthest homes and the east barn dropped, the training hall
by the west gate); all town_feel figures inside, `--start` too; walk two of two; installed.

**S4 exit criteria met; S5 (browser editor) is NOT started (11:56).** The user: "we cannot go blindly into it; the
foundation we pick (libraries, architecture, flows) will be there for the lifetime of the product." An agent writes
`devdocs/map_studio/S5_BROWSER_EDITOR.md` (+ `s5_mockups/`) from everything prepared (PLAN.md, the design page and
artifact, research, the S2 host); the user hands it to other sessions to criticise. No S5 code until that review
is done and the user decides. Agreed flow (user, 2026-11-14): another session criticises and adapts the document,
then messages this lead; the result is the fundamental baseline (what, how, wiring, use by others, assets) before
any S5 building starts. Building the rest of Xeen is content made with the studio, not a stage; the user's
Xeen decisions of 2026-11-14 are in `devdocs/xeen/README.md`.

**Xeen design documents updated (12:01):** 58 dungeons (24 S / 30 M / 4 L), X1 keeps four sites (Yak to X2, Dungeon of
Death to X7, X2 and X3 swapped so X1's west road reaches the hub), the per-map table adopted (66 families, ~4,200
monsters); built-map changes in `devdocs/xeen/CHANGES_FOR_BUILT_MAPS.md`; unreconciled points in `devdocs/xeen/HANDOFF.md`
§0. Conflict for the user (`FOR_THE_USER.md` 8): the table's ~130 hostiles for X1 against pass six's measured 208.

**S5 design document written (12:19):** `devdocs/map_studio/S5_BROWSER_EDITOR.md` (~1,530 lines; D1-D15 proposed
decisions, risks R1-R16, 19 contradictions in the prepared material, requirement-to-source appendix) and
`s5_mockups/wireframes.html`. Handed to another session for criticism; it will message `openyamm-ce` with its
adaptations and a go. The published design artifact could not be read by the subagent; `design_page.html` is its source.
**Twenty-second merge (12:19):** `kind: waterfall` rebuilt (own sheet, top water joining the stream, foot water, faceted
crags, land cut at the lip; Alvar's and Emerald's falls rebuilt on scratch projects) and the short-face bays defect
(`output/studio_s4v/`; before `oymap_before_merge22`; 322 unit cases; every project identical; every playtest passes).
Next: Vertigo gets the new waterfall.

**S5 review from openyamm-a7 (12:30):** `devdocs/map_studio/S5_REVIEW_A7.md`: go for S5-0 after seven changes, no go for
S5a yet. The changes: split the revision (source / id lock / pins); severities and a lowering that skips a broken
room (validation is the lowering; edit budget set on Erathia); keyed addressing with rename and core ids; one
append-only undo model, history by hash; native against wasm on all 22 projects in S5-0; a game `pin <text>`
command first; S5a sliced. Revised (12:44; table of changes in its section 0.5; disagreements kept beside the review's view) and sent back to
openyamm-a7: second look (12:45) gives the go for S5-0 with five small points (section 5 of S5_REVIEW_A7.md), taken in; then the user gives the go (and decides D12, D15, D8's styling, the game `pin` command).

**S5-0 GO (15:11, the user):** the S5 design is the baseline (`S5_BROWSER_EDITOR.md`, last section "The user's
decisions"; review `S5_REVIEW_A7.md`, go from openyamm-a7). Decided: S5-0 with the game `pin` command; D12 separate
download, hosted page on its own origin; D15 bounded marked sculpt patches; D8 Base UI with CSS modules; the rest as
recommended. Spikes run per section 6.4; spike code lives under `output/s5_spikes/` and is thrown away except the
request list (`openyamm-studio/schema/rpc/`); the record goes to `devdocs/map_studio/S5.md`.

**Done 15:25: the game's `pin <text>` command** (`game/debug/PinInbox.*`, writes pins format 1 YAML plus the game's
own screenshot into `pins_inbox/`, carries `project`/`revision`/`lock_hash` from `<stem>.studio.yml`; 5 unit cases,
`tests/scenarios/console_pin.yml`, a desktop run). Uncommitted, `FOR_THE_USER.md` 9. Studio side still needed (S5a1):
pins schema format 1, the revision split, `oymap pins` (import), install writing `<stem>.studio.yml`.

**S5 design Revision 3 (15:44):** the user's evening answer (via openyamm-a7): "a lot of people will want to make the
dungeons and terrains by hand entirely; some will use agents for the base and finish by hand". Taken in: 6.3 settled
as recommended; hand authors and mixed authors as users (F5, F6), S5b1/S5b2 exit tests from an empty project with
no Source tab and a mixed agent/person test; R5's person-edit mark in project.yml; D15 extended (a person may mark a
project's land hand-made and sculpt all of it, strokes as differences, a ground paint brush; heightmap import first
after S5b2); spike 7's points (the core enforces `x-kinds`, a corpus lint rule, `project.resolve`, editable is not
usable). Spike 7 report saved by the lead (subagents cannot write report files): `output/s5_spikes/7_forms/REPORT.md`.

**S5-0 spikes reported (15:58), reports saved by the lead (subagents cannot write report files) in
`output/s5_spikes/<n>/REPORT.md`:** 1+5 viewer and browsers (three.js meets every budget; BC textures everywhere,
no CPU decode; the hosted page needs the local-network permission prompt; F5/Ctrl K need the user's hand check,
FOR_THE_USER 10); 2 edit latency (indoor 300 ms reachable with parsed table lookups, one validation, the cache;
view from the edit's lowering; outdoor 1.5 s now, 500 ms in S5b2 with kept land; one broken room gives 0 faces;
provenance 97 %); 3 walk (p99 under 260 us, bit-identical once the walk uses deterministic sin/cos); 4 request list
(kept in `openyamm-studio/schema/rpc/`, 40/40 native; found `Editor::find` across files and a `triangulateRegion`
iterator bug, both being fixed); 7 schema forms (D5 holds; ~1 200 annotation decisions; lint draft). Spike 6 (16:58): 21/22 byte-identical native vs wasm,
22/22 with the deck-post clamp written out (UB answered differently by libstdc++ and libc++, not libm); five UB sites by
sanitizers; musl math natively reproduces wasm on 3.2 M inputs. Next: the S5-0 record and Revision 4, the core changes,
then the user's go for S5a.

**Twenty-third merge (16:05):** the core bugs spike 4 found (before `oymap_before_merge23`; 323 unit cases, also clean
under AddressSanitizer and libstdc++ debug mode): `triangulateRegion`'s erased iterators (caught by `_GLIBCXX_DEBUG`,
not ASan); ids unique per file (`set`/`remove` take `file`; an id in two files without it is refused); five yaml-cpp
iterator temporaries read after scope (ASan). All 22 projects build identical bytes. `issueStopsBuild` left to S5a2
(the `heights` code also marks issues that must stop a build: severity is set where each issue is found).

**S5-0 exit met (17:09):** record `devdocs/map_studio/S5.md`; design Revision 4 (`S5_BROWSER_EDITOR.md` 0.6, 37 rows; no
6.2 decision changed). S5a1 (studio side of pins: file classes and revision, the lock keeping removed ids, pins format
1, `oymap pins`/`record`, `<stem>.studio.yml` on every install route) waits only for the user's go for S5a. Open: the
user's F5/Ctrl K check (before S5a2 binds search), `~/package-lock.json`, re-measuring the indoor 300 ms on a quiet
machine before S5a2 builds the cache. Spike folders (7.4 GB) deletable after the core-changes agent finishes.

**S5a GO, the whole plan (17:33, the user: "yes sure continue with the entire plan").** The lead runs S5a1-S5a5, then
S5b1, S5b2, S5c per `S5_BROWSER_EDITOR.md` 6.4, each slice only after the previous one's exit criteria are met and
recorded in `S5.md`; anything that changes a 6.2 decision or the game goes to the user first. S5a1 starts when the
core-changes agent finishes (both touch the core's shared files). The indoor 300 ms re-measure on a quiet machine is
due before S5a2 builds the cache. Chrome key check done: F5 taken, Ctrl K taken by the browser (search binds elsewhere).

**Vertigo's waterfall (17:48):** `kind: waterfall` in place of pass five's building (creek into top water, falls, lands
in water to the sea; no dirt strip, no box); walk 388 steps two of two; installed. Remaining faults: code list 23.

**Twenty-fourth merge (18:07):** the core changes before S5a (before `oymap_before_merge24`; 324 unit cases): the Node wasm
build reads an asset root (`wasm/node_env.pre.js`, the Emscripten #ifdef gone); the deck-post clamp, `mergeFlatTriangles`
and `unionTouching` UB fixed; musl 1.2.5 math (MIT) in `third_party/musl_math/` behind `core/CoreMath.h` `oy::` (285
calls switched; three-argument hypot as libstdc++'s); `tests/native_vs_wasm.sh` over the 22 projects and
`tests/sanitize.sh`. Native before/after 22/22 identical, native vs wasm 22/22, native ASan/UBSan and wasm ASan clean.
Left: `game/`/`editor/` code in the core still calls the C library (IndoorMovers, IndoorDaylight, pathfinding, SkyState,
Lua), changing no byte today; CI can't run the 22 (FOR_THE_USER 12). Checks closed: shapes,
slice, rewire and all 25 playtests pass. S5a1 started.

**S5a1 built, merge 25 (19:16):** the studio side of pins (before `oymap_before_merge25`; 336 unit cases): source revision
over the 7 source files only (128-bit SHA-256 prefix; old histories re-keyed once, `.oymap/migrations.log`); the lock as
a record (builds keep removed ids, `.oymap/lock.log`, only `oymap lock prune` drops, indoor only); pins format 1
(`core/Pins.*`, counter and `.oymap/pins/log.jsonl`, `on`+`file` or `at`, pose, picture, states, replies; pictures in
git-ignored `.oymap/pins/pictures/`); `oymap pins` (list, show, import, add, claim, reply, resolve, accept, reopen,
decline, keep, tour); `oymap record`; install writes `<stem>.studio.yml`; spike 4's dispatcher moved into the core
(`cli/Rpc.*`, `wasm/RpcModule.cpp`, `oymap call`) with the pins/record/lock_prune methods; `calibration/pins_page.py`;
PLAY.md and both procedures. 22 projects byte-identical (build.json gains `source_revision`, `lock_hash`); native vs wasm
22/22; contract suite native and wasm; 27/27 playtests on copies. **S5a1's exit criterion needs the user** (pins faults
while playing, sees them answered): the whole loop was run on a copy of the Forge with scripted pins. Not done: a pin on
a shipped map making an overlay project; `pins keep` as JPEG; `oymap import` logging a new lock. Play copies need a
reinstall to carry `<stem>.studio.yml` (matching by map name works meanwhile). Checks closed (rerun on the rebuilt game): shapes, slice, rewire and every playtest pass. 2.4 is committed locally by openyamm-03 (not pushed, no tag): our game changes in d81e300cb9 and 4f9cbaf221, the Map
Studio and Xeen records in fab2e72847 (without `briefs/mm7_7out03`); the studio, its workflow and `output/` left out. Indoor 300 ms re-measured at load 2.5 (19:30): median 257, p95 312, max 334 ms: missed by a hair, so S5a2 takes
spike 2's next savings (validate the edited tree, plan references on the changed file) from the start (S5.md).
**2.4 release (openyamm-03 asked, 19:16):** told to keep out `devdocs/map_studio/briefs/mm7_7out03/`, `openyamm-studio/`,
`output/`; the pin command, status-line change, 22 bindings and terrain_materials.py are finished and may go in.

**S5a2 built and merged (21:07, merge 26; record in S5.md):** cached serve, severities, `view.mesh`, the host and the
first web app (`openyamm-studio/web/`, started by `node openyamm-studio/host/src/host.mjs studio`). Indoor commit p95
272 ms at load 2.7 (met); outdoor at 1.5 s with no margin until S5b2. Next: S5a3 (the pin loop in the browser).

**Scores now:** the Forge 99.7 %, Warlord's Fortress 99.7 %, Control Center 99.4 %, Castle Darkmoor 99.2 %, the Hive
97.7 %, the Lincoln 97.4 %, the Abandoned Temple 97.2 %, the Temple of the Moon 97.5 %; Harmondale 89.18 % (86.20
without the rim), Ravenshore 92.18 % (91.50). Bands: under "The user's decisions".

**The user plays the maps** (`output/studio_play/PLAY.md`): the Forge, Darkmoor, the Abandoned Temple, XD-01 to XD-04
(all four after their passes). His findings today became rules in REBUILD_PROCEDURE.md (what the measure does not
see; can a player read it; room sizes; puzzles; nothing in its stand-in; no silent clicks; no riddles the game does
not answer; keys where MM players look; liquids move; no flicker) and studio checks. Latest: message windows only for
things meant to be read, the status line held longer for the rest (game change done; studio rule in batch ten).
Open questions to him: a second eye-sector fix; whether rebuilds improve on obscure originals (Darkmoor's cube);
committing the status-text change and the lifted bindings.

**Running: two agents on Opus** (Erathia round two; S5a4 walk and Play here, with the two game debug features the user approved at 22:33: a start-of-map console file and the exit pose); merge 27 (S5a3; 354 unit cases; before `oymap_before_merge27`) checks running; merge 26's passed (Erathia round two); merge 26 checks running; S5a3 built, merged after them (Erathia round two; S5a3, the pin loop in the browser); merge 26 checks running (Erathia round two); merge 26 checks running (Erathia round two; S5a2 open and look, in `build-s4` and `openyamm-studio/web/`; S5a1's exit accepted on the scripted loop; the user's first real pins are the remaining check, whenever he plays) (Erathia round two) (Erathia round two; S5a1, the studio side of pins, in `build-s4`) (Erathia round two; core changes before S5a: the wasm asset root, the remaining UB fixes, musl-based own math, the 22-project native/wasm and sanitizer scripts, in `build-s4`) (Erathia round two; S5-0 spike 6 native against wasm on 22 projects) (Erathia round two; S5-0 spike 6 native against wasm on 22 projects; fixes of two core bugs spike 4 found, in `build-s4`) (Erathia round two; S5-0 spikes 1+5 viewer and browsers, 2 edit latency, 3 walk in wasm, 4 request list (kept, `openyamm-studio/schema/rpc/`), 6 native against wasm on 22 projects (7 schema forms done), under `output/s5_spikes/` with `BRIEF.md`) (Erathia round two) (Erathia round two; the S5 document revised to the A7 review) (Erathia round two) (Erathia round two; the waterfall code batch; the S5 browser editor design document) (Erathia round two; the waterfall code batch in `build-s4`, scratch `output/studio_s4v/`) (Erathia round two; a code batch rebuilding `kind: waterfall` and the Ironfist leftovers in `build-s4`, scratch `output/studio_s4v/`; Vertigo pass six: monsters and town spread measured against shipped maps and added to `town_feel.py`) (Erathia round two) (Erathia round two; Vertigo pass five from the user's walk, with XD-04's arrival moved to the tower's new door) (Erathia round two: O-H words and the building shots) (Erathia round two: O-H words and the building shots; Castle Ironfist round three: the roof stair, the gate block and passage, recesses, boards) (per-building shot tool and Castle Ironfist round two) (code batch O-H from the Ironfist and Erathia rebuilds in `build-s4`, scratch `output/studio_s4u/`; the per-building shot tool `calibration/building_shots.py` and Castle Ironfist round two with the user's six places) (Erathia rebuild) (Castle Ironfist and Erathia rebuilds) (Castle Ironfist and Erathia rebuilds; fixes of the words the gate pictures found wrong, incl. a Shadowspire roof regression, in `build-s5`) (Castle Ironfist and Erathia rebuilds; the indoor code batch in `build-s4`; fixes of the words the gate pictures found wrong, incl. a Shadowspire roof regression, in `build-s5`) (the user allows up to eight; Vertigo pass four; gate pictures into `output/gate_pics/REPORT.md`; new rebuilds of Castle Ironfist `mm6_outd3` and Erathia `mm7_7out03` as tests of the new words; an indoor code batch in `build-s4`, scratch `output/studio_s4s/`) (Vertigo pass four from the by-eye review; gate pictures of the overnight batches into `output/gate_pics/REPORT.md`) (the display is back: Vertigo pass three by-eye review into `output/studio_cal/x1/review/REVIEW_PASS3.md`; gate pictures of the overnight batches into `output/gate_pics/REPORT.md`) (applying the new roof words to the rebuilds) (code batch of concave outline parts under one roof, partial eaves, `parapet_walls`; `build-s4`, scratch `output/studio_s4r/`) (Ravenshore north-west block redraw, by the numbers) (Vertigo pass three by the numbers: town feel, cave-mouth doorways, waterfall, battered walls, even scatter; the by-eye review follows when the display is back) (catalog batch O-F, landmarks: arcades and porticos, portals, walkways and decks, free-standing arches, stone rings, tents; `build-s4`, scratch `output/studio_s4q/`) (catalog batch O-E, land: spires and peaks, cuts with ramps, nested terraces, closed ridges, buildings against a slope with a ground skirt; `build-s4`, scratch `output/studio_s4p/`) (catalog batch O-D: domes, batter and buttresses, roofs to the ground, stepped masses, ruins, eaves per wall; `build-s4`, scratch `output/studio_s4o/`) (catalog batch O-C: fountains, arched and sagging bridges, liquid faces, culverts, cave mouth setback, segmental arches; `build-s4`, scratch `output/studio_s4n/`) (catalog batch O-A: leave trigger, atmosphere flags, `when_flying`, invisible faces, scatter words, terraces; `build-s4`, scratch `output/studio_s4m/`) (catalog batch O-B, ways in: `build-s4`, scratch `output/studio_s4l/`) (catalog batch O-B, ways in: `build-s4`, scratch `output/studio_s4l/`; rebuild cleanup of New Sorpigal, Harmondale, Ravenshore: z-fighting and town feel) (outdoor code batch ten, finishing) (outdoor code batch ten, finishing; three Xeen design reviews: scale and density, story and atmosphere, combat and progression, into `devdocs/xeen/reviews/`) (outdoor code batch ten, finishing its last walk) (outdoor code batch ten, finishing its last walk; Vertigo trees, edges, wild-land and town density measured against shipped maps) (outdoor code batch ten, finishing its last walk; Vertigo trees, edges, wild-land and town density measured against shipped maps) (outdoor code batch ten; Shadowspire round three with the dragon cave; Harmondale round two; Xeen exits to Vertigo; ten surveyors of all 42 shipped outdoor maps, brief `output/studio_survey/BRIEF.md`, results `output/studio_survey/<map>/SURVEY.md`) (outdoor code batch ten: outdoor coplanar check, the studio's z-fighting sources, town words; `build-s4`, scratch `output/studio_s4k/`) (Shadowspire round two: the user's 10 places and its z-fighting) (Vertigo pass two, from the user's walk and the by-eye review) (New Sorpigal round two) (outdoor batch nine; New Sorpigal round two) (the user allows six). **S4 started 20:34 at the user's word ("OK then, go S4"); S3
closed.**

| Agent | Works in | Scratch | Delivers |
|---|---|---|---|

**Next, in order:**
1. S4's agents as they report: check, play, install, give the user commands for his walks. Merge outdoor batch eight
   (every playtest four times), then give the S4 projects its lines.
2. The user's answers: committing the status-text change and the lifted bindings (recommended yes); the second
   eye-sector fix (recommended no); rebuilds stay faithful to obscure originals (recommended); a git snapshot.
4. Next rounds, each from "What the measure does not see" and `oymap things`: the Lincoln round six (after spawn
   groups), the Abandoned Temple and the Temple of the Moon toward the bands, Warlord's Fortress round two (item 11),
   outdoor round five after batch seven.
5. For the user, game-side (NEXT_CODE_BATCH.md "Not studio work"): `monsters[].hp` ignored (XD-01's boss, XD-03's
   King); names need `place_mon.txt`; MM7 has no ambient sounds and refuses the engine's `lava loop.wav`; an outdoor
   model shown by an event stays unclickable; after `SetFacetBit` by cog the use key reaches through a shut door;
   headless runs plan monster paths inside the frame; an item an event gives lands in the hand where HasItem does
   not see it; scenario-runner faults (`open_door` kills nearby monsters, pulsing lights read `unset`, map timers stop
   in tours, a one-character party).

## What the work is

Map Studio (`openyamm-studio/`, untracked, its own build) builds MM6-8 indoor maps (BLV, scene, Lua) and classic
ODM outdoor maps from YAML projects. The user reviews **results only**, on `output/studio_review/index.html`
(written by `python3 openyamm-studio/calibration/review_page.py`, which re-measures every rebuild when run), and
asked for a **self-correcting loop**: rebuild shipped maps as projects, measure them against the originals by tool
(`oymap compare`, indoor and outdoor), build what the vocabulary lacks, repeat, without the user pointing at
differences. On 2026-11-12 the user added: do the outdoor maps as well; and agreed to build one new dungeon from a
written brief with no original (XD-01).

## Where this sits in the plan

`PLAN.md` section 12 has the milestones with what each delivers and how it is accepted.

| Milestone | State | Record |
|---|---|---|
| S0 skeleton, briefs, vertical slice | done | `S0.md` |
| S1 read side and metrics | done; its game-side cuts were committed on 2026-11-13 (`dfd7a236ac`) | `S1.md` |
| S2 operations, host, agent interface | done except map reload in the running game, HTTP/jobs | `S2.md` |
| S3 indoor authoring | **accepted 2026-11-13 (20:30)** pending the user's word: every map within the bands and walked by the user (the Forge, Warlord's Fortress, Control Center, the Temple of the Moon, Darkmoor in part, the Hive on its fixes, the Mad Necromancer's Lab and Goblinwatch held out, XD-01 to XD-05); set-piece import and the Python port dropped | `S3.md` |
| S4 outdoor authoring | **in work.** A sketch builds into a classic ODM with land, ground and shore tiles, roads, buildings of several parts, walls, bridges, wells, chests, signs, people, monsters, scatter, weather and travel off its edges; an outdoor `oymap compare`. Acceptance not met: Ravenshore and Harmondale are being calibrated; New Sorpigal, Shadowspire and Vertigo Meadows are not started | `S3.md` from "Second code batch merged" |
| S5 browser editor, S6 MM9 profiles, S7 consolidation | not started | `PLAN.md` |

The lead's own estimate of the dungeon work, given to the user on 2026-11-12 (a judgement, not a measurement): shape
and textures of shipped dungeons about 90 % there, behaviour 70 %, contents 40 %, new dungeons from a description
25 %, the rest of the milestone 20 %; about two thirds overall. After XD-01 (2026-11-13) the lead put "new dungeons
from a description" at about 40 %: a brief becomes a playable dungeon in the right order with one strong area,
but not every room is worth looking at and several things a designer reaches for are missing.

## State of the maps

Dungeons: `devdocs/map_studio/briefs/<key>/L4/`, each with `NOTES.md` (a section per round) and `playtest.yml`;
scratch, pictures and repro projects in `output/studio_cal/<key>/`. Scores are the lead's measurement of 2026-11-13, 09:18 (equal to the
round-five reports), and the later rounds' reports (the Forge's finishing round, the Temple's round six, the Fortress); the measure is the corrected one (S3.md, "Round three merged", links it to
earlier figures). All validate, build and pass their playtests four of four by their reports.

| Map | Key | Score | Rounds |
|---|---|---|---|
| Gharik's Forge (MM6 6d18.blv) | `mm6_6d18` | 99.7 % | five and a finishing round; played by the user |
| Control Center (MM6 sci-fi.blv) | `mm6_scifi` | 99.4 % | six and the ninth merge's lines; the user (16:39): "good" |
| Castle Darkmoor (MM6 cd2.blv) | `mm6_cd2` | 99.2 % | six; 267 rooms |
| The Hive (MM6 hive.blv) | `mm6_hive` | 97.7 % | six; 100 rooms |
| The Lincoln (MM7 7d23.blv) | `mm7_7d23` | 97.4 % | five and the ninth merge's lines; playtest ten of ten |
| Goblinwatch (MM6 6d01.blv), held out | `mm6_6d01` | 99.2 % | one |
| The Mad Necromancer's Lab (MM8 d20.blv), held out | `mm8_d20` | 99.7 % | one |
| Abandoned Temple (MM8 d05.blv) | `mm8_d05` | 97.2 % | seven; the user's walk; arrival view fixed |
| Temple of the Moon (MM7 7d06.blv) | `mm7_7d06` | 97.5 % | seven |
| Warlord's Fortress (MM6 6d16.blv) | `mm6_6d16` | 99.7 % | one (L3 to L4) and the ninth merge's lines; the user: "plays exactly the same" |

Outdoor: the same folders, by OUTDOOR_REBUILD_PROCEDURE.md. Their first sketches were written from the originals
by scripts (`output/studio_s4c/gen/`; not run again) and then worked over by one rebuild round each; scores are
the lead's measurement of 2026-11-13, 01:35, with the stricter decorations part. They show what the builder can build from a careful description of
a known map, not yet a map from a written brief.

| Map | Key | Score | State |
|---|---|---|---|
| New Sorpigal (MM6 oute3.odm), held out | `mm6_oute3` | 93.53 % | two; the user's 21 places |
| Shadowspire (MM8 out06.odm), held out | `mm8_out06` | 92.12 % | three; the dragon cave and the Lab |
| Ravenshore (MM8 out02.odm) | `mm8_out02` | 92.20 % | five rebuild rounds |
| Erathia (MM7 7out03.odm), fresh | `mm7_7out03` | 88.8 % (88.0 without the rim) | one round; the land beside sheer drops |
| Castle Ironfist (MM6 outd3.odm), fresh | `mm6_outd3` | 93.91 % (94.16 without the rim) | three; the castle roof reached on foot |
| Harmondale (MM7 7out02.odm) | `mm7_7out02` | 90.23 % (87.22 without the rim) | seven rebuild rounds; inside the band |

New: XD-01 Joe's Warehouse, `devdocs/xeen/briefs/xd01/L4/`: built from its brief on 2026-11-13 and given a second
pass (26 rooms, playtest 110 steps), in MM7's world as a stand-in. XD-02 the Red Dwarf Mines,
`devdocs/xeen/briefs/xd02/L4/`: built from its brief the same day (43 rooms, playtest 171 steps). XD-03 the Deep Mine,
`devdocs/xeen/briefs/xd03/L4/`: built from its brief the same day (24 rooms, walks of 175 and 46 steps; the first
under the texture rule). XD-04 and XD-05 have L1 to L3 only. XD-01 and XD-02 are in a texture pass (10:14, 10:25).
Warlord's Fortress (`briefs/mm6_6d16`) reached L4 on 2026-11-13 (99.7 %), in the maps table above.

The review page's Temple pictures come from a copy: before regenerating, copy `briefs/mm7_7d06/L4/*.yml` and
`diagram.txt` into `output/studio_temple/project`, build it, and run `python3
openyamm-studio/calibration/ingame_compare.py output/studio_temple/project mm7 7d06.blv
output/studio_temple/shots.yml output/studio_temple/compare --root output/studio_temple/root`; then update the
"State of these pictures" note in `review_page.py`.

## Rules that bind (the user's)

- No `git add`, `commit`, `stash`, `restore --staged`, `reset` unless asked. The studio and its docs are
  uncommitted on purpose (below).
- Never copy code from OpenEnroth or mm_mapview2. Never edit generated Lua or MM9 converter output. `assets_dev`
  files are hard links in every `cp -al` root: never edit in place. `/tmp` is not durable.
- `rm` only with literal paths, after `ls`, in its own command (a hook blocks variables and wildcards).
- No game build while an MM9 `convert.py` runs; game builds go through the lane (`flock -x
  level_generation/projects/mm9r_common/locks/cmake_build.lock cmake --build build --target openyamm -j25`); no
  Vulkan builds. Game runs minimised through `tools/run_game.sh`, `SDL_AUDIODRIVER=dummy` in front; review shots
  with the HUD off.
- Manual fix-ups live in the project, never in built maps. Outdoor is classic ODM.
- **A wrong shape that measures better is forbidden.** Check every agent report for it. Cases so far: a roof bent
  to a wrong pitch (round two, set back); slabs widened by 2 to 4 units to catch the measure's edge points (in the
  Forge since round one, found and undone by its round-three agent; the measure was then corrected).
- A fix for something the user saw is proven in the game on a part that shows the fault, before and after.

## The user's decisions

- **Models (2026-11-12; changed 2026-11-13):** on 2026-11-12 lead and code agents on the strongest model (Fable),
  effort high, rebuild agents on Opus. On 2026-11-13 the Fable limit was reached at about 02:00 and the user set the
  session to Opus 5.5; until the user says otherwise everything runs on Opus. Original note: rebuild agents on Opus
  (`model: opus` on the Agent call; agents inherit the lead's model unless told). A rebuild or code agent uses 350
  to 790 thousand tokens.
- **Scripts may write project files (2026-11-12).** Kept as a record, never re-run once a project has hand edits;
  both procedures say how. Uneven floors and roofs are given by points where the surface changes slope, within a
  budget; rooms that took the original's points one for one are named in NOTES.md.
- **Game-side changes are allowed when no existing map changes (2026-11-12).** Done so far: the `water` surface
  flag in the indoor compiler; a level-sliding door carries the party when its scene `mover` block has `carry:
  true`. Anything else outside `openyamm-studio/` is asked first.
- **The moving-texture rule stays in the studio (2026-11-12),** not in the game's indoor compiler: the user fears
  regressions. Not to be moved unless an MM9 conversion shows a sliding texture. (What it is: S3.md, "Textures on
  moving parts"; `anchorMovingFaceTextures` in `core/IndoorBuild.cpp`.)
- **Outdoor as well (2026-11-12, 20:45),** and tunnels need their cross-section (built: `section` on path rooms).
- **XD-01 from its brief (2026-11-12, 23:40):** agreed, "if you feel it is best".
- **Committed (2026-11-13):** the release session openyamm-f4 committed this work's game-side changes in
  `dfd7a236ac` (the S1 and S2 cuts, `--extra-mount`, carry, water). `openyamm-studio/`, `devdocs/map_studio/`,
  `devdocs/xeen/` and `.github/workflows/studio.yml` stay untracked: whether and how the studio enters the
  repository is the user's to decide. Never done: checking the 7 failing full-suite game unit cases against a
  clean tree.
- Gharik's Forge's lava: decided by the lead on 2026-11-13 to follow the original's data (timer only); the finishing
  round found that OpenYAMM's own overlay adds the lava flag in the shipped game, so the rebuild now burns less than
  the shipped game. Asked of the user.

- **2026-11-13, about 12:15:** the Forge's lava as OpenYAMM ships it (the floors burn, and the timer stays; applied,
  playtest four of four, in the user's copy). The textures the Xeen dungeons list: generate them ("sure no
  problem"). "Within bands" is the lead's to define (below). Set-piece import and the Python port: the lead's
  recommendation, dropped (PLAN.md 2a). A git snapshot of `devdocs/map_studio` and `devdocs/xeen`: yes (`a761ce68bd`;
  project build folders ignored; `openyamm-studio/` stays out). The user plays maps to judge them: give run
  commands (`output/studio_play/PLAY.md`), not only pictures; on the fixed Forge: "this plays exactly the same as
  original one".
- **Within bands (the lead's definition, 2026-11-13).** A rebuilt dungeon is within bands when: `oymap compare` is at
  least 97 % overall; its playtest goes from the arrival to the exit and passes every run (four of four, nothing left
  to chance); every event of the original does the same or is listed as unsayable; the "what the measure does not
  see" pass is done (every interactive thing pictured beside the original's before and after use, the view from
  every raised top, no fault left that the project can say); and no fault from the user's play is open. An outdoor
  map: at least 90 % with the rim part, its walk two of two, the same pass. A new dungeon: scale inside the bands of
  MAP_CRAFT_CALIBRATION.md, its playtests every run, the texture rule met, and the user's walk. Today: the Forge
  meets them (and the user's walk); Control Center, Castle Darkmoor, Warlord's Fortress and the Hive meet the numbers
  and wait for the user's walk; the Lincoln (a chance failure), the Abandoned Temple (96.9 %, the black arrival
  view) and the Temple of the Moon (95.9 %) do not yet.

## Build and checks

```
cd openyamm-studio && ./build.sh          # native: build/oymap, build/oymap_tests   (wasm: ./build.sh wasm)
build/oymap_tests                         # 189 cases at the last merge
tests/run_shapes.sh [--shots]             # the test map: walk of 450 steps in the game, 113 tour pictures
tests/run_slice.sh ; tests/run_rewire.sh ; tests/native_vs_wasm.sh ; (cd host && node test/mcp.test.mjs [--play])
python3 calibration/review_page.py        # re-measures all maps and writes output/studio_review/index.html
```

`tests/run_shapes.sh` checks one line of `oymap solve` on the test map (`step 1: 29 sectors (63 of 71)` now): it
changes whenever rooms are added there; set it to what the merged build gives.

## Merging code agents' work

Code agents share the source tree and build only into their own trees (`build-geo`, `build-cmp`, `build-fix`,
`build-s4`; the lead's was `build-lead`; all may be removed when no agent runs). Rebuild agents use
`build/oymap` and `build/game/openyamm` as they are. So:

1. Do not rebuild `build/oymap` while rebuild agents run unless existing projects build to the same bytes.
2. When the rebuild agents have finished: keep a copy of the old `build/oymap`, `./build.sh`, unit tests, set the
   solve line, `tests/run_shapes.sh --shots`, slice, rewire.
3. Build all seven dungeon projects with the old and the new binary and compare (`.blv`, `.scene.yml`, `.lua`);
   explain every difference; play all seven playtests (several times where one loots chests: a playtest must not
   depend on what chests roll).
4. Re-measure everything with `review_page.py`; where the measure itself changed, measure the same projects with
   the old binary too and record both (S3.md has such tables).
5. Refresh the Temple's review copy, add new test-map shots to `SHOTS` in `review_page.py`, regenerate.
6. Record in S3.md; update this file.

Editing `review_page.py` by script: `PAGE` is one long string and the placeholders (`@INGAME@` and the like) occur
twice, once in `main()` and once in `PAGE`: search from the right place, and parse the result before writing (it
was duplicated twice this way).

## Other sessions

No other session works on the studio. openyamm-fe, which drew the Temple of the Moon and the Xeen briefs, no longer
exists (the user, 2026-11-12). Other sessions of the user's work in the repository (openyamm-a7 on saves,
openyamm-f4 on the 2.2 release) and rebuild `build/game/openyamm` every half hour or so: a run that hits a
half-written binary is retried after a minute; a playtest failure that smells of saves or loading is checked
against their work first.

## Open, beyond the checklist above

- Tool defects not with an agent (S3.md, "Round four", last bullet): event casts cannot be asserted in a headless
  run, in the original either (so traps are known to fire the right call, not to hurt); `oymap build --out` and
  `oymap export <project>` write `ids.lock.yml` into the folder they read.
- The measure sees shape and textures from the floor. It does not see lighting, texture offsets, monsters, items
  or sound; the sliding door textures scored perfectly. Expect the user's first walk through these maps to find
  such things.
- A sized chest's width runs ALONG its `facing`, which every author read the other way; kept because the
  Temple's bookcases are tuned to it; a candidate for a format fix with a migration.
- The solver's gap widths (strides up to 144 at a walk) and its reach for using an event (160) come from reading
  the game's movement code, not from a run.
- S3's other deliverables: Goblinwatch and the Mad Necromancer's Lab, XD-05 (all started 16:45), the Temple of the
  Moon to 97 %, the user's walks of the Fortress and the held-out maps. Set-piece import and the Python port were
  dropped.
- S4's: New Sorpigal, Shadowspire, Vertigo Meadows; a sketch drawn from a description and not from an original.
