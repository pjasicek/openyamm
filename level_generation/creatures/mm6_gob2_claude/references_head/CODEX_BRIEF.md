# Codex brief: HD HEAD reference views for the MM6 Goblin (mm6_gob_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_gob_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Why: in the full-body references the face is under ~150 px, so the 3D goblin's face texture is soft. These views
will texture the EXISTING goblin head (a head-only retexture of the same mesh), so they must show the SAME head as
the accepted body references, much larger, with the same expression and proportions.

Use your built-in image generation, record format as in
`level_generation/creatures/mm6_wdm_claude/references_head/generation_runs.json`. Attached inputs, in order:
1. `references/01_front.png` — accepted full-body HD front view: identity authority for this head. Match it.
2. `references/04_right.png` — the same goblin, its right side (the side with the three gold ear hoops).
3. `references/00_smart_topology_three_quarter.png` — the same goblin, three-quarter.

## Deliverables (5 images, transparent background, 1024 x 1024 square, unresized returns)
- `00_front.png` — head straight on (primary; generate first)
- `01_three_quarter.png` — front-right three-quarter (45 degrees toward the goblin's right, the hoop ear)
- `02_left.png` — the goblin's LEFT profile (pure side view, ear without hoops)
- `03_back.png` — straight from behind
- `04_right.png` — the goblin's RIGHT profile (pure side view, three gold hoops on that ear)
Generate 01–04 with 00 as an additional input so all five are the SAME head, SAME expression, SAME proportions.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs) and a `selected_views_review.png` contact sheet. Regenerate a view if it breaks the checks below.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: high-definition HEAD-AND-NECK reference of the EXISTING Might and
Magic VI Goblin, for texturing its 3D head. The head must be the SAME head as in inputs 1–3, shown large. Not a new
design.
Framing: head and neck only, like a sculpted bust WITHOUT shoulders: the neck ends in a clean horizontal cut a little
below the jaw (no shoulders, no armour, no straps, no gorget). Head including the full ears fills about 75% of the
frame height, centred, generous transparent margins, near-orthographic camera at eye height, head level.
Transparent background, no floor, no shadow, no text. Even soft neutral studio light that still shows form.
Beautifully detailed, credible sculpt with semi-realistic game materials, sharp fine detail (skin pores, wrinkles).

Head identity (from the inputs): olive-green bald goblin skull with fine mottled darker green pigment; heavy joined
brow with deep wrinkles; small deep-set YELLOW eyes with dark pupils; short broad nose with flared nostrils; slight
snarl, jaw almost closed, uneven yellowed teeth visible between the lips, lower jaw projecting; large pointed fleshy
ears angled up and back, inner ear brownish; the skull tapers at the back into a short horizontal occipital wedge
behind the ears; THREE small gold hoops on the RIGHT ear only. Neck olive-green and sinewy.

Do NOT: change the expression between views, add hair, horns, helmet, extra jewellery, blood; do not move the hoops
to the left ear; do not change colours; do not crop the ears.

Checks per image: ears fully in frame; yellow eyes; teeth visible in the snarl; hoops only on the right ear; occipital
wedge in the profiles and the back view; neck cut cleanly below the jaw; transparent background; same head as input 1.
