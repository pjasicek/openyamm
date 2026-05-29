# MMMerge Icon Ownership

This repository keeps MMMerge icon assets flattened into runtime lookup folders, but preserves source ownership by
folder:

- `assets_dev/engine/icons`
  - all files from `reference/mmerge_data_forus/Data/mmmerge.icons.lod`
  - `item*` files from `mm6.icons.lod`, `mm7.icons.lod`, and `mm8.icons.lod`
  - `pc*` files from `mm6.icons.lod`, `mm7.icons.lod`, and `mm8.icons.lod`
  - globally referenced MM8 overlay UI/paperdoll files from `mm8.icons.lod`:
    - `8evtnpc.bmp`
    - `grlalhd.bmp`, `grlalho.bmp`, `grlarhb.bmp`, `grlarhd.bmp`
    - `grlblhd.bmp`, `grlblho.bmp`, `grlblhu.bmp`, `grlbrhb.bmp`, `grlbrhd.bmp`, `grlbrhu.bmp`
    - `grldlhd.bmp`, `grldlho.bmp`, `grldlhu.bmp`, `grldrhb.bmp`, `grldrhd.bmp`, `grldrhu.bmp`
  - no outdoor map minimap BMPs
- `assets_dev/worlds/mm6/icons`
  - `npc*` files from `reference/mmerge_data_forus/Data/mm6.icons.lod`
  - MM6 outdoor map minimap BMPs matching MM6 `.odm` names, plus `6outside.bmp`
- `assets_dev/worlds/mm7/icons`
  - `npc*` files from `reference/mmerge_data_forus/Data/mm7.icons.lod`
  - MM7 outdoor map minimap BMPs matching MM7 `.odm` names, plus `7outside.bmp`
- `assets_dev/worlds/mm8/icons`
  - MM8-owned `npc*` files from the original MM8 icon extraction
  - `npc*` overlay files from `reference/mmerge_data_forus/Data/mm8.icons.lod`
  - original MM8 `npc*` files that are shadowed by `mm6.icons.lod` or `mm7.icons.lod` are removed
  - MM8 outdoor map minimap BMPs matching MM8 `.odm` names, plus `outside.bmp`

Runtime filenames in these managed groups are lowercase and use mode `0644`.

MMMerge's original runtime behavior is an overlay chain: original MM8 `icons.lod` is loaded first, then custom
`Data/*.icons.lod` archives are loaded after it. This repo resolves that overlay during asset import so each managed
logical filename has one runtime owner.

There are currently a few legacy non-managed case-only icon conflicts in `engine/icons` with distinct contents:

- `Layout.PCX` / `layout.pcx`
- `Options.bmp` / `options.bmp`
- `Sprites.PCX` / `sprites.pcx`
- `winBG.PCX` / `winBG.pcx`

Do not collapse those without first deciding which logical asset each reference should use.

## Coverage Inventory

The following inventory compares logical lowercase filenames from the extracted MMMerge icon source folders:

- `reference/mmerge_data_forus/Data/mm6.icons.lod`
- `reference/mmerge_data_forus/Data/mm7.icons.lod`
- `reference/mmerge_data_forus/Data/mm8.icons.lod`
- `reference/mmerge_data_forus/Data/mmmerge.icons.lod`

against the runtime destination folders:

- `assets_dev/engine/icons`
- `assets_dev/worlds/mm6/icons`
- `assets_dev/worlds/mm7/icons`
- `assets_dev/worlds/mm8/icons`

Current coverage:

- source logical filenames: 8,773
- destination logical filenames: 12,534
- source logical filenames present in destinations: 8,773
- missing source logical filenames: 0

Per-source coverage:

- `mm6.icons.lod`: 1,793 / 1,793 present
- `mm7.icons.lod`: 2,507 / 2,507 present
- `mm8.icons.lod`: 650 / 650 present
- `mmmerge.icons.lod`: 3,827 / 3,827 present

Known source logical duplicates:

- `belt4av5.bmp`: present in `mm6.icons.lod` and `mmmerge.icons.lod`, identical content
- `belt5av5.bmp`: present in `mm6.icons.lod` and `mmmerge.icons.lod`, identical content
- `tab2a.bmp`: present in `mm7.icons.lod` and `mmmerge.icons.lod`, different content
- `tab2b.bmp`: present in `mm7.icons.lod` and `mmmerge.icons.lod`, different content

Known destination logical duplicates:

- `engine/icons` and `worlds/mm6/icons` currently overlap on 1,233 logical names. This is legacy/import debt from
  MM6-owned prefixed UI/icon files being available globally. It is not an immediate missing-asset problem while all base
  world icon roots are mounted, but it should be cleaned up when MM6 icon ownership is normalized.
- `engine/icons` has four legacy case-only duplicates with distinct contents: `Layout.PCX/layout.pcx`,
  `Options.bmp/options.bmp`, `Sprites.PCX/sprites.pcx`, and `winBG.PCX/winBG.pcx`.

Known covered-source hash mismatches:

- `title.pcx`, `makeme.pcx`, and `restmain.bmp` intentionally keep the MM8 engine defaults, even though the matching
  logical names also exist in `mm7.icons.lod`.
- `sprites.pcx` is part of the legacy case-only conflict above and must not be collapsed without checking references.

All destination files in the four runtime icon roots currently use mode `0644`.
