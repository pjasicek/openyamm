# MM8 Necromancer — m472

> **Installed model reduced (2026-10-18):** the installed runtime is now the triangle reduction from [`../mm8_m472_reduce_claude/`](../mm8_m472_reduce_claude/README.md) (LOD0 16,947 -> 11,013). This project's own exports and master remain the unreduced production; the rollback source is `../mm8_m472_reduce_claude/work/mm8_m472_source_pre_reduce.glb`.


Rigged and installed in the shared Claude humanoid pipeline. The native bitmap family is `m472`; runtime
sprite groups are **m473/m474/m475**, descriptors **Necromancer (monster) A/B/C**, monster ids **55/56/57**.
`m472.yml` belongs to Ghoul B and is not this creature. The three Necromancers share the same geometry,
rig, clips and texture atlas; native palettes 473/474/475 supply green/blue/red runes and eyes.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m472_claude/review/viewer/)
includes native references, precise frame controls, tier switching and feedback. Technical checks and
agent image review are recorded separately from user artistic acceptance. The user accepted the corrected
Necromancer on 2026-10-18 ("good"), including the upper-lining correction.

## Selected deliverables

- `work/necromancer_master.blend`: editable textured, animated master with packed maps.
- `work/rig_textured_uv.blend`: fitted animation/UV master with semantic regions for rebuilding.
- `export/mm8_m472_prepared.glb`: portable LOD0 model with nine clips and +Y normal maps.
- `export/mm8_m472.glb`: installed game source with colour/shadow LODs, merged head atlas and three palettes.
- `assets_source/worlds/mm8/models/mm8_m472.glb`: authoritative game source copy.
- `assets_dev/worlds/mm8/models/mm8_m472.glb`: cooked runtime model; bindings live in that directory's `actors.yml`.
- `creature_3d_progress.json`: selected hashes, generation receipts, corrections and completion evidence.

The native silhouette retains narrow shoulders, pale gaunt face, swept white hair, silver segmented cuirass,
black floor-length rune robe, pointed cuffs and two skull-ended cords. Both hands have five articulated digits.
This caster has no weapon. The first four-digit Meshy body and its provisional rig are retained as rejected history.

## Rig, robe and timing

The source-frame humanoid rig uses 128 bones: 56 body/twist, 48 robe, 12 cuff, four hair, four tassel and four
palm/eye sockets. It uses at most eight normalized weights per vertex, the current native renderer limit.
Measured wrists, ankles and connected finger geometry determine the fitting; source rest-frame error is zero.
Meshy supplied initial weights with zero geometric transfer error. Concealed trousers remain an editable hidden
fitting proxy and are excluded from export. Short fitted slippers remain under the robe.

The closed robe uses baked damped chains, neighbouring cloth constraints, leg/foot envelopes and floor contact.
A small lower-hem allowance and restrained strides prevent feet piercing the skirt. Running adds up to 10 cm of
outward movement to the lowest cloth controls; explicit neutral translations prevent that adjustment leaking into
other clips. Hair and cuffs deform independently. The backward fall includes cloth settling and hair-aware floor
contact. Four sub-0.2 mm hem triangles were welded away before final texture correspondence.

| Clip | Seconds | Source / treatment |
| --- | ---: | --- |
| Standing | 2.0 | Authored native upright breathing |
| Walking | 0.8 | ArmedWalk, shortened leg stride |
| Running | 0.8 | UnarmedRunForward, robe-compatible leg stride |
| Attack / Cast | 1.533333 | UnarmedCastDualAttack2, planted legs, release at 1.0 s |
| Hit | 0.5 | UnarmedGetHitF1 with standing joins; within native 0.625 s |
| Death | 1.9 | UnarmedDeath1, legs together and 18 settling frames |
| Dead | 1.0 | Held final Death pose |
| Fidget | 1.5 | Small right-palm gesture returning to Standing |

The cast wind-up is extended by 16 frames; release and follow-through retain source speed. The naturally fast
source death head motion is retained. Local clips were selected before modelling (`motion/selection.json`);
no animation library purchases were needed. Native gameplay timings, stats and collision remain authoritative.
Both palms charge, and spells launch from their average position. Head look uses neck/head, limited to 25° yaw
and 15° pitch. Measured walk/run stride lengths are 0.745966/0.925548 m.

Standing geometry is 1.699328473 m tall. Scale **112.985807685** matches the native 192-unit standing height
for all tiers; yaw offset is −π/2. Native movement sprites and retargeted poses are not frame-for-frame identical.

## Textures and LODs

Meshy generated separate 2K body/head retextures from reviewed references. Body UV correspondence has a worst
centroid discrepancy of 0.06 mm; the head matches exactly. The retained animated mesh receives those UVs.
Semantic composition produces shared 1K maps, then the house post-process merges head/body into four
2080×1024 atlases. Native rune/iris ramps are identical across head/body materials. Eye colours use native
palette index 17, preserving the red tier instead of substituting the descriptor's pink glow colour.

Metal/rough texture channels are R=OpenYAMM specular mask, G=roughness, B=metalness. Cuirass metalness is 0.85,
roughness about 0.40; cloth roughness is about 0.89. The runtime/export normals are +Y. Editable pre-preparation
maps retain Meshy's input convention; rerun preparation when exporting them.

Colour LOD triangle counts are **16,947 / 8,471 / 4,236 / 2,117**, with matching shadow levels. The final winding
check reports no inverted closed parts. One tiny inverted LOD3 shadow component was corrected. Meshy cost was
**40 credits**: two bodies, two provisional rigs and body/head retextures. No jobs remain pending.

## Review and validation

- `work/deformation.json`: all 30-fps samples of eight animated roles; no visible shoe/robe containment;
  visible arm-skin edge-stretch p99 maximum 1.3838 and hand maximum 2.5205. Floor clearance is at least 3 mm outside
  intentional airborne phases. Running's short fold edges stretch more, without visible tears in reviewed images.
- `review/playback/`: all nine clips recorded at 1× and ½×, with timed samples and contact sheets.
  Agent review used those sampled images, close views and numeric checks, not continuous human video watching.
- `review/ingame/`: actual NVIDIA/OpenGL desktop captures in New Sorpigal and Agar's Laboratory, models and
  original sprites at matching cameras. Casting, movement, LOD changes and death were captured. Indoor fixtures
  preload native sprites without altering production maps. These are visual checks, not performance benchmarks.
- Browser check: all 27 tier/clip combinations pass, with no console errors. Browser skinning uses four weights;
  native captures verify the eight-weight result.
- Development build passed. Focused regression `mm8_necromancer_actor_models_keep_tiers_and_dual_cast` passed:
  tiers, native scale, nine clips, LODs, robe/finger/socket rig, unchanged simulation and real dual-palm projectile origin.
- `review/validation/` records complete suite results and any failures outside this family. Android and Vulkan
  builds were not run. User artistic acceptance remains separate.

## Armour and cord correction — 2026-10-18

The user identified sliding white-cord roots and a cuirass that bent with the cloth. The metal is now a separate
rigid surface over recessed black lining, with the complete plate, fastening and upper cord vertices bound to
`B_Spine1`. The connected robe waist blends into that attachment; sleeves keep their original deformation.
Cord ends retain hanging motion, with torso/robe clearance and gravity settling during death. No bones, textures,
animation purchases or gameplay changes were added. The lining adds 1,885 triangles at LOD0.

`review/armour_fix/rigidity.json` checks every half-frame of all eight animated roles: maximum plate/root drift
is **0.000716 mm**. The export also verifies that `Dead` exactly matches the final `Death` pose. Visible sleeve
skin and the inner lining are measured separately in `work/deformation.json`. The final viewer passed all 27
combinations, and the focused Necromancer regression passed. New desktop GPU captures and receipts are in
`review/armour_fix/`; the original `review/ingame/` remains the earlier revision and unchanged sprite baseline.

[Cast close-up](review/shots/armour-cast.png), [forward lean](review/shots/armour-lean.png),
[settled corpse](review/shots/armour-dead.png), [validation](review/armour_fix/validation.json).
User artistic acceptance remains pending.

To reproduce the correction from the retained pre-correction UV master, run
`scripts/check_armour_deformation.py` through the guarded Blender wrapper before rebuilding the exports below.

## Upper-lining correction — 2026-10-18

The user accepted the model apart from black lining crossing the upper plate during animation. Covered lining
now uses the same rigid transform as the cuirass; its rest-space inset stays constant throughout every clip.
The neck base follows the collar, blending into the existing head motion above it. The outer sleeve motion,
cord attachment, metal geometry, textures and clip timing remain intact. Triangle and bone counts are unchanged.

`review/lining_fix/` records the reported image, attachment checks and refreshed native captures. Close-ups:
[cast frame 20](review/shots/lining-cast20.png), [cast frame 32](review/shots/lining-cast32.png),
[release](review/shots/lining-release.png). All nine clips and 27 tier/clip selections were checked, along with
the exported held death pose. Focused regression and indoor/outdoor desktop rendering passed with an isolated
fixture containing the installed model and three unchanged Necromancer bindings (see `review/lining_fix/fixture.json`).
The shared-manifest check remains blocked by an unrelated missing Guardian model, `worlds/mm8/models/mm8_m592.glb`;
see `review/lining_fix/regression-shared.log`. No Android/Vulkan rebuild.

## Rebuild / reproduce

Claim this creature through `tools/run_creature_workspace.sh` before editing; use its returned ownership token.
From the repository root:

```sh
tools/run_creature_blender.sh --token <token> level_generation/creatures/mm8_m472_claude/scripts/build_assets.py
python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m472_claude --token <token> --port 8912 check
OPENYAMM_REGRESSION_FILTER=mm8_necromancer ./build/game/openyamm --world mm8 --headless-run-regression-suite actors
```

The build script starts at the selected fitted UV master, composes maps, exports, prepares normals, generates
colour/shadow LODs, adds palettes, merges the head and refreshes portable viewer tiers. It makes no paid requests.
If rebuilding changes exports, refresh manifest hashes, reinstall with `tools/install_model.py ... --world mm8`
and repeat affected review. Native capture launch settings, tours and run receipts are retained under `review/ingame/`.

Partial MM8 suite: **30 passed, 4 failed**. The broader run was interrupted after over six minutes and over four minutes without new log output. The Necromancer case passed. The earlier MM6 run reached 94 passes and 10 failures before an allocation error. See `review/validation/regression.json` for exact failures and the baseline with its bindings removed.

## Walk2 / Run2 (2026-10-21)

New walk and run clips with a planted phase, authored here (`scripts/gait2_*.py`) and grafted into the installed
reduced GLB. Details, numbers and the gate binding: [`../mm8_m472_reduce_claude/README.md`](../mm8_m472_reduce_claude/README.md#new-walk-and-run-walk2-run2-gait2-2026-10-21).
