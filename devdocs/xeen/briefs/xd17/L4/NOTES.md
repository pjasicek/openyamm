# XD-17 Shangri-La: L4 notes (lane A5 sub-agent, 2026-11-21)

Act V's hidden town (Q-C26, party 48-52): a green valley in Mount Firestone's black flank, five services and ten
residences (A4's `source/towns/xd17.yml`, houses 4351-4365), no monsters. Built from the approved L1 (`../L1/`,
board `output/studio_cal/xd17/mockups/board_xd17.png`) with decider D-50 (`briefs/x9/L1/D50_DECISION.md`), which wins
where they differ. **Installed 2026-11-21 01:36, reinstalled 01:45 (merge point 22 pass)** as `assets_dev/worlds/xeen/maps/xeen_xd17.blv` with its
`.scene.yml`, `.studio.yml`, `events/maps/xeen_xd17.lua` and the ground's `terrain_materials/xeen_xd17_blv.yml` and
`xeen_xd17_blv_weights0.png`. map_stats 9120 (A2's row, music 51); the orchestrator has it in `openAirMaps`.

## Route: the studio

X8's route (an open-air BLV, `kind: indoor`, `profile: region`), with the valley floor drawn as terrain (Map Studio
"Ground for open-air maps", S8b). Three rooms:

- **`room:valley`**: one room open to the sky whose uneven floor (`floor_points`, 190 of the room's 192) is the whole
  basin: the town floor level at 0, the black cliffs from the foot ring (0) through a mid ring to a jagged crest
  (2,333 south to 3,304 north-east, `places.CREST`), a back slope, and Firestone's summit (crater 5,376, rim 5,632)
  beyond the north-east crest. Its ceiling (`ceiling_points`) is sky: just over the crest round the rim, high over the
  summit and the sightlines to it, low (a rib just over the rock) along the two bluffs.
- **`room:throat`**: the cave throat, 384 by 736, ceiling 448, behind an arched mouth (352 wide) in the **south
  bluff**, a sheer rock face that stands out of the cliff foot over the mouth. Its back is the way out to XD-16.
- **`room:passage`**: the back passage, a slot open to the sky about 2,400 long: it leaves square to the north-west
  cliff foot (north-west), then bends west to the rockfall. Its walls follow the rock's height beside it (from the
  640 lip at its mouth up the cliff), 1,536 at the rockfall.

Terraces are `levels` with stone banks and broad `flights` (the library 256, the temple 384, the pyramid terrace 256).
Lanes and the first square are paving slabs 4 high (gravel lanes are the ground's road layer; the square is
flagstones). Buildings are studio masses: a wall block one bay tall (two storeys of the MM7 half-timber kit, or
fieldstone, dark stone, marble, logs) and a separate gabled roof block whose gable ends are stucco (`7hhr1p`) or the
wall's stone; the guild is an octagonal marble tower with a stepped gilded dome, Sally's an octagonal hut, Pilar's a
small house with a low slate dome.

Scripts in `output/studio_cal/xd17/tools/` (new code; X8's not edited):

| Script | Writes |
| --- | --- |
| `places_l2.py` | the L2-L4 layout: `places.py` (L1, D-50 applied) with what had to move (below) |
| `geo.py` | the valley's shape: foot ring, cliff rings, crest, bluffs, summit, outline, the pool and stream |
| `gen.py` | L2-L4 plan.yml and project.yml, L3/L4 rooms.yml and atmosphere.yml, L4 objects.yml and wiring.yml |
| `gen_playtests.py` | the four playtests |
| `figures_l4.py` | the town figures on the built layout (`mockups/figures_l4.json`) |

`output/studio_cal/xd17/v.sh` (generate, fmt, validate L2-L4), `b.sh` (build into `output/studio_cal/xd17/build`),
`stage.sh` (hard-link stage of assets_dev with real data tables, install), `run.sh` (the playtests, each game run in
one of lane A5's two slots; `ASSETS`, `N`, `TESTS`). The project has no hand edits; runs are recorded
(`oymap record`, author `agent:a5-xd17`).

What moved from L1 (`places_l2.py`), by 128-768 each: the library (-4096, -1280) and the temple (-5120, 704) onto two
terraces 192 apart; Benedict (-2368, -1920) and An Education (-2112, 1344) off the steps; Murray's villa
(1792, 4160); the Light guild's tower (3200, 2560) clear of the pyramid terrace's bank; Pilar's house (4480, 3712)
clear of the pool's north shore; the tavern 64 shallower; the pool's radii (1024, 704); the back passage turned to
leave square to the cliff foot. The well, the pyramid, the arrival and the court are where L1 put them.

## What D-50 asked, and what was built

| D-50 | Built |
| --- | --- |
| 1 Lacey and Stumpy | Placed, peaceful (group 1, the build's peace event), not counted: Lacey 11915 (actor 0) at (448, -384), Stumpy 11916 (actor 1) at (4608, -2304), `immobile`. They talk from their bodies as NPCs 4719 and 4718 (A1's `monsters[].npc`, merge point 22; `gen.py` `NPC_WORD = True`): the walk asserts both A4 greetings. **Lacey's 512:** no indoor home radius in the studio; A2 adds `wander: {radius: 512}` to her row as a modifier (until then her row's `Short`, 1,024) |
| 2 The well | `platform:well` (a fieldstone basin, water at its brim) calls A3's `xd17.well`; the walk asserts the line, award 421 for member 0, then "The water is cool and refreshing." |
| 3 `entrance:d6_pyramid` | (0, 3200, 256) facing south (1536) on the pyramid terrace, as `Xeen.PyramidArrivals.shangrila`. The portal (`platform:pyramid_portal`, `xdpyrdor`) calls A3's `xd17.pyramid` |
| 4 Ways out | Both `exit` presets (D-24), titled "Leave Shangri-La" (the window's meaning: aaze0049:32). The rockfall calls `xd17.cleft_opened` in the same click (see Open items) |
| 5 Door ids | A4's file has `door:maurice` ... `door:martok`; `tools/xeen/towns.py` passes (exit 0) on the installed script |
| 6 POIs | 18: the well, the pyramid, the crystal, 15 doors. The falls are a landmark (the notch) with no event |
| 7 Concept corrections | The valley's depth kept (arrival to the pyramid 8,861, to the tower 8,562); the anvil against the forge's west wall between its two doors; Pilar's a small house with a door |
| 8 Textures | 43 of 70 (class L, `texture_budget.py`), 0 new |
| Q3 Summit | Floor of the valley room beyond the north-east crest, apex 5,632 over the floor, `view_distance_scale` 1.25; seen from the arrival (15,373 away), the library steps (14,579) and the forge square |
| Q4 Signature | From the library steps (-3200, -1280, eye 426) east-north-east: the court, the well with Lacey, the pool, the guild's dome, the summit (`output/studio_cal/xd17/shots/final/02-signature_library_steps.png`) |
| Q5 Crystal | `panel:crystal` (`gcrysc2`, 32 by 64, bottom 136) in the south bluff's face east of the mouth, calls `xd17.crystal` |
| Q6 Sky | `open_sky: {preset: fair, view: outdoor, view_distance_scale: 1.25}`, no theme, no weather; a daylight block |
| Q7 Water | The pool and its stream (one sunken level, liquid) to the south-east cliff foot; the notch in the east crest (dipping to about 1,900 over the lip). The fall decoration and its sound (`sound:falls`) are switched by `gen.py` `fall_model_bound()`: they appear when the world binds `xeen_waterfall` (absent today) |
| Q8 Passage | A slot open to the sky, about 2,400 long, 370 wide |
| Q9 Far end | D6 is installed (A6): neighbour `pyramid:alamar` to `xeen_d6.odm`, arrival `entrance:xd17_pyramid` (-5120, 1024, 1856) facing north, listed only (the click is A3's `xd17.pyramid`). The walk sets m30.done (111600), rides to D6 (asserted within 192 of the arrival) and back by D6's pyramid (its event 41, `Xeen.travelPyramid("alamar_gate")`) to `entrance:d6_pyramid` (asserted within 160, z 216-316) |

## Every door

Each door is a slab (`platform`, 128 by 256, the door's picture fitted) on the building's face; its click runs
`evt.EnterHouse(<house>)`. The walk clicks each one from 192 in front and asserts the house's screen.

| Door id | House | Point, facing | Floor |
| --- | --- | --- | --- |
| `door:tavern_xanadu` | 4353 Tavern Xanadu | (-1856, -3072), e | 0 |
| `door:arm_and_hammer_arms` | 4351 Arm and Hammer | (-128, -3456), w | 0 |
| `door:arm_and_hammer_armour` | 4365 Arm and Hammer | (-128, -2688), w | 0 |
| `door:earth_temple` | 4352 Earth Temple | (-4544, 704), e | 384 |
| `door:guild_light` | 4354 Shangri-La Wizard's Guild | (3200, 2112), s | 0 |
| `door:an_education` | 4355 An Education | (-1600, 1344), e | 0 |
| `door:public_library` | 4356 Public Library | (-3584, -1280), e | 256 |
| `door:maurice` | 4357 Maurice's House | (-1856, 2304), e | 0 |
| `door:alexander` | 4358 Alexander's House | (1568, 1664), w | 0 |
| `door:pilar` | 4359 Princess Pilar's Pavilion | (4480, 3328), s | 0 |
| `door:benedict` | 4360 Benedict's House | (-1984, -1920), e | 0 |
| `door:elona` | 4361 Elona's House | (2560, -2784), n | 0 |
| `door:murray` | 4362 Murray's Villa | (1792, 3712), s | 256 |
| `door:sally` | 4363 Psychic Sally's | (1632, -1280), w | 0 |
| `door:martok` | 4364 Martok's Lodge | (-3712, -3008), n | 0 |

Signs over the service doors (`7sgtvrn`, `sgweapon`, `7sgarm`, `sgtempl`, `sglight`).

## Arrivals and ways out (measured)

| Name | Point (installed `xeen_xd17.studio.yml`) | Facing | Who leads here |
| --- | --- | --- | --- |
| `entrance:xd16_way` (= start) | (-1280, -4736, 4), on the first street's paving | north (512) | XD-16's cool passage end (A7, exit preset) |
| `entrance:x7_cleft` | (-7296, 4224, 0), 384 inside the rockfall | east (0) | X7's `door:xd17` (live since 01:38; the lead tests the round trip from X7) |
| `entrance:d6_pyramid` | (0, 3200, 256) | south (1536) | D6's pyramid outside Alamar's gate (event 41), tested |

| Way out | Event | Lands (measured by its playtest) |
| --- | --- | --- |
| The throat's back (`exit:throat`, south wall of `room:throat`) | 20, exit preset | XD-16 `entrance:xd17_way` (4864, -18176, -1280) facing north; the party within 160, z -1,340 to -1,200. A dungeon to a dungeon moves at once: the game shows no window |
| The rockfall (`exit:cleft`, west end of `room:passage`) | 7, exit preset + `xd17.cleft_opened` | X7 `entrance:xd17_cleft` (4096, 8192, 2496) facing west (1024), after the game's leave window (OK); the party within 192; qbit 116140 set (clear before) |
| The pyramid (`platform:pyramid_portal`) | 17 | refused before m30.done (asserted); after it D6's `entrance:xd17_pyramid` (-5120, 1024, 1856), no window (`{direct = true}`), and back by D6's pyramid to `entrance:d6_pyramid` |

## Town figures (`figures_l4.py`, TOWN_FEEL's definitions, `--small` bands)

| Figure | Target | Built |
| --- | --- | --- |
| Services; residences | 4-6; 8 +- 3 | 5; 10 |
| Buildings; doors | 14; 15 | 14; 15 |
| Weapon to armour | 384-5,830 | 768 |
| Service to nearest service, median | 854-2,424 | 1,770 |
| Farthest service | 3,203-16,598 | 5,162 |
| Town core radius | 2,360-6,552 | 3,650 |
| Fringe / core; beyond 1.5 core | 1.29-3.79; 0-0.38 | 1.64; 0.15 |
| Town built share | 0.15-0.37 | 0.156 |
| Tavern rank from arrival / centre | 0.05-0.95 / 0-0.94 | 0.08 / 0.15 |
| Temple rank from centre | apart or raised | 0.77, on its terrace at 384 |
| Doors on compass axes | 0.77-1.0 | 1.0 |
| Doors with a lane within 1,024; door to lane median | 0.81-1.0; 147-381 | 0.93; 205 |
| House to nearest house, median | - | 1,722 |
| Door levels p10-p90 | 0-680 | 0-256 |
| Wells | 0-3 in town | 1 |
| Walks | - | arrival to the first door 1,722, to the well 4,906; well to the pyramid's portal 3,584; the cleft's arrival to the valley 1,945 |

### Town feel exceptions

- Wells 1 (shipped maps 3-8): the source has one well and it is the point; the pool stands in for the rest.
- Door to lane: the three terrace doors open onto paved terrace tops reached by their steps, not onto a gravel lane
  (the library 960, the temple 1,024 and Murray 1,958 from the nearest lane's end).

## Points of interest (18)

The well, the pyramid, the crystal and the 15 doors. Not POIs: the falls' notch (landmark), Lacey and Stumpy.

## Textures: 43 of 70, none new

Ground: `7grastyl` (grass), `crdflr3` (gravel lanes, road), `gcav1flr` (X7's basalt: the cliffs, bluffs, passage and
throat floors). Plain faces: `gtempflr` (the square), `7tws1f` (terraces, banks, steps, the library, the guild, the
colonnade), `orwtrmarb` (pool, stream, well), the Cloudside town kit (`7hhr1bs2`, `7hhr1b`, `hhm1b1`, `hhm2b1`,
`hhm2b2`, `hhm3b`, `hhp1b`, `7hhr1p`, roofs `7hhr1rf`, `hhm1rf`, `hhm2rf`, `hhm3rf`, `hhp2rf`, doors `7hhr1d`, `hhm1d`,
`hhm2d`, `hhm3d`, `hhp1d`, signs), `chb1` (the forge), `ch1b1` and `6grastyl` (the temple and its turf roof),
`gstrrf` (Martok's logs), `xtslate`, `ygtemprf` (the guild's gilded dome), `gtemprf` (Sally's starry roof),
`gcstroof` and `xdpyrdor` (the pyramid), `gcrysc2` (the crystal), `gcav2wal`, `gcav1wal`, `7solid01` (the throat, the
rockfall, the throat's dark back), `t5d1` (the anvil). One size per texture across the map (the build keeps one).

## Sounds

AU's list (`level_generation/sounds/xeen_20261120/review/beds/xd17.yml`), points moved with their things (the stream's
two onto the stream); the fall's sound only with the fall's decoration (absent). No lights, so no lighting bake
(X8's reason: an open-air BLV takes the daylight block).

## Checks

| Check | Result |
| --- | --- |
| `validate` L2, L3, L4 (assets_dev) | no issues |
| `fmt --check` | clean |
| `build` (oymap 01:40) | 3 rooms, 1,326 faces, 2 portals, 22 events, 0 chests, 0 lights; no warnings |
| `view_distance_scale` 1.25 | no extra cost on XD-17 (A1) |
| `audit --world xeen --reach --solve --dressing` (stage and installed) | 0 errors, 0 warnings; 0 pairs in one plane; 3 of 3 sectors on foot; info only: `texture.squashed` 7tws1f on the terrace banks (meant: banks), `click.silent` on the house doors (their screens are the game's) |
| `tools/xeen/towns.py` | exit 0 |
| `tools/xeen/texture_budget.py --map XD-17` | 43/70, 0/14 new |

Playtests (`output/studio_cal/xd17/run.sh`, headless, `build-xeen/game/openyamm` 01:40 (merge point 22), `--world xeen --map
xeen_xd17.blv`):

| Playtest | Steps | What it covers | Stage | assets_dev |
| --- | --- | --- | --- | --- |
| `playtest.yml` | 295 | The first-arrival line; the valley walked on its lanes and steps; all 15 doors clicked, each house's screen asserted and closed with Escape; the pyramid refused, then with m30.done to D6 and back; the well (line, award 421), then its water; Lacey's and Stumpy's greetings; the crystal | 2 of 2 | 2 of 2 |
| `playtest_exit_xd16.yml` | 15 | The throat's back to XD-16's `entrance:xd17_way` | 2 of 2 | 2 of 2 |
| `playtest_exit_x7.yml` | 26 | The back passage, the rockfall, X7's `entrance:xd17_cleft`, cleft_open 116140 | 2 of 2 | 2 of 2 |
| `playtest_hostility.yml` | 18 | Lacey and Stumpy peaceful, no hostile actor, also after a save and load | 2 of 2 | 2 of 2 |

Logs: stage `output/studio_cal/xd17/xrun/run_014512`, assets_dev `output/studio_cal/xd17/xrun/run_014534` (the first install's: `run_013539`, `run_013619`). Stills from
assets_dev: `output/studio_cal/xd17/shots/final/` (arrival, signature, forge square, pyramid terrace); details in
`shots/t3`, `shots/t4`.

## Dressing exceptions

None (the audit lists no dressing warning). Barrels stand in pairs against the tavern's and the forge's walls; flowers
either side of Murray's door against his wall; the anvil against the forge wall between its doors; orchard and valley
trees and fallen boulders clear of lanes and doors.

## Texture fit exceptions

None. The half-timber bays are one bay tall on their walls; the gables are their own faces (stucco or stone).

## Words the studio lacked (workarounds)

- **Room limits:** a room takes at most 192 floor points, 64 floor lines of 32 points and a 64-point outline, so the
  lanes are paving slabs (not cut floor regions) and the cliff has one mid ring.
- **Platforms on raised levels** are measured from the room's floor: `gen.py` lifts them by the terrace's height.
- **No home radius indoors:** Lacey's 512 comes from A2's row modifier (`wander: {radius: 512}`), not the map.
- **An exit preset's effects run after its move:** `xd17.cleft_opened` runs in the same click, after
  `evt.MoveToMap` (A3's hook expects that: a status line, not a message box).
- **A way out needs a room wall:** both are reached through bluffs (outline notches) whose walls draw as the cliff's
  basalt; above the cave a cleft of sky shows over the bluff's lintel, and the passage's mouth is a gorge.

## Hooks used (A3's, all present in `data_tables/quest_hooks.yml`)

`xd17.arrival` (first arrival, once, a 1-second timer: a load event's window is not shown), `xd17.well`,
`xd17.crystal`, `xd17.pyramid`, `xd17.cleft_opened`.

## Open items

- **Lacey's 512:** A2's `wander: {radius: 512}` row modifier; drop this line once it is in the rows.
- **The white fall** is placed (20th session, below): S judges the placed look from the shots; if the notch, the foot or the pool move, S refits the model (`level_generation/decorations/xeen_waterfall_claude/scripts/fit_xd17.py`).
- **XD-16's cool passage end** (A7) can now lead to `entrance:xd16_way`. X7's `door:xd17` into `entrance:x7_cleft` is
  live; the lead tests that round trip from the X7 side (`playtest_exit_x7.yml` stops at the X7 arrival).
- **The rockfall's first use:** cleft_open is set in the click, so cancelling the leave window still opens the cleft.
- Houses have no window pieces (plain bays of the kit); the bluff's rib tops are jagged where the ceiling steps.

## Merge point 22 pass (2026-11-21, 01:45-)

Rebuilt with oymap 01:40 (A1's merge point 22): Lacey and Stumpy carry their NPC ids; the pyramid's neighbour names
D6's `entrance:xd17_pyramid`; the walk talks to both and rides the pyramid to D6 and back. Reinstalled by new file and
rename after 2 of 2 in the stage; the results above are this pass's.

## Merge point 27 pass (2026-11-21, 06:15-, A5 18th session)

Rebuilt with oymap 06:06 (merge point 27: the peaceful-group event once per fill; only the Lua changed) and with
`treasure_level: 0` (maps.yml's "-", D-50: no chests; row 9120 writes 0), which validates. A4's npc.txt (06:05) gives
nine houses a single resident (Martok 4717 in 4364 and the others): such a door opens on the resident, so the walk
expects the resident's id there (`gen_playtests.py` `RESIDENT`). Stage 8 of 8 after the fix (`xrun/run_061618`, walk;
`xrun/run_061501` the other three), installed 06:17:53 (studio.yml and Lua; the BLV and scene unchanged). Waterfall
still off (S's `xeen_waterfall` not installed).

## The white fall placed (2026-11-21, A5 20th session)

S's `xeen_waterfall` (row 4016, `worlds/xeen/models/indoor_decorations.yml`, preset `waterfall_xd17`, fitted to this
rock) is on: `deco:falls` at `FALL_AT` (6272, 2304), the cliff-foot floor point under the notch (z 0), facing
`FALL_FACING` 200 (the pour, notch to foot; `places_l2.py`); `sound:falls` at the same point (AU's bed, height 256).
The notch, the foot and the pool are unchanged. The built BLV holds it as entity `falls` (list id 4015) at
(6272, 2304, 0) facing 200. Built, staged and installed by `output/studio_cal/xd17/stage_install.sh` (new: a fresh
hard-link stage, audit, `run.sh` N=2, then new file + rename): stage 8 of 8 (`xrun/run_075659`), installed 07:57:21
(BLV, scene, studio.yml; Lua and terrain materials unchanged); from assets_dev 8 of 8 (`xrun/run_075736`); audit
`--reach --solve --dressing` 0 errors, 0 warnings. Shots of the placed fall (placed, not a debug spawn):
`output/studio_cal/xd17/shots/s20_falls/` (pool, pool_sw, foot, far_southwest, cliff_top_lip, cliff_top_back,
cliff_side_north, cliff_side_south; `sheet.jpg`), tours `tour_s20_falls.yml`, `tour_s20_far.yml`.


### Re-shot on S's s11c fall (A5 25th session, 2026-11-21)

The installed `xeen_deco_waterfall.glb` (S session 11, s11c: a clear `Stream` layer down the gully, white only below
the brink) at the `s22_falls` poses: `output/studio_cal/xd17/shots/s25_falls/sheet.jpg` (tour `tour_s25_falls.yml`).
From the lip (05) the water goes over the brink clear blue-green and the white starts below it: the broad pale band
with a straight near edge of s22 is gone. From behind the notch (06) the gully stream reads as water. From the pool
and the foot (01-03) the fall is white over the pool; the foot's two mist sheets read as soft pale curtains. The map
is unchanged (no rebuild). Closes the review's rows 26 and 32.

## Twenty-ninth session (A5 s29, 2026-11-22, merge point 41 rebuild; run files output/studio_cal/a5/s29/)
- Regenerated (F5/F11's meadow `ground.grass`; F12's black throat exit 7solid01, kept) and built on MP41; the way to
  XD-16 now shows the entrance window (test step added). The well's lines are status lines (A3): playtest checks status or
  window. Stage 4/4, installed 01:2x (no bake for XD-17).
