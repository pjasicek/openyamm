# MM8 Wererat Human Form restoration

Open [viewer.html](viewer.html) locally. All 160 unique native poses are restored at 2× logical resolution.
All poses have native animation bindings. Actor IDs 34–36 retain their original durations, scales, Center flags,
eight directions and mirrors. Five base RGBA8 atlas pages have matching R8 masks and identical rectangles.
Decoded base and masks total 90,741,760 bytes (86.54 MiB), including padding; tight crops total 64,476,550 bytes.
Placement, animations and variants are exported separately and in manifest.json. Assets remain staged here.

The built-in imagegen tool restored the green base in 31 compact jobs, with 35 raw outputs including four
corrective versions. Prompts, references, selected output hashes and original tool locations are preserved.
Corrections removed an invented shoulder blade tip in the identity sheet, restored closed sword grips in the
front falling sequence, corrected the quarter-front prone sword direction, and corrected the rear-quarter
prone head orientation. Rejected raw sheets remain as provenance. registration.json selects one version of
every overlap. Actual generated sampling after anatomical registration is 2.4441–3.7167 pixels per native pixel.

prepare_compact.py uses lossless common crops over full action/view sequences, six native pixels of padding,
measured output-envelope budgets and consecutive batches with overlap. Attack sequences are split into six
and three poses with one shared pose. adjust_extraction.py records empty raw seams while retaining nominal
cell origins and scale. Every selected sheet passed the default minimum eight-pixel empty seam check.

process_compact.py unmixes the magenta matte, repairs residual edge RGB locally, applies one shared isotropic
calibration per batch, then translates whole frames by integer pixels to each native pose's lower opaque
contact. The contact band is 24 physical pixels at alpha >=128; falling/prone poses use the largest body
component. Inverse translations are exact. Contact error is zero vertically and at most half a physical pixel
horizontally. The native 256×256 logical canvas and pivot remain inside a padded 576×576 aligned canvas with
physical origin [-32,-32]. Translations are baked into pixels and must not be applied again by a future loader.
Atlas packing uses four-pixel trim support, three-pixel hidden RGB/mask bleed, and sixteen-pixel gutters/alignment.

One frozen identity-derived luminance multiplier, 0.8363782159484625, preserves native tonal weight.
materials.py and material_settings.json define deterministic native palette-delta recoloring from green (445)
to blue (446) and maroon/red (447). Enhanced-art masks cover trousers, lapels and cuffs, including dark teal
trouser shadows (green-minus-blue seed threshold >2). Connected material support extends three pixels, followed
by a six-pixel fade. Gray jacket/hood, brown beard and leather, skin and steel stay protected. Base bypass,
alpha, unmasked pixels and variant arithmetic are checked byte-for-byte. Native masks are not resized onto
enhanced anatomy. Frame-specific native edge color allowances are retained in native_frame_edge_limits.json.

Review covers all 31 native/base/blue/red/mask contacts; all five complete attack, walking and falling sequences;
final atlas contours and magnified material boundaries on light and dark backgrounds. Offline Chrome checks
passed 480 variant decodes, 160 stored poses, 192 native tracks and 1,008 timing boundaries. Captures include
front attack, mirrored blue walking and the red side corpse. Native BMPs, ACT palettes and bindings are unchanged.
Small blade segments near the head or torso in some views are present in the native poses and were retained.
Enhanced facial detail, folds and some silhouette contours remain interpretations of low-resolution originals.

## Reproduce or revise

Reuse accepted sheets. Version changed prompts/raw, update the affected selection, then run adjust_extraction.py
and process_compact.py with the job key. Remove stale frozen calibration/extraction records when selecting new
raw artwork. Process jobs sequentially; do not edit shared queue/registration files while processing runs.
Review the resulting combined contact before accepting it.

Rebuild with package.py, sequence_contacts.py, review_evidence.py, material_edge_contact.py, verify_delivery.py
and browser_checks.py. Chrome can run through the approved offline wrapper:
`/home/pjasicek/Downloads/mm8_creature_restore.py run mm8_m444/browser_checks.py`.
Refresh viewer captures, review evidence and review/decision.json hashes, then run finalize.py. Finally run
`python3 level_generation/creatures/inventory_remaining.py` from the repository root. Any revision invalidates
the previous acceptance seal until renewed checks and review. Keep originals unchanged.
