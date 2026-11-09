# Accepted spellbook reconstruction — 2026-09-27

The user explicitly accepted browser revision **`e1c5265ae12b808b`**, requested replacement of the latest accepted
spellbook artwork, and authorized installation into `assets_dev/engine/icons_x2`. All **258 PNGs** are published
in the canonical ledger and current accepted index; **156 runtime images changed**. The other 102 highlighted
spell states already matched the approved browser bytes.

| Approved artwork | Files |
| --- | ---: |
| Shared-background book pages | 12 |
| 111 spell pairs, normal and highlighted | 222 |
| 12 school bookmarks, inactive and selected | 24 |
| **Total** | **258** |

This includes the restored opacity of nine Air pairs. The spell states retain identical geometry and alpha within
each pair; the 12 pages share their paper and frame; the school tabs share one parchment bookmark. The three
bottom-left controls retain the latest previously accepted installation. No new image generation, resampling,
palette changes, YAML edits, renderer edits or release ZIP packaging were performed during publication.

[Open the accepted browser](http://127.0.0.1:8900/level_generation/ui/hud_inventory/spellbook_fixup_review/?school=Air).
It shows 135 accepted review targets (12 pages, 111 spell pairs, 12 bookmark pairs). Existing comments are retained;
older flags on this artwork are superseded by the user's explicit acceptance. New feedback can flag a subsequent
issue without rewriting the ledger. The exact pre-publication browser, images, recipe and evidence remain under
[`../spellbook_fixup_review/revisions/e1c5265ae12b808b/`](../spellbook_fixup_review/revisions/e1c5265ae12b808b/index.html).

## Current records and deployment

- [accepted.json](accepted.json) binds every target, reviewed file, output hash, prior approval and runtime destination.
- [authority.json](authority.json) records the user's instruction and the exact approved browser revision/view.
- `accepted/engine/icons_x2/` contains immutable copies of the reviewed PNGs; `receipts/` contains per-target records.
- [../accepted_icons.json](../accepted_icons.json) indexes all 9,920 current accepted exports and is hash-bound to
  [../checkpoint/state.json](../checkpoint/state.json). Both now point to this revision for these 258 targets.
- [installed.json](installed.json) records the full installation; [validation.json](validation.json) verifies it.
- `checkpoint.before.json` and `previous_accepted_index.json` preserve the prior ledger/index. Earlier accepted
  artwork and receipts remain intact. This revision supersedes 87 records from the earlier spill acceptance;
  the other 171 previously came from the original runtime cutover.

From the repository root, use the current index for future deployment:

```sh
python3 -B level_generation/ui/hud_inventory/deploy_icons.py --install
python3 -B level_generation/ui/hud_inventory/deploy_icons.py --check
python3 -B level_generation/ui/hud_inventory/spellbook_acceptance_20260927/validate.py
```

`publish.py --apply` is the recorded acceptance transaction. It never regenerates artwork and refuses to replay
this revision after a newer acceptance supersedes it. `publish_review.py` publishes the installed status to the
browser only after installation validation. Do not run the older dated installers over this acceptance.

## Explicit export-canvas migration

Five native default/highlighted pairs had differing source widths. The approved browser uses the highlighted
canvas for both states so that hover changes colour without changing shape or sampling. The new default PNGs
are copied exactly from that review, and their canvas changes are declared in
[canvas_migrations.json](canvas_migrations.json), the individual receipts, index records and staged ledger records.

| Default export | Earlier pixels | Approved pixels |
| --- | --- | --- |
| `sbf10b.png` — Inferno | 304 × 248 | 308 × 248 |
| `sba05b.png` — Jump | 252 × 274 | 250 × 274 |
| `sbe03b.png` — Earth Resistance | 268 × 296 | 266 × 296 |
| `sbe08b.png` — Rock Blast | 262 × 266 | 260 × 266 |
| `sbm11b.png` — Enslave | 288 × 304 | 284 × 304 |

The frozen `expected_targets.json`, jobs, native originals and source dimensions remain unchanged as historical
contracts. The accepted index owns the current export sizes. Deployment checks each actual PNG size and requires
an exact declared migration whenever it differs from the original contract. These five assets have only their
recorded spellbook YAML usages, whose explicit draw/hit rectangles stay unchanged. The existing shared spellbook
renderer draws both state textures into that same rectangle, matching the browser's behavior.

## Verification

Validation checks all 9,920 current runtime hashes and permissions, every new export against its approved browser
file, all 111 spell pairs' dimensions and alpha, all five canvas migrations, preserved previous artwork, unchanged
YAML/native contracts, and unchanged unrelated index/ledger records. The browser interaction check covers the
accepted status, all 12 schools, hover/selection, restored/previous Air strength and the three bottom controls.
No C++ build was needed for these asset and ledger changes.
