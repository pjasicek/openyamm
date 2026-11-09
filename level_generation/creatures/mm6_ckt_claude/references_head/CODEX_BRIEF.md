# Codex brief: HD HEAD reference views for the MM6 Cockatrice (mm6_ckt_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_ckt_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Why: in the full-body references the head is small, so the 3D head texture came out muddy (smeared red eye patches,
stray teal fringes). These views will texture the EXISTING 3D head (a head-only retexture of the same mesh), so they
must show the SAME head as the accepted body references, much larger, with the same proportions.

Use your built-in image generation, record format as in
`level_generation/creatures/mm6_pmn2_claude/references_head/generation_runs.json`. Attached inputs, in order:
1. `references_hd/01_front.png` — accepted full-body HD front view: identity authority for this head. Match it.
2. `references_hd/04_right.png` — the same creature, right profile.
3. `references_hd/00_three_quarter.png` — the same creature, three-quarter.

## Deliverables (5 images, transparent background, square, unresized returns; 1024 or 1254 px as the tool returns)
- `00_front.png` — head straight on (primary; generate first)
- `01_three_quarter.png` — front-right three-quarter (45 degrees toward the creature's right)
- `02_left.png` — the creature's LEFT profile (pure side view, beak pointing image LEFT)
- `03_back.png` — straight from behind
- `04_right.png` — the creature's RIGHT profile (pure side view, beak pointing image RIGHT)
Generate 01–04 with 00 as an additional input so all five are the SAME head.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs) and a `selected_views_review.png` contact sheet. Regenerate a view if it breaks the checks below.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: high-definition HEAD-AND-NECK reference of the EXISTING Might and
Magic VI Cockatrice, for texturing its 3D head. The head must be the SAME head as in inputs 1–3, shown large. Not a
new design.
Framing: like a sculpted bust: the vulture head, the long bare curved neck and the collar ruff of pale ivory spiky
feathers at its base; cut cleanly just below the ruff (no wings, no body). Head and neck fill about 75% of the frame
height, centred, generous transparent margins, near-orthographic camera at eye height, head level, beak closed.
Transparent background, no floor, no shadow, no text. Even soft neutral studio light that still shows form.
Beautifully detailed, realistic semi-stylised game creature sculpt with sharp fine detail (wrinkled bare skin,
beak keratin, feather barbs).

Head identity (from the inputs): a VULTURE head: bare pink wrinkled skin on the head and the long neck; a large hooked
ORANGE-YELLOW BEAK with a darker tip and a cere at its base; small round dark eyes with a glossy highlight, each set
in a clean patch of bright RED bare skin (a smooth red mask around the eye like a turkey vulture's, NOT blood, NOT a
wound); a single short ivory spike on the crown; a ruff of pale ivory spiky feathers around the base of the neck.

Do NOT: add blood, wounds, open sores or dark smears around the eyes; add any green, teal or turquoise colour
anywhere on the head or neck; add feathers to the head; open the beak; add a crest or extra horns; crop the beak.

Checks per image: pink bare head and neck, clean red eye patches with dark round eyes, orange hooked beak, ivory crown
spike, ivory ruff at the base, no teal anywhere, transparent background, same head as input 1.
