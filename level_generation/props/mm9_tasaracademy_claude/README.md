# MM9 Tasar Academy props as 3D decorations (2026-10-30)

The props, braziers, candles, chandeliers, chests, barrels, the crate, the spike pit and the scripted books, scrolls and
chalices of MM9's Tasar Academy (`TASARACADEMY.dat`), converted from their LithTech ABC models into OpenYAMM 3D
decorations for the native BLV ([map project](../../projects/mm9r_tasaracademy/)). The route is the Verhoffin Ruins
props project's ([`../mm9_verhoffinruins_claude/`](../mm9_verhoffinruins_claude/README.md)): `scripts/anskram.py` runs the
Anskram Keep scripts on this project's table, `build.py` runs the Anskram build (with this project's flame specs),
`finish.py` the isle's. No paid services, no Meshy, no Codex: every model is MM9's own mesh with its skin x4 (plain
Lanczos, the isle's `textures.py`).

## Outputs

- **13 models built here**, installed with `tools/install_model.py --world mm9` (`assets_source/worlds/mm9/models/mm9_deco_*.glb`),
  all through `check_winding.py` (0 inverted closed parts each): `candle` (13 placements, flame cards on the wick),
  `chandelier` (2, a candle flame on each of its four `Flame` sockets), `scroll1` (7: the letters), `scrollpickup` (4:
  `PickUpItems/scroll.abc` with the `scrolldouble` skin, Scroll1-4), `smithhammer` (4), `pew` (3), `weaponrack_new`
  (3: `weaponrack.abc` with the `weaponrack_new` skin; Anskram's `weaponrack` has the `_used` skin, Dook's Castle's
  `weaponracknew` is the NS model), `forge` (2), `grindingwheel` (2), `gobletfancy02` (1, the chalice Prop152),
  `bagherbs1` (1); the tipped `bookrulestilt` (BookRules: pitch 2.5045 and roll 3.1521 baked in) and the posed
  `dwarfaxeonside` (the three pickaxes, below).
- **Reused** (same ABC, skin and scale; their rows, bindings and GLBs stay with their owner, each installed GLB
  md5-checked against the owner's `work/`): the Temple of Honk's `brazier` (50; already `card` flames seated in the
  bowl), `bookflat` (21 books, plus the six skill-book stand-ins below), `desk03`, `chest3`; Anskram Keep's `bedmedium`
  (row `mm9_bedmedium_x100`, the scale-1 row), `dresserns`, `barrel03` (its plain row is scale 1.5), `chest1`
  (`mm9_chest1_x100`); the Lich Lab's `chairdesk03`, `table01`, `table01ns`, `bookstack01`, `podium01`,
  `shelfitem05` (`_x150`), `skeletonstatue`; Drangheim Prison's `tablebench2`, `bucket01`, `anvil`, `coalbin`; the Chasm
  of the Dead's `pillarstand`, `goblet` (Prop151); Beethoven's `jar01`-`jar06` (the chalices Prop145-150); the isle's
  `book` (Prop160: its lectern pose is exactly Prop160's, pitch 2.5062928 and roll pi) and `podium` (PODIUM03, the
  lecterns Prop159/Prop162 and one more).
- **Variant rows of reused models** at this map's scales (the model's GLB unchanged): `mm9_bookcase02ew_x120`,
  `mm9_bookcase02ns_x120`, `mm9_crate_x125` (Anskram), `mm9_ironingots_x150`, `mm9_ropecoil_x75` (Drangheim),
  `mm9_shelfitem03_x150` (Lich Lab), `mm9_spikepit_x100` (Anskram's spikepit at MM9's Scale 1), `mm9_suitofarmor02_x150`
  (Dook's Castle).
- Rows **2302-2322** (21 rows: the 13 models and the 8 variants) in the MM9 world's decoration contribution
  (`assets_dev/worlds/mm9/data_tables/decoration_data.txt`), sprites 26103-26123, 23 bindings in
  `worlds/mm9/models/indoor_decorations.yml` (the 21 plus indoor bindings of the isle's existing rows `mm9_book` and
  `mm9_podium`, which had only outdoor ones; same height and row, as the Lich Lab did for `mm9_cookpot`), appended in one
  run under `mm9r_common/locks/mm9_decorations.lock`. A rerun of `tables.py` reports 0 rows to add.
- `../../projects/mm9r_tasaracademy/props.json`: **304 placements** (233 props, 65 flames: 50 braziers, 13 candles and 2
  chandeliers as `kind: torch`, 4 chests, the spike pit as `kind: damager`, BookRules as `kind: quest`), every one under
  its DAT object name; scripted ones carry `script` (`BookLetter.scr 434` ...). **294** are checked against the old
  map's baked BModel of the same object: median of medians **0.52** units, worst median **0.79** (Prop160, the isle's
  book); per model the worst medians are 0.29-0.79. The ten not checked are below.
- `review/props_sheet.png`: contact sheet of the 13 models (LOD0 front, three-quarter, side, behind-above, below, LODs);
  `review/<prop>/`: the renders; `review/chandelier/closeup_*.png`, `review/candle/closeup_*.png`: the flames on the
  candle tops (`scripts/review_closeup.py`).

## Route (`scripts/`)

```sh
cd level_generation/props/mm9_tasaracademy_claude
python3 scripts/props_table.py && python3 scripts/convert_all.py && python3 scripts/textures.py
blender --background --factory-startup --python scripts/build.py
python3 scripts/finish.py --install
blender --background --factory-startup --python scripts/review.py -- && bash scripts/contact_sheet.sh
blender --background --factory-startup --python scripts/review_closeup.py
flock -x ../../projects/mm9r_common/locks/mm9_decorations.lock python3 scripts/tables.py --apply
python3 scripts/placements.py --verbose && python3 ../../projects/mm9r_common/review_root.py
```

`dwarfaxeonside` is converted by hand in `full` mode (the rigid export drops the animation), as Verhoffin's
`bedmedium2onside`: `convert_abc_model.py DWARFAXE.abc work/raw/dwarfaxeonside --id dwarfaxeonside --export-mode full
--texture 0=.../DWARFAXE.dtx`, `work/raw/dwarfaxeonside/mode.txt` says `full`; `build.py` poses it (props_table `POSES`).
`convert_all.py` skips the posed props unless named.

## Placements not checked against the old bake

- **The pickaxes** (Pickaxe3-5, `Dwarfaxe.ABC` Scale 1.5, `PropAnim.scr "onside"`): the ABC has an `onside` animation,
  so it is baked in (frame 1 of `onside`): the pickaxe lies flat (8 units high as placed). The old bake is the upright
  bind pose (fit 113-122 as placed, meaningless); they stand on the shelf under their DAT position (MoveToFloor 1:
  174 native, DAT 204.8).
- **The six skill books** (Prop5, Prop88-91, Prop94, `SkillBook.scr`): MM9 ships no `PickUpItems/Skillbook.abc` nor its
  `SkillBook_Normal.dtx` (not in `mm9/extracted`), and the old bake has no mesh for them. They are the flat book
  (`mm9_bookflat`) centred on the DAT position, on the highest surface under it (MoveToFloor 1): Prop89/Prop90 on their
  tables (86), Prop88 and Prop5 on the floor beside table Prop154 (0), Prop91 at 1065 and Prop94 at 532 (236 under its
  DAT height). The map project may move them.
- **BookRules** (`book-rules.abc`, `BookOfRules.scr`): the old transcoder baked nothing for it. It is placed as the
  transcoder places a model (binding origin, the pitch and roll baked into `bookrulestilt`, MoveToFloor 0), the route
  that puts Prop160 on its bake to 0.79; it lies on the lectern Prop162 as Prop160 lies on Prop159 (1.8 units lower
  relative to its lectern, which MM9 dropped 7.3 units to the floor).

## Notes

- **Flames** use the props pipeline as fixed on 2026-10-30: the isle's `finish.py` gives the `Fire` material
  `openyamm_billboard: card` (turns about its own centre), and the cards are seated on the head: the candle's on the top
  12 % of the model (its `Flame` socket is the model's top vertex), the chandelier's on the highest vertex within 5 units
  of each `Flame` socket (Ruined Temple's `chandelier3` route; seats printed by `build.py`). The reused `mm9_brazier`
  already had `card` flames. Not looked at in game here (the map project's flame view does that).
- **Lights:** no row carries a light. Each brazier and candle names the nearest kept light of the map project's
  `work/lights.json` in its `light` field (0-109 units away, 65 distinct); the BLV keeps MM9's lights.
- **The spike pit** (PropDamager Spikes1) is in `props.json` as `mm9_spikepit_x100` at the old bake's position, which is
  the transcoder's floor drop: base at -656.1, the pit floor under it at -655. The map project can place it from here or
  skip `Spikes1` and place its own; its damage is the map's.
- **Anchors** are the DAT names, unchanged. `Prop176` does not exist in the DAT (the letters are Prop174, 175, 177, 178,
  179, plus Prop4 and Prop96); `Prop92`/`Prop93` in the Prop88-94 range are desks, not skill books.
- **Blender 5's glTF importer adds a bone-display mesh** (`Icosphere`, 42 vertices, 80 triangles) for every skinned
  (`full`) import, and the isle's `blib.import_raw` takes every imported mesh: the posed pickaxe came out with a 2.4 cm
  ball half a metre under it. `build.py` imports with `disable_bone_shape` (the isle's `blib.SKIP_BONE_SHAPES` since 2026-10-31), so
  `dwarfaxeonside`, `grindingwheel` and `weaponrack_new` have none. **Other projects' full-mode GLBs carry it**: an 80-
  triangle ball sits in the installed `mm9_deco_bookflat` and `mm9_deco_book` (at the spine, about 2 cm; reused here),
  `mm9_deco_weaponrack` (inside the rack) and `mm9_deco_bedmedium2onside` (Verhoffin's posed bed: 156 triangles =
  76 + 80, ball 0.72 m up). Fixed in their projects on 2026-10-31
  (26 models: the isle's `blib.SKIP_BONE_SHAPES` flag, which this `build.py` now sets instead of patching
  `blib.import_raw`; each owner's README).
- `chandelier` is 816 units tall: MM9's model hangs its four-candle crown on a long rod from the ceiling (fit 0.50 to
  the old bake, rod included). `forge` is 4.4 m with its hood. `bookrulestilt` is MM9's 10-triangle book box.
- The chandelier skin has a little alpha (3 % of texels, outside the used UVs): kept opaque as MM9 (Chromakey 0).
- Reused rows keep their owner's collision and height (`tables.py` prints NOTE lines where this table's own guess
  differs: the jars, goblet, bucket, `bookstack01` and `chest3` have no collision in their owners' rows).
