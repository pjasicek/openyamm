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

## Switched lights (2026-11-06)

`evt.SetLight(key, on)` switches a scene pulsing light (by its `key`) or a BLV point light (by the BLV light's `id`,
else its index): `EventRuntimeState::indoorLightsEnabled`, saved. A pulsing light is a dynamic light and shows on a
baked map at once; a BLV point light that an event switches changes only the vertex-lit faces and the actors' grid
light, since a bake keeps every BLV light as the map starts (INDOOR_BAKED_LIGHTING.md "Not baked"). A light MM9
switches is therefore built as a pulsing light.

- **Perception lights** (MM9's PerceptionLight -> PerceptionBase: Dark Passageway 61, Thjorad Mine 10, Verhoffin
  Ruins 4): red hint lights, like the PerceptionBrush hints shown only to a party whose Perception reaches their
  PerceptionValue, put out by Off messages and lit again by On. `dungeon/lights.py` `perception_lights` writes each as
  a pulsing light with a constant intensity and radius (LightRadius x 2.56), `start_on: false`, key 40000 + its DAT
  index (the GlowingLights' key space); `dungeon/objects.py` `shared_lines` checks them on load and every 3 s
  (event 904: map variables `Light<key>`, 2 on, 1 off; `LightOff<key>` 1 for MM9's Off) and switches them with
  `evt.SetLight`. A destructible's Death/DamageTrigger "off" to one is shared (`destructibles.on_break`); the map
  converters send the rest with `objects.perception_light_lua` (Thjorad Mine's barricade, falling board, steam valve,
  torches, stalactite and cart; Verhoffin's water trap nozzles, off while the room fills and on as it drains).
- **The Lich Lab's Glow1** (Engineglass1's Open/Close triggers): on while the Transmutation Engine's pod is shut
  (`mm9r_lichlab/convert.py`, handlers 200 and 251).

Test: `level_generation/projects/mm9r_darkpassageway/scenario_lights.yml` (the `light` assert: `{key, on}`).
