# Codex brief (common): MM9 item as an MM7/MM8 inventory icon

Scope: image generation only. Write ONLY into `level_generation/ui/mm9_item_icons_20261104/items/<id>/` of the item
named in its own brief. Do not edit any other file, do not run builds or scripts other than copying your images.

Use your built-in image generation tool. Inputs (attached in this order):

1. `source_pcx.png`: the ORIGINAL Might and Magic IX inventory picture of this item (64 px, enlarged). It is the
   DESIGN AUTHORITY: the object's identity, silhouette, parts, proportions, colours, materials and ornaments. The
   repainted item must be recognisably this exact object, not a generic item of the same kind.
2. `style_reference.png`: four Might and Magic VII/VIII inventory icons of the same kind of item. They are the STYLE
   AUTHORITY ONLY: rendering technique, level of detail, lighting, viewing angle, presentation and how much of the
   frame the object fills. Do not copy their designs, colours or ornaments.
3. (weapons only) `source_upright.png`: the same MM9 picture mechanically rotated so the weapon stands upright. It
   shows the target orientation; it is blurry from the rotation, so read details from input 1.

## Style

Late-1990s pre-rendered 3D fantasy RPG inventory art in the manner of the Might and Magic VII/VIII icons: a single
physical object rendered with believable materials (forged steel with soft brushed highlights, warm aged brass and
gold, worn leather with stitching, wood grain, mail rings), soft neutral key light from the upper left, gentle form
shading, restrained specular highlights, slightly desaturated natural colours, crisp clean outline. Moderate detail
that still reads when shrunk to the small final size: clear large shapes first, fine detail second. No painterly
brush strokes, no cartoon outlines, no modern glossy mobile-game look, no glow or magic effects unless the item
brief asks for them.

## Presentation

- Exactly one complete object, nothing cropped, centred, filling the frame with a small even margin (about 5 %).
- BODY ARMOUR is the exception: see the armour view rule in its item brief.
- FRONT-FACING otherwise, like MM6-MM8 helms, rings, belts and weapons: the object seen straight on from the front at eye level,
  symmetric about a vertical centre line wherever the object itself is symmetric; no three-quarter turn, no
  view from above. Rings and belts may tilt down only very slightly, exactly as the reference rings/belts do.
- Orientation as the item brief says (weapons: perfectly vertical, functional end at the top, grip at the bottom,
  seen flat from the side like the reference weapons).
- Background: ONE FLAT UNIFORM colour, pure magenta #FF00FF, edge to edge. No gradient, no vignette, no floor, no
  cast shadow, no reflection, no border or frame, no text, no watermark, no hands, no stand.
- Do not let magenta or pink tint reach the object; keep the object's edges clean against the background.

## Deliverables

Two independent candidates, `paint_a.png` and `paint_b.png`, at the size the item brief gives (unresized returns;
if the tool returns another size, keep it and record it). Candidate b may vary lighting/detail interpretation but
must keep the same object design.

Write `generation_runs.json` in the item folder: for each candidate the prompt, inputs with sha256, output and size.
At most one corrective regeneration per candidate.

Checks per image: the object is the MM9 item of input 1 (same parts, proportions, colours, ornaments); MM7/MM8
rendering look of input 2; orientation and framing as required; flat magenta background; nothing cropped; no text.
