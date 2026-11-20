# MM8 terrain restoration handoff

Current installed revision: [v13 shared cobble material and continuous diagonals](roads/v13/README.md). Fixes the material mismatch and repeated dirt bites reported in1304. All eight diagonals reuse accepted straight-road pixels; 28 other roads are unchanged. [Final comparison](roads/v13/exact_pose_comparison.png). Pattern discontinuities at road bends remain explicitly accepted limitations; this is not an all-seams-pass revision.

Historical revision: [v12 NE2 edge and join repair](roads/v12/README.md). Only the dirt/grey-dirt NE2 diagonals changed; every straight road remains unchanged. [Exact-pose before/after](roads/v12/exact_pose_comparison.png). Rounded stone contours replace the clipped upper edge and lower ghost fragment; lower grout is aligned to the straight neighbour. Launcher and installed hashes verified. Broad gallery/ZIP/audit are historical snapshots.

Historical revision: [v11 exact1302-pose diagonal repair](roads/v11/README.md). Only eight diagonal variants changed; all straight/junction tiles remain byte-identical to v10. [Exact-pose before/after](roads/v11/exact_pose_comparison.png). Material calibrated to accepted stone pixels, and the visible NE2 east join repaired on the diagonal side only. Broad gallery/ZIP/audit remain historical snapshots.

Historical revision: [v10 clean road connections](roads/v10/README.md). Fixes the Alvar smears from1300/1301 by restoring28 non-diagonal roads byte-for-byte to v7 and repairing eight diagonal endpoints to match. [Straight-road comparison](roads/v10/straight_comparison.png). v8/v9 acceptance is superseded for these roads. Broad gallery/ZIP/audit remain historical snapshots.

Historical revision: [v9 stone material — GOOD](roads/v9/README.md). Eight diagonal variants use sharper artwork matched to accepted cobbles, retaining the approved v8 masks and boundary pixels. [Focused connections](roads/v9/connections.png). The broad gallery, ZIP and previous completion audit remain v8 snapshots; they were not rebuilt for this focused update.

Historical revision: [roads/v8](roads/v8/README.md), rebuilt from native diagonal footprints and stone layout after screenshot1298 rejected v7. Eight diagonal textures use native structural pixels plus bounded built-in-imagegen microdetail and separate contact shade. All36 roads receive shared native-endpoint colour correction; the28 other road interiors remain unchanged. See [assembled comparisons](roads/v8/assembled_paths.png), [native entry/exit](roads/v8/native_entry_exit.png) and [current review](roads/v8/visual_review.json). Historical v7 acceptance is superseded; retain its user regression report as a lesson.

The complete239-file pack is reviewed, installed and packaged. Both launcher modes were verified and the
installed pack ran successfully on the desktop GPU. Follow this document before historical iteration notes.

The final requirement audit is [reports/completion_audit.json](reports/completion_audit.json).

## Deliverables and authoritative sources

- [Launch instructions](README.md), [all14 maps](MAPS.md), [comparison gallery](review.html).
- [Complete export](complete_runtime_x2/manifest.json), [review acceptance](reports/acceptance.json),
  [installation audit](reports/integration.json), [launcher verification](reports/launcher/validation.json), [runtime ZIP](mm8_complete_terrain_x2.zip).
- [Effective inventory](effective_inventory.json) and [grids](effective_grids.json) resolve197 static names
  plus42 frames. Raw ODM inventory196/238 missed Shadowspire's `out06_1.scene.yml` master-tile override.
- `complete_runtime_x2/worlds/mm8/terrain_x2/` is the exact union. Historical `runtime_x2/` is a partial build
  input. `reports/candidate_stage.json` identifies final override sources. The export manifest is immutable;
  its candidate label records assembly chronology. Subsequent acceptance/integration records establish review.
- Originals remain in `assets_dev/engine/terrain` and world `textures`; restored terrain is separately installed
  under `assets_dev/worlds/mm8/terrain_x2`. Surface/bmodel `textures_x2` is a different category.

## Joined repair and shared border colours after screenshot1297

**Current road runtime source is `roads/v7`.** Four diagonal textures have joint AI reconstruction;
32 other roads have colour-only corrections within8 runtime pixels of open borders. Their central240×240
pixels and all road shapes remain unchanged. The other203 terrain files are byte-identical to v6.

The old protected rim cut through new stones. Reconstructing joined neighborhoods healed those cuts,
but low-angle review exposed another line at the actual boundary. UV diagnostics located it at the road
endpoint; common endpoint colours remove it without repainting all road interiors. See the v7 README
for the compose → match_ports → validation order and retained rejected candidates.

Both supplied poses, the native repeated path, entry/exit join close-ups,13 walking samples and Alvar
were reviewed on the exact final stage. All724 road checks and24,428 full-export checks pass. Do not
use the earlier v7 `final_pose` captures as final evidence: only `ports` captures include colour correction.
V6 width is retained, with small irregular stone edges; native width is not identical.

## Connected diagonal correction after screenshot1296

**Historical v6 revision, superseded by v7.** V4 targeted the wrong straight
artwork, and v5 trimmed individual stones but deepened the repeated inward bite. V6 rebuilds both connected
bands against fixed openings, using built-in imagegen artwork registered as complete stones and contact shade.
The four files are `drsrne1`, `drsrne2`, `gdrdne1`, and `gdrdne2`; other235 textures are unchanged.

[Both reported poses, before/after](roads/v6/exact_comparison.png), [notes and reproduction](roads/v6/README.md),
[review and provenance](roads/v6/visual_review.json). All724 compatible road joins and36 solid masks pass.
Outer4px runtime borders are unchanged. Both cameras and13 native walking samples use the exact final239-file
stage. The band is narrower through old bulges, with small polygonal edge protrusions retained; do not claim
identical native width or perfectly smooth edges. Review connected width/silhouette in addition to seam checks.
Historical v5 acceptance is superseded by its user regression report and this correction.

## Earlier road edge correction after screenshots1293/1294

The user exposed pointed repeating cobble fingers on Dagger Wound Island after the initial acceptance.
Alvar uses the same `drsr*` textures; this was not a Dagger-only asset. V4 applied a local
AI repaint of edge stones, followed by propagation through connected openings. `roads/v4/` records that earlier revision:
30 cobble files changed; the other209 runtime files, including every orange stepping path, are byte-identical.
The east–west donor and central stone artwork were retained. Do not repair this by clipping/smoothing a mask
through existing stones or by blurring the finished tile. Preserve blunt but irregular stone silhouettes and shade.

[Revision review](roads/v4/visual_review.json), [native comparison](roads/v4/native_comparison.png),
[repeats](roads/v4/repeat_comparison.png), [movement samples](roads/v4/movement_review.png).
The revision includes matching low-angle Dagger Wound/Alvar captures and a grounded flat approach with13 samples.
These are representative poses, not the exact unknown camera of1293. Prior v3 road evidence remains historical;
it does not prove the absence of teeth. All724 road joins and36 solid masks passed for v4.
The explicit migration is `roads/v4/install_revision.py`; it checks the previous installed manifest, preserves
other assets and refuses independent terrain edits. The previous delivery records are retained under
`roads/v4/previous_delivery/`.

## Final art ownership

| Content | Source | Notes |
| --- | --- | --- |
| Ten512px authoring masters /256px runtime | `masters/v1/materials`, `masters/v1/runtime` | Dirt, grass, volcano, red dirt, rock, sandstone, plains, plains sand, grey dirt, grey stone. |
| Native land coverage and contact shading | `transitions/fields`, `transitions/build.json` | Floating-point fields preserve interleaving; do not threshold away native flecks. |
| Grey-stone fringes | `transitions/grey_family_v1` | Thirteen final shared-art overrides; `gdtyl` uses master grey dirt. |
| Pebble dirt variants | `variants/v1` | Native stone arrangement over matching dirt. |
| Volcanic patch | `variants/volcano_v2` | `voltylx` has volcanic borders and native interior dirt patches; it is not a directional dirt-frame transition. |
| Continuous cobble roads | `roads/v7` |19 dirt and17 grey roads. Four joint-art repairs; shared border colour correction on all36. |
| Separate desert stones | `roads/stepping_v1` |12 native stepping patterns; preserve intentional gaps/component counts. |
| Water/lava/tar bodies | `liquids/v1` |14 frames plus fallback each; native broad colour/motion plus bounded AI detail. |
| Final liquid banks | `liquids/banks_v2` |57 RGBA overlays;25 refined files, including topology-preserving dirt-bank edge cleanup and tar key-bleed repair. |

The97 built-in imagegen calls are retained through prompts, receipts and raw output files in the corresponding
folders (15 masters/repairs,2 dirt variants,13 grey fringes,40 cobble art/outline calls,24 stepping art/masks,
3 liquid atlases). Reassembly uses retained sources and needs no new AI calls. See [iteration history](HISTORY.md)
for detailed receipts, experiments and rejected approaches; its old live-session/incomplete-status notes are historical.

## Validation and its limits

`check_complete_pack.py` checked24,428 compatible E/S edge contacts on the exact239-file export, including
cross-family contacts and all14 liquid phases: zero failures. It complements topology/alpha/component checks
in family reports. All10 master repeats were numerically screened and visually reviewed during authoring.

Flat/native visual evidence includes:

- 13 selected land layouts covering seven transition families and corrected volcanic patch.
- 18 original/enhanced bank animation captures across all five bank families. All recurrence screens pass;
  six sampled frames per view were visually inspected, with stationary banks and matching materials.
- Eight grounded cobble routes covering both axes/directions; eight original/enhanced stepping routes.
- Four original/enhanced cobble loop/diagonal pairs, plus native map appearance pilots and all-file offline sheets.

See `fixtures/{land_v1,banks_v2,banks_extra_v1,roads_v1}/review/` for reports/images. Native master/road pilots
are under `reports/native_*review.json`; liquid body pilots and motion evidence are under `liquids/v1/native_review`.
Old pilot reports describe their partial stage honestly; final acceptance combines them with subsequent exact-source
flat/native checks rather than relabelling historical captures as complete-pack captures.

`audit_native_joins.py` measured1,897 unique native neighbour pairs across448,056 placements. The286 metric
candidates were visually compared in all24 pages under `reports/native_contexts`; they reflect incompatible
original edge placements. There are zero metric failures between compatible native contracts. Preserve these
map cells; do not distort shared art to hide a wrong original corner placement. No claim is made that every
map cell/view/mip has been inspected or that Xvfb measures GPU performance.

Grey-water patch1 is mostly dry ground. Its motion crop is the visible southern bank at750,720,1200,960,
identical for original/enhanced and excluding HUD. The original dry central crop failed amplitude detection;
thresholds were not lowered. Native cycle:14 frames ×15/128 seconds =1.640625 seconds.

Opposite stepping views looked similar. The suspected shared-stage race was disproved: capture_gameplay.py
uses unique working directories/scenario IDs. Source, prepared and actual GUI quicksaves verified opposite
headings (`reports/stepping_camera_audit.json`). Do not revive that disproved diagnosis from historical notes.

## Reproduction and maintenance

Use README's export/check/install/package sequence. Do not regenerate raw inventories in place: older reports
bind those files. Effective scene-aware inventory is the coverage authority. Plane of Water's master remap differs
from the simple MM7 direct-ID assumption; follow `inventory.descriptor_index` and the runtime terrain table.

`stage_candidates.py --grey-family --stepping-paths --liquids --banks-v2 --volcano-variant` prepares the full
candidate test mount. It requires the original setup from `prepare_native.py`. `stage_bank_fixtures.py` supports
`--land`, `--roads`, `--extra-banks`; `--restore-snapshot` restores frozen mounts without invalidating captures.
The camera helper is rebuilt by `build_pose_helper.py`, and has a read-only `--inspect <save>` mode.

Use the authorized `tools/capture_gameplay.sh` wrapper for native captures. Bind direct captures with
`capture_bank_fixtures.py --record-existing` plus the appropriate family flag. Use distinct capture names.
Temporary setups may be removed externally; verify executable/source hashes, restore only missing setups,
and poll live handles before restarting. Retained fixture manifests/saves are authoritative.

Follow [shared terrain lessons](../TERRAIN_RESTORATION_HANDOFF.md) and
[MM7 road v5](../mm7/roads_v5/README.md): finish borders with shared stone artwork, not only a mathematically
solid mask. Retain native scale, phase and contact shade; pure matching masters must meet at tile borders.
Check both axes and corners in actual rendering. Keep stepping gaps distinct from continuous cobble masks.
For liquid banks, composite matching masters, preserve native topology/damp shading, inspect key-colour bleed,
and check all animated phases plus actual rendered motion. Never treat green seam metrics alone as visual acceptance.
