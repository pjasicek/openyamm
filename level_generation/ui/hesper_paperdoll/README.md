# Hesper paperdoll equipment

Fitted character-screen art for Hesper's worn equipment, and the hand grips of its weapons and emitters. Without it a
worn Hesper piece draws its whole inventory icon over the doll. Task: `design/kreegan_world/WORK_PACKAGES/FIX_PROMPTS.md`,
"Hesper armor and weapons on the paperdoll"; reports in `WORK_PACKAGES/requests/P4.md`.

## How the game finds the art (no engine work)

- A worn body piece looks for `<Pic File><suffix>` (`GameplayScreenRuntime::resolveEquippedItemHudTextureName`) and
  falls back to the inventory icon. Armour: `vN` with a right-hand weapon, `vNa` without (each falls back to the
  other); helm, belt, boots: `vN`; cloak: `vNa` only, the minotaur and troll using `v1a`. `N` is the doll type + 1:
  0 human male, 1 human female, 2 minotaur (no helm or boots), 3 troll, 4 dwarf; 5, the dragon, wears nothing.
- MM's files per slot, which this project matches: armour 10, helm 4 (`v1 v2 v4 v5`), boots 4, belt 5, cloak
  `v1a v2a v5a`. MM's `b` cloak pieces (one MM8 cloak) are the clasp over the shoulders and the engine never draws them.
  Gauntlets, shields and weapons have no doll files.
- The file is drawn at its item's `complex_item_pictures` point for the doll type (logical pixels). The world supplies
  those rows as a `complex_item_pictures` table contribution, as MM9 does.
- The stage (`level_generation/projects/hesper_stage/stage.py`) installs, for every staged item, its files from
  `runtime/icons_x2/` into `worlds/hesper/icons_x2` (the world's x2 icon package) and its rows of
  `runtime/complex_item_pictures.txt` as `worlds/hesper/data_tables/complex_item_pictures.txt`; and it writes
  [`grips.yml`](grips.yml) into the staged rows' Equip X / Y.

## Making a piece

[`pieces.yml`](pieces.yml) names each piece's MM reference item (whose fitted files own canvas, silhouette, pose and
placement), its coverage profile and its design facts. [`scripts/paperdoll.py`](scripts/paperdoll.py):

```sh
python3 level_generation/ui/hesper_paperdoll/scripts/paperdoll.py prepare <piece>   # targets, inputs, prompts
python3 level_generation/ui/hesper_paperdoll/scripts/paperdoll.py codex <piece>     # Codex image workers, 4 at once
python3 level_generation/ui/hesper_paperdoll/scripts/paperdoll.py candidates <piece> # every generation fitted, to pick
python3 level_generation/ui/hesper_paperdoll/scripts/paperdoll.py fit <piece> t0=gen_2.png ...
python3 level_generation/ui/hesper_paperdoll/scripts/paperdoll.py review <piece>    # previews and checks
python3 level_generation/ui/hesper_paperdoll/scripts/paperdoll.py install <piece>   # runtime/ and the record
```

- **Target:** the reference file's own soft alpha (the restored x2 icons are anti-aliased), cut by the MM9
  pipeline's reviewed coverage profile (`tools/mm9_import_discovery/mm9_armor_foot_exclusions.yml`, per-piece
  overrides in `coverage_limits`; the cut feathered over two pixels), cleared of alpha below 16, of stray islands
  under 48 pixels and, for armour, of the feet (MM7 Leather Boots on the booted dolls, the minotaur's hooves).
- **Masters:** one Codex generation per doll type (`work/<piece>/t<N>/`, the brief is
  [`CODEX_BRIEF.md`](CODEX_BRIEF.md)): image 1 the MM reference cut to the target (the edit base), 2 the grey/magenta
  mask, 3 the bare doll, 4 the icon master; one retry at most. The model draws the design well but only roughly
  follows the outline, so a generation is a proposal: `fit` keys the magenta and fits it into the exact target alpha
  with `tools/mm9_import_discovery/fit_mm9_ai_equipment_variant.py` (bounding-box fit, gaps filled from neighbours,
  strict despill).
- **References per slot** (`pieces.yml`): body armour on MM7 Officer's Leather (vests) or MM8 Rusty Breastplate (plate
  with shoulder plates); helms on MM8 Full Helm, its crown studs taken off the outline (`smooth_crown`: an opening of
  the file's top half); boots on MM7 Steel Plated Boots; belts on MM7 Strong Belt or MM8 Sturdy Belt; cloaks on MM6
  Leather Cloak or, with a standing collar, MM6 Cardinal Cloak. A cloak's file is its inside seen from the front,
  drawn behind the body.
- **Shared masters:** outside armour a doll type reuses an earlier type's master when the reference's two files are
  pixel-identical (`master_of`; `shares` in `pieces.yml` overrides it): Full Helm, Sturdy Belt and both cloaks draw
  the dwarf as the human male, so a helm takes three masters, a Sturdy belt four and a cloak two.
- **Picking:** `candidates` fits every generation of every master and shows it worn beside the reference with the
  share of the target the fitter filled from neighbours (`work/<piece>/review/candidates.jpg`; a cloak alone, since
  the doll render is opaque). Pick per doll type for the design facts (where the light, node or clasp sits) and a
  clean outline; the picks are recorded in `generation_runs_paperdoll.json`.
- **Poses:** the empty-hand file `vNa` is the master; the weapon file `vN` is the same pixels inside the reference's
  weapon-pose alpha (MM's sleeved armour cuts the sleeve away; its sleeveless armour has identical pairs, and so do
  Officer's Leather and Rusty Breastplate, so these pairs are identical).
- **Review:** `review` renders every doll in both poses beside the MM reference with the table-driven previewer
  (`tools/mm9_import_discovery/render_paperdoll_equipment_preview.py`, now reading the declared x2 icon packages and
  drawing cloaks) and checks magenta, feet overlap and pair equality (`work/<piece>/review/`). In the game:
  [`scripts/capture.py`](scripts/capture.py) dresses a party of all five doll types in a headless scenario, saves,
  and captures each member's character screen on the desktop (`review/desktop/<name>/`); `capture.py --family` puts
  several captures on one sheet, a row per capture and a column per doll type.
- [`generation_runs_paperdoll.json`](generation_runs_paperdoll.json): per installed piece, the picks, raw and output
  hashes and fit reports; each job's `raw/runs.json` holds its prompts.

## Held items

[`grips.yml`](grips.yml): Equip X / Y for every weapon and emitter (the draft rows have 0,0, which hangs the icon's
corner from the hand). Melee grips sit on the icon's shaft at MM's median grip height per weapon type; emitters at
their centre like MM's shields; bows need none (the engine centres them). Guns are held as MM6 and MM7 hold their
blasters: long guns (`up`) stand muzzle-up with grip and stock toward the body and are held at mid-length on the
barrel line, as both games' Blaster Rifles; pistols (`out`) point away from the body, held by the handle, as MM7's
Blaster. The stage installs the turned or mirrored icon (a turned gun also stands upright in the pack).
[`scripts/held.py`](scripts/held.py) previews held items with the engine's placement rules.

Gauntlets have no doll files in MM, and the jewellery panel draws the icon in a 40 x 72 slot. Hesper's icons are pairs
too wide for it, so each gets one glove of the pair, upright as MM's gloves (`paperdoll.py glove <icon>`: one Codex
generation from `item127`'s pose and the icon's design), as `<icon>v1`...`v5` (the engine looks for these before the
icon), centred on the slot by its `complex_item_pictures` row. The pack keeps the pair.
