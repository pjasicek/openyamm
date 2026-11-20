# MM8 Ogre Warrior restoration

Open [viewer.html](viewer.html) locally. All 160 unique native poses are restored at 2× logical resolution,
including 40 stored poses without descriptor bindings. Original actor bindings, durations, frame scales,
Center flags and mirrored directions are preserved. Unbound poses have no invented playback timing.

Six base RGBA8 atlas pages have matching R8 coverage masks and identical rectangles. Decoded base and masks,
including padding, total 105,939,200 bytes (101.03 MiB); tight base/mask crops total 78,753,505 bytes.
Placement, animations and variants are exported separately and together in manifest.json. No gameplay installation.

The built-in imagegen tool restored the green base in 38 compact jobs. Exact prompts, references, selected raw
outputs and their hashes are retained in compact_jobs.json and provenance.json. Versioned rejected sheets remain
as provenance. Corrections addressed invented green rear cloth/chainmail, falling head orientation and relaxed
fingers, and final recovery club foreshortening/occlusion. registration.json selects one version of each overlap.
Actual generated sampling after uniform anatomical registration is 2.3682–4.5469 pixels per native pixel,
distinct from the 2× export size. Original tool locations are recorded in generation_tool_outputs*.json.

prepare_compact.py uses lossless common crops across each full action/view, six native pixels of padding,
measured output-envelope budgets and consecutive batches with overlap. adjust_extraction.py records empty raw
seams without moving artwork or changing nominal cell origins. The front attack a_v0_0 has an explicitly verified
four-row transparent seam, retaining two empty rows on each side; its exact override is saved in compact_jobs.json.
Preserve that override when reproducing it, since the default seam search conservatively requires eight rows.

process_compact.py unmixes the magenta matte, repairs residual RGB spill locally, applies one shared isotropic
batch calibration, then translates whole frames by integer pixels to each native pose's lower opaque contact.
The lower band is 24 physical pixels at alpha >=128; falling/prone contacts use the largest body component.
Inverse translations are exact. Native contact error is zero vertically and at most half a physical pixel
horizontally. The 256×256 logical canvas and native pivot remain inside a padded 576×576 aligned canvas with
physical origin [-32,-32]. Translations are baked into pixels and must not be applied again by a future loader.

One frozen identity-derived luminance multiplier, 0.8770478888609483, retains native tonal weight across poses.
material_settings.json and materials.py define native palette-delta recoloring: green cloth/wrist wraps (441),
blue (442), red (443). Masks are selected on enhanced artwork using color features and connected green support,
with three-pixel full support and a six-pixel fade. Brown skin, black helmet, leather straps, belt fittings,
iron armor, chainmail and wooden club stay protected. Base bypass, alpha, unmasked pixels and deterministic
variant math are verified byte-for-byte. Native masks are never spatially resized onto enhanced anatomy.

Review covers all batch contacts in native/base/blue/red/mask rows, all five complete attack, walk and falling
sequences with selected overlaps, final atlas contours and magnified cloth, hand, helmet and club edges on light
and dark backgrounds. Offline Chrome checks cover 480 variant decodes, 160 stored poses, 192 native tracks and
1,008 timing boundaries. Native BMPs, ACT palettes and family bindings are unchanged; semantic source audit
evidence is under checkpoints/.

Native sprites sometimes touch the canvas boundary; padding cannot recover missing original anatomy. Enhanced
facial detail, material texture, stance width and some limb contours remain interpretations of low-resolution art.
Far shoulder strap spikes can project beside the face in quarter-front views; magnified native references confirm
this equipment detail. Contact correction preserves native placement without forcing identical silhouettes.

## Reproduce or revise

Reuse accepted sheets. Version any changed prompt/raw, update the affected selection, then run
`adjust_extraction.py KEY` and `process_compact.py KEY`; retain the explicit a_v0_0 seam override noted above.
Remove stale frozen calibration and extraction overrides when selecting a new raw version. Process jobs
sequentially and do not edit shared queue/registration files while a processor runs. Review the combined contact.

Rebuild with `package.py`, `sequence_contacts.py`, `review_evidence.py`, `material_edge_contact.py`,
`verify_delivery.py` and `browser_checks.py`. Chrome can run through the approved offline wrapper:
`/home/pjasicek/Downloads/mm8_creature_restore.py run mm8_m440/browser_checks.py`.
Refresh viewer captures and visual acceptance evidence, then renew review/decision.json hashes and run
`finalize.py`. Finally run `python3 level_generation/creatures/inventory_remaining.py` from the repository root.
Any revision invalidates the old acceptance seal until checks and review are renewed. Keep originals unchanged.
