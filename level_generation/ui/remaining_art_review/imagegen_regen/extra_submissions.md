# Additional imagegen submissions

All calls used the built-in `image_gen` editing tool with the listed local reference image. The text blocks below are
the submitted prompts; the returned raw PNGs remain unchanged under `returns/`. First-pass and regular retry prompts
are retained separately in `prompts/` and `retry_prompts/`. No prompt or return implies art acceptance.

## makeme-direct

Reference: `../originals/engine--icons--makeme.pcx.png`  
Raw return: `returns/makeme-direct.png`

```text
Precisely restore this Might and Magic VIII Create Character UI screen at higher resolution. Use the attached original as the exact image to edit, preserving its 640:480 aspect ratio and every element in its original location and size. Restore detailed smooth green-gray stone texture across the ENTIRE screen background, including the full left margin, gaps between controls, and bottom border. Preserve the original "Might and Magic VIII" logo, "Create Character" heading, Name, Class, Portrait, Voice, Bonus Pool, Skills, and Available Skills text exactly, and keep every box at its original bounds. The large black rectangle at upper right is the ONLY transparent hole; it begins near x=452, y=54 and ends near x=626, y=434 in original coordinates. Leave this one rectangle genuinely transparent, not black, and preserve a thin dark border. The other dark boxes have opaque textured stone inside. This is a full-screen flat UI texture, NOT isolated floating foreground panels. No re-layout, no recentering, no added text or decoration, no holes anywhere else. Render a high-resolution painted restoration with continuous fine detail, not enlarged source pixels.
```

## third-inventory-keys

Reference: `references/third-inventory-keys.png`  
Raw return: `returns/third-inventory-keys.png`

```text
Restore the NINE separate Might and Magic inventory sprites in the attached 3-column sheet. This is a precise edit of the attached sheet: keep all nine objects in their existing cells, each with the SAME outer silhouette, length, thickness, orientation and placement. The two long objects in the top row are a gold ritual polearm with side blades and a slender blue metal staff; keep the staff especially thin. The lower seven are seven DIFFERENT keys, each with the exact head, tooth count, tooth placement and shaft length shown; do not turn them into a matching set or add extra teeth. Do not fill missing holes in any key. Reconstruct smooth painted metallic contours and fine detail from the blocky reference, so the result is genuinely restored art rather than pixelated interpolation. Use genuine transparency around every isolated sprite; the magenta is just a temporary matte. No other objects, labels, grid lines or background. Keep ample separation and the exact 750:1200 sheet framing for precise extraction.
```

The ninth prepared cell extended beyond that reference canvas and was absent from this return. It was included in the
next three-item sheet instead. The corrected extraction plan lists the eight visible cells only.

## third-inventory-fragments

Reference: `references/third-inventory-fragments.png`  
Raw return: `returns/third-inventory-fragments.png`

```text
Precisely restore these THREE separate Might and Magic inventory sprites from the attached 3-column sheet. Keep the same three objects and their original silhouette, orientation, relative size, placement, color and material. Left: a narrow bronze key with three round lobes at the head and a broad dark metal tooth at the base. Center: a short open curved silver horseshoe-shaped metal arc; retain its incomplete open center and exact end locations, do not complete it into a ring. Right: a small dark green four-legged lizard seen from the side; preserve its long raised tail, pose, thin legs and head direction. Smoothly paint detail beyond the blocky source pixels while remaining faithful to the source. Use genuine transparency around each object; magenta is only a temporary matte. Do not enlarge objects relative to their cells, fill the negative spaces, invent extra body parts, merge cells, add labels or a background. Keep the 600:300 sheet framing and wide separation for precise extraction.
```

## third-effects-swirl

Reference: `references/third-effects-swirl.png`  
Raw return: `returns/third-effects-swirl.png`

```text
Edit and genuinely restore the seven separate Might and Magic spell-effect animation frames in the attached 4-column sheet. This is an exact-state restoration, not a redesign. Keep each effect in its existing cell, same outer shape, placement, relative size, density, hue and transparency. The first two cyan-blue swirling ovals must remain CYAN BLUE, the third dark gray stone-patterned oval must stay dark GRAY (not purple), the next two muted mauve spirals stay mauve, and the last two are incomplete clusters of pale blue-white stars, the smaller first cluster remaining sparse. Preserve their distinctive animation-state differences and all transparent gaps. Remove only the magenta temporary matte. Repaint smooth luminous detail beyond blocky source pixels with soft edges. No expanding an object to its cell, no extra stars, no changed color, no merged cells, no labels or background. Keep the exact 1040:680 sheet framing.
```

## third-effects-arc

Reference: `references/third-effects-arc.png`  
Raw return: `returns/third-effects-arc.png`

```text
Edit and restore the EIGHT sequential frames of one Might and Magic lavender magic-arc animation in this 4-column by 2-row sheet. They are separate frame states in left-to-right, top-to-bottom order. Preserve each native silhouette and state progression EXACTLY: first frame is just a tiny faint curved line at the very top; next frames gradually add ONLY the arc bands and then the bright central starburst; later frames fade. In every cell keep the occupied region in its original vertical position and original relative height, leaving most of each cell transparent where the original is empty. Do NOT generate a full-sized dome in the early sparse frames, and do not fill below the original arc. Smoothly restore continuous luminous contours from the blocky reference with violet-white shading, genuine transparency outside the source shape, and no magenta matte. Keep the exact 1040:680 sheet framing, four columns, two rows, wide separation, no captions, no new elements.
```

## third-effects-other

Reference: `references/third-effects-other.png`  
Raw return: `returns/third-effects-other.png`

```text
Precisely edit and restore the FIFTEEN separate Might and Magic spell-effect animation states in the attached 4-column by 4-row sheet. Preserve each cell's exact subject, colors, size, placement, sparse pieces and empty transparent gaps. Read cells left to right then top to bottom. Row 1 has a small red streak then three different incomplete orange fire-ring fade frames. Row 2 has two pale cream wind-ring fade frames then two sparse dark rock debris rings. Row 3 has four THIN pale gold ankh-symbol frames; the final one is magenta-white. Keep their narrow original stroke width and hollow top loop, do not thicken into a solid jewelry charm. Row 4 has three separate incomplete blue-white sparkle clusters, each with different spacing and fading. Restore painted smooth edges and fine luminosity from blocky pixels, never enlarge the subject to fill its whole cell or invent completed circles/extra pieces. The magenta field is only a temporary matte and must become genuine transparency. Keep the exact 1040:1360 framing, four columns, no labels or background.
```

The final ankh color description was wrong. Its source is fading white; a corrected four-frame submission follows.

## third-backhand

Reference: `references/third-backhand.png`  
Raw return: `returns/third-backhand.png`

```text
Restore this exact Might and Magic inventory UI backing graphic from the attached enlarged original. It is a single flat 176 by 345 pixel design shown enlarged 2x inside magenta gutters. Preserve its full rectangle, proportions, all panel locations and sizes: two separate tall green stone slots in the upper half, and one three-column by two-row group of six green stone slots in the lower half. Preserve the thin borders and the dark green charcoal cloudy texture. The checkerlike background between and around the panels is an intentional translucent dark-green veil, not magenta and not empty black; restore it as smoothly painted dark green texture that can later receive a uniform partial alpha. All eight stone slots remain more opaque and slightly brighter than that veil. Do not rearrange, crop, merge, or add compartments. Remove the temporary bright magenta exterior gutter only. Keep exact 376:714 sheet framing and faithfully painted details beyond the blocky source pixels.
```

## third-ankh-palette

Reference: `references/third-ankh-palette.png`  
Raw return: `returns/third-ankh-palette.png`

```text
Precisely restore the four separate successive frames of the SAME pale-gold to warm-white magic ankh symbol in the attached 4-column sheet. All four symbols have the same color family: soft ivory, very pale gold, white highlights. The fourth symbol is fading and dithered WHITE, NOT pink, purple or magenta. Bright magenta is only the temporary background matte and must not appear on any symbol or edge. Preserve each frame's thin stroke width, hollow oval loop, straight crossbar, tapered stem, native size and placement within its cell; the first and fourth frames remain more translucent and sparse. Smoothly reconstruct painted light and subtle glow, not blocky source pixels. Keep four isolated icons with genuine transparent surroundings, no extra glyphs, no changed colors or backgrounds. Keep the exact 1040:340 framing and wide separation.
```

## third-potions-189-198 (superseded)

Reference: `references/third-potions-189-198.png`  
Raw return: `returns/third-potions-189-198.png`

```text
Precisely restore TEN distinct Might and Magic potion inventory sprites from the attached original-reference sheet. Read in exact order, LEFT TO RIGHT across a row of FIVE, then LEFT TO RIGHT across a SECOND row of FIVE. There must be exactly TEN separate bottles, one in each position. Preserve the original silhouette, occupied size, placement, cap, decorative band, liquid color and per-frame differences for EACH bottle. Top row: blue and gold; violet and blue; blue-green; golden amber; pink and gold. Bottom row: lime green and gold; pink-orange; violet-green; orange-green; final pale pink bottle is damaged or partly missing and must remain incomplete as shown. The sixth sprite, first on the bottom row, must stay LIME GREEN and gold, not pink. Paint genuinely smooth restored details beyond the original blocky pixels. Keep all unused cell area genuinely transparent, remove temporary magenta matte completely, and keep all bottles isolated with no overlap or omission. Do not invent a complete bottle where the source is incomplete. Keep exact 750:420 sheet framing, 5 columns by 2 rows, no text or other objects.
```

The reference rows overlapped vertically, and the return fused each pair into one object. This raw return is retained but not used as a candidate.

## third-potions-189-193

Reference: `references/third-potions-189-193.png`  
Raw return: `returns/third-potions-189-193.png`

```text
Restore these FIVE separate Might and Magic potion inventory icons from the attached original reference, left to right. This is an exact-state restoration with one complete bottle in EACH of five isolated columns. Preserve their native silhouette, rounded glass body, long neck, stopper, two dark metal bands, gold/brass details, individual occupied size and placement. Preserve the precise liquid/band colors in order: blue-gold, violet-blue, blue-green, golden amber, pink-gold. Render genuinely smooth painted detail beyond the blocky source pixels, while keeping the composition faithful. Magenta is only a temporary matte; replace it with true transparent background and no magenta fringe. Keep each bottle completely separate and fully visible, including top stopper and bottom edge; do not connect neighboring bottles, omit any, enlarge into gutters or invent extra objects. Keep exact 1050:310 framing, 5 columns in one row, with generous transparent gaps and no text.
```

## third-potions-194-198

Reference: `references/third-potions-194-198.png`  
Raw return: `returns/third-potions-194-198.png`

```text
Restore these FIVE separate Might and Magic potion inventory icons from the attached original reference, left to right. This is an exact-state restoration with one bottle state in EACH of five isolated columns. Preserve native size, placement, long neck, stopper, bands and brass details. Preserve the precise liquid/band colors in order: lime green and gold, pink-orange, violet-green, orange-green, then pale pink damaged/incomplete bottle. The FIFTH icon has deliberate transparent gaps through its glass and missing pieces; it must remain visibly broken and incomplete, with the same gaps and fragments as the source. Magenta is only a temporary matte; all unused space and the broken gaps become genuine transparency with no pink matte fringe. Paint smooth faithful restored detail beyond source pixels. Keep every sprite separate with full visible top and bottom, no connected bottles, no added pieces, no omission, no labels. Keep exact 1050:310 framing, five columns in one row.
```

## third-6nwcape

Reference: `references/third-6nwcape.png`  
Raw return: `returns/third-6nwcape.png`

```text
Restore this single small Might and Magic inventory CLOAK or cape sprite faithfully from the attached enlarged original. It is a very wide, low, dark charcoal folded piece of cloth lying almost flat, with a small jagged crimson red emblem near the upper middle. Preserve its exact broad low silhouette, folded fabric outline, asymmetrical edges, very dark gray-black palette and red emblem shape/placement. Do not turn it into a tall cape, hat, helmet, shield or other object. Smoothly paint fine cloth folds beyond the blocky source pixels while preserving the strong 69:20 width-to-height proportion of the occupied object. The surrounding bright magenta is only a temporary matte; replace it with true transparency, with no magenta fringe. Keep the whole object uncropped and centered with generous transparent gutter. Keep exact 430:190 framing, no text, no extra objects.
```
