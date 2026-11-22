# FD-03 Darkstone Tower, L4 (lane A7, seventeenth session, 2026-11-21)

Map 9181, class M, on X5, `xeen_fd03.blv`, music 43, `world: xeen`. Briefs: `output/studio_cal/a7/phase6_common.md`
(and phases 5, 4, 3), the FD-03 section of `output/studio_cal/a7/phase6_maps.md`, D-57
(`devdocs/xeen/mockups/act6_a7_decisions.md`), the graph `devdocs/xeen/mockups/act6_graphs/fd03.graph.yml`.

## How to rebuild

- Every project file is written by `output/studio_cal/fd03/tools/gen.py` (`--levels` writes L1-L3). Never hand-edit
  them; diff L4 against `L4/.oymap/last` before rerunning after a hand edit. Then
  `oymap record devdocs/xeen/briefs/fd03/L4 --author agent:xeen-a7-fd03 --label "..."`.
- `bash output/studio_cal/fd03/cycle.sh`: gen, fmt, validate and build against the scratch root
  `output/studio_cal/fd03/root` (it holds the three new textures), install into that root, audit (--reach --solve).
- `python3 output/studio_cal/fd03/tools/gen_tests.py` writes the four playtests from `ids.lock.yml` and the built
  scene's actor order (run it after a build that may move ids).
- Playtests: `ROOT=$PWD/output/studio_cal/fd03/root KEY=fd03 TESTS="playtest playtest_fall playtest_exit
  playtest_hostility" N=4 bash output/studio_cal/a7/xfour.sh` (logs in `output/studio_cal/fd03/a7_xrun/`).

## What was built

One BLV of four storeys 768 apart (z 0, 768, 1,536, 2,304) round an open well, inside an octagonal tower of radius
2,048 (exact 45-degree diagonals, so the rings' facing walls are parallel). Each storey has three rings:

- **The rotunda** (apothem 896, 640 high), with the **well** (apothem 384) as a floor hole onto the rotunda below
  (`in: floor` openings, L2-L4) and a parapet 192 high round it; at L1 the well's foot is sunk 192. The gongs (XD-03's
  `xngong`) hang on the rotunda's east (L1) or west (L2) wall, both on L3, each between two niches 192 wide cut 128
  into the wall (the hidden guards).
- **The ring gallery** (apothem 1,088 to 1,440): two arcs (west, east) and a gap room at the stair side: the passage
  from the rotunda to the stairwell (L1, L3 south; L2 north) or, one storey up, the landing above it.
- **The outer ring** (apothem 1,504 to 2,048): the door hall (L1 north), the stairwells, the side rooms (forge L1
  east, library L2 west, cistern L3 east), the roof stair (L4 north).

**The gongs (D-57 Q15).** Each stairwell is one room open from its storey's floor to the storey above's ceiling. The
flight (24 steps of 32, tread 30, 224 wide) climbs the outer wall to its top step (a platform 768 high,
`platform:topN`, whose step plate calls `m41.gong_voice` before the gong). Beside it is the 512 x 512 gap against the
stairwell's inner wall, under the doorway onto the next storey's landing. **The slab** is a mover: it stands as a dais
128 high on the stairwell's floor, and the gong raises it 640, flush with the storey above. The way in from the
passage enters the stairwell west of the dais, so a party that walks off an unraised top step lands on the dais
(a drop of 640) and steps off it (128) to the floor and out.

**L3's twin gongs (Q15):** two movers in one footprint. `mover:riser3` is the dais, raised 320 by whichever gong is
rung first (half height 448 over the floor). `mover:slab3` lies sunk under the floor and rises 770, to 768, when both
bits are set (a timer handler a second after the second gong, `evt:slab3`, since the gongs' handlers cannot name a
mover in Lua). After both, the riser stays at 448 under the slab.

- Map qbits: 118120 (L1 slab), 118121 (L2 slab), 118122 (L3 west gong), 118123 (L3 east gong), 118124 (the vault's
  force down). Load handlers raise every slab and show the guards whose bit is set.
- The gongs' guards: groups 21 (L1, two Sentries), 22 (L2, two Wardens), 31 and 32 (L3 west and east, two Wardens
  each), `hidden: true`, shown by `{show_actors}` on the ring (D-18). Actors 5-6, 13-14, 25-26, 27-28 in the build.
- **Plaques (Q17):** twelve `xdplaque` panels on the arcs' outer diagonal walls (L1-L3) and four `xdhead` heads (L4).
  Each click shows its row in a message window; the click that completes a storey's four calls A3's
  `m41.plaques_lN` (the columns read down; `plaques_l4` writes autonote 4720). Map variables `plaqueN_i`, `summaryN`.
- **The vault (Q18):** `door:force` (xafield, translucent 0.5, a folding slide-down leaf), "A force repels you."
  (aazex116:0) on its click; a timer drops it when the Onyx Golem (`monster:onyx`) is dead (`ActorIndex`), sets
  118124; down on every load. A T6 chest inside. The skull on its plinth: "The skull is silent." (aazex116:15).
- **The seal (Q21):** `door:seal`, a slide-up leaf of `xdseal` (fitted once) across the roof stair's mouth (the seal
  room's north wall), opacity **0.3**: at 0.15 the tour shot from 3 m showed nothing (an open doorway), so it was
  raised to D-57's 0.3 and the texture re-toned brighter (luma 157) so the veil reads over the dark stone. Clicked or walked into (`touch: true`): `XeenQuests.can("m41.seal")` opens it and calls the hook
  (the Chime taken, 111820, 27,000), else the hook's fail or else text. Open on every load with 111820.
- **The roof (Q20, D-56):** `room:roof_stair` (outer north, L4): through the seal, west along the floor, then 24
  steps east up the outer wall to the head, a platform at 3,072 (`platform:roof_head`) under the open hatch (a ceiling
  level with `sky: true`; `atmosphere.yml` `open_sky: {mode: open, preset: xeen_cloud_sea}`).
  `entrance:p5_stair` = (224, 1904), floor 3,072, facing west (down the stair). The hatch (`exit:hatch`, `evt:hatch`)
  asks the map's own Yes/No with A3's `m41.roof_exit` question "Climb to the Clouds of the Ancients?" (D-66: a roof or
  hatch exit into a BLV asks; no hook, so nothing before it, D-65); Yes moves at once (`{direct = true}`) to P5's
  `entrance:fd03_roof` (4608, -3968, 0) facing north, No stays. P5 installed 06:41 (A5); the twentieth session dropped
  the `p5_open` seal.
- **Door to X5:** `entrance:x5_door` = (0, 1792), floor 0, facing south, in the door hall 256 inside the tower door.
  Quiet: the door hall's two ways are shut doors (the inner gate's two leaves, the east way's one leaf, D-57). The exit
  (`exit:door`, the `exit` preset, aazex113:0) names X5's `entrance:fd03_door` (-4608, 2560, 1504) facing 512.

## Counts

- 28 rooms, 28 sectors (29 with the outside), 30.4 M units² of floor (`oymap metrics`: M's band 30-90; under the
  graph's estimate of 38 because the outer ring is used only where rooms stand).
- 45 monsters (D-57 Q14): Onyx Sentry 11585 x20, Onyx Warden 11586 x16, Sky Golem 11594 x8 (L3-L4), Onyx Golem 11584
  x1; by storey L1 10, L2 10, L3 12, L4 13; 8 of them the gongs' hidden guards. 60.70k per member.
- 4 chests T6 (forge, library, cistern, vault). 12 door records: 8 doors (two of them pairs) and 4 movers.
- Textures (about 19 distinct): d29's gston1wl, gtrlwal1, gkp2ceil, gcav1flr, gston1fl, gcst2cel, gcstdoor, gkp4-bs;
  gkp1ceil (the library's shelves), trim9_32 (door edges), X5's hkm3b frieze (the door hall's band), XD-03's xngong,
  xafield (reused, D-51), MM8 gkp103a/gkp103b (the two pairs); new: xdplaque, xdhead, xdseal.

## New textures (for A6's registry; masters for `assets_source/worlds/xeen/textures_x4/`)

Made by Codex through `level_generation/textures_xeen/xtex.py --project output/studio_cal/fd03/tex` (specs.yml,
raw/, finished/), installed into `output/studio_cal/fd03/root` only:
- `xdplaque` (128 x 128, a picture laid once on a 256 x 192 panel): an old bronze plaque, four rows of raised letters.
- `xdhead` (128 x 256, once on a 192 x 256 panel): a black stone head with an open mouth in granite ashlar.
- `xdseal` (128 x 256, once on the 224 x 384 leaf, drawn at 0.3): pale silver-lilac heat-haze ripples (v1 re-toned
  twice against gston1fl, last factor 1.9, gain 0.57, luma 157, so it reads as a light veil at low opacity).

## Map rows

A2's rows had landed when the build started (2026-11-21, about 03:40): map_stats/bolster 9181, monsters 11585 and
11586. **No test rows** in the root's tables. project.yml's `map_stats` copy: encounter 0, no slots, treasure 6, music
43, lock 20, trap 10, perception 20 (the Act V M rows, as A2's row).

## Original lines

- "Exit Darkstone Tower?" (dark/aazex113:0): the exit preset's meaning.
- "Gong" (aazex113-116:1): the gongs' hover; "A voice booms: "No Sound No Ground!"" (aazex113-116:2): A3's
  `m41.gong_voice`, called by the gongs and the top steps' plates.
- The plaques' rows (aazex113:3-6, aazex114:3-6, aazex115:3-6) and the heads' rows (aazex116:3-6): map text, all
  sixteen copied verbatim from `reference/mm4_5_world_of_xeen/unpacked/text/dark/aazex113-116.txt.json` lines 3-6
  (D-63 9: the source's trailing `-` kept, nothing added; "Head 13 speaks: T-MEOE-FENN-TEAO" with no added quotes),
  `ROW_LINES` in gen.py; checked 16/16 against the source (eighteenth session). Read down, each storey gives one
  message; L4's is the terminal's code for FD-04.
- "A force repels you." (aazex116:0), "The skull is silent." (aazex116:15).
- New map lines (no source text): the arrival line "Darkstone Tower: black stone, polished like a mirror. Far above,
  the stair to the Clouds of the Ancients." (The hatch's sealed line went with the seal, twentieth session.)

## Exceptions

- None (the sealed hatch's `p5_open` warning went with the seal, twentieth session).

## Blocked on

- Nothing (P5 installed, the exit to X5 by name: twentieth session). Earlier: X5's `door:fd03` to
  `entrance:x5_door`; register xdplaque, xdhead, xdseal.

## DECIDE (cheaper-to-reverse option taken)

- The roof stair's head is a platform in `room:roof_stair` (the graph's `room:roof_head` merged into it), since a
  straight 24-step stair could only fit in the outer north with its foot reached from the seal room's side.
- L3's ground: riser + slab (two movers), the slab a second after the second gong (timer).

## Measurements and checks

- Audit (`output/studio_cal/fd03/audit.txt`, --reach --solve, dressing on): **0 errors**, 1 warning
  (`state.never_set`, the sealed hatch: see Exceptions); every sector reached with the doors and movers open.
  `fmt --check` clean; L1-L4 validate clean.
- `playtest_exit.yml`: the leave window's OK lands on X5 at **(-4608, 2560, 1505) facing 512** (measured).
- `playtest_fall.yml`: off L1's unraised top step the party lands on the dais at **z 128** (294, -1888), steps off to
  the floor and out to the passage, then the gong and the climb to L2 (z 768). At L3 after one twin gong it lands on
  the riser at **z 1984** (448 over L3's floor), steps off and out, then the second gong and the climb to L4 (2304).
- `playtest_hostility.yml`: nothing targets the party for 10 s at `entrance:x5_door`, nor for 10 s at
  `entrance:p5_stair` with the seal broken and the seal room's Sky Golems alive; all 45 golems hostile (hidden guards
  included); spawned golems never target each other.
- `playtest.yml`: the whole path, the reload (ran: "RELOAD ok") keeps the four movers, the force and the seal open.
- **Every playtest 4 of 4** from the scratch root (`output/studio_cal/fd03/four_final.out`, logs
  `output/studio_cal/fd03/a7_xrun/<test>_<n>.log`): playtest 127/127, playtest_fall 60/60, playtest_exit 15/15,
  playtest_hostility 37/37, each run 1-4.
- Headless runs: the scratch root's own `worlds/xeen/world.yml` is a real copy of assets_dev's without the
  `openAirMaps` entries `xeen_d7.blv`, `xeen_p1.blv` .. `xeen_p4.blv` (named at 03:53 but not installed: with them every
  headless game fails "could not load headless gameplay data", from assets_dev too). The lead keeps or drops this with
  the root.

## What the user should look at

- The seal at 0.3 reads only as a faint milky veil over the stair's rubble (shots3/): a tell close up, easy to miss
  from across the room. If it should read more, the next step is a stronger ripple in `xdseal` (0.3 is D-57's top).

- The gong well from the L1 rotunda, the slabs rising beside the flights, the seal's ripple (0.3) from 3 m.
- The floors are d29's gkp2ceil (riveted copper plates, as the notes' palette names it) in the rotundas.
- Pictures: `output/studio_cal/fd03/shots/`, `shots2/`, `shots3/` (contact sheets `sheet1-5.jpg`); dark rooms are only
  the missing bake.

## Installed (2026-11-21, lane A7 lead, seventeenth session)

- Rebuilt in the root with merge point 25's oymap (03:57:50; build 1 warning: P5's `entrance:fd03_roof` unknown while
  P5 is not installed; audit 0 errors, the one kept warning above). `xdplaque`, `xdhead`, `xdseal` installed in
  `assets_dev` (`xtex.py install --root assets_dev --world xeen`; masters in `assets_source/worlds/xeen/textures_x4/`).
  Installed with its bake 04:10:49 (`install_baked.sh`, profile `tools/lighting/baked_indoors/profiles/xeen_fd03.yml`),
  stale bakes 0. Audit from `assets_dev` the same (`output/studio_cal/fd03/audit_assets_dev.txt`). **16/16 from
  `assets_dev`** (playtest 127, fall 60, exit 15, hostility 37; `output/studio_cal/a7/s17_fd03_four.out`), with
  `assets_dev`'s own world.yml (its `openAirMaps` list did not stop these runs on merge point 25).
- Open (S bound `Xeen Golem D` / `E` in session 7: done); the hatch (A5's P5 install, then drop the `p5_open` condition on `evt:hatch`); the
  exit to X5's `entrance:fd03_door` by name when A6 adds it.

## Eighteenth session (2026-11-21, lane A7 lead)

- D-63 9: the sixteen plaque and head rows verbatim from dark/aazex113-116 lines 3-6 (`ROW_LINES` in gen.py), checked 16/16 against the source in the built wiring; `playtest.yml` asserts the heads' rows 13-15 and the fourth head's status line exactly. The hatch stays sealed: P5 is not installed (`xeen_p5.blv` absent at 05:40).
- Installed with its bake 05:18:16 (`output/studio_cal/a7/s18/install_queue.sh`), stale bakes 0; audit from `assets_dev` 0 errors, 1 warning (the sealed hatch's `p5_open`) (`output/studio_cal/a7/s18/audit/fd03.txt`); **16/16 from `assets_dev`** (playtest 127, exit 15, fall 60, hostility 37; `output/studio_cal/a7/s18_four.out`, merge point 25/26 binaries).

## Twentieth session (2026-11-21, lane A7 lead; oymap of merge point 27)

- P5 installed (A5, 06:41): `p5_open` dropped; `evt:hatch` asks the map's own Yes/No "Climb to the Clouds of the
  Ancients?" (D-66; A3's `m41.roof_exit` question) and on Yes moves at once to P5's `entrance:fd03_roof` (4608, -3968, 0)
  facing north. `exit:x5_door` names X5's `entrance:fd03_door` (same point, facing 512). The other way, P5's `door:fd03`
  moves to this map's `entrance:p5_stair` (224, 1904, 3072) facing 1024 (P5's built Lua, checked).
- `playtest.yml` answers the hatch No (stays); new `playtest_roof.yml`: from the head (seal broken) No stays, Yes lands
  on P5 at the arrival, measured with the facing. Built into `output/studio_cal/a7/s20/fd03/`: BLV and scene byte for
  byte the installed ones (no rebake; stale bakes 0), the Lua differs by the hatch only; Lua and studio file installed
  06:51:18. Audit from `assets_dev` 0 errors, 0 warnings (`output/studio_cal/a7/s20/audit/fd03.txt`). **20/20 from `assets_dev`** (playtest 131, exit 15, fall 60, hostility 37, roof 29; `output/studio_cal/a7/s20/four_fd03.out`).

## Twenty-seventh session (2026-11-22, lane A7): Darkstone is dark (D-89 identity); tests

- `project.yml` `identity: {shape: tower, family: d29, seen: [...]}`. D-89 2.2 (FD-03 row: "pale for Darkstone"):
  the halls' pale grey-green granite (`gston1wl`) is d29's dark rubble (`gtrlwal2`), the pale fan-paved ceilings
  (`gston1fl`) the riveted dark iron of `gcst2cel`, the two plank pairs steel leaves (`crsmdr1`). The well already
  runs open through every storey. No new texture outside d29 but `crsmdr1` (MM8). Before/after
  `output/studio_cal/a7/s27/fd03/before_sheet.jpg`, `after_sheet.jpg`. A true black ashlar would need a new texture
  (A6); not asked.
- `playtest.yml`: the seal's refusal ("An invisible seal prevents passage.") is A3's failText without `fail_status`, a
  window: gen_tests.py asserts the window again (s26 had made it a status-line read, which found it empty).
- F14: `check_drops.py` no longer lists the well's foot (the parapet round every well hole closes it; the check now
  sees blocks standing on a floor).
