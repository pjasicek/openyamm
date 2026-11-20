# MM9 Pig (`mm9_pig`) reduction: kept (no useful gain), 2026-11-05

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md), ledger row 100 of
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:pig` (owner pig-reduce-20261105, released); `mm9:pig` was free.
Source: the installed `assets_source/worlds/mm9/models/mm9_pig.glb` (sha256 7ed146da5f37, identical to
`../mm9_pig_claude/export/mm9_pig.glb`), copied to `before/`. `../mm9_pig_claude/` was only read. No Meshy, no credits, no Blender.
**Nothing exported or installed; the installed pig stays as it is (6,018 / 3,008 / 1,082 / 360).**

## Body already cut at the build
`../mm9_pig_claude/scripts/reduce_body.py 0.3 0.6 0.45` decimated the body at the build with the head denser (head charts x2):
body edges 20-43 mm, legs 12-24 mm, hooves 7-8 mm, the head 10 mm and the snout (Xnose, 1,860 faces with the two 272-face eye
pieces) 2-4 mm. The MM9 head bones own half of the mesh. Behind the ear roots (z < 0.16) there are only 4 head-weighted faces, so
there is no cuttable head-weighted neck like the Cow's (`work/survey_a.txt`).

## Protected share (`scripts/animal_sets.py`, HEAD_BONES Xhead, Xnose, EarRoot*, Xearpiv*, Xear*; feet Xbkfoot*, Xftfoot*)
| set | exact | share | free | -15 % (903 tris) needs |
|---|---|---:|---:|---:|
| a: eye pieces, head-weighted skin > 0.5 (cranium, eyes, snout, nostrils, ears) + 2 rings, hooves + 1 ring, soles 2 cm | 4,134 | **68.7 %** | 1,884 | **48 % of the free faces** |
| a1: as a, 1 ring | 4,056 | 67.4 % | 1,962 | 46 % |
Above the ~40 % stop limit; for comparison the Cat needed 48 % and its ladder passed only -6.3 %, the Dog 45 % (-5.0 %).
**Kept (no useful gain)** without a ladder.

## Files
`scripts/animal_sets.py` (generic, from `../mm9_rooster_reduce_claude/`), `work/survey_a.txt`, `work/glb_sets_*.npz`,
`before/mm9_pig.glb`.
