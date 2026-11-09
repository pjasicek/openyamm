# Codex brief: HD modelling references for the Landfall villager, female (Hesper)

Scope: image generation only. Write ONLY into `level_generation/creatures/hes_villager_f_claude/references_hd/` and
`level_generation/creatures/hes_villager_f_claude/references_head/`. Do not edit any other file, do not run builds, do not call Meshy.
Use your built-in image generation tool.

This is a new character of the Hesper world (an OpenYAMM world in the Might and Magic VI-VIII style), not an MM
sprite: its design authority is the user-approved concept sheet, `design/kreegan_world/concepts/people/villager_female.png`.

## Inputs (attached in this order)

1. `references_hd/concept.png` — the APPROVED concept sheet: a large front three-quarter view on the right, a straight
   front view (upper left) and a straight back view (lower left). Design, proportions, materials and colour
   authority. Reproduce this exact character faithfully; do not redesign. Note: the concept's small back view mirrors the bag and the sash tails by mistake; follow the front and main views (bag on her RIGHT hip, sash tails at her LEFT hip).
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

Head turnaround in `references_head/`, bust only (head, hair (braided bun), neck and top of the shoulders), 1254x1254
(or the closest square size), transparent background, the same face as the body masters, neutral expression, mouth
closed: `01_front.png`, `00_three_quarter.png`, `02_profile.png` (the figure's right side, face toward image right),
`03_back.png`.

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (separate invocation): 01–04 with the selected 00 as an input. Run 3: the head turnaround.
At most one corrective regeneration per view.

## Prompt content (adapt per view)

TASK CONTEXT — GAME ASSET: a faithful high-definition 3D modelling reference of an approved character concept, for
an MM6-8-style first-person RPG. Not a new design. Use case: 3D character modelling reference sheet view.
Near-orthographic camera, even soft neutral studio light (no dramatic lighting, no rim light, no strong shadows: the
light is baked into the texture), painterly-realistic game materials like the concept, sharp fine detail, a credible
fully three-dimensional figure, clean well-kept clothing (no rips, patches, frays or grime).

Identity (from the concept): an ordinary well-dressed Hesperian townswoman in her late thirties,
average build, a warm face, dark-brown hair braided and pinned up in a low bun with a thin gold-and-ceramic band, small
pearl-white ceramic drop earrings in gold. A fitted calf-length colony COAT-DRESS in dark SLATE grey-blue with an
asymmetric front closing on her right with small gold clasps, gold piping along every edge, a high stand-up collar,
off-white sleeves and off-white turned-back cuffs edged in gold; an off-white under-tunic shows in the front split
below the waist. A town-RED sash wrapped round the waist, knotted at her LEFT hip with two long tails hanging there,
the tail ends edged in gold. A small off-white ceramic shoulder BAG with gold fittings and a small blue lens on its
flap, its strap over her RIGHT shoulder, the bag at her RIGHT hip. On her RIGHT wrist a white ceramic cuff with a
glowing blue-white light strip. Slim light-grey trousers, dark slate ankle boots with gold rings at the ankle.

Pose (identical in all five body views): A-pose, arms straight down and away from the body about 40° from vertical
so there is clear air between the arms and the body. Hands open and relaxed, fingers slightly apart, clear of the bag and the sash. Legs straight, feet a little more than hip-width
apart with a clear gap between the legs, soles flat. Head level, looking forward.

Do NOT: add a hat, a cape, a weapon or armour; change the colours (dark slate coat-dress, off-white sleeves, red sash, gold piping, light-grey trousers); make the clothes patched or ragged; let the sash tails or bag touch the hands; crop the head, hands or feet; draw a floor, shadow, background or text.

## Per-image checks (re-run before you select a view)

Full figure inside the frame with margins; dark slate calf-length coat-dress with gold piping and high collar; off-white sleeves and under-tunic; red sash knotted at her LEFT hip; ceramic bag on her RIGHT hip with the strap over her RIGHT shoulder; lit cuff on her RIGHT wrist; braided bun with earrings; light-grey trousers; slate ankle boots; open hands; A-pose with air between arms and body and between the legs;
hands as specified; transparent background; for 01–04 the same figure, pose, proportions and colours as the primary;
side views: in `03_left` the face points to image LEFT, in `04_right` to image RIGHT, and every asymmetric detail is
on the correct side of the body. Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json` and `references_head/generation_runs.json`: one entry per generation (id, view,
prompt, input paths with sha256, output path, selected flag, reason, superseded runs). Contact sheets
`references_hd/selected_views_review.png` (the five body views) and
`references_head/selected_views_review.png`.
