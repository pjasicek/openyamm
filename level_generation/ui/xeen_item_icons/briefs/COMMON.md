# Codex brief (common): a Xeen item as an MM7/MM8 inventory icon

Scope: image generation only. Write ONLY into `level_generation/ui/xeen_item_icons/items/<file>/` of the item named
in its own brief. Do not edit any other file, do not run builds or scripts other than copying your image.

Use your built-in image generation tool, once. Input (attached): `style_reference.png`, four Might and Magic VI-VIII
inventory icons of the same kind of item. It is the STYLE AUTHORITY ONLY: rendering technique, level of detail,
lighting, viewing angle, presentation and how much of the frame the object fills. Do not copy their designs, colours
or ornaments. The object itself is described in the item brief.

## Style

Late-1990s pre-rendered 3D fantasy RPG inventory art in the manner of the Might and Magic VII/VIII icons: a single
physical object rendered with believable materials (forged steel with soft brushed highlights, warm aged brass and
gold, worn leather with stitching, wood grain, stone, glass), soft neutral key light from the upper left, gentle form
shading, restrained specular highlights, slightly desaturated natural colours, crisp clean outline. Moderate detail
that still reads when shrunk to a small icon (often under 50 pixels): clear large shapes first, fine detail second.
No painterly brush strokes, no cartoon outlines, no modern glossy mobile-game look, no glow or magic effects unless
the item brief asks for them.

## Presentation

- Exactly one complete object (or the group the brief names), nothing cropped, centred, filling the frame with a
  small even margin (about 5 %).
- View and orientation as the item brief says.
- Weapons are still-life museum pieces on display: no blood, no use, nobody holding them.
- Background: ONE FLAT UNIFORM colour, pure magenta #FF00FF, edge to edge. No gradient, no vignette, no floor, no
  cast shadow, no reflection, no border or frame, no text, no letters, no watermark, no hands, no stand unless the
  brief names one.
- Do not let magenta or pink tint reach the object; keep the object's edges clean against the background. Avoid
  magenta, pink or purple in the object itself unless the brief asks for it (then keep it clearly darker or more
  violet than #FF00FF).

## Deliverable

One image, `paint_a.png`, at the size the item brief gives (an unresized return; if the tool returns another size,
keep it). Copy the generated PNG unchanged to that path.

Check before finishing: the object is the one described; MM7/MM8 rendering look of the reference; orientation and
framing as required; flat magenta background; nothing cropped; no text. At most one corrective regeneration.
