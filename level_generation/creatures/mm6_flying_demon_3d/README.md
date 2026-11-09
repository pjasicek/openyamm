# MM6 Flying Demon — selected production delivery

The Flying Demon is a separate derivative of the selected walking-demon master. The original project and preserved source copy have the same SHA-256. All three production stages are complete; user artistic acceptance has not been recorded. Runtime installation is separate.

Open [the animation review](index.html) through the existing local server:
http://127.0.0.1:8901/level_generation/creatures/mm6_flying_demon_3d/

Choose an animation and view, scrub its 48-fps timeline, or play at normal, half or quarter speed. The native view is shown beside the actual exported model renders. Report a correction as animation + frame + view + region. Motion shows purple A; the three colours have matching geometry and animations, and their material/detail comparisons are below the player.

| Deliverable | Selected file |
| --- | --- |
| Editable master, packed textures, rig and all clips | [mm6_flying_demon.blend](delivery/mm6_flying_demon.blend) |
| Purple A / ochre B / dark-red C | [A GLB](delivery/mm6_flying_demon_a.glb), [B GLB](delivery/mm6_flying_demon_b.glb), [C GLB](delivery/mm6_flying_demon_c.glb) |
| Clip/component/palette manifest and hashes | [delivery/manifest.json](delivery/manifest.json) |
| Native anatomy and action interpretation | [STUDY.md](STUDY.md), [motion_study.json](motion_study.json) |
| Every joint at native anchors, including digits and twists | [POSE_GUIDE.md](POSE_GUIDE.md), [pose_manifest.json](pose_manifest.json) |
| Canonical progress, paid jobs and correction ledger | [creature_3d_progress.json](creature_3d_progress.json) |

| Stage | Status | Result |
| --- | --- | --- |
| Native references and motion study | Complete | Native descriptors 499/500/501, all source actions and genuine views; reused existing HD references with crop/hash provenance. |
| Model and rig | Complete | Slender body, no harness/clasp/tail, smaller ears, curved ivory horns, independent bat-wing controls and repaired skin. |
| Animation, UVs, materials and delivery | Complete | Five native actions/held states, unique body/wing charts, three PBR colours, synchronized portable death effect, verified exports and review page. |

The repaired face, jaw, fingers and body bind were retained. The Flying Demon uses six wing joints per side, attached behind the shoulders independently of the arms. There are 89 joints and at most six vertex influences. The living assembly has **20,820 triangles**, death effect 3,480 and ash 624. The inherited repaired body plus new wings was measured rather than forced to a 15k ceiling. Blender uses metres, Z up and -Y front; GLB uses Y up and +Z front.

| Delivered clip | Duration | Native aliases / endpoint |
| --- | --- | --- |
| Flight | 0.750 s | Standing, Walk and Fidget; seamless loop. No grounded walking/running cycle exists for this creature. |
| Attack | 0.750 s | Attack2 and Cast use this sequence; caller blends recovery back to Flight. |
| Hit | 0.750 s | Airborne recoil, asymmetric wings and feet; caller blends back to Flight. |
| Death | 0.875 s | Body/wings disappear at native E, 0.500 s; plume contracts to empty at 0.875 s. |
| Ash_Remains | 0.125 s held sample | One fixed ground-level pile; select after Death and hold frame zero indefinitely. |

The source bitmaps hold each phase for 0.125 seconds. Continuous limb motion, palms and depth between those observations are extrapolated; bone length and scale remain fixed. The source casting groups reuse attack rather than supplying another gesture. The spell identities are preserved in the manifest without adding spell-projectile behavior to the art package.

Materials use 4K colour/normal maps and 2K roughness sources. Skin, bone and dark leather have zero metallic response. The Blender master packs all three palettes. The first body retextures painted pink wings; a separate wing pass corrected this. A later chest topology/UV repair required the three body textures to be refreshed. **Seven successful Meshy jobs consumed 70/100 credits; no jobs are pending.** Original returns and receipts are retained under `meshy/` and the canonical progress record.

Meshy welded near-coincident Boolean seam vertices in the refreshed static upload: 20,820 triangles became 20,773. Measured deviations were under 0.1 mm and 0.5 texture pixels at 4K. Only verified maps were transferred; the delivered rigged geometry, UVs and animation remain the retained master. See [texture correspondence](work/texture_correspondence.json).

[Technical checks](review/technical_checks.json) pass: isolated GLB reimport and 317 half-frame samples; all three palettes have identical geometry/weights/animation; zero unintended positive-area UV overlaps; zero principal torso skin crossings; and 951 actual OpenYAMM loader/pose samples with zero warnings. The chest test excludes independent jaw/eyes/teeth and does not claim an exhaustive whole-body animated collision proof.

[Agent visual review](review/agent_visual_review.json) covers 775 dense poses in five views, source-anchor comparisons, hand/wrist/shoulder/foot/wing details, 15 palette/material views and five posed closeups. Live browser playback was reviewed at 1x and 0.25x, separately from the contact sheets. Loop, one-shot endpoints, ash/Flight resets, frame seeking and mobile layout pass. [Playback evidence](review/live_playback/browser_validation.json) and actual displayed-canvas captures are retained. The final Death repair was rerendered in all five views; [preservation evidence](work/death_change_preservation.json) proves the other four clips and living/ash surfaces are unchanged.

There are **14 resolved finding groups** in the correction ledger; this is a count of issues, not individual Blender executions or paid submissions. Fixes include chest folds/weights, IK reach, export filtering, attack wrist continuity, wing/Boolean UV charts, wing pigmentation, foot clearance, flame geometry/opacity, bounded texture transfer, supported material factors, native hit banking/soles and death occlusion/lowered hands. Before images remain in `review/correction_before/`; unmarked current poses and native comparisons remain in `review/`.

The original sprites clearly show three dominant long fingers. This derivative retains four long fingers plus a thumb from the source rig as an **obscured-depth inference**, not recovered anatomy or an accepted deviation. Attack/Hit/Death supply only a front bitmap per phase, so alternate-view poses and wing/flame depth are also inferred. The death plume uses portable soft-alpha crossed ribbons and morphs, not a recovered fluid simulation. These choices are visible for artistic review; there are no recorded user approvals for this derivative.

Authoring scripts record revision-specific operations; do not blindly rerun them over the delivered checkpoint. Current checks are `check_geometry.py`, `check_chest.py`, `validate_export.py`, `check_assets.py`, `check_death_change.py`, `check_consumer.cpp` and `check_viewer.mjs`. Blender operations use `tools/run_creature_blender.sh`; project writes use `tools/creature_workspace.py run` with a newly claimed lease. `render_review.py` and `make_render_contacts.py` rebuild the existing review package. Historical probes and abandoned repair attempts are retained under `work/diagnostics/` and `work/superseded_attempts/`.

No engine/runtime assets were installed by this derivative production. The loader and pose checks establish consumer compatibility; in-game GPU appearance and caller-controlled transitions are separate installation work.
