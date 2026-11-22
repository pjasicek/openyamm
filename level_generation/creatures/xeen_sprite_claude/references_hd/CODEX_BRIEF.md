# Codex brief: HD modelling references for the Killer Sprite (World of Xeen)

Scope: image generation only. Write ONLY into `level_generation/creatures/xeen_sprite_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

This is the **Killer Sprite** of Might and Magic IV: Clouds of Xeen (1992), rebuilt as a 3D creature for an
MM6-8-style first-person RPG. The original game drew her only from the FRONT, as small low-resolution sprites. Your
job is a faithful high-definition reconstruction of that character as a 3D modelling reference, not a new design.

The BODY and the WINGS are modelled separately: images 00-04 show the body WITHOUT wings (the wings would hide the back
and confuse the body model); image 05 shows the four wings alone.

## Inputs (attached in this order)

1. `native/sheet_killer_sprite.png`: two ORIGINAL hovering frames (front view), enlarged with hard pixels. This is the
   identity, proportion and colour authority. The flat grey background is NOT part of the character.
2. `native/sheet_killer_attack.png`: two ORIGINAL attack frames: she crackles with green lightning. The green
   lightning and the green outline glow are a spell effect: do NOT draw them. Use these frames only for the body.
3. (run 2 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Six images in `references_hd/`, the whole subject inside the frame with at least 60 px of margin on every side,
unresized returns, true transparent background, no floor, no ground shadow, no text:

| File | Canvas | View |
|---|---|---|
| `00_three_quarter.png` | 1024x1536 portrait | the body in A-pose, front three-quarter: the face toward image RIGHT and turned about 35 degrees toward the camera (we see the face and her LEFT side), camera at chest height, slightly above |
| `01_front.png` | 1024x1536 portrait | straight front, symmetric A-pose |
| `02_back.png` | 1024x1536 portrait | straight back |
| `03_left.png` | 1024x1536 portrait | her LEFT side: strict 90 degree profile, the face toward image LEFT |
| `04_right.png` | 1024x1536 portrait | her RIGHT side: strict 90 degree profile, the face toward image RIGHT |
| `05_wings.png` | 1536x1024 landscape | the FOUR wings ALONE, no body, seen straight from behind, spread flat in one plane as in the original frames |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): `01`-`05` with the selected `00` as input 3. At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT - GAME ASSET: a faithful high-definition 3D modelling reference of the Killer Sprite from the 1992 game
Might and Magic IV: Clouds of Xeen, reconstructed from its original low-resolution front sprite. Not a new design. Use
case: 3D character modelling reference sheet view. Near-orthographic camera, even soft neutral studio light (no
dramatic lighting, no rim light, no strong shadows: the light is baked into the texture), painterly-realistic game
materials, sharp fine detail.

Identity (from the original frames): a small, slender, graceful fey woman (a sprite, about 1.1 m tall, but with ADULT
proportions: a head about one seventh of her height, long slim legs, narrow waist). SKIN: smooth saturated cobalt /
royal BLUE everywhere (face, arms, legs, hands and feet), lighter sky-blue on the highlights, darker navy in the
creases. FACE: a pretty, sly elfin face with a small pointed chin, dark eyes, thin dark brows and a small mischievous
smile, lips a darker blue; small slightly pointed ears mostly hidden by the hair. HAIR: very long, wavy, PALE TEAL /
aquamarine (light sea-green) hair, parted in the middle, falling over both shoulders and down her back to the waist,
with a few thin wavy wisps; the hair stays CLEAR of the arms and does not cover the face or the front of the neck.
DRESS: a short MAGENTA / hot-pink dress: a fitted off-the-shoulder bodice with a sweetheart neckline (bare shoulders,
the neckline's narrow off-shoulder bands sit on the upper arms just below the shoulders), a narrow waist, and a very
short flared skirt ending at the upper thigh in a RAGGED hem of long pointed petal-like tatters; deeper purple-magenta
in the folds. No sleeves, no belt, no jewellery. ARMS and LEGS bare and blue. HANDS: five slender fingers each, open
and separated, short nails, no claws. FEET: bare blue feet with five toes, no shoes.

Pose for 00-04 (identical in all five): neutral A-pose standing, arms straight and about 35 degrees away from the
body, both hands open with the fingers spread and clearly separated, palms facing forward-down; legs straight with a
clear gap between them (feet about shoulder width apart), feet flat on one level. Head straight, looking ahead.
NO WINGS on the body in 00-04 (they are drawn separately in 05): the back and shoulder blades are bare blue skin
above the back of the dress.

Wings (05 only): four translucent insect-fairy wings (two upper, two lower) as on the original sprite, seen from
behind, spread flat and symmetric, arranged around one central root point where they would join her back (no body
drawn, the root point empty). UPPER pair: large, broad, rounded butterfly-like wings, longer than wide, angled up and
out at about 45 degrees; each has a deep indigo / ultramarine EYE SPOT near its root that fades outward through bright
cobalt to pale periwinkle and an almost white-lavender edge, with a few thin darker veins radiating from the root.
LOWER pair: smaller, narrower, teardrop / dragonfly-like wings angled down and out at about 45 degrees, pale
periwinkle-white with a soft blue tint near the root and thin veins. Paint every wing membrane OPAQUE (no see-through
pixels inside the wing outline; we add the translucency later), with a crisp outer outline, and keep a small gap of
transparent background between all four wings. Front light, no shading gradients from the light.

Do NOT: draw wings on the body in 00-04; draw any lightning, glow, aura or spell effect; add a weapon, wand, crown,
jewellery, belt, sleeves, shoes, a cape or armour; give her green or human-coloured skin; make her a child or a cute
chibi cartoon; change the colours (blue skin, pale teal hair, magenta dress); cover her face or arms with hair; crop
the hands, the hair, the wing tips or the feet; draw a floor, ground shadow, background or text.

## Per-image checks (re-run before you select a view)

Whole figure inside the frame with margins; blue skin everywhere; long wavy pale teal hair clear of the arms and face;
magenta off-shoulder dress with the very short ragged pointed hem; bare blue arms, legs and feet; five separated
fingers on each open hand; A-pose with arms about 35 degrees out and a gap between the legs; no wings on the body; no
effects; transparent background; for 01-04 the same character, pose, proportions and colours as the primary; side
views: in `03_left` the face points to image LEFT, in `04_right` to image RIGHT; the front view symmetric. 05: four
wings only, symmetric, each separated by transparent gaps, upper pair large with the indigo eye spot, lower pair
smaller and paler. Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). Contact sheet `references_hd/selected_views_review.png` (the six
selected images), written in run 2.

## Run 2 notes (after run 1)

Claude accepted `00_three_quarter.png` (the first render) as the primary: blue skin, long wavy pale teal hair behind
the shoulders, magenta off-shoulder dress with the ragged pointed hem, open hands, bare feet, A-pose. (Claude zeroed its
faint alpha haze below 16/255; the raw return is kept as `00_three_quarter_raw.png`.) In 01-04 keep exactly this
character: the same face, hair volume and length, dress cut and hem, same A-pose (arms about 40 degrees out, fingers
spread), same proportions. Side views: strict 90 degree profiles at chest height; front and back straight on. In
`02_back` the long hair falls down her back to the waist, the bare shoulder blades show above the dress, NO wings.
Make sure no faint alpha pixels or glow reach the canvas (the run-1 image had a coloured glow at alpha 0-15: keep the
background fully transparent and black). `05_wings.png`: the four wings alone as specified, landscape 1536x1024.
