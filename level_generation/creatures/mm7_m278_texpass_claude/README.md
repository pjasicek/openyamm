# Manticore texture quality pass (MM7 `mm7_m278`), 2026-11-11

This pass is part of the MM6–MM8 audit fixes, texpass stream, phase B. It was done by texpass-2
([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)). It follows the
[recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).

Only UVs, vertex splits and images changed. These are unchanged:
- mesh, rig and clips (including q3 Walk2);
- materials, ramps and variants;
- `actors.yml`.

**Projects:** [mm7_m278_claude](../mm7_m278_claude/README.md) and
[mm7_m278_reduce_claude](../mm7_m278_reduce_claude/README.md).

**Starting point:** the installed GLB, backed up as `work/before_texpass/mm7_m278.glb`.

**Lease:** `mm7:m278`.

**Meshy: 10 credits** for one 4K retexture with the production HD masters. There are no head masters, so there is
no head-only paint.

## Route

The generic toolkit in `scripts/`:
- The head is at ×1.8.
- The two tier regions are the mane and the body.
- The paid layout is **`work/uv_cut_s.npz`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0`).
- LOD1 is projected; the LOD2/3 maps are transferred again.

**Face.** With the default compose, the 4K paint drew a fine reptilian scale pattern over the human-like face, where
the installed face has smooth, wrinkled skin. Head islands therefore keep the approved colour unblurred
(`head_sigma 0`) and take 0.4 of the paint's fine band (`head_detail 0.4`). The body uses the default compose.
- The face reads like the installed one, a little crisper.
- The orange slit eyes and the teeth are kept.

Crops: [review/cmp_face.png](review/cmp_face.png), front and 3/4, tiers A and C.

The auto cameras use a new `head_offset`, because the Head bone sits at the back of the skull.

## Results (`texture_quality.py`, `M278_A`)

| | Before | After |
|---|---|---|
| Atlas | 26.5 % | **57.8 %** |
| Equivalent px | 1,053 | 1,557 |
| Density p10 / p50 / p90 | 379 / 426 / 966 | 672 / 694 / 1,237 (×1.6) |
| Islands / fragments | 1,138 / 26.8 % | 419 / 6.5 % (173 Meshy pieces; just over the 5 % target) |
| Stretch p90 | 1.48 | 1.09 |

**Tone:** the means of all regions hold within 0.1 sRGB levels.

**LOD1 colour error** (mean / p99): 3.8 / 34.6.

## Checks

- `glb_diff`: OK.
- Winding: 0.
- Flat shading: 0.00.
- Viewer check: 6 models × 9 clips, no console errors.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS.
- Floor (`Manticore*`): 3 bindings, 0 problems.

**Sheet:** [review/texpass_sheet_m278.png](review/texpass_sheet_m278.png).

Installed 2026-11-11 (MM7). To roll back, install `work/before_texpass/mm7_m278.glb`.
