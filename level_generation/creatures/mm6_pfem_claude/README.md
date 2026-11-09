# MM6 female peasant (pfem) — 3D model, v3 (2026-10-06)

**2026-10-13 head repair installed:** forehead band removed and skin seams blended; original facial landmarks, rig and clips preserved. [Before/after and rebuild notes](review/head_repair_20261013/README.md).

**2026-10-13: original model restored and selected for further review.**
[Open original model viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_pfem_claude/review/viewer/) — all three dress colours and the original animations.
The separate `mm6_pfem_codex` replacement is retained but is not installed.

Animated model of the New Sorpigal female peasant (descriptors 595/596/597 `PeasantF1 A/B`, `Peasantf1 C`)
from the reviewed [stage-1 package](../new_sorpigal_3d_stage1_20261006/pfem/README.md). Opt-in binding
(`debug.actor_models=true`), next to the demon.

![Skins A/B/C](review/lit15_abc_sheet.png)

In-game (native NVIDIA/OpenGL): [close-up](review/ingame_v3/closeup_static.png),
[1:1 crop + town comparison with the HD sprite](review/ingame_v3/v3_acceptance.png).

**v1 is superseded.** The first delivery (MPFB body + hand-built garments, `work/final_v1.blend`, `textures/`)
was rejected: generic face, limp hands, flat texture. v3 follows the stage-1 handoff instead: Meshy Smart Topology
geometry, examined and cleaned before rigging, rigged and animated before any texture was generated.

| | |
|---|---|
| Runtime GLB | `assets_dev/worlds/mm6/models/mm6_pfem.glb` (12 MB) |
| Bindings | `actors.yml` A/B/C → skins `pfem_a/b/c`, scale 111.6, z_offset 0.07, stride 1.31; review-only `pfem_sprite_compare.yml` |
| Editable master | `work/final_v3.blend` (mesh, rig, 7 clips; maps in `textures_v3/`) |
| Rebuild | `scripts/build_runtime.sh --install` |
| Launcher | `./tools/run_pfem_3d_test.sh` |
| Regression | `mm6_pfem_actor_models_bind_town_peasants` (`actors` suite) |

## Result

| Item | Value |
|---|---|
| Triangles LOD0/1/2/3 | **12,781** / 6,389 / 2,299 / 762, one draw each; merged shadow meshes |
| Skeleton | 96 joints: Mixamo body with fingers + 2 forearm twist per arm + 12×3 skirt + 3 braid + knife; ≤4 influences |
| Textures | base colour 2048² ×3 skins; normal and metal/roughness 1024² |
| Meshy credits | **85 / 100**; 30 of them discarded (see below) |

Clips (24 fps, native timing): Standing 4 s loop (clasped hands, slight breathing), Walking 1.04 s loop
(Meshy walk, retargeted), Attack 0.75 s (knife only here), Hit 0.75 s, Death 0.625 s, Dead (prone, skirt fanned),
Fidget 0.75 s. Every clip has cloth-simulated skirt and verlet braid motion baked into bones.

## Pipeline (scripts/)

1. **Geometry**: Meshy single-image Smart Topology (`references/00_smart_topology_three_quarter.png`, 15k target,
   A-pose, untextured, 5 credits). `examine_mesh.py` audit; `step1_cleanup.py`: floating fragments and mouth
   interior removed, ribbon tails cut, hair edge laid on the skin, low ponytail with tie and brass circlet added,
   triangles cut only where hidden or flat (legs under the skirt, shoes, skull under hair, flat back): 15,261 → 11,806.
2. **Rig**: `fit_skeleton.py` fits the MPFB Mixamo skeleton inside the mesh (articulated ICP; arm, hand and
   finger lengths from measured fingertips). `rig_v2.py` adds skirt/braid/knife bones and transfers proxy weights.
   Stress poses: `review/pt2_*`.
3. **Animation**: `retarget.py` (Meshy walk), `author_clips.py` (native-key poses; hand frames measured from finger
   flexion), `skirt_sim.py` (cloth sim → bones; death blends into a deterministic floor drape), `finalize_actions.py`.
4. **Texture**: `uv_atlas_v2.py` (region seams, one island per finger phalanx, angle-based unwrap, iterative cuts
   until no UV fold remains; face 2.6×). One Meshy retexture from the four reference views on those UVs (10 credits).
   `compose_textures_v2.py` repairs projection faults: hair/skin spill, jagged neck shadow, the reference's hanging
   hands painted onto the skirt sides, procedural eyes, braid and knife, island padding, B/C palette skins (786→787/788).
5. **Delivery**: `export_glb.py`, `tools/prepare_actor_glb.py`, `tools/build_actor_lods.py`, `add_variants.py`.

## Feedback round 2026-10-06 (in-game review)

[Before/after face](review/feedback_v4/face_before_after.png) · [hands](review/feedback_v4/hands_full.png)

- **Eyes**: Meshy's eyeball shells sat off-centre in lumpy sockets. `face_repair.py` removes them and relaxes the
  sockets; `compose_textures_v2.py` inpaints the old painted eyes and paints clean almond eyes centred on each socket.
- **Faceted shading on chest/neck**: Meshy surface noise lit flat-per-triangle. `face_repair.py` smooths the eye,
  nose, mouth and sternum regions, closes a torn flap at the sternum and transfers softened custom normals to the skin.
  Same result with shadows on and off, so this was shading, not shadow-map acne.
- **Mouth**: the lip crease was smoothed and a soft seam painted.
- **Hands/forearms**: arms now use a hinge-constrained IK (elbow only flexes), wrists are limited to 70° swing,
  two forearm twist bones per arm carry wrist roll, and the clasp was re-authored with bent elbows and the right
  hand resting over the left in front of the skirt.

## Feedback round 2 (shadows, elbows, PBR)

[Top-down before/after](review/feedback_v5/top_before_after.png) · [elbows](review/feedback_v5/elbow_crop.png) ·
[lit sheet](review/feedback_v5/lit22_sheet.png)

- **Triangle pattern on chest, face and elbows** was sunlight self-shadowing: at medium/low shadow quality the
  engine casts with the reduced shadow LOD, whose decimated triangles stick out of the smooth colour surface.
  `shrink_shadow_lods.py` (now in `build_runtime.sh`) moves shadow LOD 1–3 vertices 4–15 mm inside the
  full-detail surface; ground shadows are unchanged. Confirmed in-game: identical to shadows-off/high-quality.
- **PBR pass** (asset only, like the demon): baked ambient occlusion in base colour (`bake_ao.py`), roughness by
  material — skin 0.52, lips 0.40, linen 0.93, green bodice/bands 0.86, hair 0.58, leather 0.55, metallic buckle
  and circlet; lips use soft shading instead of a hard painted seam.

## Feedback round 3 (ponytail)

[Clay](review/feedback_v6/braid2_sheet.png) · [lit, standing + walking](review/feedback_v6/lit24_braid_sheet.png) ·
[in-game profile](review/feedback_v6/side_crop.png)

The tube ponytail was replaced (`braid_v2.py`) by the reference hairstyle: a three-strand plait emerging from the
gathered hair at the nape, a wrapped tie at neck level and a full lobed tuft, hanging along the neck instead of
hooking outward (+1.3k triangles). Braid bones were re-placed on the new path; the verlet braid now collides with
its own rest distance from the neck instead of a fixed 10.5 cm capsule that had pushed it away from the body.
Texture: hair colour with fine along-strand streaks, a darker tie and gentler AO.

## Credits

| Job | Credits | Outcome |
|---|---:|---|
| detail_source_v1 (multi-image) | 30 | v1 bake source only |
| baseline_remesh_v1 + baseline_rig_v1 | 10 | walk clip source, A/B baseline |
| retexture_a_v1 | 10 | v1, discarded |
| smart_topology_v1 | 5 | **v3 geometry** |
| smart_retexture_v1 | 10 | premature (before rig), discarded |
| retexture_v2 | 10 | discarded: conformal UVs had folds (shared texels → neck smudge) |
| retexture_v3 | 10 | **v3 texture** |

## Known flaws

- Face is softer than the reference portrait; eyes are painted (no separate eyeball geometry).
- A pale strip shows between the circlet and the hairline.
- Hair is a smooth shell with painted strands; the reference's wavy volume is not modelled.
- Kneeling death frame balloons the skirt; corpse shows a little calf near the hem from directly above.
- Knife is a simple box-and-blade prop.
- Texture memory ≈ 78 MiB for three skins (B/C differ only in garment colour).
- User artistic acceptance not yet recorded.

## Head texture set (2026-10-08)

Head-only retexture per [creature textures](../CLAUDE_CREATURE_TEXTURES.md) ("Head-only retexture"):
- `references_head/`: Codex head turnaround (brief `CODEX_BRIEF.md`). Meshy `head_retexture_v1` (10 credits).
- `../claude_shared/head_texture_split.py` marked the head faces in the master (backup `*_pre_head.blend`), and
  `../claude_shared/compose_head_set.py` (run by `build_runtime.sh`) writes the 1K head maps, matching brightness
  across the neck seam.
- The head is one material for all tiers (the skin does not change between palettes). The body base colour is now
  1K, and skin, cloth and metal use `openyamm_specular 0` with metallic 0.
- Capture: `review/head_set_close_20261008.png`. Previous build: `export/mm6_pfem_prehead.glb`.
