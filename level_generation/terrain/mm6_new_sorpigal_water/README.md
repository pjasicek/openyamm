# New Sorpigal water and shoreline — v1 candidate

[Visual comparison and animation review](review.html)

27 runtime PNGs at 256×256: 12 dirt/shore overlays, `6wtrtyl` static fallback, and 14 `6hdwtr000`–`013`
animation frames. The water master was created with built-in imagegen. Exact prompts and generation provenance
are retained in `prompts/` and `raw/provenance.json`.

**All shoreline earth comes from the accepted dirt master**, specifically the wrapping derivative in
`../mm6_new_sorpigal_transitions/material_seams/connected_v2/dirt.png`. No independently generated earth
is used. A narrow contact shade (up to18% at the water edge) is baked into that material. The queued damp-earth
experiment was discarded after the user's clarification; its prompt is retained only as rejected history.
The land pack and all four accepted masters are unchanged.

The 12 native shoreline alpha masks supply the shapes. The central384×384 coverage remains unchanged at512px;
small shared-edge repairs affect 0.24–1.25% of each tile's coverage to align native edge crossings.
Subpixel alpha softening is baked into PNG transparency. The engine composites these over each water frame.

One water master supplies all14 frames using spatially periodic, temporally closed displacement. This avoids
independent-frame painting changes. Native timing remains15 ticks/frame at128 ticks/second: a1.640625-second
loop. Existing rendering and animation code is unchanged. The water remains intentionally stylized blue ripple
art; it is not a photorealistic water effect. Repeated detail remains possible with a single master.

## Validation

- 131 water-related unique map joins pass on every frame at256px and512px. All14 pure-water frames wrap.
- The last-to-first change is0.988 times the mean adjacent-frame change; no exceptional closing jump.
- Frame-wide mean RGB brightness varies by less than0.05/255 over the cycle.
- Native pool, island, actual coastline and close oblique views inspected. Island pad outer edges are artificial
  fixture boundaries and are excluded; the internal island shoreline is the test.
- 28 native animation samples span22.8 seconds: water changes while stationary land stays stable. These samples
  and frame sheets do not certify full-frame-rate shimmer stability or GPU performance.
- Initial captures under `captures/v1/` and `captures/original/` are rejected: the current engine required a Fly
  effect or debug override and the camera fell. `captures/v1_flight/` contains the valid fixed-flight captures.
  Debug flight is enabled only in the isolated review stages, not in the user's normal playtest by this installer.

## Map layout

Six source vertices have contradictory material choices. An optional corrected map is in `map_correction/`:
12 terrain bytes changed, everything else preserved. This supersedes the earlier land-only seven-cell patch,
which could not account for shoreline corners. `prepare_map_correction.py` minimizes changes within small
neighbourhoods of the conflicts and validates all material corners. It does not modify the production map.
The review captures use this corrected map in both original-water and new-water modes.

## Run / rebuild

The enhanced sprite-and-texture playtest receives this candidate and the corrected map with:

```sh
python3 level_generation/terrain/mm6_new_sorpigal_water/install_playtest.py --with-map-correction
./level_generation/creatures/mm6_peasants/play.sh enhanced
```

Choose Load Game and the supplied New_Sorpigal_Start save. Existing saves, sprites and building textures are
preserved. The original mode is untouched. The old map is backed up under the playtest's `seed/` directory.
Restart an already running game to reload assets. `/tmp` stages are development snapshots, not portable installs.

Mechanical rebuild (no AI calls):

```sh
python3 level_generation/terrain/mm6_new_sorpigal_water/prepare_map_correction.py
python3 level_generation/terrain/mm6_new_sorpigal_water/build_water.py
python3 level_generation/terrain/mm6_new_sorpigal_water/check_authoring.py
python3 level_generation/terrain/mm6_new_sorpigal_water/build_fixture.py
python3 level_generation/terrain/mm6_new_sorpigal_water/prepare_trials.py
```

Python dependencies: Pillow, NumPy, SciPy, PyYAML. `build_fixture.py` uses the existing editor map writer.
Native captures use the existing `capture_gameplay.py` helper and the frozen executable in
`/tmp/openyamm-sorpigal-water-review/openyamm`. Saved poses and capture actions are in `captures/`.
`check_animation.py` checks the28 valid native samples and builds their preview. The offline loop preview runs
at approximately native speed; native sampled playback preserves screenshot spacing and is not a smooth video.
