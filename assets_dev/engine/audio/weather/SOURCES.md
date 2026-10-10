# Weather sounds

Might and Magic IX ambient recordings, copied unchanged (mono, 22 050 Hz, 16-bit WAV) from the MM9 world package
into engine scope so every world's outdoor weather can use them (`engine/rendering/weather/weather.yml`).
They stay in `worlds/mm9/audio/ambient/` for MM9 itself. Chosen 2026-10-09 over CC0 recordings and the Morrowind
base-game sounds (longer seamless rain loops, more thunder variety, same franchise); the comparison is in
`level_generation/lighting/WEATHER_PLAN.md`.

| File | MM9 source (`worlds/mm9/audio/ambient/`) |
| --- | --- |
| `rain_light.wav` | `water/rain_light03.wav` |
| `rain_heavy.wav` | `water/rain_heavy.wav` |
| `wind_strong.wav` | `wind/wind.wav` |
| `thunder_near_1.wav` to `_4` | `thunder/thunder01.wav`, `thunder03.wav`, `thunder07.wav`, `thundershort.wav` |
| `thunder_middle_1.wav` to `_4` | `thunder/thunder04.wav`, `thunder05.wav`, `thunder06.wav`, `thundermed.wav` |
| `thunder_far_1.wav` to `_4` | `thunder/thunder distant01.wav`, `thunder distant02.wav`, `thunder distant03.wav`, `thunderlong.wav` |

The originals are peak normalised; `weather.yml` sets each sound's playback volume instead of re-encoding.
