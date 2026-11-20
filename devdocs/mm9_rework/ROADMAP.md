# MM9 rework: what is left

Everything still to do, pinned down from the user's list of 2026-10-30. Decisions are in [PLAN.md](PLAN.md), the day-to-day
state in [STATUS.md](STATUS.md). Items marked **proposal** are recommendations that still need the user's yes.

## Compute-heavy production

| Work | Done | Left | Run how |
| --- | --- | --- | --- |
| 3D monsters | 19 bodies, 12 animals, Imp; Lich, Skeleton Warrior and Honk (2) running | 28 monster bodies | [overnight session](OVERNIGHT_MONSTERS.md) |
| Town NPCs and unique characters | Annud, Forad, Yrsa | 38 town NPC bodies, 16 unique characters, Magic Mine | after the monsters, same route |
| Dungeons (BLV) | 6 of 25 | 19 | [overnight session](OVERNIGHT_DUNGEONS.md), no supervision needed |
| Outdoor maps (ODM) | Isle of Ashes pilot | 19 of 20 | with the user: passable and impassable areas need calibration |

## Texture passes (Codex, last)

- **Wall, floor and ceiling textures at 4×:** done 2026-11-02 (1 002 accepted, 44 out of scope),
  [surface texture playbook](../../level_generation/textures_x4/PLAYBOOK.md). A map that gains new textures later runs
  `tex.py inventory --world mm9` and the usual loop for the new ones only.
- **Decoration and prop textures at 4×:** a separate Codex batch, because the playbook excludes decorations today. Prop skins are
  plain Lanczos ×4 until then (a few Beethoven ones are Real-ESRGAN; they get replaced too).

## Content and engine features

### 3D items on the ground
Volumetric items follow the [3D ground item playbook](../../level_generation/props/items_claude/GROUND_ITEM_3D_PLAYBOOK.md):
Codex master, Meshy Smart Topology, Codex-painted views. The per-icon relief models were rolled back on 2026-10-16.

### Item balance: MM6–MM8 style, not MM9's
The user: items should follow the MM6–MM8 style; MM9's cannot be mixed in as they are.
**Superseded by [BALANCE_PLAN.md](BALANCE_PLAN.md) (2026-11-05)**, which covers items together with monsters, loot,
shops and density; the proposal below is kept for history. There are 390 MM9 item definitions in
`assets_dev/worlds/mm9/data_tables/items.txt`, on top of the merged tables.

**Proposal, in order:**
1. A one-table audit: every MM9 item against the nearest MM6–MM8 item family and value band (damage dice, armour class, value,
   bonuses), with MM9-only mechanics flagged.
2. Rewrite each MM9 item's stats to its family's band, keeping its name, art and quest role. Most of this is scripted from the table.
3. Hand-balance artifacts, quest items and MM9-only effects, with the user.
4. Vendors and loot tables follow, with the higher monster density in mind (plan, "Balance calibration").

### MM9 character portraits and paperdolls
Sources: 20 PC portrait sets in `mm9/extracted/ART/ART/PCPORTRAITS` and 15 NPC sets in `NPCPORTRAITS`. Portraits should go in at 2× or better.
Done 2026-11-06: all 20 PC portrait families and their paperdolls (heads grafted onto existing doll bodies) are
installed as `character_data.txt` rows 9001–9024, and the 15 hireling families as `worlds/mm9/icons_x2/9npcNN-`
([portrait playbook](../../level_generation/ui/hud_inventory/mm9_pc_portraits/PLAYBOOK.md),
[paperdolls](../../level_generation/ui/hud_inventory/mm9_pc_dolls/README.md)).

The user does not want a second set of paperdoll equipment variants: the MM9 dolls reuse existing bodies and their armour
overlays, with only the head regenerated (done, see above).

### Diving (engine; PLAN.md "Water and diving")
The user's spec: the party can dive into water and move at about walking speed, going down and up; a progress bar shows the air left;
when it runs out, heavy percentage damage is taken gradually.

Needs: a swim state for the party, seabed plus water surface in the map data, rendering from below the surface, swimmers moving in 3D,
underwater rules for projectiles and spells, seabed items, indoor pools. Write the design proposal first. Waiting on it: the Sea Monster
and fish rebind, Beethoven's Grand Entrance (wading floor, walls shortened by one edit), Chasm's acid, the 1000 Terrors puzzle,
any outdoor map that raises its terrain for water. Do it before most ODMs, because it changes how they are built.

### Destructible brushes (engine)
Not in the engine for MM9 yet: `DestructableBrush` objects are not promoted into scene data, though outdoor code has some destruction support.
Inventory: 261 brushes on 23 maps and 174 destructible props on 10 maps, [goal document](../mm9/MM9_DESTRUCTIBLE_GEOMETRY_GOAL.md), first
slice the Thronheim City prison breakout. A destruction must change rendering, collision, floors, projectiles, picking, line of sight,
navigation and persistence. The user: it needs a sound and an animation. Needed in BLVs as well as ODMs.

### Smaller engine queue (from STATUS.md)
Monsters opening doors; animated creature skins and runtime skin swaps; pulsing indoor lights; outdoor translucent BModels; per-face
visibility for perception hints on translucent faces where maps need it; ambient sounds; door sounds; lava damage; walking NPCs and
followers (Ivsar); the Dragon King's grounded boss script.

## Suggested order

1. Tonight: monsters and dungeons.
2. Diving design, then the engine feature.
3. Destructibles, because the outdoor conversions depend on them.
4. ODMs in story order, with the user calibrating the first two.
5. Town NPCs and characters alongside the cities.
6. Portrait pilot, then the batch.
7. Item audit and balance.
8. 3D ground items.
9. Last: surface and decoration textures at 4×, then bakes and the stale-bake check.

## Risk

`level_generation/` is git-ignored with no repository of its own, so every map project, creature project and brief there exists only on
this disk. Back it up before the machine is rebuilt or the disk changes.
