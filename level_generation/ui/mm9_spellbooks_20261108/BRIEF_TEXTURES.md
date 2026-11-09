# Codex brief: flat cover and spine textures for the MM9 spellbook ground models

Scope: image generation only. Write ONLY into `level_generation/ui/mm9_spellbooks_20261108/<tier>/` of the tier your
prompt names. Do not edit any other file, do not run builds.

Use your built-in image generation tool. Input (attached): `<tier>/icon_x8.png`, the finished inventory icon of this
tier's spellbook, enlarged, on magenta. The icon shows the closed book at an angle; it is the design, colour,
material and ornament authority. The textures go on a simple 3D book model lying on the ground.

## Deliverables

- `cover.png`: the FRONT COVER only, seen exactly straight-on and square to the frame (no perspective), as a flat
  texture filling the WHOLE image edge to edge: no background, no margins, no page edges, no spine, no shadow, no book
  thickness. Portrait 1024 x 1536 (the cover's proportions). Reproduce the icon's cover: its leather colour and grain,
  its corner fittings, edging and clasp, and its central ornament (star, rune ring, gem, sunburst), flattened to the
  cover plane and centred. Even flat light, no strong highlights, no cast shadows (the game lights it). The
  Grandmaster tier keeps its faint golden glow only inside the runes of the central ornament.
- `spine.png`: the SPINE of the same book straight-on, flat, filling the whole image: 256 x 1536 portrait, the same
  leather and colour as the cover with raised horizontal bands and small metal ornaments in the tier's metal (iron,
  bronze, silver or gold), no lettering.

If the tool returns another size, keep the return unresized and record it. Write `textures_runs.json` (prompt, inputs
with sha256, outputs, sizes). At most one corrective regeneration per image.

Prompt content (per image, with the icon attached): a flat texture of the cover (or spine) of the spellbook in the
attached icon, for a 3D book model. Same colours, materials and ornaments as the icon; the cover (or spine) fills the
entire image, perfectly straight-on, rectangular, no perspective, no background, no text.

Checks: fills the frame edge to edge with no background; straight-on and rectangular; matches the icon's design and
colours; no lettering; flat even light.
