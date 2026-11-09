# Focused UI review repairs

[report.json](report.json) binds 37 technical candidates to their native sources and input art. None is approved.

- `ira-3_08` and `ira-3_09` were separately edited with imagegen using their native frames, restored frame 07 and
  the adjacent repaired frame as references. The edit kept the full opaque wooden panel instead of the black field
  in the earlier return. `build.py` scales each retained 1254×1254 master to the frozen 160×160 canvas.
- `newglas1` through `newglas6` were edited as a 2×3 transparent imagegen sheet from all six native frames.
  `fit_newglas.py` crops each alpha-isolated cell and fits it to the native foreground bounds. The retained sheet
  provides substantially more than 2× subject sampling, without a cyan backing panel.
- `clean_context.py` uses the established spatial magenta-matte unmixing procedure on 27 pending context/resume/
  interact controls that still had an opaque `#FF00FF` field. It fits each cleaned foreground to its native bounds
  with premultiplied-alpha resizing. The source controls contain no intended magenta material.
- `clean_cyan.py` applies the same key-unmixing geometry to the known cyan backgrounds of `6pending` and `wizeye`,
  while preserving pre-existing transparent pixels and native placement. The identical `7pending` target can reuse
  the repaired `6pending` candidate.

The magenta and cyan controls, all six small hourglasses and both opaque hourglass frames were inspected as light and
dark composites at final size. The earlier variants remain listed as alternatives in the browser for comparison.
