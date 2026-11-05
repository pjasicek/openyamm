# Indoor pulsing lights (BLV)

MM9's GlowingLight (2026-11-04; Wizard's Lab has 37, the Lich Lab one): a dynamic point light whose intensity and
radius each follow a sine between a minimum and a maximum.

```yaml
pulsing_lights:
  - key: 40123                    # evt.SetLight(key, on) switches it (EventRuntimeState::indoorLightsEnabled, saved)
    position: [1200, -340, 96]
    color: [255, 172, 47]
    intensity: [0.3, 1.0, 3.0, 0.0]     # min, max, frequency (cycles per second), phase (cycles)
    radius: [128, 512, 4.0, 0.0]        # native units
    start_on: true                      # its state until evt.SetLight sets one
```

- `game/indoor/IndoorMapData.h` `IndoorPulsingLight`, parsed by `game/maps/IndoorSceneYml.cpp` (an overlay's list replaces
  the base scene's).
- `IndoorLightingRuntime::buildFrame` adds each switched-on light to the frame as a dynamic (FX-kind) light at the
  renderer's clock: `min + (max - min) x (0.5 + 0.5 sin(2 pi (frequency t + phase)))`. Its sector is found once when the
  static cache is built, its reach each frame; it is skipped while no room it reaches is in view. Faces, models and
  sprites take it as they take spell lights (the light grid).
- The converter: `level_generation/projects/mm9r_common/dungeon/lights.py` `pulsing_lights` (key 40000 + the DAT
  index, radius x 2.56). MM9's On/Off triggers for its StartOn 0 lights are each map's Lua to write.
- Not reproduced: MM9's waveform choice (every light pulses as a sine) and its ramp sounds.
