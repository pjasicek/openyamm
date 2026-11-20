# Codex brief: HD modelling references for the Landfall Guard (Hesper)

Scope: image generation only. Write ONLY into `level_generation/creatures/hes_guard_claude/references_hd/` and
`level_generation/creatures/hes_guard_claude/references_head/`. Do not edit any other file, do not run builds, do not call Meshy.
Use your built-in image generation tool.

This is a new character of the Hesper world (an OpenYAMM world in the Might and Magic VI-VIII style), not an MM
sprite: its design authority is the user-approved concept sheet, `design/kreegan_world/concepts/people/landfall_guard.png`.

## Inputs (attached in this order)

1. `references_hd/concept.png` — the APPROVED concept sheet: a large front three-quarter view on the right, a straight
   front view (upper left) and a straight back view (lower left). Design, proportions, materials and colour
   authority. Reproduce this exact character faithfully; do not redesign. The blue shell around the main view is his energy shield (an engine effect): do NOT draw it.
2. (runs 2 and 3 only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Body masters in `references_hd/`, one figure each, full body from the top of the head to the soles, unresized
returns, 1024x1536 PORTRAIT, true transparent background, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter, body turned about 35° (we see the front and the figure's RIGHT side), camera at chest height slightly above |
| `01_front.png` | front |
| `02_back.png` | back |
| `03_left.png` | the figure's LEFT side: faces image LEFT, the left shoulder nearest the camera |
| `04_right.png` | the figure's RIGHT side: faces image RIGHT, the right shoulder nearest the camera |

Prop reference in `references_hd/`: `rifle.png`, 1536x1024 LANDSCAPE, transparent background: the blaster rifle
ALONE, seen exactly from its side (muzzle to image RIGHT, pistol grip down), the whole rifle inside the frame with
margins, no hands, no glow halo beyond the emitter itself.

Head turnaround in `references_head/`, bust only (head, hair, the helmet, neck and top of the shoulders), 1254x1254
(or the closest square size), transparent background, the same face as the body masters, neutral expression, mouth
closed: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (the figure's right side, face toward image right),
`03_back.png`.

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): 01–04 and `rifle.png` with the selected 00 as an input. Run 3: the head turnaround.
At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT — GAME ASSET: a faithful high-definition 3D modelling reference of an approved character concept, for
an MM6-8-style first-person RPG. Not a new design. Use case: 3D character modelling reference sheet view.
Near-orthographic camera, even soft neutral studio light (no dramatic lighting, no rim light, no strong shadows: the
light is baked into the texture), painterly-realistic game materials like the concept, sharp fine detail, a credible
fully three-dimensional figure, clean well-kept clothing (no rips, patches, frays or grime).

Identity (from the concept): a sturdy Hesperian town guard, a man in his forties with a weathered
clean-shaven face, short dark hair under the helmet. HELMET: an open-faced rounded helmet of white Ancient ceramic
with a gold brow band and gold rivets, a small round blue lens on its left side, the face fully visible. ARMOUR of
white/ivory ceramic plates with brushed gold edging and rivets: a chest plate, large rounded shoulder plates, upper-arm
and forearm guards, a back plate, rounded knee plates, and fitted armoured boots with white ceramic shin guards and
toe caps edged in gold over dark slate soles and joints. Under the plates a fitted slate-BLUE high-collared colony
coat reaching mid-thigh and fitted slate-blue trousers; dark brown gloves. A clean RED tabard with a straight
gold-bordered hem hangs front and back from under the chest plate to above the knees, on the front one simple gold
glyph (a ring above a vertical line). A dark brown belt with a square gold buckle and pouches; on his RIGHT hip a round
white-ceramic-and-gold SHIELD EMITTER with a glowing blue-white lens.

Pose (identical in all five body views): A-pose, arms straight down and away from the body about 40° from vertical
so there is clear air between the arms and the body. BOTH hands are loose FISTS with the fingers curled around EMPTY space as if
holding a rifle (right: the pistol grip, left: the fore-grip), knuckles forward-down. EMPTY HANDS: the rifle is a
separate prop, do not draw it. Legs straight, feet a little more than hip-width
apart with a clear gap between the legs, soles flat. Head level, looking forward.

Rifle (`rifle.png` only): the blaster rifle from the concept, about 1.0 m long at his scale: a long white/ivory
ceramic body with gold trim and rivets, a gold pistol grip and trigger guard under the rear, a short stock, a small
rectangular blue-white glowing power cell window in the body, a fore-grip under the middle, the barrel ending in four
stacked white ceramic cooling rings and a glowing blue-white emitter tip at the muzzle.

Do NOT: draw the rifle in his hands or a shield shell; add a cape, a sword, a backpack or extra weapons; change the colours (white ceramic and gold plates, slate-blue coat and trousers, red tabard); make the tabard frayed; crop the head, hands or feet; draw a floor, shadow, background or text.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins; open-faced ceramic helmet with gold band and blue side lens; white ceramic plates with gold edging; slate-blue coat; red tabard with gold-bordered hem and the gold glyph on the front; belt with the shield emitter on his RIGHT hip; armoured ceramic boots; both hands empty fists; A-pose with air between arms and body and between the legs;
hands as specified; transparent background; for 01–04 the same figure, pose, proportions and colours as the primary;
side views: in `03_left` the face points to image LEFT, in `04_right` to image RIGHT, and every asymmetric detail is
on the correct side of the body. Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json` and `references_head/generation_runs.json`: one entry per generation (id, view,
prompt, input paths with sha256, output path, selected flag, reason, superseded runs). Contact sheets
`references_hd/selected_views_review.png` (the five body views and the rifle) and
`references_head/selected_views_review.png`.

## Side-view correction run (after run 2)

Run 2 stopped on a Codex capacity error after its first returns. `01_front.png`, `02_back.png` and `rifle.png` are
selected. `03_left_run2a.png` and `04_right_run2a.png` face the right way but are turned about 25° toward the camera.
In this run regenerate ONLY `03_left.png` and `04_right.png` as STRICT 90° PROFILES (camera exactly perpendicular to
the body's facing direction; only one eye visible; the far arm hidden behind the body except the fist; shoulders seen
edge-on), same man, pose, colours and proportions as the primary (input 2) and the front view (input 3); the shield
emitter on his RIGHT hip (visible in `04_right`, hidden behind the body in `03_left`). Save over `03_left.png` /
`04_right.png` only if the new one passes; record both in generation_runs.json; update selected_views_review.png
(five views and the rifle).
