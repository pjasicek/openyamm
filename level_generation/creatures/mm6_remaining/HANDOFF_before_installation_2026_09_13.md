# MM6 creature restoration — completed staging handoff

## Status — 2026-09-13

All **60 of 60 MM6 native actor families are validated**, with zero pending, partial or blocked families. The refreshed [inventory](../remaining_inventory.json) reports zero remaining native or referenced MM6 image names. [progress.json](progress.json) links every accepted package. [coverage_audit.json](coverage_audit.json) verifies every recorded source name against those packages, including retained unused poses and empty endpoints. Existing accepted packages were reused.

Everything is staged under `level_generation/creatures/`. Originals and gameplay were not changed. No further restoration-generation work is pending for this MM6 scope. Any later runtime installation must separately check the declared material/recolor contracts and native blend/lighting behavior.

## Final blocker resolution

Earth Elemental's last missing sheet, six right-profile walking poses, succeeded on the **first attempt** of the user's latest five-attempt budget. Only one request was used. The exact plain restoration prompt, input references and service result are retained in [retry_3_2026_09_13.json](retry_3_2026_09_13.json) and `../mm6_ert/prompts/retry_3_2026_09_13/`. Earlier failures remain historical records; the service did not establish their precise cause.

Earth now covers all 59 unique images, including unused `ertfib0`. Final review also corrected its preliminary linear palette mapping: native luminance LUTs restore the green and grey variants' deep shadows. See [Earth review notes](../mm6_ert/review_notes.md) and [offline viewer](../mm6_ert/review.html). Final source/hash/coverage/placement/atlas/alpha and visual checks passed. No additional generation is needed.

The earlier two clearer-prompt rounds completed Genie and Fire. Genie review repaired omitted late-death jewelry and finger-gap matte residue. Fire review repaired flattened core shadows and flame-edge variant leakage. Exact prompts, accepted outputs, rejected checkpoints and processing settings remain in each project; aggregate earlier results are in `retry_2026_09_13.json` and `retry_2_2026_09_13.json`.

## Maintenance and reproduction

Use the creature-restore and imagegen skills plus the sprite atlas/variants and direct sprite workflow documents for any future requested revisions. Open each family's README and review notes first; family package wrappers declare special material contracts. Reprocessing or repacking resets visual acceptance and requires re-review and updated acceptance hashes. Do not overwrite accepted checkpoints or silently install them.

After accepting a future change, refresh with:

```sh
python3 level_generation/creatures/inventory_remaining.py
python3 level_generation/creatures/mm6_remaining/prepare.py ledger
```

Recheck source-name coverage and update `coverage_audit.json`. A manifest's existence alone is insufficient. Review includes all-frame contacts, original/variant comparisons, material overlays, sequence and selected-pose placement checks, and contour inspection; these offline checks do not establish real-GPU performance.

## Retained special decisions

Cactus has 89 source names / 76 unique images. Its last three nonempty decay endpoints (261, 25 and 2 pixels) are exact native 2x; two source names share a genuinely empty image. The other 72 unique images are AI restored. Palette 955 lives in engine/terrain; source names are uppercase `mCAC` and Center anchored. Never fill the native empty endpoints.

Hydra uses an RGB displacement LUT plus R8 mask for its differently colored heads. Genie uses skin/jewel luminance LUTs plus RGBA masks. Fire and Earth use one R8 material mask and native luminance LUTs. Runtime support is separate from the completed asset-staging scope.

The temporary disk-space issue and historical image-generation rejections are resolved. The previous checkpoint handoff is retained as `HANDOFF_before_earth_acceptance_2026_09_13.md`; its old blocker descriptions are not current status.

## Subsequent ground-origin audit — 2026-09-13

[Ground-origin review](ground_anchor_review/README.md) measured all 3,481 frame names and found no broad anchor drift. It identified a small 1–2.5 native-pixel lift in 31 reused goblin front frame names; deterministic registration correction is recommended before full installation. The original restoration acceptance remains recorded, but this later alignment finding is open. Cactus center anchoring also needs explicit runtime integration handling. This audit changed no art or gameplay.
