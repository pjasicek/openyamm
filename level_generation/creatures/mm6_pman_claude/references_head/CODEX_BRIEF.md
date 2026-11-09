# Codex brief: HD HEAD reference views for the MM6 Male Peasant (mm6_pman_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_pman_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Why: in the full-body references the face is under ~150 px, so the 3D face texture is soft. These views will
texture the EXISTING 3D head (a head-only retexture of the same mesh), so they must show the SAME head as the
accepted body references, much larger, with the same expression, hair and proportions.

Use your built-in image generation, record format as in
`level_generation/creatures/mm6_gob_claude/references_head/generation_runs.json`. Attached inputs, in order:
1. `references/01_front.png` — accepted full-body HD front view: identity authority for this head. Match it.
2. `references/04_right.png` — the same character, right side.
3. `references/00_smart_topology_three_quarter.png` — the same character, three-quarter.

## Deliverables (5 images, transparent background, square, unresized returns; 1024 or 1254 px as the tool returns)
- `00_front.png` — head straight on (primary; generate first)
- `01_three_quarter.png` — front-right three-quarter (45 degrees toward the character's right)
- `02_left.png` — the character's LEFT profile (pure side view)
- `03_back.png` — straight from behind
- `04_right.png` — the character's RIGHT profile (pure side view)
Generate 01–04 with 00 as an additional input so all five are the SAME head, SAME expression, SAME hair.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs) and a `selected_views_review.png` contact sheet. Regenerate a view if it breaks the checks below.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: high-definition HEAD-AND-NECK reference of the EXISTING Might and
Magic VI Male Peasant, for texturing its 3D head. The head must be the SAME head as in inputs 1–3, shown large. Not a new
design.
Framing: head and neck only, like a sculpted bust WITHOUT shoulders: the neck ends in a clean horizontal cut a little
below the jaw (no shoulders, no clothing). Head including all hair fills about 75% of the frame
height, centred, generous transparent margins, near-orthographic camera at eye height, head level.
Transparent background, no floor, no shadow, no text. Even soft neutral studio light that still shows form.
Beautifully detailed, realistic semi-stylised game character sculpt with sharp fine detail (skin pores, hair strands).

Head identity (from the inputs): young man with fair skin and light stubble; short thick curly auburn-brown hair; blue-grey eyes under straight brows; straight nose; firm closed mouth, serious neutral expression; strong jaw and chin; ears visible.

Do NOT: change the expression between views, change the hair style or colour, add jewellery, hats or clothing,
add scars or makeup; do not crop hair.

Checks per image: short curly auburn hair, stubble, blue-grey eyes, ears visible; neck cut cleanly below the jaw with no clothing; transparent background; same head as
input 1.
