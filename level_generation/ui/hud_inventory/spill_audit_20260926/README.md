# Mechanical icon spill audit

Run from the repository root:

```sh
python3 -B level_generation/ui/hud_inventory/scan_spill.py
python3 -B -m unittest discover -s level_generation/ui/hud_inventory -p test_scan_spill.py
```

Open [the report](http://127.0.0.1:8899/level_generation/ui/hud_inventory/spill_audit_20260926/index.html).
The existing repository server on port 8899 serves it. `report.json` contains all measurements and provenance;
`findings.csv` contains one row per image/color with a nonzero finding. `summary.json` records coverage and counts.
The HTML also works as a local file because it loads `report.js`, without fetching JSON.

## Keyboard review

- Up/Down selects the previous/next item in the current filtered list, including beyond the first 40 cards.
- Left/Right cycles the reason: border magenta / possible bad crop, spill on outline, spill inside image, other.
- Space flags the selected item with that reason, or updates its existing flag. It does not advance or toggle a
  flag off. Use **Remove flag** to undo. The Unflagged filter naturally removes an item once flagged.
- Click a card to select it. Shortcuts leave text fields and filters to their normal keyboard behavior.
- Optional notes are retained as drafts; flag/update the item to include them in its saved flag.

Flags, selected reason, filters and current position persist in this browser at this origin. The separate
`openyamm-icon-spill-flags-v1` / `openyamm-icon-spill-view-v1` storage keys do not modify paperdoll reviews,
placements or ledger acceptance. Each flag identifies the scope, target, image hash and master crop where present.
Use **Export flags** to download `openyamm-spill-review.json` for backup and handoff. Flags are not automatically
written back to repository files; use the same browser and `127.0.0.1:8899` origin to resume.

The viewer sources are `../spill_review.html` and `../spill_review.js`. Refresh only the deployed UI without
rerunning the scan or rewriting its measurements:

```sh
python3 -B level_generation/ui/hud_inventory/scan_spill.py --refresh-viewer
```

`node level_generation/ui/hud_inventory/test_spill_review.mjs` checks the controls with the server running,
using a separate temporary Chrome profile so the user's feedback is untouched.

## Scope

- Every accepted x2 export in `runtime_install_20260926/accepted.json`, including accepted equipment, paperdolls,
  portraits, inventory icons, spell art and UI. Source and deployed image hashes are checked.
- Masters linked through recorded candidate hashes, preparation/repair manifests, cleaned-master siblings and
  the recorded opaque portrait panel crops. Opaque portrait crops use the same recorded two-pixel trim as their
  production recipe where applicable. Repair inputs are identified as inputs, not assumed to be final clean masters.
- Other retained files named `*master*.png` under `level_generation/ui/`, listed separately. These include old
  attempts and may be superseded; a finding here does not mean the current accepted export has that defect.
  This historical-master inventory also includes MM9 pilot images if present in these workspaces.
- Targets without a recovered master link are explicitly listed. They still receive the full x2 scan; some have
  direct x2 or deterministic outputs instead of a larger master. Unlinked raw sheets are not silently treated as
  current masters. MM9 native icons are outside the accepted MM6–MM8 snapshot.

## Classification

The original BMP/PCX is decoded using its frozen consumer profiles and the archived source mapping. If profiles
differ, pixels visible in any profile remain visible for source comparison. Original background/key RGB values are
recorded from the pixels those profiles actually remove. Cyan/teal is measured separately from green because many
original keys are `(0,252,252)` rather than pure green. Generated sheets can use magenta even when the native key
was cyan, so both families are always checked.

Fully transparent RGB is ignored. Pixels with alpha below 8 are omitted from visible findings. The scan considers
mixed-color pixels within three pixels of the visible silhouette (including holes), opaque canvas borders, and
very strong key-like colors anywhere. Master edge width scales with resolution. Original-color correspondence and
nearby interior color provide evidence; they do not establish pixel-perfect geometric registration.

| Class | Meaning |
| --- | --- |
| `likely_spill` | A visible color cluster with unsupported edge excess or strong key-color evidence, without a large corresponding native/material color region. Inspect before repair. |
| `color_material_review` | Significant color signal, but intentional colored materials, reflections, spells or uncertain master provenance can explain it. |
| `trace` | A smaller signal below the significant-cluster threshold; retained in the report rather than discarded. |
| `no_spill_detected` | No signal under these thresholds; this is not a guarantee against every possible color cast. |

Significant clusters need at least three alpha-weighted pixels and either a three-pixel connected component or
eight suspect pixels. Likely findings also need three alpha-weighted pixels of unsupported evidence. A native
color fraction of 5% or more routes findings to material review. Moderate green/cyan on a fully opaque illustration
also routes to material review unless strong key-color pixels are present. Broad colored interiors are protected from
automatic likely-spill classification. These thresholds favor finding small fringes over eliminating all false
positives. No class authorizes automatic deletion or desaturation.

For raw/retained masters only, near-pure, border-connected magenta/green/cyan sheet backing is omitted from an
in-memory diagnostic mask; mixed fringe colors remain measurable. The image on disk is untouched. Accepted x2
images never receive this background exclusion, since visible key pixels there are themselves potential defects.

Previews show the rendered original, scanned image on dark and light backgrounds, an unchanged enlarged edge
detail, and the same detail with suspect pixels in orange. Master crops with different fitting have approximate
native correspondence. A master can require matting while its final x2 export is already clean.

The classifier is read-only with respect to artwork, ledger decisions, browser feedback, offsets and runtime files.
It writes only its audit report/previews. Repair and acceptance are separate operations.

## Completed scan, 2026-09-26

All **9,920 accepted x2 targets** were scanned. Counts include shared-image aliases:

| x2 classification | Targets |
| --- | ---: |
| Likely spill | 1,722 (1,467 unique image hashes) |
| Color/material review | 2,831 |
| Trace | 1,770 |
| No spill detected | 3,597 |

Agent spot checks confirmed a green fringe on `item019`, and magenta canvas borders on `7load5.pcx` and
`worlds/mm8/elemw.bmp`. This does not visually confirm every automated finding. The opaque-background guard was
added after a muted green PC01 portrait background initially triggered the likely-spill class.

The master pass scanned 5,435 linked crops/inputs from 582 files, covering 5,392 current targets, plus 3,919 other
named master files. The remaining 4,528 targets have no recovered larger-master link in this audit. Every one of
those targets still received the x2 scan. Full file/crop paths and provenance are retained in the JSON.

Two historical named masters could not be decoded because they are truncated:

- `chat_returns/resto_200_01-f929935c1bd0/incoming/outputs/processed/S023/engine--icons--item323.bmp-clean-master.png`
- `chat_returns/resto_200_04-387a87b723da/incoming/outputs/processed/S007/worlds-mm9--icons--mm9_item_10091.png-clean-master.png`

These errors are explicit in `summary.json`; master coverage is marked incomplete rather than calling unreadable
files clean. The accepted x2 coverage is complete. The command exits nonzero when such file errors remain, after
writing the report. `validation.json` records input/runtime hash preservation and complete x2 coverage.
