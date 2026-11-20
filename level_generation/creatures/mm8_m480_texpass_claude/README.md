# Troll texture quality pass (MM8 `mm8_m480` Troll Peasant, MM7 `mm7_m461` Troll) — 2026-10-31

The user asked for this pass ("OK try the first three") after the MM6–MM8 texture-quality ranking: Bone Dragon,
Troll and Water Elemental. It follows the recipe [TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md),
applied as the [MM9 brief](../claude_shared/MM9_TEXTURE_PASS_BRIEF.md) applies it to an approved creature: sharper
textures only. Mesh, rig, weights, clips, sockets, region ramps and bindings are unchanged.

Related projects:
- [mm8_m480_claude](../mm8_m480_claude/README.md): production.
- [mm8_m480_reduce_claude](../mm8_m480_reduce_claude/README.md): the installed LOD0 and LOD1.
- [mm7_m461_claude](../mm7_m461_claude/README.md): the MM7 copy. It has the same geometry and images, with MM7 ramps
  and head-bob clips.
- [lod_repair_claude](../lod_repair_claude/README.md): the far LODs.

This project has its own lease (`mm8:m480-texpass`, token in `work/LEASE.txt`). That keeps the production projects
free for the gait rollout (packages h10 and h20), which will reinstall both GLBs with Sprint clips.

**Status: built and checked, not installed.** The merge waits for gait packages h10 (`mm7_m461`) and h20
(`mm8_m480`). See "Merge and install" below. **Meshy: 20 credits** (body and head retexture, 10 each, backup
account); budget 40.

## Cause

The installed body | head atlas was 2080×1024: a 1K body set beside a 1K head set. Both were Meshy 2K paints
downsampled to 1K. The body used Meshy's own layout, the head a Smart UV layout. Together they covered 18.9 % of the
atlas, or 0.40 M texels: the detail of a 634 px square. (`texture_quality.py` reports 905 px, because it measures the
equivalent square by the width alone.)

The atlas had 748 islands, with 9.4 % of the surface on fragments. The body had about 300 texels per creature size,
under the 512 px LOD2's 275 at its own scale. Stretch p90 was 1.91; feet and toes went up to 3.4.

## Route (`scripts/`)

1. **`dump_lod0.py`** reads the installed LOD0 into `work/lod0_before.npz`:
   - positions, triangles, weights;
   - the approved head-set faces, i.e. the right half of the atlas (4,568 of 7,598 triangles, 27.6 % of the surface:
     face, ears, scalp, crest locks, horns).
2. **`uv_texpass.py`** (Blender) runs `claude_shared/uv_atlas.py` on the welded LOD0:
   - head set ×1.8, hands ×1.3 (they hold the club in close view);
   - one 2048 atlas, 2 px margin.

   Two runs:
   - `uv_fine` (fast packer sweep, `fine=250 steps=0`): **56.4 %** of the atlas.
   - `uv_brute` (brute force): 54.4 %.

   **`work/uv_fine.npz` is the paid layout. Never re-run it.** xatlas packs differently per run, and the paint
   belongs to this exact layout.
3. **Retextures** (`requests/`, `meshy-7`, 4K, `enable_original_uv`):
   - Body: the whole mesh with the four HD body masters. Upload `texturing/uv_fine_body_upload.glb`, output
     `meshy/body_retexture_v2/`.
   - Head: the head-set faces only, with the four HD head masters. Upload `texturing/uv_fine_head_upload.glb`,
     output `meshy/head_retexture_v2/`.

   Both returns keep the layout (`texture_quality.py` reports the same 56.4 % / 238 islands on the body return).
4. **`resample_approved.py`** carries the installed (approved) colour, region mask and metal/roughness onto the new
   layout at the same surface points: triangle and barycentrics per texel, then the old UV. The result is
   `work/approved_fine_*`.
5. **`bake_ao.py`** bakes AO on the layout: `textures/m480_tp_ao_2k.png`, reach 0.035 like the approved build.
6. **`compose.py`** builds the maps; its outputs are `textures/m480_tp_*`:
   - colour and normal downsampled once from 4K to 2K;
   - the head paint blended into the body paint across the head-set boundary triangles;
   - the gentle grade;
   - tone match to the approved look, so the ramps and tiers hold. Per region (skin, wrap, crest, mottled back), a
     per-channel quantile curve, area-weighted. Then, island by island, the approved colour below 4 texels (scaled by
     the island's density) plus the paint's luminance detail above it ×0.9 (as the Basilisk's `match_tone.py`).
   - normal map from the paint (+y down converted to glTF +y up), xy ×0.3 like the approved build's `softnormal`.
     The cook's normal relief lifts it in game, as for every creature.
   - region mask and metal/roughness: the approved ones carried onto the layout.

   `material_classes.py` writes `textures/m480_tp_material_classes.png` from the approved per-set class maps.
7. **`apply_layout.py`** builds the runtime GLB from an installed GLB. It changes only the following and carries
   everything else over from its input:
   - LOD0 and its shadow copy get the new UVs, with vertices split at the new seams (7,860 → 9,181).
   - LOD1 and its shadow copy: each LOD1 triangle takes the LOD0 chart under its centre, and each corner takes the
     nearest point of that chart (4,569 → 5,584 vertices; no LOD1 triangle spans a seam).
   - The four LOD0 images are replaced.
   - LOD2 and LOD3 keep their geometry and UVs. Their maps are transferred again from the new LOD0 with
     `lod_repair_claude/scripts/transfer_textures.py`, at the installed 512 and 256 px.

   It refuses an input whose LOD0 differs from `work/lod0_before.npz`.
8. **Checks**:
   - `glb_diff.py`: nodes, skin, inverse binds, every clip sampler, materials, variants, ramps, LOD lists, and
     per-corner position, normal, joints and weights are unchanged; only UVs, vertex splits and images differ.
   - `lod1_check.py`: LOD1 colour against LOD0 at the same surface points.
   - `tier_tone.py`: tier colours with the ramps applied, approved against the pass.
   - `viewer_variants.py`, `viewer_manifest.py` (review viewer), `texpass_sheet.py` (sheets).

**Separate head set: not kept.** One 2048² atlas with the head ×1.8 already gives the face 2.7× the approved head
set's linear density (1,805 against 662 texels per creature size) and the body about 3×. Keeping a separate 1K head
set beside a 2K body set would cost more memory for less face detail. The face keeps its own paint from the head
masters: the head retexture runs on the same layout and is composed in. One image keeps one material per tier and the
bindings unchanged.

## Results (`texture_quality.py`, LOD0 base colour)

| | Before (2080×1024 body \| head) | After (2048²) |
|---|---|---|
| Atlas use | 18.9 % | **56.4 %** |
| Texels used / equivalent square | 0.40 M / 634 px | **2.36 M / 1,537 px** (×5.9 texels) |
| Density p10 / p50 / p90 | 289 / 402 / 702 | 960 / 1,013 / 1,813 |
| Median per bone: thigh, pelvis, forearm, foot | 310, 311, 287, 323 | 1,002, 1,002, 971, 1,001 |
| Median per bone: head, hands | 662, 942–1,036 | 1,805, 1,245 |
| Spread p90/p10 | 2.43 | 1.89 (the head is ×1.8 by design) |
| Islands / surface on fragments | 748 / 9.4 % | 238 / 1.9 % |
| Stretch p90 | 1.91 (toes 3.4) | 1.17 (feet 1.3) |
| Zero-area UV triangles | 0 | 0 |
| Meshy source | 2K, downsampled to 1K | 4K on the final layout, downsampled to 2K |

Map sizes: colour 2048² and normal 2048², replacing 2080×1024 for each (cooked 2048×1024). Mask and metal/roughness
are 1024², down from 2080×1024. The LOD2 and LOD3 sizes are unchanged.

**Tier colours as the engine shows them** (`tier_tone.py`: ramps applied, area-weighted means at the same surface
points):
- Every region and tier of both worlds keeps its approved mean within 1 sRGB level. The one exception is MM8 B's
  mottled back blue: 194.0 → 191.8.
- Luminance sd rises with the new fine detail:
  - skin ×1.18 (14.1 → 16.7);
  - wrap ×1.02;
  - crest ×1.07;
  - mottled back ×1.35–1.42 (its scales were blurred at 1K).

**LOD1 against LOD0** colour error (`lod1_check.py`): mean 1.8 → 1.5, p99 21.6 → 20.3. The new LOD1 UVs follow LOD0
at least as well as the installed ones.

**Far LODs:** the LOD2 and LOD3 colour means are unchanged (98.5/85.9/52.8 against 98.4/85.8/52.7).

## Checks (on builds from the installed, pre-gait GLBs)

- `glb_diff.py`: OK for both worlds.
- `check_winding.py`: 0 inverted closed parts for both.
- `flat_shading_check.py`: flat 0.00 for both.
- `detached_parts_audit.py` (MM8): identical before and after. The same three pre-existing shallow parts are
  reported (head pieces 60 and 64, pelvis piece 65, 3–7 mm), and nothing is detached.
- Viewer: `review/viewer/` (revision `texpass-20261031`), installed and pass for each tier of both worlds (12 models).

**Sheets** (review-viewer shots, identical cameras, every tier, installed against pass):
- [review/texpass_mm8_sheet.png](review/texpass_mm8_sheet.png)
- [review/texpass_mm7_sheet.png](review/texpass_mm7_sheet.png)

Each has these columns: head front, head 3/4, upper back, belly and club hand, whole body 3/4.

What they show:
- The face reads its brow wrinkles, eye sockets and lips.
- The belly and arms lose the soft blotches.
- The back scales are crisp.
- The crest, wrap colours and mottled-back hues match the installed tiers in both worlds.

**Installed 2026-11-01** (user: "clearly better") with `merge_install.sh --install` on the post-h10/h20 GLBs: only
UVs, vertex splits and images differ; winding 0; atlas 56.4 % in both worlds. The first MM8 install lost one cooked
texture (`e9c086….oytex`, the metal/roughness map; the MM7 copy was intact), most likely pruned by another agent's
concurrent full cook; reinstalling MM8 restored it. Then `mm8_troll_actor_models_keep_native_tiers_and_club`,
`mm8_troll_peasant_actor_models_keep_native_tiers_and_bone_club` and `mm6_mm7_mm8_actor_models_build_every_binding`
pass. Not done: an in-game look.

## Merge and install (after gait packages h10 and h20)

```sh
level_generation/creatures/mm8_m480_texpass_claude/scripts/merge_install.sh            # build and check
level_generation/creatures/mm8_m480_texpass_claude/scripts/merge_install.sh --install  # then install both
OPENYAMM_REGRESSION_FILTER=mm8_troll ./build/game/openyamm --world mm6 --headless-run-regression-suite actors
```

`merge_install.sh` does the following for each world:
- copies the then-installed GLB (with its Sprint clips) to `work/merge_src_<stem>.glb`;
- runs `apply_layout.py` with `work/uv_fine.npz` and `textures/m480_tp_*`. It fails if the gait pass changed LOD0
  geometry.
- runs `glb_diff.py` against that source, then winding, flat shading, `texture_quality.py` and `lod1_check.py`.
- with `--install`, runs `tools/install_model.py`.

No binding change is needed: same model paths, material names, variants and ramps. Club GLBs are untouched.

Rollback: install `work/before_texpass/mm8_m480.glb` and `mm7_m461.glb` (the pre-pass, pre-gait files; after the gait
install, use the `work/merge_src_*` copies).
