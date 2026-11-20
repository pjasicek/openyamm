# Common rules for every OpenYAMM completion certificate painting

Scope: image generation only. Write ONLY into `level_generation/ui/certificates_20261031/raw/`. Do not edit any other
file, do not run builds. Use your built-in image generation tool.

What it is: the background art of an in-game certificate the player receives in OpenYAMM (an open-source engine that
plays the Might and Magic VI-VIII worlds) when they finish a continent's story. The game draws ALL the writing itself
(title, party names, ending text, time, score) and places the OpenYAMM seal in the seal recess. This is OpenYAMM's own
design: it must NOT imitate the original games' certificates (no red metal title lettering, no claws, no "Might and
Magic" logo, no parchment-with-faded-harbour look of the 2000 originals).

## Format
- 1536 x 1024 landscape, unresized. If the tool returns another size, keep it unresized and record it.
- ABSOLUTELY NO text, letters, numbers, runes that read as letters, logos, monograms, signatures or watermarks anywhere.

## Composition (follow the attached layout guide exactly; its coloured marks are instructions, not art)
- FRAME: the outer band (about 64 px on every side, the dark area outside the beige of the guide) is a carved dark
  green-black obsidian stone frame with fine polished brass filigree inlay and ornate brass corner pieces, the same
  stone and brass as `ref_obsidian_frame.png` but richer and more ceremonial. Even width all around.
- PARCHMENT: inside the frame, a sheet of warm aged ivory vellum with fine fibres and a gentle darker vignette toward its
  edges; slightly deckled edges resting on the obsidian. Clean: no stains, tears or strong creases.
- SEAL RECESS: the blue circle of the guide (centre 768,132, radius 70) is a round recess of plain dark polished
  obsidian with a polished brass rim, set into the top of the parchment. Its interior stays EMPTY and plain dark: the game
  places the seal of `ref_openyamm_seal.png` there. Do not paint that seal. Fine brass scrollwork or laurel may reach a
  short way left and right from the rim along the top edge.
- TEXT ZONE: the red rectangle stays plain, evenly lit parchment so that dark ink text drawn over it reads perfectly. At
  most a very faint engraved watermark (under 8 % contrast) as described in the certificate's own brief.
- Everything else as the certificate's own brief says. Outside the text zone the art may be rich and detailed.

## Style
High-end painted fantasy illustration, the quality of a premium collector's edition: fine sepia ink linework with muted
watercolour and gouache washes on the vellum, crisp brass and stone in the frame, soft warm light. Coherent with the
palette of the attached continent globe(s). Nothing modern, nothing photographic, no people's faces in close-up.

## Deliverables
Two candidates per certificate, `<name>_a.png` and `<name>_b.png` (the names in the certificate's brief), differing in
the illustration, not in the layout. Write `raw/<name>_generation.json` (prompt, inputs with sha256, outputs, notes).
At most one corrective regeneration per candidate.

## Checks per image
No text or letters anywhere; seal recess empty, round and centred; text zone plain and light; frame even on all four
sides; the layout guide's marks are not painted in.
