# Complete MM6 creature installation — 2026-09-13

## Goblin redo playtest — 2026-09-23

The 59-frame Goblin redo is installed in the normal `assets_dev/engine/sprites_new/mm6_gob/` package for the
requested in-game test. Its previous runtime package is preserved under
`installation_backups/redo_2x_before_install/mm6_gob/`. The native 21 animation groups and 93 frame bindings did
not change. The installation record marks this package `user_playtest_pending_animation_review`: the earlier
static acceptance did not resolve the hit `gobwic0`/`gobwid0` head-height discrepancy or the view-2 walk
`gobwad2`–`gobwaf2` lateral motion discrepancy. The retained front standing pose is an accepted exactly-2×
checkpoint; the other registered poses exceed 2× generated detail. This playtest installation does not promote
the Goblin animation to production acceptance.

The installed files match their recorded hashes, all 60 runtime palette contracts compare to their offline
previews within one RGB byte, and all 15 focused sprite-atlas tests pass. An isolated OpenGL New Sorpigal run
rendered close Goblins, reported 99/99 outdoor actors textured with none missing, and exited cleanly. Its
[engine-native screenshot](runtime_review/mm6_goblin_redo_playtest.png) and
[run record](runtime_review/mm6_goblin_redo_playtest.json) are retained. To test the current installation
interactively near those Goblins:

```sh
./tools/run_game.sh --isolated goblin-review --world mm6 --map oute3.odm \
  --position -1800 -10816 161 --yaw-radians 0 --pitch-degrees -10.313 --seconds 0
```

The scoped test installation can be reproduced with
`python3 level_generation/creatures/mm6_remaining/install_runtime.py --playtest-redo-family mm6_gob`.

## Accepted >2× redo upgrade — 2026-09-23

Eight accepted redo packages are now installed over their original MM6 atlas packages: Archer, Barbarian,
DragonCover, Air Elemental, Water Elemental, Gargoyle, Ogre, and Werewolf. The native animation tables and the
other packages were left in place at that upgrade. The current [installation record](installation.json) identifies
each upgraded source and hashes every shipping file; the original installed directories are retained under
`installation_backups/redo_2x_before_install/` where a replacement was needed. Ogre already had the redo atlas pages,
so its installation record and runtime palette contract were updated without replacing the artwork.

Water Elemental's five oversized native final walk poses (`welwkf0`–`welwkf4`) are now deliberately normalized in
the installed atlas, and `welwkb3` has a corrected torso span. The five complete loops, seams and three palettes
were re-reviewed and accepted. The largest final-pose head step fell from 69.06 to 12.75 logical pixels, the 335
waterline and all 40 half-pixel anchors remain exact, and actual generated detail stays above 2×. The scoped
[repair review](../mm6_wel/redo_2x/review_notes.md) records source hashes, contacts and motion measurements.

Lich, Sorcerer, and Thief were previously listed as accepted, but newer review notes in their `redo_2x/run.json`
identify unresolved proportion or floor-contact concerns. Those notes invalidate the frozen acceptance hash. Their
original installed packages remain active until the animations are repaired and reaccepted.

The eight upgraded runtime manifests passed the engine's actual atlas parser; all 60 recorded installed packages
passed file-hash checks, all 60 palette contracts matched their accepted previews within one RGB byte, and the 15
focused sprite-atlas tests passed. Water's revised package again passed the parser, all package hashes and palette
contracts; its 63 distinct native-time browser bindings completed two cycles. An isolated MM6 `outa1.odm` desktop
run loaded and exited without atlas errors after the earlier eight-package installation. After Water's walk repair,
an isolated OpenGL run on MM6 `oute1.odm` (which can spawn this family) loaded 62/62 outdoor actors with no missing
textures and exited cleanly.
Use `install_runtime.py --redo-family mm6_arc1` (repeat the option for additional accepted families) to reproduce
a scoped upgrade. The historical snapshot below predates these eight replacements.

**Historical quality status at the original installation:** coverage was complete, but 56 families were marked
insufficient for actual 2× generated detail. Use the [redo inventory](redo_2x/INVENTORY.md) and
[workflow](redo_2x/WORKFLOW.md) for the repair scope. The original installation counts/checks below are historical;
zero remaining applies to coverage, not quality.

All **60 MM6 native creature/actor families** are installed at `assets_dev/engine/sprites_new/mm6_*/`: 3,481 frame names, 596 shipping files, **673,744,089 bytes (642.53 MiB)**. This includes native monsters, all peasant families, animals and special actors. The catalogue has zero MM6 families remaining. All MM6 maps use these replacements through their original actor descriptors.

Run the rebuilt development game normally:

```sh
./tools/run_game.sh --world mm6
```

Restart an already running game to discard cached sprites. Existing saves keep their original actor IDs, state and behavior; no new campaign is needed. These are explicit native atlas references, with the 2x tier stored in each package. No separate sprite-quality toggle is required. Earlier isolated playtest directories contain their own tables/binaries and must be updated separately; they are not the repository `assets_dev` installation.

## Installed content and preservation

The installer changes only texture references in 1,127 native animation groups (5,249 frame-table bindings). Native descriptor IDs, gameplay tables, frame IDs, timing, mirrors, flags and frame scales are preserved. Original BMPs remain alongside the enhanced packages. Existing custom `crusader` and `pmn2` atlas packages and their custom actor groups remain intact. Terrain, building textures, decorations and settings were not changed.

MM6 Demon and Demon Fly share the existing `m498x` ash-corpse group, which also serves original actors elsewhere in the merged game. That one shared group uses the accepted Demon Fly ash art and exact palette-496 bypass; no duplicate group or invented corpse animation is introduced. Both MM6 art packages retain their full offline coverage.

Cactus's offline viewer uses its recorded Center pivot. Current native actor rendering bottom-anchors actors even when their frame groups carry Center, whereas other sprite categories have separate Center handling. The runtime export explicitly uses that same native actor bottom pivot, retaining native placement without changing the shared renderer's established actor behavior. Native flags are untouched.

## Goblin correction

The 31 reused goblin front frames now receive an integer downward registration of 2–5 physical pixels, matching their native alpha>=128 visible baseline exactly. The 28 side/rear images are unchanged. All 59 goblin names are within 0.5 original logical pixel, including antialiased edges. Raised-foot poses and the corpse alias are preserved. Original accepted art is retained, and no AI regeneration or resizing was needed. [Correction notes](../mm6_goblin/direct_complete/review_notes.md).

## Shared palette lookup support

The runtime now reads the staged one-mask and four-mask luminance lookup models and Hydra's RGB displacement model. It uploads small RGBA32F point-sampled lookup textures shared across each palette's frames; base and mask atlas pages remain shared between variants. All lookup textures together occupy **2,083,872 bytes (1.99 MiB)**. This avoids installing full duplicated color atlases per variant.

Luminance lookup uses 256 samples, one or four material rows. Hydra stores a 33x33x33 displacement grid as a 1089x33 texture and performs explicit trilinear interpolation using point samples. Float values preserve native shadow curves and signed displacement; mask weights, exact base bypass and source alpha are retained. LUT data is encoded as little-endian float32 RGBA without color-space conversion, used on the supported little-endian desktop/Android targets. Native vector-based atlas models retain their previous operation.

## Verification

- Development game and unit-test targets built successfully. All 15 sprite-atlas test cases passed (3,619 assertions), including new lookup validation and existing crop/mirror/mipmap behavior.
- The actual C++ runtime manifest parser accepted all 60 exported packages and 3,481 frames; lookup byte counts passed. All 596 installed file hashes and the two modified table hashes match the installation record.
- Sampled every page/variant against the accepted offline previews: exported float lookup/vector math agrees to at most one RGB byte. Base/mask geometry and alpha remain shared. See [palette comparison results](runtime_review/palette_math.json).
- Desktop OpenGL build and Android GLES 300 fragment shader compilation passed. No Android APK was built or tested in this task.
- A normal desktop run on RTX 3060 Ti loaded Hermit's Isle and exited successfully, with 93 actors textured and zero missing. No atlas-load errors appeared. This was a loading/rendering smoke check, not a benchmark.
- Inspected native-game screenshots of close goblins and peasants in New Sorpigal and multiple Hydra/Titan appearances on Hermit's Isle. Corrected goblin feet meet the ground; restored peasant placement is consistent. Early road/grass scouting views contain few/no close actors and are retained only as capture history.

[Runtime validation](runtime_review/validation.json), [goblin capture](runtime_review/mm6_installed_goblins.png), [peasant capture](runtime_review/mm6_installed_peasants.png), [Hydra capture](runtime_review/mm6_installed_hydras.png).

## Reproduce / maintain

```sh
python3 level_generation/creatures/mm6_goblin/direct_complete/process.py --front-only
python3 level_generation/creatures/mm6_goblin/direct_complete/package.py
python3 level_generation/creatures/mm6_goblin/direct_complete/build_viewer.py
# Review and refresh goblin acceptance after repacking.
python3 level_generation/creatures/mm6_remaining/install_runtime.py
python3 level_generation/creatures/mm6_remaining/verify_runtime_palettes.py
python3 level_generation/creatures/inventory_remaining.py
python3 level_generation/creatures/mm6_remaining/prepare.py ledger
```

`install_runtime.py --prepare-only` exports/checks files and native bindings without publishing them. The script keeps reviewable runtime exports under `runtime/`, preserves original table backups under `installation_backups/`, checks exact texture-only YAML equivalence and publishes package files before bindings. [installation.json](installation.json) records sources, every shipping hash and the before/after table hashes. Inventory understands installed `atlas:` references and still counts native frame identities.
