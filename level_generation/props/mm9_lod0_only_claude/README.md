# MM9 simple decorations without LODs (2026-11-09)

The raised coffin in Thousand Terrors (`mm9_deco_coffinraised`, 634 triangles) drew with a caved-in lid and torn sides
from a few hundred units away: its LOD2 (157 triangles) was a collapse decimation of LOD0, because MM9's ABC had no
native level near 25 %. The MM9 props builds made LODs for every prop from 250 triangles, against the
[modelling guidelines](../../GAME_ASSET_MODELLING_GUIDELINES.md) §7 ("skip LODs for assets that are already simple").
On props this small the levels save next to nothing (a draw per material per level either way, the same fill) and
decimating a hard-surface shape breaks it; the loot satchels lost their LODs for the same reason
([`lod0_only.py`](../loot_satchel_claude/scripts/lod0_only.py)).

## What changed

- `LOD_MIN = 1000` (was 250) in every `mm9_*_claude/scripts/build.py`: future builds make no LODs below 1,000
  triangles.
- `scripts/strip_lods.py --install`: the 165 installed `mm9_deco_*.glb` with LODs and fewer than 4,000 LOD0 triangles
  (153 below 1,000; the weapon and wine racks, `skeletonstatue`, `icelich`, `iceskeletonwarrior` and `greenmanstree`
  at 1,001-1,394) keep LOD0 only. LOD0's primitive data is checked byte-identical to the original before writing;
  `check_winding.py` reports 0 inverted closed parts on all of them; each is installed with
  `tools/install_model.py --world mm9`.
- Kept: the 20 posed figures and corpses (`*figure`, `*dead*`, `*seated`, 4,414-12,724 triangles, three or four
  levels). Their reductions are organic and the corpses are placed up to 30 times a map; their lowest levels were
  rendered for review (see below).

```sh
python3 level_generation/props/mm9_lod0_only_claude/scripts/strip_lods.py            # dry run into work/
python3 level_generation/props/mm9_lod0_only_claude/scripts/strip_lods.py --install  # strip and install
```

A rebuild of one of these props from its project now produces LOD0 only, so it stays consistent with this pass.
