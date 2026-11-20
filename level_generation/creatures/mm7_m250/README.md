# MM7 gog — validated, staged only

All 124 native frames are restored: five standing views, 40 walking, 40 attack/shoot,
30 recoil, four fidget, four collapse and one corpse frame. All three native palettes
are available in the self-contained [offline viewer](viewer.html). Native originals are unchanged.

The green palette 613 base derives blue 614 and red 615 through an enhanced R8 hide mask
and fixed ACT-derived RGB transforms. Ivory horns, teeth, claws, yellow eyes and the pale
chest highlights remain protected. All 372 frame/palette combinations and all mask overlays
were visually reviewed. The base preset is an exact bypass; variants preserve alpha.

The selected 33 sheets preserve 15 shared transition poses as reference-only overlaps;
each of the 124 native frames exports exactly once. The 42 retained built-in imagegen raw
outputs include the original eighteen sheets, 23 detail replacements and one targeted
collapse-foot correction. Exact submitted prompts, references, hashes, selected versions
and reviews are in generation.json. checkpoints/pre_detail_rebatch retains the earlier
batching and processing checkpoint. Superseded outputs are retained as references.

Actual generated sampling reaches at least 2 pixels per native pixel for every frame;
the measured minimum is 2.000608. This is measured from the uniform raw registration,
separately from 2x runtime export. See review/generated_detail_audit.json and
detail_rebatch_plan.json. Fine material detail is an interpreted restoration.

Native descriptor 274 walks at 62.5 ms/frame; 275 and 276 walk at 125 ms/frame.
Other actions use 125 ms. Scales approximately 0.65, 0.66 and 1.30, five stored views,
three mirror aliases, Image1 reuse, Center flags, logical 256x256 canvas and bottom
pivot are preserved. Death uses na0 da0 db0 dc0 dd0; corpse xa0; fidget fa0..fd0.
Ordered animation contacts and browser captures were reviewed, including mirrored blue
attack and red collapse. A demonstrated lowered-foot error in dd0 was corrected in
death_corpse_detail_0_v2; its raised foot now follows the native collapse pose.

Tone 0.80 is applied consistently. Demonstrated pink horn fringe was corrected locally
in RGB with material-edge repair and magenta-interior exclusion, preserving alpha.
All cleaned frames and atlas-extracted frames pass residual-spill audits; final light/dark
edge contacts were inspected. Crop reconstruction, atlas extraction, mask coordinates,
mask weights, source hashes and native timing/flags pass validation.json.

Packed decoded allocation including padding is 102,400,000 bytes (97.66 MiB):
81,920,000 base RGBA8 plus 20,480,000 R8 masks. Tight base-plus-mask pixels account for
90,006,860 bytes. Actors and variants share this artwork.

Reproduce with mm7_m514/process.py --project level_generation/creatures/mm7_m250 --tone .80,
then this project's variants.py, then mm7_m514/package.py with the same --project.
Wait for packaging before build_viewer.py, mm7_ambient/review_contacts.py,
review_variants.py and review_masks.py. Recheck affected visuals and acceptance hashes
following any modification. No gameplay installation or renderer changes were performed.
