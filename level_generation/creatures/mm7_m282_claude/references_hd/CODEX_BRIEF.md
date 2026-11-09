# Codex brief: HD reference views for the MM7 Medusa (mm7_m282_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m282_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation (record format as in
`level_generation/creatures/mm7_m278_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `references_hd/native_views.png` — ORIGINAL native MM7 sprite standing views, enlarged 3x with nearest neighbour,
   left to right: front, front three-quarter, profile (she faces image RIGHT, her right side toward the viewer), rear
   three-quarter, back. Magenta is background. Design, anatomy and colour authority.
2. `references_hd/native_palettes.png` — front and three-quarter views in the three native palettes (rows: dark
   breastplate, SILVER breastplate, gold breastplate). Use the MIDDLE row colouring (silver breastplate).
3. `references_hd/native_actions.png` — native walk (side) and attack frames: the tail lying on the floor in motion,
   the bow. Anatomy evidence only; do not copy the action poses.
4. `level_generation/creatures/mm7_m282/trimmed_2x/m282sa1.png` — restored 2x three-quarter frame, SURFACE MATERIAL
   ONLY (never the design, the pose or the colours).

## Deliverables (transparent background, 1536 x 1024 LANDSCAPE, unresized returns)

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter like the SECOND image of input 1: she faces toward image RIGHT-front (face and front of the body toward the viewer and to the right, her right flank visible), her tail runs back toward image LEFT and away; camera at chest height, slightly above. PRIMARY: generate first. This image alone becomes the 3D mesh, so the arms, both hands, the column and the whole tail must be readable. |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | her LEFT side: she faces image LEFT |
| `04_right.png` | her RIGHT side: she faces image RIGHT (like native profile) |
| `05_bow.png` | the bow alone, unstrung-side view flat to the camera (limbs vertical, string on the right), plus ONE arrow lying horizontally below it; orthographic, same materials as the native bow and arrows |

Run 1: generate ONLY `00_three_quarter.png` and stop. Run 2 (separate request): `01`–`04` and `05_bow.png`, with the
selected 00 as the FIRST input so all views show the same medusa, pose and proportions. At most one corrective
regeneration per view. Write `generation_runs.json` (id, prompt, inputs with sha256, output, selected flag, reason,
superseded runs) and, after run 2, a `selected_views_review.png` contact sheet of the six selected files.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Medusa from the supplied original sprites, as a 3D modelling reference. Not a new design. Beautifully
detailed, credible fully three-dimensional character with semi-realistic game materials and sharp fine detail
(smooth pale skin, small snake scales, glossy belly scutes, fine chain/scale mail, polished gold trim, leather),
even soft neutral studio light (no dramatic light, no rim light), near-orthographic camera, the whole figure inside the
frame with generous margins (hair snakes, fingertips and the tail tip included), transparent background, no floor, no
cast shadow, no scenery, no text.

Identity (from the native sprites): a female MEDUSA — a human woman's upper body on a giant SNAKE body instead of legs.
- Skin: smooth, pale BLUE-GREY / lavender-grey, the same on face, torso and arms.
- Face: calm, fine-featured, almost mask-like female face, small nose and mouth, glowing pale WHITE-BLUE eyes without
  pupils. No human hair at all.
- Hair: about 14 thick SNAKES grow from her scalp instead of hair, coloured olive-grey with BRONZE / GOLD bands and
  undersides, each with a small dark snake head. Most hang down behind and beside the head to the shoulders; two
  frame the face on each side; a few curl outward at the sides. They stay close to the head and shoulders and never
  touch the arms.
- Armour: a fitted silver-steel SCALE-MAIL top covering the bust and chest down to just under the bust (two cups of
  small overlapping steel scales), edged with polished GOLD trim along its lower edge and shoulder straps; a narrow
  gold COLLAR band at the base of the neck; gold ARM RINGS on both upper arms and both wrists. The belly and waist are
  bare skin.
- Snake body: from the hips down she is a thick serpent. The hip/waist skin blends into small green snake scales. The
  FRONT of the snake body carries broad pale LAVENDER-WHITE transverse BELLY SCUTES (horizontal bands, about 10 on
  the upright part) from the hips down to the ground; the back and sides are dark OLIVE-GREEN scales with a
  darker diamond/net pattern and a few dark oval markings.
- Tail: the snake body descends in a gentle S-curve (as in the native profile) to the floor, then runs as a long tail
  lying on the floor STRAIGHT BACK behind her (about 1.3 times her total height long), tapering, with three GOLD
  BANDS near the end and a beige-grey segmented RATTLE (about 6 segments) as the tip.
- Quiver: a long brown LEATHER QUIVER on her back, diagonal from her left hip up to her right shoulder, with the gold
  and yellow arrow FLETCHINGS sticking up above her right shoulder (about 6 arrows). No other straps or belts.
- Bow (only in `05_bow.png`, never in the character views): a dark, almost black RECURVE bow with gold fittings at the
  grip and limbs and strongly curled hook-shaped tips, a thin pale string; the arrow has a dark shaft, a small
  metal head and gold/yellow fletching.

Pose (identical in all five character views, a neutral rigging pose): the torso upright and facing forward, head
level looking forward; arms relaxed in an A-POSE about 35 degrees out from the body, elbows very slightly bent, hands
OPEN with five separated fingers and a clear gap between each hand and the body; NO bow and nothing in the hands. The
rattle lies on the floor at the end of the straight tail. The lowest part of the snake body and the tail rest on one
flat floor plane (do not draw the floor).

Do NOT: add human legs, a second tail, wings, a cloak, a skirt, a weapon in the hands, a shield, a crown or extra
limbs; do not give her human hair; do not change the colours (pale blue-grey skin, silver scale mail with gold trim,
olive-green snake body with lavender-white belly scutes, olive/bronze hair snakes); do not crop the tail, the rattle or
the hair snakes; do not coil the tail.

Left and right: her LEFT hand is the one on image RIGHT in the front view. The quiver's arrow fletchings are above her
RIGHT shoulder (image LEFT in the front view, image RIGHT in the back view).

## Checks per image (re-run before selecting)

Whole figure inside the frame with margins; tail straight behind on the floor with the rattle; upright S-curved
column with belly scutes on the front; human upper body with pale blue-grey skin; ~14 hair snakes and no human hair;
silver scale-mail top with gold trim, collar and arm rings; quiver diagonal on the back with fletchings over the RIGHT
shoulder; A-pose with open five-fingered hands clear of the body; empty hands; transparent background; same pose and
proportions as the primary; side views facing the stated direction.
