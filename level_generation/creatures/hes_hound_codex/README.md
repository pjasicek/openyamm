# Hesper Hellhounds — R5-1

Production request: [R5_HELLHOUNDS](../../../design/kreegan_world/WORK_PACKAGES/prompts/R5_HELLHOUNDS.md),
2026-10-26. The three tiers, rig, nine clips, shared materials, LODs, rigid equipment and map placements are built
and staged. Motion revision 2 passes focused checks; the earlier full regression passed 109 scenarios. Audio remains
blocked by ElevenLabs DNS. The user accepted colour revision 3 and the current motion on 2026-10-26.

## Resume

Read `creature_3d_progress.json` and this section first. Reuse the downloaded Meshy jobs; never resubmit them.
The project identity is `hesper:hound`, owner `codex`, budget 100. Claim a new lease only after the current lease
is released. Every mutation uses `creature_workspace.py run`; Blender operations use
`tools/run_creature_blender.sh --token TOKEN level_generation/creatures/hes_hound_codex/scripts/SCRIPT.py`.

Colour revision 3 is staged and checked; see its review links below. Remaining work is the eight queued sound jobs:
generate, process, listen, suggest picks and hook IDs 60150–60157 once `tools/run_elevenlabs.sh` can resolve its host. Do not resubmit either Meshy job or add audio hooks before processed WAVs exist. The report is in
`design/kreegan_world/WORK_PACKAGES/requests/P5.md`; colour revision 3 and motion revision 2 are accepted.

## Colour revision 3 — 2026-10-26

**User accepted:** “OK good accepted” — this is the approved appearance and motion baseline.

User accepted the revised motion and requested **A grey, B yellow, C red**. The existing hide mask now applies
an ochre-yellow ramp to B and a brick-red ramp to C. Grey A is unchanged; teeth, horns, collar/plates and the
localized mouth glow retain their materials. No new images or Meshy jobs were generated.

Only the six B/C material ramps at LOD0/1, LOD2 and LOD3 changed in the runtime GLB. A structural comparison
against `work/before_colour_v3/export/hes_hound.glb` verifies identical binary data, geometry, embedded textures,
nodes, skinning and all nine animation clips. All three tiers were inspected in the viewer (body and face),
in Blender renders and together in a minimized native D4 encounter. Browser tier/clip switching was checked.
No gameplay regression was rerun for this palette-only change.

Review: [current colours](review/colours_final.jpg), [rendered close-ups](review/colour3_closeups.jpg),
[native comparison](review/native/colour3/grey-yellow-red.png), [viewer](review/viewer/index.html).
The viewer revision is `hound_colour_3`. Earlier motion playback, clip sheets, LOD sheets and native captures
retain their original grey palettes as historical motion/geometry evidence.

## Motion revision 2 — 2026-10-26

User request: more whole-body motion in Bite/Hit, using the MM8 wolf as the reference. The native wolf attack
sheet and its accepted leaping-bite revision informed the crouch, rear-up, airborne descent and front-first landing.
Bite is now 1.05 s, with contact at .72 s; the A binding's melee/ranged event times follow it. Pounce uses the same
body mechanics compressed around its unchanged .4 s charge wind-up and .53 s contact. Hit is a .50 s backward and
sideways torso recoil followed by a left-front paw brace and recovery. The tail counterbalances the rear-up.

Every-frame checks keep all paws down during the crouch and the hind paws down until take-off. Both bites occur
with at least 8 cm clearance; peak body clearance is about 54 cm for Bite and 44 cm for Pounce, at unscaled A size.
The jaw stays within the rig's established 18-degree range to avoid stretching the mouth's small triangles.
All nine clips at all four LODs pass floor/stretch checks, and rigid attachment checks pass. Winding remains zero.
The final GLB replaces only Bite/Pounce/Hit; geometry, textures, variants, far LODs and the other six runtime clips
are preserved. The previous master, export, binding and scripts remain in `work/before_motion_v2/`.

The staged spawn/charge check passes all 28 steps. Browser checks pass all 27 tier/clip switches; all three tiers'
changed poses and normal/half-speed playback were inspected. A minimized native slow-motion encounter checks
the Pyre Hound's staged rendering. AI had already started its charge before the console command; capture names
are intended phases rather than exact clip times. The separate headless scenario verifies charge hits. This scoped
revision uses focused checks; the 109-scenario result below is the pre-revision baseline.
No new Meshy job, texture generation, engine build or map change was needed. Audio remains the existing DNS blocker.

Review: [Bite sequence](review/motion2_bite.jpg), [Pounce sequence](review/motion2_pounce.jpg),
[Hit sequence](review/motion2_hit.jpg), [Bite playback](review/playback/Bite-1.webm),
[Hit playback](review/playback/Hit-1.webm), [native encounter](review/native/motion2/).
The [viewer](review/viewer/index.html) opens on Bite; its manifest revision is `hound_motion_2`.

## Art and provenance

- Selected `design/kreegan_world/concepts/monsters/fam_hellhounds_candidate_2.png`: its deeper narrow chest,
  shorter horns and fewer broad resin plates read as a canine beside the Glassbacks and crawlers. Both original
  candidates, the canonical copy and exact prompts are retained there.
- Five true-alpha 1536×1024 masters are in `references_hd/`. Rear paws were corrected to point away from the rear
  camera. Side views retain slight obliquity and narrow complete margins; the first returns matched the primary
  better than the attempted corrections. Selection reasons and hashes are recorded. Geometry used only the
  three-quarter master; retexture used front, back, left and right.
- Meshy geometry `body_geometry_v1`, task `01a1782e-ebc8-7515-96d7-57c0d86329dd`: meshy-t2 Smart Topology,
  triangle-only 15k target, untextured; **5 credits**. Retexture `body_texture_v1`, task
  `01a17839-75aa-7072-8054-f68f105a8765`: meshy-7, original UVs, four masters, 2K PBR; **10 credits**.
  Total **15/100 credits**, backup account. No paid rig or animation job. Original downloads are unchanged.
- Official API settings were checked against [image-to-3D](https://docs.meshy.ai/en/api/image-to-3d),
  [retexture](https://docs.meshy.ai/en/api/retexture) and [pricing](https://docs.meshy.ai/en/api/pricing).
- Only our generated art and local project code are used. The rat, wolf and Glassback workflows were read or copied
  into this project without modifying them. No engine build, installed MM creature change or assets_dev install.

## Model and materials

The Meshy return had 14,963 triangles. Cleanup removes long stray bridges, two tiny jaw/paw bridges and six
duplicate/degenerate faces. The paid texture return omitted five duplicated faces; `repair_skin.py` matches the
retained geometry and UVs explicitly rather than treating different counts as interchangeable. Two disconnected
tooth shells are oriented outward in `assemble.py`, before exports and reductions.

The model is in metres, facing Blender -Y, with a 0.95 m shoulder and approximately 1.091 m maximum rest height.
Rest width is 0.824 m. Stage sizes use the rounded full height and half-width: A 110/42, B 127/49, C 143/55 game
units (height/radius), at binding scales 100/115/130. The long head and tail do not enlarge the body collision radius.

One shared 2K ash-grey base colour, 1K normal/MR/region mask and three region ramps implement grey A, yellow ochre B
and red C. Teeth, claws, horns, eyes and the mouth keep their material roles. The central mouth surface is
dark gum, not ivory. Head UV islands receive 2.5× linear density under the quadruped playbook; no redundant head
texture set. The normal green channel was measured and corrected to the engine convention. Cycles AO is baked
into the shared base colour. Runtime colour variants are `hound_a/b/c`; baked tier PNGs exist only for review.

Orange is confined to the maw and sparse lower-cheek/throat fissures. Maw emission factors are .22/.60/1.0.
Fissures are dark on A/B and emit only on C, factor .55. There is no emissive texture. A small mouth bone exposes
more glow during attacks and fades it during death. The six tapered fissures cost 36 triangles; this limited thin
geometry is an intentional exception for localized constant-factor emission without an emission texture.

Rigid attachments are transformed into their carrier joint's inverse-bind space. A has the iron/resin collar and
broken tether ring. B adds two shoulder plates and three spine plates. C replaces the collar with a heavy plated
one. The shoulder plates were narrowed after an every-frame check found them below the floor during the side roll.

| Runtime mesh | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| Body, jaw glow and fissures | 11,205 | 5,607 | 2,803 | 1,403 |
| A/B collar and ring | 312 | 156 | 78 | 38 |
| C collar and ring | 488 | 244 | 122 | 52 |
| Shoulder pair | 44 | — | — | — |
| Each of three back plates | 22 | — | — | — |

The already minimal closed plates retain their geometry at distance. The largest assembly, C, is 11,803 triangles.
Far body LODs use the established `lod_repair_claude` MeshLab/xatlas/rebake route; the first 25%/12.5% step passes.
LOD2 outline/colour errors are 1.9%/4.5; LOD3 4.5%/3.4, within the shared thresholds. LOD0/1 remain unchanged by
that repair. The existing Noble bosses' Python environment supplies MeshLab/xatlas read-only; no dependency was
installed or modified. The local audit launches `/snap/blender/current/blender` inside Blender because the nested
Snap launcher exits before running. Top-level Blender calls still use the approved creature wrapper.

## Rig, motion and gates

Local quadruped/canine animation-library searches found no matching clips. Our procedural rig uses automatic
weights, normalized to at most four influences, with jaw, articulated paws and six tail links. Disconnected parts
inherit nearby body weights. Every clip is baked at 60 fps:

| Clip | Seconds | Purpose |
|---|---:|---|
| Standing | 2.0 | breathing and tail motion |
| Walking | .7 | diagonal trot, .72 m stride |
| Running | .5 | half-bound gallop, 1.25 m stride, suspension phase |
| Bite | 1.05 | A leaping bite, impact .72 s |
| Pounce | .95 | B/C melee, .4 s crouch wind-up, impact .53 s |
| Hit | .50 | torso recoil, paw brace and recovery |
| Death | 1.15 | collapse and roll onto the side |
| Dead | 1.0 | held final corpse pose |
| Fidget | 1.6 | head shake/sniff |

The eight required role bindings are present. Ranged/cast fallback roles reuse the tier's melee clip; these are
non-casters. `Spine2` is the upper-body root, `Socket_Bite` the mouth socket; look limits are 25° yaw/15° pitch.
Walk/run stride and impact timings are explicit. Charge rules and C's Fire bite come from the design's staged rows.

`assembly_gates.py` checks every frame of all nine clips for finite geometry, floor penetration, triangle stretch
and attachment anchoring. `lod_animation_gates.py` repeats skin/floor checks on all four exported LODs. All pass:
no face exceeds the shared 20× area defect threshold; skin stays within the 15 mm floor tolerance. Dead body
contact is 3 mm above the floor, with torso within about 2 cm. The supporting shoulder plate reaches 8.6 mm below
the floor, within tolerance. The maximum nearest attachment-to-hide gap is under 1.3 cm. Walk IK error is below
0.004 mm. Running/pounce suspension is intentional. Winding checks report zero inverted closed parts for every
runtime GLB, including colour and shadow LODs.

Evidence: `review/assembly_gates.json`, `review/lod_animation_gates.json`, `work/animation_report.json`,
`work/lod_repair/result.json`, and the viewer/native captures. The 36 exported LOD/clip combinations are checked.

## Map integration

`integration/actors.yml` binds `hes_hound A/B/C`. The seven export GLBs are registered in the shared
`hesper_stage/monsters.yml`. D9 slot 2 is Hound, difficulty 2, count 3–5; D13 slot 1 is Hound, difficulty 3,
with its existing zero random-encounter count retained. These maps use placed actors.

- **D4:** append groups 50/51, three/four Kennel Hounds on the flat Waste Shafts floor at z=-1280, south of the
  slag trenches. All original 55 records keep their indices and positions. New total: 62 actors, 60 combatants.
  The five pursuit checks clear the new defenders and use spawned index 62 instead of the former 55.
- **D9:** replace all 12 Veteran Trooper records with Hellhounds while preserving indices and event groups.
  Three guard the Sinkhole Descent. Four move from the barracks to the Royal Tunnels' flat lower landing at
  x=155/445, y=-350/-120, z=-2944. Two Root Throat guards and three Royal Gallery hounds stay with Brute keepers.
  All hounds are mobile. The pursuit-scenario generator now clears unshielded actors once and shielded actors
  twice, using the authoritative shield table, instead of attempting to damage already-dead actors.
  A one-damage provocation establishes aggro for the spawned test defender; all 24 pursuits now pass.
- **D13:** replace eight Drudge Hulks with Pyre Hounds. Five occupy the Heat Exchangers' central aisle; hidden
  group 7's three move from Debris Hall to the western Exchanger Loop near (4900,7250,512), alongside countdown
  Harrowers. Visibility triggers and indices stay intact. Other actors, including the Reaver Drone records owned
  by R5-3, are preserved. The map's scenarios are regenerated from its current build record.

Each shared file/map was claimed and reread before edits. All three map builds report zero compiler warnings.
D4/D9 geometry checks and D9 script checks pass; D13's build-time ceiling/stacking checks pass. There is no separate
`check_geometry.py` in D13. No map geometry was changed.

## Sounds

Eight jobs are added to the shared audio queue: `hound_attack`, `hound_wince`, `hound_death`, `hound_fidget`,
`pyre_hound_attack`, and three pitch-down derivatives for C's wince/death/fidget. The five generated jobs each
request two candidates; the plan estimates 492 ElevenLabs credits. Three wrapper attempts failed DNS resolution
of `api.elevenlabs.io` before generation. No hound audio was charged, generated, processed, picked or hooked.
Sound ids 60150–60157 remain planned, within the assigned 60150–60159 block. Native descriptor sounds remain
until the requested family set can be generated. Audio does not block the model or placement.

## Checks and review

- Design audit: **0 findings**. Actor-size audit: **22 maps, 1,193 actors, 0 mismatches**. Decoration-ID audit:
  **22 maps, 3,433 Hesper decorations, 0 mismatches** at the first completed stage.
- D4/D9 static walkability: zero findings. D13 has one unchanged unreachable control-room plinth at
  (5304,1896,64), 0.04M units²; all actor positions pass. Its geometry is outside this replacement-only package.
- Dedicated spawn/charge scenario: passes all three row spawns and separate B/C charge-hit assertions.
- D9's extra 24-route pursuit scenario passes all **938 steps** after fixing cleanup and provocation.
- Fresh retained D4 saves prove all 31 Kept disappear after reload. D13 saves prove wave/collapse flags
  and the vent return to (5228,1000,0). Its checker explicitly accepts verified version 133 alongside 106;
  the map READMEs document `OPENYAMM_SCENARIO_SAVE_DIR`, needed now that transient saves are removed.
- Native desktop review works through the approved launcher with shared engine/stage locks held for the queue.
  Renderer: OpenGL 3.3, NVIDIA vendor 0x10de, Wayland. Runs are minimized; their FPS is not performance evidence.
  A first nested shell launch failed with `SDL_Init failed: No available video device`; direct approved launcher
  invocation succeeds. No hardware fallback or engine change was needed.
- Pre-motion-v2 full shared regression: **109/109 PASS, exit 0**, `scenarios_151422_2`; logs are copied to
  `review/regression/`, with the command and scenario list in `review/regression_result.json`.
  The earlier run had 69 passes and 40 process-launch permission errors. Its executable changed during
  the run; the complete repeat passes. Those were not 40 gameplay assertion failures.
- Browser check: **27/27 tier/clip switches**, no console errors. All 27 final stills, 12 tier renders,
  12 LOD views and eight retained native screenshots were visually inspected.
- Final native captures cover both D4 kennels, D9 Descent/Royal kennels, D13 Heat Exchangers and the
  countdown Loop. The Loop uses the mechanics proof save, including three already-killed Harrowers;
  it is not a fresh encounter or a Harrower animation review. No hound model-load failures occur.
  D4 was captured before a concurrent engine rebuild; each run record retains its executable hash.
- Seven staged cook sources match the final exports byte for byte. Stage GLBs are texture-cooked,
  so their hashes appropriately differ from the source exports.

## Review links

- [Interactive tier/clip viewer](review/viewer/index.html) — the running repository server also serves it at
  <http://127.0.0.1:8912/level_generation/creatures/hes_hound_codex/review/viewer/>.
- [Current tier colours](review/colours_final.jpg), [tier/pose sheet](review/tiers_final.jpg), [LOD comparisons](review/lods_final.jpg),
  [A clips](review/a-clips_final.jpg), [B clips](review/b-clips_final.jpg), [C clips](review/c-clips_final.jpg).
- [Native map sheet](review/native_final.jpg); full images, tours, game logs and executable hashes in
  [native evidence](review/native/). All native runs were minimized, sequential and on NVIDIA OpenGL/Wayland.
- [Final regression result](review/regression_result.json), [browser check](review/viewer_check.json),
  [D4 save check](review/r5_d04_save_check.log), [D13 save check](review/r5_d13_save_check.log).

Earlier clay/stress images and failed attempt logs are retained as diagnostics; the links above identify the
final review. No combat-balance or performance conclusion is drawn from these mechanics fixtures and captures.

## Reproduction order

For palette-only changes: `textures.py` → `refresh_ramps.py` → `viewer_export.py`, then restage.
`refresh_ramps.py` updates the existing final GLB in place, preserving motion and repaired far LODs. Run it after
`graft_motion.py` too, since that motion script starts from the pre-motion palette snapshot.

Keep the current downloaded jobs. Source processing is `prep.py`, `rig_uv.py`, `repair_skin.py`, `animate.py`,
`bake_ao.py`, `textures.py`. Final assembly/export is `assemble.py`, `build_lods.py`, `finish_runtime.py`,
`far_lods.py`, then `assembly_gates.py`, `lod_animation_gates.py`, `viewer_export.py`. For this motion-only
revision, use `animate.py` → `assemble.py` → `graft_motion.py` → `lodrep/lod_split.py` into
`work/motion_v2_lods` → both gate scripts → `viewer_export.py`; preserve the existing repaired geometry.
Run Blender scripts directly through the creature wrapper, one at a time; run ordinary Python scripts under
the project guard.
`check_texture_return.py` records the rejected strict face-count assumption and is not a final gate; use
`repair_skin.py`'s explicit correspondence report instead. `inspect_floor.py` and `clip_review.py` are optional
diagnostic/review scripts, not alternative production sources.

Restage with the exclusive stage lock. Map builds use their shared stage lock and map claim. Game/scenario queues
hold shared engine/stage locks. Never run the full map rebuild. Use
`OPENYAMM_WALKABILITY_WORKERS=1 level_generation/projects/hesper_stage/rebuild_all.sh --scenarios-only`.
