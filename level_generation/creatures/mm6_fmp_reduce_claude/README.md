# MM6 PeasantF2 (fmp) reduction (2026-10-14)

User: "3D tris count reduction playbook - do mm6_fmp". Texture-aware reduction of the installed
`assets_source/worlds/mm6/models/mm6_fmp.glb` (Codex delivery `../mm6_fmp_codex/`, 9,902 triangles, 64 skirt bones,
head and body sets merged in one 2080x1024 atlas), [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) no-rebuild
branch, no retexture, no credits. Limits scaled to the 1.804 m height: p99 5.41 mm, max 27.06 mm.

**Candidate: `export/mm6_fmp_kr77.glb`, 7,622 triangles** (LODs 3,810 / 1,371 / 457, variants A/B/C on every LOD
and shadow mesh, open edges 702 = source). **Installed 2026-10-14** (user: "accepted") as
`assets_source/worlds/mm6/models/mm6_fmp.glb`; previous source in `work/mm6_fmp_source_pre_reduce.glb`.

## Ladders

| config | kept exactly | group ratios | pass (tris) | first fail |
|---|---|---|---|---|
| uniform (`reduce_installed.sh`) | nothing | | none | r70 6,930: max 29.7 mm, skirt in Death |
| a | face skin, pieces <= 80 faces | hair+cap+eyes 0.6, hands 0.45, feet 0.5 | r75 7,424 | r70: skirt in Death |
| s3 | as a | hair+cap+eyes 0.5, hands 0.4, feet 0.45, **skirt 0.8** | r70 6,928 | r68: one waist vertex in Death:36 |
| h / hc / hr / hp | + eyeballs, + cap, + hair at the cap rim, + painted hair | hair 0.7 | r74-r76 | |
| **k** | **whole head set** (4,297) | hands 0.4, feet 0.45, skirt 0.8 | **r77 7,622** | r76: same waist vertex |
| kl | k + 2 rings around the Death error vertices | feet 0.35 | none | the lock drains the torso budget |

Findings (`review/close/`, `review/pose/`):
- The 16x4 skirt chains spread apart in Death; at a uniform cut the hem misses the source by 30-59 mm. Skirt-weighted
  faces need their own 80 % budget.
- s3 at 70 %: blue flecks along the cap rim and skin specks in the ponytail. The hair hidden under the cap is
  painted cap-blue, and the hairline/temples and the ponytail's cut end are painted skin; any cut there pushes
  that paint into view (`scripts/hair_blue.py` finds those faces). Keeping the cap, the rim hair and the painted
  hair faces cleared the cap and temples, but one skin fleck stayed at the nape. The rest of the hair would only
  save ~100 triangles, so the whole head set is kept, as in the accepted female peasant (`mm6_pfem_reduce_claude/`).
- Torso, arms, bodice and apron (1,798 faces) are already lean: below ~64 % of them, p99 rises fast and one waist
  vertex in the Death kneel exceeds the max limit.
- Hands at 40 % and shoes at 45 % are indistinguishable from the source in the close renders (shoes are mostly under
  the dress). Texture drift: no face over the threshold (`texture_drift.py r77`).

## Review

- Close renders `review/close/sheet_{whole,head,hand}.png` (top installed, bottom kr77).
- Posed `review/pose/sheet_{Death12,Death36,Dead0,Run6}.png` (worst ladder frames): identical silhouettes. The
  open hem and the leg through the skirt in Run are in the source too.
- Viewer `review/viewer/` (installed `r100` vs `kr77`, every variant and clip): `check_viewer.mjs` 42 loads, no errors.

## Rebuild

```
python3 scripts/fmp_config.py k 1 1    # whole head set kept; groups 2 hands, 3 feet, 4 skirt
REA_KEEP_FACES=work/keep_k.npy REA_GROUPS=work/groups_k.npy REA_GROUP_RATIOS=2:0.4,3:0.45,4:0.8 \
  scripts/run_ladder.sh k 0.78,0.77,0.76
cp work/selection_k.json work/selection.json; scripts/build_pick.sh r77 k
```

Installed with `tools/install_model.py export/mm6_fmp_kr77.glb --world mm6 --name mm6_fmp.glb` (the name needs the
extension). Regression: `OPENYAMM_REGRESSION_FILTER=mm6_fmp ./build/game/openyamm --world mm6
--headless-run-regression-suite actors` (`review/regression.log`).

## Gait rollout (2026-10-31)

`mm6_fmp.glb` gained a `Jog` (Mixamo Running (5) legs, arms and dress chains from Run, aligned to Walking: her Run is
half a loop from her walk) for the fleeing chase (2.65 units/s), which played Run at x1.70. Binding: `run: Jog`,
`run_stride_length: 1.6`. Details, gates and rebuild: [package h04](../gait_rollout_20261031/h04/README.md)
(`scripts/rebuild.sh fmp`). A re-export or far-LOD repair rerun must re-graft this clip (rerun the h04 rebuild on the
new source).
