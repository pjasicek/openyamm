# Codex brief (run 2): one corrective regeneration of the Druidess primary (dru1)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_dru1_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Run 1 selected `raw/dru1_three_quarter_v2.png` (now `00_three_quarter.png`). Its identity is RIGHT and must be kept
exactly: same woman, face, hair, hood, cloak, studded bodysuit, belt medallion, choker, armbands, bracers, boots,
colours, materials and render style. Two things must change, for 3D modelling (Meshy reconstructs depth from this one
image, and a hand drawn over the cloak gets fused into the cloth):

1. ARMS: hang down and OUT to the sides at about 40 degrees from vertical, elbows very slightly bent, so that BOTH
   HANDS are completely OUTSIDE the cloak's silhouette, with clear transparent background visible between each hand
   and the cloak, and between each arm and the torso. Hands relaxed and open, five fingers each, slightly apart,
   palms facing inward. The cloak still hangs BEHIND the arms from the shoulders.
2. CAMERA: a clear front-right three-quarter view, the camera turned 40-45 degrees toward HER OWN RIGHT side (her
   right arm nearer the camera, on image left), at chest height, slightly above; near-orthographic.

Also: whole figure with generous margins (at least 60 px above the hood, below the boot soles and at each side),
clean genuine transparent background with no translucent haze or glow around the silhouette, 1024 x 1536, no floor,
no shadow, no text.

Attached inputs, in order (paths relative to `level_generation/creatures/`):
1. `mm6_dru1_claude/references_hd/raw/dru1_three_quarter_v2.png` — IDENTITY AUTHORITY (keep everything but pose
   and camera).
2. `mm6_dru1/references/standing.png` — ORIGINAL native five-view sheet (magenta is background).
3. `mm6_dru1/native/dru1wka0.png` — ORIGINAL native frame with both arms in front of the open cloak.

Save the return as `raw/dru1_three_quarter_v3.png`. If it passes the checks below and keeps the identity, copy it to
`00_three_quarter.png` (selected) and mark v2 superseded; otherwise keep v2 selected. One generation only, no further
retries. Append the run to `generation_runs.json` (same record format: id, family, role, prompt, inputs with sha256,
output path, selected flag, reason, superseded runs).

Do NOT: change the outfit, colours, face or hair; add any held object or spell effect; close the cloak at the front;
let the cloak cover the arms or hands; crop anything.

Checks:
- both hands fully outside the cloak silhouette with background between; arms clear of the torso;
- front-right three-quarter at 40-45 degrees, her right arm on image left;
- identity identical to input 1; margins; clean alpha; 1024 x 1536.
