# X8 Cloudreach: L4 notes (lane A6 sub-agent, 2026-11-20)

The sky map of Act II (party 18-20): walkable cloud islands high over Cloudside, the Witch Clouds (east, over X1)
and the High Magic Clouds (west, over X3), joined by the long rope bridge. It is built from the approved L1
(`../L1/`, board `level_generation/xeen_art/phase2/x8/board_x8.png`) with D-6.2 and D-6.4. It is installed as
`assets_dev/worlds/xeen/maps/xeen_x8.blv`, with its `.scene.yml`, `.studio.yml` and `events/maps/xeen_x8.lua`.

## Route: the studio

The studio builds an open-air BLV from a project (`profile: region`). Map Studio's README calls this "Ground for
open-air maps" and "MM9 profiles"; the example is `openyamm-studio/examples/s8b_meadow`. X8 is therefore an ordinary
studio project:

- one room, `room:air`, from a safety floor at -6,000 to a ceiling at 6,000;
- the theme's walls, floor and ceiling are sky faces (`sky: true`, the `IndoorSky` bit);
- `atmosphere.yml` gives `open_sky: {mode: open, sky_texture: xeencloud, view: outdoor}`, which is the
  `xeen_cloud_sea` preset with `below_horizon: sky`, plus a `daylight` block;
- the sky is drawn above and below the islands, so the "cloud sea" is the open sky under the horizon.

The islands, bridges and causeways hang in that room as platforms:

- **Islands:** a platform with an irregular outline, from 13 to 16 points, with a cloud top (`xccloud`) and cloud
  sides (`xccloudsd`), 256 thick. Two or three flared cloud masses hang under each, as roots: rectangular blocks
  with `top_size`, whose tops are hidden inside the slab.
- **Rope bridges:** a plank deck (`t66floor`, 24 thick; `top_heights` plus `thickness`, turned along the line by
  `facing`). A bridge longer than 2,000 sags in two segments. Rope rails are raking `beams` (`hwm2rf`) 80 over the
  deck on both sides.
- **Causeways and ramps:** cloud-stone slabs (`7tws1f`, Celeste's pale marble, 96 thick).
- **Arrivals:** at each arrival, eight marble steps hang down from the south rim into the cloud. This is the head of
  the stair "rising out of the cloud sea".

Scripts write the files: `output/studio_cal/x8/tools/`, run by `v.sh` (generate, fmt, validate) and `b.sh` (build
and install into the scratch root):

| Script | Writes |
| --- | --- |
| `gen.py` | rooms.yml for L3 and L4; L3's start |
| `gen_plan.py` | L2 to L4 plan.yml and project.yml, from L1's |
| `gen_objects.py` | objects.yml, wiring.yml, atmosphere.yml |
| `gen_playtests.py` | the four playtests |

The project has no hand edits, so the generators are its source. Each run is recorded (`oymap record`, author
`agent:a6-x8`).

## What D-6.2 and D-6.4 asked, and what was built

| Decision | Built |
| --- | --- |
| Spans 3,500-4,000 | The archipelagos moved 1,536 closer each. The long bridge's east span is **3,883** rim to rim and its west span **3,858**. The islands inside each archipelago were also drawn closer, so no other link is longer than the long ramp (3,472). Causeways 2,873, 2,898 and 2,963; rope bridges 1,925-2,568; the eyrie ramp 1,927. |
| `link:garden_ramp` removed; a bridge keeps the loop | Gone. `link:garden_obs_bridge` (rope, 2,568) runs from the rhyme garden to the observatory isle. The loop is stair landing, observatory, garden, stair landing. |
| The golem heights a visible dead end by the long ramp | `link:heights_ramp` (3,472, rising 512) is the only way up. The two Cloud Golems stand at the back of the heights, `immobile`, and can be seen from the ramp (tour picture `08-heights_ramp`). |
| The Witch landing's harpies 2,000 or more from the stair head | The landing's four (3 Harpies, 1 Hag) stand 2,700-2,950 from the stair head and 2,300-2,550 from the arrival point. |
| Falling damage survivable by a level-8 party (about a third of its HP) | See "Falls" below. The arrival 850 over X1's ground costs each member about 10/256 x 850, a third of its maximum HP. Measured on a level-18 party: 42/130, 19/68, 26/87, 16/58 lost (28-32 %). Feather Fall prevents it (the engine's rule). |
| D-6.4: three zones | x > 3,072: X1 by the Witch Tower. Between -3,072 and 3,072 (the half-way cloud, which spans -1,024 to 1,024, plus the inner 2,000 of each span): Lake Darzog on X2, at the surface, no damage. x < -3,072: X3, which **is not built**, so these falls land in Lake Darzog too, the cheapest choice to reverse (below). |

## Falls (E4): what exists, and what was built

What the engine has:

- No indoor trigger volume. `trigger_volumes` exists only on outdoor scenes (`OutdoorSceneYml.cpp`).
- `evt.GetPartyPosition()` exists, and so do timers and floor step events.
- `evt.MoveToMap(..., map, {direct = true, keepHeight = true})` exists: Celeste's fall, without the
  leave-the-dungeon dialogue, arriving in the air (`EventRuntime.cpp` near 7464).

What was built (`wiring.yml`):

- **`evt:fall_check`:** a one-second timer. Under z -1,000 the party has left the clouds, and it is moved by zone
  through A3's `Xeen.skyFall`.
- **`evt:fall_floor`:** the room's own floor at -6,000 runs the same move without the height test, for a fall the
  check misses.

The party is caught in mid-air. The timer catches a fall from the highest island (896) by about -3,000 at worst, so
it never lands in X8 and takes no indoor fall damage there.

Landings:

| Zone | Landing | Note |
| --- | --- | --- |
| X1 | (11264, -7936), ground 768, facing 1752 (308 degrees, toward the door) | 1,100 north-west of XD-04's door (door at (12288, -9261); XD-04's own exit lands at (12288, -8987, 850)). The ground is clear: the nearest props are 7rock08 at 922 and dec06 at 1,374. The party arrives at 1,618 and falls 850. |
| X2 | (-10240, 8448), water 576, facing 256 (45 degrees, toward the north-east shore, about three cells away) | A5's point, at the surface. |

**Blocked on A3:** `Xeen.skyFall` (xeen_common.lua:199) calls `evt.MoveToMap(x, y, z, yaw, 0, 0, 0, 0, map)` with
no options. From a BLV onto an .odm the engine then asks "leave the dungeon?" and sets the party on the ground, so
there is no 850 fall and no damage.

- The fix is one line: `evt.MoveToMap(x, y, z, yaw, 0, 0, 0, 0, map, {direct = true, keepHeight = not onWater})`.
- It was requested through A6. `output/studio_cal/x8/patch_skyfall.sh` applies it to the scratch root only. With it,
  both fall playtests pass.
- From `assets_dev`, until A3 makes the change, a fall shows the transition dialogue and lands without damage.

**Reversing the west zone when X3 exists:** in `gen_objects.py`, give `FALL_LUA` a third branch,
`elseif x < -3072 then Xeen.skyFall(<X3 point near XD-11's door>, "xeen_x3.odm", false)`, then run `v.sh` and `b.sh`
and reinstall. Everything else stays.

## Arrivals

The studio has one start per map. The second arrival is given by explicit coordinates in the other map's exit, as D-4
does for XD-10.

| From | Arrives at | Facing |
| --- | --- | --- |
| XD-04's cloud stair (A7) | **(11520, -6802, 0)**, the head of the Witch Clouds' stair (the map's start) | north: 90 degrees, MoveToMap direction 512 |
| XD-11's Stairway to Heaven (A8) | **(-10752, -4337, 0)**, the head of the High Magic Clouds' stair | north: 90 degrees, MoveToMap direction 512 |

## Fly and spells

Fly cannot be cast on any BLV: `spellWorldAvailabilityFailure` (`PartySpellSystem.cpp:343`) refuses it on an indoor
map, and an open-air BLV has no outdoor flight. So X8 has no Fly without a new word, and E7's `allow_fly` is not
needed here. The L1's `no_fly` stays in project.yml as a record.

If the world lists X8 in `world.yml` `openAirMaps`, the outdoor spells would work here and Inferno would not. That is
the orchestrator's file, so it is a request: Meteor Shower, Starburst and Armageddon would work, and so would the
monsters' Meteor Shower. Without it the map keeps the indoor spell rules.

## Counts (MAPS section 0: party 18 -> 20, monsters 14-30, Cloud Golem 50 rare, 60 placed, kill XP 8.1k, treasure 3)

60 monsters are placed, all as fixed monsters (no spawn markers), and 60 are present at load in every run:

| Where | Monsters |
| --- | --- |
| The Witch Clouds (29) | 12 Harpies (11520, level 14), 16 Harpy Hags (11521, 18), the Harpy Queen (11522, 24) on her great nest with five Hags |
| The High Magic Clouds (29) | 15 Flying Feet (11600, 18), 14 Guardians (11601, 24) |
| The golem heights | 2 Cloud Golems (11592, 50), `immobile`: a trap (D-1.2), counted apart |

Kill experience, monster_data XP 336, 504, 816, 504, 816:

- 12 x 336 + 16 x 504 + 816 + 15 x 504 + 14 x 816 = 31,896 for the party: **7.97k per member**, against 8.1k (98 %).
- The golems add 2 x 3,000 = 1.5k per member, in A2's trap column.

Treasure:

| Chest | Kind | Contents |
| --- | --- | --- |
| The Harpy Queen's hoard | ch2 | treasure level 4, 3 items, 600 gold |
| The sorcerer's chest on the observatory porch | ch1 | level 3, 2 items, 300 gold |
| The cache at the golems' feet | ch3 | level 4, 3 items, 500 gold |
| The lantern cloud's chest | ch1 | level 3, 2 items, 250 gold |

The two offering statues each give one random item of level 3 to Crusaders. Map treasure level 3.

## Size

- Islands: 13, 123.9 M square units of cloud. They spread over 59.5 by 48.8 cells (30,464 by 25,000).
- The room: 78 by 64 cells.
- Heights: islands from -256 (windward rock) to 896 (the explorer's rock); spires up to 1,920.

## Points of interest and lines

| Thing | Where | What it does | Source |
| --- | --- | --- | --- |
| Three harpy nests | `platform:nest_1`, `nest_2` (spires), `nest_3` (perch) | "Harpy Nest. Destroy?" (Yes/No); the nest goes and A3's `x8-sky.nest_N` pays 500 XP | xeen/aaze0025:5 |
| The explorer's statue | `deco:explorer_statue` (7dec55) on the explorer's rock | A3's `x8-sky.explorer_statue`: Super Explorer, +2 Speed ("I dub all who find me 'Super Explorer'.") | xeen/aaze0025:7, :6 |
| Rhyming statue 1 | the witch's perch | "Golem, Terror, and Yak it's told have credits for King to hold." | xeen/aaze0025:1 |
| Rhyming statue 2 | the rhyme garden | "The Clerics of Yak you must outwit Taxman then must have his bit." | xeen/aaze0025:2 |
| Rhyming statue 3 | the observatory isle, by the long bridge's west head | "Conquer terror and then you'll see Illusion holds Magic's key." | xeen/aaze0025:4 |
| Offering statues (2) | the offering terrace's upper step (sta1a) | Crusaders (M4 done, 110047): an item, once each; others: 30 air damage and "It is kept for Crusaders." | "Offering", xeen/aaze0025:9 (behaviour ours) |
| The telescope | `platform:telescope` on the observatory porch | A message: the lagoon and the Tower of High Magic, Lake Darzog, the Witch Tower | ours |
| First arrival | load, once | "The cloud holds under your feet like stone..." | ours |

The rhymes can be read by anyone. L1's Linguist gate (Castle Burlock's Book of Languages) has no award or bit yet,
so it is a request to A3, not a stand-in.

## Textures (31 distinct, 21 of them the three chests'; new: 2)

| Texture | Where |
| --- | --- |
| **xccloud** (new, 256 square, tile) | the tops of the islands and the cloud lumps |
| **xccloudsd** (new, 256 square, tile) | sides, undersides and roots |
| 7tws1f (MM7 Celeste's marble) | causeways, ramps, stairs, plinths |
| t66floor (MM8) | bridge decks |
| hwm2rf (MM7) | rope rails, bell and lantern posts |
| gcav1flr (MM8) | spires, the eyrie's broken rock |
| gkp1flr (MM8 straw) | the nests |
| hwm2wall (MM7 Bracada) | the observatory |
| xtslate (towers kit) | its dome |
| xngong (XD-03) | the brass telescope |

The new textures were made with Codex through `xtex.py --project output/studio_cal/x8/tex`: one call per image,
references sky/cloudsabove, sky/skycity01, sky/stormclds and mm7/7tws1f, a seam pass, and a 3x3 check in
`tex/sheets/` (seam 1.04/1.03 and 0.97/1.03). They are installed in `assets_dev/worlds/xeen/textures_x4` (BC7) and
`textures_x2`, with sources in `assets_source/worlds/xeen/textures_x4/`. A6 registers them in `source/textures.yml`.

## Presentation

- Music 25 (A2's row).
- Sky `xeencloud`, outdoor view, daylight.
- No weather: the islands are above the rain.
- Ambient sounds: `whistling wind` over each archipelago, the half-way cloud and the eyrie; `7chimes` in the rhyme
  garden.
- Four pulsing lantern lights round the lantern cloud's candle stands (dec02).
- No lighting bake: indoor bakes are opt-in, and the open air takes the daylight block.

## Checks

| Check | Result |
| --- | --- |
| `validate` | L2, L3, L4: no issues (against `assets_dev`) |
| `fmt --check` | clean |
| `build` (against `assets_dev`) | 1 room, 1,098 faces, 17 events, 4 chests, 60 monsters; byte-identical to the scratch build |
| `audit --world xeen --reach --solve` | 0 pairs in one plane; on foot from the start, 1 of 1 sectors; info only: `xccloudsd` squashed on four tapered faces (meant, `uneven`), and the build's "silent click" note on the offering statues (their `else_effects` Lua speaks, which the build cannot see) |

Build warnings that stay:

- Two islands (the explorer's rock, the golem heights) "rest on nothing": they float. Their roots are smaller than
  they are.
- "Liquid and flow: 22 of 28": the clicked faces carry the event bits, and no liquid is used.

Playtests (`output/studio_cal/x8/run.sh`, headless, `build-xeen/game/openyamm --world xeen --map xeen_x8.blv`):

| Playtest | Steps | What it covers |
| --- | --- | --- |
| `playtest.yml` | 144 | Every island, bridge and causeway; the three nests (bits 115021-115023); the explorer (115020); the three rhymes; the telescope; both offering statues (refused, then given); the four chests |
| `playtest_fall.yml` | 9 | Off the half-way cloud into Lake Darzog, at A5's point, HP full |
| `playtest_fall_east.yml` | 10 | Off the Witch landing to X1 by the Witch Tower, HP lost, nobody dead |
| `playtest_hostility.yml` | 27 | Every kind hostile, none fighting another |

Results:

- **From the scratch root:** 4 of 4 each. The scratch root is a hard-link copy of `assets_dev` plus the X8 map_stats
  row and the `skyFall` patch. Logs in `output/studio_cal/x8/xrun/run_*` (`four.out`).
- **From `assets_dev`:** blocked until A2's map_stats row for 9106 exists ("cannot resolve map world" without it)
  and A3's `skyFall` fix is in.

## Dressing exceptions

None. `oymap audit --world xeen` on the installed map (merge point 5's oymap, with D-7's dressing audit) lists no
dressing warning:

- Statues stand on plinths, out of the walking lines.
- The nests and the great nest are low (32) and clicked.
- The candle stands stand round the lantern cloud's middle.
- No barrels, sacks or crates.

## Words the studio lacked (workarounds)

- **A fall zone or trigger volume indoors:** built as a timer plus the room's floor step (above).
- **Monster barriers** (MM9's `actor_barriers`, invisible to the party): the studio cannot write them. Flying Feet
  and Guardians walk, and one that chases the party off an edge falls to the safety floor and stays there.
  - The groups stand at least 300 inside the rims.
  - The golems are `immobile`.
  - Harpies fly.
- **A second arrival:** see Arrivals.
- **Tapering blocks:** `top_size` works only on rectangles, and only with a `facing` of 0. Turned, its faces are not
  flat on whole units, and the build refuses them. So the islands' sides are upright and their roots are square
  inverted pyramids. A tapered outline (an island whose sides lean in under it) would read better.
- **A door picture on a platform:** the observatory is a solid tower with no door. Its chest and telescope stand on
  its porch.

## For the user when playing

- The arrival from the Witch Tower's roof: the cloud stair's head, the harpies across the landing, and the spires
  and the long bridge in view.
- The long bridge from the observatory isle's east head: the signature view.
- Falling off:
  - east, you land by the Witch Tower and lose about a third of your hit points (none with Feather Fall);
  - from the half-way cloud, you land in Lake Darzog (X2) unhurt;
  - west, you land in X3's lagoon by the Tower of High Magic, unhurt (water).
  - Until A3's one-line fix, a fall asks to leave the map and lands without damage.
- The golem heights: a dead end you see from the long ramp, with two Cloud Golems (level 50) that do not move. Walk
  round them for the cache.
- The islands' undersides: inverted cloud pyramids, a known limit (above).
- The Flying Feet and the Guardians wear the Plane Guardian stand-in (A2/S: "model: new").

## Session 5 (A6, 2026-11-20)

- **From `assets_dev`** with A2's row 9106 and A3's `Xeen.skyFall` (`{direct = true, keepHeight = not onWater}`):
  `playtest`, `playtest_fall`, `playtest_fall_east`, `playtest_hostility` **4 of 4 each**
  (`ASSETS=assets_dev N=4 output/studio_cal/x8/run.sh`, logs `output/studio_cal/x8/xrun/run_152929`).
- **The west zone (D-6.4) now falls to X3** (installed by A5): `gen_objects.py` `X3_LANDING` (1536, -1280, 864, facing
  1120) in the lagoon east of the Tower of High Magic's islet, about 1,300 from XD-11's door, on the water (no damage;
  no actor within 12,000; the islet itself is the tower's footprint with no room to land), `X3_LIVE` from the
  installed map; reinstalled (`ROOT=assets_dev b.sh`). New `playtest_fall_west.yml` (off the Magic stair landing's
  west edge): **4 of 4** from `assets_dev` with X3's row 9101 (session 6, `xrun/run_161028`; pass `ASSETS` as an
  absolute path, run.sh changes directory). An earlier `build-xeen` binary (15:52) crashed on exit after every
  scenario's last step (`~GameApplication`); the 16:06 binary does not.
- **No lighting bake**: X8 is an open-air BLV with no lamps (0 lights); its light is the scene's daylight by the hour.
  A Cycles sidecar (version 1) on a map open to the sky would draw noon light at night (devdocs/INDOOR_BAKED_LIGHTING.md,
  "Daylight pages"); `stale_bakes.py` lists nothing for it.

## 2026-11-25, agent xeen-fb4-dungeon2 (D-151)

- The ways back down are the stairs back (gated as the way up) and the falls. The stair of cloud at each arrival
  stair's foot leads down only as the way up allowed: `evt:down_stair_landing` with qbit 111240 (M12 key bought) or
  111260 (M13 done), else "Below the step the cloud thins over the Tower of High Magic. Its wards let down only those
  who hold the Enchanted Key from the Cave of Illusion."; `evt:down_witch_landing` with 110046 (XD-04's climb gate),
  else "The clouds answer to the Head Witch. While she lives, they will not bear you down." (status line;
  `gen_objects.py`). `playtest_down*.yml` try each stair first without the qbit.
- The stair-of-cloud panels' 48-wide ends are plain cloud (`end_surface`): the picture was cut on them
  (`textures.feature_cut`, 4 audit errors). Audit 0 errors, playtests 7/7 from a stage, installed (no bake).

## F70, D-181 (agent xeen-fb5-dungeon, 2026-11-26)

- `rail_posts()`: each rope bridge's two rails are tied at both ends to a post on the island (8 bridges, 32 posts;
  `tools/xeen/check_beam_ends.py` 32 errors to 0). D-181: the two offering statues are `7dec55`, not `sta1a`.
