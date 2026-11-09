# Codex brief (run 1b): one targeted correction of the m246 HD primary

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m246_claude/references_hd/`.
No builds, no Meshy, no other files.

Inputs (paths relative to `level_generation/creatures/`):
1. `mm7_m246_claude/references_hd/raw/m246_three_quarter_v2.png` — the current HD primary. IDENTITY AUTHORITY: keep the
   same goblin, face, ears, chin tuft, helmet and crest, hair, blue-teal vest, strap, belt, gold hip panels, pauldron
   and armoured left sleeve, right bracer, navy scaled trousers, boots with spiked brass shin guards, colours, camera,
   light and render style exactly.
2. `mm7_m246_claude/source/native_standing_views.png` — the original native sprite views (identity evidence only).

Make ONE corrected image, saved as `raw/m246_three_quarter_v3.png`, and if it passes the checks, copy it to
`00_three_quarter.png` (otherwise leave `00_three_quarter.png` as it is). Append the run to `generation_runs.json`
(same record format; mark the selected run and why).

Correction (the only changes):
- HANDS: both green hands fully OPEN and relaxed, palms facing the thighs, the four fingers STRAIGHT (not curled) and
  visibly SPREAD apart with small gaps between every finger, the thumb clearly separated from the index finger.
  No fists, no claws, no curled or bent fingers.
- ARMS: hang out from the body at about 35 degrees from vertical (a little wider than input 1), so each hand is a
  clear hand-width away from the thigh and the gold hip panels, elbows nearly straight.

Everything else unchanged: 1024 x 1536 portrait, one whole figure with margins, front three-quarter as input 1,
transparent background, no floor, no shadow, no text, no weapon in the hands.
Checks: open straight spread fingers on both hands (thumb + four fingers each), clear gaps hand/thigh and arm/body,
same identity and colours as input 1, nothing cropped, true alpha. No further retries after this one.
