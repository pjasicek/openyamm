# Shared MM6 creature gates

This is the single numeric gate implementation for the Codex humanoid batch. It reads the exported runtime body,
all `openyamm_lods` and `openyamm_shadow_lods`, every animation, and separately exported attachments. It never opens
an authoring `.blend`, repairs an asset, takes a creature lease, installs content, launches the game, or renders.

## Using the shared gate runner

From the repository root:

```sh
level_generation/creatures/claude_shared/gates/run_gates.sh \
  level_generation/creatures/mm6_example_codex/export/mm6_example.glb \
  --config level_generation/creatures/mm6_example_codex/gates.json \
  --out output/codex_batch/example_gates
```

The creature's owner maintains the small **JSON** config beside the project. This tooling task does not write
configs into other sessions' directories. Start with [example.gates.json](example.gates.json); its coordinates
are examples, not a preset that fits every creature. Paths to props are relative to the config. `BLENDER` can
select an executable. The wrapper always uses background mode, factory startup, disabled autoexec and four threads.

Read `gates.md` for the verdict, then the failing clip/LOD/region rows. `gates.json` contains the same results,
input SHA-256 hashes, the effective config, defaults, sample times, timings, and diagnostic vertex/edge indices.
Each row records the worst value, its time, `frame_48hz = time_s * 48`, threshold and comparison. Frame numbers
are **audit frames**, not frames in an authoring file. Clip time is the GLB timeline, including a nonzero start.
Contact percentages describe the whole clip and therefore have no single worst frame. Finger contact reports
the **worst over time of each digit's nearest surface contact**, not the farthest point on its back.
Diagnostic `edge` indices address the decoded mesh; `sample_vertex` indexes the selected contact sample region.

Exit code 0 means PASS. Exit code 2 means FAIL, UNVERIFIED or ERROR; the report distinguishes them. Missing
regions, unsupported input and absent required intent never turn into a pass. `N/A` is an inapplicable semantic
check; `INFO` is a measurement without an acceptance threshold. A numeric pass is not artistic acceptance.

The [config reference](#creature-config) below lists fields and units. Blender 5.2.2 and its bundled NumPy were
used for validation; no extra Python packages are needed.

## Creature config

Required intent:

- `props`: attachment `file`, `node`, `name`, `kind`, held `hands`, grip surface and, for cutting weapons, the signed
  `edge_axis`. Use `[]` for an unarmed creature. Two-handed weapons have two hand entries, with separate grip
  surface bounds and grip centres where needed. `clips` defaults to all clips; narrow it for a released prop.
  Each hand can declare `intervals: {"Death": [[0,0.8666667]], "Dead": []}` when a prop is released mid-clip.
  Times are seconds; omitted clips remain held throughout. Release stops grip/palm checks and restores that
  hand to the prop/body collision target. The dropped prop is still tested against the body.
- `cloth`: named containment checks with a `surface` region, `samples` region and allowed `opening.axis`.
  Use `[]` when no separate sleeve/robe/skirt volume needs containment. Solid armour is handled by body contact.
- An `edge_axis` parallel to the grip-to-tip axis denotes an axial thrust. Its flat-versus-edge check is N/A;
  signed tip-leading motion, target direction, peak speed and impact timing are still checked.
- `posture`: optional per-clip `pelvis_min_m`, `pelvis_max_m`, `trunk_lean_deg` limits. Without them posture is
  measured and UNVERIFIED. `"*"` supplies common limits; set Death/Dead separately.

Optional intent and overrides:

| Field | Meaning |
|---|---|
| `version` | Currently 1. |
| `clips.rest`, `.walk`, `.run`, `.attack` | Case-sensitive glob lists; defaults Standing/Fidget, Walking, Running, Attack*/Cast. Every animation is still sampled. |
| `bones` | Map canonical `B_*` names to exported joint names. |
| `hands.L`, `.R` | Hand-local `palm_axis`, upper-arm-local `elbow_hinge_axis`, finger roots ordered thumb first, then index to pinky. Configure `palm_axis` explicitly for hands with fewer or more than five digits. |
| `regions` | Named vertex selectors; override inferred `arm_L/R`, `hand_L/R`, `limb_L/R`, `leg_L/R`, `foot_L/R`, `head`; optional `head_obstacles`. |
| `lod_regions` | Region overrides keyed by `colour0`…`colour3`, `shadow0`…`shadow3`; useful for explicit vertex IDs. |
| `thresholds` | Override the named defaults below, in their stated units. Unknown names are errors. |
| `clip_thresholds` | Same threshold dictionary, keyed by exact clip name. |
| `source_rotation_limits` | Per-clip `arms`/`hands` maximum step at 48 Hz; G6 uses these numbers +10°. No source file is needed at runtime. |
| `previous_counts` | `{ "body": {"colour": [n0,n1,n2,n3], "shadow": [...]}, "axe": {"colour": [...]}}`. |
| `floor_m` | Ground in model metres, default 0. Binding example: `-z_offset / scale`. |
| `forward` | Z-up model forward, default `[0,-1,0]`; used for in-place travel and the attack target direction. |
| `gait_scale` | Multiply walking lift limits for deliberate non-human scale; default 1. |
| `sole_band_m` | Bind-space foot vertices within this distance of the lowest foot-weighted vertex; default .005 m. |
| `refine_hz` | 48 (default), 96 or 192, only in intervals marked for refinement. |

A selector is a region name or an object. Fields intersect: `weights` (bone globs), `weight_min` (default .3),
`bounds` (`[[minX,minY,minZ],[maxX,maxY,maxZ]]`), `materials` (name globs), `component_seeds` (points near the desired
connected pieces), `vertices` (explicit indices), and `exclude` (another selector). Bounds and seeds use the
undeformed runtime mesh in **Z-up metres**. Weight selectors sum all matching influences, including WEIGHTS_1.
Connectivity welds identical exported positions and skin influences; coincident pieces with different animation
remain separate. Region selectors are checked independently on every LOD; empty
regions are reported, never silently borrowed from LOD0. Prefer weights or connected-piece seeds to vertex IDs.

Cloth surfaces must form manifold shells whose boundary loops can be capped for an inside/outside test. The loop
farthest along `opening.axis` is the permitted opening (e.g. `[0,0,-1]` for a hem); `opening.loop_seed` chooses the
loop nearest a specific bind-space point when the shell has other holes. The posed loop defines the exit
plane. Samples on its outward side may exit; all other outside samples count as penetration. A surface with a
branched boundary or no selected triangles is UNVERIFIED. `cloth: []` is an explicit statement of applicability,
not a way to hide a failed cloth check.

`containment` defaults to `true`: limbs are expected inside a robe/long sleeve until its opening. Set it to `false`
for limbs normally outside a short sleeve that must not enter its fabric volume. Both modes allow the opening's
outward side; collision mode prevents the false claim that a bent-back hand far away from a short sleeve must
somehow be inside that sleeve. Choose the mode from the garment's intended coverage, not from a desired verdict.

A modelled sleeve can have a sealed end instead of an exported boundary loop. For that case, declare
`opening: {"node": "B_R_Forearm", "point": [x,y,z], "axis": [x,y,z]}`: point and outward normal use that node's
encoded local coordinates, and the plane follows its animation. This is required intent, not an automatically
invented wrist clearance. Prefer a real boundary loop when available.

For props, `grip_surface` uses the same selectors in the standalone prop's Z-up coordinates. Per-hand `surface`
overrides it. `grip_point`, `tip` and `edge_axis` are in the **attachment node's encoded local coordinate frame**,
not model/world coordinates. Optional `impacts: {"Attack": 0.71875}` checks binding timing. The default tip is the
farthest actual prop vertex from the grip centre, measured separately at each LOD; set `tip` for an asymmetric
weapon where that is not the striking point. A zero-scale attachment is hidden, matching released arrows.

## Measurements and defaults

The batch rules provide some exact limits and several qualitative requirements. This table makes the remaining
choices explicit instead of attributing invented numbers to the batch rules. All entries are config-overridable.

| Gate | Default | Basis |
|---|---:|---|
| Skin sum error | ≤ 1e-4 | Batch requirement; stricter than the older check_weights.py implementation's 1e-3. |
| Elbow hyperextension / maximum flexion / out-of-plane | 5° / 150° / 5° | Batch + sor1 anatomical gate. Source-frame hinge is local -Z, not the fitted A-pose kink. |
| Forearm roll / wrist flexion / wrist roll | 90° / 70° / 45° | sor1 arm-motion gate. |
| Upper-arm roll | 60° | Playbook's 40–60° guidance; explicit default. |
| Roll step / G6 rotation step | 35° / 25° per 1/48 s | sor1 step limit; Claude G6's fallback 15+10°. Source limits override G6. |
| Angular acceleration | 20,000°/s² | sor1 gate; world-space rotation-vector velocity differences. |
| Free palm / grip palm | ≤36.87° / ≤60° | Free palm dot ≥.8 from arc1; grip facing cone is a shared default. |
| Mean held-finger curl | ≥10° | Minimal closed-hand check; surface contact is the stronger test. |
| Arm p99 / maximum stretch | 2× / 4.5× | G4 p99 from playbook; maximum is an explicit conservative default. |
| Hand p99 / maximum stretch | 4.5× / 4.5× | G5 limit; p99 retained alongside max. |
| Floor penetration / rest heel & toe / sole tilt | 2 mm / 10 mm / 3° | Batch rest limit and dwa1 locomotion gates. |
| Running contact / maximum flight height | ≥80% / ≤40 mm | dwa1 gate, contact means either sole ≤10 mm. |
| Walking lowest-sole peak / knee at peak | 80–120 mm / 40–60° | Batch gait criteria. Heel/toe peaks also reported. |
| Foot yaw | ≤10° | Batch. Root travel is inferred when the clip translates; otherwise uses configured forward. |
| Body / cloth / head penetration | 2 / 2 / 10 mm | Claude G6 and arc1. Monk's stricter .01 mm cloth tolerance can be configured. |
| Grip gap / penetration | 3 / 3 mm | Batch and arc1 surface-contact gate. |
| Blow pointing cone / fraction of peak speed / time error | 70° / .8 / 1/48 s | Explicit shared defaults for the qualitative timing rule. |
| Blade edge share / signed lead | ≥.7 / ≥0 | Edge-versus-flat share at the selected blow; signed direction rejects a reversed cutting edge. |
| LOD ratios | ≤.55 / .25 / .10 | Batch guidance, enforced as defaults alongside strict decrease. |

Bone gates use 48 Hz, including clip endpoints. Wrapped roll is unwrapped before differencing: 179°→−179° is a
2° turn, not a 358° flip; an actual 160° jump fails. Acceleration uses the actual interval length, including a short
last interval. G6 covers arms, hands, fingers, twist helpers and configured attachment nodes.

Meshes start at 24 Hz. Both intervals neighbouring a sample within 20% of a threshold are refined to 48 Hz (or the
configured finer rate). Contact crossings are also refined. Running contact percentage integrates elapsed time,
so extra samples near a threshold cannot bias the percentage. Every region's p99/max and worst edge are retained.
G4 includes upper-arm, forearm, twist and hand-bone weights above .3; G5 includes hand and finger weights above .3.
Both per-side and pooled percentiles are reported. Override regions when comparing a legacy gate's different mask.
Soles use an SVD plane and fore/aft heel/toe patches. Bone evidence is shared across LODs but appears on every LOD
row. Identical colour/shadow geometry at the same level shares mesh results, with provenance in JSON.

The evaluator reads GLB accessors, node hierarchy, inverse binds and all skin influence sets directly. It mirrors
`engine/models/ModelAnimation.cpp`'s shortest-path normalized quaternion interpolation and the loader's weight
normalization. STEP is supported; runtime-rejected CUBICSPLINE, morph animation and unsupported primitives produce
ERROR. This avoids texture import and repeated depsgraph work altogether. [test_gates.py](test_gates.py) checks the
result against Blender's independent importer and armature modifier at keyed and fractional times.

BVHs are built once per posed surface, reused for all its queries, with vectorized array transforms, broad-phase
culling, edge distances and reductions. Rigid grip BVHs are built once per LOD for the whole run. Blender's BVH
nearest/ray calls themselves expose a scalar API. Grip distance uses exact triangle surfaces and samples vertices,
edge midpoints and triangle interiors. No cylinder or bone-distance proxy substitutes for the grip mesh.

Closed surfaces use nearest distance signed by ray parity. Open body/armour patches use a nearest-normal cone and
majority of three **opposite ray pairs** on the hit connected component. Both directions must have odd parity;
this rejects empty space facing an open patch, which fooled the older one-direction tests. This is an
**estimate on open surfaces**, not a mathematical solid signed distance. Cloth must pass the closed/capped volume
setup; it never falls back to an open-surface sign test.
Grazing or repeated BVH hits are resolved with vectorized double-precision triangle intersections, deduplicating
shared-edge hits. They are neither silently counted repeatedly nor discarded as zero penetration.

## Tests and validation

```sh
blender -b --factory-startup --disable-autoexec --threads 4 --python-exit-code 2 \
  --python level_generation/creatures/claude_shared/gates/test_gates.py -- \
  --out output/codex_batch/gates_tool/tests \
  --glb level_generation/creatures/mm6_dwa1_codex/export/mm6_dwa1.glb
```

Repeat `--glb` for additional bodies in the same Blender process. Tests write only below `--out`. The validation
record and timings are in [VALIDATION.md](VALIDATION.md). Snapshots, full reports and logs live below
`output/codex_batch/gates_tool/`; those snapshots prevent active production sessions from changing a measurement
halfway through a comparison. Normal runs also recheck each input hash at the end.

## Limits

- Sampling is not a continuous collision proof. Refinement can miss a narrow violation whose neighbouring coarse
  samples are far from every threshold. Increase `refine_hz` for a suspicious near-threshold clip; a visual review
  remains necessary.
- Open-surface sign estimates, overlapping solids, non-manifold cloth and strongly non-planar hem openings require
  review or more precise region definitions. An average opening plane does not model a deeply folded hem exactly.
- Mesh contact samples can miss a triangle/triangle crossing with no sampled interior point inside. This runner
  does not claim exhaustive surface-intersection certification.
- Attachment configs describe the batch's rigid, single-mesh-node prop files and their colour LOD chains;
  separately animated/skinned prop files and independent prop shadow chains are outside the validated format.
- Palm sign and hinge axes assume the shared source-frame rig. Custom hand frames need explicit signed axes;
  bone names alone cannot establish artistic/anatomical intent. Generic head selection can include intentionally
  buried neck/beard geometry: configure the exposed `head` and `head_obstacles` regions where necessary.
- Triangle ratios and previous caps do not prove silhouette/SSIM preservation. Native skin luminance, library clip
  provenance, material appearance, wind-up quality, clip sheets, viewer checks and actors.yml bindings remain
  separate production evidence. No game checks or builds are part of this tool.
