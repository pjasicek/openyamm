# Accepted spill repairs — 2026-09-27

**Subsequent revision:** the [accepted spellbook reconstruction](../spellbook_acceptance_20260927/README.md)
replaces 87 records from this acceptance. This directory remains the immutable artwork/receipt history for those
targets and the current source for its other targets. Deploy and verify through `../accepted_icons.json` and
`../deploy_icons.py`; the publication-wide validation below describes this revision before later replacements.

All **1,722** entries in the spill repair review are accepted under the user's explicit instruction, recorded
in the canonical ledger and deployed. **1,531 runtime images changed**; the remaining 191 retain their existing
artwork. Additional repairs were limited to the **12 targets with recent comments**, including saved draft notes.

The user subsequently **explicitly approved all 12 final repairs** and requested redeployment. The exact final
artwork hashes and instruction are recorded in [final_12_user_approval.json](final_12_user_approval.json), linked
from each affected target and cell in the canonical ledger. This confirmation supersedes older browser flags
for these 12 revisions while retaining their saved history.

[Open the accepted review](http://127.0.0.1:8899/level_generation/ui/hud_inventory/spill_repairs_20260927/review/index.html).
Refresh once with Ctrl+Shift+R. The pending queue is empty; **Resolved recent comments** shows those 12 targets.
Historical flags and notes remain intact. New browser feedback can flag the installed revision separately.

## Current workspace and deployment

- [../accepted_icons.json](../accepted_icons.json) is the current index for all **9,920** accepted exports.
- [accepted.json](accepted.json) records this revision, approval authority, prior hashes and each resolution.
- `accepted/{engine,worlds/mm6,worlds/mm7,worlds/mm8}/icons_x2/` contains this revision's 1,722 accepted exports.
- `receipts/` contains per-target provenance; [installed.json](installed.json) records all runtime bindings.
- [../checkpoint/state.json](../checkpoint/state.json) remains the canonical acceptance ledger.
- `previous_accepted_index.json`, `checkpoint.before.json`, original masters and earlier accepted exports are preserved.

The accepted entries comprise 1,458 engine exports, 167 MM6, 53 MM7 and 44 MM8 exports. Shared items, portraits
and UI use their recorded engine destinations; world-local portraits and minimaps retain their world namespaces.
Files use lowercase names and 0644 permissions. Original retired `icons` folders remain retired.

From the repository root, redeploy or verify the **current** accepted workspace with:

```sh
python3 -B level_generation/ui/hud_inventory/deploy_icons.py --install
python3 -B level_generation/ui/hud_inventory/deploy_icons.py --check
```

This verifies hashes and ledger acceptance before copying. It does not regenerate or implicitly accept edits.
The superseded `runtime_install_20260926/consolidate.py --install` now refuses to overwrite this revision.
Release ZIP archives were not rebuilt.

## Recent comments resolved

| Targets | Resolution |
| --- | --- |
| `ui-parch`, MM7 `npc0633` | Removed remaining magenta on the left border. |
| `7pc19-56`, `pc06-28`, `pc06-32`, `pc06-34`, `pc06-38` | Removed remaining magenta on the bottom border. |
| `fr_inven` | Reduced bright, uneven cell texture and bevels while keeping the 14×9 grid in place. |
| `crysskull`, engine and MM6 alias | Regenerated crystal detail and clean teeth; both aliases use identical artwork. |
| `item263` | Regenerated the skull staff and fitted it to the accepted canvas and alpha mask. |
| MM8 `out06` | Regenerated Shadowspire as dark dead land, guided by native geography and local map data. |

Exact notes are in [commented_targets.json](commented_targets.json); the captured browser decisions and drafts
are retained in `browser_state.original.json`. [resolutions.json](resolutions.json) records each repair method
and its input/output hashes. `proofs/` contains before/after visual checks.

Three masters were generated with the built-in imagegen tool and visually inspected under the user's repair
authorization. Receipts do not represent these new images as having earlier browser approval.

| Artwork | Raw master | Exact prompt | Final accepted export |
| --- | --- | --- | --- |
| Crystal skull | [raw](generated/crysskull/raw.png) | [prompt](generated/crysskull/prompt.txt) | [x2](accepted/engine/icons_x2/crysskull.png) |
| Skull staff | [raw](generated/item263/raw.png) | [prompt](generated/item263/prompt.txt) | [x2](accepted/engine/icons_x2/item263.png) |
| Shadowspire minimap | [raw](generated/out06/raw.png) | [prompt](generated/out06/prompt.txt) | [x2](accepted/worlds/mm8/icons_x2/out06.bmp) |

Each generation directory also retains its request metadata. `resolve_comments.py` performs deterministic final
fitting/color repairs. Larger masters are provenance; deploy the accepted x2 files to retain the reviewed fit.

## Validation

[validation.json](validation.json) passes all 9,920 workspace/runtime hashes, all 1,722 affected masks and canvases,
alias consistency and preservation of unrelated ledger records. There are **zero alpha, dimension or placement
changes**. All 728 saved placement records and the installed table with 726 active adjustments remain unchanged.

The Arcomage atlas repair updates four affected ledger cells. Five prior generation-reference dependencies were
explicitly frozen to their immutable historical artifact hashes, keeping their provenance and approvals valid.
These dependency migrations do not change their artwork.

```sh
python3 -B level_generation/ui/hud_inventory/spill_acceptance_20260927/validate.py
node level_generation/ui/hud_inventory/test_spill_review.mjs
```

Both browser flows pass in an isolated profile, including the empty pending queue, 12 resolved targets, images,
keyboard controls, notes, reload/export and preservation of other review storage. The live browser profile was
read for feedback capture but its localStorage was not rewritten. The static server remains on port 8899.
