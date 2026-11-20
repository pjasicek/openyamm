# MM9 OpenYAMM Main-Branch Handoff

This handoff is for moving only the useful MM9 DAT/DTX -> classic OpenYAMM export work onto a main branch that does
not otherwise know about MM9. The target is not MM9 runtime integration. The target is generated MM6-MM8-style
`BLV`/`ODM` maps plus minimal sidecars and generated Lua so the maps can be loaded, inspected, regenerated, and later
finished as normal OpenYAMM content.

## Intended Main-Branch Shape

Carry the generated world package and the exporter/runtime patch, but do not carry the old `game/mm9/*` DAT-world
runtime direction.

Runtime content should be:

- `assets_dev/worlds/mm9_openyamm/world.yml`
- `assets_dev/worlds/mm9_openyamm/maps/*.odm`
- `assets_dev/worlds/mm9_openyamm/maps/*.blv`
- `assets_dev/worlds/mm9_openyamm/maps/*.scene.yml`
- `assets_dev/worlds/mm9_openyamm/events/*.lua`
- `assets_dev/worlds/mm9_openyamm/textures/**`
- `assets_dev/worlds/mm9_openyamm/audio/**`

Development/regeneration sidecars should stay in `assets_dev/worlds/mm9_openyamm/maps/`, but they should not be treated
as required runtime inputs:

- `*.events.yml`
- `*.material_aliases.yml`
- `*.mm9.yml`
- `*.raw_objects.yml`
- `*.model_assets.yml`
- `*.geometry.yml`
- `*.bsp.yml`
- `*.compiled_doors.yml`
- `*.source.glb`

Those files are useful for auditing and rebuilding. The game should load the generated `ODM`/`BLV`, `.scene.yml`, Lua,
textures, and audio.

## Generated Package To Take

Copy the full generated package first:

```sh
assets_dev/worlds/mm9_openyamm/
```

Current generated package shape:

- `17` ODM maps
- `28` BLV maps
- `45` `.scene.yml`
- `45` generated Lua event files
- `45` `.script_ir.yml`
- `1776` exported texture files
- `126` exported audio files

Current ODM maps:

```text
1000terrors.odm
afterworld.odm
arslegardcity.odm
chasmofthedead.odm
drangheim.odm
frosgard.odm
guberland.odm
isleofashes.odm
lindisfarne.odm
mountainpass.odm
sturmford.odm
sturmfordcity.odm
thjorgard.odm
thjorgardcity.odm
thronheim.odm
thronheimcity.odm
yorwick.odm
```

Current BLV maps:

```text
anskramkeep.blv
bathhouse.blv
beethoven.blv
bootcamp.blv
connectingtunnels.blv
darkpassageway.blv
dookscastle.blv
dragonstadium.blv
drangheimcity.blv
drangheimprison.blv
dungeonofsecrets.blv
frosgardcity.blv
greatgate.blv
guberlandcity.blv
hallofthegods.blv
inventastorca.blv
klusoshouse.blv
lichlab.blv
lindisfarnemonastery.blv
ruinedtemple.blv
tasaracademy.blv
templeofhonk.blv
thearena.blv
thjoradmine.blv
traininghall.blv
verhoffinruins.blv
wizardslab.blv
yanmirsfort.blv
```

`world.yml` currently says:

```yaml
id: mm9
name: MM9
sourceGame: mm9
start:
  map: guberland.odm
```

If main already has an `mm9` world id or if the package should be clearly marked as converted content, change the id to
`mm9_openyamm` and update references consistently.

## Patch To Take

Take and apply this patch:

```sh
mm9_openyamm_exporter_runtime.patch
```

The same patch was also refreshed at:

```sh
/tmp/mm9_openyamm_exporter_runtime.patch
```

Apply on main with:

```sh
git apply mm9_openyamm_exporter_runtime.patch
```

The patch currently contains only these files:

```text
game/audio/SoundCatalog.cpp
game/events/EventRuntime.cpp
game/events/EventRuntime.h
game/gameplay/GameplayScreenRuntime.cpp
game/maps/SaveGame.cpp
tools/mm9_import_discovery/generate_mm9_events.py
tools/mm9_import_discovery/regenerate_mm9_maps.sh
tools/mm9_import_discovery/test_dat_bsp_parser.py
tools/mm9_import_discovery/transcode_mm9_dat_to_blv.py
tools/mm9_import_discovery/transcode_mm9_dat_to_odm.py
```

The C++ part is intentionally small:

- Recursive audio indexing and normalized sound-name lookup.
- Lua `evt.PlaySoundName(...)`.
- Lua `evt.SetOutdoorModelMechanismState(...)`.
- Save/load support for pending named sounds.

No broad `game/mm9/*` runtime is required for this plan.

## Exporter Tools To Take

If main already has `tools/mm9_import_discovery/`, apply the patch above and check that these helper files also exist:

```text
tools/mm9_import_discovery/classify_mm9_maps.py
tools/mm9_import_discovery/convert_abc_model.py
tools/mm9_import_discovery/extract_rez.py
tools/mm9_import_discovery/mm9_units.py
```

If main does not have the MM9 import tools at all, copy the whole folder as development tooling:

```sh
tools/mm9_import_discovery/
```

The core current map pipeline is:

```text
tools/mm9_import_discovery/regenerate_mm9_maps.sh
tools/mm9_import_discovery/transcode_mm9_dat_to_odm.py
tools/mm9_import_discovery/transcode_mm9_dat_to_blv.py
tools/mm9_import_discovery/generate_mm9_events.py
tools/mm9_import_discovery/classify_mm9_maps.py
tools/mm9_import_discovery/convert_abc_model.py
tools/mm9_import_discovery/mm9_units.py
tools/mm9_import_discovery/test_dat_bsp_parser.py
```

`transcode_mm9_dat_to_blv.py` currently expects a built indoor source compiler:

```sh
build/tools/mm9_compile_indoor_source
```

If main does not have that tool target, either carry the already-generated `.blv` files and defer regeneration, or port
the indoor source compiler/editor metadata changes that created `mm9_compile_indoor_source`.

## Source Inputs For Regeneration

The generated package is portable, but regeneration still needs extracted MM9 source data. Keep this outside runtime
packages:

```text
mm9/extracted/WORLDS/WORLDS/*.dat
mm9/extracted/TEXTURES/**
mm9/extracted/SOUNDS/**
mm9/extracted/SCRIPTS/SCRIPTS/**
```

The tools assume the local extracted tree by default. After copying the package and tools, the main regeneration command
is:

```sh
tools/mm9_import_discovery/regenerate_mm9_maps.sh --all-classified --world-root assets_dev/worlds/mm9_openyamm
```

Generated Lua idempotency check:

```sh
python3 tools/mm9_import_discovery/generate_mm9_events.py \
  --maps-root assets_dev/worlds/mm9_openyamm/maps \
  --events-root assets_dev/worlds/mm9_openyamm/events \
  --scripts-root mm9/extracted/SCRIPTS/SCRIPTS \
  --check-idempotent
```

## Map Stats

Do not blindly copy `map_stats.txt` without auditing it. The current branch has MM9 rows in:

```text
assets_dev/engine/data_tables/map_stats.txt
```

but it is not currently a clean generated-content source of truth. For example, the package contains
`assets_dev/worlds/mm9_openyamm/maps/1000terrors.odm`, while `map_stats.txt` has a `1000terrors.blv` row.

Recommended main-branch step:

1. Copy only the rows you need for map selection/teleport/travel.
2. Validate every copied map filename against `assets_dev/worlds/mm9_openyamm/maps/`.
3. Keep generated world metadata in `world.yml` and `.scene.yml` authoritative where possible.

Also check whether `assets_editor_dev/engine/data_tables/map_stats.txt` needs the same rows for editor workflows. It did
not show the same MM9 rows in this branch during the handoff check.

## Editor Assets

`assets_editor_dev/worlds/mm9_openyamm/` exists and contains editor-facing copies such as BMP textures. It is useful if
the editor cannot directly consume the dev/runtime package, but it should be considered derived.

Preferred main-branch approach:

- First carry `assets_dev/worlds/mm9_openyamm/`.
- Regenerate or resync editor assets from `assets_dev` if the editor needs them.
- Copy `assets_editor_dev/worlds/mm9_openyamm/` only as a temporary convenience, not as an authoritative source.

## What Not To Take

Do not carry these unless a later task explicitly resurrects MM9-native runtime integration:

- `game/mm9/*`
- old `assets_dev/worlds/mm9/*`
- old `assets_editor_dev/worlds/mm9/*`
- DAT-world runtime docs/plans as implementation instructions
- LithTech reference code

The current direction is a transcoder/exporter path: preserve the useful MM9 level shell, collision, mechanisms, water,
lights, event-face hints, textures, and audio as classic OpenYAMM content.

## Verification After Switching To Main

After applying the patch and copying the package, run:

```sh
python3 tools/mm9_import_discovery/test_dat_bsp_parser.py
python3 tools/mm9_import_discovery/generate_mm9_events.py \
  --maps-root assets_dev/worlds/mm9_openyamm/maps \
  --events-root assets_dev/worlds/mm9_openyamm/events \
  --scripts-root mm9/extracted/SCRIPTS/SCRIPTS \
  --check-idempotent
cmake --build build --target openyamm -j25
```

Expected current results from this branch:

- DAT parser tests: `40` tests OK.
- Generated events: `generated=0 checked=45 validated=45`.
- Missing sound refs: `0`.
- Build target `openyamm`: OK.

If regeneration is run, also verify representative maps:

- `thjorgard.odm`
- `thjorgardcity.odm`
- `darkpassageway.blv`

Check specifically:

- collision faces are not accidentally marked `Untouchable`;
- helper BSPs such as AI tracks and rails are not exported;
- `PhysicsBSP` collision remains collidable;
- water planes render with exported first-frame texture;
- mechanisms have `.scene.yml`/Lua bindings;
- indoor mechanisms compile into BLV doors/elevators where classic data can represent them;
- unsupported rotation behavior is still tracked rather than silently lost.
