# Codex brief: MM9 spellbook inventory icons, four mastery tiers

Scope: image generation only. Write ONLY into `level_generation/ui/mm9_spellbooks_20261108/<tier>/` of the tier your
prompt names. Do not edit any other file, do not run builds or scripts other than copying your images.

Use your built-in image generation tool. These are NEW designs (not repaints of an existing item): the spellbooks of
the Might and Magic IX world, one design per spell mastery (Normal, Expert, Master, Grandmaster). Every spell of every
school uses its mastery's book, so no school symbol, element or colour coding: the four books differ only by how
precious and ornate they are, climbing a clear ladder that reads at a glance even at the small final icon size.

Inputs (attached):
- `style_reference.png`: four Might and Magic VII/VIII book icons. STYLE AUTHORITY ONLY: rendering technique, level of
  detail, lighting, viewing angle and presentation. Do not copy their designs.
- `mm9_skill_books_avoid.png`: MM9's skill books (plain tan leather). The spellbooks must NOT look like these.
- (Expert, Master, Grandmaster only) `normal_paint.png`: the finished Normal book. SHAPE AUTHORITY: paint the same
  book (same proportions, thickness, viewing angle, size in the frame, page block and spine shape) with only the
  cover material, fittings and ornament changed as your tier says.

## The four tiers (one shared book, a material ladder)

- **normal**: a sturdy spellbook bound in deep brown leather with blind-tooled border lines, plain dark iron corner
  caps on the four corners of the front cover and a simple iron strap clasp; a small embossed circle with a simple
  four-pointed star at the centre of the cover. Humble but clearly a magic book, not a ledger.
- **expert**: the same book bound in rich oxblood-red leather, burnished bronze corner pieces with a little engraved
  scrollwork, a bronze clasp, and a bronze-inlaid ring of small runes around the central star.
- **master**: the same book bound in deep midnight-blue leather, bright silver filigree corners and edging along the
  cover, a silver clasp, and a cut sapphire-blue gem set in a silver eight-pointed star at the centre.
- **grandmaster**: the same book bound in black leather with deep violet sheen, ornate gold fittings covering the
  corners and framing the cover, a heavy gold clasp, and a large faceted amethyst set in a gold sunburst at the centre
  whose runes glow faintly with soft golden light (the only tier with any glow; keep it subtle, no rays or sparkles
  leaving the book).

## Style

Late-1990s pre-rendered 3D fantasy RPG inventory art in the manner of the Might and Magic VII/VIII icons: a single
physical object rendered with believable materials (worn leather with grain and stitching, aged iron, bronze, silver
and gold with soft brushed highlights, cream page edges), soft neutral key light from the upper left, gentle form
shading, restrained specular highlights, slightly desaturated natural colours, crisp clean outline. Clear large
shapes first, fine detail second. No painterly brush strokes, no cartoon outlines, no modern glossy look.

## Presentation

- A closed book lying in a three-quarter view from slightly above, front cover facing the viewer and filling most of
  the picture, spine on the left, page block visible on the right and bottom edges, like the reference books.
- Exactly one complete object, nothing cropped, centred, filling the frame with a small even margin (about 5 %).
- Background: ONE FLAT UNIFORM colour, pure magenta #FF00FF, edge to edge. No gradient, no floor, no cast shadow, no
  reflection, no border, no text or lettering anywhere (also not on the book), no watermark, no hands.
- Keep magenta or pink tint off the object; clean edges.

## Deliverable

`<tier>/paint_a.png`, 1024 x 1024 (keep an unresized return of another size and record it). Write
`<tier>/generation_runs.json`: prompt, inputs with sha256, output and size. At most one corrective regeneration.

Checks: the tier's materials and ornaments as listed; (Expert and above) the same book shape as `normal_paint.png`;
MM7/MM8 rendering look; three-quarter view as required; flat magenta background; nothing cropped; no text.
