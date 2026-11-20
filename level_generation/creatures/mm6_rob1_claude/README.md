# MM6 Patrol Unit (rob1) — 3D model, 2026-10-08

BRobot A/B/C (622 Patrol Unit, 623 Enforcer Unit, 624 Terminator Unit; palettes 810 steel / 811 blue / 812 copper):
a hovering sentry sphere with a scanning eye belt and a sensor head on a post. Rigid and non-humanoid, so it follows
the [quadruped / non-humanoid playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md), with the
[HD master references](../CLAUDE_HD_MASTER_REFERENCES.md) and [creature textures](../CLAUDE_CREATURE_TEXTURES.md).
Opt-in via `debug.actor_models=true`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_dev/worlds/mm6/models/mm6_rob1.glb` (skins `rob1_a/b/c`: one shared skin, 4 region ramps) |
| Triangles LOD0/1/2/3 | 4,076 / 2,037 / 729 / 238 (14,291 after cleanup; reduced on user review: "too much for something this simple"; the rebuilt sensor head is 114) |
| Skeleton | Root (hover), Body, CapTop, CapBottom, RingTop, RingBottom, Eye, Sensor; sockets `Socket_Eye`, `Socket_Lens` |
| Clips | Standing 1.5 s, Walking 0.75 s, Attack, Hit, Death 1.0 s, Dead, Fidget 1.5 s (all procedural) |
| Binding | `scale: 111` (sphere width = native 134 px × 0.7), B/C `scale_reference: BRobot A`, `run: Walking`, `stride_length: 0.9`, `upper_body_root: Body`, `death_effect: explosion`, eye glow `eye_left: Socket_Eye` |
| Meshy credits | **15 / 30** (Smart Topology 5 from the HD three-quarter master, retexture 10) |

## Pipeline (scripts/)

1. `references_hd/`: five Codex HD masters (brief `CODEX_BRIEF.md`; inputs `native_views.png`, `native_palettes.png`,
   `native_attack.png` from the original frames, plus one restored frame for material). Tier-A colouring.
2. Meshy Smart Topology (15k target) from `00_three_quarter.png`. `components.py`: core sphere with belt, two rings
   with inner lips, front and **back** eye lenses, sensor pieces, two hidden discs.
3. `clean_rob1.py`: Meshy made the sphere front/back symmetric (eye and both V notches also at the back; the native
   back is plain). Remapping the back notch vertices left ragged edges, so the rings are **rebuilt** as surfaces of
   revolution from the section measured on Meshy's rings at the sides (`ring_section.py`: elevation 6.5–30°,
   0.400–0.423 m from the centre) with V notches at the front only. The back eye and hidden discs are deleted.
   Face attribute `part`: 0 core, 1/2 rings, 3 eye, 4 sensor.
4. `rig_rob1.py`: every part bound 100 % to one bone. The core is split between CapTop/CapBottom at the equator but
   the halves never separate (faces across the equator would stretch into a capsule).
5. `anim_rob1.py`: per frame, parameters become one world transform per bone. Hover 0.25 m above the actor origin
   (native frames float about a quarter of the figure height; the tallest pose, 1.35 m × 111 = 150 units, stays under
   the 168-unit collision height). The eye slides along the belt (scan); the sensor head scale is 1.0 (it was
   1.4 for the Meshy sensor before `sensor_rebuild.py`). Death: shudder with the eye spinning, then the rings and sensor
   head fly off, the core tumbles and everything shrinks to 1 mm inside the explosion (native: fireball, no corpse).
   `minz.py` reports clip bounds; `clip_sheet.py` → `review/clips_v1.png`.
6. `uv_export.py`: Smart UV, eye and sensor at 2× texel density; Meshy `retexture_v1` from the four HD views.
7. `reduce_lod0.py` (once, on `work/anim_v1.blend`; full mesh in `work/anim_v1_full.blend`): region-limited collapse
   decimation keeping UVs and weights: rings 30 %, core 40 %, sensor 30 %, eye 35 %.
   `review/lod0_reduction_before_after.png`. Do not rerun `uv_export.py` afterwards.
7b. `sensor_rebuild.py` (once, after the reduction; backup `work/anim_v1_pre_sensor.blend`): Meshy's sensor head was
   soft (open nozzle tube, blobby box and vents) and looked sloppy in game (test_img/2155-2156). It is replaced by
   clean boxes at the native proportions: bent square post, rear block with three vent ridges, tapered nozzle, closed
   lens (parts 41-45), UVs in the free strip at the top of the atlas, bound to Sensor. The clips' sensor scale went
   back to 1.0. Then rerun `anim_rob1.py` and `dump_uv3d.py`.
8. `compose_rob1.py`: base colour (the eye glow Meshy painted on the belt is replaced by the belt colour, since the
   lens moves), 1K normal and metal/roughness, material classes (metal 9, eye 6) and four regions: caps (etched steel
   + sensor box), rings (bronze rings + sensor post), belt, eye. After the review: flat metal colours on the rebuilt
   sensor, dark ring lips and inner faces (Meshy painted them light, the ramps made white rim lines), a smoothed belt
   and 3D seam blending along UV island edges. Then `bake_creature_ao.py` and `grade_basecolor.py --local 0.4
   --contrast 1.08 --saturation 1.1`.
8b. Third review (test_img/2158, Control Center: flat, washed out, no outlines; `review/look/compare_native_2158.png`):
   `claude_shared/native_shading.py` (config `native_shading.json`) measures the native brightness by elevation on the sphere from the notch-free views (camera
   about 8° above; regions by the 3D geometry, since the restored mask channels do not follow the parts). Compose
   gives core and ring texels that brightness (rings ×0.62: their shine is in highlights) times Meshy's detail
   (etching kept on the caps), then dark lips and a bright line on each ring's rounded edge. Glossy, not metallic
   (a metallic try turned chalky indoors). AO is baked without the eye lens (`bake_ao_no_eye.py`), which removed the
   dark patch around the eye. The eye lens is its own material and glows per tier (`eye_emissive.py`).
   Comparison: `review/look/look_v5.png` (left 3D now, top right sprites, bottom right the reviewed state).
9. `tier_ramps.py`: ramps per region from the native palette sprites, sampled through the restored region masks
   (`mm6_rob1/masks_2x`: R caps, G shell, B belt, A eye; death frames skipped because A holds the explosion there).
   Caps, rings and belt: colour by brightness through the same native pixels in each palette (tier-A luminance nearest
   each stop, median in the tier's palette), gain 1.1 / 1.0 / 1.1 and saturation ×1.25. Eye: mask A channel
   quantiles. Also writes the AO into the metal/roughness red channel.
10. `build_runtime.sh --install`: region variants for the body and eye materials, then `eye_emissive.py`. Specular on,
   metallic 0.

## Engine addition

`death_effect: explosion` (`game/fx/WorldFxSystem.cpp`): when the actor starts dying, the Fireball impact burst is
spawned at the actor's centre; the model then plays Death and holds Dead. It reuses the existing projectile impact
recipe; nothing else changed.

## Checks

- MM6 actor regression suite 12/12.
- In game (New Sorpigal, three tiers): `review/ingame/compare_v3.png` (top two rows 3D at scale 111, bottom sprites; C, B, A left to right; before the texture fixes). After the fixes:
  `review/ingame/close_v4_0.png`, `close_v4_1.png`, `close_v5_0.png` (close range, all tiers).
- Not yet seen in game: the death explosion. There is no console kill command and the party could not destroy a
  400 HP robot in a capture; the Death clip itself is checked in `review/clips_v1.png`.

## Not reproducible with textures alone

- **Sprite outline:** in every native view the outermost silhouette pixel is about 25 % darker than its neighbours
  (prerendered against black) and the next two pixels are a little brighter. A 3D model has neither; it would need a
  rim/silhouette term in the model shader or an outline shell (renderer work, all models).
- **Chrome glints:** the rings' white highlights at the left and right sides depend on the view; an elevation profile
  cannot carry them.

## Floor fix — 2026-10-21

`--hover -0.237515 Death Dead`: the hovering sphere now meets the floor at its lowest. Before, in world units at tier A: living lowest at +26.4 (suggested hover -0.237515).
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_rob1.glb`), written to `export/mm6_rob1_floor.glb` and installed as `mm6_rob1.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.
