# Test subjects (assigned by openyamm-b9, 2026-11-11)

Untouched by the MM6-MM8 audit texture pass and wanted redone later, so a winning paint can be adopted by b9.
Read only: start from the installed GLB (it carries reductions, floor fixes and the 2026-10-31 gait clips), copy it
into this folder first. Claim a lease while working and release it when done:
`python3 tools/creature_workspace.py claim --project level_generation/creatures/uv_research_20261111
--state partuv/<model>/creature_3d_progress.json --identity <id> --owner uv-research` (a sub-folder project is
refused; this lease locks the whole research folder, so hold it in short windows, one subject at a time).

| # | Model | Identity | Installed GLB | Project (read only) | Now |
|---|---|---|---|---|---|
| 1 | Bedraggled Human (humanoid, Meshy paint + head set) | mm8:m620 | `assets_source/worlds/mm8/models/mm8_m620.glb` | `mm8_m620_claude/` (references_hd 00-04) | atlas 33.7 %, fragments 9.9 %, stretch p90 2.19 |
| 2 | BHydra (non-humanoid, heads a separate texture set) | mm6:hyd | `assets_source/worlds/mm6/models/mm6_hyd.glb` | `mm6_hyd_claude/`, `mm6_hyd_reduce_claude/` | atlas 42.9 %, fragments 24.5 % |
| 3 | PeasantM3 (optional humanoid, staff) | mm6:mep | `assets_source/worlds/mm6/models/mm6_mep.glb` | `mm6_mep_codex/` | atlas 33.7 %, fragments 15.0 % |

Do not touch: `assets_source/`, `assets_dev/`, any `actors.yml`, production project folders (read only),
`audit_mm678_20261111/` (read `fixes/LEDGER_texpass.md` freely), and the running Merchant (mm6:mer1),
Werewolf (mm6:wwf) and Titan (mm6:ttn) work.

Toolkit pointers from b9: `mm6_demon_texpass_claude/scripts/` (tp_compose.py with detail_clip; tp_apply.py LOD and
shadow handling), detail_guard in `mm7_m218_texpass_claude/scripts/compose.py`, `claude_shared/uv_atlas.py` now
reverts charts SLIM collapsed to a point. Lesson from 66 passes: fresh 4K paints often change faces and designed
patterns, so always compare against the installed paint.

Credits: backup Meshy account has 580 left (expire 30 Nov); this study may use 100. When finished, send openyamm-b9
a short summary with the winning method and per-model numbers.
