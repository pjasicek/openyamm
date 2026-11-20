# MM6 ship replacements

The accepted New Sorpigal Ravenshore ship, extended to all **12 boats on seven MM6 outdoor maps**.
Eleven retain their original travel service; Free Haven's second boat remains scenery.
Installed into the normal `assets_dev/worlds/mm6` asset root on 2026-09-29 after user approval, including all seven
lighting files and bake recipes. All 52 installed files match the tested overlay. Saves and Lua remain unchanged.
The original maps are preserved under `source/original_maps` for reproducible builds.

[Native screenshot gallery](index.html) · [Validation record](review/validation.json) ·
[52-file overlay](build/mm6_ships_overlay.zip) · [Installation receipt](review/installation.json)

## Play

The normal game now uses these ships. For the retained isolated review launcher, run from the repository root:

```sh
./level_generation/projects/mm6_ship_replacements/run_test.sh --list
./level_generation/projects/mm6_ship_replacements/run_test.sh outd3
./level_generation/projects/mm6_ship_replacements/run_test.sh outd3 --boat 2
```

The launcher starts a fresh isolated game at the selected pier and stays open until closed. Walk through the
ship's opening, then use the cabin door. It accepts the usual `tools/run_game.sh --isolated` options, such as
`--seconds 20`. Existing travel schedules still apply. Ordinary E nearby-target selection is unchanged.

| Map | Location | Boat 1 | Boat 2 |
| --- | --- | --- | --- |
| `outc2` | Free Haven | Windrunner | Offshore scenery, no service |
| `outd1` | Silver Cove | Barracuda | Cerulean Skies |
| `outd2` | Bootleg Bay | Valkyrie | Tsunami |
| `outd3` | Castle Ironfist | Zephyr | Queen Catherine |
| `oute1` | Eel Infested Waters | Tigershark | Cirrus |
| `oute2` | Misty Islands | Adventure | — |
| `oute3` | New Sorpigal | Odyssey | — |

## Scope and preservation

- Append five native ship BModels per boat, retaining all existing model/face/decoration indices.
- Retire only the old `SHP` billboard slots: empty name, no collision/interaction descriptor, event or initial flag.
  Their slots, positions and facing remain, so unrelated scene identities do not move.
- Bind **only donor model 113, face 42**, the cabin door, to each original ship event. All other imported faces have
  event zero and no clickable flag. The scenery boat has no interactive faces.
- Keep **all Lua files unchanged**. The existing `RegisterEvent` handlers already supply the ship-name topic and
  `EnterHouse` behavior; the new door faces reference them directly. No additional Lua topic or override is needed.
- Preserve the complete original ODM header/terrain, every original BModel record (including opaque bytes),
  decoration spatial tables, spawns and trailing data. Preserve unrelated entities and every original scene record,
  including actors, items, chests, variables, environment and face attributes. The scene editor preserves original
  text formatting and adds only the new face records plus the retired billboard field changes.
- Leave piers, terrain, buildings, NPCs, monsters, quests, map keys, travel arrival anchors and timetables unchanged.
- Import the same 12 uniquely named ship textures once, shared by all seven maps. The x2 PNGs are existing MM8 art.
  Two logical BMPs are derived from their x2 source because no native BMP is present, as in the prototype.
- Refresh each changed map's lighting and bake recipe using its existing lighting profile. These are derived assets
  required by the geometry/dependency hash; the added ships cast their normal baked shadows.

There is no engine change, runtime placement/import code, migration or new per-frame logic. The ships incur ordinary
static geometry/rendering/collision costs: five BModels and 279 native polygon records per boat.

## Placement

The source is MM8 Ravenshore `out02.odm`, BModels 111–115, pivot `[8256, -14286, 0]`. Native vertices, UVs and the
invisible boarding ramp are retained. Exact quarter turns handle the four pier directions without rounding drift.
The entrance opening is centered on each existing pier's end. Heights preserve the accepted relationship to the
Ravenshore pier: ship Z = local pier floor minus 264. Local pier floors are 160, 176 or 192, placing the main deck
72 units below the pier. The scenery ship keeps its original offshore XY position and matches Windrunner's waterline.

The five covered, coplanar donor surfaces suppressed in the accepted prototype remain invisible and untouchable;
their face slots are retained. The native boarding ramp remains invisible **and collidable**.

See [ships.json](source/ships.json) for every measured pier face, boarding edge, transform, event, house and source hash.
[The import report](build/report.json) records preservation checks and resulting map hashes.

## Build and delivery

```sh
python3 level_generation/projects/mm6_ship_replacements/build.py
/snap/bin/blender --background --factory-startup --python-exit-code 1 \
  --python level_generation/projects/mm6_ship_replacements/source/bake_all.py
python3 level_generation/projects/mm6_ship_replacements/build.py --install-lighting
python3 level_generation/projects/mm6_ship_replacements/run_checks.py
python3 level_generation/projects/mm6_ship_replacements/build.py --package
```

The builder reads its explicitly configured `base_maps_root` (`source/original_maps`) and pins those original maps,
scenes and lighting profiles, plus the unchanged runtime Lua and MM8 donor. It uses the engine's native reader/writer for
new BModels, then appends those records while retaining the original binary sections verbatim. It reopens the final
files through both the native reader and the independent Python parser and compares all unaffected records.
Running the builder invalidates the isolated lighting; repeat baking/install before playing or packaging.

- [Changed-assets overlay](build/mm6_ships_overlay.zip): 52 files relative to an asset root: seven ODMs, scenes,
  lighting files and bake recipes, plus 12 logical BMPs and 12 x2 PNGs. No Lua or shared tables are included.
- [Package manifest](build/package.json): per-file checksums and archive checksum.
- [Packed Blender source](source/mm6_ships_and_piers.blend): 12 editable scenes reimported from the delivered ODMs,
  including unchanged piers and packed textures. This inspection view omits terrain, billboards and invisible faces;
  the native collision ramps and retained hidden face slots remain in the ODMs. Rebuild this authoring view with
  `source/reimport_blender.py` through Blender MCP; JSON/C++/Python remain the reproducible map source.
- `playtest/assets_dev`: complete isolated asset snapshot. Unchanged files are hardlinks. **Do not edit shared files
  here in place**; the builder atomically replaces the changed entries.
- [Boarding/door results](review/checks.json), native captures in `review/out*/`, and `review/validation.json`.

The overlay contains paths relative to an asset root; it is not a self-contained world ZIP or an automatically mounted mod.
Its approved contents are installed in the normal development asset root. Existing release ZIPs are separate build outputs
and were not repackaged. Native checks use fresh isolated state; existing saves were not edited and no migration is included.
