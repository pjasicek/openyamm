# Codex brief: HD reference views for the MM7 Treant (mm7_m479_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m479_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation (prompt style and record format as in
`level_generation/creatures/mm7_m278_claude/references_hd/generation_runs.json`). Attached inputs, in order:
1. `references_hd/native_views.png` — ORIGINAL native MM7 Treant sprites, enlarged 3x with nearest neighbour. The
   native game has ONLY ONE VIEW (this front view is shown from every direction). Left to right: disguised resting
   tree (no face visible), eyes opened, mouth wide open, mouth half open. Magenta is background, never part of the
   creature. Design, proportions and colour authority.
2. `references_hd/native_actions.png` — native attack frames (branches lashing, trunk bending), a breakup frame and
   the stump corpse. Anatomy evidence only (how the limbs attach to the trunk); do not copy these action poses.
3. `level_generation/creatures/mm7_m479/trimmed_2x/m479ae0.png` — restored 2x frame, SURFACE MATERIAL ONLY (bark
   texture, eye and teeth look); never the design and never the pose.

## Deliverables (5 images, transparent background, 1024 x 1536 PORTRAIT, unresized returns)
- `00_three_quarter.png` — front three-quarter: the face turned about 35 degrees toward image LEFT, camera at about
  mid-trunk height, slightly above (primary; generate first; this image alone becomes the 3D mesh, so the trunk, the
  whole crown of limbs and the root base must be readable in depth)
- `01_front.png` (face toward the camera), `02_back.png` (back of the trunk, no face), `03_left.png` (the treant's
  LEFT side: its face looks toward image LEFT), `04_right.png` (its RIGHT side: its face looks toward image RIGHT)
Freeze 00 once it passes the checks; then generate 01–04 in a separate step with 00 as the FIRST input so all five
show the same tree, pose and proportions. At most one corrective regeneration per view. Also write
`generation_runs.json` (id, prompt, inputs with sha256, output, selected flag, reason, superseded runs) and a
`selected_views_review.png` contact sheet.

## Prompt content (adapt per view)
TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Treant (a monstrous living tree) from the supplied original sprites, as a 3D modelling reference. Not a new
design. Beautifully detailed, credible fully three-dimensional tree creature with semi-realistic game materials and
sharp fine detail (deep furrowed bark, root tendrils), even soft neutral studio light, near-orthographic camera, the
whole tree inside the frame with margins (every limb tip and the root base included), transparent background, no
floor, no grass, no cast shadow, no scenery, no text.

Identity (from the native sprites): a LEAFLESS dead-looking tree. The trunk is a broad, flared cone: very wide at the
ground (a skirt of gnarled roots and root tendrils spreading on all sides), narrowing upward into a straight, POINTED
SPIRE that rises well above the crown like a sharp stake. At about 55–70 % of the height a crown of about SEVEN bare,
winding, twisted limbs leaves the trunk on all sides (left, right, front-left, back, ...), each limb curving outward
and then UP, forking two or three times into tapering, slightly hooked tips — like antlers. Limbs are solid wood, clearly
thicker than twigs (a limb is about as thick as a wrist on this scale), with clear air gaps between neighbouring limbs.
No leaves, no moss clumps. Colour: dark umber / chocolate-brown bark with grey-brown highlights and dark furrows, a
slight cool grey sheen on the upper limbs; roots the same brown with a few olive-green moss specks at the base.
FACE (on the front only, carved into the bark): two small glowing GREEN almond eyes with dark slit pupils set in dark
knot-like sockets at about 55 % of the height, close together; heavy furrowed bark brows above them; a long broad
nose-ridge of bark running down between them; low on the trunk (about 20–30 % of the height) a WIDE MOUTH, open about
halfway, lips of thick bark, with two rows of pale ivory, uneven, peg-like teeth (upper and lower), dark inside.

Pose (identical in all five views, a neutral rigging pose based on the native resting sprite): standing straight and
upright, symmetric crown, limbs spread out and up with gaps between them; mouth half open as described; eyes open.

Do NOT: add leaves, fruit, blossoms, arms with hands, legs, armour, a second face, extra eyes; do not make the limbs
hair-thin or a tangled twig mass; do not change colours (dark brown bark, green eyes, ivory teeth); do not crop limb
tips or roots; do not tilt or bend the trunk; no face on the back view.

Checks per image (re-run before selecting): whole tree with every limb tip and the root skirt inside the frame;
pointed spire above the crown; about seven separated bare limbs forking into antler-like tips; flared trunk with root
skirt; green eyes and half-open toothed mouth on the front only (side views show the face in profile toward the stated
side; back view shows plain bark); dark brown colours; transparent background; 1024 x 1536; same pose and proportions
as the primary.
