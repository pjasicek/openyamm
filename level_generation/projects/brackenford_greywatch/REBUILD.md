# Rebuild, install and inspect

Latest population addition: [seven restored MM6 mage groups](../../creatures/mm6_pmn2/ENGINE_INTEGRATION.md)
near the eastern centaur patrols. Use `level_generation/creatures/mm6_pmn2/play.sh` for the new God snapshot.
Install its custom monster/atlas assets before staging this map in another checkout. The content-only addition
preserves geometry and existing actors; historical checks with fixed 102-actor/11-area counts predate this revision.

Latest outdoor content: [road-purpose revision](ROAD_PURPOSE_REVISION.md), with fresh God snapshot
`/tmp/openyamm-brackenford-playtest-offroad`. Check source using
`check_frontage.py --source --review-directory road_purpose_revision`. After export run
`check_frontage.py --review-directory road_purpose_revision` and
`check_facade_revision.py --review-directory road_purpose_revision`.
`review_road_purpose_blender.py` rebuilds the automap and two focused wilderness views in one MCP import.
Earlier revision checks/reports retain their original baselines and should not be treated as current-layout tests.

**Content-only work uses visual review and quick native checks.** The extended functional commands below are
optional diagnostics, not default gates. Reuse matching built binaries. Compile/test tools only when their
implementation changes or a required binary is missing. Earlier frontage/density/facade evidence is historical.

Commands run from `/home/pjasicek/github/OpenYAMM`. Use this checkout's installed Blender, Python 3 with NumPy,
PyYAML/Pillow/Matplotlib, CMake build and local `assets_dev` MM8/base content. The Blender scripts currently use this
absolute project path. Native content depends on this project's compiler/runtime changes; an older executable is not
qualified. No original artwork is bundled in the content archive.

## Install the delivered archive

This creates an isolated development mount; it does not replace the repository's normal assets. It checks archive
checksums, safe paths, allocated IDs recorded in the package and matching original base-table hashes. The archive's
full registration tables belong only in that matching isolated test base, not in arbitrary production worlds.

```sh
python3 level_generation/projects/brackenford_greywatch/prepare_playtest.py \
  --package level_generation/projects/brackenford_greywatch/dist/brackenford_greywatch_content.zip \
  --directory /tmp/openyamm-brackenford-playtest-new
/tmp/openyamm-brackenford-playtest-new/play.sh outdoor
```

Use `indoor` for the other start. Choose Load Game → Scenario. The preparation copies the current built executable,
creates ordinary starting saves, reloads both using that executable and verifies maps/all five levels. It refuses to
refresh an existing playtest snapshot. Each launcher directory owns its saves/settings. Preserve personal saves before
rebooting if `/tmp` is volatile; use a new snapshot directory when updating content.

## Rebuild from authoring sources

First compile the required shared tools and game:

```sh
cmake --build build --target openyamm -j25
cmake --build build --target openyamm-editor mm9_compile_indoor_source openyamm_indoor_source_tests openyamm_levelgen_inspect_save -j25
build/tools/openyamm_indoor_source_tests
```

The historical `mm9_compile_indoor_source` name refers to the shared native BLV compiler. These maps use MM8 assets.
Run the following Python through Blender MCP `execute_blender_code` on the connected instance (port 9876). It creates
project authoring scenes and writes GLB/OBJ/metadata/markers with stable identities. Do this only when regenerating
geometry; re-running authors replaces their project scenes, so save deliberate manual source edits first.

```python
from pathlib import Path
project = Path('/home/pjasicek/github/OpenYAMM/level_generation/projects/brackenford_greywatch')
for name in ['author_greywatch_blender.py', 'author_brackenford_blender.py']:
    exec(compile((project / name).read_text(), str(project / name), 'exec'), {'__name__': '__main__'})
```

Normalize the isolated library exports into ordinary editable Blender main files, then reopen each independently:

```sh
blender --background level_generation/projects/brackenford_greywatch/source/lg01.blend --python level_generation/projects/brackenford_greywatch/verify_blend.py -- --finalize
blender --background level_generation/projects/brackenford_greywatch/source/lg02.blend --python level_generation/projects/brackenford_greywatch/verify_blend.py -- --finalize
blender --background level_generation/projects/brackenford_greywatch/source/lg01.blend --python level_generation/projects/brackenford_greywatch/verify_blend.py
blender --background level_generation/projects/brackenford_greywatch/source/lg02.blend --python level_generation/projects/brackenford_greywatch/verify_blend.py
```

The first normalization can say “Library file, loading empty scene”; the verifier still requires the complete authored
scene. The subsequent ordinary reopen must have its expected objects, packed images and no external libraries.

Build native geometry, companion gameplay and scoped registrations:

```sh
python3 level_generation/projects/brackenford_greywatch/build_greywatch.py
python3 level_generation/projects/brackenford_greywatch/build_town_content.py
python3 level_generation/projects/brackenford_greywatch/stage_runtime.py
python3 level_generation/projects/brackenford_greywatch/build_brackenford.py
```

Staging before the outdoor build supplies the editor's isolated asset root. The outdoor writer uses a fresh temporary
source package, not a stale existing ODM. The indoor writer derives sectors/portals/BSP/outlines and linear mechanisms.
Builders verify written native arrays, bindings and endpoints. Neither pipeline needs a manual binary patch.

Bake the automap from the written ODM through Blender MCP:

```python
from pathlib import Path
script = Path('/home/pjasicek/github/OpenYAMM/level_generation/projects/brackenford_greywatch/build_minimap_blender.py')
exec(compile(script.read_text(), str(script), 'exec'), {'__name__': '__main__'})
```

Then stage the complete result, verify native fixtures and export:

```sh
python3 level_generation/projects/brackenford_greywatch/stage_runtime.py
python3 level_generation/projects/brackenford_greywatch/verify_outdoor_source.py
python3 level_generation/projects/brackenford_greywatch/content_package.py
```

The archive is `dist/brackenford_greywatch_content.zip`. `content_package.py` refuses stale staged runtime files and
records every file/base-table hash and the tested game binary. `stage_runtime.py --package ARCHIVE --directory NEW_DIR`
installs it without re-running authoring/registration scripts. Source/base changes require regeneration and review.
The generated map sources and Lua remain in this project; the ZIP is the runtime delivery, not an editable source bundle.

## Repeat the relevant functional checks

```sh
python3 level_generation/projects/brackenford_greywatch/run_content_checks.py --report current_content.json
python3 level_generation/projects/brackenford_greywatch/run_content_checks.py --report current_routes.json \
  two_map_arrivals regional_travel regional_approaches stables_travel stable_off_day \
  greywatch_remaining_routes greywatch_combat_lift greywatch_trap_contact
python3 level_generation/projects/brackenford_greywatch/run_content_checks.py --report current_services.json \
  town_teacher_learning town_teacher_eligibility town_training town_safety
python3 level_generation/projects/brackenford_greywatch/verify_chest_rewards.py
python3 level_generation/projects/brackenford_greywatch/verify_reward_persistence.py
python3 level_generation/scripts/validate_references.py
```

`run_content_checks.py` defaults to `/tmp/openyamm-brackenford-greywatch`; `--directory` selects a clean package install.
Reports record native/source/executable hashes. Scenario YAML is preserved beside the builders. Do not revive the old
manual `greywatch_lift_route.yml` as an acceptance gate: automatic floor activation replaced that test's assumptions;
`greywatch_combat_lift.yml` covers the current open-gate route after combat.

Native saved reward/refill and trap snapshots can be inspected with `build/tools/openyamm_levelgen_inspect_save`.
The exact 335/337-day refill fixture is `review/rewards/refill.yml`, using saves from the persistence run. UI shop
captures and saved inventory/stock comparisons live in `review/gameplay/`; prices and random stock are run-specific.
Interactive transaction review must choose a visible valid item, then confirm actual gold, cursor/inventory and stock.
Do not substitute a scenario-only bookkeeping count for native held-item/inventory ownership.

## Visual review

Run `review_brackenford_blender.py` / `review_greywatch_blender.py` through MCP to reimport the written maps and render
native terrain/geometry plus decoration previews. Cutaways use inspection lighting; they do not certify dungeon lighting.
The maps' actual full-ceiling game views are captured through the normal executable:

```sh
xvfb-run -a -s '-screen 0 1600x1200x24' python3 level_generation/projects/brackenford_greywatch/capture_gameplay.py review_town \
  --map lg01.odm --pose -10240 -1536 640 1.5707963267948966 0 --warmup 2 --seconds 3
python3 level_generation/projects/brackenford_greywatch/review_performance.py
```

Use display permissions where required. The performance batch must run serially without concurrent builds/renders/tests.
Inspect all captured gameplay images before accepting its report; menus/defeat screens are not a valid workload.
Indoor native saves currently reset yaw/pitch on load; use `--look-left` and `--look-down` for actual post-load mouse
orientation. `--party-file` supports controlled Perception comparisons. Torch-off evidence uses an explicitly isolated
on-load diagnostic, not a runtime feature or delivered script override. Repeat affected visual/functional checks after
changes, then prepare a new frozen snapshot with `prepare_playtest.py`.
