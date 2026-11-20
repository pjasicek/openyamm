# Triton — MM8 m576

Full creature production for Triton A/B/C (merged monster descriptors 133–135; native palettes 577/578/579).
Technical validation: **PASS**. The user accepted the spear lunge; this texture correction awaits artistic review.

[Interactive viewer](review/viewer/index.html) · [Runtime captures](review/ingame/) · [Numeric gates](review/full_gates/gates.md)

Run the repository HTTP server on port 8776 to use the viewer at
`http://127.0.0.1:8776/level_generation/creatures/mm8_m576_claude/review/viewer/`.
The viewer includes all three native palettes, native sprite references, eight clips, slow motion and hand/head/foot cameras.

## Selected delivery

- [Portable body GLB](export/mm8_m576.glb), [separate trident GLB](export/mm8_m576_trident.glb),
  [packed editable Blender project](export/triton.blend).
- One shared skin with region masks and independently measured native tier ramps; no separate full texture sets per tier.
  Body maps retain the original 2048 square detail; the head remains 1024 square. The padded 4096 × 2048
  atlas and asset-specific `export/mm8_m576.cook.yml` preserve both resolutions on desktop. Copy that sidecar to
  `assets_source/worlds/mm8/models/` before installation; Android keeps the standard 2048 cap. ORM is **R specular / G roughness / B zero**; metallic is zero.
- Body colour/shadow triangle counts: **[10656, 5327, 3889, 2811]**. Trident colour triangle counts: **[632, 316, 176, 98]**.
  Sole contacts and the full left gripping hand survive reduction. The mid/far body budgets are capped at 38%/28%
  (far body also capped at 3,000 triangles). Preserving the gripping hand at the generic 25%/10% budgets
  overcollapsed the torso and legs; the retained budgets preserve both anatomy and shaft contact.
  The trident reduces separately to 98 triangles. These are documented asset-specific LOD budget deviations.
- 59 joints, at most four influences per vertex; source-frame humanoid rest axes, fitted elbow/wrist/finger joints,
  forearm/upper-arm twist helpers and separate shoulder-plate helpers. No runtime cloth simulation.
- Tier A uses scale **133.58256**; B and C use **144.71346** and **155.84604** (native standing sprite scales
  1.299988 and 1.399994). The original front frame measures 189 body pixels × native
  sprite scale 1.199996948; the raised shaft butt is excluded from this height measurement.
  Fitted standing body height is 1.697822 m.
- Measured walk/run strides: **1.301134 / 1.737106 m**.
  Head look is bounded to 25° yaw and 15° pitch across B_Neck/B_Head, checked separately with additive turns.

## Texture correction — 2026-10-18

Matched the body's skin luminance distribution to the accepted lower head/neck, preserving its hue and the shared
native palette ramps. The head maps remain byte-identical. Restored the original 2K body maps to reduce the difference
in surface detail; armour retains its original grade. This is a deliberate exception to the default 1K body budget.
The larger desktop texture set uses about 3.2 MB more on-disk texture storage and 19 MB more GPU texture memory including mips, shared by all three tiers.
[Indoor/outdoor checks](review/texture_revision/runtime_checks.json),
[close-ups](review/texture_revision/viewer_a/close.png) and [invariant checks](review/texture_revision/invariants.json)
record the revision. Geometry, rig, weights and every animation sample are unchanged; UVs only move into the new atlas.
Reproduce with `scripts/compose_triton.py`, `refresh_texture_exports.py`, `viewer_tiers.py`, `finalize_exports.py`,
then Blender `editable_delivery.py`. The original selected export is retained in `work/texture_revision_base/`.

## Motion

The attack revision uses the accepted **MM6 Cannibal underhand spear lunge**, mirrored onto Triton's fitted left
arm. The trident now uses a **forward grip**, 40 cm farther back on the same plain shaft. This deliberate change
from the native reverse grip follows the user's request for a better spear attack. A visible draw-back leads into
a forward step and thrust, followed by a slower recovery. The clip lasts **2.100 s**; measured tip speed peaks within
one 48 Hz frame of the unchanged **1.000 s** damage event. The carry, flinch and fall were refitted for the new grip.
The trident remains held through Death and disappears only in Dead. There is no spell or ranged attack.

| Clip | Duration, seconds |
|---|---:|
| Attack | 2.100 |
| Dead | 1.000 |
| Death | 3.633 |
| Fidget | 2.367 |
| Hit | 0.625 |
| Running | 0.733 |
| Standing | 3.000 |
| Walking | 1.000 |

Local animation sources were selected before modelling. Idle, walk, run, flinch, fidget and backward fall come from
the existing animation library; provenance and hashes are in [motion_selection.json](motion_selection.json) and
[the source motion measurements](review/source_motion_limits.json). Raw library clips are not part of the delivery.
Other source upper-body transitions retain their 42 ms filter. The adapted lunge uses 50 ms smoothing passes and a
measured timing correction; all other clip durations remain unchanged. Animation and twist-helper
keys share a linear 120 Hz sample grid.

## Validation and calibration

- [Export parity](work/export_parity.json): worst surface difference
  **0.01829 mm**, measured against Blender at fractional frames.
- [Full shared gates](review/full_gates/gates.json): {'PASS': 6474, 'INFO': 140, 'N/A': 68}; all clips, all colour/shadow LODs and the separate prop.
- [Export audit](review/export_audit.json): no degenerate triangles, no inverted closed parts, normalized four-weight skin,
  correct variants and required clips. Small opposed-normal crease triangles are enumerated in the report.
- Body UV overlap is zero; head raster overlap is 0.421% (shared triangle boundaries), with no degenerate UV triangles.
- [Head-look clearance](review/head_look_clearance.json), [running sole heading](review/running_sole_heading.json),
  [LOD stills](review/), [normal and quarter-speed playback](review/attack_revision/playback/playback.json).
- The shared gate tool has 16 passing regression tests, including a new axial-thrust test: a shaft-parallel strike axis
  has no distinct blade-flat direction, so that comparison is N/A. Signed tip lead, target direction, speed and timing
  remain active; reversed thrusts still fail.
- Creature-specific anatomical limits in [gates.json](gates.json): 90° upper-arm axial rotation for the fitted
  source-frame rig, 120° during the backward fall/corpse, and a 65° palm-to-grip cone for the broad diagonal fist.
  These replace generic 60° defaults; wrist, twist continuity, actual 3 mm shaft contact and 2 mm body-clearance limits
  remain enforced. Fidget is an active gesture, not a resting-palm pose; its mesh contacts are still checked.
- This attack revision is asset-only; its focused regression and fresh indoor/outdoor desktop captures are recorded
  in [attack revision checks](review/attack_revision/runtime_checks.json). The original ordinary OpenGL build and
  broader actor regressions are recorded in [runtime checks](review/runtime_checks.json).
  The focused MM8 family suite has 38 passes and one Juggernaut failure, also reproduced in the baseline without Triton. Triton checks with MM6/MM7 active pass. The broader `actors` run
  reports seven failures in other creature/map cases and terminates with `std::bad_alloc`; its complete log is retained.
  The isolated Bone Dragon rerun passes, with and without Triton bindings.
  Native sprite and model comparisons use MM6 oute3.odm outdoors and 6d19.blv indoors, with all three Triton tiers.
  The native indoor comparison uses an isolated fixture that mounts unchanged sprite definitions; model runs use ordinary assets.

The original 160 native BMP hashes are retained in [inventory.json](references_native/inventory.json) and rechecked
at delivery. Runtime installation uses `tools/install_model.py --world mm8`, preserving the project GLBs as sources
and producing the standard cooked desktop assets. Combat tables and original sprites are unchanged.

## References, cost and reproducibility

Five HD body views, four head views and the trident reference were generated from native evidence and reviewed by
the agent. Prompts, raw returns, selected views and hashes remain under `references_hd/`, `references_head/` and
`references_props/`. The compact crest, crossed harness, collar and plate coverage follow the native silhouette;
invented dorsal anatomy was removed before rigging.

Meshy spend: **30 credits of 100** (5 topology, 5 rig, 10 body texture, 10 head texture). All four jobs and downloads
are in [creature_3d_progress.json](creature_3d_progress.json); no paid animation jobs were needed.

The selected authoring base is `work/master_textured_uv.blend`; `export/triton.blend` is the packed portable copy.
For a selected-base re-export, run `export_runtime.py`, `tools/prepare_actor_glb.py`, `final_export_checks.py`,
`finalize_exports.py`, `audit_exports.py` and `run_full_gates.py` through the creature lease wrappers. Refresh
`viewer_tiers.py`, the viewer manifest hashes and the visual checks after a change. The attack revision is authored by `attack_cannibal.py`, `polish_lunge.py` and
`fit_forward_carry.py`, using the preserved original and intermediate checkpoints. Earlier work files and rejected
IK probes are retained as provenance; they are not the selected animation.

Desktop OpenGL visuals are checked. Android, Vulkan and performance benchmarking are outside this production check.

## Gait rollout (2026-10-31)

Package h16 of the [gait rollout](../gait_rollout_20261031/h16/README.md) appended two clips to the installed source
for Triton A/B/C: `Jog` (library Unarmed-Run-Forward legs and trunk on this model's `Running` arms and trident, 0.74
s) and `Sprint` (Unarmed-Sprint, 0.62 s, a lower chest lean so the trident clears the floor). Existing clips, meshes
and skins are unchanged (binary prefix identical). Installed 2026-10-31 with `tools/install_model.py --world mm8`;
bindings for the coordinator (../gait_rollout_20261031/h16/bindings.yml): run: Jog, run_stride_length: 2.7566, sprint:
Sprint, sprint_stride_length: 3.754. `gait_gate.py` passed for every tier under Standard and MAW
(`../gait_rollout_20261031/h16/review/m576_gait_gate.txt`). Rebuild: `../gait_rollout_20261031/h16/scripts/rebuild.sh
m576` (from the pre-gait copy `../gait_rollout_20261031/h16/work/mm8_m576_pre_gait.glb`). A far-LOD repair rerun
replaces the source without these clips: copy the new source over that pre-gait copy and rerun the rebuild before
installing. Rollback: install the pre-gait copy and drop the bindings.
