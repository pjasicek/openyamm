# MM9 Inventa Storca props as 3D decorations (2026-10-30)

The props, torches, hanging braziers, barrels, bone piles, chests, treasure bags and quest orbs of MM9's Inventa Storca,
as OpenYAMM 3D decorations for the native BLV ([map project](../../projects/mm9r_inventastorca/README.md)). The route is
the Drangheim Prison props project's ([`../mm9_drangheimprison_claude/`](../mm9_drangheimprison_claude/README.md)): its
scripts copied and pointed at this map. No paid services, no Meshy, no Codex: every model is MM9's own mesh with its skin
enlarged x4 by Lanczos (the shared `textures.upscale`).

## Outputs

- **3 models** built and installed with `tools/install_model.py --world mm9` (`assets_source/engine/models/`), all through
  `check_winding.py` (0 inverted closed parts): `mm9_deco_bench03` (BENCH03, 58 triangles), `mm9_deco_orblinking`
  (ORB_LINKING, the quest Orb of Linking, 272/135/66), `mm9_deco_treasurebag` (TREASUREBAG with bag1.dtx, 112).
- **Reused** (same ABC, skin and scale, their owners' build records): `barrel03`, `chair`, `tableround`, `scroll`,
  `walltorch`, `chest` (chest1.abc with chest2.dtx) from Anskram Keep; `hangingbowl2`, `bench04` from the Temple of Honk;
  `bonepile` from Beethoven; `tablebench2` from Drangheim Prison; `blackchest` (its x0.8 row) from the Lich Lab.
- Rows **2275-2277** in `assets_dev/worlds/mm9/data_tables/decoration_data.txt` (sprites 26076-26078), bindings in
  `worlds/mm9/models/indoor_decorations.yml`, appended under `mm9r_common/locks/mm9_decorations.lock`.
- `../../projects/mm9r_inventastorca/props.json`: **108 placements** (44 wall torches, 21 hanging braziers, 9 chairs, 7 orbs,
  5 bench tables, 5 barrels, 3 tables, 3 bone piles, 3 chests, 2 bags, 2 benches of each kind, 2 scrolls), each checked
  against the old map's baked BModel: median 0.81 units; the bags, orbs and BrazierBowl10-21, which the old map did not
  bake, stand by the transcoder's rule (MoveToFloor objects on the floor under them).
- `review/props_sheet.png`: the three new models.

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_inventastorca_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
blender --background --factory-startup --python scripts/review.py -- && bash scripts/contact_sheet.sh
python3 scripts/tables.py --apply        # takes the decorations lock itself
python3 scripts/placements.py
python3 ../../projects/mm9r_common/review_root.py
```

## Notes

- The treasure bags are loot containers (mm9_item_sources: kind `treasure_bag`): `placements.py` gives them the kind
  `chest`, so a click opens their loot like a chest's.
- Flames: `walltorch` carries the card billboard (the 2026-10-30 fix); `hangingbowl2`'s flame stands on the bowl's axis, so
  its plain billboard is right (Anskram README, Flames). Neither was rebuilt here.
- The orb's skin is a plain silver-white; MM9 shows no glow mask or alpha on it.
- No row carries a light: every torch and brazier has its MM9 `Light` beside it, kept as a BLV light.
- `tablebench2` (Drangheim Prison's model) drew black in this map's west hall: not the model (normals, winding, material
  and texture are sound; it draws lit in Drangheim Prison) but the engine's decoration light in a baked room lit by
  bake-only direct light. Traced and mitigated in the map ([map README](../../projects/mm9r_inventastorca/README.md),
  "Black tables").
