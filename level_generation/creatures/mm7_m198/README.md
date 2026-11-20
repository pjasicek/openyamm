# MM7 Earth Elemental — staged native restoration

## Missing-frame restoration, 2026-09-22

The final 11 missing frames are restored: six front-right reaction/recovery poses (`m198na1`–`m198nf1`) and five
frontal idle/fidget poses (`m198fa0`–`m198fe0`). Their measured generated detail is **2.518×–2.545× native**.
Together with the retained earlier work, native base coverage is now **120/120**. The whole family passes the
actual-detail gate at **2.256× native or better**. Cleaned generated masters are in `cleaned/`; registered 2× exports
are in `aligned_2x/`; the final atlas and masks are in `atlas/`. Nothing was installed into gameplay.

The first built-in requests for these two batches were blocked at the output stage. The accepted retry explicitly
describes the source as pre-existing *Might and Magic VII* fantasy-game artwork and the task as faithful restoration,
not character design. Exact accepted prompts, reference hashes, raw outputs, and the earlier failed request records
remain in `generation.json` and `prompts/submitted/`.

Reviewed the new poses against native in static contacts, at full generated resolution, and on light/dark contour
backgrounds. Each sequence uses one common scale and preserves native baseline placement; no new per-frame placement
offsets were needed. Supplied transparency is retained. Residual spill above 32/255 is zero in cleaned and atlas art.
Small reconstructed differences in foreshortening, hand shape, facial detail, or individual stone facets remain;
static contacts do not certify watched animation playback.

Artifact-bound acceptance is in [review/acceptance.json](review/acceptance.json). Native/restored contacts are in
`review/all_comparison.png` and its smaller `comparison_*.png` slices; contour closeups are in
`review/edge_closeups.png`. Before final atlas packaging, all previously registered frames and cleaned/aligned files
reproduced byte-for-byte. Native sources, animation order, timing, flags, descriptor bindings, and palette metadata
remain unchanged.

## Retained earlier work and resume

Reuse `sources.json`, `batches.json`, `generation.json`, `registration.json` and accepted pixels; do not reprepare.
The earlier sampling-repair acceptance remains at `review/sampling_repair_acceptance.json`, with raw/prompt
history and its previous README retained in checkpoints. All earlier undersized-frame repairs remain selected.
There is one native appearance, palette504 from `assets_dev/worlds/mm8/textures/pal504.act`, hashed in sources.json.
The one native appearance uses a zero R8 mask and exact base bypass. The package is complete and accepted as staged
offline artwork; reuse it unless a demonstrated defect requires reopening a specific batch.
