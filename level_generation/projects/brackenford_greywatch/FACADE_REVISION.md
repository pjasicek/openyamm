# Outdoor facade and variety revision — 2026-09-07

Brackenford (`lg01.odm`, the outdoor half of the Greywatch project) now uses the calibrated house vocabulary.
The [driver feedback](../../VISUAL_CALIBRATION.md) and [measured variety](../../HOUSE_VARIETY.md) guide this revision.

## Play

```sh
/tmp/openyamm-brackenford-playtest-calibrated/play.sh outdoor
```

Choose **Load Game → Scenario** for the built-in God level-100 Lich with Grandmaster-200 skills and all spells.
The `indoor` launcher also has a fresh God start. The previous `playtest-final` directory and its personal saves remain
available; use the **calibrated** launcher for these changes. The new snapshot has copied content/executable and separate
saves/settings. Original art is shared from the checkout. Both new starting saves were loaded and their map/level checked.

## Changes and visual review

- Rebuilt all 24 house/service facades with **128×256 door panels**, replacing the previous 256×512 doors.
  Coherent `t14a/b/c` wall, window, door and corner panels use one game unit per texel. No boat doors or crate windows.
- Replaced oversized generic masses with compact gabled, hipped, plain-roof and chamfered/turret houses. Inns, the
  civic hall and temple expand through larger bodies, roof levels and towers while retaining ordinary entrance scale.
  Chimneys were removed. The final close-up review also corrected foundation corners projecting beyond chamfered walls.
- Added native service signs above/right of relevant shop doors. Weapon and armor shops form **Smiths Row** under one
  continuous roof, with separate event faces, house IDs and signs. The original service and resident identities remain.
- Matched repetition to the reference: **15 ordinary residence/teacher/storage instances across five forms** (3.0 each),
  versus Ravenshore's **44 across 13** (3.38). Including services, there are 23 physical buildings/blocks across 10 forms,
  versus Ravenshore's 51 across 20. Rotations and BModel partitions do not count as extra forms.
- Moved the well from `[-8704,1792]` to **`[-8704,2560,704]`**, in a planted pocket beside the roads. Its complete native
  256×256 footprint plus 128 units of clearance excludes road cells. Building approaches/roads were regenerated for
  the revised footprints; the native terrain retains the river, bridge, shelves, screened approaches and existing tiles.
- Regenerated grounded decoration placements around the changed buildings/paths: 264 trees, 216 plants, 72 rocks and
  11 props. Actor/chest counts, dungeon approaches, service logic, regional links and the indoor map remain intact.

![Revised magic shop in the actual game](review/gameplay/calibrated_magic.png)

![Weapon and armor shops with separate entrances in the actual game](review/gameplay/calibrated_smiths.png)

These are ordinary native game views at configured eye height; screenshot preparation only creates a viewpoint save.
The captures use no interaction/transaction suite and no timed performance measurement. The following Blender views
reimport the written ODM with neutral inspection lighting and native texture UVs:

![Revised town and streets](review/brackenford_native_calibrated_town.png)

![Well beside clear streets](review/brackenford_native_calibrated_well.png)

[Magic shop close-up](review/brackenford_native_calibrated_magic.png) ·
[Joined shops](review/brackenford_native_calibrated_shops.png) ·
[Temple](review/brackenford_native_calibrated_temple.png)

The images were opened and inspected: coherent facade bands, correctly scaled doors/windows, readable signs, distinct
roof silhouettes, terrain contact and an unobstructed route around the well. The town remains a spacious original layout;
matching a reference's form ratio does not claim an exact copy of its street density or composition. Final aesthetic and
combat tuning remain subject to driver feedback. No new runtime/compiler behavior was introduced.

## Quick verification and artifacts

[Quick native check](review/facade_revision/quick_check.json) passes in under a second: all 24 door dimensions/materials,
stable event/BModel identities, house targets, texture resolution, exact source/native terrain arrays, arrivals and well
road clearance. The native builder also verifies every exported interaction and decoration record. Native output is
**75 BModels / 2,596 faces**, with 43 actors, four outdoor chests, five loose items and 563 decorations.

The new door/window panels increase face count from the rejected generic box build; no performance comparison was
requested or run. Source remains low-poly, with flat textured faces and ordinary native ODM terrain. Existing gameplay
behavior is reused; exhaustive service, combat, refill, travel and performance scenarios were deliberately not repeated.
The indoor BLV is byte-identical to the earlier delivered dungeon.

- [Editable outdoor source](source/lg01.blend), with packed textures and no linked libraries.
- [House kit implementation](brackenford_house_kit.py), [authoring script](author_brackenford_blender.py),
  [plan](outdoor_plan.json), [semantic bindings](source/lg01.semantic.json).
- [Content ZIP](dist/brackenford_greywatch_content.zip) and its [manifest](dist/brackenford_greywatch_content.manifest.json).
- [Variety membership/counts](review/facade_revision/house_variety.json), [native build](brackenford_build.json),
  [snapshot manifest](review/facade_revision/playtest_snapshot.json).
- [Rejected baseline town](review/facade_revision/before/brackenford_native_town.png); baseline source/native files
  are retained in the same directory so earlier calibration measurements remain reproducible.

## Rebuild this revision

Use Blender MCP to execute `author_brackenford_blender.py`, preserving/restoring the caller's active scene. It replaces
only its **Brackenford calibrated authoring** scene; the previous authoring scene remains available for comparison.
The helper `review_house_prototypes.py` renders small examples before a full rebuild. It is a visual aid, not an export.

```sh
python3 level_generation/projects/brackenford_greywatch/build_town_content.py
python3 level_generation/projects/brackenford_greywatch/stage_runtime.py
python3 level_generation/projects/brackenford_greywatch/build_brackenford.py
python3 level_generation/projects/brackenford_greywatch/check_facade_revision.py
```

Bake the updated minimap using `build_minimap_blender.py` through MCP, then stage and export with `stage_runtime.py`
and `content_package.py`. Use `verify_blend.py --finalize` on the isolated Blender library export as described in
[REBUILD.md](REBUILD.md). Review native views after changed geometry; no game/editor compile is needed for content edits
when the required matching binaries already exist.

`prepare_playtest.py --package ARCHIVE --directory NEW_DIRECTORY --god-source-save SAVE` preserves the built-in God
character from a save created **before visiting these generated maps**, positions it at each declared arrival and saves
fresh starts. The provided seed was captured on original `out01.odm` through normal New Game. Do not reuse an old outdoor
map-state save as the fresh-start seed after changing its geometry. Omit the option for the ordinary level-25 fixture.

## Later layout revision

The driver accepted this house art and requested closer spacing. [DENSITY_REVISION.md](DENSITY_REVISION.md) preserves the
kit while regrouping the town, roads and population. The calibrated snapshot described above remains a historical version.
