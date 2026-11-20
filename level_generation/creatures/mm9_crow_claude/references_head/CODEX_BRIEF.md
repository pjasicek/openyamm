# Codex brief: HD HEAD turnaround for the MM9 Bird (crow) (mm9_crow_claude, head rework 2026-10-30)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_crow_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

Why: the user rejected the head of the first 3D crow: a boxy flat skull, a LONG THIN wading-bird beak about 2.5 times
the head length with almost no depth at the base, and a ragged cluster around the eye. These head views are used
twice: a head-only 3D model is built from `00_three_quarter.png`, and all four views paint the head texture. So the
SHAPE (domed crown, short deep beak, eye position, smooth throat) must be clear and readable in every view.

## Inputs (attached, in order)
1. `references_head/input_raven_head_crop.png` and 2. `references_head/input_raven_reference.png` — a real raven in
   flight chosen by the user: SHAPE AUTHORITY for the head and beak (rounded domed crown flowing smoothly into the
   neck; a SHORT, DEEP, heavy beak about 1.2-1.5 times the head length, thick at the base, the upper mandible hooking
   down at the tip; the eye just above the gape line; NO chin; smooth throat feathers). Its pose (head bent down) is
   NOT the pose wanted here.
3. `references_head/mm9_head_views.png` — close renders of the ORIGINAL Might and Magic IX crow head with its skin
   (left profile, three-quarter, front, top): COLOUR authority (blue-black plumage with a blue sheen, grey-black beak,
   small dark eye). Its faceting, blur and the over-long faceted beak are NOT the design.
4. `references_head/mm9_skin_tier1_x4.png` — the original skin texture enlarged 4x, FEATHER MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized)
| File | View |
|---|---|
| `02_profile.png` | pure 90-degree profile of the bird's LEFT side: the beak points to IMAGE LEFT (generate FIRST) |
| `00_three_quarter.png` | front three-quarter: the bird's RIGHT side toward the camera, beak toward IMAGE RIGHT, camera slightly above |
| `01_front.png` | straight FRONT: beak pointing at the camera, both eyes visible |
| `03_top.png` | straight down from above: beak toward the IMAGE TOP |

Generate 02 first; then make 00, 01 and 03 with your selected 02 as an extra input so all four are the SAME head.
At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view,
prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the four selected views.

## Common prompt content
TASK CONTEXT — GAME ASSET: high-definition 3D modelling and TEXTURING reference of the HEAD of an existing Might and
Magic IX monster, a large black crow / raven. Output ONE subject only: the bird's head with the upper NECK, cut
cleanly at the base of the neck (a short neck stub about as long as the head, ending in a clean round cut, no body,
no wings, no shoulders). Centred with generous margins, never cropped. Near-orthographic camera, the head held LEVEL
(the beak pointing straight forward, horizontal, the gape line horizontal) as a raven holds it in flight, the neck
extending straight back behind the head. Even soft neutral studio lighting, no dramatic light, no rim light, no
strong shadows (the image is baked into a texture). Sharp fine detail: small contour feathers, nasal bristles over the
base of the beak, the fine texture of the beak.

## Identity and anatomy (follow inputs 1-2 for SHAPE, inputs 3-4 for COLOUR)
- Crown: a smoothly rounded, domed crown and forehead rising from the base of the beak, flowing without a step into the
  back of the head and the neck. No crest, no flaps, no spikes, no ragged tufts.
- Beak: SHORT, DEEP and heavy: its length from the forehead feathers to the tip about 1.3 times the length of the
  head behind it; its depth at the base about one third of its length; the upper mandible arching and hooking down
  over the lower one at the tip; the lower mandible straight; the beak CLOSED. Grey-black with a faint sheen. Black
  nasal bristles cover the base of the upper mandible.
- Eye: a small dark eye with a faint dark-brown iris and a tiny highlight, set just ABOVE the gape line and a little
  behind the base of the beak, in a smooth feathered face. Nothing ragged around the eye.
- Throat: smooth, slightly shaggy throat feathers running straight back from the base of the lower mandible along the
  underside of the neck. NO chin, no pouch, no dewlap, no hanging flap.
- Plumage: glossy blue-black with a blue-violet sheen (inputs 3-4). Symmetric left/right.

Do NOT: open the beak, make the beak long and thin or curved like a curlew/ibis, add a crest or ear tufts, show a
chin or wattle, add a body, wings or shoulders, a perch, text, a floor or a shadow, colours other than black /
blue-black and the grey-black beak.

## Per-image checks (re-run before selecting)
One head with a short neck stub cut cleanly; beak short (about 1.3x head length), deep at the base, hooked at the tip,
closed, horizontal; domed crown; eye just above the gape; smooth throat, no chin; the correct side toward the correct
image side (02: beak to image LEFT; 00: beak toward image RIGHT); true transparent background; nothing cropped.
