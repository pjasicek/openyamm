# Before / after viewer: MM6–MM8 audit fixes (2026-11-11)

Side-by-side three.js viewer for every MM6–MM8 model changed by the audit fixes: 104 models, filterable by stream
(texture, clips, attack, rebuild).
- **Left (before):** the model as committed in `assets_source` at HEAD (2026-11-11 12:11, before the fixes).
- **Right (after):** the installed file.
- **Shared controls:** one camera, tier, role or clip and playback position for both sides.
- **Tiers:** the engine's region ramps (`fs_model.sc`) and the binding's skin variant, scale, yaw and attachments
  from `actors.yml`, using HEAD's `actors.yml` for the before side and the working copy for the after side.
- **Notes:** each model's ledger notes are shown under the views.

```sh
python3 level_generation/creatures/audit_mm678_20261111/compare_viewer/build.py    # manifest + before/ GLBs (1.1 GB)
python3 level_generation/creatures/claude_shared/serve_review.py 8912              # if nothing serves the repo yet
# open http://127.0.0.1:8912/level_generation/creatures/audit_mm678_20261111/compare_viewer/
```

- **URL parameters:** `?tier=<index>&role=<standing|walking|run|attack_melee|cast|hit|dying|fidget>&view=<front|side|
  back|three-quarter|head close-up>&t=<0..1>#<stem>` open a given comparison, paused at fraction `t`.
- **Playback:** clips play at their real speeds; "sync by fraction" pins both sides to the same point of their clips,
  for retimed attacks.
- **Rebuild after commits:** once `assets_source` is committed, HEAD no longer holds the before state; rebuild from the
  previous commit by changing `HEAD` in `build.py`.
- **Headless check:** `node level_generation/creatures/claude_shared/check_viewer.mjs <url>#<stem>` (tiers and clips).
