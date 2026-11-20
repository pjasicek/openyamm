# Codex brief: HD reference views for MM9 The Green Man (GREENMAN.abc, skin GREENMAN) (mm9_greenman_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_greenman_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool. There are no native
sprites for MM9: the authority is the ORIGINAL MM9 3D model with its skin, shown in renders made from that model.

## Inputs (attached, in order)
1. `references_hd/mm9_views_a.png` — renders of the ORIGINAL Might and Magic IX low-poly model with its original skin,
   five views left to right: front three-quarter, front, side, back, side. Flat grey is background. This is the design,
   costume, proportions and colour authority. Its faceting, blur, T-pose and low resolution are NOT the design.
   (The model's separate wooden staff is deliberately hidden: do NOT draw a staff.)
2. `references_hd/mm9_head_views_a.png` — close renders of the same model's head (front, profile, three-quarter,
   profile, back): the face, leaf hood and branch authority.
3. `references_hd/mm9_skin_x4_a.png` — the original 256x256 skin texture enlarged, SURFACE MATERIAL AND COLOUR ONLY
   (face, leaves, bark, green skin). Never the design or shape.
4. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables (true transparent background, unresized returns, 1024x1536 portrait)
| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, he faces image right and toward the viewer, camera at chest height slightly above |
| `01_front.png` | straight front; the character's RIGHT arm on IMAGE LEFT |
| `02_back.png` | straight back; the character's RIGHT arm on IMAGE RIGHT |
| `03_left.png` | pure 90-degree profile of the character's LEFT side: faces IMAGE LEFT |
| `04_right.png` | pure 90-degree profile of the character's RIGHT side: faces IMAGE RIGHT |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01–04 with the selected 00 as an
additional input so all views are the SAME figure, SAME pose, SAME proportions and colours. At most ONE corrective
regeneration per view; then select the better and note any residual fault. Keep raw returns in `raw/`.
Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded runs)
and, after run 2, a `selected_views_review.png` contact sheet of the five selected views.

## Common prompt content (adapt per view)
TASK CONTEXT — FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of an EXISTING Might and
Magic IX character, "The Green Man" (a benevolent forest spirit and druid master), from the supplied renders of its
original 3D model, as a 3D modelling and texturing reference. Not a new design. A credible, fully three-dimensional
figure with semi-realistic game materials and sharp fine detail (skin pores, individual leaves with veins, bark grain,
moss), as if a high-quality sculpt of the original model. ONE complete figure from the tips of the head branches to the
soles, centred, generous margins, never cropped.

Pose (identical in all views; it is the model's bind pose in input 1, keep it exactly): standing upright and straight
(NOT stooped), nearly a T-pose: both arms held straight out to the sides only about 20 degrees below horizontal, wide
clear air between the arms and the body; hands open, flat and relaxed, palms facing down, the five fingers straight and
slightly spread, the thumb separated and pointing forward; legs straight and spread wide apart in an inverted V (each
leg about 18 degrees out from vertical, the feet about one metre apart), feet flat with toes forward. Head level, looking
forward. The figure is about as wide (fingertip to fingertip) as it is tall: scale it so the arms, every head branch and
both feet fit inside the 1024-wide frame with small margins.

Camera and light: near-orthographic, even soft neutral studio light, no dramatic light, no strong cast shadows on the
body; genuine transparent background, no floor, no shadow, no text.

Per-image checks (re-run before selecting): same identity, materials and colours as inputs 1–3; tall lean-muscled
proportions as input 1; the near-T pose above (arms about 20 degrees below horizontal, legs wide); five branches on the head and one small broken branch stub on each shoulder;
the correct side faces the correct image side (03: faces IMAGE LEFT; 04: faces IMAGE RIGHT); five fingers per hand;
whole figure, including all head branches and both feet, inside the frame with margins; true transparent background;
1024x1536.

## Identity
The Green Man: a very tall (about 2.2 m to the crown), lean but strongly muscled male nature spirit, ageless, wise.
- Skin: smooth olive-to-yellow-green skin with a faint bark-like grain, lighter yellow-green on the face, chest and
  belly, darker olive green on the arms, back and legs; well-defined pectorals and abdominals like the model.
- Face and head (input 2): a strong, noble, human male face with yellow-green skin, a straight strong nose, high
  cheekbones, deep-set eyes OPEN with visible warm amber-brown irises, ONE natural brow above each eye, mouth CLOSED with
  relaxed natural lips and a faint gentle smile: a CALM, WARM, KIND and wise expression (never fierce, angry or cold).
  A drooping moustache and a long full beard to the upper chest, made of fine green leaves and moss strands.
  The face is framed by a close HOOD of dense overlapping green leaves (ivy- and oak-like, dark and bright greens) that
  covers the top, sides and back of the head like a cowl, leaving the face open; the hood flows into a short leafy
  mantle over the shoulders, upper chest and upper back.
- Branches: five bark branches grow up out of the crown of the leaf hood like antlers (brown bark with lighter wood at
  the broken, cut-off tips), spreading up and outward, about 25–35 cm long; one small broken branch stub (about 10 cm)
  sticks up from the top of each shoulder.
- Body: below the mantle the chest and belly are bare green skin with dark root-like vein lines spreading down the
  sternum; a band of leaves round the lower ribs; a dark brown bark-and-root belt at the waist; below it a short kilt of
  overlapping green leaves to mid-thigh, front and back.
- Arms: bare olive-green skin, long sinewy forearms; hands large with long, slender, slightly knobbly fingers and dark
  brown nails, five fingers per hand.
- Legs: olive-green bark-textured skin with patches of moss and small leaves on the shins and calves; bare large feet
  with five toes, partly overgrown with moss and leaves, flat soles.

## Do NOT
- add a staff, weapon, clothes, armour, cloak, jewellery, horns, glowing eyes, flowers or fruit; make him a tree trunk,
  an ent or a monster; give him a fierce, angry, grim or cold expression; open his mouth or show teeth; stoop or bend
  him; change colours (greens, yellow-green skin, brown bark); change proportions; crop; stylise as a cartoon.

## Run 1b (correction, 2026-11-04): pose only
The first run-1 return (kept in `run1_first/`) is good in identity, face and materials, but its arms hang about 35
degrees below horizontal and the crown shows four branches. Regenerate `00_three_quarter.png` ONCE, using the attached
images in this order: (1) `run1_first/00_three_quarter.png` = the identity, face, materials and colours to keep
exactly; (2) `references_hd/mm9_pose_front_a.png` = the POSE authority, a straight front render of the original model's
bind pose: arms almost horizontal (wrists only a little lower than the shoulders, about 20 degrees below horizontal),
legs spread wide; (3) `references_hd/mm9_head_views_a.png` for the branches. Same three-quarter camera as before. Raise
both arms to that near-T angle (the wrists only slightly
below shoulder level), keep the hands flat with palms down and fingers slightly spread, keep everything else. Five bark
branches on the crown. Keep the first return as `run1_first/` and record this run in `generation_runs.json`.

## Run 2 note
The selected `00_three_quarter.png` (input 4) is the run 1b return with the halo removed: its near-T arm angle, wide legs,
face, branches (five large crown branches and two small ones, one stub per shoulder) and colours are the authority for
01–04. Ignore the "Run 1b" section in run 2.
