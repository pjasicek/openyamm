# MM8 Smuggler — human form

> **Installed model reduced (2026-10-19):** the installed model is now the reduction from [`../mm8_m444_reduce_claude/`](../mm8_m444_reduce_claude/README.md) (LOD0 10,074 -> 7,050; facial hair recoloured to the beard; Cast retimed). This project's exports and master remain the unreduced production; the rollback source is in `../mm8_m444_reduce_claude/work/`.

Installed human Animalist, Shapeshifter and Lycanthrope (actors 34–36, native family m444;
palettes 445/446/447). Produced with the shared Claude humanoid playbook. Agent visual/technical review is
complete; user artistic acceptance is separate. Meshy spend: **30 / 100 credits**, all jobs downloaded.

[Interactive review](http://127.0.0.1:8991/level_generation/creatures/mm8_m444_claude/review/viewer/)
· [Outdoor game capture](review/runtime/outdoor_models/01-tiers.png)
· [Indoor game capture](review/runtime/indoor_models/01-tiers.png)
· [Native outdoor comparison](review/runtime/outdoor_sprites/01-tiers.png)
· [Native indoor comparison](review/runtime/cove_sprites/01-tiers.png)
· [Matching indoor models](review/runtime/cove_models/01-tiers.png)

> **Sword rebuilt (2026-10-19, user: "his sword looks ultra plain/cheap like just a slab"):**
> `scripts/make_sword_v2.py work/mm8_m444_sword_v1.glb export/mm8_m444_sword.glb` replaces the 144-triangle slab in the
> same frame (grip on the origin, radius 12 mm where the hand closes, edge along x, point at 0.68 m): bevelled blade
> with a fuller, curved brass guard with ball ends above the fitted hand (no body vertex inside it), wrapped leather
> grip, brass ferrule and pommel; LODs 658 / 278 / 106 / 50; 512x128 maps (MR contract unchanged, empty region mask).
> Accepted by the user and installed (2026-10-19: "OK this is good"); winding 0, Smuggler regression passes. Rollback: install `work/mm8_m444_sword_v1.glb` with
> `--name mm8_m444_sword.glb`. The body's surface detail pass is in `../mm8_m444_reduce_claude/README.md`.

## Delivered files

- `export/mm8_m444.blend`: packed editable master, fitted 57-bone rig, body, sword and nine actions.
- `export/mm8_m444.glb`: shared body with three palette ramps and four colour/shadow LODs.
- `export/mm8_m444_sword.glb`: rigid right-hand sword with four LODs.
- Authoritative installed sources: `assets_source/worlds/mm8/models/mm8_m444{,_sword}.glb`.
  `tools/install_model.py` also cooked their runtime copies and textures into `assets_dev`.
- Bindings: `assets_dev/worlds/mm8/models/actors.yml`, descriptors `Wererat Human Form Male A/B/C`.
- `creature_3d_progress.json`: job receipts, native/HD provenance, corrections, final hashes and check records.

Body triangles by LOD: **10074 / 5056 / 1817 / 584**. Sword: **144 / 50 / 14 / 6**.
The face and hands retain their useful geometry; small boot fittings became texture detail.
At most eight influences; maximum normalized weight-sum error 1.8e-7. Body UVs have no zero-area faces.
One sword LOD1 face collapses to a constant-colour swatch in UV space; this is flat-colour metal with no
normal detail. Original Meshy body/head textures remain under `meshy/`, final 1K maps under `textures/`.
The runtime merges body/head into one material per LOD with a shared 2080×1024 atlas. Viewer tier GLBs bake
ramps solely for three.js preview; installed tiers share their base colour, normals, material map and mask.

## Identity, motion and material choices

The original BMPs define the bald head, pointed brown beard, grey tunic, coloured collar/cuffs/trousers,
left-shoulder-to-right-hip bandolier, laced boots, right-thigh sheath and broad straight sword. Hidden details
are interpretations from the generated HD references. `references/sources.json` records 160 verified originals;
`references_hd/generation_runs.json` retains generation provenance and selected/superseded images.

| Clip | Seconds | Source / use |
| --- | ---: | --- |
| Standing | 3.000 | Mixamo Standard Idle, fitted native ready arms |
| Walking | 1.000 | Mixamo Walk, fitted sword carry |
| Running | 0.733 | Mixamo Standard Run, source ankle paths and fitted carry |
| Attack | 2.033 | Mixamo Sword And Shield Slash, upright support, impact 1.283 s |
| Cast | 2.000 | ArmedCastLAttack1, ready lead, left-palm release 1.1167 s |
| Hit | 0.500 | UnarmedGetHitF1, planted upright flinch |
| Death | 3.633 | Mixamo Standing React Death Backward, hand clearance and ground correction |
| Dead | 1.000 | Held final Death pose |
| Fidget | 0.867 | Quiet authored ready-stance adjustment |

These are adapted professional clips, not native frame reconstruction. Native attack/cast timing and
statistics remain authoritative. Both native attack slots use Attack; spell actions use Cast. The engine
fits marked impact times to the native 1.25 s attack. Death finishes before the held endpoint and ordinary
runtime loot-bag presentation. Loop endpoints repeat exactly. Head look uses B_Neck/B_Head; palm sockets
follow the hand bones. Scale 102.9442014 derives from 179 native standing units / 1.738806 m model height.
All native tier scales are equal. Walk/run strides 1.773 / 1.981 m come from planted-foot velocity.

`compose_textures.py` writes skin/albedo correction, restrained cloth weave, native palette ramps,
roughness and per-class specular in ORM R (the current humanoid contract), with metallic zero.
It also writes standard material-class maps: skin 1, hair 2, eyes 6, mouth 7, cloth/leather 8, metal 9.
The prepare step converts Meshy's normal-map green channel to glTF convention. No extra AO pass was needed
on the already shaded Meshy base colours. Body and head UV transfer was verified by face/corner correspondence.

## Verification and limits

- Ordinary `openyamm` build passed. The focused Smuggler regression passed all three tiers, shared asset,
  native height, separate sword, LODs, nine clips, unchanged simulation state and Poison Spray palm origin.
- Final MM8 actor suite: **7 passed, 1 failed**. The failure is the separate Dark Elf warrior's body/sword binding;
  it is recorded in `review/mm8_regression_final.log` and was not changed by this creature task.
- Final exported rig reimported in isolation: every clip sampled at 48 Hz; maximum joint-position difference
  below 0.003 mm. `work/export_audit.json` records all results.
- Half-frame deformation audit: worst arm p99 1.71×, hand-edge maximum 2.23×. Isolated short tunic edges reach
  5.94× in the death fold; the playbook's arm p99 criterion is met. Wrist swing is at most 59.01° after the run repair.
- Half-frame body/arm/whole-length sword probes found no sword penetration. Tiny arm contacts: Attack 0.2 mm,
  Death 1.7 mm. Grounded soles are within the playbook's ±2 cm; the run retains its deliberate flight phase.
  Source-cast rapid motion was compared numerically with its library original, not mistaken for a rig flip.
- Fitted grip reviewed from palm, back, axis and side. Thumb is 0.7 mm off the handle; some middle-finger surface
  gaps reach about 5 mm. This is a visually reviewed grip, not a claimed pass of the separate batch's 3 mm limit.
- Viewer: all 27 tier/clip combinations load. Eighteen actual playback runs at 1× / 0.25× were exercised and their
  captured sequences reviewed; Running was repeated after its local wrist repair. Head, both hands, front/back,
  attack, cast and death detail captures are retained under `review/`.
- Native desktop OpenGL / NVIDIA / Wayland captures cover all tiers outdoors, Agar's Laboratory, combat, death,
  and Smuggler's Cove. Original sprites failed to appear when dynamically spawned into Agar, including after a
  save/reload. The required indoor sprite/model comparison therefore uses the same camera in native Smuggler's
  Cove, whose existing actors preload the native frame groups. Agar model captures are still retained.
- No Android performance benchmark or full campaign test. Renderer/engine fixes are outside this asset task.

## Rebuild / review

Claim this creature with `tools/creature_workspace.py` and use the returned token on all project writes.
The final animation/UV master is `work/rig_v6.blend`; intermediate stages remain for reproducibility.
Scripts were adapted from the current bar1/natm/gob2 playbook examples.

For a material/export rebuild, run `compose_textures.py` under the project guard, then:

1. `tools/run_creature_blender.sh --token TOKEN level_generation/creatures/mm8_m444_claude/scripts/export_runtime.py`
2. Guarded `tools/prepare_actor_glb.py export/mm8_m444_lod0.glb export/mm8_m444_runtime_lod0.glb` (project paths).
3. `export_lods.py` through the Blender wrapper, then guarded `scripts/finish_exports.py` and `scripts/viewer_manifest.py`.
4. `audit_export.py`, `audit_motion.py`, `g6_smuggler.py` through Blender; guarded `scripts/audit_assets.py`.
5. Install both final GLBs with guarded `tools/install_model.py ... --world mm8`, then rerun the focused regression.

Motion reconstruction order is `retarget_motion.py` → `fit_motion.py` → `weight_motion.py` → `finish_motion.py`.
The texture handoff/reduction is `prepare_textures.py` → `transfer_texture_uvs.py`. `fix_clearance.py` preserves
verified UVs when refreshing actions; apply `polish_run_wrist.py` after that refresh and before final export.
Do not submit replacement Meshy jobs or overwrite the final UV master merely to make a local animation edit.

The review viewer uses existing local vendor libraries. Serve the repository root (currently port 8991) and run
`node level_generation/creatures/claude_shared/check_viewer.mjs URL 60`.
Native capture tours and run logs are under `review/runtime/`; failed Agar sprite experiments are diagnostic,
not accepted comparisons. No files were staged or committed.
