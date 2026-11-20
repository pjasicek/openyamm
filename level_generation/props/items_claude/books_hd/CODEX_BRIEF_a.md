# Codex brief: flat cover textures for spellbook ground models, batch a

Scope: image generation only. Write ONLY into `level_generation/props/items_claude/books_hd/`. Do not edit any other
file, do not run builds.

Use your built-in image generation tool, one book at a time. Inputs (in this folder): the restored inventory icon of
each book, enlarged, magenta background. The icon shows the closed book at an angle; it is the design, colour,
material and ornament authority.

Books:
- `6book2`: input `6book2_icon_x8.png` (Air Resistance, Body Resistance, Deadly Swarm, Dispel Magic ...)
- `7item190`: input `7item190_icon_x8.png` (Air Resistance, Awaken, Bless, Body Resistance ...)
- `7item191`: input `7item191_icon_x8.png` (Acid Burst, Berserk, Blades, Charm ...)
- `7item192`: input `7item192_icon_x8.png` (Armageddon, Cure Disease, Cure Insanity, Dark Grasp ...)
- `7item193`: input `7item193_icon_x8.png` (Divine Intervention, Enslave, Incinerate, Lloyd's Beacon ...)
- `book1`: input `book1_icon_x8.png` (Awaken, Bless, Cure Weakness, Destroy Undead ...)
- `book3`: input `book3_icon_x8.png` (Blades, Charm, Control Undead, Cure Paralysis ...)

## Deliverables per book `<icon>`
- `<icon>_cover.png` — the FRONT COVER only, seen exactly straight-on and square to the frame (no perspective), as a
  flat texture filling the WHOLE image edge to edge: no background, no margins, no page edges, no spine, no shadow, no
  book thickness. Portrait 1024 x 1536 (the cover's proportions). Reproduce the icon's cover: its leather/cloth colour
  and texture, its embossed or inlaid central motif (skull, pentagram, sun, star, knotwork...), its border ornaments,
  metal corner fittings and clasps, flattened to the cover plane. Even flat light, no strong highlights, no cast
  shadows (the game lights it).
- `<icon>_spine.png` — the SPINE of the same book straight-on, flat, filling the whole image: 256 x 1536 portrait, same
  material and colour as the cover with raised horizontal bands and matching small ornaments, no lettering.
Write `generation_runs_a.json` (icon, prompt, inputs with sha256, outputs, selected, reason). At most one
corrective regeneration per image. If the tool returns another size, keep the return unresized and record it.

## Prompt content (per image, with the book's icon attached)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: a flat texture of the cover of the EXISTING Might and Magic spellbook
in the attached icon, for a 3D book model. Not a new design: same colours, materials and ornaments as the icon. The
cover (or spine) fills the entire image, perfectly straight-on, rectangular, no perspective, no background, no text.

Checks: the cover fills the frame edge to edge with no background; straight-on, rectangular; matches the icon's design
and colours; no lettering; flat even light.
