# Codex brief: accessory texture sheet for MM9 Yanmir's staff and crown (mm9_yanmir_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_yanmir_claude/references_acc/`. No builds, no Meshy. Use your built-in
image generation tool. This is a flat TEXTURE ATLAS for a video-game model (a frost giant king's staff and ice crown), not a picture of an object.

## Inputs (attached, in order)
1. `mm9_staff_views.png`: the ORIGINAL 2002 game staff head (silver blades, green gem), low-resolution renders: colour and motif authority.
2. `mm9_skin_x2.png`: the original skin of the whole character (the staff shaft is the white-and-dark streaked strip near the right edge; the crown
   band is top left; silver knotwork everywhere): material and colour authority.
3. `crown_master_crop.png`: our high-definition master of his crown: silver knotwork band and clear ice spikes.

## Deliverable
`acc_sheet.png`: 1024x1024, opaque, no text, no labels, no borders between regions, flat even lighting (a colour map: no cast shadows, no
perspective, no highlights from a light), seamless where stated. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with
sha256, output path). At most one corrective regeneration.

Layout, exactly (pixels from the top-left):
- **Rows 0-255, columns 0-511: GEM.** A deep emerald-green faceted gemstone surface filling the whole region: bright mint highlights and dark
  green facets, like input 1's gem. No setting, no background.
- **Rows 0-255, columns 512-1023: ICE.** Clear pale blue-white glacial ice filling the region, vertical streaks and fine internal cracks running
  top to bottom, brighter white toward the top edge, slightly deeper cyan toward the bottom edge. Seamless left to right.
- **Rows 256-511: ENGRAVED SILVER.** A horizontal band of polished silver with an engraved interlaced Celtic knotwork pattern, dark niello in the
  grooves, a thin raised plain rim along the top and bottom edges of the band, like the knotwork in inputs 2 and 3. The pattern repeats so the
  band is seamless left to right (the left edge continues the right edge). Cool blue-grey silver, not gold.
- **Rows 512-1023: FROSTED WOOD.** The staff's pole: pale frosted wood like white birch with frost, the grain running VERTICALLY (top to bottom),
  grey-white bark with thin dark horizontal-free streaks and knots, a faint blue cast from the frost, as the staff strip in input 2. Seamless
  left to right AND top to bottom.

Do NOT: draw objects, a staff, a crown, a gem with a background, shadows, text, frames, or gaps between the regions.
