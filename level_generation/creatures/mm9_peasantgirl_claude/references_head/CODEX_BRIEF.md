# Codex brief: HD HEAD turnarounds for the MM9 peasant girls, three faces (mm9_peasantgirl_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantgirl_claude/references_head/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is
the ORIGINAL MM9 3D model with its three skins, shown in renders of that model.

The same girl's body carries three different children in the original game: girl **g2** (auburn-haired, freckled, rosy), girl **g3**
(brown hair with a short curly fringe) and girl **g1e** (an ELF girl with light-brown hair). All three are about nine years old. Make g2
first, then g3 and g1e on the SAME head shape, framing and pose; only the face, the hair colour/fringe, the collar colour and (g1e) the ears
change.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_g2.png`: close renders of the ORIGINAL model's head with skin g2, five views (front three-quarter, front,
   her left side facing IMAGE LEFT, back, her right side facing IMAGE RIGHT): FACE g2 AND HAIR AUTHORITY. Low resolution, faceting and the
   dark shading are NOT the design.
2. `references_hd/00_three_quarter.png`: the approved HD body master with face g2: identity, face structure, hair and colours of the HD look.
3. `references_hd/01_front.png`: the approved HD front master (face g2, front).
4. `references_hd/mm9_skin_x4_g2.png`: skin g2 enlarged, SURFACE MATERIAL AND COLOUR ONLY (face and hair texels at the top left).
5. `references_hd/mm9_head_views_g3.png`: the same five views with skin g3: FACE g3 AND HAIR g3 AUTHORITY.
6. `references_hd/mm9_skin_x4_g3.png`: skin g3 enlarged, SURFACE MATERIAL AND COLOUR ONLY.
7. `references_hd/mm9_head_views_g1e.png`: the same five views with skin g1e (elf ears): FACE g1e AND HAIR g1e AUTHORITY.
8. `references_hd/mm9_skin_x4_g1e.png`: skin g1e enlarged, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `g2_01_front.png` | face g2: perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `g2_00_three_quarter.png` | face g2: front three-quarter bust, she looks toward IMAGE LEFT (as input 2), eye level |
| `g2_02_profile.png` | face g2: pure 90-degree profile of her LEFT side: the face points to IMAGE LEFT |
| `g2_03_back.png` | face g2: straight BACK of the head and shoulders |
| `g3_01_front.png`, `g3_00_three_quarter.png`, `g3_02_profile.png`, `g3_03_back.png` | face g3, the same four views, each made with the selected g2 view of the same name as an extra input |
| `g1e_01_front.png`, `g1e_00_three_quarter.png`, `g1e_02_profile.png`, `g1e_03_back.png` | face g1e, the same four views, each made with the selected g2 view of the same name as an extra input |

Generate g2_01 first; then g2_00, g2_02, g2_03 with the selected g2_01 as an extra input. Then the g3 and g1e views, each with the g2 view
of the same name. At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view, prompt,
inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a `selected_views_review.png` contact sheet
of the twelve selected views.

## Common prompt content
TASK CONTEXT, GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING Might and Magic IX character
(inputs 1-3, 5, 7). Not a new design. Output ONE bust only: the whole head with its hair, the neck, the neckline of the dress and the top of
the shoulders, centred with generous margins, never cropped. Near-orthographic camera at eye level, head level, a calm, warm, friendly
expression with the MOUTH CLOSED (a gentle closed-lip smile, no teeth). EYES OPEN and clearly readable: visible irises and whites, relaxed
upper lids, no squint, no staring. Natural soft child's brows, ONE brow line each. Even soft neutral studio lighting, no dramatic light, no
rim light, no strong shadows, NO dark shadow under the lower lip or on the chin (the image is baked into a texture). Sharp fine detail: skin,
brows, lashes, lips, hair strands, wool weave, embroidery. The neck and the skin under the jaw are visible, evenly lit and continuous with
the face down to the neckline. Clean edges between skin and hair: each keeps its own colour, no pale band between the hairline and the
forehead skin. A real child's face: round soft cheeks, small nose, small chin; not an adult, not a doll, not a cartoon, not big-eyed.

## Identity
- All three: a human-sized girl of about nine; long straight hair parted in the middle, falling over the ears and down the back as one long
  mass; a thin braid from each temple back along the side of the head (inputs 1, 5, 7); the dress neckline below the neck.
- g2: fair skin with light freckles and rosy cheeks, blue eyes, AUBURN / chestnut-red hair, ears hidden under the hair; neckline: a black
  bodice with gold embroidery over a rust-brown dress (as inputs 1-4).
- g3: fair skin with a few freckles, grey-blue eyes, warm BROWN hair with a short soft wavy FRINGE over the forehead (bangs to the brows),
  ears hidden under the hair; neckline: a round neck of a dark navy-blue dress with a narrow golden trim (as inputs 5-6).
- g1e: an ELF girl: fair skin, a softly pointed chin, green-grey eyes, LIGHT golden-brown hair, and small POINTED ELF EARS that poke out
  through the hair at the sides, pointing up and back (as input 7); neckline: a teal-green dress with a cream trim and front lacing
  (as inputs 7-8).

Per-image checks (re-run before selecting): the right face; the requested view (`*_02_profile` faces IMAGE LEFT); eyes open; mouth closed;
no ears visible on g2 and g3; pointed elf ears on g1e; whole head and hair inside the frame; true transparent background; square.

## Do NOT
make her older than about ten; add jewellery, a veil, ribbons, a hat or flowers; open the mouth or show teeth; show human ears on g2/g3;
stylise as a cartoon or anime; give her a fierce, cold or sad look; add text, a floor, a background or a shadow; crop.
