# New face textures for the Xeen dungeons (XD-01 to XD-03)

Made 2026-11-13 at the user's go-ahead for the textures listed in each dungeon's L4 NOTES.md ("Textures to
generate"). 31 generated textures (37 names: the gong is also cut into its six slab strips). The lists per dungeon,
with where each went, are in `devdocs/xeen/briefs/xd0N/L4/NOTES.md`, "Generated textures".

## How they were made

- **Images:** only Codex image generation, one `codex exec` worker per image (`xtex.py gen`), as the surface
  texture pipeline does (`../textures_x4/PLAYBOOK.md`). Each call gets the shipped x4 masters of the area's family as
  reference images (`../textures_x4/masters/<world>/<name>.png`; refs/ keeps every image sent) and one prompt
  (prompts/, exact text). The prompt names the family, asks for the same palette, scale of detail, painted (not
  photographic) look and flat even light, and describes the content. Raw returns are in raw/ unchanged.
- **New art, not an upscale:** there is no native to trace, so the playbook's blurred-native reference, registration
  and traced checks do not apply. What was taken from it: the family's own masters as the colour and style guide,
  brightness fixed afterwards by one linear gain (imagegen returns art 1.3-2x too bright; gains here 0.31-1.99),
  made-seamless tiling checked in a 3x3 repeat, and the x4 tier as the in-game target (the masters are 4x the
  logical size, as the shipped textures beside them).
- **Kinds** (`specs.yml`, finished by `xtex.py finish`):
  - *sign*: a board on flat grey, with a layout guide image (the board's rectangle at the exact proportions of the
    face that shows it) as reference 1; the board is cut out by its outline and resampled to the texture's size.
    Where the face stretches the texture once (`fit`), the art is made at the face's proportions, so the stretch
    gives it back undistorted (the board is stored squeezed in a power-of-two texture).
  - *picture*: full bleed, cut to the face's proportions.
  - *tile*: full bleed, then made seamless by a seam pass: the image is rolled by half so its own seams lie on the
    centre lines, a second call repaints only that cross-shaped band, and the band is blended back (gain-matched
    to its surroundings, never reaching the tile's edges, which are untouched interior). The tile edges then
    continue each other exactly; checked in sheets/check_<name>.png (3x3 repeat).
  - *edit*: painted into a family master (the gold veins into `t3ll5`, `t3ll6`, `crstont`; the chalk mark into
    `t3ll5`). The return is registered to the master, gain-matched where the model left the rock alone, and only
    what it changed is kept (a feathered mask), so the rock is the shipped master's own pixels. The window the
    switch face shows (`view_auto`, in map units) is centred on the painted vein, so the rock shows at the wall's
    own scale round it.
  - *cutout*: on flat magenta, keyed to alpha (the hoist grille); transparent texels filled with the nearest bar
    colour so mipmaps carry no magenta.
- **Checks** (`xtex.py check`, sheets/checks.json): size (power-of-two logical, x4 master), mean colour, luma
  percentiles and saturation against the family masters, luma histogram overlay, edge continuity on the repeat
  (seam ratio, about 1 for tiles), a 3x3 repeat picture. Then in the game: before/after tours at every place
  (`tours/`, `output/studio_cal/xd0N/textures_gen/before|after`).

## Install (game lookup)

Face textures are found by name through `Data/bitmaps` (engine `findCookedOrImageAssetPath`): in a development
root every world's `textures/` and `textures_<tier>/` folder is merged by name, the active world's first, and the
preferred tier's file wins, a cooked `.oytex` before a `.png`. Desktop draws the x4 tier; the cooked file must be the
surface cook's job (BC7, linear, full mip chain, statistics), which `xtex.py install` runs with
`build/game/openyamm_model_texture_cook` exactly as `tex.py install` and `tools/cook_surface_textures.py` do. Logical
size = physical / 4, so the projects' `size` is the listed one.

`xtex.py install --root R` writes `R/worlds/mm7/textures_x4/<name>.oytex` (BC7) and `R/worlds/mm7/textures_x2/<name>.png`
(Lanczos half, for an x2 run), each as a new file renamed into place (never through a hard link). Installed only in
`output/studio_play/xeen_root` and the scratch root `output/studio_cal/xeen_texgen_root`; nothing in `assets_dev`.

## A permanent home

Not made. Either:

- **A Xeen world package** (when `worlds/xeen` exists): sources in `assets_source/worlds/xeen/textures_x4/<name>.png`
  (the finished masters here) and `textures_x2/<name>.png` (the `_x2` files), cooked by
  `tools/cook_surface_textures.py --world xeen` into `assets_dev/worlds/xeen/textures_x4/`; the maps' `world: xeen`.
- **Or an MM7 addition** while the dungeons stand in MM7: the same files in `assets_source/worlds/mm7/textures_x4` and
  `textures_x2`, cooked into `assets_dev/worlds/mm7/textures_x4` by the build's surface cook. They would then ship in
  MM7's package although no MM7 map uses them.

Either way the 1x tier (`_x1` files) is only needed if a lighting bake or an x1 run reads them; no texture here is
animated, a liquid, or has surface material maps (`tools/surface_materials.py` could add relief later).

## Files

`specs.yml` (every texture: size, face proportions, kind, family references, tone, prompt text), `state.json`
(versions, the one chosen, finishing record), `xtex.py`, `strips.py` (the gong's slab strips), `retex.py` (the
project edits, counted), `cams.py` / `tour.sh` / `tours/` (cameras on the faces by texture, before/after tours),
`pairs.py`, `montage*.py`, `playtests.sh`. Images (refs/, raw/, finished/, sheets/) stay local.
