# DD-19 Wizard Quarter, L4: notes

New M dungeon behind Sandcaster's guild gate (D3; the source's wizard corner of dark maze0031), side quest Q-D14
(Astra), Promo Spy, built with the Map Studio from `devdocs/xeen/mockups/act4_graphs/dd19.graph.yml` and decider D-42
(`mockups/act4_a8_decisions.md`, which wins) by `agent:xeen-a8-dd19` (lane A8 session 9), 2026-11-21. Key `dd19`,
project `xeen_dd19`, stem `xeen_dd19.blv`, map_stats 9172, world `xeen`, music 34.

## State and next steps

**Reached:** L1-L4 written by the generator, `oymap validate` no issues, build 0 warnings (no "two sizes for one
texture"), installed into the scratch root `output/studio_cal/dd19/root` only, recorded (`agent:xeen-a8-dd19`).
Audit (`output/studio_cal/dd19/audit.txt`, `--reach --solve`): **0 errors, 0 warnings** (fit, doors, lights,
dressing), one info (`door.unused`: the mirage, never moved: it is made passable). `oymap solve` (`solve.txt`): 25 of
25 sectors in two steps, never reached 0, the exit to D3 listed. The root's `worlds/xeen/data_tables/` is a real copy,
re-copied from assets_dev in session 9 (A2 had changed rows); stale hard links refreshed then (`relations.yml`,
`events/common/xeen_quests.lua`, `events/common/xeen_common.lua`, `models/actors.yml`, `audio/sounds.txt`).

**Playtests:** `playtest` (218 steps, 246 checks), `playtest_hostility` (56) and `playtest_exit` (37) **4 of 4 each**
from the root (`output/studio_cal/dd19/run/four_013206`, summary `output/studio_cal/dd19/four_s9.txt`). **Ready to
install.**

**Next (the lane lead):** `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd19`, then
`flock output/studio_cal/a8_s5/lights/post.lock output/studio_cal/a8_s5/lights/post.sh dd19` (bake with post.sh's
template profile, stale check, `four.sh` from assets_dev), or the tests alone:
`ASSETS=$PWD/assets_dev output/studio_cal/dd19/four.sh`. Baked pictures: `output/studio_cal/dd19/shoot.sh things2`
with `ASSETS=$PWD/assets_dev` (the tour `output/studio_cal/dd19/shots/things2.yml`). A5: D3's guild gate (see
"Arrivals and exits").

**Resume:** `RECORD=1 LABEL="..." output/studio_cal/dd19/cycle.sh` (regenerates L4 from `tools/gen.py`, fmt,
validate, build, install into the root, audit, record; `LEVELS="L1 L2 L3 L4"` for all). Diff the L4 against
`.oymap/last` first if anyone edited it by hand.

**Scratch** `output/studio_cal/dd19/`: `tools/gen.py` (plan, project, diagram), `tools/geo.py` (rooms, openings,
themes, furniture), `tools/dress.py` (objects, wiring, atmosphere), `tools/tour.py rooms|things <name>` +
`tools/sheet.py` (tours, JPEG sheets), `tools/texsheet.py`, `texsize.sh`, `cycle.sh`, `four.sh` (`ASSETS=`, `N=`,
`TESTS=`), `shoot.sh <tour>`, `run/` (logs), `shots/` (sheets), `dbg/` (the debug scenarios of the session).
**Every project file of L1-L4 except the playtests and these notes is written by the generator.**

## What was built

Three levels in one frame (x east, y north, z up): the undercroft -512, the court level 0, the upper floors 640.
The inside is larger than the outside (D-42's general rule).

- **The court (0, open sky):** `atmosphere.yml` `open_sky: {mode: open, preset: xeen_darkside_fading}`; its ceiling a
  sky face at 1536. 2,048 x 1,536 of pink ashlar (MM6 `hcwall`, once per 512) on marble flags (`t1f1`): the guild
  gate's inside face in the south wall (`hclgdr` once, 256 x 256, the exit preset) between two statue niches
  (`hcuniq2`, `hcuniq3`); the Mirage Guild's great-hall doors west and the Sorceress HQ's east, each two hinged leaves
  (MM8 `t07c03c|t07c03d`) with two windows (`hcwindo`) above; three arches north into the arcade under the covered
  bridge, whose three windows look down into the court. No monster (D-11.3).
- **The arcade and the Guild Common (0):** the covered walk under the bridge; the Common behind it (marble lozenges
  `t1f2`, cedar ceiling): a long table, the hearth with its fire, the font of spell points (a marble basin of
  shimmering `orair32`), Blastem's own table and chair with Blastem behind it; Weights and Measures east (scales,
  the tax chest); the quarters stair north.
- **The Mirage Guild (MM6 Icewind Keep 6d15, grey-blue brick `t3wspp`, beams):** the foyer (0) behind the double
  doors, the hall of illusions (benches, lectern, a painted door `d8dord`), the Mirage stair (0 to 640, its head the
  graph's stair head) up to the mirror gallery (640): a tall mirror (`xkmirror` in a wooden frame) on its west wall
  facing the mirage on its east wall (a leaf of the gallery's brick, passable at load), behind which the Hall of
  Mirages (640; red-corniced brick `t3wbltd`, a floor of `orair32` shimmering like water, a chandelier): Xenoc's dais
  and chair under the triple window (`hctriw`), the bolt by the bridge door; Xenoc's study south (desk, chest, the
  vault lever).
- **The covered bridge (640)** from the Hall of Mirages over the arcade to the scrying room; its west door bolted on
  Xenoc's side.
- **The Sorceress HQ (MM6 Corlagon's Estate 6d11, dark brick, rough flags, dark vaults):** the foyer (0), the HQ
  stair (0 to 640, its head before Morgana's ward), the scrying room (640: the crystal, three skull niches
  `d2skulas`, ward lamp 1, a brazier with a violet light), the robing room (0: robe racks, ward lamp 2 on an iron
  bracket, the back stair down), Morgana's sanctum (640: her dais, a chandelier) behind the ward (`xufield`, a
  see-through leaf that sinks), her wardrobe (racks, chest).
- **The undercroft (-512):** the potion alcoves (a two-storey stair room, -512 to 0, entered at its head from the
  Mirage stair; two shelves), the wizards' quarters (five beds, the ambush chest), the vaulted undercroft (two rows
  of pillars) with the guild vault south of it behind an iron door (four Iron Golems, the hoard), the quarters stair's
  foot north, the sorceresses' quarters (three beds, chest), the alembic cellar (the still, a shelf of bottles, a
  niche of bones `d2niche1`), the HQ back stair (-512 to 0) up to the robing room.

## Measurements

`oymap metrics` (`output/studio_cal/dd19/metrics.json`): **25 sectors** (M 20-45), **50.2 M units² of floor** (M
30-90), 4 loops; **14 doors** (18 door records: two double doors as hinged pairs, eight single doors, the bolted
bridge door, the ward, the vault's iron door, the mirage; and two levers), 6 chests, 38 bound events, 50 placed
monsters + Blastem (his peaceful body and his hidden hostile swap, not counted). Textures
(`tools/xeen/texture_budget.py --root output/studio_cal/dd19/root --map DD-19`): **39 of 45, 0 new**.

| Who | Row | Level | XP | Where | Count |
|---|---|---|---|---|---|
| Wizard | 11190 | 36 | 1,656 | foyer 4, illusions 3, gallery 3, alcoves 2, quarters (hidden, the ambush) 4 | 16 |
| Sorcerer | 11191 | 45 | 2,475 | illusions 1, Xenoc's hall 2 (his group), undercroft 1 | 4 |
| Xenoc | 11196 | 60 | 4,200 | the Hall of Mirages (group 5, immobile) | 1 |
| Enchantress | 11181 | 40 | 2,000 | HQ foyer 3, scrying 3, robing 2, alembic 2 | 10 |
| Grand Sorceress | 11182 | 55 | 3,575 | Morgana's sanctum (her group) | 2 |
| Morgana | 11183 | 60 | 4,200 | her sanctum (group 6, immobile) | 1 |
| Carnage Hand | 11602 | 35 | 1,575 | gallery 2, bridge 2, HQ foyer 2, weights 2, undercroft 2, sorceresses' quarters 2 | 12 |
| Iron Golem | 11582 | 40 | 2,000 | the vault | 4 |
| Blastem (body) | 11191 | - | - | the Common, peaceful, immobile, group 21 (a Sorcerer stand-in) | not counted |
| Blastem (the lesson) | 11191 | 45 | 2,475 | the Common, hidden, group 20, shown hostile on blastem_angered | not counted |

**Kill XP:** 98,846 for the party, **24.71k per member** (MAPS 23.8k, +3.8 %, D-42's figure); with Blastem fought
+2,475 (25.33k).

## Mechanisms

- `evt:arrive` (timer, once): the first arrival's window "THE WIZARD QUARTER. ..." (`dd19_arrived_once` 117520,
  A3's).
- **The mirror and the mirage** (D-42, the graph): the mirror (`panel:mirror`, hover "Mirror") "In the mirror, the
  blank wall behind you has a door in it."; the wall opposite is `door:mirage`, a leaf of the gallery's brick (the
  hall's on its far side) made passable at every load (`evt:mirage_load`, DD-03's illusory wall). Blastem's humble
  answer points at the mirror too.
- **Xenoc** (actor 49, group 5 with his two Sorcerers, immobile before his chair): `evt:xenoc_dead` (timer) runs
  `q-d14.xenoc` at his death (xenoc_slain 113283, once).
- **The bridge door** (`door:bridge`, `evt:bridge_door`): until the bolt is drawn, from the bridge while Xenoc lives
  his voice "Begone, children, lest I blast you to ash and scatter you to the winds." (aaze0031:37, Wrathmont's line
  given to Xenoc), after his death "The door is bolted from the far side."; from his hall "The door is bolted. The bolt
  is on the wall beside it." **The bolt** (`switch:bolt`): opens it for good (`bolt_drawn`).
- **The vault lever** (`switch:vault_lever`, Xenoc's study): "Far below, iron grinds.", raises `door:vault`
  (`vault_open`); the iron door before: "An iron door with no handle on this side. The guild's seal is cut into it."
- **The ward** (`door:ward`, `evt:ward`, D-42 (6)): its click names both lamps, "A ward of light seals the door. The
  ward draws on two lamps, one above and one below."; with one lamp out "The ward thins, but holds.". **The lamps**
  (`evt:lamp_scry`, the scrying room's brazier; `evt:lamp_robe`, the robing room's bracket): the shipped typed
  question "A ward lamp. ..." / "Snuff it (Yes/No)?"; Yes puts out its light and flame and says "The ward thins, but
  holds." or, with the other out, "The ward flickers and goes out."; `evt:ward_down` (timer) sinks the ward once both
  are out (`ward_down`). Each lamp once; then "The lamp is out."
- **Morgana** (actor 30, group 6 with her two Grand Sorceresses, immobile before her dais): `evt:morgana_dead` runs
  `q-d14.morgana` (morgana_slain 113284, once).
- **Blastem** (D-42 (5)): his table (`platform:blastem_table`, hover "Blastem the Wizard") runs `evt.SpeakNPC(5248)`
  (A4's row, A3's topics "The lesson" and "Boots licked"); his body is a peaceful immobile Sorcerer (group 21). Once
  `blastem_angered` (113286) is set, `evt:blastem_swap` hides group 21, shows group 20 (Sorcerer 11191, hostile, in
  his place) and calls `q-d14.blastem`; `evt:blastem_load` repeats the swap on every load (Valio's pattern). After it
  the table says "Blastem's chair is empty."
- **The font** (`platform:font`, hover "Font"): every member's spell points refilled (`AddValue(SP, 2000)`, clamped
  to each member's maximum), "+2000 spell points." (aaze0031:61), repeatable (D-42 (7)).
- **The potions** (the alcoves' shelves, hover "Alcove"): `q-d14.orange_potion` and `q-d14.purple_potion`, A3's
  hooks deciding for the clicking member (player bits 11350, 11351).
- **The ambush** (`chest:quarters_w`, `evt:chest_quarters_w`, D-18): the first opening sets `ambushed`, shows group 7
  (four Wizards hidden in the cells), says "Ambush!" (aaze0031:56) and opens the chest; later openings open it.
- Things to read: a bed in each quarters ("Nothing here.", aaze0031:53), the painted door, the crystal, Xenoc's desk
  and chair, the scales, the still, the triple window. Nothing changes inside after `q-d14.done` (D-42 (8)).

## Dressing

Long table, hearth with its fire, font, Blastem's table and chair (the Common); scales (Weights and Measures);
benches and lectern (illusions); Xenoc's dais, chair, desk; the crystal and the lamp's brazier; robe racks (robing
room, wardrobe); Morgana's dais; beds (quarters); the still and a shelf (alembic); chandeliers in the Hall of Mirages,
the sanctum and the Common; sconces (`scon100`) above ground, torches (`torch02`) below, wall torches (`torch01`) in
the court. Audit: 0 dressing findings. **Dressing exceptions:** none.

## Texture fit exceptions

None (audit: 0 texture findings).

## Playtests

`output/studio_cal/dd19/four.sh` from the scratch root (`ASSETS=` for assets_dev), `--world xeen --map
xeen_dd19.blv`. Logs `output/studio_cal/dd19/run/four_*`.

| Test | Steps | What |
|---|---|---|
| `playtest.yml` | 218 | the arrival window; the bridge door while Xenoc lives (his voice); the Mirage Guild's double doors (both leaves), the painted door; up the Mirage stair; the mirror; through the mirage; Xenoc dies (q-d14.xenoc); the bridge door from his side, the bolt; Xenoc's study (chest, the vault lever); over the bridge; the ward names its lamps; lamp 1 (Yes: thins), the ward thins; down to the robing room, lamp 2 (Yes: goes out), the ward sinks; Morgana dies (q-d14.morgana); her wardrobe's chest; down to the court, the HQ's doors; the Common: the font twice (spell points refilled); Blastem: Boots licked (no anger), The lesson (blastem_angered), the swap, kept after a save and a load, his chair empty; Weights and Measures' chest; down the quarters stair; the vault (the hoard); the ambush (four shown, kept after a save and a load); the Orange Potion once for member 1 then "You have had your fill." (bit 11350), the Purple Potion for member 2 (bit 11351); up the alcoves' stair into the Mirage stair |
| `playtest_hostility.yml` | 56 checks | 16, 5, 1, 10, 2, 1, 12, 4 hostile at load (hidden ambush and Blastem's swap counted), none peaceful but Blastem's body; a Wizard, an Enchantress, a Carnage Hand, an Iron Golem, a Sorcerer and a Grand Sorceress side by side in the court do not take each other on; blastem_angered: the swap, kept after a save and a load |
| `playtest_exit.yml` | 37 checks | the gate's leave window, OK: D3 at entrance:dd19_gate, position and facing measured; back in by the gate's move (MoveToMap 0, 384, 0, 512): the arrival measured with its facing, no second window |

Learned: the scenario helper `open_door(event, door)` clears hostiles within 1,500 (2D, through floors) while the
door moves, and `clear_hostiles` reaches through floors too: near Xenoc (over the Mirage foyer) the playtest clicks the
double door and walks the foyer without clearing.

## Arrivals and exits

| Inside arrival | At (x, y, z), facing | Measured headless | From |
|---|---|---|---|
| `entrance:d3_guild_gate` (= start) | (0, 384, 0), north (512) | (0, 384, 0) facing 512 | D3's guild gate `thing:dd19_gate` (A5): `evt.MoveToMap(0, 384, 0, 512, 0, 0, 0, 0, "xeen_dd19.blv")` |

| This map's way out | To | Measured | Facing |
|---|---|---|---|
| The guild gate's inside face (exit preset, event 23) | D3 `entrance:dd19_gate` (-10752, 22016, 1728) | **(-10752, 22016, 1729)** | 512 (north, toward the gate: A5's installed value; D-42 (4) asks for (-10496, 22150, 1728) facing south 1536) |

**For A5:** D3's `door:dd19` is still `listed_only` with no arrival, and `thing:dd19_gate` still says "barred from the
far side": the gate's move should be `arrival: entrance:d3_guild_gate` (the point above). The return point
`entrance:dd19_gate` faces 512, toward the gate it came out of; D-42 (4) asks for about (-10496, 22150, 1728) facing
south (1536): A5's to change; the map reads it by name, so no DD-19 change is needed.

## Ids

- Map qbit: `dd19_arrived_once` 117520 (A3's; block 117520-117559). Read: xenoc_slain 113283, morgana_slain 113284
  (set by the hooks), blastem_angered 113286 (A3's topic). Player bits (A3's hooks): 11350, 11351.
- Map variables: `once.arrive` 0, `blastem_swapped` 1, `bolt_drawn` 2, `ambushed` 3, `lamp_robe` 4, `lamp_scry` 5,
  `once.morgana_dead` 6, `vault_open` 7, `ward_down` 8, `once.xenoc_dead` 9.
- Groups: 1 wizards, 2 sorceresses, 3 Carnage Hands, 4 golems, 5 Xenoc's three, 6 Morgana's three, 7 the ambush, 20
  Blastem's hostile swap, 21 Blastem's body.
- Slots for A2 (as row 9172, encounter 10): `{monster: Xeen Sorceress, tier: 0, per_marker: [2, 3], weight: 75}`,
  `{monster: Xeen Sorceress, tier: 1, per_marker: [1, 2], weight: 25}`.

## Words needed

1. A talking placed indoor monster (DD-09's, DD-14's): Blastem's table talks for him.

## DECIDE

1. **Rooms merged and moved:** the graph's mirage_landing and hq_landing are the two stair rooms' heads, its
   stair_foot the quarters stair's foot (25 sectors, M band); the Mirage Guild's way down is the potion alcoves' own
   stair (entered at its head from the Mirage stair); the arcade under the bridge is its own room (the bridge crosses
   the court's north end, over the arcade, so the court stays open sky); the sorceresses' quarters' door opens off
   the undercroft rather than the stair foot (the same loop).
2. **Mirror texture:** `xkmirror` (D-37 (2)'s silvered glass, A6's) instead of the brief's `glass2`, which reads as
   blue window glass (DD-03's finding). One word in `tools/geo.py` (`MIRROR`) to reverse.
3. **Blastem's body** is a peaceful immobile Sorcerer (11191) in group 21 until A2 gives him a row of his own (a
   peaceful figure is its own row, D-42's general rule): a one-line swap of the row in `tools/dress.py`.
4. **Xenoc and Morgana keep their places** (`immobile`, casting from their chair and dais): Xenoc otherwise walks
   through his own mirage into the gallery.
5. **The lamps** are one-way (snuffed once), not two-state: cheaper, and the ward never needs to rise again.
6. **Rest slots:** A2's row draws Dif 0 and 1 of the sorceresses, which favours the Sorceress 30 (under the band
   32-55); Dif 3-4 would favour the Enchantress 40 (D-42: in-band rows only). As DD-14's item 4.

## Open

- **A5:** D3's gate is still sealed and names no arrival (above).
- **A2:** a peaceful row for Blastem (his own faction, the wizards' look), to replace the Sorcerer stand-in.
- No bake in the root (the lane lead bakes after install).

## Pictures (looked at)

`output/studio_cal/dd19/shots/things2_1..5.jpg` (every interactive thing and set piece; the tour
`shots/things2.yml`), `rooms1_*.jpg` (every room from two corners, the stair rooms from their heads). Changed after
looking: the furniture's bright `bemtila` wood read as orange crates (now the Common's dark cedar `cedsqrdk`); the
chairs' backs stood 256 high (now 160); the crystal stand was a block (now a slim stand); the court's windows and
niches were smaller than the court's doubled brick (now 256 x 512, at the brick's scale); the lectern stood on the
line from the foyer into the hall of illusions (moved to a corner). Still plain: the rooms are boxes; the court's
walls are one brick from floor to sky; the bridge's windows show its cedar ceiling from below.

## Installed (session 9, lane lead)

- Installed 01:33 (`INSTALL=1 output/studio_cal/a8_s5/rebuild.sh dd19`, build `output/studio_cal/dd19/b_013329`: 25 rooms,
  1475 faces, 18 doors, 30 lights, 46 events, 6 chests). Audit of the L4 against assets_dev (`--reach --solve`,
  `output/studio_cal/a8_s9/audit/dd19.txt`): 0 errors, 0 warnings.
- Baked twice: post.sh's template profile blew the court's and the Common's pale sandstone yellow; lowered as DD-03's
  (`direct_scale` 1.6, `max_lighting` 1.25; before: `output/studio_cal/dd19/xeen_dd19_profile_before_s9.yml`), rebaked
  01:37, `stale_bakes` none. Tests from assets_dev 4 of 4 after the second bake: playtest 246, playtest_hostility 56,
  playtest_exit 37 checks (`output/studio_cal/dd19/run/four_013823`).
- Baked pictures `output/studio_cal/dd19/shots/baked_s9b/` (sheet `baked_s9b_check.jpg`; the first bake's sheets
  `baked_s9_a.jpg`, `baked_s9_b.jpg`): the court warm pink sandstone under the fading sky, statues in their niches, the
  great-hall doors; the HQ and undercroft dim grey and purple stone. Polish: the furniture reads as plain red slabs, and
  the court's upper recesses hold flat red panels.
- Open: D3's `door:dd19` sealed (A5: `arrival: entrance:d3_guild_gate`); the exit's facing on D3 (D-42 (4), A5);
  Blastem's own row (A2).

## Merge point 30 panels (A8 session 20, 2026-11-21)

The scrying room's third skull niche (east wall) stood wholly inside `open:scry_landing`'s doorway (y 1216-1472), so it
was never drawn; it moved from y 1408 to 1664 (`tools/geo.py`; before: `output/studio_cal/a8_s20/dd19_geo_before_s20.py`),
so the niches stand at 640 and 1024 south of the doorway and 1664 north of it. Rebuilt with oymap 09:24, installed and
baked; audit 0 / 0.

## Session 21 (A8): AU's sounds

The room-filling beds `sound:court` (the sky bed), `sound:hall`, `sound:sanctum` (the tower bed) take `pan: false` (D-48); the point sounds keep panning. Through the generator; installed 10:05, rebaked, tests 4 of 4 from assets_dev, audit 0 errors (lane log `A8.md`, "21st session").

## Session 26 (A8): merge point 40 rebuild

- No source change: the generator reproduces the L4 exactly; oymap 40 builds the .blv slightly differently (an exit
  face's UVs). Installed 00:24 (`output/studio_cal/a8_s26/run/dd19/c002433`), baked, tests 12 of 12 from assets_dev
  (playtest's step 40 already reads Xenoc's death from the status line, D-90). Audit 0 errors, 0 warnings;
  check_exits 0.

### Drop pockets

- `check_drops` reports the whole lower floor (-512: undercroft, both guild quarters, alembic cellar, vault, potion
  alcoves; doors 13, 19, 22) as a pocket. Not a trap: the three stair rooms' flights (quarters stair, alcoves, HQ back
  stair; steps of 32) stand over their rooms' continuous foot floor, so their treads share no edge with it and the
  check misses them. The playtest walks down the quarters stair and back up the alcoves' stair (-512 to 0).

## Session 29 (A8): D-89 identity (F12)

Review 2.2 ("a walled precinct of one pink brick; two rival guilds don't read") and 2.3 "Walls have structure".
`identity: {shape: hall, family: 6d11}` in project.yml (no BLV is assigned to DD-19 in `dungeon_families.yml`; the HQ
and undercroft, most of the map, are 6d11's: DECIDE). In the "D-89 identity" blocks of `tools/geo.py`, `tools/dress.py`
and `tools/gen.py` (before: `output/studio_cal/a8_s29/before/dd19/`; the generator reproduced the installed L4 first).

- **The court:** a grey base course (`cstr128`, 96), the pink ashlar (`hcwall`) to 992, a pink marble cornice
  (`t1trimb`, 992-1024) and the crenellated top storey (`hcw1ctr`) under the sky, where hcwall ran floor to sky. The
  bridge's three windows over the court are pointed arches in an ashlar reveal, and the bridge has its own theme
  under dark beams (`d2ceil1`): the court's "flat red recess panels" were the bridge's cedar ceiling seen through
  square holes.
- **Set piece, the Mirage Guild's hall** (`mirage_foyer`): bookcase walls north and south (`bookcas1`, floor to
  ceiling, `bands: false`), a magic circle in the floor (`td1`, 640, `fit`), and in its middle the guild's crystal
  (`crystl0`, pulsing) on a marble stand with a cold blue light.
- **Set piece, the Sorceress HQ's hall** (`hq_foyer`): two MM6 braziers hung on their chains (`brzier00`) in violet
  light (radius 1200), two stone ledges of skulls (`7dec20` x 6) on the north wall, two skull reliefs (`d2skulas`) on
  the south wall, purple-flamed torches (`torch05`; `torch06` is the green one).
- **Furniture polish:** the long table, Blastem's table, Xenoc's desk, the lectern and the scales' bench take 6d19's
  brass-edged `deskside` sides (were bare red cedar slabs); the scales' iron top tiles instead of one stretched
  picture (its old build warning gone).
- Textures 42/45, 0/8 new (+5: cstr128, hcw1ctr, bookcas1, td1, deskside). No event, id or Lua change; tests unchanged.
- Audit 0 errors / 0 warnings, build 0 warnings, check_exits 0, check_drops 0, `stale_bakes` none. Installed and baked
  02:37; tests from assets_dev 4 of 4 (12 of 12, `output/studio_cal/a8_s26/run/dd19/c023723`).
- Pictures: `output/studio_cal/a8_s29/shots/dd19_before.jpg` / `dd19_after2.jpg` (tour `a8_s29/dd19_tour.yml`; the
  after tour adds a look up at a brazier and at the bridge's windows, `dd19_tour2.yml`).
- Left: the braziers are small hanging fixtures with their own orange flame (the violet is the light round them); the
  other rooms (Common, robing room, quarters) unchanged.
