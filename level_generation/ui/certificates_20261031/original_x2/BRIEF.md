# Codex brief: restore an original certificate background at high resolution

Scope: image generation only. Write ONLY into `level_generation/ui/certificates_20261031/original_x2/raw/`. Do not edit
any other file, do not run builds. Use your built-in image generation tool.

The input is the background of the original game's victory certificate (640 x 480, `<name>_native.png`) and
`<name>_canvas.png`: the same image enlarged to 1365 x 1024 in the middle of a 1536 x 1024 canvas, with flat grey bars
left and right (85 and 86 px).

## Task
A faithful high-resolution RESTORATION of exactly this artwork, as if rescanned from the original painting: the
same composition, every element in exactly the same place and size, the same sepia-on-parchment colour, the same
contrast and soft faded look. Add only genuine detail: crisp knotwork borders with clean continuous interlace, sharp
title lettering, fine paper texture, clean painted forms in the faded illustration (figures, dragon, horses,
landscape) with no smears, blocks or compression artefacts.

- Keep the image exactly within the 1365 x 1024 middle area of the canvas; keep both grey bars flat grey.
- The title lettering must read exactly as in the input, letter for letter: copy its shapes, do not invent new
  letters or words.
- Do not add anything: no new figures, objects, text, logos, signatures or watermarks. Do not move, crop or recompose.
- Keep the illustration faded and low contrast as in the input (text is printed over it in the game).

## Deliverables (1536 x 1024, unresized)
`<name>_a.png` and `<name>_b.png`, two independent attempts. Write `raw/<name>_generation.json` (prompt, inputs with
sha256, outputs, notes). At most one corrective regeneration per attempt.

## Checks per image
Same framing and placement as the canvas (overlay them mentally at 50 %); grey bars flat; title lettering identical
to the input; no added elements; continuous, sharp knotwork.
