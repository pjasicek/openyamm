# MM8 Female Pirate Crossbowman — m416

Claude humanoid-playbook production, 2026-10-18. Regnan Crossbowman, Regnan Arbalester and Regnan Lieutenant share one fitted body, with separate crossbow, bolt, quiver and two animated string halves. Technical completion and user artistic acceptance are separate.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m416_claude/review/viewer/) · [Progress and Meshy receipts](creature_3d_progress.json) · [Runtime contract](review/runtime_contract.json)

![Finished creature](review/shots/final_ready.png)

## Deliverables

- [Packed editable Blender master](export/mm8_m416.blend), [portable assembled GLB](export/mm8_m416_portable.glb), [runtime body](export/mm8_m416.glb), [bindings](export/actor_binding.yml).
- Body triangles: **10,832 / 5,413 / 2,705 / 1,350**. Equipped totals: **14,414 / 7,167 / 3,570 / 1,766**. Runtime skin uses four normalized influences; the authoring master uses the same limit.
- Body/head originate as two 1K texture sets and merge into a 2080×1024 runtime atlas. Crossbow/quiver use 512px maps; strings use 64px maps. ORM red is the engine specular mask, green roughness, blue zero. Normal maps are converted to glTF +Y.
- Native `pal417–419.act` ramps affect the teal/purple/red vest and bandanna, preserving skin, hair, sash, trousers and leather. Shared geometry and variants are installed through `tools/install_model.py` under `assets_source/worlds/mm8/models/` and cooked `assets_dev/worlds/mm8/models/`.
- Bind only **Pirate Crossbowman (Female) A/B/C**, merged table IDs **13–15**. IDs 184–186 are a different m644 family and remain untouched.

## Motion and calibration

| Role | Local source/adaptation | Seconds |
|---|---|---:|
| Standing | Crossbow idle breathing, native raised right-hand carry | 3.333 |
| Walking | 2HandCrossbowWalk, fitted raised carry | 0.800 |
| Running | Mixamo Standard Run foot trajectories, fitted carry | 0.733 |
| Attack / Attack2 | Raise, two-hand aim, fire, lower and rearm | 1.700 |
| Hit | 2HandCrossbowGetHitF1 over fitted carry | 0.500 |
| Death | 2HandCrossbowDeath1 with planted lead and weapon clearance | 1.733 |
| Dead | Exact Death endpoint, including equipment scale | 1.000 hold |
| Fidget | CrossbowReload adapted to two-hand weapon inspection | 1.600 |

The physical ArrowF release remains the native **1.0 seconds** and uses `Socket_Bolt` through `bolt_tip`. Supporting-hand contact holds from 0.65–1.2 seconds, with measured maximum error 0.013 mm. The string releases over 1.0–1.033 seconds, then redraws; the held bolt is hidden from release until rearmed. This is an abbreviated rearm, not a separately animated manual loading sequence. No gameplay tables or attack timing were changed.

The rig uses fitted source frames, measured palms, connectivity-weighted fingers and four twist helpers. The left leather gauntlet and bare right hand retain their native sides. The right-hip quiver swings about its leather belt hanger; its loop was fitted separately to clear the hip. The carried crossbow is lower than the sprite's most elevated frame to keep the wrist usable, while retaining its upright silhouette.

Native visible body height is **195 pixels**, sprite scale 1.199996948. Model standing height is 1.845333934 m, giving binding scale **126.805994632**, yaw −π/2. The native 160-unit collision height is preserved. Measured walking/running strides are **1.636282682 / 3.842865467 m**. Head look uses Neck/Head, 40° yaw and 25° pitch.

## Review evidence

- [Equipment checks](review/equipment_checks.json): all seven moving clips checked at 60 Hz against closed body proxies. No prop penetration above 2 mm; grip surfaces are intentional contact. Strings meet the limb tips and moving nock; equipment remains above ground.
- [Export parity](review/export_parity.json): body surface differences below **0.18 mm** across all eight clips and dense firing samples; all six equipment/socket bone matrices compared. Four-weight truncation was moved into authoring so the editable master and delivered skin agree.
- [Authoring gate log](review/author_gates.log): arm deformation and hand/finger stretch checked on the final revision. The most stretched sampled arm region is the left shoulder during inspection (p99 about 2.45×); final visual review is retained alongside the numeric report. Hand edge maxima remain below the playbook's approximate 4.5× gate.
- [Continuous playback](review/playback/playback.json): every clip at normal and half speed, with WebM recordings and advancing-time captures. The source fall includes a quick initial turn; it is retained rather than described as a slow collapse.
- [Loop checks](review/loop_checks.json): the walking free-arm IK roll seam was closed; Standing/Walking/Running close within the recorded tolerance, and Dead matches the final Death pose exactly. [Revision comparison](review/walking_revision.json) proves all other animation samples are unchanged by that final repair.
- Final viewer check covers **24 tier/clip combinations**, with no failures or browser errors. [Face](review/shots/final_head.png), [aimed supporting hand](review/shots/final_hands.png), [front grip](review/shots/final_grip.png), [purple tier](review/shots/purple.png), [red tier](review/shots/red.png).
- Ordinary development build passed. [Pirate actor regression](review/ingame/actors_focused.log): **1 passed**, covering all tiers, eight roles, shared body geometry, five attachments, launch socket, bolt visibility and preserved simulation. [MM6 goblin baseline](review/ingame/actors_mm6.log): **1 passed**. [Broader MM8 run](review/ingame/actors_mm8.log): **34 passed, 1 unrelated Triton binding failure**; this run preceded the pirate test-name correction, so the pirate case is reported separately. The unrelated Triton work was not modified.
- Matching native comparisons: [outdoor model](review/ingame/outdoor_wide_3d/tiers.png) / [sprites](review/ingame/outdoor_wide_sprite/tiers.png), [indoor model](review/ingame/indoor_lineup_3d/tiers.png) / [sprites](review/ingame/indoor_lineup_sprite/tiers.png). The indoor preload fixture changes only a private asset copy; production scene hash is preserved. The wider outdoor camera keeps all tiers visible.
- [Native combat sequence](review/combat_sheet.jpg): aimed firing with the native ArrowF projectile, approach, hit, fall, held corpse and the normal summoned-remains transition. Captures ran on the desktop OpenGL 3.3 renderer, NVIDIA vendor 0x10de, Wayland. These are visual checks, not performance measurements. Full logs/run records are under `review/ingame/run_records/`.
- [Native sprite integrity](review/native_integrity.json) verifies all original source BMP hashes; palette hashes and comparison with HEAD are in [palette integrity](review/palette_integrity.json).

## Provenance and rebuild

**60 / 100 Meshy credits**: body Smart Topology 5, diagnostic rig 5, crossbow 15, quiver 15, body/head retextures 10 each. No paid animation jobs. Original outputs, task IDs, requests and input/download hashes remain in `meshy/` and the progress record. Five body HD views, four head views and equipment references were generated from the original native identity study. Native sprites were not uploaded to Meshy.

The reduced 10,832-triangle body and exact returned UVs are frozen in `work/textured_full_uv.blend`; `work/ready_final.blend` is the final equipped authoring checkpoint. Retexture UVs were transferred by exact face correspondence without replacing the fitted geometry. Head colour blends the detailed face with the body's clean neck/temple texture. No raw animation-library clips are installed.

Acquire a fresh `mm8:m416` workspace lease, then run:

```sh
python3 level_generation/creatures/mm8_m416_claude/scripts/rebuild.py --token YOUR_TOKEN
```

This rebuilds fitted equipment, final animation, prepared GLB, LODs, palette variants, attachment splits, merged body/head atlas, viewer tiers and numeric checks from the selected textured revision. Review continuous playback after motion changes. Reinstall all six runtime GLBs with `tools/install_model.py <file> --world mm8` under the workspace guard and rerun affected native checks. Release the lease afterward.

Android/Vulkan execution and hardware performance profiling are outside this creature-production check. User artistic approval is not recorded.
