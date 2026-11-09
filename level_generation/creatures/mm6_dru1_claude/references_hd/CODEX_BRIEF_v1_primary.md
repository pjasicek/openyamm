# Codex brief (run 1): HD three-quarter primary for the MM6 Druidess (dru1)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_dru1_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

This run produces ONLY the primary `00_three_quarter.png`; the four orthographic views are a later run.

Use your built-in image generation, with the prompt style and record format of
`level_generation/creatures/mm6_bar1_claude/references_hd/generation_runs.json`. Attached inputs, in order (paths
relative to `level_generation/creatures/`):

1. `mm6_dru1/references/standing.png` — ORIGINAL native five-view standing sheet (top row: front, front
   three-quarter, profile; bottom row: rear three-quarter, back). Magenta is background, not character. Design,
   proportion and colour authority (this sheet is the tier A green palette).
2. `mm6_dru1/native/dru1sta0.png` — ORIGINAL native front frame (transparent background).
3. `mm6_dru1/native/dru1sta1.png` — ORIGINAL native front three-quarter frame.
4. `mm6_dru1/native/dru1sta2.png` — ORIGINAL native profile frame (how far the cloak wraps round the side).
5. `mm6_dru1/native/dru1wka0.png` — ORIGINAL native walk frame, front: shows BOTH bare arms in front of the open
   cloak with the gold armbands and brown bracers.
6. `mm6_dru1/aligned_2x/dru1sta0.png` — restored 2x front view, for SURFACE MATERIAL ONLY (studded leather, gold
   belt medallion, cloth, face). It never sets the design, pose, proportions or colours.

## Deliverable

| File | View |
|---|---|
| `00_three_quarter.png` | front-right three-quarter (camera 40–45 degrees toward HER OWN RIGHT side), camera at chest height, slightly above; 1024 x 1536 portrait, true transparent background, unresized return |

Keep raw returns under `raw/` (`dru1_three_quarter_v1.png`, ...). Write `generation_runs.json` (id, family `dru1`,
role `primary`, prompt, inputs with sha256, output path, selected flag, reason, superseded runs). If the first return
fails a check, do ONE targeted corrective regeneration, select the better one and note any residual fault. Do not
chase minor differences. Stop after that.

## Prompt content

TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI Druidess (a female druid spellcaster) from the supplied original sprites, as a 3D modelling reference. Not
a new design. Output: exactly ONE 1024 x 1536 portrait PNG with a genuine transparent background. ONE complete
figure, from the hood top to the boot soles, centred, generous margins, near-orthographic camera, no floor, no
shadow, no scenery, no text. Even soft neutral studio light (no dramatic lighting, no rim light) that still shows
form. Credible, fully three-dimensional sculpt, semi-realistic game materials, sharp fine detail.

Identity (from the native sprites, tier A colours): a slim, athletic adult woman of normal height (head about
one-seventh of body height), pale natural skin, a stern, serious face with dark eyebrows, straight nose and full
lips, long thick wavy DARK BROWN hair parted in the middle that falls inside the hood over the front of both
shoulders to the upper chest.
- HOOD AND CLOAK: a deep FOREST-GREEN cloth hood, up over the head, the face and front hair fully visible in its
  opening. It joins a long full-length cloak of the same green cloth (soft velvet-like sheen, deep vertical folds)
  that hangs from the shoulders to just above the ankles. The cloak is OPEN AT THE FRONT and hangs BEHIND THE ARMS:
  its front edges fall from the tops of the shoulders straight down behind the arms and outside the hips, and it is
  closed all round the back, wide at the bottom. No clasp, no trim, no embroidery, no lining of another colour.
- BODYSUIT: a sleeveless one-piece DARK BROWN leather bodysuit covered in rows of small overlapping leather scales
  with tiny GOLD studs (studded scale leather), a deep V neckline and high-cut legs ending in a pointed panel at the
  front; the arms, shoulders and legs are bare skin.
- BELT: a wide reddish-brown leather belt at the waist with gold edging and a large round ornate GOLD MEDALLION at
  the centre front with a spiral motif, and a smaller round gold disc at each side of it.
- JEWELLERY: a thin gold neck chain / choker; a broad engraved GOLD ARMBAND around each upper arm.
- BRACERS: reddish-brown leather bracers on both forearms, from the wrist to about two-thirds of the way to the
  elbow, with a thin gold rim at the wrist. Hands bare, pale skin.
- BOOTS: reddish-brown leather boots to just below the knee with a turned-down cuff at the top edged with small gold
  studs, plain soles.

Pose: a neutral A-pose for rigging. Standing upright, weight even, legs straight and slightly apart with a clear gap
of air between the legs and between the boots, feet flat with toes forward. Arms hang down and out to the sides at
about 30 degrees from vertical, IN FRONT OF THE OPEN CLOAK (the cloak falls behind the arms), elbows very slightly
bent, palms facing the thighs, with a clear gap of air between each arm and the body and between each hand and the
thigh. BOTH HANDS RELAXED AND OPEN, fingers slightly curled and slightly apart, thumbs relaxed, five fingers each.
Head level, looking forward, hood up.

Do NOT: add a staff, sickle, weapon, wand, spell effect or any held object; add a cloak clasp, brooch, shoulder
armour, sleeves, a skirt or trousers; close the cloak at the front or let it cover the arms or hands; change the
colours (forest-green hood and cloak, dark brown studded leather, reddish-brown belt, bracers and boots, gold
jewellery, dark brown hair, pale skin); make her cartoonish or exaggerate her figure; crop the hood, the cloak hem or
the boots; add a floor, shadow or text. Neutral, modest documentation-style turnaround presentation, calm stance.

If the image tool refuses, retry ONCE with the neckline described as "a V neckline filled with a thin dark brown
leather underlayer" and the legs as "high-cut legs over thin dark brown leather shorts", and note the deviation in
the run's reason.

## Checks before selecting

- front-right three-quarter (her own right side toward the camera: her RIGHT arm is nearer the camera, on IMAGE
  LEFT), chest-height near-orthographic camera, whole figure inside the frame with margins (hood top, cloak hem,
  both boots), 1024 x 1536, true transparent background (not a drawn checkerboard);
- face visible in the raised green hood, dark brown hair over the front of both shoulders;
- green full-length cloak, open at the front, BEHIND the arms, closed at the back;
- studded dark brown leather bodysuit with V neckline, wide belt with the round gold medallion, gold choker, gold
  armbands on both upper arms, reddish-brown bracers on both forearms, knee boots with gold-studded cuffs;
- empty open hands with five separate fingers each, no held object, no spell effect;
- A-pose with the stated gaps (arms clear of the body, legs apart).
