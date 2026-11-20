# Cleric delivery and review

MM8 `m460` is installed for all three human male Cleric descriptors. The selected editable master is
`export/mm8_m460.blend`; the authoring checkpoint is `work/rig_uv.blend`. The [README](README.md) describes
provenance, animation decisions, palette/texture work, fitting and reproduction.

## Casting step revision — 2026-10-18

The latest Attack/Cast adds a 20 cm left-foot advance, 4.5 cm lift, soft knees and a 9 cm forward hip transfer.
The right foot supports the release; the left foot steps back into the exact original idle endpoint.
The fitted library upper-body channels, source speed, staff grip, palm effects and 1.20-second release stay unchanged.
The robe follows the step and clears the supporting leg. A diagnostic ray check found no exposed lower-leg vertices;
internal overlaps in folded cloth remain beneath the visible surface. The supporting ankle drifts at most 0.20 mm.

Export parity, arm/staff clearance, leg continuity, ground contact, all 24 viewer combinations, normal/half-speed
playback and the focused Cleric runtime regression pass. The updated export was installed and inspected outdoors
and indoors. Body/staff geometry, skin weights, textures and the six other clips remain unchanged.

- [Selection and native capture receipts](review/cast_step/selection.json).
- [Current checks](review/cast_step/checks.json) and [leg/unchanged-channel checks](review/cast_step/verification.json).
- [Step and landing](review/shots/step-landing.png), [rear robe clearance](review/shots/step-rear.png).
- [Current playback](review/playback/playback.json).

The earlier records below retain the initial delivery history. Their planted cast description is superseded by this revision.

## Two-handed casting revision — 2026-10-18

Attack and Cast now use the stored Mixamo **Standing 2H Magic Attack 01** performance at its original speed and
2.7-second duration. Four local candidates were compared on the Cleric. Both arms gather and drive forward, the staff remains
in the fitted right-hand grip, and spell effects charge both palms and leave the left at 1.20 seconds.
The long robe uses planted feet; wrist fitting and a steadier head clear the staff, floor and tall collar.
No extra paid animation or generation jobs were needed.

The ordinary build, focused Cleric regression, all 24 viewer combinations, normal/half-speed playback,
export parity, material/source audits and revised motion/head-clearance checks pass. The current cast has
zero measured arm/staff body crossings, at least 6 mm staff floor clearance and a 55.14-degree maximum wrist bend.
Body/staff geometry, skin weights and the six other clips are unchanged, verified by stored curve/mesh hashes.
The isolated indoor fixture was refreshed to include newly referenced effect assets before the successful rerun.

- [Selection, current native captures and receipts](review/cast_revision/selection.json).
- [Current checks](review/cast_revision/checks.json).
- [Wind-up](review/shots/cast-windup.png), [release and hands](review/shots/cast-release.png).
- [Recorded normal/half-speed playback](review/playback/playback.json).

The following full-delivery notes and native gallery describe the initial revision; the cast information above
supersedes its staff-led gesture, timing and launch point. The broader actor suite was not repeated for this
localized animation revision; its earlier Boulder binding failure remains a historical result, not a new finding.

## Initial-delivery checks

- Ordinary desktop `openyamm` build passes. A model-cook cache collision during an overlapping build/install
  was resolved by completing the installs first and rerunning the build sequentially; no engine changes were needed.
- The new `mm8_cleric_actor_models_keep_tiers_roles_and_staff_cast` regression passes. It checks the three native
  tiers, shared asset, staff attachment, standing height, four body LODs, sockets, eight clip durations,
  unchanged simulation state and actual Light Bolt origins for A/C. B retains its native non-projectile buff.
- The MM8 actor suite reports **46 passed / 1 failed**. The unrelated
  `mm8_malevolent_boulder_actor_models_keep_stone_motion_and_spells` check expects a bound Boulder model;
  the current manifest contains no `Malevolent Boulder A/B/C` entries. This task changes only Cleric bindings.
- Accepted Sorcerer and Djinn/Genie model regressions pass.
- Final viewer check passes **24 tier/clip combinations**, with no console errors. All genuine native stored views
  are available, deduplicating mirrored/repeated directions and selecting the corresponding palette.
- Export parity, half-frame deformation/contact checks, head-look clearance, static source hashes, eight-weight
  skinning and runtime material/atlas audits pass. Body/head colour and normal seams were corrected after playback;
  the final re-export preserves the same geometry and animation samples.
- Recorded normal/half-speed playback covers every role; close views inspect face, both hands, feet/robe and corpse.

The selected walking adaptation carries the staff upright. Native walking sprites carry it low and more horizontally;
this is an intentional fitted 3D adaptation using the grounded Sorcerer-style carry, not an exact sprite reconstruction.
The Djinn source supplies the open-hand cast. The death releases the staff and settles into a side/prone corpse;
its final pose is held exactly by Dead. Nine planar staff endcap triangles intentionally sample a single UV texel each, with uniform paint and flat normals.
Coarse LODs are intended for distance and lose small trim/face detail.

## Native game review

Captures use the normal OpenGL desktop build on NVIDIA (`vendor=0x10de`), SDL Wayland. They are visual checks,
not performance measurements. All three tiers are shown outdoors at New Sorpigal and indoors at Agar's laboratory,
with corresponding original-sprite captures at the same cameras. The indoor fixture only preloads the native sprite
family; its scene change is isolated from production maps. Forced LOD0–LOD3 captures inspect silhouette continuity.
Live combat captures inspect walking, the charge/release gesture and the dropped-staff death.

- [Outdoor models](review/ingame/lod_tour/lod0.png) / [native standing sprites](review/ingame/outdoor_sprite/party.png).
- [Indoor models](review/ingame/fixture_in_3d/party.png) / [native sprites](review/ingame/fixture_in_sprite/party.png).
- [LOD3 forced close for inspection](review/ingame/lod_tour/lod3.png).
- [Casting charge](review/ingame/casting/cast-03.png) / [release](review/ingame/casting/cast-15.png).
- [Death and dropped staff](review/ingame/death/death-06.png). The later capture shows the normal loot bag
  replacement after the fall; the persistent Dead pose is also reviewed in the exported viewer.
- [Capture receipts and hashes](review/ingame/captures.json).
- [Build and regression logs](review/checks/).
- [Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m460_claude/review/viewer/).

The user explicitly accepted the current Cleric and stepping two-handed cast on **2026-10-18**: "ok accepted".
The accepted revision and body hash are recorded in `creature_3d_progress.json`. Android and Vulkan were not tested. No staging or commit was performed.
