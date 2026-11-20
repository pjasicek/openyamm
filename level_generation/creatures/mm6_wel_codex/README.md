# MM6 Water Elemental (`wel`)

Revision **water_v6**, accepted by the user on **2026-10-13**, installed and verified.

[Interactive review](http://192.168.1.130:8912/level_generation/creatures/mm6_wel_codex/review/viewer/?v=water_v6)
includes all three tiers, nine clips, slow playback and frame controls. The canonical record is
[creature_3d_progress.json](creature_3d_progress.json). Previous deliveries, including v5, remain under
[revisions](review/revisions/).

## Accepted attack timing

The wind-up now continues to **frame 32** with no chamber hold. The point-first thrust takes **12 frames / 0.20 s**
and impacts at **frame 44 / 0.733333 s**, about 44% less release time than v5. Recovery finishes at
**frame 79 / 1.316667 s**. The tail, hips, torso and head drive together; the left hand counterbalances.
The deeper draw-back, forward/inward aim and low grip from v5 are retained.

The three tiers' Attack impact markers match the new visible strike. The engine still fits the lead-in to the
native **1.125 s** action, preserving gameplay timing; Cast retains its **1.02 s** marker. Other eight clips,
geometry, textures, skinning and props are byte-for-byte preserved in all seven animated GLB exports.

[Attack sequence](review/attack_timing_v6/attack_contact.jpg),
[actual normal/quarter-speed playback](review/attack_timing_v6/playback/check.json),
[close views](review/attack_timing_v6/details/), and
[mechanics](review/attack_timing_v6/mechanics.json) document the result. Every frame from 32–40 advances the tip.
Maximum wrist change from ready is **17.61°**, forearm axial change **30.33°**, and half-frame bone rotation
**6.87°**. Dense checks find no shaft/body intersections; the arm lengths and grip remain fixed.
[Preservation checks](review/attack_timing_v6/preservation.json) cover all seven animated GLB exports.

All 27 tier/clip viewer combinations, export parity, installed-asset validation and the focused actor regression
pass. [Indoor/outdoor native combat](review/attack_timing_v6/game/) was inspected with the normal shared assets
on NVIDIA/OpenGL. No new Meshy or texture generation jobs were needed.

## Accepted v2 appearance corrections

- **Submerged tail:** checked the restored `mm6_wel/trimmed_2x/welwka2.png`, `welwkd2.png` and `welsta2.png`.
  Their flat bubbly waterline hides the lower tail; the crest and fluke can emerge. The new geometry removes the
  submerged underside, lowers the body 0.255 m and anchors the cut edge under three foam collars. The tail still
  glides. This works in the transparent-grid reviewer without relying on a ground plane to conceal the underside.
- **Head:** one surface and one head material were present. The generated texture and normal map placed facial
  features below the sculpted nose/mouth. A geometry-guided face projection now registers a single nose and mouth
  to the sculpt. The separate 1K head atlas remains; the misleading normal detail is removed in the corrected area.
- **Attack/Cast:** the right elbow follows an authored anatomical path, upper-arm roll is bounded, and forearm roll
  changes gradually through release. The gripping wrist bends at most about 35 degrees. Frames 33–61 were inspected,
  including 60→61. Dense sampling found no shaft/body intersections or abrupt rotation changes.
- **Poseidon trident:** replaced the wire fork with a **972-triangle** beveled steel head, purple shaft and gold/silver
  fittings, using MM6 item 2037 (`6trident5`) as the design reference. It has a dedicated 1K colour/material atlas
  and proper UVs. Its colours remain the same across creature tiers. The hand grip and projectile socket are retained.

[Feedback screenshots and diagnostic evidence](review/feedback_v2/),
[attack sequence](review/feedback_v2/attack_contact.jpg), and
[generated references, prompts and receipts](references_feedback_v2/) document the correction.
The reference images used built-in imagegen. No additional Meshy jobs were needed; spending remains **25/100 credits**.

## Selected assets

- [Packed editable Blender master](export/mm6_wel.blend): 80-bone rig and nine 60 Hz actions.
- [Portable GLB](export/mm6_wel_portable.glb): body, trident and foam together with all three palette-ramp variants.
  Generic glTF software shows the base appearance unless it supports the OpenYAMM ramp extras; the browser review
  bakes each tier's appearance into its preview GLB.
- [Runtime body](export/mm6_wel.glb) and [rigid attachment](export/mm6_wel_trident.glb), installed through
  `tools/install_model.py` into `assets_source/worlds/mm6/models/` and the processed `assets_dev` copies.
- Separate 1024-square body/head colour, normal, material and mask maps in [textures](textures/).
  Runtime merging produces four 2080×1024 atlases with a 32-pixel gutter. Foam has its own RGBA map.

| Source geometry | LOD0 | LOD1 | LOD2 | LOD3 |
| --- | ---: | ---: | ---: | ---: |
| Body/head | 13,128 | 6,564 | 2,361 | 784 |
| Poseidon trident | 972 | 972 | 972 | 972 |
| Foam | 480 | 480 | 480 | 480 |

The source close-up total is **14,580 triangles**. The installed total is **15,393**, including back-face copies
added by the shared installer. The small attachment retains all three points and collars at every distance.
The main mesh has at most four influences; reduced LODs have at most eight. Shadow LODs are included.

## Animation and runtime

Standing and Fidget are 3 s; Walking/Hit/Death 1.116667 s; Running 0.85 s; Attack 1.316667 s; Cast 1.4 s; Dead 1 s.
The native gait, Cast, recoil and sinking death remain; Attack uses the requested point-first thrust. Foam closes during death and no corpse
remains visible. Native gameplay tables and timing remain authoritative.

Descriptors 532/533/534 (`ElemWater A/B/C`) select `wel_a/b/c`, based on palettes 730/731/732.
Visible standing height is 1.979880 m; scale **98.1871159** preserves 216 native pixels × 0.899994 = 194.398704 units.
Stride **2.72914563** preserves the previous world-space gait distance. Attack impact markers are 0.7333333333 s; Cast remains 1.02 s.
Cast is distinct from both attack slots. Eye/palm/gaze sockets, restrained head look and `Socket_Trident_Head`
remain present. The trident uses the `Trident` rigid attachment. Materials use ordinary PBR lighting.

The foam represents a local flat waterline, including on land as in the native sprite; sloping terrain can occlude
parts of it. The animation and hidden anatomy are authored reconstruction choices.

## Current export checks and retained appearance evidence

- [Dense animation check](review/reduced_dense_audit.json): all nine clips at half frames, no sampled shaft/body
  intersections. Attack/Cast maximum half-frame rotation is about 6.87/7.26 degrees, with continuous release interpolation.
  Living-pose minimum height is about 8 mm; loop endpoints match.
- [Export/reimport parity](review/export_parity.json): every clip and eye/palm/gaze sockets retained;
  maximum surface difference 1.77 mm during sinking death and maximum socket difference 0.019 mm.
- [Delivery validation](review/checks/delivery.json): source/installed hashes, LODs, variants, material maps,
  80 bones, nine actions and the rigid attachment. Animation samples survive runtime processing unchanged.
- [Browser checks](review/attack_timing_v6/viewer.json): all 27 tier/clip combinations, no console errors.
  [Normal/quarter-speed playback](review/attack_timing_v6/playback/check.json), [loop checks](review/checks/loops.json),
  [close views](review/attack_timing_v6/details/check.json) and [exact feedback frames](review/attack_timing_v6/poses/check.json).
- [Focused actor regression](review/attack_timing_v6/regression.log) passes tier scale, animations, sockets and attachments.
- [Retained v2 appearance GPU captures](review/game_v2/) cover all tiers, walking, hit, death, combat and LOD0–3,
  indoors (`6d19.blv`) and outdoors (`oute3.odm`), with OpenGL 3.3 on NVIDIA. The original same-camera sprite
  captures in [the initial comparison](review/game/comparison.jpg) remain valid references.

No renderer/gameplay feature or native sprite was changed. This revision needed no engine rebuild.
Android, Vulkan and the broader regression suite were not checked. No commit was made.

## Reproduce v6

With a fresh project lease, run `attack_timing_v6.py` in Blender using the archived v5 master, then
`verify_timing_v6.py`, `verify_reduced.py` and `export_water.py`. Run `export_timing_v6.py` in regular Python:
it transplants only Attack into the archived v5 exports and regenerates the tier previews/manifest.
Install `export/mm6_wel.glb` with `tools/install_model.py --world mm6`; retain the rigid trident. Set only
`animation.events.attack_melee.impact` and `attack_ranged.impact` to `0.7333333333` for `ElemWater A/B/C`;
leave Cast at `1.02`. Re-run parity, delivery, browser and scoped runtime checks. Do not rerun an older generator
over the accepted v6 delivery.

## Reproduce the preserved v2 base

Acquire a fresh `mm6:wel` lease before project writes; use the creature workspace wrappers. Preserve the archived
v1 master, paid returns, UVs and all selected references. Do not restart the paid jobs.

1. `animate_water.py` builds the corrected actions from `work/rig_prop.blend`.
2. `feedback_textures.py` bakes the selected generated projections into the existing UV atlas and Poseidon layout.
   It reads the archived v1 head maps, so repeated execution does not accumulate colour edits.
3. In Blender, `rebuild_feedback.py` runs `add_foam.py`, `water_surface_v2.py`, `poseidon_v2.py`,
   `export_water.py` and the dense final-mesh check. It retains the selected v1 reduced mesh and UVs.
4. Run `prepare_runtime.py` and `update_viewer_manifest.py` with regular Python; `build_lods.py` in Blender;
   then `finish_runtime.py` with regular Python.
5. Install both exports with `tools/install_model.py`, retain the binding scale/stride above, and run affected
   parity, delivery, browser and game checks. `install_water.py` is a one-time append and must not be rerun.

The original reduction/UV/Meshy scripts remain as provenance. Running `compose_water.py` restores the v1 texture
composition; follow it with `feedback_textures.py` to reapply the selected head and weapon correction.
