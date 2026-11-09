# New Sorpigal dirt — original-fidelity candidate

The new directional transition pack is now a separate follow-up: [transition catalogue](transitions/review/index.html)
and [workflow / validation](transitions/README.md). Launch it with `./level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/play.sh transitions`.
The earlier `candidate` mode below remains the initial master-only comparison.

[Open the comparison](review/index.html): native/current/candidate material tiles and real game captures at the
user's supplied viewpoint. This is a separate study. The accepted dirt master, terrain package, development assets,
renderer, main settings, and peasants enhanced playtest were not edited.

## Finding from 1271 / 1272

The original dirt is made of relatively large, tightly interlocking clods with broad light/brown faces and dark
creases. The current v6 enhanced dirt is much finer-grained and darker, with more uniform small detail. In perspective
it loses the original's substantial, full surface appearance. This is not evidence of missing geometry.
The screenshots also differ in framing, party and grass coverage; those differences are not all a dirt-color issue.
The separate trial uses the same camera/party/weather for all versions to make the material comparison more useful.

## Candidate

- **2× runtime tile:** [runtime/6dirttyl.png](runtime/6dirttyl.png), 256×256 RGB; native tile is 128×128.
- **512×512 authoring master:** [generated/dirt_v2_512.png](generated/dirt_v2_512.png).
- [Native/current/candidate comparison](review/native_current_candidate.png).
- [2×2 repeat review](review/tiled_v2.png).
- [Generation and image metrics](manifest.json).

Built-in imagegen generated v1 directly from the native tile, using `1272.png` only as supporting in-game material
context. V1 recovered the large interlocking clods but was too orange and too contrasty. A targeted second imagegen
edit preserved the arrangement while matching native brown and shallower shading. Both raw outputs and exact prompts
are retained in `generated/` and [prompts/](prompts/). No CLI/API fallback, procedural repainting or color grading was
used. Lanczos reduction exports the tool output to 512px and then to 256px.

| Tile | Mean RGB | RGB standard deviation |
| --- | --- | --- |
| Native | 106.16, 65.41, 47.71 | 20.38, 17.83, 16.53 |
| Current enhanced master | 93.87, 56.67, 41.08 | 18.47, 14.91, 13.20 |
| Candidate v2 | 104.26, 65.00, 46.70 | 23.54, 19.53, 17.10 |

These metrics support the palette comparison; they do not establish visual equivalence. The candidate's clods are
more substantial than the current fine grain and its color is close to native, but its creases remain somewhat more
defined. The 2×2 sheet and game capture reveal repeat joins, including the conspicuous central foreground join at
this viewpoint. The original also has a visible join here; the candidate is not a finished seamless replacement.
A seam-only finishing pass and transition re-review should follow material acceptance. No production promotion was
performed, and the candidate does not claim pixel-identical recovery of the original clod layout.

## Independent playable comparison

The prepared snapshot is `/tmp/openyamm-sorpigal-dirt-fidelity/`. From the repository root:

```sh
./level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/play.sh candidate
./level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/play.sh current
./level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/play.sh original
```

Run one at a time and load **Terrain camera reference**. The file is `Dirt_View.oysav`, but the load menu displays
the title stored inside the save, not its filename. All modes use the same save, copied executable and enhanced non-terrain
assets. Original mode selects native terrain x1; current uses the existing enhanced terrain; candidate replaces only
the dirt material contribution in the copied enhanced terrain. The camera is (-9728, -11319, 161), yaw 89.227°,
pitch -9.626°. Saves are private to this trial. The original peasants `play.sh enhanced` remains unchanged.

For readable map context, `prepare_trial.py` exports 33 diagnostic dirt-bearing mixed tiles plus the dirt base using
the existing connected_v4 coverage and v5 baked boundary appearance. Fully foreground-owned pixels remain unchanged
at authoring resolution. No new grass, rock, cobbles, masks or boundary artwork was generated; these mixed exports are
only a preview of the new master. Existing enhanced grass coverage remains different from native, and the candidate
is not a newly accepted transition package. Original maps/events and large art folders retain the snapshot's shared
mounts, so this trial needs the repository available; it is not a portable distribution.

Recreate in a new destination if `/tmp` is cleared:

```sh
python3 level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/prepare_trial.py
xvfb-run -a -s '-screen 0 1600x1200x24' \
  python3 level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/capture_review.py
```

Preparation refuses an existing directory to protect trial saves. Use `--directory` for a new location and
`OPENYAMM_SORPIGAL_DIRT_TRIAL` with the launcher. The source snapshot can be selected with `--snapshot`.
The existing save-pose helper is used (or built if absent). No game renderer rebuild was needed for this study.

## Validation

- Visually inspected both user screenshots, native/current masters, both generated candidates, final runtime tile,
  repeated material sheet, and original/current/candidate game captures.
- Actual game captures at 1600×1200 use one frozen binary and identical native map hashes, retained in capture JSON.
  Ordinary actors and cloud animation can differ slightly; these are visual checks, not performance benchmarks.
- Verified the 256×256 RGB export and input/output SHA-256 records.
- Verified foreground ownership was preserved while exporting diagnostic dirt-bearing composites.
- All 4,042 private files in the peasants playtest matched the pre-study hashes after capture, including its binary,
  settings, saves, metadata and enhanced assets. The hash inventory is retained in `references/`.
- Checked the independent launch script's Bash syntax.
