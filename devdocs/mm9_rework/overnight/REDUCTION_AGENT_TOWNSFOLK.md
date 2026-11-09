# MM9 townsfolk reduction: standing agent brief (orchestrator, 2026-11-04)

The orchestrator hands each agent one ledger row (or one family of rows sharing a body) plus this file. Everything here applies;
the assignment message names the GLB(s), ledger row(s), creature project and lease names.

Read first, fully: [REDUCTION_BRIEF_20261104.md](REDUCTION_BRIEF_20261104.md) (route, keep sets, gates, UV-chart audit hard gate,
review/install rules) and [RUN2_COMMON.md](RUN2_COMMON.md). AGENTS.md / CLAUDE.md apply: no git add/commit/stash/reset/restore
--staged; no `game/` or `engine/` edits; no engine or game builds; safe deletes only; kill only PIDs you started, never parents.
Read the creature's own README (gates it ran, tiers, head set, see-through/sleeve fixes, how variants are built).

## Reference projects (installed 2026-11-04)
- `level_generation/creatures/mm9_peasantf3_reduce_claude/` (−18.8 %): pose-aware `scripts/mpqem.py` with the chart guard sampled
  at 12, texture guard over every tier, texture weight 4, hands 0.6 with every finger kept, head/veil/braids/skirt lining exact,
  `lining_gate.py`, `gates.sh`, `see_through.sh`. Start from its scripts.
- `mm9_peasantf7_reduce_claude/` (−30.6 %), `mm9_monk_reduce_claude/` (−29 %, robe linings with one ring kept),
  `mm9_clansoldier_reduce_claude/` (linings rebuilt as exact reversed copies of the surviving outer faces; contact keep sets for
  hands-on-body and skirt-on-thigh), `mm9_dwarf_reduce_claude/` (dwarf proportions, −25 %), `mm9_skeleton_reduce_claude/` (the
  audit's own chart test inside each collapse when the guard alone lets faces land on another island).

## Rules
- Families: GLBs that share a body mesh are reduced once and every variant re-derived from that cut; heads stay exact.
- Project `level_generation/creatures/mm9_<name>_reduce_claude/`; copy each installed source to `before/` first (rollback). Helpers
  and temp files inside the project, never the session scratchpad.
- Lease `mm9reduce:<name>` via `python3 tools/creature_workspace.py claim`; check `mm9:<name>` is free; release at the end.
- Ledger: your rows to "reducing (<name>-reduce-<date>)" at the start and "ready for review" with counts at the end; only your rows,
  inside `flock level_generation/creatures/claude_shared/locks/reduction_ledger.lock`, re-read inside the lock, split columns on
  `'|'` (not `' | '`), temp file + `os.replace`.
- Face skin, ears and neck seam exact. Hair shells 0.6–0.8, hands 0.6–0.75 with every finger. No Meshy, no repaint: UVs, textures,
  tier variants, clips byte-identical. Animals: the head (eyes, muzzle, beak, ears) exact the same way.
- Memory: every Blender or heavy Python job under `systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0`, one Blender
  at a time, `--threads 4`.
- Hard gate per GLB: `level_generation/creatures/claude_shared/reduction_uv_audit.py <candidate> before/<file> --json
  review/uv_audit_<variant>.json` = 0 LOD0 escaping faces in every node.
- LODs via the snap-fixed builder (`mm9_lesserdemon_reduce_claude/scripts/build_lods.py`); verify LOD heights and floor contact by
  number.
- Review server already runs at http://127.0.0.1:8912/ (do not start or kill it; at most 2 viewer shot scripts at once).
  Side-by-side reduction viewer (installed vs reduced, every tier of every GLB); pass the viewer check.
- Skip the actor binding regression; the orchestrator runs it after install.
- Read your own sheets at full size: face sheet (front close-up, 3/4, true profile, low 3/4, party) every tier with a diff; full
  body front/3-4/back; close-ups of hands/fingertips, sleeves/cuffs, hem and painted details.
- If no step saves ~15 %, record "kept (no useful gain)" with the numbers and stop. Do NOT install.

## Final report (short)
Per GLB before/after LOD0 and LOD1–3, picked step and why, UV audit result, gates before/after, sheets read (absolute paths),
viewer URL, candidate paths, what to look at, what you did not check.
