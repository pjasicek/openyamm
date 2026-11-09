# Codex brief: HD head turnaround for the MM9 dog (mm9_dog_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_dog_claude/references_head/`. No builds, no
Meshy, no other files. Use your built-in image generation tool. Record `generation_runs.json` (id, prompt, inputs
with sha256, output, selected, reason) and a `selected_views_review.png` contact sheet.

## Inputs (attached, in order)
1. `references_hd/00_three_quarter.png`: the accepted HD dog: identity, colours, fur.
2. `references_hd/01_front.png`: the same dog from the front.
3. `references_hd/03_left.png`: the same dog in profile.
4. `references_hd/mm9_head_views.png`: renders of the original low-poly MM9 dog head, markings only, not the shape.

## Deliverables (true transparent background, unresized 1254x1254 returns, bust only)
`01_front.png`, `02_back.png`, `03_left.png` (pure profile, nose to IMAGE LEFT), `04_right.png` (pure profile, nose to
IMAGE RIGHT). Generate 01 first and use it as an input for the others, so all four show the same head. At most one
corrective regeneration per view.

## Prompt content
Faithful high-definition reconstruction of the same dog's head as a texturing reference, the head of inputs 1-3 at
much higher detail: sharp short fine fur, semi-realistic.
- Black-and-tan: rich tan/chestnut head and cheeks, dark brown-black muzzle toward the black nose, dark hanging ears,
  brown eyes with defined lids and a small catchlight, wet black nose with nostrils, dark lips.
- The mouth CLOSED in these views (lips together), the dark lip line clearly visible, no tongue, no teeth: the mouth
  interior is modelled separately.
- Pose: head perfectly straight and level, strictly left/right symmetric, ears hanging down beside the head. Include the
  upper neck as a stub, no shoulders.
- Light: even soft neutral studio light, no strong shadows, near-orthographic. Nothing cropped, no floor, no text.
Do NOT add a collar, change the colours, turn the head or open the mouth.

## Per-image checks
Same head in all views; two hanging ears; both eyes open; black nose; closed mouth; correct side faces the correct
image side; true alpha; 1254x1254.
