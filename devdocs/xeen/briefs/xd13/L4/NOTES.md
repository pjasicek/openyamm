# XD-13 Newcastle Keep (staged): L4 notes

Lane A7, agent `agent:xeen-a7-xd13`, 2026-11-20. Map `xeen_xd13.blv`, map_stats 9128, music 49, class S (staged), on
X3, party 14-16 (stage 3 at about 33-36), treasure level 2 (the vault's hoard 3). Design: the MU-6 graph
`devdocs/xeen/mockups/act2_graphs/xd13.graph.yml` with D-4 (`mockups/act2_dungeon_decisions.md`, XD-13) winning
where they differ; A3's M8/M9/M11/M22/M23 quest files; A4's `source/towns/xd13.yml`.

Every file of L1-L4 is written by `output/studio_cal/xd13/tools/gen.py` (`--levels` for L1-L3); rebuild with
`output/studio_cal/xd13/cycle.sh` (fmt, validate, build, install into `output/studio_cal/xd13/root`, audit). Never
hand-edit the written files. Not installed into `assets_dev` (the lane lead installs and bakes).

## What was built

Twelve rooms, twelve sectors, 19.8 M units² of floor (S: at most 15 and 20), one loop (stage 0-1), 3 chests, 4 doors
and a lift, 43 events. Frame: x east, y north; the keep at z 0, the foundations and the old dungeon at -640.

| Room | Size | What |
| --- | --- | --- |
| Keep gate | 896 × 768 | The arrival from X3's hatch; the gate out to X3; the smithy's house door (west), Newcastle's arms (east) |
| Great hall | 2,304 × 2,176, 768 high | Stage 0: the roof open to the rafters over its middle, rubble in two corners, the woodpile, the floor broken into the foundation pit; syllable 1 (la) on the north wall; from stage 2 the roof mended, the hole floored, banners |
| Pantry | 1,536 × 768 (storeroom) | The larder ("Food. Fill pack?"); syllable 2 (bo) under a sack; the rubble ramp's mouth (walled up at stage 2) |
| Statue court | 1,792 × 1,664 | The statue and its plaque; YOUR well; the training hall (east), chapel and counting room (north) house doors; syllable 3 (ra) by the stair |
| Head of the dungeon stair | 448 × 512, 4 steps down | The rubble that blocks the stair until stage 3 |
| Dungeon stair | 448 × 1,152, 16 steps down | To the cellar (stage 3) |
| Foundation pit | 1,408 × 896 at -640 | Stage 0-1: under the hall's hole; five wood golems; the scientists' strongbox (T2); bones |
| Rubble ramp | path, 320 wide, climbs 640 | From the pit up into the pantry (the loop) |
| Flooded cellar | 1,536 × 1,408 | Lagoon water (a sunken level of `7wtrtyl`, 40 deep); swamp things; syllable 4 (to) on a shelf |
| Old laboratory | 1,408 × 1,280 | Bookshelves, the workbench with the notebooks, a cold cauldron, the locker (T2); two iron golems; syllable 5 (ry) |
| Vault door | 768 × 384 | The speaking grille; the steel door with the password; two iron golems |
| Sword vault | 896 × 1,024 | The pedestal, the rack with the Xeen Slayer Sword (A3's `m23.sword`), the vault's hoard (T3) |

### Stages (built as stage 0; load events make the rest)

`Xeen.Stages.newcastle` is walls (m9.walls), keep (m11.keep 111221), dungeon (m22.dungeon 111441). The map tests the
qbits directly: stage 2 = keep or dungeon set, stage 3 = dungeon set.

- **Stage 0-1** (deed bought; walls change nothing inside): `evt:stage_ruin` hides the stage-2 roof patch. 15 Wood
  Golems (11580, group 10): hall 6, court 4, pit 5. House doors show Harmondale's ruined arched door (`ch1b1dl`) under
  Emerson's chalk mark (`xnchalk`); clicked, A4's `closed_text`.
- **Stage 2** (`evt:stage_keep`): golems hidden (`hide_actors 10`), the pit's lift raised 640 so its top is the hall's
  floor (the hole floored over), the ramp's masonry door shut, the rubble and woodpile hidden and passable, the roof
  patch shown, banners (`xkncsban`) and arms (`xkncscrst`) swapped in, the smithy's and training hall's doors and
  signs swapped in (`chb1dl`, `sgweapon`, `7sgtrain`), the daylight off and the lord's lamps on. Hidden golems do
  not block the party (A1, merge point 10; `evt:park_golems` removed 2026-11-20).
- **Stage 3** (`evt:stage_dungeon`): the stair's rubble sinks, the 10 stage-3 monsters shown (group 30: 4 Bog Things
  11461 and 2 Marsh Horrors 11462 in the cellar, 4 Iron Golems 11582 in the laboratory and at the vault door, D-4), the
  well's rubble cap hidden (water under it), the chapel's and counting room's doors and signs (`sgtempl`, `7sgbank`).
- **Vault** (`evt:vault_state`): once `m23.vault_opened` is set the door stays open.

Monsters: 25 over all stages (15 + 10), all placed (exact counts). No spawn points; `encounter_chance` 0 (the party's own
castle: no rest ambushes). Slots for the map card only: 1 Xeen Golem, 2 Xeen Swamp Thing.

### Services (A4's houses, BLV house doors)

Wall panels whose events run `evt.EnterHouse(<id>)` under the house's `opens` condition, else A4's `closed_text`:
`door:smithy` 4141 (gate, west wall; m11.keep), `door:training` 4142 (court, east; m11.keep), `door:chapel` 4143 (court,
north; m22.dungeon), `door:counting` 4144 (court, north; m22.dungeon). The ids are A4's proposals unchanged. Each has a
sign panel above it (`panel:sign_<key>`), Emerson's chalk mark until its stage.

### Hooks and lines

- A3's hooks: `m23.syllable_la` (hall), `_bo` (pantry sack), `_ra` (court, by the stair), `_to` (cellar shelf), `_ry`
  (laboratory, last wall before the vault), `m23.vault_door` (the right word; the door also opens), `m23.sword` (the
  rack). `m23.vault_wrong` is not called: a question's wrong answer runs no effects, so the wrong answer's status line
  carries its text ("Incorrect! The door hums a little louder. Nothing else happens.").
- Original lines (aaze): Woodpile, Rubble, Bones (0072:1, 3, 5); "Food.  Fill pack?" (0073:0); the plaque (0073:3);
  the stair's rubble (0073:7); YOUR well / "Even your well's water is cool and refreshing." (0073:8, 9); "What is the
  password?" / "Incorrect!" (0073:15, 16); "The pedestal is cool to the touch." (0073:12).
- YOUR well (D-4): each member's ArmorClassBonus raised to 20 if lower (`IsAtLeast` / `SetValue`), cleared by rest
  (`clearTemporaryEventBonuses`); free and repeatable. The larder raises the party's food to 20, repeatable.

### Exit

Live: the gate (`exit:gate_door`, event 13) leads to X3 at A5's arrival **(10496, 15216, 1760) facing south** (270°,
MoveToMap 1536). Measured by `playtest_exit.yml`: the party stands at (10496, 15216, **1761**) on X3.
X3's hatch (`thing:xd13_stair`, A5's, still sealed with a message in X3's Lua) should lead in to this map's start:
**(0, 320, 0) facing north (90°, MoveToMap 512)**, and should refuse without the deed (m8.deed 111160).

## Measurements

- 12 sectors, 513 faces, 12 portals, 19.78 M units² (`oymap metrics`), doorways 160-512 wide.
- Textures: 24 distinct as built, 30 over all stages (the six swapped in by stage: `xkncsban`, `xkncscrst`,
  `sgweapon`, `7sgtrain`, `sgtempl`, `7sgbank`); cap S 30. **No new textures**: all shipped MM6-MM8 or the world's
  existing (`xnchalk`, `xngrille`, and the royal kit's Newcastle arms and banner). One family per area: Castle
  Harmondale (MM7 7d29) for the keep (`chb1`, `tfb09`, `7tws1h`, ruin pieces `ch1b1`); the foundations' rough stone
  (`cwb1`, `cfb1`, the hall's boards `7gt003a`); Harmondale's grey brick (`cwb`) for the dungeon.
- Checks (scratch root, `--world xeen`, `build-xeen/game/openyamm`):
  - `cycle.sh`: validate clean, fmt clean, build 1 warning (below), audit `--reach --solve`: no error, 1 warning
    (below). `output/studio_cal/xd13/build.log`, `audit.txt`.
  - `playtest.yml` 4 of 4 (163 steps), `playtest_hostility.yml` 4 of 4 (30 steps): `output/studio_cal/xd13/four.out`,
    logs `output/studio_cal/xd13/run/playtest_N.log`, `playtest_hostility_N.log`. All exited 0.
  - `playtest_exit.yml` 1 of 1 (`run/e1.log`).
- Root: hard-link copy of `assets_dev` with real copies of `worlds/xeen/maps`, `events/maps` (X3 refreshed after A5's
  reinstall) and of `data_tables/map_stats.txt`, `bolster_maps.txt` with a test row 9128 (A2 writes the real one).

## Dressing exceptions

- Build warning "nothing tells the player on arrival why he is here": the map has three arrival timers, one per stage,
  each with a `condition`; the check counts only unconditional ones.
- Audit warning `question.answer` (event 38, "laboratory"): the syllables and Crodo's autonote give it through A3's
  hooks (Lua), which the audit does not read.
- No dressing errors; no set-piece warnings (the cauldron stands in the laboratory's north-west corner).

## Words needed

- ~~Hidden actors still block the party~~: they do not (A1, merge point 10, as the originals). The stuck walk was the
  hostility playtest's `reload` skipped behind the arrival window (stage 3 never loaded). The window is closed before
  the reload now and `evt:park_golems` is gone (2026-11-20, fifth session).
- **A question's wrong answer runs no effects** (studio): A3's `m23.vault_wrong` hook cannot be called; its text is the
  wrong answer's status line.
- **No open sky in a studio BLV room**: the stage-0 hall is "roofless" only as a lantern open to the rafters and the
  roof boards, lit grey; a real sky needs the scene's `sky` block and IndoorSky faces, which the studio does not write.
- **Tours and console events**: `event 31` from the console in a screenshot tour swaps faces and textures but the
  group bits on actors do not show in the frozen tour (the golems stay drawn in the stage-2 pictures); the playtest's
  `actor_visible` checks after a reload confirm them hidden.

## What the user should look at

- The great hall at stage 0 against stage 2: does the open roof read as fallen, is the hole into the pit clear enough
  (it shows as a lit patch of the pit floor 640 below)?
- The drop through the floor (fall damage, 640) and the climb out by the ramp into the pantry.
- The house doors' chalk marks before their stage and the signs after.
- The statue (MM7's `7dec55`, an armoured figure) is small for "Great Adventurers".
- The stage-3 dungeon is quiet by D-4: 10 monsters at levels 26-40 against a party of about 33-36.

## Where it stands, next steps

Built, checked and looked at in the scratch root; not installed. Next: the lead installs into `assets_dev` and bakes;
A2 writes map_stats/bolster row 9128 from the slot lines; A5 points X3's hatch at the start above (with the deed
check); A3 decides on `m23.vault_wrong`, the syllables' numbering and places; A1 looks at hidden actors' collision
(then `evt:park_golems` can go).

## Installed (2026-11-20, lane lead A7)

Built from this L4 (`output/studio_cal/xd13/a7_lead_build/`, identical to the scratch install) and installed into
`assets_dev`; baked (profile `tools/lighting/baked_indoors/profiles/xeen_xd13.yml`, `bake_map.sh xd13
output/studio_cal/xd13/root --sources assets_source`, then `install_bake.py xd13`; the base geometry, stage 0-1).
`stale_bakes.py` lists nothing; `texture_budget.py` 24/30, 0 new; `quests.py` clean. The map does not load from
`assets_dev` until A2 writes map_stats/bolster row 9128; the playtests from `assets_dev` follow then.

## D-22.6: open sky over the hall (2026-11-20, lane lead A7, fourth session)

- The roof hole's top (the hall's `ceiling_levels` lantern at 1,152) has `sky: true`; `atmosphere.yml` (new, written
  by gen.py) has `open_sky: {mode: open, preset: swamp}` (X3's preset in the world's `sky.yml`); no daylight block, no
  weather; the rafters (two tie beams) kept. The studio took both words (no warning). Stage 2's roof patch (752)
  closes the sky off.
- Pictures from `assets_dev` (`output/studio_cal/xd13/sky_a.jpg`, `sky_b.jpg`): stage 0 by day (clouds over the
  beams), by night (stars), the pit below looking up through the floor hole and the roof hole; stage 2 looking
  straight up: the mended roof, no sky.
- A3's new syllable texts (D-22.5, "1: la" ... "5: ry") are in the playtest's asserts.
- Rebuilt, installed into `assets_dev`, re-baked (1.4 MB); `stale_bakes.py` lists nothing for it; textures 24/30, 0
  new. From `assets_dev` with `--world xeen` (A2's row 9128, A4's houses 4141-4144): `playtest.yml` (163 steps),
  `playtest_hostility.yml` (30), `playtest_exit.yml` (12) **4 of 4 each, clean exits**
  (`output/studio_cal/a7/s4_xd13_four3.out`). The generator before D-22: `output/studio_cal/xd13/tools/gen_before_d22.py`.

## Sixth session (2026-11-20, lane A7)

- **Lamp rule (A1's lights audit, merge point 14):** `light:hall_day` stood 516 over the open roof (its height is over the rafter top at 768): height 132, z 900;
  `court_torch_s` along 0.75 → 0.6, out of the stair head's opening. Clean under the audit.

## Texture fit (2026-11-20, merge point 16, lane A7, eighth session)

- No error. Warning kept:

### Texture fit exceptions

- `textures.feature_border` `xngrille` on `cwb`: the speaking grille beside the vault door, a dark iron grate meant to read against the stone.

## Merge point 35 (2026-11-21, lane A7 twenty-fifth session)

- `playtest.yml` failed once at step 37 (the walk back from the pantry): a pit golem had climbed the rubble ramp into the
  pantry, since merge point 33's clears keep to the party's storey and no longer kill the pit from the hall. The five
  pantry walks now carry `clear_hostiles: 1500`. The map unchanged; 3 tests 4 of 4 (208 steps a round).

## Twenty-seventh session (2026-11-22, lane A7): what makes it the party's own staged castle (D-89 identity)

`project.yml` `identity: {shape: castle, family: 7d29, seen: [...]}`. gen.py's new "D-89 identity" pass
(`reviews/DESIGN_GATING_AND_IDENTITY.md` 2.2, XD-13's row):
- **Castle Harmondale's ruin (7d29) in the great hall:** a base course and a string course of squared stone (`chb1s`,
  hung from its top), the cobble (`chb1`) to 384 and above it the smoke-blackened ruin stone (`ch1b1`, the hall's own
  theme `theme:keep_hall`). The gate and the statue court take the base course.
- **The roof fallen in on the sky:** a broken 16-sided hole (about 1,100 by 830) over the hall's middle, a lantern 128
  thick (ceiling 896, its edge the ruin stone, its top the open sky, X3's `swamp` preset) over the two tie beams; the
  stage-2 roof patch has the hole's own outline. Kept clear of the floor's hole into the pit and of the golems' places.
- **A breach in the north-east corner:** a gable gap (384 wide, sill 224, apex 672) in the north wall's east end onto
  `room:breach` (seen, never walked; walls and roof open sky, `space: room:great_hall`): fallen stone level with the
  sill, then heaped away under the sky (steep, `uneven` top), lit by its own daylight. Stage 2 shows
  `platform:breach_plug` (Emerson's masonry, chb1) behind it; stage 0-1 hides it.
- **Rubble mounds** in the north-east (up to 144 at the corner, under the breach) and south-east (112) corners:
  platforms with sloped tops (`top_heights`, fanned from the corner), walkable, the old ids and click lines kept;
  hidden at stage 2. A **fallen rafter** (352 long, 32 high) under the hole, hidden at stage 2.
- **The laboratory at work (stage 3):** two more benches of glass along the south wall with glasses (`dec35`),
  candles (`cndlab0`), a goblet and a glowing crystal (`crystl0`) on them, a pulsing green alchemist's glow.
- **The heavy steel vault door:** two riveted leaves (`t5d1` whole on each, 160 by 320) parting sideways, 48 thick,
  in a riveted iron frame (`reveal t5d1`); the doorway 320 wide (was a single 192 leaf).
- Not here: the wood golems still wear the MM7 pharaoh golem's headdress (a body or tint for S, REQUEST).

Checks: build warnings 0; audit 0 errors, the 2 kept warnings (below); textures 30/30 (cap S); `check_exits` 0,
`check_drops` 0 pockets; tests 12/12 (`playtest`, `playtest_hostility`, `playtest_exit`, 4 rounds each); installed with
its bake; MAW reserve none (placed monsters only). Name test (arrival, the first fight room = the hall, the signature
rooms = the hall and the vault): before `output/studio_cal/a7/s27/xd13/before_sheet.jpg`, after `after_sheet.jpg`
(and `after2_sheet.jpg` with the breach lit and its plug at stage 2). Does it read as Newcastle? The hall reads as a
burnt-out castle hall open to the sky at stage 0 and as a mended lord's hall at stage 2; the cellar and vault stay
plain brick (Harmondale's own dungeon brick).

## F71 (agent xeen-fb5-dungeon, 2026-11-26; the player's pin p2)

- The speaking grille was a wall panel in `xngrille` (a cutout): the sky showed between its bars. Now a thin block
  4 off the wall with the bars on its face, over a black speaking hole (`7solid01` wall panel); `evt:grille` moved to
  `platform:grille`. `tools/xeen/check_cutout_backing.py` (cutout faces with nothing drawn behind them).
