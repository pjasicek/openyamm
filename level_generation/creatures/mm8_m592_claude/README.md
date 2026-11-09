# MM8 Plane Guardian — m592

> **Installed model reduced (2026-10-19):** the installed model is now the reduction from [`../mm8_m592_reduce_claude/`](../mm8_m592_reduce_claude/README.md) (LOD0 10,996 -> 8,574). This project's exports and master remain the unreduced production; the rollback source is in `../mm8_m592_reduce_claude/work/`.

Complete creature package, installed for all six Plane/Chaos Guardian descriptors. Technical checks and agent
visual review are complete. User accepted revision 03, including the subtle side-to-side attack lean, on 2026-10-18. The canonical state, selected hashes
and all paid-job receipts are in [creature_3d_progress.json](creature_3d_progress.json).

[Open the review viewer](http://127.0.0.1:8912/level_generation/creatures/mm8_m592_claude/review/viewer/).
It provides three native palettes, nine clips, source-frame comparisons, normal/slow playback and close views.


Latest revision: **subtle side-to-side attack lean** following the user's feedback.
Windup leans 5.5 degrees toward one side; the release leans 4.5 degrees toward the other, with planted feet. Compared the local Mixamo mutant attacks and
MM6 wolfman, then adapted the wolfman's hip/chest drive, planted-foot knee bend and double-claw follow-through.
[Selection and rationale](review/attack_revision_02/selection.json), [preservation checks](review/attack_revision_03/preservation.json),
[native attack review](review/attack_revision_03/native_review.json) and [focused regression](review/attack_revision_03/regression.log).
The seven other clips, geometry and materials are exactly preserved. Additional Meshy cost: **0 credits**.

## Deliverables

- [Editable packed Blender master](export/mm8_m592.blend): 30 fps authoring, fitted anatomy and all actions.
- [Portable LOD0 GLB](export/mm8_m592_lod0.glb): embedded textures and nine animations sampled at 60 Hz.
- [Runtime GLB](export/mm8_m592.glb): three region-ramp palettes, four colour and four shadow LODs.
- [Texture maps and masks](textures/), [palette ramps](textures/m592_ramps.json),
  [runtime bindings](review/runtime_bindings.json) and [measured animation timing/stride](review/runtime_measurements.json).

The runtime source is installed at `assets_source/worlds/mm8/models/mm8_m592.glb`, with its cooked model/textures
under `assets_dev/worlds/mm8/models/`. Six entries in that world's `actors.yml` bind the shared model.
Runtime source SHA256: `afc035cb9fd6f1e1c39f1c262faa92d3c1b3ff8debb9000878c0b0dc5b6e28ce`.

| Palette | Plane ID/name | Chaos ID/name | Descriptor suffix |
| --- | --- | --- | --- |
| 593, gold | 145 Plane Guardian | 196 Chaos Guardian | A |
| 594, green | 146 Plane Protector | 197 Chaos Protector | B |
| 595, red | 147 Plane Overlord | 198 Chaos Overlord | C |

Plane descriptors are `Plane Guardian A/B/C`; Chaos descriptors are `Wimpy Plane Guardian A/B/C`.
Native visible standing height is 132 pixels. Plane scale 2.0 gives 264 world units; Chaos scale 1.199997 gives
158.399604 world units (60%). Exact posed LOD0 bounds validate both sizes. Native statistics and Paralyze remain intact.

## Anatomy, motion and materials

The Guardian has its own fitted anatomy: hunched grey body, low fanged muzzle, mane/beard, three rigid claws per
hand and three-toed feet. There is no equipment. The completed MM6 Ogre supplies adapted locomotion and recoil
plus fall timing; the MM6 Devil/Demon was a gesture benchmark. The current attack adapts the completed MM6 wolfman double-claw rake, with a hip drive, knee bend and trunk lean.
Its grounded choreography replaces the initial single-arm rake after user feedback. This does not depend on building an Ogre Warrior or copying another creature's mesh.

The rig has 33 bones plus the exported right-palm socket, with at most four influences per vertex. Whole upper/lower
dental arches prevent split-fang deformation. Four arm twist controls spread soft-skin rotation; all six talons stay
rigid. Neck/head following is limited to 15 degrees yaw and 10 degrees pitch after shoulder-clearance checks.

| Clip | Seconds | Use |
| --- | --- | --- |
| Standing | 2.0 | Low guard and breathing |
| Walking | 0.8 | Adapted Ogre gait, measured stride 0.939 m |
| Running | 0.833333 | Adapted Ogre gait, measured stride 1.059 m |
| Attack | 1.5 | Wolfman-derived whole-body double-claw rake |
| Cast | 1.5 | Native attack alias for Paralyze |
| Hit | 0.5 | Recoil |
| Death | 1.3 | Backward fall, spread arms and raised feet |
| Dead | 0.033333 | Held final death pose |
| Fidget | 0.633333 | Shoulder lift and jaw roar |

The attack/cast marker is 0.95 seconds on the descending rake, near peak six-claw forward reach at 0.941667 seconds.
The engine fits it to the unchanged native 1.0-second gameplay event. Cast uses the right-palm launch socket.
There is no added hand glow. Export sampling preserves every clip's duration.

Colour LOD triangle counts are **10,996 / 5,476 / 2,724 / 1,350**. Each has one merged body/head primitive and a
corresponding shadow level; reduced shadow shells are inset to avoid self-shadow artifacts. Closed shells face
outward and there are no zero-area triangles. The reduction protects face and claw detail.

The independent body/head 1K maps are joined into 2080 × 1024 atlases with a 32-pixel gutter. Body UVs were transferred
from the Meshy retexture by verified face correspondence; the head retains its dedicated UV layout. Gold/green/red
mane ramps follow native palettes and exclude teeth. Hide/hair remain matte; eyes, teeth and claws receive selective
shine using the runtime `openyamm_specular_mask` channel. Tangent normals use glTF +Y.

Nine selected HD body/head masters, exact prompts, input/output hashes and actual dimensions are recorded in
[references_hd/generation_runs.json](references_hd/generation_runs.json). Native evidence is in the
[inventory](native_inventory.json), [anatomy study](references/anatomy_details.png),
[motion selection](motion_selection.json) and [source motion comparison](review/source_motion/selection_contact.jpg).
Hidden anatomy is reconstructed, not recovered original geometry.

## Verification

- [Static export audit](review/static_audit.json): counts, weights, indices, normals, variants and source/export hashes;
  final merging/LODs preserve LOD0 positions and animation samples exactly.
- [Export parity](review/export_parity.json): 117 master-versus-GLB poses, maximum 0.845 mm interpolation difference.
- [Final GLB motion gates](review/export_motion_gates.json): all nine clips sampled at 120 Hz, no sampled arm/body
  contacts, hard-claw edge error below 0.011%; maximum sole penetration 5 mm running and 1.27 mm during death.
- [Head-follow probes](review/head_look.json): 150 samples across the selected yaw/pitch limits.
- Shared viewer check: all 27 palette/clip combinations passed without console errors. Eighteen actual normal/half-speed
  recordings and temporal frames are retained in [playback](review/playback/). Temporal frames, close views and dense
  surface samples were inspected; continuous video perception is not claimed.
- [Focused regression](review/native-regression.log): six descriptors, visible heights, shared variants, all clips,
  LODs, palm marker and unchanged native combat/simulation state passed. Ordinary desktop build passed.
- [Initial-production broader actor suite](review/actors-regression.log), not rerun for this attack-only revision: 113 passed, 7 failed before aborting with `std::bad_alloc`; the full suite is not green. The Guardian passed. Reported failures concern Malevolent Boulder, MM6 Demon/Ooze bindings and four DWI/map-state cases. The [isolated DWI state check](review/dwi-isolated-regression.log) passes. The broader suite failure/crash cause remains a separate investigation; [exact results](review/actors-regression.json) are retained.

[Native capture records](review/ingame/captures.json) cover eight successful runs on NVIDIA OpenGL 3.3/Wayland:
matching model/sprite cameras outdoors in New Sorpigal and indoors in Agar's Laboratory, unobstructed indoor gold/red
views, the 60% Chaos scale comparison, four forced LODs, live claw attacks, hit, backward death, held corpse and normal
loot-satchel transition. Exact launch records, logs and tours are retained under `review/ingame/runs/`.
Two initial indoor launches failed EGL surface creation before loading; both retries passed. The temporary indoor
spawn fixture is recorded in [indoor_fixture.json](review/ingame/indoor_fixture.json); the production map was unchanged.

Useful contact sheets: [LODs](review/m592_lod_comparison.jpg), [combat](review/m592_combat_contact.jpg),
[death](review/m592_death_contact.jpg) and [slow action review](review/m592_slow_review.jpg).
[Agent review](review/agent_visual_review.md) records corrections and measured limits. Android and Vulkan were not tested.

## Reproduction and cost

All service originals are retained in `meshy/`. Meshy used **30 of 100 credits**: body 5, rig 5, body retexture 10,
head retexture 10. All four jobs succeeded and were downloaded; there are no pending jobs. Rebuilding the selected
package requires no new paid jobs.

The selected attack master is `work/attack_revision_03.blend`. `scripts/author_attack_revision.py` reproducibly
adapts the recorded wolfman source from `work/attack_revision_02_before/work/rig_uv.blend`; its preserved baseline
is intentional. Run it only when revising this attack, before the package rebuild below.

Claim `mm8:m592` through `tools/creature_workspace.py` before any project mutation. With that claim's token in
`CREATURE_3D_TOKEN`, rebuild the selected corrected checkpoints using:

```sh
tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" \
  level_generation/creatures/mm8_m592_claude/scripts/refresh_package.py
```

This composes the retained maps, exports the packed animated master/GLB, prepares portable tier previews, generates
LODs, merges head materials and corrects shadow shells. Earlier anatomy/UV scripts are ordered historical steps;
do not reapply symmetry to an already mirrored mesh. After changing the package, rerun the affected export/motion,
viewer and game checks before replacing the installed asset with `tools/install_model.py <export.glb> --world mm8`.

The existing shared viewer check is:

```sh
python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m592_claude --port 8912 check
```

Release the workspace lease after completion. No staging or commit is part of this delivery.
