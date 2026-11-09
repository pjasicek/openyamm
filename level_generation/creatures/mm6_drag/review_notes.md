# Cave dragon restoration review

Accepted 59/59 unique native sources: all 58 referenced images and unused dragfib0. Eleven AI sheets restore the native five stored views, six-phase walking cycle, front attack/hit/fidget and falling/corpse frames. Native actions, timing, mirrors, scale and source-relative logical anchoring are retained; unused artwork is not added to playback.

Reviewed all native and raw sheets, complete ordered base/mask contacts, three palette standing sets and magnified light/dark contours. Offline viewer captures inspect mirrored walk view 6 / palette 690 / frame 4 and death view 0 / palette 691 / frame 4. Tail swing, alternating raised feet, head/ear silhouette and falling/prone mass follow native poses. All three palettes keep distinct hide, underside and ivory material. Enhanced scales and brown mottling are larger and more defined than the tiny native noise, and variant spikes are slightly dimmer; these are visible restoration interpretations. No missing anatomy, pose replacement or surrounding magenta halo found.

Four soft enhanced-art mask channels distinguish teal hide, orange underside/fins/warm mottling, pale horns/claws and mauve mouth. Native palette indices guide fixed sigma=4 luminance LUTs; masks come from enhanced pixels. Base gain .82 and hide saturation .82 preserve native tonal weight. Palette 689 is an exact bypass; 690 and 691 are deterministic recolors of this artwork, not independent generations. Native source/palette/provenance hashes, alpha invariance, sequence bindings, crop/atlas reconstruction and mask weight checks pass. Zero residual magenta candidates at cleaned, exported and atlas-extracted stages.

Decoded base and matching RGBA masks total 117,727,336 bytes (112.27 MiB), excluding preview variants. The manifest declares multi_mask_luminance_lut_v1 and requires matching loader/shader support or deterministic variant baking before installation. Staged only; no GPU-performance claim.

Reproduce from repository root:
```
python3 level_generation/creatures/mm6_drag/process.py
python3 level_generation/creatures/mm6_drag/package.py
python3 level_generation/creatures/mm6_peasants/build_viewer.py drag
```
Rebuild resets acceptance; review affected outputs again.
