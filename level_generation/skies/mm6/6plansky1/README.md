# Native MM6 6plansky1 — x2 restoration pilot

Open the [current seam-repair gallery](review/v3/index.html). The selected pilot is **v3_local**, a 1024×1024
opaque RGB PNG based on native MM6 `6plansky1`. User screenshot `1292.png` exposed a visible wrapping seam in v2;
this revision repairs the crossing boundaries using built-in imagegen, preserving the rest of v2 through a local mask.
The user accepted the repaired pilot artwork on 2026-09-09 (“OK this is fine”). The separate grey renderer fade
reported in `1290.png` remains unresolved. Full original-game fidelity is not accepted.
Future jobs should follow the [pilot lessons](../../MM6_MM8_SKY_RESTORATION_PLAN.md#lessons-from-the-6plansky1-pilot).

- [Current runtime export](runtime_x2/6plansky1.png), [identical alias](runtime_x2/6sky01.png).
- [Seam-repair prompt](prompts/v3.txt), [raw AI output in half-offset orientation](generated/v3_offset.png).
- [Manifest](manifest.json), [current asset checks](review/v3/asset_checks.json), [feedback](review/feedback.md).
- [Historical v2 gallery](review/index.html), [v2 export](review/v2/6plansky1.png), [v2 manifest](review/v2/manifest.json).

Export: raw 1254² → Lanczos 1024², select the repaired central cross (48px core, sigma-12 mask feather),
composite onto v2's half-offset tile, then undo the 512px roll. Only the selection mask is blurred; cloud pixels are not.
This confines the AI repair instead of accepting its unrelated changes elsewhere. No palette grading, sharpening,
mirroring, forced identical edge strips or global seam smoothing is used. The source BMP remains unchanged.
SHA-256: `41bddc20a7ab2545b53d746ff35803f1cc062aeb08d14d0462aa0c499dd8d747`.

## Play the isolated pilot

From the repository root:

```sh
./level_generation/skies/mm6/6plansky1/play.sh x2
```

The launcher loads **Sky_pilot** directly at the saved review pose. Use `x1` instead to compare the original. It prepares an isolated
asset tree/settings/saves under `/tmp/openyamm-mm6-6plansky1-pilot`, using the current built executable. Only this sky
and its identical alias use the new art; the other five unique Enroth weather skies are explicitly labelled native
nearest-neighbour x2 placeholders. The stage is for New Sorpigal, not general all-world sky validation.
Main `assets_dev`, `settings.ini`, weather lists and user saves are not changed. Repreparing may refresh the staged
binary; play sessions keep their metadata under `/tmp` and preserve the historical capture manifest.

## Evidence and its limits

**Follow-up on `test_img/1290.png`: original-game appearance is still unresolved.** The captured pilot really opens
the restored native `6plansky1.png`, but the renderer overlays a grey alpha gradient from the viewport top to the
horizon even in clear weather. Both x1 and x2 comparisons include this fade. Matching each other did not establish
a match to original MM6 (`test_img/1289.png`), whose sky stays deep blue much closer to the horizon. The local
OpenEnroth renderer has the same broad fade when its graphics fog option is enabled; this alone is not proof of
original MM6 behaviour. Investigate presentation separately before declaring full in-game authenticity accepted.
No sky selection or renderer changes were made for this follow-up. The pilot launcher previously inherited blank
startup-save settings; it now explicitly loads the retained review save instead of starting a fresh session.

The historical v2 gallery's four main captures use the same executable and corresponding saved camera/time/weather states under isolated
Xvfb at 1600×1200. Surface textures and other quality categories are x1 in both runs. The overhead pose was verified
through the game's `loc` console: position (-9954.209, -9427.790, 161), yaw 83.552°, pitch 25.955°.
The horizon save uses the same position, yaw 173.552°, pitch 5°.
Cloud scroll uses wall time, so the two runs are not exactly pixel-aligned; original actors/UI can differ slightly.
The gallery's slider is for visual comparison, not a pixel-perfect subtraction test.

The two motion previews contain 12 real game frames at roughly 0.25-second intervals. Original PNGs and timestamps
are retained; WebM is a compressed convenience preview. They demonstrate short-term continuity, not every possible seam
crossing, weather transition, night state or graphics backend.

Successful file-open tracing confirms the native `textures/6plansky1.bmp` and staged `textures_x2/6plansky1.png`.
Horizon captures were traced and their timings are excluded from performance comparison. Untraced overhead captures
ran at about 59.4 FPS in this Xvfb environment in both tiers; this is not a meaningful target-GPU speed comparison.
Separate untraced load checks use the existing `OPENYAMM_MAP_LOAD_TIMING` diagnostics. The current executable already
preloads its initial sky while loading the map, so the first sky does not need a render-time cache miss. See the
runtime report for measured preload times: a single untraced sample was **47.8 ms native / 70.3 ms x2**,
inside map loading. The OS file cache was not flushed, so this is not a cold-storage benchmark. No frame-level p95/p99, long-run cache or target-GPU benchmark is claimed.

## Reproduce

`build_review.py` needs Python, Pillow and NumPy; `prepare_review.py` needs Python and ImageMagick. The capture helper
also needs PyYAML, python-Xlib, Xvfb and ImageMagick. No engine code changes or new compilation were needed for this asset. `build_review.py` defaults to the selected
manifest version; v3 checks are written under `review/v3` so historical v2 comparisons stay intact.
The old `collect_review.py` describes v2 only and refuses to overwrite a newer manifest.
The v3 gallery documents the additional matched-phase capture procedure and its diagnostic limitations.

```sh
python3 level_generation/skies/mm6/6plansky1/build_review.py
python3 level_generation/skies/mm6/6plansky1/prepare_review.py
xvfb-run -a -s '-screen 0 1600x1200x24' env OPENYAMM_MAP_LOAD_TIMING=1 \
  python3 level_generation/projects/brackenford_greywatch/capture_gameplay.py mm6sky_repeat_x2 \
  --world mm6 --map oute3.odm --stage /tmp/openyamm-mm6-6plansky1-pilot/x2 \
  --binary /tmp/openyamm-mm6-6plansky1-pilot/openyamm \
  --review-directory level_generation/skies/mm6/6plansky1/review \
  --start-save level_generation/skies/mm6/6plansky1/source/overhead.oysav \
  --actions level_generation/skies/mm6/6plansky1/review/capture_actions.json --warmup 1 --seconds 5
```

Use the x1 stage for the native capture and `source/horizon.oysav` for the horizon pose. Keep the same frozen executable
for each pair. Do not replace the original reference with a capture made using an incomplete x2 weather set.
