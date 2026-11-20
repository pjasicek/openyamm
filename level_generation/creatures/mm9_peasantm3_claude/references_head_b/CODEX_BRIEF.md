# Codex brief: HD HEAD turnaround for the MM9 townsman PeasantM3, skin B (mm9_peasantm3_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantm3_claude/references_head_b/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_b.png` — close renders of the ORIGINAL Might and Magic IX model's head with skin B
   (front, left profile, three-quarter, right profile, back): FACE, HAIR AND COLOUR AUTHORITY for this man. Its low
   resolution, faceting and dark shading are NOT the design.
2-5. `references_head/01_front.png`, `00_three_quarter.png`, `02_profile.png`, `03_back.png` — the approved HD head
   turnaround of ANOTHER man (skin A) on the SAME 3D head: take ONLY the head shape, size, framing, camera, the hair's
   outer silhouette and volume, the neck and shoulders from them, view for view. The face, hair colour and texture,
   beard and expression must be the skin-B man of input 1, not the blond man.
6. `references_hd/mm9_skin_x4_b.png` — the original skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `01_front.png` | perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `00_three_quarter.png` | front three-quarter bust from the character's RIGHT side: he looks toward IMAGE RIGHT and toward the viewer, as input 3; eye level |
| `02_profile.png` | pure 90-degree profile of the character's LEFT side: the face points to IMAGE LEFT |
| `03_back.png` | straight BACK of the head and shoulders |

Generate 01 first (matching input 2's framing); then make 00, 02 and 03 with your selected 01 and the matching view of inputs 2-5 as inputs so all four are the SAME head on the same silhouette.
At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view,
prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the four selected views.

## Common prompt content
TASK CONTEXT — GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING
Might and Magic IX character (inputs 1-3). Not a new design. Output ONE bust only: the whole head with all hair, the
neck, and the top of the shoulders, centred with generous margins, never cropped (hair fully inside the frame).
Near-orthographic camera at eye level, head level, calm, warm and friendly expression (relaxed, a hint of a kind smile in the eyes, never fierce or cold), mouth CLOSED with ONE pair of natural lips. Even soft neutral studio
lighting, no dramatic light, no rim light, no strong shadows (the image is baked into a texture). Sharp fine detail:
skin pores, fine wrinkles, brows, lashes, lips, beard and hair strands, velvet and brocade. Eyes open with visible irises; ONE brow over each eye; no light band between brows and eyes; no pale crescent under the lower lid; no heavy red eye rims; one nose with two natural nostrils. The neck skin under the jaw and
chin must be clearly visible and continuous with the face (no collar hiding the jaw line). Clean edges between skin
and hair: hair has its own colour with no skin tone bleeding into it, and skin carries no hair colour except the light
stubble.

## Identity
A different human townsman, about thirty-five: fair, slightly pale skin with a warm tone; a lean face with defined
cheekbones; a straight nose; dark brown eyes, open, irises visible; ONE natural dark-brown brow over each eye; a dark
brown moustache over the upper lip and a narrow short dark goatee on the chin with a thin line of short beard along the
jaw (as input 1), the cheeks clean-shaven; thick dark-brown wavy hair with soft lighter brown highlights, swept back
from the forehead, falling to just below the ears and to the nape, covering the tops of the ears, within the SAME
outer hair silhouette as inputs 2-5. At the bottom edge: a brown knitted wool tunic with a gold brocade neckline band
and a round silver knotwork brooch at the throat.

Per-image checks (re-run before selecting): same man as input 1, same head shape and hair silhouette as the matching view of inputs 2-5; the requested view (02 faces IMAGE LEFT; 00 looks
toward IMAGE RIGHT); whole head and hair inside the frame; mouth closed; true transparent background; square.

## Do NOT
- change the face, hair, colours or age; give him a full beard or the blond man's face; add a hat, hood, jewellery or headwear; stylise as a cartoon; add
  text, a floor, a background or a shadow; crop.
