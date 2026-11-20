# Codex brief: HD reference views for the MM6 Flying Demon (wdm)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_wdm_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation (as for `new_sorpigal_3d_stage1_20261006`, see its `pmn2/generation_runs.json`
for the prompt style and record format). Attached inputs:
1. `level_generation/creatures/mm6_wdm/references/standing.png` — ORIGINAL native five-view sheet (front, front
   three-quarter, profile, rear three-quarter, back). Magenta is background, not creature. Design/anatomy/palette
   authority.
2. `level_generation/creatures/mm6_wdm/aligned_2x/wdmflya0.png` — restored 2x front view, for surface material only.

## Deliverables (5 images, transparent background, 1024 x 1536 portrait, unresized returns)
- `00_three_quarter.png` — front-right three-quarter (primary; generate first)
- `01_front.png`, `02_back.png`, `03_left.png` (creature's left side), `04_right.png`
Generate 01–04 with 00 as an additional input so all five are the SAME creature, SAME pose, SAME proportions.
Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason) and a
`selected_views_review.png` contact sheet. Regenerate a view if it breaks the checks below; record superseded runs.

## Prompt content (adapt per view)
TASK CONTEXT — MM6 FANTASY-GAME ASSET RESTORATION: faithful high-definition reconstruction of the EXISTING Might and
Magic VI Flying Demon (Devil Captain) from the supplied original sprites, as a 3D modelling reference. Not a new design.
Use case: stylized-concept / faithful 3D modelling reference. ONE complete creature, full body head-to-talons plus the
complete wingspan, centred, generous margins, near-orthographic camera at chest height, transparent background, no
floor, no shadow, no scenery, no text. Even soft neutral studio light (no dramatic lighting) that still shows form.
Beautifully detailed, credible fully three-dimensional sculpt with semi-realistic game materials, sharp fine detail.

Identity (from the native sprites): tall gaunt humanoid demon, small head relative to body (about one-seventh of body
height), long thin limbs. Skin deep violet-purple with fine dense stippled fur/hide texture. Chest and belly
DARK CHARCOAL-GREY with horizontal ribbed bands (scute-like), from collarbone to groin. Head: broad grinning mouth with
rows of sharp ivory teeth, bright BLUE eyes, pointed ears swept outward, TWO curved ivory horns rising from the brow
curving up and slightly outward, a small ivory spike on the crown. THREE tall curved ivory spikes rising from EACH
shoulder, and a row of short ivory spikes along the outer edge of EACH forearm. Very long arms reaching mid-thigh,
large long-fingered hands, each finger ending in a long curved ivory claw, fingers clearly separated. Legs long and
thin, large feet with long curved ivory talons, toes clearly separated. Large dark charcoal-black BAT WINGS attached at
the upper back (shoulder blades, behind the shoulder spikes), finger struts clearly visible, membrane with subtle
vein/wrinkle texture, scalloped trailing edge ending in points at each strut, a hooked thumb claw at the wrist on the
leading edge.

Pose (identical in all five views): wings spread wide and raised in a high V like the native front sprite (do not
fold them), membranes fully open and not overlapping the body; arms hanging slightly away from the torso (about 20
degrees), elbows softly bent, hands open with fingers apart and claws visible, palms toward the thighs; legs straight
and slightly apart, gap between thighs, feet hanging naturally with talons visible. Head level, looking forward.

Do NOT: add armour, harness, belt, weapon, tail, extra horns, extra limbs, glowing effects, blood; do not make it
muscular/bodybuilder; do not change colours (purple body, charcoal chest, ivory horns/spikes/claws, blue eyes, black
wings); do not crop wings or talons.

Checks per image: whole wingspan and talons inside the frame; wings attached at the shoulder blades; three shoulder
spikes per side; forearm spike rows; horns + crown spike; blue eyes; ivory teeth; separated fingers and toes;
transparent background; same pose/proportions as the primary.
