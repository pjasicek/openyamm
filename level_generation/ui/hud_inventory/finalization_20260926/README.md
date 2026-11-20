# Equipment/inventory ledger acceptance and full icon audit — 2026-09-26

> Superseded by the [completed runtime cutover](../runtime_install_20260926/README.md): all eight gaps are resolved,
> 9,920 exports are installed, offsets are imported and native MM6–MM8 roots are archived. The report below is
> the preserved pre-cutover audit.

The user approved the final medallion/Fine Ring repairs and authorized proper acceptance of the completed
equipment/inventory slice into the icon restoration ledger. This import is complete. The full-folder audit
found **eight artwork gaps**, so the original icon folders have not been retired and runtime assets are unchanged.

## Accepted and staged

| Scope | Distinct targets |
| --- | ---: |
| Reviewed equipment and jewelry, all supported body/pose variants | 1,349 |
| Previously approved inventory review slice | 770 |
| Shared between equipment and inventory | −369 |
| Previously accepted Real-ESRGAN doll bodies and limbs | 466 |
| **Unique canonical accepted/staged images in this import** | **2,216** |

[accepted.json](accepted.json) enumerates every exact source hash, approved image hash, canonical staging path
and intended runtime destination. The canonical `checkpoint/state.json` now contains the accepted cells and
staged targets; the canonical exports manifest also contains them. Files are under
`icons_x2_stage/engine/icons_x2/` (and package equivalents), following the existing runtime x2 contract.
They have not been copied into `assets_dev/`.

All **1,260 review decisions and 728 saved placement records** remain retained. There are 726 active placement
proposals: 150 complex item/type offsets and 576 item/type/slot screen offsets. Two old `grip:` records remain
archived but inactive. The six inventory-footprint changes, all 79 inventory fitting records, five jewelry
overlay scale groups and shared-image aliases are retained with the stage.

The latest untouched browser capture is [browser_state.original.json](browser_state.original.json), taken
at 16:09:19.905 UTC. It persisted the new medallion approval but still contained the old Fine Ring approval.
The user's explicit chat acceptance of both final repairs supplies the Fine Ring amendment in
[decisions.json](decisions.json); it does not discard the earlier browser value. The historical Athena flag
also remains in the raw feedback; its current image follows the approved shared Scarab Ring representative.

[authority.json](authority.json) records authorization. Each image has an immutable receipt under `receipts/`.
[checkpoint.before.json](checkpoint.before.json) retains the full prior canonical state; earlier approved and
staged files were not deleted or overwritten. Existing unrelated ledger entries remain intact.

The paperdoll browser now imports `review.js` and `inventory_fit.js` from this directory. All 63 jewelry groups
are accepted and the main equipment, held-armor, jewelry and latest-repair queues are empty. Accepted-only
artwork mode uses the canonical staged exports. Newer browser edits are preserved by the timestamp import.

## Full-folder result: originals cannot yet be retired

[Open the eight gaps](http://127.0.0.1:8899/level_generation/ui/hud_inventory/finalization_20260926/remaining.html).

| Remaining artwork | Finding |
| --- | --- |
| `7item344.bmp` — Shadow's Mask **inventory** sprite | Missing from the prior inventory review. Its native source is `sources/native_overrides/7item344.bmp`, while review selection looked up that path in a runtime-path usage census. Its equipped `vN` variants are already accepted. No reviewed inventory candidate exists. |
| `6backdol.bmp` | Paperdoll background candidate has no approval receipt. |
| `7backdoll.bmp` | Paperdoll background candidate has no approval receipt. |
| `backdol3.bmp` | Paperdoll background candidate has no approval receipt. |
| `backdol4.bmp` | Paperdoll background candidate has no approval receipt. |
| `backdoll.bmp` | Paperdoll background candidate has no approval receipt. |
| `backelff.bmp` | Paperdoll background candidate has no approval receipt. |
| `backelfm.bmp` | Paperdoll background candidate has no approval receipt. |

These backgrounds are live character-table selections; `GameplayPartyOverlayRenderer.cpp` loads
`backgroundAsset` when constructing the doll composite. They were outside the approved body/limb and equipment
acceptance scopes. The mask is an actual inventory-table item, not an unused equipped variant.

The audit checks **14,735 current original raster files**, verifies **12,658 approval records** across the
existing slices, and identifies **9,607 distinct approved targets**. This is an audit of all approval authorities,
not a claim that all 9,607 were imported into the canonical ledger in this equipment transaction.

| File disposition | Count |
| --- | ---: |
| Approved exact-2× replacement at the same logical namespace/name | 9,609 |
| Same-name, identical-source aliases of approved art | 307 |
| Unapproved live backgrounds | 7 |
| Missing inventory coverage | 1 |
| Unused equipped variants | 309 |
| Metadata-only head/beard names | 17 |
| Excluded legacy UI | 2,011 |
| Excluded unreferenced art | 1,593 |
| Preserved MM9 exclusion | 881 |

Original-format siblings and the verified native override are mapped by namespace/name while retaining their
individual source hashes. The approved Arcomage `sprites.pcx` atlas is included. Seventeen head/beard names are
metadata rather than separately rendered head layers; 309 equipment images are not selected by the current
item/body/pose resolver. Their lack of approval is not counted as missing live artwork. Exclusions and MM9 are
reported separately rather than silently accepted.

See [complete measured coverage](icon_coverage.json), [per-file CSV](icon_coverage.csv), and
[summary](icon_coverage_summary.json). The report also retains overlapping older approvals and identifies the
selected later dedicated review, so shared inventory/equipment images do not acquire competing runtime files.

## Required before a restored-only runtime cutover

1. Restore/review the missing Shadow's Mask inventory sprite and approve the seven backgrounds. Correct the
   source-override usage join when preparing the additional inventory review, preserving the historical 770-item receipt.
2. Consolidate the remaining already-approved HUD, NPC/PC portrait, spell/page and effect records into the
   canonical staging manifest, using the verified receipts and explicit supersession in this audit.
3. Integrate the recorded placement and sizing data. The 576 item/body/slot offsets cannot be represented by
   globally changing `items.txt` equip X/Y. Apply that scoped data in shared equipment placement; preserve the
   inventory cell fitting and jewelry scaling separately. Include same-sprite wand inheritance already saved
   in the placement proposals.
4. Introduce a restored-only icon lookup policy and test package-qualified/unqualified paths, extension
   selection and native logical dimensions. `prefer_restored_icons=true` currently still allows native fallback.
   The existing tier name is `icons_x2`; simply renaming it `icons_new` would lose the loader's x2 scale contract
   unless that name is explicitly supported. New files must retain the same logical dimensions.
5. After coverage and in-game validation, move originals **outside mounted development/package roots**, with a
   source/archive manifest and remapped restoration-source references. A `legacy/` directory inside a mounted
   asset package may still be indexed. Preserve the separate MM9 scope explicitly and rebuild packages without
   archived originals. Verify lookup never touches the archived paths.

The current eight gaps prevent this cutover. No loader change or native-folder move has been made in this pass.

## Validation and reproduction

[equipment_validation.json](equipment_validation.json) verifies all source/art hashes, exact x2 dimensions,
complete acceptance scopes and preserved table bases. An idempotent second `--apply` validates the already-applied
ledger without changing it. [browser_checks.json](browser_checks.json) verifies canonical accepted-only drawing,
zero remaining reviewed-slice targets, all 728 placements, all 63 jewelry groups and preservation of newer notes.
The full icon audit verifies the other slices' source/art hashes and both aggregate PC-portrait approval digests.

```sh
python3 -B level_generation/ui/hud_inventory/finalization_20260926/accept_equipment.py --apply
python3 -B level_generation/ui/hud_inventory/finalization_20260926/audit_icons.py
python3 -B level_generation/ui/hud_inventory/finalization_20260926/publish_review.py
node level_generation/ui/hud_inventory/finalization_20260926/test_browser.mjs
```

The browser test needs the repository HTTP server on port 8899 and uses an isolated Chrome profile. No engine
code or runtime data changed, so no game build was required. These scripts replay this frozen transaction;
future approvals require a new capture and explicit scoped import rather than modifying these receipts.
