# MM6 spider (spi1) — 3D model, 2026-10-08

Abandoned Temple spiders, BSpider A/B/C (634–636, palettes 822 brown / 823 dark blue / 824 dark red; the sprites
reuse one art set at frame scales 0.7 / 0.9 / 1.1). Built with the [quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md),
[HD master references](../CLAUDE_HD_MASTER_REFERENCES.md) and [creature textures](../CLAUDE_CREATURE_TEXTURES.md).
Opt-in via `debug.actor_models=true`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_dev/worlds/mm6/models/mm6_spi1.glb` (skins `spi1_a/b/c`: one shared skin, region ramps) |
| Triangles LOD0/1/2/3 | 9,564 / 4,781 / 1,721 / 572 (Smart Topology 15,804, reduced outside head and joints) |
| Skeleton | Thorax (root), Abdomen, Fang_L/R, per leg L1–L4 / R1–R4: Femur, Tibia, Tarsus (28 bones) |
| Clips | Standing 2.0 s, Walking 0.75 s, Running 0.5 s, Attack, Hit, Death, Dead, Fidget (all procedural) |
| Binding | `scale: 130` (silhouette area), B/C `scale_reference: BSpider A`, `stride_length: 0.26`, `upper_body_root: Thorax` |
| Meshy credits | **15 / 30** (Smart Topology 5 from the HD three-quarter master, retexture 10) |

## Pipeline (scripts/)

1. `references_hd/`: five Codex HD masters (brief `CODEX_BRIEF.md`; inputs `native_views.png` and
   `native_palettes.png` from the original frames, plus one restored frame for material). The masters use the
   tier-A brown and a neutral star pose with every leg separated.
2. Meshy Smart Topology (15k target) from `00_three_quarter.png`. `components.py` lists the pieces: the mesh comes
   as rigid parts (body, abdomen shell, chelicerae, head bumps, and per leg femur / tibia / tarsus).
3. `rig_spi1.py`: an exoskeleton rig. Each joint sits where two consecutive pieces meet (closest-vertex junction).
   The hip is the femur's junction with the body or a side bump. Every piece is bound 100 % to its bone; the body
   piece blends Thorax → Abdomen across the waist. No heat weights.
4. `anim_spi1.py`: procedural clips.
   - Feet are placed by two-bone IK (Femur + Tibia); the tarsus keeps its rest direction; the knee pole sits above
     and outside, so the knees stay high.
   - Gait: alternating tetrapod (L1 R2 L3 R4 / R1 L2 R3 L4).
   - Attack rears up with the front legs raised and fangs spread, then lunges.
   - Death rolls onto the back with the legs curling up; the corpse is grounded exactly.
   - `clip_sheet.py` → `review/clips_v1.png`.
5. `uv_export.py`: the cephalothorax and fangs get 2× texel density. Meshy `retexture_v1` from the four HD views.
6. `compose_spi1.py`: base colour, 1K normal and metal/roughness, and the region weight `chitin` (eyes and fangs
   excluded). Then `bake_creature_ao.py` and `grade_basecolor.py`.
7. `tier_ramps.py`: ramps taken directly from the native palette sprites. Body pixels of every frame (the same
   pixels in all three palettes) are matched to the shared base by luminance quantile and brightened per tier for the
   sprites' baked shading: brown ×1.45, blue ×1.6, red ×1.95 (raised from ×1.35 after review: the red tier is pure red
   and read too dark). `review/tiers_brightness_before_after.png`: before (top) and after (middle, temple below).
8. `reduce_lod0.py` (once, on `work/anim_v1.blend`; full mesh kept in `work/anim_v1_full.blend`): region-limited
   collapse decimation that keeps UVs, weights and the texture.
   - Femurs 45 %, tarsi 50 %, tibiae 70 %, abdomen 60 %, thorax 88 %, fangs untouched.
   - Each leg piece's ends (3 cm) are protected so the joints keep their shape.
   - Before/after: `review/lod0_reduction_before_after.png` (rest, head close-up, leg joints, attack, death, walk).
   - Do not rerun `uv_export.py` afterwards. It would re-UV the reduced mesh and break the painted texture.
9. `build_runtime.sh --install`: skin materials get `openyamm_specular 0` and metallic 0.

## Checks

- MM6 actor regression suite 11/11. All clips keep the lowest vertex at or above the floor; the corpse rests on it.
- Size: `review/size_check_static_vs_sprite.png`. A static `model spawn` at scale 130 beside a sprite spider at the
  same distance (friendly actors walk to the party, so moving shots exaggerate size).
- Tiers: `review/tiers_3d_vs_sprites.png` (New Sorpigal test spot; top 3D, bottom sprites; C, B, A left to right).

## Native shading transfer (2026-10-09)

`scripts/native_shade.py` runs between `compose_spi1.py` and the grade (defaults): chitin texels take the native
brightness by height (all five standing views, palette 822) times their own detail raised to 0.5 (softer leg bands),
blended at 0.7; `tier_ramps.py` is unchanged, so each tier's brightness stays as reviewed. Pre-transfer files:
`textures_pre_native/`.

## Gait pass: Walk2 and Run2 (2026-10-21)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 3. The engine plays one walk/run loop per stride of travel,
and the old clips covered 0.26 m (Walking) and 0.40 m (Running) per loop, so the game played them at 1.6–2.9×
(wandering) and 3.2–5.7× (chasing). `scripts/gait2_spi1.py` authors `Walk2` and `Run2` at the game's speeds
(`gait_gate.py` fit range walk 1.54–1.70, run 3.08–3.39 model units/s):

| Clip | Length | Stride (binding) | Authored speed | Duty | Sweep per stance |
|---|---|---|---|---|---|
| Walk2 | 0.300 s (18 keys at 60 fps) | 0.4845 m | 1.615 | 0.55 | 0.27 m |
| Run2 | 0.2167 s (13 keys) | 0.6998 m | 3.23 | 0.45 | 0.31 m |

- Same tetrapod and IK as `anim_spi1.py`, plus a small metachronal lead (back legs first).
- Footholds are planned per leg for the sweep, keeping hip-to-ankle within 0.96 of femur + tibia and above the leg's
  fold limit. The front legs rest almost straight, so some footholds come in by up to 14 % and the rear ones move back.
- The planted tarsus tip is the contact, with each tarsus piece's lowest vertex 2 mm above the floor. The tarsus turns
  about it with the leg's azimuth and tucks its tip in swing.
- Run2 lowers the body 4 cm, lifts the feet higher and tilts the front down by 3°. The abdomen bounces upward only.
- The `.blend` master is not re-exported. The clips are grafted onto the installed reduced export with
  `../claude_shared/graft_clips.py`, which checks that every joint's rest pose matches.

```sh
blender -b --factory-startup -P scripts/gait2_spi1.py -- work/gait2_clips.glb     # also saves work/gait2.blend
python3 ../claude_shared/graft_clips.py ../mm6_spi1_reduce_claude/export/mm6_spi1.glb work/gait2_clips.glb \
  ../mm6_spi1_reduce_claude/export/mm6_spi1_gait.glb --clip Walk2 --clip Run2
```

Gate (`gait_gate.py --set walking=Walk2 --set run=Run2 --set stride_length=0.4845 --set run_stride_length=0.6998`)
passed. The measured strides were 0.484 and 0.699. The window was ×0.79–1.43 on every tier, and the floor check was
ok. Installed as `mm6_spi1.glb`; see [the reduce project](../mm6_spi1_reduce_claude/README.md#gait-pass-2026-10-21).

## Gait rollout: Sprint (2026-10-31)

[Gait rollout package q1](../gait_rollout_20261031/q1/README.md) added `Sprint` for MAW's chase. Before, MAW's chase
played Run2 at ×2.00 on A and ×1.63 on B. The script is `../gait_rollout_20261031/q1/scripts/sprint_spi1.py`, a copy
of `scripts/gait2_spi1.py` with only a Sprint.

- The same tetrapod, with duty 0.32 and two short flights per loop.
- Run2's sweep, 0.33 m.
- 0.2 s, stride 1.018, authored speed 5.09.

It was grafted onto the installed source; the existing clips are byte-identical. Binding: `sprint: Sprint`,
`sprint_stride_length: 1.018`. The gate passed: MAW chase ×1.03-1.36.

```sh
cd ../gait_rollout_20261031/q1
blender -b --factory-startup -P scripts/sprint_spi1.py -- work/spi1_clips.glb
python3 ../../claude_shared/graft_clips.py work/rollback/mm6_spi1.glb work/spi1_clips.glb export/mm6_spi1.glb --clip Sprint
```

A far-LOD repair rerun (`lod_repair_claude`) must re-graft Walk2, Run2 and Sprint.
