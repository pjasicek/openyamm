# MM8 Raven Man — m584

Shared Claude playbook production: winged humanoid with an articulated feather fan, five-fingered hands,
bird feet, leather harness, tier-coloured loincloth and two-handed glaive.

## Deliverables

- [Interactive review](http://127.0.0.1:8765/level_generation/creatures/mm8_m584_claude/review/viewer/):
  Rook, Corbie and Raven; six clips, frame scrubbing, normal/slow playback and native references.
- [Packed editable master](export/raven_master.blend).
- Portable baked-colour GLBs: [Rook](review/viewer/raven_a.glb), [Corbie](review/viewer/raven_b.glb),
  [Raven](review/viewer/raven_c.glb).
- Runtime sources: [body](export/mm8_m584.glb), [polearm](export/mm8_m584_polearm.glb).
  Installed through `tools/install_model.py` under `assets_source/worlds/mm8/models/` and cooked under
  `assets_dev/worlds/mm8/models/`. Bindings are Raven Man A/B/C in the MM8 `actors.yml`.
- [Canonical progress](creature_3d_progress.json), [delivery receipt](delivery.json).

## Native authority and placement

| Monster | Descriptor | Skin | Palette |
|---|---|---|---|
| 139 Rook | Raven Man A | raven_a | Pal585 |
| 140 Corbie | Raven Man B | raven_b | Pal586 |
| 141 Raven | Raven Man C | raven_c | Pal587 |

Original BMPs, palette tables, monster descriptors and native sprite-frame groups establish identity and timing.
The native inventory records 140 source files, including five view aliases. The existing `mm8_m584` 2D project
and original sprites remain separate. HD views clarify the anatomy; hidden surfaces and individual feather
construction are an interpretation, not recovered original geometry.

All tiers use model scale **75**, yaw offset **-pi/2**. The approximately 1.8 m body corresponds to the native
roughly 134-pixel head-to-foot figure. The original 256-pixel canvas leaves about 42 pixels below the living
feet: living clips add **0.56 m** of hover, and Death eases this away over 0.9 seconds. Dead remains grounded.
An initial scale 83.2 with feet at the actor anchor was rejected after native outdoor comparison.
`work/native_placement.json` records the correction. No permanent `z_offset` lifts the corpse.

The native one-second wingbeat is authored twice in each two-second flight clip. The existing runtime requires a
locomotion stride for an animation block: both flight strides are 5.333333 m, giving a two-second clip cycle at
native speed 200 / scale 75. Native flight, collision dimensions, physical melee damage, recovery and AI remain
owned by existing gameplay data; no renderer or gameplay feature was added.

## Mesh, rig and feather treatment

Body plus wings: **14,290 triangles**, 7,763 connected vertices before UV splitting. Polearm: **1,536 triangles**.
Colour LODs are **14,290 / 9,394 / 6,909 / 5,384** for the body and **1,536 / 767 / 383 / 192** for the polearm.
The body has matching shadow LODs. Global collapse opened gaps between feather shells in the native LOD check.
The final LODs therefore retain all 4,024 wing triangles while reducing the humanoid and polearm. This intentional
deviation from halving each level preserves feather coverage. `work/lod_preservation.json` verifies that LOD0,
textures, skin and animation samples are unchanged by this correction.

The source-frame rig has **101 bones**: 52 fitted humanoid bones, 44 wing/flight-feather controls, one polearm
joint and four arm twist bones. Hands were fitted from the actual mesh and weighted by connected fingers.
Automatic arm weights were smoothed through the shoulder/armpit transition after the falling-pose check.
Up to eight influences preserve those transitions; the largest removed weight is 0.00465.

Meshy's fused wing sheets were replaced with two closed wing cores, 36 individual primary/secondary flight
feathers and 144 overlapping coverts. Shoulder, elbow, wrist and feather controls fold and fan through each
stroke. Coverts follow their associated flight feather. The corpse fans the inner secondaries away from the
thighs. All feather geometry is opaque. Feather material class 2 intentionally uses roughness around 0.72 and
specular mask 0.3, instead of the shared fur class's fully matte settings.

The polearm is rigidly weighted to its own joint. Both hands fit the shaft, with measured palm centres and
finger poses. During death the shaft slides axially clear of the closed hands before the hands open; the
released weapon then settles beside the corpse. Runtime uses a separate attachment on the same animated joint.

## Materials and tiers

Body/wings and head were painted separately from the selected HD references. The first head upload was rejected
because its UV islands used less than 1% of the texture. Separating the head before square Smart UV packing
produced approximately 51% coverage; the second head texture is selected. All original returns and paid receipts
are retained. Body UV coverage is about 63%; nearest-face/corner transfer reports under 0.1 mm maximum mismatch.

Body and head use separate 1K PBR sets, merged without rescaling into 2080 x 1024 runtime atlases with a 32-pixel
gutter. The polearm has its own cropped shared set. Native palette indices 8-33 drive the loincloth/blade ramps;
black feathers, skin, leather, silver fittings, beak and eyes retain their own colours. Three variants share
geometry and textures. Portable copies bake the same ramps into their base colours for ordinary glTF viewers.

Ambient occlusion is graded into base colour. ORM red is the engine's specular mask. Skin, feathers, keratin,
eyes, leather/cloth, metal and wood use separate material classes. All three normal maps were measured and
corrected once to the glTF convention. The atlas audit found no zero-area geometry or UV triangles and only
0.0232% overlapping interior texels at atlas resolution.

## Motion and checks

| Clip | Seconds | Source / purpose |
|---|---|---|
| Standing | 2.0 | Native wingbeat and hovering carry |
| Walking | 2.0 | Forward flight, slight body lean |
| Attack | 1.166667 | Body-led right-high to left-low slash, fitted two-hand grip |
| Hit | 0.733333 | Local spear hit response with airborne recovery |
| Death | 1.5 | Authored forward fall, wing settling and polearm release |
| Dead | 1.0 | Held grounded corpse |

Local source clips were selected before modelling. The sideways source death was rejected for the winged body.
These are adapted 3D performances rather than exact sprite-keyframe reconstructions. The native attack lasts
0.875 s and has no earlier attack marker; model impact is **26/30 s**, within 8.4 ms of the native action end.
The full clip fits the fastest tier's 70/60-second recovery. Hit fits inside the native 0.75-second duration.
Fidget uses the same hovering Standing loop, as in the native data.

- Half-frame checks: [deformation](work/deformation_final.json), [contacts](work/contacts_final.json).
  Worst arm edge p99 is about 1.98x; hand maximum 2.32x. No checked limb/feather/polearm penetration over 2 mm
  remains. The final corpse floor error is below 0.001 mm. These are sampled geometry checks, not a universal
  collision proof for every possible runtime blend.
- [Export/reimport parity](work/export_parity.json): 60 Hz samples retain the reviewed motion within 0.07 mm.
- [UV audit](work/uv_audit.json), [material audit](work/material_report.json),
  [package assertions](work/package_check.json).
- Textured frame sequences: `review/animation_textured/`. Actual normal/quarter-speed browser playback:
  `review/playback/`. The existing viewer includes the eight-weight skinning extension.
- Native captures and launch records: `review/ingame/`. Comparisons use an isolated asset fixture that preloads
  the MM8 sprite families into known indoor/outdoor review scenes; production maps are unchanged.

## Reproduction and cost

Use the project lease with `tools/run_creature_blender.sh` / `tools/run_creature_meshy.sh`; do not run competing
writers in this project. Geometry/rig scripts preserve their intermediate checkpoints and source selection.
The finish order is `finish_rig.py`, `export_uploads.py`, `repair_head_uv.py`, `finish_uv.py`,
`compose_textures.py`, `export_textured.py`, `tools/prepare_actor_glb.py`, `finish_exports.py` (including feather-preserving LODs),
`package.py`,
`uv_audit.py`, then installation and native checks. `hover_height.py` is idempotent and runs after final weighting.
Existing selected body/head/prop returns should be reused; reproduction does not require new paid jobs.

Meshy receipts total **55 / 100 credits**: body 5, auto-rig 5, textured polearm 15, body texture 10, rejected first
head texture 10, corrected head texture 10. Animation comes from the local library and authored motion; no paid
animation jobs were needed. User artistic acceptance is separate from technical and agent visual completion.

## Final delivery verification

Ordinary `openyamm` build passed. The focused
`mm8_raven_man_actor_models_keep_flight_and_polearms` regression passed against the final installed body.
The shared viewer checker passed all 18 tier/clip combinations with no console errors. All three portable
exports completed normal and quarter-speed playback of all six clips, with reports bound to the original delivery hashes.
The Attack-only revision below supersedes that clip; preservation checks retain the other five clips exactly.

Desktop OpenGL captures cover all tiers indoors/outdoors, the six posed actions, live hostile flight/combat,
hit/death and the ordinary loot-satchel transition. A stationary model verifies LOD0-3 at the same pose;
the earlier moving-actor LOD attempts are not used as placement evidence. See
[native review](review/validation/native_review.json) and [launch records](review/ingame/launch_records/).
The fixture's production map sources and all inventoried native sprites passed hash preservation checks.

Technical production and agent visual review are complete. Android/Vulkan rendering was not checked;
user artistic acceptance is not recorded. No commit was made.

## Stronger diagonal Attack — revision 3

The requested attack revision starts beside and above his own right shoulder, holds the coiled wind-up at
0.62–0.70 s, then slashes across to his left. The body leans back 15 degrees during anticipation and forward
22 degrees through the follow-through, with a 32-degree rightward coil and 55-degree leftward finish.
The pelvis and chest share the turn; the feathers sweep back to clear it. Both hands remain fitted to the shaft.
Impact remains 26/30 s and the complete action remains 35/30 s, preserving the runtime timing contract.

[Revision evidence](review/attack_revision_1/revision.json) includes the 60 Hz contact/deformation checks,
normal/quarter-speed playback for all tiers, indoor/outdoor native poses, live combat and focused actor regression.
Exported Attack surface error is under 0.05 mm. Geometry, materials, LODs, skin and all five other clips are
unchanged, verified in [export preservation](work/attack_revision_1/export_preservation.json).
The editable master and intermediate checkpoints carry the same revised action. The viewer now opens on Attack.

To reproduce this scoped revision from its retained baseline: run `revise_attack.py`, `check_attack_candidate.py`,
`publish_attack_blends.py`, then `publish_attack_clip.py`; install `export/mm8_m584.glb` with `tools/install_model.py`
and repeat the recorded browser/native checks before `finalize_attack_revision.py` with the two launch folders.
The full-production finish order above predates this revision. No additional Meshy credits were used.
Android and Vulkan were not rechecked; user artistic acceptance is not recorded.
