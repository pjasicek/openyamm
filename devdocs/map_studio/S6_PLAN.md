# S6: MM9 profiles and extras (plan)

Status: 2026-11-15, written at the start of S6 by the S6 agent (the user's go relayed at 13:27). PLAN.md section 12:
"Open-air BLV terrain, water volumes, ladders, destructibles, pulsing lights, cinematics timeline, MCP App viewer,
named mods and sharing"; accepted when "an MM9 region [is] edited as an overlay; a mod installed and switched off in
the game". S5 deferred to S6 (S5_BROWSER_EDITOR.md 6.2 D14, 6.3, 6.4 "Deferred beyond S5"): named mods and sharing,
world projects and the project list's world view, lighting bakes as jobs, overlay projects that say more than
handlers, map numbers proposed from the manifests' ranges.

The game side is not changed by S6's agent. Every game change S6 needs is listed in section 3 with what, why, the
files and the risk, for the lead to put to the user; until one lands the studio does without the feature that needs it
(PLAN.md 10a's rule), and says so in its warnings.

## 1. What exists before S6 (read from the code, 2026-11-15)

| Engine feature (doc) | Scene key | Game: in a scene overlay? | Studio before S6 |
|---|---|---|---|
| Ladders (INDOOR_ROTATING_MOVERS_AND_LADDERS.md) | `ladders` | **no** (`applyOverlayFromText` has no `ladders`) | `objects.yml ladders[]` (upright, `grab_at_top`); no `grab_in_air`, no leaning ladder |
| Pulsing lights (INDOOR_PULSING_LIGHTS.md) | `pulsing_lights` | yes, the list **replaces** the base's | `lights[].pulse` |
| Ambient sounds (AMBIENT_SOUNDS.md) | `ambient_sounds` | yes, replaces | `sounds[]` (no `day_only`, `night_only`, `sprite`) |
| Destructibles (INDOOR_DESTRUCTIBLES.md) | `destructibles` | yes, replaces | none |
| Water volumes (MM9_WATER_SWIMMING_DESIGN.md) | `water_volumes` | yes, replaces | none (`floors[].kind: water` is only the face bit) |
| Open sky, terrain, daylight, fog, mist (INDOOR_OPEN_SKY.md, MIST.md) | `sky`, `terrain`, `daylight`, `fog`, `mist` | yes, each replaces | `atmosphere.yml mist` only |
| Spawns | `spawns` | add (`authored_content.spawns`), remove (`removals.spawns`) | new maps only |
| Actors | `initial_state.actors` | `actor_overrides` only (no adding) | new maps only |
| Cinematics (mm9_rework/MM9_CUTSCENES.md) | `<stem>.cinematics.yml` | **no overlay file** | none |
| Baked lighting (INDOOR_BAKED_LIGHTING.md) | `<stem>.lighting` | keyed on the BLV's geometry only: an overlay keeps a bake | none (deferred from S5) |

Overlay projects (`oymap import`) today replace map handlers only (`<stem>_<id>.lua`). The game applies indoor scene
overlays named `<stem>_<name>.scene.yml` in name order, then the ruleset's (MAW's MM9 pack reserves are
`<stem>_zz_maw.scene.yml`); a list key in an overlay replaces the base list, so an overlay that changes one pulsing
light writes the whole list.

The game's parser for cinematics (`parseCinematicLibrary`) is in `game/gameplay/CinematicRuntime.cpp`, which includes
`EventRuntime.h`: the studio cannot link it without dragging the event runtime (PLAN.md 1, "tangled"). Mods: the game
mounts `<install>/mods/engine` and `mods/worlds/<w>` as one merged folder (`AssetFileSystem::mountMods`); a table
file there replaces the whole table; there is no manifest, no enabled list and no way to switch one off.

## 2. The items, in build order

Each item: what the studio needs (schema words, lowering, UI, request list), what in the game (section 3), and its
exit criteria. Every item lands with unit cases (`tests/S6Tests.cpp`), contract cases where it adds or changes a
method, Vitest cases where it adds UI, and screenshots looked at before reporting. The standing checks after each:
all unit cases, the 22 calibration projects building identical map bytes to `build/oymap`, native against wasm 22/22,
the contract suite and `tests/s5_checks.sh`.

### 2.1 O: overlay projects that change a scene (the region profile)

The first exit criterion. An imported shipped map becomes a project that can say, besides handlers, what the game's
indoor scene overlay can say.

- **Import** (`core/Import.cpp`): `profile` from the scene (`sky.mode: open` with `terrain`: `region`; open sky
  without terrain: `city`; else `dungeon`); the base scene's things under stable ids in `ids.lock.yml`:
  `pulsing_lights` (`light:p<key>`), `ambient_sounds` (`sound:a<key>`), `destructibles` (`destructible:k<id>`),
  `water_volumes` (`water:<id>`), spawns (`spawn:s<index>`). The lock keeps their numbers, as it keeps doors and events.
- **Words** (objects.schema.json, overlay projects only; refused in a project without `base`): `base_changes[]`
  (`of:` a base thing's lock id plus the fields it changes: `hp`, `damage_enabled`, `sound`, `volume`, `radius`,
  `color`, `on` ...), `base_removals[]` (lock ids), and new things placed by an absolute `position: [x, y, z]`:
  `lights[]` with `pulse` (a scene pulsing light; a key from the lock's range 49000+ unless given), `sounds[]`,
  `spawns[]` (monster slot and count), `destructibles[]` (on base faces by their `cog`, or base decorations by
  `decoration_cog`), `water[]` (pieces as polygons with top and bottom). atmosphere.yml: `fog`, `daylight`, `sky`
  (open sky block), `terrain` (the terrain block, a material file of the world by name), `mist` (exists): each
  replaces the base's.
- **Build**: `<stem>_<id>.scene.yml` (`kind: indoor_scene_overlay`) holding only the keys the project touches, each
  list as the base's with the changes, removals and additions applied (the game replaces lists); checked by the game's
  own `IndoorSceneYmlLoader::applyOverlayFromText` against the base scene when the build has an asset root; the Lua
  overlay as before. `install --mount/--root` copies both; never into `assets_dev`, never over a converter's file
  (the overlay is a file of its own; MM9's converter outputs are not touched: AGENTS.md MM9 map Lua rule).
- **Ladders, cinematics, new actors, new items in an overlay**: refused with a message naming the game change
  (section 3, G1, G2, G5).
- **UI**: the overlay's things in the plan view (points at their positions, base things it changes or removes
  marked); the schema inspector edits them (D5); `view.layout` lists them. Request list: no new method (edits are
  `edit.apply` on `objects.yml`).
- **Exit**: Isle of Ashes (MM9 region) imported; an overlay that adds a pulsing light and an ambient sound, changes a
  destructible's hit points, removes a spawn and replaces one handler, made by operations; built, installed into a
  mount, loaded by the game headless from the mount with asserts on the light, the destructible and the handler;
  `assets_dev` untouched; a screenshot of the region with the overlay's light in the game and one of the plan view.

### 2.2 D: destructibles in new maps

- **Words**: `objects.yml destructibles[]`: `id`, `of` (a platform, wall panel, plate, decoration, or a door's leaf by
  id: its faces' cog, a decoration's sprite key), `hp`, `damage` (bool, default true), `trigger_only`, `sound`,
  `material` (stone, wood, glass, metal: the effect and a default sound), `effect_scale`, `on_destroyed` and
  `on_damaged` (wiring event ids). Effects `{destroy: id}`, `{damage: {of, amount}}`, `{breakable: id}` /
  `{unbreakable: id}`; condition `{destroyed: id}`. The lock keeps destructible numbers (`destructibles`).
- **Lowering**: cogs for the named faces (the lock's `cogs`, as `set_texture` uses), the scene list, centres from the
  faces' bounds; `evt.DestroyDestructible`, `evt.DamageDestructible`, `evt.SetDestructibleDamage`,
  `evt.IsDestructibleDestroyed` in handlers. A destructible between two rooms without an opening is warned of (the
  game's "seals rooms" rule: a broken brush leaves a hole that is still a wall to sight).
- **Exit**: a test project with a breakable board across a doorway and a breakable barrel opened by an event; the
  game's parser accepts the scene; a headless scenario breaks both (`destructible <id> state` broken).

### 2.3 W: water volumes in new maps

- **Words**: `objects.yml water[]`: `id`, `of` (a room, level or region: its outline) or `outline`, `top` (the
  surface), `bottom` (default the floor), `liquid` (water, lava), `tint`, `current`, `fog`. The surface itself is the
  author's (a platform with `solid: false` and a liquid texture); the build warns of a volume whose top lies on a solid
  floor (no swimming there) and of a liquid surface over no volume.
- **Exit**: a pool in a test project, the scene's `water_volumes` accepted by the game's parser; a headless scenario
  puts the party in the pool and reads its water state.

### 2.4 L: ladders and pulsing lights completed

`ladders[].grab_in_air`, `top_at` (a leaning ladder: the top's point when not straight above the foot); `sounds[]`
`day_only`, `night_only`, `sprite` (a decoration whose shown state switches it); `lights[].key` (the number
`evt.SetLight` uses, kept in the lock). Exit: unit cases and the game's parser on a test project.

### 2.5 C: cinematics

- **Words**: `wiring.yml cinematics[]`: `id`, `skippable`, `letterbox`, `shots[]` (`seconds`, a camera `at` [x, y, z]
  or `from` an object id with `offset`, an aim `look_at` (point or object id) or `yaw`/`pitch`, `fov`, `keys[]` for a
  moving camera, `easing`), `cues[]` (`at` seconds; `event` (a wiring event id), `sound`, `subtitle`, `fade`, `shake`,
  `actor` (a placed monster's id) with `show`/`hide`/`move`/`face`). Effect `{cinematic: id, then: <event id>}`
  (`evt.PlayCinematic`), `{shake: ...}` exists.
- **Lowering**: `<stem>.cinematics.yml` (format_version 1, `kind: openyamm_cinematics`) with object ids resolved to
  positions and actor indices; checked by the studio against the game's format rules (ranges and keys as
  `parseCinematicLibrary` enforces them) and, when the game's parser is cut out (G4), by that parser.
- **UI**: a Cinematics panel: shots and cues on a time ruler, a shot's camera taken from the 3D view, the 3D view
  played along the shots (camera keys interpolated as the game does: smoothstep, linear, spline).
- **Exit**: a cinematic in a test project, played in the game headless (`cinematic list` shows it; its event cues
  run); the panel screenshotted; a skip runs the remaining event cues.

### 2.6 M: named mods and sharing (studio side)

- **Manifest** `mod.yml` (`schema/mod.schema.json`): `id`, `name`, `version`, `author`, `description`, `worlds`,
  `maps` (new maps and overlays with their files), `tables` (the rows a mod adds, as the ruleset's table
  contributions: `override` patches with an `append` file, so two mods adding `map_stats.txt` rows do not clash),
  `idRanges` (map numbers, quest bits), `requires`.
- **Commands and methods**: `oymap mod pack <project>... --id <mod> --out <folder>` (the builds, the manifest, the
  row patches; `--zip`), `oymap mod install <mod> --mods <install>/mods [--layout named|merged]` (`named`: the proposed
  game layout `mods/<id>/`; `merged`: today's one folder, with whole tables and the clash warning), `oymap mod list
  <mods folder>`; request list `mod.pack`, `mod.list`; the hosted page's "mods folder" export writes the same layout.
  The free map number for a new project comes from the world's and mods' declared ranges.
- **Exit**: a mod of two projects (a new dungeon and the Isle of Ashes overlay) packed, installed in the merged
  layout into a scratch install, and loaded by the game; the named layout written and listed. **"Switched off in the
  game" is not reachable without G3**, the game's named mods.

### 2.7 A: the MCP App viewer

- `ui://openyamm/viewer` (MCP Apps: a `text/html;profile=mcp-app` resource; tools `map_overview` and `map_render`
  carry `_meta.ui.resourceUri`): one self-contained page that draws a project's plan (rooms, objects, pins) from the
  tool's structured result, with pan and zoom, and asks the host for `map_overview` of another revision through the
  app bridge. The host serves it from `host/src/viewer.html`.
- **Exit**: `resources/list` and `resources/read` give it; the tools name it; a host test drives it in headless
  Chrome with a fake host and the screenshot shows a map's plan.

### 2.8 S: open-air BLVs for new maps

atmosphere.yml `sky` (open, preset, view, view distance), surfaces `sky: true` (the faces drawn as open sky),
`daylight`, `fog`, `footsteps` by texture; the region profile's terrain block for a new map needs a weights
rasteriser (`terrain_blend.py`'s job) and is left for later unless time allows. Exit: a test courtyard open to the sky
built, accepted by the game's parser, and pictured in the game.

### 2.9 Deferred from S5, if time allows

World projects (`world.yml`, `travel.yml`) and a world view in the project list; lighting bakes as jobs
(`tools/lighting/bake_indoor.py` on a project's build, local mode only).

## 3. Game changes S6 needs (not made by S6; for the user)

| # | What | Why | Files | Risk |
|---|---|---|---|---|
| G1 | Scene overlays may carry `ladders` (replacing the base list, as the other MM9 lists) | an overlay adds or moves a ladder | `game/maps/IndoorSceneYml.cpp` (`applyOverlayFromText`) | small; lists are map data, never saved |
| G2 | Cinematics overlays: `<stem>_<name>.cinematics.yml` merged by cinematic id after the map's own | an overlay adds or replaces a cutscene of a shipped map | `GameApplication::loadMapCinematics`, `SceneOverlayPaths` | small |
| G3 | **Named mods**: `mods/<id>/mod.yml` + `mods/<id>/{engine,worlds}`; an enabled list (`mods/enabled.yml` or a settings key) and a Mods page or console command to switch one off; table contributions from a mod's manifest through the ruleset's `ContentTableComposer` (override and append), id ranges checked against worlds | PLAN 10b item 3; the S6 exit "a mod installed and switched off in the game"; two mods adding map rows today clash | `engine/AssetFileSystem.cpp` (`mountMods`), `game/content/*` (manifests, table composition), settings, a UI or console entry | medium: mount order, table composition at start, saves of maps a disabled mod provided (the map is gone: the save's map state must be dropped as for a rebuilt map) |
| G4 | Cut `parseCinematicLibrary` and the format types out of `CinematicRuntime.cpp` into a file without `EventRuntime.h` (move only, as cuts G1-G5 of PLAN 10a) | the studio checks cinematics with the game's own parser | `game/gameplay/CinematicRuntime.*`, a new `CinematicLibrary.*` | small, move only |
| G5 | Scene overlays may add actors and items (`authored_content.actors`, `items`) | an overlay places a monster or an item on a shipped map | `IndoorSceneYml.cpp`, `OutdoorSceneYml.cpp` | medium: actor indices of the base must stay, saves of the map keep its actors |

## 4. Order and stopping points

O, D, W, L, C, M, A, S, then 2.9. O alone meets half of the exit; M needs G3 for the other half. Each item is whole
before the next starts; what remains at the end is listed in S6's record with its reason.

## 5. State after the first S6 run (2026-11-15, the S6 agent)

| Item | Built | Exit | Met? |
|---|---|---|---|
| O overlay scene projects | import of the scene things and the profile; objects.yml `scene` (lights, sounds, spawns, destructibles, water, changes, removals); atmosphere.yml `open_sky`, `scene_fog`, `daylight`, `terrain` (+ `mist`); `<stem>_<id>.scene.yml` checked by the game's overlay reader; install and removal of a stale overlay; `view.overlay`; the drawer's Overlay tab; `oymap build` says the scene counts | Isle of Ashes (MM9 region) overlay: a pulsing light, a sound, a destructible added, one changed, a sound changed, a spawn removed, a handler replaced; built, installed into a mount, loaded headless with asserts (`output/studio_s6/isle_overlay.yml`); the control run without the mount fails; a picture pair with the beacon's light (`output/studio_s6/shots_isle/`) | yes; the edits were written as files, not through the browser's tools (the generic `edit.apply` covers the `scene` lists; no bespoke tool) |
| D destructibles | `objects.yml destructibles`, effects `destroy`, `damage_destructible`, `breakable`, `unbreakable`, condition `destroyed`, wiring `trigger: call` | test map's barricade and barrel break headless and run their events | yes |
| W water volumes | `objects.yml water` (`of` a room or level, or `outline`) | the party sinks into the test map's pool headless | yes |
| L ladders, sounds | `grab_in_air`, `day_only`, `night_only`; leaning ladders not built | parser accepts | partly (leaning ladders left) |
| C cinematics | `wiring.yml cinematics`, effect `cinematic`; `<stem>.cinematics.yml`; Cinematics tab (timeline, camera at a scrubbed time) | the game loads and plays it on arrival, the done event runs; a skip still runs the event cues | yes, checked by the studio's rules and the game run (the game's parser in the studio waits for G4) |
| M mods | `schema/mod.schema.json`, `oymap mod pack/install/disable/enable/list` (merged and named layouts, table rows composed) | a mod of the test map and the Isle overlay packed, installed merged, both maps played from it, switched off (the overlay gone), on again | studio side yes; "switched off in the game" needs G3 (the game mounts `mods/` only on packaged installs and has no switch); the native core cannot read a player's install's tables (packages) |
| A MCP App viewer | `ui://openyamm/viewer`, tool `map_view` | resource and tool listed and read through the SDK's client; the page drawn in a stand-in host (`output/studio_s6/shots_viewer/`) | yes; not tried in a real MCP Apps client |
| S open air for new maps | surface `sky: true`, the scene blocks of atmosphere.yml in a new map | the test map's yard draws the sky in the game | yes, without terrain (no weights rasteriser) |
| 2.9 world view, bakes as jobs | not started | | no |
