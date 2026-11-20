# MM8 Skeleton Archer — m628

Rigged 3D replacement for native monsters 172–174, with the three original colour tiers, articulated skeletal
hands and jaw, flexing longbow, drawn arrow, bow-mounted spare arrows, seven clips and four colour/shadow LODs.
The canonical production record is `creature_3d_progress.json`. User artistic acceptance is recorded separately.

Review: http://127.0.0.1:8912/level_generation/creatures/mm8_m628/review/viewer/

## Selected delivery

| File | Purpose |
| --- | --- |
| `export/m628_master.blend` | Editable rig, actions, retained source UV layers and packed textures |
| `export/mm8_m628.glb` | Portable final asset; 60 bones, maximum 3 influences at LOD0 |
| `../../../assets_source/worlds/mm8/models/mm8_m628.glb` | Authoritative installed source |
| `../../../assets_dev/worlds/mm8/models/mm8_m628.glb` | Cooked desktop runtime model |
| `../../../assets_dev/worlds/mm8/models/actors.yml` | `Skeletons Archer A`, `B`, `C` bindings |
| `textures/` | Body, separate 1K head and bow PBR maps, native region mask and tier ramps |
| `export/runtime_receipt.json`, `export/delivery_receipt.json` | Counts, hashes and installed paths |
| `review/viewer/` | Existing shared viewer, three palette previews, native frame comparisons |

LOD triangle counts are **12,067 / 5,992 / 2,885 / 1,346**, with two draws at each level. The last level is intended
for distant silhouettes; forced close-up captures deliberately expose its simplification. Body/head share one
merged atlas; all colour tiers share its images and recolour only the breeches using the original ACT ramps.
Viewer-only previews bake the ramps so the generic browser viewer displays them accurately.

The bow remains a separate **skinned primitive** in the shared rig: its limbs flex, the string deforms, the nocked
arrow appears/disappears, and the whole bow drops during Death. A rigid attachment would lose those motions.
This is an intentional exception to rigid-weapon splitting, with the same two-draw body/equipment budget.

## Native identity and motion

The 160 source BMPs were verified against `sources.json`. Native ACT palettes 629, 630 and 631 colour the
Bowman green, Hunter blue-purple and Archer red. The embedded BMP palette uses magenta recolour placeholders.
A/B retain native scale 1.199997 and C 1.0: upright model heights are 249.5994 / 249.5994 / 208 world units.
There is one long black glove and boot on the anatomical right; the left forearm/shin remain bare bone.
Spare arrows are carried along the lower bow, with no invented back quiver.

| Clip | Seconds | Source / purpose |
| --- | ---: | --- |
| Standing | 2.0 | Local `2HandBowIdle`, adapted to native low-hand carry |
| Walking | 0.8 | Local `2HandBowWalk`, planted soles; stride 1.966447 m |
| Attack | 1.233333 | Local `2HandBowAttack1`, continuous raise and fitted draw; release at **0.916667 s** |
| Hit | 0.5 | Local `2HandBowGetHitF1`, fits the native 0.75-second reaction |
| Fidget | 0.5 | Authored restrained head glance |
| Death | 1.033333 | Local `2HandBowDeath1`, independent bow release and ground clearance |
| Dead | 1.0 | Held final Death pose |

Both native attack roles use Attack, including the occasional fire arrow. Gameplay stats, AI and native action
timings are unchanged. No run clip is selected: native speeds at the calibrated sizes remain below the runtime
running threshold. `Socket_Arrow` follows the measured arrow tip at release; the ordinary projectile system owns
the fired projectile. Native locomotion timing is replaced by movement-driven 3D playback under existing rules.

The local source is `anim_library/humanoid_set/2Hand Bow.glb`, SHA256
`b0d046b7f26828dd1a68dd646de0e6081ef9b7694f728131020b18e130b51f48`.
No library animations were purchased. Source world bone frames were cloned, then fitted to this creature.
The bare hand has 19 capped rigid segments with small joint clearances; glove weights follow digit connectivity.

## Corrections and evidence

Body v2 retained the native asymmetry and thin bones. Both generated skull attempts fused the jaw/teeth; the
selected skull instead reuses our own MM6 skeleton's separated cranium, mandible and teeth, fitted inside the
m628 hood and retextured from its five head references. Protrusions/folds inside the eye sockets were removed.
Original service returns and rejected revisions remain immutable under `meshy/`.

Meshy omitted one 74.8 mm² rib triangle and moved three head corners by less than 0.1 mm. The animated master
retains its geometry; returned UVs were transferred by verified face correspondence, with a local bone-painted
chart for the omitted rib. Seventeen overlapping head triangles moved into empty atlas space at unchanged texel
density. Normal-map green channels were corrected using the shared convention check. Local AO and material
classes keep bone, cloth, leather, brass and wood distinct. See `work/texture_correspondence.json`,
`work/head_uv_repairs.json` and `work/uv_coverage.json`.

Dense fractional string keys keep the two string segments joined through the draw/release. Final review caught
excessive anatomical wrist bending during Attack; `correct_attack_wrists.py` limits the palm/forearm bend to
55° left and 50° right, preserves grip, and recalculates string/arrow contact. This correction changes only Attack
and its release socket. Death's dropped bow was separately moved clear of the collapsing torso.

The final numeric checks cover every clip: rigid bone edges, glove stretch, influence sums, soles, string joints
and 48 Hz rotation continuity against the local source. The early Death arm transition accelerates more than the
source because it leaves the native low-hand carry; its measured step remains modest and retained views show
continuous release. Evidence is in `work/motion_gates.json`, `work/final_motion_audit.json`,
`work/attack_wrist_correction.json` and `work/death_clearance.json`.

`work/export_parity.json` compares the actual GLB with the packed master at multiple times in every clip and
densely around release. Post-processing separately verifies byte-identical animation channels. The final viewer
switch check covers all 21 tier/clip combinations. Recorded normal/half-speed playback and captured frames live
in `review/playback/`; earlier clay evidence is retained in `review/playback_clay/`.

## Attack opening follow-up (2026-10-18)

The user reported the first 21 viewer frames as idle. They were a 13-frame Standing prefix at the authored
30 fps. `smooth_attack_opening.py` spreads the existing raise (old frames 13–22) across frames 0–22. The final
draw from 0.733 seconds, release at 0.916667 seconds, total duration and recovery remain unchanged. Every body
channel uses the same time mapping; `refine_motion.py` rebakes only the opening's string/arrow contacts at the
new fractional times. The bow starts moving immediately. Geometry, textures, rig, sockets and all six other
clips compare byte-for-byte unchanged in `work/attack_opening_export_audit.json`.

The selected work/master files already contain this change; do not apply it twice. The pre-change checkpoint
is retained under `work/attack_opening_v2/`. To replay from that checkpoint, run `smooth_attack_opening.py`,
then `refine_motion.py <project>/work/textured_uv.blend`, followed by the normal export pipeline below.
Normal/half-speed recordings are updated under `review/playback/`; prior recordings are in
`review/playback_textured_v2/`. The focused actor regression passes after installation; the broader suite and
indoor/outdoor comparisons below are retained from production because this follow-up changes only Attack.

## Runtime checks

The ordinary `openyamm` build and focused Skeleton Archer actor regression pass. The affected MM8 actor suite
reports **34 passed, 1 failed**: the Triton binding test also fails in the isolated fixture with all three new
Skeleton Archer bindings removed. Its logs are retained under `review/`; no Triton code or assets were changed.

Native engine PNG captures compare the three sprite tiers and models at the same cameras in New Sorpigal
(`oute3.odm`) and Agar's Laboratory (`6d19.blv`). Both model runs force LOD0–3. Captures and launch records are in
`review/ingame/`. Logs confirm NVIDIA (`vendor=0x10de`) on Wayland. Runs use isolated settings/saves and are visual
checks, not performance benchmarks. The indoor fixture adds distant native actors only to preload sprite
families; its scene is a private hard-link copy with the edited scene link broken first. Production maps are unchanged.

The tier/LOD comparisons precede the final Attack-only wrist correction; their geometry, materials, scale and
locomotion remain unchanged. `review/ingame/motion_final/` renders the final draw, release, fall and corpse through
the engine's model diagnostic. A live hostile-actor attempt moved outside the fixed camera, so its captures are
retained for provenance but are not relied on for attack-contact review.

Android and Vulkan were not tested. The user approved the general appearance, then requested a smoother attack opening.

## Reproduction and provenance

Resume from `work/textured_uv.blend`, the verified animated mesh with returned UVs and final wrist/contact fixes;
do not rerun the wrist correction on an already corrected action. `export/m628_master.blend` is the packed editable
delivery. Earlier scripts/checkpoints document the source-frame rig and anatomy work; they are intermediate
stages, not an instruction to regenerate paid jobs.

With a current creature workspace lease, use `tools/run_creature_blender.sh --token <token>` for Blender scripts
and `creature_workspace.py run` for other project writes. Final export order:

1. `scripts/materials_export.py`
2. `tools/prepare_actor_glb.py export/mm8_m628_raw.glb export/mm8_m628_lod0.glb`
3. `scripts/build_lods.py`, then `scripts/finish_runtime.py`
4. `scripts/export_audit.py`, `scripts/motion_gates.py`, `scripts/final_motion_audit.py`
5. `scripts/viewer_tiers.py`, shared viewer check/playback, then `tools/install_model.py export/mm8_m628.glb --world mm8`

Paths above are relative to this project where appropriate. The three native bindings retain calibrated scale,
stride and release time from `export/export_info.json`. Re-run affected runtime checks after changes.

Five body masters, five head masters and the isolated bow master are preserved in `references_hd/`,
`references_head/` and `references_props/`, with generation records. Meshy spent **50 of 100 credits** across seven
finished/downloaded jobs: four geometry jobs (20 credits) and body/head/bow retextures (30). Two geometry returns
were rejected. There are no pending paid tasks. The shared progress record contains task IDs, requests and hashes.
