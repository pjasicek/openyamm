# Blaster refit — 2026-10-18

Five ground weapons are remade and installed to fit their actual inventory icons: MM7 pistol `7item064`, MM7 rifle
`7item065`, MM6 ray pistol `raygun1`, MM6 rifle `raygun2` and blaster shotgun `blastsg`.
The user explicitly requested this follow-up after the ranged batch. This project supersedes only those five
models from `weapons_wip_ranged_magic`; it does not alter the other ranged weapons or their original project.

**Complete:** five scoped desktop cooks verified, twenty final native captures reviewed on NVIDIA/OpenGL 3.3,
with no outstanding asset defects. [Handoff](handoff.json) binds the final source/runtime hashes and receipts.

The source/runtime scope is exactly [ownership.json](ownership.json). Existing binding lengths and IDs are retained.
Baseline sources, runtimes and icons are preserved in `references/`. The five corresponding `items.yml` bounds
entries now match the final geometry for placement and picking; icon/model mappings and lengths are preserved.
[Final binding bounds](bindings_with_bounds.json) and [exact five-entry changes](receipts/bounds_changes.json)
record the integration. Gameplay and engine code are unchanged. This remains `engine/world_items` WIP,
excluded from releases.

## Route and evidence

Built-in imagegen creates one faithful HD reference per icon. Five Meshy Smart Topology textured jobs provide
the corresponding geometry and maps. Local cleanup closes generated gaps, removes duplicated caps and attached
zero-thickness flaps, checks outward closed components and corrects opposed corner normals. Ground support comes
from a convex hull below the volume centre; MM6 rifle/shotgun expose their icon's receiver face.

The shotgun requires a hybrid correction: Meshy returned five emitters despite the corrected seven-emitter master.
`repair_shotgun.py` replaces the fan with exactly seven physical flared tubes, gold rims and blue mouths, retaining
the generated receiver. A 128-row atlas strip supplies their painted surfaces; the original receiver occupies
896 rows, preserving one material draw. `receipts/shotgun_bank.json` records the seven mouth centres.
The newly cut coupling cap uses the dedicated steel swatch, avoiding stretched UV fragments at the join.

Textures are 1024-square base colour, normal and packed metallic/roughness PNGs. Steel/brass are metallic;
red coating, ivory and blue/green indicator lenses are dielectric. The ivory mask uses the lower off-axis grip's
actual UV-mapped geometry. Roughness is material driven. Normal maps are converted from Meshy's measured negative
mixed-derivative correlation to glTF/OpenGL +Y. Normal strength is 0.75.

Review: [baseline](review/baseline_comparison.png), [icon/old/clay/new comparison](review/comparison.png).
Full above, three-quarter, low and underside images are in `review/meshy/` and `review/meshy_clay/`.
Per-icon state is in [ledger.json](ledger.json); `receipts/` records geometry, PBR, verification and installs.
[Outdoor normal/low views](review/native_outdoor_sheet.png),
[dim indoor normal/low views](review/native_indoor_sheet.png) and
[seven-mouth close view](review/meshy_detail/blastsg_raking_left.png) show the final assets.
The final outdoor and indoor runs used the same executable and both exited normally. Pure metal is dark in the
unlit cave; binary masks are retained, with daylight/studio views establishing the full colours.

The five source/runtime models total **23,394 triangles**, ranging from **4,114 to 4,900** per model. Each has
one opaque PBR material and three embedded 1K PNG maps. Runtime GLBs total 933,468 bytes; the fifteen cooked
textures total 8,446,196 bytes. The standard static model path is retained; no creature LOD builder or renderer
change was introduced. These are detailed rigid props below the approximately 5k rigid guideline and 15k hard cap.

All built-in imagegen prompts and outputs are retained in `references/prompts.json`, `references/masters/`, and
`textures/`. The first six-emitter shotgun master is explicitly rejected and preserved alongside its correction.
The Meshy project has a separate identity, `engine:blasters-refit-20261018`. The existing unlimited weapon-scope
authorization applies; the operational bookkeeping ceiling is 600 credits. Five successful jobs cost 15 credits
each, 75 credits total. No paid retries were required.
The dedicated Meshy lease is released. Android/device cooking, release packaging and performance benchmarking
were not performed.

## Reproduction

Use separate background Blender processes. Run these stages in order, waiting for each to finish:

1. `scripts/prepare_models.py` in Blender: original downloads to grounded `work/meshy/*_raw.glb`.
2. `python3 scripts/pack_bank_textures.py`, then `scripts/repair_shotgun.py` in Blender.
3. `python3 scripts/finalize_pbr.py`.
4. `scripts/choose_ground_faces.py`, then `scripts/fix_export_normals.py` in Blender.
5. `python3 scripts/verify_models.py`; visual review with `scripts/review_items.py -- meshy [--clay]` in Blender.
6. `scripts/install_owned.py` installs only validated, accepted hashes via the serialized standard installer and
   verifies each exact desktop cook. It accepts the recorded baseline or its own previous installed hash.

Do not rerun `choose_ground_faces.py` twice without regenerating its inputs; it turns the two models over.
Native outdoor review uses actual ground items in the unchanged MM7 all-items save. Indoor material review uses
the existing unobstructed MM6 `6d19.blv` entrance-floor fixture at actual item binding lengths.
