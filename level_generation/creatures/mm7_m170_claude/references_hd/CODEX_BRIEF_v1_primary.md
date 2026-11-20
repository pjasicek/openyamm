# Codex brief (run 1): HD primary three-quarter view for the MM7 Cleric of the Moon (m170)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m170_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. The other four views are a separate later run.

Use your built-in image generation. Record format: as in
`level_generation/creatures/mm6_cle_claude/references_hd/generation_runs.json` (id, prompt, inputs with sha256,
output path, selected flag, reason, superseded runs). Attached inputs, in order (paths relative to
`level_generation/creatures/`):

1. `mm7_m170/native/m170sa0.png` — ORIGINAL native FRONT frame (256 x 256, transparent background). Design,
   proportions and palette authority.
2. `mm7_m170/native/m170sa1.png` — ORIGINAL native FRONT THREE-QUARTER frame.
3. `mm7_m170/native/m170sa2.png` — ORIGINAL native PROFILE frame (shows the back frame and banners from the side).
4. `mm7_m170/native/m170sa4.png` — ORIGINAL native BACK frame (shows the back plate, the V frame and the banners).
5. `mm7_m170/aligned_2x/m170sa0.png` — restored 2x front view, SURFACE MATERIAL ONLY (cloth texture, gold, skin).
   It never sets the design, pose or proportions.

## Deliverable

`00_three_quarter.png`: 1024 x 1536 portrait, genuine transparent background, unresized native return. Keep raw
returns under `raw/`. Write `generation_runs.json`.

Accept the first image that passes the checks below. For a failed image do at most ONE targeted corrective
regeneration, then select the better of the two and note any residual fault in its reason. Do not chase minor
differences in fold detail. Stop after that.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII "Cleric of the Moon" from the supplied original sprites, as a 3D modelling reference. Not a new design.
Output: exactly ONE 1024 x 1536 portrait PNG, genuine transparent background. ONE complete figure, full body from the
tips of the back frame above the head down to the robe hem and the feet, centred, the figure about 82% of the canvas
height with about 120 px of transparent space above and below, generous side margins. Near-orthographic camera, no
floor, no shadow, no scenery, no text. Even soft neutral studio light (no dramatic or rim light) that still shows
form. Credible fully three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

Identity (from the native sprites):
- A tall, gaunt adult man with ashen GREY skin (cool blue-grey, like a pale corpse), a long narrow severe face with
  high cheekbones, sunken cheeks, thin lips and a straight nose, pale eyes; clean-shaven. Long straight BLACK hair
  falls from under the helmet down the back to the shoulder blades.
- HELMET: a polished GOLD domed cap-helmet (rounded, ribbed top) with a broad gold browband and short gold cheek
  plates framing the face, the face itself open.
- CRESCENT MOON: a large polished GOLD crescent rises behind the head and shoulders like a pair of horns: its lower
  middle sits behind the shoulders, its two points curve up and outward to about the height of the top of the
  helmet, beside the head; its surface engraved with fine ornament.
- COLLAR: a broad round gorget collar round the neck: alternating black and gold vertical bars (like a ribbed
  Egyptian collar), and below it on the chest a small gold Y-shaped chain holding a round gold pendant.
- BACK FRAME AND BANNERS: from a small square gold plate between the shoulder blades, two thin GOLD rods rise in a
  wide V behind the head, reaching well above the head (higher than the crescent tips), with a small hook at each
  tip. From each rod hangs a long DARK OLIVE-BROWN cloth banner with a ragged lower edge, hanging straight down behind
  the body to about hip height, and a row of small TURQUOISE glass tassels/beads hangs along each rod. Seen from the
  front the banners show to both sides of the body BEHIND the arms; they never cover the arms or hands.
- ROBE: a floor-length, loose GREEN robe (rich grass green, soft felted/velvety cloth) with wide sleeves to the
  wrists, a slightly bloused chest, falling in broad straight folds to the floor; a thin GOLD trim line runs down
  the front edge from the waist to the hem and a gold band edges the hem all round.
- BELT: a gold-ochre ROPE cord tied at the waist with a knot at the front, two cord ends hanging to mid-thigh.
- HANDS: bare, grey, long bony fingers with long dark nails (claw-like), no rings.
- The feet are hidden under the robe hem (only the hem touches the ground).

Pose (the pose for every later view as well): standing upright, relaxed, weight even, legs slightly apart under the
robe. Arms in an A-POSE: hanging down and away from the body at about 35 degrees from vertical, elbows very
slightly bent, with a clear gap of air between each arm and the torso and between each hand and the robe; the arms
are IN FRONT of the hanging banners. Both hands OPEN and relaxed, palms facing the thighs, the long fingers
slightly spread apart with a gentle natural curl, thumb clearly separate from the index finger. Head level, looking
forward.

Do NOT: draw a staff, weapon or any held object; add a beard, a hood, armour, a cape over the robe or extra
jewellery; change the colours (grey skin, black hair, gold helmet, crescent and frame, black-and-gold collar, green
robe with gold trim, gold-ochre cord, dark olive banners, turquoise tassels); let the banners cover the arms, hands
or the front of the robe; crop the frame tips, the banners or the hem; add a floor, shadow, glow, spell effect or
text.

INPUT ROLES (put these in the prompt):
- Inputs 1–4: ORIGINAL native front, front three-quarter, profile and back frames: anatomy, costume placement and
  back-frame/banner authority. Their transparent background is not part of the character.
- Input 5: restored 2x front view, SURFACE MATERIAL ONLY (cloth, gold, skin), never design/pose/proportions
  authority. Ignore edge artefacts.
- Reconstruct the native design in the requested neutral A-pose with open empty hands (the native arms are bent
  with the hands held in front of the hips; do not copy that).

Camera for this PRIMARY view: FRONT-RIGHT THREE-QUARTER, camera 40–45 degrees toward the cleric's anatomical RIGHT
from straight front, at chest height and slightly above, near-orthographic with only a subtle downward view. It shows
the FRONT and his RIGHT flank: his nose and the robe front point diagonally toward SCREEN-LEFT; his right arm is the
nearer arm (on the image left), his left arm is farther. Head aligned with the torso, no separate head turn.

## Checks (re-run before selecting)

- camera: front-right three-quarter, nose toward screen-left, right arm nearer;
- whole figure inside the frame (V-frame tips, crescent, banners, hem), true transparent alpha, 1024 x 1536;
- grey gaunt face, black long hair, gold domed helmet, gold crescent behind the shoulders, black-and-gold collar
  with the pendant;
- V frame of two gold rods with dark olive banners and turquoise tassels behind the body, banners not covering the
  arms;
- green floor-length robe with wide sleeves, gold front trim and hem band, gold-ochre rope belt with hanging ends;
- A-pose arms clear of the body, both hands open and empty with separated fingers; no staff, weapon or effect.
