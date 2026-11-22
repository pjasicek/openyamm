# Writing the Xeen guide's walkthroughs

The Xeen guide (tools/xeen_site, built like the MM9 guide in tools/mm9_site) renders hand-written walkthroughs from
this folder: the main story by act in `act1.yml` ... `act6.yml`, and the side and promotion quests as flat lists in
`side_*.yml` and `promotions.yml`. `build_site.py` reads every `*.yml` here (acts first, the rest by name) and checks
every quest id, map, marker type and person.

## Reader and tone

A player on a blind first playthrough of the World of Xeen as built in OpenYAMM (an MM6-MM8-style world on the story
of Might and Magic IV and V). They want to know exactly what to do: where the giver stands, where to go, what to
click, kill or carry, how each puzzle or door is solved, traps to expect, the order of things, what is easy to miss,
and where to report. Concise and factual, no story retelling, no headings inside steps. Plain sentences, second person
("Take the road north out of Vertigo"). 3-8 steps per quest (a long quest may have more, never padding); tips only
for things genuinely useful. Use game units only where a distance matters; prefer landmarks and compass directions.
No riddle is left to the reader: when the game asks for a word or an order, the step gives it and says where the game
itself shows the answer.

## Sources, in order of authority

1. **The playthrough segments** are what actually works, step by step, in the built world:
   `tests/playthrough/xeen/NN_*.yml` (the main story, M1-M42 in segments 01-99, read with its `README.md`),
   `tests/playthrough/xeen/promotions/*.yml`, `tests/scenarios/xeen/side_quests/*.yml` (one or more per side quest).
   Each step names the map, where the party stands (positions), which NPC topic it clicks, which event it fires and
   what it checks afterwards. Translate positions into landmarks with the map's points in guide.js (below).
2. **The quest files**, `assets_dev/worlds/xeen/source/quests/<id>.yml` (format
   `devdocs/xeen/formats/QUESTS_FORMAT.md`): topics with their texts and conditions, hooks with `where` (where the
   thing is) and their player texts, qbits and journal lines, rewards. The NPC files `source/npcs/*.yml` and town files
   `source/towns/*.yml` (who lives where, teachers, shops).
3. **The map scripts**, `assets_dev/worlds/xeen/events/maps/<map>.lua` (events by name; `XeenQuests.hook(...)` calls
   name the quest hook) and `events/common/xeen_common.lua` (mirrors, pyramids, stages, promotions, genie lamps,
   tolls), `events/common/xeen_quests.lua` (the compiled quest logic).
4. **Lane A3's records**: `devdocs/xeen/lanes/A3.md`, `devdocs/xeen/QUESTS.md` (the design: M1-M42 in six acts, side
   quests, promotions §3, Newcastle and Castle Kalindra §4), `devdocs/xeen/ORIGINAL_LINES.md` (the ledger of what was
   ported from the original Xeen text and what changed), `devdocs/xeen/DECISIONS.md`.
5. **The original game's data**, as A3 ported it: `reference/mm4_5_world_of_xeen/unpacked/` (events
   `events/.../mazeNNNN.evt.json`, texts `text/xeen|dark/aazeNNNN`). Use it only to understand intent; the built world
   wins where they differ (the sources' comments say when something changed on purpose: describe the built world).

Where the sources disagree or a fact stays unclear, do not guess: describe what the playthrough does, and list the
question in your final report as `QUESTION for A3: ...` (the orchestrator routes it). Do not write online-walkthrough
knowledge of the original games into the steps.

## The guide's data

`output/xeen_site/data/guide.js` is `window.GUIDE = {...};` (JSON after the prefix). Its `maps[]` have `id`
(xeen_x1, xeen_xd07, xeen_dd10a ...), `name`, and `pois[]` with `t` (marker type), `n` (name), `d` (detail), `quests`,
and for houses `people` (the residents). `quests[]` have `id` (the quest file's stem: m1 ... m42, q-c1, q-d17, t1-a,
obelisks, x1-tam ...), `title`, `givers`, `steps`. Map images are `output/xeen_site/img/maps/<map>.webp` (surface maps:
the journal map, north up; other maps: a floor plan drawn from the geometry, north up). Rebuild to check your file:

```sh
cp -r output/xeen_site output/xeen_site_work/check_<you>   # once
python3 tools/xeen_site/build_site.py --skip-images --out output/xeen_site_work/check_<you>
```

It stops on an unknown quest id, map or marker type and prints `story <file>: {...} not found` for a person or point
it cannot find. A `from`/`to`/`giver` person matches a point's name or one of its `people`.

## File format (YAML)

Main story, one file per act (`act1.yml` ... `act6.yml`), chapter ids 1-6:

```yaml
chapters:
  - id: 1
    title: "Act I: Vertigo"
    intro: "One or two sentences: the goal of the act and how it is structured."
    sections:
      - title: "Vertigo: Mayor Gunther"
        intro: "optional, one sentence"
        giver: {map: xeen_x1, npc: "Gunther"}     # a person on that map (point name or a house's resident); optional
        quests:
          - quest: m1                              # a quest id
            requires: "optional: what must happen first"
            steps:
              - "..."
            tips: ["optional, short"]
            reward: "what the hand-in gives (from the quest file's do: lists)"
            points:                                # optional: extra points the maps must show (exact point names)
              - {map: xeen_x1, name: "Joe's Exterminations"}
            maps:                                  # 1-2 inline maps per quest, the ones the player needs
              - map: xeen_x1
                show: [exit, objective, lever]     # mechanism marker types to draw besides the quest's own points
                focus: "Vertigo Town Hall"         # optional: a point name substring selected first
                caption: "Where things are on this map."
```

Side and promotion quests: flat lists (`side_cloudside.yml`, `side_darkside.yml`, `promotions.yml`):

```yaml
quests:
  - quest: q-c22
    from: {map: xeen_x1, npc: "Derek"}           # who gives it
    to: {map: xeen_x1, npc: "Derek"}             # where to report, if worth stating
    summary: "One sentence: what you are asked to do."
    requires: "optional"
    steps: ["..."]
    tips: ["optional"]
    reward: "..."
    points: [{map: xeen_x1, name: "..."}]
    maps: [{map: xeen_x1, focus: "...", caption: "..."}]
```

Marker types: teacher, promoter, quest, vendor, guild, service, transport, mirror, house, npc, objective, exit, chest,
bonus (wells, fountains, shrines), lever, hint (obelisks, clues), teleporter, sign, door, monster. `show:` draws the
mechanism types (exit, lever, hint, teleporter, door, sign) besides the quest's own points.

If a person or object the walkthrough needs has no point in guide.js (or the wrong name), say so in your report (map,
the event or NPC id, what it is); you may still describe it in the steps.

## Your final report

The files you wrote; the quests covered (and any left out, with why); facts you could not confirm (and what you
assumed); the `QUESTION for A3:` list; points the generator should add or rename. Do not edit any other file.
