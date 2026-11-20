# MM6 Gargoyle — Codex

Selected revision: **mm6_gar_codex_v6_attack_momentum**, 2026-10-12. Installed and technically verified;
the user approved the stronger Attack on 2026-10-12. The 7,247-triangle reduction was already accepted;
separate explicit approval of the earlier toe placement and textures is not recorded.

Attack now draws the torso back before driving the chest and hips forward through the right-hand swipe.
Six pelvis/spine/neck/head rotation tracks and pelvis translation carry the motion, while the existing arm curves
and left-hand balance remain. Impact is still **0.75 s** within the **1.5 s** action; ready endpoints are unchanged.

- [Backward preparation](review/attack_v6/windup.png), [forward delivery](review/attack_v6/impact.png),
  [sampled quarter-speed playback](review/attack_v6/playback_sequence.png)
- [Motion/clearance check](work/attack_v6/motion_check.json): zero intersections across 181 exported poses;
  early elbow speed 1.42 m/s, frame 6–8 travel 0.0499 m, peak forward wrist reach exactly at 0.75 s.
- [Animation-only audit](work/attack_v6/animation_only_audit.json): geometry, materials, UVs, skins, LODs,
  back-face processing and all four other clips remain byte-identical in every GLB.
- [Viewer](review/attack_v6/viewer_check.json): all 15 tier/clip combinations pass;
  [playback](review/attack_v6/playback_check.json) reaches the full Attack endpoint at normal and quarter speed.
- [Focused runtime regression](review/attack_v6/gargoyle_regression.log): 1 passed, 0 failed.
  [Final desktop capture](review/attack_v6/game/outdoor/attack.png): outdoor OpenGL run completed successfully.
  Indoor appearance evidence below is retained from v5; no indoor recapture was needed for this Attack-only edit.

To reproduce v6 after the v5 pipeline below, run Blender `scripts/attack_momentum_v6.py`, then guarded Python
`scripts/install_attack_v6.py`. They use immutable v5 snapshots in `work/attack_v6/` and replace only seven Attack
channels in each handoff. Run Blender `scripts/check_attack_v6.py` and `scripts/gar_verify_export.py`, then the
viewer/runtime checks and refresh delivery hashes. Do not regenerate geometry or buy a new animation.

The two added foot claws now grow into the soles instead of leaving exposed, blunt rear caps. The repair is local
to those roots and retains four claws per foot. The body and wings have independent UV layouts and Meshy texture
sets, each shipped at **1024×1024**. All three head maps remain pixel-identical to v4. The enlarged hands and
corrected right-hand swipe, body sway, left-arm balance and smooth early wind-up are retained.

- [Interactive viewer](http://127.0.0.1:8912/level_generation/creatures/mm6_gar_codex/review/viewer/)
- [Front](review/parts_v5/front.png), [quarter](review/parts_v5/quarter.png), [back](review/parts_v5/back.png)
- [Textured feet](review/parts_v5/feet.png), [sole inspection](review/parts_v5/feet_below.png),
  [original feedback](review/parts_v5/user_toe_feedback.png)
- [Attack](review/parts_v5/attack.png), [settled fragments](review/parts_v5/dead.png)
- [Outdoor tiers](review/parts_v5/game/outdoor/tiers.png), [indoor tiers](review/parts_v5/game/indoor/tiers.png)
- [Canonical progress](creature_3d_progress.json), [delivery hashes](export/delivery.json),
  [installation receipt](work/installation.json)

## Deliverables

2026-10-14: the installed model is this export plus body/rubble swap keys (the collapsed mesh is no longer drawn);
see [mm6_gar_reduce_claude](../mm6_gar_reduce_claude/README.md). Rerun `tools/model_hide_collapsed_meshes.py` on any
new export before installing it.

| Artifact | Path |
| --- | --- |
| Editable packed Blender master | `export/mm6_gar.blend` |
| Portable animated GLB | `export/mm6_gar_lod0.glb` |
| Runtime GLB with tiers and colour/shadow LODs | `export/mm6_gar.glb` |
| Installed model | `assets_dev/worlds/mm6/models/mm6_gar.glb` (repository root) |
| Bindings | `assets_dev/worlds/mm6/models/actors.yml`: BGargoyle A/B/C, IDs 541–543 |
| Body, wings, head texture sets | `textures/{body,wings,head}_{basecolor,normal,metal_rough,regions}.png` |
| Texture composition receipt | `work/parts_v5/composition.json` |
| Shared native palette ramps | `textures/gar_ramps.json` |
| Clip roles and durations | `work/animation_manifest.json` |

The authored living model has **7,247 triangles**, down from 14,497: body 3,764, wings 485, head 2,998.
Its authored LOD chain is **7,247 / 3,621 / 2,605 / 866**. The normal transfer preserves the smooth surface shading
that the user accepted. Distant LODs retain the previous approximate budget because automatically halving those
again shortened the wings' picking bounds; the focused runtime regression now passes.

Runtime back-face processing adds a few reversed faces where they can be seen: the installed living chain has
**7,249 / 3,675 / 2,655 / 921** triangles, and rubble has **6,545 / 3,273 / 1,180 / 491**.
Each part keeps its own material and 1K maps instead of merging into the former head/body atlas. Stone, Marble and
Diamond share those texture sets and rig, using native palette ramps 736/737/738. The normal maps use the verified
glTF convention; the packed material's red channel remains the runtime specular mask.

The rig has 66 live bones plus 36 independent fragment bones and at most eight influences per vertex.
Flight is a 0.75-second loop; Attack is a 1.5-second right-hand swipe with impact at 0.75 seconds; Hit is 0.75 seconds.
Death lasts 0.95 seconds, switches to fragments at 0.10 seconds and ends in held Dead. Standing/walking/running use
Flight; attack2/fidget and the required loader cast role use Attack. These native monsters remain melee-only.
Runtime scale remains 94.29 units/metre, with B/C retaining native 0.75/0.80 frame scales through `scale_reference`.

## Provenance and rebuilding

The shared Claude playbooks remain the procedure. Native source sheets live in `../mm6_gar/`; selected generated
body/head references and provenance are in `references_hd/` and `references_head/`. Both new texture jobs use the
selected three-quarter stone reference and `enable_original_uv: true`. Immutable 4K Meshy returns are retained in
`meshy/body_texture_v5/` and `meshy/wings_texture_v5/`; runtime composition reduces each to 1K.

Total Meshy spending is **60/100 credits**: original body/head geometry 10, earlier body/head texture jobs 30,
and the two new part retextures 20. No paid rig or animation job was used. The head remains `head_texture_v1`.
The body’s UV directional stretch at the 95th percentile is 1.48×, and the wings' is 1.53×. The wing map now covers
438,652 occupied texels. Fracture interiors use an undistorted stone patch from that same map; intact fragment
surfaces are reprojected to the new part UVs.

Claim the top-level `mm6:gar` project with `tools/creature_workspace.py` before writes. Blender scripts run through
`tools/run_creature_blender.sh --token <token> <script>`; ordinary Python operations use the workspace guard.
Stop on a nonzero exit. Starting from retained checkpoints and downloaded texture returns:

1. Blender `scripts/prepare_parts_v5.py` reads the preserved v4 master/LODs in `work/parts_v5/`, repairs roots,
   promotes the accepted geometry and writes `work/parts_v5/parts.blend` plus independent part UVs/uploads.
2. Blender `scripts/verify_parts_v5.py` validates both retained Meshy returns against those part meshes and UVs.
3. Guarded Python `scripts/compose_parts_v5.py` composes the new maps while preserving the head.
4. Blender `scripts/export_parts_v5.py` updates living/fracture materials and exports the unchanged actions.
5. Blender `scripts/gar_verify_export.py` verifies master/portable deformation parity.
6. Guarded Python `tools/prepare_actor_glb.py <project>/export/mm6_gar_lod0.glb <project>/export/mm6_gar_prepared.glb`.
7. Blender `scripts/build_lods.py`, which includes `scripts/preserve_lod_normals_v5.py`.
8. Guarded Python `scripts/gar_pack.py` builds the native variants and existing review viewer files.
9. Blender `scripts/install_runtime.py` installs the asset, processes back-face culling and syncs the delivery copy.
10. Guarded Python `scripts/audit_parts_v5.py`, then update delivery/progress hashes and repeat affected checks.

Do not rerun paid jobs for an ordinary rebuild. Earlier fitting, hand and attack scripts remain historical/deeper
editing checkpoints; running the old `export_final.py` sequence directly would discard the v5 part revision.

## Retained v5 verification and limits

- [Part correspondence](work/parts_v5/texture_correspondence.json): Meshy retained geometry within 0.0001 mm and
  UV corners within 0.00000003. Only its textures were used.
- [Export parity](work/export_parity.json): 244 poses across all five clips; maximum master/GLB error 0.011 mm.
- [Final audit](work/parts_v5/audit.json): all five animation sampler arrays exactly match v4, finite attributes,
  correct 1K maps, valid LOD chains and matching installed/export hashes. Head maps are pixel-identical to v4.
- [Viewer check](review/parts_v5/viewer_check.json): all 15 tier/clip combinations pass without browser errors.
  [Playback check](review/parts_v5/playback_check.json): normal and quarter speed. Foot undersides, wing fronts/backs,
  attack and death fragments were inspected in the viewer.
- [Focused Gargoyle regression](review/parts_v5/gargoyle_regression.log): **1 passed, 0 failed**. Reproduce with
  `OPENYAMM_REGRESSION_FILTER=mm6_gargoyle_actor_model_tiers_clips_and_rubble ./build/game/openyamm --world mm6 --headless-run-regression-suite actors`.
- [Native captures](review/parts_v5/game/): outdoor `oute3.odm` and indoor `6d19.blv` completed on NVIDIA OpenGL 3.3
  / SDL Wayland. These show the final authored geometry/textures/actions; the distant LOD budget was subsequently
  restored and verified by the runtime regression. The previous indoor console-input blocker did not recur with
  longer input-settle intervals.
- Historical attack evidence remains in `review/attack_v4/`: the elbow snap and arm/wing intersection corrections
  are preserved. The old v3 full-suite Lizard failure is historical; this revision reran the affected Gargoyle case.

The Diamond Gargoyle survives the physical `actor kill` command by native immunity; Death/Dead was checked in the
viewer. Its indoor spawn is raised by a pillar. Viewer studio lighting is brighter than the indoor scene.
Android/Vulkan were not tested. No engine/renderer code change, rebuild or commit was needed for this revision.
