# Jackalman review and reproduction

Accepted 59 native unique images, including unused jak1fib0; all 58 referenced sources,
five stored directions, eight view aliases, original action sequences, timings, scale and anchoring retained.
All raw batches, ordered all-frame contact, mask overlays, three standing variants and enlarged
light/dark contour contact reviewed. Offline viewer samples cover mirrored walk view 6 / palette 758 /
frame 4 and death view 0 / palette 759 / frame 3, alongside their native reference poses.
Sequence/paused-viewer checks are not a real-GPU performance measurement.

Corrected walk view 1 after the first image incorrectly used the standing vertical staff.
The accepted correction uses native walk poses and enhanced side walk identity; exact references,
prompts and the rejected output are retained in generation.json.
Fixed RGB gain 0.86 brings generated blue, gold and chest highlights closer to native tonal weight.
R8 cloth coverage uses enhanced blue connected regions, excluding native-invariant cyan staff bands.
Gold, skin and silver remain unchanged in purple/red variants. Native palette fits are fixed per family.
All-frame alpha/crop/atlas/provenance and native sequence checks pass; residual magenta candidates
above 16 are zero in cleaned, exported and atlas-extracted frames. The inspected edges are clean.
The silver hook and pleated skirt detail are interpretations of low-resolution native artwork;
original anatomy, pose and broad tonal appearance remain recognizable.

Rebuild from repository root:
```
python3 level_generation/creatures/mm6_jak1/process.py
python3 level_generation/creatures/mm6_peasants/package_family.py jak1
python3 level_generation/creatures/mm6_peasants/build_viewer.py jak1
```
Extraction comparison sheets precede final grading; packaged contacts and viewer include it.
Rebuilding resets visual acceptance. Stage only; no gameplay installation or originals modified.
