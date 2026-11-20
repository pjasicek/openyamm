# Codex brief: HD HEAD turnaround for the MM9 Wyrde of the Known, Igrid (mm9_wyrdold_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_wyrdold_claude/references_head/`. Do not edit any other file,
do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the
ORIGINAL MM9 3D model with its skin, shown in renders of that model, and the approved HD body masters.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views.png`: close renders of the ORIGINAL model's head (three-quarter from her right, front, her left side facing
   IMAGE LEFT, back, her right side facing IMAGE RIGHT): FACE, HAIR, BRAIDS, CIRCLET AND HOOD AUTHORITY. Low resolution, faceting and dark
   shading are NOT the design.
2. `references_hd/00_three_quarter_clean.png`: the approved HD body master: identity, face, hood, circlet, braids and colours of the HD look.
3. `references_hd/01_front_clean.png`: the approved HD front master.
4. `references_hd/mm9_skin_x4.png`: the original skin enlarged, SURFACE MATERIAL AND COLOUR ONLY (face, hair and braid texels).

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `01_front.png` | perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `00_three_quarter.png` | front three-quarter bust from her RIGHT side (she looks toward IMAGE RIGHT, as input 2), eye level |
| `02_profile.png` | pure 90-degree profile of her LEFT side: the face points to IMAGE LEFT |
| `03_back.png` | straight BACK of the hooded head and shoulders |

Generate 01 first; then 00, 02, 03 with the selected 01 as an extra input. At most ONE corrective regeneration per view; keep raw returns in
`raw/`. Write `generation_runs.json` (id, view, prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha
extrema) and a `selected_views_review.png` contact sheet of the four selected views.

## Common prompt content
TASK CONTEXT, GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING Might and Magic IX character
(inputs 1-3). Not a new design. Output ONE bust only: the whole head in its hood, the neck with the pearl choker, the top of the pendant
and the top of the shoulders with the hood's drape, centred with generous margins, never cropped. Near-orthographic camera at eye level,
head level and upright in the frame (the body's stoop is NOT shown in these head views), LIPS CLOSED (no teeth showing). Even soft neutral
studio lighting, no dramatic light, no rim light, no strong shadows (the image is baked into a texture). Sharp fine detail: skin pores and
fine wrinkles, brows, lashes, lips, hair strands, braid weave, cloth weave, gold. The neck and the skin under the jaw are visible,
continuous with the face, and evenly lit (no dark shadow under the lower lip or on the chin). ONE natural brow per eye, ONE natural lip
line, no pale band under the lower lids, no makeup or lipstick. Clean edges between skin, hair and hood: each keeps its own colour, no skin
tone in the hood or hair, a soft natural hairline (no pale band between hair and forehead).

## Identity
- Igrid, about 85 years old: a deeply wrinkled, KIND old face, warm ruddy-tan skin, fine wrinkles on the forehead, crow's feet, soft smile
  lines; bright pale-blue eyes, open and clear with visible irises; thin soft white-grey brows; a long straight nose; a broad calm warm
  closed-lips smile with thin natural old lips (no lipstick); a soft rounded chin.
- HAIR: thin white-grey hair parted in the middle and drawn back under the hood at the temples; two long thin GREY BRAIDS hanging from inside
  the hood down both sides of the face in front of the shoulders.
- CIRCLET: a thin gold circlet with a small dark-red cabochon stone at the centre of the forehead, just inside the hood's front edge.
- HOOD: a deep DARK-BROWN (cocoa / umber) wool hood with a faint darker damask pattern, covering the top, sides and back of the head and the
  ears, rising to a soft point on top, its front edge framing the face closely and folding softly; it drapes in soft folds round the neck
  onto the shoulders. It does not cover the face or the front of the neck. No ears visible.
- NECK: a choker of small pearls with gold beads; below it the top of a gold pendant with an amber stone.

Per-image checks (re-run before selecting): the requested view (02 faces IMAGE LEFT); lips closed; eyes open; whole head and hood inside
the frame; true transparent background; square; one brow per eye; no dark smudge under the lower lip; braids grey.

## Do NOT
change the hood colour; make her stern, fierce, cold, sinister or witch-like; show teeth; add a veil, a crown or extra jewellery; show the
ears; stylise as a cartoon; add text, a floor, a background or a shadow; crop.
