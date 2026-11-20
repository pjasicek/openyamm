# MM8 Human Mercenary — m656

Full Claude humanoid-playbook production for Soldier of Fortune, Mercenary and Captain (merged monster ids 193–195).
The new body follows the native dark studded armour, horned helmet, cheek guards, moustache, green/blue/red cloth,
right-hand straight sword and left-hip black scabbard. The Chain Fighter and Barbarian projects supplied workflow
and source-frame rig techniques; this creature has its own references, geometry, fitted joints and textures.

## Delivery

- `work/mercenary_final.blend`: packed editable master, 120 Hz export timeline.
- `export/mm8_m656.glb`: portable body, three palette variants and colour/shadow LODs.
- `export/mm8_m656_sword.glb`, `export/mm8_m656_scabbard.glb`: rigid runtime attachments.
- `review/viewer/`: shared review viewer, three tiers and all eight clips. Viewer-only GLBs bake the runtime palette
  rule for three.js; installed models retain one base texture set and semantic masks/ramps.
- `export/install_receipt.json`: installed source/runtime hashes; `creature_3d_progress.json`: canonical receipts/state.

Body triangles: 10,623 / 5,309 / 2,653 / 1,285. Sword: 136 / 68. Scabbard: 164 / 82 / 40 / 24.
58 bones, four influences maximum, one 1K body set and one 1K head set merged into a padded 2080×1024 runtime atlas;
each prop uses a 256×1024 set. ORM is specular mask / roughness / zero metallic. Meshy normal maps are converted to
OpenYAMM's glTF convention by `prepare_actor_glb.py`.

The sword deliberately stops at its verified 68-triangle LOD: further collapse made the thin blade disappear
edge-on. The extra distant triangles preserve an important part of the silhouette. The body budget preserves the
face, helmet and individually fitted fingers. Distant body LODs simplify the studs, armour edges and hands.

## Motion and scale

Standing 3 s; Walking 1 s; Running 0.733333 s; Attack 1.766667 s; Hit 0.5 s; Fidget 2.833333 s;
Death 3.633333 s; Dead holds the final death pose for 1 s. Local humanoid-set and Mixamo sources are listed with
hashes in `motion_selection.json`. No paid animation clips were purchased.

Meshy's joints are a proposal; the final rig retains the source animation's rest frames, fitted glove cuffs and
connectivity-based fingers. Forearm/upper-arm twist helpers distribute roll. The raised-sword carry uses the
measured fist and a 10.5 mm grip radius. Armour plates have consistent rigid/blended weights. The fidget's opening
arm crossing was corrected and its short IK transitions smoothed. The scabbard hangs from the left side of the belt with an outward cant. The empty arm clears it throughout locomotion.
During the fall the sheath swings outward at the belt, with a smooth floor-preserving sweep;
the right hand keeps the sword above the floor without releasing its grip. The corpse holds that equipped pose.

The measured attack contact is 1.017 s, near the native 1 s action. Gameplay timing is unchanged. Runtime stride
lengths are 1.783 m walking and 3.864 m running. Scale 112.224675 maps the 1.693032 m upright body to the native
190-pixel body (excluding the raised sword); all three native tiers have equal standing scale. Head look is limited
to 30° yaw / 15° pitch to suit the helmet and pauldrons.

## Evidence

Native: all 150 BMP hashes verified; `references_native/inventory.json` records descriptors, palettes and timelines.
HD: five body views and four head views with generation receipts; original imagegen returns and original Meshy
returns are retained. Smart Topology, rig, body retexture and head retexture cost 5 + 5 + 10 + 10 = **30 credits**
against the default 100-credit limit. Sword/scabbard are locally modelled from their isolated generated prop sheet.

UV transfer matched every face with zero positional discrepancy. Body UV interiors have no overlaps; head
raster overlap is 0.11% at 512 pixels, within the boundary-raster tolerance; neither set has degenerate UV triangles.
Dense export checks at 48 Hz found a maximum surface discrepancy of 0.613 mm (the fast run between 120 Hz samples),
and at most 0.046 mm at integer source frames. Linear contact keys avoid Bézier overshoot between export samples.
No degenerate exported triangles or inverted closed components were found. `review/export_audit.json` records
per-LOD diagnostics; `review/lod_review.png` shows standing, run, attack and corpse at each detail level.

The selected revision is **m656_equipped_v3**. Ordinary development build passed. All **21 MM8 actor regressions**
passed, including the new Mercenary test; that focused test also passed with MM6 active and no Mercenary sprite
metadata supplied to the model bindings. All three tiers use explicit equal scale, avoiding a cross-world lazy-load
failure from `scale_reference`.

The shared viewer checker passed all **24 tier/clip combinations**. Actual browser playback covered all eight clips
at normal and half speed; close-ups cover all palettes, face and both hands. At 48 Hz, the exported sword had no body
penetration and the scabbard had **zero body triangle intersections** in every clip. The smallest body floor value is
−0.79 mm during running; all other clips stay above the floor. Head/shoulder contact stays within the 5 mm review
threshold. Logs and receipts are under `review/`.

`review/ingame/` contains the three tiers approaching, fighting, falling and becoming normal runtime loot remains,
in New Sorpigal and Agar's Laboratory on the NVIDIA/OpenGL desktop renderer. Native comparison uses the same cameras.
The indoor native sprites required an isolated fixture that preloads their unchanged family definitions into the
common frame table; its provenance is recorded alongside the captures. Some unrelated HUD graphics are absent in
that linked fixture mount. All model captures use the ordinary development assets. No engine behavior was changed.

The last revision changes only green-contaminated nape hair to brown. `review/final_revision_equivalence.json`
verifies identical geometry, skin, skeleton and animation samples against the fully played-back revision. The final
material was checked again in the viewer and native game. Final playback, regression and capture receipts are recorded
in the progress JSON. Technical and
agent visual completion are separate from user artistic approval. Android/Vulkan builds and performance benchmarks
are outside this asset-validation run. Original sprites and unrelated world bindings are preserved.

## Body retexture v2 and no cheek guards (2026-10-19, installed)

User review of the triangle reduction: remove the helmet's cheek guards and retexture the body (10 credits approved).
Installed 2026-10-19 with the raised studs (v3) and the reduced mesh: the installed source is
`../mm8_m656_reduce_claude/export/mm8_m656.glb` (8,093 triangles), no longer this project's `m656_equipped_v3` export.

- `scripts/make_body_upload_v2.py` writes `texturing/mercenary_body_upload_v2.glb`: the v1 Meshy return's own mesh and
  UV layout (the layout `transfer_uv.py` copied to `UVMap`) without its images. Job `body_retexture_v2`
  (`requests/body_retexture_v2.json`: meshy-7, the four `references_hd` views, `enable_original_uv: true`, 2K) cost
  **10 credits** (total now 40). The return keeps every face corner's UV, so the new maps fit the existing body UVs
  and the reduced mesh unchanged. meshy-7.1 is refused for retextures (m484, m568), so meshy-7 was kept.
- The result is close to v1: mean base-colour difference 5.7/255, the same fine-detail level, and the same flat yellow
  studs (slightly smaller and more numerous). The same references give Meshy the same answer.
- `compose_mercenary.py` now takes `MERC_BODY_RETEXTURE`, `MERC_TEXTURES` and `MERC_CHEEKLESS` (defaults reproduce
  `textures/` byte for byte). `MERC_CHEEKLESS=1 MERC_BODY_RETEXTURE=body_retexture_v2 MERC_TEXTURES=textures_v2`
  writes `textures_v2/`. The cheek skin the guards covered has the flat skin colour without Meshy's dark
  guard-shadow blotch. On the rim behind them, tan smears take the nearby steel colour. Ramps are re-measured; the
  region mask changes by 0.5/255 on average.

## Raised studs, textures v3 (2026-10-19, installed)

User choice after v2: "Add stud relief, then show me". Local texture work only (no credits, no geometry or UV change):
`scripts/stud_relief.py textures_v2 textures_v3` (under the workspace guard).
- Studs are yellow/brass blobs on the armour, glove, boot, pauldron, bracer and skirt pieces. Each is kept when it is
  8-140 texels, compact and much brighter than its leather ring. The belt, buckle, belt hardware, fur cuffs and spikes
  are excluded by piece. Helmet rivets on the head set: 3-60 texels. Found: 300 body studs and 22 helmet rivets
  (`textures_v3/stud_report.json`, previews `work/studs/<part>_mask.png`).
- Meshy's ragged blobs are redrawn as the ellipse of each blob's second moments (same centre, area and UV stretch,
  aspect at most 1.8), clipped to its UV island. The leather under the old blob is filled from the nearest leather.
- Normal map: a dome per stud (about 0.9 × its short radius in texels), blended in Meshy's +y-down convention like the
  rest of the composed folder. A grazing-light render confirms the studs are raised.
- ORM: studs at specular mask 1, roughness 0.30 on top to 0.48 at the rim; metallic stays 0.
- Base colour: one brass for all tiers, lighter on the dome and darker at the rim, with a 2-texel contact shadow on the
  leather. The native studs (palette entries 164/165) are the same olive-yellow in 657/658/659, so the studs leave
  the region mask instead of taking the armour ramp's top stop. Ramps are v2's, unchanged.

## Reproduction

Claim this project using `tools/creature_workspace.py` before writes; use `tools/run_creature_blender.sh --token`
for every Blender script and the guarded runner for ordinary scripts. Meshy original jobs must be reused, not resubmitted.
The selected resumed authoring base is `work/master_settled.blend`; historical intermediate masters are retained as
evidence and are not interchangeable with it.

The final export sequence is `export_runtime.py`, `tools/prepare_actor_glb.py`, `lods_and_parity.py`,
`finalize_exports.py`, `audit_exports.py`, then `tools/install_model.py` for body and both attachments. Texture
composition is `compose_mercenary.py`; `viewer_tiers.py` creates browser-only palette previews. The project scripts
record explicit inputs/outputs and assertions. Runtime binding entries live in `assets_dev/worlds/mm8/models/actors.yml`.

The native capture tours use the playbook's New Sorpigal and Agar's Laboratory cameras, with all three tiers spawned
in one console session and the same camera for model/sprite runs. They include approach, combat, death and remains.

## Review and resume

Local viewer: <http://127.0.0.1:8656/level_generation/creatures/mm8_m656_claude/review/viewer/>.
If the server has stopped, run `python3 -m http.server 8656 --bind 127.0.0.1` from the repository root.
The native gallery is `review/ingame/`; `review/final_playback_grid.png` and `review/lod_review.png` summarize motion
and silhouette checks. The `.blend` and separate runtime GLBs are listed under Delivery above.

To reconstruct the equipped authoring base: `make_props.py` → `arm_clearance.py` → `finalize_motion.py` →
`equipment_floor.py` → `scabbard_sweep.py`. The sweep replaces every 120 Hz contact key before export; leaving the
old quarter-frame keys would reintroduce transient clipping. Recompose maps with `compose_mercenary.py`, then use
the export sequence above. The recorded physics, parity and native checks must be revisited for motion changes.
