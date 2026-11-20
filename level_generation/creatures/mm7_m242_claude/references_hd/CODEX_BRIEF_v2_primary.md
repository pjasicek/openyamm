# Codex brief (run 1b): corrected HD primary for the MM7 Ghost (m242)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m242_claude/references_hd/`.
No builds, no Meshy, no other files. Append to the existing `generation_runs.json`; raw return as
`raw/m242_three_quarter_v3.png`. If v3 passes the checks below, copy it over `00_three_quarter.png` and mark it
selected (v2 superseded); otherwise keep v2 selected and record why.

Inputs (paths relative to `level_generation/creatures/`):
1. `mm7_m242_claude/references_hd/raw/m242_three_quarter_v2.png` — the current primary: IDENTITY, camera, robe,
   skull, colours, light and render style to keep exactly.
2. `mm7_m242/native/m242sa0.png` — ORIGINAL native front (design authority).
3. `mm7_m242/native/m242sa2.png` — ORIGINAL native side profile.

ONE correction only: the ARMS. Regenerate the same ghost, same front-right three-quarter camera (skull pointing toward
SCREEN-LEFT), with both bony arms held OUT TO THE SIDES at about 45 degrees from vertical and only slightly forward, so
that BOTH forearms and BOTH skeletal hands are entirely OUTSIDE the robe's silhouette with a clear gap of transparent
air between every finger and the cloth (no hand in front of the robe). Hands open, five long bony fingers spread,
palms down. Everything else exactly as input 1: the pointed hood with the skull, the open robe front with the ribcage,
the dark umber tattered robe hanging straight with long pointed shreds, NO legs or feet, no weapon, no effects.
1024 x 1536 portrait, true transparent background, generous margins (whole figure about 85 % of the height), no floor,
no shadow, no text.

Checks: both hands and forearms fully clear of the robe silhouette; same identity, camera and colours as input 1;
nothing cropped; true alpha; 1024 x 1536.
