# Named mods

A named mod is a folder in the player's `mods` folder with a manifest, its own files and the rows it adds to or
changes in the engine tables. The game mounts the mods that are switched on, in a fixed order, at its start. The Map
Studio packs and installs them (`oymap mod pack`, `oymap mod install --layout named`; `openyamm-studio/README.md`).
Game change G3 of the Map Studio's S6 (`devdocs/map_studio/S6_PLAN.md`); approved on 2026-11-15.

Code: `game/content/NamedMods.{h,cpp}` (manifest, enabled list, choice and order, id ranges, table rows, the start),
`AssetFileSystem::mountNamedMods` and `setNamedMods` (`engine/AssetFileSystem.cpp`), the rows in
`GameDataLoader::applyActiveRulesetTable`, the start in `GameApplication::loadGameData`, the `mods` console command and
the save check in `GameApplication::quickLoadFromPath`. Tests: `tests/NamedModsTests.cpp`, the named-mods case in
`tests/AssetFileSystemTests.cpp`, `tests/scenarios/mods/`.

## Layout

```
<user data>/mods/
  enabled.yml                  the mods that are on, in mount order
  <id>/
    mod.yml                    the manifest
    engine/...                 files as the engine package holds them (engine/data_tables/x.txt)
    worlds/<world>/...         files as a world package holds them (maps, scenes, scripts, overlays, cinematics)
    tables/<table>.override.txt, <table>.append.txt
                               the rows it changes in and adds to engine/data_tables/<table>
  engine/, worlds/<world>/     the loose layout (packaging/MODDING.md): unchanged
```

`<user data>` is the installation folder of a release (`packaging/RELEASE.md`), the `--user-data` folder, or the
working directory of a development run. The loose `mods/engine` and `mods/worlds/<world>` folders work exactly as
before: mounted over a release's packs only, every file logged. The Map Studio's merged installs
(`oymap mod install --layout merged`) write that loose layout and keep their records in `mods/studio_mods.yml` and
`mods/studio_mods/`, which the game ignores; `studio_mods` has no `mod.yml`, so it is never a named mod.

## Manifest

`mod.yml`, the Map Studio's `openyamm-studio/schema/mod.schema.json`:

- `format: 1`, `id` (lower case letters, digits, underscores; the folder's name; not `engine` or `worlds`), `name`,
  `version`; optional `author`, `description`, `worlds`.
- `maps`: `{file, world, kind: new|overlay}` (and the studio's `project`, `source_revision`, `files`, not read).
- `tables`: `{table, override, append}`: `table` below `engine/data_tables/`, the files inside the mod.
- `map_numbers`: the map_stats numbers its new maps take; `idRanges`: `{domain: {begin, end}}` as world.yml and
  ruleset.yml declare theirs (`maps` for map numbers; any domain is compared with the same domain elsewhere).

A key the schema does not know, a wrong format, an id that is not the folder's name, a table file outside the mod or
missing: the mod is refused (when it is listed as on) with the reason in the log and in the console's `mods`.

## The enabled list

`mods/enabled.yml`, as the studio's named install writes it:

```yaml
format: 1
enabled: [s6_demo, other_mod]
```

- A mod the list does not name is **off**: an installed mod never plays until someone switches it on. That is the
  safer reading: a folder copied in by hand, or left from an earlier install, changes nothing by itself.
- The order is the mount order: each mod mounts in front of the ones before it (its file wins) and its table rows apply
  after theirs. When two mods clash (below), the earlier one stays and the later one is refused.
- A missing file switches nothing on. A malformed file is logged and switches nothing on; the console refuses to
  rewrite it. A listed mod that is not installed is logged and listed by `mods`.

A file in the mods folder rather than a setting in `settings.ini`: it travels with the mods (the studio writes it),
the player edits it beside them, and Settings → Defaults cannot switch mods off by accident.

The self-updater and the release packages never touch `mods/`: the updater only writes `app/<version>/`, `assets/`,
the pack store and its own update folder (`engine/update/AppUpdater.cpp`), and no release archive carries a `mods`
folder (`tools/package_runtime_assets.py`, `packaging/`). Saves, settings and mods are user data in the same folder.

## Mount order

At the start (`GameApplication::loadGameData`, before anything is read from the assets) the game reads the mods
folder once (`mountNamedMods`):

1. the catalog: every folder with `mod.yml`, its manifest and table files, and `enabled.yml`;
2. the id ranges (below); refused mods are logged (`Mods: <id> is refused: <reason>`);
3. the mods that are on are mounted (`AssetFileSystem::setNamedMods`, which mounts everything again as a world switch
   does), then their table rows are tried on the tables as mounted; a mod whose rows do not apply is refused and the
   rest mounted again without it;
4. `Mods: <id> <version> is on (<name>)` for each, and each mod's files as the loose folder's are logged
   (`Mods: <id>: engine/data_tables/x.txt replaces the game's file`, at most 100 lines, then the count).

Where they mount:

- Over a release's packs: each mod's `engine/` at `/engine` and `worlds/<world>/` at `/worlds/<world>`, as the loose
  layout's, in front of the packs and the language pack, and **behind the loose folders** (a player's loose file wins).
- Over a development root (`assets_dev`): each mod as an `--extra-mount` folder is mounted (its root, its `engine/` and
  active world, every world's `maps`, `events` and `textures`), in front of the root and **behind `--extra-mount`** (a
  map build played from its folder wins). Named mods work on development roots so that they can be tested
  headless; the loose layout still does not.
- Android has no mods folder.

The choice is made once per start and kept: a world switch mounts the same mods again; a new game or a load keeps the
mods of this start. Mounting at another time would change files under a running game and its loaded tables.

With no `mods` folder nothing is read beyond one directory check, nothing is mounted again, and no world or ruleset
manifest is read for mods: the start is the same as without this feature. With only the loose layout the folder is
listed once (the loose layout listed it already) and nothing else changes.

## The switch

The debug console's `mods` command (a player-facing Mods page in the menus is not built: the menus follow the approved
Carved Obsidian design, so a page is a design task of its own):

- `mods` / `mods list`: the mods on at this start, in order, with name and version; the others as off, refused (with
  the reason) or listed but not installed; and what `enabled.yml` now says for the next start.
- `mods enable <id>`: adds an installed mod to the end of `enabled.yml`. `mods disable <id>`: takes it out.
  The reply says the change takes effect at the next start of the game, and that until then this start's mods stay,
  also for a new game or a load.

The command only reads or writes `enabled.yml`: it does not mark the playthrough as assisted.

## Table rows

A mod's `tables` entries are composed with the rulesets' machinery (`game/content/ContentTableComposer.h`):

- `override`: the rulesets' override format, a `key<TAB>column<TAB>value` header and one changed cell per line. The key
  is a row's first cell; the column is `#<index>` (what the studio writes) or a name from the table's first row.
- `append`: whole rows in the table's own layout; each key must be new.

They apply wherever a ruleset's table contributions apply (`GameDataLoader::applyActiveRulesetTable`: `map_stats.txt`,
`decoration_data.txt` and every table read through `loadTextTableRows`), after the active ruleset's own, mod by mod in
the enabled order. Two mods adding map_stats rows therefore compose instead of replacing each other's table; two mods
adding the same key, or changing a row that is not there, refuse the later one.

The start checks the rows against the tables as mounted without a ruleset (and parses a changed `map_stats.txt` as the
game does). A ruleset that is chosen later can still make a mod's rows fail (it adds the same key): the game then
leaves that mod's rows of that table out, logs `Mods: rows left out of <table> under ruleset <id>: <id>: <reason>`,
and goes on.

A mod may also bring a whole table file under `engine/data_tables/`; it replaces the table like a loose file, and the
mods' rows then apply on top of it. Rows for a world's own tables (`worlds/<world>/data_tables/`) are not supported.

## Id ranges

Each mod that is on is checked, in the enabled order, against:

- every mounted world's `world.yml idRanges` and every available ruleset's `ruleset.yml idRanges` (all rulesets, so
  the result does not depend on which one a game later picks): an overlap in a domain refuses the mod;
- its own `idRanges.maps`: a `map_numbers` entry outside it refuses the mod;
- the mods before it: an overlapping range, a map number another mod takes or whose range holds it, a range that holds
  another mod's map number, or the same new map (world and file) refuses it.

A refusal is never silent: one log line (`Mods: <id> is refused: its monsters ids overlap those of world mm9`) and
the console's `mods` list.

## Saves

- A shipped map that a mod changes (a scene overlay that adds, moves or removes spawns, destructibles, movers and the
  like) has another layout identity with the mod on than off: its saved state is reset when the party enters it, as for
  a rebuilt map (`devdocs/SAVED_MAP_STATE_IDENTITY.md`). A script overlay or table cell does not change the identity.
- A new map a mod brought is gone while the mod is off (no map_stats row, no files). Its saved state stays in the save
  as data and is used again when the mod is back on. A travel into it fails as any travel to a missing map does: the
  party stays where it was.
- A save made **on** such a map is refused before anything of the game in progress changes: the status line says
  `Quick load failed: this save was made on <map>, a map that is not installed (a mod that brought it may be off)` and
  the log `Load refused: the save's map <map> is not installed`. Switching the mod on again and restarting loads it.
  (Before this change such a load replaced the game in progress and then failed to build the map.)

Saves do not record which mods were on; a save made with a mod loads without it as described.

## Scenarios

Scenarios play no mods unless they say so with a root key `mods`:

- `mods: {fixture: <folder beside the scenario>}`: the folder is copied into a temporary folder of the run (removed at
  its end), so `mods enable`/`mods disable` in the run change only the copy; `enabled: [ids]` beside `fixture`
  replaces the copy's `enabled.yml`. Fixtures: `tests/scenarios/mods/fixtures/mods/` (hand-written: a map_stats.txt
  cell and a script overlay of Goblinwatch, a mod refused for MM9's monster ids, a listed mod that is not installed),
  played by `tests/scenarios/mods/named_mod_on.yml` and `named_mod_off.yml`.
- `mods: {user_data: true}`: the mods folder of `--user-data`, as the game reads it (end-to-end runs of a studio
  install).

The scenario runner mounts the mods first, for its own table loader, and the game's start then reads the same folder
and keeps the same mounts; so a scenario's log names the mods twice.

## Not built yet

- A Mods page in the menus (see the switch).
- Switching mods without a restart.
- `requires` (dependencies between mods) and mod versions compared with what a save was made with.
- Rows for a world's own tables, and named columns from a header row other than the first.
- Checking a mod's rows under each ruleset at the start (they are checked without one; see table rows).
- Named mods on Android.
