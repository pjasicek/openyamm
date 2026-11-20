# MM6 Demon Queen — HD modelling references (rock alcove only)

## Scope

Image generation only, with your built-in image generation tool. Write only into
`level_generation/creatures/mm6_qfi_claude/references_rock/`. No builds, no other files, no Meshy.

This is a faithful high-definition reconstruction of part of an existing Might and Magic VI game sprite as a 3D
modelling reference: the large rock mound/alcove in which the Demon Queen of the Hive sits. It is NOT a new design.
The queen herself is modelled separately: draw the rock ALONE, with its central niche EMPTY.

## Inputs (attached, in this order)

1. `inputs/native_qfia0_full.png` — the original native standing frame (queen in the rock). AUTHORITY for the
   rock's silhouette, lobes, niche and colours. Transparent background.
2. `inputs/native_qatc0_full.png` — another native frame of the same rock (the queen in a different pose). AUTHORITY.
3. `inputs/native_qdef0_corpse_full.png` — native corpse frame: the same rock after it has collapsed (flattened).
   Use it only to understand the rock's structure (lobes, crack pattern); do NOT draw this shape.
4. `inputs/restored_x2_qfia0_surface_only.png` — AI-restored enlargement of frame 1. SURFACE MATERIAL ONLY
   (rock grain, cracks, colour variation). It never sets the design.

## Deliverables

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter (the rock turned about 35° so its right side shows), camera at about half the rock's height, slightly above |
| `01_front.png` | front, matching the native framing (niche centred) |
| `02_back.png` | back |
| `03_left.png` | its left side (the niche faces the image RIGHT) |
| `04_right.png` | its right side (the niche faces the image LEFT) |

Landscape 1536x1024, transparent background, no floor, no cast shadow, no text, the whole rock in frame with
generous margins (nothing cropped).

This run: generate `00_three_quarter.png` only, unless told otherwise. One corrective regeneration at most.

## The rock (from the native frames)

- **Shape:** one massive rounded boulder mound, wider than tall (width : height about 1.2 : 1, depth about 0.7 of the
  width), flat bottom resting on the floor. Its surface is made of big soft bulging lobes and folds, like a lumpy
  organic hive mound: a high rounded crown, a big lobe on each upper shoulder, heavy rolled lobes along the bottom
  front edge.
- **Niche:** in the centre of the front, a tall shallow recess (about a third of the rock's width, from the floor to
  about two thirds of its height) where the queen stood; its back wall is smooth and slightly concave, and a thick
  rounded lip of rock frames it at the bottom. The niche is EMPTY.
- **Material:** weathered stone: olive-grey to sandy tan, lighter sandy highlights on the bulges, faint rusty-red
  veins and patches, thin dark hairline cracks branching across the surface (as in the native frames). Matte.
- **Light:** even, soft studio light. The native frames have a strong blue-black shadow on the rock's right side:
  that is scene lighting, do NOT reproduce it. Show the true stone colour everywhere.
- The back of the rock (against a wall in the game) is simpler: rounded lobes of the same stone, no niche.

## Do NOT

- No queen, creature, figure, eggs, bones, plants, glowing elements, carvings or symbols.
- No floor, ground plane, cave background or cast shadow.
- Do not make it a cave entrance or a hollow shell: it is a solid mound with a shallow recess.
- No dramatic or coloured lighting; no text or watermark; nothing cropped.

## Per-image checks (re-run before selecting)

- Silhouette and lobes match inputs 1–2 (the front view must read as the same rock); niche empty and centred.
- Stone colours match the lit (left) side of the native rock; no blue shadow baked in.
- True alpha, 1536x1024, nothing cropped, flat bottom.

## Records

Write `generation_runs.json` (id, prompt, input file sha256, output path, selected flag, reason, superseded runs) and
`selected_views_review.png` (contact sheet of the selected views). Keep every tool return under `superseded/` if not
selected.
