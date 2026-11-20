# Codex brief v2: warmer, relaxed face repaint of the MM9 townswomen PeasantF4 A / B head renders (mm9_peasantf4_claude)

Scope: image generation/editing only. Write ONLY into `level_generation/creatures/mm9_peasantf4_claude/references_face/v2/`. Do not edit any
other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

`in_face_<t>.png` is a flat, UNLIT (albedo) front orthographic render of a game character's 3D head texture, 1254x1254. The output is
projected back onto the 3D head pixel for pixel, so the FRAMING MUST NOT MOVE: the face outline, the hood and its edge, the hairline, the
nose and its nostrils, each eye's centre and opening, and the mouth's centre line stay on the same pixels.

Review of the current render (a game art director's notes): both women read worried and pale, with large staring eyes, heavy lower-lid bags,
the nostrils too dark, the mouth thin. The game originals are warm: woman A smiles broadly and warmly with tanned, rosy skin; woman B is
older and calm.

## What to change (inside the face, from the hood's edge to the chin)
- SKIN: warm, lightly sun-tanned skin (golden-tan, not pale or pink), natural rosy cheeks (a soft warm blush on the cheekbones), even.
- EYES: relaxed and friendly: the upper lid resting on the top of the iris (no white above the iris), the lower lid close under the iris
  (no white below it), soft natural lashes, no bags or pale steps under the eyes, no dark sockets. Brows relaxed, level (not raised at the
  inner ends: not worried).
- NOSE: the same shape; the nostrils small, soft and only slightly darker than the skin (no dark holes).
- MOUTH (woman A): a broad, warm CLOSED-lip smile, the corners clearly lifted, soft smile lines, lips together (no teeth), natural rose
  lips of normal fullness. (woman B): a calm, kind closed mouth with the corners very slightly lifted, natural lips.
- Keep the age: A about 45 (a few soft lines), B about 60 (lined forehead and cheeks, grey in the dark hair).
- Flat even albedo like the input: no added light, shadows, highlights or reflections.

## Keep EXACTLY (pixel positions and colours)
The hood (olive-brown cloth) and its edge, the hair parting and hairline, the neck, the grey background, the face outline, the nose shape
and position, each eye's centre. Same size and framing; no zoom, no shift.

## Checks before saving (one corrective regeneration at most)
Overlay on the input: hood edge, nose tip, eye centres, mouth centre and face outline coincide within a few pixels; closed lips, no teeth;
no white above or below the irises; warm tan skin with rosy cheeks; calm, warm expression (never worried, fierce, cold or staring).
Save `out_face_<t>.png` (1254x1254) and a `review_<t>.png` with input and output side by side.
