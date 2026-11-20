# MM8 Dragon Turtle — m580

Completed desktop production, 2026-10-18. User approved revision `m580_v1` on 2026-10-18 ("good").

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m580_claude/review/viewer/)
· [portable GLB](export/mm8_m580_portable.glb) · [editable Blender master](export/mm8_m580.blend)
· [runtime source](export/mm8_m580.glb)

Dedicated aquatic rig: rigid shell, three neck joints, head and jaw, two large front paddles,
two smaller rear paddles, and a three-joint tail. There is no held equipment or humanoid animation source.
All three native tiers are installed through `tools/install_model.py` and bound in
`assets_dev/worlds/mm8/models/actors.yml`.

## Appearance and motion

Original indexed BMPs, SFT timings and palettes establish the identity. See [motion study](MOTION_STUDY.md),
[native anatomy](references/native_anatomy.png) and [reference inventory](references/native_inventory.json).
Five generated HD views are retained with their prompts and input hashes under `references/`.
The first front reference was rejected for extra appendages; its corrected version is selected.

The first Meshy mesh was rejected for duplicate appendages. The second mesh has four flippers and one tail.
Local work lengthened the neck and tail, swept the front paddles outward, reduced the rear pair, closed unintended
root holes and kept the shell rigid. The model is a reconstruction: the more rounded paddle outlines and finer
head differ from the tiny original sprites; hidden anatomy is inferred from the five-view study.

Swimming uses a downward/backward power stroke, a feathered return, delayed rear steering and tail motion.
The head compensates for the small shell pitch. The bite lifts the neck and opens the jaw during anticipation,
then drives the entire body forward/downward as the jaw closes. Death recoils, rolls 28 degrees and settles low
on its side. The rejected 112-degree roll perched the body on a flipper.

| Clip | Seconds | Runtime use |
| --- | ---: | --- |
| SwimIdle | 1.0 | Standing |
| Swim | 1.0 | Walking/running; distance driven |
| Bite | 1.10 | Melee; contact at 0.75 s, then 0.35 s follow-through |
| Hit | 0.75 | Native recoil timing |
| Fidget | 0.50 | Native timing; head turn |
| Death | 0.875 | Full settle through the existing death completion path |
| Dead | 1.0 | Constant exact terminal Death pose |

Native attack damage still occurs at 0.75 s. Native gameplay timers, collision dimensions, HP, speed,
nonflying movement and physical melee remain unchanged. The ranged role maps to Bite for a complete binding;
these descriptors have no native spell/projectile. `upper_body_root: Root` lets the whole aquatic body follow
through under the existing runtime blend path. No renderer or gameplay feature was added.

## Geometry, materials and scale

18 bones, at most four normalized influences per vertex. The shell has one rigid owner.

| LOD | Triangles |
| --- | ---: |
| 0 | 12,971 |
| 1 | 6,485 |
| 2 | 2,334 |
| 3 | 777 |

The shared actor profile uses 50%, 18%, 6% of LOD0 rather than successive exact halves. This is the documented
engine-driven budget choice; native forced-LOD captures retain the shell, horns and paddle silhouette.
Shadow meshes have separate positions; thin paddles, jaw and tail are excluded from the inward shadow adjustment.
The intentional internal tongue sheet is open; all closed components pass the winding check.

One shared 2K base-colour map, 1K tangent normal, 1K packed AO/roughness/nonmetal map and 1K region mask serve
all three tiers. Skin specular is disabled (`openyamm_specular: 0`, metallic factor 0); the red channel retains baked
AO under this selected skin contract. The class map is retained for future material work. The head has 2.06×
body texel density. Meshy's returned model matched all 12,971 triangles and every UV; its normalization did not
replace the rig. The normal map was converted to glTF +Y-up by `prepare_actor_glb.py`.

The green shell alone receives native ACT-derived teal/ochre ramps. Head, flippers, ivory and the golden shell rim
remain shared. Tier A bypasses colour ramps exactly; its unused empty-ramp extras are removed before installation.
The weighted native palette fit has linear-RGB RMSE 0.0058/0.0051.

All tiers use scale 650 and yaw offset -π/2. Eight native front walk frames at SFT scale 4 give an equal-area
model scale of 662.31. Scale 650 is 3.68% smaller in mean silhouette area and keeps approximately the native
940-unit side length. See [scale calibration](review/scale_calibration.json).

## Verification

- Development `openyamm` build passed; no Vulkan build.
- Focused Dragon Turtle runtime regression passed: three variants, seven clips/eight roles, four colour LODs,
  required rig nodes, valid bounds and unchanged gameplay state.
- All 50 MM8 actor regressions passed against the [stable installed asset snapshot](review/regression_fixture.json).
  Two earlier production-root attempts encountered texture files being replaced by concurrent creature jobs;
  their logs are retained separately. The stable snapshot uses original production maps and tables.
- [Export parity](review/export_parity.json): all seven clips, nine sampled poses per clip, surface deviation below
  0.000001 units. Dense 192 Hz samples show positive floor clearance; both swim loops and Dead close exactly.
  Dead equals the final Death pose, and shell rigidity error is below 0.000001 units.
- [UV audit](review/uv_audit.json): no meaningful overlap (three shared-edge rounding pixels at 1K), padded islands.
- [Delivery validation](review/delivery_validation.json): all LOD/shadow indices, finite normalized normals,
  normalized weights, tier contracts and installed source hashes. Winding: zero inverted closed parts.
- [Browser check](review/viewer_check.json): all 21 tier/clip combinations load without console errors.
  [Actual playback recordings](review/playback/) cover all seven clips at normal and half speed;
  [motion review](review/motion_review.json) records agent findings.
- Native desktop GPU captures use NVIDIA OpenGL 3.3: [three tiers outdoors](review/ingame/coast_models/01-tiers.png),
  [same-camera native sprites](review/ingame/coast_sprites/01-tiers.png),
  [indoor model](review/ingame/indoor_models/02-lod0.png), [indoor sprite](review/ingame/indoor_sprites/01-tiers.png),
  forced LOD0–3 in both scenes, live movement/bite, and death/settle/loot transition.
  [Outdoor settled pose](review/ingame/outdoor_death/death_01.png) ·
  [indoor settling pose](review/ingame/indoor_death/death_01.png).
  The shared game now sinks corpses and replaces them with loot satchels; this asset preserves that behavior.
  [Run records](review/ingame/runs.json) retain binary and screenshot hashes. These are visual checks, not performance benchmarks.

The indoor town-hall fixture has a low ceiling: the native sprite's upper extent clips there, and a giant creature
fills the view at melee distance. The larger outdoor view and browser turntable are the clean anatomy references.
Private hard-link fixtures preload the native family for comparisons; production maps are unchanged.
Android device rendering and Vulkan were not tested.

## Rebuild and provenance

Meshy spending: **20/100 credits** (two 5-credit geometry jobs, one 10-credit PBR job); task IDs and source hashes
are in `creature_3d_progress.json`. There was no paid rigging or animation job.

Use the project lease and standard creature wrappers. `build_rig.py`, `animate.py`, `prepare_uv.py` create the
weighted, animated UV master. `refresh_actions.py` updates only actions after motion revisions, preserving UVs.
`compose_textures.py` builds the shared maps/ramps from the retained Meshy maps, native palettes and AO.
`export_turtle.py` packs the editable master and LOD0; run `tools/prepare_actor_glb.py`, `build_lods.py` and
`finish_runtime.py` for runtime normal convention, colour/shadow LODs and palette variants. `viewer_tiers.py`
bakes preview-only tier maps for Three.js. `export_parity.py`, `delivery_check.py`, `measure_scale.py` and
`scale_area.py` verify the selected outputs. Reinstall with `tools/install_model.py`, never by copying runtime files
back over the source. The final runtime source hash is recorded in `review/delivery_validation.json`.
