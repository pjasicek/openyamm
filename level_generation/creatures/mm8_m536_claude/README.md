# MM8 Efreeti · m536

Complete desktop production, 2026-10-18. Agent visual review passed; user artistic acceptance is pending.
Native descriptors **Efreeti A/B/C**, IDs **103–105**, sprite aliases **m537/m538/m539**.

[Interactive motion/tier viewer](http://127.0.0.1:8765/level_generation/creatures/mm8_m536_claude/review/viewer/)
· [Portable runtime GLB](export/mm8_m536.glb) · [Packed editable Blender master](export/mm8_m536.blend)

![Efreeti](review/assembled_Standing_front.png)

## Delivered

- Gold horned floating torso, curled cheek horns, five-digit hands and silver jeweled cuffs.
- Separate skinned fire shell/fringes: eight tail bones, transparent unlit materials, upward UV scroll,
  authored inside/outside draw order, vertex-alpha end fades, no specular or creature edge darkening.
- Native flask remains: the body/fire contract over the 0.75-second Death clip. The Dead clip holds the flask.
  Ordinary gameplay subsequently dissolves those remains into the shared loot satchel, as required by the
  current [runtime contract](../../../engine/render/MODEL_RENDERING.md).
- Nine clips: Standing, Walking, Running, Attack, Cast, Hit, Fidget, Death and Dead. Two-hand casting uses the
  local Unarmed library; crossed-arm hover and legless movement are authored. Attack/cast impact is 1.25 seconds,
  with a 1.5-second visual clip. Hit is 0.625 seconds. This is an adapted 3D performance, not frame reconstruction.
- Three shared-texture palette variants change cuff gems green/violet/red. Golden skin, eyes and fire stay fixed.
- 55 bones, at most four influences; measured eyes/gaze/palm sockets and neck/head look bindings.
- Body LOD triangles: **12,310 / 6,152 / 3,073 / 1,529**. Fire: **2,584 / 1,196 / 480**.
  Living LOD0 total: **14,894**; flask: **1,120**, hidden while alive. Reduced shadow meshes are separate.
- Body/head each use a 1K painted set, merged with a padded gutter for runtime. Skin, cuff metal and gem
  roughness/specular are separated by texture masks. Flame atlases are 1024×512; flask is 512×512.

The authoritative installed source is `assets_source/worlds/mm8/models/mm8_m536.glb`; its desktop cooked copy
and external textures are under `assets_dev/worlds/mm8/models/`. `actors.yml` binds all three equal-sized tiers.
No rendering feature or gameplay behavior was changed. The only C++ addition is the focused actor regression.

## Evidence

- [Native identity](native/native_identity.png), [selected HD views](references_hd/selected_views_review.png),
  selected body/head image hashes and Meshy receipts in [canonical progress](creature_3d_progress.json).
- [Fitted joint X-ray](review/joint_xray.png), [proportions](review/proportions.json),
  [source-frame check](review/rest_frame_gate.json).
- [Final per-clip gates](review/final_gates.json): 60 Hz posed closed-shell hand/digit probes, no penetrations
  beyond the stated 12 mm tolerance; geometry stays above the floor. Worst edge ratio 3.633, worst p99 1.980.
  [Motion steps](review/source_motion_comparison.json) stay below the source clips' own maxima.
- [Reduction selection](review/reduction/selection.json): step 2 retains face/fingers/UV seams exactly;
  maximum sampled surface difference 10.5 mm. Step 3 was rejected for torso distortion.
- [Export parity](review/export_parity.json): all nine body clips, maximum surface difference 0.137 mm,
  maximum socket difference 0.0094 mm. Runtime exports sample at 120 Hz to retain the 30 Hz source knots
  and exact fractional native endpoints. [Delivery validation](review/delivery_validation.json).
- [Viewer check](review/viewer_check.json): all 27 tier/clip combinations, no browser errors.
  [Actual browser playback recordings](review/playback/) contain every clip at normal and half speed.
  Camera framing was subsequently widened to include the highest casting fingertips.
- [Outdoor comparison](review/ingame/outdoor_comparison.jpg), [indoor comparison](review/ingame/indoor_comparison.jpg),
  [indoor actions](review/ingame/in_actions/), [outdoor actions](review/ingame/out_actions/).
  The same-camera tier comparisons use live AI, so exact facing and position can differ.
- [Live damage/death check](review/ingame/live_validation/): visible living tier C, hit, contraction with flask,
  then the ordinary loot satchel. [Desktop run records](review/ingame/runs.json): OpenGL 3.3, NVIDIA, Wayland.
  Isolated scene copies preload the foreign MM8 sprite family; production maps were not edited.
- Ordinary `openyamm` build passed. [MM8 Efreeti regression](review/regression_mm8.log) verifies shared assets,
  palette tiers, native height, unchanged actor simulation, clips/sockets and flame material semantics.
  [Existing MM6 Genie regression](review/regression_mm6.log) also passed.

## Production notes

Shared Claude HD-master, humanoid and creature-texture playbooks were used with the legless hybrid route.
The measured torso/arms, cloned source frames and connectivity-fitted digits replace a biped auto-rig; there
are no leg/sole constraints. Meshy's extra sixth digit on each hand was removed before texturing. The native
attack starts open-armed, so the runtime owns the transition from crossed-arm idle; no extra folding transition
is embedded in the action. Contact gates cover individual clips, not every possible runtime crossfade.

Meshy spending: **25 / 100 credits**: Smart Topology 5, body retexture 10, head retexture 10. No paid animation.
Selected generated references clarify hidden detail; they are an artistic reconstruction. Raw returns and hashes
are retained. The primary v2 image's exact original prompt was not retained; its selected file/hash is recorded.

For local rebuilds, use the project lease and the guarded Blender/Meshy wrappers. The retained selected assembly
is `work/assembled.blend`; `select_reduction.py` produces `work/final_master.blend`. Run `export_efreeti.py`
(Blender), `prepare_runtime.py` (Python), `build_lods.py` (Blender), `finish_runtime.py` (Python), then the existing
`tools/install_model.py ... --world mm8`. `pack_editable.py` restores a clean opening view with lower flame LODs
hidden. Texture scripts retain verified UV correspondence and the dedicated head UV domain.

Android and Vulkan were not run. The native fire is intentionally rendered more brightly than the original
lit sprite. No user artistic approval has been inferred from the technical checks.
