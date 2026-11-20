# Codex brief (front view, reworded variant 3 (last) after refusals): the HD front view for the MM7 m422 character (costumed nobleman)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m422_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Do NOT touch `00_three_quarter.png`.

The primary `00_three_quarter.png` is ALREADY SELECTED by the orchestrator (run `m422_three_quarter_r2b` in
`generation_runs.json`). Do not regenerate or re-judge it. This brief keeps the neutral wording of the accepted
reworded brief (`CODEX_BRIEF_r2_primary.md`, see `note_refusal_override_20261020`). `02_back.png`, `03_left.png` and
`04_right.png` are ALSO already selected; do not touch them. The front view was declined twice by the image tool
(output stage, category other: runs `m422_front_v1`, `m422_front_r1`, `m422_front_r2`); this is reworded variant 3, the last one, under the recorded
user decision `note_refusal_override_20261020`. Generate ONLY `01_front.png`. Append the new run(s) to
`generation_runs.json` (same record format, id `m422_front_r3`, `m422_front_r3b` for a correction), and refresh
`selected_views_review.png` with all five selected views, keep raw returns under `raw/`, and at the end write `selected_views_review.png` (all five
selected views side by side on a mid-grey background). If the image tool declines a request, record the refusal text
(with error code and moderation fields) in `generation_runs.json` and in your last message, skip that view, continue
with the other views, and do not reword the request yourself.

## Attached inputs, in order (paths relative to `level_generation/creatures/`)

1. `mm7_m422_claude/references_hd/00_three_quarter.png` — the selected HD primary. IDENTITY AUTHORITY for every new
   view: same man, costume, colours, pose (wide A-pose, open hands), proportions, light and render style.
2. `mm7_m422/native/m422sa0.png` — original low-resolution game frame, front.
3. `mm7_m422_claude/references_hd/02_back.png` — the selected back view (the same figure from behind: match its
   pose, arm angle, proportions and render style exactly, seen from the front).
4. `mm7_m422_claude/references_hd/04_right.png` — the selected right profile (same figure, same style).

## Deliverables (1024 x 1536 portrait, true transparent background, unresized returns)

Camera conventions (the man faces the viewer in `01_front`; "his left" means his own anatomical left):

| File | Camera | What the image must show |
|---|---|---|
| `01_front.png` | straight in front of him | symmetric front: gold front strip and belt buckle centred, both arms out in the A-pose, cape edges visible behind the arms, collar rising behind the head |

Generate each view with input 1 as the main reference. Accept a view as soon as it passes the checks below; for a
failed view do at most ONE targeted corrective regeneration, then select the better of the two and note any residual
fault in its reason.

## Prompt content (adapt per view)

TASK CONTEXT — 3D MODELLING REFERENCE for an original fantasy video game character: the FRONT view of the
character turnaround whose back view is input 3 (a costumed court nobleman, the same figure as input 1), for a
neutral, dignified model sheet: the outfit, its colours and its construction are what matter. Stylised
hand-painted fantasy game-art render with softened, simplified features (clearly a game character, like a painted
miniature or a stylised RPG model, not a photograph); the face is small, softly painted and generic, an original
character who does not resemble any real person, actor or film character. Not a new design. ONE complete figure from the top of the collar to the boot soles, centred, about 78% of the
canvas height, generous margins, camera at chest height, transparent background, no floor, no shadow, no scenery, no
text. Even soft neutral studio light, same materials as input 1.

Character (as input 1): a tall, lean, calm aristocratic man with very pale ivory skin, a calm, friendly, neutral face with a slight relaxed look, short
neat charcoal-grey hair; a tall flared dark-red stand-up cape collar with a thin gold edge; a royal-blue long
coat to mid-shin with a white shirt V, a small gold neck ornament, a vertical gold front strip with gold clasps, a gold
hem band and white cuffs; a broad ornate gold belt with an oval buckle; a dark-red cape behind the arms to about the
coat hem with a scalloped gold-trimmed edge; black trousers and black calf-high boots.

Pose (identical to input 1): standing upright, feet apart; arms in a wide A-pose, out from the body with clear air
between each hand and the coat and between each inner sleeve and the torso; arms in front of the cape; both hands open,
palms toward the body, five fingers, empty. Head level.

Do NOT: change the costume or colours; add a weapon, armour, jewellery, animals, blood, glow or effects; draw an
aggressive expression; let the cape cover the arms or hands; crop the collar or boots; add a floor, shadow or text.

Checks per view:
- the camera matches the table (side and facing direction); same pose, proportions and costume as input 1;
- whole figure inside the frame (collar, boots), true transparent background, 1024 x 1536;
- the cape hangs behind the body in every view and does not wrap over the arms.
