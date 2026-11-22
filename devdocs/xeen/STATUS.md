# Xeen: status

> **Start here (2026-11-21 ~17:00):** the third orchestrator stopped at usage limits; the fourth starts from [HANDOFF_ORCHESTRATOR4.md](HANDOFF_ORCHESTRATOR4.md).

**2026-11-22 ~06:05 (fourth orchestrator, final pass for the release check):** the user's 15-screenshot feedback (F1–F18) fixed world-wide (`reviews/USER_FEEDBACK_20261121.md`), D-89 gating + identity rebuilds done, mirrors reflect (MP39), Dimension Door globes (MP38). **Game merge point 44 (= MP41 engine code + a scenario log line), oymap MP42. All test sets green: main 52/52, promotions 41/41, side quests 71/71, each normal and --reload**; quests_smoke, 10 hook scenarios, quest_stub 19/19, quests.py 0, build_world 0 differ, stale bakes 0. Android cooks current (all verifies 0 problems); CI steps pass locally with and without Xeen (`lanes/P.md`); Xeen guide redeployed (G 8th). Shipping Xeen needs the user's commits (see P.md).

**2026-11-21 ~22:40 (fourth orchestrator, record `ORCHESTRATOR_SESSION4.md`):** the Reviewer's five fixes are in (D7 Olympus,
P1 walls and vent, DD-02, FD-01, DD-10C, XD-19's ceilings and its never-installed mirror cinematic, FD-02 blades); merge points 36
(input leak, `loot_chest`) and 37 (**MAW plays Xeen**: `devdocs/maw/XEEN_SUPPORT.md`, fifth bank, save 200, Supreme any 4 of 5 (U-4),
bands for 82 maps, dungeon pack reserves to Beyond Madness, Vertigo pedestal, Seers, MAW guide redeployed); D-83–D-88 (the Sphinx
door, MAW choices, no ranged disabler within 5,888 of any outdoor arrival or giver: markers moved on X1, X2, X4, X5, X6, D1, D2,
D3, D6; Randon undamageable). **All three test sets green on MP37 after every rebuild: main 52/52, promotions 41/41, side quests
71/71, normal and --reload, with D-82's party checks.** 0 stale bakes; balance unchanged; both guides current.

**2026-11-21 16:40: the Reviewer decided every review row** (`reviews/G3_REVIEW_20261121.md`: 78 rows, 73 accepted, 5 need work — Olympus' plain facades, DD-02's washed-out marble, FD-02's slab blades, FD-01's grey levers and pyramid, DD-10C's cold nest; the MM6–MM9 behaviour changes of merge points 31, 33, 34 accepted). Fixes running.

**2026-11-21 14:05: the Xeen guide is published at https://jasicek.net/openyamm/xeen-guide/** (lane G: 82 maps, 109 quest walkthroughs, 24 promotions, 116 teacher offers, shops, travel, 286-monster bestiary, items, FAQ; `tools/xeen_site/`, republish with `tools/xeen_site/deploy.sh`). A3 is answering the 44 places where the story sources disagree.

**2026-11-21 11:45: playthroughs like MM9's** — main campaign (A3: **complete — M1–M42 in segments 01–99, a new game to the ending; the whole chain passes in one go on today's world, normal (8 min) and --reload (34 min), no BLOCKER or ISSUE**; `tests/playthrough/xeen/README.md`), every side quest (A3-side, `tests/scenarios/xeen/side_quests/`: **complete — 70 scenarios covering all 54 side quests, Q-F1/Q-F2 and the world's own, all pass normal and --reload on merge point 33**; README and prep sheets), promotions (A3-promo, `tests/playthrough/xeen/promotions/`: **complete: 41 segments, class table 24 of 24, all pass normal and --reload on today's main checkpoints**).

**2026-11-21: the user lifted the ElevenLabs budget ("use however much you need, if it makes sense"); AU's audio queue ran: 25 new sounds installed; 37,791 credits charged, 132,950 committed of a 140,000 job budget.**

**2026-11-21 08:28: all 82 maps are installed** (FD-01 Alamar Depths last). The last two doors (D6's stair, D7's hatch into FD-01) opened at 08:39–08:40: **every door in the world is live**. The main-line chain passes through **M38 (segments 87–93), normal and --reload**; M39–M41 and the ending are being added (A3 27th).

**Handover (2026-11-21 ~17:00): the third orchestrator stopped at usage limits — the fourth starts from [HANDOFF_ORCHESTRATOR4.md](HANDOFF_ORCHESTRATOR4.md).** Earlier handover (2026-11-20): the third orchestrator took over at 23:30 (record: [ORCHESTRATOR_SESSION3.md](ORCHESTRATOR_SESSION3.md)). Earlier, the first orchestrator session stopped every lane at a clean checkpoint. Resume from
[HANDOFF_ORCHESTRATOR.md](HANDOFF_ORCHESTRATOR.md). The second orchestrator restarted all nine lanes the same day with
the §4 relays in their briefs, and sent §4's design questions to deciders D-15 (X3/X4: POI count, X4's first fight,
Asp's pedestal caps), D-16 (Act IV promotion XP), D-17 (XD-26's climb and winch ladder), D-18 (XD-09's blocks, XD-10's
skull offer and reservoir monsters), D-19 (Xeen's Guard model); answers go into DECISIONS.md.

Owner: the orchestrator (`xeen-o`). The tracker of [ROADMAP.md](ROADMAP.md) §9. A cell is a date when the item met
its definition of done (ROADMAP §5.1), "blocked: <owner>" when it waits on another lane, or "—" when not started.
"stand-in" marks the 11 maps built on MM7 rows before the world existed (they are rebased in phases 0–1).

## Phase

Current: **gate G0 open for the user's play** (review page https://claude.ai/artifact/PkSizVA5CUSMdfEcToTvbY,
2026-11-20; the fuller X1 of D-1.3 is installed without waiting, the user's rule of 2026-11-20 that a decider's answer is not held for the user). Phase 0 done; phase 2 dungeons (XD-09, XD-10, XD-11 by A8) started early,
their graphs approved and their questions decided by decider D-4. Gate G0: a new Xeen game starts in Vertigo from the
new-game screen; X1 and XD-01 to XD-05 installed in `assets_dev/worlds/xeen` with no MM7 stand-in; Vertigo's houses
open their Xeen residents; Town Portal shows the Xeen page; MM6–MM9 unchanged.

## Decisions

Since 2026-11-20 design decisions are taken by decider agents and recorded in [DECISIONS.md](DECISIONS.md); the
list below is the earlier record.

| Date | Decision |
| --- | --- |
| 2026-11-20 | Q2 interleave Darkside from about level 14; Q6 portraits generated new, Xeen sprites as references; Q1 MM6–MM8 Fly, restricted; the 3D lane starts now. Every other §2.2 question on its default |
| 2026-11-20 | Superseded by DECISIONS.md D-1.2: a deliberate trap far above a map's band (X2's level-60 lake dragons, X5's cyclops corner, D4's octopods) does not count against the map's arrival-act XP budget; `balance.py` counts it in the act where its level fits and reports it separately |
| 2026-11-20 | (orchestrator) Kalindra's Gem (Perception) and Errol (Armsmaster) teach up to Master from stage 1; their Grandmaster offers open at stage 4. Castleview's inn roster unlocks with 119021. Flavour topics of NPCs with no quest role move from A3 to A4 (`source/npcs/flavour/`); quest and story topics stay A3's |
| 2026-11-20 | (orchestrator) The Act I dungeons' new textures made on 2026-11-13 at the user's go-ahead (XD-01 11, XD-02 15, XD-03 12 of which 6 are one gong's cuts, XD-05 11) stay, over the per-map new-texture caps that came later; they count toward the world's 450. Xeen model sources stay in `assets_source/worlds/xeen/` (the route of `tools/install_model.py`), kept out of the submodule's git status by its local `.git/info/exclude` |
| 2026-11-20 | (orchestrator) XD-01 may keep 46 textures against S's 30 (the rest are signs and one-off pictures). No exit of a map in the Xeen world may lead into an MM7 map: exits to unbuilt Xeen maps are sealed with a message until the target exists. Q-C1 (Seasons relay) moves to Act III; T1-C back to Act II on Q-C10 (D-1.5) |
| 2026-11-20 | (orchestrator) X1's orc outposts are placed groups that never refill; "stop refilling after the drums burn" is dropped. X1 stays at 133 hostiles … superseded by D-1.3 (fuller X1, about 175) |
| 2026-11-20 | (orchestrator) Mirror qbits 119001–119012 are also each town's Town Portal unlock; the Vertigo inn roster (119020) is open from a new game |
| 2026-11-20 | (confirmed by D-1.1, D-2.2) T1-A Crusader promotion pays 8,000 XP per member, not 16,500, so Act I's quest XP stays on budget (15,750 of 16,500). Orothin's statues give the Cure Poison and Cure Disease books (no event teaches a spell) |

| 2026-11-20 | (orchestrator) XD-09 and XD-10 (Act II, party 16–19) stand on X5 (party 24–28): their doors go near X5's east edge, the X3 border, in a pocket whose monsters fit 16–19 |

## For the user's review

Collected for the gate review pages.

| Gate | Item | Where |
| --- | --- | --- |
| G0 | First Xeen start: Vertigo square with the opening text (A5) | `output/studio_cal/x1/world/start.png` |
| G0 | MU-1 world boards (A6) | `level_generation/xeen_art/mu1_world/board_mu1.png` |
| G0 | Two Roland hints before M21 (A4's laundress greeting, the King's line about the Prince) against the no-early-twist rule; rescaled rewards (Ebenezer 12,000 gold, the skull's 10 gems) | `assets_dev/worlds/xeen/source/npcs/xd07.yml`, `source/towns/` |
| G0 | X1 and X2 tour sheets in the world (A5) | `output/studio_cal/x2/world_tour/sheet_x1.jpg`, `sheet_x2.jpg` |
| G0 | Xeen item icons, 64, with in-game inventory and doll shots (A2) | `level_generation/ui/xeen_item_icons/review/` |
| G0 | MU-2 material boards for the 13 surface maps (A6) | `level_generation/xeen_art/mu2_materials/board_mu2.png` |
| G0 | MU-5 house kit boards (A6) and the six kit sheets | `level_generation/xeen_art/mu5_houses/board_mu5_*.png`, `level_generation/xeen_art/kits/*_sheet.png` |
| G0 | Invented coats of arms for Burlock and Kalindra (Newcastle has none yet) | `level_generation/xeen_art/kits/royal_castle.yml` |
| G0 | Music per map (A6 proposal) | `devdocs/xeen/MUSIC.md` |
| G1 | Act II dungeon graphs, each with its open questions (A8) | `devdocs/xeen/mockups/act2_dungeon_graphs.md` |
| G0 | NPC portraits, 324 (batches 3–4: `contact_batch3.png`, `contact_batch4.png`); 202 (A4; second batch with the Barok and Spring Druid fixes in `contact_batch2.png`) | `level_generation/ui/xeen_npc_portraits_20261120/review/contact.png` |
| G0 | Town Portal pages, new-game card, loading pages (A4) | `level_generation/ui/xeen_town_portal_20261120/review/` |
| G3 | D1's Western Tower by its front door (turn the key once, then enter) and the rope; D4's guild back stair, jetty shaft and wrong riddle answer into DD-20; the rim glow a little below the horizon, best at night from D4's arrival looking east (A6) | D1, D4 in game |
| G3 | Olympus: the mirror, Town Portal to Olympus and Lucio's boats from Castleview, Sandcaster and Lakeside (after M30); Cyrano's portrait (A4) | D7 in game; `assets_dev/worlds/xeen/icons_x2/npc15614.png` |
| G3 | D5: the Great Pyramid's green doors (with the key), Bosco's door and the Northern Tower door take you inside; D6: Alamar's gate asks first and throws you back without the Soul Box; D7: genie lamps, Rest Stop benches, the Megadragon roams about 1,024; P1's heat column asks before lifting (A6) | in game |
| G3 | DD-22 Sheltem's Pod: walls read more teal than the red-accent plan (red only in floors, ceilings and the bridge) (A8) | in game once D6's hatch opens; **06:43 reinstalled with D-67 (red walls but the airlock, day sky, Yes/No buttons, couch arms), rebaked; 4/4 incl. way in from D6; audit 0/0** |
| G3 | Cyrano's counter: the sale asks with Yes/No buttons (merge point 28); the Olympus arrival line appears as you walk off Lucio's jetty (A3) | in game |
| G3 | **The ending**: `output/a3_s25/p5_ending/shots/03_after_40s.png` (ceremony window), `04_after_return.png` (certificate), `05_after_escape.png` (Roland and Kalindra under the pavilion with the Pharaoh, cake and gift) (A3) | in game |
| G3 | D7: the sewer grate, Alamar's roof hatch and the Pyramid's sky door show Yes/No buttons; the sky door says "Access Denied!" before Corak is freed. D6: Sheltem's pod opens after Alamar's fall and leads into DD-22 (A6) | in game |
| G3 | FD-03's roof hatch asks "Climb to the Clouds of the Ancients?" and takes you up to P5; DD-06/DD-07's roof trapdoors ask before the Skyroads after M30; leaving XD-02, XD-05 or XD-26 puts you in front of the mouth (A7) | in game |
| G3 | DD-15: the Pharaoh's rooms show the blue-and-white tile at its own brightness, no glare (`output/studio_cal/a8_s15/dd15_baked3_sheet.jpg`); DD-17: the Heads, dais, hatch and vault ask with Yes/No buttons, and walking over a belt carries the party to the Head's end (A8) | in game |
| G3 | The Elemental Planes with S's pieces: the sleepers read as asleep (helmet and crest from eye height, closed lids from above); P3's dust shaft now dimmer and see-through (`output/studio_cal/a6/s21/pics/sheet_p3_wayup.jpg`); P1's heat column's edge still shows a grey band over the rock (`output/studio_cal/a6/s21/pics/p1_near_edge_crop.jpg`; S fixing). Sheets `output/studio_cal/a6/s20/pics/sheet_p1.jpg`–`sheet_p4.jpg`, `p2_dais.jpg` (A6) | in game |
| G3 | The Reflectors on X1 (the rim), X6 (the rock spit) and X7 ask with Yes/No buttons and show the disc's description in the same prompt; in P5's ending, Roland and Kalindra under the pavilion have topics (A5) | in game |
| G3 | Dark knights in black and red (Slayer, Voweless, Death, Doom; D-61); Sandro's heart jar in green glass; FD-04's dragon eggs; P1's heat column: whether the wider shimmer's faint grey edge over the dark rock bothers you (S) | in game as maps are rebuilt |
| G3 | DD-08's Hall of Thrones `output/studio_cal/a8_s17/dd08_thrones17.jpg`; DD-17's apse throne and teal statues `output/studio_cal/a8_s17/dd17_statues17.jpg`; DD-21's heart jar `output/studio_cal/a8_s17/dd21_jar17.jpg`; XD-12's cloud stair to X9 after freeing Crodo (A8) | in game |
| G3 | XD-17: the white fall down the east cliff, from the pool and from the cliff top (`output/studio_cal/xd17/shots/s20_falls/sheet.jpg`; S fixing the mist rim and the source above the notch) (A5) | in game |
| G3 | FD-02: the carved throne against the west shelves with Picard before it; FD-04: three dragon eggs on the warm rock, one gone once taken; leaving XD-02 by the west adit faces you west in front of it (A7) | in game |
| G3 | D-70: wells, shrines and stones that give a temporary bonus work once a day for the whole party (repeat clicks no longer stack; the "come back tomorrow" ones really reset); X9's Accuracy booth has a small cask, Sure-Eye Tonic, with a free round of two Accuracy Boosts once; X3's town well cures every member (A5, A6) | in game |
| G3 | D1's prayer shrine: +10 to each stat for everyone until you rest, refused a second time the same day, again the next day; P4: under the sea a teal fog in which the octopods fade (`output/studio_cal/a6/s22/pics/sheet_p4_fog.jpg`) (A6) | in game |
| G3 | FD-01 Alamar Depths: the coffin under its field and the lid opening when clicked; the bolted grate from both sides; the climb up the shaft to D7 (A8; tour `output/studio_cal/fd01/shots/things1_1..4.jpg`) | in game; **D-71 met, reinstalled and baked 08:47 (ladder, lever arms that throw, statue line), 7 tests 4/4, playtest_in 4/4 from D6, audit 0/0 (A8 19th)** |
| G3 | S's last pieces: XD-17's waterfall now with a stream above the notch and soft mist (`level_generation/decorations/xeen_waterfall_claude/review/s10/sheet.jpg`); P1's heat column without the grey edge (`level_generation/decorations/xeen_wayup_claude/review/s10b/`); D5's boulders with a carved bearded face; DD-12's canary cage birds; FD-04's lizard; FD-02's lecterns; D7's sky-barges and celestial boat (S; placing: A6, A7, A8) | in game as placed |
| G3 | X6/X7: the doors of Castle Basenji, the War Zone, the Volcano Cave and the Dragon Cave, the Shrine of Energy and the orc outpost show the whole line with Yes/No buttons (D-72); XD-17's fall after S's fix `output/studio_cal/xd17/shots/s22_falls/sheet.jpg` (the lip still a broad pale band) (A5) | in game |
| G3 | FD-04: after Alister's paid talk a small green lizard stands in his alcove; FD-02: the four books lie open on carved lecterns; Alister now stands in the west alcove in green and brown with a staff (S: `level_generation/creatures/xeen_tiers_claude/work_s11/shots/sheet.jpg`) (A7) | in game |
| G3 | D7: each Merchant of the Elements' sky-barge from its island, and Lucio's celestial boat docked at the jetty (`output/studio_cal/a6/s24/pics/sheet_d7_barges.jpg`); D5: the boulders' carved faces in both rings (`sheet_d5_boulders.jpg`); P1's heat column a faint shimmer with embers, grey edge gone (`sheet_p1_heat.jpg`) (A6) | in game |
| G3 | XD-17: the waterfall from the cliff top above the notch — clear water over the brink, white breaking out below (`level_generation/decorations/xeen_waterfall_claude/review/s11c/sheet.jpg`) (S) | in game |
| G3 | FD-04's gongs in matching pairs either side of the fountain doorway; DD-02's last door a little lower with the carved mouth over it (A7) | in game |
| G3 | P1: the Ember Font on the islet (once a day +20 Fire resistance until rest) and the burnt camp's note; P2: the wrecked balloon basket's logbook, the trapped chest in the rocks beside it (`output/studio_cal/a6/s25/pics/sheet_p1.jpg`, `sheet_p2.jpg`) (A6) | in game |
| G3 | **New sounds (AU, picked by measurement, not by ear)** — worth a listen first on `level_generation/sounds/xeen_20261120/review/index.html`: the wedding fanfare, the four chimes, DD-17's klaxon, DD-22's pod alarm, the night crickets, P3's quiet earth bed (in game as the lanes paste them) | review page |
| G3 | FD-01's levers swing when pulled, the dark pyramid and the key vault's racks (`output/studio_cal/a8_s20/shots/fd01_sheet_1.jpg`, `fd01b_sheet_1.jpg`); DD-03's sign and banners, DD-19's skull niches, XD-12's portraits and tapestry moved clear of doorways (`dd03_sheet_1.jpg`, `dd19_sheet_1.jpg`, `xd12_sheet_1.jpg`, `xd12b_sheet_1.jpg`) (A8) | in game |
| G3 | D7: at a corner tip hear that plane's sound; at Alamar's roof the Megadragon breathing, quiet after the kill; X5's pocket: crickets at night; Castleview's smithy and Winterkill's furrier now have barrels where an invisible campfire stood (A6) | in game |
| G3 | The P5 ending: four far bells during the pull-back over the ring (the last the deepest) and the fanfare as the pavilion fades in; X1/X2/X4 at night crickets replace the meadow beds; X7's volcano rumble over the north strip (A5) | in game |
| G3 | DD-17's Lava Heads roar with their plane's sound, klaxon blasts round the self-destruct; DD-21's heartbeat stops once the heart is taken; FD-01's stasis hum stops when the field drops (A8) | in game |
| G3 | Rivercity's Martial Training: Flint and the new Sparrow, "Pit Fighter", who teaches the Dodging and Unarmed Experts (D-73; `assets_dev/worlds/xeen/icons_x2/npc14158.png`) (A4) | in game |
| G3 | **MM7/MM8 change (merge point 31, hidden monsters no longer count as killed):** MM7 Wine Cellar (7d16) — leaving no longer sets "Slayed the vampire" while its vampires are hidden (exit event 501 still sets it); MM7 Wromthrax's Cave (mdt09) — the Crusader bit needs Wromthrax actually killed; MM8 Smuggler's Cove (d07) — **bug fix**: the were-rats no longer turn mad a minute after peace; MM8 Garrote Gorge (out05) — the original's own "all dragons killed" path is blocked by its hidden marker (as in the original), OpenYAMM's own script still sets the bit at the last kill; MM7 Harmondale, MM9: no change in play (A1) | MM7/MM8 in game |
| G3 | Between Newcastle (X3) and Burlock Savannah (X4) the party crosses the shared map edge directly; the old step plate on that road is gone (A3) | in game |
| G3 | X5's cyclops outpost: answer "Burn?" Yes — the tents and fire vanish, charred embers and stumps appear (fence, bones and hoard chest stay); D1: after Yog's "Battle!" the Sardaj camp attacks within a second; D1's lettered chests and the small lamps now speak (A6) | in game |
| G3 | **MM6–MM9 change (merge point 33):** magical age from ageing monsters, events or Divine Intervention now stays after rest and travel until cured (a Rejuvenation potion or an event), as in the original games — before, any rest wiped it. Xeen: shops stock enchanted MM6–MM8 equipment; loot has no MM9 items (A1) | all worlds in game |
| G3 | **MM6–MM8 change (merge point 34, a bug fix):** with MM9 mounted, MM6–MM8 armour, weapon and magic shops no longer sell plain MM9 weapons, armour or rings (stock refreshes on each shop's timer; bought items stay). With "MM9 loot in MM6-MM8" on, MM6–MM8 drops still include MM9 items; Xeen's never do (A1) | MM6–MM8 shops |
| G3 | Q-D10's robbery route: Sharla refuses to pay ("We pay nothing to robbers."); the treehouse chest gives the two disks after the village's sprites are dead. DD-23: the gargoyles' nest refuses the glass until the roost is destroyed (A3-side) | in game |
| G3 | **Tier colours match their names (S, your request):** Water Dragon turquoise-blue, Acid Dragon poison green, Fire Dragon red, Frost Dragon ice blue, Dragon King black and gold; Darkside dragons (Cloud grey, Green, Phase indigo, Energy violet); undead dragons apart; elementals by element (air, water, four earth tiers, fire guardian); Ice Troll frost-blue; Shadow Ninja charcoal; Swamp/Bog/Marsh things apart; Hell Hornet crimson; Devil red, Venomous Hydra green. After shots `level_generation/creatures/xeen_tiers_claude/ingame_s12/sheet2.jpg`, `sheet4.jpg`, `sheet6.jpg`, `guardians_crop.jpg`, `trolls_crop.jpg`; watch the Hell Hornet in dim dungeons, the Marsh Horror's specks up close, the Guardian of Air vs the Lesser Air Elemental at distance | in game; guide portraits being recaptured |
| G3 | XD-17's fall from the cliff top, clear over the brink and white below (`output/studio_cal/xd17/shots/s25_falls/sheet.jpg`); X6 with Arie's amulet: the first click on the Sphinx's door shows the amulet line and stir sound, the second enters; D3's cottage opens on every knock (A5) | in game |
| G3 | Reviewer follow-ups (S 13th): the Hell Hornet lighter crimson with glowing ember wings (`level_generation/creatures/xeen_tiers_claude/ingame_s13/hornet_v2.jpg`, D3's Aging Forest); the Guardian of Air gold at distance (`ingame_s13/air_v3.jpg`); Power and Skeletal Lich their own looks (`ingame_s13/liches_v2.jpg`, FD-04) | in game |
| G3 | Reviewer fixes (A8 23rd): DD-02's marble rooms dimmer and lamplit; FD-01's levers textured pipes with red grips and the pyramid black stone; DD-10C's cold nest with frost, ice and a blue light (frost floor bakes near white — polish); DD-14's Queen faces her cell door (`output/studio_cal/a8_s23/shots/check_all.jpg`) | in game |
| G3 | FD-02's Swinging and Chopping Death runs: thin steel blades, not falling blocks (`output/studio_cal/a7/s24/shots/fd02_sheet.jpg`); XD-19's ceilings still pale (open) (A7) | in game |
| G3 | D7: a refused toll pair stays hostile after a save and load (fixed, merge point 27); FD-04's crossword accepts punctuation and "Xeens Sceptre" (A7); FD-04's roof hatch asks Yes/No; leaving FD-02 puts you outside the sphinx | in game |
| G3 | DD-10C's cold nest and the eyes in the lava gallery; DD-21: Sandro falling and the risen Sandro by his bier, the Dead Food barrel, the green jar; DD-25 (once installed): the empty throne under Bosco's banner, the goblet after the Chalice (A8) | `output/studio_cal/dd10c/shots/baked13/`; in game |
| G3 | P2: the curtain of wind between the Eye's stones before and after the test; a misstep off an island costs a level-60 party 112/49/69/46 HP (a sorcerer under 47 HP dies); P3 and P4 contact sheets (A6) | `output/studio_cal/p2/pics/gate_crop.jpg`, `p3/pics/contact_t3.png`, `p4/pics/contact_t1.png` |
| G3 | FD-02: the Swinging and Chopping Death runs' thin steel blades, Picard's wooden throne; FD-03's original plaque and head rows; XD-18: refuse the tax and you're thrown out to X7 at once; FD-04: the Ultimate shrine's Yes throws you out at once; DD-06/DD-07: after M30 the roof trapdoors lead up to the Skyroads; XD-16: faint smoke over the five trap chests (A7) | `output/studio_cal/fd02/s18/sheet.jpg`; in game |
| G3 | **MM6–MM8 change (merge point 26, bug fix):** about 1 outdoor fall in 11 used to end with no landing sound and no fall damage; such falls now land and hurt like any other of the same height (jumps always play their landing sound). In Xeen, falls from the Skyroads onto D5, D1, D2 and from X9 onto Darzog's island now take about a third of HP (A1) | MM6–MM8 outdoors, Xeen sky maps |
| G3 | DD-08: the books accept the proverb with or without punctuation, or its vowels; the Euphoria Throne gives +1 to all seven only after the clicking member has sat on all four lows (A3) | DD-08 in game once installed |
| G3 | D7: Olympus is plain marble blocks, the roads white cloud slabs with a paved middle band; P1's crater has jagged cliffs and lava gullies but steep vertical walls; D5's Barrier glows blue at night again (a little brighter and less see-through by day) (A6) | `output/studio_cal/d7/pics/sheet_d7.jpg`, `p1/pics/contact_t2.png`, `d5/pics/sheet_s16mp25.jpg` |
| G3 | FD-03: the gong slabs rising, the seal veil; XD-18: the view from the ledge into the roost, the starwell's slot of sky, the King on his gold; FD-04: the crossword, Alister's vanish, the terminal (COMPUTER); FD-02's blades are teal slabs and its chair and lecterns plain blocks (polish pending); DD-13: the hides burn away and embers show in the pits (A7) | in game |
| G3 | D7 (once installed): refuse one toll and pay another — only the refusing toll's pair fights; buy a scarab, swap a reserve member in and buy again — only those without it gain, nobody is charged when all have it (A3) | D7 in game |
| G3 | D6's lava creatures now read "Lesser Fire Elemental" and "Fire Elemental", XD-19's fire guard "Fire Blower"; in FD-04 the crossword accepts variants ("Sceptre", "Kalindra's", "Lord Xeen"); the Ultimate shrine always throws the party out to X7 and never kills (A2, A3) | in game |
| G3 | D5's Parabolic Barrier see-through by day (dark at night until A1's fix; the pylons glow); X5: Darkstone's door faces north toward Winterkill on a wider rock top; with Surface materials off, D4's Blackfang windows and D6's Alamar slits glow at night (A6) | `output/studio_cal/d4/pics/sheet_s15d55.jpg`, `d5/…`, `d6/…`, `x5/pics/sheet_s15b.jpg` |
| G3 | Every world: the completion certificate now waits until an open message window is closed (MM9: may appear one click later); Xeen's Alamar windows and energy fields glow at night with Surface materials off (D-55, merge point 24) (A1) | in game |
| G3 | X6's sphinxes are S's models now (a stone infill shows above each door until the door leaves can be 512 high); P5's observatory dome dark weathered copper (A5) | `output/studio_cal/x6/tour/s16b/sheet_s16b.jpg` |
| G3 | The new World of Xeen completion certificate (new painting in the MM6/MM7 layout, new ending text; the source had no certificate art) (A4) | `level_generation/ui/xeen_certificate_20261121/review_ingame.png` |
| G3 | X2: Lake Darzog's dragons sit further out (north-west lobe, west channel, south lobe), the east channel by Medin's jetty is free; a dragon that sees the party from a shore may still chase past its circle until A1's leash fix (A5) | X2 in game; `output/studio_cal/x2/world_tour/s15/sheet_s15.jpg` |
| G3 | XD-19: take the scepter, watch the mirror shatter, end outside on X9; DD-13: open the plunder store's trapdoor from below; DD-24 at war: the giants challenge at the threshold; DD-16: click Corak once the field is down; XD-16: the cool passage into Shangri-La and back (A7) | in game |
| G3 | Sandcaster's Guild of Light shuts 6PM–6AM (a party with Ellinger's letter at night waits outside); travelling D5→D6 rests the party, clearing the shrine's and the Fountain of Might's bonuses (A3) | D3, D5 in game |
| G3 | X9 from the brink by night and day (the faint wisp way, the castle at 23,000); a fall off X9 onto Darzog's island (the dragons: D-54); Shangri-La's arrival view with the summit; Lacey and Stumpy talking; D3's `rim_glow` night view (A5) | X9, XD-17, X2, D3 in game |
| G3 | Lakeside's boats now name their destinations ("the Isle of Lost Souls", "Lakeside"; merge point 23 + A4); the yachts are shut at night (6AM–6PM); at DD-24 at war the People's challenge appears only after stepping out of the entrance room and back (A3) | D4, DD-24 in game |
| G3 | D5's Great Pyramid from the arrival and the dune crest; D6's Castle Alamar by day and at dusk (no night glow yet) and Necropolis; X7's Dragon Tower crag now black basalt by the lava (A6) | `output/studio_cal/d5/pics/sheet_final.jpg`, `d6/pics/sheet_final.jpg`, `a6/x7mat/cmp_s12_s13c.jpg` |
| G3 | Listen to AU's seven new picks (lava falls, forge hammer, striker ding, aspen, Necropolis, fair, tavern beds; chosen by measurement) | `level_generation/sounds/xeen_20261120/review/index.html` |
| G3 | Corak behind the half-see-through stasis field (DD-16 bridge); DD-24's near-black bloody throne; XD-19's element cores, sigil banners and the Sixth Mirror before and after (`output/studio_cal/xd19/s14_look/sheet.jpg`) (A7) | DD-16, DD-24 in game; XD-19 sheet |
| G3 | Merge point 21 changes shipped maps to match the originals: MM6 Abandoned Temple's six barrels appear only after Mom is saved; the MM7/MM8 arena torches (7d05, d42) and MM8 d24's 48 decorations start hidden (A1) | MM6 6d03, MM7 7d05, MM8 d42, d24 |
| G3 | Lakeside's ferries (and MM6's Tsunami on outd2, Cirrus on oute1): the boat's menu now closes on arrival again (fixed in merge point 22) | D4, MM6 in game |
| G3 | DD-12's SHELTEM maze (automap `output/studio_cal/dd12/shots/automap/automap-zoom2.jpg`) and the ruined tower under the fading sky; DD-14's great hall, throne and crypt (octopods do not fight yet); the genie lamps on D5/D6 ask in-game questions; the Cloudside rhyme statues now need Castle Burlock's Book of Languages first | in game once installed |
| G3 | Act V dungeons before bake: XD-19 `output/studio_cal/xd19/look/sheet1.jpg`, `sheet2.jpg`; DD-16, DD-24 `output/studio_cal/dd16/shots/sheet.jpg`, `dd24/shots/sheet.jpg`; XD-16's trap tell `output/studio_cal/xd16/shots/11-vault-3m.png`; X7's idols `output/studio_cal/x7/tour/s13/sheet_idols.jpg`; D3's night rim glow `output/studio_cal/d3/tour/s13/sheet_below15.jpg` | as listed |
| G3 | Listen once the beds are pasted: X6 desert and sand-falls, D1 crickets and Kalindra's shimmer, X1 meadow by day and Toad Marsh; the five XD-19/DD-16 sounds (AU; picks made from measurements) | `level_generation/sounds/xeen_20261120/review/index.html` |
| G3 | DD-05's chapel marble under the timber cone; DD-20's dark sewer; DD-02's marble rooms still very bright (A8) | `output/studio_cal/dd05/`, `dd20/`, `dd02/shots/s8/` |

## Lanes

At 23:10 on 2026-11-20 the second orchestrator asked every running lane to stop at a safe milestone for the handover
(HANDOFF_ORCHESTRATOR.md §4); each lane file's State is the authority on where it stopped.
At 23:30 the third orchestrator restarted A1, A2, A3, A5, A6, A7, A8 and S (agent list and open relays:
[ORCHESTRATOR_SESSION3.md](ORCHESTRATOR_SESSION3.md)); A4 and AU wait on relays.

| Lane | Session | Current work | Waiting on |
| --- | --- | --- | --- |
| A1 platform | stopped 2026-11-21 (thirtieth session: merge point 34, game only, 15:21). Twenty-ninth session: merge point 33, game only, 14:44). Twenty-eighth session: merge point 32, game only, 13:44). Twenty-seventh session: merge point 31, game and studio, 12:41/12:43). Twenty-sixth session: merge point 30, studio only, 09:24). Twenty-fifth session: merge point 29, 08:18). Twenty-fourth session: merge point 28, game only, 06:49). Twenty-third session: merge point 27, studio only, 06:06). Twenty-second session: merge point 26 05:26 — fall-damage landing fix, dungeon leash, world decorations in BLVs). Twenty-first session: merge point 25 03:57). Twentieth session: merge point 24 03:13; open: hidden chest for P5 (merge point 25), indoor smoke emitter, D4 frame cost). Nineteenth: merge point 23 (02:31). Eighteenth session: merge points 21 (00:57) and 22 (01:40) released; open: trapdoor pose check, smoke emitter, D4 frame cost) | see lanes/A1.md | — |
| A2 data | stopped 2026-11-21 (tenth session: D-53 most-experience line, Lacey wander, named edge arrivals for D1/D4/D5/D6; Act IV 1.04, Act V 1.02) | see lanes/A2.md | — |
| A3 story | 2026-11-21 (twenty-seventh session: **the chain reaches the ending — M1–M42, segments 01–99**; 63–99 pass normal and --reload). Twenty-fifth session: **segments 69–85 pass normal and --reload — main line through M37, the four Reflectors**; hooks_dd26, hooks_p5; the ending works in game; segment 83 uses a logged stat profile pending D-68). Twenty-fourth session: Q-D28 written; **segments 69–77 pass normal and --reload — main line from a new game through M33, Castle Alamar**). Twenty-third session: D7, FD-02/03/04, XD-18 and X9 hooks pass in game; **segment 69 (M28, the Great Pyramid) passes** — main line from a new game to 69). Twenty-second session: D-61/D-62/D-63 texts and hooks; segments 61, 63, 65, 67 pass on DD-14's placed Ambrose and Queen). Twentieth session: every phase-5/6 quest hook written — D-56 to D-59; segments wait on DD-14's reinstall, DD-15, P5, D7). Seventeenth session: Act IV main line through segment 67 — 20 disks, Queen restored, Pyramid key; hooks scenarios for X9/XD-17 and D5/D6 with amounts). Sixteenth: Act IV chain to segment 61 (57, 59, 61 pass normal and --reload); Q-D16 in game; D-52/D-53 texts. Earlier (fifteenth session: Q-D6, Q-D22 side quests (20 scenarios), all D-47–D-51 texts and hooks, built-map qbits; segment 57 waits on A6's D4 rebuild). Earlier (fourteenth session: D-47 hooks, sundial helper, 18 side quests; waits on D1/D4 unseals) | see lanes/A3.md | A8: DD-12/DD-14 for segment 57 |
| A4 towns | stopped 2026-11-21 (twelfth session, resumed: Xeen completion certificate in world.yml; D6 and D5 built; shop qualities fixed in six planned shops; earlier: XD-17 door ids, D6 Ambrose and Necropolis, reinstalls checked; same-map ride dialog bug to A1). Earlier (eleventh session: D4 built, Blastem 5248, Ambrose on DD-14 as data; 424 portraits) | see lanes/A4.md | next installed town map |
| A5 outdoor 1 | stopped 2026-11-21 (fifteenth session: X2's dragons leashed (D-54), X9's gate into XD-19, P5 L1 with D-56). Fourteenth session: X9 and XD-17 installed; X2's fall landing (D-54 pending); X7's cleft to XD-17; beds pan: false on six maps). Earlier (thirteenth session: X7 idols and XD-16 door, X6 XD-20 door and sand-fall, AU beds on six maps; X9/XD-17 L1 with D-50). Earlier (twelfth session: X7's crag flank in basalt, installed 23:13 with bake, 2/2) | see lanes/A5.md | — |
| A6 outdoor 2, art | stopped 2026-11-21 (seventeenth session: P2, P3, P4 installed; D6 for DD-10C; registry 192/450) (sixteenth: D7 and P1 installed; surface falls; registry 185/450). Fifteenth session: D5 Barrier translucent, D1/D6/X5 reinstalled, DD-16 rebaked, D-55 recaptures, D7/P1–P4 L1 with D-58; 168 textures). Thirteenth session: D5, D6 installed; D4 DD-12/griffin, D1 north edge, X8 rhymes; beds re-pasted with pan: false; 154 textures). Earlier (twelfth session: D5/D6 L1 with D-49; D1 and D4 doors to DD-05/DD-20 live; AU beds in X5, D1, D2, D4; rim glow `below_deg` 1.5). Earlier (eleventh session: rim glow live on D3/D4, D4/D1/X5 reinstalled, xkmirror v2, xogorge, X7 basalt and maps block; textures 141 of 450) | see lanes/A6.md | A1: rim glow over horizon clouds; A8: DD-12/14/20 |
| A7 dungeons 1 | stopped 2026-11-21 (eighteenth session: D-63 changes; DD-06/07 roofs to D7; DD-16 exit by name; 160/160). Seventeenth session: phase 6 installed — FD-02, FD-03, XD-18, FD-04; DD-13 cover panels; DD-06/DD-07 roof stairs; build choices with D-63). Fifteenth session: phase 5 complete — XD-16, XD-19, DD-16, DD-24 installed with exits live; DD-13 trapdoors and hides; NPCs talk from bodies in DD-06, DD-11C, XD-22; beds pan). Thirteenth session: XD-16, DD-16, DD-24 installed; XD-19 L4 in root, waits on S's xeen_guard and A1's damage hook/E11; XD-20 exit facings fixed). Earlier (eleventh session: XD-20 built and installed with bake; phase-5 graphs XD-19, DD-16, DD-24 drawn, XD-16 and the page to do) | see lanes/A7.md | A2: row 9121; A5: X6's arena door |
| A8 dungeons 2 | stopped 2026-11-20 (eighth session: DD-04 fix confirmed; five phase-4 textures; DD-02/03 re-baked on xkmirror v2; XD-27 xogorge; DD-05 and DD-20 built L1–L4, not installed; DD-12/14/19 briefs) | see lanes/A8.md | — |
| S 3D | stopped 2026-11-20 (sixth session: sand worm, XD-16 idols, D-44 mummy copy; armadillo parked at its README's "Resume here"; Meshy lane total 290) | see lanes/S.md | — |
| AU audio | stopped 2026-11-21 (fourth session: `pan: false` beds, indoor bed list, D5/D6/X9/XD-17 sound lists, 239 sounds; 27.0k charged, 93.75k committed of 100k). Earlier (third session: outdoor bed lists for 10 maps in AUDIO.md, D-47 sounds; 23.0k charged, 79.4k committed). Earlier (second session: D-38 voices — 5 designed voices, 9 sounds, ids 63000–63040; batch 2 — 12 sets, 84 sounds; 227 sounds in all; 19.9k charged, 67.7k committed of 100k) | see lanes/AU.md, AUDIO.md | A2: batch 2 names; A1: E9, enter_sound |

## Maps

Columns: brief level; built; installed in the Xeen world; monster and item rows real; houses and residents; quests
wired; travel linked; presentation (music, ambience, bake, minimap); playtest; playthrough segment; reviewed by the user.

| Map | Lane | Phase | Brief | Built | In world | Rows | Houses | Quests | Travel | Present. | Playtest | Segment | Reviewed |
| --- | --- | --: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| X1 Vertigo Meadows | A5 | 0 | L4 | 2026-11-20 (fuller, D-1.3: 176 at load) | 2026-11-20 22:07 with bake (texture fit 0; north edge to X7 open) | 2026-11-20 (row 9130, fuller slots; 1.14) | 2026-11-20 (A4 ids) | hooks wired, obelisks.x1 | north sealed; X2 edge | materials, minimap, bake | walk 2/2 (383), hostility 2/2 | Act I chain 01–11 passes on the fuller X1, also --reload (A3) | —; **2026-11-21 (A5 18th):** 06:18:36 with bake; XD-02/XD-05 arrivals moved off the mounds; walk 417 2/2, hostility 2/2 |
| X2 Rivercity and Lake Darzog | A5 | 1 | L4 | 2026-11-20 (rebase: 142 at load incl. 3 trap dragons) | 2026-11-20 22:10 with bake (texture fit) | 2026-11-20 | 2026-11-20 (47 houses) | 11 hooks, obelisks.x2; q-c23.upriver, q-c18.teacher pending (A5) | east X1, west X3, north X4 walked | materials, minimap, bake | walk 2/2, hostility 2/2; six side-quest scenarios pass every step (A3) | Act II chain 13–37 passes 2026-11-20 (also --reload) | — |
| X3 Lifeforce Lagoon | A5 | 2 | L4 | 2026-11-20 (135 at load, 38 POIs, 6,000 rule closed) | 2026-11-20 22:13 with bake (texture fit; AU sounds) | 2026-11-20 (row 9101, Dif raised; 0.98) | 2026-11-20 (A4) | Q-C7 hooks, coffin, obelisks.x3 | X2, X4 (plate), X5 edges; XD-11 islet; XD-08/13/24 sealed | minimap, bake | walk 684 steps 2/2, hostility 2/2, edge_spans scenario | Act II chain 13–37 passes 2026-11-20 (also --reload) | — |
| X4 Burlock Savannah | A5 | 2 | L4 | 2026-11-20 (135.5 at load; POIs 72 by D-15's count, D-20 pending) | 2026-11-20 22:15 with bake (texture fit 0; east edge to X7 open) | 2026-11-20 (row 9102, renegades) | 2026-11-20 (A4; Asp doors gated on q-c5.done) | q-c5 pedestals with A6's caps; obelisks.x4 pending | X2, X3 edges; XD-07/25/26 sealed until A7's exits | minimap, bake | walk 399 steps 2/2, hostility 2/2, edge_spans scenario | Act II chain 13–37 passes 2026-11-20 (also --reload) | —; **2026-11-21 (A5 18th):** 06:22:24 with bake; XD-26 arrival moved off the mound; walk 427 2/2, hostility 2/2 |
| X5 Winterkill Tundra | A6 | 2 | L4 2026-11-20 (D-6.1, D-6.3, D-6.5, D-4) | 2026-11-20 | 2026-11-20 23:03 with bake (gong boards fixed; audit 0/0) | 2026-11-20 (slots; Ghost Rider 11263) | 2026-11-20 (A4; 16 town doors gated on q-c6.done) | Q-C6 (16 a wave), q-c16, q-c18, m10, obelisks.x5 | east edge to X3 both ways; X6 sealed; XD-09/10 doors | 2026-11-20 (bake, minimap, ice; glacier view done: icefall and lookout, D-6.5) | walk 2/2 (677 steps), hostility; audit 0 | Act II chain 13–37 passes 2026-11-20 (also --reload) | — |
| X6 Desert of the Sphinx | A5 | 4 | L4 (D-31) | 2026-11-20 (POIs 25, 135 at load, 42.1k, relief 2,720) | 2026-11-21 02:51 with bake (S's sphinx models; XD-14, XD-15, XD-20 open; sand-fall sound; FD-02 sealed) | 2026-11-20 (row 9104) | 2026-11-20 (A4: houses 4301–4305, routes 406, 415, 427–431) | — | X4 west edge and X5 walked both ways | — | walk 2/2 (296), hostility 2/2 from assets_dev | — | —; **2026-11-21 (A5 18th):** 06:16:42 with bake; FD-02 door live; walk 351 2/2, hostility 2/2; audit 0/0 |
| X7 Mount Firestone | A5 | L1 2026-11-20; approved with changes (D-40, `briefs/x7/L1/D40_DECISION.md`); L2–L4 started | — | 2026-11-20 (D-40: lava, ash 40, south trimmed; 95 at load, 75.8k, POIs 20) | 2026-11-21 00:37 with bake (S's idols at the Volcano Cave; XD-16 open; XD-17/18, FD-04 sealed) | 2026-11-20 (row 9105; Act I 1.148) | — | — | X1 north and X4 east edges open, walked both ways | — | walk 2/2 (346), hostility 2/2; audit 0/0 | — | —; **2026-11-21 (A5 18th):** 06:14:59 with bake; XD-18 and FD-04 doors live (every X7 door open); walk 430 2/2, hostility 2/2; audit 0/0 |
| X8 Cloudreach | A6 | 2 | L4 2026-11-20 (D-6.2, D-6.4) | 2026-11-20 | 2026-11-20 | 2026-11-20 (row 9106, slots) | — | x8-sky hooks | three fall zones (west into X3's lagoon) | open-air, no Fly, no bake (no lamps) | all five playtests 4/4 from assets_dev | Act II chain 13–37 passes 2026-11-20 (also --reload) | — |
| X9 Clouds of Xeen | A5 | 5 | L1 approved with changes (D-50) | 2026-11-21 (D-50) | 2026-11-21 01:29, gate into XD-19 02:16 (open-air BLV); falls land on X2's `entrance:x9_fall` (D-54) | 2026-11-21 (row 9107) | — | — | — | — | 2/2 from assets_dev; audit 0/0 | — | —; **2026-11-21 (A5 18th):** 06:16; way down to FD-04 live; fall HP after merge point 26; MP27; 14/14; audit 0 |
| D1 Castleview Vale | A6 | 3 | L4 (D-23) | 2026-11-20 | 2026-11-20 23:01 with bake (dd05_door facing south) | 2026-11-20 (row 9108, D1↔D2 travel) | 2026-11-20 (A4: houses, mirror, Town Portal, arrivals) | — | — | — | walk 2/2, hostility; two gates, Western Tower key, grove rope | — | — |
| D2 Sprite Forest and Ogre Pass | A6 | 3 | L4 (D-23) | 2026-11-20 | 2026-11-20 with bake (oymap 21:33; doors by name; fire ignite sound) | 2026-11-20 (row 9109) | 2026-11-20 (A4) | — | — | — | walk 2/2, hostility (load, friends, burned fort, robbery) | — | — |
| D3 Sandcaster and the Aging Forest | A5 | 3 | L4 (D-28) | 2026-11-20 (52 POIs, relief 818–3,367, 1.07) | 2026-11-20 22:39 with bake (DD-07 door open; DD-19 sealed) | 2026-11-20 (row 9110, D2↔D3 travel; 1.07) | 2026-11-20 (A4: 48 houses, routes 413/416, mirror, Town Portal) | — | — | — | walk 678 steps 2/2 incl. D3↔D2, hostility 2/2 from assets_dev | — | —; **2026-11-21 (A5 18th):** 06:20:31 with bake; walk 696, hostility 44, D7 fall 23, all 2/2 |
| D4 Lakeside and Blackfang | A6 | 4 | L4 2026-11-20 (D-36, D-39, D-42; 119.5 at load, 33 POIs) | — | 2026-11-20 22:52 with bake (view distance 1.6, octopods swim, bat storm ends Fly, DD-23 door live, rim glow; DD-12/14/20 sealed) | — | 2026-11-20 (A4: 16 houses, routes 414/417/420/432, mirror 4656, Town Portal, 3 trainer places; Isle Ferry 4667) | — | — | — | walk 2/2 (328, D3 edge both ways), hostility; audit 0 incl. doors and texture fit | — | — |
| D5 Desert of Doom | A6 | 5 | L1 mock-ups 2026-11-21 (110 hostiles, 55.6k, +6 %; POIs 24 after D-49), approved with changes (D-49, `briefs/d5/L1/D49_DECISION.md`); L2–L4 started | 2026-11-21 (D-49; 110 at load, 55.6k, POIs 21, relief 2,656) | 2026-11-21 with bake; D4 edge walked both ways; DD-24, DD-18 doors live; boulders on shipped rock until S's model; Barrier opaque until A1's outdoor translucent | 2026-11-21 (row 9112) | 2026-11-21 (A4: no house; Gurodel on row 11085; Bosco's Hall sealed until DD-25) | — | — | — | walk 2/2, hostility; audit 0 | — | —; **2026-11-21 (A6 18th):** reinstalled 06:09 with bake; DD-15, DD-25, DD-08 doors live; walk 2/2, hostility; audit 0 |
| D6 The Forbidden Zone | A6 | 5 | L1 mock-ups 2026-11-21 (110 hostiles, 73.4k, +3 %; POIs 27 incl. Necropolis's 8), approved with changes (D-49); L2–L4 started | 2026-11-21 (D-49, D-50, D-52; 110: 33 markers + 44 placed; 73.3k; POIs 27) | 2026-11-21, reinstalled 02:04 with bake (DD-10C adit fixed; Alamar night glow with Surface materials on — D-55 on the default); pod hatch, crust, travel pyramid, Necropolis live | 2026-11-21 (row 9113) | 2026-11-21 (A4: 11 houses, mirror 4756, Town Portal Necropolis, 5 trainer places; town_feel --small, 9 exceptions; guild and Grave Market open 21:00–06:00) | — | — | — | walk 2/2 (301, Ambrose's flight, both edges both ways), hostility; audit 0 | — | —; **2026-11-21 (A6 18th):** reinstalled 05:57 with bake, Lua 06:08 (MP27); DD-21, DD-17 gate (asks), DD-10C live; 2/2; audit 0; **2026-11-21 (A6 19th):** reinstalled 06:48 with bake; DD-22 hatch live after m33.done; walk 2/2, hostility; audit 0 |
| D7 The Skyroads | A6 | 6 | L1 approved with changes (D-58, `briefs/d7/L1/D58_DECISION.md`); L2–L4 started | 2026-11-21 (D-58, D-61; road gaps ≤ 8,128) | 2026-11-21 04:53 (open-air BLV, no bake); dungeon roofs open by name as they install | 2026-11-21 (row 9114) | 2026-11-21 (A4: Olympus 4801–4814, mirror 4807, Town Portal, Lucio's routes 424–426) | — | — | — | 20/20 (walk, hostility, corner, Megadragon, six falls); audit 0/0 | — | —; **2026-11-21 (A6 18th):** reinstalled 06:10 (MP27); hatch to DD-17, sky door to DD-15; Megadragon leash 1024; S's lamps, benches; 22/22, 11/11; audit 0; **2026-11-21 (A6 19th):** reinstalled 06:44; DD-26 grate live; Yes/No buttons on grate, hatch and sky door (D-66); sky door 'Access Denied!' before m30.done; hooks_d7 passes; audit 0 |
| P1 Plane of Fire of Xeen | A6 | 6 | L1 approved with changes (D-58, `briefs/d7/L1/D58_DECISION.md`); L2–L4 started | 2026-11-21 (D-58) | 2026-11-21 04:56 (open-air BLV); way up to D7 live; S's pieces pending | 2026-11-21 (row 9115) | — | — | — | — | 10/10 (walk, hostility, lava, test with reload, P-2 bypass); audit 0 | — | —; **2026-11-21 (A6 18th):** reinstalled 06:02; the heat column asks; 12/12; audit 0; **2026-11-21 (A6 20th):** 07:42 with S's pieces (fire statue + plaque, sleeper, new dais to D7, heat column); 16/16; audit 0/0 |
| P2 Plane of Air of Xeen | A6 | 6 | L1 approved with changes (D-58, `briefs/d7/L1/D58_DECISION.md`); L2–L4 started | 2026-11-21 (D-58, D-64: wind curtain) | 2026-11-21 05:15 (open-air BLV); S's pieces pending | 2026-11-21 (row 9116) | — | — | — | — | 14/14 from assets_dev; audit 0 | — | —; **2026-11-21 (A6 20th):** 07:39 with S's pieces (couch under the dome); 18/18; audit 0/0 |
| P3 Plane of Earth of Xeen | A6 | 6 | L1 approved with changes (D-58, `briefs/d7/L1/D58_DECISION.md`); L2–L4 started | 2026-11-21 (D-58; gate a sinking slab) | 2026-11-21 05:42 (open-air BLV); S's sleeper/couch needed for the dais | 2026-11-21 (row 9117; environment to fix) | — | — | — | — | 10/10 from assets_dev; audit 0/0 | — | —; **2026-11-21 (A6 20th):** 07:41 with S's pieces; the earth sleeper sets 111762; 14/14; audit 0/0 |
| P4 Plane of Water of Xeen | A6 | 6 | L1 approved with changes (D-58, `briefs/d7/L1/D58_DECISION.md`); L2–L4 started | 2026-11-21 (D-58; water volumes, edge currents, 5 Great Octopods) | 2026-11-21 05:37 (open-air BLV); S's pieces pending | 2026-11-21 (row 9118) | — | — | — | — | 14/14 from assets_dev; audit 0/0 | — | —; **2026-11-21 (A6 18th):** reinstalled 06:11; octopods mid-sea (above_floor 512, leash 1280); 14/14, 7/7; audit 0; **2026-11-21 (A6 20th):** 07:45 with S's pieces and the Drowned Bell; octopods 11474; 16/16; audit 0/0; underwater tint/fog with A1 |
| P5 Clouds of the Ancients | A5 | 6 | L1 approved with changes 2026-11-21 (D-56, `briefs/p5/L1/D56_DECISION.md`); L2–L4 started | L4 in scratch root 2026-11-21 (20/20; 12 new textures); install waits on FD-03, S's Pharaoh and decorations | —; S's figures and decorations bound 2026-11-21, openAirMaps added; install with A5 18th | — | — | — | — | — | — | — | —; **2026-11-21 06:41 installed (open-air BLV), FD-03 stair live, 20/20 from assets_dev, audit 0/0 (A5 18th)** |
| XD-17 Shangri-La | A5 | 5 | L1 approved with changes (D-50) | 2026-11-21 (D-50; 15 doors, Lacey and Stumpy talk) | 2026-11-21 01:45 (open-air BLV); pyramid round trip to D6 works | 2026-11-21 (row 9120) | 2026-11-21 (A4: 15 houses, 8 trainer places; day hours) | — | — | — | 2/2 from assets_dev; audit 0/0 | — | — |
| XD-20 The Warzone | A7 | 4 | MU-6 graph approved with changes (D-39, `mockups/act4_a7_decisions.md`) | 2026-11-20 (arena word, 3 rooms, 20 ring marks, open sky) | 2026-11-20 with bake; X6 door sealed until A5 opens it | 2026-11-20 (row 9121: encounter 0, no slots) | — | — | — | — | 4/4 from assets_dev (walk 38, exit 14, hostility 15; A7) | — | — |
| DD-25 Bosco's Hall | A8 | 5 | MU-6 approved with changes (D-62, `mockups/act5_a8_decisions_b.md`); L1–L4 started | 2026-11-21 (D-62; 8 peaceful dwarves, no counted monsters) | 2026-11-21 05:48 with bake; D5 door at A6's rebuild | 2026-11-21 (row 9122) | 2026-11-21 (A4: houses 4701–4706) | — | — | — | 4/4 from assets_dev; audit 0/0 | — | — |
| XD-01 Joe's Warehouse | A7 | 0 | L4 | 2026-11-20 (rebase design; textures 46, D-3.4) | 2026-11-20 (re-baked 2026-11-20, 4/4) | — | — | — | — | — | — | Act I chain 2026-11-20 | — |
| XD-02 Red Dwarf Mines | A7 | 0 | L4 | 2026-11-20 (rebase design) | 2026-11-20 | — | — | — | — | — | — | Act I chain 2026-11-20 | — |
| XD-03 Deep Mine | A7 | 0 | L4 | 2026-11-20 (rebase design) | 2026-11-20 | — | — | — | — | — | — | Act I chain 2026-11-20 | — |
| XD-04 Witch Tower | A7 | 0 | L4 | 2026-11-20 (rebase design) | 2026-11-20 | — | — | — | — | — | — | Act I chain 2026-11-20 | — |
| XD-05 Orc Caves | A7 | 0 | L4 | 2026-11-20 (rebase design) | 2026-11-20 | — | — | — | — | — | — | Act I chain 2026-11-20 | — |
| XD-06 Temple of Yak | A8 | 0 | L4 | 2026-11-20 (rebase design; props rule) | 2026-11-20 | 2026-11-20 | — | 3 hooks wired | to X2, walked 4/4 | sounds | 4/4 with re-entry steps (2026-11-20) | Act II chain 13–37 passes 2026-11-20 (also --reload) | — |
| XD-07 Castle Burlock | A7 | 2 | L4 | 2026-11-20 | 2026-11-20 (rebaked) | 2026-11-20 (row 9123) | 2026-11-20 (A4, 4201-4204) | court hooks | X4 linked (gate, throne throw); postern waits on A5's moat-bank arrival; throne step after MP10 (D-24) | bake | 4/4 from assets_dev; throw with no window (D-24), dragon stays penned (D-32), postern live; fall damage waits on A1 | Act II chain 13–37 passes 2026-11-20 (also --reload) | — |
| XD-08 Tomb of a Thousand Terrors | A7 | 2 | L4 | 2026-11-20 (24 sectors, ~50 monsters) | 2026-11-20 (baked) | 2026-11-20 (row 9124; 1.07) | — | m10 tomb hooks | X3 exit live; X3's door in (A5) | bake | 4/4 from assets_dev (173, 28, 17), clean exits; D-22.2 potions, D-22.3 juices | Act II chain 13–37 passes 2026-11-20 (also --reload) | — |
| XD-09 Golem Dungeon | A8 | 2 | L4 | 2026-11-20 | 2026-11-20 | 2026-11-20 (slot, Iron Key 12261) | — | m10 hooks wired | X5 linked both ways, walked 4/4 | sounds, forge corner; bolts and lid in xwiron (A6) | 4/4 (160, 25, 22, 36) | Act II chain 13–37 passes 2026-11-20 (also --reload) | — |
| XD-10 Cave of Illusion | A8 | 2 | L4 | 2026-11-20 (24 sectors, 50 placed, D-18, D-22.2) | 2026-11-20 | 2026-11-20 (row 9126) | — | m12 skulls, plug, reservoir reveal | both X5 mouths 4/4 | sounds, 21 lights | six tests 4/4 | Act II chain 13–37 passes 2026-11-20 (also --reload) | — |
| XD-11 Tower of High Magic | A8 | 2 | L4 | 2026-11-20 | 2026-11-20 | 2026-11-20 (slot) | — | m13.skeleton_key wired | X8 and X3 islet walked 4/4 | sounds | five tests 4/4 incl. hostility | Act II chain 13–37 passes 2026-11-20 (also --reload) | — |
| XD-12 Darzog's Tower | A8 | 0 | L4 | 2026-11-20 (rebase design; props rule) | 2026-11-20 | 2026-11-20 (Crodo binding pending) | — | m21 hooks wait on A3 | lake island to X2, walked 4/4; cloud stair sealed | sounds | 4/4 with re-entry steps (2026-11-20) | — | — |
| XD-13 Newcastle Keep (staged) | A7 | 2 | L4 | 2026-11-20 (12 sectors, 25 monsters over stages) | 2026-11-20 (baked) | 2026-11-20 (row 9128; 0.99 + Act IV part 0.98) | 2026-11-20 (A4, 4141-4144 as wall doors by stage) | YOUR well, vault word, syllables (D-22.5) | X3 exit live; X3 hatch in (A5) | bake | 4/4 from assets_dev (163, 30, 12); D-22.5 texts, D-22.6 open sky | Act II chain 13–37 passes 2026-11-20 (also --reload) | — |
| XD-14 Castle Basenji | A7 | 4 | L4 2026-11-20 (D-39) | 2026-11-20 (D-39; oymap 21:33) | 2026-11-20 21:46 with bake; X6 door sealed until row lands | 2026-11-20 (row 9129) | — | — | — | — | 4/4 from assets_dev (12/12) | — | — |
| XD-15 The Sphinx | A7 | 4 | L4 2026-11-20 (D-39) | 2026-11-20 (D-39; oymap 21:33) | 2026-11-20 21:48 with bake; X6 door sealed until row lands | 2026-11-20 (row 9141) | — | — | — | — | 16/16 from assets_dev (visible disc sink) | — | — |
| XD-16 Volcano Cave | A7 | 5 | MU-6 approved with changes (D-47) | 2026-11-21 (40 demons, 29 sectors, 19/45 textures) | 2026-11-21 02:08 with bake; X7 door and the cool passage to XD-17 live | 2026-11-21 (row 9142) | — | — | — | — | 20/20 from assets_dev | — | — |
| XD-18 Dragon Cave | A7 | 6 | MU-6 graph approved with changes (D-57, `mockups/act6_a7_decisions.md`); L1–L4 started | 2026-11-21 (D-57; 40 dragons + King) | 2026-11-21 04:33 with bake; X7 door (A5); Dragon King skin (S) | 2026-11-21 (row 9143) | 2026-11-21 (A4: Dragon Tax Office 4852) | — | — | — | 20/20 from assets_dev | — | — |
| XD-19 Castle Xeen | A7 | 5 | MU-6 approved with changes (D-47, D-51) | 2026-11-21 (70 + bosses; seven new textures; Lord Xeen sword-only, 2,200 HP) | 2026-11-21 02:07 with bake; gate and scepter leave to X9 (X9's gate being opened by A5) | 2026-11-21 (row 9144 matches L4; 1.09 with bosses) | — | — | — | — | 16/16 from assets_dev | — | — |
| XD-21 Robbers' Den | A8 | 0 | L4 | 2026-11-20 (rebase design; props rule) | 2026-11-20 | 2026-11-20 | — | 3 hooks wired | quay to X2, walked 4/4 | sounds | 4/4 with re-entry steps (2026-11-20) | Act II chain 13–37 passes 2026-11-20 (also --reload) | — |
| XD-22 Ninja Pagoda | A7 | 3 | L4 (D-25) | 2026-11-20 | 2026-11-20 (baked; row 9145 pending) | 2026-11-20 (row 9145) | — | — | — | — | 4/4 in scratch root | — | — |
| XD-23 Troll Warren | A7 | 3 | L4 (D-25) | 2026-11-20 | 2026-11-20 (baked) | 2026-11-20 (row 9146) | — | — | — | — | 4/4 from assets_dev | — | — |
| XD-24 Nightshadow Crypt | A7 | 3 | L4 (D-25) | 2026-11-20 | 2026-11-20 (baked; coffin stair live) | 2026-11-20 (row 9147) | — | — | — | — | 4/4 from assets_dev | — | — |
| XD-25 Asp Undercroft | A7 | 2 | L4 | 2026-11-20 | 2026-11-20 (rebaked) | 2026-11-20 (row 9148) | — | q-c5 hooks | X4 linked (cellar door to Asp's square) | bake | every step 4/4 | Act II chain 13–37 passes 2026-11-20 (also --reload) | — |
| XD-26 Gargoyle Eyrie | A7 | 2 | L4 | 2026-11-20 (D-17: shaft ladder, the fence's hoist) | 2026-11-20 (baked) | 2026-11-20 (row 9149; 1.09) | — | q-c10.scarab | X4 exits open (mouth, sky crack); X4's door in (A5) | bake | 4/4 from assets_dev (four tests), clean exits | Act II chain 13–37 passes 2026-11-20 (also --reload) | — |
| XD-27 Ogre Lair | A8 | 0 | L4 | 2026-11-20 (rebase design; props rule) | 2026-11-20 | 2026-11-20 | — | 3 hooks wired | to X2, walked 4/4 | — | 4/4 with re-entry steps (2026-11-20) | Act II chain 13–37 passes 2026-11-20 (also --reload) | — |
| DD-01 Castleview Sewer | A8 | 3 | MU-6 approved with changes (D-26, mockups/act3_a8_decisions_a.md); L1–L4 started | — | 2026-11-20 (A8, baked) | 2026-11-20 (row 9150) | — | — | — | — | — | — | — |
| DD-02 Ellinger's Tower | A8 | 3 | MU-6 approved with changes (D-26, mockups/act3_a8_decisions_a.md); L1–L4 started | — | 2026-11-20 (A8, baked) | 2026-11-20 (row 9151) | — | — | — | — | — | — | — |
| DD-03 Castle Kalindra (staged) | A8 | 3 | MU-6 approved with changes (D-26, mockups/act3_a8_decisions_a.md); L1–L4 started | — | 2026-11-20 (A8, baked) | 2026-11-20 (row 9152) | 2026-11-20 (A4: houses 4501–4511, mirror 4512, routes 418–419; stage check passes) | — | — | — | — | — | — |
| DD-04 The Gremlin Court | A8 | 3 | MU-6 approved with changes (D-26, mockups/act3_a8_decisions_a.md); L1–L4 started | — | 2026-11-20 (A8, baked) | 2026-11-20 (row 9153) | — | — | — | — | 4/4 from assets_dev | — | — |
| DD-05 Western Tower of Mok | A8 | 4 | MU-6 graph 2026-11-20 (decider D-42) | 2026-11-20 L4 (D-42; 45 monsters, 14.29k; audit 0; Pegasus stand-in until S's row) | 2026-11-20 23:38, baked 23:41; D1 front door and rope live 2026-11-21 (A6) | 2026-11-20 (row 9154) | — | — | — | — | 4/4 from assets_dev (232, 40, 51) | — | — |
| DD-06 Southern Tower | A7 | 3 | L4 (D-25) | 2026-11-20 | 2026-11-20 (baked; strongroom waits on a key) | 2026-11-20 (row 9155) | — | — | — | — | 4/4 from assets_dev; strongroom open with key 12262 | — | — |
| DD-07 Eastern Tower | A7 | 5 | MU-6 graph approved with changes (D-39, `mockups/act4_a7_decisions.md`) | 2026-11-20 (D-39, D-45; 30 monsters, light door with two pylons) | 2026-11-20 with bake; D3's door opening (A5) | 2026-11-20 (row 9156) | — | — | — | — | 12/12 from assets_dev | — | — |
| DD-08 Northern Tower | A8 | 5 | MU-6 approved with changes (D-61, `mockups/act5_a8_decisions.md`); L1–L4 started | 2026-11-21 (D-61; 45 knights, 31.14k) | 2026-11-21 06:04 with bake; D5 door at A6's rebuild; thrones stand-in blocks (S) | 2026-11-21 (row 9157) | — | — | — | — | 4 tests 4/4 from assets_dev | — | —; **2026-11-21 (A8 17th):** thrones `xeen_throne`/`xeen_throne_gold` (D-66 met), rebaked, 4/4, audit 0/0 |
| DD-09 Temple of Bark | A8 | 3 | MU-6 approved with changes (D-27, mockups/act3_a8_decisions_b.md); L1–L4 started | — | 2026-11-20 (A8) | 2026-11-20 (row 9158) | — | — | — | — | — | — | — |
| DD-10A Gemstone Mines, west pocket | A8 | 3 | MU-6 approved with changes (D-27, mockups/act3_a8_decisions_b.md); L1–L4 started | — | 2026-11-20 (A8) | 2026-11-20 (row 9159) | — | — | — | — | — | — | — |
| DD-10B Gemstone Mines, east pocket | A8 | 3 | MU-6 approved with changes (D-27, mockups/act3_a8_decisions_b.md); L1–L4 started | — | 2026-11-20 (A8, baked) | 2026-11-20 (row 9160) | — | — | — | — | — | — | — |
| DD-10C Gemstone Mines, north pocket | A8 | 3 (geometry), 5 (Act V on D6, D-27) | MU-6 approved with changes (D-27, D-62); Act V update in progress | 2026-11-21 (D-62: Act V update, 11.50k) | 2026-11-21 05:06 with bake; D6 adit live after A6's door | 2026-11-21 (row 9161) | — | — | — | — | 4/4 from assets_dev | — | — |
| DD-11A Troll Holes, first pocket | A7 | 3 | L4 (D-25) | 2026-11-20 | 2026-11-20 (baked; row 9162 pending) | 2026-11-20 (row 9162) | — | — | — | — | 4/4 in scratch root | — | — |
| DD-11B Troll Holes, second pocket | A7 | 3 | L4 (D-25) | 2026-11-20 | 2026-11-20 (baked; row 9163 pending) | 2026-11-20 (row 9163) | — | — | — | — | 4/4 in scratch root | — | — |
| DD-11C Troll Holes, third pocket | A7 | 3 | L4 (D-25) | 2026-11-20 | 2026-11-20 (baked; row 9164 pending) | 2026-11-20 (row 9164) | — | — | — | — | 4/4 in scratch root | — | — |
| DD-12 Dungeon of Lost Souls | A8 | 4 | MU-6 graph 2026-11-20 (decider D-42) | 2026-11-21 (45 minotaurs, 23.8k; SHELTEM maze reads on the automap) | 2026-11-21 00:36 with bake; D4's Isle door live 00:57 (A6) | 2026-11-21 (row 9165) | — | — | — | — | 4/4 from assets_dev (306, 23, 31); audit 0/0 | — | — |
| DD-13 Ogre Forts | A7 | 3 | L4 (D-25) | 2026-11-20 (15 sectors, two-leaf gates) | 2026-11-20 (baked; D-34 smoke holes and xddaylt) | 2026-11-20 (row 9166) | — | — | — | — | 16/16 from assets_dev | — | — |
| DD-14 Castle Blackfang | A8 | 4 | MU-6 graph 2026-11-20 (decider D-42) | 2026-11-21 (31 sectors, 70 monsters, 40.9k) | 2026-11-21 00:47 with bake; D4's griffin live 00:57 (A6); octopods → indoor row 11473 (D-52) | 2026-11-21 (row 9167) | — | — | — | — | 4/4 from assets_dev (main, hostility); audit 0 | — | — |
| DD-15 Great Pyramid | A8 | 5 | MU-6 approved with changes (D-61, `mockups/act5_a8_decisions.md`); L1–L4 started | 2026-11-21 (D-61; 70 mummies, 51.92k) | 2026-11-21 with bake (rebaked 05:47); D5 door at A6's rebuild; floors fixed 06:38 (D-66) | 2026-11-21 (row 9168) | — | — | — | — | 4/4 from assets_dev; segment 69 passes | — | —; **2026-11-21 (A8 15th):** rebaked 1.2/1.0 (D-66), floors at their texture mean, no glare; MP27 Lua; 4/4 |
| DD-16 Corak's Pod | A7 | 5 | MU-6 approved with changes (D-47) | 2026-11-21 (7 monsters, 10 sectors, 20/30 textures) | 2026-11-21 01:55 with bake; exit live to D6 (measured crust point); Corak talks from his body | 2026-11-21 (row 9169) | — | — | — | — | 8/8 from assets_dev | — | — |
| DD-17 Castle Alamar | A8 | 5 | MU-6 approved with changes (D-61, `mockups/act5_a8_decisions.md`); L1–L4 started | 2026-11-21 (D-61; 68.85k) | 2026-11-21 with bake and cinematics; D6 gate and D7 hatch at A6's rebuild | 2026-11-21 (row 9170) | — | — | — | — | 6 tests 4/4 from assets_dev | — | —; **2026-11-21 (A8 15th):** D-66: Heads one Yes/No each, gate the whole source line, Yes/No buttons on dais/hatch/vault, belt test asserts (MP28), arrival line once per entry; 7 tests 4/4; segment 77 passes; waits only on S's throne and teal statue; **2026-11-21 (A8 17th):** `xeen_throne_steel` and four `xeen_statue_teal` (D-66 met), rebaked, 7 tests 4/4; Sheltem and Corak seen before the throne after the reveal (S: `level_generation/creatures/xeen_tiers_claude/work_s10/sheltem/sheet.jpg`); Sheltem and Corak seen before the throne after the reveal (A8 19th) |
| DD-18 Sandcaster Sewer | A8 | 3 | MU-6 approved with changes (D-27, mockups/act3_a8_decisions_b.md); L1–L4 started | — | 2026-11-20 (A8, baked) | 2026-11-20 (row 9171) | — | — | — | — | — | — | — |
| DD-19 Wizard Quarter | A8 | 4 | MU-6 graph 2026-11-20 (decider D-42) | 2026-11-21 (D-42) | 2026-11-21 01:33, baked 01:38 (A8's report pending) | — | — | — | — | — | — | — | — |
| DD-20 Lakeside Coven and Sewer | A8 | 4 | MU-6 graph 2026-11-20 (decider D-42) | 2026-11-20 L4 (D-42; 45 monsters, 13.42k; audit 0) | 2026-11-20 23:39, baked 23:40; D4 guild stair, jetty shaft, trapdoor live 2026-11-21 (A6) | 2026-11-20 (row 9173, D-46) | — | — | — | — | 4/4 from assets_dev (250, 67, 49) | — | — |
| DD-21 Necropolis Sewer | A8 | 5 | MU-6 approved with changes (D-62, `mockups/act5_a8_decisions_b.md`); L1–L4 started | 2026-11-21 (D-62: 15 + Sandro, 10.70k) | 2026-11-21 05:36 with bake; D6 stair door (A6) | 2026-11-21 (row 9174) | — | — | — | — | 4/4 from assets_dev (5 tests) | — | —; **2026-11-21 (A8 17th):** heart jar `xeen_heartjar`, rebaked; `playtest_reload` 2/4 on a scenario-driver flake (A1); `playtest_reload` heals member 0 first: 4/4 (A8 19th) |
| DD-22 Sheltem's Pod | A8 | 6 | MU-6 approved with changes (D-62, D-65); L1–L4 started | — | — | — | — | — | — | — | — | — | —; **2026-11-21 06:27 installed, baked, 4/4 from assets_dev, audit 0/0 (A8 14th); D6's hatch opens at A6's next rebuild** |
| DD-23 Gargoyle Lair | A7 | 4 | MU-6 graph approved with changes (D-39, `mockups/act4_a7_decisions.md`) | 2026-11-20 (D-39, D-45; 15 monsters, open sky) | 2026-11-20 with bake; D4's mouth opens at D4's next rebuild | 2026-11-20 (row 9176) | — | — | — | — | 12/12 from assets_dev (xdcraglt, D-45) | — | — |
| DD-24 Giants' Hall | A7 | 5 | MU-6 approved with changes (D-47) | 2026-11-21 (30 People, 12 sectors, 19/30 textures incl. xdgiantd, xdthrone) | 2026-11-21 02:08 with bake; exit live to D5; war challenge on arrival | 2026-11-21 (row 9177) | — | — | — | — | 16/16 from assets_dev | — | — |
| DD-26 Olympus Sewer | A8 | 6 | MU-6 approved with changes (D-65, `mockups/act6_a8_decisions.md`); L1–L4 started | — | — | — | — | — | — | — | — | — | —; **2026-11-21 06:33 installed, baked (DD-03's lower profile), 5 tests 4/4 from assets_dev, audit 0/0 (A8 14th); house 4815 (A4); D7's grate opens at A6's 19th**; **06:47 reinstalled with D-67 (exit Yes/No, bed headboard, reach step), rebaked; 4/4 incl. way in from D7; audit 0/0** |
| FD-01 Alamar Depths | A8 | 6 | MU-6 approved with changes (D-69, `mockups/act6_fd01_decisions.md`); L1–L4 started 08:35 (A8 18th) | — | — | — | — | — | — | — | — | — | —; **installed 08:28 with bake (D-69); 7 tests 4/4 from assets_dev; audit 0/0; D6 stair and D7 hatch at A6's 23rd** |
| FD-02 Southern Sphinx | A7 | 6 | MU-6 graph approved with changes (D-57, `mockups/act6_a7_decisions.md`); L1–L4 started | 2026-11-21 (D-57) | 2026-11-21 04:00 with bake; X6 door to be pointed (A5); mummies and Picard unbound (S) | 2026-11-21 (row 9180) | — | — | — | — | 20/20 from assets_dev | — | — |
| FD-03 Darkstone Tower | A7 | 6 | MU-6 graph approved with changes (D-57, `mockups/act6_a7_decisions.md`); L1–L4 started | 2026-11-21 (D-57) | 2026-11-21 04:10 with bake; X5 door (A6), P5 stair sealed until P5; onyx tiers unbound (S) | 2026-11-21 (row 9181) | — | — | — | — | 16/16 from assets_dev | — | — |
| FD-04 Dragon Tower and the Dungeon of Death | A7 | 6 | MU-6 graph approved with changes (D-57, `mockups/act6_a7_decisions.md`); L1–L4 started | 2026-11-21 (D-57) | 2026-11-21 04:52 with bake; X7 door (A5); roof to X9 live; Alister body, lizard, eggs (S) | 2026-11-21 (row 9182) | 2026-11-21 (A4: Wyrm's Hall 4853) | — | — | — | 36/36 from assets_dev | — | — |

## Engine (A1)

**Merge point 47 (2026-11-22; oymap only, released 15:17:14; game stays merge point 46's):** the user's chest reports
(Darkstone Tower: "wrong rotation of the chests ... based on the position to the doors"; the Sphinx: "chest in front of
stairs/entrance to another room"). **D-99**: a chest stands with its back to the wall it stands by (in a niche facing out,
free toward its room's entrance) and keeps a party's width and a margin (128) clear of doorways and 64 off the walking
lines. The studio turns every indoor chest without `facing` by it and warns `chest.facing` / `chest.placement`; `oymap
audit` fails built maps' chests by the same numbers (`chest.facing`, `chest.placement`), so **lanes drop `facing` on
chests** unless the audit needs one. 120 chests on 50 maps fixed at the source (L4 and generators; 6 moved, 3 given an
audited `facing`) and rebuilt with bakes, MAW reserves and playtests; audit 0 chest faults on all 82 maps; stale bakes 0,
build_world 0 differ. Studio 512/512. Details: A1.md Log (42nd), `reviews/USER_FEEDBACK_20261121.md` "F22 chest facing".

**Merge point 46 (2026-11-22; game only, released 14:34:12; oymap unchanged; `build/` rebuilt for the user):** the user's
request: **Xeen's new-game card reads "Xeen (alpha)", caption "Begin in Vertigo"** (Standard and MAW). New optional card
field **`short_title`** (default: the title): the card shows `title`; the journal's Quests/Notes/Trainers/Arcomage tabs,
the Ledger of Teachers ("ask for it in any tavern on Xeen"), MAW's trainer hints and the portrait filter use
`short_title`, which must equal the Owner of the world's quests and notes. Xeen's card sources (`source/towns/continents.yml`,
regenerated; MAW's file through `tools/maw/xeen_balance.py`) say `short_title: Xeen`. Save/load summaries keep the
continent `name` ("World of Xeen"). The journal runtime test now fails when a tab names no owner. TABLES.md documents
the field. Shots `output/a1_s41/newgame/01-standard.png`, `02-maw.png`, `output/a1_s41/journal/shots_xeen/1_quests.png`.
Regressions 48 pass + the stale Hesper unit case (`output/a1_s41/regressions.txt`).

**Merge point 45 (2026-11-22; game only, released 09:10:08; oymap unchanged; `build/` rebuilt for the user):** four user
requests. **(1) Dimension Door order = the new-game cards** (U-8): a door's `place` is now its rank, its continent's
`card.order` (engine Enroth 2, Antagarich 3, Jadame 4, Chedian 5; Xeen 1), not a slot; the doors take the screen's places
in that order. Xeen, Enroth, Antagarich, Jadame, Chedian with Xeen; Enroth, Antagarich, Jadame, Chedian without. Globes
regenerated for both screens (`tools/ui/dimension_door_globes.py` ranks too). **(2) No names under the portals** (U-8,
the user's change to U-5): no place has `label` (code keeps it); the hovered name stays at the bottom right. **(3) Inspect
name:** checked on Vertigo's Plague Cult members: inspect title and hover say "Plague Cult member" on MP41+ (the user's
`build/` was 2026-11-21 21:01, before F9-R2); a save from before F9-R2 kept "Peasant" for outdoor actors with an NPC, so a
restored outdoor map now names them from the NPC tables again (`resolveActorNpcName`; indoors was already derived).
**(4) Journal tabs from the cards:** Quests and Notes owner tabs, the Trainers tabs, the Ledgers of Teachers and the
Arcomage notes come from the mounted worlds' new-game cards in card order (Xeen, Enroth, Antagarich, Jadame, Chedian,
Shared); a card's world's other continents join it (Xeen's Darkside 7 is Xeen, ledger and tab 6). Xeen's quests, notes and
112 trainers show under Xeen, its taverns sell its Ledger ("ask for it in any tavern on Xeen"). Without Xeen: Enroth,
Antagarich, Jadame, Chedian, Shared. Regressions 48 pass + the stale Hesper unit case (`output/a1_s40/regressions.txt`).

**Merge point 44 (2026-11-22; game only, released 05:57:38; oymap unchanged):** **To A3 (37th's FD-04 request): not an engine
fault, and not the door.** In q-f1 `--reload` the party stops at (-904, 133) against **actor 9, a live hostile Phase Dragon** (radius
200; 237 = 200 + the party's 37). The `reload` step plays 0.5 s after the load (dialog dismissal), so the dragon is ~190 nearer when
the walk starts; with no reload at all, `advance_runtime: 0.5` before the same walk fails identically, and `clear_hostiles` after the
reload passes. No map reset; door states and collision equal. **A3: add `clear_hostiles: 1500` to the walks at lines 231–234 of
`tests/scenarios/xeen/side_quests/q-f1_alister_dragon_egg.yml`** (or a `clear_hostiles` step before 231). Game change: walk_to's
stuck line now says "in the party's way (its radius N, hostile: clear_hostiles)" when the nearest actor holds the party up. New
regression `tests/scenarios/xeen/fd04_rotating_door_reload.yml` (rotating doors saved open and closed, walked through and past after
loads). No MM6–MM9 gameplay change (scenario-runner text only).

**Merge point 43 (2026-11-22; game only, released 05:09:51; same code as merge point 41):** A3's reload failures of 83 and 85
after a lift ride are **not an engine fault**: their reload checkpoints predated the XD-12 and DD-15 rebuilds, so the game reset
those maps on entry (a hostile of fresh DD-15 stands in the lift top's gateway; fresh XD-12's disc/grille `Trigger` pair runs in
phase and shuts the grille). `run.py --reload 81 83 85` in order passes. The runner prints `STALE` lines (maps reset on entry);
new regression `tests/scenarios/xeen/dd15_lift_reload.yml` (reload mid-ride and at the top, then walk off). No MM6–MM9 change.

**Merge point 41 (2026-11-22; game + oymap, released 00:55:24):** outdoor chests are the shipped 19-face chest; ground heights follow the
game's triangles; doors pair wing pictures and show each picture whole; cave mouths buried, `form: shelter|blocked`; door rules in
`oymap audit`; actors with an NPC id show the NPC's name (**MM7/MM8 behaviour change**: 122/20 placed actors, as the originals); missile
launch height min(collision, model top) (**MM6/MM7 change**: Dust Devil 118→104, Air Elemental C 168→138, Water Elemental A 126→124); a
model texture missing from its package is read from the engine's or another world's.

**Merge point 40 (2026-11-22; game + oymap, released 23:46:19 by the lane's clock):** F1 a talking proprietor is shown once (sole
resident → straight to his talk with the house's services); F16 studio moves into a BLV write the standard MM6–MM8 entrance window
(`screen: none` direct; audit error on a Yes/No question before a move into a BLV); worlds may add `trans.txt` entrance lines;
`carries:` on outdoor actors; `oymap metrics` cave shape + `identity:` brief field; platform-top `fit`; exits default to the black
face (7solid01/solid01). MM6–MM9: no house or entrance change (0 proprietor pairs; exported maps unaffected).

**Merge point 39 (2026-11-21/22; game only, built 22:33:12, released 22:46:36):** mirrors: a `kind: mirror` liquid (`xmirror_xeen`,
texture name `xmirror`) reflects about its own plane at any angle (water's planar-reflection machinery, occlusion-gated, within
4,096, its own `fs_mirror.sc` loaded only on maps with a mirror); MM6–MM9 unchanged (no mirror liquids). MAW world-entry patch test
reads the world's own table. **A game built from older sources rejects the new liquids.yml (no water/tar/lava) — rebuild `build/`.**

**Merge point 38 (2026-11-21; game only, openyamm 22:10:42, released (copied) 22:17:50; oymap 12:46:47):** the Dimension Door screen
shows each lit portal's continent globe from its new-game card (U-5; `tools/ui/dimension_door_globes.py` writes the engine's 4-door and
Xeen's 5-door pictures) and every portal's name under it (`label` rects per place, style `TownPortalDoorName`); the stale-reserve log
line names the world's tool. Vertigo's dimensional travel pedestal is Xeen's own overlay (every ruleset). Unit 3137/3139 (the stale
Hesper case; RulesetTests' MAW-patch case reads MAW's `world: xeen` entry as an engine path — fixed in MP39).

**Merge point 37 (2026-11-21; game only, built by lane MX 18:29:40, released (copied) 18:35:58; oymap 12:46:47):** MAW plays Xeen
(`devdocs/maw/XEEN_SUPPORT.md`): `ruleset.yml` worlds add xeen; a fifth MAW level bank (continents 6 and 7 share it) — **save version
200** (older saves read four banks); Xeen promotion quests count as a fifth MAW world (Supreme from any four of five, x1.75 unchanged);
Progress tab Xeen card, Level popup, `ruleset banks` fifth value, scenario `ruleset_banks.xeen`; Xeen houses in `shopRerollCost`, XD-20
as a MAW arena; a ruleset may replace a world's `new_game_continents`. New `tests/scenarios/xeen/maw_new_game.yml`, MawClassTests/
MawMonsterLevelTests/RulesetTests cases. Regressions pass except the staged Hesper missiles unit case (also failing on MP35/36).

**Merge point 36 (2026-11-21; game only, openyamm 17:40:51, released (copied) 17:48:12; oymap 12:46:47):** a key press that closes a
screen or message (or is typed into a search field) no longer also acts in play — Combat, Yell, Always Run, Inn (P) and Trigger need a
fresh press (**shared MM6–MM9 behaviour change**; the Xeen ending's Return no longer toggles turn-based mode); the runner's `loot_chest`
closes a message the chest's event showed and then the chest (new `xeen/loot_chest_closes.yml`); `app` suite 29/29 (new case
`app_return_closing_message_does_not_toggle_turn_based`). Unit 3136/3137 (the stale Hesper case), runtime tests, 36 scenarios, model
dependencies pass; 0 stale. D-82 on MM9's main chain (MP35, report only): 41/43 pass, no PARTY DOWN; 55 and 61 fail for other reasons
(the user's MM9 program).

**Merge point 35 (2026-11-21; game only, openyamm 16:34:21, released (copied) 16:43:29; oymap 12:46:47):** the scenario loader takes
`clear_hostiles: {radius, height, min}` and `walk_to`'s `clear_height`; an event's given item that waits for room is the party's and is
saved (**save version 199**; older saves load with none; shared MM6–MM9, though nothing can wait in MM6–MM8); D-82: a `playthrough` or
`side_quest` scenario fails with PARTY DOWN after a step that leaves nobody able to act (not yet run against the chains); new scenarios
`mm8/garrote_gorge_dragons_quest.yml`, `xeen/given_item_waiting_saved.yml`. Unit 3136/3137 (the stale Hesper case), runtime tests, 35
scenarios, model dependencies pass. One stale bake at release: DD-14 (A8's 16:34 scene edit).

**Merge point 34 (2026-11-21; game only, openyamm 15:21:44, released (copied) 15:26:23; oymap unchanged):** shop stock keeps to the
world's pools — **MM6–MM8 and Xeen shops no longer sell plain MM9 equipment** when MM9 is mounted (a first stocking had put plain MM9
weapons, armour and rings into 564 slots: 43 MM6, 39 MM7, 22 MM8 and 31 Xeen shops); "MM9 loot in MM6-MM8" no longer reaches Xeen (D-80).
New unit test on the real tables. Unit 3135/3136 (the stale Hesper case), runtime tests, 33 scenarios, model dependencies pass; 0 stale
bakes.

**Merge point 33 (2026-11-21; game only, openyamm 14:44:29, released (copied) 14:48:13; oymap unchanged):** magical age survives rest
and travel (**shared: MM6–MM9** — before, any rest wiped it; now only a Rejuvenation potion or an event takes it away, as in the
original games). The runner's hostile clears keep to the party's storey indoors (below radius 5,000; new `height` / `clear_height`
overrides) — fixes XD-22's "Clan Master dies by himself". Xeen's loot and shops draw on the merged MM6–MM8 base through its world.yml
dependencies and roll no MM9 equipment unless "MM9 loot in MM6-MM8" is on (D-80); Xeen shops now stock enchanted MM6–MM8 equipment.
New scenario `mm7/magical_age_survives_rest.yml`. Unit 3134/3135 (the stale Hesper case), runtime tests, 33 scenarios, model
dependencies pass; 0 stale bakes.

**Merge point 32 (2026-11-21; game only, openyamm 13:44:19, released (copied) 13:58:30; oymap stays 12:43:03):** an event's given item
never deletes the held one or itself. With full packs the held item falls in front of the party as in MM6–MM8 (Dimitri's Songbird lay on
DD-03's floor). A held item that cannot be dropped stays on the cursor while the given item goes to the packs or the ground, or waits for
room (a waiting item is not saved yet). New scenarios `mm6/given_item_full_packs.yml`, `xeen/given_item_held_kept.yml`; scenario Lua
`ground_items()`. Unit 3132/3133 (the stale Hesper case; the merged-tables test now expects the new card order), runtime tests, 32
scenarios, model dependencies pass; 0 stale bakes. The headless `app` suite's `app_npc_granted_item_enters_held_cursor_slot` fails as it
did on merge point 31. MM6–MM9 change only where a given item used to vanish (a no-drop item held with full packs; none in MM6–MM8).

**Merge point 31 (2026-11-21; game 12:41:41 and oymap 12:43:03, released (copied) 12:46:47):** hidden monsters count as dead in
`evt.CheckMonstersKilled` only when its InvisibleAsDead argument says so, indoors and outdoors (before, a hidden monster always counted
— Castle Kalindra's liches counted as slain on the first visit). A room's step event now also runs on the tops of its low platforms
(standing on its floor, ≤ 50 high, no step event of their own); takes effect at each map's next rebuild (26 rooms on 17 Xeen projects,
`output/xeen_a1/mp31/room_step_tops.txt`). New scenario `mm7/hidden_monsters_not_killed.yml`. Unit 3131/3132 (the stale Hesper case),
runtime tests, 30 scenarios, model dependencies pass; studio 493/493; 0 stale bakes. **Changes MM7 and MM8 behaviour** (listed in the
review table: Wine Cellar, Wromthrax's Cave, Smuggler's Cove bug fix, Garrote Gorge).

**Merge point 30 (2026-11-21; studio only, oymap built 09:24:21, released (copied) 09:31:22 — the file on disk shows 09:31:22; game stays 08:18:10):** studio movers can turn about a line
(`movers[].turn: {pivot: [x, y, height], axis: x|y|z, degrees}`), so FD-01's levers can swing. Two new build warnings: a ladder that
climbs through a floor hole and stands less than 10 inside its edge, and a wall panel over part of a doorway (or a `fit` panel over a
whole one) — 11 panels on 7 Xeen maps now warn (A7, A8 fixing). Studio exit/into docs carry D-72; RUN_GAME.md notes what screenshot tours
hold. Unit 3131/3132 (the stale Hesper case), runtime tests, 29 scenarios and model dependencies pass; studio 492/492; 0 stale bakes. No
MM6–MM9 change.

**Merge point 29 (2026-11-21; game and oymap 08:18:10):** the studio's solve takes the Yes branch of Yes/No prompts (DD-17's fields
19–22 no longer wait; DD-15, DD-08 and D7 list the exits behind their prompts). Water volumes take a `fog` in objects.yml; with `sky` above
0 that fog replaces the outdoor view's haze under water. No false "liquid and flow" warning for decorations, lights and spawns in a room
with a liquid floor. New scenario step `equip_item`. A scenario's `load_game {path}` no longer reloads an earlier save of the same file
name. Escape drops an unanswered Yes/No prompt. A failed select_member says why. Unit 3131/3132 (the stale Hesper case), runtime tests and
29 scenarios pass, studio 489/489, 0 stale bakes. MM6–MM9 unchanged (MM9's Yorwick underwater view differs by at most 6 of 255 levels).

**Merge point 28 (2026-11-21; game only, openyamm 06:49:47; oymap stays 06:06:32):** DD-17's belt plates ride with forward held, keep
the facing they give and leave the party at rest. The failures were in the scenario runner: a held `press_action` now takes an in-map
move in the frame, and `movement_segment` stops turning the party after an event moves it. New scenario
`xeen/dd17_belt_forward_held.yml`. NPC topics and house dialogues show `AskChoiceWithAnswerSteps` as Yes/No buttons. No MM6–MM9 change
(no game code changed for the belts; no MM6–MM9 topic uses the prompt). Unit 3130/3131 (the stale Hesper case), runtime tests and 28
scenarios pass, 0 stale bakes. Known rough edge: Escape from a resident back to the house menu keeps an unanswered choice's buttons.

**Merge point 27 (2026-11-21; studio only, oymap 06:06:32):** the build's peaceful-group event runs once per fill, before the map's
own load events (D7's refused tolls stay hostile over a reload and a re-entry; D1's Sardaj camp turns hostile on its quest as meant)
— 25 installed Xeen maps with peaceful groups need a rebuild to get it (only their generated Lua changes); indoor monsters take
`above_floor` (flyers, swimmers in water); a click condition that calls a quest hook counts as saying something; `leash` on indoor
monsters confirmed. Unit 3129/3130 (the stale Hesper case), runtime tests and 27 scenarios pass, studio 489/489, 0 stale bakes. Game
binary unchanged (05:26:19); no MM6–MM9 map uses this event.

**Merge point 26 (2026-11-21; game and oymap 05:26:19):** falls outdoors of the same height now do the same damage on every map
(a falling step ending within 1 unit of the floor never "landed": no sound, no damage — D5, D1, D2 and X9's landing on X2 hit it every
time; about 1 outdoor fall in 11 in MM6–MM8 too). **MM6–MM8 behaviour change (bug fix):** those falls now land and hurt like any other
of the same height; jumps always play their landing sound. Same-map outdoor `evt.MoveToMap` with `keepHeight` keeps the height (no
MM6–MM9 event uses it). Studio: dungeon monsters take `leash`; BLV projects accept the world's own decorations; the overlap check names
a platform by its `id`. New scenario `xeen/x2_fall_damage.yml`. Unit 3129/3130 (the stale Hesper case), runtime tests and 27 scenarios
pass, studio 487/487, 0 stale bakes.

**Merge point 25 (2026-11-21; game and oymap 03:57:50):** P5's hidden chest (studio `chests[].hidden: true`, `{show|hide:
chest:x}`, kept by map state); an outdoor named arrival on a structure's walkable top stands on that top (D6 `entrance:dd16_hatch`
1,440 → 1,466; a warning when a point is lifted more than 64 — X1's `xd02_portal`, `xd05_mouth` and X4's `xd26_eyrie` sit on
cave-mouth mounds and must move; plaza/square arrivals rise 8–16 on rebuild); D-55 glow on outdoor and indoor translucent faces
(D5's curtain glows at night again; DD-16's and XD-19's fields glow); the `smoke` decoration smokes indoors; D-58's open-air checks
(water volumes, swimmers, hidden actors shown mid-visit, small plates fire; currents carry only the party, sideways). Unit
3128/3129 (the stale Hesper case), runtime tests and 26 scenarios pass, studio 486/486, 0 stale bakes. No MM6–MM9 drawing changes.

**Merge point 24 (2026-11-21; game and oymap 03:13:18):** leashed monsters stay inside their circle (flyers, swimmers and
walkers; scenario `xeen/x2_lake_dragon_leash.yml`, D-54); D-55's glow-only drawing for worlds that declare `surfaceGlowContent:
true` (Xeen's world.yml has it since 03:2x; MM6–MM8 read nothing new); a `cover` panel may stand over another panel; `dec24x`
bound for dungeons; the cinematic fade cue takes `color: [r, g, b]`; the completion certificate waits for an open event window as
well as the cinematic (every world; in MM9 it may appear one click later); P5 classed Dungeon M with 13 new textures. Unit
3128/3129 (the stale Hesper case), runtime tests and 26 scenarios pass, studio 484/484, 0 stale bakes.

**Merge point 23 (2026-11-21; game and oymap 02:31:45):** a save made in mid-air no longer loses the first floor plate after
the load (DD-12's statue hall; shared code, every world); outdoor structures take `translucent: true` (texture alpha; scene
`bmodel_faces.translucent_faces`, blended, sorted back to front); `transport_locations.txt` takes an optional Name column (empty
keeps the map's name); wiring effect `{exit: <neighbour>}`; `terrain_materials.py edges` skips `_blv` grounds; scenarios
`xeen/d6_ambrose_flight.yml`, `xeen/dd12_plate_after_load.yml`. Confirmed: `evt.GetCurrentMapName()` works in topic programs
(no bug); X9's `view_distance_scale: 2` affordable (one sector); merge point 22 changed no outdoor build output. Unit 3125/3126
(the stale Hesper case), runtime tests and 25 scenarios pass, studio 483/483, 0 stale bakes.

**Merge point 22 (2026-11-21; game and oymap 01:40:33):** rides inside a map close the house dialogue again (MM6's two
same-map boats included; scenarios `xeen/d4_same_map_ferry.yml`, `mm6/same_map_boat_closes_dialog.yml`); a named neighbour
arrival keeps its facing on every exit; DD-13's trapdoor (a door in an `in: floor` opening: `hinge`, `swing` ±) and covering
wall panel (`cover: true`); indoor `monsters[].npc`; `ActorIndex()` in wiring Lua; the audit counts cinematic event cues;
monster modifier `wander: {radius}`; X9 and XD-17 budgeted as Dungeon L; D-50's three checks confirmed. Open: the trapdoor's
open pose not yet seen on screen (axis sign), `state: open` at load. Unit 3123/3124 (the stale Hesper case), runtime tests and
23 scenarios pass, studio 481/481, 0 stale bakes.

**Merge point 21 (2026-11-21; game and oymap 00:57:49):** DD-13's hidden decorations (`hidden: true`, `show`/`hide` of a
decoration) and blocks on legs; E11, the hit's `attack` and `weaponItemId` in the indoor MonsterDamage hook; D-2.3's
`SlayingDemon` item flag; the studio damage hook (`trigger: monster_damage`, `monsters`/`actors`, `set_damage`); D-48's
per-sound `pan: false` and random loop starts; scenario `party_position.facing`. Indoor maps now honour the map's own
"invisible" flag on decorations, as the originals do (MM6 6d03's six barrels until QBit 1036; MM7 7d05 and MM8 d42's 31 arena
torches; MM8 d24's 48 `dec07`). Confirmed by code: a leave can follow `evt.PlayCinematic` (in its done event, `{direct =
true}`); a timer can show a hidden placed actor; no lava damage on a BModel floor; an Untouchable-hidden BModel has no
collision. Unit 3123/3124 (the stale Hesper case), runtime tests and 21 scenarios pass, studio 477/477, 0 stale bakes.

**Merge point 20 (2026-11-20; game and oymap 23:40:17):** E9 outdoor ambient sounds (an ODM scene's or overlay's
`ambient_sounds`; studio sketch.yml `sounds` → the scene's `ambient_sounds`; checked in a game run with
`OPENYAMM_AUDIO_TRACE=1`, headless scenarios play none); the rim glow lights the horizon cloud banks (`fs_sky.sc`);
`OPENYAMM_AUDIO_TRACE=1` logs placed ambient sounds, weather and effect clips (`play source=assetInstance`). Unit 3121/3122
(the stale Hesper case), runtime and 21 scenarios pass, model dependencies 0 broken, studio 474/474, 0 stale bakes.

**Merge point 19 (2026-11-20, studio only; oymap 23:02:35):** the studio `arena` word (objects.yml `arena:
{monsters, party, marks, ring}`; the build writes the scene's `arena` block and MM7's runtime restrictions; checked in the
game on a scratch XD-20: Varro offers Page..Lord, saving refused, award 46 in Xeen wording); destructible
`on_destroyed`/`on_damaged` events counted by the audit; `lifts[].trap: true`; the arrival-message check accepts timer
events conditioned only on qbits/player bits. Studio 473/473. Game binary is merge point 18's.

**Merge point 18 (2026-11-20; game and oymap 22:38:19):** XD-20 arena award wording (`award_texts`, override mode;
A2's file and the world.yml line in); D-36 outdoor swimmers (water facts, kept to water, studio `leash`); D-36 `rim_glow` on sky themes;
`evt.RemovePartyBuff("Fly")`; atmosphere `view_distance`; sign pictures at their own size; `7sg*`/`xkportc`/`xwcage`
classes; the door audit measures leaves hidden at load; surface maps of borrowed textures found from Xeen maps; faction
reset only on a real switch (DD-04's Gettlewaithe); in-map moves keep the event window; fit checks skip sky faces;
studio scatter reads world decorations; D-44 model-path check (`tools/xeen/model_dependencies.py`, MM6–MM8 exempt among
themselves). Regressions: unit 3120/3121 (stale Hesper only), Town Portal and Dimension Door runtime tests, 21
scenarios, model dependencies; studio 469/469; stale bakes 0. X7's edge_spans added (orchestrator), `x7_edges.yml`
passes. Not yet in: E9 outdoor ambient emitters.

**Merge point 17 (2026-11-20; game 21:33:20, oymap 21:33:52):** status lines set before `evt.MoveToMap` show on the
arriving map; an event window over an open chest closes alone and leaves the chest open; neighbour `keep_height`; world
contributions `place_mon` and `bolster_monsters` (NoArena live; world.yml line added); D-41 `storey_stack` (edge is an
error, module gives no finding; Xeen now 524 errors / 276 warnings); D-40 lava set (`tile_set: lavtyl`, MM8's lava in the
MM7 tile table's unused rows 450–485) and `ash: N` in atmosphere.yml; house Enter Sound; `oymap build` warns when one
texture is given two sizes. Regressions: unit 3115/3116 (the stale Hesper case only), Town Portal and Dimension Door
runtime tests, 22 scenarios, studio 469/469. Bakes: the 13 MM7 outdoor bakes' table hashes refreshed without re-baking after a per-bake check that their tile
sets and rows are untouched (`tools/lighting/refresh_tile_table_dependency.py`, evidence in A1.md); stale_bakes 2 (A8's
DD-02, XD-12, own map changes). Rebuild maps with the new oymap.

**Merge point 16 (2026-11-20, studio only; oymap 20:45:55):** the texture-fit check (`textures.*` in `oymap audit`,
default on Xeen maps; `devdocs/xeen/formats/TEXTURE_FIT.md`): errors `feature_repeated`, `feature_cut`, `trim_tiled`;
warnings `storey_stacked` (D-41: error for `edge` panels, none for `module`, warning otherwise), `tile_seams`, `feature_border`, `family_switch`. Studio words `fit: true`
(a picture once per bay), trim posts laid along their length, `raise` on `kind: wall`. Calibrated on 203 shipped maps.
Xeen today: 712 errors / 555 warnings (list `output/xeen_a1/fit/fit_xeen.txt`); every map lane fixes errors and fixes or
keeps warnings with a line under "Texture fit exceptions" in NOTES. Studio 469/469. Game binary still merge point 13's.

**Merge point 15 (2026-11-20, studio only; oymap 20:03:53):** hinged door pairs (`kind: hinged, leaves: 2`) and the
double-door check in `oymap audit` (the user's request; `devdocs/xeen/formats/DOORS.md`, calibrated on 1,788 shipped
leaves; Xeen list `output/xeen_a1/doors_xeen.txt`: 34 errors on 11 of 43 maps, sent to A5, A7, A8); texture classes as data
(`tools/xeen/texture_classes.py`, `engine/models/texture_classes.yml`; A6 reviews the overrides); outdoor decoration
`turn` (D-35); two-leaf building doors show each wing once. Studio 467/467. Next: the texture-fit check (merge point 16).

**Merge point 14 (2026-11-20, studio only; oymap 19:17:10):** the light-fixture audit in `oymap audit` (the user's
request; rules `devdocs/xeen/formats/LIGHTS.md`, mounts in `engine/models/light_fixtures.yml`; calibrated on 161 shipped
dungeons; Xeen maps' findings in `output/xeen_a1/lights_xeen.txt`, sent to A7 and A8: most errors are MM6's chained
brazier stood on the floor and torches with no wall); named arrivals (`arrivals:` in objects.yml; doors name
`arrival: entrance:<id>`). Studio 466/466. The game binary is merge point 13's. Next: the double-door check, then the
texture-fit check.

**Merge point 13 (2026-11-20; game 18:28:34, oymap 18:33:47):** indoor touch trigger (a wall face with the touch bit and
an event runs it on contact, opt-in per map via the scene's `party_movement: {touch_faces: run}`; studio `touch: true`;
MM6–MM9 unaffected); scenarios close the Adventurer's Inn roster and read numbered `mapvar(n)`; `town_feel.py` handles a
town of stalls; `SetValue(Age, 0)` clears magical age (Q-C1). Regressions: unit (stale Hesper only), Town Portal and
Dimension Door, 22 scenarios plus the relation, temple and inn-roster scenarios, studio 464/464; Xeen: quests_smoke,
edge_spans, 12 of 13 side quests (q-c15 waits on X5's warren), six dungeon playtests.

**Merge point 12 (2026-11-20; game 18:08:59, oymap 18:05:01):** D-25's paper-screen checks pass (translucent, blocks
movement, sight and missiles until broken; no speckle on an opaque-alpha texture); surface `translucent` word →
`translucent_faces`; event Age Add/Subtract ages a member (the Jewel of Ages blocks it, D-27); relation rows proven to stay
with their map; scenario step `heal_at_temple`; `oymap install --mount` keeps engine tables out of a mount. Regressions:
unit (stale Hesper only), Town Portal (now with Xeen's Darkside page) and Dimension Door, 21 scenarios plus two new,
studio 463/463; Xeen: 10 side quests, quests_smoke, edge_spans, six dungeon playtests. Built at -j12.

**Merge point 11 (2026-11-20; game 17:10:53, oymap 17:26:09):** map transitions, teacher schedules, transport routes and
hirelings load for any world whose world.yml declares them (E1; RUDE stays MM9); `AgingImmunity` item flag, party-wide when
carried (D-2.4); the studio hatch wedge closes both ends of its front (X1's shaft-head line). Maps rebuilt with the 17:22
oymap must be rebuilt again. Regressions: unit (stale Hesper only), Town Portal and Dimension Door runtime tests, 21
scenarios, studio 462/462; Xeen: 10 side quests, quests_smoke, edge_spans, XD-04/08/10/11/13/21 playtests.

**Merge point 10 (2026-11-20):** a studio `leave` moves at once (D-24); a choice-button answer that leaves a dungeon for
an outdoor map shows the leave window instead of losing the move; `question.wrong_effects` indoors and outdoors; hidden
actors confirmed not to block the party. Regressions: unit (stale Hesper only), Town Portal and Dimension Door runtime
tests, 22 scenarios, studio 462/462; Xeen: 10 side quests, quests_smoke, the XD-04, 08, 10, 11, 13, 21 playtests.

**Merge point 9 (2026-11-20, about 16:50):** scenario `status()` keeps every line shown across moves, waits and walks;
one map edge with several destinations from the world's `edge_spans.yml` (D-11.6: X4's south edge to X3 and X2; scenario
`tests/scenarios/xeen/edge_spans.yml`); tour poses over lift decks draw the right room; studio warns on `facing` with a
random-yaw model, `oymap record` on a project with no history; npc.txt Title column (D-21); `town_feel.py --small` and world
monster tables (D-20); seven `xjuice*` liquids, XD-04 grandfathered, liquid faces in the indoor bake (D-22). Regressions:
unit 3111/3112 (stale Hesper), Town Portal and Dimension Door runtime tests, 21 scenarios, studio 462/462; Xeen: all 10 side
quests, quest smoke, six dungeon playtests, edge spans.

**Merge point 8 (2026-11-20, 16:06; announced by the second orchestrator):** use the 16:06 game binary (the 15:52 build
crashed on exit from stale objects). Stables and boats take routes from `transport_index`, training caps from house_data
column 17, loading pages per face from the continent row; D-14 in `oymap audit`; outdoor `player_bit`, `question`,
`ShowThing`/`HideThing` from handler Lua, `barrier` line and height; Xeen outdoor builds take any shipped world's textures;
`evt.SetMist(amount [, seconds])`; A8's studio queue (event-exit trace, several `--extra-mount`, arrival check, solve with
`Xeen.itemCount` and `on_destroyed`); Q11 (relation rows win indoors too); MM7 indoor decoration models bound outdoors
(7dec11, 7dec18, 7dec20, 7dec21, 7dec32, 7dec54, brazir2f, mushrm01-03, 05, 6tree09). Regressions: unit (stale Hesper case
only), Town Portal and Dimension Door runtime tests, 21 scenarios, studio 461/461.

**Merge point 7 (2026-11-20, studio only):** `oymap audit` checks dressing outdoors (house doors and walls, walking lines
between house doors, roads, clumps; numbers under decider D-14); shipped MM6–MM8 outdoor calibration 1 error, 25 warnings
over 42 maps; studio 460/460. Dimension Door test green (five lit doors). Music: all 39 MUSIC.md tracks resolve. The game
binary is still merge point 5's.

**Merge point 6 (2026-11-20, studio only):** `kind: model` takes `from.world` (Nystor's ship from 7out03); bake and
stale lookup find native MM6–MM8 textures (`stale_bakes.py` 0 stale); studio 459/459.

**Merge point 5 (2026-11-20):** D-7's dressing audit (containers and set pieces, doorway band, walking line for floor
props of radius 24+, merged openings, 128 free gap, `store: true` storerooms via `<stem>.studio.yml`; Xeen maps by
default); Dimension Door listed in world.yml (its test red until A2 writes package paths); Kalindra's teacher gates
confirmed by a unit test. 27 scenarios pass, studio 459/459. Shipped MM6–MM8 calibration: 41 errors (was 94).

**Merge point 4 (2026-11-20):** X1's placed NPCs talk as themselves (a shared outdoor bug, MM7 too; new scenario
`tests/scenarios/npcs/placed_npc_actor_outdoors.yml`); an item held on the cursor counts for HasItem; the Xeen card is
offered on the new-game screen; `oymap audit` checks dressing indoors (calibration by decider D-7); `OPENYAMM_GAME_BINARY`
for the run wrappers; the bake tool reads terrainTileset. Act I chain and all four side quests pass. Studio 458/458.

**Merge point 3 (2026-11-20):** five-card new-game screen (the Xeen card shows once A4 adds its `card:` block),
Town Portal face pages, Dimension Door as data, studio reads world continent/sky/relations, scenario runner starts the
active world. Regressions: 20 scenarios pass, unit 3104/3105 (stale Hesper case), studio 457/457. Two runtime tests fail
in `build/` too ("quick cast attacks instead …", "party creation offers all starting characters …"): not Xeen work.

**Merge point 2 (2026-11-20):** regression set passes (20 scenarios, studio 456/456); world tables, world Lua, world sky, studio
kit fallback and world install in. **G0 progress:** a new Xeen game starts in Vertigo square (X1 in the world, A3's opening
text; `output/studio_cal/x1/world/start.png`). Open for G0 (2026-11-20, later): the fuller X1 density table (D-1.3, A5), XD-01's slogan texture (A7), the
switched lights' rebake in XD-01–05 (A7), then the review page.

**Merge point 1 (2026-11-20):** `build-xeen/game/openyamm`, `build-xeen/tests/openyamm_unit_tests`,
`openyamm-studio/build-xeen/oymap`. Use these for every Xeen run. Table formats: [lanes/TABLES.md](lanes/TABLES.md).
Regressions: 20 scenarios and studio 456/456 pass; one unit test fails on a stale git-ignored Hesper stage (fails in
`build/` too).

| Item | State | Landed |
| --- | --- | --- |
| W1 table contributions | done; world.yml lists 28 entries (Town Portal waits for its group line format) | MP2 candidate |
| World Lua | a map loads only its own world's events/common scripts (fixed: MM9's world_common.lua was prepended to MM6–MM8 scripts) | MP2 candidate |
| World sky file | composed into the engine library | MP2 candidate |
| W2 terrain tileset | done (`terrainTileset`) | MP1 |
| W3 map state identity | verified | MP1 |
| E2 new-game card, portraits, continent, Dimension Door | done (card shows with A4's card block; five-door Dimension Door art pending) | MP3 |
| W4 Town Portal from data | done | MP3 |
| E1 world tables beyond MM9 | done (map transitions, teacher schedules, transport routes, hirelings for any world declaring them; RUDE stays MM9) | MP11 |
| W5 studio install into a world | done (`oymap install --root assets_dev`, map files only) | MP1 |
| W6 packaging excludes xeen | done | MP2 |

## Balance (A2, `tools/xeen/balance.py`)

| Date | Act I kill XP per member | Notes |
| --- | --- | --- |
| 2026-11-21 (A2 19th, D-70; FD-01 installed) | 1.15 | **Stat gates 17 of 17 pass**; M34 Accuracy 78 with X9's tonic (D5's shrine extra, not counted); route help no longer counted, so M34 Speed 56 (short 4, inside the rule); guard check: 35 temporary sources, 0 unguarded; gem margin 8 at M34; FD-01 row 9179 matches L4; **every map installed and counted: Act VI complete 345.4k of 333.0k (1.04)**, FD-01+02 71.9k (1.06); I 1.15 (traps), II 1.08, III 1.02, IV 1.04, V 1.03, optional 1.05; quest XP unchanged, no trigger (`stat_gates_20261121b.md`, `balance_installed_20261121m.md`) |
| 2026-11-21 (A2 18th, D-68 stat gates; D-69 FD-01 row) | 1.15 | **Stat gates 17 of 17 within D-59's rule**; M34's Accuracy only with D5's shrine carried (48 permanent, 63 with it; D-70); gem margin 8 at M34; temporary wells on X4, D2, D3 stack per click (D-70); FD-01 row 9179; Act VI projected 345.4k of 333.0k (1.037), FD-01+02 71.88k (1.057) (`stat_gates_20261121.md`, `balance_installed_20261121l.md`) |
| 2026-11-21 (A2 17th) | 1.15 | 11474 Great Octopod (`Xeen Octopod E`) for P4's mid-sea swimmers; 11919 height 230; 9170 perception 15; **Act V complete 515.2k + 1.6k of 501.9k (1.03)**; Act VI installed 273.5k of 265.0k (1.03), projected 341.5k of 333.0k (1.025) with FD-01 36.93k; quest XP unchanged; no trigger (`balance_installed_20261121k.md`) |
| 2026-11-21 (A2, D-65 rows; installed recount) | 1.15 | DD-26 9178 before install; P3 9117 MOUNTAIN; DD-17 perception 5 (card, A8 to confirm); Tribble 25,000 gold sink; **Act V installed 473.4k + 1.6k of 462.3k (1.03), projected 1.03; Act VI installed 237.5k of 231.5k (1.03), projected 1.025**; optional kill 170.2k of 161.4k (1.05); quest XP IV 179.5k closed, V 231.5k (1.11), VI 209.0k (1.00), optional 77.0k (1.10) (`balance_installed_20261121j.md`) |
| 2026-11-21 (A2, D-62 rows) | 1.15 | DD-25 9122, DD-21 9174, DD-10C 9161, DD-22 9175 before install (rests Dif 0, 10 %; DD-25 encounter 0); Bosco's Guard 11054 (peaceful), Cinder Roach 11363, risen Sandro 11926 (peaceful); planned DD-21 10.70k (group DD-08+21 41.84k, +5.7 %), DD-10C 11.50k, DD-22 17.20k, DD-25 0; Act V projected 1.03; Dead Food +2 Endurance (Act V ~+27); Act VI installed 109.5k of 107.4k (1.02) (`balance_installed_20261121i.md`) |
| 2026-11-21 (A2, D-61 rows; D-60) | 1.15 | DD-15 9168, DD-17 9170, DD-08 9157 before install (encounter 10, rest slots Dif 2/2/0); Sheltem 11924, Voweless Knight 11925 (peaceful); xeen_voweless_knights [11150–11151] friendly after 113344, xeen_dark_knights [11152] hostile; planned DD-15 51.92k (1.03), DD-17 68.85k (1.01), DD-08 31.14k; Act V projected 1.03; Act IV quest 179.5k closed (D-60); Act VI quest 209.0k of 210k (1.00), most experience 213.5k (`balance_installed_20261121h.md`) |
| 2026-11-21 (A2, D-58 rows; D-59) | 1.15 | D7 9114 and P1–P4 9115–9118 before install (encounter 0); Fire family renamed (Lesser Fire Elemental, Fire Elemental, Fire Blower, Sleeper's Guardian of Fire); element rows 11700–11722; Sky Bandit 11116; Megadragon unique (by qbit); Alamar roof key 12377; balance.py counts quest-file AddValue(Experience); **Act IV quest 179.5k of 160k (1.12) accepted (D-60); Act IV closed at 179.5k: additions need an equal trim**; optional 77.0k of 70k (1.10); Act VI planned 339.0k of 333.0k (1.02); gem ledger (`balance_installed_20261121g.md`) |
| 2026-11-21 (A2, D-57 rows) | 1.15 | XD-18 9143, FD-02 9180, FD-03 9181, FD-04 9182 before install (encounter 0, no slots); Ghost Mummy 11273, Phase Mummy 11274, Onyx Sentry 11585, Onyx Warden 11586; Power Lich 11284 and Skeletal Lich 11285 as ordinary tiers (788, 978 HP); Picard 11922, Alister 11923 (peaceful); Dragon Egg 12375, Key to the Dragon Tower 12376; Q-F1's artifact Elder Staff 12505; Act VI planned 334.8k of 333.0k (1.01); A7's four maps 1.035 (1.049 with the King); optional quest XP 64k of 70k before X9's devices (D-59) (`balance_installed_20261121f.md`) |
| 2026-11-21 (A2, D-56 rows; XD-19 installed) | 1.15 | P5 row 9119 (encounter 0, no slots, NoBolster); Dragon Pharaoh 11919, Prince Roland 11920, wedded Queen Kalindra 11921 (peaceful, placed only, NoArena, not counted); M42 40k in Act VI (205.0k of 210k, 0.98); XD-19 58.0k of 53.3k (1.09 with the bosses, D-47's 57.99k; 1.02 without); **every Act V map with a kill target installed: Act V 341.1k + 1.6k of 332.5k (1.03)**; Act IV 1.04 (`balance_installed_20261121e.md`) |
| 2026-11-21 (A2, D-53; D6, X9, XD-17 installed) | 1.15 | D5 55.6k of 52.3k (1.06); D6 73.3k of 71.1k (1.03); X9 26.0k of 26.1k (1.00); XD-17 0 (Lacey, Stumpy peaceful); Act V installed 283.1k + 1.6k of 279.2k (1.02), projected with XD-19 1.02 (1.03 with its bosses); Act IV 275.6k + 24.5k of 287.9k (1.04); quest XP Act V counted 231.5k of 209k (1.11), most experience 239.5k (1.15, D-53); Lacey wander 512; named D1/D4/D5/D6 edge arrivals walked (`balance_installed_20261121d.md`) |
| 2026-11-21 (A2, D-52 rows; D5 installed) | 1.15 | DD-12 23.8k of 23.5k (1.01); DD-14 40.9k of 39.2k (1.04); D5 55.6k of 52.3k (1.06); Act IV installed 249.6k + 24.5k of 264.1k (1.04), projected 1.04; Act V installed 183.8k + 1.6k of 182.0k (1.02), projected 1.02 (1.03 with XD-19's bosses); quest XP with NPC files: IV 176.5k of 160k, V 236.5k of 209k (1.13; 1.19 if every wish lamp is taken as experience: decider D-53); rows 11473, 11917, 11918; monster kinds on 73 rows (Slayer Sword SlayingDemon works; MM6–MM8 slaying loot and undead spells now apply to these Xeen monsters); Lord Xeen 2,200 HP (`balance_installed_20261121c.md`) |
| 2026-11-21 (A2, D-50 rows) | 1.15 | X9 9107 and XD-17 9120 before install; Slick 11914, Lacey 11915, Stumpy 11916 (peaceful, not counted); Act V installed 1.00, projected with X9 26.0k, XD-19, D5, D6: 342.9k of 332.5k (1.03); Act V quest XP with X9's nests (10k) and XD-17's well (20k, not trimmed): 225k of 209k (1.08) (`balance_installed_20261121b.md`) |
| 2026-11-21 (A2, D-49 rows; XD-16, DD-16, DD-24, DD-12 installed) | 1.15 | XD-16 27.3k of 26.6k (1.03); DD-16+24 25.6k of 26.7k (0.96, People on the war route); DD-12 23.8k of 23.5k (1.01); Act V installed 128.3k + 1.6k of 129.7k (1.00), projected with XD-19, D5 55.6k, D6 73.4k: 316.9k of 306.4k (1.03); Act IV installed 208.7k + 24.5k of 224.9k (1.04), projected 1.04; Act V quest XP 195.0k of 209k (one route per choice); D5 row 9112, D6 row 9113; D5's Last Water +2 Luck (least-served stat, D-49 Q5) (`balance_installed_20261121a.md`) |
| 2026-11-20 (A2, D-47 rows; DD-05 and DD-20 installed) | 1.15 | DD-05 14.3k, DD-20 13.4k: DD-05+20+23 32.8k of 30.5k (1.08); Act IV installed 184.9k + 24.5k of 201.4k (1.04), projected 1.04; Act V X7 1.01, with D-47's four maps 187.8k of 183.0k (1.03; 1.01 without XD-19's bosses); rows 9142, 9144, 9169, 9177, 11083–11085, 11624–11626, Corak 11912; Lord Xeen 2,445 HP (2,200 since A2's ninth session); Slayer Sword value 0 + NoDrop; quest XP Act IV 176.5k of 160k, Act V 233.0k of 209k (A3 asked) (`balance_installed_20261120v.md`) |
| 2026-11-20 (A2, eighth session) | 1.15 | XD-20 row 9121; Sand/Great Worm bodies 127/130, 146/149 on xeen_sandworm; DD-05/DD-20 slots match A8's L4; no recount (no XP change) |
| 2026-11-20 (A2, DD-07/DD-23 rows) | 1.15 | DD-07 11.6k of 11.2k (1.03); DD-23 5.1k (D-39's figure); Act IV installed 152.1k + 24.5k of 170.9k (1.03), projected 1.04; place_mon 401–415 (`balance_installed_20261120u.md`) |
| 2026-11-20 (A2, XD-14/XD-15 rows) | 1.15 | XD-14+15 26.9k of 25.3k (1.06); Act IV installed 140.5k + 24.5k of 159.7k (1.03), projected 1.04 (`balance_installed_20261120t.md`) |
| 2026-11-20 (A2, X7 installed; place_mon) | 1.148 (X7's south trimmed to 8 markers + 2 Orcs) | X7 95 hostiles, Act V 75.3k of 76.4k (0.99); D4 119.5 hostiles, 39.4k of 43.0k (0.92); Act IV installed 1.03, projected 1.04; place_mon 401–410 live (`balance_installed_20261120s.md`) |
| 2026-11-20 (A2, D-39/D-42 rows, X7 and D4 rows) | 1.10 (1.17 with X7's south until A5 trims) | Act II 1.08; Act III 1.02; D4 114 (120), 39.4k of 43.0k (0.92) plus octopods 4.3k (Act IV trap); Act IV installed 113.7k + 24.5k of 134.4k (1.03); Act IV projected over every map with the deciders' figures: 298.9k of 287.9k (1.04); X6 42.1k (1.01); X7 planned Act V 75.35k of 76.4k (0.99) (`balance_installed_20261120q.md`) |
| 2026-11-20 (A2, Act III complete) | 1.10 | Act II 1.08; **Act III complete 192.6k + 5.3k traps of 194.4k (1.02)**; Act IV installed 1.03 (X6 1.01, DD-03 Act IV part 1.00); DD-10/11 pockets 0.75 (inside the act's gate) (`balance_installed_20261120o.md`) |
| 2026-11-20 (A2, phase-3 rows) | 1.10 | Act II 1.08; Act III maps and complete groups 137.6k + 5.3k traps of 133.8k (1.07), XD-22/23/24 1.08; projected ~1.04; Act IV installed 1.03; rows for XD-22, DD-09, DD-10A, DD-11A–C; Strongroom Key 12262 (`balance_installed_20261120m.md`) |
| 2026-11-20 (A2, D3 and DD-02 rows) | 1.10 | Act II 1.08; Act III installed 118.2k + 5.3k traps of 115.9k (1.07): D1 0.97, D2 1.03, D3 1.07, X5 1.02, DD-01 1.09, DD-02 1.09, DD-04 0.37 by design; projected ~201.4k of 194.4k (1.04); Act IV installed 1.00 (`balance_installed_20261120l.md`) |
| 2026-11-20 (A2, DD-01 and DD-06 rows) | 1.10 | Act II 1.08; Act III installed 74.7k + 5.3k traps of 75.4k (1.06): D1 0.97, D2 1.03, X5 1.02, DD-01 1.09, XD-23/24 13.2k of 17.9k, DD-06 5.7k of 17.1k (group), DD-04 0.37 by design; projected ~1.03; Act IV installed 1.00 (`balance_installed_20261120k.md`) |
| 2026-11-20 (A2, sixth session) | 1.10 | Act II 1.08; Act III installed 1.05 (D1 0.97, D2 1.03, X5 1.02, XD-23/24 13.2k of the XD-22..24 group's 17.9k, DD-04 0.37 by design: the court is friendly), projected ~200.9k of 194.4k (1.03); Act IV installed 1.00; Jewel of Ages AgingImmunity; permanent-stat ledger in A2.md (`output/xeen_a2_check/balance_installed_20261120j.md`) |
| 2026-11-20 (A2, D-26/D-27, D1 and D2 installed) | 1.10 | D1 0.81 and D2 0.83 (under target; A6 raising); Act III installed 0.96; DD-03 split III 6.8k / IV 14.1k; DD-10C to Act V (11.5k); traps Valio (III), Scraps, Barkman (IV); rats renamed, Dire Rat 11393; DD-04 court/army, D2 village sprites (11537/11538), Snog 11044 as factions; budgets III 194.4k, IV 287.9k, V 501.9k |
| 2026-11-20 (A2, D-25 rows) | 1.10 | D-25's rows 11074, 11075, 11114, 11115, 11123, 11124, 11413; pass ogres 11066–11068 and Troll Holes trolls 11690–11692 as their own factions with qbit relation rules; XD-22/23/24 planned 1.08 (Act III) |
| 2026-11-20 (A2, D-23 rows) | 1.10 | X5 with D-13's waves 26.5k of 26.0k (1.02); D2 by D-23 +1.4k (about 1.06); Darkside sprites 11534–11536 and Graalg's faction 11064–11065 written; Act II 1.08, Act IV installed 1.00 |
| 2026-11-20 (A2, Act II complete in the world) | 9.3k of 8.5k (1.10; fuller X1 1.14) | Act II 110.4k of 102.6k (1.08): XD-08 1.07, XD-13 0.99 (+ Act IV part 0.98), XD-26 1.09; Act III (X5 only) 1.02; Act IV installed 1.00 (`output/xeen_a2_check/balance_installed_20261120g.md`) |
| 2026-11-20 (A2, fuller X1 installed) | 9.3k of 8.5k (1.10); X1 176, 3.8k of 3.3k (1.14) | X3 0.98 after its Dif change; Act II 1.08 on the maps with slots (XD-08, XD-26 installed without slots, wait on A7) (`output/xeen_a2_check/balance_installed_20261120f.md`) |
| 2026-11-20 (A2, with X3, X4, XD-10) | about 9.3k of 8.5k (1.09) with the fuller X1 (176, 3.8k of 3.3k, 1.14) | Act II installed 1.05 (X3 0.77, raised by A5; X4 1.10, XD-10 1.03) (`output/xeen_a2_check/balance_installed_20261120e.md`) |
| 2026-11-20 (A2, 17 installed maps) | 8.3k of 8.5k (0.97) | Act II installed 55.8k + X5 pocket 3.1k of 53.3k (1.11); X5 1.01, X8 0.98, XD-07 1.06, XD-09 1.06, XD-11 1.04, XD-25 1.11; Act III 1.19 only from the X2/X8 traps on its one installed map; X1 0.82 awaits the G0 call (`output/xeen_a2_check/balance_installed_20261120d.md`) |
| 2026-11-20 (later) | 8.3k of 8.5k (0.97×; D-1.3's budget) | X2 1.08×; Act IV +4 %, Act V −4 % after D-9.3; X5, XD-09, XD-11 await their slots |
| 2026-11-20 | 10.0k of 7.6k (1.32×, over the 15 % gate) | X1 1.23, XD-01 0.80, XD-02 1.55, XD-03 1.57, XD-04 1.24, XD-05 1.21; trim by tier mix sent to A5 and A7. Act I quest XP 15.8k of 16.5k. Act II so far 1.04× |

## Content

| Kind | Owner | Made | Notes |
| --- | --- | --- | --- |
| Monster families (66) | A2 | 66 families, 238 rows (11010–11673) | relations and modifiers written; models are stand-ins until S |
| Boss rows | A2 | 34 | |
| Item bases, artifacts, quest items | A2 | loot MM6–MM8 only (new bases removed, U-1); 25 artifacts, relics, tiara copy and gem gear borrow MM6–MM8 skins; quest items with generated icons; 136 of 143 items draw a ground model | 7 quest-item models wait for Meshy (S) |
| Quests (42 main, 54 side, ~20 promotion) | A3 | 2026-11-20: all quest files full; D-36 to D-42 texts, bits and hooks; voiced lines installed; sounds on mirrors, pyramids, obelisks, springs | chain passes a new game to segment 55 (Q-D7 gem mines, Q-D19 and M19 stage 2), normal and --reload (25–55); 11 quest stubs; quests.py 0 errors but D4's player bit 1 (A6) |
| Towns (rosters, teachers, stock) | A4 | Vertigo, Rivercity live; every other town as planned data (Act II, Darkside, Lakeside, Necropolis, Olympus, Bosco's Hall, Shangri-La); teacher plan 116/116; inn rosters 18; 148 flavour topics; new-game card block; five-door Dimension Door art | planned files become built as the maps are drawn |
| NPC portraits | A4 | 427 (2026-11-21: 427 NPCs; Rivercity 20 teacher offers after D-73) | |
| New creatures (10–13) | S | 9 + Doom Bug (toad, witch, sprite, swarm, Flying Feet, Guardian, Carnage Hand, mole, sorceress with Morgana's `sorc_m`); decorations: great-tree crown, sand-fall, 7 quest-item ground models, hay bale, woodpile, Crodo's bottle; 275 descriptors, 0 refused; Meshy 205 credits | Act III–IV creatures next (mantis, sand worm/armadillo, sabertooth, electrapede, octopod; ≤ 30 credits each), then xeen_guard (D-19) |
| Sounds (ElevenLabs) | AU | batch 1: 15 monster family sets + 11 pitched tier sets, 20 world/event sounds, 10 ambience beds (review page `level_generation/sounds/xeen_20261120/review/index.html`) | hooks being wired; outdoor beds wait on E9 |
| New textures (world cap 450) | A6 + map lanes | 108 (57 dungeon, 51 kit) | `source/textures.yml`, `level_generation/xeen_art/register.py` |
