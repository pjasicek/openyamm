# The old import's original tables (converter inputs)

Frozen copies of the tables as the old MM9 import had them, before the rebuilt maps were promoted into assets_dev
(P1, 2026-11-06; copied from output/mm9_rework/promotion_backup_20261106). The converters rebuild each map's rows
from these originals (dungeon/tables.py: the map's map_stats rows by the old `.odm` name, its map_transitions ends,
its painted-map catalog entry): assets_dev now holds the rebuilt rows, so it can no longer serve as "the original".
Do not edit; regenerate only if the old import itself is re-imported.

- map_stats.txt (engine/data_tables), map_transitions.txt and transport_routes.txt (worlds/mm9/data_tables),
  catalog.yml (worlds/mm9/ui/maps)

One row is not the old import's: `mm9:transition/arslegardcity/638` (ExitTrigger3, Arslegard City's chasm catch
volume into Thjorgard, which the old import never made), a copy of row 648 in the old frame, added 2026-11-06 so that
Thjorgard's conversion moves its arrival like any other row; Arslegard City's convert.py `add_catch_row` sets its volume.
