# Codex brief: HD reference views for the MM6 New Sorpigal guard (mm6_gua_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_gua_claude/references_hd/` and
`level_generation/creatures/mm6_gua_claude/references_head/`. Do not edit any other file, do not run builds, do not
call Meshy.

Use your built-in image generation. Record format as in
`level_generation/creatures/new_sorpigal_3d_stage1_20261006/gua/generation_runs.json`.

## Why

The accepted stage-1 HD masters of this guard (inputs 1–5) show OPEN hands. The guard always holds a halberd in his
right hand (and with both hands when attacking), so the 3D model needs CLOSED GRIP HANDS. This job edits the five
accepted masters so the hands are closed grip fists. Everything else must stay identical. It also makes a head
turnaround for texturing the head.

## Attached inputs, in order

Paths are relative to `level_generation/creatures/mm6_gua_claude/`, except input 6, which is relative to
`level_generation/creatures/`.

1. `references_stage1/00_smart_topology_three_quarter.png` — accepted HD three-quarter master (identity authority).
2. `references_stage1/01_front.png` — accepted HD front master.
3. `references_stage1/02_back.png` — accepted HD back master.
4. `references_stage1/03_left.png` — accepted HD left-side master (the guard's left side).
5. `references_stage1/04_right.png` — accepted HD right-side master (the guard's right side).
6. `new_sorpigal_3d_stage1_20261006/gua/source/generation_inputs/standing.png` — ORIGINAL native low-res standing
   sprites (five views). Design authority for helmet, coif, mail, sleeves, belt, trousers and shoes. The halberd in
   the sprite must NOT be drawn. Dark/magenta background is not part of the character.

## Part 1 — body masters with closed hands (5 images, 1024 x 1536 portrait, transparent background)

Write into `references_hd/`:

| File | Edit of | View |
|---|---|---|
| `00_three_quarter.png` | input 1 | front three-quarter (primary; generate first) |
| `01_front.png` | input 2 | front |
| `02_back.png` | input 3 | back |
| `03_left.png` | input 4 | guard's left side |
| `04_right.png` | input 5 | guard's right side |

Generate `00` first, then 01–04 each with its own stage-1 view AND the new `00` as inputs, so all five show the same
closed hands.

The ONLY change: both hands become closed grip fists, as if each hand were holding an invisible round pole about
4 cm thick that runs horizontally FORWARD-BACKWARD through the fist: fingers curled tightly around it, the thumb
wrapped over the index finger at the front, palms facing the thighs, knuckles facing outward. Wrists straight. The
fists are solid (no visible hole is required), compact and clearly separated from the thighs (a clear gap of air
between each fist and the body, as now). Arms stay in the same A-pose (about 35 degrees from vertical), same length,
same position.

Keep EXACTLY as in the input: helmet (rounded iron cap with brass rivets, brass rim and a nasal bar), the bronze mail
coif covering chin, mouth and neck with only the eyes and nose bridge visible, the bronze/copper riveted mail shirt
with short sleeves to mid upper arm, the navy-blue cloth sleeves showing below the mail, the bare forearms, the brown
leather belt with brass buckle, dark teal trousers, brown leather shoes, body proportions, the legs and feet, camera,
light, framing and canvas size.

Do NOT: add a halberd, pole, weapon, shield or gloves; change the face, helmet, coif, colours or materials; add
gauntlets; move the arms; crop hands or feet; add a floor, shadow or text.

Per-image checks (re-run before selecting): both hands are closed fists with the thumb wrapped in front; five fingers
counted on each fist where visible; fists have air between them and the thighs; no added object; the rest of the
figure matches the input view; transparent background; 1024 x 1536.

## Part 2 — head turnaround (5 images, 1024 x 1024 square, transparent background)

Write into `references_head/`, generated from the accepted `references_hd/01_front.png` and `00_three_quarter.png`
as inputs (plus input 6 for the native helmet):

| File | View |
|---|---|
| `00_front.png` | head straight on (primary; generate first) |
| `01_three_quarter.png` | front-right three-quarter (45 degrees toward the guard's right) |
| `02_left.png` | the guard's LEFT profile (pure side view) |
| `03_back.png` | straight from behind |
| `04_right.png` | the guard's RIGHT profile (pure side view) |

Generate 01–04 with `00_front.png` as an additional input so all five show the SAME head.

Framing: head and neck only, like a sculpted bust WITHOUT shoulders: the mail coif ends in a clean horizontal cut a
little below the chin (no shoulders, no mail shirt). The helmeted head fills about 75% of the frame height, centred,
generous transparent margins, near-orthographic camera at eye height, head level. Even soft neutral studio light,
no dramatic shadows. Sharp fine detail: individual mail rings, rivets, the skin and eyes around the nose bridge.

Head identity: exactly the head of `references_hd/01_front.png` — rounded iron helmet with brass rivets, brass rim
band and a straight nasal bar; bronze mail coif covering chin, mouth, cheeks and neck, opening only for the eyes and
upper nose; calm stern eyes.

Do NOT: change the helmet shape, add plumes, crests, visors or face paint; show the mouth; change colours; crop.

Checks per image: same helmet and coif as the body master; only eyes and nose bridge visible; neck cut cleanly
below the chin; transparent background; 1024 x 1024.

## Records

In each folder: `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason,
superseded runs) and a `selected_views_review.png` contact sheet. Keep raw returns under `raw/`. Selected files are
unresized image-generation returns.
