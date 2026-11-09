# Beholder review and reproduction

Accepted all 48 unique native images, including five stored flight views, mirrored aliases, six attack frames, five hit frames and seven disintegration/corpse images. Native idle/walk/fidget reuse, attack2 reuse, 125 ms timing, variant scales and anchoring are preserved.

Reviewed all native/raw sheets, ordered base/mask contacts, all standing variants, magnified light/dark edge contacts and offline viewer captures: mirrored walk view 6 / palette 669 / frame 4, attack view 0 / palette 671 / frame 2, death view 0 / palette 669 / frame 4. The first attack and death generations omitted the native eye flash; rejected outputs and correction prompts are retained. Final flash saturation was reduced to match the pale native catchlight. Three enhanced mask channels separate blue skull skin, gray face/horns/teeth and iris. Fixed native-used LUTs reproduce brown/gray/green-eye and black/olive/green-eye variants. White eye highlights and flash are protected.

Purple-safe matte extraction preserves the iris. Native colored-eye locations provide coarse search bounds only; actual iris selection follows enhanced color components/hulls. Reviewed profile bounds exclude false purple in the horn loop; rear views have no iris. Non-eye purple contamination is neutralized. Final generic purple candidates (790 cleaned, 1585 exported and atlas-extracted) are intentional eye/iris fragments; reviewed light/dark contacts show no external magenta halo. Atlas extraction, source/palette hashes, alpha, exact base bypass and native sequences pass recorded checks.

Enhanced creases and carved-looking facial detail are interpretive and stronger than the original fine texture. The narrow profile eye sliver and disintegration fragments are approximate. Native silhouette, dark tonal weight and characteristic appearance remain recognizable. Sequence/contact and paused-viewer checks do not measure GPU performance.

Rebuild from repository root:
```
python3 level_generation/creatures/mm6_bh/process.py
python3 level_generation/creatures/mm6_bh/package.py
python3 level_generation/creatures/mm6_peasants/build_viewer.py bh
```
Fixed 0.80 RGB gain and neutral temperature [0.94,1,1.07]. Rebuild resets visual acceptance. Staged only; no gameplay installation or original replacement.
