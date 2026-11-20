# Codex brief: HD HEAD turnaround for MM9 The Green Man, skin GREENMAN (mm9_greenman_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_greenman_claude/references_head/`. Do
not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no
native sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders of that model.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views_a.png` — close renders of the ORIGINAL Might and Magic IX model's head (front,
   profile, three-quarter, profile, back): FACE, LEAF HOOD AND BRANCH AUTHORITY. Its low resolution, faceting and dark
   shading are NOT the design.
2. `references_hd/00_three_quarter.png` — the selected, approved HD body master of this figure: exact identity, face
   structure, leaves, branches and colour authority for the HD look. The heads you make must be THIS face.
3. `references_hd/01_front.png` — the approved HD front master (same figure, front).
4. `references_hd/mm9_skin_x4_a.png` — the original skin texture enlarged, SURFACE MATERIAL AND COLOUR ONLY.

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `01_front.png` | perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `00_three_quarter.png` | front three-quarter bust: he looks toward IMAGE RIGHT and toward the viewer, as in input 2; eye level |
| `02_profile.png` | pure 90-degree profile of the character's LEFT side: the face points to IMAGE LEFT |
| `03_back.png` | straight BACK of the head and shoulders |

Generate 01 first; then make 00, 02 and 03 with your selected 01 as an extra input so all four are the SAME head.
At most ONE corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view,
prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a
`selected_views_review.png` contact sheet of the four selected views.

## Common prompt content
TASK CONTEXT — GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING
Might and Magic IX character, The Green Man (inputs 1-3). Not a new design. Output ONE bust only: the whole head with
the whole leaf hood and ALL crown branches, the beard, and the top of the shoulders with their branch stubs, centred
with generous margins, never cropped (every branch tip inside the frame). Near-orthographic camera at eye level, head
level. Expression: CALM, WARM, KIND and wise, a faint gentle smile; mouth CLOSED with natural relaxed lips (no teeth,
no pout); eyes clearly OPEN and relaxed with warm amber-brown irises and pupils visible, natural lids with no red rims
and no dark bags. Even soft neutral studio lighting, no dramatic light, no rim light, no glow, no strong shadows (the
image is baked into a texture). Sharp fine detail: yellow-green skin pores, faint bark-like grain, brows, lashes, lips,
individual leaves with veins, moss strands in the beard, bark grain on the branches. ONE natural brow above each eye
and nothing else between brow and eye: no light outlined band, no second brow line. ONE nose with two small nostrils.
Clean edges between skin and leaves: no skin tone bleeding into the leaves, no pale band along the hood's edge.

## Identity
The Green Man (inputs 1-2): a strong, noble, ageless male face with smooth yellow-green skin (lighter on the face),
a straight strong nose, high cheekbones, deep-set eyes; a drooping moustache and a long full beard of fine green leaves
and moss strands down to the upper chest; a close HOOD of dense overlapping green ivy/oak leaves covering the top, sides
and back of the head like a cowl, leaving the face open, flowing into a leafy mantle over the shoulders; five or more
bark branches growing up and outward from the crown of the hood (brown bark, lighter cut wood at the broken tips); one
short broken branch stub on top of each shoulder.

Per-image checks (re-run before selecting): same face as input 2; the requested view (02 faces IMAGE LEFT; 00 looks
toward IMAGE RIGHT); whole head, hood and every branch inside the frame; mouth closed, eyes open with irises; one brow
line; one nose; true transparent background; square.

## Do NOT
- change the face, leaves, branches, colours or age; give him a fierce, angry, grim or cold look; open his mouth or
  show teeth; add flowers, fruit, jewellery, horns or glowing eyes; make him a tree trunk or an ent; stylise as a
  cartoon; add text, a floor, a background, a glow or a shadow; crop.
