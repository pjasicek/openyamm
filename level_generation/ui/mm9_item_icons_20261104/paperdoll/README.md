# MM9 equipment on the paperdoll (2026-11-05)

New fitted doll art for MM9 worn equipment, painted from the new MM7/MM8-style icons (`../items/<id>/`), and new
weapon grips. The prototype (two armours, two helms, two belts, two pairs of boots, five weapons) was approved by the
user ("very good, including the placement"); the full pass then made **all 68 worn items** (35 armour, 16 helms,
11 boots, 6 belts) on all five dolls: human male, human female, minotaur, troll and dwarf (the minotaur wears no helm
or boots). The finished files are collected in `runtime/` and installed into MM9 at x2 (2026-11-05, see `../README.md`,
"Installed"); the renders are in
`review/`, with `review/viewer/index.html` as the local review page (handoff: [`../HANDOFF.md`](../HANDOFF.md)).

## Where things are placed (the position tables)

Two tables place equipment on the doll, both in logical (x1) pixels:

- **Worn pieces** (armour, helm, belt, boots, cloak): the world's `complex_item_pictures.txt` row gives, per doll type,
  the point where the fitted file's top-left corner is drawn. The engine picks the file `<Pic File><suffix>`: armour
  `vN` while a weapon is held and `vNa` without, helm/belt/boots `vN`, N = doll type + 1.
  Technique: every MM9 piece is painted **on the canvas of an MM7/MM8 reference piece** (the reviewed choice per item
  in `tools/mm9_import_discovery/mm9_equipment_legacy_base_mappings.yml`), so its row is the reference's row, unchanged.
  MM9's current table already follows this rule (all 68 rows equal their reference's), so the table stays as it is;
  only a piece remapped to another reference takes that reference's row (`P.picture_rows`).
- **Held weapons and shields**: the item's Equip X / Y in `items.txt` is the grip point on the icon. The engine hangs the
  icon so that point sits on the doll type's main-hand anchor (right-hand fingers' centre X, closed-hand Y plus the main
  hand offset); the fingers are drawn over it, centred on the point. Technique: `../scripts/check_doll_grip.py` runs the
  repo's generator (`generate_mm9_item_equipment_visuals.py`: the nearest MM6-MM8 silhouette's grip, scaled, then
  centred on the shaft) on the new icons; `scripts/equip_table.py` writes the proposed values beside the current ones
  (`runtime/equip_anchors.tsv`, 97 weapons and shields). The generator's manual override for the Imperial Star belongs
  to the old diagonal art and is dropped.

## How a fitted piece is made

The Hesper pipeline (`level_generation/ui/hesper_paperdoll/README.md`), configured for MM9 by
`scripts/mm9_paperdoll.py` rather than copied:

1. **Target outline:** the reference file's own soft alpha per doll type, cut by the item's coverage profile (armour:
   `short_torso`, `hip_length`, `thigh_length`, `full_harness`; `coverage_limits` per doll type), with the feet
   (boots, the minotaur's hooves) kept clear and, for helms, crown studs or horns opened away (`smooth_crown`).
2. **One Codex image per doll type** (`work/<piece>/t<N>/`, brief `CODEX_BRIEF.md`) from four inputs: the reference
   piece cut to the target (the edit base), the grey/magenta target mask, the bare doll, and the new icon's full-size
   painting (the design). Codex draws the design well but follows the outline only roughly.
3. **Fit:** the generation is keyed and fitted into the exact target alpha
   (`fit_mm9_ai_equipment_variant.py`: bounding-box fit, gaps filled from neighbours, strict despill). The candidates
   sheet (`work/<piece>/review/candidates.jpg`) shows every generation worn, with the share the fitter had to fill;
   pick per doll type.
4. **Poses:** armour's weapon pose `vN` is the master's pixels inside the reference's weapon-pose outline (no second
   generation).
5. **Review:** `review` renders each piece on every doll in both poses beside the reference and checks magenta, feet
   and pair equality; `scripts/outfit.py` dresses whole outfits with a weapon, as the game composites the screen.

Rule of thumb from this run: when the reference's outline has parts the MM9 design lacks (horns, a full-leg suit), cut
the outline (`smooth_crown`, `coverage_limits`) before generating instead of letting the fitter invent them; a fill
share above about 15 % means the outline and the design disagree.

## Prototype findings

- The human female's MM7 armour references (Resplendent Chain Mail, Splendid Plate Armor) are full-leg suits; with
  the reviewed `thigh_length`/`full_harness` profiles the mail and the plate skirt became leggings. Cut at y 230
  (mid-thigh) for her.
- Jarl's Helm keeps MM7 Phynaxian Helm (open cheeks) with its side horns opened away (`smooth_crown: 9`).
- Generated at the engine's x2 scale. MM9's icon package is x1 today: installing means either halving these files or
  moving MM9 to an x2 package.

## Full pass (2026-11-05)

- `pieces.yml` holds all 68 pieces. Facts were written from the new icons. References and coverage come from the
  mapping table, with these exceptions, each commented in `pieces.yml`:
  - **Female cut at y 230** for every MM7 full-leg reference (Golden Chain Mail, Plate, Splendid and Noble Plate), as
    in the prototype.
  - **Thigh-length instead of full harness** for Full Plate, Heavy Plate and Swordsbane, whose designs end at the
    thigh.
  - **Imperial Scale and Brigandine** end higher on the human male and dwarf (`coverage_limits`). Their MM8
    references are bodysuits whose legs survived the hip-length cut, which painted scale trousers. The first
    generations are kept in `raw/old_thighs/`.
  - **Five helms on another reference** where the table's had parts the design lacks:
    - Loaf Helm, Witchbane and Death Cap: MM8 Full Helm.
    - Prize Skullcap: MM7 Conscript's Helm.
    - Fre's Helm: MM7 Phynaxian Helm, as Jarl's Helm.

    Their placement rows change with the reference: `runtime/complex_item_pictures.txt`, five rows differ from MM9's
    current table.
  - **Fuzzy Slippers:** `keep_lower` cuts each boot outline to its foot (`mm9_paperdoll.py`).
  - **Brongnoker** has the same design and reference as Plain Helm. `same_art_as` reuses its generations.
- Generation: `scripts/codex_queue.py` (16 Codex workers, the user's limit; jobs claimed at start).
- Fit and review: `scripts/finish_piece.py` (picks the least-filled generation per doll unless a pick is given or an
  earlier fit exists, so the prototype picks stayed).
- Each piece was looked at on every doll. All 68 pass the checks: 0 opaque magenta, 0 feet overlap, exact alpha.
  The picks and fill shares are in `work/<piece>/review/picks.json`.
- `runtime/icons_x2/` holds the 488 doll files at x2 and `runtime/complex_item_pictures.txt` their rows (written by
  `paperdoll.py install`, which records hashes in `generation_runs_paperdoll.json`).
- `scripts/viewer_data.py` refreshes the viewer: piece sheets, icons, outfit renders and the inlined data. Outfits C
  and D use full-pass pieces.

## Follow-ups (2026-11-05)

- **Witchbane** (skull helm): `see_through: [darkness, minimum]` in `pieces.yml` makes its dark eye sockets, nose
  and mouth transparent after the fit (`mm9_paperdoll.py` `see_through`), so the wearer's face shows through.
- **Flail handles:** War Star, Imperial Star and Blutterbunger had handles 13-15 px wide where MM6-MM8 flails and
  maces are at most 12.5 (median 9). They were repainted with a CORRECTION line in their briefs, and their grips
  recomputed (`check_doll_grip.py`, `equip_table.py`). Their old art is in `items/<id>/old_thickgrip/`.
- **Blackpowder** sits at the doll's bow point behind the body. It was 180 px tall, taller than any MM crossbow, so
  its muzzle showed over every head. It is now fitted to 120 px (`BOX_OVERRIDES` in `prep_all.py`). MM's own
  crossbows also show over the minotaur's head.
- **Gauntlets:** the family box is now 68x128 at x2 (34x64 logical), inside the jewellery panel's 40x72 cell like
  MM7's 61-63 px gloves; the old icons are in `items/<id>/old_bigglove/`. Their complex_item_pictures rows centre
  them in the cell (`pieces.yml` `gauntlets`, `paperdoll.py` `picture_rows`). Amulets and rings are centred by the
  engine; the jewellery panel review is `scripts/jewelry.py`.
- `scripts/all_weapons.py` renders every weapon, missile weapon and shield on all five dolls
  (`review/weapons/<id>.jpg`). The shields sit where MM's do.

## Commands

```sh
python3 scripts/mm9_paperdoll.py prepare|candidates|review <piece>
python3 scripts/mm9_paperdoll.py fit <piece> t0=gen_2.png t1=gen_1.png ...
python3 scripts/codex_queue.py [--workers N] <piece> ...   # every pending master job, 16 Codex workers by default
python3 scripts/finish_piece.py <piece> ... [--pick <piece>:t<N>=gen_<n>.png]   # candidates, picks, fit, review
python3 scripts/retire_masters.py <tag> <piece> t<N> ...    # after a target change: old raws aside, re-prepare
python3 scripts/all_weapons.py [id ...]          # review/weapons/<id>.jpg: weapons and shields in the hand
python3 scripts/jewelry.py                       # review/jewelry/: the jewellery panel, MM6-MM8 beside MM9
python3 scripts/viewer_data.py                   # review/viewer/ from the finished pieces
python3 scripts/outfit.py                        # review/outfits/*.jpg
python3 scripts/equip_table.py                   # runtime/equip_anchors.tsv
```
