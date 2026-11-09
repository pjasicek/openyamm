# Obsolete UI removal — applied 2026-09-29

**Removed the approved 528 files, 40,909,521 bytes (39.0 MiB).** A separate 61-file batch
(10.8 MiB) requires legacy settings, animation-table or test retirement first.
The runtime exports are removed and their deployment records explicitly retired. Accepted source artwork
and the accepted-art index remain intact. The Git index was not changed. See [the application receipt](applied.json).

[Visual candidate review](index.html) · [Exact removal paths](remove-files.txt) ·
[Removal manifest with hashes and evidence](removal_manifest.json) ·
[Conditional candidates](conditional_manifest.json) · [Native preview](native/index.html)

## First removal batch

| Group | Files | Examples / replacement |
| --- | ---: | --- |
| Legacy restored UI exports | 490 | Old frames, borders, selection/meter art, hero/skull layers, followers panel, menu buttons, journal and beacon art, touch/context buttons, jewelry background and magnifiers. Includes all 121 `hglas000`–`hglas120` rest-hourglass frames. Their native Obsidian replacements are active. |
| Superseded or unused Obsidian exports | 26 | Previous minimap rings/shading, floating command/resource/followers plates, horizontal meter art, unused button states and early journal/rest surfaces. |
| Unmounted Android layout | 1 | `gameplay_mobile.yml`; Android mounts `gameplay.yml` plus the approved `touch_controls.yml`. |
| Superseded MM9 dialogue files | 11 | Old RUDE background variants, arrow states and unused popup coordinates. The active `RUDEBG_OPENYAMM_LIGHT_ORNATE_SLIM.png` and RUDE font atlases are retained. |

These are mounted runtime copies. Accepted source artwork, design studies, historical receipts, original asset
archives, screenshots and generation inputs are not removal candidates. Removing the runtime copies therefore
reduces the mounted/package payload; 39.0 MiB is not a claim about total repository disk savings.

Every candidate has a SHA-256 and recovery source in [recovery.json](recovery.json). The 490 accepted-icon exports
already have byte-identical preserved source artifacts. The other 38 files are copied into
[recovery_extras.zip](recovery_extras.zip), including the unmounted YAML. Recovery checks pass for all 528 files.

## Conditional batch

| Dependency | Files | Required follow-up |
| --- | ---: | --- |
| Dormant settings | 44 | Retire `controls.yml`, `keyboard.yml`, `video_options.yml`, their entries in `GameplayLayoutFiles`, and the corresponding legacy screen state/render/input paths. Only then remove their 41 exclusive textures. The current `settings_*.yml` / `MenuDesignScreen` flow stays. |
| Old turn-indicator registration | 15 | Remove the unused `turnstart`, `turn0`–`turn4`, `turnstop` registrations from `icon_frame_data.txt` together with `ia01-001`–`ia01-015`. The old `ia02-*` loading animation is outside this reviewed batch; its table registration also needs retirement after the Obsidian loading replacement. |
| Stale screen-background tests | 2 | Migrate `TableRegressionTests.cpp`'s old background expectations before retiring `makeme.png` and `restmain.png`. Those tests still describe original assets under the already-retired `engine/icons/` root; they do not validate the current Obsidian screen designs. |

[conditional-files.txt](conditional-files.txt) lists this batch separately. It is absent from both the first removal
manifest and the staged deployment-retirement registry. No claim is made that these dependencies were removed.

## Preventing accidental reinstallation

`hud_inventory/deploy_icons.py --install` now excludes the 490 explicitly retired exports while preserving
their accepted source artwork. A complete deployment check passes for the remaining 9,430 accepted exports.

[deployment_retirement.patch](deployment_retirement.patch) preserves the reviewed initial change to that tool and adds an
explicit `runtime_retirements.json`. It preserves the accepted artwork/index while excluding the retired runtime
exports from deployment and marking their installation status as retired. A changed accepted revision, unknown
target, missing preserved source or still-mounted retired file fails validation. Ordinary deployment behavior is
unchanged when no retirement registry exists.

The patch and deletions have been applied together. The final deployment tool also separates artifact verification
from generation-time live-layout validation: evolving gameplay YAMLs no longer prevent deploying accepted art.
It retains frozen catalog/job/index hashes, accepted-cell evidence and dependencies, image dimensions, canvas
migrations and destination checks. Generation still validates its original inputs. New deployment receipts are
written under `hud_inventory/checkpoint/deployments/`, preserving historical installation receipts.

The initial staged files remain in [staged/](staged/) as review history. Their original tool/index hashes are
recorded in [patch_inputs.json](staged/patch_inputs.json). The live tool is authoritative; do not reapply the patch.
Focused retirement-guard and accepted-cell dependency checks pass. Historical one-off export scripts can still
recreate their old outputs; use the current deployment tool, not dated install receipts, for redeployment.

## Scope and evidence

The audit inventories **11,234 files**, scans **2,031 source/data/test/provenance inputs** and checks **38 UI YAMLs**:

- Engine `icons_x2`, `hud_x2`, UI and fonts; every world's mounted icons, UI and fonts.
- Shared game/engine/editor C++, active YAML asset states, runtime tables/scripts and world/mod configuration.
- Formatted/prefixed asset names, icon-animation consumers, map filenames that become texture names,
  and test-only dependencies. Recognition predicates such as `starts_with("obsidian_")` are not asset consumers.
- Existing restoration classifications establish UI identity; they do not establish current liveness.
  An unused literal alone is not enough to remove character, item, spell, map or FX content.

Spellbook pages/bookmarks/icons, recreated MM fonts, Fondamento, portraits, paperdolls/equipment, chests/shop
illustrations, map/town-portal art, Fly/Water Walk animations, rest panoramas and loading artwork remain.
The explicitly reserved future timed-buff strip is preserved, including its expiring state. Current Android
touch controls and their approved placement are preserved.

[inventory.tsv](inventory.tsv) is the complete path/status/size/hash census. [inventory.json](inventory.json)
contains detailed UI evidence, classifications, layout and animation records. It omits repeated portrait/item
provenance from its detailed records while retaining them in the census/counts. Up to 16 source examples per asset
and reference kind are stored; all relevant sources are scanned. [inputs.json](inputs.json) pins those inputs.
Name matching conservatively retains same-named assets in every mounted package instead of treating world
overrides as duplicates.

## Validation

[validation.json](validation.json) confirms all approved paths are absent, all 528 recovery sources match and
deployment retirement guards pass. [pre_removal_recheck.json](pre_removal_recheck.json) records the fresh
source/reference/hash audit immediately before deletion. [deployment_check.json](deployment_check.json) records
the successful deployment check and retirement status update, with no active exports needing reinstallation.
[The native capture tour](native/tour.yml) runs against a private asset tree excluding all 528 candidates.
The ordinary desktop OpenGL game completed successfully on the NVIDIA GPU; screenshots cover gameplay,
turn-based HUD, inventory/jewelry, stats, skills, awards, quick reference, rest, map/quests/notes/story,
spellbook, Lloyd's Beacon and pause menu. See [the run receipt](native/run.json).
The journal's initial `__journal_map_composited__` cache miss is followed by successful dynamic texture creation;
it is not a removed image. This is a desktop/MM6 smoke check, not Android-device or exhaustive world/service coverage.

To verify the applied cleanup:

```sh
python3 level_generation/ui/obsolete_ui_cleanup_20260929/validate.py
python3 level_generation/ui/hud_inventory/deploy_icons.py --check
```

`audit.py` and `prepare.py` refuse to overwrite this applied record; use a fresh directory for a future cleanup.
The separate conditional batch remains mounted until its dependencies are retired. Packaged releases must be
rebuilt from the cleaned development tree. The [Obsidian loading window](../obsidian_loading_20260929/README.md)
is the accompanying UI replacement.
