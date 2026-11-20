# MM8 Lizardman Warrior — finished production

Completed 2026-10-18 for Lizardmen Warrior A/B/C (Soldier, Sergeant, Captain), descriptors 4/5/6.
All three native colour tiers are installed. Original sprites and gameplay tables are preserved.
The user approved the full-body Mixamo attack; the final textured appearance has been reviewed by the agent,
with separate user acceptance not yet recorded. The October 15 handoff and earlier pilots are historical.

## Selected delivery

- Editable, packed textured master: `work/warrior_finished.blend`.
- Rebuild input: `work/rig_textured.blend`; corrected delivery animation: `work/rig_delivery_animation.blend`.
- Runtime exports: `export/mm8_m404.glb` and rigid `export/mm8_m404_sword.glb` on `Socket_Sword`.
- Installed authoritative sources: `assets_source/worlds/mm8/models/`; desktop runtime copies:
  `assets_dev/worlds/mm8/models/`; bindings: that directory's `actors.yml`.
- Viewer: `../review/viewer/`, green Soldier, blue Sergeant and red Captain.
- Exact selected and installed hashes: `creature_3d_progress.json`.

Body LOD triangle counts are 11,229 / 5,613 / 2,019 / 670; sword counts are 932 / 466 / 166 / 54.
The protected head, hands and feet retain their silhouette; the remaining body was reduced before texturing.
Four colour LODs and three inward-corrected shadow LODs use four influences and one merged body material per tier.
The 3,182-triangle detailed head is retained at LOD0; 18 microscopic hidden neck-cut triangles were removed by
the returned head texture mesh. Retained head positions match within 0.00003 mm.

Body and head use separate 1K source maps merged into padded 2080×1024 runtime atlases. The mantle mask uses
native palettes 405/406/407; grey skin, leather, brass and blade remain shared. ORM red is the material specular
mask, green roughness and blue metallic; AO is composed into base colour. Native ramp samples exclude neutral
metal entries to prevent bright speckles on the mantle. Raw Meshy returns remain in the parent `meshy/` folder.
Total Meshy consumption: **55 / 100 credits**, including the two 10-credit body/head texture jobs.

## Motion and game contract

Standing 2 s; Walking 0.8 s; Attack and Attack2 1.266667 s; Hit 0.5 s; Fidget 2.333333 s;
Death 1.4 s; held Dead 0.133333 s. Melee impact and native ranged release are at 0.635417 s.
Attack2 keeps the original Arrow gameplay with the native sword presentation; no bow is invented.

The approved Mixamo source legs and pelvis remain intact. Walking's source lift phase is corrected to the
measured horizontal paths, with stride 0.769552 m. Native standing scales are identical (1.299988);
all tiers use the same measured 200-unit body height, model scale 105.149139 and yaw −π/2.
Explicit equal scales keep these bindings independent of another world's sprite lookup.
`B_Spine` is the upper-body root, `B_Neck`/`B_Head` provide look motion and `B_R_Hand` is the ranged release socket.

Death opens/releases the left grip at 0.1 s and right grip at 0.35 s. The free right hand relaxes beside the body;
the wavy sword settles visibly on the floor, matching the native corpse's retained visible weapon.
This is presentation on the existing attachment, not a new dropped gameplay item. Back mantle, apron and tail
clear the falling body and floor. Export sampling is 240 Hz to retain the tail correction between source keys.

## Verification and limits

The actual source delivery has **850 PASS / 18 FAIL / 28 INFO / 4 N/A** in
`review/delivery_gates/gates.json`. The 18 raw FAIL rows are the nine disclosed joint/acceleration limits repeated
for Attack and Attack2; the user accepted that full-body motion before requesting this finish. They remain
visible as accepted deviations, not relabelled PASS. No new Death, Dead, grip, cloth or prop collision failures remain.
The approved attack's common-bone world matrices differ by less than 0.000001 at 240 Hz.
Every clip's body and sword floor clearance passes at 240 Hz; the fast tail fall was additionally checked at 480 Hz.

Ordinary OpenGL game build passed; focused warrior regression passed; all **55 MM8 actor regression cases passed**.
The viewer loaded all 24 tier/clip combinations without browser errors. All eight clips were recorded at normal
and half speed, and timed playback frames, face, hands, gait, attack, fall and corpse were visually inspected.
All three model tiers were inspected in New Sorpigal and Agar, with the native sprites compared at the same
outdoor camera. Native MM8 sprites spawned into MM6 Agar are absent from the renderer, so an in-game indoor
sprite comparison remains unavailable; preserved native references provide the indoor likeness comparison.
This existing sprite-renderer limitation does not affect the installed 3D tiers. Game LODs and combat/death were inspected on the desktop NVIDIA OpenGL renderer. Evidence is under
`review/ingame/production_20261018`, `../review/shots/`, `../review/playback/` and `review/delivery_checks.json`.
Android, Vulkan builds and release packaging were outside this check; minimized captures establish appearance,
not GPU performance. Native proportions and low-resolution palette shading remain interpretive HD reconstruction.

## Rebuild

With a project lease, run `scripts/build_runtime.py` through `tools/run_creature_blender.sh`.
It starts from the retained textured checkpoint, settles Death/Dead, measures final floor clearance, exports,
prepares material normals, builds LODs, corrects shadows, adds native palette variants, splits the sword and merges
head materials. Run `scripts/check_delivery.py` through the same wrapper; its exit reports FAIL for the retained
accepted attack deviations. `scripts/verify_delivery.py` asserts that only those 18 deviations remain, verifies
floor clearance and compares the approved attack. Install both exports through `tools/install_model.py`.
`scripts/bind_runtime.py` is the initial three-entry binding recipe and refuses to overwrite existing entries.
Historical preparation checkpoints and old gate reports do not supersede these selected delivery files.
