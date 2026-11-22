# XD-25 Asp Undercroft, L4: notes

Built 2026-11-20 by `agent:xeen-a7-xd25` (lane A7, phase 2) with Map Studio, `world: xeen` from L1, from the MU-6 graph
(`devdocs/xeen/mockups/act2_graphs/xd25.graph.yml`) and D-4's decisions (`mockups/act2_dungeon_decisions.md`, XD-25).
Key `xd25`, `xeen_xd25.blv`, map_stats 9148, music 44, class S, under Asp on X4.

**State: done in the scratch root, not in assets_dev.** Installed only in `output/studio_cal/xd25/root` (hard-link copy
of assets_dev with real `worlds/xeen/maps`, `events/maps`, and real copies of `data_tables/map_stats.txt` and
`bolster_maps.txt` carrying a hand-written row 9148 for testing: A2 writes the real row). The lane lead installs into
assets_dev.

Scratch: `output/studio_cal/xd25/` — `tools/gen.py` writes every project file (**edit gen.py, never the YAML**;
`gen.py --levels` writes L1-L3); `v.sh` regenerate + validate; `cycle.sh` regenerate, fmt, validate, build, install
into the scratch root, audit `--reach --solve`; `four.sh` the playtests (one game at a time); `tools/sheet.py` texture
contact sheets; `tex/proj/` the new texture's xtex project; `shots*/` pictures.

## What was built

13 rooms = 13 sectors, 17.1 M units² (S: ≤ 15 sectors, ≤ 20 M), 8 doors (S 3-8), 3 chests, 2 loops, 28 monsters.

Cellars under Asp (z 0; the stair's top 256):
- **Cellar stair** (arrival from X4's door:xd25, the map's start): eight steps down; the door back up to Asp's square
  is a sealed panel (daylight picture `xodaylt`, "wedged from the square ... no way up here for now").
- **Old cistern**: 1,920 × 1,536, the dry basin (192 deep, six steps) in its north half; two piers; a loose slab
  (secret door, sinks) to the **hidden cache** (a townsman's savings, chest T2, 400 gold).
- **Moulting room**: drying poles across it, a chest of the townsfolk's belongings (T2, trapped).
- **Holding pens**: three barred cages (bar panels `xngrille`, one gate mover with three gates) with three peaceful
  half-turned townsfolk (engine peasants 358, 352, 355, group 20, immobile); the gates lift when the machine dies;
  "Thank you for saving us!" on the next step in the pens (qbit `townsfolk_thanked` 110840); on the next entry the
  group is hidden (load event).
- **Brood hall**: 1,792 × 1,664, four piers; the **brood stair** (its own room, 20 steps) down to the machine level.

Machine level (z -640):
- **Coil passage**: an L round two sides of the transformer hall; the **keeper's cell** (one step up) off its east
  wall: two Snake Lords (D-4: no Guardian Asps), the Straw Bed ("There is nothing on, in, or under the bed."), the
  keeper's hoard (T3, trapped).
- **Field gate**: the field of light (door `door:field`, the new cut-out `xufield`, sinks) into the hall; on entry
  the stone's second rhyme (aaze0031:7). Opens on `q-c5.pedestals` (112101, set on X4); its click calls A3's
  `q-c5.field_gate` (fail text while shut).
- **Transformer hall**: the set piece: a slab plinth, four bronze coils (`xngong1`), a chamber of bars with the
  scarab socket, a crystal crown (`xnquartz`) under a pulsing blue light and the "humming" ambient. Click: the source's
  question "You have found the transformer!  Do you wish to destroy it?" (aaze0031:4). Yes: A3's `q-c5.transformer`
  (q-c5.done 112102), the hum stops, the crown goes to rust, dying sparks, the crystal housing's iron door and the
  cages open. No: "You leave the machine humming."
- **Crystal housing**: the iron box, `crclstr` crystals on it; click: A3's `q-c11.crystals` (the crystals 12313,
  crystals_found 112222, once). Its door's click before: the hook's fail text.
- **Drain tunnel**: 20 steps up north from the hall to a grate in the pens' south wall; reaching it sets
  `drain_reached`, then the grate opens (from the pens before: "bolted fast from the other side").

Critical path: stair → cistern → moulting → brood → brood stair → coil → field gate → transformer hall → crystal
housing. Return: hall → drain → pens → cistern → stair. Loops: upper (cistern/moulting/brood/pens), return (down
the brood stair, up the drain).

## Monsters and treasure

One slot `Xeen Snake Man` (A2's snake_men, block 11500), markers with fixed tiers, `per_marker [2, 3]`:
6 tier-a markers (Snake Man 16), 4 tier-b (Snake Warrior 20); placed: three Snake Lords 11502 (26): one in the hall,
the keeper and his guard. Mean 15 + 10 + 3 = **28**; kill XP 15 × 416 + 10 × 600 + 3 × 936 = 15,048, **3.76k per
member** against MAPS §0's 3.4k (1.11, inside 15 %). Levels 16-26 (band 14-26). Treasure level 2; the keeper's hoard
at 3. `tools/xeen/balance.py` cannot count it until A2's row 9148 exists ("no map_stats row: spawns not counted").

## Textures (25 distinct; S cap 30; 1 new)

One family per area:
- cellars: **MM8 Ancient Troll Home `d43`** (Ravage Roaming's desert dungeon): `gkp2-bs1` sandstone rubble,
  `gkp2flr` carved sandstone tiles, `tfb11` dark slab vaults, `t01a01a` sandstone ashlar (piers, risers, reveals,
  basin edge), `hhr1bwall` / `hhr1p` sandy plaster and gravel (the snake men's moulting room and brood hall),
  `trim9_32a` plank doors;
- machine level: **MM8 Naga Vault `d18`** (the snake people's vault): `gston1wl` granite under the `gstn1tp1` scale
  frieze, `gston1fl` snake-scale floor, `tfb1` warm slabs;
- the machine: the world's own `xngong1` bronze (XD-03), `xnrustirn` (XD-02), `xwiron` (XD-04), `xnquartz` (XD-03),
  `xngrille` (XD-02); `xodaylt` (XD-05) for the daylight at the sealed door; chests MM6 `ch1` (the world's plain chest);
- **new: `xufield`** 256 × 256 cut-out (curtains of red and blue light with a gold scale lattice), Codex, project
  `output/studio_cal/xd25/tex/proj` (raw `raw/xufield_v1.png`, finished `finished/`, x4 1024²). After the finish the
  magenta fringe was keyed out and the transparent texels filled with the nearest colour by hand (the step is in this
  note; the pre-edit master `tex/proj/xufield_finish_before_defringe.png`). Installed only into the scratch root. For
  A6's registry: family "map XD-25; MM8 Naga Vault (gston1wl)", area "the field of light (door:field)".

## Original lines (aaze0031)

- "You have found the transformer!  Do you wish to destroy it?" (:4) — the transformer's question;
- "A message appears in the stone: Alternate the colors around the well / Then the machine can no longer repel" (:7) —
  the field gate;
- "There is nothing on, in, or under the bed." with the name "Straw Bed" (:12, :15) — the keeper's cell;
- "Thank you for saving us!" (:22) — the freed townsfolk.

## Checks

- `validate` no issues (L1-L4); `fmt --check` clean; build: 4 warnings (below); `audit --reach --solve`
  (`output/studio_cal/xd25/audit.txt`): no error, no warning, 0 coplanar pairs, no dressing finding; solve: step 0 2
  sectors, step 1 12 (stair, pens, cache doors), step 2 13 of 13 (needs qbit 112101); never reached 0.
- Build warnings kept: the cage gates rise to within 200 of the pens' ceiling (nobody rides them); `evt:crystal_door`,
  `evt:field`, `evt:transformer` "silent when the condition fails": their else branch is A3's hook, which shows the
  hook's text (fail text, else text) from Lua; the build cannot see it. The playtest asserts both texts.
- Playtests from the scratch root with `--world xeen` (`four.sh`, logs `output/studio_cal/xd25/run/`, summary
  `output/studio_cal/xd25/four.out`): `playtest.yml` (110 steps; every mechanism, the pedestals' qbit by a setup
  shortcut, a save-and-load at the end showing the townsfolk hidden) and `playtest_hostility.yml` (27 steps).
- Pictures: `output/studio_cal/xd25/shots/` (18, sheets `shots_a.jpg`, `shots_b.jpg`), `shots2/`, `shots3/`.
  Looked at; fixed: a pier standing in front of the pens door (moved), straw piles that draw nothing in this world
  (removed), the field's magenta fringe (keyed).

## Dressing

Audit: no finding. Containers: sack pairs against the cistern's north-east corner and the brood hall's north-east
corner, one sack in the cache, a bucket in the pens' south-east corner. Set pieces: none on a walking line.
Dressing exceptions: none.

## Words needed / workarounds

- No floor hatch with a ladder through it was tried: the drain's grate is a door in the pens' south wall at the top
  of a stepped culvert (the graph's "grate in the floor, ladder up" made a wall grate and a stair).
- The "one door from each side" rule: the grate opens from below by a step event in the drain (`drain_reached`)
  rather than by a click that knows its side.
- Map vars for the grate; the pens' first-sight text on a plate (`plate:pens_entry`), since the room's step event is
  the thanks.

## Open issues

1. **Cut-out door leaves show pink/cream speckles** in their transparent parts in `build-xeen/game/openyamm`
   (desktop, x4 tier): seen on `xufield` and, as a test, on XD-04's `xwward` in the same doorway
   (`output/studio_cal/xd25/shots4/`, `shots3/`); the textures themselves are clean (alpha 0/255, transparent texels
   filled). For A1 (renderer or surface cook of alpha textures).
2. The field gate's pink light makes the granite round it pinkish; fine as the field's glow, could be paler.
3. The cellar stair's risers show the carved tile pattern thinly; cosmetic.
4. A2's map_stats row 9148 is needed in assets_dev (the scratch root has a hand copy).
5. Lighting bake: the lane lead's.

## When X4 exists (A5)

The panel `panel:asp_door` becomes an exit on the stair's west wall (top of the stair, floor 256, at x -2304,
y 1760), a project neighbour to `xeen_x4.odm` at X4's door:xd25 arrival; X4's door:xd25 should arrive here at
(-2208, 1760, 256) facing east (the map's start).

## Installed (2026-11-20, lane lead A7)

Built from this L4 (`output/studio_cal/xd25/a7_lead_build/`) and installed into `assets_dev` and the scratch root, with `xufield` (x4 `.oytex`, x2 `.png`) copied into `assets_dev/worlds/xeen/textures_x4`/`textures_x2`; baked (`tools/lighting/baked_indoors/profiles/xeen_xd25.yml`; `bake_map.sh xd25 <scratch root> --sources assets_source --sources output/studio_cal/a7/bake_sources`, 1.4 MB). `stale_bakes.py` lists this bake until A6 puts the master `output/studio_cal/xd25/tex/proj/finished/xufield.png` into `assets_source/worlds/xeen/textures_x4/` (byte for byte: no rebake then). The map does not load from `assets_dev` until A2 writes map_stats row 9148.

## Rows and the X4 switch (2026-11-20, lane A7, third session)

- **A2's row 9148** is live (Xeen Snake Man 2 [2,3] w100) and A6 has registered `xufield` (its master in
  `assets_source`): `stale_bakes.py` lists nothing. From `assets_dev` with `--world xeen`: `playtest` and
  `playtest_hostility` 4 of 4 each (`output/studio_cal/a7/p2_assets_four.out`); `audit --reach --solve` from
  `assets_dev`: no error, no warning (`output/studio_cal/a7/p2_audit_xd25.txt`).
- **The X4 switch.** `output/studio_cal/xd25/tools/gen.py` opens the cellar door by itself once
  `assets_dev/worlds/xeen/maps/xeen_x4.odm` exists (`XD25_X4=1`/`0` overrides): neighbour `exit:asp_square` to A5's
  arrival on Asp's square (-11520, -9360, 1056) facing south (direction 270; X4's hatch door:xd25 at (-11520, -8960,
  1056), briefs/x4/DOORS.md), the exit face `exit:asp_door` (192 x 256, xodaylt) over the panel and `evt:asp_door` an
  exit preset. X4's door:xd25 arrives at this map's start (-2208, 1760, 256) facing east. Checked with a scratch build;
  with X4 absent gen.py writes the installed L4 unchanged. When X4 is in: gen.py, copy
  `output/studio_cal/xd25/x4_prepared/playtest_exit.yml` into L4, cycle, playtests, install, rebake.

## X4 linked (2026-11-20, lane A7, third session)

gen.py opened the cellar door (X4 installed); `playtest_exit.yml` leaves by it (`execute_event` 2, the leave-map "OK")
and arrives on Asp's square at (-11520, -9360) at **Z 1057** (A5's 1056). Checks in `output/studio_cal/a7/root_x4`:
audit clean; `playtest_exit` (11), `playtest` (110), `playtest_hostility` (27) every step 4 of 4
(`output/studio_cal/a7/x4_four2.out`; the binary's exit crash as XD-07's). Installed into `assets_dev`, re-baked.
X4's door:xd25 arrives at this map's start (-2208, 1760, 256) facing east: right.

**A5's built X4 points (2026-11-20, later):** the exits now use A5's built arrivals (they supersede the provisional
DOORS.md ones above): XD-07 gate (-1024, 6912, 1808) south, throw (-4608, 9728, 2504) east; XD-25 (-11520, -9448, 1056)
south; XD-02 adit (20080, -16128, 1504) west; XD-26 mouth (-9216, 11208, 1824) south, sky crack (-7424, 14592, 3600)
south. Measured landing Z: 1802, 1505 (ground), 1057, 1505, 1821.5, 3593. Exit playtests 4 of 4 with clean exits in
`output/studio_cal/a7/root_x4` (`output/studio_cal/a7/x4_built_four.out`); installed, re-baked.

## Texture fit (2026-11-20, merge point 16, lane A7, eighth session)

- Cage bars, cage gates (mover parts), the drain grate and the transformer's chamber: `xwcage` (A6's cage band, `trim_u`, repeats along its width; the transformer at `scale: 1.125`, one picture up its 288) in place of the once-only grille `xngrille` (shown 2.3 times along the cages). `xngrille` is no longer used here (texture count unchanged).
- A8's report: `evt:townsfolk_gone` hid the freed townsfolk on any load, a saved game inside the map included. Now DD-09's fix: the load event hides group 20 only when `townsfolk_thanked` 110840 is set and `in_visit` is not, then sets `in_visit`; `evt:visit_end` (leave) clears it.
- `gen.py` now writes `xufield` with `translucent: 1` (merge point 12 had been set in L4 only).

- `playtest.yml`: a save and a load in the pens now asserts the freed townsfolk stay; the next entry is out by the cellar door's exit (event 2, the leave window's OK) to X4 and back in by `evt.MoveToMap`, which hides them.

### Texture fit exceptions

- `textures.tile_seams` `xwiron`: the cages' 8-wide tops (seen only from below) and the crystal housing's folding leaf (a folding leaf takes pictures at one texel a unit).

## Nineteenth session (2026-11-21, lane A7 lead)

- Merge point 27 (oymap 06:06:32): rebuilt; the peaceful-group load event now runs once per fill (map var
  `studio_peaceful_groups`), first of the load events. Only the generated Lua changed (BLV, scene and studio file byte
  for byte the installed ones; `output/studio_cal/a7/s19/`), so no rebake; installed 06:10:39, stale bakes 0. Audit
  from `assets_dev` 0 errors, the kept warnings (`output/studio_cal/a7/s19/audit/xd25.txt`); playtests 2 of 2 from
  `assets_dev` (`output/studio_cal/a7/s19/two_xd25.out`).

## Door pictures (2026-11-22, lane A7 twenty-seventh session)

F12(b), the orchestrator's decision (plank-strip leaves titled Door show a door picture of the family): the three plank doors (trim9_32a strips: stair, pens, keeper) are two leaves parting sideways with the troll-home kit's plank door pair gkp103a/b; the keeper's doorway 256 wide (was 192). gen.py. Installed with the bake; build warnings and audit as before; tests 4 of 4.
