# MM8 Wererat Rat Form restoration

Open [viewer.html](viewer.html) locally. All 160 unique native frames are restored, including standing,
attack, walking, hit, fidget, falling and corpse poses across five stored views. Actors 40–42 retain native
timing, scale, Center flags, eight directions and mirrors. All poses are bound; there are no pixel aliases.
Original assets are unchanged and nothing is installed into gameplay.

Five RGBA8 base atlas pages have matching R8 masks and identical rectangles. Decoded memory totals
90,561,280 bytes (86.37 MiB), including masks and packing; tight crops total 62,952,255 bytes. Runtime
artwork has two physical pixels per native logical pixel. Actual generated sampling after shared anatomical
registration ranges from 2.4276 to 5.8966 pixels per native pixel. Placement, animations and variant metadata
are available separately and in manifest.json. All three actors share native palette 452: zero masks and
exact base bypass are intentional. There are no native recolors to generate.

## Generation and transparency

The built-in imagegen tool produced 33 compact jobs and 35 retained raw outputs. Identity v1 was rejected
for enlarged pixel blocks; identity v2 established fine fur detail. Rear fidget v1 had two malformed forepaws
and an incorrect tail curve; v2 corrected these against enlarged native references. Rejected versions,
prompts, tool metadata and accepted checkpoints are retained. Seven overlap checkpoints preserve preceding
versions and their registration before selecting continuation artwork.

All selected sheets supplied genuine PNG alpha. Extraction preserves it byte for byte across all 160
frames and bypasses matte extraction/unmixing. No painted checkerboards are accepted. Light/dark composites
verify visible contours; transparent padding RGB is not evidence of a visible background. Local RGB-only
edge treatment uses measured per-frame native color allowances without changing supplied alpha.

Safe extraction seams retain nominal grid origins and ordinarily require an eight-pixel band with no more
than alpha=1 residue. Individually reviewed outer-boundary exceptions are alpha=3 for m452af1, alpha=4 for
m452nc0, and alpha=2 for m452dc0. The n_v1 sheet has a measured three-pixel row seam at alpha<=2; its queue
record and light/dark closeups document the exception. All residue is preserved, with visible paws, claws,
tails and whiskers intact. These exceptions do not relax other jobs' limits.

## Deterministic placement and export

prepare_compact.py retains a common action/view crop with six native pixels of padding, chooses compact
grids for a minimum detail budget, and splits consecutive poses with overlap. Calibration uses one isotropic
anatomical scale per sheet. Integer whole-frame translations match each native pose's lower opaque contact
using a 24-physical-pixel band at alpha>=128; falling poses use the largest rat body component. Vertical
contact error is zero, horizontal error at most half a physical pixel, and inverse translations are exact.
Native airborne motion remains intact. Never fit each silhouette independently or apply translations twice.

The native 256×256 logical canvas occupies a 576×576 aligned master with physical origin [-32,-32]. Frozen
luminance multiplier 0.9252413830828491 preserves tonal weight. Resampling uses premultiplied color/alpha;
packing uses four-pixel trim support, three-pixel hidden RGB bleed and sixteen-pixel aligned gutters without
mipmaps. The viewer gives each master its full 576-pixel panel, avoiding mask-panel overlap on long tails.

## Review and reproduction

Review covers all 33 combined native/base/empty-mask contacts, complete attack/walk/falling sequences in
five views, all seven overlap comparisons, final atlas contours on light/dark backgrounds and viewer attack,
mirrored walking and corpse captures. Browser checks pass 160 decodes, 160 stored poses, 192 tracks and
1,008 timing boundaries. Three rendered panel comparisons exactly match exported masters, including the
mirrored tail. Source provenance, native bindings, alpha preservation, contacts, atlas reconstruction,
single-palette bypass and every cleaned/aligned/atlas contour pass deterministic checks.

Fine fur, facial details and silhouette contours remain interpretations of low-resolution artwork. Native
canvas-edge clipping is preserved as a source limitation.

For revisions, reuse selected raw sheets; version changed outputs/prompts and update compact_jobs.json.
Run adjust_extraction.py JOB then process_compact.py JOB, review the affected contact, and accept_review.py
with the review finding. Preserve shared calibration, contact rules and frozen tone unless a demonstrated
defect requires changing them. Rebuild with package.py; refresh sequence_contacts.py, overlap_contacts.py
and review_evidence.py. Run verify_delivery.py and browser_checks.py, refresh viewer captures and review
evidence hashes, then finalize.py and the parent inventory_remaining.py. Any revision invalidates the seal
until affected work is reviewed again. The approved browser wrapper is
`/home/pjasicek/Downloads/mm8_creature_restore.py run mm8_m452/browser_checks.py`.
