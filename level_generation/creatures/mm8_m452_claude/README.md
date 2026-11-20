# MM8 Rat / wererat animal form — m452

> **Sprint (2026-10-31):** Sprint (a full bound for MAW chase speeds) comes from `scripts/anim_sprint.py` on `work/rat_gait2.blend`, see [the reduce project](../mm8_m452_reduce_claude/README.md#sprint-2026-10-31).

> **Gait pass (2026-10-21):** Walk2 and Run2 come from `scripts/anim_gait2.py` on `work/rat_final.blend`, see [the reduce project](../mm8_m452_reduce_claude/README.md#gait-pass-walk2-and-run2-2026-10-21).

> **Installed model reduced (2026-10-19):** the installed model is now the reduction from [`../mm8_m452_reduce_claude/`](../mm8_m452_reduce_claude/README.md) (LOD0 6,602 -> 4,950). This project's exports and master remain the unreduced production; the rollback source is in `../mm8_m452_reduce_claude/work/`.

Completed 2026-10-18. Rigged and installed for **Wererat Rat Form Male A/B/C**, monster IDs **40–42**. The three native tiers use
one palette-452 model at factors 1 / 1.25 / 1.5. Technical completion and agent visual review are recorded
separately from user artistic acceptance in [creature_3d_progress.json](creature_3d_progress.json).

[Interactive review](http://127.0.0.1:8901/level_generation/creatures/mm8_m452_claude/review/viewer/) ·
[Editable Blender master](work/rat_final.blend) · [Portable GLB](export/mm8_m452.glb)

![Native sprites and models at the same cameras](review/ingame/comparison.jpg)

## Source and construction

The original m452 frames establish the heavy shoulder hump, narrow pointed muzzle, small round ears,
dark brown-grey fur, bare tan paws and long bare tail. Native bitmap family m452 supplies sprite groups
m453/m454/m455. All three use palette 452; their differences are size, not colour.
[Source inventory](sources/native_summary.json) and the source action contact sheets retain the evidence.
Five [HD references](references_hd/selected_views_review.png) guided generation. Native silhouettes remained
authoritative; visible toe count and tiny facial details require interpretation at this resolution.

Meshy Smart Topology v1 produced large overlapping fur plates and was rejected. The second pass, using the
selected side reference, supplied a continuous deforming body. Width and height were fitted against native
front/side silhouettes. Tangled facial pieces were replaced by six tapered whiskers and paired upper/lower
incisors. No collar or equipment belongs to this animal form.

The fitted 24-bone rig uses heat weights on the connected body, nearest-body weights for detached paw pieces,
explicit head/jaw ownership and six tail bones. Four influences maximum; no unweighted vertices. Close bite
review found upper-lip vertices following the jaw; the final correction confines that movement to the lower lip.
[Jaw correction](work/jaw_fix.json). Teeth and whiskers retain their owning jaw/head transforms.

| Property | Delivered value |
| --- | --- |
| Colour LODs | 6,602 / 3,301 / 1,182 / 391 triangles |
| Skin | 24 bones, maximum four normalized influences |
| Maps | 2048² base colour and normal; 1024² material classes / ORM |
| Material | Opaque, nonmetallic; matte fur, rough skin, glossy eyes |
| Native calibration | 71-pixel standing height / 0.326295 m = 217.594357 world units/metre |
| Tier scales | 217.594357 / 271.992946 / 326.391535 |
| Meshy cost | 20 credits: two geometry jobs at 5, one retexture at 10 |

The head receives 2.5× UV density. Retexturing preserved the authored UV layout. Native colour classes, baked AO
and an outdoor sprite comparison set the final fur colour. Raw service returns and request receipts remain in
`meshy/` and `requests/`. Lower shadow meshes are inset to avoid coarse caster triangles shading the fur.
The first reduction below the selected level pinched the corpse silhouette; the retained level preserves it.

## Motion

The MM6 Rat provides the diagonal gait, foot IK, bite and tail methods. Choreography follows m452: its hit
rears upward, and death rises then collapses belly-down with spread paws. It does not use the MM6 side-roll.

| Clip | Seconds | Behaviour |
| --- | ---: | --- |
| Standing | 2 | Restrained idle, head and tail motion |
| Walking | 1 | Diagonal gait; 0.30 m stride |
| Running | 0.625 | Faster gait; 0.43 m stride |
| Attack | 1 | Rear, leap/lunge and bite; contact at 0.65 s |
| Hit | 0.625 | Upward recoil and recovery |
| Death | 0.75 | Rear, fall and belly-down collapse |
| Fidget | 0.625 | Head/tail movement |
| Dead | 1 | Exact final death pose held |

Keys are baked at 24 fps, with linear samples and continuous quaternions. The engine needs no IK solver.
The noncaster cast role reuses Attack. Head look uses Neck1/Head with 22° yaw and 15° pitch limits; the upper-body
root is Spine2 and sockets are empty. Gameplay attack timing remains unchanged.

## Installation and evidence

- Portable export and `assets_source/worlds/mm8/models/mm8_m452.glb` are identical. Runtime cooking installs
  `assets_dev/worlds/mm8/models/mm8_m452.glb` and its external textures. Only this family's three entries were
  appended to `assets_dev/worlds/mm8/models/actors.yml`. [Installation receipt](review/installation.json).
- The ordinary `openyamm` build and focused actor regression pass. The case checks native tier ratios,
  shared palette/asset, eight clip durations, jaw/tail bones, lower LODs and unchanged simulation state.
  [Regression log](review/regression.log).
- Final GLB reimport matches the editable master within 0.01 mm. Half-frame samples check finite transforms,
  floor contacts and loop endpoints; Death joins Dead exactly. Maximum locomotion floor undershoot is 5.63 mm,
  below the playbook's 15 mm gate. [Export audit](work/export_audit.json).
- The existing browser viewer passes all 24 tier/clip selections with no console errors. Normal and half-speed
  playback, close mouth/paw/tail views and source-pose anchors are retained under `review/`.
- Native OpenGL/NVIDIA captures cover New Sorpigal (`oute3.odm`) and Agar's Laboratory (`6d19.blv`), all three
  sizes, forced LOD2, action poses and ordinary hostile approach/combat/death/remains.
  [Run records](review/ingame/runs.json), [action overview](review/ingame/action-overview.jpg).

The comparison fixture changes copied maps only. It declares the foreign sprite families and places immobile
actors with their native 60-unit height/radius. Initial attempts inherited town-NPC dimensions and were rejected.
Actors can still turn or fidget, so the sprite/model pose may differ. Production maps remain unchanged.
The review uses a saved executable to avoid mixing concurrent builds. Android and Vulkan were not tested;
these captures establish visual correctness, not performance.

## Reproduce or revise

Acquire the `mm8:m452` lease before writing. Run project Blender scripts through
`tools/run_creature_blender.sh --token <token> ...`; run other mutations through `tools/creature_workspace.py run`.
Retained service downloads avoid further paid generation.

The authoring chain is `prepare_body.py` → `rig_rat.py` → `uv_export.py` → `anim_rat.py`, followed by texture
composition, AO/grade and `reduce_review.py`. `export_asset.py -- r53` selects the reviewed reduction.
`fix_jaw.py` applies the final lower-lip correction to `work/rat_final.blend` and exports all eight clips.
The retained textures already contain the selected colour calibration; do not compound the gain.

Runtime processing is `tools/prepare_actor_glb.py` → `claude_shared/material_classes_to_orm.py` with
`textures/rat_material_classes.png` → `scripts/build_lods.py` → `scripts/shrink_shadow_lods.py` →
`scripts/audit.py` → `tools/install_model.py <export> --world mm8`. The final path is `export/mm8_m452.glb`.
`scripts/deliver.py` is a first-install binding helper and deliberately refuses duplicate bindings.
For revisions, preserve the three existing bindings and update the viewer's revision/hash after audit.

Run the focused regression with:

```sh
OPENYAMM_REGRESSION_FILTER=mm8_wererat_animal ./build/game/openyamm --world mm8 --headless-run-regression-suite actors
```

`scripts/prepare_reviews.py` prepares an isolated native fixture and comparison tours. Recorded launcher
arguments are in each native `run.json`. `scripts/viewer_playback.mjs` records all eight clips at 1× and 0.5×.
Intermediate renders and pre-correction exports are historical evidence, not selected deliverables.

## Sprint (2026-10-31)

`scripts/anim_sprint.py` opens `work/rat_gait2.blend` and adds one clip, `Sprint`: a full bound,
1.17 m stride in 0.3542 s (3.30 model units/s, for MAW's 2.83-4.14 chase), keyed at 96 fps on Run2's footfall
phases. It saves `work/rat_sprint.blend` (scene at 96 fps; the other clips keep their 48 fps keys) and the donor
`work/sprint_donor.glb`, and writes `work/sprint_report.json` (planted reach at most 0.964, lowest point -0.1 mm).
`SPRINT_DRY=1` prints per-frame reach and floor diagnostics without saving. `scripts/render_sprint.py` renders side
and three-quarter frames of Run2 and Sprint to `review/sprint/`. The Sprint clip is grafted onto the installed export,
then gated and installed, in [the reduce project](../mm8_m452_reduce_claude/README.md#sprint-2026-10-31).
