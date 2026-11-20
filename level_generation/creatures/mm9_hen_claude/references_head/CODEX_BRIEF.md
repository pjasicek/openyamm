# Codex brief: HD HEAD turnaround for the MM9 Hen (mm9_hen_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_hen_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

Why: a 3D model built from the full-body reference came out with a weak head: a thin pointed beak and, worse, the
wattles under the beak read as an OPEN, gaping lower jaw. A head-only 3D model is built from `00_three_quarter.png`,
so the SHAPE must be clear and unambiguous: a CLOSED, short, deep beak whose two mandibles touch along a tight gape
line, and the fleshy wattles hanging as separate lobes BELOW and BEHIND the beak, never forming a jaw.

## Inputs (attached, in order)
1. `references_head/input_body_master_head.png` — the head of the accepted HD full-body reference of this bird: the
   IDENTITY, SHAPE and COLOUR authority (comb, eye, beak colour, wattles, feathers). Grey is background.
2. `references_head/mm9_head_views.png` — close renders of the ORIGINAL Might and Magic IX model's head with its skin
   (left profile, three-quarter, front, top): the beak points straight FORWARD, level. Its faceting and blur are NOT
   the design.
3. `references_head/mm9_skin_tier1_x4.png` — the original skin enlarged 4x, MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized)
| File | View |
|---|---|
| `02_profile.png` | pure 90-degree profile of the bird's LEFT side: the beak points to IMAGE LEFT (generate FIRST) |
| `00_three_quarter.png` | front three-quarter: the bird's RIGHT side toward the camera, beak toward IMAGE RIGHT, camera slightly above |
| `01_front.png` | straight FRONT: beak pointing at the camera, both eyes visible |

Generate 02 first; then make 00 and 01 with your selected 02 as an extra input so all three are the SAME head.
At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view,
prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the three selected views.

## Common prompt content
TASK CONTEXT — GAME ASSET: high-definition 3D modelling reference of the HEAD of an existing Might and Magic IX
farmyard animal, . Output ONE subject only: the bird's head with the upper NECK, cut cleanly at the base of
the neck (a short feathered neck stub about as long as the head, ending in a clean round cut, no body, no wings, no
shoulders). Centred with generous margins, never cropped (the whole comb inside the frame). Near-orthographic camera,
the head held LEVEL: the beak pointing straight forward and horizontal, the gape line horizontal, the neck rising
straight up and slightly back below the head. Even soft neutral studio lighting, no dramatic light, no strong
shadows. Sharp fine detail: small white contour feathers, the comb's fine fleshy texture, the beak's horn texture.

## Identity and anatomy (input 1 for identity and colour)
- Comb: a small, low, bright-red single comb with five small rounded points along the top of the head, from the
  base of the beak back over the crown (as input 1).
- Wattles: two small rounded red wattles directly under the base of the beak, compact (shorter than the beak).
- Beak: SHORT, DEEP and stout, pale horn-yellow: a conical beak about as long as the eye-to-beak distance, deep at the
  base (its depth at the base about half its length), the upper mandible gently curving down to a blunt point
  overlapping the lower mandible. The beak is CLOSED: the lower mandible is a solid pale wedge pressed against the
  upper one along its whole length, with no gap, no dark mouth, no tongue. The nostril is a small slit at the base of
  the upper mandible.
- Eye: a round amber-orange eye with a black pupil and a small highlight, in a patch of bare red skin, set level with
  the base of the beak and a little behind it.
- Throat: smooth white feathers run from the base of the lower mandible back and down the throat; the wattles hang in
  front of the throat as thin separate red lobes, attached only at the base of the lower mandible.
- Plumage: clean white feathers with soft light-grey shading. Symmetric left/right.

Do NOT: open the beak, show a mouth, tongue or a gap between the mandibles, make the beak long, thin or hooked, merge
the wattles with the beak into a jaw shape, add a body, wings or shoulders, a perch, text, a floor or a shadow, or any
plumage colour other than white.

## Per-image checks (re-run before selecting)
One head with a short neck stub cut cleanly; beak short, deep, pale yellow, CLOSED with no gap, horizontal; wattles as
separate lobes below the beak; comb complete; amber eye; the correct side toward the correct image side (02: beak to
image LEFT; 00: beak toward image RIGHT); true transparent background; nothing cropped.
