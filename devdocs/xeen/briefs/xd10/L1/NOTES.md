# XD-10 Cave of Illusion: notes (state at the hand-over, 2026-11-20)

A new M dungeon (no original), story step **M12** (the Enchanted Key from the great skull), built with the Map Studio
from its graph (`devdocs/xeen/mockups/act2_graphs/xd10.graph.yml`) and decider D-4
(`devdocs/xeen/mockups/act2_dungeon_decisions.md`, which wins) by lane A8's sub-agent `agent:xeen-a8-xd10`. Key
`xd10`, project `xeen_xd10`, stem `xeen_xd10.blv`, map_stats 9126, world `xeen`.

## State

Stopped at a clean checkpoint on the orchestrator's hand-over request: **L1 only**.

- `L1/` (`plan.yml`, `project.yml`, `diagram.txt`): `oymap validate --assets assets_dev` **no issues**, `fmt --check`
  clean, recorded as `agent:xeen-a8-xd10`. Written by `output/studio_cal/xd10/tools/gen.py L1` (the generator is the
  source; extend it for L2-L4, as XD-11's `tools/gen.py`, `geo.py`, `dress.py`).
- Nothing built, installed or played. No textures generated. `assets_dev` untouched.

## What L1 says (the design, decided)

- **Rooms (23 spaces)**: the graph's 20 plus three connectors for its stair links (`ice_stair` 0 to -640,
  `steps` -640 to -1280, `wreck_stair` -640 to -1280). Floors 0 (upper caves), -640 (drowned galleries), -1280
  (reservoir bed).
- **Exits: not sealed.** X5 is installed (A6). `exit:x5_north` arrives on X5 at (16640, 9987, 1408) facing south,
  `exit:x5_south` at (6915, -9472, 1216) facing west (the orchestrator's coordinates; studio directions 270 and 180).
  Both mouths ask "Leave the Cave of Illusion?" (aaze0042:49). The map's start is the north mouth (D-4 item 5).
- **Monsters, all placed (exact counts)**: 30 Flying Feet 11600, 12 Guardians 11601, 8 Water Golems 11591 = 50,
  kill XP 33,424 for the party, **8.36k per member** (MAPS 8.1k, +3 %). By room: north mouth 2 FF, icicle hall 4 FF,
  phantom safe 2 FF, Hall of Mirages 3 FF + 2 G, frost cavern 2 FF + 2 G, south mouth 2 FF, sluice 3 G; drowned
  gallery 3 WG, mirror maze 4 FF + 1 G, guardian post 4 G, echo cave 2 FF; sump 2 WG + 1 FF, sunken boat 2 FF,
  reservoir 2 WG + 4 FF (placed **hidden** under the water, shown by a `show_actors` effect when the party first
  steps onto the drained bed: they are neither stuck nor moved by the water mover), phantom vault 1 WG + 2 FF.
- **Chests (5)**: behind the mirage (T3 + Might Boost 240: the game gives a placed potion power 5-19, so +15 to +57
  Might, enough to lift Might 20 to 30), guardian post (T3), sunken boat's strongbox (T3), echo cave (15 fixed gems of
  `Xeen.GemItems`, e.g. 177-186), phantom vault (the hoard).
- **Doors (8)**: four mirages, three stone sluice gates, the sluice's door.

## Mechanisms, as they will be built (L4)

- **Mirages** (D-4 item 1): door leaves (`slide_down`, speed about 4000: open at once) whose surface is the cave rock
  `t68a02b` with `liquid: liquid`: the studio says the game draws a non-liquid picture with the fluid bit "rippling
  and swirling slowly", so the mirage is the cave wall wavering like heat haze, **no new texture** (check in the game;
  if it does not ripple on a wall, one Codex shimmer texture). A click, or a step on a floor plate before the wall
  (the studio has no touch trigger: the fallback), runs "The mirage dissipates with your touch." and opens it, once
  (a map variable per mirage). The phantom safe: a block of `xnrustirn` iron with the same rippling flag, hover name
  "Safe", clicked: "Your hand passes through the safe as though it were not there."; it stands beside the mirage, not
  in front of it.
- **The plug** (D-4 item 3): a bronze (`xngong`) block in a pool of the sluice chamber, its chain (`xnrustirn`) a part
  of the same mover rising into the ceiling. Clicked: condition `stat: {name: ActualMight, at_least: 30}`
  (`ActualMight` reads `resolveCharacterDisplayedActualPrimaryStat`: base, items and the magical bonus, so a potion's
  temporary Might counts; to be confirmed in the playtest), else "You aren't strong enough to pull the plug.";
  once pulled it sets qbit `plug_pulled` 110640, raises the plug, sinks the water and opens the three gates; a later
  click says the plug hangs free (no silent click). A `load` event reopens the water and gates when the qbit is set
  (a refill would otherwise leave the water up for good).
- **Draining** (D-4 item 2): the reservoir is a tall cavern (floor -1280, roof about +700) seen through a railed
  opening from the ledge (-640, sill 128) and a railed window from the sluice (0). The water is **one mover** filling
  the reservoir's outline from the bed to -660, `travel: [0, 0, -640]`, speed about 107 (6 s), sinking 20 under the
  bed. A1 has not answered (A1.md lists it as an open D-4 item): **check it first in L4** (pictures from the ledge at
  the start, mid-travel and the end, by `event <id>` in a startup console file plus a screenshot tour; and a scenario
  step standing the party on the drained bed). If it draws or collides wrongly, D-4's fallback: the same block as a
  platform hidden and made passable by the plug's event behind a fade ("The water roars away down the sump.").
- **Skulls** (D-4 item 4): `7dec20` skull decorations on rock shelves, hover names "Skull (Luck)" and so on. Each a
  `script` event in Lua: `XeenQuests.hook("m12.skull_sold")` when the member's bit is set, `m12.skull_poor` without
  the gems, else the offer hook (`m12.skull_upper` / `m12.skull_deep`) followed by `evt.AskQuestion(eventId, ...)`
  Yes/No; on Yes `Xeen.payGems(n)`, `AddValue(Base<Stat>, n)`, `SetPlayerBit`. Upper: Luck 11236, Personality 11237,
  +2 for 3 gems; deep: Intellect 11238, Speed 11239, +3 for 5 gems. The great skull: before the key
  `XeenQuests.hook("m12.skull")` (the key 12306, qbit 111240, 1,500 XP, its own fail and else texts); after it,
  `m12.skull_grotto` then **a plain question of three buttons** (`AskChoiceWithAnswerSteps`: Might, Endurance,
  Accuracy), +5 Base stat for 10 gems, bit 11240 once per character across the three.
- **Gems before the great skull** (D-1.6): the echo cave's 15 lie on the way (ledge, maze, post, echo) before the
  steps open; a notice on the ledge says plainly that the skulls take gems and the echo cave past the Guardians' post
  keeps some; the arrival message says why the party came (Artemus: a talking skull deep in this cave sells the key to
  the Tower of High Magic, for gems).

## Textures (chosen, nothing new planned)

One family everywhere: **MM8 Passage Under Regna `d33.blv`** (a wet passage under the sea): rock walls and roofs
`t68a02b` (256), granite floors `t68a03b` (upper) and `t68a03a` (lower), the sluice's bricks `t09a01`, flags
`t09a02b`, trim `t09b11b`, door `t09a03c`, timber `t06a10` and `t09a05b` (the boat). Water `wtrtyl` (MM8, flowing).
Ice and snow where d33 has none: `orair32` (MM6 Icewind Keep ice) on the icicles at the mouths and in the icicle hall,
`snow` (MM8) on the mouths' floors (in no shipped dungeon: snow blown in at the lip). The world's `xngong` (bronze,
XD-03) for the plug, `xnrustirn` (iron, XD-02) for the chain and the safe, `xnnotice` for the ledge's notice. About 17
distinct of 45, 0 new. MM8 Dragon Cave `d17` (same rock) was not taken: A6 gave it to XD-18.

## Map_stats for A2 (`source/map_rows.yml`, row 9126)

lock 5, trap 3, perception 5, music 2, environment `cave`, refill 672, bolster LowerToEqual, encounter 10, treasure 3;
slots: `{family: magic_constructs, tier: 0 (a), count: [2, 3], weight: 75}`, `{family: elemental_golems, tier: 1
(b), count: [2, 3], weight: 25}`. Every monster is placed with its row, so the slots only serve the map card.
Until A2 writes the row the game will not load the map from assets_dev: make a test mount
`output/studio_cal/xd10/mount` as XD-11's (`output/studio_cal/xd11/mount`, `four.sh`).

## Ids

Map qbits: `plug_pulled` 110640 (of 110640-110679). Player bits 11236-11240 (registered by A3 in m12.yml). Items:
Enchanted Key 12306 (hook), Might Boost 240, gems 177-186.

## Next steps, in order

1. **L2**: positions and extents for every space (the layout worked out in this session, `tools/gen.py` to carry it;
   upper column at x -1500..1500, y 200..10100 with the phantom safe, cache and skull alcoves west and the sluice
   east at x 1328..4000; ledge x 3300..4000 y 3700..6300 at -640; reservoir x 3300..7500 y 900..6300 at -1280, roof
   +700, its west wall x 4128 facing the ledge and the sluice; drowned gallery x 1700..3172 y 3628..4800; steps and
   gallery stair under the sluice; sump, wreck south; grotto and vault east; maze, post, echo cave, deep skulls north
   at -640). Walls 128 thick (gaps between outlines), connecting walls axis-aligned (XD-11's `shared()`), caves as
   12-sided outlines with `rough`, roofs by `ceiling_points`, stalactites in the wide caves.
2. **L3**: `rooms.yml`; build, render, `audit --reach`, `scale_bands.py` after every few rooms.
3. **L4 early: the water-mover check** above (A1 wants the answer); then objects, wiring, atmosphere.
4. Test mount for row 9126; `playtest.yml` (start to the key through every mechanism, Might refused then a potion,
   the skulls once per character, the drain seen and the bed walked), `playtest_hostility.yml` (as XD-11's), and
   **one exit playtest per mouth** (take OK, assert `map: xeen_x5.odm` and the party within 128 of the arrival, as
   XD-06's `playtest_exit.yml`), plus a way-in test from X5 if X5's doors lead into XD-10 (XD-06's `playtest_in.yml`);
   each 4 of 4.
5. Install with `oymap install <L4> --build output/studio_cal/xd10/build --root assets_dev`, `oymap audit --world
   xeen` (D-7 dressing), `check_dressing.py`, tours of every room and every mechanism before and after, NOTES.md in L4.
