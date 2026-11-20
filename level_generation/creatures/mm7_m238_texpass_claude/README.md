# Genie texture quality pass (MM7 `mm7_m238`), 2026-11-11

This is part of the MM6–MM8 audit fixes, texpass stream, done by texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md),
using the Troll's route for a body | head atlas.

Only the body's UVs, vertex splits and images changed. These are unchanged:
- the lamp mesh and its 512 set;
- the mesh, rig and clips;
- materials, ramps, variants and `actors.yml`.

No clip changed, so the arm and hand gate does not apply.

- Projects: [mm7_m238_claude](../mm7_m238_claude/README.md) and
  [mm7_m238_reduce_claude](../mm7_m238_reduce_claude/README.md).
- Starting point: the installed GLB, backed up as `work/before_texpass/mm7_m238.glb`.
- Lease: `mm7:m238`.
- **Meshy: 20 credits.** Two 4K retextures: the body with the full-body HD masters, and the head only with the
  production head masters.

## Route

The generic toolkit in `scripts/`. Settings in `texpass.json`:
- `head_uv_split 0.5`, head ×1.8, hands ×1.3;
- paid layout **`work/uv_cut_s.npz`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0`);
- LOD1 projected, LOD2/3 maps transferred again.

**The fresh paint changed the creature.** With the default compose (sigma 4, detail 0.9):
- the smooth blue skin turned grainy, and on the shoulders and arms scaly;
- the gold-green irises came out paler and smaller.

So the installed paint is composed close to the approved one, with new toolkit options:

| Option | Setting | Effect |
|---|---|---|
| `compose.py textures/tp 1.5 0.35` | body sigma 1.5, detail 0.35 | approved colour to a fine scale; little of the paint's pattern |
| `head_sigma 0`, `head_detail 0.35` | head islands | approved colour unblurred, so the diadem, brows and lips keep crisp edges (sigma 1.5 gave the gold diadem a yellow halo) |
| `keep_approved_near` | two eyeballs, by bind-pose position (radius 2.5 cm, 426 triangles) | the approved eye paint as it was |
| `normal_carry.py textures/tp 1.5 0.3` | approved normal map moved per chart | approved relief plus 0.3 of the 4K normal's fine band |

The gain is therefore mostly the layout: no stretched charts, no shards. The installed right shoulder had a dark
rectangular shard, which is now gone. The new paint adds a finer band but no new pattern.

## Results (`texture_quality.py`, `M238_A`)

| | Before (2080×1024) | After (2048²) |
|---|---|---|
| Atlas | 40.6 % | **55.7 %** |
| Equivalent px | 1,325 | 1,528 |
| Density p10 / p50 / p90 | 425 / 584 / 2,037 | 1,363 / 1,434 / 2,433 (body ×2.5) |
| Spread | 4.79 | 1.78 |
| Islands / fragments | 478 / 11.9 % | 172 / 0.1 % |
| Stretch p90 | 2.02 | 1.19 |

The lamp set (`Lamp_A`, 63.3 %) is unchanged.

**Tone** (sRGB, approved → pass):
- tier region: (17.1, 125.6, 52.9) → (18.2, 125.9, 53.2);
- skin and the rest: (111.9, 158.6, 191.5) → (111.9, 158.6, 191.4), luminance sd 62.6 → 62.1.

**LOD colour error** (mean / p99, before → after):
- LOD1: 6.9 / 83.5 → 2.6 / 36.0;
- LOD2: 6.3 / 43.4 → 6.8 / 35.0;
- LOD3: 14.1 / 75.7 → 12.8 / 61.4.

**Face and eyes** were checked front and three-quarter in tiers A and C
([review/cmp_eyes.png](review/cmp_eyes.png), [review/cmp_face.png](review/cmp_face.png)):
- eyes, brows, lips, diadem and earrings match the installed look;
- a faint scale pattern is left on the shoulders.

## Checks

- `glb_diff`: OK.
- Winding: 0. Flat shading: 0.00.
- Viewer check: 6 models × 7 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor (`Genie*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_m238.png](review/texpass_sheet_m238.png), every tier, installed against pass. Its
cameras use the `auto_shots.facing` override, because the facing of an upright figure is not found from its head.

Installed 2026-11-11 (MM7). To roll back, install `work/before_texpass/mm7_m238.glb`.
