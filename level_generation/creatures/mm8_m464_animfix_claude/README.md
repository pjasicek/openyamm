# Vampire Female Peasant (mm8_m464): anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md), part 3. Before:
`work/before_anim/mm8_m464.glb` and `work/before_anim/actors_*.yml` (one copy reverts it).

## Running: the loop seam jumped

**Audit:** Running's last key differed from its first by 0.0776 H (several times a normal frame step), so the loop popped
at every wrap. **Cause:** 11 rotation channels end off their start values (upper arms 15° and 12°, forearms and hand 3–7°). **Fix:**
`../audit_mm678_20261111/fixes/anim_tools/loop_close.py work/before_anim/mm8_m464.glb export/mm8_m464.glb --clips Running`:
each such channel's end-to-start difference is spread linearly over the whole loop (a left-multiplied correction), so
the last key lands on the first; nothing else changes.

Result: loop pop 0.0776 -> 0.0 H; region bad shares unchanged within 0.4 (`review/finish.txt`); hands inside the body
0 %. Checks: winding 0; only Running samplers changed; floor and gait audits clean (strides untouched); every-binding
regression PASS; viewer check clean. Arm and hand gate: the arm channels move at most the seam angle spread over the
loop (no new contact, no deformation change).
