# XD-08 Tomb of a Thousand Terrors, L4: notes

`agent:xeen-a7-xd08` (lane A7), 2026-11-20. Key `xd08`, project `xeen_xd08`, stem `xeen_xd08.blv`, map_stats 9124,
music 20, world `xeen`, class M, on X3, treasure 2 (hoard 3). Every project file of L1-L4 is written by
`output/studio_cal/xd08/tools/gen.py` (edit it and rerun `output/studio_cal/xd08/cycle.sh`: gen, fmt, validate L1-L4,
build, install into the scratch root `output/studio_cal/xd08/root`, audit); the playtests are hand-written. Not
installed in `assets_dev` (the lane lead installs). Sources: the MU-6 graph `devdocs/xeen/mockups/act2_graphs/xd08.graph.yml`,
decisions D-4 XD-08 (`act2_dungeon_decisions.md`, which win), the reading of `../L1/NOTES.md`.

## What was built

23 rooms (the graph's 22 and the cage shaft), 24 sectors, 40.2 M units² of floor, all rectangles; no room stands
over another.

```
 -1280                [Hall of a Thousand Terrors: throne of skulls, Tomb Guards, hoard T3]
                          | great doors
                      [Bone pit: two pits of bones, the ledge between, Skeleton Lords]
                          | open
                      [Deep crypt: graves, Grave Ghouls]
                          | stair (20 x 32)
  -640  [Barracks T2: 2 Might Boosts]=door=[W ring]--[PORTCULLIS way]--[E ring]--[Cage pit]
        [Embalming: 7 juices]=door=        |  \       | PORTCULLIS     |   |       | lower gate
                                           |  [COFFIN VAULT: great coffin, 5 Megacredits, Might 30]
                                           +--[Ossuary: bones that rise]--+   |      [SHAFT: hanging cage]
                                                              maiden stair |      | upper gate
     0  [Stocks T2]--[W mourning T2]=door=[Chain room: MANACLES]  [Iron maiden: SECRET]  [Cage room]
                          || door          | open                 | open                 | open
                     [Hall of Welcome: statue]--[GALLERY OF TERRORS: devices]=door=[E mourning: biers]
                          | open
                     [Tomb door: arrival; out to X3]
```

- **The tomb** (0; MM7 Temple of Baa d04: brick `t6s1bs`, flags `t6s1fl`, coffered ceiling `t6s1c`, the skull frieze
  `t6s1b` as a band in the tall halls): entry, Hall of Welcome (the statue on its plinth: its plaque is
  `m10.tomb_welcome`), Gallery of Terrors (3,328 long; four cages on plinths, the plaques "Manacles" and "Iron Maiden"
  by their arches), the west mourning hall (four stone coffins, two say "The coffin is empty."), the east mourning hall
  (three biers with their dead). Loop: welcome - gallery - chain room - west mourning.
- **The torture rooms** (0; d04's green-black slabs `t4s1fl`, iron): the stocks yard (three stocks of iron-banded
  timber `7gt001a`, a skeleton in each, a chest under the last, plaque "Stocks"); the chain room (four chains from roof
  to floor, two skeletons under them, the manacles lever: "Far below, iron grinds upward." raises the portcullis);
  the iron maiden (its front a secret iron door between two tall iron case blocks; behind it a stair of 20 risers down
  to the east crypt ring); the cage room (the cage's gate, its call button and plaque "Cage").
- **The hanging cage** (D-4.4): `mover:cage` in `room:shaft` (512 square, -640 to 640), XD-04's hoist method with
  cage_1's bars: an iron floor 504 square filling the shaft, see-through `xwcage` bar panels on its two closed sides,
  four corner posts, a top frame, a hanger bar and the chain to the roof, all riding as one mover (the bars ride: the
  D-4.4 fallback was not needed). Travel 640, at the top on first entry. Click the cage to ride; the call buttons beside
  both gates and the gates themselves call it. The upper gate (`door:gate_top`, bars) is shut whenever the cage is
  down, the lower gate whenever it is up (no 640 drop, nobody under the cage).
- **The crypts** (-640; MM7 Barrow I mdt03: `t5bs`, `t2bs`, `t4bs`; the dressed `hwp1b` in the coffin vault, embalming
  room and ossuary): the cage pit, the crypt ring (east and west sides, the portcullis way between them north, the
  ossuary south: loop), the coffin vault (eight heavy coffins; the great coffin at the north wall, flanked by
  candelabra), the barracks (a halberd rack, barrels and sacks in pairs along the walls, the pay chest), the embalming
  room (seven basins round the slab, each with its own coloured light), the deep stair. Loops: the crypt ring; the cage
  down and the maiden's stair up.
- **The deep** (-1280; MM8 rock `gcav1flr`, `gcav2flr`): the deep crypt (graves, bones), the bone pit (two halves 192
  deep with skull piles, a rock ledge between them, steps out of each half), the Hall of a Thousand Terrors (the Baa
  set again with slabs and the frieze, four pillars, a dais with the throne of skulls and two skull piles, braziers,
  the hoard).

**Monsters** (MAPS §0: party 15-17, levels 15-30, treasure 2; D-4.1: no Tomb Terror): 25 spawn markers with fixed
tiers. Slot 1 Xeen Zombie at c (Grave Ghoul 18, 11252): 11 markers of 2-3; slot 2 Xeen Spirit at a (Polter-Fool 18,
11260): 3 markers of 1-2, at b (Tomb Guard 26, 11261): 9 markers of 1-2 (east mourning, barracks, coffin vault, the
Hall); slot 3 Xeen Skeleton at c (Skeleton Lord 16, 11242): 2 markers of 2-3 (ossuary, bone pit). About 50 (38-63)
monsters; kill XP about 30.8k, 7.7k per member against MAPS's 7.2k (+7 %).

**Chests** (5): stocks T2, west mourning T2, barracks T2 (two fixed Might Boosts 240 and pay), the great coffin T2
(five King's Megacredits 12192 and offerings; Might 30), the hoard T3.

**Textures**: 27 distinct (cap 45), 0 new (`tools/xeen/texture_budget.py --root output/studio_cal/xd08/root --map
xeen_xd08.blv`).

## Quest hooks (A3), qbits, player bits

- `m10.tomb_welcome`: `evt:welcome` (35), the statue's plinth (`platform:statue`).
- `m10.tomb_vault`: `evt:great_coffin` (19), the chest preset on `chest:great_coffin` (title "Coffin"), condition
  `stat: {name: ActualMight, at_least: 30}`, else "You are not strong enough to open the coffin." (aaze0080:10). The
  coffin holds the five Megacredits (the hook's `map_gives`). The playtest asserts bit 111201 and five 12192.
- Map qbits (110760-110799): `manacles_pulled` 110760 (one used).
- Player bits 11270-11276: the juices red (Might), blue (Personality), orange (Intellect), green (Endurance), yellow
  (Accuracy), purple (Speed), white (Luck), in the source's order (aaze0080:2-8 with :17-23); +2 each (D-4.2), then
  "The liquid is powerless." (aaze0080:9).

## The Might check, measured (D-4.5)

- A chest's fixed potion gets its power from `ItemGenerator::assignPlacedPotionPower` (`game/gameplay/ChestRuntime.cpp`
  around line 477): **uniform 5 to 19**, seeded per save, map, chest and item record; the two Might Boosts roll apart.
  Might Boost (`engine/data_tables/potion_effects.yml` 240) gives TempMight 3 x power: **+15 to +57**.
- Measured in `playtest.yml`: a member of Might 15 drinks a Might Boost of power 5 (the least a chest gives,
  `grant_item`): **Might 30** (`party()` log), and the coffin opens for her. The check reads the member who clicks:
  Brokk (Might 17 after the red juice) is refused while she has 30. In one run the chest's own potion (power 18) gave
  Sefa Might 69.
- A starting human has Might 11, an elf 7 (`class_starting_stats.txt`; level does not raise it). A human reaches 30 with
  power 7 or more (13 rolls in 15), or 6 or more after the red juice (+2, same dungeon; 14 in 15); an elf of 7 needs 8
  or more (12 in 15). With two potions a party fails only if both roll low: about 1 in 225 for a human who drank the red
  juice. The scenario's default party has Might 15 for every class, which reaches 30 with any chest potion.
- So: **yes in nearly every game, not certain** (DECIDE 1 below).

## Exit to X3 (live since 2026-11-20)

X3 was installed while this map was being built (lane lead's message): the tomb door is a real exit.
`exit:x3` (the door room's south wall, a 224 x 448 iron door `t5d1`), `evt:exit_x3` (36) preset exit, hint "Leave the
Tomb of a Thousand Terrors" (aaze0080:24; the game's window asks "Do you wish to leave ...?"), project neighbour
`door:x3` to `xeen_x3.odm`, arrival (-15360, -9830, 1146) facing north (direction 90, MoveToMap 512), from X3's
`DOORS.md`. `playtest_exit.yml` takes the door and asserts X3 and the party at (-15360, -9830): **measured Z 1146.5**,
as DOORS.md says.

**For X3 (A5)**: X3's barrow door (`thing:tomb`, `m10.tomb_door`) should bring the party to this map's start, inside
the tomb door: **(0, 384, 0), facing north (90 deg, MoveToMap 512)** (`objects.yml` start).

## Sealed exits

None any more. (Before X3 was installed the tomb door was a text panel "The tomb door has swung shut behind you ...";
replaced by the exit above.)

## Original lines

"A plaque at the base of the statue reads: Welcome to the Tomb of a Thousand Terrors. Insanity is our fame, undead is
our game." (aaze0080:0, through A3's hook); "The coffin is empty." (aaze0080:1, two coffins of the west mourning hall);
the seven "<Colour> Tomb Juice" (aaze0080:2-8) and "The liquid is powerless." (aaze0080:9); "You are not strong enough
to open the coffin." (aaze0080:10); the plaques "Manacles", "Cage", "Iron Maiden", "Stocks" (aaze0080:11-13, 25);
"Leave the Tomb of a Thousand Terrors" (aaze0080:24, the exit's hint); "King's Megacredit!" (aaze0080:26, A3's hook).

## Words needed (workarounds)

- **Liquid colour per face**: the seven juices want seven coloured liquids. The liquid shader colours a liquid by its
  texture name (`engine/liquids/liquids.yml`), so seven juices need seven entries there (A1; a texture name needs no
  art for a shader liquid, and `worlds: [xeen]` keeps them in this world). Workaround: all seven basins are MM7's slime
  water (`7slimywtr`, liquid) and each has its own coloured light 112 over it (red, blue, orange, green, yellow, purple,
  white); the colours read on the walls and the liquid. MM6's stat barrels already have the seven colours as models
  (`decoration_overlays.yml`, `mm6_deco_barrel_liquid_*`), but the overlay is picked by the decoration's state, which the
  studio cannot set (a second way: a decoration `state` word).
- A one-shot arrival timer for the arrival line (as XD-07: a load event's window is not shown).
- Many MM6 dungeon decorations draw nothing in Xeen dungeons (`hngncge2`, `empty`, `noose`, `sklabra0`, `sklspear`,
  `urn`, `tcurn`, `urn2`, `dec21`: bound per map only, or not at all); replaced by `7dec05`-`7dec07`, `cndlab0`,
  `7dec20`, `dec29`.

## Dressing exceptions

None: `oymap audit --world xeen --reach --solve` gives no dressing error or warning.

## Checks

All from the scratch root `output/studio_cal/xd08/root` (a hard-link copy of `assets_dev` with real copies of
`worlds/xeen/maps`, `events/maps` (X3's files copied in after its install), and of `data_tables/map_stats.txt` and
`bolster_maps.txt` with a **test row 9124** (kept by `output/studio_cal/a7/sync_test_rows.py`); A2 has no XD-08 row
yet), `build-xeen/game/openyamm --world xeen`:

- `validate` L1-L4 clean; `build`: 23 rooms, 1,194 faces, 25 portals, 15 door records, 27 lights, 25 spawns, 35
  events, 5 chests, **no warning** (`output/studio_cal/xd08/build.log`); `audit --reach --solve`
  (`output/studio_cal/xd08/audit.txt`): no error, warning or info; 0 faces in one plane; on foot 6 of 23 sectors with
  the doors as they start, 23 with every door out of the way; `oymap solve`: 2 steps, never reached 0.
- `playtest.yml` (155 steps), `playtest_hostility.yml` (28) and `playtest_exit.yml` (17), 4 of 4 each:
  `output/studio_cal/xd08/four.out` (after the last build; `four_r1.out` the round before), logs `output/studio_cal/xd08/run/`.
- Texture budget 27/45, 0 new.
- Pictures (contact sheets; the PNGs were deleted for disk space, `look1.yml`/`look2.yml` remake them with `tour.sh`):
  `output/studio_cal/xd08/look1_a.jpg`, `look1_b.jpg` (29 shots, every room), `look2.jpg` (after the fixes).
  Fixed after looking: the welcome statue (`sta1a` read as a white urn in a cage) is now an armoured statue `7dec55`;
  the chain room was bare (two skeletons under the chains); the throne of skulls was the wall's slab and vanished into
  the wall (now the skull frieze `t6s1b` on its seat and back); the Hall's red light was too strong.

## DECIDE

1. **The Might check's certainty.** What: the great coffin needs the clicking member's Might 30; the barracks' two
   Might Boosts have power 5-19 (+15 to +57), so a party fails only if both roll low for its strongest member (about 1
   in 225 for a starting human who drank the red juice, 1 in 25 for an elf of Might 7 with no juice). Options: (a)
   keep (taken: cheapest to reverse; shops, alchemy and spells also give Might); (b) lower the check to 25 (always met
   with one potion by a human); (c) potions of a fixed power in the chest (needs a studio word: an item's power in a
   chest); (d) test the party's strongest member, not the clicking one (a Lua condition). Evidence: "The Might check,
   measured" above. Depends on it: the coffin's condition only.
2. **The juices' colours.** Seven shader liquids for Xeen (A1, liquids.yml) or the MM6 stat barrel models (a studio
   decoration-state word) instead of the slime water with coloured lights. Taken meanwhile: the lights.

## Open issues

- **A2**: map_stats row 9124 (slots below; lock 2, trap 1, perception 2, treasure 2, music 20, STONEROOM); the test
  root has a copy.
- See-through door leaves show pink speckles in the current game build (known, reported to A1); the cage's bars and
  gates are `xwcage`.
- Lighting is unbaked (the lane lead bakes after install).

## What the user should look at

The hanging cage ride (in the cage, click it; the gates and the call buttons); whether the iron maiden reads as a
maiden (an iron door between two iron case blocks under its plaque in the gallery) and is found by a click; the juice
basins' coloured lights; the great coffin's refusal and the potion; the bone pit's two pits and ledge.

## Installed (2026-11-20, lane lead A7)

Built from this L4 (`output/studio_cal/xd08/a7_lead_build/`, identical to the sub-agent's scratch install) and
installed into `assets_dev`; baked (profile `tools/lighting/baked_indoors/profiles/xeen_xd08.yml`, `bake_map.sh xd08
output/studio_cal/xd08/root --sources assets_source`, then `install_bake.py xd08`; 3.1 MB); `stale_bakes.py` lists
nothing for it. The map does not load from `assets_dev` until A2 writes map_stats/bolster row 9124 (slot lines in
the lane's report, as in "What was built"); the playtests from `assets_dev` follow then. The tomb door is live to X3 (measured Z 1146.5 at the
arrival). The barracks chest's two Might Boosts roll their power (5-19) in the game: A2's "power 10" needs a studio
word for a chest item's power (asked of A1); meanwhile the check stays at 30 (DECIDE in the lane's report).

## D-22.2 and D-22.3 (2026-11-20, lane lead A7, fourth session)

- **The pay chest's Might Boosts (D-22.2).** The barracks chest holds no fixed Might Boost any more (pay and two random
  items); `evt:chest_barracks` gives two Might Boosts 240 of power 10 (+30 Might) on its first opening only:
  `evt.SetHeldItem(240, {bonus = 10})` twice behind the new map qbit `pay_potions` **110761** (A3 to register), with
  the status line "Two flasks of red draught lie on top of the pay." (the first flask goes into the opener's pack, the
  second onto the cursor). `playtest.yml` now: the coffin refuses Sefa at 15; the pay chest gives both flasks and the
  qbit, a second opening gives nothing; the console sets Sefa's Might to 7 (`lua SetValue(BaseMight, 7)`), one flask
  makes her 37; Brokk (15) is refused, Sefa opens the coffin; Ivar at 7 drinks the other flask, 37 again (both power
  10). The "chest item power" studio word is withdrawn.
- **The juices (D-22.3).** The seven basin tops are A1's world liquids `xjuicered`, `xjuiceblu`, `xjuiceorg`,
  `xjuicegrn`, `xjuiceyel`, `xjuicepur`, `xjuicewht` (no art: the liquid shader draws them; a root without A1's
  `liquids.yml` entries draws nothing there, so check from `assets_dev`). Pictures (`output/studio_cal/xd08/juice_b.jpg`
  with the old lights, `juice_c.jpg` after): the full-colour lights 288 painted the walls in rainbow bands once the
  liquids carried the colours; each basin now keeps a faint glow of its own (radius 160, colour at 40 %).
  Textures 33/45 (the seven liquid names count), 0 new.
- Rebuilt (`xcycle.sh`: validate clean, build no warning, audit no error or warning), installed into `assets_dev`,
  re-baked (`bake_map.sh xd08 assets_dev`, 3.1 MB), `stale_bakes.py` lists nothing for it. From `assets_dev` with
  `--world xeen` (A2's row 9124): `playtest.yml` (173 steps), `playtest_hostility.yml` (28), `playtest_exit.yml` (17)
  **4 of 4 each, clean exits** (`output/studio_cal/a7/s4_xd08_four.out`). The generator before D-22:
  `output/studio_cal/xd08/tools/gen_before_d22.py`.

## Sixth session (2026-11-20, lane A7)

- **Lamp rule (A1's lights audit, merge point 14):** the terror hall's two chained `brazir2f` are `flamb00` flambeaux; `skulltorch_08` moved along the west
  mourning room's south wall (0.7 → 0.4) out of the doorway. Clean under the audit.

## Texture fit (2026-11-20, merge point 16, lane A7, eighth session)

- The vault portcullis `xkportc` at `scale: 1.5` (one picture up the 384-high gate; was 1.5 copies).

- `playtest.yml`: the coffin's `loot_chest(19)` is followed by `close()` (A1, merge point 18: Take All leaves the loot
  screen open, as in the game). It was the screen the eighth session's Escape after the second Might Boost closed; the
  Escape is gone. 12 of 12 from `assets_dev` (`output/studio_cal/a7/s10_names_xd08.out`, tenth session).

### Texture fit exceptions

- `textures.tile_seams` `xwiron`: the cage's bars, posts and rails, the iron maiden's case and its folding leaf (a folding leaf takes pictures at one texel a unit); the plate edges read as the iron's joints.
