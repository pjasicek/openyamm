# Hesper loading screens — 2026-10-24

Four 1280×960 RGB loading pages, with two retained Codex imagegen candidates per subject:

| Icon | Subject |
|---|---|
| `hes_loading1` | The lander in Starport Reach's glassed crater, dead Starport and debris ring |
| `hes_loading2` | A Kreegan Trooper squad in the Brood Spires' resin forest |
| `hes_loading3` | Aster's projected face in the Undervault chapel |
| `hes_loading4` | The great ion cannon on the Crownspire beneath the debris ring |

[Four selected pages at 50% progress](review/selected_50_sheet.jpg) ·
[All eight candidates](review/candidates_sheet.jpg) ·
[Exact prompts, raw returns, hashes and selection reasons](generation_runs.json).

`raw/` preserves every built-in imagegen return unchanged (1448×1086). `selected/` contains the four final pages;
`review/hes_loading<N>_50.png` contains each full-size progress preview. Only the review sheets have labels.
The exports downsample the full generated frame with Lanczos, convert to RGB, then composite the native frame.

All five engine loading pages were inspected, along with `LoadingOverlayScreen.cpp`, Hesper's concept brief,
the world art direction, Aster's portrait/chapel description and the 2026-10-24 Kreegan skin palette.
Troopers retain violet, slate-blue and black-crimson skin; Aster is a damaged pale-blue projection in ivory/gold
architecture. The Crown uses the current single cannon mounted on the fortress dome.

## Native progress-bar fit

The engine draws `loadprog` at (173, 459), 299×14 in its 640×480 reference. These x2 pages therefore reserve
**(346, 918), 598×28**. The native `loadprog.png` is already 598×28 RGBA.

`build_pages.py` crops `assets_dev/engine/icons_x2/loading2.png` at **(322, 896)–(962, 960)** and feathers only
the crop's outer eight pixels. The complete gold frame and empty fill well remain native pixels, without scaling
or displacement. The subject stays above this band. The script composites the left **299×28** pixels of
`loadprog` at **(346, 918)** for the 50% previews, matching the engine's source crop and alpha blending.
The final installed pages have an empty bar.

The script checks all eight raw hashes, exactly one selection per pair, RGB dimensions, unchanged native frame
pixels, unchanged art above the frame crop, and the preview fill's bounds and untouched right half.

## Rebuild and stage

From the repository root:

```sh
flock -s output/hesper_stage/locks/stage.lock python3 -B level_generation/ui/hesper_loading/build_pages.py
flock output/hesper_stage/locks/stage.lock python3 -B level_generation/projects/hesper_stage/stage.py
level_generation/projects/hesper_stage/rebuild_all.sh --scenarios-only
```

`stage.py` reads the four files in `selected/`, checks their RGB dimensions, and copies them into
`output/hesper_stage/assets_editor_dev/worlds/hesper/icons_x2/hes_loading1.png` through `hes_loading4.png`.
No new engine lookup, world setting, map build or `assets_dev` write belongs to this package. The destination-world
loading-screen switch remains the separate task queued in `design/kreegan_world/ENGINE.md`.
The 50% previews demonstrate composition and pixel fit; they are not runtime captures.

## Verification status

The export checks pass; see [build_pages.log](review/build_pages.log). The stage attempt acquired its lock but
failed before the page-copy step in unrelated Noble weapon cooking; see [stage.log](review/stage.log) and
[invalid burn-map indices](review/model_blocker.log). The exported `hes_noble_fang.glb` and
`hes_noble_sidearm.glb` each have one texture but refer to higher texture indices in `openyamm_burn_map`.
The previous live stage is intact. The loading pages therefore await a successful restage after those inputs
are repaired by their owning session. No unrelated model or cooker changes were made.

The scenario sweep is recorded in [scenarios.log](review/scenarios.log). The default walkability audit cannot
start Python 3.14's forkserver socket in this sandbox. The same audit with `multiprocessing.set_start_method("fork")`
passed its existing `hes_d03,hes_d08` gates; see [walkability_fork.log](review/walkability_fork.log).

The completed sweep passed **95/97 scenarios**, exit 1, on the preserved live stage.
D12 `d12_main_path` and D5 `relay_spire_climb` failed movement-height assertions;
[details](review/scenario_failures.log). Decoration IDs and actor sizes both had zero mismatches.
[Check receipt](review/checks.json). The four pages are ready for the next successful stage run.
