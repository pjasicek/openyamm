# Codex brief (run 1b): corrected HD primary for the MM7 Cleric of the Sun (m174)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m174_claude/references_hd/`. No builds,
no Meshy. Append to the existing `generation_runs.json` (same record format), keep the raw return under `raw/` as
`m174_three_quarter_v3.png`, and if it passes the checks copy it to `00_three_quarter.png` (selected) and mark v2 as
superseded; otherwise keep v2 selected and record why.

Inputs (paths relative to `level_generation/creatures/`):
1. `mm7_m174_claude/references_hd/raw/m174_three_quarter_v2.png` — the previous HD return: IDENTITY, COSTUME, MATERIAL
   and COLOUR authority (keep the sun mask, rays, grey cap, scarlet collar, wavy gold mantle, striped robe, teal
   jewelled stole, gold wrist bands exactly as they are).
2. `mm7_m174/native/m174sa1.png` — ORIGINAL native front three-quarter frame (silhouette and proportion check).

Generate ONE image, 1024 x 1536 portrait, genuine transparent background, the same character as input 1, changing
ONLY the pose and the camera:
- POSE: A-POSE. Both forearms angled OUT from the body at 35 to 40 degrees from vertical (the hands well away from the
  robe), elbows nearly straight, with a clear, wide gap of transparent air between each forearm/hand and the robe and
  the mantle edge along the whole arm. Hands open and relaxed, palms toward the body, fingers gently separated. The
  mantle still covers the shoulders and upper arms. Legs slightly apart under the robe, hem on the ground. Head level.
- CAMERA: a TRUE front three-quarter view, 45 degrees to one side of straight front, chest height, near-orthographic:
  the robe and mantle show clear depth and one flank, the far arm partly overlapping the body silhouette is fine as
  long as its hand is clear of the robe.
- Framing: whole figure (all ray tips and the hem) inside the canvas, about 80 % of its height, generous margins.
- Even soft neutral studio light; no floor, shadow, glow, sparkles or text.

Checks: true 45-degree three-quarter; both hands clear of the robe with visible air; identity unchanged from input 1;
nothing cropped; true alpha. One attempt only.
