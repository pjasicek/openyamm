# P5 Clouds of the Ancients: L4 notes (lane A5 sub-agent `agent:a5-p5`, 2026-11-21)

P5 is Act VI's finale (M42, party 61-65): one ring of cloud road above Darkstone Tower, past three Rest Stop huts, ten
billboards and the closed observatory, to the Dragon Pharaoh's shrine, the ending cinematic and the wedding. It is
built from the approved L1 (`../L1/`) with D-56 applied (`../L1/D56_DECISION.md`, which wins).

**Not installed** (blocked: FD-03 not installed, the world's decorations not read by the indoor studio). It is built and tested in the scratch root `output/studio_cal/p5/root` only (a hard-link copy of
`assets_dev` with copied `worlds/xeen/data_tables` and `world.yml`, `xeen_p5.blv` added to the copy's `openAirMaps`;
`output/studio_cal/p5/setup_root.sh` remakes it). See "Open items" for what keeps it from being called done.

## Route: the studio (X9's)

- **The room:** one open-air room, `room:air`, from the safety floor at -6,000 to the sky at 6,400; walls, floor and
  ceiling are sky faces.
- **Atmosphere:** `open_sky: {mode: open, sky_texture: xeencloud, view: outdoor, view_distance_scale: 1.5}` and X9's
  daylight block; no weather (D-56 Q9).
- **The clouds:** every pad is a hanging platform with its L1 outline (`geom.blob`), cloud top `xccloud`, sides
  `xccloudsd`, two or three flared roots. The shrine's cloud is 512 above the crown and its underside shows.
- **The road and the causeway:** cloud slabs with a cloud top (cloud road), 8 over their pads at the ends, climbing 64 a
  pad to 448; the causeway the same (not a paved plaza, D-56 9). A dashed centre line of cloud-stone flags (`7tws1f`,
  X9's), 256 long every 512, 48 of them, from the crown's road start to the shrine's paving.
- **Board lobes:** seven boards stand on a lobe of cloud 1,280 wide, from 640 before their face to 384 behind it, 4
  under the road or pad they join (no faces in one plane); their legs are off the walking line.

The scripts are in `output/studio_cal/p5/tools/` (L1's `design.py`, `geom.py` unchanged):

| Script | Writes |
| --- | --- |
| `gen.py` | rooms.yml for L3 and L4 (and L3's start); the texture table `BOARD_TEX` (one line per board) |
| `gen_plan.py` | plan.yml and project.yml for L2 to L4, from L1's |
| `gen_objects.py` | objects.yml, wiring.yml (with the cinematic) and atmosphere.yml; the switches |
| `gen_playtests.py` | the ten playtests (needs the build's ids.lock.yml and Lua) |

| Shell script (`output/studio_cal/p5/`) | Does |
| --- | --- |
| `setup_root.sh` | remakes the scratch root from assets_dev |
| `v.sh [root]` | generate, fmt, validate |
| `b.sh` | v.sh, build into `build/` against the scratch root, playtests, fmt, install into the scratch root only |
| `a.sh` | the audit (`--reach --solve --dressing --lights --doors --textures`) |
| `run.sh` | the playtests N times through lane A5's game slots (`ASSETS`, `TESTS`, `N`) |
| `stage_install.sh` | not run: a hard-link stage, build, install, audit, playtests, then with `INSTALL=1` new file + rename into assets_dev |

There are no hand edits: the generators are the source.

## What D-56 asked, and what was built

| D-56 | Built |
| --- | --- |
| 1. One ring, no monsters, falls to X5 | The ring as L1 (29,137 to the dais, road spans 1,512-2,200, causeway 1,373). No hostile monster. Falls through A3's `Xeen.skyFallTo("p5")`. |
| 2. The note at the start | A plank on a post at (4096, -4224), A3's `m42.pharaoh_note`. |
| 3. Three peaceful, placed, unkillable figures | The Pharaoh 11919 behind the dais (0, 192), Roland 11920 and the wedding Kalindra 11921 under the pavilion (±224, 960), immobile, peaceful, group 50 / 51; the couple `hidden` until state:wedding; `evt:figures_load` makes all three unkillable (`SetMm9ActorCanReceiveDamage(ActorIndex(...), false)`). Behind the FIGURES switch. |
| 4. Cube and Scepter in the hands | Waits on S's decorations (DECO switch); `evt:hands_filled` (the cinematic's first cue) is written when they exist. |
| 5. The ending's order | The shrine's click calls only A3's `m42.shrine`, which takes the items, sets m42.done, gives award 417 and 40,000 and plays `unification` with A3's global done event 42149 (`m42.ceremony`, the text once). The voice and the subtitle come from the cinematic's cues only. |
| 6. Fade to white | Since merge point 24: the fade out into the sky (19.5 s) and the fade in on the pavilion (24 s) carry `color: [255, 255, 255]` (`FADE_COLOUR`); the first fade in is from black. Seen white in a visible run (`output/studio_cal/p5/cert_s17/sheet.jpg`, frames 10-11). |
| 7. The disc | `platform:disc` (1216, 320), r 192, cloud-stone; hidden until state:wedding; click: A3's `m42.disc` (its `requires` is m42.done), then a move inside the map to entrance:fd03_roof facing north. |
| 8. Textures, Dungeon M | 30 named textures plus the ch3 chest's family: about 33 distinct (cap 45); new: the lane's 12 (`xp5brd`, ten fronts, `xp5rest`). No `xp5gold`: the shrine's paving and dais top are MM7's `7tws1h` (pale gold Celeste stone), the dais's sides `7tws1g` (its medallion trim, one 64 band). |
| 9. Concept corrections | Shrine cloud at 512 with its underside showing; the observatory on the north road's widening, drawn once, no banners; the dais 64 high (the hands are S's, on it); the Pharaoh behind it, the couple under the pavilion; the causeway cloud road; the huts at the plan's scale (768 wide, 384 high). Board grounds: the lane's faces. |
| 10. Falls in D-54's shape | Three playtests (ring, causeway, shrine); see "Checks". |

**The stair house** (D-56 A7: a copy of X5's crown): 16 sides of radius 448 at (4608, -4864), X5's black stone
`gtrlwal1` 512 up (192 more sunk in the cloud), the skull frieze `hkm3b` (one band 256), a slate cone of 1,562
(`xtslate`; two square pyramids, one turned 45 degrees, sized so every face stays flat). Its door on the north face
(`7solid01`, X5's door, a plain dark leaf 256 x 448). Arrival `entrance:fd03_roof` (4608, -3968, 0) facing north.

**Boards:** each a face 1,024 x 512, its bottom 256 over the cloud, on three plank legs (the build stands a block on
three legs or more): the lettered front (`fit`, once, whole) and 4 behind it the blank board, ends in plank. **Rest
Stops:** plank hut (back wall 768 x 384, sides 480 deep, shingle roof `pxshings`), a plank bench along the back (S's
bench decoration replaces it when it exists), the REST STOP sign 512 x 128 (`xp5rest`, once) over the front.
**Observatory:** 16 sides of radius 576 at (0, 4672), MM8's pale temple ashlar `gtempw1` once up its 1,024 (lane, sixteenth session: MM7's `7tws2` read brown in game), a stepped dome of six rings
of weathered metal (`gn_mtl03`), its door on the south face (`cwdr`, MM7's stone-framed door with the orb, once).
**Shrine:** a 16-sided paving of radius 768 round the dais (8 high), the dais 1,024 x 704 x 64 facing south.
**Pavilion:** four gilt posts (`ctflor5`), a white canvas roof 1,600 x 1,088 at 512 (`tentrf1`), canvas walls on the
north, west and east (`tentwal1`, once up), open to the south.

**Hover and click:** every board's two faces and each hut's sign, sign back and back wall call A3's hook (the ten
`m42.board_*`, `m42.rest_stop`); their hover titles are A3's texts read from `source/quests/m42.yml` at generation (no
copies of the source strings).

## The wedding state (`state:wedding`)

- `evt:wedding_hide` (load, not m42.done): the pavilion's seven parts and the disc hidden and passable.
- `evt:wedding_show` (the cinematic's cue at 22.5 s, in the fade; a gameplay step, so a skip runs it) and
  `evt:wedding_load` (load, m42.done; every later visit, also after a save made before the ending): the same parts
  shown and solid, the couple's group shown, S's Cube, Scepter and cake when they exist, the gift raised.
- **The gift** (treasure 6, `ch3`, 2,000 gold, three items) stands at (-576, 1352) against the pavilion's back wall,
  clear of the couple and its open side. The studio cannot hide a chest, so it rides `mover:gift`, a stand sunk in
  the shrine's cloud (both unseen inside the cloud) that state:wedding raises 80 (the movers' own "hidden in the floor
  and rises" use). See "Words the studio lacked".

## The cinematic `unification` (`wiring.yml cinematics` → `xeen_p5.cinematics.yml`)

Skippable, 35 s, five shots: (1) 8 s close on the dais, a slow push in; the voice `xeen_vo_pharaoh_unification` and A3's
subtitle (`cinematic_subtitles` of `m42.shrine`) at 1.5 s; (2) 10 s a rising pull-back over the ring; (3) 6 s up into
the sky, fade out at 19.5 s (2.5 s), `evt:wedding_show` at 22.5 s in the dark; (4) 8 s fade in at 24 s on the pavilion,
the Pharaoh turning to the couple at 25 s (a `face` cue); (5) 3 s the party's view. Gameplay steps are only in event
cues. AU's four far bells `xeen_chime_1`..`_4` at 9.5, 11.5, 13.5, 15.5 s (the sleepers answer, shot 2) and `xeen_wedding_fanfare` at 24.5 s (the pavilion fades in); all six sounds start in a minimised run with the audio trace (23rd session, `output/studio_cal/a5/s23/p5_audio/game.log`). The studio writes the file beside the map; A3's hook plays it by name.

## Switches (each flips by itself on regeneration)

| Switch | Off until | Off means |
| --- | --- | --- |
| `gen_objects.FD03` | `assets_dev/worlds/xeen/maps/xeen_fd03.blv` exists and its studio.yml names `entrance:p5_stair` (or `P5_FD03_LIVE=1`) | the stair door gives "The stair house door is shut fast. (Not open yet.)" and does not move; on, `{exit: door:fd03}` (the leave window) and the neighbour's `arrival: entrance:p5_stair` |
| `gen_objects.FIGURES` | rows 11919-11921 in monster_data and their actors.yml bindings (`P5_FIGURES=0` forces off) | no figures. **On**: the rows and bindings exist; the Pharaoh on lane S's figure since 2026-11-21 |
| `gen.DECO` (`DECO_NAMES`) | S's decoration rows `xeen_cube`, `xeen_scepter`, `xeen_stonehand`, `xeen_cake`, `xeen_bench` (S's rows exist since 03:34, with bindings in the world's `models/indoor_decorations.yml`); `P5_DECO=0` forces it off | no Cube/Scepter/hands/cake; the huts keep their plank bench. **Blocked:** the indoor studio of merge point 24 reads only the engine's decoration_data.txt and indoor_decorations.yml, not the world's `decorations` contribution and bindings, so validate refuses the five names (request to A1); the scratch build runs with `P5_DECO=0` until then |
| `gen_objects.FADE_COLOUR` | on since merge point 24 (`[255, 255, 255]`) | `None`: black fades |

## Checks

| Check | Result |
| --- | --- |
| `validate` L2, L3, L4 (scratch root) | no issues |
| `build` | 1 room, 1,545 faces, 1 door (the gift's mover), 42 events, 1 chest. One warning stays (below). |
| `audit --reach --solve --dressing --lights --doors --textures` (project, scratch root) | 0 errors, 0 warnings; faces in one plane: 0 pairs; on foot from the start: 1 of 1 sectors. Info: `click.silent` on the disc (A3's `m42.disc` requires m42.done; the disc is hidden before) |

The build warning that stays: `evt:disc` "when its condition does not hold, a click does nothing": the disc is not
there (hidden, passable) until m42.done, so nobody can click it.

Playtests, headless (`build-xeen/game/openyamm`, merge point 23, `--world xeen --map xeen_p5.blv --asset-root
output/studio_cal/p5/root`), level-61 party without equipment:

| Playtest | Steps | Covers |
| --- | --- | --- |
| `playtest.yml` | 94 | the whole ring from the arrival: every pad, road and the causeway walked; the stair door sealed (status, no move); the note; all ten boards (front and back) and all three Rest Stops (sign and back) give A3's line; the observatory closed; the shrine refused (no m42.done) |
| `playtest_refusal.yml` | 19 | the Cube and the Scepter without the sleepers: the refusal, nothing taken, the couple hidden, the gift down |
| `playtest_ending_played.yml` | 65 | the shrine with everything: `playing unification`, m42.done, the items gone, award 417; at 12.5 s the couple still hidden; at 23.5 s (after the fade's cue) the couple shown and the gift risen mid-visit; the ceremony text once (111841 set) when it ends; the gift looted; the shrine's else_text; a map reload with the state shown and no text again |
| `playtest_ending_skipped.yml` | 56 | the same, skipped at 2.5 s (`cinematic skip`): the state shown and the ceremony text at once |
| `playtest_reload.yml` | 19 | a visit after m42.done: the figures shown, the gift up, no window, the quiet shrine |
| `playtest_disc.yml` | 15 | after the ending the disc gives A3's line and puts the party within 256 of entrance:fd03_roof |
| `playtest_fall_ring.yml`, `_causeway`, `_shrine` | 19 each | off the east road, off the causeway, off the shrine's west rim: on X5 within 256 of A6's entrance:p5_fall (-4608, 2560) (landed exactly there, facing 1536); every member's HP 345, 154, 216, 144 at 0.5 s and again after 20 s on X5 (D-54) |
| `playtest_hostility.yml` | 20 | nothing hostile on arrival; after m42.done the three figures peaceful (min 1 each), none hostile, none hurt after 12 s |

Results, two runs each, scratch root (`output/studio_cal/p5/xrun/run_030056`): **20 of 20** (every playtest 2 of 2).
The three falls landed at exactly (-4608, 2560, 1505) facing 1536, with the same HP in every run.

## Dressing exceptions

None. No containers but the gift (against the pavilion's back wall); the huts' benches stand against their back walls;
boards stand on lobes off the road, huts on the pads' outer sides; nothing on the walking line.

## Texture fit exceptions

None. Lettered boards and the REST STOP sign are `fit`, once per face (`uneven: true`: the x4 textures of 256 x 128 and
256 x 64 are stretched 4x and 2x on purpose to the 1,024 x 512 and 512 x 128 faces); the observatory's stone and the
pavilion's canvas once up their walls; the skull frieze one band.

## Words the studio lacked (workarounds)

- **A chest hidden until an event** (`show`/`hide` take no chest): the gift rides a mover sunk in the cloud and raised
  by state:wedding. Asked of A1: `hidden: true` on a chest and `{show: chest:x}` would make it plain.
- **An event number fixed by a quest file:** none needed. A3's done event 42149 is a global event, so the map writes no
  done event of its own.

## Open items (owners)

- **FD-03 (A7):** the stair door is sealed until `xeen_fd03.blv` is installed and names `entrance:p5_stair`; then
  regenerate (`b.sh`): the door takes `{exit: door:fd03}`. Down-and-up across the two maps is then FD-03's playtest's.
- **S:** done (2026-11-21): the Pharaoh's figure and the five decorations (`xeen_stonehand`/`_l`, `xeen_cube`,
  `xeen_scepter`, `xeen_cake`, `xeen_bench`).
- **A1:** the indoor studio to read the world's `decorations` table contribution (`world.yml` `tableContributions`,
  `models/decoration_data.txt`) and the world's `models/indoor_decorations.yml` bindings, as the outdoor build does
  (`readWorldTable`); until then validate refuses the five names and P5 builds with `P5_DECO=0`. The left hand
  (`xeen_stonehand_l`) is a sixth name for `DECO_NAMES` when the hands go in.
- **AU:** done: the four chimes and the wedding fanfare are cues (23rd session); a P5 bed list if AU wants one
  (the map uses X8/X9's `xeen_amb_sky` bed, `pan: false`, and two `xeen_sky_gust`).
- **A1:** (1) the fade colour (D-56 6); (2) a chest shown by an event; (3) the certificate and the ceremony window: see
  "A1 findings".
- **A3:** after-lines for the couple and the Pharaoh's P5 talk when wanted (D-47's `npc:` on a placed monster exists
  since merge point 22; the rows' npc 5453 and 5001 carry D5's and DD-03's topics, so P5 sets no `npc` yet).
- **Orchestrator:** `xeen_p5.blv` in `world.yml` `openAirMaps` at the install.

## A1 findings

- **Mid-visit state on an open-air BLV (relay 1): works.** In `playtest_ending_played.yml` the cinematic's event cue
  showed the hidden couple (actor Invisible bit cleared) and raised the gift's mover mid-visit; faces hidden on load were
  shown by the same cue (not assertable headless: no face-visibility assert; walk checks pass).
- **Certificate and the ceremony window (relay 3), from reading `GameApplication::processPendingCompletionCertificate`
  (merge point 23), not observed headless** (the headless runner shows no WinGameScreen): it waits for a pending or
  playing cinematic, but once none is playing it calls `closeActiveEventDialog()`, so it would close the done event's
  ceremony window instead of waiting for it. Repro: `playtest_ending_skipped.yml` in a visible isolated run, or the
  same steps by hand: the ceremony text should stay until closed, then the certificate.

## Session log

**2026-11-21 (A5 sub-agent `agent:a5-p5`).** D-56 read; the relays of A2 (row 9119, rows 11919-11921), A3 (m42 hooks,
global done event 42149, the landing (-4608, 2560)), the lane (textures) and the orchestrator (certificate in
world.yml) folded in. L2-L4 generated; built, audited (0 errors, 0 warnings) and played in the scratch root: 20 of
20 runs (`xrun/run_030056`). Tour `output/studio_cal/p5/shots/t1` (six views before the wedding; contact sheet
`shots/t1_sheet.jpg`): the boards read whole and once, the Rest Stop sign once over the hut, the stair house as X5's
crown. Seen there: the observatory's `7tws2` reads brown-grey rather than pale in this light, and its stepped dome
dark (A6 may prefer another pale stone or a copper-coloured metal; one line each in gen.py). The wedding state was
not toured (asserted headless only).

**2026-11-21 (lane A5, sixteenth session).** The observatory's stone changed to MM8's `gtempw1` (pale ashlar; `PALE`
in gen.py); rebuilt (`b.sh`), audit 0/0, walk 94 and the played ending 1/1 again (`xrun/run_030741`), tour
`shots/s16/` (the observatory pale; the dome's `gn_mtl03` stays a dark weathered copper).

**2026-11-21 (lane A5, seventeenth session).**
- Merge point 24: the fade to white on (see D-56 6), rebuilt; the scratch root remade (`setup_root.sh`: the copied
  tables were older than the world's actors.yml, "unknown actor model descriptor: Xeen Lich D", every run failed to
  load the map) and rebuilt with `P5_DECO=0`.
- **The couple stood on the pavilion roof** in a visible run (the game stands a placed monster on the highest solid top
  over it; headless `report_state` showed z 1,048 after a reload with m42.done). The roof is now shown but never made
  solid (`wedding_show`); the couple stand at z 512 on the cloud after the ending and after a reload (probe
  `output/studio_cal/p5/probe_s17/`). Nobody can reach the roof.
- **The certificate (visible run, `output/studio_cal/p5/cert_s17/`):** the shrine played out (`event 37` from a start
  console file): the white fade, the pavilion, then A3's ceremony window, which stayed for 50 s with no certificate
  over it (merge point 24's wait for an open event window). A second, minimised run with m42.done set and no window
  showed the certificate at once (`cert_s17/b/shot_001.png`: the Xeen painting, the headline, the ending text, the
  OpenYAMM mark). The step "close the window, then the certificate" needs a click a console file cannot give.
- The Dragon Pharaoh now draws on lane S's figure (`xeen_pharaoh.glb`, gold-and-blue skin, nemes and book).
- Playtests 20 of 20 (every playtest 2 of 2) in the scratch root (`xrun/run_034125`).


**2026-11-21 (lane A5, eighteenth session): installed.**
- The orchestrator put `xeen_p5.blv` in world.yml's `openAirMaps` (06:3x); S bound the Pharaoh (11919), Roland
  (11920), Kalindra (11921) and decorations 4017-4022. Built with `P5_DECO=1` (BLV projects take world decorations
  since merge point 26). S's notes applied: the hands look south (`facing` 270, their `yaw_offset` -90); the Cube and
  the Scepter at their hand's own x/y and floor, facing 0 (the bindings raise them 394 and 398 onto the palms);
  Cube, Scepter and cake hidden until state:wedding.
- Merge point 25's hidden chest replaces the sunk mover (`chest:gift`, `hidden: true`, `show: chest:gift` in
  `wedding_show`); the tests walk into its spot before the wedding (passable) and open it by a click after.
- Without `floor_height` the build stands things on the highest floor at their place, hidden structures included:
  the gift chest, the cake and the couple went onto the pavilion's roof (1,048) and the benches onto the rest huts'
  roofs. Each now names its floor (`SHRINE_Z`, the hut's floor). Tours `shots/s18/`, `s18c/`, `s18d/` (`sheet.jpg`).
- `door:fd03` live: `MoveToMap(224, 1904, 3072, 1024, ..., "xeen_fd03.blv")` (FD-03's `entrance:p5_stair`, facing
  west); the walk goes down and asserts the point.
- Merge point 26: the three falls onto X5 now cost 233/105/147/98 of 345/154/216/144 (`FALL_HP`, measured
  `xrun/run_062348`; `P5_FALL_PROBE=1` regenerates them as a probe).
- Installed 06:41 by `INSTALL=1 P5_DECO=1 stage_install.sh` after 20 of 20 in the stage; audit 0/0; every playtest
  2 of 2 again from assets_dev (`xrun/run_064149`). `run.sh` now defaults to assets_dev (it defaulted to the old
  scratch root, now removed).
- Not seen in a tour: the couple under the pavilion after `event 41` from the console (the headless tests assert them
  shown); look in a played ending.

## Nineteenth session (A5, 2026-11-21)

- Roland (actor 2) is NPC 4405 and Kalindra (actor 0) NPC 5001 (`monsters[].npc`, `tools/gen_objects.py`), so their
  m42 topics "The wedding" and "One world" show when they are clicked. Installed 07:43 through `stage_install.sh`
  (20/20 in the stage, audit 0 errors); A3's `tests/scenarios/xeen/hooks_p5.yml` with its talk steps uncommented
  (`output/studio_cal/p5/s19/hooks_p5_talk.yml`) 2/2 from assets_dev.

## Thirtieth session (A5 s30, 2026-11-22; run files output/studio_cal/a5/s30/)
- F16: `door:fd03` carries `screen: {text: 5064}` (`gen_plan.py`): the stair house shows the entrance window with A3's
  "A tower of black stone..." line; the walk selects OK (`gen_playtests.py`; backups `*.pre_s30`). Only the Lua line
  and studio.yml changed (blv, scene, cinematics byte-identical); installed 01:43 by hand from the stage, audit 0.
- Stage 7 of 10: the walk, refusal, both endings, reload, disc, hostility pass; the three fall tests fail on X5 (A6's
  map rebuilt 01:08): two markers at (-960, 4512) and (-672, 4000), about 4,100 from the landing (-4608, 2560), reach
  the party within the 20 s and Brokk dies. Not P5's change: request to A6.
