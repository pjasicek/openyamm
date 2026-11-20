# MM6 Ghost (`gst`, BGhost A/B/C) reduction (2026-10-14)

User: "check the tris reduction playbook and do Ghost gst". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md))
on the installed `assets_source/worlds/mm6/models/mm6_gst.glb` (17,143 tris, one primitive, unlit, three variants,
eight skin influences), started with `../reduce_installed.sh gst Body "MM6 Ghost"` and `REA_INFLUENCES=8`.
Weld 20,657 -> 1,860 open edges; limits scaled to the 2.23 m height (p99 6.68 mm, max 33.39 mm).

## Ghost-specific changes
- **Eight influences.** `REA_INFLUENCES=8` (new, default 4) in the shared template's `export_cand.py` and
  `reduce_ladder.py` (`mm6_wdm_reduce_claude/scripts/`): the cloth uses eight influences, as installed.
- **Protection by the region mask.** `REA_PROTECT_HEAD=1` protected 7,584 faces: B_Head weights cover the whole hood,
  and the head texture set (skull + hood, one connected piece) is 8,423 faces. The rest was cut 90 % and failed
  (p99 37 mm). `work/bone_faces.npy` is the skull and eyes instead (head-set faces on the green/blue region mask,
  3,751 faces). `scripts/decimate_tex.py` takes it as `REA_PROTECT_FACES`. With `REA_PROTECT_RATIO`, the protected
  part is decimated on its own to that ratio instead of being kept (cut edge preserved on both sides).
- `scripts/run_ladder.sh <label> <ratios>` reruns decimate/ladder/compare on the dumped mesh;
  `scripts/build_pick.sh <tag> [label]` builds one step (LODs, variants, viewer GLBs, close renders).
  `close_views.py`: `REA_FACING=-Y` (the ghost faces -Y), `REA_CLIP`, root as the foot (no legs).
  `probe_max.py` locates the worst ladder errors.

## Ladder

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 17,143 | | | | |
| uniform | 70 % | 11,999 | 2.7 / 30.4 | 0.998 | 0.999 | auto-pick |
| uniform | 55 % | 9,427 | 4.2 / 40.3 | 0.996 | 0.996 | max only; skull jaw and eyes degrade |
| uniform | 45 % | 7,713 | 5.3 / 39.9 | 0.993 | 0.993 | max only; angular eyes |
| uniform | 40 % | 6,857 | 6.0 / 39.9 | 0.993 | 0.991 | max only; hood artefacts |
| skull kept | 55 % | 9,427 | 6.8 / 39.9 | 0.989 | 0.988 | skull exact, hood/chest holes |
| **skull 60 %** | **55 %** | **9,425** | 5.1 / 39.9 | 0.993 | 0.993 | **pick** |
| skull 60 % | 45 % | 7,711 | 7.4 / 29.7 | 0.989 | 0.987 | p99; lower alternative |

The max error sits in the collapsed shroud heap on the floor (Death/Dead; folded cloth layers, `probe_max.py`) and
is already 30 mm at 70 %. `review/close/sheet_dead.png` shows the heap unchanged.

## First pick (superseded by the head retexture below)
`export/mm6_gst.glb` (= `mm6_gst_skull60r55.glb`): LODs 9,425 / 4,705 / 1,678 / 544 (installed 17,143 / 8,571 /
3,075 / 1,008), variants carried to all 7 LOD/shadow primitives, `KHR_materials_unlit`, eight influences.
Alternative `export/mm6_gst_skull60r45.glb`: 7,711 / 3,846 / 1,367 / 441.
Close renders: `review/close/sheet2_head.png` (rows installed, uniform 55 %, skull kept, skull 60 % 55 %,
skull 60 % 45 %), `sheet2_whole.png`, `sheet_dead.png`. Viewer `review/viewer/`: installed / pick / alternative per
variant, eight-influence skinning as in the Ghost project viewer; `check_viewer.mjs` 72 loads, no errors.

## Head retexture (2026-10-14)

User: "OK, the head might benefit from retexture though ... I want the eyes clear" (screenshot of the pick: faceted
skull texture, ragged eye glow). The installed glow is a texture mask (two position ellipses clipped by depth) on the
coarse socket wall, so its outline followed triangles even before the reduction.
- `scripts/head_uv.py`: fresh UVs for the 5,193 head-set faces, skull (2,254) and hood unwrapped apart, density
  averaged, skull islands x2, convex pack, overlapping folded-cloth faces re-projected until none overlap. Skull
  9.6 texels/cm (installed 4.2), hood 4.8 (3.8); `scripts/head_uv_check.py`, `texturing/head_uv_layout.png`.
- Meshy `head_retexture_r55` (`requests/`, the Ghost's accepted head_retexture_v2 request and head references):
  10 credits, UV parity exact. Lease `mm6:gst-reduce` (budget 10) is still held for the install.
- `scripts/head_chain.sh` (47 s): `bake_head_shade.py` (native shade rebaked on the new mesh) -> `add_eyes.py` (a
  20-segment front dome per socket against the back wall, rigid on B_Head, UVs in an empty square: +200 tris) ->
  `compose_head.py` (skull: Meshy colour x shade, luminance matched to the installed skull; hood and the tan brim
  piece: installed colour at the same 3D point and cloth side; bone mask carried over from the installed mask; eye
  mask only on the domes) -> build -> `head_atlas.py` (head half of the four atlases; body half pixel-identical) ->
  `eye_sockets.py` (eye sockets moved to y -0.050, in front of the domes, so the engine's eye embers stay visible).

`export/mm6_gst.glb` (= `mm6_gst_eyesr55.glb`): **9,625 tris** (LODs 9,625 / 4,807 / 1,714 / 556), materials, tier
ramps, clips and sockets otherwise unchanged. Close renders `review/close/sheet5_{face,head,tiers}.png`,
`sheet4_eyes.png` (rows installed, earlier pick, final). Viewer: installed / final / earlier pick, 72 loads pass.
Known: a few small dark wedges on the hood's outer side (decimation, already in the earlier pick).

## Installed (2026-10-14)

User: "good accept". Previous source backed up to `work/mm6_gst_source_pre_reduce.glb` (rollback: install that
file), `tools/install_model.py export/mm6_gst.glb --world mm6`; `mm6_ghost_actor_model_tiers_and_hover_clips` passes
(`work/regression_ghost.log`). Ledger row added; lease released.

Original install plan: back up the installed source to `work/mm6_gst_source_pre_reduce.glb`, then
`tools/install_model.py export/mm6_gst.glb --world mm6`, the Ghost actor regression, and the ledger row.

## Floor fix — 2026-10-21

`--lift-joints Death Dead --ground-death Death Dead`: the shroud strips bend at most 33 degrees. Before, in world units at tier A: corpse at -15.1; dying sinks to -15.2.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_gst.glb`), written to `export/mm6_gst_floor.glb` and installed as `mm6_gst.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.
