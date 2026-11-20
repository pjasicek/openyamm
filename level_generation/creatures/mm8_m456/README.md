# MM8 Dragon Hunter restoration

Open [viewer.html](viewer.html) locally. All 160 unique native poses are included: standing, attack,
walking, hit, fidget, falling and corpse poses in five stored views. Actors 43–45 retain their original
timing, logical size, scale, Center flags and eight directions with native mirrors. No pixel aliases
or unused poses were omitted. Native assets are unchanged; this package is staged, not installed.

Eight RGBA8 base atlas pages have matching R8 coverage pages and identical placement. Decoded base,
mask and packing memory totals 138,415,360 bytes (132.00 MiB); tight crops total 105,258,220 bytes.
Exports use two physical pixels per native logical pixel. Actual generated sampling after shared
registration ranges from 2.4458 to 4.6599 pixels per native pixel. Separate placement, animation and
variant JSON accompany the complete manifest.

## Artwork, alpha and palettes

The built-in imagegen tool produced 43 compact jobs and 59 retained raw outputs. Exact prompts,
reference hashes, selected versions, rejected versions and acceptance checkpoints are preserved.
Identity V1 remains frozen in references/accepted_identity.png because action requests used it;
standing V2 corrects the sword teeth. Never replace the frozen historical reference. Corrections
also repair reversed body views, foreshortened weapons, falling anatomy and blade projections.
Seventeen overlap checkpoints retain previous selections alongside the accepted continuation.

All selected sheets supply real PNG alpha. No painted checkerboards were accepted. Ordinary
extraction preserves the supplied alpha byte for byte. Reviewed per-job seam and boundary residue
exceptions are recorded in compact_jobs.json and demonstrated in the light-background crops.
The d_v3 sheet has disjoint figures with overlapping rectangular bounds: deterministic component
ownership assigns every nonzero-alpha pixel exactly once, without cutting visible anatomy.
Its extraction masks and independent reconstruction proof are retained.

The padded transformation exposed detached alpha=1 specks in a few poses. Only explicitly inspected
whole components were removed, with exact masks, pixel counts and before-images under
checkpoints/residue. This is not a blanket alpha cutoff. The native-aware edge audit also checks
nearby enhanced interior colours; one opaque green crest rib highlight in m456wg1 is explicitly
accepted with a master hash and light/dark evidence. It is not matte contamination.

Palette 457 is the exact base bypass; 458 and 459 derive blue and burgundy appearances from the
enhanced R8 mask and fixed native palette deltas. Warm skin, gold trim and boots are protected.
Native tinted steel remains recolorable. Nine exposed blades needed local tint/brightness correction
after the teeth edits. blade_color_masks contains masks on the enhanced artwork; frozen per-channel
native/enhanced blade median gains preserve generated shading, alpha and all unmasked pixels.
These correction masks are offline processing inputs, separate from the runtime variant mask.

## Placement and validation

Common action/view crops include six native pixels of padding; compact grids split with one pose
of overlap when needed for detail. Each sheet uses one isotropic anatomical scale. Integer whole-frame
translations match the native lower contact band; falling poses use the largest body component.
Vertical contact error is zero and horizontal error is at most half a physical pixel. Native motion
is preserved; silhouettes are not independently fitted to equal bounds.

The 256×256 logical canvas occupies a 576×576 aligned master at origin [-32,-32]. Current processing
keeps a 1024×1024 temporary canvas through normalization, affine resampling and contact translation,
then proves that the final crop loses no pixels. Historical normalization/affine clipping found in dc0
and ag2 was repaired; earlier affected masters and diagnostics are archived. Independent checks replay
all 160 selected transforms exactly and verify the lossless pose partition. Reprocessing an earlier
chunk retains an already selected later overlap.

Frozen family luminance multiplier is 1.0664089640296452. Resampling uses premultiplied alpha;
packing uses four-pixel trim support, three-pixel hidden colour/coverage bleed and sixteen-pixel
gutters without mipmaps. The viewer displays the full aligned canvas in each panel.

Review covers all combined native/base/blue/burgundy/mask contacts, complete action sequences in
all stored views, all overlaps and final light/dark contours. Browser checks pass 160 stored poses,
480 variant decodes, 192 tracks and 1,008 timing boundaries. Front attack, mirrored walking and corpse
panels exactly match exported masters. Native source hashes and bindings, alpha, contacts, palette math,
protected pixels, crop reconstruction and atlas extraction pass independent checks. Fine details remain
interpretations of low-resolution artwork; original canvas-edge clipping is a native source limitation.

## Revisions

Reuse selected raw sheets and version any changed generation. Review affected native sheets before
calling the built-in imagegen tool. Stage exact tool records with stage_outputs.py, run
adjust_extraction.py JOB and process_compact.py JOB, inspect the contact and use accept_review.py
with the actual finding. Preserve frozen calibration and tone unless a demonstrated defect requires
a change. Changed registered masters invalidate their local blade-mask hashes: redraw/review those
masks deliberately before reapplying colour; do not silently reuse masks on changed anatomy.

Rebuild package.py, refresh_contacts.py, sequence_contacts.py, overlap_contacts.py and
review_evidence.py as affected. Run audit_transform_extent.py, verify_transform.py and
verify_partial.py --final. Run the authorized browser wrapper:
`/home/pjasicek/Downloads/mm8_creature_restore.py run mm8_m456/browser_checks.py`.
Refresh affected viewer captures and review evidence hashes, then run finalize.py and the parent
inventory_remaining.py. Revisions invalidate acceptance until the changed outputs are reviewed again.
