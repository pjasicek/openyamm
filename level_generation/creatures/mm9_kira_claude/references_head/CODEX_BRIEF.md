# Codex brief: HD HEAD turnaround for MM9's Kira the Cold (mm9_kira_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_kira_claude/references_head/`. Do not edit any other
file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is
the ORIGINAL MM9 3D model with its skin, shown in renders of that model, and the approved HD body masters made from it.

## Inputs (attached, in order)
1. `references_hd/mm9_head_views.png`: close renders of the ORIGINAL model's head, five views (three-quarter from her right, front, her
   left side facing IMAGE LEFT, back, her right side facing IMAGE RIGHT): FACE AND HAIR AUTHORITY. Low resolution, faceting and dark
   shading are NOT the design.
2. `references_hd/00_three_quarter_clean.png`: the approved HD body master: identity, face structure, hair, braid and colours of the HD look.
3. `references_hd/01_front_clean.png`: the approved HD front master.
4. `references_hd/03_left_clean.png`: the approved HD left profile master.
5. `references_hd/mm9_skin_x4.png`: the original skin enlarged, SURFACE MATERIAL AND COLOUR ONLY (face and hair texels at the top left).

## Deliverables (true transparent RGBA background, 1254x1254 or the closest supported square size, unresized returns)
| File | View |
|---|---|
| `01_front.png` | perfectly straight FRONT bust, face and shoulders square to the camera (generate FIRST) |
| `00_three_quarter.png` | front three-quarter bust from her RIGHT side (she looks toward IMAGE RIGHT, as input 2), eye level |
| `02_left.png` | pure 90-degree profile of her LEFT side: the face points to IMAGE LEFT |
| `03_back.png` | straight BACK of the head and shoulders |
| `04_right.png` | pure 90-degree profile of her RIGHT side: the face points to IMAGE RIGHT (the braid side) |
| `05_face.png` | CLOSE straight front of the FACE only, from the hairline to the chin, ears at the frame edges (texture source for the face) |

Generate 01 first; then the others with the selected 01 as an extra input. At most ONE corrective regeneration per view; keep raw returns in
`raw/`. Write `generation_runs.json` (id, view, prompt, inputs with sha256, output path, selected flag, reason, superseded runs, size, alpha
extrema) and a `selected_views_review.png` contact sheet of the six selected views.

## Common prompt content
TASK CONTEXT, GAME ASSET: faithful high-definition 3D modelling and TEXTURING head reference of an EXISTING Might and Magic IX character,
Kira the Cold, the woman Jarl of Thronheim (inputs 1-4). Not a new design. Output ONE bust only: the whole head with all the hair and the
braid, the neck, and the top of the shoulders with the mail collar and the steel-and-gold shoulder plates, centred with generous margins,
never cropped. Near-orthographic camera at eye level, head level, calm composed expression, MOUTH CLOSED, lips relaxed. Even soft neutral
studio lighting, no dramatic light, no rim light, no strong shadows (the image is baked into a texture). Sharp fine detail: skin pores,
brows, lashes, lips, hair strands, mail rings. The neck and the skin under the jaw are visible and continuous with the face. Clean edges
between skin and hair: each keeps its own colour, no skin tone in the hair, no pale band where the fringe meets the forehead.

## Identity
- A handsome, stern woman about 35, light natural skin, an oval face with defined cheekbones, a straight nose, dark straight brows,
  clear ICE-BLUE eyes WIDE OPEN with the irises fully visible (never sleepy or half closed), a calm firm mouth with closed natural lips,
  a complete chin, a smooth slender neck, small silver stud earrings.
- HAIR: very dark brown, long and straight. A side-swept fringe across the upper forehead, parted near the centre, falling to the brow line
  at the sides, its lower edge lying directly on the skin. The sides fall behind the ears; the back hangs as one long smooth mass down to
  the shoulder blades. ONE thin three-strand braid starts behind her RIGHT ear and hangs in FRONT of her RIGHT shoulder.
- Collar: a mail collar round the neck with a round gold medallion set with a blue gem at the base of the throat, steel-and-gold layered
  shoulder plates at the bust's lower edge.

Per-image checks (re-run before selecting): the requested view (02 faces IMAGE LEFT, 04 faces IMAGE RIGHT); eyes open and blue; mouth
closed; the braid on her right side; the fringe edge clean on the skin; whole head and hair inside the frame; true transparent background; square.

## Do NOT
change the hair colour or length; add a helmet, a crown, a hood or a veil; add make-up; open the mouth or show teeth; close or narrow the
eyes; stylise as a cartoon; add text, a floor, a background or a shadow; crop.
