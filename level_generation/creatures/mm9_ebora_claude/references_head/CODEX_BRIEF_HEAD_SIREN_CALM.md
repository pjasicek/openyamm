# Codex brief: calm face repaint, MM9 Concubine siren skin 1 (mm9_ebora_claude, 2026-11-01 evening)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_ebora_claude/references_head/`. No builds, no Meshy.
Use your built-in image generation tool.
A fantasy video-game character: one of Ebora's handmaidens, a horned demon woman with fair skin and copper-red hair, a
restoration of a 2002 game character for a game mod. A close face texture reference, non-sexual.

The user reviewed the current face paint (image 2) and found it ugly: sullen and crooked, knitted angry brows with frown
lines between them, squinting, a pursed pouting mouth, heavy dark shading on the cheeks and jaw, a muddy chin. Repaint the
SAME woman as an attractive, CALM, SYMMETRIC face.

## Inputs (attached, in order)
1. `references_head/clay_shp_08_face.png`: the EXACT 3D head, orthographic close front view. Geometry and framing
   authority: the eye openings, the nose, the mouth slit (now wide: corners at about x 544 and 712, y 846), the chin point,
   the jaw outline, the hairline and the hair masses stay exactly where this clay has them, same framing and scale.
2. `references_head/s_08_face.png`: the current paint. Keep its identity and colours: the peach skin tone, the green
   irises, the copper-red hair with strand groups and sheen. Do NOT keep its expression, brows, mouth or shading.
3. `references_hd/mm9_head_views_siren1.png`: the original game model's head. Look authority for colours (peach skin,
   dark red lips, green eyes, copper-red hair).

## Deliverable
`s2_08_face.png`: 1254x1254, true transparent background outside the clay silhouette, the same framing as image 1,
unresized. Raw return(s) in `raw/` as `s2_08_face_attempt<N>.png`; `generation_runs_head_siren_calm.json` (prompt, source
path, attempt). At most one corrective regeneration.

## Paint
- EXPRESSION: calm, serene, slightly aloof; relaxed face, no frown, no squint, no smirk. Perfectly left-right symmetric
  about the nose (the clay is symmetric).
- BROWS: thin, softly and evenly arched, relaxed (not pulled down toward the nose, not raised), dark red-brown, the same
  height on both sides. NO frown lines or creases between the brows, smooth forehead.
- EYES (exactly on the clay's eye openings): open almond eyes, green irises with dark pupils, clean white sclera, crisp dark
  upper lash line with a small flick at the outer corner, thin lower line, soft lid crease. Both identical.
- NOSE: straight, soft shading on its sides, a gentle bridge highlight (no hard white streak), small nostrils.
- MOUTH: closed, relaxed, neutral (a hint of a soft smile at most), centred and symmetric, lip corners exactly at the clay's
  slit ends. Full dark red lips (MM9's deep crimson, about RGB 120,20,25 in the shade, 160,35,40 in the light), a crisp
  outline, a darker line between the lips, a small soft highlight on the lower lip. Not pursed, not pouting, not pulled to
  one side.
- SKIN: fair warm peach (about RGB 222,152,109 in mid light), CLEAN soft form shading only: a light shadow under the
  brows, beside the nose, under the cheekbones and under the lower lip; a faint rosy flush on the cheeks. Cheeks, jaw and
  chin stay clean and light: no dark brown patches, no stubble-like or muddy shading on the chin or jaw line, no heavy
  contour. The chin is the same light skin as the cheeks with only a soft shade below the lower lip.
- HAIR (outside the face, where the clay has hair): the same copper-red strand groups as image 2. Clean hairline: no
  skin paint on the hair, no hair paint on the skin, no strand across the forehead or face.
- NECK below the jaw: the same light skin, only a soft shadow right under the jaw.
- Light: flat, even studio light, NO cast shadows, no rim light, no strong specular: an albedo reference with painted form
  shading only.

Do NOT: horns inside this crop (the clay shows none), jewellery, make-up other than the lash line and lips, move any
feature or edge, change the framing, add a background.
