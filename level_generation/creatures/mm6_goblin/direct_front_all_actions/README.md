# All front-view goblin actions in one AI generation

One built-in image-generation call enhanced a sheet of **31 original front-view poses**, with one action per row.
The accepted earlier six-frame attack sheet was the second input for identity/material quality; the native combined
sheet remained the pose/layout authority. No Blender model or paid API fallback was used.

- [Raw generated sheet](enhanced_front_all_actions_v1.png), **1272×1237 RGB** on magenta.
- [Cleaned RGBA at unchanged generated coordinates](enhanced_front_all_actions_v1_rgba.png).
- [Uniform-cell transparent sheet](all_actions_front_rgba.png), **1440×1680**, six 240×240 cells per row.
- [Labeled overview](previews/all_actions_labeled.png).
- [Original input with row labels](original_labeled.png) and [exact generation prompt](prompt_v1.txt).
- [Source inventory](source_manifest.json), [output/crop/timing manifest](output_manifest.json),
  [individual frames](frames_rgba/) and [separate action strips](action_sheets/).

| Row | Action | Poses | Exact source duration | Comparison playback |
| --- | --- | ---: | ---: | --- |
| 1 | Attack | 6 | 0.75 s | [GIF](previews/attack.gif) |
| 2 | Death | 5 | 0.625 s | [GIF](previews/death.gif) |
| 3 | Walk | 6 | 0.75 s | [GIF](previews/walk.gif) |
| 4 | Hit | 6 | 0.75 s | [GIF](previews/hit.gif) |
| 5 | Fidget | 6 | 0.75 s | [GIF](previews/fidget.gif) |
| 6 | Standing | 1 | Static/held; native raw length 2 | [GIF](previews/standing.gif) |
| 7 | Corpse | 1 | Held; native raw length 2 | [GIF](previews/corpse.gif) |

Blank cells are intentional: Death column 6, Standing/Corpse columns 2–6. Do not invent poses to fill them.
GIFs alternate 120/130 ms for six-frame actions. Death rounds to 630 ms; single held poses use 500 ms for review.
The manifest retains 125 ms source frame timing and remains the timing authority.

## Findings from this attempt

The generator preserved seven action rows, their pose counts, the blank cells, crouch-to-prone death progression,
walking phases and shielding hit motion. Full-sheet review plus native/death/walk/hit comparisons show recognizable
source actions and coherent overall goblin identity. Fine equipment and facial details still vary; this is an
experiment for driver review, not a fully calibrated replacement for native actor assets.

The larger sheet divides the returned image among 31 poses. The tool returned 1272×1237 rather than the requested
2880×2800. Upright figures are roughly 160–180 pixels tall, versus roughly 390 pixels in the earlier attack-only
result. New interpreted detail is present, but this is NOT a higher-pixel-resolution replacement of the native
355×289 canvases. No deterministic enlargement is presented as additional generated detail. For detailed production
art, separate action sheets currently offer more pixels per figure; the all-action sheet is useful for testing
cross-action consistency and as a shared reference. This does not establish a universal tool resolution ceiling.

The generator also redistributed the row spacing instead of maintaining the original equal grid. The raw output is
preserved. `package_preview.py` uses measured empty seams and explicit extraction rectangles, then translates each
ENTIRE action row to a shared baseline at y=224 in 240×240 cells. It performs no per-pose resizing or recentering.
Prone figures remain small and horizontal near the floor. This row normalization is post-processing, not evidence
that the generator honored exact original pivots. Source/AI scale and slight pose drift remain visible in comparisons.
The generated art is somewhat larger relative to its cells than the source; do not infer runtime scale from it.

The shared [deterministic cleanup](../direct_ai_attack/clean_edges.py) removes the estimated magenta contribution
before RGBA packaging. It retains actual alpha and avoids another AI redraw. As previously calibrated, this is an
estimated matte; thin details and colored edge bias still need inspection at the final display size. All 31 output
cells are nonempty/unclipped and have real alpha. All 31 source hashes remain unchanged. No live sprite IDs, engine
assets, palette replacements or gameplay definitions were changed.

## Reproduce and continue

`prepare_reference.py` creates the native sheet and source manifest. The selected output came from the built-in
tool with `prompt_v1.txt` and two explicit inputs: `original_front_all_actions.png` and
`../direct_ai_attack/attack_restored_v1.png`. `package_preview.py` creates the cleaned sheets and comparisons;
its measured seams/baselines apply to this output revision only and must be reinspected for another generation.

For another angle, inventory which native action views exist first. Front-only native groups do not supply genuine
side/back poses; mark newly inferred views separately. Use the accepted character sheet as a style reference and
the actual new angle's native frames as the pose authority. Keep one action per row and preserve source-specific
counts and intentionally empty cells. See [direct restoration workflow](../../DIRECT_SPRITE_WORKFLOW.md) for the overall
procedure.
