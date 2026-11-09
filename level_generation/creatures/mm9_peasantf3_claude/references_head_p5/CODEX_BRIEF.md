# Codex brief: head texturing references for PeasantF3 A and B, painted over renders of the current 3D head (mm9_peasantf3_claude, pass 5)

Scope: image generation/editing only. Write ONLY into `level_generation/creatures/mm9_peasantf3_claude/references_head_p5/`. Do not edit
any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## What these are for
The images are the view references for re-texturing an EXISTING 3D head (head, white/cream linen veil and hood, two braids, neck and the
top of the dress) of a young Might and Magic IX townswoman. The texture is projected from your images onto the 3D model, so each output
must keep the EXACT framing, silhouette and feature positions of its input render: the same pixels for the outline of the veil and
hood, the braids, the eyes, the nose, the mouth, the chin, the neck and the shoulders. Only the PAINT changes: clean, sharp, high-quality,
naturally lit (soft even light, no harsh shadows, no specular shine), and correct for the person.

## Inputs (attached, in order)
1-4. `cur_a_hfront.png`, `cur_a_hq34.png`, `cur_a_profile.png`, `cur_a_hback.png`: the current 3D head of woman A, rendered (front,
     front three-quarter from her right, her left profile facing IMAGE RIGHT, back). SHAPE AND FRAMING authority for outputs a_*.
5-8. `cur_b_hfront.png`, `cur_b_hq34.png`, `cur_b_profile.png`, `cur_b_hback.png`: the same for woman B. SHAPE AND FRAMING for b_*.
9.   `mm9_head_views_a.png`: the ORIGINAL 2002 game head of woman A (low resolution): her identity (golden-blonde hair parted in the
     middle, two blonde braids, white linen veil, fair skin).
10.  `mm9_head_views_b.png`: the ORIGINAL game head of woman B: dark-brown, almost black hair parted in the middle, two dark braids, a worn
     cream veil, pale skin, a slimmer face.
11.  `01_front.png` (references_head_f3): an earlier HD portrait of woman A, for skin and hair quality only.

## Deliverables (same size as the inputs, 1254x1254, unresized returns; plain flat light-grey background like the inputs)
| File | From input |
|---|---|
| `a_front.png`, `a_q34.png`, `a_profile.png`, `a_back.png` | 1, 2, 3, 4 |
| `b_front.png`, `b_q34.png`, `b_profile.png`, `b_back.png` | 5, 6, 7, 8 |
Make the two FRONT views first, then the others with your own front output as an extra input so each woman is consistent across views.

## Paint
Both: young women of about 25, calm and warm, a gentle closed-lip smile (lips together, no teeth, no dark line or shadow between or above
the lips), natural soft-pink lips; relaxed open eyes with clear irises (A blue-grey, B grey-blue), clean whites, natural lids with NO dark
marks, wedges or shadows under or beside the eyes and no red rims; ONE thin natural brow per eye; NO makeup. The NOSE is painted exactly
on the render's nose: the same tip, the same nostril positions, plain skin with soft natural shading and two small, soft nostrils on the
underside only; no dark blob, no lighter halos beside it. Even, clean skin over the whole face, cheeks, chin, jaw, under the chin and the
neck (no blotches, no smudges, no patches in front of the ears); a soft natural blush on the cheeks.
- A: golden-blonde hair parted in the middle and drawn back under the veil; the braids golden-blonde plaits; the veil and hood clean white
  linen with a fine weave; fair warm skin.
- B: dark-brown, almost black hair parted in the middle; the braids dark-brown plaits; the veil and hood worn cream linen; pale skin; her
  own face (slightly slimmer and more serious than A, but calm and kind).
The edge where the veil meets the hair is one clean line (no white teeth over the hair). The dress and necklace at the bottom keep the
render's colours.

## Do NOT
- move, resize, crop or re-frame anything; change the head, nose, lip, chin or veil shapes; add a hat, jewellery, text or a shadow;
  paint harsh light, shine or specular highlights; open the mouth; add makeup or a second brow line.

## Checks before saving (one corrective regeneration per image at most)
Overlay each output on its input: outlines, eyes, nose tip and mouth within a few pixels. Clean eyes and nose, closed lips, no blotches.
Write `generation_runs.json` (id, prompt, inputs with sha256, output, selected, reason) and `review.png` (inputs and outputs side by side).
