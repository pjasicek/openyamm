# Codex brief (run 1): HD three-quarter primary for the MM7 Lich (m270)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m270_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`. The four orthographic views are a later, separate run.

Use your built-in image generation. Record format: `level_generation/creatures/mm6_ske_claude/references_hd/
generation_runs.json` (id, family `m270`, role `primary`, prompt, inputs with sha256, output path, selected flag,
reason, superseded runs). Attached inputs, in order (paths relative to `level_generation/creatures/`):

1. `mm7_m270/native/m270sa0.png` — ORIGINAL native front frame (transparent background). Design, proportions and
   palette authority.
2. `mm7_m270/native/m270sa1.png` — ORIGINAL native front three-quarter frame.
3. `mm7_m270/native/m270sa2.png` — ORIGINAL native right profile (coif, crown, plate profile, skirt).
4. `mm7_m270/native/m270sa3.png` — ORIGINAL native rear three-quarter.
5. `mm7_m270/native/m270sa4.png` — ORIGINAL native back.
6. `mm7_m270/aligned_2x/m270sa0.png` — restored 2x front view, for SURFACE MATERIAL ONLY (chain links, plate, gold,
   bone finish). It never sets the design, pose or proportions.

The sprites show a tall staff in the left hand. The 3D model gets the staff as a separate prop later, so this
reference must show the lich EMPTY-HANDED.

## Deliverable

| File | View |
|---|---|
| `00_three_quarter.png` | front-right three-quarter (camera 40–45° toward the figure's own RIGHT side), camera at chest height, slightly above; 1024 x 1536 portrait, true transparent background, unresized return |

Keep raw returns under `raw/` (`m270_three_quarter_v1.png`, ...). Write `generation_runs.json`. If the first return
fails a check below, do ONE targeted corrective regeneration, then select the better of the two and note any
residual fault in its reason. Do not chase minor differences.

## Prompt content

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VII Lich monster from the supplied original sprites, as a 3D modelling reference. Not a new design. Output:
exactly ONE 1024 x 1536 portrait PNG with a genuine transparent background. ONE complete figure, from the crown points
to the bottom of the skirt and the shoe tips, centred, generous margins, near-orthographic camera, no floor, no shadow,
no scenery, no text. Even soft neutral studio light (no dramatic lighting, no rim light) that still shows form.
Credible, fully three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

Identity (from the native sprites): an undead skeletal king-sorcerer in armour and chainmail.
- HEAD: a small bare ivory-grey human SKULL with empty dark eye sockets, dark nasal opening and exposed teeth, lower jaw
  closed; a gold pointed open CROWN of tall points sits on top. Around the skull a dark blue-violet grey CHAINMAIL COIF
  (hood of fine chain links) covers the top and back of the head, the ears and the neck, leaving the skull face open
  and falling to the shoulders.
- TORSO: a polished SILVER articulated BREASTPLATE (sculpted chest, segmented abdomen plates) with gold-orange borders,
  large angular silver SHOULDER PLATES (pauldrons) with upswept gold-rimmed points; a matching back plate. A broad
  GOLD waist belt with an ornate gold buckle.
- ARMS: the upper arms and forearms are covered in the same dark blue-violet grey chainmail sleeves, silver plate
  cuffs with gold rims at the wrists; the HANDS are bare bone: bony skeletal hands with five long thin finger bones.
- SKIRT: a long narrow floor-length CHAINMAIL skirt in the same dark blue-violet grey chain from the belt to the ground,
  slightly flaring, its hem just above dark steel pointed shoe tips.
- COLOUR AND MATERIAL: bright polished silver plate, warm gold-orange trim and crown, dark blue-violet grey chain links
  (distinct individual rings), ivory-grey bone.

Pose: a neutral pose for rigging. Standing upright, the skirt falling straight, the shoe tips slightly apart. Arms
held down and out to the sides at about 35 degrees from vertical, elbows very slightly bent, with a clear gap of air
between each arm and the body. Both bony hands open and relaxed, the finger bones slightly apart, palms facing the
body. Head level, looking forward.

Do NOT: draw the staff or any weapon, an orb, a cape, a cloak, wings, extra ornaments or jewellery; add skin or flesh
to the skull or hands; cover the face; add glowing eyes, aura, smoke or magic effects; change the colours (the chain
stays dark blue-violet grey, the plate silver, the trim gold); make it cartoonish or bulky; crop the crown or the
feet; add a floor, shadow or text.

INPUT ROLES: Inputs 1–5 are the native standing views (front, front three-quarter, right profile, rear
three-quarter, back): design, proportions and palette authority; transparent pixels are background. Input 6 is the
restored front: SURFACE MATERIAL ONLY, never design, pose or proportions.
CAMERA for this primary: FRONT-RIGHT THREE-QUARTER, camera 40–45 degrees toward the figure's anatomical RIGHT from
straight front, chest height slightly above, near-orthographic. Show FRONT and RIGHT flank: the skull points
diagonally toward SCREEN-LEFT. FRAMING / ALPHA: the whole figure occupies about 80 % of the height with generous
transparent margins, genuine RGBA alpha outside the silhouette and in the air gaps between the arms and the body. No
painted checkerboard. Return exactly 1024 x 1536 unresized.

## Checks before selecting

- front-right three-quarter camera at chest height, near-orthographic, whole figure inside the frame with margins,
  1024 x 1536, true transparent background (not a checkerboard drawn into the pixels);
- empty hands, no staff;
- bare skull face under a gold pointed crown, chain coif around the head and neck;
- silver breastplate and angular pauldrons with gold trim, gold belt, chain sleeves, bony five-digit hands;
- floor-length chain skirt; arms out with clear gaps.
