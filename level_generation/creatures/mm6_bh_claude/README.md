# MM6 Flying Eye (bh) — 3D model, 2026-10-08

Flying Eye / Terrible Eye / Maddening Eye, BBeholder A/B/C (484–486, palettes 669 / 670 / 671; the sprites reuse
one art set at frame scales 0.5 / 0.6 / 0.75). Built with the [quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md)
flyer route, [HD master references](../CLAUDE_HD_MASTER_REFERENCES.md) and
[creature textures](../CLAUDE_CREATURE_TEXTURES.md). Opt-in via `debug.actor_models=true`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_dev/worlds/mm6/models/mm6_bh.glb` (skins `bh_a/b/c`: one shared skin, three region ramps) |
| Triangles LOD0/1/2/3 | 7,341 / 3,670 / 1,315 / 430 since 2026-10-14 ([reduction, teeth and texture repair](../mm6_bh_reduce_claude/README.md)); previously 10,722 / 5,361 / 1,928 / 635 |
| Skeleton | Body (hover root), Head, Jaw, EyeBall, Tendrils |
| Clips | Standing 2.0 s, Walking 1.0 s, Running 0.75 s, Attack, Cast, Hit, Death, Dead, Fidget (all procedural) |
| Binding | `scale: 121` (silhouette area), B/C `scale_reference: BBeholder A`, `cast: Cast` (B/C cast spells), `death_effect: disintegration` |
| Meshy credits | **15 / 30** (Smart Topology 5 from the HD three-quarter master, retexture 10) |

It flies: no legs and no ground contact. The model's lowest point (the tendril tips) sits at the actor origin, like
the sprite's bottom edge; the engine handles the flying height.

## Pipeline (scripts/)

1. `references_hd/`: five Codex HD masters (1254² square; brief `CODEX_BRIEF.md`, inputs `native_views.png` and
   `native_palettes.png` from the original frames and one restored frame for material), tier-A colouring.
2. Meshy Smart Topology (15k) from `00_three_quarter.png`. `components.py`: main head, eyeball (piece 3; the iris is
   painted on its front), lower lip and teeth, upper gum and teeth, brow ring, crest.
3. `rig_bh.py`: Body → Head → Jaw / EyeBall / Tendrils. Pieces bind rigidly; on the main head the jaw blends in
   below the mouth line and the tendrils below 0.2 m.
4. `anim_bh.py`: procedural clips.
   - Hover bob and tilt with lagging tendrils, plus the forward lean when flying.
   - Attack: draw back, gaping jaw, lunge. Cast: rise, gape, eyeball tremble. Spellcasting tiers need a cast clip
     distinct from Attack (engine check).
   - Hit: twist and recoil. Death: shudder, drop and roll onto its side (the engine adds disintegration particles,
     like the native shatter frames).
5. `uv_export.py` (no extra head density: the whole creature is a head) → Meshy `retexture_v1` from the four HD views.
6. `compose_bh.py`: regions like the sprite package masks.
   - skin (red-brown back), face (grey face, horns, ivory teeth and fangs) and iris.
   - Pupil, highlight and mouth interior are kept as painted.
   - Then `bake_creature_ao.py` and `grade_basecolor.py`.
7. `tier_ramps.py`: per-region ramps from the native palette frames. The region coverage comes from
   `../mm6_bh/masks_2x` (R skin, G face, B iris), so all three palettes sample the same pixels.
8. `reduce_lod0.py` (superseded 2026-10-14: its Blender collapse slid UVs across seams and caused black shards; the installed model is reduced from `work/anim_v1_full.blend` in `../mm6_bh_reduce_claude/`): horns 40 %, back skin 50 %, face 80 %, separate
   pieces untouched. UVs kept; do not rerun `uv_export.py` afterwards.
   Before/after: `review/lod0_reduction_before_after.png`.
9. `build_runtime.sh --install`: `openyamm_specular 0`, metallic 0.

## Checks

- MM6 actor regression suite 12/12.
- Tiers in game: `review/tiers_3d_vs_sprites.png` (New Sorpigal test spot, flying at 260; top 3D, bottom sprites,
  C / B / A left to right). The 3D heads face the camera while the sprites turn, so the angles differ.
- Lesson: ivory teeth have a skin-like hue (below 40°), so classify them separately. Otherwise tier C's lime skin
  ramp turns the teeth green.

## Native shading transfer (2026-10-08)

User request after the Patrol Unit result. Applied with [native shading transfer](../NATIVE_SHADING_TRANSFER.md):
- `native_shading.json`: walk frames a and c in all five views, `height` coordinate, regions from the restored masks
  (R skin, G face/horns/teeth, B iris; on this creature they follow the parts).
- `scripts/compose_bh.py`: the skin takes the native brightness at 50 % (the back skin is very dark in the sprites and
  went black at 100 %), and the face 70 %. Horns (face texels out to the sides) and ivory teeth keep their own
  painting: the face profile darkened the horns, while the sprite's horns are lighter than the face.
- `scripts/tier_ramps.py`: skin and face ramps by palette transfer through the same native pixels (gain 1.35,
  saturation ×1.15); the iris keeps the quantile method. Result: richer back skin per tier, banded horns lighter than
  the face, a slightly darker face. A modest step; the old texture was already close.
- Comparison: `review/native_shading/before_after_native.png`. Pre-transfer files: `textures_pre_native/`.
