# v11 —1302 exact-pose diagonal repair

Scope: only `drsrne1/2`, `drsrnw1/2`, and four grey counterparts. All28 other road textures, including every straight tile, are locked by `protected_straights.json` and remain unchanged.

Reference: Dagger Wound Island, position(7766.500,3508.695,545), yaw1.782, pitch-26.385 degrees. All review captures use that pose. `mm8_1302_before` is installed v10, `material` is the calibration-only candidate, `fitted` is a rejected endpoint-strip candidate, and `exact_repair` is the final local-patch candidate.

Final build: run `build.py`, then `repair_exact_join.py`. Material calibration removes exaggerated bright grain from diagonal stone faces and introduces restrained detail sampled inside an actual accepted straight-road stone. Existing geometry, mortar and native coverage guide the operation. The generated local crop repairs the NE2 east connection visible at this camera; only its diagonal half is inserted. The straight half and all outer boundary pixels remain fixed. The grey counterpart receives the same stone repair over its own substrate.

Two built-in imagegen calls were made. The broad pair edit (`raw/rejected_pair.png`, `prompt.txt`) was not used because it changed the material inconsistently. The focused joint crop (`raw/exact_join.png`, `join_prompt.txt`) supplies the final local repair. Inputs and prompts are retained. `fit_connections.py` is a rejected experiment and must not run over the final output.

Focused evidence: `join_comparison.png`, `captures/mm8_1302_exact_repair.png` and `visual_review.json`. No broad gallery, ZIP or historical completion-audit rebuild; those remain prior snapshots. The installed assets and export are updated after review.
