# MM6 Demon Queen — HD head turnaround

## Scope

Image generation only, with your built-in image generation tool. Write only into
`level_generation/creatures/mm6_qfi_claude/references_head/`. No builds, no other files, no Meshy.

A faithful high-definition head reference of an existing Might and Magic VI creature, the Demon Queen, for a
head-only 3D model that is grafted onto the body model. Not a new design: the head must be exactly the head of the
accepted body references (inputs 1–3).

## Inputs (attached, in this order)

1. `input_body_front_head_crop.png` — head and shoulders cropped from the accepted front body reference. AUTHORITY.
2. `input_body_threequarter_head_crop.png` — the same from the accepted three-quarter reference. AUTHORITY.
3. `input_body_left_head_crop.png` — the same from the accepted left profile reference. AUTHORITY.
4. `input_native_qfia0_head_crop.png` — the original tiny game sprite of the head (identity only).

## Deliverables

| File | View |
|---|---|
| `01_three_quarter.png` | front three-quarter (her right cheek toward the camera), camera at eye height |
| `00_front.png` | front |
| `02_left.png` | her LEFT profile (the face points to the image RIGHT) |
| `03_back.png` | back of the head |

Square 1254x1254, transparent background, no text, no shadow. A bust: head, horns and neck down to just below the
collar bones, cut cleanly horizontally there; shoulders as short stubs. The whole horn tips inside the frame with
margin (the horns are tall: leave room above).

This run: generate `01_three_quarter.png` first, check it, then the other three with it as the design reference.
One corrective regeneration per view at most.

## The head (from the inputs)

- A narrow, elegant, sharp-featured demonic female face: high cheekbones, narrow tapering chin, thin sharp nose,
  narrow lips, a stern cruel expression, NOT a soft or childlike face. Crimson red skin with a fine reptilian scale
  texture.
- Eyes: almond-shaped, glowing violet irises, dark sclera edge; thin dark red brow ridges.
- Two long slim ivory fangs pointing straight down from the upper jaw at the corners of the mouth, reaching below
  the chin line (as in inputs 1–2).
- Two very long straight ivory horns rising almost vertically from the top of the head, symmetric about the centre
  line, slightly apart, gently curving outward-back at the tips.
- A symmetric crown of shorter curved ivory spikes ringing the head: about five per side, from the temples down
  behind the jaw, pointing outward and slightly up, framing the face like a ruff (as in inputs 1–2). The head and
  spikes are left/right symmetric.
- Bald smooth scaled scalp; no hair, no ears visible (the spikes cover the ear area).
- Neck slim and long; a hint of the black studded shoulder straps at the cut is optional.
- Even soft studio light, near-orthographic, no rim light, no glow halo.

## Do NOT

- No hair, crown jewellery, helmet, earrings, extra horns, wings or text.
- Do not change the face's character from inputs 1–3 (sharp demonic, red, violet eyes, fangs).
- Do not crop horn tips or spikes.

## Per-image checks

- Face matches inputs 1–3; horns and spike crown symmetric with counts as above; fangs present.
- True alpha, 1254x1254, bust cut below the collar bones, nothing cropped.

## Records

Write `generation_runs.json` (id, prompt, input sha256, output path, selected flag, reason, superseded runs) and
`selected_views_review.png`. Keep unselected returns under `superseded/`.
