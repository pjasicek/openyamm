# MM7 session 03 restoration review

Current result: **8 families with complete accepted native coverage, 957/957 canonical bitmaps**. Seven families are complete under the latest outline method. Chain has **20/23 latest-method returns plus 15 reviewed older generated frames** covering its three failed jobs, reused under the user's explicit 2026-10-03 instruction. The latest-method run remains **181/184 returned sheets**; reuse does not turn a failed generation into a successful outline return. Every current pose has 100% material/alpha evidence, independent native placement review and all-palette/material-mask review.

| Family | Current merged IDs | Latest outline returns | Native bitmaps | Status | Lowest actual sampling |
| --- | --- | --- | --- | --- | --- |
| [Elf Archer A](../mm7_m214/redo_2x/review/acceptance.json) | 247–249 | 23/23 | 120/120 | Accepted, frozen | 2.02113× |
| [Elf Spearman A](../mm7_m218/redo_2x/review/acceptance.json) | 250–252 | 23/23 | 119/119 | Accepted, frozen | 2.17518× |
| [Fighter Chain A](../mm7_m222/redo_2x/review/acceptance.json) | 253–255 | 20/23; 3 older groups reused | 124/124 | Accepted with reviewed older art | 1.74879× |
| [Fighter Leather A](../mm7_m226/redo_2x/review/acceptance.json) | 256–258 | 23/23 | 120/120 | Accepted, frozen | 2.08163× |
| [Fighter Plate A](../mm7_m230/redo_2x/review/acceptance.json) | 259–261 | 23/23 | 114/114 | Accepted, frozen | 2.27632× |
| [Gargoyle A](../mm7_m234/redo_2x/review/acceptance.json) | 262–264 | 23/23 | 124/124 | Accepted, frozen | 1.77934× |
| [Genie A](../mm7_m238/redo_2x/review/acceptance.json) | 265–267 | 23/23 | 112/112 | Accepted, frozen | 2.36364× |
| [Ghost A](../mm7_m242/redo_2x/review/acceptance.json) | 268–270 | 23/23 | 124/124 | Accepted, frozen | 2.26415× |

Each selected latest-method return contains every native frame of its submitted animation/view in one sheet. Inputs are untouched native colour/alpha, a separate matching outline-only geometry guide and same-family appearance art. Source union crops, padding, optimized grids, attempts and prompt provenance remain in each `redo_2x/run.json`. Native animation/descriptor metadata, timing, stored views, mirrors, aliases and exact fractional placement are preserved. Genie includes the five unused `m238wf0`–`m238wf4` bitmaps without introducing them into playback. All native palettes are exported.

All masters and atlas placement use a **physical 2× export**. Actual generated sampling is measured separately and conservatively: the Gargoyle front walking sheet has a reviewed **1.77934×** minimum, and the new Chain profile attack has **1.74879×**. Both complete cycles passed anatomy, detail, palette and alpha review. They were retained under the whole-animation priority rule. No sheet was split or regenerated solely for a sampling shortfall.

Within each family, `redo_2x/aligned_2x/` contains the physical masters; `redo_2x/atlas/` contains base and shared material-mask atlases; palette atlases are in `redo_2x/previews/`. `redo_2x/manifest.json`, `registration.json`, `variants.json` and `validation.json` record exact export and native contracts. `redo_2x/review/acceptance.json` pins the current evidence and artifact hashes. Placement edits translate entire poses; scales are shared across a sheet. The Archer hair/feather selections were reprojected with the corrected pose placement.

## Previous prompts and older-art reuse

The earlier accepted Archer and Chain projects were found and their original successful prompts/raw hashes verified. Seven user-requested attempts reused those prompts with the required MM7 context, current complete animation/view grid, separate outline-only guide and genuine transparency. Four returned: Archer corpse, Chain profile attack, rear-oblique hit and corpse. Exact archived successful prompts and adapted submissions are in each family's `redo_2x/prompts/` and `run.json`.

Three Chain attempts remained moderation blocked: `standing_3_sheet` (one frame), `attack_4_sheet` (eight frames) and `hit_4_sheet` (six frames). Their [original and fresh failure records](../mm7_m222/blocked_jobs.json), prompts and request IDs remain preserved; no further generation was attempted.

Following the user's instruction to check older 2× restorations after failures, all fifteen matching frames were found in the unchanged accepted `level_generation/creatures/mm7_m222/` package. All **389 previous acceptance artifact hashes** match. Its whole back attack/hit sheets and multi-view standing sheet provide **2.03856×–3.11803×** generated detail. Their original-resolution cleaned masters and physical 2× exports were copied into the current Chain staging, preserving alpha, visible pixels, shared historical scales and pose placement. Current native contracts, every reused pose, all palettes and alpha edges were reviewed again. Fresh sleeve/waist support envelopes protect tinted equipment edges from clothing recolouring while preserving all artwork and hair coverage.

[Reuse provenance](../mm7_m222/redo_2x/legacy_reuse/provenance.json) identifies the original accepted package, raw sheets, exact prompts, source/master hashes and reused native frames. The earlier latest-method partial records are archived there. Chain's acceptance is `accepted_with_reviewed_legacy_reuse`, with `latest_method_complete: false`; the three failures are retained. Native frame coverage is complete, with no substituted native bitmap or omitted playback step.

## Shared reviewer

[Open the shared reviewer](http://127.0.0.1:8873/) for all eight staged packages. The unchanged shared server loads the hash-pinned [collection](review_collection.json). Restart from the repository root:

```sh
/tmp/openyamm-creature-restore-venv/bin/python -B level_generation/creatures/mm6_remaining/acceptance_viewer/serve.py \
  --collection level_generation/creatures/mm7_mm8_packed_outline/session_mm7_03/mm7_m214/review_collection.json \
  --port 8873
```

[Reviewer check](review_state/server_check.json) verifies all eight packages and representative native/base/mask/palette endpoints, plus shared UI assets. The recorded art review is static; watched browser playback is not claimed.

[Session status](session_status.json) is the machine-readable coverage report. Final validation checked unchanged source and palette hashes, exact untouched native sheet cells, outline-only guides, complete-cycle policy, original descriptor bindings/flags/timing/aliases, fractional anchors and atlas/mask extraction. Work is staged only in the eight requested family directories; original projects, shared tools/skills, global ledgers and runtime assets were not changed by this session. Nothing was installed into gameplay.
