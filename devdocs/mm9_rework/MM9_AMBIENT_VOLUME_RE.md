# MM9 ambient sound volume (reverse engineering)

How loud Might and Magic IX plays an `AmbientSound` object, compared with OpenYAMM's
[placed ambient sounds](../AMBIENT_SOUNDS.md). Research date 2026-11-05, from `objdump -M intel` listings of the
shipped binaries (the listings in `re_mm8/work/mm9_slope/`, MSS32 disassembled ad hoc). The Jupiter sources in
`mm9/lithtech/runtime/sound/` were read only to name the structures; every claim below is checked in the MM9 binaries.

| Binary (`mm9/game/`) | SHA-256 | Role |
| --- | --- | --- |
| `data/object.lto` | `b1271f37e5314281035efe6425dd59051bb8a9b0271de0d75a5926a7bc37f162` | `AmbientSound` object |
| `data/cshell.dll` | `678700ff1cc795aeee49fe8427a42e1686d5a20dfdc1617eb46a8ef19f82f7ae` | Volume options, sound init |
| `lithtech.exe` | `4e9ddd2b69db934ecbd7399dd92992004e596907da4a214450f31c5dd39e56d8` | Ambient sound instance update |
| `MSS32.DLL` | `b3251203c3f68b4cb1f69ade0b300af0160d03094c08d6ce69821d475325206e` | Miles 6.0f mixer |

## The chain

1. **object.lto** (`0x100777dd`): the object passes its `Volume` (0–100) unchanged as the play request's volume
   byte; the helper at `0x100d7b20` only adds the control-volume flag when it is below 100.
2. **lithtech.exe**, sample start (`0x4622c5`): `AIL_set_sample_volume(Volume * 127 / 100)`. Ambient sounds take a
   plain 2D sample: no `AIL_set_3D_*`, no DirectSound rolloff, and no pan (centred).
3. **lithtech.exe**, every update (`0x462f15`–`0x462fb4`): `scale` is 1 inside the inner radius, 0 beyond the outer
   radius and `1 - (d - inner) / (outer - inner)` between, as in OpenYAMM. The result `min(Volume * scale, 100)` goes
   to `AIL_set_sample_volume` **without the 127/100 rescale**, so after the first frame an ambient sound plays at
   `Volume / 127` of full scale (−2.1 dB at Volume 100).
4. **MSS32** (`0x21114f80`): sample scale = `master * volume / 127`, linear in amplitude, then a pan table whose
   centre entry is full scale on both channels (no −3 dB pan law).
5. **Digital master** (`lithtech.exe` `0x465184`): `AIL_set_digital_master_volume(v * 1.27)`, called by cshell with
   `SfxVolume` when the sound system starts (`0x1007f15c`) and with `MasterVolume` whenever the options screen
   applies (`0x10040ef0`). Shipped defaults (`autoexec.cfg`): MasterVolume 75, SfxVolume 100, MusicVolume 75.
6. **Music** goes through the CD-audio line (`cdaudio`, WINMM mixer/`auxSetVolume`) at `MusicVolume`; the GOG build
   emulates the CD with MP3s. Its level against Miles' output is therefore not fixed by the game code.
7. **Voices**: `MaxSWVoices` and `Max3DVoices` default to 32 (`0x1007f037`, `0x1007f088`), more than any MM9 map
   overlaps, so MM9 also sums every ambient sound in reach, copies of the same loop included.

## Against OpenYAMM

OpenYAMM plays `volume (Volume / 100) * linear falloff * sound volume`, panned. The falloff and the summing match.
Two things differ:

- **The 127 quirk:** MM9's ambient sounds are 2.1 dB quieter than `Volume / 100` against other sounds. The converter
  (`mm9r_common/dungeon/ambient.py`) would match MM9 with `Volume / 127`.
- **Sound against music:** OpenYAMM's default sliders (sound 3/9, music 2/9) put every sound 3.5 dB above music. MM9's
  defaults give ambient sounds about +0.4 dB against music at launch (SfxVolume 100) and −2.1 dB after the options
  screen has applied MasterVolume 75, taking the CD line as linear. OpenYAMM's MM9 ambience is therefore about
  3–5.5 dB louder against music than MM9's, 2.1 dB of it from the quirk and the rest from the shared default sliders.

## Decision (2026-11-05)

The converter now writes `Volume / 127 * 2/3` (`ambient_volume` in `mm9r_common/dungeon/ambient.py`): the quirk, plus
a 2/3 balance that cancels the default sliders' 1.5x sound-over-music for MM9 ambience only. Volume 100 becomes 0.525
(−5.6 dB), which puts it 2.1 dB under the music, as in MM9 with its shipped MasterVolume 75. The global sliders stay as
they are because they also set MM6–MM8's balance, and placed ambient sounds are MM9-only so far. Other MM9 sounds are
unchanged. The nine review-root scenes built before this change (`output/mm9_rework`) had their volumes rescaled in place.

Files are not the cause: `assets_dev/worlds/mm9/audio/ambient` matches the original WAVs in RMS and peak (for
example `ambient/torchlight.wav` −38.8 dBFS RMS, `tropical.wav` −22.4 dBFS); the MM9 MP3 music is about −16 dBFS RMS.
