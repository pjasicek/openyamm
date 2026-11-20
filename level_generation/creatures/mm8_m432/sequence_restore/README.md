# Complete Dark Elf Warrior processing and resume

The authoritative delivery is `../complete/`; root `../manifest.json` references those same pages.
`../complete/selection.json` identifies each selected master. It reuses 47 earlier detail restorations and
5 front-attack trial frames, with 108 frames from this compact sequence queue (including 3 attack repairs).
The original checkpoints remain in `../detail_upgrade/` and `../front_attack_grid_trial/`.

`jobs.json` preserves source order, common native crop, measured output dimensions, extraction exceptions,
frozen isotropic calibration and integer contact translations. `generation_history.json` records all 23
built-in imagegen outputs, exact prompts, input references and hashes, including rejected repair versions.
`raw/`, `prompts/`, `references/`, registered masters and review contacts are retained.

Grids use one action/view common crop including sword extremes and six native pixels of padding. Five-pose
sequences use 3×2 cells; narrow eight-pose walk cycles fit 4×2 cells above the actual 2× sampling gate.
Exposed tips crossing a nominal cell seam are retained by explicit cuts through empty space, preserving
their nominal cell coordinates. No per-frame silhouette fitting or interpolated resolution claims are used.

`tone_settings.json` freezes a pooled native/enhanced luminance curve, with strength 0.8 and enhanced RGB
chromaticity preserved. It replaces spatial native color transfer on new sequence artwork and the retained
front-attack frames: that method demonstrably placed green cloth shading on a displaced face/shoulder.
The earlier accepted detail artwork retains its reviewed grading. Masks are classified on enhanced artwork
and constrained by connected enhanced green/teal support, with no resized native mask transfer.

For a targeted revision, preserve the accepted files and create a new raw version. Update only the relevant
job selection/prompt/references. From the repository root:

```sh
python3 level_generation/creatures/mm8_m432/sequence_restore/process_sequence.py JOB_KEY
python3 level_generation/creatures/mm8_m432/sequence_restore/assemble.py --frames FRAME_NAME ...
python3 level_generation/creatures/mm8_m432/sequence_restore/verify_delivery.py
python3 level_generation/creatures/mm8_m432/complete/browser_checks.py
```

Omit `--frames` for a full assembly. Targeted assembly rejects changed selections or source hashes outside
the requested frames; use a full assembly after changing grading/mask algorithms or shared settings.
`retone.py` reapplies the frozen curve without resampling or changing anchors. `process_sequence.py` uses
the frozen calibration on reruns; intentionally remove it only for a newly reviewed sheet registration.
Front attack uses the mean of the two planted foot centers and sole baseline. Rear `dd4/xa4` use the recorded
heel region for Y; other poses use their individual native lower-leg/body contact, preserving native motion.

Inspect changed native/base/variant/mask contacts and the viewer, then renew `../complete/review/decision.json`
with hashes of the actual reviewed artifacts. `finalize.py` verifies that decision and all source/provenance
records before publishing validation and acceptance. Finally refresh the repository inventory:

```sh
python3 level_generation/creatures/mm8_m432/sequence_restore/finalize.py
python3 level_generation/creatures/inventory_remaining.py
```

Python/Pillow/NumPy/SciPy perform offline processing. Chrome is needed only for the offline viewer checks.
No built-in generation is necessary to reproduce the selected export. Engine installation is not performed.
