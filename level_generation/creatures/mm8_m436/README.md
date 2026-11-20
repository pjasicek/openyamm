# MM8 Ogre Peasant male restoration

Open [viewer.html](viewer.html) locally. All 160 unique native poses are restored at 2× logical resolution,
including 65 stored poses without native descriptor bindings. All original actor bindings, durations, frame scales,
Center flags and mirrored directions are preserved. The stored throw sequence does not replace the native actors'
walk-based attack binding. Unbound poses have no invented playback timing.

The five base RGBA8 atlas pages have matching R8 masks and identical rectangles. Decoded base plus masks including
padding total 90,018,560 bytes (85.85 MiB); tight base/mask crops total 64,459,840 bytes. No gameplay installation.
Placement, animations and variants are exported separately and together in manifest.json.

The built-in imagegen tool restored the green base in 34 compact jobs. Exact prompts, references, selected raw
outputs and their hashes are in compact_jobs.json and provenance.json. One rear preparation sheet was rejected
and corrected; a missing front held stone was replaced using its overlapping following batch. Rejected artwork is
retained, but registration.json selects the actual delivered version for each pose. Actual generated sampling after
uniform anatomical registration is 2.6345–4.2672 pixels per native pixel, distinct from the 2× export size.

prepare_compact.py uses a lossless common crop across each full action/view, six native pixels of padding, measured
output-envelope budgets and consecutive batches with an overlapping pose. adjust_extraction.py records proven empty
raw seams without moving artwork or changing nominal cell origins. process_compact.py extracts/unmixes the magenta
matte, fixes residual RGB spill locally, applies one shared isotropic batch calibration, then translates whole frames
by integer pixels to each native pose's lower opaque contact. The lower band is 24 physical pixels at alpha >=128;
falling/prone contacts use the largest body component to exclude loose stones. Inverse translations are exact.
Native contact error is zero vertically and at most half a physical pixel horizontally. The native 256×256 canvas
and bottom-center pivot are retained inside a padded 576×576 aligned canvas with physical origin [-32,-32].

One frozen identity-derived luminance multiplier, 0.7775028358830823, preserves original tonal weight across all
poses. material_settings.json and materials.py define native palette-delta recoloring: green cloth (437), blue
(438), red (439). Masks are selected on enhanced artwork using color features and connected green cloth support,
with a three-pixel full support and six-pixel fade. Brown skin, ochre hair, leather pack/belt, buckle and gray stones
are protected. Base bypass, all alpha, unmasked pixels and deterministic variant math are verified byte-for-byte.

Review includes every batch in native/base/blue/red/mask contacts, five assembled throw sequences, all-frame final
atlas contours, magnified hand/stone/cloth edges on light and dark backgrounds, and the actual offline viewer.
Browser checks cover 480 variant decodes, 160 stored poses, 192 native tracks and 984 timing boundaries. Native BMPs,
ACT palettes and family bindings are unchanged. Shared-table provenance was refreshed only after exact semantic
comparison; retained evidence is under checkpoints/.

Original source sprites sometimes touch the bottom canvas boundary. Padding does not reconstruct original missing
anatomy. Enhanced stance widths, facial details and material texture remain interpretations of low-resolution art;
the contact correction preserves native placement rather than forcing identical silhouettes.

## Reproduce or revise

Do not regenerate accepted sheets unnecessarily. For an affected job, retain the old prompt/raw as a versioned
checkpoint, update its selection, run `adjust_extraction.py KEY`, then `process_compact.py KEY`. Processing jobs must
run sequentially; their shared registration and queue files must not be edited while a processor is running.
Review the new combined contact and mark only visually accepted jobs accordingly. Rebuild using `package.py`,
`review_evidence.py`, `verify_delivery.py` and `browser_checks.py`. The browser can run through the approved
`/home/pjasicek/Downloads/mm8_creature_restore.py run mm8_m436/browser_checks.py` offline wrapper.

After visual review, renew review/decision.json evidence hashes, run `finalize.py`, then run
`python3 level_generation/creatures/inventory_remaining.py` from the repository root. Any revision invalidates the
old acceptance seal until those checks and review are renewed. Native originals must remain untouched.
