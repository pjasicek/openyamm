# MM9 see-through linings on installed bodies (orchestrator, 2026-11-05)

User decision 2026-11-05 ("do what you recommend"): line the four bodies with the worst see-through openings in the
2026-11-02 sweep (`level_generation/creatures/claude_shared/mm9_overview/holes_sweep_20261102.png`); leave HOM1/HOM2 as
they are (trousers 62 px in one clip, the rest at most 26 px).

| Model | Installed source | Creature project | Worst openings (sweep, px at 4 mm) | Note |
|---|---|---|---|---|
| Bjarni | `mm9_bjarni.glb` | `mm9_bjarni_claude` | torso 2,542 (Death), collar 810, sleeves 649 / 628 (Running), boots 46 / 40 | after his reduction (row 78) is installed or kept |
| Sven | `mm9_sven.glb` | `mm9_sven_claude` | torso 2,529 (Death), sleeves 118 / 99, head 77 | reduction kept (row 75) |
| Tryggva | `mm9_tryggva.glb` | `mm9_tryggva_claude` | sleeves 590 / 502 (Fidget, AttackMelee), torso 406, head 42 | reduction kept (row 74) |
| PeasantM1 | `mm9_peasantm1.glb` | `mm9_peasantm1_claude` | torso 255 (Death), sleeve R 152, collar 95, sleeve L 65, head 63 | added by the user 2026-11-05; installed LOD0 is the reduced e80 (row 89) |
| PeasantM1d | `mm9_pm1d.glb` | `mm9_peasantm1d_claude` | torso 762 (Death), boots 273 / 251 (Running), trousers 122 / 108 | installed LOD0 is the reduced one (row 82, `mm9_pm1d_reduce_claude/`) |

## Route
- Project `level_generation/creatures/mm9_<name>_lining_claude/`; copy the installed source (`assets_source/worlds/mm9/models/`)
  to `before/` first (rollback). Lease `mm9lining:<name>` via `tools/creature_workspace.py claim`; check `mm9:<name>` and
  `mm9reduce:<name>` are free.
- Start from the **installed GLB**, not the creature's master blend (a rebuild from the master would undo PeasantM1d's reduction
  and change approved clips). Add lining faces only: every existing vertex, UV, normal, weight, texture, tier variant and clip stays
  byte-identical; new lining vertices copy the skin weights of the rim/outer vertex they line.
- Methods that already work: PeasantDM2 `mm9_peasantdm2_claude/scripts/{linings.sh,rim_lining.py,neck_cap.py}` (rim bands,
  neck cap, one-texel lining paint per region, skip the cloth's own inner layer, inner offset 0.5 mm), Hanndl
  `mm9_hanndl_claude/README.md` step 5c, the reductions' GLB-level lining re-emission (`mm9_hanndl_reduce_claude/scripts/`,
  `mm9_clansoldier_reduce_claude/`: exact reversed copies of the outer faces), PeasantM1d's own `v2/scripts/sleeve_lining.py`.
- Lining texel: a dark texel of the garment's own paint (inside of the cloth), per tier if tiers differ; never a new texture.
- LODs: LOD1-3 rebuilt with the snap-fixed builder (`mm9_lesserdemon_reduce_claude/scripts/build_lods.py`) or the linings
  carried into the existing LODs; shadow LODs drop the one-texel lining triangles (DM2's `shrink_shadow_lods.py`); winding
  fix as pm1d's `fix_winding.py`.
- Budget: line only the openings the gate shows; expect a few hundred to about a thousand LOD0 triangles (Hanndl: 662).

## Gates (installed -> lined; the creature's own scripts where it has them)
- `see_through_gate.py` (DM2's, every clip): the target is every zone's maximum at or below about 20 px, and no zone worse.
- Lining poke: no lining face visible from outside in any clip (`lining_gate.py` from the reductions; dark specks on the cloth
  were DM2's failure mode). Arm/hand gate, sleeve poke, jitter, detached parts: equal to installed.
- `level_generation/creatures/claude_shared/reduction_uv_audit.py <candidate> before/<file>` = 0 LOD0 escaping faces;
  `check_winding.py` 0; LOD heights/floor contact equal by number.
- Read your own sheets at full size: face diff (black), full body, close-ups of every lined opening from outside (cuffs,
  collar, boot tops, hem) and the worst sweep views of each zone before/after.

## Rules
AGENTS.md / CLAUDE.md apply: no git add/commit/stash/reset; no `game/`/`engine/` edits; no engine or game builds; no Meshy, no
repaint. Every Blender/heavy Python job under `systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0`, one Blender
per agent, `--threads 4`. Wait on your own PIDs (`kill -0`). Do not install: the orchestrator pre-screens ("looks the same
from outside, holes closed") and installs with `tools/install_model.py`, then appends the post-install note to the creature
README and runs the binding regression. Skip the binding regression yourself.

## Final report (short)
Before/after LOD0 and LOD1-3, openings lined, see-through per zone before/after, other gates, sheets read (absolute paths),
candidate path, what to look at, what you did not check. Write the same into the project's `README.md`.
