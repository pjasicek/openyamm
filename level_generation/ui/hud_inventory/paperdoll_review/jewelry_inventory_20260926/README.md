# Jewelry inventory footprints and shared images — 2026-09-26

All **79 items** in the merged `items.txt` Gauntlets/Amulet/Ring rows are accounted for. The exact native rendered
images form **63 distinct groups**: 17 glove images, 15 amulet images and 31 ring images. Sixteen duplicate item
images belong to twelve shared families. Compare pixels after the normal item-profile transparency conversion;
only RGB beneath fully transparent pixels is ignored. Dimensions and equipment category must match. There is no
similarity-based or name-based merging.

The user's captured review is preserved verbatim in `browser_state.original.json`: **1,260 decisions and 728
placement records**, captured at 12:41:49 UTC. The individual items had 72 accepted, six flagged and one unreviewed.
After grouping there are **58 accepted image groups, five flagged groups, zero unseen image groups**. Igraine's
unreviewed file is the same original image as the already-reviewed Scarab Ring. Its group remains flagged.
No new approval was granted. Notes, offsets, previous staged files, canonical checkpoint entries and image pixels
are preserved. The narrowly scoped earlier-approval import repair below updates twelve already-authorized snapshots.

## Shared-image classification

The normal item is the representative for each group. Artifact/relic/special names are listed on its selection
option and inventory preview, and searching any alias finds the one shared review entry. Alias item/target links
resolve to the representative. Notes recorded on aliases remain visible as saved alias feedback.

| Normal item | Items sharing exactly the same original image |
| --- | --- |
| Bronze Ring | Cycle of Life |
| Gemstone Ring | Ring of Planes |
| Ruby Ring | Ring of Fusion |
| Dragon Hide Gauntlets | Forge Gauntlets |
| Dazzling Ring | Faerie Ring |
| Wizard Ring | Ghost Ring |
| Angel's Ring | Lady's Escort |
| Death's Head Pendant | Medusa's Mirror |
| Sun Amulet | Clanker's Amulet |
| Lunar Ring | Guinevere, Aphrodite |
| Scarab Ring | Igraine, Athena |
| Ruby Star Amulet | Morgan, Hera, Fire Amulet |

Six of these families had divergent restored candidates despite identical native images. The staged
`shared_image_proposals.csv` maps every item to its normal representative's selected artwork, for **both inventory
and jewelry overlay**. Older independently restored files and their approvals remain archived in their existing
locations. This proposal does not install aliases or alter the canonical acceptance ledger.

## Inventory fit

| Items | Staged footprint |
| --- | --- |
| All 41 rings | 1×1 cell |
| All 18 gauntlets | 1×2 cells |
| Five short amulets | 1×1 cell |
| Fifteen tall amulets | 1×2 cells |

One cell is 32×32 logical game pixels, or 64×64 at 2×. Inventory drawing centers the complete image canvas inside
the allocated cells and uniformly shrinks only when needed. It never stretches, crops or enlarges the art. The
browser's inventory card renders this independently of the paperdoll preview; paperdoll image placement is intact.

The current engine converts scaled textures to logical dimensions before calculating inventory slots. Its native
slot rounding allows up to 13 pixels of overhang, so occupying one cell did not mean fitting entirely within it.
The normal canvas-derived rules also give the five `gontlet1`–`gontlet5` MM6 gloves and `amulet2` (Gothic Amulet)
three cells. `items_table_proposals.csv` stages explicit 1×2 dimensions for these **six items**. All other occupied
cell counts already match the requested policy. `inventory_fit.csv` records every item and its drawing scale;
42 of 79 original canvases need reduction to remain strictly within the cells.

**Runtime application remains deferred.** At installation, both parts are required: apply the six item-table
width/height proposals and the inventory-only uniform-fit drawing policy. Merely changing table dimensions would
leave tall images overlapping other cells. The draw scale must also cover held/cursor inventory art; it must not
change paperdoll or world-sprite sizing. All image aliases should resolve to the same representative file under
the normal asset scale-tier system. Do not install 2× PNGs as unscaled BMP replacements.

References inspected locally: `game/tables/ItemTable.cpp` (logical image size, slot rounding, optional authored
inventory dimensions), `game/ui/GameplayPartyOverlayRenderer.cpp` and `GameplayHudOverlayRenderer.cpp` (centering),
`assets_dev/engine/ui/gameplay/character.yml` (448×288, 14×9 grid). The local OpenEnroth reference confirms the same
native slot rounding; no reference code was copied.

## Review and validation

[Open the five remaining image groups](http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?review=jewelry&hide_accepted=1&item=1731).
Clear Hide accepted / staged to see all 63 groups. The live toolbar count covers all 79 item definitions.
Export review JSON includes inventory sizing and shared-image proposals alongside the current decisions and offsets.
The proposal file's review fields describe the immutable captured state; live decisions remain authoritative.

Remaining notes are Paladin Gauntlets (size), Shadow Sect Medallion (gold versus white color), Fine Ring (cut off),
Ethereal Ring (size), and Scarab Ring/Igraine/Athena (size). Inventory fitting does not silently approve these flags.

The captured browser had imported the 14:11 acceptance overlay before its twelve approved offset snapshots were
finalized, leaving the header at twelve remaining armor images. `approval_snapshot_sync.js` carries only those
original/approved record pairs from the immutable `acceptance_snapshot_20260926_1411/offset_sync.json` receipt.
The one-time migration requires an exact old decision match and the exact authorized current delta, backs up each
changed record and leaves all placement records untouched. Cleared decisions and newer edits are not replaced.
Main equipment and held armor then correctly show zero remaining; the five jewelry flags stay visible.

```sh
python3 -B level_generation/ui/hud_inventory/paperdoll_review/jewelry_inventory.py
node level_generation/ui/hud_inventory/paperdoll_review/test_jewelry.mjs
```

The generator checks all 79 source-table rows, actual 2× image dimensions/hashes, full-canvas fit and exact source
equivalence. Browser checks exercise all 63 displayed image groups, eight selection modes, actual grid overflow,
alias search, review coverage, export, and preservation of the captured review state in an isolated Chrome profile.
See `browser_checks.json`, `browser.png`, `inventory_fit.json`, and the CSV proposals.
