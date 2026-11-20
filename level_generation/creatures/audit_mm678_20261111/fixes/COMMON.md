# MM6–MM8 audit fixes: rules for every stream (2026-11-11)

The user approved, on 2026-11-11, fixing what the [audit](../README.md) found. There are four streams, each with its
own brief and ledger here:

| Stream | Brief | Ledger |
|---|---|---|
| Texture pass (three agents, one shared queue) | [TEXPASS.md](TEXPASS.md) | `LEDGER_texpass.md` |
| Clip and weight fixes, then the blandest attacks | [ANIM.md](ANIM.md) | `LEDGER_anim.md` |
| Rebuilds (PeasantF1, lizardman peasant, Merchant, Thief, Guard, Werewolf, Titan's hands) | [REBUILD.md](REBUILD.md) | `LEDGER_rebuild.md` |
| Blandest attacks re-animated from donors (two agents) | [ANIM.md](ANIM.md), part 4 | `LEDGER_attacks.md` |

Read the audit README, this file and your brief before starting. After a context compaction or a restart, re-read
them and your ledger, then resume. The ledger is the only memory that survives.

## Ownership: one lease per installed GLB

- Before you touch a model, claim it:
  `python3 tools/creature_workspace.py claim --project <your project dir> --identity <world>:<id> --owner <stream>-<agent>`.
  The identity is the installed file's stem: `mm6_gob2.glb` → `mm6:gob2`, `mm8_lizardman_peasant.glb` →
  `mm8:lizardman_peasant`, `mm7_7m500.glb` → `mm7:7m500`. Every stream uses this same identity, so two streams can
  never install the same GLB at once. Release the claim (`release --project ... --token ...`) when the model is
  installed and checked.
- **If a claim fails, another agent owns the model.** Skip it, take the next item, and come back later. Never break
  someone else's lease. One exception: `mm7:m182` (2026-10-21) and `mm8:m532` (2026-10-18) are stale leases from
  October. The stream that needs one may release it using the token in its JSON
  (`output/creature_3d_locks/<identity>.json`).
- MM7 copies of MM8 GLBs share one layout: m390 = m552, m434 = m560, m210 = m500, m461 = m480. Claim both
  identities, and rebuild the MM7 copy with its own palettes as its project README describes.
- Mark the item `in progress (<agent>)` in your ledger when you claim it, and `done` or `skipped: <reason>` when you
  release it.

## Starting point and changes

- Start from the **installed** GLB at claim time: `assets_source/worlds/<w>/models/<stem>.glb`. Never start from an
  old project export; installed files carry reductions, far-LOD repairs, head-bob reshaping, floor fixes and the
  2026-10-31 gait clips. Check `sha256sum` against `assets_dev` (runtime vs source memory note).
- Change only what your stream owns:
  - Texture pass: UVs, images and region ramps.
  - Animation: clips and weights, plus `actors.yml` clip names and event times where a clip is replaced.
  - Rebuild: everything for its models.
  Before install, diff the result against the claimed GLB (`mm8_m480_texpass_claude/scripts/glb_diff.py`) and
  explain every difference you did not intend.
- Back up the claimed GLB and the `actors.yml` entries to `<project>/work/before_<stream>/` before installing, so one
  copy reverts it.
- Work in a project folder per model and stream: `<stem>_texpass_claude`, `<stem>_animfix_claude`, or
  `<stem>_rebuild_claude`. Blender runs through `tools/run_creature_blender.sh`. Meshy runs only through
  `tools/creature_meshy.py`, which uses the backup account.
- Do not use the Blender MCP tools (`mcp__blender__*`). They drive one shared, live Blender session, so parallel
  agents would overwrite each other's scenes. Use headless Blender only. If a problem can only be solved
  interactively, write it as a BLOCKED row and the coordinator will take it.

## Install and checks (every model)

1. `level_generation/decorations/mm8_3d/animated/scripts/check_winding.py <glb>` must report 0 inverted closed parts.
2. Install with `tools/install_model.py <export.glb> --world <w>`, never by copying.
3. Re-measure with the audit tools. For motion:
   `python3 level_generation/creatures/claude_shared/motion_audit.py <installed glb> --out <project>/audit_after`.
   For textures: `texture_quality.py`. Record before and after numbers in your ledger. `motion_frames.py --highlight`
   shows bad triangles in red.
4. Floor (`claude_shared/floor/floor_audit.py --world <w> --match '<descriptor>'`) and, for any change to walk, run
   or stride, `postprocess/gait_audit.py`.
5. Regression, built through the shared lock:
   `flock -x level_generation/projects/mm9r_common/locks/cmake_build.lock cmake --build build --target openyamm -j16`
   (build only when game code changed; usually it has not), then
   `OPENYAMM_REGRESSION_FILTER=mm6_mm7_mm8_actor_models_build_every_binding ./build/game/openyamm --world mm6 --headless-run-regression-suite actors`.
   It must pass. Then run the model's own cases in the full actors suite: `grep -n '<stem or creature name>'
   game/outdoor/HeadlessOutdoorDiagnostics.cpp` finds them. Simplest is to run the whole suite (no
   `OPENYAMM_REGRESSION_FILTER`). On 2026-11-11 three models passed every_binding but failed their own cases (clip
   names, lengths, release timing). Wait about 20 s after an install before running it: run straight after an install, the regression
   failed a few bindings that passed on a re-run (seen four times on 2026-11-11). A failure that a re-run clears was
   not caused by your model.
6. Viewer: `python3 tools/run_creature_review.py --project <p> check` must show no console errors. Look at the
   viewer shots yourself before calling a model done; viewer shots are the acceptance, Blender renders are not.
   For humanoids, run the arm and hand gate from the humanoid playbook on every changed clip.

## Limits

- **CPU is the shared constraint** (eight agents from 16:10). At most two Blender processes per agent at a time,
  four threads each (`-t 4`), and only one heavy job per agent (a bake, a simulation, a brute-force pack) at a time. No `-j25` builds. No game or Vulkan builds unless game code changed.
- **Meshy credits** (backup account, 1,640 on 2026-11-11, monthly credits lost on 2026-11-30). Caps:
  - texture pass 900, both agents together;
  - rebuilds 600;
  - animation 100.
  Run `tools/creature_meshy.py balance` before each paid job, and write the credits spent per model in the ledger.
  Check `anim_library` (`meshy_anim_library.py check`) before buying any animation, and `ingest` every paid result.
- **Codex image workers** (HD masters, painted views): at most 16 parallel sessions across all streams, through
  `codex exec`.
- Do not `git add`, `commit`, `stash` or `reset`.
- `assets_dev` files are hard links: never edit them in place. Use the install tool.
- Never kill a process you did not start, and never kill a parent pid.
- Keep project READMEs current: add a dated section per change, with numbers, sheet paths and what was checked.
- Do not ask the user mid-stream. Decide within these rules and record the decision. Stop and write
  `BLOCKED: <question>` in your ledger only for a real blocker; for example, a change that would visibly alter a
  creature's identity beyond what your brief allows.
