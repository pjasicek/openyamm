# Jewelry feedback repairs — 2026-09-26

[Open the two repaired images](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?review=latest&hide_accepted=1&item=150)
and refresh with Ctrl+Shift+R. The active overlay is `jewelry_repairs_20260926/review.js`.

## Changes

| Item | Feedback addressed | Result |
| --- | --- | --- |
| Shadow Sect Medallion (`item150`) | Too yellow/gold | Broad metal changed to white/silver; emerald insets and fine gold trim retained. New artwork needs review. |
| Fine Ring (`ring1`) | Top cut off | Complete pearl and ring recovered from the retained Dense64 master. New crop needs review. |
| Paladin Gauntlets (`gontlet3`) | Too big | Jewelry display scaled uniformly to 74.07%, about its existing center. Accepted image unchanged. |
| Ethereal Ring (`ring6`) | Too big | Jewelry display scaled uniformly to 80%. Accepted image unchanged. |
| Scarab Ring (`ring10`), including Igraine and Athena | Too big | Shared jewelry display scaled uniformly to 76.19%. Accepted image unchanged. |

The repaired Fine Ring and medallion also use uniform display fitting (80% and 94.12%) within their jewelry
slots. The PNGs keep their exact native-times-two canvas sizes. These display factors are separate from the
inventory fitting already proposed: rings 1×1 cells, gauntlets 1×2, amulets 1×1 or 1×2. No image is stretched or
cut to fit. Manual x/y deltas are preserved and arrows still move by one native pixel.

## Captured acceptance and placement state

The latest browser capture is **2026-09-26 15:49:48.968 UTC**, newer than the earlier five-flag classification.
It contains **1,260 decisions, 1,258 approvals and 728 placement records**. The user had subsequently approved
the three size-related images and the old Fine Ring crop. Those exact approved files are staged and retained;
only the medallion and the new Fine Ring crop require another artwork review.

There are **79 item definitions / 63 distinct image groups: 61 accepted, two replacements to review**.
The old Athena alias flag remains archived verbatim; shared Scarab Ring review uses the newer normal-item
approval. Main equipment and held-armor queues remain complete. There is no new automatic acceptance.

- [Original browser capture](browser_state.original.json), [preserved review](review.original.json).
- [Staging manifest](stage_manifest.json): 33 newly staged files plus 1,225 prior staged files reused by hash.
- [All placement records](placements.json) and [728 placement proposals](placement_proposals.csv).
- [Inventory and jewelry sizing](inventory_fit.json), [common-image/scale proposals](shared_image_proposals.csv).
- [Prior six inventory-footprint changes](items_table_proposals.csv), retained for later runtime integration.

The browser imports this pass once, backing up existing storage and preserving newer local edits by timestamp.
The canonical ledger, runtime tables and installed assets remain unchanged. Final ledger acceptance remains
deferred until the user approves the entire slice.

## Artwork provenance

The medallion used one **built-in imagegen edit**, with the previous restoration as edit target and the native
sprite as color reference. The [exact prompt](generated/item150-prompt.txt),
[edit target](generated/item150-edit-target.png), [native reference](generated/item150-native-reference.png),
and [generated master](generated/item150-raw.png) are retained in this workspace.
The [final 68×106 PNG](repaired/engine--icons--item150.bmp.png) preserves transparency.

The Fine Ring used no generation. Its earlier crop `[65,415,249,526]` cut through the pearl. Re-extraction from
`chat_bundles/dense64_20260916/dense64_inventory_001/outputs/raw/S001.png` using search box `[40,370,280,550]`
recovers the complete silhouette. See the [recovered master](generated/ring1-recovered-master.png) and
[final 80×48 PNG](repaired/engine--icons--ring1.bmp.png). Both new sprites are uniformly fitted to the required
canvas with a transparent margin. [Repair records](repairs.json) retain source hashes, previous versions and
placement-compatible hashes. The original approved Fine Ring is preserved in `staged-accepted/`.

## Validation

[Asset validation](validation.json) checks source/candidate hashes, all approvals/placements and unchanged
ledger hash. [Magenta scan](magenta_scan.json) reports no spill on either new image.

[Isolated Chrome checks](browser_checks.json) verify all 1,260 decisions and 728 placements, both pending
replacements, five slot fits, zero inventory overflow, one-pixel keyboard movement, unchanged original
comparison panels, both Scarab Ring aliases and preservation of newer local notes/offsets on import.
Screenshots include [the browser](browser.png), [medallion](item150-current.png),
[Fine Ring](ring1-current.png), [gauntlets](gontlet3-current.png), [Ethereal Ring](ring6-current.png)
and [Scarab Ring](ring10-current.png), with corresponding `*-original.png` comparisons.

Reproduce from the repository root, with the HTTP server running on port 8899:

```sh
python3 -B level_generation/ui/hud_inventory/paperdoll_review/jewelry_repairs_20260926/prepare.py
node level_generation/ui/hud_inventory/paperdoll_review/test_jewelry_repairs.mjs
```

Preparation replays this fixed capture; it is not a collector of future browser reviews. The browser test uses
its own temporary Chrome profile and does not write to the user's profile.
