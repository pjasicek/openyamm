# G: the Xeen guide website

The user (2026-11-21 13:28): "I want the guide which we have for MM9 (and also on the server) to have it also for the
Xeen, like same formats, same walkthroughs, minimaps, locations, teachers and stuff like that ... we should have all
the data." Later (relayed by the orchestrator): finish the hand-written story, consulting the story side (A3's files,
the original data A3 ported, the quest files, the playthroughs) instead of guessing; questions go to A3 as
"QUESTION for A3".

## Owns

- `tools/xeen_site/` (generator, config, story, FAQ, capture scripts, deploy script, README).
- The shared parts it changed in `tools/mm9_site/` (generic, MM9 output unchanged): `web/app.js` (`GUIDE.site` texts,
  travel extras and world links, giver text and reward, teacher `when`, promotion path chip, `defaultFloor`),
  `web/style.css` (four rules at the end), `build_site.py` (parameters with MM9 defaults on `load_monsters`,
  `build_items`, `load_story`, `load_faq`, `attach_shots`, `attach_portraits`; `read_tsv` skips a "# Generated"
  banner; the story loader also matches a house's `people`), README paragraph.
- Output: `output/xeen_site/` (the site), `output/xeen_site_work/` (plans, checks, scratch), `output/xeen_site_shots/`,
  `output/xeen_site_monsters/`.
- The server folder `/var/www/html/openyamm/xeen-guide/` (via `tools/xeen_site/deploy.sh`).

## State (2026-11-22, end of the ninth session)

- **Ninth session (14:12-14:25 by the machine clock): the guide follows A3 38th-39th (topics by role, journal lines,
  D-93 cursor finds), F19 walls, D-92 signs, D-95 sunken entrances and D-96 villagers; republished** (`data/guide.js`
  matches the server, md5 235742b3...; the new figures and the recaptured shots too).
  - Data against the s8 copy: `quest_hooks.yml` changed only in D-93 (`m2.rain_barrel`, `q-c18.book` give the item,
    no `map_gives`). Points: X1 "Rain barrel" (objective, m2) replaces the ground "Warehouse Key", X5 "A torn pack"
    (q-c18) the ground "Holy Book of Elvenkind"; X1's culvert grate moved about 600 south into its ditch; X4's undercroft
    stair about 600 north, the rule stone about 1,000 to the pedestal ring's north-east. Journal stages: m37/m38 gained
    four lines each, q-c25 and t2-clan new lines, done-lines gone (m22, m42, q-c9, q-c26, q-d16, q-d17, q-d24-26, q-f1,
    q-f2; quests left with no line show none). No other point moved over 200.
  - Walkthroughs (two sub-agents, checked against `output/a3_s39/renamed.txt`, the quest files and `npc_topic.txt`): every
    renamed topic reads 'Quest' or 'Promotion' (act1-6 about 60 edits, promotions 32, side files about 110); an NPC with
    several Quest topics at once names them by slot order (Artemus m6/m7/m12/m22, Emerson m9/m10/m11/m22, the Pharaoh
    m28/m30/m36, Burlock m5/m35, Thaddeus, Jethro; all stay visible, checked in the quest files); afterwords described
    where useful (Dudley 'Joe', Valia 'Falista', Ellinger 'Alamar', Dimitri 'The Songbird', Burlock 'Lord Xeen', Arie
    'My master' with Golux, Tito, Scaldrith 'The tax', Oslo 'Tam', Otto 'Lesson'); Luna's statuettes and altar one topic;
    m18 'Bow low, slave!' and 'Gifts'. m38's journal sentence fixed. FAQ unchanged.
  - Lead's own text: m2 rain barrel (click: key on the cursor, Android into the packs), culvert grate in its ditch beside
    the warehouse (the creek arch is only the outfall), Fenwick's topic until the key is found; q-c18 torn pack; q-c5/
    q-c11 rule stone north-east of the ring, undercroft stair cut into the square north of the well; Shops lead: every
    service hangs a sign (guild school signs, the inn's key and heart).
  - Captures (`tools/heavy.sh 6`, at most two games): arrival and giver shots of X1-X6, D1-D4, D6 (before copies
    `output/xeen_g/s9/before_shots/`, sheets `sheet1.jpg`, `sheet2.jpg`: villagers, signs, walls; nothing cut).
    D4's Leafpoint (a22) showed the inside of his trunk since the seventh session: `capture_shots.py` `FAR_NPCS` puts the
    camera 1,400 off with the pitch up; the whole tree shows now. New story figures from place tours
    (`output/xeen_g/s9/place/`): `x1_culvert.webp` (m2) and `x4_undercroft.webp` (q-c5); `asp_pedestals.webp` redrawn
    (rule stone moved). Creek ends and other walls show in no guide picture (place shots kept in `place/`).
  - No NPC topic screens in the guide (houses have no 3D view), so Falagar's topics needed no capture. Dimension Door is
    not in the guide. `check_story_refs.py` 0 problems. Fresh copies in `output/xeen_g/s9/`: `quest_hooks_1412.yml`,
    `npc_topic.txt`, `npc.txt`, `npc_topic_text.txt`, `quests.txt`, `quest_sources.tgz`, `guide_before.js`,
    `guide_after.js`, `poidiff.py` (points matched by type, name and text; moves over 200 units).

## State (2026-11-22, end of the eighth session)

- **Eighth session (05:50-06:00 by the machine clock): the guide follows A3 36th-37th, A6's D6 gate and A8 30th's
  XD-12 disc; republished** (`data/guide.js` matches the server, md5 d28cbf1a...).
  - `quest_hooks.yml` against the s7 snapshot: one change only, `q-c25.inner_door`'s `where` (east wall). The rest of
    A3 36th (the retired `q-d14.quarter_gate`, `q-d28.sewer_grate`, `q-d15.lair_door`, `m33.arrival_gate`, the X1/X2/
    X7/X5 ground items, the q-c2 strongbox pendant, Fenwick's `{not: {found: warehouse_key}}`) was already in the
    03:13 snapshot and the seventh session's build; checked again: no walkthrough leans on a retired hook, the ground
    items read "Pick it up like any item", the strongbox step stands. World files newer than the s7 build: only D6
    (gate event 33 calls the hook) and XD-12's Lua; `build_site.py` output differs only in D6 e33 (now an m33 point and
    the quest's first step) and q-d10's shown level (the known `quest_levels` tie-break). No point moved.
  - Text: m33 (act5) the gate refuses without Corak in the Soul Box (the status line "Chosen Ones. You have nothing I
    need to fear.", the gate stays shut), the window only with him; q-c25 the inner door "in the tax hall's east wall";
    m21 (act4) tip: the grille stands open while the disc is up on Darzog's floor and shuts while it is down, the
    bottom button calls it from the gate floor; m2 (act1) Fenwick's topic shows until the key is picked up. D4's boat
    locker (e53) is a plain chest point; no walkthrough named it, nothing to change.
  - No shot recaptured (D6's points did not move; XD-12 changed only its Lua). `check_story_refs.py`: 0 problems.
    Before copy `output/xeen_g/s8/guide_before.js`, diffs `jsdiff.txt`, `poidiff.txt`; hooks snapshot
    `output/xeen_g/s8/quest_hooks_0553.yml`.

## State (2026-11-22, end of the seventh session)

- **Seventh session (02:50-03:35 by the machine clock; started by openyamm-65 at its 05:30): the guide follows the
  night's world (D-89 gating, D-90 finds, F16 entrances, D-91 caves, the dungeon identity rebuilds); republished**
  (`data/guide.js`, all webps and story figures match the server; MM9's `data/guide.js` rebuilt into scratch is
  byte-identical to the local and the live copy; `tools/mm9_site/` not edited).
  - Generator (`build_site.py`): chests list their `fixed_items` ("Holds ..."), and a chest holding a quest item a
    hook records in `map_gives` is merged into the quest point on the same spot ("A wooden chest holding ..."); items
    lying on the ground (scene `sprite_objects` with an item) are points: quest items as objectives named after the
    item (Warehouse Key, Ligono's Skull, Holy Book of Elvenkind, Ever-Hot Lava Rock, Golden Pegasus Statuette, Key to
    the Western Tower, Jewel of Ages, Golden Dragon Statuette, Alacorn of Falista), other loot as "Chest / loose item"
    (the legend's new name; XD-01-03 potions and tools, the planes' potions). README "Sources" says so.
  - Walkthroughs (two sub-agents, checked against quest sources, hooks, map Lua, rooms.yml): the ten opened doors and
    retired keys, Nadia's/Nibbler's/Arie's/Vespar's new rewards, Sandcaster open, the inward locks (XD-11 study chest,
    XD-18 King's door only, DD-12 cage, DD-15 antechamber), Q-C7 without night, status lines instead of windows,
    entrance windows instead of Yes/No, ground and chest items, the X7 shelters, rebuilt routes (XD-05, XD-16/17
    fissure, XD-23 warren, DD-04, DD-11C, DD-20 sump ladder, DD-23, DD-08, FD-03 gong route), pronouns (Autumn Druid).
    All story map references resolve (`output/xeen_g/s7/check_story_refs.py`, also checks inline-map `focus`).
  - FAQ: Newcastle (Ebenezer names the two dungeons; both open), gems (the tax buys the Dragon King's audience only).
    Shops lead: guilds sell Xeen's own spellbooks, which also drop. `extra_pois.yml`: X6 e81 (the Sphinx's door: first
    click opens, second enters), XD-18 e7 (King's door: "Tax first") and e14 (inner door opens for anyone).
  - Captures: all 82 arrival views and outdoor giver shots recaptured (XD-20 cannot); before copies
    `output/xeen_g/s7/before_shots/`, sheets `output/xeen_g/s7/s1-s3.jpg` (27 rebuilt maps, none cut or empty).
    Story figures redrawn (Bark dials and gongs shifted slightly). Bestiary: no new or changed placed monster row
    (11927 Sablewing, 11928/11929 druids are NPCs, not in the bestiary); no portrait recaptured.
  - Extra_pois renames checked against moved events: all still hit their objects (XD-11 gates, DD-12 statue, XD-13
    syllables moved a little with the rebuilds).
  - `quest_hooks.yml` unchanged since 03:13 (snapshot `output/xeen_g/s7/quest_hooks_0313.yml`); rebuild once more if
    A3's final chain changes it (`cmp` against the snapshot).

## State (2026-11-21, end of the sixth session)

- **Sixth session (20:10-20:25): checked the D-85/D-87/D-88 marker moves and the D7/P1 rebuilds; republished**
  (`data/guide.js`, D7 and P1 map images and arrival shots match the server; MM9's `data/guide.js` rebuilt into scratch
  is byte-identical to the local and the live copy).
  - Full rebuild: only monster points moved (X1 6, X2 21, X4 10, X5 5, X6 2, D1 4, D2 3, D3 2, D6 7); no named point
    moved on the outdoor maps. X2's inline maps show Danulf, the sprite eggs (4,576 WSW of him; three sprite groups
    within 1,690 of the nest; none within 5,989 of Danulf) and the Temple of Yak door (the five placed Killer Sprites
    1,600-2,600 from it, so "Killer Sprites roam around it" stands); X5's Randon map and D6's pod hatches unchanged.
  - Walkthrough text against the moves: only Rescue Celia was stale (X1's two skeleton groups between Derek's camp and
    the hut moved west of the hut): the step now reads "about 4,500 units south of the camp, a little east ... Skeleton
    groups roam the forest west and south-west of the hut". No text names the X4 renegades, D6's eyes, X5's wolves,
    X6's worms, D1's gremlins or D3's mantises by place.
  - D7: the framed mirror carries five events (glass, frame, posts, sill); `build_site.py` now marks one mirror point
    per mirror (same name, same storey, within 1,024), so Olympus shows one Mirror, not five stacked pins.
  - Recaptured the D7 arrival (Olympus's new walls and windows behind the Megadragon) and P1's (new crater walls);
    before: `output/xeen_g/s6/before_shots/`.
  - The `quest_levels` tie-break swapped m27 and q-d15 again (Next 5).

## State (2026-11-21, end of the fifth session)

- **Fifth session (17:20-17:45): republished** (`data/guide.js` and the changed webps match the server; MM9's
  `data/guide.js` rebuilt into scratch is byte-identical to the local and the server's copy, and the server's MM9 guide
  is untouched).
  - Recaptured S 13th's reskins with the session-4 framing: 11350 Hell Hornet, 11702 Guardian of Air, 11284 Power Lich,
    11285 Skeletal Lich (new colours from the front; sheet `output/xeen_g/s5/four_before_after.jpg`).
  - Dragons framed tighter: `capture_monsters.py` `CLOSER` puts the camera at 0.72 (Dragon `xeen_cdr1`), 0.85 (Dark
    Dragon `xeen_m492`, raised wings reach above the bounds) and 0.82 (Bone Dragon `xeen_m616`) of the bounds'
    distance; all 13 recaptured, wing tips and feet inside (`output/xeen_g/s5/dragons_after.jpg`; before:
    `dragons_before.jpg`). README says so. The Dragon Pharaoh (humanoid model) is unchanged.
  - XD-05's arrival line no longer names Gunther (A7): the drums step lost its "Mayor Gunther" clause.
  - Q-C9 (D-83): the step reads "With the Jewelled Amulet, click the door between the Sphinx's paws: 'The amulet grows
    warm, and the stone between the paws slides aside.' Click again to go in." X6's door point (e81) got the same
    detail in `extra_pois.yml` (the two-click door made the generator fall back to the hook's place, "on Desert of the
    Sphinx").
  - Q-C22: the first-visit hint is gone (D3 event 93 now enters on every knock once `q-c22.moved` is set).
  - S 14th's heart jar (DD-21) and P2 balloon basket: neither shows in any guide picture (arrival shots checked), no
    recapture.
  - FD-02's plan shifted slightly (the map was rebuilt elsewhere); no other change in `data/guide.js`.
  - Found: the MM9 guide's full build fails (`load_presentations` opens `assets_dev/worlds/mm9/ui/maps/*.pcx`, which
    are `.png` now); its `--skip-images` build with the existing `presentations.json` works. Request to the MM9 owner.

## State (2026-11-21, end of the fourth session)

- **Fourth session (16:00-16:20): bestiary portraits recaptured, all 286 plus 11651 and 11671; republished**
  (`data/guide.js` and the webps match the server; the MM9 `data/guide.js` rebuilt into scratch is byte-identical to
  the local and the server's copy).
  - `capture_monsters.py` now frames by the larger of the collision box (placed actor, else the descriptor row) and the
    3D model's drawn size (its static GLB bounds at the `actors.yml` scale: the swamp things' treant 1,155 tall, the
    dark dragons 1,428 wide), measured to the model's front, keeps the monster's back 100 off the hall's north wall,
    and looks down by the crop's offset (the old `+ CROP_AIM` looked up and sat every monster low: feet, toads, rats,
    moles, octopods, hydras, trolls and giants were cut at the bottom). README states it.
  - Lane S's 27 recoloured tiers show their new colours from the front (sheets `output/xeen_site_work/caps/after_*.jpg`,
    the old ones `before_*.jpg`); no portrait is cut off, empty or from behind. 11651 (Green Dragon) and 11671 (Undead
    Dragon) have portraits now but no bestiary row: no map places them (the bestiary lists placed monsters only).
  - Not landed, so not folded in: D3 event 93 still enters only through the once-only `q-c22.cottage` hook (A5), and
    XD-05's arrival line still names Mayor Gunther (A7); both hints stay.
  - The rebuild swapped the shown map of two quest levels again (m27 dd03 to dd14, q-d15 d4 to dd23: the known
    `quest_levels` tie-break); nothing else in `data/guide.js` changed.

## State (2026-11-21, end of the third session)

- **Published**: https://jasicek.net/openyamm/xeen-guide/ (republished at the end of the third session;
  `tools/xeen_site/deploy.sh`, SSH and `sudo -n` work without a password; the server's `data/guide.js` matches).
- Generator: all 82 maps, 6,257 points; 109 quests, all with hand-written walkthroughs; 24 promotions; teachers, shops,
  services, travel, 286 monsters with portraits, 112 items, FAQ (12).
- **D-76 and D-79 done**: point details are player text and never say how to solve a puzzle. The third session swept
  every sign, objective, lever, hint and quest point (two read-only sweeps, judged by hand) and cut 85 points in
  `extra_pois.yml` (`rename`, under "D-79"): the 13 obelisk words, the Dragon Rune books, the Book of Ascension, the
  Asp rule stone (x4, xd25), the Count's sign and x3's sundials (dd17's wording), dd09's dials (named East/North/West),
  dd12's statue, gate carving, lever plaque and lever hall (all twelve levers now read alike, so the working one does
  not show), dd15's pad map, rule statue, tapestry combination and verses, dd26's note pieces, fd01's "Nine is the
  time", fd02's letter runes, d2's whispering stone, d5's boulder riddle and xd15's hieroglyph riddle (letter riddles
  spelling a typed answer), d7's true-name plaque, x5's gong plaque, x9's "9N" sign, Crodo's vault word (xd12), xd13's
  syllables, xd21's ledger. `extra_pois.yml` `solutions` lists each map's solution phrases (map-wide; per point for
  short pieces such as FI/IN/NI/TY and the obelisk words) and the build stops on any of them (`declared_solutions`,
  `says_solution` in `build_site.py`; checked against the old output: 68 faults found, 0 now). README "Player text"
  states D-79. Kept by the test: xd02 e33 (the dwarves' pools check nothing: bonus effects), x8 e15 and x9 e36-e39
  (quest lore, the NPCs ask openly), x3 e54/e55 ("A stitch in time", "Lives of a cat": cryptic), fd02's books and
  throne naming Picard (the person is on the map by name).
- **D-80 done**: the Shops lead says the stock is enchanted and rises town by town (Vertigo mostly plain, the late towns
  magic gear) and that Xeen's shops and treasure are MM6-MM8 items, the "MM9 loot in MM6-MM8" setting not applying.
  The shop data itself did not change with merge point 33 (qualities are A4's).
- **Landed fixes folded in**: Q-D10 (robbers get the chest's 2 disks and nothing from Sharla), Q-D15 (the glass only
  after the roost: the roost step is no longer optional), Q-C1's rest tip dropped (rest keeps magical age). XD-05's
  drums clause stays until A7 fixes the arrival line.
- MM9 guide unchanged: rebuilt into scratch, `data/guide.js` byte-identical to the local and the server's copy;
  `tools/mm9_site/` not edited.
- Known: the shared `quest_levels` breaks ties between equally rated maps by set order, so a rebuild can swap the
  shown map of a quest level (m27, q-d10 this time; the level itself stays).

## Next

0. After later story changes: `cmp output/xeen_g/s9/quest_hooks_1412.yml assets_dev/worlds/xeen/data_tables/quest_hooks.yml`
   (and `npc_topic.txt`, `quests.txt` against the s9 copies; `output/xeen_g/s9/poidiff.py` for points);
   if it differs, `build_site.py --skip-images`, `check_story_refs.py`, deploy. D7, X8, X9, D3, D5 still ask Yes/No at
   some entrances (not yet rebuilt for F16): their walkthrough lines follow the built Yes/No and need a pass after.
1. (Done in the fifth session: Q-C22 hint, XD-05 drums clause, Q-C9 two-click door.)
2. Any new clue text on a map: judge it by D-79 and add its phrases to `solutions`.
3. More figures if wanted (the Witch Tower's skulls, XD-15's riddles, the Skyroads' merchants); more hand renames for
   generic points.
4. Rerun the captures after map changes (`capture_shots.py --maps ...`, `capture_monsters.py --ids ...`; through
   `tools/heavy.sh 6`; a `--skip-images` build keeps an existing webp, so delete the recaptured maps' `img/shots` webps first); S's next
   recolours (Power Lich, Skeletal Lich) need `--ids 11284,11285`.
5. Optional: make `quest_levels`' tie-break stable (sorted maps) once the MM9 owner agrees (MM9 output may change).

## Requests (to other lanes, through the orchestrator)

- MM9 guide owner: the MM9 point detail `isleofashes a14` ("Fre's Rain: special_passage") shows an identifier; the
  Xeen build's developer-wording check flags it (`build_site.py` `DEV_WORDING_RE`). The MM9 output was left unchanged.
- MM9 guide owner: `tools/mm9_site/capture_monsters.py` adds `CROP_AIM` to the pitch, which looks up and sits the
  monster low in the crop (in the Xeen copy it cut feet and small, long or big monsters at the bottom); subtracting it
  centres the monster. Not checked against the MM9 portraits; the MM9 tool was left unchanged.
- MM9 guide owner: `tools/mm9_site/build_site.py` `load_presentations` reads `worlds/mm9/ui/maps/<map>.pcx`, which are
  `.png` since 2026-11-09, so a full MM9 build (without `--skip-images` and an existing `presentations.json`) stops.
- MM9 guide owner (D-79): move the Gemstone angles and the Floor plates order out of `tools/mm9_site/extra_pois.yml`
  (darkpassageway) and judge the Academy tables by the same test.

## Log

- 2026-11-22 14:12-14:25 (ninth session): topics by role (two sub-agents), D-93 cursor finds, culvert ditch, Asp stair
  and rule stone, signs sentence; 11 maps' shots recaptured, Leafpoint framed (`FAR_NPCS`), two new figures, Asp figure
  redrawn; story refs 0 problems; republished, live md5 matches.
- 2026-11-22 05:50-06:00 (eighth session): hooks diff (only XD-18's east wall), rebuild diff (D6 gate, q-d10 level);
  m33 gate refusal, q-c25 east wall, XD-12 disc/grille tip, Fenwick topic; `--skip-images` build, story refs 0
  problems; republished, live md5 matches.
- 2026-11-22 02:50-03:35 (seventh session): full rebuild on the night's world; chest items and ground items in the
  generator; walkthroughs (two sub-agents), FAQ, Shops lead, three point texts; all arrival shots recaptured; story
  figures redrawn; MM9 output byte-identical; republished; live pages checked headless.
- 2026-11-21 20:10-20:25 (sixth session): checked the D-85/D-87/D-88 marker moves (only monster points moved; X2 nest,
  Danulf and Yak door shown right), Rescue Celia's skeleton line, one mirror point per mirror (D7), D7 and P1 arrivals
  recaptured; full rebuild, MM9 output byte-identical; republished; live checked.
- 2026-11-21 17:20-17:45 (fifth session): four reskinned portraits and the 13 dragons (tighter, `CLOSER`) recaptured;
  XD-05 drums clause, Q-C9 (D-83) step and X6 door point, Q-C22 hint; full rebuild, MM9 output byte-identical;
  republished; live pages spot-checked headless.
- 2026-11-21 16:00-16:20 (fourth session): capture framing by model size and to the front, pitch sign fixed; all 286
  portraits plus 11651/11671 recaptured and checked on contact sheets; rebuilt, bestiary checked headless, MM9 output
  byte-identical; republished. A5's D3 event 93 and A7's XD-05 line not landed.

- 2026-11-21 13:30-14:45 (first session): read the MM9 guide and the world; refactored the MM9 tool's shared parts
  with defaults (MM9 output proven unchanged); wrote `tools/xeen_site/` (generator, config, FAQ, captures, deploy,
  README, story brief); two sub-agents wrote the walkthroughs; published the first version.
- 2026-11-21 14:45-16:30: storeys, SpeakNPC people, hook exits (the planes), merged exits and hook points, edge spans,
  hook-named generic points; all 109 walkthroughs in; portraits and shots captured; republished.
- 2026-11-21 14:20-15:40 (second session): D-76 (player-text point details from hook texts and prompts, answers kept
  out of the map pages, puzzle pieces of the common script, named clickables, the developer-wording and answer check,
  generated rewards cleaned, story source talk removed, quest ids to titles, home lead); A3's 44 answers and D-77
  folded in; `extra_pois.yml`; `story_figures.py` (five figures); arrival reframing (23 maps recaptured); MM9 output
  checked byte-identical; republished.
- 2026-11-21 15:05-16:00 (third session): D-79 (sweep, 85 points cut, `solutions` check, README sentence); D-80
  (Shops lead); Q-D10, Q-D15 and Q-C1 lines updated; rebuilt, routes shot headless, MM9 output byte-identical;
  republished.

## Questions for A3 (from the side-quest walkthroughs, 2026-11-21)

The walkthroughs describe what the scenarios and the built maps do; these are where the sources disagree or stay open.

1. Q-C1: resting and travel already clear magical age (`Party.cpp:339`); is the Spring Druid's reward still "removes magical aging"?
2. Q-C4 / T2-CLAN: is the way down to Shinobu's cellar the mat trapdoor (XD-22 event 18) or the kitchen ladder under the dojo hatch?
3. Q-C5: does the pedestal timer check only the final colours, or also that the south-west pedestal is touched first?
4. Q-C6: the quest file's gong asks "Bang on gong?", X5 event 149 asks nothing. Which is intended?
5. Q-C8: is `after: [m7.sigil]` a real requirement? Arie's topic has no `show` condition.
6. Q-C9: X6 event 81 never shows "The amulet grows warm..." (open issue A5). Is a fix planned? **Answered (D-83):** the door takes two clicks; the first shows the line and stays on X6, the next enters XD-15.
7. Q-C13: can the Water Dragons be fought from the shore, or does the party need Water Walk or flight?
8. Q-C16: the hook says "Burn?" and burns a destructible; X5 event 112 fires at once and the tents stay (D-72). Which is intended?
9. Q-C22: does the D3 sequel (the cottage hook, Celia's "The sword", the camp hidden on `q-c22.moved`) work? The text says zombies; the forest spawns skeletons.
10. XD-05: the arrival line says Gunther asked the party to silence the war drums; no topic gives that task.
11. obelisks.yml and x8-sky.yml still say "pending: not built" / "X8 not built", though the scenarios pass: stale notes?
12. X8-SKY has three nests, the L1 plan four (one in the Queen's eyrie): dropped on purpose?
13. Q-F1: is FD-01's key vault box (D-69, 117844) the guide's FD-01 e5 "The key chest in the warden's room" (tagged m39)?
14. Q-D1: is the treasury's 600 gold meant on top of the fight route's 3 disks?
15. Q-D2: the header says the jail window works "at night"; the hook has no time condition.
16. Q-D7: each smith gives one fixed item (12540-12543); QUESTS §2.2 says "weapon or armour". Final?
17. Q-D10 robbery route: Sharla's "freed but not polite" payment does not check `treehouse_looted` (2 + 2 disks?); is Sharla reachable once the village is hostile; can Sheewana still be freed?
18. Q-D13: the quest starts only on the thief's letter, but nothing later checks that bit. Intended?
19. Q-D15: the glass hook has no `requires`; taking the glass without destroying the lair: intended?
20. Q-D16: nothing reads `q-d12.friends`; what does peace with Yog change? After war with Yog, can the party still talk to Gurodel?
21. Q-D19: the Master Thief "fights after inner_circle is refused", but there is no refuse choice.
22. Q-D23: the note calls the plain release "the light route", but it promotes nobody and Morbius still offers the Dark promotions after it.
23. Q-D26: the Megadragon pays 16,875 shared by the party; was 67,500 shared (16.9k per member) intended?
24. Q-D27: D2's and D4's small lamps say nothing on a second rub; should they get "The lamp is cold."?
25. Promotions: until engine item O2, a hand-in promotes every eligible member at once. Is "do the other path's quest first" the intended advice for splitting one class line?
26. T2-CLAN: Shinobu speaks of "the Dark Queen's walls", but her check is `m20.started`. Intended?
27. T2-A: Dimitri marks the test done and pays 6,000 with no Cavalier in the party. Intended?

## Questions for A3 (from the main-story walkthrough, 2026-11-21)

28. M1: is QUESTS.md's pest kill count meant to be built, or is "no pest reward" final (the guide says M1 closes with Joe's invoice)?
29. XD-06's heavy coffin checks base Might 25 (potions don't count); segment 23 says 30 and D-4 "Might ≥ 30". Which?
30. The m12 `skull_upper` hook says the upper skulls are "by the north mouth"; as built they are by the frost cavern near the south mouth.
31. m13 puts the Archmage's study "on floor 3"; the plan's top floor: the same?
32. m18's header lists "the Northern Tower 2", but DD-08 holds no disks; the two come from Q-D17 (Bosco or the Voweless Knights). Intended source?
33. QUESTS §4.2 promises six disk safes on Kalindra's second floor; built: one safe with 4 disks (`m24.disk_safes`). Is 4 final?
34. Ellinger's Tower door question is typed ("Let him take up his sword" / "Cut him down"): other wordings accepted?
35. Natasha (M25) is in Sandcaster, whose gates need Q-D8's pass; the playthrough places the party inside. Is Q-D8 a requirement of M25?
36. Ellinger's stage-4 line says to find the pyramid key in the castle; the Queen hands it over in M27. Change the line?
37. A3.md says the cloud stair refuses with "It will not bear you yet"; the map asks "Climb the cloud stair into the sky?" once Crodo is free (the guide follows the map).
38. Lucio's topic says "Chosen Ones ride free", but Lakeside charged 250 gold in segment 73. Which?
39. The Great Pyramid's four verse statues lead to no answer: acceptable under the no-unanswered-riddle rule?
40. Slick's booths check the active character, not the best member; intended, and do temporary bonuses count?
41. Alamar's dial and true-name autonote (4134) arrives only when the gate opens, after it is needed: earlier (Atlas's "Nine" topic)?
42. The Earth Reflector's event point (-12288, -19763) is about 3,600 from where segment 85 clicks it (-8960, -18227): which is real?
43. Picard says Halon lives "just north of Darkstone Tower"; his workshop is about 20,000 units north-east.
44. Award 417 is "Made Xeen One World" in m42.yml, "Unified the World" in segment 99's comment (the guide uses the quest file's).

## A3's answers (A3 session 29, 2026-11-21 14:10-15:00)

Each answer says what the game does now and which source rules, then the kind: **(a)** the guide is wrong or should
say more (the text for G), **(b)** a quest-file or text fault (fixed, or a request to A3-side, which owns `q-*`), **(c)** a
map or engine fault (a request to the owner), **(d)** a design question (sent to a decider). "Fine" means no source is
wrong: the guide already matches the game. The game's Lua and the quest files rule. QUESTS.md is the older plan.

1. **Q-C1, (c) engine, A1.** Every rest, revival and long rest-less stretch clears `ageModifier`
   (`game/party/Party.cpp:339`). MM7 does not do this: OpenEnroth's `resetTempBonuses` keeps it. The reward stays
   "removes magical aging" (`Xeen.renewAges`). G: keep the reward and add the tip "For now, a rest also clears magical
   aging." Drop the tip once A1 fixes it.
2. **Q-C4 / T2-CLAN, fine.** The way to the cellar is the mat trapdoor (XD-22 event 18 opens door 7; event 28 opens it
   on load once `q-c4.done` is set). Promotions segment 25 proves it. The kitchen ladder joins the kitchen and the
   dojo only.
3. **Q-C5, fine.** X4's timer (event 176) checks only the final pattern: the four corners red. The order of touches is
   never read. (Request to A3-side: in `q-c5.yml`, the `where` should say "the final pattern", not "south-west
   first".)
4. **Q-C6, (b), request to A3-side.** The game rings the gong on a click with no question (X5 event 149). That is
   right by D-72: ringing costs nothing, so the map asks nothing. In `q-c6.yml`, the `gong` hook's `where` should say
   "the map rings it on a click and calls this (no question, D-72)". The guide is right.
5. **Q-C8, fine.** `after:` only orders the main quests for `quests.py`, so on a side quest it is never a requirement.
   Arie's topic has no gate. G: give no prerequisite.
6. **Q-C9, (c), A5 (with A1). Answered by D-83 (A5's two-click door kept; the guide's step says so).** X6 event 81 sets the status line and then moves the party. The side scenario still
   finds no "The amulet grows warm..." on arrival, although merge point 17 carries status lines over a move. Request to
   A5: show the line from XD-15's arrival once 112180 is set, or find with A1 why the carried line drops. G: keep the
   line in the walkthrough. It is the quest file's text and will show once the map is fixed.
7. **Q-C13, (a).** The Water Dragons fly (row 11640: Fly, a Water missile and Ice Blast). Their leashes keep them
   within about 300 of a bank at the far end. G's tip: "The dragons stay close to the banks: ranged attacks and spells
   reach them from the shore or the islands, so Water Walk is not needed." No scenario fights them from the shore
   (they are tested from the lake), so the tip says "close to the banks", not "always in reach".
8. **Q-C16, (c), fixed by A6 at 14:35.** X5 event 112 now asks "You have found the Cyclops' outpost! Burn?" with
   Yes/No. Yes hides the tents and calls the hook; a burnt outpost does nothing. This matches the quest file (D-72:
   destroying is a real choice). G: "Click the outpost and answer Yes to 'Burn?': the tents burn and Glom pays." A3-side
   reruns its Q-C16 scenario.
9. **Q-C22, (c), A5 (D3); (a) for the monsters.**
   - The first knock works: `q-c22.cottage` moves Celia and Derek in and enters house 4647.
   - Every later knock does nothing. The hook is `once` and has no else line, so `XeenQuests.hook` returns false and
     D3 event 93 never enters the house again. Celia's "The sword" can then be had only on the first visit.
   - Request to A5: D3 event 93 should enter when `IsQBitSet(QBit(112443)) or XeenQuests.hook("q-c22.cottage")`, as
     the hook's `where` already says ("enters the house when q-c22.moved is set").
   - "The sword" is Celia's topic, not Derek's.
   - G: "Five zombies wait round the ruined shrine; the groups that roam the forest are skeletons."
10. **XD-05, (c), A7; (b) fixed.** Nobody gives the drum task: Gunther has only Pests, Joe's invoice and Dwarves. The
    drums are part of Oslo's quest.
    - Request to A7: in XD-05's arrival line (event 1), replace "Mayor Gunther asked you to silence them." with, for
      example, "Oslo the farmer says the orcs took his son Tam into these caves."
    - Fixed in `x1-tam.yml`: the last drum's line now ends "Oslo will want to hear of it." (He has the Drums topic.)
    - G: the drums belong to X1-TAM and are not Gunther's.
11. **Obelisks / X8-SKY, (b), fixed.** The notes were stale. Every map is installed and the three scenarios pass. The
    `pending:` fields in `obelisks.yml` (10) and `x8-sky.yml` (4) are now plain notes naming their hooks; `quests.py`
    shows 0 errors.
12. **X8-SKY nests, fine.** There are three nests. The fourth was dropped on purpose at L2: the queen's great nest in
    the eyrie is her hoard, not a nest to burn. That reason is now in `x8-sky.yml`'s nest_3 note.
13. **Q-F1, (a), optional.** These are two containers. The key vault's Box (FD-01 event 20, 117844) gives the Key to
    the Dragon Tower, which is Q-F1's key. The warden's chest gives Darkstone Tower's key (M39). G may add
    `{map: xeen_fd01, name: "Box"}` to Q-F1's points.
14. **Q-D1, fine.** The fight route's treasury chest is the dungeon's hoard: T3, 600 gold, two items and the 3 disks.
    The peace route gets Snarfblad's 3 disks instead. Both routes get his 2,500 gold.
15. **Q-D2, (b), request to A3-side.** The window works at any hour: the hook needs only `started` and not
    `jasper_freed`. In the `q-d2.yml` header, drop "at night". The guide is right.
16. **Q-D7, fine.** U-1 (no new equipment) makes it final: one fixed item per smith (12540-12543). QUESTS §2.2's
    "weapon or armour" is the older plan's wording (request to the orchestrator below).
17. **Q-D10, (b), a bug, request to A3-side.**
    - On the robbery route, freeing Sheewana and then talking to Sharla pays "two Energy Disks and a LOT of gold, as
      agreed". Her paying state checks only `sheewana_freed`.
    - Together with the treehouse chest's 2, the robbers get 4 disks and 3,000 gold (plus the 2 alcove disks).
    - The header's intent is that the chest is the robbers' alternative.
    - The fix, in `q-d10.yml`'s Sharla topic 1: a state `when: {qbit: robbery}` before the paying states, with a
      cold line and no payment, e.g. "You came to rob us. Sheewana is home, and that is all you will have from me.".
      Optionally, the chest's fail text should not say a sprite sits on it when the sprites are dead.
    - Sharla can be reached on every route: D2 event 1 enters house 4553 with no check, and a house ignores the hostile
      relation.
    - Sheewana can be freed on every route: her topic needs only `cage_opened`, and gives 6,000 each and her move home.
    - G, once the fix lands: "Robbers get the chest's 2 disks and nothing from Sharla."
18. **Q-D13, fine.** The letter only opens the journal entry. Hobstadt's topics, the throne and the hoard do not need
    it, so the guide's "optional, starts the quest" is right. (Request to A3-side: the bits' "pending: phase 3"
    notes are stale.)
19. **Q-D15, (b), a bug, request to A3-side.**
    - The plan (DD-23's NOTES, its graph role) and the quest's header ("Destroy the lair, take the glass") want the
      roost destroyed first, but the `glass` hook has no `requires`.
    - The fix, in `q-d15.yml`: `glass` gets `requires: {qbit: lair_destroyed}` and a `fail_text` such as "A nest of
      spoons, buckles and broken mirrors, and the gargoyles watch it from their roost. Break the roost first."
    - G's tip (side_darkside, q-d15) should then read: "The nest gives up the glass only after the roost is destroyed."
      Until the fix lands, the current tip is wrong: Caleb asks only for the glass.
20. **Q-D16, (a).** `q-d12.friends` is read only by Yog's own topics. Gurodel's People are friendly by default and turn
    hostile on Yog's "Battle!" (113242) or on a burnt camp (113244). A hostile actor cannot be talked to. G's text
    for side_darkside's q-d12 or q-d16:

    > "Gurodel's giants are friendly unless you fight the Sardaj. War, or a burnt camp, turns them hostile as well:
    > Gurodel will not talk, and only the bloody throne in the Giants' Hall gives his two disks."

    Peace with Yog changes nothing else.
21. **Q-D19, (b), request to A3-side.** There is no refusal. "Inner circle" either promotes or says nobody has the
    hands, and stays open. The Master Thief fights only when attacked. In `q-d19.yml`'s `master_thief` hook, the
    `where` should drop "or after inner_circle is refused". The guide is right.
22. **Q-D23, (b), request to A3-side.** D-74 §5 settles it: the release is `released`, not a Light promotion. Morbius
    teaches the ritual afterwards, so nothing crosses. In `q-d23.yml`'s header line 6, replace "(the source's ending,
    the light route)" with "(the source's ending; it promotes nobody, and Morbius promotes afterwards, D-74 §5)". The
    guide is right.
23. **Q-D26, settled by D-77.** 16,875 shared by the party (4,218 each of four) is intended. It is L×(L+10), equal to
    MMerge's Ruby Dragon, the highest in MM6-MM8. "16.9k per member" was a slip. G: "16,875 experience shared by the
    party (4,218 each of four)."
24. **Q-D27, (c), fixed by A6 at 14:31.** D2 event 46 and D4 events 73 and 95 now answer a second rub with "The lamp is
    cold. Its genie has gone back in for good." A3-side reruns its D2 and D4 lamp scenarios.
25. **Promotions, (a); O2 stays open (A1).**
    - Until engine item O2, a hand-in promotes every eligible member of the class line (`Xeen.promote`). So "do the
      other path's quest first" chooses the path for the whole class line; it does not split it.
    - D-74 lets a later member use either surviving promoter's unpaid later path.
    - G's sentence: "Until each character can choose a path, a hand-in promotes every member of that class at once. To
      send two members of one class different ways, keep one out of the party (at an Adventurer's Inn) for the first
      hand-in, then bring them to the other path's promoter, who promotes later members unpaid."
    - This is not tested with a parked member: the tests stand in with `SetPlayerClass`, D-77.
26. **T2-CLAN, (b), fixed.** The gate is right: `m20.started`, the Queen's castle rising (D-12.2). The wording was the
    fault. `t2-clan.yml` now says "Come back when Queen Kalindra's walls are rising". Promotions segment 25 asserts the
    line's start and passes.
27. **T2-A, fine.** D-74 §1: a quest pays once, on its hand-in, whoever it promotes. T2-A is its own quest (D-16, five
    liches), so Dimitri pays 6,000 with no Cavalier present. The guide is right.
28. **M1, closed: final as built (D-78).** M1 has no kill count and no pest reward. Its journal line runs until M2,
    and Joe's invoice closes it; Gunther pays once, in M2, for the cleanup and Joe together (the source's maze0028
    has no kill-count check). QUESTS' M1 row now says "no reward of its own, paid in M2". G: keep "Gunther does not
    pay for kills".
29. **XD-06, fine for the guide; test comment fixed.** XD-06's heavy coffin checks base Might 25 (`xeen_xd06.lua:103`),
    so potions do not count. D-4's "Might ≥ 30, potions counting" is XD-08's coffin in the Tomb (`xeen_xd08.lua:121`,
    `ActualMight 30`). Segment 23's comments now say "base Might 25". The guide is right on both.
30. **m12, (b), fixed.** The upper skull alcoves open off the frost cavern, about 2,100 from the south mouth. The hook's
    `where` now says so. The guide is right.
31. **m13, fine; fixed for clarity.** The study is at height 1920, the third floor above the ground and the top floor.
    The `where` now says "on the top floor (the third above the ground, 1920 up)".
32. **m18, (b), fixed.** DD-08 holds no disks. The 2 come from Q-D17's Chalice of Protection, by either route: Bosco in
    DD-25, or the Voweless Knights' plaque in DD-08.
    - The m18 header now says so.
    - Autonote 4118 now lists "the Southern, Western and Eastern Towers (2 each), the Chalice of Protection (2)".
    - G: name the source as "the Chalice of Protection (Q-D17), 2".
33. **Kalindra's safes, fine: 4 is final.** Kalindra's safes give 2 + 4 = 6 disks: the two thievery safes at stage 1
    and one disk safe with 4 at stage 2. That is M18's "Kalindra's own safes (6)", and the 25-disk count needs it.
    QUESTS §4.2's "six disk safes" means six disks (request to the orchestrator). The guide is right.
34. **DD-02, fine.** The question is not typed: three buttons (`AskChoiceWithAnswerSteps`, `xeen_dd02.lua:182`).
    - "Let him take up his sword" and "Cut him down" pass; "I just don't know" says "Begone!" and puts you on D1.
    - The only typed prompt in the tower is the password, Ellinger, at the top. Typed answers are matched whole (trimmed,
      any case).
    - G may write: "The door asks a question with three answers to choose from; either honest one passes, 'I just
      don't know' throws you out."
35. **M25, (a).** M25 needs no qbit, but you cannot reach Natasha without the gates: Sandcaster's outer gates want Q-D8's
    pass. Kramer's caravan lands outside, and the mirror is inside. The playthrough places the party inside the city,
    which PLAYBOOK §2 allows. G's M25 `requires`: "Dimitri's 'The Songbird' talk (M24) and the Sandcaster Pass (Q-D8,
    Vespar's Staff) to get through the gates." The quest file stays as it is: its header already names the pass.
36. **M26, fine.** The stage-4 line is the source's (dark/aaze0056:27, "close"). The key does come out of the castle,
    by way of the Queen's crown and her hand in M27. The line stays, and the guide's explanation is right.
37. **XD-12, fine.** The guide follows the map, which is right. Before Crodo is free, the stair says "The cloud gives
    under your foot like fog. Something holds it shut: Crodo would know what." After, it asks "Climb the cloud stair
    into the sky?" "It will not bear you yet" in A3.md is an old session note. G may quote the first line as a tip.
38. **Lucio, (b), fixed.** The boats charge their fare: segment 73 pays 250 at Lakeside, and the towns format has no
    free route. Lucio's line now reads "Chosen Ones may ride, the Pharaoh says. He doesn't pay the fare, mind: that's
    yours." The guide's "250 gold from Lakeside" is right.
39. **DD-15, fine under the rule.** The verses are the source's flavour (aaze0084:1-4) for the registry lock. Its answer,
    1701, is given plainly by the brass plaque (`m28.registry_plaque`). So no riddle is left that the game does not
    answer. The guide's "flavour; ignore the arithmetic" is right.
40. **Slick, fine, intended.** The booths test the clicking (active) member's current statistic (`ActualMight` etc.,
    60), as MM6-MM8's carnival games do. Potions, wells, items and the Sure-Eye Tonic count (D-70 depends on that).
    The guide is right.
41. **M33, (b), fixed.** Autonote 4134 (the gate's rule: four dials at nine, the name Sheltem) is now set by both ways
    into Castle Alamar: `m33.arrival` and `roof_arrival`, before the dial hall. It is no longer set when the gate opens.
    The answers themselves were already given plainly: Atlas's "Nine" in Olympus, and M31's plaque for Sheltem.
    Segment 77 asserts the note on arrival and passes, normal and `--reload`. G: "On entering, the journal notes the
    gate's rule."
42. **The Earth Reflector, fine.** The event is at (-12288, -19763), which is the Reflector. Segment 85's (-8960,
    -18227) is the ledge where its walk starts. The walk ends 512 from the disc, and `click()` runs the event by id
    without a distance check. The guide is right.
43. **Picard, (b), fixed.** The source says "Halon the Inventor, who lives just north of Darkstone Tower"
    (dark/aazex126:3), but X5's workshop is about 20,000 east of the tower and the NPC is Halon the Efficient. Picard
    now says "Go and see Halon the Efficient, the clockmaker, whose workshop stands east of Darkstone Tower in
    Winterkill Tundra." The change is noted in ORIGINAL_LINES' row. The guide is right.
44. **Award 417, test comment fixed.** It is "Made Xeen One World" (m42.yml, `awards.txt`). Segment 99's comment now
    says so; its assert checks the id. The guide is right.

**For G, in short:**
- Change the text for 7, 8, 9 (the monsters), 19 (now: the roost is optional, Caleb asks only for the glass; after
  A3-side's fix: the glass comes only after the roost), 20, 23, 25, 35, 41.
- Optional: 1's tip, 13's point, 34's wording, 37's tip.
- 17 changes when A3-side's fix lands.
- All the rest already match.
