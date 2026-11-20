# Agent evaluation: results

Tasks: [tasks.yml](tasks.yml). Each run is a fresh agent that may use only the tools (`host/src/call.mjs`), with no
access to the studio's sources, examples, tests or documents, or to the game's files. The check decides whether a
task is done; the agent's friction list decides what changes in the tools.

## Run 1, 2026-11-12 (the tools as first written)

| Task | Done (by the check) | Tool calls | Notes |
|---|---|---|---|
| rewire-goblinwatch | Yes: `check_rewire.sh`: 16 of 16 replaced handlers test and do the same, no other handler changed. 13 switch presets, 1 teleport preset, 2 scripts | about 85 | The agent also wrote a 22-click playtest of its own: same door states on the shipped and the built map |
| rewire-wells | Yes: 5 of 5, no other handler changed. All five as scripts: the presets could not say a gold or stat condition | about 75 | Wrote a 14-case playtest reading gold, variables and autonotes: same log both ways |
| slice-edit | Yes: one transaction (speed 64, a light of radius 400), validates, builds | about 30 for three tasks | |
| placeholder | Yes: searched the catalogue (nothing fits), added a placeholder, the build warns about it | | |
| review-pin | Yes: found that the project already does what the note asks (the lever opens the gate once), resolved the pin with that reply, changed nothing | | Needed build, install and flow to learn what the project does today |
| outside-edit | Yes: named the edit (door:gate speed), undid it, showed the revision was the earlier one again | about 7 | |
| find-defects, opening-order | Yes: events 38, 54, 57, 58; five steps, no items needed, nothing unreached | about 35 | Could not answer "which is the vault's last door": no tool names a place |

Every task was done. The price was the number of calls and several things found only by trial.

### What the friction lists changed

Fixed the same day:

- **`map_flow` showed only the first four arguments of a call**, so two handlers could look the same and differ
  in the game (`CastSpell` has nine). It now shows all, and a teleport its direction and the rest. The comparison
  of shipped and overlaid handlers (`tests/compare_flows.py`) therefore compares all of them; the four overlays
  made so far still pass.
- **The flow sandbox accepted any `evt.` name and any selector**: `evt.Nonexistent()` and `evt.Set("MapVar2", 0)`
  passed the build and failed in the game. The names of the game's functions are now read from the game's own
  registration when the studio is built; a call to anything else, a selector that is not a number and a call of
  something that is not a function are build issues for an overlay and audit findings for a map. All 247 shipped
  maps have none of these (other Lua errors in the sandbox, 460 of them, come from the sandbox's game functions
  returning nothing and are not reported).
- **`map_query` list `events` answered with the lock's table** instead of the project's events; an unknown id was
  not an error. Both fixed; an id now also gives its engine number (the event number `map_flow` takes).
- **`map_playtest` hid the Lua error** of a failing step (it was on the error stream). Shown now.
- **`map_overview` counted `info` findings without showing them**, and reported 0 chests for a built map (its
  chests are scene loot containers; now counted as `loot_containers`).
- **`map_edit`**: a dry run answered `applied: false` with a new `revision` (now `revision_if_applied`); a new file
  showed as "file added" without what it added; a changed field did not show its values (now `speed (96 -> 64)`).
- **`map_build`** returns the generated overlay script; a project that replaces nothing says so.
- **`map_api`** gained "lua" (what a script may call, with every function name of the game), "playtest" (a scenario
  to start from, the helpers of its Lua steps, and the advice to change one thing on purpose), and `section` for one
  list of a schema. The `exit` preset, the `assets` variable of `map_exec`, the order of a handler's lines and what
  `sets` and conditions cannot say are written where an agent reads them.
- **`map_assets`** matches every word of the query instead of the whole text.
- A preset's extra `lua` ran before its text although the schema said after. It runs last now.
- A handler path that does nothing printed as an empty line; it says "nothing".

Open, with where they belong:

- **Conditions the schema offers and the build cannot lower** (gold, a stat, time ...) and `sets` to a value other
  than 1: the wells needed five scripts for this. S3 (the wiring vocabulary grows with authoring).
- **No picture or flow of a project without building and installing it**; no resolved positions of objects placed
  by relation. S3 (project previews).
- **`map_render` cannot zoom or crop**; labels pile up in a dense centre. S3.
- **Nothing names a place** ("the vault"): the solve gives sector numbers. The plan file of an import has spaces;
  joining them to the solve is S3.
- **Scenario helpers**: `mapvar()` answers 0 for numbered variables and `status()` came back empty for the agents.
  These are the game's scenario runner, not the studio; to be looked at with the next playtests (PLAN 10b item 4).
- **The door states' names** ("close" opens the way on some doors) are the engine's. The tool text now says so;
  a per-door "this state clears the way" needs the reachability data joined in. S3.

## Run 2, 2026-11-12 (after the fixes)

The wells task again, with a fresh agent: done (5 of 5 by the check, again as five scripts), about 75 tool calls,
the same as before. What changed is the quality of the evidence, not the effort: the agent proved that its overlay
is what runs (a marker text seen on the overlay and not on the shipped map, as the playtest guide suggests), and the
build stopped two wrong selectors that the first run's build had let through.

Its friction, and what was done:

- The new "lua" reference claimed `VAR_` constants; the scripts' selectors are bare globals (`Gold`, `HP`,
  `BaseLuck`). The agent had to dump the globals to find them. The text and the build's message are corrected, and
  say plainly that the list of helpers is not complete. **A generated reference of the scripts' selectors and
  helpers (from the game's support script) is the fix; S3.**
- The build's message did not name the identifier that was nil. Lua cannot give it after the fact; the message now
  says what nil means.
- `status()` in a playtest returns the status line only right after the click; the guide described it wrongly
  (taken from the scenario README). To be corrected with the scenario helpers (PLAN 10b item 4).
- A playtest cannot set gold, stats or numbered map variables, so branches that need them rest on the flow
  comparison. Same item.
- No preset reaches gold, stats or autonotes: as in run 1, S3.
- `map_build` shows a block of zero geometry counts for an overlay; `map_query` gives no number for an overlay's
  event (it is the number of the event it replaces); no "replace" operation; import has no tool of its own. Small,
  not done.

**Reading of the two runs:** the tools are sufficient and now refuse the wrong scripts they first accepted, but a
rewire still costs about 75 calls, most of them spent finding out how to write in Lua what the flow shows. The
next gain is not in the tools' plumbing but in presets that cover what handlers commonly do and in a generated
script reference.

## Run 3, 2026-11-12 (S3: presets with conditions and effects, a generated script reference)

The wells task a third time, fresh agent: done (5 of 5 by the check). **31 tool calls instead of about 75, and no
script at all** (five text presets; one carries a one-line `lua` effect for a call no effect names). The agent again
proved by a marker text that its overlay is what runs.

Its friction: the "import" help still said gold and stats need a script (corrected); `status()` and the party
helpers of a playtest were described wrongly or not at all (corrected in the guide); a playtest cannot read luck,
hit points, spell points, autonotes or numbered map variables, and cannot set gold, so some branches rest on the
flow comparison (the scenario runner's helpers; PLAN 10b item 4); an overlay's build still prints a block of zero
geometry counts; an imported project is named after its map, so its overlay file is `oute3_oute3.lua`.

### author-dungeon (new in S3)

A fresh agent built "The Old Crypt" from one paragraph, through the tools only: an L-shaped antechamber, a bent
corridor, eight steps down 200 units, a crypt with two pillars and a dais, a side chamber behind a door that only a
lever opens, two chests, a light in every room. By the check: it builds (5 rooms, 130 faces), the solve reaches
four rooms at once and the side chamber only after the lever, and the agent's own playtest takes both chests in the
game. It looked at its render and moved two pillars that stood in front of the side door. 59 tool calls.

It also found the milestone's worst defect: **one edit made `oymap` crash and left a lock that blocked the project
for good** (the agent abandoned two folders). An event whose chest or door had been refused for another reason was
looked up as if it existed. Fixed: such an event is skipped (its object's issue stands); the lock holds its
writer's process number, and a lock whose writer no longer runs is taken over.

Its other friction, and what was done:

- A switch needed an `off` surface and a chest a `surface`, with no way to find fitting textures (`map_assets`
  finds nothing for "lever" or "chest"; the names are `t1swdd` and `ch1frntb`). Both have defaults now.
- The first edit of rooms alone was refused for lack of a start, though the tool said "rooms first"; the start is
  not a list and had to be guessed. The tool and the schema now say how to set it and to do it in the first edit.
- `ceiling` read as if it might be a height above the floor; it is an absolute z. Reworded with an example, as is
  the floor of a sloped room.
- The solve spoke of sector numbers only; for a project it now names the room of each.
- The build's own `ids.lock.yml` was reported as someone else's edit. It is recorded as the build's.
- The playtest guide did not describe `walk_to`. It does now.
- Open: renders do not draw objects (chests, switches, lights, platforms' tops are not told apart); the whole
  schema is 29 KB (ask for a `section`); `handlers` against `bound_events` in an overview is unexplained.

