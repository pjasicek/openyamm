# MM6 Goblin A — Meshy body references and native animation study

Prepared 2026-10-06 with `$creature-to-3d`. This run prepares an **unarmed body** for Smart Topology and the
anatomy/motion evidence for later model correction and animation. The original right-hand sword remains a
separate required prop in the study. No Meshy submission or model/rig changes were made in this run.

## Files to use

| Purpose | Selected file |
| --- | --- |
| Smart Topology single-image input | [00_smart_topology_three_quarter.png](submission/00_smart_topology_three_quarter.png) |
| Front anatomy reference | [01_front.png](submission/01_front.png) |
| Back anatomy reference | [02_back.png](submission/02_back.png) |
| Anatomical left reference, no near pouch/ear hoops | [03_left.png](submission/03_left.png) |
| Anatomical right reference, pouch and three hoops | [04_right.png](submission/04_right.png) |
| Review all selected views | [selected_views_review.png](guides/selected_views_review.png) |
| Anatomy and model-ingest checks | [ANATOMY_GUIDE.md](ANATOMY_GUIDE.md), [structured targets](anatomy_targets.json) |
| Every native animation, pose-by-pose | [ANIMATION_STUDY.md](ANIMATION_STUDY.md), [structured motion specification](motion_spec.json) |
| Native anatomy close-ups and annotations | [native_details.png](guides/native_details.png), [anatomy_native.png](guides/anatomy_native.png) |
| Native timing, sources, hashes, duplicates and aliases | [source_inventory.json](source_inventory.json) |
| Prompts, inputs, raw outputs and selections | [generation_runs.json](generation_runs.json) |
| Verified counts and selected hashes | [verification.json](verification.json) |
| Current stage and next owner/action | [creature_3d_progress.json](creature_3d_progress.json) |
| Complete portable handoff | [mm6_goblin_stage1_meshy_and_study.zip](mm6_goblin_stage1_meshy_and_study.zip) |

Each selected image is a separate **1024×1536 native imagegen return**, with transparency. No enlargement,
padding or resolution claims were added. The contact image is a review sheet, **not a Meshy upload**.
Eleven imagegen returns produced five selected views through two correction stages: raising the initial low
arms/opening fingers, then enlarging the head and shortening the legs to match native proportions and deriving
the four supporting views again. Older September views were material/identity inputs, not final
selections. Original sprites remain authoritative for silhouette and motion.

The five views share the important identity: compact heavy-browed head, pointed up/back ears, short rear skull
wedge, olive-green muscular body, dark iron gorget/caps/bracers/greaves, bare belly/back, short leather strips,
right pouch/jewelry, three long fingers plus thumb and three forward toes. They remain AI appearance references:
small differences in straps, riveting, profile perspective and projected hand attitude are not measured 3D
geometry. Use the anatomy contract to reconcile those details when the model returns.

## Meshy handoff

Use `submission/00_smart_topology_three_quarter.png` for **Image to 3D → Smart Topology**, target approximately
**15,000 triangles**, A pose, with texture generation off for this geometry pass. In the current API documentation
this route is `model_type: smart-topology`, `ai_model: meshy-t2`, `target_polycount: 15000`,
`pose_mode: a-pose`, `should_texture: false`. T2 generates triangles directly; remesh controls are ignored.
[Meshy Image to 3D documentation, checked 2026-10-06](https://docs.meshy.ai/en/api/image-to-3d).

The four supporting views are prepared separately for appearance review and model correction. The current
documented Multi-Image endpoint accepts 1–4 images but lists standard models and does not document the T2 Smart
Topology route. Do not assume that uploading four images keeps Smart Topology enabled. If the web UI offers
that combination, verify its selected route before submitting; otherwise use the single-image input above.
[Meshy Multi-Image documentation](https://docs.meshy.ai/en/api/multi-image-to-3d).

Download the **unrigged GLB** and retain its Meshy task/settings. Return it with this package using:

```text
$creature-to-3d MM6 goblin — ingest this unrigged Smart Topology model against stage1_20261006;
correct anatomy and obvious topology defects before rigging.
```

Next owner is the user for Meshy generation; next Codex step is geometry/anatomy ingestion. After the corrected
base is satisfactory, the user can auto-rig it in Meshy and return the rig. The anatomy guide identifies fingers,
shoulder attachments, rigid armor, foot pivots, skirt gaps and right-hand grip as deformation checks. UV and
texture finish follow geometry/rig/animation review, as later stages; this package does not mark them complete.

## Native study coverage

All **59 original BMP hashes** match the retired native archive; all 59 retained RGBA PNGs were checked against
index-zero-transparent decoding of those BMPs. Native sources use a common **355×289** bottom-anchored canvas,
palette 745, frame scale 0.649994. The package includes all 59 PNGs and unannotated native sheets.

| Action | Native temporal anchors | Genuine images/views | Duration |
| --- | ---: | ---: | --- |
| Standing | 1 | 5 | held; 125 ms metadata |
| Walk | 6 | 30 / five per anchor | 750 ms, looping |
| Attack | 6 | 6 / front only | 750 ms |
| Hit | 6 | 6 / front only | 750 ms |
| Death | 5 | 5 / front only | 625 ms, then Corpse |
| Corpse | 1 | 1 / front only | held; 125 ms metadata |
| Fidget | 6 | 6 / front only | 750 ms |

AttackMelee and AttackRanged share the same native animation. Standing/walk use five genuine views plus three
mirrored octants; those mirror shortcuts do not change actual 3D weapon handedness. There is no native running
clip. Death frame d is byte-identical to the held corpse; e is a small intervening settling variation.

The motion guide covers all **31 temporal anchors**, main force/driver, both shoulder-elbow-wrist chains,
palm/finger/roll decisions, hips/knees/sole support, body/head/jaw, prop/cloth response, continuous timing and
frame-specific review criteria. Numeric ranges and annotated landmarks are explicitly **fitting seeds**, not
recovered bone transforms. Hidden death legs and action-side depth have lower confidence. Do not interpret a
missing landmark as a missing limb or convert source-projected angles directly to local Euler keys.

## Rebuild and verification

`motion_notes.json` and `anatomy_targets.json` are the editable study inputs. `build_guides.py` checks originals
and native decodes, expands timings/view paths into `motion_spec.json`, makes the readable guides and annotated
sheets, validates selected image hashes/bounds, and builds the ZIP:

```sh
python3 level_generation/creatures/mm6_goblin/stage1_20261006/build_guides.py
```

The script runs locally with installed Pillow. It never invokes imagegen/Meshy or modifies historical model or
runtime assets. Native overlay sheets are deterministic source visualizations, enlarged with nearest-neighbor
sampling; they are not additional high-resolution AI source art. Source GIFs were omitted because their old
10 ms rounding does not preserve the exact 125 ms holds; descriptor timings in the motion specification are exact.

Technical validation, agent visual review and user artistic acceptance are separate in the progress record.
No new animation has been implemented or visually verified on a rig yet.
After changing selected references or study inputs, update the progress record and its revision-bound review
hashes; rebuilding files alone does not carry artistic acceptance to a changed revision.
