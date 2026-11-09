# Codex brief: HD HEAD turnaround for the MM9 elf townswoman PeasantF6, face A (mm9_peasantf6_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantf6_claude/references_head/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is
the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

These four views will be PAINTED onto an existing 3D head (input 4 shows its shape in grey clay): a rounded bob of hair, one thick plait
at the nape, two long pointed elf ears coming out of the hair. Paint exactly that shape.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_a.png`: close renders of the ORIGINAL model's head with skin A, five views (front, her left side facing
   IMAGE LEFT, three-quarter, her right side facing IMAGE RIGHT, back): FACE, HAIR, BRAID AND EAR AUTHORITY. Low resolution, faceting and
   dark shading are NOT the design.
2. `references_hd/00_three_quarter.png`: the approved HD body master: identity, face structure, hair colour and costume of the HD look.
3. `references_hd/mm9_skin_x4_a.png`: skin A enlarged, SURFACE MATERIAL AND COLOUR ONLY (face, hair, braid and ear texels at the top left
   and lower middle).
4. `references_hd/shape_head_clay.png`: grey clay renders of the 3D head (front, left side, three-quarter, right side, back): HEAD SHAPE,
   HAIR OUTLINE, BRAID AND EAR PLACEMENT AUTHORITY. Same framing as the deliverables below.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `a_01_front.png` | perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `a_00_three_quarter.png` | front three-quarter bust from her RIGHT side (she looks toward IMAGE RIGHT, as input 2), eye level |
| `a_02_profile.png` | pure 90-degree profile of her LEFT side: the face points to IMAGE LEFT |
| `a_03_back.png` | straight BACK of the head and shoulders: the bob and the plait hanging down the upper back |

Generate a_01 first; then a_00, a_02, a_03 with the selected a_01 as an extra input. At most ONE corrective regeneration per view; keep raw
returns in `raw/`. Write `generation_runs.json` (id, view, prompt, inputs with sha256, output path, selected flag, reason, superseded runs,
size, alpha extrema) and a `selected_views_review.png` contact sheet of the four selected views. The tool takes at most five reference
images per call: pack inputs side by side into one sheet in `raw/` if needed.

## Common prompt content
TASK CONTEXT, GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING Might and Magic IX character
(inputs 1-2). Not a new design. Output ONE bust only: the whole head with its hair, braid and ears, the bare neck, the round cream chemise
collar and the top of the shoulders, centred with generous margins, never cropped. Near-orthographic camera at eye level, head level.
A calm, warm, friendly expression with the MOUTH CLOSED: a gentle closed-lip smile, no teeth, ONE pair of natural soft pink lips (no
lipstick red, no second lip line). EYES OPEN and relaxed: visible irises, the upper lid resting just over the top of the iris, no staring,
no squint, no red rims, no pale crescent under the lower lid. One soft brow per eye. A small natural nose with soft nostrils (no dark
triangle). Even soft neutral studio lighting, no dramatic light, no rim light, no strong shadows, NO dark shadow under the nose, the lower
lip or the chin (the image is baked into a texture). Sharp fine detail: skin, brows, lashes, lips, hair strands, the plait's strands. The
neck and the skin under the jaw are visible, evenly lit and continuous with the face down to the collar. Clean edges between skin and
hair: no pale band at the hairline, hair strands only on the hair.

## Identity
A YOUNG ELF woman, about 25 years old (inputs 1-2): fair warm-peach skin, smooth, a few faint freckles over the nose, blue eyes, fine
light-brown brows, a small straight nose, soft pink lips, a slightly pointed chin.
- HAIR: HONEY-BLOND / golden-blond, parted in the middle at the forehead and swept back over the head and over the ears' roots into a
  smooth ROUNDED BOB covering the top, sides and back of the head down to the jaw line (exactly the outline of input 4), with fine
  combed strands; at the nape it is gathered into ONE thick three-strand PLAIT that hangs down the upper back (input 1 back view, input 4).
- EARS: two long POINTED ELF EARS, plain skin coloured with a soft pink inner bowl, coming out of the hair above and behind the cheeks and
  pointing out, up and back (input 4). No earrings, no hair painted on the ears, nothing on the ears.
- Neck bare; a round cream linen chemise collar with a short slit at the base of the neck.

Per-image checks (re-run before selecting): the face of inputs 1-2; the requested view (a_02 face IMAGE LEFT); eyes open and relaxed; mouth
closed; ears pointed and skin coloured; the hair outline and plait of input 4; whole head inside the frame; true transparent background;
square.

## Do NOT
add jewellery, a necklace, a hat, a scarf, a coif, a veil, flowers or a hair band; let loose hair fall over the shoulders; open the mouth or
show teeth; paint red lipstick; make her old, stern, fierce or cold; stylise as a cartoon; add text, a floor, a background or a shadow; crop.
