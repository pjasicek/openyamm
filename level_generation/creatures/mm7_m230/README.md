# MM7 Crusader — repaired native restoration

The staged repair covers all **114 native unique frames**, all actions and five stored views with the original
eight-view mirror aliases. **69 frames were regenerated; 45 valid frames retain their previous registration exactly.**
The active package selects 25 sheets (8 retained and 17 replacement) from 42 preserved raw outputs.
All frames provide at least **2.002435× actual generated detail**; replacements provide at least **2.320414×**.
The export is 2×. These measurements come from raw-to-native registration, before export resampling.

This repair is staged only. Original art and the historical custom-crusader 901–903 gameplay installation were
not changed. That older installation is documented separately in [ENGINE_INTEGRATION.md](ENGINE_INTEGRATION.md).

Open [review.html](review.html) locally; it embeds the manifest and supports native/restored playback, palettes,
mirrors, masks and placement. For actual 2× pixels use `zoom=2`; for a light background use `background=%23eeeeee`.
For example: `review.html?action=walk&view=7&variant=55&frame=4&paused=1&zoom=2&background=%23eeeeee`.

## Native coverage

| Action | Native artwork and playback |
| --- | --- |
| Standing | One pose × five views |
| Attack | Six poses × five views; shared by melee/ranged descriptor slots |
| Hit | Six poses × five views |
| Walk | Eight poses × five views |
| Fidget | Four unique front poses; a,b,c,d,c,b, with d held 375 ms |
| Death | Front hit-a, hit-b, death-a,b,c,d |
| Corpse | One front pose |

Ordinary frames last 125 ms. Image1 actions reuse one native view; directions 5/6/7 mirror stored 3/2/1 otherwise.
Groups m231/m232/m233 share m230 pixels and use palettes 54/55/233. Native logical canvas 256×256, center pivot
(128,128), Center flag and scale 0.899994 are preserved. Physical crop origins retain the original anchoring.

## Artwork, alpha and registration

Built-in imagegen supplied the replacement artwork, using native pose grids and the accepted standing identity.
All replacement sheets have genuine RGBA transparency. No painted checkerboard is accepted. Opaque historical
magenta sheets keep their established extraction. Raw outputs and exact submitted prompts are immutable checkpoints.

Real alpha bypasses keying. Only disconnected components with maximum opacity 1/255 are removed. Two reviewed
attached gutter tails also required local cleanup: alpha exactly 1 below y=1018 in hit_3_detail_0_v1 and below y=1248
in walk_0_detail_0_v1. Full stronger foreground and connected soft edges are retained. Walking sheets with inadequate
margins were regenerated; the rear walk and last front-oblique poses use four-pose layouts with increased padding.

Registration uses common batch scale and native lower-body/baseline landmarks. Ordered walk review demonstrated
row-wise generator zoom drift in walk_0_detail_0, walk_1_detail_0 and walk_3_detail_0. Each three-pose row now uses
one shared native/raw median scale, preserving native differences within the row. Falling/prone poses use separate
height or width measurements. No limb warping or per-pose equal-bounds fitting is used.

Tone remains 1.0. The user selected [this preserved sheet](raw/walk_1_detail_1_v1.png) as a good crispness reference.
[Actual 2× walking pixels](review/crispness_runtime_0.png) and [attack/recoil pixels](review/crispness_runtime_1.png)
were inspected separately from the sampling gate. Recoil shading is smoother, with clearly resolved visor and armor
edges. Microdetails, heraldry and plume/weapon contours remain interpretations of the original low-resolution art.

## Variants and export

A soft R8 mask covers green cloth, plume and green heraldic ink. White heraldry, steel, gold and leather are protected.
In normalized sRGB, `n=min(R,B)`, `c=max(0,G-n)`, target=`n+c*ramp`; mix through mask coverage. Palette 54 is an exact
base bypass. Blue 55 uses `[0.20,0.18,1.00]`, red 233 uses `[1.00,0.12,0.27]`. Fixed parameters preserve shading without
per-frame histogram normalization or separate variant generation.

Base and masks share transforms, crops and atlas rectangles. Color/alpha resizing uses premultiplied Lanczos;
the retained green-base contour correction limits magenta excess to 10/255. Crop padding is four physical pixels,
with matching three-pixel transparent RGB/mask extrusion. Atlas pages have no generated mipmaps.

Decoded shared memory including packing is **64,038,250 bytes (61.07 MiB)**: 51,230,600 RGBA8 base bytes and
12,807,650 R8 mask bytes. Baked palette previews are review assets and are excluded from shared runtime memory.

## Validation and reproduction

All replacement palette appearances and masks were visually reviewed, together with ordered walk, attack, hit and
collapse contacts, final light/dark edges, and browser comparisons of blue mirrored walk, red hit and green collapse.
Source hashes, complete frame coverage, sampling, unclipped extraction, crop reconstruction, exact atlas extraction,
mask placement, unchanged variant alpha, protected zero-mask RGB and exact base bypass pass. Final contour audit has
zero candidates above 16/255 alpha-weighted magenta excess; visual review confirms no visible matte fringe.
The two focused extraction/resize regression tests pass. [Acceptance](review/acceptance.json) pins current artifacts.

From the repository root:

```sh
python3 level_generation/creatures/mm7_m230/process.py
python3 level_generation/creatures/mm7_m230/package.py
python3 level_generation/creatures/mm7_m230/build_viewer.py
python3 level_generation/creatures/mm7_m230/review_repair.py
python3 level_generation/creatures/mm7_m230/test_edge_cleanup.py
```

Do not rerun preparation on resume. `generation.json` selects immutable raw outputs and preserves their exact prompt
and reference hashes; `generation_provenance.json` retains the historical requests. `batches.json`,
`detail_rebatch_plan.json`, `registration.json` and `processing_settings.json` record layout and processing decisions.
Pre-repair and intermediate layout/scale checkpoints remain under `checkpoints/`. The local scripts are Crusader-specific.
