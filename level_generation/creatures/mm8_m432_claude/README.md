# MM8 Dark Elf warrior — Claude humanoid workflow

Installed production model of the m432 family: Dark Elven Warrior, Defender and Crusader (monster IDs 25–27;
`Dark Elf Warrior A/B/C`; native palettes 433/434/435). User artistic acceptance remains pending.

[Interactive three-tier viewer](http://127.0.0.1:8767/level_generation/creatures/mm8_m432_claude/review/viewer/)
uses the existing repository server on port 8767. [Native motion study](ANIMATION_STUDY.md) records the source
inventory, action intent and selected local clips. [Progress and receipts](creature_3d_progress.json) are canonical.

## Selected deliverables

- [Editable Blender master](delivery/mm8_dark_elf_warrior.blend), with packed textures and 60-fps actions.
- [Portable assembled GLB](export/mm8_m432_lod0.glb), including the animated sword.
- [Runtime body](export/mm8_m432.glb) and [rigid sword attachment](export/mm8_m432_sword.glb).
- Installed authoritative sources: `assets_source/worlds/mm8/models/mm8_m432.glb` and
  `mm8_m432_sword.glb`; installed runtime copies and cooked textures are under the matching `assets_dev` scope.
- Bindings are appended to `assets_dev/worlds/mm8/models/actors.yml`. Original sprites remain intact.
- Five selected body masters are under `references_hd/`; head and sword references have their own folders.
  The three-quarter v2 is selected; the first draft is retained as superseded provenance.

The fitted 58-bone rig has measured five-finger hands, four twist helpers, a sword socket and a left-palm spell socket.
The long gold-hilt sword uses both hands for locomotion and attack, the right hand during casting, and drops during
Death. Dead holds the settled side corpse and the same dropped sword position.

| Clip | Seconds |
| --- | ---: |
| Standing | 2.000 |
| Walking | 1.367 |
| Running | 0.600 |
| Attack | 1.833 |
| Cast | 1.667 |
| Hit | 0.600 |
| Death | 2.400 |
| Dead | 1.000 hold |
| Fidget | 2.000 |

These are fitted local Mixamo/humanoid motions and an authored fidget, rather than frame-by-frame native animation
reconstruction. The native attack aliases share Attack. Melee impact is measured at 0.916667 s, cast release at
0.816667 s. Runtime presentation fits these to unchanged native combat timing; Hit remains within the native 0.625 s.
Walking and running strides are 2.094 m and 3.509 m. All tiers share scale 120.3479286: 167 native body pixels ×
1.299988 divided by the exported standing head top, 1.8039197 m. The sword is excluded from that measurement.

## Geometry and materials

Body colour/shadow LODs: **10,893 / 5,444 / 1,955 / 647 triangles**. Sword LODs: **278 / 138 / 49 / 23**.
The established actor LOD builder uses stronger reduction for its two distant levels than a strict half-per-level
sequence. Skinning is limited to four influences. Face, hair and glove geometry was preserved during base reduction.

One shared 1K body set, one 1K head set, and a 256×1024 sword set. Runtime body/head materials are merged into
2080×1024 atlases. Cloth and medallion regions use measured native palette ramps; the viewer bakes those ramps solely
for three.js preview. Skin, hair, black armour and gold fittings retain their colours across tiers.
Metallic is zero; ORM red carries the current playbook's specular mask, green roughness. Body/head normal maps were
measured and converted to glTF +Y. The two broad sword faces intentionally share their symmetric ornament.

Meshy UV transfer matched every corner with no geometry mismatch. Local repacking separated 183 overlapping head
triangles while retaining their pixels and geometry. The final 1K raster check has no body overlap and two isolated
head boundary pixel coincidences among 522,870 covered pixels. Collar hair-colour spill was cleaned locally; silver
hair retains strand detail. Thirty-three armour studs were refitted to the reduced surface with interpolated host
triangle weights. Meshy spending: **30 credits** of the 100-credit project limit (body 5, rig 5, body/head textures 10 each).

## Verification

- Ordinary `openyamm` build passed; all **8 MM8 actor regressions passed**, including this family's three variants,
  attachment nodes, nine durations, reduced LODs and unchanged simulation state.
- All **27 tier/clip switches** passed in the viewer, without console errors. Browser playback completed all
  **18 clip/speed combinations** at normal and quarter speed; timed frames and readouts are in `review/final_playback/`.
- Export reimport was compared against the master across every clip, densely through attack, cast and death:
  maximum sampled surface error **0.235 mm**. See `review/export_parity.json`.
- Body/opposite-arm/sword penetration gates passed all moving roles at half frames. Attack wrist swing is at most
  58.60°, twist at most 88.48°. Contacts, grip, fingers, soles, fall and corpse were also visually reviewed.
- Native desktop checks use OpenGL 3.3 on the NVIDIA GPU, isolated settings/saves, and engine-written PNGs.
  Outdoor native sprite scale comparison and indoor model/death checks passed. See [native review](review/ingame/README.md).
  The indoor original-sprite baseline remained invisible in three reference attempts; that playbook comparison is
  explicitly incomplete. This did not prevent the 3D family from rendering or passing its runtime regression.

Android and Vulkan were not tested. The final appearance is available for the user's artistic review.

## Attack v2 (2026-10-19, installed)

Installed 2026-10-19 (round 2, user: "dark elf warrior ok") with the reduced model
(`../mm8_m432_reduce_claude/`, 8,253 triangles); the installed source is no longer this project's export.

User review of the reduction (`../mm8_m432_reduce_claude/`): the old Attack crossed the arms, drove the right upper
arm into the pauldron and left the left hand off the hilt (42 mm grip gap in `work/two_hand_fit.json`); "find some
fitting 2 handed animation, like the lizardman warrior". `scripts/attack_v2.py` fits the Lizardman Warrior's
approved slash (Mixamo Great Sword Slash (2); `../mm8_m404/3d_claude/scripts/fit_mixamo_attack.py` and
`fit_mixamo_legs.py`, read only) to this rig.

- **Retarget and grip:** world-rotation copy onto the cloned frames, and a rigid two-hand grip with the left hand
  0.115 m down the handle, as in Standing.
- **Wind-up re-path** (round 2, after the user found rubber-hose arms in round 1's low back-swing, which needed
  about 185 degrees of hand roll against the upper arms): before the source's top of the wind-up (source frame 15.5)
  the grip, both hands and the arm reference poses blend from the guard to that top pose in the chest frame. That is
  the shortest turn, plus a 0.12 m bulge to the right side. The torso, head and legs keep the source.
- **Arm fit:** elbow plane and hand roll chosen over the whole clip, with head clearance (an in-box test, since the
  head set is an open shell). Shoulder roll is softly limited from 60 degrees and forearm twist from 80. A smoothed
  grip turn (5 degrees here) applies where a wrist would bend past 55. Blade roll makes the edge lead. Then the
  source steps and pelvis weight transfer.
- **Solver:** `scripts/armik_v2.py` is the m404 solver. Its elbow-plane normal blends from the arm's own plane at the
  clip ends (exactly Standing frame 0) to the hinge axis.
- **Impact and timing:** impact is where the blade passes level, pointing ahead, on the downswing. The clip is
  retimed so that lands on the bound 0.917 s inside the unchanged 55 frames: the wind-up 1.2x slower, easing to real
  speed at the blow.

Output: `work/rig_textured_fit_attack_v2.blend` (old clip kept as `Attack_v1`; `export_runtime.py` now reads it) and
`work/attack_v2/fit.json`. Round 1 is kept as `work/attack_v2/*_round1.*`.

- **Grip and wrists:** grip gap 0.0006 mm; visible wrist bend 48 / 56 degrees; forearm twist 31-96 / -84 to -31
  degrees across the clip (round 1 ran to 240).
- **Soles and impact:** soles >= -1 mm; the blade is 7 degrees off the facing at impact.
- **Probes:** `scripts/attack_v2_gates.py` (hand stretch 2.14x, soles, jerk, g6: no contacts;
  `work/attack_v2/g6_contacts.json`). `scripts/attack_v2_contacts.py` samples the upper arms against the torso,
  other arm and pauldrons, which g6 does not (`work/attack_v2/arm_contacts.json`): one right upper-arm vertex in the
  follow-through.
- **Shipping:** only through the reduced model. `scripts/attack_v2_export.py` writes the animation-only GLB that
  `../mm8_m432_reduce_claude/scripts/attack_transplant.py` puts into that export.

## Rebuilding from retained work

The selected motion checkpoint is `work/rig_reduced.blend`; `final_motion_tune.py` records its arm-continuity recipe.
Paid returns under `meshy/` are immutable. The finish sequence is `texture_return.py`, `repack_head_uv.py`,
`reproject_head_maps.py`, `raster_final_uv.py`, `fit_final_fasteners.py`, `compose_m432.py`, then `final_export.py`.
Use the creature workspace lease and guarded Blender launcher described by the creature-to-3D skill.

After export: `tools/prepare_actor_glb.py`, `scripts/build_lods.py`, `scripts/postprocess_runtime.py`, and
`tools/install_model.py --world mm8` for both body and sword. `viewer_tiers.py` and `update_manifest.py` refresh the
browser artifacts. Final hashes and installed-file receipts are recorded in `delivery/manifest.json`.
