# Malevolent Boulder — MM8 m588

> **Installed model reduced (2026-10-19):** the installed model is now the reduction from [`../mm8_m588_reduce_claude/`](../mm8_m588_reduce_claude/README.md) (LOD0 5,350 -> 4,928). This project's exports and master remain the unreduced production; the rollback source is in `../mm8_m588_reduce_claude/work/`.

Completed rigged 3D production, 2026-10-18. Technical and agent visual review are complete;
The user accepted this version with “good” on 2026-10-18. The original 2D restoration remains in `../mm8_m588/`.

[Interactive review viewer](http://127.0.0.1:8765/level_generation/creatures/mm8_m588_claude/review/viewer/)
includes all three tier sizes, seven clips, normal/quarter-speed playback, camera views, scrubbing and
frame-specific feedback. The viewer starts on Attack. It uses the portable GLB; engine mouth effects are
visible in the native combat captures instead.

## Selected deliverables

- [Packed editable master](export/boulder_master.blend), with the final mesh, rig, materials and all clips.
- [Portable GLB](export/boulder_portable.glb), including embedded ordinary PBR maps and animations.
- [Runtime GLB source](export/mm8_m588.glb), including native palette variants, colour and shadow LODs.
- [Exact actor bindings](export/actor_bindings.yml), installed for Malevolent Boulder A/B/C in
  `assets_dev/worlds/mm8/models/actors.yml`.
- Installed source: `assets_source/worlds/mm8/models/mm8_m588.glb`; cooked asset and content-addressed
  textures: `assets_dev/worlds/mm8/models/`.
- [Canonical progress and receipts](creature_3d_progress.json), [final review](review/final_review.json),
  [package counts and hashes](work/package_check.json), [placement](work/placement.json).

## Identity, construction and materials

The native creature is an eyeless, squat grey-violet boulder with a jagged mouth and rounded basal stones.
Earth Elemental was a surface/silhouette benchmark only: there are no invented arms, legs or eyes.
The native sprite inventory and motion selection are preserved in [native/](native/); selected front,
back, left, right and three-quarter HD references and generation provenance are in [references_hd/](references_hd/).

The model uses one opaque material and 34 bones: Root/Core, the cap, the jaw, and rigid stone clusters.
Every vertex has exactly one joint influence. Separate rocks move as solid pieces; no rubber-like skinning.
`Socket_Mouth` follows Core for native projectile and spell release. No external equipment or attachments.

LOD triangle counts are **5350 / 2673 / 1327 / 648**, with four shadow LODs. No degenerate triangles or
non-finite positions/normals were found. The upper LODs preserve the small rock contours; distant LODs
use angular stone masses. The rock material uses a 2K diffuse map, 1K normal/ORM/region maps, zero metal,
roughness 0.86–0.98 and specular 0.12. The normal green channel was corrected for the selected convention.

All tiers use native palette 588. Their frame scales are **1 / 1.299988 / 1.699997**;
there are no invented colour variants. Standing height is calibrated to the native 163-pixel alpha height
at A scale (210-pixel width), with asset scale 83.24835228474802. Collision and gameplay dimensions are unchanged.

## Motion

| Clip | Seconds | Construction |
| --- | ---: | --- |
| Standing | 3.0 | Subtle stone settling, seamless loop |
| Walking | 1.0 | Grounded rocking and basal stone motion, seamless loop |
| Attack | 1.5 | Backward anticipation, large cap/jaw gape, forward bite/release and recovery |
| Cast | 1.5 | Longer sustained gape, stone tremble and release recoil |
| Hit | 0.625 | Short rigid recoil matching native timing |
| Death | 1.25 | Rock clusters break apart and settle into rubble |
| Dead | 1.0 | Held rubble with no loop motion |

Native Standing/Walking/Fidget reuse one standing frame, so gait is an authored adaptation. Fidget maps to
Standing. Native attack impact stays at **1.0 seconds**; extra recovery and death-settling time are visual tails.
The mouth charges gold-white through existing engine socket effects. Physical melee, Rock ranged attack,
Blades/Rock Blast spell selection and the native earth explosion special remain table-driven.
The game's normal corpse presentation removes the finished rubble and leaves loot bags; the portable Dead clip
retains the rubble for inspection.

Clips use dense quaternion keys. [Export parity](work/export_parity.json) compares the reimported portable
GLB against the Blender master at half-frame intervals: maximum vertex error is approximately 0.0000011 m,
with zero loop seams. Ground error is below 0.00014 m penetration; the largest between-sample clearance is
0.0093 m (under one game unit).

## Verification and review evidence

- All 21 tier/clip combinations load in the browser without console errors. All seven clips were played at
  normal and quarter speed; [playback evidence](review/playback/) retains 70 frames and timing results.
- Native OpenGL 3.3 captures used the NVIDIA GPU. [Outdoor models](review/ingame/out_models_fixed/tiers.png)
  and [sprites](review/ingame/out_sprites_fixed/tiers.png), plus [indoor models](review/ingame/in_models_fixed/tiers.png)
  and [sprites](review/ingame/in_sprites_fixed/tiers.png), preserve the tier scale comparisons.
- [Outdoor pose/LOD contact sheet](review/ingame/out_poses/contact.png) and
  [indoor pose/LOD contact sheet](review/ingame/in_poses/contact.png) cover all seven clips and forced LOD0–3.
  Their directories retain full-resolution engine screenshots, exact console tours, run records and logs.
- [Live combat](review/ingame/out_combat/contact.png) shows the mouth charge, gape and physical rock release
  through ordinary actor AI. [Death transition](review/ingame/out_models_fixed/death.png) and
  [normal corpse cleanup](review/ingame/out_models_fixed/rubble.png) were also inspected.
- Normal development build passed. [Focused Boulder regression](review/regression-focused.log): 1 pass,
  0 failures, covering shared assets, three tiers, rigid bones/socket, LODs, clips, launch point and unchanged
  simulation state across native animation roles.
- [Wider MM8 actor suite](review/regression-mm8.log): 46 passes, 4 failures in other creature checks:
  Dark Dwarf Attack duration, Troll peasant presentation/simulation, Bedraggled Human standing height,
  and incomplete Dragon Turtle tiers. The Boulder case passes in this suite too.

The review uses isolated copies of the standard MM6 indoor/outdoor reference scenes with MM8 tiers inserted;
production maps were not edited. [Fixture record](review/ingame/fixture.json) documents the stationary actors
and an isolated exclusion of a concurrently introduced Wisp effect that initially prevented fixture startup.
Earlier `out_models`/`out_sprites` captures are superseded because friendly AI moved the subjects out of frame.
Android and Vulkan were not tested. Minimized capture runs are visual evidence, not performance measurements.

## Production checkpoints

Meshy receipts total **25 credits**: 5 for mesh-only Smart Topology, 10 for the first texture pass, and 10 for
selected texture v2. The first texture pass was superseded after correcting inefficient UV packing from
16.1% to 49.9% coverage. The final mesh was widened 1.125 times to match the squat native silhouette.
All requests, returns and rejected references remain preserved; no additional paid work is pending.

The selected animated UV master is `work/animated.blend`. `scripts/export_textured.py` produces the packed
master and portable model. `scripts/export_parity.py` validates that actual export. The existing shared
material-preparation, `scripts/lods.py`, `scripts/package.py` and `tools/install_model.py` complete the runtime
handoff. `scripts/bind_runtime.py` is a one-time installer and asserts that the family is absent; do not append
the bindings again. The proportion, UV and node-name correction scripts are historical one-time migrations.

All future project writes use a new creature-workspace lease. This run's lease is released at handoff.
