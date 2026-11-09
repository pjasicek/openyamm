# MM9 Rooster (`mm9_rooster`) reduction: kept (no useful gain), 2026-11-05

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md), ledger row 95 of
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:rooster` (owner rooster-reduce-20261105, released); `mm9:rooster`
was free. Source: the installed `assets_source/worlds/mm9/models/mm9_rooster.glb` (sha256 59c9bfcaf209, identical to
`../mm9_rooster_claude/export/mm9_rooster.glb`), copied to `before/`. `../mm9_rooster_claude/` was only read. No Meshy, no credits.
**Nothing exported or installed; the installed rooster stays as it is (6,930 / 3,465 / 1,245 / 408).**

## Body already cut at the build
`../mm9_rooster_claude/scripts/reduce_body.py ... 0.3 0.35 0.5` decimated the body at the build. 69 components: the main body
2,468 faces (median edge 20 mm; head skin 13 mm), the grafted comb 658, wattles 178 + 176, eyes, and about 60 open sickle-feather
sheets on the tail chain (XtailB/C/E about 3,100 faces, 20-31 mm edges). The feather sheets are single open sheets: 2,136 of the
4,575 welded vertices lie on open edges and stay locked in a half-edge collapse.

## Protected share (`scripts/animal_sets.py`, HEAD_BONES Xhead,Xbeak,beaknode; feet Xfoot/Xtoe*/Xtoepiv*)
| set | exact | share | free | -15 % (1,040 tris) needs |
|---|---|---:|---:|---:|
| a: every separate piece (comb, wattles, eyes, tail feathers), head-weighted skin > 0.5 + 2 rings, feet + 1 ring, soles 2 cm | 5,607 | 80.9 % | 1,323 | 79 % of the free faces |
| b: as a but the tail feather sheets free (head pieces stay exact through their Xhead weight) | 2,663 | **38.4 %** | 4,267 | **24 %** (but only 1,108 movable vertices: about 47 % of the removable capacity) |

## One ladder (set b, `scripts/mpqem.py`: the Ram/Dog pose-aware collapse, chart guard 12, texture guard on the base colour;
limits for the 0.732 m GLB height p99 <= 2.20 mm, max <= 10.98 mm; `work/selection_b.json`, `review/ladder_sheet_b.png`)
| step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---:|---|---|---|
| r80 | 6,076 (-12.3 %) | 3.19 / 9.56 (Death:15) | .9933 / .9923 | fail |
| r75 | 5,862 (-15.4 %) | 4.64 / 19.32 (Death2:15) | .9897 / .9892 | fail |
| r70 | 5,708 (-17.6 %) | 7.42 / 29.16 (Death:21) | .9758 / .9823 | fail |
Error at r80 (`err_by_bone.py`, 2.44 % of samples over 2.2 mm): tail feathers XtailC 0.95 %, Xtail 0.47 %, XtailE 0.21 %, and the body
(Xbody 0.21 %, neck, thighs). The feather sheets are already coarse (one or two interior rows) and fan in every clip; keeping them
exact returns to set a (79 % needed). Nothing at or above -15 % passes (not even -12 %): **kept (no useful gain)**. One ladder used.

## Files
`scripts/` (Dog copies made generic: `animal_sets.py` survey + sets from env HEAD_BONES/FOOT_BONES, `mpqem.py` node from env NODE
with guard images `work/tex_<material>_*.png`, `tex_extract.py`, `run_mp.sh` with env GLB, `ledger_row.py --key`), `work/`
(source.blend, mesh_in.npz, sets, ladder), `review/` (ladder sheet), `before/mm9_rooster.glb`.
Rerun: `GLB=mm9_rooster.glb NODE=Rooster SETS=b REA_HEIGHT_M=0.732 MP_GROUPS= scripts/run_mp.sh b 0.8,0.75,0.7` after
`import_source.py` (REA_NODE=Rooster), `dump_mesh.py`, `tex_extract.py before/mm9_rooster.glb` and `SMALL_FREE=1 animal_sets.py
before/mm9_rooster.glb Rooster b`.
