# MM6 male peasant (pman) — 3D model, 2026-10-06

New Sorpigal male peasant (descriptors 607/608/609 `PeasantM1 A/B/C`), made with the
[humanoid NPC playbook](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md) after the female peasant. Opt-in binding
(`debug.actor_models=true`); `./tools/run_pfem_3d_town.sh` shows both peasant families in town.

![Skins A/B/C](review/lit_abc_sheet.png)

In-game: [standing](review/ingame/full.png), [face](review/ingame/face_crop.png), [top-down](review/ingame/top.png),
[town, B tier walking](review/ingame/town2_sheet.png).

| Item | Value |
|---|---|
| Runtime GLB | `assets_dev/worlds/mm6/models/mm6_pman.glb` |
| Bindings | `actors.yml` A/B/C → skins `pman_a/b/c`, scale 112.4 (253 px × 0.7), z_offset −0.26, stride 1.35 |
| Triangles LOD0/1/2/3 | **7,985** / 3,989 / 1,433 / 475 (shadow LODs tucked inside the colour surface) |
| Skeleton | 57 joints: Mixamo with fingers + 2 forearm twist per arm + knife; ≤ 4 influences |
| Textures | base colour 2048² × 3 tiers (only the tunic changes: green / slate / wine, palettes 798→799/800); normal and metal/roughness 1024² |
| Meshy credits | **15 / 100** (Smart Topology 5, one retexture 10) |
| Clips | Standing 4 s (loose fists), Walking 1.04 s (Meshy walk retargeted), Attack 0.75 s (knife), Hit 0.625 s (5 native keys, forearm guard + squat), Death 0.625 s (side fall → prone), Dead, Fidget 0.75 s |
| Regression | `mm6_pman_actor_models_bind_town_peasants` (A=1, B=9, C=7 in New Sorpigal) |
| Master / rebuild | `work/final_v1.blend`; `scripts/build_runtime.sh --install` |

## What was cheapened (per the brief)

Boots/trouser legs and the tunic back decimated hard, skull under hair reduced, belt and buckle reduced to
157/63 triangles (detail in texture), Meshy eyeballs and mouth interior removed (eyes are painted), hands and face
kept. 11,643 → 7,985 triangles before any rigging.

## Fixes found by the self-check loop

- Knee: a torn flap in the Meshy legs (welded and closed in `step1_pman.py`).
- Spine/neck joints sat at the back of the skull: the tunic hides the torso from the ICP fit, so axial joints are
  now placed from ray-cast cross-sections (`fit_skeleton.py`).
- Collar: skin z-fighting/poking through the tunic at the collar points — `tuck_skin.py` keeps 10 mm clearance
  and `drop_shoulder_skin.py` deletes the few covered faces still seen in front of the cloth (UVs unchanged, no
  retexture). Meshy tunic texels painted skin-colour/near-black near the collar are inpainted in `compose_pman.py`.

## Known flaws

- Brows read a little heavy/stern (as in the reference); light stubble from the reference retained.
- The collar's inner layer reads as a narrow stand collar.
- Death/side-fall is authored from five native keys only; no cloth sim (the tunic is short and rigidly weighted to
  hips/thighs).
- User artistic acceptance not yet recorded.

## Head texture set (2026-10-08)

Head-only retexture per [creature textures](../CLAUDE_CREATURE_TEXTURES.md) ("Head-only retexture"):
- `references_head/`: Codex head turnaround (brief `CODEX_BRIEF.md`). Meshy `head_retexture_v1` (10 credits).
- `../claude_shared/head_texture_split.py` marked the head faces in the master (backup `*_pre_head.blend`), and
  `../claude_shared/compose_head_set.py` (run by `build_runtime.sh`) writes the 1K head maps, matching brightness
  across the neck seam.
- The head is one material for all tiers (the skin does not change between palettes). The body base colour is now
  1K, and skin, cloth and metal use `openyamm_specular 0` with metallic 0.
- Capture: `review/head_set_close_20261008.png`. Previous build: `export/mm6_pman_prehead.glb`.
