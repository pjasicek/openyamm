# Codex brief: HD HEAD turnaround v2 for the MM9 Wyrde of the Known, Igrid (mm9_wyrdold_claude), 2026-11-04

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_wyrdold_claude/references_head_v2/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is a CORRECTION of the approved head turnaround (inputs 1-4): keep the same woman, hood, circlet, braids, pearls, pendant, colours,
camera, framing and lighting; change ONLY the three points under "Changes". The images become the paint reference for a 3D head, so every
view must show the same person and the same coif from its own angle.

## Inputs (attached, in order)
1. `references_head/01_front.png`: approved FRONT bust (identity, hood, circlet, braids, framing, lighting).
2. `references_head/00_three_quarter.png`: approved three-quarter bust from her right (she looks toward IMAGE RIGHT).
3. `references_head/02_profile.png`: approved profile of her left side (face points to IMAGE LEFT).
4. `references_head/03_back.png`: approved back view.
5. `references_hd/mm9_head_views.png`: renders of the ORIGINAL Might and Magic IX model's head: authority for the hood shape and the
   pale cloth showing under the hood above the forehead. Low resolution and faceting are NOT the design.

## Changes (the only differences from inputs 1-4)
1. **White linen coif under the hood.** A soft ivory-white linen coif (a close-fitting cloth cap, like a medieval wimple cap) covers the
   top of her head and her hair inside the hood: it shows as a band of soft white cloth, about two fingers to three fingers wide, between
   the hood's front edge and her forehead, running down both temples to the jaw line beside the cheeks. Visible soft cloth folds and
   gathers, a faint linen weave, gentle shading where the hood overhangs it. Its lower front edge lies on the forehead, and the thin gold
   circlet with the small dark-red stone sits on the coif's lower edge at the centre of the forehead. A few strands of white-grey hair may
   show at the temples; the two long grey braids hang from under the coif at the temples, as before. It must read clearly as CLOTH, not
   as a bald scalp, not as white hair and not as a smooth helmet.
2. **Natural soft wrinkles.** Keep her about 85 years old and clearly aged, but render the wrinkles as soft natural creases in the skin's
   own warm tone: a few soft horizontal forehead lines, crow's feet at the outer eye corners, soft folds under the eyes, nasolabial folds,
   soft lines beside the mouth, a softly creased neck. Smooth skin with fine pores between the creases. NO network or mesh of fine dark
   lines, no outlined or drawn-on wrinkles, no orange or red lines, no blotches.
3. **Gentle closed-lips smile.** A calm, warm, kind expression: lips closed and relaxed, the mouth corners only slightly raised, the mouth
   no wider than in a relaxed neutral face, thin natural old lips with no lipstick. Eyes open and clear, kind, with visible pale-blue
   irises. Warm ruddy-tan skin, a little rosier on the cheeks (MM9's face is warm and ruddy), never pale or grey.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `01_front.png` | perfectly straight FRONT bust as input 1 (generate FIRST, from input 1) |
| `00_three_quarter.png` | three-quarter bust from her RIGHT side as input 2 (she looks toward IMAGE RIGHT) |
| `02_profile.png` | pure 90-degree profile of her LEFT side as input 3: the face points to IMAGE LEFT |
| `03_back.png` | straight BACK of the hooded head and shoulders as input 4 (the coif does not show from the back) |

Generate 01 first; then 00, 02, 03 each from its own approved view plus the selected new 01 (for the coif and the face). At most ONE
corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view, prompt, inputs with sha256, output
path, selected flag, reason, superseded runs, size, alpha extrema) and a `selected_views_review.png` contact sheet of the four views.

Per-image checks (re-run before selecting): the requested view; the coif clearly white cloth with folds in 01, 00, 02; circlet on the
coif's lower edge; lips closed, corners only slightly raised; eyes open; no wrinkle net or drawn lines; whole head and hood inside the
frame; true transparent background; square; braids grey; even soft neutral studio lighting (the image is baked into a texture): no
dramatic light, no rim light, no dark shadow under the lower lip or chin.

## Do NOT
change the hood colour or shape; make her stern, fierce, cold, sinister or witch-like; show teeth; add a veil over the face or the
shoulders, a crown or extra jewellery; show the ears; stylise as a cartoon; add text, a floor, a background or a shadow; crop.
