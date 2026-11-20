# MM8 Salamander — m568

Rigged production for **Fire Newt, Fire Lizard and Salamander** (IDs 127–129), following the shared Claude creature playbooks. The body, forked polearm, nine animations, three native palette tiers and four LOD levels are delivered. User artistic acceptance has not been recorded.

[Interactive review](http://127.0.0.1:8901/level_generation/creatures/mm8_m568_claude/review/viewer/) · [Editable master](export/mm8_m568.blend) · [Portable bronze GLB](export/mm8_m568_portable_a.glb) · [Blue](export/mm8_m568_portable_b.glb) · [Red](export/mm8_m568_portable_c.glb) · [Canonical progress](creature_3d_progress.json)

![Native sprites and models at matching cameras](review/ingame/comparison.jpg)

## Source and construction

The 160 original BMP hashes were checked against `../mm8_m568/sources.json`. Native groups m569/m570/m571 use palettes 569/570/571. The [native study](ANIMATION_STUDY.md), source sheets and [HD reference history](references_hd/generation_runs.json) retain the evidence and corrections. The short rear tail, continuous J silhouette, spotted scales, narrow ribbed crest and forked polearm are authoritative. Five digits and unseen surfaces are interpretations of the small sprites.

Meshy Smart Topology v2 supplies the corrected body. Local fitting shortened the tail, repaired a displaced thumb and removed duplicate digits. The 74-bone rig uses 26 measured serpent segments, fitted arm frames, distal forearm twists and five connected finger chains per hand. Owned spear clips were reviewed; native-authored arm IK and serpent motion fit this anatomy better than biped lunges. The polearm is locally modelled and remains a separate rigid runtime attachment.

Body and head multiview retextures preserve the animated geometry. Verified face correspondence transfers the service UVs back; seven repaired hand-cap facets use a bounded projection within one UV island. This prevents those tiny caps from contaminating unrelated UV islands during AO baking. The neck blends the body paint into the dedicated head map. Normal green channels were corrected, material classes set roughness/specular, and short-range AO is baked into colour/specular. Native palette ramps share the body maps across tiers and recolour only the grips on the weapon.

**Meshy cost: 30 credits:** two 5-credit geometry jobs and two 10-credit retextures. A rejected model-version request consumed zero. Originals, requests, task IDs and receipts remain in the canonical record.

| Asset property | Delivered value |
| --- | --- |
| Body colour LOD triangles | 12,490 / 6,243 / 3,122 / 1,549 |
| Polearm colour LOD triangles | 268 / 134 / 66 / 30 |
| Skinning | 74 bones, at most four normalized influences |
| Body maps | Shared 2080×1024 body/head atlases; one material per tier |
| Polearm maps | Compact shared atlas, steel/wood/cloth classes |
| Scale | 197 native pixels × 1.299988 / measured upright model height = 106.707292 world units/metre |
| Tier sizes | Identical native sizes; colours differ |

Bent-pose reduction protects the face, hands, crest and UV boundaries. Reduced shadows tuck the connected body inside its colour surface; thin claws, crest ribs and equipment retain their volume. All finished colour/shadow meshes pass the closed-part winding check with zero inverted parts.

## Animation and runtime

| Clip | Seconds | Behaviour |
| --- | ---: | --- |
| Standing | 3.0 | Quiet upper body and tail |
| Walk | 1.0 | Grounded travelling tail wave |
| Running | 0.75 | Faster, wider wave |
| Fidget | 0.625 | Left hand releases and lifts; right retains the shaft |
| Attack | 1.333333 | Gather, raised strike at 1.0 s, recover |
| Cast | 1.25 | Raise and release Fire Bolt at 1.0 s, recover |
| Hit | 0.625 | Backward recoil and raised weapon |
| Death | 0.75 | Both hands release; body falls, weapon settles beside it |
| Dead | 1.0 | Exact held final death pose |

The 48-fps keys preserve native gameplay action timing. Existing event markers fit attack/cast contact to the native one-second release, with recovery continuing afterward. Upper-body overlay begins at `B_Pelvis`; head look uses `B_Neck`/`B_Head` with 30° yaw and 20° pitch limits. Strides derive from each tier's native movement speed and the measured scale.

The cast charge/release is on the upper shaft just below the fork, at `Polearm` offset `[0, 0.58, 0]`. The separate `Socket_Polearm_Tip` marks the actual tip. The upper-shaft release stays inside the existing engine launch bounds even at full lift; gameplay bounds and timing were not changed.

Installed source files are `assets_source/worlds/mm8/models/mm8_m568.glb` and `mm8_m568_polearm.glb`. `tools/install_model.py` produced their cooked desktop copies under `assets_dev/worlds/mm8/models/`. The three entries in that world's `actors.yml` select `m568_a/b/c` and attach the polearm at `Polearm`; original sprites and unrelated bindings are preserved.

## Validation

- The ordinary `openyamm` build and focused Salamander actor regression pass. Coverage includes all tiers, native simulation state, clips, carried equipment, cast contact time and the usable launch point.
- The broader MM8 actor suite reports **8 passed, 2 failed**. The separate Mercenary and Ether Knight tests lack their model bindings in the current workspace; their names are absent from `actors.yml`. Their content was not changed here. Logs are retained under `review/checks/`.
- [Dense export checks](review/checks/export_audit.json) sample every half frame. No hand/torso or weapon/torso intersections; maximum held-grip interpolation error 3.79 mm. The death transition has 1.45 mm maximum floor undershoot at half frames on a 2.4 m body; the held corpse is grounded. Reimported surfaces and the tip socket match the editable master within 0.1 mm.
- The existing viewer checker switches through all **27 tier/clip combinations** with zero console errors. [Normal/half-speed playback](review/playback/playback.json) records 54 WebMs. The final corpse arm adjustment has replacement Death/Dead playback in `review/playback_death/`. Front, side, back, face, grip and corpse stills are retained in `review/browser/` and `review/angles/`.
- Native review uses the authorized isolated desktop launcher, OpenGL 3.3 and NVIDIA on Wayland, with native engine screenshots. Matching sprite/model cameras cover New Sorpigal and the Temple of Baa, all tiers and forced LOD2; the combat tour covers attack, hit, death and the existing loot transition. The [Fire Bolt capture](review/ingame/cast_review.jpg) verifies the upper-shaft charge glow and projectile release. Its isolated table copy forces Spell1 selection to 100% and makes the actor stationary; production chance, movement and speed are unchanged. Run records and captures are under `review/ingame/`.

The comparison fixture adds foreign sprite preload declarations to isolated hardlinked map copies. The final cast-only run also uses the explicitly recorded isolated table override in `review/ingame/fixture.json`. Original map and monster-table hashes were verified unchanged. Live friendly actors can turn or wander between captures; cameras and initial spawn positions match. This is a visual review, not a performance benchmark. Android and Vulkan were not tested.

## Reproduce

Claim `mm8:m568` at this project with `tools/creature_workspace.py` before writing. Use the ownership guard for ordinary writes and the existing Blender/Meshy wrappers for their jobs.

1. The selected geometry/rig inputs are retained in `work/`; `fit_geometry.py`, `fit_fingers.py`, `build_rig.py`, `solve_grips.py` and `prepare_texturing.py` record their construction.
2. Run `animate_salamander.py`, `transfer_body_uv.py`, `uv_raster.py`, `bake_ao.py`, then `compose_salamander.py`. Geometry/UV edits require a fresh AO bake; animation-only edits do not.
3. Run `export_salamander.py` and `audit_export.py`. Prepare the raw export with `tools/prepare_actor_glb.py`, run `build_lods.py`, then `finish_runtime.py` for corrected shadows, variants, equipment split and head merge.
4. Run `viewer_tiers.py`, `update_viewer_manifest.py` and `pack_editable.py`. Install both final runtime GLBs with `tools/install_model.py --world mm8`. `deliver.py` is an initial binding append and refuses to replace existing entries; revise only this family's entries on maintenance runs.
5. Run `OPENYAMM_REGRESSION_FILTER=mm8_salamander ./build/game/openyamm --world mm8 --headless-run-regression-suite actors`, the shared viewer checker, and affected playback/native checks. `prepare_reviews.py` records the isolated fixture and tours. Preserve selected hashes and actual review results, then release the lease.

No staging or commit was performed.
