# XD-01 Joe's Warehouse, L4: notes

A new dungeon built from the written brief (L1 to L3 here, `devdocs/xeen/MAPS.md`, QUESTS.md Story M2) with the Map
Studio, by one agent, 2026-11-12/13. No original exists; nothing was measured from a shipped map except scale and
density (Goblinwatch `6d01`, the Abandoned Temple `6d02` and `6d07` of MM6: `output/studio_cal/xd01/ref/`).

State: `oymap validate` no issues; `fmt --check` clean; the build has three warnings, all placeholders (hoist, loft
ladder, pool grate). 24 rooms, 24 sectors, all reached. The playtest passes three runs of three (84 steps each).
Pictures: `output/studio_cal/xd01/shots/` (33 in the game, HUD off, plus `plan.png`, `iso.png`, `captions.yml`).
Scratch: `output/studio_cal/xd01/` (`go.sh` builds, installs into `mount/` and runs the playtest; `tour.yml` takes the
pictures from the scratch root `root/`; `shots_take1/` is the first take, before the fixes listed under "Pictures").

## The world it is built in

The Xeen world has no package, monsters or items. `world: xeen` validates and builds, but `oymap render`, `solve` and
the game refuse it ("assets_dev has no world 'xeen'"). So L4 says `world: mm7` (one line to change back), and every
Xeen thing stands in for something that exists:

| Brief | Built as | Why |
|---|---|---|
| Slot 1 Oozes (Slime 2) | MM7 Rat family, tier 1 (Giant Rat 2) | No slime or ooze below level 12 exists in MM6-8; every ooze row is immune to physical damage |
| Slot 2 Swarms (Doom Bug 2) | Dragonfly family, tier 1 (Dragonfly 2) | A flying insect at the right level; MM7 has its 3D model |
| Pen slimes | Giant Rats (385), 8 placed | As slot 1 |
| Mr and Mrs Wobbles (Breeder Slime 4, x3 hit points) | Two Fire Rats (387, level 6, 21 hp, 1D8+6) | The first stand-in, MM7's Emerald Ooze (310), looked right but is immune to physical, mind, spirit and body: a level 2-4 party could not hurt it (found when the playtest's kill sweep did nothing). A placed monster cannot be given more hit points |
| warehouse_key 12001 | Store Room Key (2176) | Name fits; Xeen items are unregistered |
| pen_key 12003 | Key (2110) | |
| joes_invoice 12002 | Bill of Sale (1530), an MM7 message scroll | The nearest name; reading it shows MM7's text |
| qbits 110010-110012 | kept as numbers | The game sets and reads them (the playtest checks all three) |
| music `dungeon_light` | MM7 track 18 | The game refuses a name (HANDOFF E10) |
| X1 street and riverbank | Emerald Island `7out01.odm` at the Temple of the Moon's arrival point | X1 does not exist |

## What the brief asks, and how each thing was built

Shell (L3 redrawn with today's words; L3's plan kept where it was right):

- **Loading dock (new, the arrival).** The brief's lock (warehouse key or Perception 3) belongs to X1's side of the
  street doors. With no X1, the lock is played in this map: the party arrives on a covered dock under a lean-to canopy
  (`ceiling_slope`), the warehouse front with the barred street doors (`slide_left`, `leaves: 2`), the notice board
  and the shuttered windows (readable wall `panels` with ids) on one side, the yard gate to the lane (the exit) on the
  other.
- **Loading bay**: L3's chamfered bay; crate stacks as blocks, two with a smaller crate stacked on top (`base`), two in
  dark shipping-crate planks; two joists (`beams`); corner posts (`ends`); Joe's carved sign (panel) over the barn
  doors. **Office**: L3's trapezoid; the two steps have treads and risers; the desk is a sized chest (the drawers);
  the ledgers are a readable bookcase panel; two framed notices; the counter window (`sill`).
- **Grain hall and loft**: one room now. The loft is a `levels` gallery 256 up along the north wall, reached by a
  `flights` stair along that wall; its rail is a beam on four posts (blocks standing on the level), broken at the west
  end where the ladder would stand. The roof is a whole-ceiling `ceiling_levels` gable (eaves 640, ridge 1088) on three
  tie beams and a ridge beam. Two grain bins are free blocks with straw tops. The north-east aisle (lean-to ceiling)
  carries the KEEP OUT door under a skull-and-crossbones notice. L3's separate loft, loft stair and overlook opening
  are gone.
- **Cellar stair**: two flights with stone treads and mossy risers (`slope.tread`, `riser`), ceilings that fall with
  them (`ceiling_slope`), the landing under a small barrel vault.
- **Breeding pens (the cistern)**: L3's sixteen-sided outline (springing 352 over the floor) under a brick dome
  (`ceiling_levels` with `top_scale: 0.3`, crown 640 over the floor, as the brief asks); a mossy stone course
  (`bands`); the drain pool sunk 64 (`levels`) with the liquid slime texture (`7slimywtr`, `floors: water`) behind a
  closed kerb ring (`parapets`); three shelves of glass bug tanks on plain walls (outlined blocks with `base`), one
  tank lower and of other glass (the cracked one, where the doom bugs spawn); FEEDING TIME on a plaque over the lever
  and a plaque over the heart gate. The six pens are L3's wedges, now with a low ceiling.
- **Feed store, stash**: L3's plans; plank joists over the store; the stash door is a sliding piece of the brick wall.
- **Honeymoon pen**: L3's kidney one step down, under a shallow dome; the pair's nest, feeding bowls, bones, the rival
  exterminator's body with his boots and a scroll lying beside it.
- **Shipping room**: L3's pentagon; the delivery chute as a raised `ceiling_levels` well in the north-east corner with
  a hanging sloped slab coming down out of it (`top_slope` + `thickness`, `steep_floor`); racks of bottles (panel);
  the crate stack; the packing table with a potion and gloves on it (items with `floor_height`).
- **Culvert**: L3's three rooms (bend, ramp, mouth) are one `path` tunnel with an eight-sided `section` (flat wet
  floor 192 wide, walkable banks, upright walls, chamfered crown), path points `[x, y, z]` for the 256 slope, a square
  head with the iron door, water underfoot; it ends in an outfall chamber (barrel roof, rubbish heaps) and the grate's
  sill with the exit.

Surfaces: eight themes from the MM6-8 library the brief names (warehouse weatherboard over an upright-board skirting,
bay boards, office panelling, cellar brick on a stone footing, cistern brick, feed store, culvert stone, the dock's old
brick), door faces chosen per door (barred plank barn and street doors, a studded office door, a grilled plank KEEP
OUT door, an iron culvert door, a red flowered gate for the heart, iron bars for the river grate), thresholds on the
main doorways, corner posts, signs as panels. 42 textures; the largest share is 14 %.

Objects and wiring (every mechanism a preset; Lua only for the pair's death check):

| Brief | Built |
|---|---|
| Entrance: warehouse key or Perception 3, open for good | `evt:street_doors`, door preset, `condition: any[item, stat PerceptionSkill >= 3]`, `action: open`, locked text; the shutter panel answers differently with Perception 3 (`else_effects`) |
| Barn doors, office door, shipping door | door presets (two-leaf slide, hinged, hinged) |
| Slime bucket over the office door, once | a plate inside the door, `trigger: step`, `once`, 4 Body damage to the current character, text |
| Pen key in the desk drawers, ledger clue | chest with `items: [pen_key]`, 50 gold, one random item; readable panel |
| KEEP OUT, pen key, not consumed, open for good | door preset `condition: {item: pen_key}`, `action: open` |
| Six pen gates singly, or all on FEEDING TIME | six door presets (`action: open`); `evt:feeding_time` switch preset `opens:` all six, `once`, sets a map variable |
| Heart gate | door preset, `action: open` |
| Mr and Mrs Wobbles, bonus bit | two placed monsters in group 2; a timer event (every 2 s) whose Lua tests `CheckMonstersKilled(Group, 2)` and sets `joe_pair_slain` |
| Invoice crate: invoice, quest bit, mild trap | chest `items: [joes_invoice]`, 40 gold, `random_items: 0`, `trap_level: 1`; its preset `sets: {qbit: joe_invoice_found}` and shows the invoice's text |
| Stash behind the Chow, tier 2 | sliding door preset; chest level 2, 2 items, 300 gold |
| Loft chest tier 1 | chest, 2 random items |
| Culvert iron door | door preset (slide up) |
| Grate lifted from inside on first use | door preset on the grate, `action: open`, `sets: {qbit: culvert_grate_open}`; the exit beyond it |
| Lights | 20 wall torches with their own light (13 iron lanterns, 6 green flames, 1 iron torch), 7 point lights (pool glow, office candle, pink heart candle, two hanging lanterns, lane and river daylight); sector darkness 10 to 24 as the brief's atmosphere says |
| Population | 9 spawn points (6 doom bugs, 3 rats) where the brief puts them, 8 placed rats in the pens, the boss pair |
| Floor items | potion and gloves on the packing table, boots and a scroll by the corpse, a bottle in the bay |

## Scale against the MM6-8 bands

`oymap metrics <L4> --reach` (`output/studio_cal/xd01/metrics.json`); bands from
`devdocs/xeen/research/MAP_CRAFT_CALIBRATION.md` 3.1, 3.3 and 6.3.

| Figure | XD-01 L4 | Band or comparison |
|---|---|---|
| Floor area | 14.6 M units² (walkable 10.7) | S class 20-35; MM8 p25 20; 6d07 26.1 (the brief chose under the band: a ten-minute first dungeon) |
| Sectors | 24 | S 10-20, M 20-35; starter median 22 |
| Floor levels | 4 (loft 256, street 0, cellar -384, culvert -640); floors span 896, roof to 1,088 | 2-4 |
| Loops | 1 (the hall and its loft: up the stair, drop off the broken rail) | at least 1 for M and L |
| Doors | 17 (16 door events) | M 8-16; starter median 10 |
| Monsters | about 31 (9 markers x 2-3, 8 pen rats, 2 boss) | S 20-35 |
| Chests | 4 (plus the corpse's floor loot) | S 2-4 |
| Lights | 27 (20 torches + 7 points) = 1.9 per M units² | 6d01 1.8, 6d07 2.8; `metrics` says 0.48 because it does not count torches (defect 3) |
| Decorations | 70, 4.8 per M units² | 6d01 2.1, 6d07 4.1 |
| Doorways | median 256 wide, 288 high | 6d01 304 x 256, 6d07 256 x 256 |
| Sector height | median 448 (288 to 1,088) | 256-328 small rooms, 464-592 mid rooms; 6d07 484 |
| Plates, traps | 1 plate; 2 traps (bucket, crate) | 1-15 plates; traps on one map in three |
| Secret faces | 0 (no word) | 1-6 per M dungeon |
| Boss | yes (the pair) | about 1 dungeon in 5 |

## Order of play (`oymap solve`)

```
step 0: the dock
step 1: street doors (key or Perception) -> ramp, bay, office steps
step 2: barn doors, office door -> grain hall and loft, aisle, office
step 3: needs item 2110 (pen key): KEEP OUT -> the cellar stair
step 4: the cistern and everything off it: iron door, FEEDING TIME (six gates), heart gate, shipping door, stash
step 5: river grate -> the sill and the exit
never reached: 0 sectors
```

That is the brief's order (entrance, hall and loft, cellar, cistern and pens, crate, culvert out); the crate is not a
gate, so it shares step 4.

## Playtest (`playtest.yml`)

84 steps; passes three runs of three on the final build (`output/studio_cal/xd01/run/final1.log` to `final3.log`).
It reads the notice board and the shutter, opens the street doors, walks the ramp and bay, opens the office (the
bucket's step event runs once and not again), loots the desk (the pen key), reads the ledger, opens the barn doors,
climbs the loft stair and walks the loft, opens KEEP OUT with the key, walks both flights to the cistern, opens pen 6
by its own click and checks the other five stay shut, pulls FEEDING TIME and checks all six open, opens the stash,
opens the heart gate, kills the pair and checks `joe_pair_slain`, opens the shipping room, loots the invoice crate
and checks the invoice and `joe_invoice_found`, opens the culvert door, walks the tunnel round its bend and down its
slope, lifts the grate (`culvert_grate_open`) and leaves for Emerald Island with the invoice and all three bits.
It loots only the desk (one random item) and the crate (none), so no run depends on what chests roll.

What it cannot show: **the key's way in**. The MM7 world's new-game party already has a member with Perception 3
(Perception is read from the party's best member), so the doors always open for it, and no scenario step removes a
skill. The locked branch and the key's branch are shown by `oymap flow devdocs/xeen/briefs/xd01/L4 --assets assets_dev
--event 31`: locked text without either, open with item 2176 or with Perception 3. The walk still grants the key and
checks the doors stay open.

## Where I departed from the brief

1. **The arrival is a covered loading dock outside the street doors**, not the middle of the bay, so the doors' lock
   can be played in this map (the brief puts it on X1). When X1 exists the dock can stay (an alcove off the lane) or go.
2. **The loft is a gallery level inside the grain hall** (the task's word), not a room beside it; the L3 note "rooms
   cannot stack" no longer holds. The hall lost its L-shape: the aisle is its own room off the east wall.
3. **Monsters and items are MM7 stand-ins** (table above); the boss pair are Fire Rats.
4. **The pen slimes are placed monsters**, not spawn markers, so each pen holds its occupant until its gate opens and
   the fight is the same every time.
5. **The bucket trap is a plate** just inside the office door (a door preset has no `once`).
6. The corpse's loot lies on the floor beside it instead of being searched.
7. The culvert's water is drawn with the slime liquid texture all the way; the brief's "unlit" culvert is kept at
   darkness 20 so it reads at all.

## Gaps (what I wanted to say and could not), most harmful first

1. **A placed monster cannot be made into a boss**: no `monsters[].hp` (or a hit-point factor), `name` ("Mr Wobbles"),
   `level` or actor script (`behaviour`: split into two slimes below half health, which the engine's actor scripting
   can do). The brief's small boss is two ordinary Fire Rats. Together with the missing Xeen rows this is what most
   weakens the map.
2. **An entrance condition on the arrival side**: the plan's `entrances[].condition` and the neighbour's `condition`
   are not built; a dungeon whose door is locked from outside has to move the lock inside (departure 1). A field that
   writes the check into the neighbour's door, or an arrival that starts outside a named door, would say it.
3. **No ladder** (`objects.yml ladders`; the scene has `ladders`): the loft's ladder is a placeholder and the loop is a
   drop.
4. **No secret flag on a door** (`doors[].secret`, the facet's IsSecret bit with the map's perception difficulty): the
   stash door is a plain sliding door that looks like the wall; it is found by clicking walls after reading the ledger.
5. **No barred gate**: no grille or bars texture in MM6-8 (MM9's grilles are cutouts and not mounted for MM7), and no
   see-through leaf, so the pen gates are grilled plank doors, the pool's grate is a placeholder and the pens cannot be
   seen into before they open.
6. **No pulsing light** (`lights[].pulse`; the scene has `pulsing_lights`): the pool glows steadily.
7. **No placed ambient sounds** (scene `ambient_sounds`) and **no indoor haze** (scene `mist`): the brief's wind,
   chitter, bubbling and running water, and the faint green haze in the cistern, are missing.
8. **`levels` need a level room floor**, so the grain hall cannot have both its loft and the sag toward a gutter the
   brief wants (`floor_points` with `levels`).
9. **A chest has no top surface** (`chests[].top_surface`): Joe's desk is a box of planks on all sides.
10. **Readable text surfaces**: signs are carved plaques with foreign script; the brief's painted signs (KEEP OUT, MR &
    MRS WOBBLES, FEEDING TIME) exist only as their hover titles and status text.
11. **A Lua test cannot guard a handler's effects**: the order is condition, doors, sets, effects, text, lua, so the
    pair's death check had to be written wholly in Lua (`kills`, which would say it, is not lowered: defect 4).
12. Hanging and swinging decorations: the brief's swinging lantern (`dec07`) and hanging cage (`hngncge2`) have 3D
    bindings only for named shipped maps (`maps:` in `engine/models/indoor_decorations.yml`), and `oymap assets` does
    not say so; I used a standing chandelier hung by `height` and a standing cage.

## Tool defects (repros under `output/studio_cal/xd01/repro/`)

1. **Texture names with a hyphen are refused.** `rooms.yml: rooms[0].walls[0].panels[0].surface.texture: 'sign01-1'
   does not match ^[A-Za-z0-9_]{1,10}$` though `oymap assets sign --world mm7` lists `sign01-1`, `sign06-1` and the
   framed portraits `cnbport-1` to `-5`. Repro `texture_hyphen/` (`oymap validate`).
2. **A ridge over a chamfered convex room is refused with a misleading message.** `ceiling_levels: [{ceiling: 1088,
   top_scale: [1, 0]}]` over a seven-sided convex outline gives "`top_outline` has one point for each point of the
   level's outline (7 here) ... Every point must lie inside the outline or on it"; so does an explicit ridge through
   points that are all inside or on the outline. Accepted: each chamfer leaning to the ridge's end point (what L4
   uses). Repro `gable_chamfer/`.
3. **`oymap metrics` does not count lights that decorations carry**: three wall torches give `lights: 0`,
   `lights_per_area: 0`, so a torch-lit studio map measures as unlit against the shipped bands. Repro
   `metrics_lights/`.
4. **`kills` is offered by the condition schema but not built**: "wiring.yml: events[0].condition.kills: the build
   cannot lower a 'kills' condition yet". Repro `kills_condition/`.
5. `oymap render`, `solve` and the game refuse a project of a world without a package ("assets_dev has no world
   'xeen'") while `validate` and `build` accept it: a new world's brief can be built but never looked at. Command:
   `oymap render devdocs/xeen/briefs/xd01/L3 --assets assets_dev --out x.png`.
6. Minor: `oymap install <project> --root <r>` without `--build` reads `<project>/build` and says "(build the
   project first)" after a build with `--out`; `oymap build --out` still writes `ids.lock.yml` into the folder it
   reads (known).

Test-harness notes (not the studio): `status()` in a `play_lua` step does not see status lines shown during an earlier
`walk_to` (so the bucket's text cannot be asserted; its once variable is); a scenario has no step to remove a skill;
`clear_hostiles` kills through walls within its radius, so a boss behind a closed gate dies before the party arrives
unless the radius is kept small near it (the walk uses 450 in the cistern).

## What in the brief was unclear or contradictory

- Its monsters do not exist at its levels in any shipped world: Slime 2 and Breeder Slime 4 have no row, and every ooze
  of MM6-8 is level 12+ and immune to physical damage. A Xeen monster table is the precondition for this map.
- Perception 3 opens the doors for a default MM7 party, so the key quest (the drunk's rumour, the rain barrel) is
  skipped by nearly every party. Expert Perception, or a higher number, would make the key matter.
- The lock is stated twice, on the neighbour (outside) and on `entrance:street_doors` (inside space).
- L3 still says rooms cannot stack and lays the loft beside the hall; MAPS.md and the task call it a loft beside the
  hall too, which a level inside the hall now draws better.
- `music: dungeon_light` and the unregistered item ids (12001-12003) cannot be played as written (known, HANDOFF E10).
- The brief wants the pens seen into ("barred"), a grate over the pool and a lever "labelled FEEDING TIME"; none of the
  three has an asset, which the brief could not know.

## Pictures

Best: `shots/17-cistern-from-stair.png` (the signature room), `shots/16-cellar-landing.png` (the green glow and the
heart gate from the stair: the brief's landmark), `shots/18-cistern-pool.png`, `shots/04-ramp-into-bay.png`,
`shots/28-shipping-room.png`. Weakest: `shots/11-hall-loft-stair.png` (the stair along the wall is cramped and all one
plank colour) and `shots/31-culvert-bend.png` (a dark, bare stone tube).

Fixed after looking at the first take (`shots_take1/`): the warehouse front tiled a window into every 256 units (now
plank with one pair of shuttered windows); two signs showed black squares (their textures' empty halves); the drain
pool showed brick instead of slime (its level had no edge surface; fixed and checked close up); the grain bins blocked
the view through the barn doors; the honeymoon pen was bare; the candle under the heart gate blocked the neck (found by
the playtest); camera places for the bay and the loft stair.

## Judgement

As a first dungeon it works: a short, readable route with a clear goal, a locked door that teaches a key, a lever that
does something bad, a secret behind a clue, two small traps, a boss and a back door out, all of it played end to end.
The cellar is the good part: the walk down the stair toward the green glow and the red gate, the domed cistern with its
pool, gates and tanks, the shipping room with its chute. Every set piece of the brief is there and wired with presets.

What is weak: the upstairs is one hue of orange plank from floor to roof, so the bay, hall, aisle and loft run
together; the hall is large and empty above the bins. The pens are bare wedges with doors the player cannot see
through, so FEEDING TIME is a sound and some rats rather than a spectacle. The culvert is a long dark tube with nothing
in it. The boss pair are rats, there are no slimes at all, and Perception makes the key moot. And the map is under
the S band's area by a quarter: right for ten minutes, thin for a player who wants to explore.

With another day: darker floors and a plaster or whitewash band upstairs, a second wood tone and more varied crates;
straw floors, troughs and a drain channel in the pens; a ledge and a midway grating with a rat nest in the culvert,
its water lit by a shaft of daylight; real slimes and a splitting boss when the Xeen rows exist (and an `hp` on placed
monsters); the ladder, the secret flag, pulsing pool light and sounds when the words exist; a Perception threshold that
leaves the key worth finding.

## Second pass (2026-11-13)

A second agent took the map through the words added since 2026-11-12. The first pass is kept as it was above; the
project as it stood is in `output/studio_cal/xd01/pass1_backup/`. Pictures: `output/studio_cal/xd01/shots2/` (42 in
the game, HUD off, with `captions.yml`, `plan.png`, `iso.png`); the tour is `output/studio_cal/xd01/tour2.yml`, the
build-and-play script `go2.sh`, the four runs `four.sh` (logs in `run2/`). Reference looks: MM7's Wine Cellar (`7d16`)
and MM6's Free Haven Sewer (`sewer`), rendered and toured (`output/studio_cal/xd01/ref2/`): their lesson was dark walls,
one warm light source per bay, and water down the middle of a stone channel; nothing of theirs was copied.

State: `oymap validate` no issues, `fmt --check` clean. The build has two warnings, both the boss names (below); the
three placeholders are gone. 26 rooms, 26 sectors, all reached. `solve` opens it in the same six steps as before
(dock; street doors; barn and office doors; KEEP OUT with item 2110; the cistern and all off it, now with the six bars
as movers 18-23 and `more of sector 1`; the river grate). Metrics: floor 15.1 M units², 102 decorations (6.7 per M),
28 light sources (1.85 per M units², `decoration_lights` 23), 20 lights in objects.yml (5 light records and 15 pulsing
lights: metrics counts only the records as `lights`), 4 secret faces.

Playtests: `playtest.yml` (110 steps) and `playtest_perception.yml` (6 steps) each pass four runs of four
(`run2/four.out`).

### What changed, room by room

- **Loading dock**: cobbles (`thjophayqa`) instead of the bay's flags; the hoist placeholder became the real thing: a
  dark arm off the warehouse front to the beam, a rope (a hanging 8-wide block) and a crate hanging 120 over the dock.
- **Loading bay**: its own materials, no longer the hall's: dark tarred upright boards (`bmplnk`) over a brick footing
  192 high (a room band), stone flags (`tfb07`) where the carts come in, dark log posts in the corners and as joists
  (`d6ebeam`), a packing bench on the east wall, a pallet of sacks, Joe's hand-painted sign (`sign01-1`, a hyphen name)
  over the barn doors; base darkness 14 to 20, so the two lanterns make pools.
- **Joe's office**: the one white room: whitewashed plaster under a moulded cornice (`grtop`) over a plank wainscot
  (`bemhwal` band 128); the desk has drawer fronts on its long sides and a board top (`chests[].top_surface`); a stool,
  a strongbox, a filing cabinet that is clicked (a platform with an `id`: the Mayor's cellar billed three times, the
  SUPPLIERS drawer empty) and a painted Pest of the Month notice (`sign06-1`, clicked).
- **Grain hall**: half-timbered walls of dark oak frames and rubble stone (`beams1v9u9`), two rows of three dark posts
  under the tie beams, the floor sagging 24 into a slimy gutter down the middle (`floor_points`, `floor_lines`, the
  gutter's own surface by `floor_surfaces` `at`), the loft a level over that uneven floor (the new rule), now along the
  whole north wall with a planked front (`bwooda2` edge) and straw on top; three hanging lanterns whose light flickers
  (`pulse`, 0.82 to 1), ambient 20 between them; the grain bins moved back to the barn doors' sides, shipping crates in
  the south-east corner, a crate at the loft's foot, chaff heaped in the gutter, a bucket, barrels and sacks.
- **Loft stair**: no longer squeezed along the north wall from the corner: an open flight (`open_below`) of pale
  treads with dark hand rails (`sides`) rising straight north from the middle of the hall to a gap in the loft's rail,
  in full view from the barn doors (pictures 10 and 12).
- **Loft and ladder**: a ladder (`ladders[]`) at the broken rail's west end; the playtest climbs down and up it. A
  broken grain bin on the loft.
- **Aisle**: its own theme (weatherboard over a brick footing, log posts, flags), crates at its south end, a sorting
  bench, Joe's painted house rules (clicked: "1. No Gunther ... 4. See rule 1").
- **Cistern and pens**: the six pen doors are gone; each pen has **real bars**: a mover (`movers[]`) whose block is the
  bottom rail and whose `parts[]` are seven iron bars and the top rail, standing 22 inside the pen's mouth, rising 322
  into the pen's ceiling. A click on the bars lifts that pen's set (the switch preset with the mover as `source`);
  FEEDING TIME lifts all six and switches on a red lamp over the lever that flashes (`on: false`, `lights_on`,
  `pulse`). Each pen is bedded with straw (its own theme), has a muck heap, a feeding bowl and a slow green glow of its
  own, out of step with the others (`pulse` with `phase`), so what waits in it is seen through the bars. The drain pool
  glows in a slow pulse (`pulse` with a radius swing) and has a round iron grate in its middle (`d1lggrt` on a 6-high
  block), the placeholder gone. The FEEDING TIME and MR & MRS WOBBLES signs are hand-painted boards (`sign01-3`,
  `sign01-2`).
- **Feed store, stash**: the stash's sliding door is now `secret: true` with the store's own brick as its surface; dark
  joists.
- **Honeymoon pen**: the boss's room: a heart-shaped stone trough brimming with slime chow, the pair's straw bed in the
  bean's hollow, four candles round it under a pink candle-light, the corpse with his boots and scroll as before.
- **Mr and Mrs Wobbles**: placed monsters with `name` and `hp: 40` (the game ignores the `hp`: gaps); each splits on
  death into two Slime 2 stand-ins in the pair's group (a timer event with `kills: {monster: ...}`, `once`, `summon`
  with `group: 2`); the bonus bit is set only when the whole group, splits included, is dead and both splits have
  happened (`kills: {group: 2}` with two map variables), and then the heart's candle goes out (`lights_off`). The first
  pass's Lua timer is gone: no Lua is left in wiring.yml.
- **Culvert**: split into a short head, a drain shaft and the rest. The drain shaft is a square chamber where the
  tunnel turns: a well rises 288 to the street's round iron grate (a `ceiling_levels` well with `d1lggrt` on its top),
  grey daylight falls down it (a light that dims now and then as something passes over), a dry ledge one step up (a
  level) holds a rats' nest (the culvert's slot-1 spawn moved there: the fight on the way out), bones and a Bronze Ring
  lost down the drain (the playtest picks it up); rubbish washed down below the shaft. The water underfoot is MM7's
  moving water (`7wtrtyl`) now; two faint green glows in the channel down the slope (slime washing out of the pens),
  rocks fallen into it, one of Joe's buckets dropped near the foot, and a second daylight in the outfall.
- **Shipping room**: unchanged (it was one of the good rooms).

### What each new word did here, and how it read in the game

| Word | Used for | Read in the game |
|---|---|---|
| `ladders[]` | the loft ladder at the broken rail | Climbed both ways by the playtest; the rails and rungs read as a ladder (picture 14). |
| `monsters[].hp`, `name` | Mr and Mrs Wobbles | Built; the scene holds hp 40 and the names, but the game gives each its kind's 21 hit points and shows the kind's name (gaps 1, 2). |
| condition `kills` | the splits (`monster`), the bonus bit (`group`) | Works: the splits run on each death, the bit and the candle wait for the whole group. |
| effect `summon` with `group` | the splits | Works: two Giant Rats per death, in group 2, so `kills: {group: 2}` waits for them. |
| `doors[].secret` | the stash door | Builds; `metrics` counts 4 secret faces. Opens on its click; the pulse for a party with Perception was not checked in a picture. |
| `movers[].parts[]` as bars | the six pen gates | Builds and reads very well: the pens and their occupants are seen through the bars (pictures 21, 24, 25, 27); the bars lift into the ceiling on a click or on the lever (28). |
| `pulse` | pool, pens, hall lanterns, red lamp, culvert glows, shaft daylight, honeymoon candles | All draw; the pens' out-of-step glow and the red lamp are the best of it. A flickering lantern pool is hard to see in a still. |
| `on: false`, `lights_on`, `lights_off` | the red lamp (on), the heart candle (off) | Both switch (the playtest checks both; picture 29). |
| `sounds[]` | drip, bubbling pool, river, shaft drip | **Refused** for an MM7 project (repro `sound_world_audio/`): not in the map. |
| level over an uneven floor | the loft over the sagging hall | Builds; the loft's front reaches down to the sag (picture 10). |
| `floor_surfaces` | the gutter's slime | Works (pictures 10, 13). |
| `chests[].top_surface` | Joe's desk | Works (picture 8). |
| hyphen texture names | `sign01-1`, `-2`, `-3`, `sign06-1` | Work: Joe's signs are now painted boards, not carved plaques. |
| platform with an `id` as a click source | the filing cabinet | Works (the playtest reads it). |
| condition `lua` | not needed: `kills` and `map_var` said everything | |
| `solid: false`, `visible: false`, hanging slabs, arches on vaults | not needed here | |

### Refused (each with a repro built from a copy with `--out`)

1. **Placed sounds of an MM7 project**: "objects.yml: sounds[0].sound: the world mm7 has no sound file waterdrip.wav
   (looked for worlds/mm7/audio/waterdrip.wav and the same with .wav): name a file of that folder, as
   \`waterdrip.wav\`", and the same for `7fountain.wav`. The MM7 world's audio folder holds 14 shop and boat samples; the
   drip is MM6's (`worlds/mm6/audio/waterdrip.wav`) and the fountain and bubbling cauldron are engine sounds
   (`engine/audio/7fountain.wav`, `7bubbling cauldron01.wav`). The example message names a file the folder does not
   have. Repro: `output/studio_cal/xd01/repro/sound_world_audio/` (`validate.txt`). The four sounds wanted are kept in
   `output/studio_cal/xd01/tools2/sounds_refused.yml`.
2. **A liquid texture needs a `size`**: `rooms.yml: themes[2].floor: missing required key 'size'` for `{texture:
   7wtrtyl}`, though `oymap assets` says a liquid "has no picture and no size". L4 writes `size: [128, 128]`. Repro:
   `repro/liquid_size/` (`validate.txt`).

Found in the game (not refusals):

3. **The game ignores a placed monster's `hp`**: the scene has `hp: 40` for actor 0, the game gives it 21 (its kind's)
   and 25 damage kills it. Repro: `repro/boss_hp/` (project, `scenario.yml`, `run.log`: `hp=21/21`). The build's
   description of `hp` says the game honours it; a game-side change is needed.
4. **Test harness**: `play_lua`'s `mapvar(n)` and `mapvar("name")` read 0 for map variables the map's handlers set
   (the splits' status lines show, `state_dump_map_var` reads 1). Repro: `repro/mapvar_play_lua/` (`run.log`). The
   first pass's check `mapvar("feeding_time") ~= 0` before the lever passed for the same reason. The playtest checks
   map variables with `state_dump_map_var` only.
5. Test harness: the `light` assertion's `key` for a light record is its index among the map's records (the heart
   candle is key 0) while ids.lock.yml `lights` gives it 13 (the number `evt.SetLight` uses), and a pulsing light that
   starts dark reads `unset` (not `false`) until an event switches it.

### Pacing, walked as a level-2 party

The dock is the first choice (the key from X1's rain barrel, or a sharp eye on the loose shutter; the notice board
sets the joke). The bay is the first fight, out of sight of the doors (doom bugs at the barn doors), with a bottle in a
corner. The office is the first reward and the first trap: the bucket, the desk's pen key and 50 gold, the ledger's
clue, the cabinet's joke. The grain hall is the big upstairs fight (two bug packs and rats in the gutter) and the
loop: up the open stair to the loft's chest, look down on the hall, down the ladder. The aisle's house rules prepare
the lever ("3. Do not pull the FEEDING TIME lever"). The cellar stair is a short quiet walk toward the green glow. The
cistern is the surprise: six pens of waiting stock behind bars, a loose swarm from the cracked tank, and the choice:
lift the bars one pen at a time, or pull the lever and fight everything in the stair's mouth under a flashing red
lamp. The feed store is quiet; the stash behind the secret brick is the best loot. The honeymoon pen is the boss: the
pair, then their splits; the candle going out marks the bonus. The shipping room is the goal (the invoice and its
itching powder). The culvert is the way out: the drain shaft's daylight, rats on its ledge and a ring by their nest,
then the river.

The stretch with least in it is the culvert's slope (752 long): it got a glow in the water, rocks and a bucket, not a
fight; shortening it would move the outfall and the brief's 256 drop.

### Gaps still open, most harmful first (with the word that would say each)

1. **A boss's own hit points do not reach the game** (`monsters[].hp` is built and ignored; repro `boss_hp/`). Mr and
   Mrs Wobbles are two 21-hit-point Fire Rats; with the splits the fight is six monsters, not a boss. Also no level,
   attack or resistance of its own (the field description says so): a Xeen Breeder Slime row is the real answer.
2. **Boss names show only on the corpse**: `name` needs a row in `engine/data_tables/english/place_mon.txt` (outside
   the project); the build warns twice. A project-scoped names table (`project.yml names`) would say it.
3. **No placed sounds in an MM7 project** (`sounds[].sound` limited to `worlds/<world>/audio`): the brief's dripping,
   bubbling and running water are missing. A `sounds[].scope: engine` or a path into another world's audio would say
   it.
4. **The split below half health** needs an actor script (`monsters[].behaviour`); the split on death is the nearest.
5. **An entrance condition on the arrival side** (first pass gap 2, unchanged).
6. **Indoor haze** in the cistern (the scene's `mist`; no word).
7. **Painted text**: the signs are painted boards in the game's script; Joe's words exist only as their click texts. A
   panel `text` drawn on the face would say it.
8. **Hanging decorations bound to named maps** (the swinging lantern `dec07`, the hanging cage `hngncge2`): still the
   standing chandelier `dec27` hung by `height`, and the standing cage.
9. A liquid texture's `size` (repro `liquid_size/`, minor).

### Departures from the brief

1. **The loft stair** rises straight north from the middle of the hall to a gap in the rail, not west along the north
   wall from the aisle: the first pass's flight along the wall was cramped and hard to read; the brief's eight steps
   of 32 and its arrival at the loft are kept.
2. **The pair split on death**, not below half health (no actor script), into two Slime 2 stand-ins each.
3. **The pens' gates are movers with bars**, not doors: the brief's "barred gate (rising)" in its own shape; one click
   or the lever as the brief says.
4. **The loft runs along the whole north wall** (it ended 384 short of the east wall), so the stair could come up in
   the middle.
5. **The culvert gained a drain shaft** where it turns (the brief's "unlit" culvert now has daylight down a street
   drain), and the slot-1 spawn moved from the culvert's head to the shaft's ledge.
6. The first pass's departures 1 (the dock), 3 (stand-ins), 4 (placed pen monsters), 5 (bucket as a plate) and 7 (the
   culvert's darkness, now 22) stay.

### With a real Xeen world

`world: xeen` in project.yml, then: the encounter slots and placed monsters to the Xeen Slime 2 / Doom Bug 2 /
Breeder Slime 4 rows (with the split as an actor script, and the boss's hit points from its row), the items to 12001-
12003, music by name, both neighbours to X1 (and the entrance's lock on X1's side if that word exists then), the four
sounds from the Xeen audio folder (if it holds a drip, a bubbling pool and a river), names for the pair in the names
table, and the Perception threshold the brief settles. The textures are from the shared MM6-MM8 library and would
stay unless Xeen gets a warehouse kit.

### The first pass's weak pictures, and the pictures that answer them

| First pass (`shots/`) | Second pass (`shots2/`) |
|---|---|
| 11-hall-loft-stair (cramped stair, one plank colour) | 12-hall-loft-stair, 10-hall-from-barn-doors, 14-hall-ladder |
| 09, 10 (the hall bare above the bins) | 10-hall-from-barn-doors, 11-hall-roof-bins, 13-hall-gutter, 15-loft-overlook |
| 04, 05, 07, 14 (upstairs all one orange plank) | 05-ramp-into-bay, 06-bay-crates, 08-office-desk, 17-aisle-rules |
| 20, 22, 23 (solid pen gates, a weak lever) | 24-cistern-west-gates, 25-pen-through-bars, 27-cistern-bug-tanks, 28-feeding-time, 29-feeding-lamp |
| 27-honeymoon-pen (no boss worth the name) | 32-wobbles, 34-honeymoon-pen (better dressed; the boss itself is still weak) |
| 31-culvert-bend, 32-culvert-slope (a dark empty tube) | 37-culvert-iron-door, 38-culvert-bend, 39-culvert-shaft-grate, 40-shaft-ledge-nest, 41-culvert-slope |

### Judgement

Good now: the cistern is the set piece the brief means: the pens are seen through real bars with their occupants
waiting in their own green light, and FEEDING TIME visibly lifts six sets of bars at once under a flashing red lamp
(pictures 21, 24, 25, 28, 29). The upstairs reads as three places with jobs: the dark bay of flags and tarred boards,
the white office, the half-timbered grain hall with posts, lanterns, gutter and loft; the loft stair is seen from the
barn doors and the loop has its ladder. The culvert has a place in its middle (the drain shaft's daylight, the rats'
ledge, the ring) and water that moves. Everything is wired with conditions and effects; no Lua is left.

Still weak: the boss: the game ignores `hp`, so the pair are ordinary rats with a split, and their names do not show;
the honeymoon pen's walls are bare brick above its furniture (pictures 32, 34). The culvert's slope is still a plain
stone tube with a glow in it (picture 41). The map is silent. Joe's signs are in the game's script. The grain hall's
upper walls are one texture all round; under a lantern it reads, in the corners it is dark wood and stone.

A third pass would: give the honeymoon pen panels and a painted heart on its walls and a lower dome; put a fight or a
find on the culvert's slope (a side niche with a second ledge); add a second warm material to the hall's upper walls
(a plank gallery front over the barn doors); take sounds and boss rows as soon as the words reach the game; and look at
the secret door's pulse with a Perception party in a picture.

## Texture pass (2026-11-13)

The user, on the second pass: the warehouse was built of "ship" tiles (ship windows inside a warehouse), "avoid making
it a Frankenstein's monster, the wood there doesn't really fit", and named the Pirate Outpost (MM8 `d06.blv`) as
fitting wood. This pass changes surfaces only: shape, objects, wiring, `ids.lock.yml` and both playtests are as the
second pass left them (the diff against `output/studio_cal/xd01/pass2_backup/` is texture names, sizes, one office band
removed, five rail posts given a surface, and notes). The edit was one script, `output/studio_cal/xd01/tools3/retex.py`
(exact string swaps, each counted), plus a few hand swaps after looking. Build and install: `go3.sh` (into `build3/`,
`mount3/` and the scratch root); playtests `four3.sh` (logs in `run3/`).

### The Pirate Outpost, looked at first

Pictures at the user's view (-439, -731, 0, facing 60, pitch -6) and in its other rooms, a render and the export's
faces by role: `output/studio_cal/xd01/ref3/` (`shots/`, `d06.plan.png`, `d06.iso.png`, `d06.json`), the family as
contact sheets in `output/studio_cal/xd01/tex3/` (`t66_all.png`, `pirate_misc.png`). How d06 uses it:

| Where in d06 | Walls | Floor | Ceiling | Trim, doors, things |
|---|---|---|---|---|
| Storerooms (the start room 7, room 1: the user's view) | `t66b01` dark panel with a carved wainscot, one picture (256) high; `t66floor` planks on some walls | `t66floor` planks | `t66roof` beams lashed with rope | `t66abc10a` posts, `t66b03l`/`r` braced plank doors with a small grille, `ch002a` studded crates |
| Upper room 2 (the captain's) | `t66a01` rough plaster in a timber frame over the carved wainscot; `t66a12*` weapon racks and banners | `t66flr2`, `t66floor` | `t66d13tb` | `trim9_32` |
| Hall 3, stores 4, bunk room 5 | `t66c01a` tan brick; in 4 and 5 `t66b01` under `t66cave` rock | `t66flr2` flagstones | `t66d04` carved knot panels | MM8 chests `gt002*`, furniture `t1books1`, `t1beds*`, `t1cab` |
| Corridor 10, hall 11 | `t66d01` cream plaster over carved panelling, `t66d01m`; `t66d01ma`/`mb` arched windows with ships at sea, `t66d01e`/`f` framed ship paintings, `t66d01h`-`l` bookcases | `t66flr2` | `t66d04` | |
| Cave 6, dock 12 | `t66cave` | water | `t66cave` | `t66e01s1` with `t66e01ph` (porthole) and `t66e01r1`/`r2` riveted strips: the moored boat's hull |

So `t66e01s1` is not a wall: it is the boat's riveted hull plating (also the hull of MM8's Small Sub Pen `d34`); its
211 faces are the boat and room 2's furniture. Kept out of the warehouse, with the other motifs of a pirate's den or a
ship: the porthole, the ship pictures and arched sea windows, weapon racks, banners, curtains (`t66b12i*`), the carpets
(`t66d01p1`/`p2`) and the carved knot ceiling.

### Families chosen per area

| Area | Rooms | Family | Why |
|---|---|---|---|
| Upstairs | dock, ramp, bay, office and steps, grain hall and loft, aisle | **MM8 Pirate Outpost `d06`** (its storerooms, hall and better rooms) and the same set as its neighbour the Abandoned Pirate Keep `d32` lays it | The user's choice: a wooden pirate hold is a warehouse. Bay and aisle: d06's storeroom walls (`t66b01` wainscot as a band 256, `t66floor` planks above), flagstones, the rope-lashed roof, posts, d06's doors and crates. Grain hall: d06's hall brick (`t66c01a`; the sagging floor allows no band) with plank floor, roof and the loft's front in the panelled wainscot. Office: d06's plaster over carved panelling (`t66d01`, one picture floor to ceiling at scale 1.5), its bookcase for the ledgers. Dock: the hall brick for the neighbours, the warehouse front in planks, the lane in flagstones. From `d32` only: `t66abc11a` (horizontal beam: risers, thresholds), `gt001a` (studded crate), `gkp103a`/`b` (plain plank doors: KEEP OUT, the lane gate). |
| Cellar | cellar stair and landing, cistern, six pens, feed store, stash, honeymoon pen, shipping room | **MM6 brick on MM6 `d1` stone**: the cistern's own red and mixed brick (`cbrdbrck`, `cbmxbrck`, kept) and mossy footing (`d1smbw`), the rest from the **Free Haven Sewer** (`sewer.blv`: `d1medbw`, `d1lggrt`, `d1ceil1`, `cbeam5`, `crcn96`) and the **Lair of the Wolf** (`6d17`: `cbrdbrck`, `d1smbw`, `straw`, `d6dorb`) | The cistern is the part the user and the lead found good: its look is kept. Its brick, footing, dome and grate were already MM6; what came from elsewhere is replaced: MM7 `tfb07` floors by the sewer's block stone `d1medbw`, the ship-window grille `bwooda2`, the no-dungeon glass, bars and slime pictures, MM8's rune door `gcstdoor`. No shipped dungeon has red brick as its main wall (6d17 and 6d03 use it on a few dozen faces), so the cellar cannot be one map's set without losing the cistern's look: the two bricks are the reasoned exception, everything round them is the sewer's and the Lair's MM6 stone and wood. |
| Culvert | head, drain shaft, slope, outfall, sill | **MM6 Free Haven Sewer**, whole | A culvert is a sewer: its mossy block walls (`d1wldle2`, lower `d1wldle3`), roof stone (`d1wle`), walkway stone for the ledge (`d1medbw`), its sewage liquid (`swprrf3`) in place of MM7's moving water, its round grate on the shaft and now on the river grate (`d1lggrt`), its water (`orwtrtyl`) beyond the exit. |

Two families and a half, then: d06/d32 upstairs, MM6 sewer stone below (with the cistern's bricks). Of the 46
textures, 22 are in d06's or d32's set (18 in d06's own), 11 in the Free Haven Sewer's, 4 more in the Lair of the
Wolf's; the rest are listed below with their reasons.

### Before and after (`texture_use.py --project`)

| | Second pass | Texture pass |
|---|---|---|
| Textures | 50 | 46 |
| Their main source maps (the tool's count: each texture's biggest user) | 23 | 17 |
| From no shipped dungeon | 23 | 5 (Joe's painted signs) |

The tool's "main source" names a texture's biggest user, not the family it was taken from: `t66abc10a` counts as the
Ogre Fortress, `t66flr2` as the Ogre Fortress, `gt002*` as the Plane of Earth, `t1books1` as Alvar's Merchant House,
though all of them are in d06's own set. Full lists: `output/studio_cal/xd01/texuse_before.txt`, `texuse_after.txt`.

Gone, with what replaced them: `bwoodb1` weatherboard and `bwoodb4` shutters with window holes (`t66floor`,
`gt003b`), `bwooda2` grille-window planks (`t66b01` on the loft front, `gkp103a` on KEEP OUT), `bwoodb1`, `bwooda1`,
`beams1v9u9` half-timbering, `grtop`, `bembllg`, `bmplnk`, `d6ebeam`, `d2ceil1`, `d2ceil2`, `cbeam5` upstairs,
`lilbrick`, `thjophayqa` cobbles, `tfb07` slabs, `tdoora`, `vh3door`, `dkwdr`, `csdoor` (castle doors), `gcstdoor`
(rune), `swr4` (a sci-fi machine panel from MM6's Control Center, on the river grate), `t66cratev`/`h` (no dungeon),
`crate_w64`, `7t1cab`, `bemhwal`, `bookcas1`, `ironn7dmbs`, `bigsign` (a carved bronze plaque in runes), `glass2` (a
blue house window) and `glass11` (stained glass) on the bug tanks, `rustjlf2n5` on the bars, `slim423fqx` on the
gutter and trough, `7wtrtyl`, `orwtrlga`, `beamplnv`.

### Kept from outside the area's family, and why

| Texture | From | Where | Why |
|---|---|---|---|
| `cbrdbrck`, `cbmxbrck` | MM6 6d17, 6d03; 6d10, 6d03 | cistern, pens, honeymoon pen; dome, stair, feed store, shipping room | The cistern's look, kept on purpose (above). |
| `straw` | MM6 6d17 | loft, grain bins, pens, feed store | The only straw of MM6-8; grain and bedding are the warehouse's goods, not its build. |
| `7slimywtr` | MM7 Erathian Sewers `d01` | drain pool, hall gutter, honeymoon trough, bug tanks | Slime is Joe's product, not sewage: MM6 has no slime liquid; the sewer's `swprrf3` read as dark water in the pool (tried, `shots3_try1/22`). On the tanks it stands in for glass (below). |
| `d8dorf` | MM6 6d15, 6d03 | culvert iron door, the pens' bars | MM6's plain iron door; the sewer's own door (`d8dora`) carries a lion mask and a cross. On the bars it reads as riveted iron (`shots3/25`). |
| `gcrydoor` | MM8 Escaton's Crystal | the heart gate | The cistern's landmark (red gate seen from the stair). A crystal-temple flower door: a stand-in until the painted heart gate exists (to generate). |
| `7winerack` | MM7 Wine Cellar | shipping room racks | Racks of bottles; none in the chosen sets (MM8 `winerack` is one face each in two maps). To generate if Joe's tonic bottles should show. |
| `gt001a` | MM8 d32 | shipping room crates, the invoice crate | Goods carried down from the warehouse: the same studded crates as upstairs (the sewer's `crcn96` stacked as bare planks, `shots3_try1/35`). |
| `sign01-1`, `-2`, `-3`, `sign06-1`, `warnsign` | no shipped dungeon (MM7 outdoor signs) | Joe's painted signs | Stand-ins: painted boards in the game's script, nearest to "Joe's hand-painted signs". To generate. |

### Textures to generate

| What it shows | Size (texels) | Where | Stand-in now |
|---|---|---|---|
| Joe's shop sign on planks: JOE'S EXTERMINATING, a cartoon slime under a boot | 256 x 128 | bay north wall over the barn doors (`panel:bay_sign`) | `sign01-1` |
| Joe's notice board: pinned notices (opening hours, NO CREDIT, a bill) | 128 x 128 | dock, left of the street doors (`panel:notice_board`) | `sign01-1` (the same picture as the bay sign) |
| MR & MRS WOBBLES - DO NOT SEPARATE, painted on a board with a heart | 128 x 32 | over the heart gate (`panel:heart_sign`) | `sign01-2` |
| FEEDING TIME, painted on a board, an arrow down to the lever | 128 x 32 | over the lever (`panel:feeding_time`) | `sign01-3` |
| Joe's house rules (1. No Gunther ... 4. See rule 1), painted on a plank | 128 x 256 | aisle east wall (`panel:rules`) | `sign06-1` |
| Pest of the Month notice with a drawing of a slime | 128 x 256 | office north wall (`panel:pest_notice`) | `sign06-1` (the same picture as the rules) |
| KEEP OUT (THIS MEANS YOU, GUNTHER), skull and crossbones, painted on planks | 256 x 128 | over the KEEP OUT door (`panel:keep_out`) | `warnsign` |
| A plank gate in t66/d6dorb wood, painted red with a big white heart | 128 x 256 | the heart gate (`door:heart_gate`) | `gcrydoor` |
| Side of a glass bug tank: dirty glass, a lid rim, doom bugs and slime behind it | 64 x 128 | the six tanks (and the cracked one, glass broken) | `7slimywtr` (liquid on the tank sides) |
| A rack of Joe's stock: stoppered bottles and jars of green tonic and powder, labels | 128 x 256 | shipping room east wall | `7winerack` |
| Optional: a pair of plank shutters, one hanging loose on a nail | 256 x 256 | dock, the Perception clue (`panel:shutter`) | `gt003b` (boarded) |

In the t66 wood and painted in readable letters; the signs' size is their panel's picture size (panels stretch with
`fit`).

### Playtests

On the retextured build (`run3/`): `playtest_perception.yml` passed every run (24 of 24). `playtest.yml` passed 20 of
24 in six sets of four: set A 3 of 4 (`run3/first/`: step 101, the party 0.5 above the assert's height band at the
culvert's foot), B 4 of 4, C 3 of 4 (`run3/third/`: step 68, one Giant Rat alive after FEEDING TIME's sweep), D 4 of 4,
E (final build) 2 of 4 (`run3/fifth/`: step 77, three Fire Rats where two are asserted), F (final build) 4 of 4
(`run3/four.out`). None is a texture effect: geometry, spawns and events are unchanged, and step 77's cause is shown at
the map's start: a probe that only loads the map and counts Fire Rats (`tools3/spawn_probe.yml`, `run3/probe_*.log`)
found three in 1 of 10 runs, because a slot-1 Rat marker (tier 1) can roll its C tier (Fire Rat, 387), and the
assert at `playtest.yml` line 193 counts monster 387 over the whole map. The fix is the playtest's, not the map's
(`near: [2112, 6400, 700]` on that assert, and on the step-68 count a sweep radius that covers the pens), and was not
made here because the playtests were to stay as they are.

### What looks worse

- `14-hall-ladder`: the ladder (now `t1books1`, d06's plain furniture wood) is dark on the dark panelling in the
  hall's unlit corner; it reads close up (`shots3_extra/04-ladder-close.png`), not from the second pass's camera.
- `13-hall-gutter`: the gutter is MM7 slime water now, a dark green-blue channel, where the no-dungeon picture was a
  bright yellow-green slime.
- `27-cistern-bug-tanks`: the tanks are flat teal panels of liquid, not glass; better than house windows, still a
  stand-in.
- `22-cistern-pool`: the floor's sewer block stone is lighter and coarser than MM7's dark slabs; the kerb went to the
  darker footing stone so it still stands out.

### What I was unsure of

- Whether the cellar should go wholly to the sewer's stone (losing the red brick). I kept the brick because the
  cistern's look was to stay; one sewer wall in place of the brick would make the cellar a single shipped set.
- The office's plaster at scale 1.5 (one picture floor to ceiling): coarser texels than the rest of the map, but no
  seam; with a band the cornice would sit at 256 in mid-wall.
- `t66roof` (rope-lashed beams) is d06's storeroom ceiling; the user may read the rope as nautical. `t66floor` planks
  would be the plainer ceiling of the same set.
- The tour's monsters differ between passes (spawns roll), so a few pairs of pictures show different creatures.
- `plan.yml` still names the first pass's library picks in its theme lines (`bwoodb1`, `bmplnk` ...): it is the
  brief, so it was left; `rooms.yml`'s themes are what is built.

### Pictures

`output/studio_cal/xd01/shots3/` (the second pass's 42 cameras, `captions.yml`, `plan.png`, `iso.png`; shapes are
unchanged), `shots3_extra/` (the desk, cabinet, loft chest, invoice crate and stash chest from above and the ladder
close: every kind of chest and the ladder looked at where a player uses them). Trial takes: `shots3_try1/` (first
retexture), `shots3_try2/`, `shots3_prev/`, `shots3_prev2/`. Showing the change best, each beside its `shots2/` twin:
`01-dock-arrival`, `06-bay-crates`, `10-hall-from-barn-doors` (the ship-window loft front gone), `08-office-desk`,
`17-aisle-rules`; `42-outfall-river-grate` shows the sci-fi grate gone.
