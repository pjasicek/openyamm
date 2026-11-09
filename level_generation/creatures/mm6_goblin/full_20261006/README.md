# MM6 Goblin — staged FULL delivery, 2026-10-06

The rigged, textured assets and seven native actions are built. Export, UV, skinning and native-consumer checks pass. Agent review covers sequential rendered/decoded poses, native comparisons and material details. **Real-time temporal viewing at normal/slow speed remains unverified**; the session exposes still-image inspection, not video inspection. This package is ready for that review, and does not claim the FULL motion-review gate or user artistic acceptance is complete.

Start with `review/review_reel.mp4` for the normal/quarter-speed front/profile reel. Open `delivery/mm6_goblin.blend` for the editable, packed-texture master. `delivery/mm6_goblin_745.glb` is the primary olive/brown version. `746` and `747` are blue/teal and red/brown pigment variants. All three contain the body, curved sword and the same seven actions. The triangle count is **13,773 body + 540 sword = 14,313**, with 64 joints and at most four normalized influences per vertex.

`mm6_goblin_full_review.zip` contains the master, portable files, manifests, selected submission views, anatomy/motion studies, correction evidence and normal/quarter-speed previews. Working checkpoints, `.blend1` backups, raw render frames and transient network URLs are excluded.

## Timing and use

| Clip | Duration | Endpoint / use |
| --- | --- | --- |
| Standing | 0.125 s | Truly held ready pose; caller may hold indefinitely |
| Walk | 0.750 s | Closed native cycle; in-place gait |
| Attack | 0.750 s | Native coil, slash and recovery; returns to Standing |
| Hit | 0.750 s | Free-hand guard and release; returns to Standing |
| Death | 0.625 s | Forward collapse; ends at Corpse |
| Corpse | 0.125 s | Truly held prone pose; caller may hold indefinitely |
| Fidget | 0.750 s | Small native free-hand/shoulder movement; returns to Standing |

The six observed locomotion/action frames hold 125 ms each; Death has five. Smooth authoring passes through the observed anchors. The final master/export use 192 Hz sampling to retain fast collapse/contact keys; visual previews use 48 fps, with normal and quarter-speed versions. No native Running clip exists. Meshy's stock walk/run were deformation probes and are excluded from delivery. AttackMelee/AttackRanged share Attack; native GotHit/Dying/Dead/Bored alias Hit/Death/Corpse/Fidget.

Blender is metres, Z up, +X anatomical left, forward −Y. glTF is Y up, forward +Z. Rest body height is 1.65 m; ground is Z=0 in Blender. The native front fitting offset is retained. The in-place gait was authored for approximately 1.6 m/s; runtime movement/blending must be configured by the caller. Variant files have equal geometry scale: apply the native A/B/C size ratio once using `clip_manifest.json`, without also baking the same ratio into the imported model.

The separate sword is rigid on `Weapon.R`, a child of `RightHand`. Fingers, thumb, forearm twist, jaw, shoulder caps and twelve leather-strip hinges remain editable bones. Switch actions on `Goblin_Rig`; there are no stock-action/NLA tracks in the delivery. In Blender the B/C maps are packed as `Goblin palette 746 4K` / `747`; the corresponding GLBs are ready to load.

## Evidence and production record

- `review/source_comparisons/`: every native anchor, including all five genuine stored Standing/Walk views at 0/45/90/135/180 degrees, with one fixed native canvas/scale.
- `review/final_playback/`: all seven clips from front/profile, normal and quarter speed. Sequential decoded-frame inspection is recorded separately from unverified real-time temporal viewing. `review/attack_wide/` exposes the entire blade arc beyond the narrow native camera.
- `review/final_materials_v2/` and `review/export_materials/`: neutral body/detail/variant views and actual reimported GLB in demanding attack, hit and death poses.
- `review/full_dense_checks.json`: quarter-frame (192 Hz) numerical surface/rotation checks, bone scales, floor screens and endpoint parity. Some locally compressed faces occur beneath armor or inside folded joints; these checks are screens, not a claim of zero self-intersections everywhere.
- `review/export_reimport_checks.json`: actual reimported skin/sword motion against the master, 121 samples per clip, with ≤1 mm tolerance. Measured errors are recorded, not replaced by an art pass.
- `delivery/asset_validation.json`: actual PNG decoding, tangent/UV/normal/weight checks, exact clip times and OpenYAMM's existing native loader/evaluator across all three GLBs. This is an asset-consumer check, not GPU/in-game visual acceptance.
- `delivery/uv_validation.json`, `review/texture_transfer.json`: no unintended UV overlap/degenerate triangles, unique asymmetric charts, 16-pixel packing margin at 4K. Meshy's static texture return uniformly resized/recentred the model; per-corner UV triangle identity was verified and only the downloaded maps were transferred to the retained master.
- `review/fixup_comparisons/` and `delivery/correction_ledger.json`: highlighted native/before/after evidence and repair causes. The ledger contains 20 recorded repair/review entries, covering anatomy, skinning, curve interpolation, UVs, materials and export timing. Counts are not quality guarantees.

Meshy spending for this FULL run is **20 / 100 credits**: smart-topology body 5, auto-rig 5, 4K PBR texture 10. There are no pending paid jobs. One sandbox DNS rejection created no task and cost zero; its reconciliation is retained in the canonical progress record. The selected five imagegen references and their two historical correction stages were reused. Body, rig and texture originals and immutable upload hashes remain under the creature project.

## Provenance and limits

The studies are `../stage1_20261006/ANATOMY_GUIDE.md`, `ANIMATION_STUDY.md`, `anatomy_targets.json` and `motion_spec.json`; native sources include 59 original frame decodes. `motion_fit_revision.json` records corrections to early depth/blade fitting seeds. The study's preparation-only status describes its creation checkpoint; the canonical record now tracks FULL. The original study's +X anatomical right/+Y forward convention was explicitly converted to the authoring basis above. Those manual landmarks are fitting seeds, not tracked ground truth. Fixed limb/prop lengths take precedence where an inferred wrist cannot be reached: some Attack/Hit tips or wrists differ by about 9–16 native pixels, and the prone wrist differs by about 16 pixels. Current measurements are in `review/native_tip_fit_after.json`; exact fit is not claimed for every seed.

Standing/Walk have five genuine views and three mirrors. Attack, Hit, Death, Corpse and Fidget have one stored front view reused in every direction; their depth, hidden elbows/knees and secondary motion are careful inferences. The sword reuses the earlier `corsair_goblin_sword.glb` prop, with native-compatible length/grip/tip fitting and gold pommel. Its historical MM7 Corsair provenance is retained; it is not a recovered MM6 weapon mesh.

B/C are derived HD **pigment variants**, not literal per-index recreations of every native palette colour: skin/leather hue and saturation come from real ACT745/746/747 pigments, while HD shading, natural ear/nose colour variation, shared yellow eyes/golden details and iron hardware are retained. The 15k-triangle target limits small curved details. No death particles/effects are required by these source frames.

The next step is actual-speed and slow-speed temporal/art review of the provided previews. The skill requires “Review actual playback at normal and slower speeds”; sequential image inspection does not establish that gate. User artistic acceptance is unrecorded. No engine installation, runtime asset replacement or directional sprite export was performed.

Canonical progress: `../stage1_20261006/creature_3d_progress.json`. The selected deliverables and their final hashes are in `delivery/delivery_manifest.json`.
