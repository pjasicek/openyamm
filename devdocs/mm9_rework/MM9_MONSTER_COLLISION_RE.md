# MM9 monster collision size (reverse engineering)

How Might and Magic IX sizes a monster's collision body, from the shipped game code, and what that means for our
MM9 monster table. Research date 2026-10-31, Rizin 0.10.0 and `objdump -M intel` on `mm9/game/data/object.lto`
(SHA-256 `b1271f37…7bc37f162`, the server game code; image base `0x10000000`). Project and full listing:
`re_mm8/work/mm9_collision/` (ignored). Earlier method notes: [render lighting RE](MM9_RENDER_LIGHTING_RE.md).

## The rule

**A monster's body is the axis-aligned box whose half extents are its model's animation dims (the `static_model`
animation, else animation 0) times its scale. Its scale is the `MONSTERS.txt` `Scale` column, unless the DAT object
has its own `Scale` property other than 1.0, which then replaces it (it does not multiply).** No class property, DAT
`Dims` property, table column or hard-coded radius is involved. The game code also keeps a separate actor radius,
`sqrt(x² + z²)` of the box (its half diagonal), for AI distances.

In our units (LT × 2.56): **radius = half width × scale × 2.56, height = 2 × half height × scale × 2.56.**

## Evidence (`object.lto`)

The server interface pointer is `[0x102babe8]`. Its vtable slots `+0x158`/`+0x15c`/`+0x160` are
GetObjectDims/SetObjectDims/SetObjectDims2 and `+0x17c` is GetModelAnimUserDims(hObj, &dims, hAnim) (the order of the
LithTech server headers). Its function-pointer members `+0x1a8`/`+0x1ac` are ScaleObject/GetObjectScale and `+0x1a0`
is GetObjectPos. The Actor base vtable is `0x100ee198`. All 288 actor class vtables (found by their `+0x3a0` slot
`0x10001bf0`) carry the same dims slots below, Terrors included.

| Address | Vtable slot | What it does |
| --- | --- | --- |
| `0x1000cdf0` | — | Actor setup. Reads the `Scale` property (default 1.0) and the monster record's scale (`[this+0xb54]+0x84`). If the property is 1.0 it uses the record's scale, otherwise the property's. Calls SetScale with it, then `0x10001dc0`. |
| `0x10042e14…` | — | `data\monsters.txt` loader. Reads columns by spreadsheet letter. Column `BG` (59th, `Scale`) goes to record `+0x57c`, and the record pointer the actor keeps is `+0x4f8`, so `+0x84` is `Scale`. |
| `0x10005ce0` | `+0x20` | Actor::SetScale: ScaleObject, then actor radius `[this+0x484] = sqrt(dims.x² + dims.z²)`. |
| `0x10001dc0` → `0x100be860` → `0x100bc710` | — | Property read, then initial update. The base skips its own `Scale` read for actors (slot `+0x64` = `0x100018c0` returns 1), and the initial update first calls slot `+0x60`. |
| `0x10003450` | `+0x60` | Actor InitDims: calls `0x100bd8d0`, then recomputes `[this+0x484]` as above. |
| `0x100bd8d0` | (base `+0x60`) | For a model object: looks up the animation `STATIC_MODEL` (`0x1019bfe0`), or 0 if there is none. Calls GetModelAnimUserDims on it, then slot `+0x38` with those dims. |
| `0x10002050` | `+0x38` | Actor SetDims: dims = GetObjectScale × given dims. If they differ by more than 0.5 from the current dims, SetObjectDims2. When the height shrinks, the position is moved so the feet stay on the floor. |
| `0x100bd460` | `+0x4c` | Base SetAnimation(hAnim, loop, setDims, keepFeet). With `setDims`, it calls GetModelAnimUserDims(new anim) and slot `+0x3c` (`0x100bd2a0`: scaled the same way, through the physics interface SetObjectDims). So bodies can follow per-animation dims. |
| `0x10002580` | — | Animation keyframe commands `Dims x y z` / `DeadDims` (slots `+0x3b0`/`+0x3b4`): a value ≥ 1 sets that dim, < 1 scales it, 0 keeps it. `Terror.abc` has no such keys. |

The engine treats the object dims as the half extents of the collision box. This comes from the LithTech reference
source (`mm9/lithtech/runtime/shared/src/collision.cpp`, `world/src/de_objects.h`); it is not traced in
`lithtech.exe`. The box does not rotate with the monster: its half width is 25 LT along the axes and 35.4 LT on the
diagonal.

Not traced: whether the AI's animation calls pass `setDims`. This makes no difference for the Terror, whose 15
animations (and AnimBindings) all have (25, 50, 25). 28 of the scanned rows have models whose animations differ;
the scan uses `static_model`/anim 0, as the initial dims do.

## The Terrors

All three rows use `models\Terror.abc` (`static_model` (25, 50, 25) LT) and `MONSTERS.txt` Scale 1.0. The earlier
converter check found DAT `Scale` 1 on every Terror object; it was not repeated here.

| Row | MM9 | Ours now (H / R / ToHit) | MM9 rule (H / R) |
| --- | --- | --- | --- |
| 9237 | Amphibious Terror | 256 / 160 / 160 | **256 / 64** |
| 9238 | Desert Terror | 256 / 175 / 175 | **256 / 64** |
| 9239 | Reptilian Terror | 256 / 190 / 190 | **256 / 64** |

The three variants are the same size. MM9's AI radius (the half diagonal) is 90. Radius 64 (128 wide) fits the
246-wide bottom doorway of the stair. It is also not squat (256 > 2 × 64), and the pathing harness passes every
step at radius 80 (see [Spiral stair pathing](SPIRAL_STAIR_PATHING.md)).

## Other rows (quick scan)

[`mm9_monster_collision_scan.py`](mm9_monster_collision_scan.py) covers all 158 MM9 table rows that have a model;
the result is in [`mm9_monster_collision_scan.tsv`](mm9_monster_collision_scan.tsv). The descriptor rows are
copied whole from MM6–MM8 stand-ins (`generate_mm9_monster_tables.py`), so most bodies are wrong:

- 107 of the 158 rows are at least 1.5 times MM9's radius; 37 rows are over by 60 or more. Only 27 rows are within
  25 %.
- Worst oversize (our R → MM9 R): Gezzampt Elder 180 → 51 (and height 450 → 256), the Terrors, the Jelly/Gelatinous/
  Nettle Spores 144–153 → 41, Oculus/Orbus/Eye 144–153 → 51, Imps 125 → 26, Lobbers 112 → 38, Gezzampt 140 → 51,
  Ebora/Concubine 120 → 38, Winged Mutants 120 → 46, Plain/Forest Giant 233 → 154 (height 650 → 845), the Birds,
  Flying Ickies, Thralls 100 → 31 and Liches 79 → 31.
- Undersize: Dragon King 300 / 400 → 512 / 1700. Sea Monster Male and Female 60 → 192 and 230. Colloidal Soldier,
  Warrior and Guardian 63 → 134, 157 and 179 (Scale 1.5–2.0; heights 177 → 307–410). Magreebs 60 → 77–134. Nagate
  Elder 109 → 138.
- Height only: Yanmir 650 → 957; Shadow/Apparition/Specter 128 → 295; Greater Demon 179 → 343.

Placed actors keep the radius and height baked into the map at conversion time (`content.monster_bases` reads the
descriptor). Summoned and spawned monsters take the table's values. Seven converters already override placed actors
with the ABC extents (`mm9_extents()` in Dark Passageway, Dook's Castle, Training Hall, Yanmir's Fort, Thjorad Mine,
Dragon Stadium and Connecting Tunnels; Dark Passageway's Terrors are already 64). Those helpers *multiply* the table
Scale by the DAT Scale. MM9 *replaces* the table Scale with a DAT Scale other than 1, so a row with both would come
out too large.
Both are fixed: see [Applied](#applied-2026-10-31).

## Applied (2026-10-31)

### The table
All 158 MM9 rows of `worlds/mm9/data_tables/monster_descriptors.txt` now carry MM9's body by the rule above (Radius
changed on 158 rows, Height on 155, ToHitRadius on 6). ToHitRadius is 0 on every row: the engine then uses the actor's
own radius for projectile hits, which also follows a placed actor's DAT Scale (MM9 has no separate hit radius).

| | Row | Ours before (H / R) | MM9 (H / R) |
| --- | --- | --- | --- |
| Shrinks most | Gezzampt Elder 9173 | 450 / 180 | 256 / 51 |
| | Reptilian, Desert, Amphibious Terror 9239-9237 | 256 / 190, 175, 160 | 256 / 64 |
| | Nettle, Gelatinous, Jellyspore 9170-9168 | 267 / 153-144 | 133 / 41 |
| | Bird (1.5) 9095 | 240 / 140 | 61 / 31 |
| | Imply, Imp, Imp Elder 9078-9080 | 200 / 125 | 123 / 26 |
| Grows most | Dragon King 9212 | 400 / 300 | 1700 / 512 |
| | Sea Monster Female, Male 9178, 9177 | 160 / 60 | 215 / 230, 179 / 192 |
| | Colloidal Guardian, Warrior, Soldier 9236-9234 | 177 / 63 | 410 / 179, 358 / 157, 307 / 134 |
| | Armored Magreeb, Magreeb 9278, 9277 | 220 / 60 | 314 / 134, 269 / 115 |

Hand checks with the full ABC reader (`convert_abc_model.read_abc`, `static_model` binding, `MONSTERS.txt` column
BG): Terror, Dragon King, Colloidal Guardian, Armored Magreeb, Gezzampt Elder, Sea Monster Male, Imply and Lobber Pod
match the scan. The models' only `Dims` keyframe commands are `DeadDims` (corpses), so no living body changes with
an animation. No row was left out: every one has a shipped model. Approximations: the round body takes the larger
horizontal half extent (cow.abc 15 x 35 LT: radius 90; fish, goose and The Great Honk likewise), and the mouse rows are
8 x 5.

### Surviving a regeneration
- `tools/mm9_import_discovery/mm9_monster_bodies.py`: the rule (`initial_half_extents`, `effective_scale`,
  `native_body`, `Mm9MonsterBodies`); `--write-overrides` writes `mm9_monster_body_overrides.tsv` (158 rows, each
  naming its model, animation, half extents and Scale). It reads `MODELS/` only: `PROPS/MUMMY.abc` and
  `SAVE/SKELETON.abc` would shadow the monster models (the old converters' `rglob` picked them up).
  Deliberate exceptions (2026-11-02, the user's "Refresh all" over every NPC row): where the sizing animation's box lies
  on its side, `SIZING_ANIMATION_OVERRIDES` sizes SVEN.abc by his standing `Sven` animation (218 / 38 at Scale 1.25),
  and `BODY_EXCEPTIONS` gives the children their measured bodies (boys 69/70/73: 133 / 26, girls 71/72/74: 130 / 21;
  their only animation's (128, 16, 16) box gives 82 / 328). The file now has 214 rows (the NPC rows of
  `mm9_npc_actor_rows.tsv` included).
- `generate_mm9_monster_tables.py` applies that file after copying the stand-in descriptor rows (`--body-overrides`,
  default the file above; a separate hook, `read_body_overrides` / `apply_body_overrides`; an override naming a row
  the generator does not write fails). A regeneration reproduces the installed tables byte for byte.
- Tests (`test_generate_mm9_monster_tables.py`, 3 new): override columns and empty cells, the replace-not-multiply
  scale and the round body, and a regeneration from the repository's inputs that must give the Terror 256 / 64, the
  Dragon King 1700 / 512 and the Gezzampt Elder 256 / 51.
- Installed by temp file + rename into `assets_dev`; the review root's copy was relinked to the new file (under
  `review_tables.lock`). The other hard-linked stages (`lightmap_transfer_stage/{linear,display}`,
  `geometry_audit/e_fix/frozen_root`, `textures_x4_runs/mm9-native`) keep the old file on purpose.
- The superseded `mm9_terror_collision.patch` and the proposal TSV in this folder were removed.

### Placed actors
- **Drawn size (2026-11-06).** The engine draws a 3D actor at its binding's scale times its height over its
  descriptor's (`WorldFxSystem::syncActorModels`, since 1.2), so an MM9 body that differs from the descriptor
  rescaled the model (Sturmford's townsfolk at 2/3, Thjorgard's dwarves at 1.5x). A scene actor's `draw_scale`
  (`MapDeltaActor::drawScale`, saved from version 157; outdoor `MapActorState::drawScale`) replaces that ratio: the
  model's scale against its binding's, which is 100 x the row's `Scale`. The converters write it as the placement's
  DAT Scale over its row's Scale (the DAT Scale replaces the row's, as above), so the body stays MM9's for collision
  and the AI while the model is drawn at MM9's size. Without it the model follows the height as before.
- One shared helper, `level_generation/projects/mm9r_common/dungeon/bodies.py`: `placed_body(monster_id,
  properties)` returns `{}` at DAT Scale 1 (the row's body applies) and otherwise the row's model at the DAT Scale,
  which **replaces** the row's Scale. The playbook's "Package change: MM9's monster bodies" has the details.
- Converted: Anskram Keep (GiantImp 2, the bust-out Nagates and Ickies 0.7, before unscaled), Beethoven (37 Bone
  Thrashers at 1.001 on the 0.5 row: full size, 179 / 38, not half; Lobber Pod A gets its own body, not the Scale
  2 pod's), Connecting Tunnels, Dark Passageway, Dook's Castle, Dragon Stadium, Drangheim Prison (11 Nagates at
  0.75-1.1, before at the row's Scale), Inventa Storca (by row, not by the DAT `Filename`, which ignored the row's
  Scale at DAT Scale 1), Lich Lab (Lich Kings at 1.2 on a 1.35 row: 184 / 37, not 211 / 95), the Ruined Temple's Genie
  (0.94 on the 1.75 Colloidal Warrior row: 193 / 84), Thjorad Mine (a Troglodyte at 1.8 on a 0.8 row: 212 / 69), the
  Training Hall and Yanmir's Fort. Their `mm9_extents()` helpers are gone.
- Kept as they are (their own constants already give MM9's body at row Scale 1, multiplied by the DAT Scale, which
  for a row at Scale 1 is the same rule): Bathhouse, Klusos House, Lindisfarne Monastery, Ta'Sar Academy (cows by
  their mean half width, 64), The Arena, Verhoffin Ruins, Hall of the Gods (its Great Honk is 123 / 38: goose.abc's half width
  10 at its DAT Scale 1.5, as MM9 ships no TheGreatHonk.abc; the row's rule takes the larger half extent, 58: not
  changed, the model is unknown), the
  Dungeon of Secrets (Chadwick, an NPC).
- The body follows the row's model, not the DAT `Filename` (242 placed objects name another model there, many
  impossibly). Lich Lab `--plan --scratch` is identical before and after; each converted hook was run to its actors
  stage into a scratch folder (nothing installed) and gives the rule's bodies.

### Which maps need a rebuild
Placed actors keep the body baked into the scene, so only a rebuild (or a re-import) gives them the new sizes.
Summoned and spawned monsters (`evt.SummonMonsters`, `spawn_actor`) use the table already. Per map, the placed MM9
actors of the review-root scene against what the current `convert.py` gives (its actors stage) or, for maps whose
hook keeps the row's body, the new row:

| Rebuild (`convert.py`) | Placed actors that change |
| --- | --- |
| `1000terrors` | 114 of 114 (13 Terrors 160-190 -> 64; Oculus/Orbus/Eye 144-153 -> 51; Ickies 115 -> 31; Lesser Demons 179 -> 261 tall; Sea Monsters 60 -> 192) |
| `chasmofthedead` | 171 of 171 (skeletons, mummies, zombies 60-72 -> 31-38; Imp Elders 125 -> 26) |
| `lichlab` | 147 of 147 |
| `beethoven` | 84 of 84 |
| `anskramkeep` | 47 of 47 |
| `drangheimprison` | 35 of 74 (guards, the Nagates with their own DAT Scale, the animals) |
| `templeofhonk` | 18 of 18 (Honks 74 -> 31) |
| `inventastorca` | 17 of 39 |
| `thjoradmine` | 7 of 83 (the Scale 1.8 Troglodyte, Ebora, five cats) |
| `ruinedtemple` | 1 of 15 (the Genie, 63 / 177 -> 84 / 193) |

No change on a rebuild (their bodies were MM9's already; the converted hooks give the same values): bathhouse,
connectingtunnels, darkpassageway, dookscastle, dragonstadium, dungeonofsecrets, hallofthegods, klusoshouse,
lindisfarnemonastery, tasaracademy, thearena, traininghall, verhoffinruins, yanmirsfort. `isleofashes` is not built
in the review root yet; its hook keeps the row's body, so it gets the new sizes when it is built.

Old-importer maps (`regenerate_mm9_maps.sh`, outside the dungeon rebuild) whose placed MM9 actors carry the old
stand-in bodies: arslegardcity 1, drangheim 32, drangheimcity 1, guberland 40, lindisfarne 42, mountainpass 76,
sturmford 56, thjorgard 38, thronheimcity 3 (its Desert Terror), wizardslab 58, yorwick 48. That importer also
ignores the DAT Scale (open).

### Consequences (checked without rebuilding)
Tools and per-actor results: [`mm9_monster_body_check/`](mm9_monster_body_check/) (`actors_only.py` runs a
converter to its actors stage; `body_check.py` applies the walkability audit's actor test, `check_walkability.py`
`actor_findings`, to old and new bodies on the review-root BLV, and walks a radius-clearance field over the floor cells
from each actor to the party start; `results.tsv`).
- **No placed actor gets a new fit problem** (wall within its radius, ceiling under its height, overhang) on any of
  the 18 built maps checked. The growing bodies (Sea Monsters 192, Lesser and Greater Demons 261 and 343 tall, the
  Genie, the Scale 1.8 Troglodyte) all fit where they stand. 86 actors lose an old finding (mostly a wall inside
  their old radius). The Dragon King (Dragon Stadium) and the Colloidals (Bathhouse) already had MM9's bodies.
- **Newly reach the party start through gaps that were too narrow** (approximate: doors counted open, 16-unit cells):
  Thousand Terrors 2 Terrors; Anskram Keep 19 (Imps, Nagate Hatchlings); Chasm of the Dead 7 Imp Elders; Lich Lab 3
  Lich Kings and a Skeleton Master; Temple of Honk 16 Honks. None loses a way it had.
- Headless on the review root (new table, maps not rebuilt; `mm9_monster_body_check/*.yml|.log`): a spawned Desert
  Terror (9238, 64 x 256) at the Thousand Terrors' stair foot enters the 246-wide doorway and climbs the spiral well to
  the landing in about 12 s (at 175 it never entered the well); a spawned Sea Monster (9177, 192 x 179) at the crypt
  lake stands clear of the walls and attacks a party 495 away.
- No placement fix is needed. Pre-existing findings that stay (not from this change): Lich Lab's wall-hung Oculi and
  caged Skeleton Masters, Thousand Terrors' Njam (hidden, under a 1-unit ceiling) and two Oculi, Beethoven's Lobbers on
  a ledge edge, Drangheim's cat and rooster with no floor under them and one guard against a wall.

### Combat
Monster melee starts at an edge gap of 307 (actor-target distance minus the monster's radius, indoors also the party's)
and the party's melee reaches 407 plus the monster's radius, so a monster shrunk by d must come d closer and the party
must stand d closer to hit it: Terrors about 100-125, Gezzampt Elder 129, Spores and Eyes about 100; the Dragon King,
Sea Monsters and Colloidals hit and are hit from 70-212 farther. Projectiles now hit the body's own radius (ToHitRadius
0): the Terrors' 160-190 hit radius is 64.

### Open
- The engine has no per-actor draw scale: an actor with its own DAT Scale gets MM9's body but is drawn at its row's
  size (Beethoven's full-size Bone Thrashers drawn half size; Dook's Scale 0.3 Basilisks drawn full size).
- Sprite stand-ins (rows without a 3D model: Colloidals, Giants, Yanmir, Greater Demon) now have MM9's bodies under
  MM6-MM8 sprites of other sizes.
- The old importer (outdoor maps) writes the row's body and ignores the DAT Scale.
- Hall of the Gods' Great Honk (no shipped model) keeps its own 123 / 38.
