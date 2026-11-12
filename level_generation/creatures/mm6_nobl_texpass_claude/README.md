# Swordsman texture quality pass (MM6 `mm6_nobl`, Nobleman A/B/C), 2026-11-11

Texpass stream of the MM6–MM8 audit fixes, agent texpass-3 ([TEXPASS.md](../audit_mm678_20261111/fixes/TEXPASS.md)),
after the [recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) and the [handoff](../claude_shared/texpass_mm678/HANDOFF.md),
which listed the Swordsman as "not a retexture first: find out what is broken in its UVs". Only UVs, vertex splits and
images change; mesh, rig, the 11 clips, ramps, materials, variants, the Sword attachment and `actors.yml` stay.

Production projects: [mm6_nobl_codex](../mm6_nobl_codex/README.md) (model, rig, HD masters) and
[mm6_nobl_reduce_claude](../mm6_nobl_reduce_claude/README.md) (reduction, chest repair, front detail set, installed
2026-10-14). Starting point: the installed GLB, backed up as `work/before_texpass/mm6_nobl.glb` with
`actors_entries.yml`. Lease `mm6:nobl` (token in `work/LEASE.txt`). Kit: texpass-1's `tp_*.py` (from
[mm6_demon_texpass_claude](../mm6_demon_texpass_claude/README.md)), config `texpass.json`.

## What was broken in the UVs

The installed atlas is one 3104 x 2080 image of three sections (`mm6_nobl_reduce_claude/scripts/atlas_layout.py`):
head 1024 at (0, 0), body 1024 at (0, 1056), front detail 2048 at (1056, 0). Measured on the LOD0
(texel-space singular values per triangle, p50 texels per metre, minor / major axis):

| Section | Surface | Source 3104 x 2080 | As cooked (2048², the cook makes every side a power of two) |
|---|---|---|---|
| head | 5.5 % | 1,074 / 1,123 | 727 / 1,093 |
| body | 76.2 % | 206 / 439 | 139 / 419 |
| detail (collar, capelet, chest, tabard, belt) | 18.3 % | 775 / 1,839 | 694 / 1,240 |

- The body set (three quarters of the surface) has its texels stretched about 2:1 along v (stretch p90 7.9): its UVs
  were laid for the 3136 x 1024 strip and squeezed into a 1K section; the detail set is 2.3:1 (p90 8.5) in mixed
  directions. That is the reported stretch p90 8.25; the head set is fine (1.28).
- 2,330 islands, 15.9 % of the surface on fragments, 33.3 % atlas use, and the cook then squashes the 3104-wide image
  to 2048 (u x 0.66).
- Decision: a normal texture pass (one 2048 atlas from `uv_atlas.py`, 4K paints), keeping the front detail section
  denser as the user asked on 2026-10-14 ("an extra texture is welcome if it adds clarity").

## Route

1. `tp_dump.py`: LOD0 (6,603 triangles). Head set = the faces in the old head section (`head_uv_box`, 5.5 % of the
   surface: face, hair, collar band) x1.8; hands x1.3; the old front detail section (`uv_box_groups` Detail) x1.8, so
   the collar, capelet, chest and tabard keep their requested density. Both are new kit options.
2. `tp_uv.py` (fast packer sweep `fine=250 steps=0`): `uv_fine` (detail x1.5, 57.1 %), `uv_v2` (cut_closed etc.,
   57.0 %) and **`uv_d18` (detail x1.8, 55.5 %, 1.0 % fragments, stretch 1.14): the paid layout; never re-run it.**
   Per section (minor / major texels per metre against the cooked installed atlas): head 727 / 1,093 -> 896 / 954,
   body 139 / 419 -> 510 / 522, detail 694 / 1,240 -> 909 / 932. No section loses detail at runtime.
3. Retextures with the production masters (`references_hd/` from mm6_nobl_codex; head: its `references_head/` front,
   three-quarter, profile, back), meshy-7, 4K, our UVs: `body_retexture_v1` and `head_retexture_v1` (head faces only),
   **20 credits**. Both kept the layout (55.5 %, 431 islands).
4. `tp_resample.py` (approved colour, mask, metal/roughness and normal onto the layout), `tp_bake_ao.py` (reach 0.03),
   `tp_compose.py`, then `tp_apply.py` (LOD1 projected; LOD2/LOD3 512/256 maps refilled; shadow meshes matched).

Compose additions on this model (all in `texpass.json`, kit options for later models):
- `keep_approved_faces` (`work/keep_faces.npy`, 1,053 faces): the modelled silver cord, gold chain, pendant and gem
  were flat colour squares by design; they keep the approved colour exactly.
- `detail_limit` 1.3 (texpass-2's limiter) and `ornament_faces` (cord, chain, gold pieces) with radius 0.8-2.2 cm,
  plus `ornament_sets` clasp ends at 3.5-7.5 cm: no paint detail (colour and normal) there. The 4K paint drew a
  second, pink-white necklace on the tunic beside the modelled chain, a ring round the pendant and white spirals on
  the capelet beside the clasp ends; all three are gone.
- `head_sigma` 1.2: head islands take the approved colour down to 1.2 texels (default 4) and skip the limiter. With
  the default the face lost its brows, lids and eye detail (the approved head is as dense as the new one, so the
  paint had nothing to add there); now the face matches the approved one, and the hair gains strand detail.

## Results (`texture_quality.py`, LOD0 `Swordsman_A`)

| | Before | After |
|---|---|---|
| Image | 3104 x 2080 (cooked 2048², squashed) | 2048² |
| Atlas | 33.3 % | **55.5 %** |
| Equivalent px | 1,790 (before the cook's squash) | 1,526 |
| Density p10 / p50 / p90 | 466 / 509 / 2,050 | 855 / 881 / 1,578 |
| Spread | 4.4 | 1.84 (head and detail x1.8 by design) |
| Islands / fragments | 2,330 / 15.9 % | 431 / 1.0 % |
| Stretch p90 | 8.25 | 1.14 |

Tiers (`tp_tier_tone.py`, engine ramps, same surface points, approved -> pass): every class of A, B and C within
1.8 sRGB levels (A cloak 104.9/104.9/61.1 -> 105.8/105.7/62.0, A tunic 125.6/56.6/67.6 -> 124.1/55.8/66.7, untiered
rest 83.0/69.1/56.7 -> 82.9/68.8/56.5); luminance sd within 2. LOD1 against LOD0 colour error mean 3.0 -> 2.0,
p99 56.1 -> 40.5.

## Checks

- `tp_diff.py`: OK (only UVs, vertex splits 9,056 -> 10,348 at LOD0, images and texture references).
- Winding 0 inverted closed parts; flat shading 0.01.
- Viewer (`review/viewer/`, installed and pass per tier): `run_creature_review.py check` 0 console errors, 66 switches.
- `mm6_mm7_mm8_actor_models_build_every_binding`: PASS (647 descriptors on 185 models) after install.
- Floor audit Nobleman A/B/C: 0 problems. Motion audit re-run on the installed GLB (`audit_after/`; UV-only change,
  clips identical per `tp_diff`), so the arm and hand gate was not re-run.
- Sheets (review-viewer shots, identical cameras, installed vs pass, every tier):
  [review/texpass_head_sheet.png](review/texpass_head_sheet.png) (face front and 3/4, shoulders),
  [review/texpass_body_sheet.png](review/texpass_body_sheet.png) (3/4, back, tabard and belt).
- Seen: the capelet loses the old speckled mottling (wool weave instead), the tunic gets a fine weave, the boots and
  belt are crisper, the face is unchanged. Left as is: the orange collar keeps its streaky approved paint (head set,
  approved colour), a faint light patch of the approved paint beside each clasp end, and the smooth band of cloth
  right around the chain and clasp (no paint detail by design).

Installed 2026-11-11 with `tools/install_model.py export/mm6_nobl.glb --world mm6`. Rollback: install
`work/before_texpass/mm6_nobl.glb` (actors.yml unchanged; copy in `work/before_texpass/actors_entries.yml`).
