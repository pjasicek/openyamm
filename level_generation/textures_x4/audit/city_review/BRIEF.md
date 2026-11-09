# First-pass review of MM9 city x4 candidates (2026-11-01)

You review generated x4 surface textures against the MM9 originals and write recommendations. You do not accept or
retry anything yourself: the texture session reads your file, checks the sheets and acts.

## Sheets
`python3 audit/city_review/rv.py <job>` (from `level_generation/textures_x4`) writes
`audit/city_review/sheets/rv_<job tail>_<k>.png`, 6 textures per sheet, latest candidate of each unaccepted texture.
Each row: label `<name>_v<N> [flags]`, then five panels:
1. the native (original, 1x, enlarged; blocky and blurry is normal),
2. the x4 candidate,
3. the candidate tiled 2x2 (how it repeats on a wall),
4. a 1:1 crop centred on the left/right wrap joint (the texture's right edge meeting its own left edge, in the middle),
5. a 1:1 crop centred on the top/bottom wrap joint (bottom edge meeting its own top edge, in the middle).
Transparent areas of cut-out textures (grilles, windows, banners) show black.

## The user's blocking requirements
1. No seams in tiled surfaces: in panels 3-5, no visible line, step in brightness, or broken pattern at the joints,
   unless the native itself has that line at its edge (a trim strip, a frame, a border that is part of the picture:
   check panel 1).
2. No shading difference: overall brightness, colour and saturation close to the native (no blue cast on a brown
   material, no washed-out or over-dark result).
3. Doors: a double door must keep the native's layout exactly (leaf joint at the same column, symmetric where the
   native is symmetric).

## Also reject when
- the layout differs from the native (features moved, missing, added, wrong count of planks/stones/panels/windows),
- lettering differs (signs must read exactly as in the native),
- the material is wrong (stone became wood, a rug became stone),
- a cut-out silhouette differs (bars moved, shape changed, things painted where the native is transparent),
- obvious AI artefacts: smeared areas, doubled features, a frame/border the native does not have, text noise.
Do not reject for: more detail, sharper texture, slightly different grain or stone shapes inside the same layout.

## Flags (from the automatic checks)
seam, edge, rim, line, layout, colour, shift, alpha, brightness, traced. A flagged candidate may still be
recommended ACCEPT when the sheet shows the flag is the native's own joint/border or a false alarm: say why.
Never recommend ACCEPT for `traced`.

## Output
Write `audit/city_review/<job>.txt`, one line per texture in the sheets:
- `<name> ACCEPT` (optionally `# reason` when flagged),
- `<name> RETRY roll=<u|v|uv|-> note="<one sentence telling the image model what to fix>" # reason`
  (roll=u/v/uv when the problem is a seam on that axis; the note names the concrete fix, e.g. "keep the three
  windows evenly spaced as in the native", "even brightness from top to bottom").
Then report back: per job, the count of ACCEPT and RETRY, and the RETRY lines.

## Rules
Only read-only commands plus `rv.py` and writing your `.txt` files. Never run `tex.py accept`, `retry`, `gen`,
`check`, `next`, `install`, `inventory`, never git.
