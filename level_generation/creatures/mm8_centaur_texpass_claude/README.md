# Centaur texture quality pass (MM8 `mm8_centaur`), 2026-11-11

Texpass stream of the MM6–MM8 audit fixes, agent texpass-3 ([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)),
after the [recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md).
Only UVs, vertex splits and images change; mesh, rig, clips (with the q4 gait clips), ramps, materials, variants, the
bow and `actors.yml` stay.

Production projects: [mm8_m532_claude](../mm8_m532_claude/README.md) (model, masters) and
[mm8_centaur_reduce_claude](../mm8_centaur_reduce_claude/README.md) (installed reduction). Starting point: the
installed GLB, backed up as `work/before_texpass/mm8_centaur.glb` with `actors_entries.yml`. Lease `mm8:centaur`.
Kit: the `tp_*.py` scripts from [mm8_m588_texpass_claude](../mm8_m588_texpass_claude/README.md), config `texpass.json`.

## Cause

A 2208 x 1024 atlas: body set 1K (horse body, torso, harness; 145 texels per metre, 803 islands, 33.9 % of the
surface on fragments, stretch p90 2.20), a 160-px strip of flat colour bars (bow string, arrow: 108 faces) and the head
set 1K (619 texels per metre).

## Route

1. `tp_dump.py`: head set = old atlas u > 0.536, x2.0 (keeps its density); hands and fingers x1.3; the strip's faces
   keep the approved colour and normal (`work/strip_faces.npy`).
2. `tp_uv.py` **`uv_h20`** (`cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250 steps=0`):
   53.7 %, 6.9 % fragments (almost all the tail's separate hair strands), stretch 1.18; face 619 -> 643, body 145 -> 323
   texels per metre. **The paid layout; never re-run it.**
3. One retexture with the production masters (`references_hd/` 01-04 from mm8_m532_claude), meshy-7, 4K, our UVs:
   `body_retexture_v1`, **10 credits**. No head paint (`head_sigma` 1.2 keeps the approved face).
4. `tp_resample.py`, `tp_bake_ao.py` (0.03), `tp_compose.py` with sigma 2.5 and detail 0.55 (arguments 7 and 8; with
   the defaults 4 / 0.9 the chest skin turned coarse and pebbled and the harness studs went soft), limiter 1.3,
   `tp_apply.py` (LOD1 projected, its shrunk shadow copy takes LOD1's UVs; LOD2/LOD3 refilled).

## Results (`texture_quality.py`, LOD0 `Centaur_A`)

| | Before | After |
|---|---|---|
| Image | 2208 x 1024 | 2048² |
| Atlas | 46.4 % | **53.7 %** |
| Equivalent px | 1,504 | 1,501 |
| Density p10 / p50 / p90 | 326 / 515 / 1,188 | 1,039 / 1,082 / 1,181 |
| Spread | 3.65 | 1.14 |
| Islands / fragments | 803 / 33.9 % | 321 / 6.9 % |
| Stretch p90 | 2.20 | 1.18 |

Tiers (`tp_tier_tone.py`): skin, hide and the rest within 0.2 sRGB levels; the harness rim (region 0, 1.5 % of the
surface) 3-6 levels lighter (A 57.9/83.4/61.2 -> 61.1/87.8/63.2, B 88.2/74.9/118.0 -> 93.9/78.8/124.5); left, too small
to see in the sheets. LOD1 against LOD0 colour error mean 3.8 -> 2.1, p99 41.4 -> 20.3.

## Checks

- `tp_diff.py` OK; winding 0; flat 0.01; viewer `check` 0 console errors (66 switches).
- `mm6_mm7_mm8_actor_models_build_every_binding` PASS (20 s after the install); floor audit Centaur A/B/C 0 problems;
  motion audit re-run (`audit_after/`, clips identical).
- Sheets: [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (face front and 3/4, chest),
  [review/texpass_body_sheet.png](review/texpass_body_sheet.png). Face, beard and hair match the installed ones;
  hide, mane and leather straps are crisper; the harness's green halo on the skin is the approved paint's.

Installed 2026-11-11 (MM8). Rollback: install `work/before_texpass/mm8_centaur.glb`.
