# Beholder texture quality pass (MM7 `mm7_m166`), 2026-11-11

Part of the MM6–MM8 audit fixes, texpass stream, done by texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). Recipe:
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md), with the
[handoff](../claude_shared/texpass_mm678/HANDOFF.md).

Only UVs, vertex splits and images changed. Mesh, rig, clips, materials, ramps, variants and `actors.yml` are
unchanged.

- Projects: [mm7_m166_claude](../mm7_m166_claude/README.md) and
  [mm7_m166_reduce_claude](../mm7_m166_reduce_claude/README.md). The far LODs come from `lod_repair_claude`.
- Starting point: the installed GLB, backed up as `work/before_texpass/mm7_m166.glb`.
- Lease: `mm7:m166`.
- **Meshy: 10 credits.** One 4K retexture, using the production HD masters.

## Route

This is the generic toolkit in `scripts/`, configured by `texpass.json`:
- Head and EyeSocket at ×1.5. The central eye is painted on the head.
- Regions: tips, flesh and shafts.
- Detail limiter: 1.3.
- The paid layout is **`work/uv_fine.npz`**.
- LOD1 is projected; the LOD2/3 maps are transferred again.

## Results (`texture_quality.py`, `Beholder_A`)

| | Before | After |
|---|---|---|
| Atlas | 21.2 % | **57.5 %** |
| Equivalent px | 944 | 1,553 |
| Density p10 / p50 / p90 | 725 / 931 / 1,049 | 1,197 / 1,234 / 1,847 (×1.33 median; head ×1.5) |
| Islands / fragments | 999 / 21.9 % | 193 / 0.3 % |
| Stretch p90 | 2.01 | 1.15 |

**Tone** (sRGB, approved → pass):

| Region | Approved | Pass |
|---|---|---|
| tips | (18.9, 159.2, 16.2) | (19.1, 159.1, 16.3) |
| flesh | (164.6, 68.0, 33.4) | (164.7, 68.2, 33.5) |
| shafts | (140.4, 94.9, 66.0) | (140.3, 95.1, 66.0) |
| rest | (165.2, 100.9, 57.3) | (165.0, 100.8, 57.5) |

**LOD colour error** (mean / p99, before → after):

| LOD | Before | After |
|---|---|---|
| LOD1 | 6.3 / 47.7 | 4.6 / 43.2 |
| LOD2 | 5.5 / 29.2 | 9.3 / 38.4 |
| LOD3 | 10.4 / 47.0 | 11.9 / 45.8 |

The LOD2/3 rise comes from the sharper LOD0 detail. Their 512/256 maps are unchanged in size.

**Eye.** [review/cmp_eye_a.png](review/cmp_eye_a.png) shows the eye before and after. The central eye keeps its
pupil position and green iris, and its radial iris detail is crisper. The teeth, tongue and drool are sharper.

## Checks

- `glb_diff`: OK.
- Winding: 0. Flat shading: 0.00.
- Viewer check: 6 models × 5 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor (`Beholder*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_m166.png](review/texpass_sheet_m166.png). It shows the head front, head 3/4, top,
side and whole body for every tier, installed against pass.

Installed 2026-11-11 (MM7). To roll back, install `work/before_texpass/mm7_m166.glb`.
