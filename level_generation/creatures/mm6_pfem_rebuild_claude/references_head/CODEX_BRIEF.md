# Codex brief: HD HEAD reference views for the MM6 Female Peasant (mm6_pfem_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_pfem_claude/references_head/`.
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
Magic VI Female Peasant, for texturing its 3D head. The head must be the SAME head as in inputs 1–3, shown large. Not a new
design.
Framing: head and neck only, like a sculpted bust WITHOUT shoulders: the neck ends in a clean horizontal cut a little
below the jaw (no shoulders, no clothing); the long braid continues down behind the neck and is cut at the same height. Head including all hair fills about 75% of the frame
height, centred, generous transparent margins, near-orthographic camera at eye height, head level.
Transparent background, no floor, no shadow, no text. Even soft neutral studio light that still shows form.
Beautifully detailed, realistic semi-stylised game character sculpt with sharp fine detail (skin pores, hair strands).

Head identity (from the inputs): young woman with fair, lightly freckled skin; chestnut-auburn hair parted in the middle, smoothed back over the head into ONE long thick braid hanging down the back; a thin plain GOLD circlet band across the forehead and around the head; hazel-green eyes, natural brows, straight nose, full calm closed lips, soft neutral expression; small ears partly visible.

Do NOT: change the expression between views, change the hair style or colour, add jewellery, hats or clothing,
add scars or makeup; do not crop hair or the braid, do not loosen the braid.

Checks per image: middle parting, braid at the back, gold circlet band, hazel eyes; neck cut cleanly below the jaw with no clothing; transparent background; same head as
input 1.
