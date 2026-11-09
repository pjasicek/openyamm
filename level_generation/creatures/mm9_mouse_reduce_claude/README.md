# MM9 Mouse (`mm9_mouse`) reduction: kept (no useful gain), 2026-11-05

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md), ledger row 110 of
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Leases `mm9reduce:mouse` and `mm9:mouse` (owner mouse-reduce-20261105, both
released; the stale `claude-mouse-fish` lease had been released by the orchestrator). Source: the installed
`assets_source/worlds/mm9/models/mm9_mouse.glb` (sha256 efb1dd8cde28, identical to `../mm9_mouse_claude/export/mm9_mouse.glb`),
copied to `before/`. `../mm9_mouse_claude/` was only read. No Meshy, no credits, no Blender.
**Nothing exported or installed; the installed mouse stays as it is (4,735 / 2,367 / 852 / 282).**

## Already cut at the build
`../mm9_mouse_claude/scripts/reduce_mouse.py` decimated the mesh at the build with the head denser: body (Bone05) edges 5.1 mm,
tail 3.8-7.8 mm, the head (Bone08) 2.6 mm and the snout (Bone06) 1.5 mm, paws 1.6-2.1 mm; eyes are two 168-face beads.
The MM9 head bones own 2,155 of the 4,735 faces (46 %).

## Protected share (`scripts/animal_sets.py`, HEAD_BONES Bone08, Bone06; feet LegFL/FR/HL/HR; `work/survey.txt`)
| set | exact | share | free | -15 % (710 tris) needs |
|---|---:|---:|---:|---:|
| **a: eye beads, head-weighted skin > 0.5 (cranium, ears, snout, whisker pad, nose) + 2 rings, paws + 1 ring, soles 3 mm** | 3,759 | **79.4 %** | 976 | **73 % of the free faces** |
| head + 1 ring, soles 3 mm | 3,647 | 77.0 % | 1,088 | 65 % |
| head without ring, soles 3 mm | 3,531 | 74.6 % | 1,204 | 59 % |
| head + 2 rings, no soles | 3,282 | 69.3 % | 1,453 | 49 % |
| loosest: head without ring, paws + 1 ring, no soles at all | 3,046 | 64.3 % | 1,689 | 42 % |

The soles band is large (1,205 faces within 3 mm) because the mouse is 4.8 cm tall, its belly hugs the floor and the tail lies on
it. Even the loosest set, which drops the head rings and every floor-contact face, needs 42 % of the free faces, above the ~40 %
stop limit (for comparison the Cat needed 48 % and passed only -6.3 %, the Pig 48 %: kept); the free part is the thin tail tube
and the 5 mm body, where a 50-70 % cut would show. **Kept (no useful gain)** without a ladder, as the read-only screen expected.

## Files
`scripts/animal_sets.py` (generic, from `../mm9_goose_reduce_claude/`), `work/survey.txt`, `work/survey_a.txt`,
`work/glb_sets_a.npz`, `before/mm9_mouse.glb`.
