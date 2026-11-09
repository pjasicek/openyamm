# Complete effect sequence imagegen submissions

All seven submissions used the built-in imagegen tool. The four source references contain all eight native frames
in row-major order, four columns by two rows. `jobs.json` records source and reference hashes. `report.json` records
selected raw-return and fitted-candidate hashes. No Real-ESRGAN was used. No art in this directory is accepted yet.

## Initial complete sequence returns

### `sp05e.png`

Reference: `references/sp05e.png`.

> Use case: precise-object-edit. Asset type: OpenYAMM 2D PC spell effect animation. Image 1 is the authoritative native source: one complete EIGHT-frame animation, ordered left-to-right across a 4-column by 2-row sheet. Restore ALL EIGHT frames together into one coherent high-detail painted 2D sequence. Each frame is a gold-and-deep-brown oval magical swirl; preserve the frame-specific diagonal, horizontal or vertical bands and their phase progression exactly. Frame 6 (bottom row second cell) has broad horizontal glowing gold bands and must be fully restored in the SAME artistic style and detail as the other seven. Keep each complete oval inside its own 300×380 cell with transparent gutters, consistent object scale, shared material and lighting, no touching neighboring cells, no clipping. The source magenta is ONLY a matte: output genuine transparent background and transparent gaps, no magenta fringe. No grid, labels, text or extra objects. Return one 4×2 spritesheet.

### `spell14e.png`

Reference: `references/spell14e.png`.

> Use case: precise-object-edit. Asset type: OpenYAMM 2D PC spell effect animation. Image 1 is the authoritative native source: ALL EIGHT consecutive frames in a 4-column by 2-row sheet. Restore the entire white/silver wind-cloud oval sequence together in one consistent painted style. Preserve each frame's exact phase, broad white wispy bands and irregular transparent openings; the first and last frames are deliberately sparse fade-in/fade-out states and must stay sparse, not become solid ovals. The dark central holes in middle frames must remain genuinely transparent. One complete sprite per 300×380 cell, ample transparent margin, same scale and lighting across all eight; no crop, overlap or added particles. Magenta is matte only; output real alpha transparency with no magenta edges. No grid, labels or text. Return one 4×2 spritesheet.

### `spell36e.png`

Reference: `references/spell36e.png`.

> Use case: precise-object-edit. Asset type: OpenYAMM 2D PC spell effect animation. Image 1 contains the complete EIGHT-frame native sequence in a 4-column by 2-row sheet. Restore ALL EIGHT frames together as one coherent high-detail painted animation of scattered warm-brown stone fragments with small gold star glints. Follow each frame's exact fragment distribution and density progression: frames 1 and 8 are sparse fade endpoints; middle frames become denser, then recede. These are fragments floating in a transparent oval region, NOT a solid rock egg or solid disk. Preserve every important gap and the phase of the glints. One complete uncropped frame per 300×380 cell, all in the same material, scale and lighting, 25+ pixels of clear gutter on every cell side. Magenta is only source matte; output genuine transparent background. No grid, text, labels, extra frames, or stray neighboring fragments. Return one 4×2 spritesheet.

### `spell68e.png`

Reference: `references/spell68e.png`.

> Use case: precise-object-edit. Asset type: OpenYAMM 2D PC spell effect animation. Image 1 is the authoritative native source: ALL EIGHT frames of one continuous healing/magic visual in a 4-column by 2-row sheet. Restore the complete sequence together into a single consistent high-detail 2D painted style: bright icy blue-white jagged arc bands and star-like glints with small cyan accents, over truly transparent irregular dark gaps. Preserve each frame's distinct band layout and phase, and the sparse eighth fade-out state. Keep the art distinctly BLUE-WHITE across every frame, avoiding purple/pink color shifts and avoiding solid filled discs. One complete sprite per 300×380 cell, matching size and lighting, generous transparent margins, no crop or overlap. Magenta is matte only; output real alpha with no magenta fringe. No grid, labels, text or added objects. Return one 4×2 spritesheet.

## Whole-sheet cleanup passes

The first cloud and blue returns spread low-alpha material into gutters. They were edited as complete eight-frame
sheets, with the original full reference supplied again. The selected returns are `spell14e-v2.png` and
`spell68e-v2.png`.

### `spell14e-v2.png`

References: `returns/spell14e.png` (edit target), `references/spell14e.png` (native phases).

> Use case: precise-object-edit. Asset type: eight-frame 2D spell effect spritesheet. Image 1 is the current smooth generated sheet and is the edit target. Image 2 is the complete eight-frame native sheet and is authoritative for each phase. Keep Image 1's unified silver-white painted detail and all eight distinct frame phases. Clean the sheet: REMOVE ALL detached spray, fog, white flecks and halo OUTSIDE each frame's central oval. Each frame should occupy at most the central 70% width and 70% height of its own equal 4-column by 2-row cell, leaving wide completely transparent gutters on EVERY SIDE, including between rows. Preserve the large genuinely transparent internal holes and the sparse first and eighth phases. Do not fill gaps into a solid disk. Each one of the eight ovals must be complete and separate, same visual scale and style. Transparent background and gaps, no black backing, no magenta fringe, no grid, no text. Return the complete 4×2 sheet.

### `spell68e-v2.png`

References: `returns/spell68e.png` (edit target), `references/spell68e.png` (native phases).

> Use case: precise-object-edit. Asset type: eight-frame 2D PC spell effect spritesheet. Image 1 is the current smooth generated sheet and edit target; Image 2 is the complete eight-frame native reference and governs phase/order. Keep the coherent icy BLUE-WHITE jagged bands and star glints in Image 1. REMOVE ALL loose cyan/blue mist, splashes, bloom and small debris outside each central oval. Each complete frame must fit within the central 70% width and 70% height of its own equal cell on the 4-column by 2-row sheet, with wide clean transparent gutters between every frame and around the sheet. Keep all eight phases distinct and the last frame sparse; keep the original large holes and gaps transparent. No purple or hot pink shift, no solid opaque disc, no black background, no magenta fringe, no grid, labels, text or extra objects. Return the complete 4×2 sheet.

### `spell36e-v2.png`

References: `returns/spell36e.png` (edit target), `references/spell36e.png` (native phases).

> Use case: precise-object-edit. Asset type: complete eight-frame fantasy game effect animation sheet. Image 1 is the current high-detail eight-frame generated sheet and the edit target. Image 2 is the authoritative original eight-frame animation. Preserve ALL eight distinct phases, their fragment placements, brown stone material, gold glints, common style and 4×2 cell layout. Correct ONLY the red/orange/magenta patches and fringes visible in the empty gaps and around rock outlines: these are leaked source matte and must become genuinely transparent. Keep warm brown rocks and gold glints intact. No colored backdrop, no red smoke, no new rocks, no joined solid discs. Keep 30+ pixels of empty transparent gutter around each frame; no clips or neighboring cells. Return one complete 4×2 sheet with genuine alpha.

The selected returns were extracted from their equal cells, with low-alpha outer mist removed. Every frame in a
sequence uses the union of its eight native occupied rectangles as one 2× oval envelope. This centers all frames
at (59, 79) on identical 118×158 canvases and prevents the sparse phases from changing the oval's size or anchor.
The unselected initial returns remain for provenance.
