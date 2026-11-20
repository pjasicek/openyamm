# MM8 Cleric (`m460`)

> **Installed model reduced (2026-10-19):** the installed model is now the reduction from [`../mm8_m460_reduce_claude/`](../mm8_m460_reduce_claude/README.md) (LOD0 9,811 -> 7,645; staff unchanged). This project's exports and master remain the unreduced production; the rollback source is in `../mm8_m460_reduce_claude/work/`.

Rigged, textured human Cleric using the shared Claude humanoid workflow. The accepted
[MM6 Sorcerer](../mm6_sor1_codex/README.md) informs the grounded robe, staff and caster fitting;
[Djinn](../mm6_djn_claude/README.md) informed the initial cast study. The user-requested revision now uses
Mixamo **Standing 2H Magic Attack 01** for both Attack and Cast, with the staff carried as an accessory.
The Cleric has independently fitted joints, hands, robe and staff.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m460_claude/review/viewer/)
contains three palettes, eight clips, native view comparisons, frame stepping and feedback links.

## Delivery

- [Packed editable master](export/mm8_m460.blend).
- [Portable animated body and staff](export/mm8_m460_lod0.glb).
- Runtime [body](export/mm8_m460.glb) and rigid [staff](export/mm8_m460_staff.glb).
- [Exact family bindings](export/bindings.yml); installed in `assets_dev/worlds/mm8/models/actors.yml`.
- Authoritative installed sources: `assets_source/worlds/mm8/models/mm8_m460{,_staff}.glb`.
  Desktop-cooked models and textures are under `assets_dev/worlds/mm8/models/`.
- [Canonical progress and service receipts](creature_3d_progress.json),
  [native provenance](references/sources.json), [native action inventory](native_inventory.json).

Descriptors **46–48**, `Cleric (human male) A/B/C`, are Acolyte, Cleric and Priest of the Sun.
The model retains the bare arms/chest opening, high collar, russet brocade robe, red ornamented front panel,
gold belt/cuffs and pale pointed staff finial. Native palettes **461/462/463** change only the hair and staff:
black/green, brown/blue and blond/red. The native sprites are preserved.

## Motion and fitting

| Role | Seconds | Selected behavior |
| --- | ---: | --- |
| Standing | 2.0 | RelaxIdle, fitted upright staff carry |
| Walking | 0.8 | RelaxWalkForward, grounded steps and fitted closed robe |
| Attack | 2.7 | Two-handed library cast with a fitted forward step and weight transfer; staff follows the right hand |
| Cast | 2.7 | Same fitted two-handed performance under the independent spell role |
| Hit | 0.6 | Short recoil; stable staff grip, within the native 0.625 s window |
| Death | 2.0 | Collapse to the floor, early staff release, fitted robe drape |
| Dead | 1.0 | Exact final Death pose held |
| Fidget | 2.4 | Grounded head turn and staff settling |

Attack/Cast preserve the library performance's **2.7-second** duration and source speed. The hands gather
overhead and drive forward; release is **1.20 s**, at the end of the forward drive near full reach. The left foot steps **20 cm** forward with **4.5 cm** lift; soft knees and a **9 cm** hip shift carry weight into
the release while the right foot supports the body. The step returns smoothly to idle. The robe follows the legs
without exposing them through its outer surface. The staff grip and fitted head response stay unchanged.
Entry/recovery blend smoothly to the exact Standing pose. Both palms carry the existing spell charge effects;
projectiles leave the left palm. Tier B retains its native Day of the Gods buff; A/C retain Light Bolt.
Native spells, damage, movement and AI data are unchanged. [Current selection and fitting record](review/cast_step/selection.json).

Measured stride is **1.523 m/cycle**. Speeds 160/180/200 remain below the existing run threshold at this scale;
`run` aliases Walking. Native standing body height is **188 world units**, excluding the staff.
The posed model height is **1.699728 m**, giving scale **110.605921**. The staff finial is two native pixels
below the scalp; the butt reaches the hem. The right hand lifts the staff during steps without sliding its grip.
Head look uses `B_Neck`/`B_Head`, limited to **15° yaw / 8° pitch** to clear the high collar.

The source-frame rig has **124 bones**, including five fitted fingers per hand, four arm twist bones,
64 robe controls, the Staff joint and three effect sockets. Meshy's independent joint estimate was checked
against actual limb rings and hand connectivity. Arm p99 stretch is at most **1.65×**, hand-edge stretch
**1.55×**, wrist swing **55.2°**. Half-frame full-shaft checks found no body crossing. The only residual signed
arm proximity is **0.14 mm** at the free hand during Hit. Ground contact remains within **1 mm** penetration;
held-staff clearance is at least **5.6 mm**. Open robe folds are judged visually, not by a closed-skin inside test.
[Full motion measurements](review/delivered_motion_checks.json) and [head-look measurements](review/head_look.json)
retain exact frames and positions.

## Geometry and materials

Body colour/shadow LODs: **9811 / 4905 / 2452 / 1224** triangles.
Staff LODs: **600 / 300 / 149 / 75**. The 10,411-triangle close model exceeds the 5–8K guide to retain
articulated hands, the separate face region and the closed floor-length robe; it remains below 15K.
Reduction followed weighting. Runtime skinning uses at most eight influences; fitting the 16 affected vertices
to that limit introduces at most **1.23 mm** error across the sampled actions, below a quarter native pixel.

The body and head originated as separate 1K PBR sets. Verified per-face/per-corner UV transfer retained our
geometry, rig and motion; the Meshy returned model never replaced the animated master. Body/head maps merge
into padded **2080×1024** runtime atlases. The staff uses **128×1024** maps. All three tiers share textures and
RGBA region masks, with native palette ramps in [m460_ramps.json](textures/m460_ramps.json).
Body UVs have no zero-area triangles. Nine small, planar staff endcap triangles deliberately sample a single
UV texel each for uniform paint and flat normals; the material audit checks this exception.
The red staff ramp excludes unrelated cyan/blue effect-edge palette indices. Body and head share one hair ramp.

Normal-map green direction was measured and corrected before export. The neck boundary converges in colour
and tangent normal; average base-colour seam mismatch is **0.45/255**, p95 **2/255**. Skin and cloth remain matte;
metallic is zero. MR red is the runtime specular mask, green roughness, blue metallic. Gold and eyes retain their
separate specular response. [Texture composition](textures/composition_report.json) records the native indices.

## Verification and review

[Export parity](work/export_parity.json) samples all eight clips after GLB reimport: maximum surface difference
is **0.10 mm**. [Static audit](work/static_audit.json) checks the installed-source hashes, four LODs, materials,
variants, finite animation values and normalized eight-weight skinning. The [material audit](work/material_audit.json)
checks UVs, atlas dimensions, unit normals and the runtime PBR channel contract.

[Recorded playback](review/playback/playback.json) covers all roles at normal and half speed, with videos and
sampled frames. Close views cover the face, both hands, casting, walking and corpse. The viewer checks all
**24 tier/clip combinations**. Current playback includes the revised stepping cast and final textures.
The previous planted-cast playback is retained under `review/cast_step/before/playback/`. Geometry, skin weights and the other six
clips are verified identical to the initial delivery.

Runtime test and capture results are recorded in [the handoff](HANDOFF.md). The user accepted the current
Cleric, including the stepping two-handed cast, on **2026-10-18** ("ok accepted"). Android and Vulkan were not tested.

## Reproduction

Claim this project with `tools/creature_workspace.py` before writing. Use the guarded Blender/review wrappers.
The selected authoring checkpoint is **`work/rig_uv.blend`**. `scripts/build_final_package.py` exports the packed
master, prepares the portable model, rebuilds the viewer, verifies export parity, builds LODs, applies palette
ramps, splits the staff and merges head materials. Install both final GLBs with `tools/install_model.py --world mm8`,
then run `scripts/static_audit.py`. Serialize installs and ordinary builds because both update the model cook cache.

`compose_textures.py` reproduces current maps from retained Meshy returns, UV rasters and AO. `fit_staff_length.py`
and `fit_hit.py` are the final motion refinements already applied to the selected checkpoint. The current cast is reproduced by `fit_dual_cast.py` from `work/pre_dual_cast.blend`, followed by
`promote_dual_cast.py`. The leg revision applies `fit_cast_step.py` to `work/pre_cast_step.blend`, then
`verify_cast_step.py` checks and selects it before the normal export/install pipeline. Earlier rig fitting, source-motion and drape scripts
are retained as provenance; do not rerun them over that checkpoint.
Meshy consumed **30 credits**: 5 body, 5 independent rig, 10 body retexture, 10 head retexture. No paid animation jobs.

## Anim fix (2026-11-11, MM6–MM8 audit)

Jog recomposed with shorter, quicker strides: robe cloth bad 23.2 -> 16.1 %; `run_stride_length` 1.805. Details:
[mm8_m460_animfix_claude](../mm8_m460_animfix_claude/README.md).
