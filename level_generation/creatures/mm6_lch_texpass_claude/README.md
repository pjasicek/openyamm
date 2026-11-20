# MM6 BLich texture quality pass (`mm6_lch`, BLich A/B/C) — 2026-11-11

Stream texpass-1 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/TEXPASS.md), recipe
[TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md) and
[texpass_mm678/HANDOFF.md](../claude_shared/texpass_mm678/HANDOFF.md). Only UVs, images and texture references
changed. Lease `mm6:lch` (token in `work/LEASE.txt`). Production: [mm6_lch_codex](../mm6_lch_codex/README.md)
(Codex batch, round-2 rebake reduction), gait h03, lod_repair_claude. Kit: [mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md)
(`tp_*.py`, `texpass.json`).

## Texture quality pass (2026-11-11)

**Cause.** A 2080x1024 body | head atlas (two 1K Meshy sets rebaked after the reduction): 15.3 % of the atlas
(equivalent 813 px), 823 islands, 14.3 % fragments, stretch p90 2.27, spread 2.84.

**Route.**
1. `tp_dump.py` with the approved head set (old atlas u > 0.5: skull, crown, neck; 15 % of the surface) as head x1.8,
   hands and fingers x1.3. `tp_uv.py`: `uv_fine` (fast packer) 59.5 % but 7.1 % fragments; **`uv_v2`**
   (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`) 58.5 %, 3.4 % fragments:
   **the paid layout, never re-run it**.
2. Retextures with the production masters (`references_hd/` body, `references_head/` head turnaround), meshy-7, 4K,
   our UVs: `body_retexture_v1` and `head_retexture_v1` (head faces only), **20 credits**. Both kept the layout.
3. `tp_resample.py` carries colour, region mask, metal/roughness **and now the approved normal map** onto the layout:
   the old shaded normal is rebuilt in its old fs_model.sc frame and stored in the new triangle's frame (as
   `transfer_textures.py` does for far LODs). The Lich's normal map is a relief bake from the 16k mesh (p90 tilt 0.65,
   against 0.17 in the Meshy paint); `tp_compose.py` keeps it (rule: approved p90 tilt above 0.3, or `keep_normal`)
   and adds the paint's fine detail (above 4 texels) x0.5. Shaded normals against the installed model at the same
   surface points (`tp_normal_check.py`): p50 0.5°, p90 2.9°, p99 6.1°.
4. Compose: head paint crossfaded in over the head set; gentle grade; tone match per class (region 0 = bracers,
   tiered; the rest untiered); `tp_apply.py`: LOD1 projected, LOD2/LOD3 maps refilled.

## Results (`texture_quality.py`, LOD0)

| | Before | After |
|---|---|---|
| Atlas | 15.3 % of 2080x1024 | **58.5 %** of 2048² |
| Equivalent square | 813 px | 1,567 px |
| Density p10 / p50 / p90 | 333 / 534 / 945 | 1,453 / 1,511 / 2,685 (head x1.8) |
| Islands / fragments | 823 / 14.3 % | 460 / 3.4 % |
| Stretch p90 | 2.27 | 1.19 |
| Spread | 2.84 | 1.85 (head x1.8 by design) |

Tiers (`tp_tier_tone.py`): untiered surface 107.3/81.8/57.1 -> 107.5/82.1/57.5; bracers A/B/C within 2 levels
(C 138.0/38.6/38.4 -> 136.3/37.1/36.8). LOD1 against LOD0 colour error mean 5.8 -> 7.3, p99 39.5 -> 64.0 (the sharper
4K skull and crown detail at LOD1's coarser geometry; LOD1 draws from about 8 m).

## Checks

- `tp_diff.py` OK; winding 0; flat 0.00; viewer check 0 console errors (54 switches); floor audit BLich A/B/C ok;
  motion audit re-run (`audit_after/`, UV-only change).
- `mm6_mm7_mm8_actor_models_build_every_binding`: the first run right after the install failed 3 bindings (cook still
  settling, likely a concurrent install from another session), the immediate re-run PASS (647 descriptors, 0 failed).
- Sheets: [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (skull front and 3/4: teeth, sockets and the
  crown's tooling now read; the red eyes unchanged), [review/texpass_body_sheet.png](review/texpass_body_sheet.png).

Installed 2026-11-11. Rollback: `work/before_texpass/mm6_lch.glb` (actors.yml unchanged, copy in
`work/before_texpass/actors_entries.yml`).
