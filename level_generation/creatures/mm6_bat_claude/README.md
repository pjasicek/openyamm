# MM6 bat (bat) — 3D pilot, 2026-10-07

Flyer pilot of the [quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md) route: Meshy model → own wing rig →
procedural flap clips. BBat A/B/C (481 Bat, 482 Giant Bat, 483 Vampire Bat), opt-in via `debug.actor_models=true`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_dev/worlds/mm6/models/mm6_bat.glb` (skins `bat_a/b/c`, double-sided membrane) |
| Triangles LOD0/1/2/3 | 8,729 / 4,362 / 1,567 / 518 |
| Skeleton | Spine1–2, Neck1, Head; per side UpperArm/ForeArm, Finger1–3 a/b, Thigh/Shin, Ear |
| Clips | Fly (0.75 s loop, used for standing/walking/fidget), Attack, Hit, Death, Dead (all procedural) |
| Binding | `scale: 155`, `run: Fly`, `stride_length: 0.53`, `cast: Attack`, `sockets: {}` |
| Meshy credits | **15 / 30** (Smart Topology 5, retexture 10) |

## Pipeline (scripts/)

1. `references/` — restored spread front view (`batwae0`) for Smart Topology, plus three-quarter/side/back views.
2. `rig_bat.py` — wing joints given as top-view (x, y) with z sampled from the membrane so the bones lie in the
   sheet; Blender automatic weights. `stress.py` renders extreme poses.
3. `anim_bat.py` — Fly: shoulder raise 6 ± 38°, lagging elbow, fingers fold on the upstroke, body bobs against
   the wings. Attack lunges and dips, Hit jolts back, Death rolls and falls; the corpse lies on its belly
   (body pitched 35°, legs trailing) and each wing is fitted down segment by segment until it rests on the floor.
   Grounding the lowest vertex is not enough: drooped wings prop the body up like a tent.
4. `uv_export.py` → Meshy retexture → `compose_bat.py` (blue membrane recoloured to tier medians: A brown,
   B blue, C red; body and eyes kept).
5. `build_runtime.sh --install`.

## Size and hover (from the native frames, frame scale 0.7)

- No hover lift. Native fly frames float ~60 px above the sprite anchor, but billboards lean toward the camera, while
  an upright model does not. Flyers rise until their collision box (height 56/73/89 for A/B/C) meets the ceiling, so a
  lifted model (first try: +47 units) put its head and wings into low ceilings. The model now starts at the actor
  origin, and the flap is biased downward (shoulder 6 ± 38°), so the top is ~0.57 m × 155 ≈ 88 units, down from 141.
  A flapping 1 m wingspan cannot fit a 56-unit box, so wingtips can still touch a very low ceiling on the upstroke.
  A complete fix would be engine-side (fit the model under the sampled ceiling).
- Scale matched by silhouette area, not by wingspan: the Meshy body is heavier than the sprite's thin wings.
  Area match ≈ 145, wingspan match ≈ 198; 155 is used (199 looked ~1.4× too big in game).

## Results

[3D vs sprites in game](review/bat_3d_vs_sprites.png) (left 3D, right restored sprites; Abandoned Temple
`6d02.blv`, party at (16000, −18300, 752) facing east, spawns 481/482/483 by console). The temple's own bats join
the fight at random, so crowd sizes differ between runs. Corpses:
[bat_corpses_3d_vs_sprites.png](review/bat_corpses_3d_vs_sprites.png).

## HD retexture and shared-skin tiers (2026-10-08)

Per [HD master references](../CLAUDE_HD_MASTER_REFERENCES.md) and [creature textures](../CLAUDE_CREATURE_TEXTURES.md):
- `references_hd/`: five Codex masters (1536×1024, brief `CODEX_BRIEF.md`, inputs `native_views.png` from the
  original native frames plus one restored frame for material). They replace the enlarged sprite frames.
- Meshy `retexture_v2` (10 credits; 25/30 used) on the existing mesh from `01_front`, `03_left`, `02_back` and `04_right`.
  The rig and clips are unchanged.
- `uv_export.py` now gives head islands 2.5x scale before packing (`../claude_shared/uv_head_density.py`):
  about 2x linear texel density on the head. `work/anim_v1_pre_headuv.blend` keeps the previous UVs.
- Tiers: `compose_bat.py` writes `textures/bat_region_weights.npz`, and `build_runtime.sh` fits ramps
  (`../claude_shared/fit_tier_regions.py`) and builds one shared skin with `../claude_shared/region_variants.py`.
  `textures_v1/` keeps the previous baked textures.
- Review: `review/hd_retexture_3d_vs_sprites_20261008.png` (New Sorpigal, left 3D, right sprites).

## Native palette transfer (2026-10-09)

`scripts/native_tiers.py` replaces `claude_shared/fit_tier_regions.py` in `build_runtime.sh`: two regions on the
tier-A skin, `membrane` (ramps by `native_shading.transfer_ramps` from the native walk frames' amber pixels read in
666/667/668) and `body` (`compose_bat.py` writes `bat_body_weight.npz`; ramps by luminance rank from the native body
pixels, the same in every tier). No brightness bake (the bat banks). Pre-transfer files: `textures_pre_native/`.
