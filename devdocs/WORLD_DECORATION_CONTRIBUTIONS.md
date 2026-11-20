# World decoration contributions

A world adds its own decorations without touching the engine's `engine/data_tables/decoration_data.txt`: it declares a
range of decoration numbers and a table file with the engine table's columns, and the engine merges that file after the
engine rows while the world is active. Implemented in `game/content/WorldDecorations.{h,cpp}`; tests in
`tests/WorldDecorationTests.cpp`.

## Format

`worlds/<world>/world.yml`:

```yaml
idRanges:
  decorations:          # decoration_data.txt row numbers ('#'), a map entity's decoration_list_id + 1
    begin: 2001
    end: 2999
tableContributions:
  - table: decorations
    idDomain: decorations
    mode: append
    path: data_tables/decoration_data.txt
```

- `worlds/<world>/data_tables/decoration_data.txt`: the engine table's header and columns (`#`, InternalName, Hint,
  Type, Radius, Height, LightRadius, LightRed/Green/Blue, SoundId, Flags, SpriteId, Comments, MapAliases). `#` is the
  decoration number inside the declared range; a map entity places it as `decoration_list_id = # - 1`.
- `worlds/<world>/rendering/sprite_frame_data_world_decorations.yml` (optional): the sprites the world's rows name, in
  the format of `engine/rendering/sprite_frame_data_common.yml`, appended to the sprite frame table once at load. It
  stays out of the common file, which outdoor lighting bakes depend on. A sprite id that is already taken fails the
  load.
- `worlds/<world>/models/decorations.yml` (and `indoor_decorations.yml`, `decoration_overlays.yml`): model bindings by
  decoration name. These world manifests already extended the engine's (`game/maps/DecorationModelManifest.cpp`); a
  decoration's model is found through its sprite, so each modelled decoration needs its own sprite id. A one-frame
  sprite of the engine's `pending` texture is enough: it is never drawn while the model is bound.

## Rules

- Every consumer loads the rows through `loadDecorationTableRows` (game map loading and its shared cache, the event
  runtime's interactive decorations, outdoor party start points, the editor); none reads `decoration_data.txt` itself.
  `tools/lighting/bake_decorations.py` and the MM9 isle conversion merge the same files.
- Only the active world's contribution is merged (as house contributions). A world without one sees exactly the engine
  rows, so MM6-MM8 are unchanged.
- The merged rows must increase. The numbers between the engine's last row and the world's first are no decoration:
  `DecorationTable::get` returns null for them, so nothing draws or collides there. A map entity that places such an id,
  or one past the table, is reported once per id at map load (`Map <file>: N entities (first '<name>') place
  decoration_list_id ...`).
- The load fails, with a message, on a world range that does not start past the engine's last row or ends past 65536,
  a world row outside its range or out of order, a world row without a name, and a world decoration name that the
  engine table or an earlier world row already has.
- Built maps store the ids, so a world's rows never move once maps use them; new rows take the next free number.

## Ranges in use

| Owner | Rows | Sprite ids |
| --- | --- | --- |
| engine | 1-673 | 0-23312 (common), 23990-23999 (engine items) |
| MM9 world | 2001-2999 | 24801-24999, then 26001-26999 (MM9's world item sprites are 24197-24600) |
| Hesper world (its stage) | 3001-3999 | 25001-25999 |

MM9's rows are written by `level_generation/props/mm9_isleofashes_claude/scripts/tables.py` (`--apply`). The range
starts at 2001 so that the engine table can grow.

## Hesper

Done on 2026-10-29. Hesper's stage (`level_generation/projects/hesper_stage/stage.py`) declares `idRanges:
decorations` 3001-3999 and the `decorations` contribution in the staged `worlds/hesper/world.yml`, writes its rows to
`worlds/hesper/data_tables/decoration_data.txt`, numbered by the append-only `hesper_stage/decoration_ids.yml` (`base:
3001`), and its sprites to `worlds/hesper/rendering/sprite_frame_data_world_decorations.yml` (a decoration's sprite id
is its number + 22000, so 25001-25999). The stage's engine `decoration_data.txt` and `sprite_frame_data_common.yml`
are plain copies of `assets_dev` again, and stage.py only checks that the engine table ends before 3001. The rows were
674-934 of a stage copy of the engine table before; every Hesper map was rebuilt once with the new ids (by name,
through the map projects' builds, which read `output/hesper_stage/decoration_ids.json`).
