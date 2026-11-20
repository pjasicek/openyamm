# Shared gate runner validation — 2026-10-12

This validates the **runner**, not production acceptance of the four creatures. Every complete audit includes
all exported clips, all four colour and shadow body LODs, and every declared prop LOD. Reports deliberately
retain failures and missing intent. No creature project, runtime asset, binding, game process or build was changed.

## Reproduce

The read-only inputs, copied handoffs, JSON configs, complete reports and logs are under
[`output/codex_batch/gates_tool/validation/`](../../../../output/codex_batch/gates_tool/validation/).
For example:

```sh
level_generation/creatures/claude_shared/gates/run_gates.sh \
  output/codex_batch/gates_tool/validation/dwa1/mm6_dwa1.glb \
  --config output/codex_batch/gates_tool/validation/dwa1/gates.json \
  --out output/codex_batch/gates_tool/validation/dwa1/final
```

Each `final/gates.json` records the exact input hashes, config, runner hash, per-clip sample times and timings.
`suite.json` records process wall time, including Blender startup, separately from the runner timer.
Files named `before_fixes*` and earlier `report/` directories are development evidence, not the final result.
The scratch configs demonstrate the intent fields with provisional region definitions. They are not approved
production presets and are not installed into the actively edited projects.
The final edit added one guard: an empty head sample/obstacle region must report UNVERIFIED. A regression
tests that case; all 56 validation meshes were checked to have nonempty head regions and targets, so this guard
does not change their measured results. The exact two-line difference and both code hashes are recorded in
[`guard_receipt.json`](../../../../output/codex_batch/gates_tool/guard_receipt.json). The final code passes the
12 tests and 99-pose independent Blender comparison again. Timed reports retain their original code hash.

Blender 5.2.2 LTS, Linux, AMD Ryzen 9 5950X, `--threads 4`, OpenBLAS/OMP limited to four threads.
Runs are sequential. Other production sessions share the host, so these are observed timings, not an isolated
hardware benchmark. No render, texture import or game startup is included in the gate runner.

## Input identity and timing

<!-- timing-table -->
| Input snapshot | Body hash | Clips | Colour LOD triangles | Runner / wall seconds | Verdict |
|---|---|---:|---|---:|---|
| [Dwarf current](../../../../output/codex_batch/gates_tool/validation/dwa1/final/gates.md) | `a5f8a244baa1` | 8 | 11563 / 5938 / 2091 / 629 | 69.0 / 71.4 | FAIL |
| [Archer current](../../../../output/codex_batch/gates_tool/validation/arc1/final/gates.md) | `e56663a91bff` | 8 | 9531 / 9531 / 8579 / 10058 | 260.1 / 263.4 | FAIL |
| [Monk current](../../../../output/codex_batch/gates_tool/validation/mnk1/final/gates.md) | `837f171e365d` | 9 | 12364 / 9272 / 8654 / 8035 | 150.7 / 153.2 | FAIL |
| [FighterChain current](../../../../output/codex_batch/gates_tool/validation/figc/final/gates.md) | `296072967399` | 8 | 10340 / 10340 / 10076 / 9562 | 407.4 / 409.7 | FAIL |
| [Archer handoff](../../../../output/codex_batch/gates_tool/validation/arc1_handoff/final/gates.md) | `7360aaf76501` | 8 | 10588 / 5291 / 1904 / 627 | 134.5 / 138.7 | FAIL |
| [Monk pre-repair control](../../../../output/codex_batch/gates_tool/validation/mnk1_handoff/final/gates.md) | `2652dd6cde30` | 9 | 12427 / 6212 / 2235 / 744 | 116.8 / 119.6 | FAIL |
| [FighterChain handoff](../../../../output/codex_batch/gates_tool/validation/figc_handoff/final/gates.md) | `52a7298d6d3d` | 8 | 11511 / 5754 / 2067 / 685 | 130.1 / 133.5 | FAIL |

Timed numeric runner SHA-256: `3b4146873a11149a98a5e20f9dd7409251f367be735382f9e9e78764d549213e`. Final runner SHA-256: `e42a1f060b03d1ad311729fc9f2ed2e5b3948a8e83f38c6c244e33ceeb21616c`; see the guard-only validation note above.
<!-- /timing-table -->

The approximately five-minute target is met by three of the four current snapshots and every archived reduced
chain. **Current FighterChain takes 407 seconds and misses the target**: its colour chain stays near 10k triangles
at every level, and its modified shadow meshes require separate checks. The matching reduced handoff takes
130 seconds. This is a measured performance limit, not an assertion that all possible exports finish in five minutes.
Static LOD failure does not skip the expensive checks; a full run still produces the requested clip/LOD evidence.

Dwarf and Monk exports match the copied handoffs. Archer and FighterChain were already being revised:
the current-export checks therefore cannot be compared directly with older handoff numbers. Additional archived
exports resolve that mismatch:

- Archer: `mm6_arc1_codex/review/round2/baseline/export/`, matching the round-1 handoff body, bow and arrow hashes.
- FighterChain: `mm6_figc_codex/review/round2/before/export/`, matching the handoff's round-1 replacement body/axe.
  The handoff repeats the same G4/G5 numbers in its later round-2 section.
- Monk: `mm6_mnk1_codex/review/round3/before/export/` is an extra **pre-repair** control. It does not represent the
  round-3 handoff; the current `837f171e…` export does.

Full hashes are in the machine reports. These frozen copies matter: rereading an active `export/` later can give
a different model even when its filename has not changed.

## Handoff comparisons

<!-- comparison-table -->
| Matching handoff/export | Handoff G4 p99 | Runner G4 p99 | Handoff G5 max | Runner G5 max |
|---|---:|---:|---:|---:|
| Dwarf current | 1.96 | 1.955616 | 2.818 | 2.817813 |
| Archer handoff | 1.67 | 1.665557 | 2.132 | 2.131809 |
| Monk current | 1.915050 | 1.959659 | 2.680344 | 2.680344 |
| FighterChain handoff | 1.4948 | 1.494815 | 2.4189 | 2.418829 |
<!-- /comparison-table -->

G4 means the worst **per-side** arm p99 for Dwarf, Archer and Monk, and the **pooled** arm p99 for FighterChain,
matching their own reporting conventions. The configs explicitly reproduce the older arm-weight selectors;
the shared report also retains the other convention. G5 is the maximum hand/finger edge ratio on colour LOD0.
The complete reports separately evaluate every other LOD; this table does not substitute LOD0 for those gates.

### What agrees, and why other numbers differ

- **Dwarf:** its 1.96 G4, 2.818 G5, zero arm/exposed-head contact and 1.34110450745e-7 weight error reproduce.
  The configured 0.71875 s blow also reproduces. The stricter new per-digit surface test finds a 4.643 mm middle
  finger gap; the handoff preserved accepted grip frames and checked shaft clearance, which is not the same as
  proving every digit within 3 mm. This is new evidence, not proof that the older numeric result was calculated
  incorrectly. The tunic has branched boundaries after seam welding: this runner refuses to invent a closed
  containment volume, while the old script tested triangle crossings. That is an unresolved coverage difference.
- **Archer:** G5 reproduces to the handoff's precision. Compare the archived body to the archived handoff; the
  current body has different geometry/animation. The original grip test used 45 barycentric
  points per hand triangle and a cylindrical penetration proxy; this runner uses seven points and the actual prop
  triangle surface. The old handoff's grip-envelope statement therefore is not a comparable per-digit certificate.
  Its quiver sign test accepted three of four forward rays; this runner requires a majority of opposite ray pairs
  for open surfaces. A different head maximum under that definition is not evidence of broken skinning.
  Its short puff sleeves use collision mode. An initial long-sleeve containment config falsely demanded that a
  bent-back exposed hand, far from the garment, be inside it; the garment's intended coverage selects the mode.
- **Monk:** G5 and the 0.2965° elbow-plane maximum reproduce. The original dense G4 was measured on the authoring
  mesh, whose edge multiplicities differ from the exported UV-split mesh. The runtime audit retains exported edges.
  A separate 60 Hz probe measured 1.959935 on exported edges versus 1.914031 after deduplicating physical edges,
  explaining the handoff's 1.915050. See
  [`stretch_definition_probe.json`](../../../../output/codex_batch/gates_tool/validation/stretch_definition_probe.json).
  Its old cloth result was explicitly measured on the selected Blender master, with separately tagged cuff faces,
  permission to be inside either sleeve during crossed-arm motion, and a local hem rule. It was not repeated on
  every simplified runtime LOD. The scratch runtime sleeve selector and exit plane are not an identical volume;
  their failures cannot honestly be labelled a defect in either deformation evaluator. The owner's exact cloth
  region definitions remain necessary before replacing that evidence.
- **FighterChain:** pooled G4 reproduces 1.4948; per-side p99 is larger and is also reported. G5 differs only at the
  last reported decimal because of the sampling grid and runtime arithmetic. Its props intentionally release
  during Death at authored frame 26/30 s; the config tests grip up to release, and excludes Dead from held-hand
  checks. An earlier all-clip-held config falsely reported metre-scale gaps. The correction is explicit intent,
  not an inferred distance cutoff. Head comparison uses the two pauldron components rather than every torso face.
  The resulting head maximum is 4.983582 mm versus 4.9838 mm reported. The old prop test also exempted the gripping
  hand **after release**: at Death 0.916667 s the shared audit finds 14.652682 mm of axe penetration against three
  vertices weighted entirely to the right hand. Restoring the old exemption returns zero. This is a concrete
  coverage bug in the legacy contact script; see
  [`release_contact_probe.json`](../../../../output/codex_batch/gates_tool/validation/release_contact_probe.json).

The current Archer and FighterChain snapshots contain equal/increasing colour LOD counts. Those are actual
failures of the requested strictly-decreasing chain, not a gate-runner discrepancy. Monk's chain decreases but
exceeds the default approximate ratio budgets; the handoff itself records those counts. Ratios can be overridden
with the owner's accepted switch-size evidence. No previous-count caps were supplied for these observational runs.

Source checks reviewed include the batch projects lch, figc, kni, mnk1, sor1, arc1, dwa1, lzd, jak1 and min1,
plus the bar1/gob2 Claude rig gates, timing and grip solvers. The runtime loader, animation sampler and
`output/codex_batch/check_weights.py` were read to establish runtime semantics. No reference-engine code was copied.

## Tests and runner corrections

Twelve regression tests pass. They cover normalized/strided/sparse accessors and malformed bounds, shortest-path
runtime quaternion interpolation, STEP and rejected CUBICSPLINE, hierarchy/nonzero starts, wrapped roll and jitter,
closed and capped signed distance, animated opening planes, open-sheet false positives, all-LOD skinning,
raw weight/material rejection, strict LODs and previous-count caps, skin-aware seam welding, forward region
references, adaptive timestamps, time-weighted support, two-handed surface contact/release and report semantics.

An independent Blender import/armature-modifier comparison checks **99 poses across all clips of all four current
bodies**, including fractional times. Maximum position differences are:

| Body | Maximum error |
|---|---:|
| Dwarf | 0.000767 mm |
| Archer | 0.000781 mm |
| Monk | 0.000896 mm |
| FighterChain | 0.000923 mm |

Evidence: [`tests/tests.json`](../../../../output/codex_batch/gates_tool/tests/tests.json) and
[`tests_final.log`](../../../../output/codex_batch/gates_tool/tests_final.log).

Validation caught and corrected these runner issues:

1. Spherical quaternion interpolation did not match the runtime's normalized linear interpolation.
2. Float32 endpoints created near-duplicate adaptive timestamps; grids now start with Python double precision.
3. One-direction open-surface parity misclassified empty space facing a patch as penetration. Dwarf's spurious
   133 mm head result became zero after requiring opposite-ray agreement. The isolated open-sheet regression
   protects this correction. Open meshes still do not define mathematical solids.
4. Float32 weight summation obscured the exact raw error; validation now sums in double precision.
5. Position-only welding could join vertices that move differently; skin influences now participate in topology.
6. Named region references depended on JSON key order; dependency resolution now rejects unknown/cyclic references.
7. Grip caching must include hand geometry, weights, inverse binds and prop surface identity. FighterChain's altered
   shadow LOD positions cannot share evidence just because their counts match.
8. Grazing BVH hits at the archived Archer's double-sided quiver could lie behind the ray origin or repeatedly
   hit the same face. Rays advance monotonically; repeated-face/long traversals are resolved with vectorized
   double-precision triangle intersections. Regressions cover both cases and shared-edge intersection deduplication.

## Remaining limits

This tool supplies the shared numeric implementation. Production owners still have to provide correct cloth
regions/openings, prop grip surfaces/release intervals and posture limits. Missing required intent remains
UNVERIFIED and returns exit code 2. These validation configs deliberately do not invent per-clip posture approvals
or old source-relative G6 limits, so the final creature verdicts are not PASS.

Open-surface sign is an estimate; vertex/barycentric sampling is not exhaustive triangle-intersection or continuous
collision certification. A plane is an approximation for a strongly folded hem. Seven grip samples per triangle
can overestimate a small gap relative to the older 45-point test. Two-handed behavior has a synthetic regression;
the four production validation creatures do not include a two-handed weapon. Silhouette/SSIM, native luminance,
library provenance, artistic review, viewer and game/binding checks remain separate, as documented in README.md.

Everything was written only under the shared gate directory and the authorized scratch directory. No commit was
made. The repository currently ignores `/level_generation/`, so later version-control inclusion needs an explicit
decision by the owner; this task did not change ignore rules or stage files.
