# OpenYAMM / MM9 effects viewer

Local browser viewer for all 48 groups in the original `SPELLS.fxf` and three authored OpenYAMM showcases.
Reads the original FXF, SPR, DTX, ABC and WAV assets without modifying them. Authored previews read
`assets_dev/engine/effects/authored/library.yml`, its bindings and PNG textures directly.
Requires Python 3 with PyYAML and a browser with WebGL 2; no frontend build or CDN dependencies.

From `re_mm8`:

```bash
./mm9_vfx/viewer/run.sh
```

This opens <http://127.0.0.1:8099/> and starts Column of Fire. Keep the terminal running;
Ctrl+C stops the server. Use `--no-browser` to open the URL yourself or `--port 8100`
to run another instance. The repository `mm9/` directory is the default; override it with
`--reference /path/to/OpenMM9/reference` or the `MM9_REFERENCE` environment variable.

## OpenYAMM showcase

The three new entries appear first in the list:

- [Healing Bloom](http://127.0.0.1:8099/?effect=openyamm%3Afx%2Fhealing_bloom&target=off): green pulses and rising sparks.
- [Ember Impact](http://127.0.0.1:8099/?effect=openyamm%3Afx%2Fember_impact&target=off): fire animation, embers and alpha smoke.
- [Arcane Pulse](http://127.0.0.1:8099/?effect=openyamm%3Afx%2Farcane_pulse&target=off): purple energy, an expanding ring and sparks.

These links hide the optional target so the artwork is unobstructed. The target is positioned at foot level
for authored previews. Native MM9 previews retain their original origin. Restart the server after changing
YAML or textures, then refresh the browser. JS/CSS edits only need a refresh.

Authored playback uses full particle lifetimes and precise animation clocks, separate from recovered MM9
quirks. The native Detail control is disabled for authored recipes. Both modes support 30/60/120 Hz updates;
like the engine, emission is evaluated on those ticks. This is a browser approximation, not the C++ renderer:
particle RNG placement, lighting and exact floating-point tick boundaries can differ. Unsupported authored
component types, attachments and rotation are rejected rather than silently omitted. Current support covers
world-space sprite emitters and fixed sprites used by these showcases.

## Controls

- Search and select an effect in the left list. Selection starts playback.
- Replay, pause, drag the timeline, and change playback speed.
- Drag to orbit, scroll to zoom, right-drag or Shift-drag to pan; Reset camera restores the view.
- Space pauses/resumes; R replays when a text/control input does not have focus.
- Enable Sound to audition the original WAV components; use the adjacent volume slider.
- Toggle the target monk and grid, or change the background.
- Frame rate changes **simulation updates**, which affect native emission density.
  Detail reproduces the recovered low/medium/high interval behavior.
- Effect details lists timed components and assets. Path-helper meshes can be shown there.

`?effect=spell-column%20of%20fire&time=0.55` opens a paused, repeatable preview.
Repeat replays the complete effect after its remaining particles finish.

## Fidelity

The simulation uses the [binary investigation](../README.md): numeric emission opcodes,
inverted transparency, unnormalized wind, update-dependent emission, detail scaling,
particle expiry, sprite frame timing and recovered blend choices. Original textures and
the first ABC animation are decoded directly. The optional monk uses its static model pose.

This is a visual research preview, **not demonstrated original-game visual parity**.
World lighting, full LithTech texture/material stages, exact model tracking and attachment
transforms, and engine RNG ordering remain approximate. Model skins use opaque texture
alpha with component opacity; particle/sprite textures retain their alpha. Audio is a 2D
audition with volume/pitch, not the game's positional attenuation. There is no level geometry,
collision, combat, or casting logic. FX library groups are not a complete spell implementation.

Two referenced assets are absent from the supplied extraction: `skins/ghost.dtx` (Ghost)
and `models/spells/armortube.abc` (Blobby). Their affected previews display a warning.

## Validation

From `re_mm8`:

```bash
python3 -B mm9_vfx/viewer/serve.py --check-assets
node mm9_vfx/viewer/test_simulation.mjs
node mm9_vfx/viewer/test_authored.mjs
node mm9_vfx/viewer/test_browser.mjs
```

The browser test requires Google Chrome and a running viewer. It checks all 51 selections,
rendering errors, search, audio, pause and monk visibility; screenshots go to ignored
`work/mm9_vfx/viewer_checks/`. It uses a temporary Chrome profile and software WebGL.
The simulation tests exercise recovered timing, emission, alpha, wind and detail rules.
