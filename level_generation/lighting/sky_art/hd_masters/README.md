# HD sky masters

Approved Codex HD repaints of the original MM6–MM8 sky textures, one `<name>.png` per sky, named like the original
texture. `tools/sky/derive_legacy_skies.py` builds each runtime layer `assets_dev/engine/rendering/sky/legacy/<name>.png`
from its master here (falling back to the original bitmap only when no master exists). The masters stay outside the
runtime packages.

`masters.json` records, per sky, the job folder and attempt each master came from, why it was selected and its SHA256.

## Making or redoing a master

1. `tools/sky/prepare_hd_sky_job.py <job> <sky names...>` exports the native bitmaps (never x2 restorations) into
   `level_generation/lighting/sky_art/hd_skies/<job>/inputs/`, writes the job's `CODEX_BRIEF.md` and prints the
   `codex exec` command. The brief asks for a faithful repaint: same composition, cloud layout, palette and mood, open
   sky painted as one flat colour (for clean keying), seamless tiling, no added elements.
2. Run the printed command. Codex saves `<name>_hd.png` (selected) and `<name>_hd_try<N>.png` (rejected) with
   `generation_runs.json` and `selected_review.png` in the job folder.
3. Review each result beside its input: same layout and colours, real painted detail, no new elements. Codex's own
   checks can be stricter than needed (for example, a gap colour off by 1–2 RGB keys cleanly), so judge the image.
4. Copy the chosen file to `hd_masters/<name>.png`, add its `masters.json` entry, then run
   `tools/sky/derive_legacy_skies.py`.

The generator resamples a master to 1024², brings opposite edges together over a 4% band (image generators do not tile
exactly) and records the result's `seam_ratio` in `legacy_skies.json` (about 1 or lower is seamless).
