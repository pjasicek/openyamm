# Held weapons probe, 13 November 2026

Probe for [devdocs/solo_action/WEAPONS.md](../../devdocs/solo_action/WEAPONS.md): can our ground-item weapon models
be held in the first-person arms?

- `scripts/align_held.py`: Blender script turning `assets_source/engine/world_items/models/item_<icon>.glb` into a
  held weapon (palm at the origin, head along +Y, length by kind). Usage in its docstring.
- `aligned/`: seven aligned probes (sword, two-handed sword, two-handed axe, spear, halberd, staff, mace). Local only.
- Renders of them in the arms are under `reference/oblivion_poc/preview/weapons_ours/` (git-ignored: the arms are
  Oblivion's).

- `scripts/make_held_table.py` (2026-11-14): writes `assets_dev/engine/world_items/held.yml`, the grip of every
  weapon, shield and bow ground model, from geometry; hand corrections in its `OVERRIDES`. See WEAPONS.md "Held weapons
  in the game". `--check` reports whether the table is current.
