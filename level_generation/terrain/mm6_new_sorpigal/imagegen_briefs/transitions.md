# Transition preparation

Generate/review shared material masters before rebuilding any mixed tiles. The numbered/native suffixes are identifiers, not permission to rotate or mirror artwork. Inspect each source and its actual-map context.

Grass/dirt and rock/dirt: the native source is opaque artwork; no true material alpha exists. A material-coverage mask must be derived and reviewed across the whole family. Match adjoining edge coverage and shared material texture phase. Preserve intentional islands and silhouette structure unless a later task explicitly changes them. Do not independently regenerate each mixed tile.

Roads: nine pieces are actually used. There is no standalone native road material in this map. Use the road reference sheet for a master, then preserve each road footprint and its edge connections.

Water: rgba/6wtrdr*.png contains exact visible shoreline overlays. alpha/shore_visible is white for visible shore; alpha/water_opening is its inverse. These are source masks, not imagegen-specific edit masks. Check the edit tool mask convention before use. Keep masks separate from generated RGB; reapply them during composition. Pure 6wtrtyl is a static fallback; the runtime uses the 14 listed water_mm6 frames. Do not paint cyan key pixels as water or independently animate the land.

Review complete families at native, target and mip sizes, and in contexts/*.png layouts. Reference sheets contain labels for humans; individual source_rgb/ and rgba/ images are unlabelled inputs.
