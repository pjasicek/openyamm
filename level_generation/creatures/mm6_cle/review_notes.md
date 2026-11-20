# Cleric review and reproduction

Accepted all 59 native unique and referenced frames, native actions, five stored views/eight aliases, timing, logical placement and scale. Reviewed all raw sheets, ordered all-frame base/mask contacts, three native palette variants, light/dark edge contact and offline viewer samples (walk view 6/palette 674/frame 4; attack view 0/palette 676/frame 2). These ordered-sequence and paused-viewer checks are not a GPU performance measurement.

Replaced the rear-oblique walk sheet because its staff projected above the head where the native staff was occluded. Rejected output and exact prompts remain recorded. Fixed RGB gain 0.92 preserves native tonal weight; aligned boot material additionally uses 0.65 gain. Enhanced-pixel masks separate blue tunic, violet legs/boots and grey cloak. Native index groups guide fixed luminance ramps; a native lower-body guide limits boot proposals, while enhanced connected pixels define mask edges. Protected gold, skin and staff magic retain base colors. Explicit native leg indices avoid the incorrect flat bright shadow mapping of the earlier fit. Final variants and edges reviewed after correction. Zero residual magenta candidates above 16 in cleaned, exported and atlas-extracted frames.

The staff is somewhat brighter and its metal detail is interpretive, but the original pose, material identity and tonal appearance remain recognizable. Extraction contacts precede final grading; final packaged contacts/viewer include it.

Rebuild from repository root:
```
python3 level_generation/creatures/mm6_cle/process.py
python3 level_generation/creatures/mm6_cle/package.py
python3 level_generation/creatures/mm6_peasants/build_viewer.py cle
```
Rebuild resets visual acceptance. Stage only; no gameplay installation.
