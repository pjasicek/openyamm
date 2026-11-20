# Inventory and ground sprite reuse

Run `python3 -B level_generation/ui/remaining_art_review/review_repairs/world_item_links/build.py` from the repo root.
It follows `assets_dev/engine/data_tables/items.txt` (`Pic File`, `Sprite Index`) to
`assets_dev/engine/data_tables/object_list.txt` (`ObjectId`, `SpriteName`), then to the approved
`assets_dev/engine/decorations_x2/manifest.json` bindings.

The report requires matching native foreground alpha shapes and a strong RGB correlation before calling two
drawings the same. The two pearls with coincidental alpha shapes are excluded. Approved world artwork is fitted
to the original inventory canvas without clipping: exact placement when possible, translation when enough room
exists, and uniform scaling of the whole foreground for oversized masters.

Of 770 inventory targets, 139 have the same native drawing as a linked approved world sprite. The donor provides
the accepted inventory art for 138: 112 exact placements, two translations, and 24 uniform fits. `item160` and
`item162` retain the exact world pixels. The one reverse case is `7item263`: its approved inventory art also
replaces the installed `7obj263_p9` ground image. The [review acceptance ledger](../../review_acceptance.json)
records the chosen candidates.
