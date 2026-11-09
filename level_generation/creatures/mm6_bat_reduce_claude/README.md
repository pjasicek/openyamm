# MM6 Bat (`bat`, BBat A/B/C) reduction, repairs, retexture (installed 2026-10-14)

User: "OK do bat first." (after the dragon; next in line: rat, spider, bloodsucker). No-retexture route
([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)), scripts copied from `mm6_cdr1_reduce_claude/` with
`REA_NODE=Bat`. One texture set (body, wing membranes, ears in one material), tiers by region ramps.

Weld 5,759 -> 153 open edges; limits scaled to the 0.90 m wingspan (p99 2.7 mm, max 13.5 mm).

| step | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| source | 8,729 | | | | |
| 70 % | 6,109 | 1.1 / 5.9 | 0.995 | 0.999 | pass |
| 55 % | 4,799 | 1.7 / 7.8 | 0.991 | 0.998 | pass |
| 45 % | 3,927 | 2.3 / 12.7 | 0.987 | 0.997 | pass |
| **40 %** | **3,491** | 2.5 / 12.7 | 0.984 | 0.997 | **auto-pick** |
| 35 % | 3,055 | 3.0 / 12.7 | 0.981 | 0.996 | fail (p99) |

No new open edges (153 as the source): the membranes stay whole. Build: export_cand -> swap_lod0 -> build_actor_lods
-> `mm6_bat_claude/scripts/shrink_shadow_lods.py` -> carry_variants: `export/mm6_bat.glb`, LODs 3,491 / 1,740 /
624 / 205 (installed 8,729 / 4,362 / 1,567 / 518). No burn death on the bat. `review/close/sheet.png` (whole views,
installed / 40 %; head close-ups, installed / 40 %). Viewer `review/viewer/` (installed / 40 % per tier, 30 loads
pass). The white flake by the left wing root is in the installed model too.

## Round 2: holes, fangs, claws, retexture (2026-10-14)

User: "fix the holes here ... fix the teeth ... and retexture", then "yeah the fangs fix aswell" (the foot claws).

- `scripts/fix_bat.py` (on the 40 % candidate): the 5-vertex hole by the left wing root and the one at the tail tip
  are fanned shut; the rectangular notch in the left membrane's trailing edge is filled (outline cycles directed by
  winding; a notch is a short boundary detour turning against the outline, so the wingtip fingers are left alone);
  the four 4-triangle fang slivers become clean 6-sided cones on Head (upper 8 mm hanging, lower 6 mm rising;
  the bat has no jaw bone). The claws keep their geometry: rebuilt cones floated on the small toe tips, so the claw
  faces (ivory in the installed texture) are labelled with a 0..1 tip fraction for the paint instead. 3,537
  triangles. Open edges afterwards: membrane outlines and the mouth only (`review/holes/fix_sheet.png`).
- `scripts/uv_upload.py`: fresh Smart UV Project (as the original), head islands 2.5x texel density, concave
  packing (48 % coverage). Meshy `requests/bat_texture_r1.json` (meshy-7, original UVs, PBR, 4k, the bat's four HD
  masters), 10 credits; UV parity exact.
- `scripts/compose.py`: AO grade; regions from Meshy's own colours (blue membrane, grey fur; the red and pink eyes,
  inner ears and mouth keep Meshy's colours and take no ramp); each region's luminance quantile-matched to the
  installed texture (membrane and body medians equal), so the accepted tier ramps are unchanged; fangs ivory; claws
  ivory from just above the toe. First attempt (user: "is this really retextured?"): the installed mask carried over
  by nearest face put grey body-ramp blotches along the wing bones, and the installed eyes/ears pasted back looked
  blocky; both replaced. Note: an RGBA PIL resize premultiplies by alpha, and the bat's mask has an empty alpha, so
  masks are resized per channel.
- `scripts/texture_chain.sh` (30 s): UV parity, raster, AO, compose, geometry export, swap into the installed GLB,
  maps swapped in, LODs 3,537 / 1,763 / 631 / 207, shadow LODs, variant mappings, viewer tiers (`rt`).
- Review: `review/close/sheet_tiers_rt.png` (installed / new per tier), `sheet_head_rt.png`, `sheet_feet_rt.png`.
  Viewer: installed vs new per tier, 30 loads pass. The hind feet keep their pink toe tips (only some were ivory).

## Installed (2026-10-14)

User: "ok this is good, accepted". Previous source backed up to `work/mm6_bat_source_pre_reduce.glb` (rollback:
install that file with `tools/install_model.py --world mm6`); `export/mm6_bat.glb` installed with
`tools/install_model.py`. No regression case covers the bat; a desktop run in the Abandoned Temple (`6d02.blv`,
party at (16000, -18300, 752), `debug.actor_models=true`, NVIDIA OpenGL 3.3) loaded and drew the new bats with no
model errors in the log. Dev assets only; `assets/worlds/mm6.zip` and Android not repacked.

## Floor fix — 2026-10-21

`--hover 0.175229 Death Dead`, then `--lift-joints Death Dead --lift-only 'Finger*'` (wing fingers bend at most 9 degrees as it falls). Before, in world units at tier A: living lowest at -27.2 (suggested hover 0.175229); dying sinks to -26.2.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_bat.glb`), written to `export/mm6_bat_floor.glb` and installed as `mm6_bat.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.
