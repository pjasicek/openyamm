# Accepted MM7 Town Portal — 2026-09-27

The user accepted the MM7 map and all six matching destination buttons, and requested installation into `icons_x2`.
All seven reviewed PNGs are recorded in the canonical ledger and installed in `assets_dev/engine/icons_x2/`
with lowercase names and 0644 permissions.

| Artwork | Installed files |
| --- | --- |
| Regenerated MM7 map | `antagrich.png` |
| Registered city highlights | `tpharmon.png`, `tpavli.png`, `tpwarl.png`, `tpisl.png`, `tpheav.png`, `tpdeja.png` |

Installed bytes exactly match the browser-approved exports. The map is 1280 × 960, logical size 640 × 480.
Hover textures retain the original draw and hit rectangles. Their normal-state crops exactly match the map;
highlighting adds feathered warm light without changing geometry, with four unchanged pixels around each border.
No image generation or processing took place during acceptance or deployment.

[Open the accepted browser review](http://127.0.0.1:8900/level_generation/ui/hud_inventory/town_portal_fixup_review/mm7/).
Its Accepted view reads the immutable accepted exports. Previous and original artwork remain available.
The [restoration workspace](../town_portal_fixup_review/mm7/README.md) retains prompts, raw output, original references,
all default and hover crops, light masks, and visual evidence.

- [authority.json](authority.json), [accepted.json](accepted.json), and `receipts/` bind the explicit approval,
  reviewed hashes, previous acceptances, native canvases, and runtime destinations.
- `accepted/engine/icons_x2/` holds immutable accepted exports; `review_before/` preserves the prior browser page
  and review records. Old accepted images remain untouched in their original acceptance folders.
- [../accepted_icons.json](../accepted_icons.json) indexes all 9,920 accepted images; its hash is bound to the
  canonical ledger in `../checkpoint/state.json`. `previous_accepted_index.json` and `checkpoint.before.json`
  preserve the state immediately before this seven-file publication.
- [installed.json](installed.json) records deployment. [validation.json](validation.json) verifies exact installation,
  dimensions, permissions, masks, crop alignment, and preservation of unrelated acceptance and ledger records.

The installer changed exactly seven runtime images. Checks passed for all 9,920 accepted icons and 10,106 cells,
with no pending deployments. The MM6 palette study remains pending, and MM6/MM8 artwork and Town Portal layout
files are unchanged by this revision.

An existing change to inventory-grid offsets in three shared input files initially blocked the frozen queue.
The [explicit input reconciliation](../input_reconciliation_20260927/README.md) verifies and preserves those changes
without altering art contracts or the historical catalog. Its receipt is pinned in the canonical ledger;
future unrecorded input changes still fail validation. Seven focused guard tests passed.

Publication used `publish.py --apply`, followed by the current-index installer and verification:

```sh
python3 -B level_generation/ui/hud_inventory/deploy_icons.py --install
python3 -B level_generation/ui/hud_inventory/deploy_icons.py --check
python3 -B level_generation/ui/hud_inventory/town_portal_mm7_acceptance_20260927/validate.py
```

The last command audits this revision against its immediate predecessor. After later unrelated acceptances,
use the current-index deployment check. Preparation now refuses to overwrite the accepted MM7 revision.
Release ZIP packaging is separate.
