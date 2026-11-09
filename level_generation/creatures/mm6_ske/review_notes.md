# Skeleton review and reproduction

Accepted offline restoration of all 59 native unique frames, 58 referenced plus unused skefib0.
Five stored standing/walking views, native mirrors, front-only actions, repeated fidget skefia0,
logical placement, frame scale and exact per-palette native sequences are preserved.
Native palette 816 has five death frames; palettes 817/818 use six. This difference is intentional.

Reviewed every native/raw sheet, final all-base/all-mask contacts, all three standing palettes,
ordered action frames, light/dark enlarged edges and paused offline viewer samples:
standing palette 818, mirrored walk view 6 / palette 817 / frame 4, death palette 816 / frame 3.
These are sequence/placement checks, not real-GPU or continuous-video performance measurements.

The generated warm bone was neutralized to ivory with a fixed material-only correction.
Bone, rusty blade/hilt and red eyes have separate enhanced-art mask channels. Native sword and eye
bounding guides restrict material selection; the sword guide uses its connected native component
so scattered native antialiasing indices do not turn ribs bronze. Mask edges come from enhanced art.
Native palette 818 crushes dark bones and clamps highlights, requiring a nonlinear luminance LUT;
a single RGB multiplier was insufficient. Materials.py fits usage-weighted native palette curves.
Base palette bypass is exact; variants preserve sprite alpha and zero-mask pixels.

Final checks pass: source/palette/provenance hashes, unclipped raw cells, crop/atlas reconstruction,
mask weight sum, native playback contracts and variant protection. Magenta candidates are zero at
cleaned, exported and atlas-extracted stages. Light/dark edge inspection found no remaining matte halo.
Fine bone anatomy and skull shading are clearer/rounder than native pixels. The unusual skull-like
shape among collapsed ribs in skedyd0 also exists in the native source and is deliberately preserved.
No gameplay installation was performed. Earlier extraction comparison sheets precede the final grade;
all_base_dark, standing_variants, ordered_actions, edge_current and viewer captures show final output.

Rebuild from retained raw checkpoints (repository root):
```
python3 level_generation/creatures/mm6_ske/process.py
python3 level_generation/creatures/mm6_ske/package.py
python3 level_generation/creatures/mm6_peasants/build_viewer.py ske
```
Use the family package wrapper to declare the nonlinear LUT contract and correct shipping size.
A rebuild resets visual acceptance; inspect changed output before accepting again.
