# MM9 spellbooks (2026-11-08)

The user asked for MM9's own spellbook art: four books, one per spell mastery (Normal, Expert, Master, Grandmaster),
the same for every school, as inventory icons and 3D ground models. MM9 now has its own book per spell (items
10901-10999, World:mm9, `tools/mm9_import_discovery/mm9_spellbooks.py`), sold in its shops instead of MM6's and dropping
in MM9 like the other worlds' books.

The design is a material ladder on one book, deliberately unlike MM9's plain tan skill books
(`inputs/mm9_skill_books_avoid.png`): brown leather and iron (Normal), oxblood and bronze (Expert), midnight blue and
silver with a sapphire (Master), black-violet and gold with an amethyst and faintly glowing runes (Grandmaster).

## Steps

1. `python3 -I run_codex.py icons normal`, then `icons expert master grandmaster` (they take the Normal paint as the
   shape authority): `<tier>/paint_a.png` by Codex from `BRIEF_ICONS.md`, style from MM7/MM8 books.
2. `python3 -I finish.py`: keys the magenta and fits each into the MM9 book canvas at x2 (`<tier>/icon_x2.png`, as
   `mm9_item_icons_20261104/scripts/finish.py` does for every MM9 icon) plus `icon_x8.png` for the texture brief.
3. `python3 -I run_codex.py textures <tier> ...`: flat `cover.png` and `spine.png` from `BRIEF_TEXTURES.md`.
4. `tools/mm9_import_discovery/mm9_spellbook_art.yml` lists the icons with their sha256;
   `python3 tools/mm9_import_discovery/import_mm9_items.py` installs them as
   `assets_dev/worlds/mm9/icons_x2/mm9_spellbook_<mastery>.png` and writes the book rows; then
   `generate_mm9_vendors.py` restocks the shops.
5. `blender --background --python build_models.py`: the MM6-MM8 spellbook model (`props/items_claude/scripts/
   build_books.py`, 46 triangles) with these covers, `work/mm9_spellbook_<mastery>_export.glb`.
6. `python3 -I install_models.py`: winding check, `tools/install_model.py --world-items --world mm9`, an entry per
   mastery in `props/items_mm9_claude/ledger.json` and the bindings (`assets_dev/worlds/mm9/world_items/items.yml`).
