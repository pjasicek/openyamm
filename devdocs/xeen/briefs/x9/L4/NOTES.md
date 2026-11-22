# X9 Clouds of Xeen: L4 notes (lane A5 sub-agent, 2026-11-21)

X9 is the sky map of Act V (party 46-48): walkable clouds over Lake Darzog, Slick's carnival and Castle Xeen's shell.
It is built from the L1 plan with D-50 applied (`../L1/D50_DECISION.md`; `../L1/NOTES.md` "D-50 applied") and A7's
measured XD-19 shell.

It is installed as `assets_dev/worlds/xeen/maps/xeen_x9.blv`, with its `.scene.yml`, `.studio.yml` and
`events/maps/xeen_x9.lua`. See "Checks" for the install time.

## Route: the studio

The route is X8 Cloudreach's (`../../x8/L4/NOTES.md`).

- **The room:** one open-air room, `room:air`, from the safety floor at -6,000 to the sky at 6,400. Its walls, floor
  and ceiling are sky faces.
- **Atmosphere:** `atmosphere.yml` sets
  `open_sky: {mode: open, sky_texture: xeencloud, view: outdoor, view_distance_scale: 2}` and X8's daylight block.
- **The clouds:** every cloud is a hanging platform with its L1 outline (`geom.blob`), so the spans measured at L1 are
  the spans built. Each has a cloud top (`xccloud`), cloud sides (`xccloudsd`) and two or three flared roots.
- **Necks:** cloud slabs.
- **The Xeen road and the gate causeway:** cloud slabs with cloud-stone flags (`7tws1f`) on top.
- **Rope bridges:** plank decks (`t66floor`) with rope rails (`hwm2rf`), as X8's.
- **The aviary stair:** a cloud-stone ramp.
- **The unseen way:** a slab whose top is the new wisp texture at 55 % opacity. Its sides and underside are sky faces,
  which are not drawn.

The scripts that write the files are in `output/studio_cal/x9/tools/`:

| Script | Writes |
| --- | --- |
| `design.py`, `geom.py` | The design as data and its outlines, shared with L1 (`gen_l1.py`, `render_x9.py`, `tune_chain.py`) |
| `gen.py` | rooms.yml for L3 and L4, and L3's start |
| `gen_plan.py` | plan.yml and project.yml for L2 to L4, from L1's |
| `gen_objects.py` | objects.yml, wiring.yml and atmosphere.yml (A3's hooks by name; the XD-19 switch) |
| `gen_playtests.py` | the five playtests (needs the build's ids.lock.yml) |

The shell scripts are in `output/studio_cal/x9/`:

| Script | Does |
| --- | --- |
| `v.sh` | generate, fmt, validate |
| `b.sh` | v.sh, build into `build/`, playtests, fmt |
| `run.sh` | the playtests N times through lane A5's game slots |
| `stage_install.sh` | a hard-link stage, install, audit, the playtests, then with `INSTALL=1` new file + rename into `assets_dev` |

There are no hand edits: the generators are the source.

## What D-50 asked, and what was built

| D-50 | Built |
| --- | --- |
| 1. Unseen way 768 wide, faint, readable underfoot, lips | 768 wide, 4,606 (nine cells) due north of the sign, falling 192. Wisp top (`xcwisp`) at 55 % opacity over the sky, sides not drawn. From the brink it is a faint band, underfoot a pale path (tour `t2/01-signature`, `t2/05-unseen_way`). Cloud-stone lips 1,024 x 256 at both ends. |
| 2. Plaza about 6,144 x 4,608, booths spread at least 1,024 apart, a 1,536 shooting line, the Xeen road up its east side | The plaza is 6,144 x 4,608 at (-2560, 2560), flagged to 82 % of its outline. Booths: Might (-1024, 1280), Speed (-1536, 3968), Endurance (-4352, 3840), Accuracy's line (-3712, 1536). They are 2,382-4,183 apart and each faces the plaza's middle; the Accuracy booth looks west. The bullseye is at (-5248, 1536) on the west rim, 1,536 from the line. The road runs on x 0 up the plaza's east side. Spans unchanged (bridges 3,399-3,895); the aviary stair 4,138. |
| 3. The gate with the exit preset and `m34.gate` | See "The gate". |
| 4. Falls to X2's `entrance:x9_fall` with damage | Every fall goes through A3's `Xeen.skyFallTo("x9")`, which is (-15360, 3072, 768, east), the lead's moved point. Tested from three regions (see "Checks"). |
| 5. Shell closed on every side, roof included | Closed blocks: the curtain walls with a roof, a frieze course, four towers and the keep, each with a closed top. |
| 6. Plan distance, no gryphons, banners only as `7tws1f` flag dressing | The gate is 23,009 from the signature camera, never nearer or larger. No gryphons and no banners: `7tws1f` is Celeste's marble (here the flagstones and lips), not a flag, so no banner was placed. |
| 7. Dragon Clouds built, empty | The Dragon Clouds are at (20864, 18304), floor 2,048, 3,892 from the aviary. The dragon-head rock is five rock masses (skull, snout, jaw, two horns). Since D-57 they hold Q-F1's court (see "The Dragon Clouds"); still no chest, light or monster. |
| 8. Dungeon L, cap 70, shipped canvas first | MM6's tent canvas: `tentwal7b` on the counters, back walls and awnings, `tentwal7a` hems. New textures are `xctarget` and `xcwisp` only. |
| 9. Castle gone, return point, aviary sign | The castle-gone stage is below. The return point is `entrance:xd19_gate`. "Xeen's Aviary" stands at the stair's head. |
| Q4. 50 placed in 19 groups | 38 Rocs, 6 Griffins (aviary), 6 Cloud Golems. |
| Q5. 6 offerings, 5 nests | All are A3's hooks (below). |
| Q6. Slick behind the prize stand if his model draws | Placed, and he draws (tour `t2/06-slick_close`). |

## The Dragon Clouds (Q-F1, D-57 Q36, D-59)

- **The arrival:** `entrance:fd04_roof` at (20352, 17280), floor 2,048, facing north (512) toward the dragon-head rock,
  on the cloud about 900 south of the snout. plan.yml's note is corrected: (20864, 18304) is the room's centre, inside
  the skull's footprint.
- **The way down:** a leaf 256 x 512 (MM6's framed stone door `cvdor1`, once; `7solid01` was tried first and is pure
  black, a hole in the rock) against the skull's south face at (21632, 18048), a marble step before it; `evt:fd04_door`, the exit preset's leave (`{exit: door:fd04}`,
  meaning "Descend into Dragon Tower?", dark/aazex128:0) to FD-04's `entrance:x9_clouds`. **Sealed until FD-04 is
  installed** ("The door in the rock does not move. (Not open yet.)"): `gen_objects.py` `FD04` turns on when
  `xeen_fd04.blv` is installed and its studio.yml names `entrance:x9_clouds` (or `X9_FD04_LIVE=1`). The neighbour is
  `door:fd04` (was `roof:fd04`, listed only).
- **The Eye:** MM6's crystal `crystl0` on a rock ledge out of the skull's south face at (21056, 17984), ledge top 128
  over the cloud. `evt:qf1_eye` shows the source's two lines and asks "What is the secret of the Dragon?"
  (dark/aazex128:1-2): "Infinity" or "Infinite" (any case) calls A3's `q-f1.eye` (the Elder Staff 12505, 8,000 each,
  bit 114021), any other answer `q-f1.eye_wrong` (70 Energy to everyone, "Die fools!", ask again); once done, a click
  is the hook's else line.
- **Four Ancient Books** (`q-f1.runes_in`, `_fi`, `_ni`, `_ty`; only a Linguist reads them): rock lecterns 160 x 160 x
  112 with D6's open book `xnpbook` on top (fit once), at (19600, 17300), (19712, 19200), (21300, 19700),
  (22450, 18300).
- **Three crystal balls** (D-59 1; `q-f1.ball_mind`, `_past`, `_future`: current Intellect 60 hears the phrase, less
  70 Mind and Weak): MM8's air orb `dec57` on marble plinths 112 high at (19350, 17900), (19300, 18350),
  (19400, 18800), west of the snout.
- **The Well of Fantastic Skill** (D-59 2; `q-f1.well`: +20 to all seven statistics until rest, once a day): a marble
  curb 448 square, 112 high, round `wtrtyl` water at (21800, 17250); the water and each curb block call the hook.
- **Three Dragon Power Crystals** (D-59 3; `q-f1.crystal_1`-`3`: 3,000 / 4,000 / 5,000 once per character, a 70 Energy
  surge): `crys5` (20600, 19600), `crys6` (21950, 19400), `crclstr` (22350, 18950).
- **No monsters** (D-57 Q37). New textures: none (`cvdor1`, `xnpbook`, `wtrtyl` are shipped or world textures).
- Tour: `output/studio_cal/x9/shots/s17/sheet.jpg` (the court), `shots/s17c/` (the door).
- `playtest_dragon_clouds.yml` (214 steps, not immortal; see "Checks").

## Castle Xeen's shell (A7's XD-19 measurements)

The shell is the outside of XD-19 in X9's frame. XD-19's coordinates + (0, 16096) give X9's.

| Part | Where (X9 units) | Top (z) |
| --- | --- | --- |
| Outside footprint | x -5280..5280, y 11136..21536 (10,560 x 10,400), centre (0, 16336) | |
| Corner towers | 16-sided, radius 768, centres (±4512, 11904) and (±4512, 20768); their faces are the footprint's edges | 4,864 |
| Curtain walls and roof | x ±5120, y 11296..21376 (160 behind the towers) | 4,352 |
| Gold frieze course (`gnecwalt`) | along the walls' top | 4,096-4,352 |
| Keep | 3,584 x 2,816 centred at (0, 17872) | 5,376 |
| Gate recess | x -384..384, from y 11296 back to the gate wall at y 11776, 640 high | |
| Gate leaves | west leaf x -256..0 (`gnecdr1l`), east leaf x 0..256 (`gnecdr1r`); front faces at y 11768, back on the gate wall at y 11776; z 768..1280 (512 x 512) | |
| Castle cloud | rounded rectangle 1,024 beyond the shell, x ±6304, y 10112..22560 | 768 |

- The walls are XD-19's black stone (`gnecwal1`) with the gold frieze course at the top.
- The walls clear XD-19's highest room (the aviary walls, 3,456 over the sill) by 128.
- The causeway climbs from the gate court (704) onto the castle cloud. It is `platform:gate_causeway`, 1,024 wide.

## The gate

The studio's `exit` preset needs an `exit` object, and an exit lies only on a room wall: it is a wall panel that can be
neither hidden nor put on a platform's face. X9 is one open-air room with no wall where the castle stands. So the gate
is two leaf blocks, each clicked by its own `script` event (`evt:gate_l`, `evt:gate_r`).

Since the seventeenth session (D-57) their effects are `[{lua: 'if not XeenQuests.hook("m34.gate") then return end'},
{exit: door:xd19}]`: merge point 23's `{exit: <neighbour>}` writes the exit preset's own move (no `direct`), so the
script no longer spells out the MoveToMap.

- Without `direct`, a move from one indoor map to another shows no window (only a way onto an outdoor map asks), so a
  click with the doll takes the party straight in; the ledger's "Enter Castle Xeen?" (aaze0027:40) is not asked.
- Without the Lord Xeen doll, A3's hook gives the fail text. The map asks no question of its own.
- **Switch:** `gen_objects.py` `XD19` reads XD-19's `entrance:x9_gate` from the installed `xeen_xd19.studio.yml`. It is
  on when `assets_dev/worlds/xeen/maps/xeen_xd19.blv` exists and names that arrival, or when `X9_XD19_LIVE=1` is set.
- **Open since 2026-11-21 02:16** (A7 installed XD-19 at 02:07:37): both leaves lead to XD-19's `entrance:x9_gate`
  (0, -4064, 0) facing north (512). The main playtest shows the doll, clicks the right leaf, asserts XD-19 and the
  arrival within 256, runs XD-19's right leaf (its event 36, A7's leave with `direct`) and asserts X9's
  `entrance:xd19_gate` (0, 11264) within 256 before walking on.

## Castle gone (`state:castle_gone`, D-47 Q14)

- `evt:castle_gone` is a load event on m35.done (111707). It hides and makes passable every shell part: walls, frieze
  course, lintel, towers and their friezes, keep and its frieze, and both leaves.
- The castle cloud stays, and so do the causeway, the return point and the aviary stair.
- After that, the gate's spot gives A3's `x9.castle_gone` line ("The great Castle Xeen recently stood here.",
  aaze0027:44). It comes from stepping onto the threshold (`evt:castle_spot`), or from the leaves' click (their
  `else_effects`).
- `playtest_castle_gone.yml` tests it (below).

## Falls

These work as on X8:
- `evt:fall_check` is a one-second timer. Under z -1,000 it calls `Xeen.skyFallTo("x9")`.
- `evt:fall_floor` is the safety floor's step event and makes the same call.

The landing moved from D-50's (-14592, 2816), which was 3,874 from the lake dragon placed at [36.5, 66]. Under D-50's
rule it moved along Darzog's island toward the tower door, to cell [34, 58]. That was 4,136, 4,291 and 5,976 from the
three placements of the time (not 6,800, as first written).
A3's table `Xeen.SkyFalls.x9` holds (-15360, 3072, 768, 0, "xeen_x2.odm"). The party arrives in the air over X2's
ground and takes falling damage.

**The fall alone is safe.** It costs each member 850 x maximum HP / 2,560, about a third. The test party (level 46, no
equipment) keeps 270, 124, 171 and 114 HP, the same in every run and from every region (9 runs, `xrun/run_012744`).
The arrival starts a fresh fall measure (`OutdoorPartyRuntime::teleportTo`), so the depth reached on X9 before the
one-second check does not add to it.

**X2's Water Dragons no longer reach the landing (D-54, 2026-11-21).**
- Before D-54, two of X2's three Water Dragons (11640, level 60, flying, Ice Blast) were placed 4,136 and 4,291 from
  the landing; with an 8-second wait one run in ten left the cleric dead, and 3 of 9 runs showed a hit 0.5 s after
  landing.
- D-54 kept the landing and moved the dragons out on the lake with a leash (X2 NOTES, fifteenth session): each leash
  circle is now at least 5,888 from the landing and from Darzog's door (6,307 at the nearest).
- The three fall playtests check the dragons again (`gen_playtests.py` `fall`, `FALL_HP`): every member's HP equals its
  value just after the fall (270, 124, 171, 114) at 0.5 s, again after 20 s on X2, and again after the walk to
  Darzog's door (-15731, 3014). 2 of 2 each from assets_dev (`xrun/run_020148`, 26 steps).
- Known (A1): a leashed flyer that sees the party leaves its circle (X2's `playtest_lake_dragons_leash.yml`). The
  landing is safe because the dragons, 6,300 and more away, do not notice the party there.

## Checks

| Check | Result |
| --- | --- |
| `validate` L2, L3, L4 (against `assets_dev`) | no issues |
| `fmt` | run on every generation |
| `build` | 1 room, 2,199 faces, 41 events, 4 chests. Two warnings stay (below). |
| `audit --reach --solve --dressing --lights --doors --textures` (project) | 0 errors, 0 warnings. Faces in one plane: 0 pairs. On foot from the start: 1 of 1 sectors. Info: `xccloudsd` squashed on tapered roots (meant, `uneven`); `click.silent` on the gate leaves (A3's hook speaks); `state.never_read` on A3's `x9_offering_N` map variables (the hooks read them). |
| `audit xeen_x9.blv --world xeen --assets assets_dev` (installed map) | 0 errors, 0 warnings; faces in one plane: 0 pairs (`output/studio_cal/x9/audit_assets.txt`) |

The build warnings that stay:
- The Dragon Clouds "rest on nothing": they float.
- "Liquid and flow: 23 of 34", as on X8.

Playtests, headless (`build-xeen/game/openyamm` of merge point 21, `--world xeen --map xeen_x9.blv`):

| Playtest | Steps | Covers |
| --- | --- | --- |
| `playtest.yml` | 222 | Every cloud, neck, bridge, the road, the causeway, the aviary stair and the unseen way. Also: the four signs; the rhymes (runes, then read with the Linguist bit); the five nests (bits); the six offerings (refused, then given); the four booths and the prize stand; the gate (refused without a doll; with one into XD-19 and back); the four chests. |
| `playtest_fall_south.yml` | 26 | off the brink (the stair clouds) |
| `playtest_fall_chain.yml` | 26 | off the lone pillar (the east chain) |
| `playtest_fall_xeendom.yml` | 26 | off Xeendom's landing |
| `playtest_hostility.yml` | 23 | Rocs, Griffins and Golems hostile, none fighting another; Slick peaceful and unhurt |
| `playtest_dragon_clouds.yml` | 214 | The Dragon Clouds (D-57, D-59), not immortal: no monster within 3,000; the well (Brokk's might 30 -> 50, a second drink nothing, 30 again after a rest); the sealed way down (its line, the party stays); the Eye (a wrong answer: "Die fools!", all alive; "infinity": the Elder Staff and bit 114021; then its else line); the balls (Brokk, intellect 20 + 20: Weak and alive; Sefa, 45 + 20: each phrase); the books (the runes line, then IN, FI, NI, TY for a Linguist); each crystal (Hild paid 3k/4k/5k and hurt, her second touch "nothing more" and no pay, Ivar paid); nobody dead or unconscious. HP is set back to full between devices with `set_member_points` (`hp full` restores the party and drops the well's +20). |
| `playtest_castle_gone.yml` | 18 | m35.done set and the map reloaded at the gate (`load_map` with `pos`); stepping onto the gate's spot shows A3's "The great Castle Xeen recently stood here."; the party walks to the shell's middle, its north-east tower and its north wall (hidden and passable) |

Each fall asserts the landing on X2 within 256 of (-15360, 3072) and every member's HP at its after-the-fall value, at
0.5 s, after 20 s and at Darzog's door (D-54).

Results, two runs each:

| Playtest | Stage (hard-link copy of `assets_dev`, `xrun/run_012833`) | `assets_dev` after the install (`xrun/run_013016`) |
| --- | --- | --- |
| `playtest.yml` | 2 of 2 (213 steps) | 2 of 2 |
| `playtest_fall_south.yml` | 2 of 2 | 2 of 2 |
| `playtest_fall_chain.yml` | 2 of 2 | 2 of 2 |
| `playtest_fall_xeendom.yml` | 2 of 2 | 2 of 2 |
| `playtest_hostility.yml` | 2 of 2 | 2 of 2 |
| `playtest_castle_gone.yml` | added after the install (the map unchanged) | 2 of 2 (`xrun/run_014316`) |

## Dressing exceptions

None. There are no containers. The booths stand on the plaza away from its walking lines, and the statues stand on
plinths.

## Texture fit exceptions

None. The canvas is laid at 2x and 4x so it never repeats up a face. The gate's wings and the bullseye are `fit`, once
per face, and the leaves' and the target's ends are laid at their size.

## Words the studio lacked (workarounds)

- **An exit on a platform's face, or `hide` on an exit:** the gate is a script with the exit preset's Lua (see "The
  gate"). Asked of A1: either word would let X9 use the `exit` preset itself.
- **Monster barriers:** the golems are `immobile` and the rocs and griffins fly (X8's rule).
- **A fall zone indoors:** the timer plus the safety floor (X8's).
- **D-50 change 6's `7tws1f` "flag dressing":** `7tws1f` is a marble texture, not a flag decoration, so no banner
  was placed.

## Open items

- **Request to A1, still open:** confirm the cost of `view_distance_scale: 2` on X9, an open-air BLV of one sector.
  A1 confirmed 1.25 for XD-17 only. On X9 everything is drawn anyway; the scale only moves the far plane and the haze,
  so the castle reads from the brink 23,000 away.

## Session log

**2026-11-21 (A5 sub-agent, `agent:a5-x9`).**
- D-50 applied at L1. L2-L4 generated, built and audited.
- The two new textures were made and installed.
- The stage run passed 10 of 10. The map was installed into `assets_dev` at 01:29 by new file + rename, and the stage
  removed.
- From `assets_dev`: 10 of 10.
- `oymap record` on L2-L4.
- Tours: `output/studio_cal/x9/shots/t1` (ten views), `shots/t2` (after the fixes); contact sheets in
  `output/studio_cal/x9/look/`.
- Fixed during the session:
  - the gate court and the castle cloud only overlapped, so the walker went round by the aviary: a causeway slab now
    joins them;
  - Slick stood on the prize stand's awning (the game stands a placed monster on the highest top): the stand is now an
    open counter;
  - the unseen way read as a plain path from the brink: its top is now translucent;
  - the awnings and canvas were laid at the wrong size;
  - a first fall test waited 8 s on X2, where the Water Dragons struck (see "Falls").

**2026-11-21, merge point 22 (game and oymap 01:40:33).**
- Rebuilt with `b.sh`. The built `.blv`, `.scene.yml` and Lua are byte-identical to the installed ones, so there was
  no reinstall.
- Added `playtest_castle_gone.yml`: 2 of 2 from `assets_dev` (`xrun/run_014316`).

**2026-11-21, fifteenth session (lane A5).**
- D-54: the three fall playtests check X2's dragons again (see "Falls"); 2 of 2 each (`xrun/run_020148`).
- The gate opened into XD-19 (see "The gate"): the L4 diff is the two leaves' Lua, the project's neighbour
  `arrival: entrance:x9_gate` and the main playtest. Stage 2 of 2 for every playtest (`xrun/run_021459`, the walk
  again in `run_021621` after dropping a leave-window assert), installed 02:16; from `assets_dev` every playtest 2 of 2
  (`xrun/run_021702`: walk 222 steps, three falls, hostility, castle gone). Installed audit 0 errors, 0 warnings.

**2026-11-21, seventeenth session (lane A5).**
- Merge point 24: the three falls 2 of 2 from `assets_dev` (`xrun/run_032139`); X2's dragons stay leashed (X2's
  lake_dragons and lake_dragons_leash 2 of 2).
- D-57 Q36/Q37 and D-59: the Dragon Clouds' court (see "The Dragon Clouds"); the gate on `{exit: door:xd19}`. Project
  audit 0 errors; warnings kept: `question.answer` on the Eye (its answer comes from A3's runes hooks and FD-04's notes,
  which the audit does not read) and the air orbs sunk 9 into their plinths (the model's own `z_offset`). Stage 14 of
  14 (`xrun/run_034025`), installed 03:41, every playtest 2 of 2 from `assets_dev`; the door's texture changed after
  the tour (`7solid01` -> `cvdor1`, at its native size: `size: [256, 512]` tiled it 2 x 2), reinstalled 03:49 (stage 7
  of 7), from `assets_dev` again (`s17/assets_dev_tests3.log`).
- Studio note for A1: a decoration's `inside:` names a block by id, but the build's overlap warning names the block by
  its path (`rooms[0].platforms[N]`), which the schema refuses as an `inside` value (seen with the orbs).


## FD-04 and merge points 26-27 (2026-11-21, A5 18th session)

- The way down (`evt:fd04_door`, `{exit: door:fd04}`) is live: `MoveToMap(-1312, 608, 4224, 1536, ..., "xeen_fd04.blv")`,
  FD-04's `entrance:x9_clouds` facing south; `playtest_dragon_clouds` asserts the point.
- Merge point 26 (falls land and hurt on every map): the three fall playtests expect 181/85/115/78 (of 270/124/171/114)
  just after the fall, after 20 s and at Darzog's door (`gen_playtests.py` `FALL_HP`).
- Rebuilt with oymap 06:06 (merge point 27). Stage 14 of 14 (`xrun/run_061459`), installed 06:16; audit 0 errors.

## Sure-Eye Tonic (D-70 Q1, 2026-11-21, A5 21st session)

- `deco:tonic_crate` (event 59, `evt:tonic_crate`, "Sure-Eye Tonic") calls A3's `m34.tonic`: the first click in the game
  puts two Accuracy Boosts (245, power 10) on the cursor, later clicks give Slick's else line only.
- Placed at (-3328, 960), 64 beyond the south end of the Accuracy booth's counter (`gen_objects.TONIC_AT`, from the
  booth's own point). D-70 and A3's `where` say (-4608, 1280), which lies in the shooting lane, 832 west of the line
  toward the bullseye; the counter itself stands at x -3328, y 1024..2048. No crate model exists in the world's
  indoor bindings, so the object is MM7's cask (`7dec21`), off the lane and the line.
- `playtest_tonic.yml` (`gen_playtests.tonic`): member 0 set to 30 Accuracy loses the Accuracy game; the crate gives 2
  boosts, a second click the else line and no more; one boost drunk gives 60 and wins the doll (111684, 12370), one
  bottle left. The main walk clicks the crate twice after the booths.
- Stage 16 of 16, installed 08:22; from `assets_dev` 16 of 16 (`xrun/run_082342`); audit 0 errors (the 5 kept
  warnings: the orbs' sink and the Eye's answers).

## Twenty-ninth session (A5 s29, 2026-11-22, merge point 41 rebuild; run files output/studio_cal/a5/s29/)
- Not rebuilt. gen_playtests.py's `says`/`click_dialog` accept a status line or a window (F13): dragon_clouds passes
  step 15; it now fails at step 45 (the riddle's "Very good, mortals" line, A3's hook change) and the walk at step 118
  (XD-19's way out, its new leave window): both need a session with X9's rebuild for F16 (gates into XD-19/FD-04).

## Thirtieth session (A5 s30, 2026-11-22; run files output/studio_cal/a5/s30/)
- F16: `door:xd19` carries `screen: {text: 5019}` and `door:fd04` `screen: {text: 5065}` (`gen_plan.py`): the gate
  and the dragon-head door show the MM6-MM8 entrance window with A3's trans line; OK enters. D-72: the five roc nests
  ask "Roc Nest.  Destroy?" with Yes/No buttons (`gen_objects.py`; No leaves a status line). The bullseye's top strip
  in deck, not xctarget (the audit's `textures.feature_repeated` error gone; `gen.py`). Backups `*.pre_s30`.
- Tests (`gen_playtests.py`): the gate's window and XD-19's leave window (OK both ways), the FD-04 window, the nests'
  buttons, the Eye's answer and the crystals' else line as window-or-status (F13). Stage 8 of 8, installed 01:43
  (blv/scene/studio/lua); audit 0; MAW reserve and `xeen_balance.py --check` clean.
