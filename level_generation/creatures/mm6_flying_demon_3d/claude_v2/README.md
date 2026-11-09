# MM6 flying demon — Claude rework (2026-10-07)

Replaces the Codex wings and animations (user: wings looked nothing like the original; palms bent the wrong way, limbs
barely bent, no body turning). The Codex body, horns, rig weights, finger chains and A/B/C body textures are kept.
Installed as `assets_dev/worlds/mm6/models/mm6_wdm.glb`, bound to DemonFly A/B/C (499–501) in `actors.yml`
(skins `wdm_a/b/c`, `death_effect: disintegration`, scale 100, opt-in via `debug.actor_models=true`).

| Item | Value |
|---|---|
| Triangles LOD0/1/2/3 | 17,398 / 8,695 / 3,120 / 1,663 |
| Clips | Flight 2.25 s loop (3 wingbeats), Attack, Cast, Hit 0.75 s, Death 1.0 s, Dead |
| Meshy credits | 17 (rig 5 + four library clips 12); project total 87 / 100 |

## Pipeline (`claude_v2/scripts/`)

1. `extract_wing.py` — traces the wing outline from the restored native spread frame `wdmflyd0` (2x), triangulates it
   (outline + interior grid, Delaunay clipped to the mask) and cuts the membrane texture from the sprite (spikes and
   body pixels inpainted, ×1.7 gain); B/C tints from the native palette medians.
2. `assemble.py` (on `delivery/mm6_flying_demon.blend`) — removes the Codex wings/struts/death meshes/actions, builds
   both wings in rig space (sprite px → m at s = 0.0035, eye-level reference; the root strip hugs the upper back),
   wing bones Root → Arm → Finger1–4 along the native struts, inverse-distance weights. Note the rig object sits at
   z = 0.16: convert to rig space.
3. Meshy: `export_body_for_rig.py` → rigging job `claude_rig_v1` on this body; library clips `claude_anim_v1`
   (Idle 1, Mage Spell Cast 1, Hit Reaction, Electrocution Reaction).
4. `animate.py` — delta retarget (clip bone's world rotation change from rest) onto the existing mixamorig rig, then
   hover posture, dangling legs, half wrist flex, forearm twist share, claw curl, and a procedural wing flap on the
   native 0.75 s cycle (high V → spread/drooping → rising, outer wing lagging, fingers folding on the upstroke).
   Attack/Cast/Hit time-warp segments of the clips and blend back to Flight; Death flails and shrinks away inside the
   engine's disintegration burst.
5. `build_runtime.sh --install` — tier exports (joined mesh, one UV layer, body maps 2K), `prepare_actor_glb.py`,
   LODs, `merge_variants.py` (B/C materials as KHR_materials_variants).

Pitfalls hit: unused tier materials are dropped on save (fake user); a non-unique UV layer name on join leaves the
wings on a second UV set (black in game); a wing alpha link exports BLEND, which the shadow LOD merge rejects.

## Review viewer

Interactive three.js viewer (same as the goblin's): <http://127.0.0.1:8901/level_generation/creatures/mm6_flying_demon_3d/claude_v2/review/viewer/>.
Tier GLBs come from `scripts/export_glb.py <a|b|c> viewer` (full skin and clips per tier); the manifest holds the
clips and native anchor frames. Rebuild the three GLBs and update the manifest hashes after any change.

## Results

In game, Abandoned Temple hall: [close-up 3D vs sprites](review/wdm_closeup_3d_vs_sprites.png) (top 3D).
Blender vs native frames: [Flight](review/flight_vs_native.png), [Attack](review/attack_vs_native.png),
[Hit](review/hit_vs_native.png), [Death](review/death_vs_native.png). The Codex review page (`../index.html`) still
shows the old Codex delivery.
