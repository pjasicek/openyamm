# MM8 female Dark Elf peasant (m428) head turnaround brief

Scope: image generation only; write only into `level_generation/creatures/mm8_m428_claude/references_head/`.
Inputs: `../references_hd/01_front.png` and `../references_hd/00_three_quarter.png` (the selected full-body HD
masters, exact identity authority) and `../references_hd/03_left.png` (profile authority).

Deliverables (unresized returns, square 1254x1254 if supported, else the largest unresized square; transparent
background; exactly one bust each):

| File | View |
|---|---|
| `00_front.png` | exactly front, face looking straight at the camera |
| `01_three_quarter.png` | front three-quarter showing her right side (~35 degrees) |
| `02_profile.png` | exact LEFT profile: her nose points to IMAGE LEFT, only the left side of the face visible |
| `03_back.png` | exactly back: back of the head and hair, no face |

Prompt content: one sharp HD HEAD modelling/texture reference of the EXISTING MM8 female Dark Elf peasant. The SAME
face as the masters: soft oval adult female face, dark warm brown skin (not blue, grey or purple), straight nose,
full lips with a natural muted lip colour, light grey eyes, long pointed elven ears standing out from the hair,
very long straight silver-white hair with a short straight fringe, hair falling behind the shoulders, two narrow
side locks framing the face. Realistic restrained game sculpt, fine skin pores and hair strands, even soft neutral
studio light. Bust only: head, neck and the top of the shoulders with a little of the pale grey chemise and green
bodice straps; keep the whole head, ears and the hair at the top of the head inside the canvas with at least 8 %
transparent margins at top and sides. Near-orthographic, head upright, neutral expression. Genuine transparent
background (alpha 0 outside the bust), no haze, floor, shadow, labels or panels. No jewellery, make-up changes,
glowing eyes or new features.

Checks per image: one bust; view direction as in the table (profile nose to image LEFT); two pointed ears where
visible; skin and hair colours as the masters; nothing cropped at the top; alpha 0 outside. One corrective
regeneration per view at most.

Records: `generation_runs.json` (id, prompt, input paths with sha256, output, sha256, selected, reason).
