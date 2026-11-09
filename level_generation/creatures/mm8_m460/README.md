# MM8 Human Male Cleric restoration

Completed staged restoration of all 160 native unique poses, palettes 461/462/463 and actors 46/47/48.
Open `viewer.html` locally to compare native art, 2× restored art, variants and masks. Nothing is installed
into gameplay. Native assets are unchanged.

The user identified pixelated rendering in identity V1. V2 redraws face, skin, hair and fabric with finer
continuous detail at the same 1335×1178 dimensions. `review/identity_quality_comparison.png` preserves
the comparison. V2 is the frozen reference for all actions; V1 remains rejected provenance. Actual
generated sampling is 2.505310–4.763701 pixels per native pixel; export resolution is 2×. Raster size and
visual detail were reviewed separately, as now required by the pipeline.

The delivery contains 40 attack, 40 walk, 25 hit, 25 fidget, 20 falling, five standing and five corpse poses.
Twenty falling/corpse poses in stored views 1–4 are unused by native actor timelines but fully restored
and selectable through the viewer's stored-pose control. Native death uses front hit/falling frames and
native corpse uses xa0 in every direction. Metadata preserves these bindings, native timing, mirror
reuse, 256×256 logical dimensions and bottom-center anchoring without inventing new playback.

Thirty-four compact jobs use sequence-wide native crops and shared isotropic calibration, with eight
overlap checkpoints connecting split actions. There are 37 retained raw images, including rejected
identity V1, attack a_v3_1 V1 with an unfinished outer spark edge, and d_v4 V1 with an invented rear
front-panel motif. Accepted d_v4 V2 preserves the plain rear robe and the native folded-foot fall pose.
Exact prompts, reference hashes, tool records, version selection and calibration live in
`compact_jobs.json`, `prompts/`, `raw/`, `references/` and `checkpoints/`.

Processing uses supplied PNG alpha. No painted checkerboard is accepted. `process_compact.py` maps
each job with a shared isotropic scale and row translation, followed by integer translations to native
lower-body contacts; falling poses use the largest body component. A padded 1024-pixel working canvas
prevents intermediate clipping before the final 576-pixel aligned 2× canvas (logical origin −32,−32).
Exact inverse translations and final crop reconstruction are checked. Recorded near-zero alpha at
some raw outer edges is retained. Only six explicitly reviewed detached alpha-one pixels in three
frames are removed after alignment; before images and masks are retained in `checkpoints/residue/`.
The frozen whole-art tone multiplier is 0.8888435198496263.

Variants are deterministic: base 461 bypasses recoloring exactly; palette 462 uses brown hair/blue
staff and 463 blond hair/red staff. RGB8 masks use red for enhanced green staff coverage and green for
enhanced neutral-dark hair coverage, with blue zero. Native palette differences guide regions; native
silhouette masks are not resized. Seven reviewed hair component exceptions are pinned to enhanced
master hashes in `hair_component_extensions.json`. Rear falling/corpse dd4/xa4 also use boundaries
traced around actual enhanced hair to exclude adjoining robe shadows. Rejected unbounded growth
examples are preserved. `materials.py` and `material_settings.json` define exact sample deltas, ramps
and coverage. Skin, russet cloth, front red panel and gold/ivory fittings remain protected.

Eight matching RGBA8 base/RGB8 mask atlas pages occupy 183,276,800 decoded bytes (174.786 MiB), including
packing. Tight base/mask rectangles occupy 141,601,621 bytes. Base and mask rectangles match exactly;
exports retain trim offsets, three-pixel hidden-color/coverage bleed, four-pixel trim padding and
16-pixel aligned gutters. Renderer installation and the selective runtime shader are separate work;
the offline viewer uses deterministic baked variant previews.

Validation covers every native source and binding, 160 exact transformation replays, 480 variant
images, unchanged alpha/protected colors, native contact error at most half a physical pixel, exact
atlas extraction and crop reconstruction, and automatic cleaned/aligned/atlas contour checks.
Visual review covers all compact native/palette/mask contacts, all 30 action/view sequences, eight
overlap comparisons, magnified light/dark worst edges and attack/mirrored-walk/corpse viewer captures.
Chrome checks decode all 160 stored poses and 480 variants and inspect 192 actor/palette/action/view
tracks at 1008 timing boundaries. Fine details necessarily interpret low-resolution originals.

For a revision, preserve accepted raw art and checkpoints. Regenerate only a demonstrated artwork
fault using the built-in imagegen skill, or revise an enhanced material mask deterministically. Update
any affected master-pinned hair settings after review. Reprocess only affected jobs, then rebuild
`package.py`, contacts, `sequence_contacts.py`, `overlap_contacts.py` and `review_evidence.py`. Inspect
changed contacts and sequence joins; renew immutable acceptance using `accept_review.py`. Run
`audit_transform_extent.py`, `verify_transform.py`, `verify_partial.py --final` and `browser_checks.py`.
Renew `review/decision.json` evidence hashes only after actual review, run `finalize.py`, then refresh
`../remaining_inventory.json` using `../inventory_remaining.py` and check full coverage and issues.
