# Recorded runtime input changes — 2026-09-27

During MM7 Town Portal acceptance, the frozen icon queue detected three existing runtime file changes:

- `chest_data.txt`: `GridOffsetX` for chest IDs 1 and 2 moved from 18 to 42.
- `character.yml`: `CharacterInventoryGrid` moved from offsets 5, 6 to 7, 8.
- `chest.yml`: `ChestNestedInventoryGrid` moved from offsets 5, 6 to 7, 8.

The [reconciliation recipe](reconcile.py) verifies that these are the only changed values, retains the original
and current file bytes, and pins both versions in [receipt.json](receipt.json). The original snapshots are checked
against the frozen catalog hashes. Asset bindings, image canvases, native bitmaps, Town Portal placement, frozen
catalog and job definitions are unchanged. This migration preserves the existing runtime edits.

The canonical ledger gains an `input_reconciliation` pointer and receipt hash. No existing ledger entry is replaced
by this migration. `checkpoint.before.json` and `checkpoint.reconciled.json` retain its exact state transition.
The queue now validates explicitly reconciled input hashes and immutable snapshots; unrecorded changes still fail.
It does not waive input checks or edit the historical catalog to make the new files look original.

Seven focused tests in [test_input_reconciliation.py](../test_input_reconciliation.py) cover strict behavior without
a receipt, exact reconciliation, future drift, altered receipts, wrong catalog/baseline, unknown inputs, and
changed snapshots. The normal current-index deployment checks also run after this migration.
