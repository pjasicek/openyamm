# Rebuilding a shipped dungeon as a Map Studio project (procedure for rebuild agents)

Purpose: a rebuild is a test of the studio's vocabulary, not a copy for its own sake. If an agent can describe a
known dungeon in project files and the build comes out like the original, the same means will make new dungeons as
good. Where the vocabulary cannot say something, that is the finding. The user decided (2026-11-12) that these
rebuilds run as a self-correcting loop: build, compare with the original by tool, fix, repeat, without a person
pointing at differences.

Read first: `openyamm-studio/README.md`; `devdocs/map_studio/S3.md` (section "State at the end of 2026-11-12": what
exists, what does not, the mistakes made); the worked rebuild `devdocs/map_studio/briefs/mm7_7d06/L4/` (Temple of
the Moon: rooms.yml, objects.yml, wiring.yml, project.yml) and the test map `openyamm-studio/examples/shapes_gallery/`
(one of every room feature). Every field is described in its schema: `openyamm-studio/build/oymap schema rooms`
(also `objects`, `wiring`, `project`, `common`).

## What you produce

In `devdocs/map_studio/briefs/<key>/L4/`: `project.yml`, `rooms.yml`, `objects.yml`, `wiring.yml` (and
`ids.lock.yml`, which the build writes; keep it), plus `NOTES.md` (below). Work only in that folder and in
`output/studio_cal/<key>/` for scratch data and pictures. Give `project.yml` a `map_stats` block with an `id` of your
own (9700 + the number given in your task) and `reference: <the original map file>`.

## Rules

- **The original's frame.** Draw in the original map's own x, y and z, so the two maps can be laid over each other
  and compared point by point. Not on a 512 grid.
- **Measured shapes, not traces.** Read the original with the tools (below) and describe it: a room is its outline
  with as many points as its shape needs (a rectangle 4, a cave 8 to 30), its floor and ceiling, and its features.
  Do not copy vertex lists of the original's faces into outlines: if a room needs more than about 30 points, it is
  several rooms or it needs a feature the vocabulary lacks. Positions of doors, chests, torches and spawns may be
  taken exactly.
- **Uneven floors and roofs** (`floor_points`, `ceiling_points`): give a height where the surface changes slope,
  read from the original; not every vertex of the original's faces. A cave's floor rarely needs more than about
  25 points and its roof about 40; a room that needs more is several rooms. Where you did take the original's
  own points one for one, say so for that room in NOTES.md.
- **A script may write the project files** (the user's decision, 2026-11-12), for a first shell or for one edit
  over many rooms. It is held to the same rule as a hand: rooms as their shapes need them, numbers measured from the
  original. Keep it in `L4/gen/` (a first shell) or your scratch folder (a one-off edit) and check its whole diff.
  Once a project has hand edits, the files are the source: a generator that would write them afresh is not run
  again. Say in NOTES.md what was scripted. **After every run of a script (and any edit of the files by hand), run
  `oymap record <L4> --author agent:<your name> --label "<what it did>"`**: the change becomes a history entry with
  your name instead of an anonymous `outside` one (it also names entries an earlier read recorded as `outside`, and
  lists them; check none is another's).
- **The original's own textures**, by name, wherever a surface of the rebuild stands for one of the original's
  (`oymap metrics` lists them by area; `oymap assets <name>` gives sizes).
- **Say it with the vocabulary**; where it cannot be said, do the nearest honest thing, put what is missing into a
  `placeholders` entry or a `notes` field, and list it in NOTES.md. Do not fake a shape with a trick that will have
  to be undone (the Temple's first nave used wedge rooms and loose treads; all of it was thrown away).
- **Do not edit** anything outside your two folders. Do not build the studio or the game (use
  `openyamm-studio/build/oymap` and `build/game/openyamm` as they are; if a command fails because the binary is
  being rebuilt, wait a minute). No git commands that change anything. No `rm` with wildcards or variables.
- Run `oymap fmt <folder>` before every check: project files are kept in canonical form.

## What the measure does not see (the user's walk through Gharik's Forge, 2026-11-13)

The Forge measured 99.6 % and its playtest passed every run, and the user still found, in one walk: levers of the
wrong kind (the original's are small 3D handles that move; the studio built flat plates), a lever whose picture did
not flip back, chests textured wrongly (the original lays a left end, a middle and a right end on front and top),
things that stood under a lift instead of on it, and faces flickering in one plane. `oymap compare` looks at walls,
floors and ceilings from the floor; a playtest checks that events run. Neither sees what the player sees at the
things he uses. So, in every round and every new dungeon:

- **Every interactive thing takes the original's form, not the studio's default:** levers, buttons, chests, doors,
  clicked panels and blocks. Read its faces in the original (`oymap export`: textures, sizes, which door record moves
  them) before you write it, and say in NOTES.md for each kind what the original has and what you built.
- **Look at every kind of interactive thing in the game,** in a picture from where a player uses it, before and
  after it is used (a lever pulled and pulled back, a chest from above, a door half open, a lift at the top and the
  bottom with what stands on it). Not only at the measure's worst places.
- **Things over moving parts:** check in the game that what stands on a lift, bridge or deck is on it at the start.
- **From the user's walk through the Hive (round seven):** panel walls on the original's exact corners, panels at
  full texture width (a wall a few units askew breaks a carved picture at its middle strip); where a tunnel opens onto
  side rooms, build that stretch as a room so the original's wall ends and posts between the openings exist; every
  side door of a sloping tunnel walked with `oymap probe` and the playtest (a doorway above the tunnel floor cannot be
  entered).
- **Untouchable liquids are ways down; secret faces counted** (the user in the Lab, 2026-11-13): a water or floor face
  over a room below that the original marks untouchable is a fall, not a floor: read every such face's attributes in
  the export. Match the original's `secret_faces` (`oymap metrics`).
- **Caves curve; lights hang from something; torches on walls** (the user in XD-05, 2026-11-13): a cave passage
  bends in several segments, never a square 90-degree turn; a lamp hangs from a ceiling or beam or stands on the
  floor, never in the air; torches go in wall sconces at the shipped height, not on poles stuck in the floor before a
  wall; wide caverns have stalactites overhead as well as stalagmites, narrow passages and tunnels none; nothing stands beside a door that a player cannot
  name (keyhole blocks with no key).
- **No flicker** (the user, 2026-11-13: "an automatic sanity check that no faces share the same plane, both when
  mechanisms are inert or activated"): `oymap audit` lists `geometry.coplanar` pairs (two faces in one plane over each
  other, at the start and with moving parts moved). A map is not done with any pair the project causes; in a rebuild,
  a pair the original has at the same place may stay, named in NOTES.md. Code batch ten makes the check binding
  (moving parts mid-travel too, pairs matched against the original, a strict mode that fails).
- **Where the party stands high:** take a picture from the top of every platform, flight, ledge and mover the party
  can stand on, looking round. A top that stands up into the room above puts the party's eye in another room, and
  the view goes black (the Abandoned Temple's arrival, round six); the measure scores it as perfect.
- **Flicker:** look for faces in one plane over each other near doors, movers and blocks; the build warns of them
  once the check exists.
- **Tools for this (since the eighth merge, 2026-11-13):** `oymap things <map|project>` lists every interactive thing
  (doors, levers, buttons, plates, chests, exits, teleports, clicked panels and decorations) with its textures, what
  it changes and where a player stands to use it; run it on the original and the rebuild and compare the lists.
  `python3 openyamm-studio/calibration/things_shots.py` takes a picture of each from there, before use, after one
  use and after a second. Switches take `kind: lever|button` (the originals' 3D handles and pushed blocks; `plate`
  only where the original is a flat plate) and chests `kind: ch1..ch5|7gt002|gt002|ch001..ch006`. `oymap build`
  warns of faces in one plane over each other (`geometry.coplanar` in `audit`): fix each the project causes, and
  say in NOTES.md which ones the original has too.
- **Can a player read it?** (the user's walk through XD-01, 2026-11-13): a lootable thing looks like what MM6-8
  players know as lootable (a chest, or furniture with the chest's hover name), and nothing looks like a chest that
  is not one; every clicked thing shows the hover name MM shows and has a reason to be clicked; signs open a message
  window; nothing floats (every prop stands on something, or is a kind that hangs); no picture is stretched; doors,
  buttons and plates come from the area's texture family, not the studio's defaults from another world; everything
  the brief names is recognisable as that thing. Look for each in the game, not in the files.
- **No riddles the game does not answer** (the user, 2026-11-13: MM6-MM8 had almost none; combat, mechanisms and loot
  instead; a passphrase is fine "if the answer is obvious, like in some scroll the party can read"): a typed answer
  may block the way only when the game gives it plainly before (a scroll, note, sign or person on the way); else it
  becomes a key, mechanism, fight or found thing (`devdocs/xeen/README.md`). `oymap audit` shows where each answer is
  met. Yes/no offers are fine.
- **Puzzles a player can solve** (the user at XD-04's word door, 2026-11-13: "how am I supposed to know the answer?"):
  every question, password, lock and hidden thing has its clue where a player meets it before needing it, in a form
  he will notice (a message window from a thing that shows a hover name and invites a click, a sign, a person), and
  the playtest takes the player's own route to the clue first. Name each clue and its place in NOTES.md.
- **Keys where MM players look** (the user could not find XD-04's cage ring, a small item on a table, even with a
  message on entering): a key or item the way depends on goes in a chest, or is carried by a named boss whose death
  the dungeon makes plain; never a small sprite lying about. The thing it opens says where it is.
- **Liquids move:** water, lava, slime and brew flow as the shipped ones do, on tubs, troughs and pools as well as
  floors (the user took XD-04's still green trough for acid).
- **Say why the party is here** (the user after XD-02: "I don't know the intention of it, what quest was there"): until
  the world's quests exist in the game, a new dungeon says on first entry, briefly and in the world's voice, who sent
  the party, what it seeks and roughly where; its goals (the thing to bring back, the boss) are visible on the way.
- **Monsters where they can fight:** no monster or spawn point where it cannot come out to the party or the party
  cannot reach it (XD-02's bats stuck in shelf openings high in a wall).
- **Usable from where the party is:** a switch used while riding a mover faces the deck and is within reach at that
  stop (XD-02's lever faced away from the cart).
- **No silent clicks, no riddles about the world outside** (the user's second walk through XD-04): a click that
  cannot work yet says why in a message (a hoist whose brake holds above), and a gate opened by something outside the
  dungeon (a promotion, a quest elsewhere) says plainly that it is not for now and what opens it, in the world's voice.
- **Nothing in its stand-in when the user plays:** generate the textures a new dungeon lists before it goes to the
  user's play copy; a named thing with a misleading stand-in (XD-04's slate as a stone slab) reads as nothing.
  Hanging things hang from something (a brazier's chain reaches the beam), and nothing stands inside something else
  (a skeleton in a cage with a child) unless it is meant to.
- **Room sizes of a new dungeon** (the user found XD-01 cramped, 2026-11-13): run
  `python3 openyamm-studio/calibration/scale_bands.py <built .blv> --world <world> [--assets <root>]` on every
  build. Its main rooms (the upper quarter by floor area) and their ceilings sit at least at the shipped median of
  the 161 MM6-8 dungeons unless the brief makes a room small on purpose (pens, cells, crawlways, closets); a figure
  below the shipped 25th percentile is a fault to fix. XD-01's bigger rooms measured 0.72 M square units against a
  shipped median of 1.64 M (the Pirate Outpost's 2.17 M); XD-02 0.93 M, XD-03 0.76 M.
- A map is not done when it measures well and its playtest passes; it is done when a person could play it without
  meeting a thing that looks or behaves unlike the original.

## Textures for a new dungeon (the user's look at XD-01, 2026-11-13)

A rebuild takes the original's own textures. A new dungeon has no original, and XD-01 showed what goes wrong: its
agent picked 50 textures one by one by name from 23 shipped maps of three worlds, 23 of them from no shipped dungeon at
all (ship and outdoor woods: the user saw ship windows inside a warehouse). The user: reuse shipped textures where they
fit well, generate new fitting ones where nothing fits, and "avoid making it a Frankenstein's monster". So:

- **One family per area.** Build each area (a wing, a level, a cave system) from the set of ONE shipped dungeon whose
  purpose fits (a warehouse from a wooden pirate hold, a mine from a mine, a dwarven hall from a hall), and keep
  areas few. Say in NOTES.md which shipped map each area's set comes from. The MM8 pirate maps (Pirate Outpost
  `d06.blv` and its neighbours) show a coherent wooden set (wainscot `t66b01`, planks `t66floor`, hall brick
  `t66c01a`, posts `t66abc10a`, flagstones `t66flr2`, roof `t66roof`, doors `t66b03l`/`r`); the user named it.
  A family is not a list of names: look at how its map lays each one (`t66e01s1`, the most used, is the hull of the
  moored boat, not a wall; XD-01's texture pass found it).
- **Look up where a texture comes from** before using it: `python3 openyamm-studio/calibration/texture_use.py
  <texture>` (the shipped dungeons that use it), `--map <world/map.blv>` (a dungeon's set), `--project <folder>`
  (every texture of a project with its source; textures from no shipped dungeon are flagged). A texture no shipped
  dungeon uses needs a reason in NOTES.md.
- **Look at each texture as a whole picture in the game** (a wall of it), for motifs that betray where it comes from:
  windows, portholes, signs, symbols of another place.
- **Where nothing shipped fits,** do not borrow a misfit: list it in NOTES.md under "textures to generate" (what it
  shows, size, where it goes) and use the nearest coherent stand-in meanwhile. The repository can generate textures
  (`level_generation/textures_x4/PLAYBOOK.md` is the pipeline for upscaled ones; new ones are a separate request to
  the user).

## Tools

```
O=openyamm-studio/build/oymap ; A=assets_dev
$O export assets_dev/worlds/<world>/maps/<map> --world <world> --assets $A --pretty --out x.json
                                   # every vertex, face, sector, light, spawn; with --world and --assets also `doors`
                                   # (each moving part: direction, travel, speeds, its faces and where they stand)
$O audit|metrics|solve|flow <map> --world <world> --assets $A [--reach] [--json]   # the original, as the game reads it
$O render <map> --world <world> --assets $A --out x.png --view plan|iso            # labelled picture (look at it)
$O assets <word> --assets $A --world <world> [--kind texture|decoration]
$O script-reference --assets $A --world <world>                                    # what a script may call
$O validate <L4> --assets $A ; $O build <L4> --assets $A --out output/studio_cal/<key>/build [--dry-run]
                                   # always with --out: without it the build lands in the brief
$O audit|metrics|solve|flow|render|probe <L4> --assets $A ...                      # the rebuild, built privately
$O record <L4> --author agent:<you> --label "<what>"     # after a script or a hand edit wrote the files
$O pins list|claim|resolve|reply|tour <L4> ...           # the user's pins from the game (below)
python3 openyamm-studio/calibration/compare.py <L4> openyamm-studio/calibration/originals/<key>.metrics.json
$O compare <map> --world <world> --with <L4> --assets $A --out output/studio_cal/<key>/compare   # see below
```

`oymap compare` is the loop's measure (it may not exist yet when you start: check `$O compare`; until it does, use
renders, `compare.py` and probes, and start using it as soon as it appears). It stands at points all over the
original's floors, looks in 50 directions in both maps, and reports where the rebuild's walls, floors, ceilings and
textures differ, with the worst places named. Its `shots.yml` feeds
`python3 openyamm-studio/calibration/ingame_compare.py <L4> <world> <map> <shots.yml> <out folder>`, which takes
same-camera pictures of both maps in the game with a difference sheet for each pair. Look at those sheets yourself.

MM7 map files hold no usable light radius or colour (every light reads radius 0, colour 31,0,0, brightness 31: that
is the file, the game reads the same); take positions from the export and give the rebuild's lights a radius by eye.
`solve` and `audit --reach` ride moving floors (lifts, sliding bridges) since 2026-11-12.

To play the rebuild: `$O install <L4> --build output/studio_cal/<key>/build --mount output/studio_cal/<key>/mount
--assets $A`, then a headless scenario
with `build/game/openyamm --asset-root $A --extra-mount output/studio_cal/<key>/mount --world <world>
--headless-run-scenario <file> --scenario-no-color`, run from `output/studio_cal/<key>/run/` (form:
`devdocs/map_studio/briefs/mm7_7d06/L4/playtest.yml` or `openyamm-studio/examples/shapes_gallery/playtest.yml`).

## Order of work

1. **Read the original**: audit, solve (the order it opens up), metrics, the plan and iso renders, then the export
   for measurements. Write down the room list with what each room is.
2. **Shell**: rooms, openings, levels, stairs, in the original's frame. Check after every few rooms: `validate`,
   `render` beside the original's, `audit --reach`. Every room reached, the same way the original connects.
3. **Compare and fix the shell**: `oymap compare`; fix the worst places; repeat until the geometry score stops
   rising or what is left needs a feature that does not exist.
4. **Surfaces**: themes with the original's textures, bands, per-wall surfaces. `compare`'s texture score.
5. **Objects and wiring**: start, doors (the original's door records: which are real doors, which are moving walls,
   buttons, lifts), chests, spawns with the original's slots, lights or torches, switches, events (read each
   handler with `flow --event`; use presets, conditions and effects; a script only where no preset fits). `solve`
   must open the rebuild in the same order as the original.
6. **Play it**: a scenario that walks the critical path and uses every mechanism.
7. **Pictures**: `ingame_compare` at the comparison's worst places; look; fix what is yours to fix.

Stop when another round changes little. A rebuild is never finished; say where it stands.

## Answering pins (the user's notes from the game; S5a1, 2026-11-14)

The user plays the studio's maps from `output/studio_play/PLAY.md` and, where something is wrong, opens the game's
console and types `pin <what is wrong>`. The game writes the note, where the party stood and looked (`loc`'s numbers)
and its own picture of the view into `pins_inbox/` at the repository root. Every map `oymap install` put into a play
copy has `<stem>.studio.yml` beside it naming its project, so each pin knows where it belongs. Answer pins through the
command line, with game pictures:

```
$O pins import pins_inbox                        # files each pin into its project (by the studio file, else by the
                                                 # map's name; --project <L4> when two projects build the map)
$O pins list <L4> --status open                  # text, pose, map, picture (.oymap/pins/pictures/p3.png: look at it)
$O pins claim <L4> pin:p3 --by agent:<you>       # before working on it, so no other agent does
   ... fix it in the project (oymap edit; or the files, then oymap record), build, install into a scratch root ...
$O pins tour <L4> --pin pin:p3 --out output/studio_cal/<key>/pins/tour.yml --shots output/studio_cal/<key>/pins/after
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated pins-<key> --world <world> --map <map> \
    --assets "$PWD/output/studio_cal/<key>/root" --seconds 120 \
    --set debug.screenshot_tour_path=$PWD/output/studio_cal/<key>/pins/tour.yml    # the after pictures
$O pins resolve <L4> pin:p3 --by agent:<you> --text "<what you changed, where>" \
    --picture output/studio_cal/<key>/pins/after/01-p3.png
$O pins reply <L4> pin:p3 --by agent:<you> --text "<a question, or a note>"    # no status change
$O pins decline <L4> pin:p3 --by agent:<you> --text "<why not>"                # only with a reason the user can check
python3 openyamm-studio/calibration/pins_page.py   # output/studio_review/pins.html: the user reads the answers there
```

- **The game's picture answers a pin**: the user's own picture is the before; the after is the game's picture at the
  pin's pose (`pins tour`), looked at before resolving. A studio render alone does not answer a pin, and no pin is
  resolved without the after picture having been looked at ("A fix for something the user saw is proven in the game").
- **Say what changed**: the reply names the objects and the files (`door:vault_gate`'s leaf in objects.yml, 4 short of
  the jamb now), in words the user can check in the game.
- **The fix is the project's**, never a built map's; where it is general (a word that should exist, a check), it also
  goes into this procedure or the studio's list, as for every fault the user finds.
- **Only the user accepts** (`oymap pins accept`) or reopens a pin. A reopened pin is open again with his reply: read
  it, claim it again. An agent never sets `accepted`.
- **Pins are not the source.** Claims, replies and resolutions change the pins document's own counter, never the
  project's revision or its undo; `review/pins.yml` is changed only through `oymap pins` (never by `oymap edit` or by
  hand). Pictures stay in `.oymap/pins/pictures/` (outside git); `oymap pins keep` copies one into `review/pictures/`
  only when the user wants it kept.
- **The lock keeps removed ids' numbers.** A build no longer drops the `ids.lock.yml` entry of a door, event or
  variable you removed, so an undo or a re-add gives it its old number back. `oymap lock prune <L4>` drops them: run it
  when a build says a table has no free number left (it names the retired entries), or when the lead asks before a map
  is shipped; never as a routine step.

## NOTES.md (the product, as much as the project)

- The scores: `compare`'s totals at the start of each round and at the end; `compare.py`'s line; rooms reached;
  whether the playtest passes.
- **Gaps**: everything the vocabulary could not say, most harmful first, each with where it occurs in this map, what
  you did instead, and what field would have said it. Be exact: "a floor opening onto the room below (the reactor
  shaft, 512 square, between level 2 and level 1)", not "vertical connections".
- **Tool defects**: every wrong result, crash, misleading message or check that should exist, with the command that
  shows it.
- What you were unsure of in the original (a room you could not read, a mechanism you did not understand).


## Projects edited by hand (S5b1, 2026-11-15)

A project whose `project.yml` carries `edited_by_hand` (a person changed it in the studio, or someone ran
`oymap protect`) is changed only by operations (`oymap edit`, MCP `map_edit`, the request list), never by writing its
files. Read `hand_objects` in every edit result (objects a person changed last that your change touches) and leave
them alone unless the person asked. Never set or clear the mark: only a person does. Rename an object with the
`rename` operation, never by changing its id in the files (the lock and pins follow a rename).


## Playtests never assume room in the packs (Temple of the Moon, 2026-11-15)

The scenario's default party is one member with one pack, and chest loot is random every run (the game seeds chests
per session, not from the scenario's seed). "Take all" leaves in the chest whatever does not fit, so a playtest that
loots several chests and then checks for an item fails now and then. Before looting a chest whose item a step checks,
empty the packs (as the library step does) and check that item before looting further chests.
