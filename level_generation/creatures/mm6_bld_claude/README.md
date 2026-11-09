# MM6 bloodsucker (bld) — 3D model, 2026-10-07

Winged lamprey-serpent from Goblinwatch, built with the [quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md) flyer
route (bat lessons applied). Bloodsucker A/B/C (487 Blood Sucker, 488 Brain Sucker, 489 Soul Sucker), opt-in via
`debug.actor_models=true`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_dev/worlds/mm6/models/mm6_bld.glb` (skins `bld_a/b/c`, double-sided wings) |
| Triangles LOD0/1/2/3 | 10,774 / 5,386 / 1,934 / 600 |
| Skeleton | 30 bones: Spine1–2, Neck1–2, Head, Mouth (scaled for the maw), Tail1–6; per side UpperArm/ForeArm/Hand, Finger1–2 a/b, FrontLeg, HindLeg |
| Clips | Fly (0.75 s loop: standing/walking/run), Attack, Hit, Death, Dead, Fidget (glide) — all procedural |
| Binding | `scale: 160`, `stride_length: 0.66`, `cast: Attack`, `upper_body_root: Spine2`, `sockets: {}` |
| Meshy credits | **15 / 30** (Smart Topology 5 from `bldflya1`, retexture 10 with four restored views) |

## Pipeline (scripts/)

1. `rig_bld.py` — joints read from gridded orthographic views (head −Y, tail +Y); wing joints as front-view (x, z)
   with y sampled from the membrane; automatic weights. The mesh has 62 separate pieces (dorsal spikes, mouth
   tentacles, wing thumbs): each is rebound rigidly to the main-body vertex where it attaches, otherwise mixed heat
   weights let them drift off the wings. `stress_bld.py` renders extreme poses.
2. `anim_bld.py` — run it on `work/anim_v1.blend` (it carries the UVs the texture was painted on; the rig file has
   none). Fly flaps from the rest V down past level; Attack rears back and lunges with the Mouth bone scaled ×4.6
   (see below); Death rears up vertically, twists and falls; the corpse is grounded on the body, wings
   twisted flat about the upper arm and fitted to the floor, neck and tail fitted down.
3. `uv_export.py` → Meshy retexture → `add_maw.py` (once: a funnel disc on a `Maw` bone in the mouth opening; all
   UVs shrink to 90% toward the top-left, freeing the bottom-right square for the maw art) → `dump_uv3d.py` →
   `bake_ao.py` → `compose_bld.py`: texels classed by hue (teal body, tan membrane, red maw/belly, ivory bone);
   body/membrane/maw recoloured to the native medians measured with the restored region masks (palettes 162
   purple/brown, 672 tan/teal, 673 red), bone kept, AO multiplied in, and the native attack-frame maw (`bldattb0`
   per palette) painted into the disc square. Then `../claude_shared/grade_basecolor.py --ao textures/bld_ao_2k.png
   --ao-strength 0 textures/bld_{a,b,c}_basecolor.png` writes the `_graded` textures the export uses.
4. `build_runtime.sh --install`.

The attack scales only the maw disc (×4.9 at the lunge peak) and flares the tube a little; scaling the mouth tip
itself balloons the head into a faceted bulb. At rest the disc sits at 55% inside the opening.

## Size and hover

Scale from the native fly frames (frame scale 0.7): front silhouette area gives 158, side body length 162; 160 used.
No hover lift (see the bat). The flapping model peaks at ~0.61 m × 160 ≈ 97 units, inside the 109-unit collision
height.

## Results

[3D vs sprites in game](review/bld_3d_vs_sprites.png) (left 3D, right sprites; Goblinwatch `6d01.blv`, party at
(15350, 8700, −768) facing east, 487/488/489 spawned by console; the map's own bloodsuckers join in). Attack close
range: [3D](review/bld_attack_maw_3d.png), [sprites](review/bld_attack_maw_sprites.png).

## HD retexture and shared-skin tiers (2026-10-08)

Per [HD master references](../CLAUDE_HD_MASTER_REFERENCES.md) and [creature textures](../CLAUDE_CREATURE_TEXTURES.md):
- `references_hd/`: five Codex masters (1536×1024, brief `CODEX_BRIEF.md`, inputs `native_views.png` from the
  original native frames plus one restored frame for material). They replace the enlarged sprite frames.
- Meshy `retexture_v2` (10 credits; 25/30 used) on the existing mesh from `01_front`, `03_left`, `02_back` and `04_right`.
  The rig and clips are unchanged.
- UVs unchanged (the maw disc keeps its reserved corner); `texturing/bld_neutral_upload.glb` reused.
- Tiers: `compose_bld.py` writes `textures/bld_region_weights.npz`, and `build_runtime.sh` fits ramps
  (`../claude_shared/fit_tier_regions.py`) and builds one shared skin with `../claude_shared/region_variants.py`.
  `textures_v1/` keeps the previous baked textures.
- Review: `review/hd_retexture_3d_vs_sprites_20261008.png` (New Sorpigal, left 3D, right sprites).
