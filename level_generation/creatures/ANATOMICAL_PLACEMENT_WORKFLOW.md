# Anatomical placement proposals from reviewed MM6 examples

Use this procedure when an agent is asked to prepare scale/offset JSON resembling the user's manual
**Match family height & bottom → inspect anatomy → correct frames → review motion** process.
It applies to MM6–MM8. It supplements [independent placement review](DIRECT_SPRITE_WORKFLOW.md#independent-placement-review),
not the generation or deployment workflow. A placement request does not authorize regeneration or installation.

The [MM6 manual study](mm6_manual_placement_study_20261004/README.md) compares all 60 frozen families and visually
examines eight complete example clips. The approved source recipe is
[`assets_source/creatures/mm6/adaptations.json`](../../assets_source/creatures/mm6/adaptations.json).
Its transforms are reproducible, but its anatomical landmark maps and notes are empty. Consequently,
the examples and the user's explanation establish a review procedure; they do not train an automatic detector
or reveal which particular foot was chosen in every old edit. Never replace approved geometry with a new heuristic.

## 1. Resolve the exact selected inputs

Read the requested family's selected manifest, its artifact hash, current checkpoint and native action/view
bindings. For this MM6 bank, use `adaptations.json.families[family].source`, with the matching
`<family>/selected.json` retained inputs. Choose the checkpoint version by **artifact hash**, not date or filename.
Use the selected reviewed atlas for geometry, even if a higher-resolution retained master supplies export detail.
The alpha bounds of that reviewed atlas define the existing transform anchor.

Inventory every distinct frame, including unused and completely transparent art. Review every action and stored
view; bindings can reuse walking frames for standing or reuse an initial pose in another action. A fixup belongs
to a frame name across all actions/palettes/views, so check every consumer. Do not invent separate adjustments for
an alias that still points at the same bitmap. Keep native timings, native scales, mirrors and fractional pivots.

Work in a new isolated proposal directory and preserve the user's checkpoint and recipe. Approved frame edits,
colour controls, guides, notes and regeneration flags are the starting state, not values to reset.

## 2. Initialize, then classify each action

For new unreviewed placement, apply **Match family height & bottom** once as an initial proposal. It fits the
whole silhouette independently per frame and retains existing X offsets. For an already reviewed family,
compare that initialization without replacing its accepted edits. Weapons, flames, wings, tails and shadows can
make this initial fit misleading. A family has a body type; each action additionally has contact/motion mechanics.
For example, a flying creature's collapse or corpse must be examined separately from its hover loop.

| Policy | X alignment | Y alignment | Size calibration | Independent checks |
| --- | --- | --- | --- | --- |
| `humanoid_walk` | Head axis, eye midpoint, visible profile eye, or a corresponding rear-head feature | Native stance-foot ground contact | Crown to stance contact in comparable upright poses; use a torso span when bent | Pelvis/shoulders, contact foot, opposite leg, original head bob |
| `humanoid_planted` | Selected planted foot during the native stationary phase | Same foot's sole/contact | Body span inherited from compatible poses, checked against crown/torso | Head, pelvis, other foot and swinging arm |
| `flying` | Eye/head centre; use pelvis/body core if head is obscured | Same corresponding head/body point in that native frame | Two separated body points, such as crown to pelvis or torso span | A body point outside the fit; native head bob, torso tilt and wing-root motion |
| `grounded_beast` | Corresponding thorax/abdomen/body core; profile eye when appropriate | Native stance contacts/ground plane | Body core span or comparable back-to-ground height | Head, rear body, alternating leg contacts |
| `collapse` | Native fall/contact mechanics, examined phase by phase | Native fall/contact mechanics | Anatomical size from compatible poses, accounting for foreshortening | Body trajectory, impact and final corpse continuity |
| `other` | Explicitly documented body feature | Explicitly documented contact/motion feature | Explicit anatomical evidence | Independently located feature; use for amorphous/no-head creatures |

For humanoids, “left foot” means the **actor's** left foot, not screen-left after mirroring. Choose whichever
native foot is actually planted. If contact switches, change the constraint at the corresponding native phase.
Never freeze a moving foot just because the action is called attack/fidget/hit. In walking, feet alternate;
keep the source's head sway and vertical bob rather than forcing every head onto one fixed family-wide line.

For flying actors, feet and wing tips are movement checks, not compulsory height/bottom constraints. Matching
head Y alone cannot solve both scale and translation: obtain size from another separated body feature first,
then align the head. A grounded beast's tail or longest leg must not define body scale or X centre.

The “crown” is the corresponding actual head/ordinary head covering, excluding a raised weapon, staff flame,
extended wing, tall crest or unrelated spike. When the relevant body landmark is obscured, use a different
visible pair or record the uncertainty. Do not infer a hidden eye from symmetry or substitute alpha top silently.

## 3. Mark anatomy before calculating

Draw the selected points on **both** actual sprites at native logical size or larger. Check each identity
visually. Suggested detector points are candidates, not evidence. Save named points, their visibility and the
reason for the chosen action policy. A point used for an independent check must not also determine the fit.

Start with one anatomically justified scale for a coherent generated animation/view. Compare several poses
and the transitions to other actions. Do not force all recorded scale factors to be identical: the reviewed MM6
recipe legitimately contains per-frame scales. Allow an exception only after visible body spans demonstrate
generated size drift or a mismatch with native foreshortening. Record that reason. Do not derive exceptions from
weapon reach, wing spread, a lifted knee or the overall pose height. See [scale diagnosis](SPRITE_SCALE_DIAGNOSIS.md).

Check two or more separated body features where possible. Size fit, X alignment and Y alignment can use
different features. After changing scale, recompute translations so the intended semantic pivot stays aligned.
Moving a guide alone never moves art. A short eye-to-eye span is unstable for whole-body size calibration.

## 4. Compile the existing JSON operation

The checkpoint accepts `scale_anchor` values `bottom`, `top` and `pivot`. A semantic planted-foot constraint
does **not** require a new anchor enum. Retain the usual `bottom` serialization and compute the compensating
translation for the selected foot (or head/body point):

```text
k = pixels_per_logical_pixel
A = [crop_x + (reviewed_alpha_left + reviewed_alpha_right)/2,
     crop_y + reviewed_alpha_bottom]                 # physical pixels, unmodified reviewed bounds
T(p) = A + s * (p - A) + O
O_axis = k * native_landmark_axis
         - (A_axis + s * (k * restored_landmark_axis - A_axis))
```

Both measured landmark arrays are in canonical actor-canvas **logical** coordinates before fixups, native
frame scaling and mirroring. On an unchanged cropped restored tile, add `crop_origin_px / k` to tile-local
coordinates. On the prepared native PNG, include the viewer's exact correction:

```text
dx = (logical_width - source_width)/2 - floor((logical_width - source_width)/2)
dy = -(logical_height - source_height)/2 if manifest.anchor == "center" else 0
```

Native previews already contain floor-centred/bottom-aligned padding; do not add that padding again. If measuring
from an already adjusted displayed sprite, invert its current scale/offset first. The shared reviewer landmark
editor does this inversion, including displayed native frame scale and mirrors. Do not double-apply them.

Offsets in the current checkpoint are **integer physical atlas pixels**. Use JavaScript-compatible rounding
`floor(O + 0.5)`. Quantization can leave up to 0.5 physical pixel per axis, or 0.25 native pixel at 2×.
Retain fractional native pivots and anchor calculations; do not round the intermediate geometry. This checkpoint
rounding rule does not change the exporter's fractional resampling or the native timing/binding contract.

### Shared proposal compiler

[`propose_anatomical_placement.py`](mm6_remaining/acceptance_viewer/propose_anatomical_placement.py) turns an
agent's explicitly measured landmarks into the existing `frame_fixups.json` format. It reuses the shared
family loader, artifact hashing and checkpoint validator. It does not locate anatomy, choose contact phases,
resample art, accept a family or replace the user's checkpoint. No per-family tool/viewer is needed.

Create a `placement_plan.json` in the task's isolated family directory with these top-level fields:

```json
{
  "schema_version": 1,
  "family": "mm6_goblin",
  "manifest": "<exact selected manifest path relative to repository root>",
  "manifest_sha256": "<SHA-256 of that manifest>",
  "artifact_sha256": "<current selected-art digest from the shared reviewer>",
  "checkpoint": "<existing frame_fixups.json path relative to repository root>",
  "checkpoint_sha256": "<SHA-256 of the unchanged checkpoint>",
  "frames": {}
}
```

Each `frames[name]` needs `policy`, `reason`, `points`, `align`, `checks`, `check_tolerance_native_px`, and either
`scale_factor` or `scale_from`. Arbitrary named point pairs are retained in the evidence; the existing viewer's
saved landmark UI still supports only `eye1`, `eye2`, `head`, `head_top` and `groin`. Custom sole/contact names
do not extend that UI schema. The following is a **synthetic coordinate example**, not measured Goblin anatomy:

```json
{
  "policy": "humanoid_planted",
  "reason": "Actor-left sole is planted; crown-to-sole calibrates size; hip checks it independently.",
  "points": {
    "left_sole": {"native": [37.25, 100.25], "restored": [40, 100]},
    "crown": {"native": [37.25, 12.25], "restored": [40, 20]},
    "hip": {"native": [48.25, 56.25], "restored": [50, 60]}
  },
  "scale_from": {"points": ["crown", "left_sole"], "axis": "y"},
  "align": {"x": "left_sole", "y": "left_sole"},
  "checks": ["hip"],
  "check_tolerance_native_px": [0.26, 0.26]
}
```

For a walking frame, select head/eye X and stance-contact Y. For flying, align both axes to a head/body point
after a separate body-span calibration. `scale_from.axis` accepts `x`, `y` or `distance`. Alternatively,
repeat an independently calibrated shared `scale_factor` across the clip, recording its reference frames in
`reason`. Tolerances must reflect the family's visible native detail and measurement uncertainty. The tiny
synthetic tolerance above is a rounding test, not a recommended artistic threshold.

Run from repository root, replacing the example paths with the authorized staging directory:

```sh
python3 -B level_generation/creatures/mm6_remaining/acceptance_viewer/propose_anatomical_placement.py \
  --plan level_generation/creatures/<session>/<family>/placement_plan.json \
  --output level_generation/creatures/<session>/<family>/proposal/frame_fixups.json
```

The compiler requires unchanged manifest, art and seed-checkpoint hashes. It merges passing annotated frames
into a copied checkpoint, preserving other frames/versions, guides, colours, notes and flags. It writes a
companion `frame_fixups.evidence.json` containing measured pairs and independent residuals. A failed frame
keeps its previous transform and gets a recorded reason; other valid frames continue. If every fit fails,
only evidence is written. Missing/unannotated frames retain their seed state and do not count as newly reviewed.

Inspect the candidate in the existing shared reviewer with an isolated state directory:

```sh
python3 -B level_generation/creatures/mm6_remaining/acceptance_viewer/serve.py \
  --package <exact-selected-manifest> --state-dir <proposal-directory> --port <unused-port>
```

`--state-dir` must contain the candidate named `frame_fixups.json`. Decisions in this directory remain proposals;
do not copy an older accepted decision onto a changed fixup revision. Freeze acceptance only after actual review.

## 5. Inspect residual motion and finish the review

Review every pose on a common fixed actor canvas with the same guides and zoom. Native, initial fit and proposed
result should be directly comparable without individually centring or stretching them. Inspect profile/back
views using a corresponding visible feature; then verify mirrored consumers with the native frame scale enabled.

For a body landmark, compare `e_i = T(restored_i) - native_i` across the native sequence. A changing native
head/hip location is intentional motion; an unexplained jump in `e_i` suggests added jiggle. Review adjacent
steps, the loop's final-to-first transition, and standing/walk/fidget/attack/hit/death/corpse transitions where
the bindings connect them. Preserve original holds/repeated frames. Use timed playback to resolve ambiguity;
only claim it was watched when it actually was. Do not smooth offsets blindly across native impact/recoil steps.

Check planted-foot sliding and independently measured head/hip/shoulder/other-foot movement. A near-zero fitted
foot or head residual validates the arithmetic, not anatomy. If uniform scale plus translation cannot reconcile
the independent body features, record the affected frame/sheet as an art/proportion issue rather than stretching
axes, switching to a weapon anchor, raising tolerances to hide it or inventing a new pose.

Before accepting a complete family, inspect every animation/view, unused art, 100% material detail, alpha edges,
all palettes and material masks. Apply identical geometry to base/masks/palette outputs. Retain the source recipe,
plan and selected-art provenance. Export from immutable retained masters through the shared exporter, resampling
once; use the deployment workflow only when installation is explicitly in scope. Report numerical coverage,
actual visual coverage, blocked frames and proposal-versus-accepted status separately.

## Agent task template

> Prepare anatomical placement proposals for [families] using ANATOMICAL_PLACEMENT_WORKFLOW.md.
> Treat the current reviewed checkpoint as the seed; stage in [directory]. Inspect every native action/stored
> view, classify motion/contact phases, mark scale/anchor/independent-check landmarks on both images, and compile
> the existing checkpoint JSON with the shared tool. Preserve native motion, aliases, mirrors, timing, palettes
> and fractional anchors. Inspect fixed-coordinate sequences and use playback for uncertain motion. Record
> blocked anatomy rather than forcing a fit. Deliver reviewable JSON/evidence and exact review coverage; keep
> approved recipes, source art and runtime assets unchanged.
