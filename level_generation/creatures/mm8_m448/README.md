# MM8 Wererat Ratman Form restoration

Open [viewer.html](viewer.html) locally. The staged package covers 165 native filenames from 160 unique
restored poses. Five `xa` corpse filenames exactly reuse their matching `de` pose, including every palette.
Twenty-five stored poses remain unbound, as in the source. Actor IDs 37–39 retain their native durations,
scales, Center flags, eight directions and mirrors. Nothing is installed into gameplay.

Six RGBA8 base atlas pages have matching R8 clothing masks and identical rectangles. Decoded base and masks
total 104,737,280 bytes (99.89 MiB), including padding; tight crops total 77,340,730 bytes. Placement, animations
and variants are exported separately and in manifest.json. All runtime artwork is 2× native logical resolution.
Actual generated sampling after uniform anatomical registration ranges from 2.3728 to 4.2899 pixels per native pixel.

The built-in imagegen tool produced 33 compact jobs and 40 retained raw outputs, including seven corrective
versions. Six corrections removed an invented brown diagonal torso/back strap: native gray folds are cloth.
The side falling sheet was regenerated at the correct grid aspect ratio. Rejected raw sheets, exact prompts,
reference roles, original tool locations and selected hashes remain available. Registration selects one version
of every overlapping attack/hit pose. No palette variant required a separate AI generation.

prepare_compact.py preserves common crops across complete action/view sequences, six native pixels of safety
padding and measured detail budgets. It splits consecutive complete poses with overlap where needed. The short
side/front attack continuation sheets retain the accepted preceding sheet as an additional identity reference.

## Alpha, placement and selective palettes

Genuine PNG alpha is now preferred, as requested on 2026-09-14. A viewer checkerboard is acceptable; a painted
checkerboard in visible pixels is not. Several sheets returned real alpha even when their historical prompts
requested magenta. Keep their supplied alpha and bypass matte recovery. Hidden RGB can look colored in a preview
that ignores alpha; the saved light/dark composites establish the actual visible result. Accepted historical
magenta sheets still use local matte unmixing. Every job records its actual background mode and handling branch.

adjust_extraction.py records safe seams and retains nominal grid origins. Sparse alpha=1 residue in four sheets
is preserved; documented seam checks permit only that residue within the separating bands. One rear-quarter
sheet has alpha=2 residue on its outside border. Its visible feet/tail remain inside the image; the job records
the measured exception. This does not erase alpha or authorize cutting a visible silhouette.

process_compact.py uses a shared isotropic anatomical calibration per sheet, then integer whole-frame
translations to each native pose's lower opaque contact. The contact band is 24 physical pixels at alpha >=128;
falling poses use the largest body component. Inverse translations are exact. Vertical contact error is zero;
horizontal error is at most half a physical pixel. The native 256×256 logical canvas and pivot remain in a
576×576 aligned canvas with physical origin [-32,-32]. Translations are baked into pixels and must not be
applied again by a runtime loader. Resampling uses premultiplied color and alpha. Packing uses four-pixel trim
support, three-pixel hidden RGB/mask bleed and sixteen-pixel gutters/alignment, without mipmaps.

The frozen luminance multiplier is 0.9015888462069217, measured on the initial identity and retained after its
strap correction. Native tonal weight remains consistent across sheets. Palette 449 is the green base;
450 and 451 produce blue and maroon/red trousers with deterministic native palette deltas. Gray shirt, fur,
hands, tail, claws, leather and steel are protected. Masks classify enhanced colors with eight nearest native
palette samples, inverse fourth-power weights, green material seeds and a six-pixel support fade. They are
authored on enhanced pixels rather than resized from native masks.

Final viewer inspection found isolated green-tinted blade/boot pixels in the initial clothing mask. The mask-only
correction retains substantial connected clothing regions (at least 64 pixels or 2% of the largest region),
plus small antialiased islands within four physical pixels. Base artwork, alpha and placement remain unchanged.
The correction audit and pre-correction contacts are retained. material_settings.json records all recolor settings.

## Review and reproduction

Review includes all 33 native/base/blue/red/mask contacts, full attack/walk/falling sequences in five stored views,
all native aliases, final atlas contours and magnified material boundaries on light/dark backgrounds. Browser
checks cover 495 variant decodes, 165 stored poses, 192 native tracks and 1,008 timing boundaries. Source files,
bindings, crop/atlas reconstruction, native contacts, alpha and palette arithmetic are independently checked.
Fur, folds, face detail and some silhouette contours remain interpretations of low-resolution originals.

Reuse selected raw sheets. Version any changed prompt/raw, update selection, remove stale calibration/seam data,
then run adjust_extraction.py KEY and process_compact.py KEY sequentially. Review affected contacts. For mask-only
work, derive variants from the existing toned masters with process_compact.variants, then refresh_contacts.py.

Rebuild with package.py, sequence_contacts.py, review_evidence.py, material_edge_contact.py, verify_delivery.py
and browser_checks.py. The approved Chrome wrapper is
`/home/pjasicek/Downloads/mm8_creature_restore.py run mm8_m448/browser_checks.py`.
Refresh viewer captures and review/decision.json evidence hashes, then run finalize.py and
`python3 level_generation/creatures/inventory_remaining.py`. Revisions invalidate acceptance until reviewed again.
