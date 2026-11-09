# Accepted icon runtime cutover — 2026-09-26

**Historical installation receipt:** the [spill revision](../spill_acceptance_20260927/README.md) and the newer
[spellbook reconstruction](../spellbook_acceptance_20260927/README.md) supersede parts of this snapshot.
The current authoritative export index is
[../accepted_icons.json](../accepted_icons.json). Redeploy with `../deploy_icons.py --install`, and verify with
`../deploy_icons.py --check`. This directory's stage and receipts remain immutable history; its dated installer
refuses to overwrite a newer accepted revision. The validation results below describe the original cutover.

The live MM6–MM8 icon restoration scope is accepted, consolidated in the canonical icon ledger, and installed
in development assets. All four retired native icon roots are archived outside the mounted content tree.
The separate MM9 native scope is retained unchanged.

| Installed package | Accepted exact-2× exports |
| --- | ---: |
| `assets_dev/engine/icons_x2` | 7,995 |
| `assets_dev/worlds/mm6/icons_x2` | 846 |
| `assets_dev/worlds/mm7/icons_x2` | 517 |
| `assets_dev/worlds/mm8/icons_x2` | 562 |
| **Total** | **9,920** |

This consolidates the equipment/inventory/doll slice and the previously approved HUD, NPC/PC portraits,
spell icons/pages, effects and Arcomage atlas. It includes 307 byte-identical source aliases in their required
package namespaces. All images keep their exact native logical canvas at twice the physical resolution.
Shared items and dolls remain engine-owned; world NPC portraits are deliberately not flattened into engine
because the same names can mean different people in different worlds.

The seven displayed doll backgrounds were explicitly accepted by the user in this continuation.
Shadow's Mask inventory icon (`7item344`) had been omitted from the inventory queue. Its runtime original was
an unrelated 996×2880 armor contact sheet. The verified frozen source is 50×55; the replacement is 100×110.
[The new master](shadow_mask/master.png) was made with the built-in imagegen tool using
[this prompt](shadow_mask/prompt.txt), then uniformly fitted onto the native full canvas. The agent inspected
[the final export](shadow_mask/7item344.png). Its receipt explicitly records this newly generated repair under
the user's completion authorization; it does not claim that this particular new image had an earlier user review.

Two old MM9 pilot approvals appeared in the old global audit, but the ledger explicitly excludes them and says
to retain their native artwork. They were excluded from this installation. All 881 MM9 original files remain
byte-for-byte unchanged. An interrupted preflight's copies are retained under `excluded_mm9_pilots/` solely
for audit, outside both the accepted stage and runtime assets.

## Runtime ownership and placement

`assets_dev/engine/icon_packages.txt` declares the authoritative icon tier for each package. The loader obeys
this content policy even with old x1 settings, resolves unqualified names in active-world/base/other-world
order, and confines qualified requests to their declared package. MM6–MM8 have no native fallback. MM9 retains
x1. ZIP engine packages now mount at `/engine`, matching their content namespace and the existing world-package
mounting contract. The policy works for loose assets and freshly built packages.

`assets_dev/engine/data_tables/item_visuals.txt` contains all **726 active placement adjustments**:
150 body-item/type adjustments and 576 item/type/slot screen deltas, including the saved same-sprite wand
inheritance. The old two global `grip:` experiments remain in the preserved 728-record feedback file but are
not applied. These adjustments run after the original anchors/rotation, in native logical pixels. Armor poses
share their accepted body-type placement. The original `items.txt` and complex-offset tables remain unchanged,
so the review's original side and frozen source-table evidence remain reproducible.

The same visual table preserves all 79 inventory fits, six new-item footprint corrections and five jewelry
scale groups (seven item IDs including aliases). Inventory rendering, chest rendering, picking/dragging and
the held cursor use the same draw scale; jewelry scaling stays separate and centered on its original placement.
Already serialized inventory cell sizes in older saves are not rewritten by this asset installation. No user
save was modified. Newly generated items use the updated cell footprints.

## Ledger, sources and review

- [accepted.json](accepted.json): every selected source/art hash and runtime destination.
- `receipts/`: per-target provenance; older receipts and superseded artwork remain intact.
- [installed.json](installed.json): exact installed files and hashes.
- [source_archive.json](source_archive.json): all **13,854** original files, hashes and archive locations.
- `assets_legacy/icons_20260926/{engine,worlds/mm6,worlds/mm7,worlds/mm8}/icons`: originals; not a runtime mount.
- [validation.json](validation.json): hashes, dimensions, placements, source preservation and MM9 exclusion checks.

`checkpoint/state.json` and its canonical export manifest contain the consolidated approvals. Frozen target
and job manifests retain their historical source paths and hashes. `native_sources.py` supplies an explicit,
manifest-bound relocation for restoration tooling; it never looks in runtime roots for a replacement original.
All 14,780 frozen native contracts still verify. [The scope disposition](scope_disposition.json) classifies
9,920 installed targets, 3,924 retired unused targets and 936 separate MM9 targets (including its non-icon UI
contracts). Retired targets are explicitly excluded from future queue scheduling; they are not approved art. The paperdoll catalog builder and canonical queue use this
relocation. Historical pre-cutover audit reports remain historical, not current runtime inventories.

The browser on **port 8899** uses this directory's `review.js` and `inventory_fit.js`. All 1,260 feedback decisions
and 728 placement records remain intact, and newer browser edits survive re-import. Main, held-armor, jewelry
and latest-repair queues are empty; all 63 jewelry groups are accepted.

[Open the review](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?hide_accepted=1).
Use Ctrl+Shift+R once to load the new catalog. To inspect accepted art, clear **Hide accepted/staged**.

## Validation and use

The normal OpenGL build and focused AssetFileSystem/image/item-visual tests pass, including all installed icon
paths, archive package precedence, retained-native MM9, logical dimensions and invalid visual-table imports.
[Browser checks](browser_checks.json) verify zero remaining queues, shared jewelry images and exact feedback
preservation. [Runtime checks](runtime_checks.json) record successful isolated MM6/MM7/MM8 launches with native
HUD screenshots after the original folders were removed. These captures cover gameplay HUDs, not every equipped
item combination; the equipment combinations retain the reviewed browser data.

```sh
# Recheck the current accepted workspace and installed bytes:
python3 -B level_generation/ui/hud_inventory/deploy_icons.py --check
python3 -B level_generation/ui/hud_inventory/spellbook_acceptance_20260927/validate.py

# Review browser (server root must be the repository):
python3 -m http.server 8899 --bind 127.0.0.1

# Launch the current development build:
./tools/run_game.sh
```

The existing `assets/*.zip` release archives were **not rebuilt** by this development-assets task. Release
packaging from `assets_dev` will include the new roots and policy and exclude `assets_legacy`. Do not use stale
release ZIPs to judge this cutover. No Vulkan build was run.

`consolidate.py --accept --install` is the recorded import/install transaction; `archive_sources.py` records
source retirement. `close_scope.py` records the unused-source disposition. Their receipts are frozen. For a future artwork revision, create a new receipt/transaction,
not an edit to an already approved file. Faithful generative doll restoration remains optional future work;
the accepted Real-ESRGAN bodies and limbs remain the current choice.
