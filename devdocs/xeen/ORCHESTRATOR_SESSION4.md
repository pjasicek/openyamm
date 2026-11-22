# Xeen: fourth orchestrator's running record

Started 2026-11-21 ~17:05 (session `openyamm-65`) from [HANDOFF_ORCHESTRATOR4.md](HANDOFF_ORCHESTRATOR4.md). Agent ids
below can be resumed with SendMessage only from this session; a later orchestrator starts lanes fresh from their lane
files.

At the start: every lane stopped, 0 stale bakes, `build_world.py --check` 0 differ, game binary merge point 35
(16:34:21), oymap 12:46:47. Disk 99 % (64 GB free), RAM 70 GB available, swap full. A peer session `openyamm-1c`
runs co-op scenarios on `build/` (not Xeen).

## Lane agents

| Lane | Session | Agent id | Started | Asked for | State |
| --- | --- | --- | --- | --- | --- |
| A3 | 32nd | a0fc04c61f28ebd1d | 17:10 | D-82 item 0 (61/67 DD-14 clears, 77 keys), whole chain both modes, rewrite checkpoints | done (~265k): chain 01–99 green both modes on MP36 with D-82; checkpoints rewritten 17:53–18:27 |
| A1 | 32nd | ac2dc90cc33152a06 | 17:10 | Return→Combat input leak, app case, MP36, MM9 chain PARTY DOWN report | done (~323k): MP36 released 17:48 (input leak, app 29/29, loot_chest closes); MM9 chain 41/43, no PARTY DOWN |
| A8 | 24th | ab608b3776f1a8562 | 17:10 | DD-14 playtest step 115, all A8 maps' tests on MP35 | done (~212k): DD-14 fixed (test), 29 maps on MP35 all pass (5 test fixes), 6 step-top rooms reinstalled + baked 4/4, 0 stale |
| A7 | 25th | ad9b22ae139de2bd2 | 17:10 | XD-19 ceilings (bake profile), event 61, all A7 maps' tests on MP35, E14 names if A2 done | done (~186k): XD-19 profile (ceilings grey), cinematics.yml installed (mirror cinematic now plays), 31 maps 119 tests on MP35 (XD-13, XD-22 test fixes) |
| A6 | 29th | adeb9853450ad0546 | 17:10 | D7 Olympus dressing install, P1 crater/vent install, old bake folders | done (~262k): D7 Olympus installed 17:16 (11/11, audit 0/0), P1 batter + vent 17:23 (9/9, 0/0); 2.2 GB freed |
| S | 14th | a1db97d649a01157b | 17:10 | heart jar glass, P2 basket install | done (~120k): both installed and seen in game; 335/84, 0 refused; 0 stale; no Meshy | 
| A2 | 22nd | ad4a2cadfe42bbe9b | 17:10 | monsters.yml records, D-81 balance.py, E14 placed_names | done (~188k): 15 families records = bindings, 7 skins fixed; D-81 choice_gems (Q-C25 +1 pass); E14 already in; --check 0 | 
| A3-side | 3rd | a929c872c0918c98f | 17:20 | D-83 scenario + q-c9 where, Q-C22, Q-D10 mercenary, D-82 asserts, all on MP35 both modes | done (~317k): 71/71 normal and --reload on MP37; D-83, Q-C22 status line, Q-D10 mercenary, D-82 asserts |
| G | 5th | a2560c60473a42f8f | 17:20 | 4 portraits, XD-05 drums clause, D-83 Q-C9 text, Q-C22 hint, republish | done (~144k): all 5 items, dragons tighter, republished; MM9 guide.js byte-identical |
| MX | 1st | aca3905071daa82e9 | 18:00 | MAW in Xeen: design XEEN_SUPPORT.md, balance/promotions/engine (may build as MP37 while A1 idle), MAW guide Xeen page + deploy | done (~379k): XEEN_SUPPORT.md, balance.yml 82 maps, promotions xeen bits, 5th bank (save 200), MP37 released 18:35:58, MAW guide deployed 18:41 |
| A3-promo | 6th | a7a0cbb559bec4c41 | 18:35 | refresh on MP36 checkpoints, D-82 asserts, seg 63 comment | done (~256k): 41/41 normal ×3 and --reload on MP37; D-82 per-member checks (20 hand-ins, 23 class tables); 24/24 |
| A8 | 25th | a53d0077d5d5480f1 | 18:35 | XD-12 gate-hall eyes (quiet arrival), DD-10C frost floor, DD-03/09 texture warnings | done (~231k): XD-12 Well eyes moved to the cistern (quiet arrival 3/3; A3 probe 37 3/3), DD-10C profile 1.2/3/1.0; 0 stale |
| MX | 2nd | a577b0af99bee657d | 19:10 | D-84 fixes (bands v2, gem gear), dungeon pack reserves to Beyond Madness, Vertigo teleporter, Seers + town-hall bounties, guide redeploy (may release MP38) | done (~428k): bands v2, gem rungs, pack_reserve.py (MM9 byte-identical) + 48 Xeen reserves, Vertigo pedestal, Seers Zephyra/Oorla, bounties, guide redeployed; no engine change |
| A5 | 26th | a068057e9c95fb8a8 | 19:45 | D-85 X2 markers + ring playtest; measure A5 maps' givers | done (~240k): X2 markers (nearest 5,989), X1/X4/X6/D3 givers cleared and reinstalled with bakes; check_d85.py; 0 stale; 13 GB freed |
| A6 | 30th | a711bd0deeaed9be9 | 19:45 | D-85 measure A6 maps' givers + D2 edge arrivals; D7 mirror; P1 NOTES | done (~328k): D-85 on X5, D1, D2 (edge arrivals ≥6,001), D6 installed with bakes; D7 mirror framed; P1 elementals fine; D7 reserve rerun |
| A5 | 27th | a928b50a64e4f13bc | 20:30 | D-87 ranged-disabler arrival check on A5 maps, X6 NOTES | done (~184k): checker with ranged-disabler filter in 8 build scripts; all A5 maps pass except X2 XD-06 exit (→ D-88); nothing rebuilt |
| A6 | 31st | a029080f76dcd07c6 | 20:30 | D-87 Randon undamageable + test, Graalg parley test, arrival check on A6 maps | done (~225k): Randon undamageable (test), Graalg parley test, D6 field eyes moved (≥6,608), X5/D6 installed 19:57/20:00; 0 stale |
| A5 | 28th | ab45e5acdf6a5c032 | 21:10 | D-88: X2 markers 17/20/21/22, waiver to group 63, rebuild with bake | done (~147k): X2 markers moved (≥6,110 from exits), `--kept-group 63`, installed 20:05, tests 2/2 |
| A3 | 33rd | a7099398c5972f1a7 | 21:25 | full chain both modes on the rebuilt maps; README D-82 rows; checkpoint 35 disease | done (~161k): chain 52/52 both modes on MP37 and the rebuilt maps; 71 DD-16 eyes fix; checkpoints 20:08–20:48 |
| A3-side | 4th | afe9631b67cad211f | 21:25 | all 71 side quests both modes on the rebuilt maps | done (~106k): 71/71 normal and --reload on the rebuilt maps, no fixes needed |
| A2+G | 23rd/6th | ad7897001150bbda2 | 21:25 | balance confirm on rebuilt maps; guide maps/text check, redeploy if changed | done (~230k): no balance drift (acts unchanged, markers only moved); guide: Celia step text, one D7 mirror pin, D7/P1 shots; redeployed |
| A3-promo | 7th | a0969d5ce41a920f1 | 22:15 | refresh on A3 33rd checkpoints, full both modes, 03 ring clear | done (~138k): 41/41 normal ×2 and --reload; 21 hall fought from the stair; 03 clear 3,000; 24/24 |
| A5/MX | pedestal | a42c0eee04da76699 | 22:50 | Vertigo dimensional travel pedestal for every ruleset (world overlay), drop MAW-only copy | running |
| A1 | 33rd | a244200000ca9c10f | 22:55 | U-5 Dimension Door globes + labels (tool, renderer), IndoorSceneYml log line, MP38 | running |
| FB F1+F7 | 1st | a1f4804df19252468 | 23:50 | houses list a person twice; empty guild/shop stock — all houses | done (~243k): F7 fixed (99 Xeen spellbooks 12901–12999; 29 guilds stocked; towns.py check + shop_stock.yml); F1 = engine spec for A1 (91 houses) |
| FB F4+F9 | 1st | a89b125bf27c293de | 23:50 | projectile spawn height; placed NPC bodies/names/unkillable — world-wide | done (~392k): F4 6 rows\' heights fixed + check_actor_heights.py; F9 71 figures protected (xeen_key_npcs.lua), Sablewing row 11927 gold dragon (X7 job queued on lock) |
| FB F13+F15+F16 | 1st | a2d7fdd994dfd0456 | 23:50 | shrines status-line, quest items as loot, standard dungeon entry dialog | done (~399k): F13 88 hooks status-line + check (41 map sites open), F15 6/7 chests, F16 = studio spec; D-90 decider on 5 questions |
| FB F2+F8 | 1st | ae724eb303cf77ad3 | 23:50 | building doors, cave mouths | stopped (~443k): F2 66/70 doors (X1 installed; D1/D3/D4/D6/X6 via finish.sh), F8 cause + 2 mouths; X7/X1/X2/X4/X5 mouths left; studio specs to A1 |
| FB F6+F3 | 1st | a52ac06f286ab3d3b | 23:50 | chests, props at edges | done (~422k): props_support check; X1/X2/X3/X5 + 28 indoor sites fixed; X7/X6 den chests queued; 90 outdoor chests need F6-R1 |
| FB F5+F11 | 1st | ad9db81770c45ada4 | 23:50 | ground decorations, terrain material seams | done (~319k): F11 NaN weights (X7, D6) + pool lines fixed, terrain check; F5 plants.yml + `terrain_materials.py plants` on 11 maps; D1, D4 (lock), XD-17 left |
| FB F12+F14 | 1st | a17f2b846b0a4e601 | 23:50 | black exits, door textures, door→outside, podium lore, drops with no way back | done: queue finished 23:59 — 32 dungeons rebuilt with black exits + 9 already; 13 refused (L4/Lua changed since last install); ~13 maps with failing playtests; 22 bakes pending |
| FB F10 | 1st | aab019e42dad9ea02 | 23:50 | empty outdoor areas | done (~314k): empty_zones.py (MM6–MM8 calibrated) ; X7, X3, D1 fixed + installed; 9 maps left |
| Design | gating+identity | ac30e22678b3cffd8 | 23:50 | F17 gating + F12 dungeon identity → reviews/DESIGN_GATING_AND_IDENTITY.md | done (~325k): DESIGN_GATING_AND_IDENTITY.md → D-89 |
| Art | loading filter | af62a085ec754463c | 00:00 | filter on Xeen loading screens (less AI look), comparison artifact | done: "combined" (paint pass, MM grade, 16-bit dither, grain) installed; originals in output/xeen_loading_filter/originals; artifact https://claude.ai/artifact/V8t8h9yoFiB8heVCobrguK |
| Size | distro estimate | a278e15aaf1f166a8 | 00:05 | Xeen world size in a release vs MM6–MM9 (read-only) | done: desktop +1,149 MiB (+12.4 %), Android ~+740 MiB; ship blockers listed |
| P | 1st | ab7171f2a53c926ea | 00:45 | U-7 size savings (dedupe, WAV, deco 1K, bakes 32 u/texel) + packaging blockers (packs.yml, Android cook, decoration_data) | done (~324k): dedupe ready (needs A1 fallback), ADPCM 77.8→18.9 MiB, 22 deco cook sidecars, packs.yml + Android cooks, bakes 32 u/texel (rebake queue running), CI desktop packaging + 16 release scenarios pass |
| Mirrors | switch | a1f84bc0e2f3dd04e | 01:00 | xmirror on the town mirrors (A5/A6/A8 maps), DD-03 yard/Queen's | running |
| A1 | 35th | a81dae83d16ef4956 | 01:30 | MP40: F1 proprietor, F16 entrance window (studio), carries:, cave metrics, shop_stock regression | done (~418k): MP40 released (F1, F16 studio + world trans rows, carries:, cave metrics, platform-top fit, black exit default) |
| A3 | 34th | a11bd99b5c7615ca5 | 01:40 | D-89 gating hooks + quests.py check; D-90 hook rules, 47 finds sorted; trans rows draft; tests | stopped (~513k): D-89 gating hooks + quests.py checks, D-90 hooks, trans.txt 65 rows; main fails 09, 15, 39, 41, 43, 57, 63; side 61/71 |
| A1 | 36th | a7e4d0abc0e9bef61 | 00:20 | MP41: outdoor chests, ground height, doors/caves studio, F9-R2, F4-R1, gates | done (~309k): MP41 released 00:55:24 (outdoor chests, ground heights, scatter, doors, cave forms, F9-R2 names, F4-R1, texture fallback) |
| A7 | 26th | afb13b53887eebcfe | 00:20 | dungeon follow-ups: refused maps, A3 requests, F16, playtests, XD-18 cave rebuild, XD-13 | done (~495k): 12 refused maps installed (MP40 rebuild differences only), A3 requests, F16 on 4 sites, XD-18 rebuilt as a real cave (20/20); FD-03, FD-04 tests left; XD-13 identity, drops, plank doors not started |
| A8 | 26th | a895f483f9acce56a | 00:20 | dungeon follow-ups: A3 requests, playtests, F16, heights, tops, drops, DD-09 | done (~469k): all 29 A8 maps clean on MP40 (audits 0, checks 0, tests 4/4); A3 requests, F16 on 8 sites, heights, 10 tops, door pictures, drops; DD-09 identity not started |
| A3 | 35th | a78f7a71587942108 | 00:20 | test step fixes (status lines, F1 lobby, D-89), then all three sets both modes | stopped (~443k): all known test steps fixed in files (status lines, F1, ~100 entrance OKs, finds); main 43/51 normal mid-rebuild; full reruns pending after outdoor rebuilds; fixer scripts in output/a3_s35/ |
| A5 | 29th | ad2041c9d0af032d0 | 01:05 | outdoor follow-ups on X7, X2, X1, X4, X6, X3, D3, XD-17, X9, P5 (one rebuild each) | done (~437k): X7, X2, X1, X4, X6, X3, D3, XD-17 rebuilt on MP41 with all pending items; X9, P5, F10 D3/X6, ground items, sundials left |
| A6 | 32nd | a0d98b5865e9ee52b | 01:05 | outdoor follow-ups on D1, X5, D6, D2, D4, D5, D7, P1–P4, X8 | done (~424k): D1, X5, D6, D2, D4, D5 (bakes), D7, P1–P4 rebuilt; F16, D-91 blast door, Soul Box gate, empty zones, druid; P1–P4 18 audit errors (studio plate tops) |
| S | 15th | a449976b0083298d9 | 01:05 | robed old man's row for the Winter/Spring Druids | done (~119k): row 11928 Xeen Elder Druid on xeen_sor1 skin xsor_i; A5/A6 told |
| A7 | 27th | af641c84fe3f82f19 | 02:00 | FD-03/FD-04 tests, XD-13 identity, drop pockets, plank doors, chest.front | done (~471k): FD-03/FD-04 tests, XD-13 + FD-03 identity, check_drops.py fixed (14→6 pockets, by design), chest fronts, door pictures on 4 maps |
| A8 | 27th | ac6c0300ebf5185c2 | 02:00 | DD-09 and DD-14 identity rebuilds, check_drops stair fix | done (~335k): DD-09 (round trunk hall, roots, open crown) and DD-14 (grey castle, ribs, stone coffins) identity rebuilds 12/12; DD-05/DD-20 bits, Cult Leader moved |
| A1 | 37th | a67b5bcafe4c87a3d | 02:30 | MP42: verify outdoor 19-face chests, outdoor ground-item kind, indoor chest default, q-d9, tools, x6 test | done (~331k): MP42 oymap-only 01:57:08 (outdoor ground items, indoor default chest by style world, fitted undersides, props rules in audit, x6 test); chests already fine; q-d9 and XD-26 not engine faults |
| S | 16th | a4772625333b048d1 | 02:30 | friendly "Xeen Druidess" row for the Autumn/Summer Druids | done (~87k): row 11929 Xeen Druidess (friendly, Druidess A body) |
| A5 | 30th | a6da6e5672a9b8410 | 02:40 | X4/X6 druids on 11929 + X6 F10, X9 F16, D3 F10, P5, X3 sundials; MP42 ground items + shelter captures | done (~340k): druids on 11929, X6/D3 zones, X9 F16 + nests buttons, X3 buttons, P5 window, ground items X1/X2/X7, shelter captures |
| A8 | 28th | aa4c41cf085bb39b1 | 03:00 | D-89 identity rebuilds: DD-12, DD-10A–C, DD-25, DD-20, XD-10, XD-11, XD-09, DD-02, DD-04, DD-19 | done (~439k): identity DD-12, DD-10A–C, DD-25, DD-20, XD-10, DD-04 (7 of 11); DD-04 playtest step 60 open |
| A7 | 28th | ae46380351e20074e | 03:20 | XD-15 slabs, XD-01 culvert, FD-04 warning; D-89 cave set XD-05, XD-16, XD-23, XD-26, DD-11A–C, DD-23 | stopped (~312k): `tools/xeen/cave_shape.py`; 7 cave maps pass the cave-shape audit; q5/q6 queues still rebuilding/testing; XD-23, captures, NOTES left |
| A6 | 33rd | ab82deb29104b63cc | 03:30 | P1–P4 vent tops (18 audit errors), X5 holy book ground item | done (~160k): P1–P4 audits 0/0, X5 holy book ground item, X5 wolves moved (P5 falls 2/2) |
| A8 | 29th | aefd4eeeb6ce999d0 | 04:00 | identity XD-11, XD-09, DD-02, DD-19; MP42 rebuilds of the rest; DD-04 step 60 | done (~305k): identity XD-11 (octagon tower), XD-09, DD-02, DD-19; MP42 rebuilds; DD-04 step; XD-10 family fixed; EXCEPTIONS in check_identity |
| A7 | 29th | aebfe5e87c023bcb5 | 04:00 | verify q5/q6, XD-23 cave pass, name-test captures, MP42 rebuilds | done (~262k): cave set all pass (XD-05, XD-16, XD-26, DD-11A–C, DD-23), XD-23 in d13, check_identity.py, name-test sheet, MP42 rebuilds |
| A5 | 31st | a2ab4c28a8b581fa7 | 04:30 | X7 den chest question dropped; scan other chests with questions | done (~122k): X7 den chest opens at once + status line; installed with bake; no other A5 chest questions |
| Fix-ups | final | af59e968a18877dbc | 05:00 | DD-11B quests.py error, XD-12 lava way out, DD-17 statue, D4 boat locker; all checks | done (~212k): DD-11A/B/C lost map_code (comment swallowed it) fixed + quests.py check; XD-12 lava ladders + check_drops fix; DD-17 statue; D4 locker; all checks 0 |
| A3 | 36th | ab3087e499adb633f | 05:30 | FINAL: quest map_gives/bits, fixers, main + promotions + side quests both modes until green | running |
| P | 2nd | ac22ec3608246a7a8 | 05:30 | FINAL: share textures on, Android cook/packaging, CI steps locally (with and without Xeen) | done (~245k): CI steps PASS locally without and with Xeen; share textures on (no CONTENT_FORMAT bump — would block 2.x updaters); sizes |
| G | 7th | abfb288812845398b | 05:30 | FINAL: Xeen guide for tonight's changes, recaptures, deploy | done (~286k): guide matches tonight\'s world (finds as map points, 109 walkthroughs, 82 arrival shots), deployed; MM9 guide.js byte-identical |

## Deciders

| D | Question | Agent id | State |
| --- | --- | --- | --- |
| D-91 | druid bodies vs portraits, dead-end caves, D6 blast door | a8f5719225c53818d | answered (`reviews/D91_DECISION.md`) |
| D-90 | dialogs vs loot | a03c1d71f7438700b | answered (`reviews/D90_DECISION.md`) |
| D-88 | X2 XD-06 exit: Killer Sprites and dark-end markers | a8f325e39a9e03ed5 | answered: keep the placed guards, move markers 17/20/21/22 (`reviews/D88_DECISION.md`) |
| D-87 | givers in fights (Randon, Graalg), edge-arrival leeway, Arie | a90ab8cebcff39fa0 | answered: keep both givers (Randon undamageable), ranged-disabler rule for all outdoor arrivals (`reviews/D87_DECISION.md`) |
| D-86 | MX session 2's five choices | a7207ce3e412514fc | answered: all confirmed, records only (`reviews/D86_DECISION.md`) |
| D-85 | X2 Danulf ring: sprites curse/stone the party | a46cbc08dc325cb4f | answered: move six markers ≥5,888; same rule for all outdoor givers (`reviews/D85_DECISION.md`) |
| D-84 | MAW in Xeen MX-1,3,4,6,7,8 | ae22ed4194fb60897 | answered (`reviews/D84_DECISION.md`) |
| D-83 | X6 Sphinx door two clicks vs line in XD-15 | a31339f4b75df46b7 | answered: keep two clicks (`reviews/D83_DECISION.md`) |

## MP40 queue — DONE in MP40 except the MP41 list below

### MP43 queue
- oymap hangs `wall:` decorations on the plan wall, so a rough (cave-pass) wall can swallow a wall torch (`lights.in_solid`, XD-05 back gate): hang them on the rough face. Optional: `check_identity.py` family share into the audit.

### MP42 queue
- q-d9: the Temple of Bark's arrival message never shows on the first arrival (the arrival event runs during the map move, no window); repro `output/a3_s35/probe/q-d9_probe.yml`.
- `tools/xeen/check_drops.py`: a stair whose steps stand on a room's continuous floor shares no edge with it → whole lower floors read as pockets (DD-14, DD-19, DD-21, XD-09); treat a step edge inside another floor as touching it (tool fix; any lane).
- Indoor default chest kind follows the style world (Xeen → 7gt002), not the project world (MM6 ch1).
- F6-R4 props checks into `oymap audit`; check_exits/check_drops into the audit; indoor `doors.part_picture` on the shut door; fallen timbers for `form: blocked`; shelter capture check.
- `tools/xeen/check_actor_heights.py` misses `engine/rendering/sprite_frame_data_common.yml` (fixed copy `output/xeen_a1/mp41/a/check_heights_fixed.py`) — tool owner (F4/A2).

### MP41 queue (done in MP41)
- F6-R1 shipped 19-face chest outdoors (indoor chest-kind code shared; default by style world: 7gt002 Xeen, gt002 MM8, ch1 MM6) → all 13 ODMs rebuilt after; F6-R2 terrain height by the game's triangle split for decorations/actors/spawns/chests (chests at the lowest corner); F6-R3 scatter refuses > 48 height spread under a decoration; F6-R4 props checks into `oymap audit`; F6-R5 README: indoor chest `facing` = long axis + `chest.front` rule. Specs: USER_FEEDBACK Results F6/F3.
- F9-R2 (actor named by its NPC; needs NPC table plumbing into the world runtimes); F4-R1 (launch height min(collision, model top)); then `key_npcs.py`, `check_actor_heights.py` into regressions.sh.
- F2/F8 studio items 1–4 (double doors from half pictures, leaves at picture width, sunk cave mouths, door_check rules into `oymap audit`); maybe check_exits/check_drops into the audit.
- X6 War Zone gate question dropped → `x6_warzone_entrance.yml` into regressions.

### MP40 items (history)

- F1 (from FB F1+F7): `game/events/EventDialogContent.cpp` house lobby / `collectSelectableResidentNpcIds`: a resident
  whose portrait equals the house's non-zero `proprietorPictureId` is the proprietor (no second portrait); sole resident
  → straight to his menu (services + his topics, as that NPC with the house as host). MM6–MM8 0 matches; confirm MM9
  vendor houses. Test `output/xeen_fb/F1_F7/house_proprietor_once.yml` → tests/scenarios/xeen/ + a unit test; then
  `PROPRIETOR_TWIN_MERGED = True` in tools/xeen/towns.py, rerun `towns.py --stock-scenario`. Spec in
  reviews/USER_FEEDBACK_20261121.md (F1/F7 Results).
- Add `tests/scenarios/xeen/shop_stock.yml` to tools/xeen/regressions.sh.
- F16 (from FB F13+F15+F16): studio: outdoor `into:` a .blv writes house 0, picture 1 by default (OutdoorBuildings.cpp
  ~2263–2281, OutdoorThings.cpp ~872–889; drop `house ≥ 1` on `screen`; `screen: none` for direct moves); indoor `exit`
  toward a BLV neighbour defaults to picture 1 (IndoorLowering.cpp ~17017–17125; `leave` stays direct); audit warns on a
  BLV entrance `0, 0` without `screen: none`, errors on a Yes/No question before a move into a BLV. Tests: studio unit
  case; Xeen scenario on X6's War Zone gate. Then every Xeen map Lua-only rebuild, lanes drop 44 Yes/No prompts, test
  steps `answer_input: Yes` → `select_topic: {match_label: "OK"}` (D-24/D-72 superseded). Optional: world `trans.txt`
  contributions (per D-90). Gap: outdoor sketch actors have no `carries:` word (OutdoorBuild.cpp ~769).
- D-89 (identity §): cave-shape numbers in `oymap metrics` + an audit warning for cave/mine maps (targets from shipped MM6–MM8 caves) — studio, with A6.

## Log

- 17:05 Read the handoff, ORCHESTRATOR_SESSION3, lane States. Wave 1: D-83 decider, A1 32nd, A2 22nd, A3 32nd, A6 29th,
  A7 25th, A8 24th, S 14th. Wave 2 after D-83: A3-side 3rd, G 5th; A3-promo 6th after A3 32nd rewrites the
  checkpoints; AU and A5 small items later.
- 17:15 D-83 answered (keep A5's two-click door); recorded in DECISIONS.md and `reviews/D83_DECISION.md`. A3-side 3rd and
  G 5th started with it. Waiting: A3-promo 6th after A3 32nd's checkpoints; AU (AUDIO.md paste list) and A5 (D-72 at
  next rebuilds) not started — nothing urgent.
- S 14th done: heart jar (DD-21) and P2 basket installed, seen in game, 0 refused, 0 stale, no credits. Relayed G
  (optional recapture).
- A2 22nd done: monsters.yml records match S's bindings; D-81 in balance.py (Q-C25 +1 with one wish, --gates 0); E14
  names were already installed (A7 told to drop its item 4). Open note: A2 lists S's `Xeen Octopod E` binding as open
  although S 9th bound it — check at S's next session.
- G 5th done: four portraits, XD-05 drums clause, Q-C9 (D-83, exact game line), Q-C22 hint, tighter dragons;
  republished. For the user (MM9 guide owner): `tools/mm9_site/build_site.py`'s full build stops on missing map images
  (`load_presentations` opens `worlds/mm9/ui/maps/<map>.pcx`, now `.png` since 2026-11-09); `--skip-images` works.
- A7 25th done: XD-19 bake profile (direct 1.2/bounce 3/max 1.0) — ceilings mid grey; XD-19's cinematics file had never
  been installed (mirror cinematic never played) — installed, audit 0/0, 4/4; all 31 A7 maps pass on MP35 after
  XD-13/XD-22 test fixes. stale_bakes: XD-12, XD-21 (A8's) — A8 24th told. Cinematics files in assets_dev: DD-17, P5, XD-19.
- A6 29th done: D7 Olympus classical dressing installed 17:16 (D-8 kept; north gate's inner columns dropped, lintel on
  the temple/guild walls), P1 battered walls + vent 17:23; audits 0/0; 2.2 GB freed. Optional next: D7 Mirror of
  Olympus reads as a plain brown slab (gilt frame, picture once); P1 NOTES' placeholder-elementals line.
- A8 24th done: DD-14 step 115 fixed in the test (clear at the hall's mouth); all 29 A8 maps pass on MP35 (test fixes
  DD-05/12/15/21 storey clears, XD-06 chest window close); step-top rooms DD-05, DD-15, XD-06, XD-09, XD-12, XD-21
  reinstalled 17:15 + baked, 4/4; 0 stale. Relayed A1: loot_chest window stays open (XD-06). DD-12 cage recess dropped
  (needs studio panel recess). Next polish: DD-10C frost floor bakes near white; DD-03/DD-09 texture warnings listed.
- A1 32nd done: merge point 36 released 17:48:12 (shared behaviour change: a key that closes a window needs a fresh
  press to act in play; loot_chest closes message + chest; app 29/29). MM9 main chain on MP35: 41/43, no PARTY DOWN;
  55_dark_passageway step 73 (storey-bound clear misses the sea monster below) and 61_tomb step 77 (walk blocked by
  actors 85/78, no clear) fail — for the user. A3 32nd and A3-side 3rd told about MP36 (their runs may straddle it).
  Two A1 builds were spoiled by peer sessions' header edits (IndoorWorldRuntime.h, OutdoorWorldRuntime.h, CoopSession.h).
- **User ~17:55: "work on MAW scaling for the world of xeen now, including the conjoined promotions for the classes
  (check what MM9 does for the classes), document it in the MAW html page and refresh it on the server."** New lane MX
  (MAW in Xeen) started 18:00 on MM9's model (devdocs/maw/MM9_SUPPORT.md, MM9_BALANCE_DESIGN.md §9, MAW
  `data/promotions.yml`); it may build game merge point 37 while A1 is idle; guide `tools/maw_site/` → deploy.sh
  (https://jasicek.net/openyamm/maw-guide/). Its DECIDE items go to deciders; MAW-wide changes (Supreme's world count,
  promotion-factor cap, save format) are reported, not built for MM6–MM9.
- A3 32nd done: main chain 01–99 green normal (512 s) and --reload (2,012 s) on MP36 with D-82's check; temple cures
  added (Mok, Desert Sun, Pray N Pay); checkpoints rewritten 17:53–18:27. Causes: D2 Gorgons/Medusa at edge arrivals,
  XD-12's gate-hall Floating Eyes (paralyse within 1.5 s of arrival), Temple of Yak. A3-promo 6th and A8 25th (XD-12
  eyes, DD-10C) started 18:35.
- A8 25th done: XD-12's Well eye group moved out of the arrival's line (quiet arrival test added), DD-10C frost floor
  toned by profile, DD-03/09 warnings already listed. Queued for A3 (after A3-promo 6th finishes, so the checkpoints it
  reads don't change under it): rerun segments 37 and 79–85 on the new XD-12 (the Pray N Pay heal may then go);
  checkpoint 35 loads with members 1 and 3 DiseaseMedium (before XD-12). Optional for A6: a greyer frost texture.
- MX 1st done: MAW plays Xeen (design `devdocs/maw/XEEN_SUPPORT.md`, `rulesets/maw/worlds/xeen/balance.yml` 82 maps,
  `tools/maw/xeen_balance.py`, promotions.yml xeen bits + mids, fifth bank shared by continents 6/7, save version 200,
  Supreme any 4 of 5); merge point 37 built and released by MX (18:35:58); MAW guide with a Xeen page deployed 18:41.
  A3-promo and A3-side told of MP37. STATUS Engine + ROADMAP §3 (lane MX) updated. D-84 decider on MX-1,3,4,6,7,8;
  MX-2 (save version 200) and MX-5 (Supreme any 4 of 5) change MAW for MM6–MM9 players → the user.
- User ~19:00: "horizontal progression there also implemented? also for beyond madness?" — answered: levels yes; missing
  the Vertigo continent teleporter and dungeon density. D-84 answered (bank one; D–G as is; pack reserve; gem tiers
  4/5/5/6; Seers Burlock/Castleview, town-hall bounties; band rule fix, X7 natives). Orchestrator moved MX-4's
  reserves from phase 7 to now (all maps installed). MX 2nd started 19:10. Open for the user: MX-2 (save version 200),
  MX-5 (Supreme any 4 of 5) — decider recommends accepting both.
- User ~19:15: accepted MX-2 (save version 200) and MX-5 (Supreme any 4 of 5) → U-4 in DECISIONS.md; MX told.
- A3-promo 6th done: promotions 41/41 on MP37 normal (×3) and --reload with D-82 checks before hand-ins and class
  tables; fixes: 03 clear at Danulf's ring, 11 Chapel of the Crown heal, 55 D2 west-edge clear, 85 Mok heal, 89
  Necropolis heal. D-85 decider on Danulf's ring (Dark Sprites from 3,000–9,000 curse/stone the party in seconds).
  A3's rerun of 37 and 79–85 on the new XD-12 waits until MX 2nd reports (it may release MP38; batch the reruns).
- D-85 answered (move X2's six sprite markers to ≥5,888 from Danulf; the rule for every outdoor giver). A5 26th and
  A6 30th started 19:45. Rerun batch after A5/A6/MX: A3 (17, 37, 79–85, + A5/A6's list), A3-promo (03 + list), A3-side
  (q-c17 + list), A2 confirm balance on X2.
- A3-side 3rd done: 71 side-quest scenarios pass on MP37 both modes (new Q-D10 mercenary; Q-C22 cottage line now a
  status line; D-82 end lines + can-act asserts; fixes Q-F2, Q-C9, Q-D16 war, temple heals). No relay needed (G's
  Q-C22 text already matches).
- MX 2nd done: balance.yml v2 (34 bands; MM6–MM9 rows identical), gem rungs, `tools/maw/pack_reserve.py` (MM9's 28
  reserves byte-identical) + `xeen_pack_reserve.py`: 48 Xeen dungeon reserves (39 reach x2.0 at Beyond Madness;
  15 spawn-point dungeons grow by group size); Vertigo MAW pedestal (overlay, event 1777); Seers Zephyra (X4 4312)
  and Madame Oorla (D1 4921); town-hall bounties tested; guide redeployed. No engine change. Rule for map lanes: rerun
  `tools/maw/xeen_pack_reserve.py <stem>` + `xeen_balance.py --check` after rebuilding an indoor map (added to lanes
  README). For A1 next build: IndoorSceneYml.cpp stale-reserve log line names mm9_pack_reserve.py. D-86 decider on
  MX's five small DECIDE items.
- D-86 answered: all five MX choices confirmed; pending for MX's next session: XEEN_SUPPORT wording (tiers vs rungs, FD-01 story map, FD-04 105), tester check for hidden groups after a refill.
- A5 26th done: D-85 on X2 (installed 19:19) and on X1 (Derek, Celia, Orothin), X4 (Joe; knight pair moved to the
  Rivercity road past the landing fork), X6 (Saul), D3 (Cornelius); warnings X6 Arie 5,258/5,621 (kept); new
  `x2/tools/check_d85.py` in X2's pipeline. Rerun batch (after A6): A3 full chain both modes, A3-promo full (03 clear
  9,000→3,000 if 3/3), A3-side full, A2 balance confirm (X1, X2, X4, X6, D3 + A6's), G inline maps check.
- A6 30th done: D-85 moves on X5 (Winter Druid), D1 (Joe, Justine), D2 (edge arrivals from D1/D3 now ≥6,001), D6
  (Ambrose) installed with bakes 19:30–19:36; D7 mirror gilt-framed (19:30) and its MAW reserve rerun; P1's elementals
  are real (NOTES fixed). D-87 decider on Randon (X5), Graalg (D2), edge leeway, Arie (X6). Reruns wait for D-87.
- D-87 recorded; A5 27th and A6 31st started 20:30. The full rerun batch (A3, A3-promo, A3-side, A2, G) follows their reports.
- A5 27th done: D-87 checker (ranged-disabler filter, every arrival kind) in all 8 A5 build scripts; only X2's XD-06 exit breaches (temple sprites + markers 17/20/21/22) → D-88. Nothing rebuilt.
- D-88 answered (keep the temple guards, move the four dark-end markers); A5 28th started 21:10. Rerun batch after A5 28th and A6 31st.
- A6 31st done: D-87 applied (Randon flag + test, Graalg parley test, D6 eyes moved off the DD-22 hatch; X5 and D6 reinstalled with bakes). Rerun batch waits only for A5 28th (X2).
- A5 28th done (D-88 on X2, 20:05). Rerun batch started 21:25: A3 33rd (full chain), A3-side 4th (all side quests), A2+G combined check. A3-promo 7th after A3 33rd's checkpoints.
- A2+G done: balance unchanged on every rebuilt map; guide republished (Rescue Celia step, D7 one mirror pin, D7/P1 arrival shots). quest_levels tie-break swapped m27/q-d15 again (shared front end; MM9 owner item).
- A3-side 4th done: 71/71 both modes after the D-85/87/88 rebuilds, nothing needed changing.
- A3 33rd done: main chain 52/52 both modes on the rebuilt maps (71 fights DD-16's eyes before the door); D-85/87/88 removed the causes at 17, 23, 37 and D2; 79 (XD-12 upper eyes) keeps its cure; checkpoint 35 Disease from XD-08 Grave Ghouls (27). A3-promo 7th started 22:15.
- A3-promo 7th done: promotions 41/41 normal (×2) and --reload on A3 33rd's checkpoints; 21 fixed (XD-22 hall fought
  from the stair); D-85: 03's clear lowered to 3,000. **All three test sets green on MP37 after every rebuild of this
  session** (main 52/52, promotions 41/41, side quests 71/71, both modes). D85_DECISION's probe path updated.
- User ~22:45: pedestal / Town Portal / Dimension Door for Xeen; reuse the new-game globes and labels on the Dimension Door screen? Town Portal has Cloudside/Darkside buttons; the Dimension Door has a 5-portal screen (tpglobal5); the Vertigo pedestal was MAW-only → session started to make it the world's own (every ruleset). Globe/label redesign asked of the user.
- User chose "globes + labels" for the Dimension Door screen → U-5; A1 33rd started 22:55 (MP38).
- User ~23:05 (screenshot of Vertigo's Magic Mirror: streaky water membrane): "any chance for this to actually reflect?"
  The town mirrors (`kind: portal`, membrane `wtrtyl` liquid water flowing down: thing:mirror X1, burlock, newcastle,
  nightshadow, asp, cv D1, sc D3, lk, np D6, reflectors) don't reflect. Queued for A1 34th after U-5/MP38: a `mirror`
  liquid/surface kind with a planar reflection about the face's own (vertical) plane, reusing WaterRenderer's
  reflections (occlusion-gated, cost only when visible), a faint magic sheen; map lanes (A5 X1/X2/X3/X4/X6/D3,
  A6 D1/D6/X5…) switch their mirror membranes; captures before/after.
- Vertigo pedestal done (world overlay `worlds/xeen/maps/xeen_x1_dimensional_travel.scene.yml` + `events/maps/xeen_x1_dimensional_travel.lua`, every ruleset; MAW copy removed; MAW guide wording redeployed; scenario `xeen/dimensional_travel_vertigo.yml`).
- A1 33rd done: merge point 38 released 22:17:50 (U-5 Dimension Door globes + labels; `tools/ui/dimension_door_globes.py`; names under portals; IndoorSceneYml log line). New unit failure = RulesetTests reading MAW's `world: xeen` entry as an engine path (test bug; the patch applies in game). A1 34th started 23:25: test fix + mirror reflections (`kind: mirror`), MP39.
- **User ~23:40: a big play-feedback batch (15 screenshots), "solve GENERICALLY ... STRUCTURALLY on all similar sites".**
  Recorded with families F1–F18 in `reviews/USER_FEEDBACK_20261121.md` (images `output/xeen_o4/feedback_20261121/`);
  shared rules for the fix agents `briefs/FEEDBACK_FIX_RULES.md` (per-map locks `output/xeen_locks/<stem>.lock`, one bake
  at a time `bake.lock`, engine changes as specs to A1 for merge point 40). Eight family agents + a design session
  (F17 gating, F12 dungeon identity) started 23:50. A1 34th (mirrors, MP39) still running.
- User ~00:00: a filter on the Xeen loading screens so they don't look 100 % AI-made → art session started.
- User ~00:05: how much disk space Xeen adds to the distribution → read-only size estimate session started.
- Loading filter done: `tools/ui/loading_screen_filter.py`, variant "combined" installed on the four Xeen loading pages; comparison artifact https://claude.ai/artifact/V8t8h9yoFiB8heVCobrguK; rollback copies in output/xeen_loading_filter/originals/.
- Size estimate done: Xeen adds ~1.15 GiB desktop / ~0.75 GiB Android (+12–14 % on 2.8). Drivers: model textures 602
  MiB (303 MiB are byte copies of MM6–MM9 textures from stand-in creatures), bakes 213 MiB, surface textures 97, GLBs 84,
  WAVs 79. **Ship blockers (for a release lane later):** Xeen missing from `tools/packaging/packs.yml` (needs an MM9-like
  entry: audio domain, ~18–20 model buckets); no Android cook `assets_cooked/android/worlds/xeen`; `models/decoration_data.txt`
  not shipped by the packager (move to data_tables/ or allow); leftovers `.build_world.lock`, `maps/*.studio.yml`.
  Savings ideas: shared hashed texture store (~303 MiB), indoor bakes at 32 u/texel (~60 MiB), sounds 22 kHz/ADPCM
  (40–65 MiB), 25 decorations 2K→1K (~95 MiB), PNG→JPEG for map/loading images (~20 MiB).
- FB F1+F7 done: Xeen guilds were empty because no book was flagged for Xeen → 99 Xeen spellbook copies (MM8 400–498 → 12901–12999), all 29 guilds stocked, checks added; books also drop as loot at MM8 rates (orchestrator: accepted, MM6–MM8/MM9 precedent). F1 duplicate proprietors need the engine (MP40 queue).
- User ~00:30: the "combined" loading-screen filter is fine → U-6.
- User ~00:40: approved the size savings (U-7). New lane P started 00:45 (dedupe vs engine/dependencies, compact WAV, decoration 1K, packaging blockers, indoor bakes at 32 u/texel last under the locks).
- Design session done → D-89 adopted (the design session the user asked for; no further decider). Implementation waits
  for the running agents that touch the same files: gating edits (A3 hooks, gen_quests, test segments) after FB
  F13+F15+F16 finishes; XD-18 and the other identity rebuilds after FB F12+F14 finishes (both edit the same hooks/maps).
- A1 34th done: merge point 39 released 22:46:36 (mirrors reflect about their own plane, `kind: mirror`, `xmirror`;
  MAW world-entry unit test fixed). **Caution for the user:** `assets_dev/engine/liquids/liquids.yml` now has a `mirror`
  kind; a game built from older sources (e.g. `build/game/openyamm`, the user's and the peer session's) rejects the whole
  liquids file and draws no water/tar/lava until rebuilt from current sources. Mirror switch session started 01:00.
- FB F13+F15+F16 done (88 touch hooks → status line, 6 quest chests real chest items; 41 map-own F13 sites for A5/A7/A8; X2 strongbox for A5; F16 studio spec queued). D-90 decider on its five questions.
- A1 35th started 01:30 on the MP40 queue (later specs from F4/F9, F2/F8, F6/F3, F12/F14 relayed by message).
- D-90 answered: no window on finds/XP touches/deaths (status-line finds, containers → chests, bare items → 3D ground items; `window:` reason only); entrance lines kept via a world trans.txt contribution inside the standard window (A1 with F16); quest item conditions read HasEverOwnedItem (`found:`). A1 35th told; A3 34th (D-89 gating + D-90 hooks) starting.
- FB F2+F8 stopped at its budget: half-door pictures hung alone → `tools/xeen/house_doors.py` + `door_check.py`; X1
  installed 22:58; D1, D3, D4, D6, X6 installing via `output/xeen_fb/f2/finish.sh` (log `run/finish.log`, ends FINISHED).
  Cave wings = shell as wide as the footprint; dead-end mouths got a click line. Left: X7's 6 mouths (prepared
  `output/xeen_fb/x7s/tools/gen.py`), X1×2, X2, X4, X5×2. Studio specs relayed to A1 35th (MP40). Open DECIDE: dead-end
  caves get small interiors?; D6's split blast door acceptable? → next decider batch. A continuation session after
  finish.sh and MP40.
- FB F12+F14 stopped at context: exits → `7solid01` at the source on 57 maps (78 faces; SPECIAL list kept), rebuilt by
  its background `output/xeen_fb/f12_f14/tools/queue.sh` + `bake_worker.sh` (+ follow-up job); new checks
  `check_exits.py`, `check_drops.py` (added to lanes/README "Map checks"); Robbers' Den/Dragon Cave ladders; 2 book tops.
  Left: 18 stand tops (A1 `fit` on platform tops, relayed), drop pockets list (liquid channels, pits), DD-11A/DD-13
  L4s that don't build to the installed BLV (someone's uninstalled change), XD-05 L4 `exit:x7`. Orchestrator decision on
  its DECIDE: leaves titled "Door" drawn as plank strips/stone slabs get a door picture from their map's family (the
  user flagged door textures); secret walls/cages/webs/boulders stay. The user's Dragon Cave door (1917, -3321) is the
  tax office's house door with the dungeon's double-door picture — check with a capture in the continuation.
- FB F4+F9 done: missile launch heights (6 Xeen rows; MM6 ElemAir has the same engine fault → F4-R1 spec to A1),
  `tools/xeen/key_npcs.py` → `events/common/xeen_key_npcs.lua` protects all 71 placed talking figures (story-hostile ones
  excepted), Sablewing gets row 11927 and a gold-dragon body (X7 job `output/xeen_fb/F9/x7_job.sh` waits on the X7 lock,
  held by a running agent's `sleep 7200` reservation); "Peasant" names need F9-R2 (A1). Map lanes: run
  `key_npcs.py --write` after any install; rebuild dd01, dd02, p2 for heights. D-91 decider (druids, dead-end caves,
  D6 blast door).
- FB F5+F11 done: seams were NaN weights from two materials with the same reference colour (X7 443k, D6 975k texels) +
  straight sand lines under small water faces → `tools/terrain_materials.py` fixed + `check`; Xeen had no
  `terrain_decorations/` → `worlds/xeen/terrain_decorations/plants.yml` + `terrain_materials.py plants` (every `weights`
  run writes them; terrain_swap.sh swaps them) on 11 maps. Left: D1, D4 (run terrain_swap after F2's finish.sh releases
  them), XD-17 rebuild (F12's queue). X5 tundra stays bare (orchestrator: fine).
- D-91 answered: portraits win (Autumn → Druidess A, Winter → robed old man's row; Summer/Spring follow; pronouns);
  dead-end mouths become lit shelters (Sablewing's cave, orc den) or blocked (adit, werewolves' den), `caves.blind_mouth`
  an error, "no way on" line withdrawn; D6's gate shows a whole `swdoora` per leaf, split exemption removed.

## Final steps the user asked for (2026-11-22 ~02:30), after every fix lands and the scenarios pass

1. All three test sets green (main, promotions, side quests; normal and --reload) on the final binary; stale_bakes 0;
   build_world --check 0; xeen_balance --check; key_npcs / check_actor_heights / check_exits / check_drops / door_check.
2. Update the Xeen guide (lane G: recapture changed maps/monsters, texts for D-89 gating, D-90 finds, F16 entrances;
   deploy) — and the MAW guide if MAW-relevant data changed.
3. Cook all textures for Android too (Xeen and anything changed tonight: engine Dimension Door pictures, mirrors,
   loading screens, decorations at 1K) — lane P's Android cook.
4. Check packaging end to end for the next release as CI runs it (packaging/RELEASE.md, the GitHub Actions workflow,
   packs.yml with Xeen, desktop + Android packs locally, the updater's checks, unit tests CI runs, release scenario list
   `tests/scenarios/release/scenarios.txt`), so a `vX.Y` tag would succeed — without tagging, pushing or publishing.

## Pending map application (after the running agents release their maps)

Sources: A3 34th's per-lane list `output/a3_s34/REQUESTS.md` (D-89 doors, D-90 chests/ground items/status lines, map
faults), the F-family Results in `reviews/USER_FEEDBACK_20261121.md`, A1 MP40's F16 list (every map Lua-only rebuild;
60 Yes/No prompts to drop: A3's draft `drafts/XEEN_TRANS_ROWS_DRAFT.md` lists them; `screen: {text: <id>}` for a
door with a trans row), D-91. world.yml has the trans contribution since 00:15 (validated).

- A5 maps: X7 (F8 six mouths prepared in `output/xeen_fb/x7s/tools/gen.py`; F9 Sablewing job; D-91 shelters/blocked),
  X1 (F8 two mouths; Spring Druid body), X2 (F8 mouth; D-89 Yak door; F15/D-90 strongbox), X4 (F8 mouth; Autumn Druid
  body, pronouns; F13 map sites), X6 (D-91 werewolves' den blocked; Summer Druid body), XD-17 (rebuild for plants),
  D3/D1/D4/D6/X6 via F2's finish.sh (check `output/xeen_fb/f2/run/finish.log`).
- A6 maps: X5 (F8 two mouths; Winter Druid body; pronouns), D6 (D-91 blast door), D1 + D4 terrain_swap (F5/F11).
- A7/A8 dungeons: F13 map-own sites (DD-02, DD-03, DD-09, DD-12, XD-06, XD-11, XD-12, XD-07, XD-08, XD-13), D-90
  chests/ground items (A3 34th's list), D-89 inner gates and identity rebuilds (XD-18 first, then XD-13, DD-09, FD-03,
  DD-14), F14 drop pockets, door pictures for plank/slab leaves, DD-11A/DD-13 uninstalled L4 changes, XD-05 `exit:x7`,
  heights rebuild dd01/dd02/p2, 18 stand tops after A1's `fit`.
- F10 empty zones left (`tools/xeen/empty_zones.py --check`, add to each build script): D5, X5, D6, D2, X6, D4 (A6); D3, X2, X1 (A5; X1 move-only, Act I 1.147). Walk updates: X7, X3 (A5), D1 steps 121/189 (A6). D1 `entrance.question` events 117/121 (F16).
- After MP40: every map Lua-only rebuild for F16 (entrance window + trans rows), 44 Yes/No prompts dropped, test steps.
- F12/F14 queue update (~23:45 by its clock): DD-10A/B/C, DD-11B/C, DD-12, DD-15, DD-16 installed 4/4; DD-17 `playtest`
  0/4 and DD-19/DD-20 `playtest` 3/4 (not yet traced; may be other families' concurrent changes); DD-11A, DD-13, DD-23
  refused (L4 ≠ installed: uninstalled changes — find whose); DD-22 unchanged though listed; DD-02 needs a manual
  `tools/bake_one.sh dd02` after the queue. For the dungeon continuation session.
- F12/F14 queue update: DD-21 12/20 and DD-24 12/20 too (`playtest` 0/4; DD-21 `playtest_heart_first`, DD-24
  `playtest_friends`); DD-22, FD-01, FD-02, FD-03 already had the black exit installed (another session rebuilt them).
  Logs `output/xeen_fb/f12_f14/run/<key>/tests/`. Triage after the queue + A3 34th (hooks moving) finish.
- **A1 35th: merge point 40 released (game + oymap):** F1 proprietor once (91 houses; MM6–MM9 0 pairs), F16 standard
  entrance window from the studio (`screen: none` for direct; audit `entrance.question` error, `entrance.no_window`
  warning), world `trans.txt` rows (ids 5001–5999; world.yml lines added by the orchestrator once A3 writes
  `data_tables/english/trans.txt`), `carries:` for outdoor actors, `oymap metrics cave_shape` + `identity:` field,
  platform-top `fit`, black exit default; regressions 38 pass (Hesper stale), studio 498/498. Consequences: ~34 Xeen
  test files step through the old lobby (A3 34th told); every Xeen map needs a Lua-only rebuild for F16; 59 Yes/No
  handlers on 26 maps are now audit errors until dropped.
- FB F10 done: one big empty stretch per Xeen map vs MM6–MM8 (median 738 vs 228 tiles) → `empty_zones.py` + allow-list; X7 (orcs spread, same XP; Act I 1.1468), X3, D1 fixed. Orchestrator on its DECIDE: limits stay at the MM6–MM8 median/p75; formerly "quiet by design" areas stay sparsely populated (the user asked for it).
- FB F12+F14 queue finished: black exits on 32 rebuilt + 9 already installed; refused 13 (DD-11A, DD-13, DD-23, XD-04,
  XD-14, XD-16, XD-17, XD-19, XD-20, XD-22, XD-23, XD-25, XD-26 — someone's uninstalled L4/Lua change; likely tonight's
  hook work) → rerun `output/xeen_fb/f12_f14/tools/cycle.sh <key>` after their owners install; playtest failures on
  DD-05/06/07 (traced: F13 hook changes), DD-17, DD-21, DD-24, XD-01, XD-09, XD-11, XD-13, XD-27 (untraced), DD-19/20
  (1/4); DD-02 follow-up + manual bake; 22 of 29 bakes still queued (bake.out "bakes done"). `check_drops.py` ladder fix.
  Plan: after A3 34th, dungeon continuation sessions (A7/A8 roles) and outdoor ones (A5/A6 roles) work the pending lists.
- FB F6+F3 done: outdoor chests are a 9-face box (studio) → F6-R1 for A1 (MP41); props on terrace lips / floating on
  bilinear vs triangle ground (F6-R2) / steep scatter (F6-R3); `tools/xeen/check_props_support.py`; X1 barrel pair
  moved (your report), X2, X3, X5, 28 indoor sites + 16 wall-texture chests → MM8 chests; X7 "orcs' den" chest
  (renamed "The orcs' stash") and X6 den chest queued. Orchestrator killed an orphaned `sleep 7200` holding X7's lock
  (from a finished agent): F9's Sablewing job took the lock 00:05:53, F6's X7 cycle next. Walks broken by tonight's
  hook changes: X5 step 315, X9 dragon_clouds step 15, XD-01 culvert, D3 walk step 31 (after F2's D3 install).
- A3 34th stopped at budget: D-89 hooks done (10 outer locks gone, Sandcaster pass gone, 4 inward, 21 sealed with
  refusal lines; `quests.py` sealed list + entrance scans), D-90 (82 hooks to status, 15 windows with reasons, 49 finds
  sorted in `output/a3_s34/d90_finds.md`), `found:` → HasEverOwnedItem, `english/trans.txt` 65 rows. Main normal fails
  09, 15, 39, 41, 43, 57, 63 (test steps: status lines, F1 `house_dialog: false`); side 61/71; reload/promotions not run.
  Its per-lane REQUESTS in `output/a3_s34/REQUESTS.md`. Orchestrator added world.yml `transitions` range + trans
  contribution (backup output/xeen_o4/world.yml.bak_trans); world loads (scenario passes).
- 00:20 wave: A1 36th (MP41 — outdoor rebuilds wait for it), A7 26th and A8 26th (dungeon follow-ups), A3 35th (test steps, full reruns). Outdoor A5/A6 follow-up sessions after MP41. Orchestrator decision for A7: XD-24's vault door follows the outer door (no night condition).
- FB F6+F3 final: X7 (00:09:38, "The orcs' stash" beside the den) and X6 (00:12:03) installed with bakes; X1–X7 hostility
  pass; walks broken by tonight's deliberate changes: X5 step 315 (holy book status), X6 step 59 (cairn status), X7 step 67
  (Orc Caves back gate now an entrance window, F16), X9 dragon_clouds step 15 → outdoor A5/A6 follow-ups.
- FB F4+F9 final: Sablewing installed on X7 as a gold dragon (00:15:05), unkillable; key_npcs.py 0 errors. Druid decision already made (D-91) → outdoor follow-ups. 18 stale bakes from queued installs (bake worker catching up).
- P 1st done: Xeen desktop 1,149 → 792 MiB measured (dedupe on, bakes at 16), → about 500 MiB once the A1 fallback
  (MP41, relayed) and the 32 u/texel rebake land; ADPCM sounds (−59 MiB), decoration sidecars (−36), dedupe (−263 once
  the fallback lands), bakes (~−50 est.). CI-style desktop packaging 299 packs 9,868 MiB OK; 16 release scenarios pass;
  CI pipes scenarios into `| cat` (a failing scenario wouldn't fail the job) — for the user. Background: rebake queue
  (`output/xeen_p/bake/rebake.log`), Android chain (`output/xeen_p/android_chain.log`). To ship Xeen at all: un-ignore +
  commit `assets_dev/worlds/xeen/`, commit `assets_cooked/android/worlds/xeen/`, add it to both checkout lists in
  `.github/workflows/packages.yml`, `xeen` in packs.yml `worlds:` — the user's call (commits/release). Orchestrator:
  keep the 44 MiB MM9-only shared textures in Xeen; keep decoration cook quality (no further −40 MiB).
- **A1 36th: merge point 41 released 00:55:24 (game + oymap):** outdoor chests = shipped 19-face chest (`core/ChestKinds`),
  game-triangle ground heights, scatter spread rule, doors pair wing pictures + whole picture per leaf, cave mouths buried +
  `form: shelter|blocked`, door rules in `oymap audit` (errors on Xeen), F9-R2 NPC names (MM7 122 / MM8 20 placed actors now
  show their NPC names — original behaviour), F4-R1 launch heights (MM6 Dust Devil 118→104, ElemAir C 138; MM7 Water A
  126→124), shared model texture fallback (P to switch `share_model_textures` on + CONTENT_FORMAT bump). Regressions 45 pass
  (Hesper stale). Orchestrator on its DECIDE: outdoor chest front north at turn 0 fine; indoor default chest should follow
  the style world (7gt002 for Xeen) → MP42 queue. Outdoor follow-ups A5 29th, A6 32nd and S 15th started 01:05.
- A8 26th done: lane clean on MP40. Orchestrator on its DECIDE: XD-11 keeps the lock on the Skeleton Key's chest, not the study door (D-89: the study must stay clearable). Relayed A3 35th (test steps, reruns) and A6 32nd (D7 grate Yes/No, D6 Soul Box gate). DD-09/DD-14 identity rebuilds still to do.
- S 15th done: row 11928 "Xeen Elder Druid" (MM6 wizard body, moss-green robe skin `xsor_i`); A5 29th and A6 32nd told to re-place the druids at their rebuilds.
- A7 26th done: the 12 "refused" maps were MP40 oymap differences (no one's uninstalled change); all rebuilt/installed/baked;
  XD-18 rebuilt as a real cave (rough walls, uneven floors >30 %, stalactites, King on a gold mound, stars in the
  starwell; captures `output/studio_cal/a7/s26/xd18/{before,after}_sheet.jpg`), 20/20; finds → chests/ground items +
  map_gives. Left: FD-03 main playtest (status read), FD-04 alister/shrine/terminal (alister: actor name check — MP41's
  F9-R2 now names actors by NPC, likely), XD-13 identity, F14 pockets on A7 maps, plank/slab door leaves. Relayed A3 35th,
  A6 32nd (xfgrid tile), A5 29th (XD-17, XD-16 playtest_way).
- A3 35th stopped: every known broken step fixed in the files; fixers `output/a3_s35/{scan_entrances,fix_entrances,drop_gone_prompts,scan_status_map,to_status}.py` to run after each outdoor rebuild; then `output/a3_s35/full_runs.sh` + side quests + promotions both modes. Refusal lines of finds default to the status line (accepted). Relayed A7 27th (DD-07 jewel_found), A8 27th (DD-05/DD-20 found bits, Cult Leader body over the key). A1 MP42: q-d9 arrival message.
- A5 29th done: X7 (shelters: Sablewing's cave, pickets' den; adit blocked; six mouths narrowed; trans rows), X2 (Yak door,
  strongbox pendant, F10), X1 (Spring Druid 11928, F10 by moving), X4 (Autumn Druid; 8 F13/D-90 sites), X6 (werewolves' den
  blocked, Summer Druid, sphinx doors, prompts gone), X3, D3, XD-17 — all 0 audit/door/D-85/key_npcs errors, walks pass.
  Doubts: `oymap things` still shows outdoor chests as 9 faces after MP41 → A1 37th checks first. Orchestrator on its
  DECIDE: druids get their own friendly row (S 16th) instead of making row 517 friendly map-wide; D3's empty north-west
  corner gets a population (next A5 session). Left: X9 (F16, steps 45/118), P5, F10 D3/X6, ground items (need an
  outdoor ground-item kind → A1 37th), X3 sundials/ranger camp and X9 nests to buttons, shelter/chest screenshots.
  For A3: `q-c2.strongbox` → map_gives (pendant given twice now), `q-d14.quarter_gate` unused, reruns listed.
- S 16th done: row 11929 "Xeen Druidess". Note: `build_world.py --check` shows `trainer_places.txt` differing — someone's pending change, not S's (find the owner before a full write). A5 30th started 02:40.
- A8 27th done: DD-09 and DD-14 rebuilt for identity (captures `output/studio_cal/a8_s27/dd09_*`, `dd14_*`); DECIDE accepted (DD-14 ribs under flat ceilings; no banners — no banner picture). For A3: rerun 49, 61, 67, 63; delete bits 113122, 113401, 113402. A8 28th started 03:00 on the weak-identity list.
- A6 32nd done: all A6 maps rebuilt on MP41 (D1 burrow's message replaced the entrance window — real fault fixed; D6
  whole-picture gate leaves + Soul Box check; F10 zones down on X5, D6, D2, D4, D5; Winter Druid on 11928); new
  `tools/xeen/entrance_screens.py`; removed a self-referencing symlink `data_tables/data_tables` (00:11, unknown owner)
  that broke stage copies. P1–P4 18 audit errors each (studio ignores top fit/size on plate tops → A1 37th). Orchestrator
  on its DECIDE: D5's behind-the-Barrier strip exempt (D-49) — accepted; D1 rope hook setting `rope_climbed` before the
  window choice — accepted (harmless line flag). For A3: trans 5046 placeholder text, hook `m33.arrival_gate`,
  `q-d22.guild_wrong` direct move, retire `q-d28.sewer_grate` question / `q-d15.lair_door` message; reruns listed.
- A7 27th done: XD-13 (Harmondale-style ruin hall, broken roof/breach/rubble at stage 0, lab, steel vault door; captures
  `output/studio_cal/a7/s27/xd13/`), FD-03 (dark tower; `.../fd03/`), check_drops.py fixed; door pictures DD-06, XD-04,
  XD-03, XD-25; chest fronts. Orchestrator on its DECIDE: XD-15 slabs stay sliding slabs retitled "Stone slab"; XD-04 48
  textures accepted. Relayed A1 37th: XD-26 ladder grab fails since MP41. For S: XD-13 wood golems wear the pharaoh
  golem headdress (D-89 wants a wooden body/tint). For A3: delete bit 113361. A7 28th started 03:20.
- A1 37th: merge point 42 (oymap only, 01:57:08): outdoor sketch `items` (ground items), indoor default chest by style
  world (101 chests on 30 maps at their next rebuild), fitted tops' undersides, F6-R4 props rules in `oymap audit`
  (2 errors: fd04 chest.entrance, dd10b support.overhang), check_actor_heights reads sprite_frame_data*.yml, x6 War Zone
  test in regressions. Outdoor chests were already right after MP41 (86 × 19-face; captures
  `output/xeen_a1/mp42/chests/sheet.jpg`). q-d9: test checks the arrival message too late (A3). XD-26: gargoyles, not
  MP41 (A7 told). Orchestrator: X1's key goes on the ground beside the barrel. Relayed A5 30th, A7 28th, A8 28th; A6 33rd
  started 03:30 (P1–P4 vents, X5 holy book).
- A5 30th done: every A5 outdoor map passes empty_zones; ground items placed (X1 key at the barrel's foot, X2 skull, X7
  lava rock); X9 gates show the window, nests/sundials/ranger camp on buttons; P5 stair window; shelter captures
  `output/studio_cal/a5/s30/x7_shelters/sheet.jpg`. P5's three fall tests fail on X5's markers near the landing →
  relayed A6 33rd. Orchestrator on its DECIDE: X7's den chest drops its "Pillage?" question — the chest opens at once,
  the line goes to the status bar (the user: "let me open the chest and loot it") → small A5 follow-up in the final pass.
  For A3: map_gives for m2.rain_barrel, q-c19.skull, q-c14.lava_rock, q-c2.strongbox; reruns listed in A5.md.
- A6 33rd done: P1–P4 0 errors/0 warnings; X5 holy book on the ground (event 108 unused), wolf circle moved off P5's
  landing (P5 falls pass). For A3: `q-c18.book` → map_gives, q-c18 scenario → pick_up. Orchestrator regenerated
  `trainer_places.txt` (`--only gen_towns`; entrance coordinates shifted a few units after X1/X7 rebuilds; backup
  output/xeen_o4/trainer_places.txt.bak) → `build_world.py --check` 0 differ.
- A7 28th stopped at budget: shared cave pass `tools/xeen/cave_shape.py`; DD-11A/B/C, DD-23, XD-05, XD-16, XD-26 pass
  the cave-shape audit; its queues `output/studio_cal/a7/s28/q5.sh` → `q6.sh` (results `q5.out`, `q6.out`, ends Q6DONE)
  still running (XD-05/XD-26 fixes rerun). Orchestrator on its DECIDE: DD-11 guard rooms stay as built; XD-05's drum-hall
  bowl is later polish. Left: XD-23 cave pass, name-test captures, NOTES lines.
- **Orchestrator: 17 self-referencing symlinks** (`assets_dev/engine/{effects,fonts,ui,audio,music,rendering,behaviors,
  terrain_materials,liquids,scripts,branding,rulesets,view_model,sprites}/<same>`, `worlds/xeen/{rendering,
  surface_materials_x4,source}/<same>`), all created 00:11:14 by an unknown agent script (an `ln -s` into an existing
  directory), broke P's Android chain ("Resolve asset symlinks before packaging") and stage copies (A6 removed
  `data_tables/data_tables` earlier). Removed (links only; list `output/xeen_o4/selflinks.txt`). P's Android chain must
  rerun. Final-pass check: no self-links (`find assets_dev -type l`).
- A8 28th done (identity: DD-12, DD-10A–C, DD-25, DD-20, XD-10, DD-04; captures `output/studio_cal/a8_s28/`). Orchestrator on its DECIDE: DD-20 arcade enough; near-threshold cave warnings accepted. A8 29th and A7 29th started 04:00 (last identity maps + MP42 rebuilds of the rest).
- A7 29th done: whole cave set installed and passing; XD-23 now d13; `tools/xeen/check_identity.py`; name-test sheet `output/studio_cal/a7/s29/names/names_sheet.jpg`; MP42 rebuilds of A7 maps (no chest issues). Orchestrator on its DECIDE: DD-11 dirt burrows recorded as an exception to the d43 share; XD-23 keeps d13 (a troll home). Relayed A8 29th the check_identity failures.
- A5 31st done: X7 den chest opens at once. Other chest question: D4 event 53 "Search the boat?" (A6) → same treatment in the final pass; DD-03/DD-06 combination/password stay (D-90 (d)).
- A8 29th done: identity XD-11 (octagonal tower, sky windows, merlons, lab benches with brew-coloured light), XD-09 (trunk,
  forge, crystal pillars), DD-02 (octagon floors 3–4), DD-19 (court, guild furnishings); MP42 rebuilds of all other A8
  maps; DD-04 step was a status line. Orchestrator on its DECIDE: DD-02 sky stays `xeen_darkside_day`; DD-19 family 6d11;
  DD-02's elongated octagon fine. **The identity pass of D-89 is done** (worst-first list built; remaining polish noted in
  lane files). Final fix-up session started 05:00; then the final pass (A3 tests, P packaging/CI, G guide).
- Fix-ups done; all world checks clean (stale 0, build_world 0 differ, xeen_balance, key_npcs, heights, exits, quests 0,
  no symlinks). Orchestrator added DD-11A/B/C to `check_identity.py` EXCEPTIONS and a CAVE_EXCEPTIONS list (DD-10B, DD-10C,
  XD-10) per the decisions → rc 0. **Final pass started 05:30:** A3 36th (tests), P 2nd (Android + CI), G 7th (guide).
- **P 2nd done (release check):** every CI step that runs locally PASSES both as CI would build today (MM6–MM9: desktop
  299 packs 9,865 MiB, Android 231 packs 5,944 MiB, 16/16 release scenarios from packs) and dry with Xeen (desktop 322 /
  10,602 MiB, Android 252 / 6,446 MiB; Xeen 737 / 502 MiB). Android cooks current, verifies 0 problems; Map Studio
  workflow 510/510; installation tests 38/38; MAW checks pass. Not run: publish prepare/sign/check, OS builds, APK.
  `share_model_textures: true` WITHOUT a CONTENT_FORMAT bump (a bump would make every installed 2.x updater refuse the
  update). For the user's release: commit `engine/models/GltfModelLoader.cpp` (A1's fallback) with packs.yml; commit 68
  untracked engine asset files + 10 Android cooks + glow/surface files CI checks out; to ship Xeen un-ignore/commit the
  world + Android cook, add it to packages.yml checkouts and packs.yml worlds; release notes: MM7/MM8 NPC names.
  quests_smoke step 10 relayed to A3 36th.
- G 7th done: Xeen guide deployed (finds on the maps, chests list contents, all 109 walkthroughs rechecked, FAQ, shops
  intro, 82 arrival shots recaptured). After A3 36th: if `quest_hooks.yml` differs from `output/xeen_g/s7/quest_hooks_0313.yml`,
  `build_site.py --skip-images` + `check_story_refs.py` + deploy. Remaining Yes/No `AskQuestion`s (orchestrator check):
  X8 harpy nests ×3 "Destroy?", X9 1, D5 3, D7 21 (incl. the Rope's Head "Descend to the Darkness Below?" into D1 — an
  outdoor-to-outdoor move, not a BLV entrance) — choices shown with buttons (D-72), not F16 entrance prompts; left as built,
  noted for later polish (an outdoor travel window like MM6–MM8's for D7→D1 would be the MM convention).
- **A3 36th done (final test pass, game MP41):** main 52/52, `--reload` 50/52 (83 XD-12 disc, 85 DD-15 cage: after a lift
  ride, save+load leaves the party stuck on the lift — engine/map fault, not worked around); promotions 41/41 both modes;
  side quests 71/71, `--reload` 67/71 (q-c17 petrified before the wand, q-c5_q-c11 dialog after reload, q-c8_q-c9 stuck
  XD-14, q-f1 stuck FD-04). quests.py 0, quest_stub 19/19, build_world 0 differ. Runner: `--reload` no longer reloads
  between a wait and its status-line read. New `m33.arrival_gate` (needs a D6 rebuild). Requests in
  `output/a3_s36/REQUESTS.md`. quest_hooks.yml differs from G's copy only in the XD-18 east-wall text → guide rebuild at
  the end. Started: A1 38th (lift state after load), A6 34th (D6 rebuild), A3 37th (side `--reload` four, then
  83/85 after A1).
- A6 34th done: D6 rebuilt with `m33.arrival_gate` (hook decides, voiced refusal), all checks 0; D4 event 53 was already
  question-free (fixups); no test step needs changing for either.
- A1 38th done: main 83/85 `--reload` failures were stale reload checkpoints (saved before the XD-12/DD-15 rebuilds →
  maps reset on entry), not an engine fault; `--reload 81 83 85` in order passes; MP43 (= MP41 code); runner prints
  STALE lines; regression `tests/scenarios/xeen/dd15_lift_reload.yml`. Relayed A3 37th. Started A8 30th: XD-12 events
  15–17 set disc 32 / grille 13 explicitly (a map reset no longer shuts the grille at the top).
- A8 30th done: XD-12 disc/grille set explicitly from map var `disc_down`, restored on every load (event 62), event 56
  same fix; playtest_reset added; 81/83 pass both modes. Orchestrator on its DECIDE (Darzog back after a map reset):
  (a) as a generic rule — a unique boss whose death sets a quest bit stays gone on load once the bit is set (as DD-04's
  `king_gone`) — queued as later polish for all maps, not now: no player save of Xeen exists yet that a map update
  could reset.
- A3 37th request (interim): FD-04 door 7 (rotating mover, closed) blocks a walk only after a save/load; probes
  `output/a3_s37/probe/qf1_a.yml`/`qf1_b.yml` differ only by the reload. Started A1 39th (root cause, shared fix, MP44).
- **A3 37th done:** main 52/52 both modes; promotions 41/41 both; side 71/71, `--reload` 70/71 (q-f1: FD-04 door after
  load → A1 39th); quests_smoke + 10 hook scenarios pass; quest_stub 19/19; quests.py 0; build_world 0. q-c17 temple cure
  + 2,000 gold; q-c5 runners skip a reload between a timer dialog and its check; q-c8/q-f1 fight on the way; five hook
  scenarios updated (D-90 status lines, FD-02 event 56, FD-03 hatch). Started G 8th (guide rebuild + deploy).
- G 8th done: guide redeployed (m33 gate refusal, q-c25 east wall, m21 disc/grille tip, m2 Fenwick topic);
  check_story_refs 0; hooks copy `output/xeen_g/s8/quest_hooks_0553.yml`. Waiting only on A1 39th (FD-04 door).
- A1 39th done: FD-04 "door after load" was a live Phase Dragon in the way (the reload's 0.5 s dialog step let it close in),
  not the door; MP44 (stuck walk_to now names the actor in the way); regression `fd04_rotating_door_reload.yml`.
  Orchestrator added `clear_hostiles: 1500` to q-f1's two roof walks (lines 231–232) → q-f1 PASS normal and --reload.
  **Side quests 71/71 both modes; all sets green.** Android incremental cooks: 0 to cook, every verify 0 problems
  (`output/xeen_o4/android_final.log`); stale 0, build_world 0, quests.py 0. STATUS.md summary updated. Final report sent.
- **User: "commit all the necessary xeen stuff"** → asked: code entangled with co-op (save 198–200 adjacent; co-op's
  staged copies hold Xeen hunks) → user chose ONE code commit (co-op + Xeen code), then Xeen assets/docs, then the
  Android cook; co-op's scenarios/tools/lobby/plans and AGENTS.md stay uncommitted. Script
  `output/xeen_commit/build_trees.sh` (private indexes, commit-tree, CAS update-ref, shared index synced for committed
  paths); dry run OK (code 462 files, assets 8,234, cook 1,367). Xeen un-ignored, added to packs.yml worlds and the
  packages workflow. Held until three user requests land: A1 40th (Dimension Door in new-game order, labels removed,
  inspect shows the NPC's name) and A4 signs (Adventurer's Inn sign as MM8 Ravenshore, every house kind audited).
- A1 40th done: MP45 (09:10; build/ rebuilt 09:13): Dimension Door place = card order rank (Xeen, Enroth, Antagarich,
  Jadame, Chedian), globes regenerated, labels removed (U-8); inspect shows NPC names (also outdoor saves renamed on
  load); journal Quests/Notes/Trainers/ledger/Arcomage tabs from the mounted worlds' cards (Xeen tab incl. Darkside;
  112 Xeen trainers). Started A3 38th: journal lines for 14 quest files without one.
- A3 38th done: journal lines for M37 (4 reflectors), M38 (4 sleepers), T2-CLAN, Q-C25 task; every line now ends
  (19 got endings, 13 finished-quest records dropped; quests.py refuses a line without `until` unless
  `journal_stays`); quest_stub 19/19, quests_smoke, run 59 85 pass on MP45. Waiting on A4 signs, then commit.
- A4 signs done: Adventurer's Inns hang `sginn` (X1, D1), taverns the mug; kits stopped dropping cottage/temple signs
  (10 signs restored); `tools/xeen/house_signs.py` via towns.py; X1, D1, X2, X4 rebuilt; main 52/52 from 01, 37 side
  files pass. Android incremental cook 0 to cook, verifies 0 problems.
- **COMMITTED (user's request):** 335c92e11e "Game code" (468 files, co-op + Xeen), 1afa1b3f2c "Assets and docs"
  (8,235 files: Xeen world un-ignored and shipped), fb149b6313 "Android cook" (1,367). Shared index synced; co-op's
  scenarios/tools/lobby/plans/AGENTS.md stay staged for openyamm-1c (told). Not committed: assets_source submodule
  changes (MM7 decos, ice terrain sources), `.github/workflows/studio.yml`, settings.ini.
- D-92 (orchestrator, on A4's DECIDE): every service signed (ERROR), guilds their school's sign on both faces,
  sginn/sgtempl/sgdock `feature`. Started A4 signs2 for the 13 unsigned houses (X3, D3, X5, D2, D4, D6) + D1/D3
  guilds — uncommitted follow-up.
- User: quest-granting topics should read "Quest" as in MM6–MM8. Started A3 39th: measure the MM6–MM8 convention,
  generator labels quest topics by role + check, update test steps, regenerate after A4 signs2 lands, full reruns.
- User batch (shots `output/xeen_o4/feedback_20261122/27–31.png`): town walls leave gaps / end on walkable banks;
  culvert/wall joints with slits; rain barrel key should go to the cursor. Decisions: F19 rules (closed circuits
  anchored in water/cliff/edge, flush joints, enclosure flood-fill check); D-93 hidden finds → cursor (GiveItem),
  visible items stay ground items, chests stay chests. Started A4 walls (`output/xeen_walls/`, after signs2, ends
  with "WALLS DONE" in A4.md); D-93 relayed to A3 39th, which now waits for WALLS DONE before regenerating/reruns.
- A3 39th (prepared, stopped at ~364k by the orchestrator before the reruns): rule measured (MM6–MM8 "Quest", second
  Quest topic tracks/hand-in, promotions named); Xeen `role: quest` → "Quest", `role: promotion` → "Promotion",
  `named:` for 9 choice answers, afterwords after hand-in; 108 topics renamed (`output/a3_s39/renamed.txt`); checks
  in generator/quests.py/quest_stub; D-93 hooks (rain barrel, X5 book) give to cursor; 420 test steps converted.
  Orchestrator on DECIDE: plain "Promotion" stays; several Quest topics on hub NPCs stay (MM7 convention).
  Remaining steps 1–4 (A3.md Session 39 / its report) go to a fresh A3 40th after "WALLS DONE".
- **10:19 the PC locked up (OOM: RAM + swap full, power cycle).** Per the user's report: three MM9 convert.py runs
  (4 voxel workers each, ~57 GB), two lane.sh C++ builds (~19 GB), game runs, /tmp files. Not started by Xeen lanes
  except game/tour runs. Guard added: `tools/heavy.sh <cap GB> cmd` (waits for cap+24 GB free, systemd scope
  MemoryMax, no swap; tested: over-cap job killed alone); `mm9r_common/lane.sh` jobs (cap 48) and builds (24, -j16)
  through it; AGENTS.md "Heavy jobs and memory"; lanes/README.md "Memory"; ≤3 heavy agents. After reboot: no
  half-written Xeen installs (last 09:58), walls queue never ran; build_world 5 differ = A3 39th's prepared, not
  regenerated; stale bake = MM9 guberland (not Xeen). Resumed signs2 (shots, block) and walls (queue via heavy.sh).
  Next: fresh A3 40th after WALLS DONE (A3 39th's steps 1–4).
- A4 signs2 done: every service signed (house_signs 0/0, NO_WALL empty), guild school signs on both faces, 20 sign
  boards `feature`, kits size signs to their picture (D4/X2 1.5× boards fixed), D4 gen.py retired hook line removed;
  contact sheet `output/xeen_a4_signs2/shots/contact_sheet.jpg`. Open: DD-25 `sgearth` feature_border warn (A8),
  texture_classes full rerun drift (A1/A6). Walls running.
- A4 walls done (F19): `tools/xeen/wall_check.py` + `town_walls.yml` via towns.py --strict (60 errors → 0 on 13 maps);
  X1 creek walls into the water + one-piece culvert headwall, X4 wall up to the castle towers, X6 yard enclosed, D1
  corners/gate leaves, D3 corner towers, D6 gatehouse/fields, X2 terraces; rebuilt one at a time through heavy.sh;
  sheet `output/xeen_walls/sheet_before_after.jpg` (checked). Map checks in README extended. Started A3 40th: apply
  A3 39th (Quest topics, D-93 X1/X5), regenerate, full reruns (all through heavy.sh).
- User: X1's full crenellated creek wall is "a little too much", wants an "end water piece". D-94: a generic water end
  piece (low battered cutwater/pier, no crenellations, still impassable; stakes/grille if needed) for every circuit end
  in water. Started A4 walls2 (`output/xeen_walls2/`, after A3 40th's X1 install; writes "WATER END DONE");
  A3 40th told to start playthroughs only after it.
- User: X1 culvert entrance should be sunk into a sloped-down terrain cut, not a structure on flat ground with a water
  quad on grass; the creek side view makes no sense. D-95 sunken/culvert entrance kit piece (terrain cut, arch at
  ground level, outfall at the waterline on the creek side, no water quads on land), survey all maps. Relayed to the
  walls2 session (same X1 rebuild).
- User: Lifeforce Lagoon's village has no villagers; wants diversity of villager types per town (as MM7/MM8 towns).
  D-96 (to record by the agent): every settlement has wandering peaceful villagers at MM density, a per-settlement
  palette of 3–5 installed MM6–MM8 townsfolk types fitting WORLD_DESIGN, neighbours differ, data-driven + towns.py
  check. Started A4 villagers (`output/xeen_villagers/`, writes "VILLAGERS DONE"); A3 40th waits for both DONE lines.
  Heavy agents now 3 (A3 40th, walls2, villagers) — the cap.
- Castle Blackfang (DD-14) user pose: open battlements by design (arrival line says so); answered, offered a lean-to.
- A4 walls2 done: D-94 `water_end` pier (kit `tools/xeen/kit_pieces.py`, wall_check `walls.water_end`), D-95
  `SunkenEntrance` on X1's culvert (ditch, revetments, barred outfall at the waterline); X1 installed 12:10, checks
  pass; sheet `output/xeen_walls2/caps/sheet_before_after_x1.jpg` (checked). DECIDE X4 undercroft → yes, folded
  into the villagers session's X4 rebuild.
- A4 villagers done (F20, D-96): palettes in `source/towns/villagers.yml`, spots by `tools/xeen/villagers.py`, check in
  towns.py (density ≥ 0.45/door, ≥2 types, allowed races, neighbours, peaceful, clearances); 11 maps rebuilt, race pass
  on 8; Nightshadow 0→12, Castleview 0→30, Lakeside 0→12, Necropolis 0→8…; X4 undercroft sunken (D-95). VILLAGER
  RACES DONE 13:20. Orchestrator on DECIDE: (1) cursed towns keep villagers from day one (the user complained of the
  empty village; align X3 plan text); (2) no off-race story groups (user's rule); (3) 640 clearance from all doors ok.
  Left for after A3 40th's reruns (each rebuild resets checkpoints): XD-17 Shangri-La villagers (A5), D7 Olympus (A6),
  D2 sprite townsfolk type (A2+S), DD-25 dwarf by a door (A8).
- Music: original Xeen .m rendered (Nuked-OPL3, own renderer, `output/xeen_music/`); user: doesn't fit. ElevenLabs
  balance (user's dashboard): 48,006 left of 131,000. **U-9: plan B approved — 8 Xeen themes, one take each, cap
  18,000 credits**; retakes only on the user's say. Started AU music (`level_generation/sounds/xeen_music_20261122/`,
  review page, install plan in MUSIC.md, no install yet).
- AU music done (U-9): 8 themes, one take each, ledger 18,000 (price-list rate; real ~16,500), review
  https://claude.ai/artifact/Tca95rfncnb6hzGFk7r97K; install plan in MUSIC.md (tracks 92001–92008, 21 maps, town
  musicAreas), nothing installed. Dungeon take weak (loop level jump). Awaiting the user's listen.
- User resumed the AU music agent to retake the dungeon theme (~2,250 credits, user's own instruction).
- **A3 40th done:** Quest topics + D-93 applied (X1, X5 rebuilt), tables regenerated; on the final maps main 52/52
  normal and --reload, promotions 41/41, side 71/71, quests_smoke + 10 hooks + 9 playtests pass, quest_stub 19/19,
  quests.py 0, build_world 0. Screens `output/a3_s40/shot/` (Falagar Quest+Carlawna, barrel key on cursor).
  Started G 9th (guide update + deploy). Still open: XD-17/D7 villagers, D2 sprite townsfolk, DD-25 dwarf; music
  install (user listening; dungeon retake running).
- AU dungeon retake done (take 2 even level, loop drop ~3 dB vs 10–15); ledger 20,250 total; review page updated with both takes. Awaiting user: install proposal, finale elsewhere, bitrate.
- User approved installing the music (U-10): 8 themes per MUSIC.md proposal, dungeon take 2, 320 kbit/s, finale only per plan. AU resumed to install (maps.yml music, world.yml musicAreas, map_stats regen, packaging check, audio-trace runs).
- Peer openyamm-40: main moved to e20d4fc9cd (Unicode text fix: game/ui, engine/FontAsset.cpp; GameplayHudFontLayer gained `shadow`). build-xeen (MP45) predates it; next A1 build: touch GameplayOverlayTypes.h / GameplayHudCommon.h first if crashes appear.
- Peer openyamm-d2: main moved to 04bf8e6193 (party pouches for Standard games; Party.h gained m_partyPouches). Next A1 build: touch Party.h too.
- Peer openyamm-c7: main moved to 6966c1c87b (MM9 player-report fixes, 88 files incl. shared Indoor/OutdoorWorldRuntime, ScenarioRunner/RuntimeDriver, EventRuntime; whole working-tree files, so any uncommitted Xeen hunks in them (e.g. A1 39th's walk_to stuck line) are now in that commit).
- AU music install done (U-10): 92001–92008 in `worlds/xeen/music/`, 21 maps retracked, town musicAreas, runs on X1/D3/P5
  confirm, +43.5 MiB (xeen.music.0/1). 
- User: Xeen card "Xeen (alpha)" instead of "Experimental: begin in Vertigo". Orchestrator edited continents.yml +
  MAW card (title "Xeen (alpha)", caption "Begin in Vertigo"), regenerated (0 differ). Journal tabs/ledger use the card
  title since MP45 → would break the "Xeen" owner match → A1 41st: optional short-name card field, MP46, build/ too.
- G 9th done: guide redeployed (md5 235742b3…), ~200 Quest/Promotion topic edits with afterwords, journal lines, D-93
  finds, culvert ditch + Asp undercroft figures, signs on the Shops page, arrival/giver shots of X1–X6, D1–D4, D6
  recaptured (villagers, signs, walls), Leafpoint shot fixed; copies `output/xeen_g/s9/`. Note: Q-C1 Autumn/Winter
  Druids keep own labels (no journal line) — possible A3 consistency polish.
- User: Castle Xeen corridor shows sky instead of a ceiling; DD-14 Blackfang 'roof' likely the same. Started roofs session (F21, D-97: sky only over deliberately open places, survey of all 69 BLVs + check, rebuilds via heavy.sh; `output/xeen_roofs/`). Playthroughs will need a rerun after its rebuilds.
- User: Castle Xeen more monsters overall; throne room 4–6 guards (now Xeen + 2). D-98: +30–40% XD-19 monsters (measured vs MM7/MM8 final castles), throne Lord Xeen + 6 guards; DD-17 Alamar checked to the same rule. Folded into the roofs session (same XD-19 rebuild).
- A1 41st done: MP46 (14:34; build/ 14:37): card `short_title` (journal/ledger/hints/portrait filter), Xeen card 'Xeen (alpha)' + 'Begin in Vertigo' (Standard and MAW), journal tab 'Xeen'; runtime test fails a tab naming no owner. TOWNS_FORMAT line fixed by orchestrator.
- User: chests in dungeons often rotated wrong relative to doors (e.g. FD-03 Darkstone Tower). Started chests session (A1 + dungeon lanes; D-99 rule measured on MM6–MM8; fix in studio + audit check; survey all BLVs/ODMs; rebuilds via heavy.sh; MP47; `output/xeen_chests/`). Two heavy agents now (roofs, chests). Playthroughs rerun after both.
- User: Castle Basenji no roof (relayed to roofs session). User: The Sphinx (XD-15) WAY too bright with torch → started bright session (F23, D-100; measure vs MM7/MM8, fix profile/kit/engine spec, all bright-stone BLVs; `output/xeen_bright/`). Heavy agents: roofs, chests, bright = 3 (the cap).
- User: XD-15 chest in front of stairs/entrance → relayed to the chests session (D-99 placement: clear of doorways, stair ends, through-routes; same check).
- Roofs session done (F21, D-97/98): cause = sky rooms walled full height both sides read as lidless corridors; 57 sky sectors on 33 BLVs all declared outdoors in briefs; fixed 7 (XD-19 4 wall walks, XD-14 3) by lowering the outer wall to a 160 parapet with sky beyond; `tools/xeen/check_open_sky.py` + open_sky.yml; Castle Xeen 72→98 monsters, throne Lord Xeen + 6 guards; DD-17 has no boss fight. DD-14 kept (DECIDE pending: parapet too?). Asked the user whether parapets suit or real roofs wanted. Sheet `output/xeen_roofs/sheet_roofs_a.png` (checked).
- Decider D-101: keep open battlements (7 walks), Blackfang as built, parapets 160–224; check rule for parapet height queued (orchestrator's quick attempt measured the sky face's bottom = 0 behind separate parapet faces → reverted).
- Bright session done (F23, D-100): cause = copied default profile (bounce ×5, ambient 0.9, ceiling 1.5) floodlit pale
  stone; `bake_indoor.py` `rendered_limit` (opt-in, all 60 xeen profiles mean 90 / ceiling 0.85), check
  `tools/lighting/indoor_bake_brightness.py --world xeen --check`; all Xeen BLVs rebaked; Sphinx 186→117 (torch 210→171).
  Orchestrator on DECIDE: torch stays as in MM6–MM8 (a). Follow-ups: DD-26 playtest_in step 10 (grate dialog text,
  A8); XD-20 isolated launch fails saving the start game (A8/A1); Southern Sphinx library wall still pale (cap by
  texture max later if judged).
- Chests session done (F22, D-99, MP47 oymap): cause = `facing` meant width direction, lanes wrote front direction;
  rule measured on MM7/MM8; studio turns chests by rule + placement clearances; audit `chest.facing`/`chest.placement`
  errors; 120 chests on 50 maps fixed, 6 moved; 0 chest faults on 82 maps; sheet `output/xeen_chests/sheet_user.png`
  (checked). Started A3 41st: fix DD-26/XD-06/XD-21/XD-27 entrance-window playtests, XD-20 launch fault, full rerun.
- Peer openyamm-d2: HEAD 4e9cc80053 (Protection from Magic blocks event/hazard/MAW affix conditions; Party.h declaration) + 63ef301795 on top. build-xeen MP46 predates; next A1 build: touch Party.h.
- Peer openyamm-1a: 63ef301795 cycle-speed key (KeyboardBindings.h arrays resized). Next A1 build: touch KeyboardBindings.h too.
- run_game.py start save renamed to 'autosave' (arena maps refuse other saves; XD-20 launches now, X1 still fine) — A3 41st's A1 request done by the orchestrator. A3 41st at 16:50: normal main 52, promo 41, side 70/71 (q-c8 XD-15 waypoint, fixed, passes), 16 scenarios; reload passes running (ETA ~17:40).
- User: remove Xeen custom loading screens (U-11): done by the orchestrator (source, regen 0 differ, 4 images moved to output/xeen_o4/loading_removed/, X1 launch clean).
- **A3 41st done (all green on the final maps):** main 52/52 normal + --reload, side 71/71 normal + --reload,
  promotions 41/41 normal, 16 scenarios, 4 fixed playtests, quest_stub 19/19, quests.py 0, build_world 0.
  Open polish: XD-15 gen_tests stair waypoint (A7), promotions --reload, XD-17/D7 villagers, D2 sprite townsfolk,
  DD-25 dwarf, Q-C1 druid labels, check_open_sky parapet-height rule, Southern Sphinx library wall. All of today's
  work after fb149b6313 is uncommitted (user commits).
