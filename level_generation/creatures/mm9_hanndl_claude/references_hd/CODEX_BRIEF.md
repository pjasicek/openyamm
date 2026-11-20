# Codex brief: HD reference views for the MM9 Gate Keeper Hanndl (mm9_hanndl_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_hanndl_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

These views will be PAINTED onto an existing 3D body (built earlier for another MM9 character on the very same MM9
mesh). So the figure must have THAT body's pose, proportions and silhouette (input 4 / inputs 6-9), while the face,
hair colour, costume, colours and materials come from the MM9 renders (inputs 1-3).

## Inputs (attached, in order)
1. `references_hd/mm9_views.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter from the character's RIGHT (he faces image right and toward the
   viewer), front, character's LEFT side (faces IMAGE LEFT), back, character's RIGHT side (faces IMAGE RIGHT). Flat
   grey is background. This is the design, costume and colour authority. Its faceting, blur and low resolution are
   NOT the design.
2. `references_hd/mm9_head_views.png` — close renders of the same model's head (front, left profile, three-quarter,
   right profile, back): the face, hair and ear authority.
3. `references_hd/mm9_skin_x4.png` — the original 256x256 skin texture enlarged 4x, SURFACE MATERIAL AND COLOUR ONLY
   (face painting, white hair and beard, fur, chain mail, brown wool, studded belt, leather lattice, boots). Never the design or shape.
4. `mm9_annud_claude/references_hd/00_three_quarter.png` — POSE, BODY SHAPE AND SILHOUETTE AUTHORITY ONLY: the 3D body
   these views will be painted on (another person in other clothes). Copy its pose, arm angle, proportions, leg
   stance, tunic length and skirt, head size and the hair VOLUME (long hair falling to the shoulders, a full beard).
   ONE exception: the SLEEVES. Input 4 has wide bell-shaped flared cuffs; this character's sleeves are FITTED and
   end snugly at the wrist with no flare. Do NOT copy its face, hair colour, rust-red tunic, rope belt, cross-gartered
   leg wraps or low shoes.
5. (run 2 only) the selected `references_hd/00_three_quarter.png`.
6.-9. (run 2 only) `mm9_annud_claude/references_hd/01_front.png`, `03_left.png`, `02_back.png`, `04_right.png`: the
   same pose/silhouette authority per view (same rules as input 4).

## Deliverables (true transparent background, unresized returns, 1536x1024 landscape so the spread arms fit)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the character's RIGHT, camera at chest height slightly above (as input 4) |
| `01_front.png` | straight front; the character's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the character's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the character's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the character's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as
an additional input so all views are the SAME character, SAME pose, SAME proportions and colours. At most ONE
corrective regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`.
Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs)
and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and
Magic IX character from the supplied renders of its original 3D model, as a 3D texturing reference. Not a new
design. A credible, fully three-dimensional character with semi-realistic game materials and sharp fine detail
(skin, wrinkles, face, hair and beard strands, fur, chain-mail rings, wool weave, leather grain, metal studs). ONE complete figure from the top
of the head to the soles, centred, generous margins, never cropped.

Pose (identical in all views, exactly as input 4): standing upright; the arms held straight out to the sides and
slightly down as in input 4, clear air between the arms and the body; hands open and flat, palms facing DOWN, the
four fingers straight and close together with small gaps, the thumb separated; legs straight and slightly apart
with a clear gap between them, feet flat. Head level, looking forward.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, costume and colours as inputs 1–3; the pose and silhouette
of input 4 (arms out, open flat hands with five fingers, legs apart); the correct side faces the correct image side
(03: faces IMAGE LEFT; 04: faces IMAGE RIGHT); whole figure inside the frame with margins; true transparent
background; 1536x1024.

## Identity
HANNDL, the old Gate Keeper: an ELDERLY HUMAN man of sturdy build (the body of input 4), dignified, calm and wise, a
grave but kindly face.
- Face and head (input 2): ruddy weathered skin with deep wrinkles on the forehead and round the eyes; pale blue-grey
  eyes under thick bushy WHITE brows; a strong straight nose; a full WHITE BEARD, short and neat on the cheeks and
  coming to a rounded point below the chin, with a white moustache; the mouth closed and relaxed. Long straight
  WHITE / silver-grey hair swept back from a high receding forehead and falling behind the ears to the shoulders and
  upper back (the hair volume of input 4). Human ears, mostly covered by the hair.
- Costume (inputs 1 and 3): a long-sleeved DARK BROWN wool tunic reaching mid-thigh (as long as input 4's), its
  sleeves FITTED down the forearms to the wrists; on each forearm a CRISS-CROSS LATTICE of dark leather straps with
  small BRASS STUDS at the crossings, ending in a thin gold-trimmed cuff at the wrist; a short shaggy dark brown-grey
  FUR MANTLE lying over both shoulders and the upper back and upper chest like a fur collar; in the front opening of
  the chest a vertical panel of polished steel CHAIN MAIL edged with gold trim, with a round bronze filigree brooch
  at the upper left of the chest and a gold-trimmed collar round the neck; a broad dark-red-brown leather BELT at
  the waist set with a row of round silver studs in gold settings and a large ornate gold buckle at the front; the
  tunic skirt below the belt plain dark brown wool; dark brown wool breeches; mid-calf red-brown leather BOOTS with
  a band of grey-brown FUR round the top, a thin dark green piping stripe and a small brass button at the ankle.
  Bare hands with ruddy old skin.

## Do NOT
- add a weapon, staff, bag, hat, hood, cape below the shoulders, gloves or extra jewellery; give the sleeves a bell or
  flared cuff; make him young; change colours; change the pose; crop; make the expression angry, fierce or cold
  (the MM9 render grimaces; draw him calm).
