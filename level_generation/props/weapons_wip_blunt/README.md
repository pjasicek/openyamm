# Blunt ground weapons — 2026-10-18

**Complete: all 43 rebuilt and installed; none kept or deferred.** All 43 exact desktop cooks passed verification.
Native acceptance passed on NVIDIA/OpenGL 3.3: 43 outdoor survey captures plus an unobscured Mace of the Sun detail,
and four indoor captures covering twelve representative constructions/materials. Both main final runs used the
same executable. Binary metal masks were retained without an indoor-lighting adjustment.

**Normal-map follow-up complete:** the sixteen Blender weapons now have height-derived tangent normals, so all
43 final models have base colour, metallic/roughness and normal maps. The follow-up passed all sixteen exact cooks,
sixteen outdoor captures and four indoor captures covering twelve representative designs.

This workspace owns the **43 icons** in [ownership.json](ownership.json). Production and native acceptance are
recorded per icon in [progress.json](progress.json); the coordinator receipt is [handoff.json](handoff.json).
This remains development WIP under `engine/world_items`, excluded from releases.

The rebuild replaces the original icon reliefs with physical cross-sections and separate forged heads, handles,
collars, flanges, curved picks, wooden bodies and closed chain links. The Warhammer, Sturdy Mace and Flail were
the initial construction pilots. Review rejected generic component versions of ornate heads; those received
individual HD masters and Meshy geometry. The final selection is **16 authored Blender icons and 27 icons from
24 Meshy designs**. Shared geometry is limited to the actual duplicate designs Thor/Holy Hammer, Ares/Death Mace
and Temple Mace/Mace of the Sun. Forty design groups cover all 43 icons.

## Evidence

- [Comparison 1](review/comparison_01.png), [2](review/comparison_02.png), [3](review/comparison_03.png),
  [4](review/comparison_04.png), [5](review/comparison_05.png), [6](review/comparison_06.png),
  [7](review/comparison_07.png): inventory icon, original relief, final clay, textured above, three-quarter, low and
  underside views. Full 320-pixel renders are in `review/blender*` and `review/meshy*`.
- [Geometry/UV/image validation](review/validation.json), [texture density](review/texture_density.json),
  [install and exact cook-verification logs](review/install_logs/).
- Native tours: [MM7 all-icons outdoor](review/native_outdoor_tour.json),
  [MM6 indoor constructions/materials](review/native_indoor_tour.json). Captures are in the corresponding folders;
  completed run records and the lighting decision belong in `handoff.json`.
- [Outdoor contact sheet 1](review/native_outdoor_sheet_1.png), [2](review/native_outdoor_sheet_2.png),
  [unobscured Mace of the Sun](review/native_outdoor_detail/01-item340_unobscured.png),
  [dim indoor material sample](review/native_indoor/04-right_wood_bone.png).
- Normal follow-up: [opposing-light comparison](review/normal_pass/raking_comparison.png),
  [outdoor detail sheet 1](review/normal_pass/native_outdoor_sheet_1.png),
  [2](review/normal_pass/native_outdoor_sheet_2.png),
  [indoor sample](review/normal_pass/native_indoor/04-right_wood_metal.png) and
  [generation/unchanged-geometry receipt](review/normal_pass/generation.json).

## Materials and modelling

All final exports use one opaque PBR material and embedded PNGs at 1024. The Blender components deliberately reuse
material regions in the imagegen-painted [UV atlas](textures/material_albedo.png), with UV insets of about eight pixels and an
explicit metal/roughness atlas. Steel and gold are metallic; wood, leather, red lacquer, bone, ivory and gems are
dielectric. Meshy maps were corrected where they classified bark, amber, ivory wraps or grips as metal. Corrections
use the actual UV triangles and physical shaft regions, rather than treating a whole mixed weapon as one material.
Metal masks are binary before any separately recorded native-lighting adjustment. Roughness is material driven;
it is not inferred from albedo brightness. Meshy tangent normal maps were converted to glTF/OpenGL +Y.

The sixteen Blender models share a new [normal atlas](textures/material_normal.png), derived analytically from
separately authored [material heights](textures/material_height.png). It adds shallow forging depressions, fine
tool marks, vertical wood grain and leather pebble detail. Enamel and decorated gold stay smoother. Height is not
inferred from painted brightness; existing painted ornament and quilt patterns are not converted into invented
relief. Normal detail stays subtle at ordinary ground-item distance. The sixteen accepted GLBs received one appended
normal image and material slot; all original mesh, UV, albedo and metallic/roughness buffer bytes remain identical.
The atlas uses glTF +Y, unit vectors and a flat eight-pixel border with an eight-pixel fade inside each material cell.
Checks include known height ramps, unit lengths, nonflat tile content and mixed-derivative correlation (+0.923).

The maps are clean local colour with no invented glow, light beam or environment. Geometry carries the volume;
the inventory painting is never pasted onto every side. The painted atlas and the Meshy returns retain fine
surface marks for game-distance readability. The source icons and generated references are preserved beside the
review evidence; every built-in imagegen prompt is in [textures/prompts.json](textures/prompts.json).

Export checks require no degenerate triangles, no open boundary edges, no opposed exported normals, outward closed
components, finite 0–1 UVs, power-of-two embedded PNGs, horizontal footprint length one, centered X/Z footprint and
minimum glTF Y zero. Small returned mesh gaps were closed with caps; nonplanar closures use a ring and short strips,
avoiding large vertex fans. A single loose Dwarven Hammer fin was removed, with its exact repair receipt retained.
Small opposed corner normals were corrected without repainting the artwork. The final total is **117,712 triangles**,
with every icon below the 15k ceiling. Chain links use eight major and four minor segments.

The standard static back-face cook adds 33 recorded reverse-face copies, producing **117,745 runtime triangles**;
this is accounted for in each icon's ledger rather than mistaken for source geometry drift. The largest source
is the three-head Justice flail at 5,276 triangles. The 75 unique PNG maps become 41,633,026 bytes of cooked textures;
the 43 runtime GLBs total 4,343,800 bytes. Shared paint atlases and true duplicate designs reuse cooked textures.
The shared normal atlas adds 284,351 cooked texture bytes across the sixteen models.

Resting angles derive from the head and grip support radii. Flail handles and heads rest separately, with the
chains laid between their attachments. Origins are at actual lowest contact, not at the old icon plane. Existing
binding lengths are retained. Density receipts state their world-unit calibration and measured effective density;
deliberate reuse of material swatches is not accidental UV overlap. Simple rigid props follow the existing static
installer/cooker path; no creature LOD or renderer feature was introduced.

## Reproduction and ownership

Use isolated background Blender processes with `scripts/build_blunt.py` for the sixteen selected regular icons.
`scripts/build_surface_normals.py` reproduces the height/normal atlas and appends it to the sixteen archived accepted
exports in `review/normal_pass/before/`; its assertions preserve their original buffer data. The regular generator
also binds this atlas for subsequent builds. `scripts/review_items.py -- blender <icons> --detail` and the same command
with `--without-normal` provide 768-pixel opposing-light comparisons.
`scripts/prepare_sculptures.py` prepares downloaded Meshy geometry; `scripts/finalize_pbr.py` makes PNG/PBR maps and
compacts unreferenced embedded data. `scripts/fix_export_normals.py` is the final corner-normal repair when needed.
The Dwarven fin receipt documents its additional targeted repair. Run `scripts/verify_blunt.py` before installation;
it selects `work/meshy/<icon>_export.glb` when present, otherwise `work/blender/<icon>_export.glb`.
Earlier component alternatives remain as studies and are not selected for installation.

`scripts/review_items.py -- <route> [icons] [--clay|--checker]` creates the exact-camera evidence.
`scripts/contact_sheets.py` assembles it. `scripts/install_owned.py` requires every icon ready and its validated
export hash unchanged, preserves unrelated sources, calls `tools/install_model.py --world-items` serially, then
explicitly runs `tools/cook_models.py --verify --profile desktop --only engine/world_items/models/item_<icon>.glb`
for **each** icon. It never rewrites bindings or gameplay tables.
An explicit icon list restricts installation and verification to those owned files; the normal follow-up installed
only its sixteen changed exports. The guard accepts the previously recorded source hash and rejects unexpected edits.

Unlimited Meshy spending was authorized by the weapon task. The operational bookkeeping ceiling was 2,000 credits;
**24 successful Smart Topology + PBR jobs consumed 15 credits each: 360 credits total**, with no paid failures or
duplicate submissions. Requests, task IDs, hashes and downloads are under `meshy/`; the dedicated
`engine:weapons-blunt` ownership lease was released after downloads. No credentials are stored.

No engine or shared-script changes, global builds/cooks, staging, commits, Android or release promotion are part of
this asset job. Native acceptance uses the ordinary desktop executable and isolated saves/settings.
