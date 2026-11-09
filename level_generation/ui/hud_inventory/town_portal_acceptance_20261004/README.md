# Installed MM7/MM8 Town Portal corrections — 2026-10-04

The user approved the corrected backgrounds and requested matching buttons and deployment to `assets_dev/*`.
Both backgrounds and all twelve destination hover images are accepted and installed in
`assets_dev/engine/icons_x2/`, with lowercase filenames and 0644 permissions.

| World | Background | Matching destination highlights |
| --- | --- | --- |
| MM7 | `antagrich.png` | `tpharmon`, `tpavli`, `tpwarl`, `tpisl`, `tpheav`, `tpdeja` |
| MM8 | `townport.png` | `tp_alvar`, `tp_ravenshore`, `tp_balthazarlair`, `tp_regna`, `tp_shadowspire`, `tp_daggerwoundislands` |

The [MM7](../town_portal_fixup_review/mm7/) and [MM8](../town_portal_fixup_review/mm8/) comparison pages read
these immutable accepted exports. Maps retain their 1280 × 960 physical and 640 × 480 logical canvas.
Button normal crops exactly match the maps. Hover light stays inside a feathered mask with four unchanged
pixels around each border; native draw/hit rectangles and image sizes remain unchanged.

The matching buttons were already generated from the corrected maps in the preceding turn. Deployment rechecked
them and published their exact bytes. Fourteen images belong to this revision; eleven needed runtime replacement,
while three MM7 hover exports already matched their installed bytes.

[authority.json](authority.json), [accepted.json](accepted.json), individual `receipts/` and [installed.json](installed.json)
record user authorization, selected hashes, previous acceptances and deployment. Earlier source and accepted artwork
remain preserved. `previous_accepted_index.json`, `checkpoint.before.json` and `review_before/` capture the predecessor.
The canonical index and acceptance ledger now reference this fourteen-image revision.

[validation.json](validation.json) verifies runtime hashes, dimensions, permissions, acceptance evidence and preservation
of unrelated ledger/index records. The current-index installer validated all 9,920 accepted targets: 9,430 active,
490 explicitly retired, and 9,616 active cells. No pending deployment remains. Both accepted browser previews also
pass six-destination hover pixels/reset, hit-area and keyboard-selection checks.

Publication uses frozen target contracts and existing acceptance evidence. Current generation-only UI inputs are
not consumed during this exact-byte acceptance/deployment. No new generation or runtime code changes were needed.

```sh
python3 -B level_generation/ui/hud_inventory/deploy_icons.py --check
python3 -B level_generation/ui/hud_inventory/town_portal_acceptance_20261004/publish.py --check
```

This deployment targets loose development assets. Release ZIP packaging remains a separate operation.
