# Xeen world: design

A proposal (2026-11-12) for the next world after MM9: a new MM6–MM8-style world that adapts the story, places,
characters and quests of **World of Xeen** (Might and Magic IV: Clouds of Xeen, V: Darkside of Xeen and their combined
ending) on **new maps**, with new and recoloured monsters and items on the MM6–MM8 power curve. On 2026-11-20, 11 of
its 82 maps were built as MM7 stand-ins (X1, X2, XD-01 to XD-06, XD-12, XD-21, XD-27), and the user asked for the
whole world at MM6/MM7 quality: the plan for that is [ROADMAP.md](ROADMAP.md). All 82 maps were built and shipped
in v3.0 (2026-11-22) as "Xeen (alpha)".

| Document | Contents |
| --- | --- |
| [AGENT_GUIDE.md](AGENT_GUIDE.md) | **Start here** (2026-11-22): the entry point for an agent new to Xeen work: state and open polish, where everything lives, the workflows with their commands, the rules, how a multi-agent run is organised |
| [HANDOFF_ORCHESTRATOR.md](HANDOFF_ORCHESTRATOR.md) | How the program was resumed (2026-11-20; its §3–§4 superseded by [HANDOFF_ORCHESTRATOR4.md](HANDOFF_ORCHESTRATOR4.md)): how the orchestrator, lanes and deciders run, where everything stands, the open relays and questions |
| [ROADMAP.md](ROADMAP.md) | The plan. The production plan from 2026-11-20: the quality bar, the world package in `assets_dev/worlds/xeen` (committed since v3.0), the orchestrator and eight lanes, content pipelines, phases by act with gates, engine work, working rules |
| [HANDOFF.md](HANDOFF.md) | State of the work, how to continue it, and what is pending (start here when resuming) |
| [WORLD_DESIGN.md](WORLD_DESIGN.md) | The pitch, the decisions D1–D9, the two faces and their maps, travel, Fly, visual identity, towns and services, teachers and hirelings, dungeon counts, pacing by act |
| [QUESTS.md](QUESTS.md) | The main quest (42 steps in six acts), 54 side quests, composite promotions with a Light/Dark second tier, Newcastle and Castle Kalindra, recurring systems |
| [MAPS.md](MAPS.md) | The adopted per-map progression table; one sheet per outdoor map (13 surface, 3 sky, 4 planes, finale); the 58 dungeons with size class, levels and set pieces; original lines per map; layout sketches |
| [CHANGES_FOR_BUILT_MAPS.md](CHANGES_FOR_BUILT_MAPS.md) | What the built X1 and XD-01 to XD-05 must change after the decisions of 2026-11-14 |
| `reviews/` | The three design reviews of 2026-11-13 (scale and density, story and atmosphere, combat and progression) |
| [MONSTERS_AND_ITEMS.md](MONSTERS_AND_ITEMS.md) | Conversion rules, 66 monster families with models to reuse or make, density targets, treasure levels, gems, new item bases, artifacts, training caps |
| `briefs/` | Map Studio briefs for the new maps. Act I dungeons XD-01 to XD-05 at L1 (`briefs/xd0N/L1/`, provisional ids: qbits 110010–110052, items 12001–12033, map_stats 9131–9135) |
| [PLAN_YAML_NEEDS.md](PLAN_YAML_NEEDS.md) | What the map plans must express, sent to Map Studio so both use one `plan.yml` format |
| [PRODUCTION.md](PRODUCTION.md) | World package and id ranges, engine work E1–E9, content routes, the mock-up stages MU-1 to MU-7, phases, the lean variant, risks |
| `research/` | The evidence. Clouds content ([MM4_CLOUDS_CONTENT.md](research/MM4_CLOUDS_CONTENT.md)), Darkside, the ending and a critique of the earlier MM5 projects ([MM5_DARKSIDE_CONTENT.md](research/MM5_DARKSIDE_CONTENT.md)), the decoded monster/item/class/spell tables ([XEEN_SYSTEMS.md](research/XEEN_SYSTEMS.md)), MM6–MM9 world numbers ([MM678_CALIBRATION.md](research/MM678_CALIBRATION.md)), map craft and the "not bland" checklist ([MAP_CRAFT_CALIBRATION.md](research/MAP_CRAFT_CALIBRATION.md), with its measuring scripts in `research/map_craft/`) |

## Decision of 2026-11-13: no riddles the game does not answer

The user, after playing XD-04: "MM6-MM8 had almost no riddles and nobody really minded; it should be more like combat
+ mechanisms + loot; one can't get frustrated by having to solve riddles one doesn't know anything about." And,
refining it: a passphrase is fine "if the answer is obvious, like in some scroll or something the party can read".
So in the Xeen world a password, riddle or syllable puzzle stays only when **the game itself gives the answer
plainly before it is needed** (a scroll or note the party reads, a sign, a person who says it, found on the way
there), so that nobody needs to know the source games. Otherwise it becomes a key, a mechanism, a fight or a found
thing. Yes/no offers are fine. The documents below name the riddles as the source has them (the Rosebud door,
Newcastle's sword vault syllables, Ellinger's password, the Sphinx's name riddle, the Eye of the Dragon, the Basenji
and tribble passwords, the Lakeside riddle guild, the obelisk words); a brief or map built from one says where the
answer is given, or what replaced it. `oymap audit` lists for every question where its answers are met and at which
step of the way.

## Decisions of 2026-11-14 (after the three design reviews in `reviews/`)

- **Original text:** short original MM4/MM5 lines (signs, NPC quips, jokes, Joe's invoice, the guidebook) may be quoted
  or closely paraphrased; longer text is rewritten in the original's spirit.
- **Vertigo Meadows:** keeps 3-4 dungeons; the rest move to neighbouring maps; a road joins it to the hub X2.
- **Progression:** the combat review's MM6-MM8 per-map table is adopted (levels, monster bands, treasure on the MM6-MM8
  table, experience budgets, level 62-65 at the end as played), the over-wide monster families are split, training
  caps as proposed.
- **Dungeon sizes:** "S" shrinks to the shipped band (MM7 median 8 rooms, 22 monsters); XD-03 and XD-05 count as M as
  built; 4 large set pieces instead of 6.

## In short

- **One world, two faces.** Cloudside (bright: Vertigo, Rivercity, Castle Burlock, the cursed towns, Lord Xeen in the
  clouds) and Darkside (amber days under a failing sun: Castleview, Castle Kalindra out of phase, Sandcaster,
  Lakeside, Necropolis, Alamar). Travel pyramids join them; the world's edge is a visible cliff above the stars.
- **13 surface maps** (7 + 6), **3 sky maps**, **4 small elemental planes**, a finale map and **58 dungeons** (24 S,
  30 M, 4 L), within MM7/MM8's range for two games' worth of story. A lean variant (11 + 2 + 1, about 49 dungeons)
  keeps the story.
- **Start on Cloudside**; Darkside opens at about party level 14 through Burlock's advisor and is played alongside, so
  the two halves form one MM7-like open middle instead of two tutorials. Both villains fall in Act V; Act VI wakes the
  elemental sleepers, frees the real Prince Roland and unites the world.
- **MM6–MM8 rules**: towns in outdoor maps, house shops and guilds, stables, boats and mirrors, Fly allowed with
  restrictions on the sky maps, 90–135 monsters per outdoor map by role, treasure levels by monster level on the MM6–MM8
  table, no inflated rewards; about 4,200 monsters and a party at level 62–65 at the end as played.
- **Promotions** are attached to existing Xeen side quests: 5 first-tier quests on Cloudside, a Light or Dark second
  tier on Darkside, 5 racial ones: about 20 quests, none invented only for promotion.
- **Two home projects**: Newcastle built with Megacredits, Castle Kalindra restored with Energy Disks. **Five cursed
  towns** open their houses when freed.
- **First step**: a vertical slice of Act I (Vertigo Meadows, five small dungeons, eight monster families, the first
  promotion), then a verdict before scaling up.

The review page ([review.html](review.html), published privately at
https://claude.ai/artifact/FA4PpnWpTm6b8tdr8cEV3Q) draws the two faces, the level curve, the quest flow and
to-scale plans of the first two maps.

## Open questions

Answers change the plan; the design states its recommendation for each.

1. **One world with two faces, or two worlds?** Recommended: one world (D1).
2. **Fly** (MM6–MM8, restricted on sky maps and story castles) **or MM9's Fleet Foot and no Fly?** Recommended: Fly.
3. **Interleave Darkside from about level 12, or play the faces in sequence?** Recommended: interleave (D4).
4. **Full plan or lean variant?** Recommended: decide after the phase 1 slice.
5. **Light/Dark promotions per character or per party?** Recommended: per character (needs O2).
6. **Artifacts**: MM9's black-chest-only rule, or MM6–MM8 random level-6 drops? Recommended: MM6–MM8 random, plus the
   fixed quest artifacts.
7. **Source art**: may restored Xeen face sprites become NPC portraits, and Xeen sprites serve as monster references
   for HD masters? (They are references either way; this is about shipping derived art.)
8. **Gems as a second currency** for talking skulls, the dragon tax, gemsmiths and expensive guilds? Recommended: yes.
9. **Xeen's Barbarian class and Gnome race**: leave out (recommended), or add to the shared tables?
10. **Music**: reuse MM6–MM8 tracks by area, or new music?
