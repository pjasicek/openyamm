# Gloves and jewelry candidates — 2026-09-26

Subsequent [shared-image classification and inventory sizing](../jewelry_inventory_20260926/README.md) consolidates
these 79 items into 63 distinct review images. The prepared files below remain preserved; current selectors review
one normal image per exact-native alias family. The extended browser check now writes evidence to that new folder.

Fixes the native fallback reported in `test_img/2046.png`. Of 79 distinct equipment icons, 43 already had canonical
accepted art and three had review candidates. This pass connects the remaining **eight gloves and 25 jewelry
icons**: 26 retained-sheet extractions and seven exact-source donor copies. All **18 gloves and 61 jewelry icons**
now have exact-2× RGBA images. No imagegen, new acceptance, runtime installation or table changes.

The original `backhand` panel is still native; it had no retained restoration. This does not affect which art is
used for the glove, amulet and ring sprites drawn over it. [Open Fleetfingers](../index.html?item=517&art=candidate).

`manifest.json` records exact native/raw/output hashes, measured rectangles, sampling, matte extraction and donor
provenance. The contact sheet was inspected for complete items and neighboring-cell contamination. Conservative
boundary and registration findings remain attached for user review; preparation does not grant visual approval.
The scoped [magenta screen](magenta_scan/report.json) covers all 36 pending images and 49 alternatives: no selected
candidate is classified as suspected spill, and five have purple-material checks shown in the browser.

The selection dropdown now includes Gloves, Amulet and all six ring slots. Space advances that slot; Shift+Space
accepts its displayed image without advancing; arrows nudge one native game pixel. Item next/previous buttons,
direct selection and Tab body-type cycling retain the overlay. F1–F9 return to body equipment. Duplicate rings
can be selected and adjusted in their individual slots. Existing storage keys and approval imports are unchanged.

Rebuild only this group without rewriting the existing weapon preparation:

```sh
python3 -B level_generation/ui/hud_inventory/paperdoll_review/prepare_inventory_candidates.py --group jewelry
python3 -B level_generation/ui/hud_inventory/paperdoll_review/build.py
python3 -B level_generation/ui/hud_inventory/paperdoll_review/scan_magenta.py --group jewelry
python3 -B level_generation/ui/hud_inventory/paperdoll_review/verify.py
node level_generation/ui/hud_inventory/paperdoll_review/test_jewelry.mjs
```

The browser test uses a fresh temporary Chrome profile on port 9247, with the review server on port 8899. It checks
all 79 actual selected images, exact dimensions, eight jewelry modes, overlay continuity, native comparison,
slot-specific nudges, accepting/skipping, note editing, queue selection, F1–F9 and reload persistence. It verifies
all prior 1,225 approvals and 726 placement records remain intact. It never opens or modifies the live profile.
