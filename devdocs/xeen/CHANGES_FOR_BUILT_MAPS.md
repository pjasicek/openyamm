# Xeen: changes for the built maps

Written 2026-11-14. What the six built Act I maps (X1 and XD-01 to XD-05, briefs in `briefs/`, installed in
`output/studio_play/xeen_root` as MM7 stand-ins) must change to match the design after the user's decisions of
2026-11-14 (README) and the revised documents. Nothing here has been applied: each map changes later in its own pass,
which updates its L4 project and NOTES, rebuilds, re-walks and ticks the item here. Built numbers are from the reviews
(`reviews/SCALE_AND_DENSITY.md`, `reviews/COMBAT_AND_PROGRESSION.md` §2.3, `reviews/STORY_AND_ATMOSPHERE.md` §1 F8, §3).

## All six maps

| # | Change | Why |
| --- | --- | --- |
| A1 | Each boss gets its own monster_data row with its HP multiplier and treasure, instead of a scene `hp` the game ignores: the Wobbles (XD-01, level 4), the Clan King (XD-03, 18), the Head Witch (XD-04, 20), the Drum-Master (XD-05, 12); XD-02's Tallymaster becomes an ordinary Clan Guard (XD-02 has no boss in the table) | MONSTERS_AND_ITEMS §1, PRODUCTION E14 |
| A2 | Monster levels to the per-map table (MAPS §0) and the split families (MONSTERS_AND_ITEMS §2) when the Xeen rows replace the MM7 stand-ins; until then pick stand-ins inside each map's band | Decision: the per-map table |
| A3 | Treasure: map Tres 1 on all six; chests at treasure level 1, one boss hoard at 2 in XD-03 and XD-04 (and XD-01, XD-05 if their boss has one) | MM6–MM8 treasure table (MONSTERS_AND_ITEMS §4.1) |
| A4 | A `LowerToEqual` row in `bolster_maps.txt` for each map (X1 has kind 0 and XD-01..05 none) | MONSTERS_AND_ITEMS §4.3 |
| A5 | NOTES list at least three short original lines from the source map, with their `aaze` reference (the lines per map below) | Decision: original text; WORLD_DESIGN §1 |
| A6 | Music by number on every map card (already done at install; keep it in the projects) | PRODUCTION E10 |
| A7 | The dungeons' own exits lead to `xeen_x1.odm` at the X1 doors, not to Emerald Island (open since the X1 build) | X1 NOTES |

## X1 Vertigo Meadows (`briefs/x1/L4`, `xeen_x1.odm`, map_stats 9130)

| # | Change | Why |
| --- | --- | --- |
| X1-1 | **West edge: the road leads to X2 Rivercity** (the river road), not X3; signposts and the transition's target change (stand-in: keep 7out03 until X2 exists) | Decision: a road joins Vertigo Meadows to X2; X2 now lies west of X1 (WORLD_DESIGN §3.1) |
| X1-2 | **Remove the Temple of Yak door** in the dead forest (the sealed `cave_mouth`, its torches and skull piles); put a POI in its place (a ruined shrine with a chest or a grave field) | XD-06 moved to X2 |
| X1-3 | Keep the four dungeon sites: XD-01 (warehouse doors and culvert), XD-02 portal, XD-03's shaft head (a one-way exit of the mines), XD-04 door, XD-05 mouth. Nothing more goes on X1 (no Dungeon of Death: it is in FD-04 on X7) | Decision: Vertigo keeps 3–4 dungeons |
| X1-4 | Hostiles at load 130 (built 172): orc groups 3–5, the rest 2–4; 55–60 markers; the camps merged into four encounter areas (the northern hills' orc country, Toad Meadow, the dead forest, the orc outposts' road), at least a third of the central land cells without monsters | MAPS §0 and X1 sheet; MONSTERS_AND_ITEMS §3 |
| X1-5 | Families: orcs 5/7/10 (d1), toads and snakes 5–12 (Toad Meadow), skeletons and zombies 6–18 (dead forest, d2); stand-ins inside those bands (the MM7 Goblin, Dragonfly and Skeleton slots are close; the 4 town guards at level 17 stay peaceful) | X1 sheet |
| X1-6 | 8–12 outdoor chests (built 6), half in plain sight for a level-1 party, each with a reason | X1 sheet |
| X1-7 | POI budget 40–50: add 20–30 generic devices out in the land (wells or fountains 4, camps with a fire 4, graves or ruins with a chest 4, signposts at forks 4, one stat challenge), no more than 6,000 of road or open land without a POI or fight | X1 sheet; `reviews/SCALE_AND_DENSITY.md` §7 |
| X1-8 | Decorations at most 800 (built 1,183), at least 40 central land cells with fewer than 3 decorations as open meadow | X1 sheet; review §6 |
| X1-9 | Opening message with Crodo's dreams: "Vertigo. For weeks you dreamt of an old man in a dark tower who begged you to finish 'the sword'. Then a bolt from the sky destroyed Newcastle, and you woke here among its survivors. Mayor Gunther asks your help: …" | QUESTS M1 |
| X1-10 | Crodo's bottle in Pitchfork Creek: "Help! I'm in Darzog's tower!--Crodo" | QUESTS M1 |
| X1-11 | Original lines: Gunther's welcome as the town hall topic; Joe's "I've just about got the situation under control" before M2 and the "Out of Business" sign after; three or four Plague Cult street peasants ("Sinners must repent." / "The end is near." / "The plague is upon us." / "Slime lords shall rule"); sign boards "This space for rent", "Pest control by Joe"; the gate sign "Please help clean up our beautiful town." (after M2 "Thank you"); the hiccuping drunk in the tavern pointing at the warehouse (M2's clue, beside the rain-barrel key); the money-tree sceptic; Vern's guild dues; Valia's Falista story in full; stock bed and well lines; Eeried's guidebook on sale | MAPS X1 sheet; QUESTS M2; WORLD_DESIGN §1 |
| X1-12 | Vertigo's training hall caps at level 10 (×10) | WORLD_DESIGN §5.1 |
| X1-13 | Joe's shop: before M2 a working shop or Joe's topic, after M2 the closed sign (was a message only) | QUESTS M2 |

## XD-01 Joe's Warehouse (`briefs/xd01/L4`)

| # | Change | Why |
| --- | --- | --- |
| XD01-1 | Stays S as built (26 sectors, 32 monsters: the upper bound of S); 28 monsters target, levels 2–6, Wobbles a boss row at 4 | MAPS §0, WORLD_DESIGN §6 |
| XD01-2 | The invoice verbatim: "Breeder Slimes, 1 mated pair 287 / 5 Doom Bugs at 145 each 725 / Total: 1012 gold" (built: "Doom Bugs, 5 (assorted)") | Original lines |
| XD01-3 | A Plague Cult slogan painted on a warehouse wall | Original lines |
| XD01-4 | Optional: fewer gates (18 doors; S band 3–8, pens and gates count) only if a later pass rebuilds anyway | WORLD_DESIGN §6 doors |

## XD-02 Red Dwarf Mines (`briefs/xd02/L4`)

| # | Change | Why |
| --- | --- | --- |
| XD02-1 | 55 monsters (built about 71), levels 3–10; no level-20 Lieutenant (the stand-in) | MAPS §0 |
| XD02-2 | Tres 1 (built 2); the level-3 chest becomes level 1–2 | Treasure table |
| XD02-3 | The dwarves' shopping list ("1 bottle orc's milk, 2 boxes of Dwarf biscuits, 1 can of split toadsoup, and one everlasting stick of troll jerky") and "There are many DEEP mines." at the Deep Line head | Original lines |
| XD02-4 | Optional: fewer doors (34; M band 6–16) | WORLD_DESIGN §6 doors |

## XD-03 Deep Mine (`briefs/xd03/L4`)

| # | Change | Why |
| --- | --- | --- |
| XD03-1 | Class M as built (24 sectors, 40 monsters); MAPS and the brief's header say M | Decision: XD-03 counts as M |
| XD03-2 | Levels 6–12, Clan King a boss row at 18 (stand-in Dwarven Commander 30 is 4–6 × the party) | MAPS §0 |
| XD03-3 | Tres 1 with one hoard at 2 (built chests at 3, 4, 4, 2, 3) | Treasure table |
| XD03-4 | "Robbers and thieves take a good look at your fate, should you decide to steal from these mines!" and "Dead men tell no tales." by the bones near the hoard; the Brakka inscription shortened or dropped | Original lines; voice |

## XD-04 Witch Tower (`briefs/xd04/L4`)

| # | Change | Why |
| --- | --- | --- |
| XD04-1 | Head Witch a boss row at 20; witches 10/14 (the Witches family); Tres 1 with one hoard at 2 (built Tres 2, a level-3 chest) | MAPS §0, treasure table |
| XD04-2 | The source's skulls: "Feed me!" (toss a gem), "Goblins back to work!" over the goblin pens, the two vanity skulls ("You are the fairest one of all") in the coven's bedchamber, the levitate hint ("Don't forget to use the levitate spell before you enter the cloud world!") on the roof stair. The built "One gem. A shiny one." skull stays | Original lines |
| XD04-3 | One freed child says "Thanks for getting me out of there … I want to go home." | Original lines |
| XD04-4 | The goblin slate stays; NOTES record that it is ours, not the source's (assumed, the user may change) | WORLD_DESIGN §1.2 |
| XD04-5 | Toad lids, vats and cages in front, the MM7 Moon Temple frieze in the background ("Nothing but rags", "Vat", "Cage") | `reviews/STORY_AND_ATMOSPHERE.md` F9 |
| XD04-6 | The key door stays (Rosebud as a password was replaced after the user's playtest); Rosebud's name stays | Decision of 2026-11-13 |
| XD04-7 | Optional: fewer doors (29; M band 6–16) | WORLD_DESIGN §6 doors |

## XD-05 Orc Caves (`briefs/xd05/L4`)

| # | Change | Why |
| --- | --- | --- |
| XD05-1 | Class M as built (25 sectors, 40 monsters, 44 M units²); MAPS and the brief's header say M | Decision: XD-05 counts as M |
| XD05-2 | Levels 4–10 (orcs 5/7/10), Drum-Master a boss row at 12; Tres 1 | MAPS §0 |
| XD05-3 | The drums use the source's outpost wording: "You have found an observation post for the Orcs! Destroy?" (adapted to the drums) and "The outpost collapses in a heap of ashes, smoke, and smoldering timber." | Original lines |
| XD05-4 | The back exit to X7's south slopes stays; X7's south edge has orcs 5–12 when X7 is built | X7 sheet |
