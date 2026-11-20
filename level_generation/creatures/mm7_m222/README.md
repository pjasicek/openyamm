# MM7 Chain Fighter — accepted staged restoration

## Missing-frame restoration, 2026-09-22

All five missing falling/resting poses restored: `m222da0`, `m222db0`, `m222dc0`, `m222dd0`, `m222xa0`. Their measured master detail is **3.004161× native**.
Native base coverage is now **124/124**. Cleaned original-resolution generated masters are in `cleaned/`;
registered downsampled exports are in `aligned_2x/`. Raw sheets are in `raw/*missing_20260922.png`.
The `registration.json` scale maps raw/cleaned pixels to the 2× export: generated detail is `2 / scale`.
All new frames exceed 2× before export resizing. This delivery is staged base artwork; nothing was installed into gameplay.

The full package is now accepted: 124/124 frames, minimum generated detail 2.038555x, 2x aligned exports, enhanced cloth/hair masks and deterministic palettes223/224/225. Skin, steel, brass and leather remain protected. Final base/mask atlases and placement/animation metadata are in atlas/ and manifest.json; review/acceptance.json pins the completed artifacts. Decoded atlas memory is 85,041,152 bytes. All native/base poses, three identity variants, eight action/death variant examples and worst light/dark edges were reviewed. No frame falls below 2x; no temporary native fallback is used.

Reviewed every new pose against native in static contacts, independent anatomical placement markers,
100% master-detail crops and worst-edge light/dark composites. Applied one scale per sequence and reviewed
whole-frame horizontal translations to correct falling-pose drift. Vertical placement preserves each native baseline.
Residual spill above32 is zero on all new cleaned and aligned frames. Thin hands, sword tips, and supplied alpha
were inspected. Small reconstructed differences in foreshortening, facial detail or stone facets remain;
static contacts do not certify watched animation playback.

The historical five-frame increment is recorded in [review/missing_frames_20260922.json](review/missing_frames_20260922.json); final acceptance supersedes its pending mask/package status.
Compact review: [placement](review/missing_frames_20260922_placement.png),
[master detail](review/missing_frames_20260922_detail.png), [edges](review/missing_frames_20260922_edges.png).
All previously registered frames and cleaned/aligned/mask files match
`checkpoints/before_missing_frames_20260922/` exactly. Native sources and timing metadata are unchanged.

The first successful return already contained valid character alpha. Its apparent brown gradient is RGB in
fully transparent pixels and disappears when composited correctly. A subsequent unnecessary transparency-edit
request was output-moderated; its request ID and exact prompt remain recorded. The original successful return
was used. Processing clears only reviewed outer-border pixels with alpha at most 1/255; it preserves the silhouettes.

## Retained earlier work and resume

Reuse `sources.json`, `batches.json`, `generation.json`, `registration.json` and accepted pixels; do not reprepare.
The earlier sampling-repair acceptance remains at `review/sampling_repair_acceptance.json`, with raw/prompt
history and its previous README retained in checkpoints. All earlier undersized-frame repairs remain selected.
Keep af2/ag2/ah2 from `a_2_detail_2_intact`, ae2 from `a_2_detail_1` v2, and ag3/ah3 from `a_3_detail_1` v2.
The historical clipped ae2 remains excluded. Reuse the accepted package. To reproduce masks/variants and packing, run shared mm7_ambient/material_variants.py and mm7_m514/package.py with --project level_generation/creatures/mm7_m222. Final review used mm7_ambient/review_contacts.py and mm7_m230/edge_audit.py; a shared-template viewer.html is provided.
