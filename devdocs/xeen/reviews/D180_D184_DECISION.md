# D-180 to D-184: the decider's answers to the 2026-11-26 round's design questions

Decider, 2026-11-26, read-only. Source: [PLAYER_FEEDBACK_20261126.md](PLAYER_FEEDBACK_20261126.md) (F74, F77). Every
number below was read from the files named beside it on 2026-11-26.

---

## D-180: the Temple of Yak's door, and doors on big buildings (X2 p14, F74)

**What is there.** `level_generation/projects/xeen/x2/gen.py` 1421–1437: `thing:yak_temple` is a stone building
4 × 2.5 cells; its `front` part is 1,152 wide with walls 704 high, a 288-deep porch on posts 576 high, two towers of
1,088; `door: {part: front, wall: n}` gives no size, so the studio lays its default door. The latest X2 build
(`output/studio_cal/x2/build_w/export.json`, 2026-11-25 15:01) has it **128 wide and 256 high** (`xvtdoor`, the classic
tower kit's single door, at z 1088–1344). Inside, XD-06's porch (`xd06/gen.py` 99, 536–538) is 1,280 × 1,152 with a
1,024 ceiling, and its way out, `exit:woods`, is a door face **224 × 448**; the porch's inner Yak door is 256 × 512. So
the player is right in both halves: the door is a house door on a front 2,048 wide with walls 704 to 1,088 high, and
the same door seen from inside is 1.75 times as tall and as wide.

**MM6–MM8.** All 42 shipped ODMs measured (door-class textures of `engine/models/texture_classes.yml` on BModel
faces): the door leaf is 128 × 256 on almost every building whatever its size (median 128 × 256 in every height band,
also on MM8's Temple of the Sun, 1,792 high, and MM7 `out10`'s temple `kTemple2`, 2,032). Big buildings show their
size with **two leaves** (MM6's castles `tdoorb` 256 × 256, MM6's pyramid 256 × 256, `kTemple2` a 2 × 128 pair) and a
porch or frame round the door; no shipped door is taller than 256. Xeen has already gone past that on its own big
gates, with the studio's `door_height` and a door bay listed wider: Castle Burlock's gatehouse 512, Castle
Blackfang's gatehouse 384 × 448 (D4), Necropolis's gate 384 × 384 (D6), one D2 hall 352, others 288–320. The
classic kits carry a wing picture for the pair (`xvtdoorw`, `xvdoorw`, `xvsdoorw`; texture_classes `door: wing`).

**DECISION.**
1. **The Temple of Yak:** a double door, the door bay 384 wide (two leaves of 192), `door_height: 384`, the tower kit's
   wing picture `xvtdoorw` (the second leaf mirrored, as F2's pairs), laid as D6's Necropolis gate lays its pair (the
   north wall's bays listed with `['door', 384]`, `door: {..., leaves: 2}`). Each leaf is then 192 × 384, the
   picture's own 1:2, so nothing is stretched. It stands under the 576 porch with a lintel, and from inside the 224 × 448 exit reads
   as the same door (rule 2's tolerance); XD-06 is not rebuilt.
2. **The rule, every outdoor map of Xeen:**
   - (a) *A building whose door leads into a dungeon* (`into:` a BLV through a building's door; cave mouths, hatches
     and culverts are not building doors): its outside door is at least as wide as the BLV's inside exit face and
     within 64 of its height. Where the BLV's exit is the larger, the outside door grows; the BLV is changed only
     when the outdoor wall cannot hold the door (wall height less 128 for the lintel).
   - (b) *A big building* (a temple, castle, keep, gatehouse, guild hall or tower; or any building whose door part has
     walls ≥ 640 high and a front ≥ 1,024 wide): a double door of its kit's wing picture, door bay 384, door_height 384
     (448 where the walls are ≥ 896 or rule (a) asks for it). A building already larger by its own decision (Castle
     Burlock 512, Blackfang 384 × 448, Necropolis 384 × 384) keeps its size.
   - Town houses, shops and the town temples at house scale (walls under 640) keep MM6–MM8's 128 × 256.
3. **The check that keeps it:** `tools/xeen/door_check.py` gains `doors.small_for_building` (rule b) and
   `doors.inside_mismatch` (rule a: reads the BLV's exit face from its export, as `check_door_leaves.py` does); an
   error on Xeen's outdoor maps, with `--list` giving the before/after table.

**WHY.** The inside and the outside of one door must agree; that is the player's actual complaint. MM6–MM8 kept the
leaf small and doubled it, but Xeen's own big gates already use taller doors through the studio, and a 384 double
door is the size those gates and the temple's interior both read at. 384 × 384 keeps the wing picture at its native
1:2 (no stretching, which `door_check` would otherwise have to judge by eye).

**WHO ACTS.** Outdoor agent: X2's `gen.py` (the temple), every other outdoor generator for the sites rule 2 lists
(found with the new check, `door_check.py --list`), and the check in `tools/xeen/door_check.py`; a tour capture of
the temple front at the pin's pose and from inside XD-06's porch. Dungeon agent only if rule (a) finds an outdoor wall
too low for its BLV's exit.

**REVERSIBLE.** Yes, a `door_height` and a bay per building. Confidence 70 % (the 384 against 448 is taste; 384 keeps
the picture true).

**SUMMARY ROW**

| D-180 | 2026-11-26 | X2 p14: the Temple of Yak's door; doors on big buildings (decider) | Temple of Yak: double door, bay 384 (two 192 leaves of `xvtdoorw`), `door_height` 384 (was 128 × 256; XD-06's inside exit is 224 × 448). Rule, every outdoor map: (a) a building door into a BLV is at least as wide as the BLV's inside exit and within 64 of its height; (b) temples, castles, keeps, gatehouses, guild halls, towers, or walls ≥ 640 with a front ≥ 1,024: kit wing pair, bay 384, height 384 (448 for walls ≥ 896 or (a)); town houses keep 128 × 256 (MM6–MM8's leaf; their big buildings pair it). `door_check.py` `doors.small_for_building`, `doors.inside_mismatch`. 70 % | outdoor; tools |

---

## D-181: the "Statue" in XD-06's chapels is MM6's fountain (XD-06 p1, F74)

**What is there.** `xd06/gen.py` 496–497: `deco:chapel_w_statue` and `deco:chapel_e_statue` are decoration `sta1a`
on each chapel's side altar (a platform 512 × 128, rise 96, against the south wall), the pin's [1741, 4279] looking
south at the east one. `sta1a` is row 153 of `engine/data_tables/decoration_data.txt`, hint **"Statue"**, but its
sprite is MM6's New Sorpigal fountain (`fount1`–`fount3`), and its 3D model is `engine/models/mm6_deco_fountain.glb`
(`engine/models/indoor_decorations.yml` and `decorations.yml`, height 266): an urn under a canopy with sixteen falling
streams. Revision 3 of that model (`level_generation/decorations/mm6_new_sorpigal_3d/props/README.md`, "Fountain
water") deliberately has **no basin**: it stands in New Sorpigal's octagonal BModel pool, and the streams end just
under its base to meet that water. Its streams fan out to about 93 units round it, wider than the 128-deep altar.

**Other uses in Xeen** (all generators grepped): FD-04 1 (`fd04/gen.py` 823, `deco:fountain` in `room:fountain`, the
source's "Ahh, refreshing!" fountain, aazex123:4-5), X8 2 (`x8/gen_objects.py` 118–119, the offering statues) and X9 6
(`x9/gen_objects.py` 135, the offering statues); 11 in all. None stands in water. The name "Statue" misled every
generator that picked it; only FD-04 means a fountain.

**DECISION.**
1. **XD-06's two chapel statues become a dry statue:** `7dec55` (MM7's statue, indoor model
   `mm7_deco_7dec55.glb`, 171 high) on the same altars, facing the nave as now. A chapel's side altar holds a statue;
   a fountain pouring onto a brick altar in a dry chapel is the fault, not the missing basin.
2. **X8's 2 and X9's 6 offering statues** take the same `7dec55` (X9's other statues are `7dec54`, so the offerings
   still read apart). Their `Offering` events keep their source ids (`deco:offering_<k>`).
3. **FD-04's fountain gets its basin:** an octagonal kerb about 384 across (inner about 320), 64 high, a water floor
   16 under its top as one of the world's indoor water faces (D-22's liquids, `kind: water`), and `sta1a` standing on
   the basin floor with its base at the water line (the model's streams end 0.027 m under its base). The click stays.
4. **The rule:** `sta1a` (and any other fountain decoration whose model has no basin) is placed only standing in water;
   a "statue" is a statue. The check: `tools/xeen/check_props_support.py` (or a sibling) fails a `sta1a` whose base is
   not within 32 of a water or liquid surface, on every Xeen map.

**WHY.** The piece is a fountain built to stand in a pool, and the user's own review (revision 3) removed its basin
for that reason; giving it a basin again would undo that on MM6's New Sorpigal. Ten of the eleven Xeen sites wanted a
statue and took this one by its hint. A basin on XD-06's 128-deep altar does not fit the spray, and a temple of Yak
has no reason for a fountain in a side chapel. The one real fountain (FD-04) gets the pool it needs.

**WHO ACTS.** Dungeon agent: XD-06 (`gen.py` 496–497), X8 and X9 (`gen_objects.py`), FD-04 (the basin in `gen.py`),
rebuilds and a capture of each changed site; the check in `tools/xeen/`.

**REVERSIBLE.** Yes: a decoration name per site, and a platform on FD-04. Confidence 75 % (the player asked for the
fountain; a dry statue is the cheaper and more fitting reading of a chapel altar).

**SUMMARY ROW**

| D-181 | 2026-11-26 | XD-06 p1: the chapel "Statue" is MM6's basin-less fountain (decider) | `sta1a` (row 153, hint "Statue", model `mm6_deco_fountain.glb`, made to stand in New Sorpigal's pool) is on 11 Xeen sites, none in water. XD-06's 2 chapel altars and the offering statues of X8 (2) and X9 (6) become `7dec55` (a dry statue); FD-04's real fountain gets an octagonal basin (~384, kerb 64, indoor water 16 under it) with `sta1a` at the water line. Rule: a basin-less fountain stands only in water; a check fails `sta1a` more than 32 from a water surface. 75 % | dungeon; tools |

---

## D-182: loot from elementals, sprites and bosses (XD-19 p1; X2 p7 of 2026-11-23; F77)

**What is there.**
- `worlds/xeen/data_tables/monster_data.txt` gives every one of these rows table loot by the world's formula
  (`tools/xeen/gen_monsters.py` `treasure()`: gold per 1,000 XP and items per million XP by level, bosses ×3 gold, a
  100 % item one treasure level up): Fire Elemental 11621 `23%101D10+L5`, Fire Blower 11622 `29%126D10+L5`, Medusa
  Sprite `5%9D4+L1`, Sprite Queen `8%10D8+L2`, Sharla (the sprites' boss) `54D10+L4`.
- **The sprites are fixed already.** F54 (2026-11-24, `PLAYER_FEEDBACK_20261124.md`): they wore the Will o' Wisp's
  descriptor, whose dead sprite is `null`, so the game left no corpse and dropped none of their loot. `monsters.yml`
  now says `corpse: dying` on the sprites and dark sprites (`monster_descriptors.txt` 11530–11538: dead sprite
  `m529d`), checked by `tests/scenarios/xeen/sprites_leave_loot.yml`. X2 p7 was made on 2026-11-23, before it; the
  "bosses" in its log are Sprite Queens (tier C, not boss rows; the "P.S." prefix reads like a MAW affix).
- **The elementals are not.** F54 set `corpse: none` on the fire elementals (11620–11624), the air elementals
  (11700–11702) and the robots (11610–11612): their descriptors have no dead sprite (`null`), so they vanish and,
  by the engine's rule (`OutdoorWorldRuntime`/`IndoorWorldRuntime` `actorShouldLeaveCorpse`; Standard
  `MonsterRules::lootWithoutCorpse` returns nothing), drop nothing. The note in `monsters.yml` says so: "their table
  loot is lost". The water and earth elementals have bodies and drop.
- **How much is lost:** placed on Xeen's installed maps, 136 robots, 47 fire and 34 air elementals: about **93,000
  gold and 47 treasure-5/6 items** at the table's averages (887k kill XP of Acts V–VI). The economy was built with
  that gold in it (the curves apply to every row).
- **MM6–MM8** (`engine/data_tables/monster_data.txt`, `monster_descriptors.txt`): MM6's fire, water and earth
  elementals keep a body and drop `10D30`–`10D40` gold and 10–20 % items; its air elementals vanish with their table
  loot unused. MM7 gives its fire, water, air and light elementals no treasure at all (earth: gems); MM8's air, fire
  and water elementals vanish with no treasure (earth: `30D20`). So MM never pays for a monster that vanishes, but MM6
  pays its bodied elementals well.
- The 3D models fit a body: `xeen_fie1` and `xeen_aie1` play `Death` then a `Dead` clip that holds everything hidden
  (`mm6_fie1_claude/README.md`: "the native corpse is empty"); a slain creature's place is then taken by its loot
  satchel (`WorldFxSystem` "Loot satchels", none for an empty corpse).

**DECISION.**
1. **Every hostile Xeen row with table loot leaves a body and drops it.** The fire elementals (11620–11623, and 11624),
   the air elementals (11700–11702) and the robots (11610–11612) go from `corpse: none` to `corpse: dying`, as the
   sprites did in F54: the death clip (or the robots' explosion) plays, the body is hidden, and the satchel with the
   table's gold and item appears where it came to rest. No change to their treasure, no engine change, no change to
   MM6–MM8 (only the Xeen descriptor rows change).
2. **Sprites:** nothing more; F54 stands. The outdoor agent resolves X2 p7 with `sprites_leave_loot.yml`'s pass and an
   after picture.
3. **Bosses** keep the boss curve (gold ×3, a 100 % item one treasure level up); `boss_loot: false` stays only where a
   decision set it (Darzog's Clone). A boss must leave a body.
4. **The check that keeps it:** `gen_monsters.py` refuses `corpse: none` on a row whose treasure is not `0` ("loot is
   never silently lost": such a row says `corpse: dying`, or its family sets the treasure to nothing on purpose with a
   note). A scenario as `sprites_leave_loot.yml` kills a Fire Elemental (XD-19 or D6), an Air Elemental (P2) and a
   Patrol (D6) and finds a satchel with gold for each, Standard and MAW.

**WHY.** The world's own economy counted this loot; dropping 93k gold and about 47 high items from Acts V–VI was a side
effect of following MM's "vanish" convention, not a choice, and the player has now hit it twice. The satchel already
stands in for every body in OpenYAMM, so a hidden body with a satchel looks the same as a vanishing elemental that
leaves its treasure. It is one field on three families, cheap to undo.

**WHO ACTS.** Engine and data agent (A2's data: `source/monsters.yml` three families, `gen_monsters.py`'s refusal,
`build_world.py --only gen_monsters`, the scenario, a capture of a slain fire elemental's satchel indoors and an air
elemental's outdoors); outdoor agent resolves X2 p7.

**REVERSIBLE.** Yes, three `corpse:` lines. Confidence 75 %.

**SUMMARY ROW**

| D-182 | 2026-11-26 | Elemental, sprite and boss loot (XD-19 p1, X2 p7) (decider) | Sprites fixed by F54 (`corpse: dying`, `sprites_leave_loot.yml`); X2 p7 resolved with it. Fire (11620–11624) and air (11700–11702) elementals and robots (11610–11612) go `corpse: none` → `corpse: dying` (death clip, hidden body, satchel with the table loot): ~93k gold and ~47 L5/L6 items the curves already budgeted. Bosses keep the boss curve. `gen_monsters.py` refuses `corpse: none` with nonzero treasure; scenario kills a fire, an air elemental and a Patrol and finds gold. 75 % | engine/data (A2); outdoor (X2 p7) |

---

## D-183: X7's south orcs, more of them and in bigger groups (X7 p1, F77)

**What is there.** The "goblins" are X7's south orcs (the Xeen orc family wears MM7's goblin body, `xeen_m246.glb`).
`source/map_rows.yml` X7: orcs `tier: 1, count: [1, 2]`, weight 21, `act_rows: {I: [11030, 11031, 11032]}` (D-40: met
by an Act I party from X1's road). The installed scene has **13** slot-1 markers (F10, 2026-11-21, in six areas: west
slopes 4, red river 3, east range 3, gap south 1, south hills 1, pony ridge 1), the nearest 2,044 from the pin;
plus 2 placed Orcs at the outpost (`places.py` 584). F10 cut the groups from 2–3 on 8 markers to 1–2 on 13 to fill
the empty south (`tools/xeen/empty_zones.py`) at the same orc count, because Act I had no room.

`tools/xeen/balance.py --detail`, run 2026-11-26 on the installed maps: X7's Act I share is Orc 19.6, Orc Archer 1.6,
Orc Guard 0.4 (21.6 kills, 433 kill XP per member, about 20 per orc); **Act I is 9.6k of 8.5k, 1.13** (it was 1.147
when F10 was made; X1's skeleton fix, F38, took it down). Room to the 1.15 mark: about 170 per member, about 8 more
orcs. Every other orc, goblin and gremlin slot in Xeen is `[2, 3]` (X1, D1, XD-04, XD-05, DD-01, DD-04, DD-09); MAPS
§0 writes X1's orcs as 3–5. MM6–MM8 put their goblins in 3–5 (New Sorpigal `BGoblin`) and 2–5 (Harmondale, `7out02`); 1–3,
MM's commonest slot size, is for beasts and loners there.

**DECISION.**
1. **X7's south orcs: `count: [3, 4]` on 8 markers** (no group under 3). One or more in each of F10's six areas:
   west slopes 2, red river 2, east range 1, gap south 1, south hills 1, pony ridge 1; the outdoor agent picks which
   five of the 13 go so that `empty_zones.py --check` still passes on X7 (the two decided quiet places unchanged).
   Expected 28 orcs from markers + the 2 placed = 30 (was 21.6), Act I about 1.149.
2. **Budget guard:** `balance.py` after the change must read Act I ≤ 1.15. If it does not, 7 markers (24.5 orcs, about
   1.14). If 8 markers leave an empty zone, the remaining markers move (never a 9th) before any group shrinks.
3. **The rule for other maps:** the tribe families (goblins, orcs, orc warband, gremlins) never come in slots under
   2; a map short of kill-XP room spreads fewer, larger groups (and moves markers to cover its land), it does not
   halve their groups (F10's method is retired for them). No other map changes now: every other tribe slot is already
   2–3. The other outdoor slots that start at 1 (X5's wolves, barbarians and trolls 1–3, X7's hydras and dragons, the
   birds, eyes, golems, harpies and robots of X8, X9, D4–D7) stay: 1–3 is MM6–MM8's commonest outdoor slot size (map_stats,
   the shipped ODMs). `balance.py` warns on a tribe slot whose count starts at 1.
4. Not done: more orcs past the budget, or moving the west slopes (reached from X4) into Act II's count. Act II has
   room (1.09), but D-40 counted the whole south in Act I and nothing in this pin asks for a re-count; it is the
   fallback if a player asks for still more.

**WHY.** The player's two asks are met: about 40 % more orcs and every group of 3–4, the size MM6–MM8 and Xeen's
other orc and goblin slots use. Act I can take it now that F38 freed room. Fewer, larger groups keep the empty-zone
fix if the markers stay one or more per area.

**WHO ACTS.** Outdoor agent (X7: `source/map_rows.yml`'s orc count through A2's `build_world.py --only gen_maps`,
`gen_l1.py` AREAS / `places.SOUTH_MARKERS` 8, rebuild, `empty_zones.py --check`, `balance.py`, D-85/D-87/D-138/
D-142/D-157 checks, hostility and walk, bake, a capture at the pin's pose). A2 adds the slot warning.

**REVERSIBLE.** Yes, a count and a marker number. Confidence 75 %.

**SUMMARY ROW**

| D-183 | 2026-11-26 | X7 p1: more orcs ("goblins"), groups over 2 (decider) | X7's south orcs `count: [1, 2]` → `[3, 4]`, markers 13 → 8 (one or more in each of F10's six areas, `empty_zones.py --check` still passing): ~28 + 2 placed = 30 orcs (was 21.6); Act I 1.13 → ~1.149 (balance.py 2026-11-26; F38 freed the room); over 1.15 → 7 markers; an empty zone → move markers, never shrink groups. Rule: goblin/orc/gremlin slots never start below 2 (all others already 2–3; other 1–3 slots stay, MM's commonest); short budgets use fewer, larger groups; `balance.py` warns. West slopes into Act II only if more is asked. 75 % | outdoor (X7); A2 (count, warning) |

---

## D-184: snow, not rain, on Winterkill Tundra (X5 p14, F77)

**What is there.**
- X5 means snow: `x5/gen.py` 557 `rules: {weather: snow}`, its atmosphere `weather: {snow: true}`, MAPS's X5 "snow",
  `source/map_rows.yml` X5 `bolster: {snow: true}`, so `worlds/xeen/data_tables/bolster_maps.txt` row 9103 has Snow
  `x`. Its land is snowfields, frozen lakes (D-6.3's ice) and a snowy forest.
- But the engine's Rain column means "rain **unless** `-`" (`game/tables/MergedBaseTables.cpp` 2141:
  `entry.rain = !isDisabledCell(row[10])`), and the generator writes `x` or an empty cell
  (`tools/xeen/gen_maps.py` 144), never `-`. So every Xeen map with weather rolls rain, X5 included: snow is rolled
  first (15 % a day × the month multiplier, 0 in June–August), and a day without snow rolls rain at 20 %
  (`engine/rendering/weather/weather.yml`). In summer X5 can only rain.
- MM6–MM8: their snow maps (Kriegspire, Harmondale, Erathia, Mount Nighon, the Land of the Giants) also rain on
  snowless days; Kriegspire's snowfields get `snow: 30` in `weather.yml`. Their deserts have no weather at all
  (`bolster_maps.txt` Weather `-` on Ironsand Desert, the Bracada Desert and Dragonsand; Rain `-` on the first two). A world may add its own
  `worlds/<id>/rendering/weather/weather.yml` with `maps` entries (`GameDataLoader.cpp` 6034).
- D-116 (weather never greys the void) is not touched.

**DECISION.**
1. **A map whose walked land is snow and ice snows and never rains.** On Xeen that is X5 alone (D4 and D5 have snow
   only on high ground, their land is lake, forest and sand; they keep their weather). X5: `bolster: {snow: true,
   rain: false}`, and a new world file `assets_dev/worlds/xeen/rendering/weather/weather.yml` with
   `maps: {xeen_x5.odm: {snow: 30}}` (Kriegspire's snowfields). Summer days on X5 are then dry and cold (the month
   multiplier), not wet.
2. **The generator bug:** `gen_maps.py` writes `-` in the Rain column for `rain: false` and leaves it empty otherwise
   (rain allowed, MMerge's default; the shipped rows use the same `-`); `rain: true` (X2) changes nothing and may stay
   as a record.
3. **The deserts, same family:** X6 Desert of the Sphinx and D5 Desert of Doom also get `rain: false` (MM6–MM8's
   deserts never rain); they keep their weather row (sky ladder, wind).
4. **The check:** `build_world.py --check` (or `gen_maps.py`) fails an outdoor row with `snow: true` that is not
   `rain: false`, and lists every outdoor map's rain/snow pair in its report.

**WHY.** Rain falling on deep snow reads wrong to any player, and Xeen's X5 was always meant to snow; the rain came
from a generator that could not say "no rain". MM's own snow maps rain in summer, but they are mixed lands
(Harmondale is mostly grass); Winterkill is all snow. Keeping it chance-based (not `always: snow`) keeps clear days
and the view distance, and it is two data lines to reverse.

**WHO ACTS.** Engine and data agent (A2): `source/map_rows.yml` X5, X6, D5; `gen_maps.py`'s Rain cell and check; the
world weather file; `build_world.py --only gen_maps`; a capture on X5 with `weather snow` and a check that `weather
rain` is refused there (or a forecast over a year of days showing no rain on X5, X6 or D5).

**REVERSIBLE.** Yes, data only. Confidence 80 % (X5); 65 % for the deserts' part.

**SUMMARY ROW**

| D-184 | 2026-11-26 | X5 p14: rain on the snowfields (decider) | A snow-and-ice map snows and never rains: X5 `bolster: {snow: true, rain: false}` and a Xeen `rendering/weather/weather.yml` `xeen_x5.odm: {snow: 30}` (Kriegspire's); summer dry. Cause: the engine's Rain column is "rain unless `-`" and `gen_maps.py` never writes `-`, so every Xeen weather map rains. `gen_maps.py` writes `-` for `rain: false`; deserts X6 and D5 `rain: false` too (MM's deserts have no rain); `--check` fails `snow: true` without `rain: false`. D4, D5's high snow keep their weather. 80 % | engine/data (A2) |
