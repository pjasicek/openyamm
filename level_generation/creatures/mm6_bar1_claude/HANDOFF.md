## Running clip swap 2026-10-13

**Historical: Jogging rejected by the user on 2026-10-13; superseded by Standard Run below.**

Staged **Running only**, sourced from Mixamo `Jogging.fbx` through the project's Mixamo retarget path.
27 keys at 30 fps; exact first/last pose; **1.86 m run stride** (unchanged 1.2 × engine 1.55).
Both masters, the final GLB, LOD0 export and three review-viewer GLBs contain the replacement.
All other clip keys, geometry, textures, sword and bindings compare unchanged.

- G4: p99 **1.38×**, max **1.96×**. G5 hand stretch: **2.91× R / 1.85× L**; solved grip unchanged.
- G6: **0 mm** arm/body and actual sword/body contact at full detail.
- Contact **97.596%**, flight **12.424 mm**, floor penetration **0 mm**, torso lean **12.39°**.
- Binding check: exit **0**, no BAD. Viewer: **24/24** switches, zero errors.
- Full shared runner: **FAIL**, retaining inherited grip/coarse-LOD findings; no new failure categories.
  All **5,619** non-Running result rows match the accepted baseline. Details in
  [TEST_DRIVE.md](TEST_DRIVE.md#running-clip-swap-2026-10-13) and
  [gate report](review/runswap_20261013/gates/gates.md).

Review: [running sheet](review/runswap_20261013/running_review.png), [viewer](review/viewer/index.html).
Backup: `work/pre_runswap_20261013/`.

Final `export/mm6_bar1.glb` SHA-256:
`aeb96ef8b33ad883112f56b81946417f4b752c5a1cd17a8a519f4d66c77068f5`

Nothing installed; no game launches/builds or commit. Next: user review of the staged Running clip.

## Running clip: Standard Run

**Superseded by Review round 2 below: user rejected the low pelvis/crouched stance in image #95.**

Replaced the rejected Jogging clip with **Mixamo `Standard Run.fbx`** (`mx/standard_run_f8c60f`),
retargeted through the project's Mixamo path. Stronger arm swing, forward lean, longer stride,
toe-down recovery and a low brief flight; sword swings clear with the arm. Solved grip unchanged.

**2.015 m stride**, 22 intervals at 30 fps; exact loop endpoints. Staged stride **1.2 → 1.3** for
Barbarian A/B/C. Full-detail contact **88.636%**, flight **11.364%** above the 10 mm contact band,
maximum flight height **13.836 mm**. Pelvis/head jitter checks pass; symmetric pelvis bob.
G4 p99/max **1.35×/2.04×**, G5 hands **2.91× R / 1.61× L**, G6 and actual sword/body contact **0**.

Bindings: **PASS, no BAD**. Viewer: **24/24**, zero errors. Shared runner: **FAIL** with inherited
palm/grip and coarse-LOD findings (16 FAIL, 9 UNVERIFIED); **no new failure categories**. See
[gate report](review/runswap2_20261013/gates/gates.md) and [detailed record](TEST_DRIVE.md#running-clip-standard-run--review-round-1-2026-10-13).

[Running sheet: front, side, three-quarter](review/runswap2_20261013/running_review.png).
[Review viewer](review/viewer/index.html). User acceptance of this replacement is pending.

## Review round 1

Only Running keys changed in both masters, runtime/LOD0 export and three viewer models. All other
clip keys, geometry, textures, sword and bindings compare identical except the explicitly staged
stride adjustment. Because the binding is shared, Walking's distance-driven cadence will also use
1.3; its clip keys are unchanged. No installed files changed.

| File | New SHA-256 prefix | Triangles (unchanged) |
| --- | --- | --- |
| `work/rig_v5.blend` | `f8d7ade766a9b4be` | Mesh data identical |
| `work/rig_v6.blend` | `14dd3553494528cd` | Mesh data identical |
| `export/mm6_bar1.glb` | `4810e5fad20a9ed1` | 10,117 / 5,084 / 1,812 / 578; same shadow LODs |
| `export/mm6_bar1_lod0.glb` | `4da76ac76f521684` | 10,465 |
| `review/viewer/mm6_bar1_a.glb` | `b18c78b43d2a4a21` | 10,465 |
| `review/viewer/mm6_bar1_b.glb` | `059379525ecde309` | 10,465 |
| `review/viewer/mm6_bar1_c.glb` | `d7a590a6fea38a0d` | 10,465 |
| `integration/actors.yml` | `cf9a67d4a9b22e67` | — |

Sword remains **348 / 144 / 47 / 23** triangles; SHA-256
`553712fdb2f53f917bd687226b24ead39496d12cada0105843b31dc11c19e20f`.
Final body SHA-256: **`4810e5fad20a9ed11885ee1a46ccc7ece438139a47abdb5f02ad723a44ed8abe`**.
[Full before/after hashes and triangle receipt](review/runswap2_20261013/artifact_receipt.json).

Supporting changes: `scripts/swap_running.py`, `scripts/rebuild.sh`, `scripts/running_jitter.py`,
viewer manifest, this handoff, TEST_DRIVE, project progress and `review/runswap2_20261013/` evidence.
Backup: `work/pre_runswap2_20261013/`. **integration/actors.yml changed only stride_length** in
three entries. No assets_dev writes, game launches/builds or commit; **0 credits spent**.

## Review round 2

Fixed image #95's crouch in **Running only**: removed the 19 cm hip drop, adapted Standard Run's
own vertical profile around Standing height, shortened stride to **1.600 m**, and fitted brief
flight between individual stances. Arm/sword swing and the accepted grip are retained.

- Pelvis minimum **92.100%**, mean **93.568%** of Standing; smooth **30.664 mm** bob.
- Contact **38.352% L / 38.068% R**, total **76.420%**; flight **23.580%**, max **42.798 mm**.
- Runtime stance drift **0.207 / 0.212 mm**; 89 export samples at 120 Hz, unchanged 0.733333 s duration,
  exact loop endpoints. Source-based recovery, forward toes, upright trunk.
- Posture, flight, floor, arm/sword clearance and pelvis/head jitter pass. G4 **1.35× p99 / 2.04× max**,
  G5 hands **2.91× / 1.61×**, G6 **0 contacts**. Bindings **PASS, no BAD**; viewer **24/24**, zero errors.
- Shared runner remains **FAIL (17 FAIL, 9 UNVERIFIED)** for palm/grip and coarse-LOD foot findings.
  Shadow LOD2 contact is newly flagged at **56.818%** with this pose; its mesh is unchanged.
  [Full report](review/runswap3_20261013/gates/gates.md), [measurements](review/runswap3_20261013/gait.json).

[New running sheet: front, side, three-quarter](review/runswap3_20261013/running_review.png).
[Viewer](review/viewer/index.html). **New user acceptance is pending.**

**integration/actors.yml changed only stride_length** for Barbarian A/B/C:
**1.3 → 1.032258064516129** (×1.55 = 1.600 m). Walking's keys remain identical; its cadence also
uses this shared binding. All other clip keys, mesh/weights, textures, skeleton, sword and bindings
compare unchanged. Nothing installed.

| File | New SHA-256 prefix | Triangles (unchanged) |
| --- | --- | --- |
| `work/rig_v5.blend` | `7cd1501c94c0dc3a` | Mesh data identical |
| `work/rig_v6.blend` | `4f74c19d719d038d` | Mesh data identical |
| `export/mm6_bar1.glb` | `9003969a9f845f90` | 10,117 / 5,084 / 1,812 / 578; same shadow LODs |
| `export/mm6_bar1_lod0.glb` | `2c852f99a9421af8` | 10,465 |
| `review/viewer/mm6_bar1_a.glb` | `2ab32c7aabef442a` | 10,465 |
| `review/viewer/mm6_bar1_b.glb` | `b46893570f1f1b09` | 10,465 |
| `review/viewer/mm6_bar1_c.glb` | `5f2246bb2b289526` | 10,465 |
| `integration/actors.yml` | `1d4e353f302325f8` | — |

Sword unchanged: **348 / 144 / 47 / 23** triangles, SHA-256
`553712fdb2f53f917bd687226b24ead39496d12cada0105843b31dc11c19e20f`.
Final body SHA-256: **`9003969a9f845f90acba05a20255dfb5f3ec810e65f922c97d76e9a87e9b2681`**.
[Full before/after hash and triangle receipt](review/runswap3_20261013/artifact_receipt.json).

Supporting updates: `scripts/swap_running.py`, `scripts/export_running.py`, `scripts/running_gait.py`,
`scripts/running_jitter.py`, `gates_runswap.json` (user-directed Running thresholds), viewer manifest,
TEST_DRIVE, README and project progress. Backup: `work/pre_runswap3_20261013/`.
No assets_dev writes, game launches/builds or commit; **0 credits spent**.
