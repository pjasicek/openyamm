# Codex brief: HD reference views for the MM9 Nosferatu (mm9_nosferatu_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_nosferatu_claude/references_hd/`. Do not edit any other file, do not run
builds, do not call Meshy. Use your built-in image generation tool. There are no native sprites for MM9: the authority is the ORIGINAL Might and
Magic IX 3D model with its skin, shown in renders of that model.

This is a fantasy video-game creature, a goblin-faced undead noble in a long ceremonial robe, a restoration of an existing 2002 game monster for a game mod.

## Inputs (attached, in order)
1. `mm9_views_b.png`: renders of the ORIGINAL low-poly model with its skin (tier "Annelid"), five views left to right: front three-quarter from the
   figure's RIGHT, front, figure's LEFT side (faces IMAGE LEFT), back, figure's RIGHT side (faces IMAGE RIGHT). Grey is background. Design, layout,
   proportions and colour authority. The faceting, blur and low resolution are NOT the design. The pose of the input is NOT the pose wanted.
2. `mm9_chest_views_b.png`: closer renders of chest, sleeves and hands, same five views.
3. `mm9_head_views_b.png`: close renders of head and collar, same five views.
4. `mm9_hand_views_a.png`: the belt, centre panel and one hand, closer (another tier's colours: shape only).
5. `mm9_skin_x4_b.png`: the original 256x256 skin enlarged, SURFACE MATERIAL AND COLOUR ONLY.
6. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1536 PORTRAIT)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the figure's RIGHT, camera at chest height slightly above (as input 1 view 1) |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree profile of the figure's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the figure's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so all views are
the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective regeneration per view; then select the better and note any residual fault.
Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs) and, after run 2,
a `selected_views_review.png` contact sheet.

## Common prompt content (adapt per view)
TASK CONTEXT: faithful high-definition reconstruction of the EXISTING Might and Magic IX "Nosferatu" (tier Annelid) from the supplied renders of its original
3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional figure with semi-realistic game materials and sharp
fine detail (damask silk, braided gold cord, tooled leather, pale creased linen, leathery skin). ONE complete figure from the top of the ear tips to the hem, centred, both hands
inside the frame with margin, never cropped.

Identity (exactly the layout of inputs 1-4):
- A gaunt, tall, thin humanoid, about 1.75 m tall to the top of the skull, narrow chest, square padded shoulders. Thin arms inside wide sleeves. No bodybuilder.
- HEAD: completely BALD, an elongated high domed cranium, sallow tan leathery skin, heavy angry brow ridges, a raised vein ridge up the middle of the forehead, deep-set small amber eyes,
  a flat wrinkled nose, sunken cheeks. A snarling half-open mouth: lips drawn back, two rows of small jagged yellow teeth, red-orange gums, a strong narrow chin. No hair, no beard, no eyebrows hair.
- EARS: two very large pointed ears, like long leaves, standing out sideways and up from the skull, each as long as the head is tall, as input 3.
- COLLAR: a tall stiff standing collar of pale cream creased linen with a gold edge, rising behind and beside the neck to ear level, open in a V at the throat, as input 3.
  No hair, no hood, no cape.
- CHEST FRONT: a V-shaped pale cream linen bib on the upper chest, inside it a narrow panel of olive-gold embroidery running down to the belt. At the top of the bib a small brass pendant with a red faceted gem on a dark cord, as input 3.
- ROBE: one closed floor-length robe of deep blood-red silk damask with a darker tone-on-tone woven pattern (scrolls, diamonds, eyes, circles) from shoulders to hem, as input 5.
  Fitted through the chest and waist, then flaring smoothly from the belt into a wide bell that touches the floor all round, a little longer at the back as a low train. Soft long folds. The robe hides legs and feet completely: NO feet, NO shoes, NO legs visible.
- BRAIDED TRIM: thick braided gold cord follows the V of the bib from the shoulders down to the belt, and below the belt two parallel gold cords run down the front centre of the robe to the hem, with a dark almost black panel between them, as input 1.
  Also a band of gold braid across the top of each shoulder yoke, as input 3.
- SHOULDERS: square, slightly padded, ending in a small cream linen knot on the back of each shoulder, as input 2.
- SLEEVES: long wide bell sleeves of the same damask, closely following the upper arm and widening from the elbow into a big open square cuff, with two gold braid bands near the cuff edge and a cream linen lining at the wrist, as input 2.
- BELT: a narrow brown tooled leather belt at the waist with a large oval gold filigree clasp at the front, as input 4.
- HANDS: bare, thin, long bony hands, skin the same sallow tan as the face, FIVE separate very long thin tapering fingers (four fingers and a thumb) each ending in a long sharp black claw, the black claw about a third of the finger's length, clear air between the fingers, relaxed and slightly curled, as inputs 2 and 4.
- No weapons, no staff, no cape, no hood, no pouches, no extra limbs, no jewellery beyond the pendant.

Pose (identical in all views; NOT the pose of input 1): standing perfectly upright and symmetrical, facing the camera direction of the view, head level looking straight ahead; arms straight, held out to the sides and down at about 45 degrees from vertical, palms facing the thighs, slightly forward, elbows nearly straight, wrists straight, sleeves hanging free with clear air between each sleeve and the robe; robe hem a smooth round circle on the floor.

Camera: near-orthographic, even soft studio light, no drama in the light, no cast shadows on the figure, no rim light.

Do NOT: add weapons, a staff, a cloak, a hood or visible feet; change colours; crop any part; copy the blur or faceting; give him hair; merge the fingers; merge the sleeves into the robe.

Per-image checks (redo at most once): ear tips to hem in frame; both hands in frame; true alpha; five clawed fingers on each visible hand; both big ears; tall collar; bib with red gem; belt with oval clasp; two gold cords down the front; both sleeves clear of the robe; no feet.
