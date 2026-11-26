# XD-19 Castle Xeen: L4 notes (lane A7 phase 5, agent:xeen-a7-xd19)

Map 9144, stem `xeen_xd19.blv`, class L, on X9 (the Clouds of Xeen), music 22, treasure 5 (hoard 6). Graph
`devdocs/xeen/mockups/act5_graphs/xd19.graph.yml`; decider D-47 (`mockups/act5_a7_decisions.md`, Q7-Q16) wins.

## How to resume

- Everything is written by `output/studio_cal/xd19/tools/gen.py` (L1-L4) and `tools/gen_tests.py` (playtests).
  Never hand-edit the written files; change the generator and run `bash output/studio_cal/xd19/cycle.sh`
  (gen, fmt, validate, build to `output/studio_cal/xd19/build`, install into the scratch root
  `output/studio_cal/xd19/root`, audit to `output/studio_cal/xd19/audit.txt`), then
  `openyamm-studio/build-xeen/oymap record devdocs/xeen/briefs/xd19/L4 --author agent:xeen-a7-xd19 --label "..."`.
- Run the cycle twice after a change that adds sounds: gen.py reads the sound numbers from `ids.lock.yml`. Lord
  Xeen and his two guards are freed by `ActorIndex("monster:lord_xeen")`, `"monster:throne_1"`, `"monster:throne_2"`
  (sixteenth session; no actor index is read from a build any more).
- Then `python3 output/studio_cal/xd19/tools/gen_tests.py` and the playtests:
  `ROOT=/home/pjasicek/github/OpenYAMM/output/studio_cal/xd19/root KEY=xd19 TESTS="playtest playtest_pool
  playtest_hostility" N=4 bash output/studio_cal/a7/xfour.sh` (logs in `output/studio_cal/xd19/a7_xrun/`).
- Pictures: `output/studio_cal/xd19/shots.sh` (tour `shots.yml`, PNGs in `shots/`, sheets in `look/`).

## What was built

Four floors 640 apart, drawn on a base grid scaled by 5/4 (walls 160 thick). 51 rooms (52 sectors), 140.8 M units²,
2,481 faces; 18 doors (two two-leaf pairs: the great hall's north doors gnecdr1l/r and the throne doors gnecdr4l/r)
plus the gate's two leaves (exits to X9); 7 chests; 72 monsters (70 + the two bosses).

- **F0 (z 0), the lower castle:** the gatehall (arrival, the gate to X9), the Hall of Xeendom (nave and two aisles behind
  arcades), the west and east wards, the barracks and the armoury (chests), the west and east galleries, the cold
  vault (Water Generator) and the gravel vault (Earth Generator, gravel bed), the stair hall (the grand stair), the
  two towers' first stairs.
- **F1 (z 640):** the towers' upper stairs, the wall walks under open sky (each with a roofed turret), the keep's two
  doors into the foundry's machine bays, the guard foundry (the slow line, the bays' shutters), the grand landing,
  the parts store (store: true, chest), the guard bays (gem tray), the keep stair's foot.
- **F2 (z 1280):** the tower tops (Fire Generator south-west, Air Generator south-east), the upper galleries, the war
  room and the demons' quarters (chests), the barrier hall (four pylons, the field, two Greater Elementals) with its
  two bays, the keep stair top, the crown stair behind the field.
- **F3 (z 1920):** the crown landing, Xeen's Aviary (two rooms under open sky, the Pet held by two 256-high arches),
  the keeper's walk round it, the keeper's loft (six steps up, chest), the throne doors, the throne room (sight plate
  inside the doors) and Lord Xeen's dais (throne, Sixth Mirror), the treasury (hoard, T6).

Vertical ways: two-storey stair halls (20 steps of 32 over 800 to a gallery 640 deep), as DD-07's: towers (two each),
the grand stair, the keep stair, the crown stair.

### Monsters (D-47 Q16): 70 + 2

Demon 11630 x 28, Devil 11631 x 14, Screamer 11632 x 4, Xeen's Guard 11603 x 14 (four hidden at the chutes), Lesser
Elementals 2 each (fire 11620 at the fire top, air 11624, water 11625, earth 11626 at theirs), Greater Elemental
11622 x 2 at the barrier; Xeen's Pet 11644 in the aviary's roost, Lord Xeen 11634 on the dais. Floors: F0 27, F1 16,
F2 19, F3 8. Quiet: the gatehall, the crown landing, the throne doors. Kill XP 54.38k per member (57.99k with the
bosses), D-47's numbers. Rest encounters (map card): 10 %, slot `Xeen Demon` tier 5 (Dif 5), per marker 1-2.

### Mechanisms

- **Generators (Q8):** each core a destructible platform (hp 300, metal) between two Ancient housings; its click asks
  "X Generator.  Destroy?" (Yes breaks it; blows and spells break it too); `on_destroyed` calls `m35.gen_<element>`,
  switches its hum off (`AmbientSound<n>` 2), puts out its glow and its pylon's light, and darkens the pylon. A load
  event keeps it so.
- **Barrier (Q9):** four pylons in the barrier hall, each's hover "<Element> pylon: to <its tower or vault>"; a 1 s
  timer asks `XeenQuests.can("m35.barrier")`: true drops the field (door, xafield), sets barrier_down 118062, calls
  the hook (its line), stops the crackle, shakes; a load event keeps the field down. The field's click while it
  stands calls the hook (its fail line).
- **Guard pool (Q7):** two destructible machines (hp 400) in the machine bays with the "Guard Making Machine.
  Destroy?" question; the first step into the foundry (any of its rooms or the grand landing) starts a clock: every
  45 s while either machine stands one of the four hidden guards (groups 41-44, at the chutes) is shown (its group's
  Invisible bit cleared) and takes the party on; both machines broken: every guard still hidden is shown, the bays'
  shutters roll up (bays_open 118063), the gem tray gives three Emeralds once. The count is always 70.
- **Xeen's Pet:** a 2 s kill timer calls `m35.pet`. Opens nothing.
- **First sight (Q13):** the plate inside the throne doors calls `m35.lord_xeen_sight` once; Lord Xeen and his two
  guards are placed immobile and freed 4 s later (`evt.SetActorImmobile` false, `evt.SetActorTarget` party).
- **Lord Xeen (Q12, Q13; merge point 21's `monster_damage` trigger, fourteenth session):** `evt:lord_damage`
  (`trigger: monster_damage`, `actors: [monster:lord_xeen]`) zeroes every hit but melee with the Xeen Slayer Sword
  (12500) (`evt.SetHookDamage(0)` unless `hook.attack == 'melee' and hook.weaponItemId == 12500`); the first zeroed
  hit of a visit calls A3's `m35.untouchable` (map var `untouched`, cleared by `evt:lord_untouched_leave`); a hit
  before the plate runs `m35.lord_xeen_sight` and starts the 4 s clock (the plate then skips: its condition is the
  sight bit 111709). The load-time `evt.SetMm9ActorCanReceiveDamage` is gone. His death (kill timer) calls
  `m35.lord_xeen` and opens the treasury (a load event keeps it open). The sword's double damage on demons is A2's
  `SlayingDemon` item flag.
- **Scepter (Q14):** the throne's click: before his death `m35.scepter`'s fail line; after it `m35.scepter_ask`
  shows its text (called from the condition, so the question follows it) and asks "Take (Yes/No)?"; Yes calls
  `m35.scepter` and plays `cinematic:mirror` (three shots, A3's four subtitles, `xeen_mirror_shatter`, shake,
  `xeen_castle_groan`, the mirror's light out); its done event `evt:after_mirror` leaves at once to X9's
  `entrance:xd19_gate` (the studio's `leave`: `evt.MoveToMap(..., {direct = true})`). After: the hook's else
  line. The mirror's click: `m35.mirror` (aaze0078:5) before, a map-local line after.

## Measurements

- **For A5's X9 (D-50 assumed a shell of 7,168 x 6,656 with walls 2,688 high; measured from gen.py's rooms):** the
  rooms span x -5,120..5,120 and y -4,800..5,280 (10,240 x 10,080 inside), with walls 160 thick about 10,560 x 10,400
  outside. The gate stands in the gatehall's south wall at y -4,320, recessed 480 behind the towers' south faces
  (y -4,800). Gate opening: 512 wide (two leaves of 256: inside, the west leaf shows `gnecdr1r` and the east leaf `gnecdr1l`;
  on X9's outside face the west leaf, the left seen from outside, shows `gnecdr1l` and the east leaf `gnecdr1r`) and 512 high, sill at the gatehall floor (0 here).
  Heights above the gate's floor: the gatehall and halls 768-1,152; the wall walks (F1, open sky) at 640 with walls
  768 high (top 1,408); the tower tops (F2) to 1,984; the keep (F3: throne room) to 2,816; the aviary's walls (open
  sky) to 3,456, the highest point.
- **Exits (D-50; fifteenth session):** the gate's two leaves (`exit:gate_r`, `exit:gate_l`, each its wing, the `exit`
  preset "Exit Castle Xeen"; X9 is indoor, so no leave window) and the scepter's leave go to X9's named arrival
  `entrance:xd19_gate` (0, 11264, 768) facing south (1536); the party lands at z 768. X9's gate names this map's
  `entrance:x9_gate` (A5 opens it once this map is installed).

- Arrival `entrance:x9_gate`: (0, -4064, 0), F0, facing north (the leaves at y -4320, 256 behind).
- The way out: the gate's two leaves to X9's `entrance:xd19_gate`.
- Levels and treasure as MAPS §0 and D-47. 32 distinct textures (cap 70), 7 new (D-51 3(c), "Textures").

## Map qbits (block 118060-118079)

118060 machine_w_down, 118061 machine_e_down, 118062 barrier_down, 118063 bays_open. A3's bits named in
project.yml: 111700-111707, 111709.

## Test rows

None. A2's rows landed before the build (map 9144, elementals 11624-11626, Lord Xeen's HP); the root's tables are
real copies of `assets_dev`'s (`copy_tables.py`), no rows of its own.

## Blocked on

- **A5:** X9's gate into this map (to `entrance:x9_gate`), opened once XD-19 is installed (fifteenth session).
- **S:** bindings and skins for 11624-11626, and the bosses' own recolour skins (no map change). `xeen_guard` landed
  (S session 7): Xeen's Guard 11603 wears it.

## Words needed

- None open. (A placed monster's actor index: `ActorIndex("monster:x")` since the sixteenth session; the cinematic's
  `event` cue is counted by the audit since merge point 22.)

## Audit exceptions

None since merge point 22 (the cinematic's `event` cue counts as run). No dressing, lights, doors or texture-fit findings (0 errors, 0 other warnings).

## Original lines

aaze0075:0 (the machines' question), aaze0075:1-4 (the generators' questions, renamed Fire, Air, Water, Earth after
the source's Fire, Electricity, Cold, Poison), aaze0078:5 (the mirror, by A3's m35.mirror), aaze0078:4 (the
cinematic's subtitles, A3's text), aaze0075:6 (the exit's meaning). aaze0075:5 and aaze0078:3 are not
used (D-47 Q15).

Map-local lines (for A3's ledger): a broken
machine "A broken press. Nothing comes out of it any more." and "The machine shudders, jams, and stops stamping.";
the pool "A press thumps. A new guard steps off the line." and "Both machines are still. The bays' shutters roll up,
and the last guards step off the line."; the gem tray "Green gem eyes, a whole tray of spares. You take three
emeralds." / "An empty tray."; the pylons "The <element> pylon. Its conduit runs to <the tower or vault>."; the empty
frame "An empty frame. Silver dust and shards of glass."; the war table; the demons' beds.

## Textures

MM8 Escaton's Palace d35 (gnecwal1, gnecwalt frieze row, gnecwal2 pillars, gnecflr, gtrlflr, gnecclg2, gnecstpv/f,
the gnecdr door family) and the Ancient kit (swll4dk, swll5dk, swpnl, swtrpnl, swdoorc, xahullbn, xaenergy, xafield).

**The seven new textures (D-51 3(c), fourteenth session, 2026-11-21):** made in one Codex batch with
`level_generation/textures_xeen/xtex.py --project output/studio_cal/xd19/tex` (specs.yml, raw/, refs/, prompts/,
finished/, sheets/; `sheets/finished_v1.jpg`, `sheets/mirror_pair.jpg`), installed with `xtex.py install --root
assets_dev --world xeen` (and into the scratch root), masters in `assets_source/worlds/xeen/textures_x4/`. A6 registers
them (D-47):
- `xcorefire`, `xcoreair`, `xcorewater`, `xcoreearth` (128 x 256, a picture seen at 192 x 448, `fit`): each
  generator core's four faces, an Ancient steel column round a window of its element (fire, violet lightning, ice
  water, green-fumed rock). The pylons in the barrier hall stay `xaenergy` (their own light per element).
- `xsigilban` (128 x 256, `fit`): Lord Xeen's sigil (a horned crown over a staring eye in a ring of points, gold on
  red and black) on a swallow-tailed banner. Four in the Hall of Xeendom (192 x 384, either side of the inner arch and
  of the great doors, from 256 up) and one over the gatehall's inner arch (112 x 224, hanging from the roof; that wall
  is black stone to its top, without the gold frieze row, so the banner hangs on the stone it was painted on).
- `xmirror6` (256 x 256, seen at 512 x 448, `fit`): the Sixth Mirror, `panel:mirror` on the dais's north wall behind
  the throne (it replaces the free-standing block that showed D-37's `xkmirror`). `xmirror6x`: the same frame
  shattered (an `edit` of xmirror6's master, so the frame is the same), swapped in by the cinematic's cue
  (`evt:mirror_shatters`, `set_texture`) and on every later load (`evt:mirror_load`).
Textures: 32 distinct of 70 in the L4 files (7 new; `xkmirror` no longer used).

## What the user should look at

- The unbaked rooms are dark or flat until the lead bakes; the pale vault (gnecclg2) reads bright in the captures.
- The barrier field (`xafield` door leaf) is `translucent: 0.5` (D-51 (1)): the crown stair shows behind it.
- The new textures in the scratch root: `output/studio_cal/xd19/s14_look/` (the sigil over the arch, the nave's
  banners, the four cores, the field, the mirror before and after).
- Xeen's Guards show the row's stand-in look until S's model.
- The aviary's walls are 1,536 high round its sky.

## Playtests

All 4 of 4 from the scratch root with `--world xeen` (merge point 21 game, fourteenth session, with the seven
textures and the damage hook), `output/studio_cal/xd19/s14_four_mp21.out`, logs
`output/studio_cal/xd19/a7_xrun/<test>_<n>.log`:

- `playtest.yml` (174 steps): the critical path on foot from the gatehall: arrival, sealed gate, the four
  generators by their questions, the field still up with three down (its fail line), down with four, the crown
  stair, the Pet (m35.pet), the plate (m35.lord_xeen_sight, freed after 4 s); without the sword 96 swings that would
  add up (`kill: true`) leave Lord Xeen at 2,445 and set `untouched` (m35.untouchable once); then the Xeen Slayer
  Sword (12500) in member 0's main hand: he dies (66 landed blows of 178 swings, an Archer of level 50), the
  treasury, the mirror (aaze0078:5), the scepter No then Yes (m35.done, the cinematic, the party stays), the hoard,
  a save and load.
- `playtest_pool.yml` (44 steps): the clock shows one hidden guard after 46 s (the second still hidden), one machine
  down keeps the bays shut, both down show the other three and open the bays, the gem tray, a save and load.
- `playtest_hostility.yml` (48 steps): every row hostile at load and after a reload; four rows side by side do not
  fight each other and go for the party.
- Fifteenth session (merge point 22, installed with its bake): `playtest.yml` now ends with the scepter's Yes and
  the cinematic out on X9 at (0, 11264, 768) (the hoard and the save and load before it; Lord Xeen's HP read from
  A2's row, 2,200); `playtest_gate.yml` (10 steps): the gate's west leaf out to X9. From `assets_dev`:
  `output/studio_cal/a7/s15_xd19_four.out`.
- Not tested by a scenario: a hit before the plate running the first
  sight (the hook's code path; the plate is on the only way in).

Pictures looked at: `output/studio_cal/xd19/look/sheet1.jpg`, `sheet2.jpg` (17 tour shots, unbaked). Fixed after
them: the nave's pillars (were the gold strip gnectr2v, read as glowing tubes; now gnecwal2).

## Twenty-first session (2026-11-21, lane A7 lead)

- The gem tray (A3's question: a probe's `GiveItem(183)` on X3 added no gem) works: `playtest_pool.yml` now counts the
  Emeralds (183) in the packs before and after the click (stowing the held one), 0 -> 3 every run, and a second click
  says "An empty tray." and gives nothing. By the code (`GameplayHeldItemController::
  applyGrantedEventItemsToHeldInventory`), an event's `GiveItem` items arrive on the next frame, each in the hand (the
  one before it pushed into the packs), so a probe that counts the packs alone, or at once, sees fewer. The map is unchanged (no rebuild).
- `gen_tests.py` repaired: gen.py no longer names a build scene (`SCENE`, `LORD_IDX` gone since the sixteenth
  session); the tests read the installed scene's actors for the pool and Lord Xeen's index (group 60). Regenerated: only
  `playtest_pool.yml` changed. 4 of 4 from `assets_dev` (`output/studio_cal/a7/s21/four_xd19.out`).

## Twenty-fourth session (2026-11-21, lane A7 lead): ceilings after the bake (review G3 row 72)

- The reviewer saw the ceilings near white in several baked frames; re-shot from `assets_dev` before the change
  (`output/studio_cal/a7/s24/shots/xd19_before/`, sheet `xd19_before_sheet.jpg`): every room of 448 to 768 showed it
  (vaults, generators, barrier hall, aisles, barracks, quarters, threshold, treasury). Cause: the rooms' fill lights hung
  96 under the ceiling (`min(height - 96, 420)`, radius 1,100-1,600) right under the pale vault `gnecclg2` (mean albedo
  134 against the walls' 66), so the bake (A7's common profile: direct 2, bounce 5, max 1.5) burned a white pool round
  each. The profile and the texture are the set's own (every A7 map bakes with the same profile without it).
- Fix: the fill lights at half the room's height (at most 420): 256 in the 512 rooms, 224 in the 448 ones, 352 in the
  generators; the tall halls (840 and over) keep 420. Colours, radii and the element, field, throne and mirror lights
  unchanged. gen.py's light loop (one line); the L4 regenerated, only `objects.yml`'s light heights changed.
- Built with the oymap of merge point 31: build warnings 0, audit from the root 0/0 (from `assets_dev` 1 warning,
  `event.unbound` on event 61, the cinematic cue; not this change). Installed 16:35:39, baked from `assets_dev`.
- **It did not fix it.** After (`output/studio_cal/a7/s24/shots/xd19_after_sheet.jpg`): the pools are gone but the
  ceilings are evenly pale, the top sixth of the frames as bright or brighter (vaults 180 -> 191, barrier 192 -> 211,
  barracks 175 -> 191, upper_e 139 -> 179; the rest within 1). So the light comes from the bounces off the floors onto a
  pale ceiling (bounce 5, max 1.5), not the lights' height. Next (open, row 72): a per-map profile
  (`tools/lighting/baked_indoors/profiles/xeen_xd19.yml`: bounce_scale about 2.5 and/or max_lighting 1.0), or a darker
  vault than `gnecclg2`; the light heights may then go back. Gameplay unchanged: the installed map is tested as is.


## Twenty-fifth session (2026-11-21, lane A7 lead): the bake profile and the missing cinematic

- **Ceilings (review G3 row 72).** Trials recomposed from the saved passes (no Cycles) and toured from hard-link roots
  (`output/studio_cal/a7/s25/`, `measure.py`: the top sixth and the wall band of the 13 tour frames). The bounce was not
  the cause: halving it (2.5, max 1.5) moved the ceilings by 1 to 10. The direct light of the fill lights saturates the
  ceilings at the 1.5 ceiling, and the pale `gnecclg2` (mean 133 against `gnecwal1`'s 43) then reads near white. Only
  the cap and the direct scale move them. Kept: **`xeen_xd19.yml` direct 1.2, bounce 3, max 1.0** (was 2, 5, 1.5; the
  other keys unchanged). Ceilings at most the texture's own grey (top sixth 191 -> 129 in the vaults, 211 -> 148 in the
  barrier hall, 191 -> 130 in the barracks, 193 -> 132 at the throne), walls a little darker (wall band 74-138 -> 52-95),
  with some fall-off left (only about 11 % of texels reach the cap, against 47 % before). Installed with
  `--recompose` (same BLV) and stale bakes 0. Before/after `output/studio_cal/a7/s25/shots/xd19_before_after.jpg`, all
  13 after `xd19_after_sheet.jpg`. MM9's lightmaps clip at ×1 the same way. A darker vault texture is still possible
  (`gnecclg1` is the warm gilt-strip version, 100) if the reviewer wants the ceiling darker than the walls' frieze.
- **Event 61 `event.unbound` (from `assets_dev` only).** `xeen_xd19.cinematics.yml` (the build's file holding the
  mirror cinematic and its `event: 61` cue) was never installed into `assets_dev`: the lane's install scripts copied the
  BLV, scene, studio file and Lua only, so in the installed game `evt.PlayCinematic("mirror")` played nothing and the
  mirror never shattered on screen. Installed from the session-24 build (its BLV, scene and Lua byte for byte the
  installed ones): audit 0/0 from `assets_dev`; the playtest's log now shows `Cinematic: mirror starts (16 s)`.
  **Every later install of XD-19 copies `maps/xeen_xd19.cinematics.yml` too.**

## F75 (2026-11-26, agent:xeen-fb5-dungeon-f75)

Xeen's Pet (487 high, radius 238) leashed 320 so it stops 64 clear of the 256-high openings round its hall instead of
sinking into the nearest (640 from its post; `tools/xeen/check_monster_fit.py`: 3 stuck -> 0).
