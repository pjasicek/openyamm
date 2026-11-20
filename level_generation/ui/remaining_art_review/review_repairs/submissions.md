# Imagegen submissions for the 2026-09-24 review repairs

All eleven calls used the built-in imagegen tool with the local PNG references named below. The raw outputs are in
`returns/`; `effect_jobs.json` and `inventory_jobs.json` record reference hashes and cells. The two processing reports
record each output hash, registration and fitted 2× artifact. No ESRGAN was used.

## Effects

### `effects-fire.png`

Reference: `references/effects-fire.png`

> Use case: precise-object-edit. Asset type: game spell animation sprites. The attached image is a 4-column by 2-row contact sheet of SEVEN different original animation frames, with the eighth cell empty. Restore each original frame into clean high-detail 2D painted game art while preserving its exact identity, phase, color, silhouette, internal swirls, and position. These are gold and brown smoky oval swirl effects. Each frame stays entirely inside its own 300 by 380 cell, with at least 25 pixels of transparent padding all around; preserve all seven as separate objects and leave the eighth cell empty. Do not enlarge or crop any swirl at a cell edge. Keep a genuinely transparent background and transparent openings between tendrils. No magenta, no checkerboard, no cell outlines, no labels, no text, no neighboring content in a cell. Return one 4 by 2 spritesheet matching the reference layout.

### `effects-cloud.png`

Reference: `references/effects-cloud.png`

> Use case: precise-object-edit. Asset type: game spell animation sprites. The attached image is a 3-column by 2-row sheet of SIX distinct original frames. Restore the six white-gray wind/cloud oval effects as richly painted smooth game sprites. Precisely preserve each frame's phase, silhouette, wispy strands, large irregular see-through central holes and all transparent gaps. The gaps are essential; do not fill them into solid balls or rings. One full uncropped sprite per 300 by 380 cell, with at least 25 pixels clear transparent padding to every cell edge. Keep a genuinely transparent background. No magenta, no checkerboard, no cell outlines, no labels, no text, no content from adjacent cells. Return one 3 by 2 sheet matching the reference layout.

### `effects-sparse.png`

Reference: `references/effects-sparse.png`

> Use case: precise-object-edit. Asset type: game spell animation sprites. Attached image is one row of FOUR distinct source frames. Restore each as high-detail 2D game art, keeping exact phase, sparse fragmented silhouette, color, and transparent voids. Cell 1 is scattered small brown rocks and pale glints. Cells 2 to 4 are different sparse blue-white jagged magical arc fragments. Do not join fragments into a filled circle or expand them until clipped. One full uncropped sprite per 300 by 380 cell, at least 25 pixels transparent padding on each side. Genuinely transparent background; no magenta, no checkerboard, no lines, no labels, no extra objects. Return one 4 by 1 sheet matching the reference.

## Inventory and UI

### `portraits.png`

Reference: `references/portraits.png`

> Use case: precise-object-edit. Asset type: two framed fantasy inventory portraits. Reference image has TWO separate portraits, left and right, on magenta matte. Restore both portraits as refined painted 2D game sprites with smooth detail. Keep each original person's identity, face shape, crown/hair, clothes, frame, red background at left and blue background at right. LEFT: male ruler with crown and black coat; his mustache belongs ONLY immediately above his mouth, without a large full beard or facial hair extending across the lower cheeks or chin. RIGHT: brown hair visibly frames the man's head; it is hair, not a hood or cape. His striped dark cloak remains on his shoulders. Exactly one full portrait in each half, no changing pose, crop or proportions; transparent outside the frame, no magenta spill, no text, no added ornament.

### `inventory-a.png`

Reference: `references/inventory-a.png`

> Use case: precise-object-edit. Asset type: four isolated fantasy RPG inventory sprites. Reference is one row of FOUR originals on magenta matte; preserve the four different objects and their exact proportions, colors, orientation, visible structure and empty spaces. Left to right: 1 a mostly EMPTY CLEAR GLASS BOTTLE with old brass/olive metal top and base, transparent clear glass body, no pink liquid or pink glass; 2 a long horizontal dark brass telescope/instrument with BOTH ends fully present; 3 an upright rectangular purple faceted crystal/prism with its white etched pattern and full top/bottom; 4 a dark gray hooked axe/war tool with the characteristic large black center gap, no new gold ornament. Paint genuine 2D game sprite detail, one whole object in each of four equal cells, ample transparent padding, no cropped parts. Transparent background, no magenta, no cell lines, no text.

### `inventory-b.png`

Reference: `references/inventory-b.png`

> Use case: precise-object-edit. Asset type: four isolated fantasy RPG inventory sprites. Reference is a row of FOUR different originals on magenta matte. Restore with richer but faithful painted 2D game art and genuine alpha. Preserve each specific object's silhouette, component count and palette. Left to right: 1 paired BRIGHT LIME-GREEN and YELLOW bells on a thin green decorative cord; retain vivid green and both bell forms, never turn all gold. 2 a weathered matte GRAY circular stone or metal medallion with the dark angular curved engraved mark, not a smooth blank sphere. 3 ornate ring with a prominent saturated GREEN center gemstone and multicolored small gems; avoid purple/magenta dominating. 4 a compact GOLD winged bat/skull emblem with only the ORIGINAL tiny red eye or stone, never a large purple central gem. Four separate whole objects, one per equal cell, 25+ pixels of transparent padding, no crop, no added objects, no magenta spill, no lines or text.

### `inventory-c.png`

Reference: `references/inventory-c.png`

> Use case: precise-object-edit. Asset type: four isolated fantasy RPG inventory sprites. Reference is a row of FOUR originals on magenta matte; preserve the identity, silhouette, orientation, palette and small structure of EACH. Left to right: 1 antique brass key with dull GOLD/BROWN jewels in its bow, no pink or purple jewels; 2 tall heraldic shield with original steel grille on upper half, PURPLE left panel and aged gold/green right panel bearing embossed lion; the purple panel is intentional but no fluorescent magenta fringe; 3 tall wood and steel crossbow with thin brown/dark bowstring, no magenta or pink string; 4 tall staff topped by a ram skull with its ORIGINAL OPEN TRANSPARENT HOLE near upper right of skull, never fill hole with an added gem. Restore painterly sharp detail from source. Keep all parts visible with transparent padding in each of four equal cells. Genuinely transparent background, no magenta spill, no cell lines, no text.

### `status-gems.png` (first attempt, superseded)

Reference: `references/status-gems.png`

> Use case: precise-object-edit. Asset type: four tiny fantasy game UI status gems. Reference is one row of FOUR near-identical icons on magenta matte. Restore the SAME rustic bronze-gold rounded rectangular frame with its dark olive outer border and bright gold glint at upper right in all four cells. The central inset jewels are, left to right: pale blue-gray, emerald green, rose red, golden yellow. Preserve the original inset shape, frame thickness, rounded corners, proportions and colors; do not replace with black/steel beveled frames. Each full icon stays separate and centered in its equal cell with generous transparent padding. Genuinely transparent background, no magenta fringe, no letters, no text, no cell lines.

The first attempt retained enlarged pixel blocks, so it is not offered in the viewer.

### `status-gems-smooth.png` (selected)

References: `references/status-gems-current.png` (current smooth edit target), `references/status-gems.png` (native frame colors).

> Use case: precise-object-edit. Asset type: four 2D fantasy game status icons. Image 1 is the CURRENT smooth restored sheet and is the edit target; Image 2 is the pixelated ORIGINAL sheet and is the authoritative color/shape reference. Output ONE ROW of four separate smooth, detailed painted icons, one per equal cell. Keep Image 1's smooth high resolution painting, jeweled centers, proportions and exact four positions. Change the outer frame to match Image 2: rustic dark OLIVE-GREEN stone outer border, warm worn BRONZE-GOLD inner frame, with a single small bright gold glint near upper-right corner. Do not retain the current slate-gray metallic outer border. Preserve jewel colors pale blue-gray, emerald green, rose red, yellow in that order. Do not produce pixel art or visibly blocky staircase pixels: the result must be smooth restored art at this large size. Genuinely transparent background, no magenta, no text, no cell lines.

### `review-notes.png`

Reference: `references/review-notes.png`

> Use case: precise-object-edit. Asset type: three small fantasy game UI sprites. The reference is ONE ROW of THREE different original sprites on magenta matte. Restore each into smooth, sharp, high-detail hand-painted 2D game art while preserving its exact identity and original silhouette. Left cell: an opaque rectangular town portal picture, a small reddish-brown castle or city frontage resting on pale gray cracked stone ground; keep the WHOLE rectangular scene and all four corners, with no horizontal magenta band or neighboring cell content. Center cell: a tiny bronze-gold spiked circular eye amulet with a small loop at its top, central RED eye, all spikes visible, sharp detail. Right cell: a thin hanging GOLD necklace cord with an oval GREEN stone pendant in ornate gold setting, preserve the complete cord and jewel. One full object per equal cell, ample clear transparent gutter around each; only the left object's own rectangular stone background is opaque. No clipped edges, no magenta pixels, no checkerboard, no text, no labels, no extra objects.

### `spill-regens.png`

References: `references/spill-regens.png` (native objects), `references/spill-regens-current.png` (existing detail).

> Use case: precise-object-edit. Asset type: two fantasy game inventory sprites. Image 1 is the AUTHORITATIVE pixelated original of each item; Image 2 is a current smoother candidate shown only for painting style and detail. Produce ONE ROW with exactly TWO separate full sprites. LEFT: a tall narrow reddish wooden bow oriented vertically with silver grip hardware and a COMPLETE thin pale gray bowstring running taut from top tip to bottom tip. Keep the full top tip, full bottom tip and the bowstring, without the candidate's pink/magenta stains on the string. RIGHT: a tiny gold ornate ring or jeweled orb on a circular lower base. The lower base in the original has an aged BRONZE-BROWN band and small ivory or silver bead ornaments; remove the candidate's broad hot-pink band completely. Preserve small deep RED jewels on the upper orb. No other pink/magenta. Keep separate objects centered in two equal cells with transparent padding, genuinely transparent background, no crop, no labels, no cell lines.
