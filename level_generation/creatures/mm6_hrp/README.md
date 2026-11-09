# MM6 Harpy restoration

Accepted complete: 48/48 native unique images, three palettes, all actions and five stored flight views/mirrors. Staged only.

Open [review.html](review.html) for the offline native/restored viewer. [review_notes.md](review_notes.md) records visual checks and limitations; manifest.json and validation.json describe the 2x atlas/mask export.

Reproduce offline: `python3 level_generation/creatures/mm6_hrp/process.py`, then `python3 level_generation/creatures/mm6_hrp/package.py`, then `python3 level_generation/creatures/mm6_peasants/build_viewer.py hrp`. Repackaging clears visual acceptance and requires re-review. Native inputs, exact prompts, raw output/provenance, rejected identity experiments and processing settings are preserved.
