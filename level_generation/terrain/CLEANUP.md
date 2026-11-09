# Terrain workspace cleanup — 2026-09-10

User requested removal of unneeded terrain restoration/upscaling data while retaining potentially useful terrain sources. Removed **8.873 GiB**: 5,310 files and 59 obsolete isolated MM8 review stages. Exact paths, original hashes and retained-output verification are in [CLEANUP_REPORT.json](CLEANUP_REPORT.json).

Removed raw animation screenshot sequences, unreferenced diagnostic/comparison renders, historical logs, Python caches, and superseded ESRGAN terrain image outputs under `tools/upscaling/`. Compact animated WebP reviews, human-linked comparison images and direct acceptance evidence were retained. Some historical reports still record hashes of deleted raw animation frames; these are provenance records, not claims that every historical capture remains on disk. Re-run the relevant capture script to regenerate full raw sequences. Old rejected-version gallery pages may lack unreferenced diagnostics.

Retained:

- Complete accepted MM6 (134), MM7 (116) and MM8 (239) runtime exports, their manifests and packaged deliverables.
- Installed development textures, including MM8 `assets_dev/worlds/mm8/textures_v2`, unchanged.
- Original references, generated source art, master materials, masks, floating-point coverage/shading fields, prompts, build scripts, fixture maps/saves, source hashes and lessons learned. Historical source versions remain where they may be dependencies or useful restoration references.
- Current review evidence and compact water/lava/tar animation reviews. MM8's accepted current road work is `mm8/roads/v13`; its material/coverage result was accepted by the user, with documented bend-pattern limitations.
- The frozen MM8 review executable and base/final review stages. The final retained diagonal stage is `/tmp/openyamm-mm8-terrain-review/diagonal_v13_width`; other diagonal/flat trial stages were deleted.
- The peasants enhanced playtest, original game assets, gameplay code, bmodel/sprite upscales, ESRGAN model weights, and upscaling recipes.

Verification after cleanup: 1,120 retained export/source/install files matched their pre-cleanup hashes. All three accepted terrain export manifests verify; MM8 installed-pack verification and the separate 239-file `textures_v2` installation audit also pass. The workspace remains ready for terrain maintenance; archived diagnostic sequences must be recaptured before rerunning analyses that explicitly consume those individual frames.
