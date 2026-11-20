# MM7 Treant — repaired native restoration

All **33 native unique frames** are staged: one resting disguise, 18 attack poses, seven reaction poses,
six breakup poses and one stump. **31 insufficient frames were regenerated; two valid identity frames retain
unchanged transforms.** Twelve selected sheets (11 new and one retained) come from 21 preserved raw outputs.
Minimum actual generated detail is **2.639851×**, measured before the **2×** runtime export.

Open [viewer.html](viewer.html) locally for native/restored playback. Descriptor scale is included in the viewer;
`zoom=0.4` displays actual 2× pixels because native Treant scale is 5. Example:
`viewer.html?action=attack&view=7&palette=530&zoom=0.4&background=light`.

Descriptors 451–453 share palette 530 and the single native Image1 view in every direction, without mirrors.
Native logical canvas 256×256, pivot (128,256), scale 5, 62.5 ms timing, action reuse and flags remain intact.
The death timeline uses da–dd; unused de/df artwork is exported without adding invented playback steps.

Built-in imagegen restored the dark brown leafless trunk, ragged roots, winding bare branches, small green eyes
and pale uneven teeth from native pose grids and the retained identity reference. Exact submitted prompts,
raw PNGs, hashes, reference roles and selected versions are preserved. Fine bark and twig details interpret
native pixels; they are not recovered historical high-resolution originals.

All 11 selected replacement sheets supply genuine RGBA transparency. Preserve their actual alpha; no painted
checkerboards are accepted. Brown backdrop RGB in two raw previews is invisible under alpha and is not keyed.
The processor removes only disconnected components with maximum opacity 1/255. One demonstrated attached
1/255 gutter column at x=1023 in death_corpse_detail_margin_2_v1 is cleared; stronger branch coverage and the
remaining soft edge are retained. Three attack sheets with inadequate gutters were regenerated. The clipped
four-pose breakup sheet was replaced by two portrait pairs.

Complete breakup poses, including detached wood fragments, are isolated using documented ownership rectangles.
Portrait row boundaries move through verified empty space at y=864 and y=950. The first breakup sheet uses
reviewed four-cell ownership and a shared native calibration to correct the returned canvas's scale mismatch.
Other new sheets use connected-pose extraction and one common native calibration per sheet. Native baseline
translations preserve anchoring. Retained standing transforms are unchanged; registration adds a neutral
calibration field. No per-pose equal-bounds fitting, limb warping or anisotropic stretching is used.

Tone remains a fixed 0.75 RGB multiplier. The original opaque standing sheet keeps its established matte
extraction. Local process.py preserves alpha, applies the documented tone and edge processing, and uses
premultiplied Lanczos for export. Every mask is zero R8 because all native descriptors share one identical
palette; palette 530 is an exact base bypass. No extra variant artwork was generated.

The 2048×3101 RGBA8 base atlas and matching R8 mask use **31,754,240 bytes (30.28 MiB)** decoded, including
packing: 25,403,392 base bytes and 6,350,848 mask bytes. Preview images are excluded from runtime memory.
Base/mask crop origins and atlas rectangles match exactly.

Full native coverage and source hashes, actual sampling, raw boundaries, crop reconstruction, atlas extraction,
mask weights, exact base bypass, alpha, timing and flags pass [validation.json](validation.json).
Every pose was visually reviewed, with ordered attack/reaction/death contacts, actual 2× crispness,
light/dark edges and final playing attack / held breakup browser comparisons. The final edge audit reports
zero residual candidates above 32/255. [Acceptance](review/acceptance.json) pins the final reviewed artifacts.

Reproduce from repository root, preserving raw checkpoints:

```sh
python3 level_generation/creatures/mm7_m479/process.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m479
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m479
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m479
python3 level_generation/creatures/mm7_m479/review_repair.py
```

Do not rerun preparation/rebatching on resume. All work remains under this staging project. No native source
or gameplay installation was changed.
