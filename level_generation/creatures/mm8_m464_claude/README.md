# MM8 m464 — Vampire female peasant

> **Installed model reduced (2026-10-19):** the installed model is now the reduction from [`../mm8_m464_reduce_claude/`](../mm8_m464_reduce_claude/README.md) (LOD0 11,719 -> 8,433). This project's exports and master remain the unreduced production; the rollback source is in `../mm8_m464_reduce_claude/work/`.

Completed and installed on 2026-10-18 using the shared Claude humanoid workflow. Technical and agent visual
review passed. The user accepted the corrected v2-arms adaptation on 2026-10-18; the source F3 was already accepted.

[Interactive review](http://127.0.0.1:8765/level_generation/creatures/mm8_m464_claude/review/viewer/)
uses the shared creature viewer. Select A/B/C and any of the seven clips.
[Front](review/shots/front.png), [head](review/shots/head.png),
[outdoor comparison](review/ingame/outdoor_comparison.jpg),
[indoor comparison](review/ingame/indoor_comparison.jpg),
[normal-speed motion](review/motion_1x.jpg), [half-speed motion](review/motion_0.5x.jpg).

## Sleeve correction — current revision v2-arms

The user-reported arm deformation is fixed and installed. The sleeves were refitted to the accepted F3 arms;
the elbow weights now preserve the anatomical hinge. Maximum sleeve-center error fell from 42.92 to 2.01 mm.
[Right-arm close-up](review/shots/arms_right.png), [left arm](review/shots/arms_left.png),
[correction and validation](review/arm_fix/README.md). All seven motions, UVs and textures are preserved.

Current checks: 5,210 shared gates, 21 tier/clip switches, 14 playback runs and the actor regression pass.
The two fresh native runs contain 23 captures, including forced LOD2. Earlier sprite comparisons and the six
initial runs remain historical evidence; the current native captures are under `review/arm_fix/ingame/`.

## Selected delivery

- Editable, packed master: [export/mm8_m464.blend](export/mm8_m464.blend).
- Portable GLB: [export/mm8_m464.glb](export/mm8_m464.glb).
- Installed source: `assets_source/worlds/mm8/models/mm8_m464.glb`.
- Cooked desktop model: `assets_dev/worlds/mm8/models/mm8_m464.glb` and four referenced `.oytex` files.
- Bindings: `assets_dev/worlds/mm8/models/actors.yml`; exact family entries in [integration/actors.yml](integration/actors.yml).
- [Delivery manifest](export/manifest.json) records selected hashes, variants, clips, textures and components.

The 57-bone model has seven actions and four colour/shadow LODs: 11,719 / 5,859 / 2,929 / 1,463 triangles.
The body and head share a padded 2080×1024 atlas and one material per draw. Normals use glTF +Y;
the material red channel carries the engine specular mask, not ambient occlusion. Hair is opaque geometry.
There are no weapons, equipment attachments, Attack clip or required effects. An unused empty source-rig
`Socket_Knife_Tip` node remains, with no weapon mesh or runtime binding.

| Native descriptor / ID | Variant / palette | Clothing | Hair |
|---|---|---|---|
| Vampire Female Peasant A / 49 | m464_a / 465 | Green | Auburn |
| Vampire Female Peasant B / 50 | m464_b / 466 | Purple | Blonde |
| Vampire Female Peasant C / 51 | m464_c / 467 | Crimson | Black |

Scale 127.16803763770572 maps the 1.651358 m upright body to the native 210-unit standing height.
All variants use that same reference. Yaw offset is −π/2. Head look uses B_Neck/B_Head, upper-body root
B_Spine, with gaze and both palm sockets.

## Source and adaptation

The explicit source is `../mm6_mfp_codex/export/mm6_mfp.blend`; its unchanged hash is recorded in
[references/source.json](references/source.json). Inspection found a sari rather than trousers.
The accepted face, neck, hands, proportions, core rig and professional motion sources were retained.
Sari, braid, jewelry and dagger were removed. A new fitted jacket, trousers, boots and short hair follow the
native m464 silhouette and palette references. Hidden details are an interpretation from the HD views.

Five body and four head HD references, prompts and provenance are retained under `references_hd/` and
`references_head/`. Meshy generated the garment surface and supplied body/head textures and UVs;
its static return did not replace the animated rig. Verified face/corner correspondence transferred the UVs.
Two tiny changed scalp triangles use a recorded hair-only projection (maximum about 2.2 mm); see
`work/uv_transfer.json`. Jacket weights were smoothed, boots aligned to the inherited gait, the hip hand
moved to clear all LODs, and the unarmed Hit recoil eased and reduced for the fitted jacket.

| Clip | Seconds | Runtime use |
|---|---:|---|
| Standing | 2.0 | Relaxed, native-inspired hand-on-hip idle |
| Walking | 1.2 | Walking and both native peasant attack slots |
| Running | 0.8 | Run override |
| Hit | 0.75 | Native hit duration, unarmed recoil |
| Fidget | 2.0 | Subtle inherited head/body motion with the hip posture |
| Death | 2.1444445 | Accepted source forward fall, beginning matched to Standing |
| Dead | 1.0 | Held final Death pose |

Native attack slots intentionally resolve to walking, as the original descriptors do. No gameplay timing or
simulation state was changed. Fidget keeps the accepted professional idle motion rather than reconstructing
the native chin-touch gesture. The final Fidget endpoint has a small inherited matrix deviation (0.001609);
Hit and Death start from Standing, and Dead matches the Death endpoint within floating-point precision.

## Verification

- Shared sampled gates: **PASS, 5,210 passed, 120 informational, 64 not applicable, zero failed/unverified**.
  Every clip and colour/shadow LOD was sampled at 48 Hz for bones and 24–48 Hz for mesh checks.
  [Full report](review/shared_gates/gates.md). LOD3 ratio limit is explicitly 0.13 for the successive 50%
  reductions; other shared thresholds remain unchanged. No separate cloth/underlying torso collision
  volume is claimed: the garment is the visible body surface. No props are applicable.
- Shared viewer: **21/21** tier/clip switches without console errors; 14 normal/half-speed playback runs.
- Ordinary `openyamm` build passed. Focused MM8 actor regression passed: **1 passed, 0 failed**.
- Initial revision: six native NVIDIA OpenGL 3.3 runs produced 36 captures: indoor/outdoor models, native sprites,
  lower LOD and direct clip poses through death. Selected captures and motion sequences were visually
  inspected. Logs and run records are preserved beside captures.
- [Delivery validation](review/delivery_validation.json) verifies export/source hashes, all clips, endpoints,
  LOD counts, installed bindings/textures, unchanged F3 source and unchanged production test scenes.

Native comparisons use the same cameras, but live AI can put actors in different positions/poses.
Height is calibrated from the upright native frame and checked by the actor regression.
The isolated visual fixture adds MM8 sprite preloads to copies of MM6 oute3 and 6d19 scenes; production maps
are unchanged. No Android, Vulkan or performance benchmark was run. The user accepted v2-arms on 2026-10-18.

## Reproduction and cost

Claim this project as identity `mm8:m464` before edits and use the returned workspace token.
The selected intermediate input is `work/repaired_master.blend`; the packed exported blend is the editable
delivery. `scripts/rebuild.py` rebuilds motion from the retained checkpoints, repairs weights, exports,
applies runtime preparation/variants/head merge and runs the shared gates through the guarded Blender launcher:

```sh
tools/run_creature_blender.sh --token <token> level_generation/creatures/mm8_m464_claude/scripts/rebuild.py
python3 tools/install_model.py level_generation/creatures/mm8_m464_claude/export/mm8_m464.glb --world mm8
OPENYAMM_REGRESSION_FILTER=mm8_vampire_female_peasant_actor_models_keep_native_roles ./build/game/openyamm --world mm8 --headless-run-regression-suite actors
```

The installer cooks textures, so installed runtime bytes differ intentionally from the portable/source GLB.
After changes, refresh viewer tiers with the existing project scripts and repeat affected checks before replacing
this manifest. Historical `adapt_body.py` / `join_sleeves.py` manual prototypes were rejected and are not inputs.

Meshy consumed **25 of 100 authorized credits**: garment geometry 5, body retexture 10, head retexture 10.
All three jobs succeeded; no paid task is pending. Durable request/download/hash receipts are in
`creature_3d_progress.json` and `meshy/`. Rebuilding uses those local results and requires no new paid jobs.
