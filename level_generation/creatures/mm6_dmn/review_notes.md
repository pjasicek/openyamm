# Walking demon restoration review

Accepted all 67 native source names, 59 unique enhanced images and eight native pixel aliases. The 66 descriptor-referenced names, unused native alias, all actions, native stored directions, mirrors, timing, scale and offsets are preserved. Five shared ash sources reuse the accepted flying demon ash generation with fixed palette 496 and zero recolor masks.

Reviewed every generated/native sheet, all ordered base and mask contacts, three standing palette appearances, light/dark edge contacts and the offline viewer. Final captures cover mirrored walking view 6 / palette 687 / frame 4, front attack / palette 687 / frame 4 and front death / palette 686 / frame 4. Corrected demonstrated warm claw/effect confusion, insufficient neutral belly protection, pale variant eyes and gray patches in flame tips. Final orange death plume has continuous warm coloration. Arms crossing the neutral belly retain their own skin material. Four soft enhanced-art masks distinguish body, harness, hard ivory material and eyes/effect; a reviewed anatomical region protects neutral belly paint. No resized native pixel masks.

The new skin scales and angular disintegration fragments are interpretations of native detail. Enhanced spikes have somewhat stronger pink/orange shading in variants than the tiny native spikes. The original dark body, small head, long claws, tail and harness remain recognizable. Zero residual magenta candidates in cleaned, exported and atlas-extracted frames; thin contours and effect gaps survive light/dark review. Source, palette and generation hashes, native sequences, crop/atlas reconstruction, alpha invariance and mask weight checks pass.

Base gain .86; death highlights remain at 1.0; reused ash gain .42. Native-used sigma=4 luminance curves are fixed and explicitly declared as multi_mask_luminance_lut_v1. Decoded base plus RGBA mask atlases: 109,110,376 bytes (104.06 MiB), excluding baked variant previews. Staged only; no gameplay installation or GPU-performance claim.

Reproduce from repository root:
```
python3 level_generation/creatures/mm6_dmn/process.py
python3 level_generation/creatures/mm6_dmn/package.py
python3 level_generation/creatures/mm6_peasants/build_viewer.py dmn
```
Rebuilding resets visual acceptance; review changed outputs before accepting again.
