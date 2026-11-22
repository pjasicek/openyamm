# Xeen: third orchestrator's running record

Started 2026-11-20 23:30 from [HANDOFF_ORCHESTRATOR.md](HANDOFF_ORCHESTRATOR.md). Agent ids below can be resumed
with SendMessage only from this session; a later orchestrator starts the lanes fresh from their lane files.

## Lane agents

| Lane | Session | Agent id | Started | Checkpoint asked for | State |
| --- | --- | --- | --- | --- | --- |
| A1 | 19th | a4864097bc7f959f7 | 02:00 | ended (~471k): merge point 23 released 02:31 | stopped |
| A1 | 20th | ad2f8b0700c3007ab | 02:40 | done (~461k): merge point 24 released 03:13 | stopped: fresh 21st for MP25 (P5 hidden chest, smoke emitter) |
| A1 | 18th | a164acc1d1566a597 | 01:15 | ended (~401k): merge point 22 released 01:40 | stopped: fresh 19th when a lane needs engine work (trapdoor pose, smoke) |
| A1 | 17th (ended, ~433k) | a502f1c0fd6d4f0f1 | 23:30 | merge points 20 (23:40) and 21 (00:57) released | stopped |
| A8 | 9th | a80d2323ee57ccf47 | 23:30 | DD-19 installed 01:33; DD-14 D-52 helper looked stalled at 04:05 (no files since 00:52) — told to check/finish DD-14 only and stop | stopped (done) |
| A7 | 12th (ended) | a458eb69cb227a3f9 | 23:30 | stop after XD-16's graph and `mockups/act5_dungeon_graphs_a7.md` (→ D-47) | stopped (~288k tokens): XD-01 at 46, xosoot already registered; resume with D-47 (fresh session if long) |
| A2 | 8th | a2767ca3d146ce4d5 | 23:30 | ended (~308k) | stopped |
| A2 | 11th | a52375d54031858b5 | 02:50 | done (~176k): edge_spans, S's collision bodies; --check clean | stopped |
| A2 | 10th | a49422591dd62a6b7 | 02:00 | done (~185k): D-53 line, Lacey wander, edge arrivals; next: XD-19 recount when installed | stopped |
| A2 | 9th | aecd1110f2ddda3d7 | 01:10 | done (~231k): D-52 rows, monster kinds, Slayer Sword flag, Lord Xeen 2,200, D5 rows + travel; stopped | stopped |
| A7 | 13th | ab0e5db5008327fbc | 23:48 | ended (~495k): XD-16, DD-16, DD-24 installed; XD-20 facings fixed; XD-19 L4 in root, blocked (S guard, A1 hook/E11) | stopped: fresh session when XD-19 unblocks or D-51 answers |
| A5 | 13th | a517df6bf0c1dc07f | 23:30 | ended (~374k): X7 XD-16 door open 00:37; X9/XD-17 L1 with D-50 | stopped: fresh 14th session with D-50 |
| A6 | 15th | a2720a09012dbab53 | 02:35 | done (~374k): D5 Barrier translucent, DD-16 rebaked, D1/D6/X5 reinstalled, D-55 recaptures, P5 textures registered (168), D-57 family lines; D7 + P1–P4 L1 → D-58 | stopped: fresh 16th with D-58 |
| A6 | 14th | aadc4a6d6b54b8006 | 02:20 | done (~284k): 156 textures, Alamar night glow (surface maps), D6 02:04 (adit, flight, edges), X8 fall retest | stopped |
| A6 | 13th (ended, ~440k) | aef3646cf10cb133f | 00:45 | D5, D6 installed with bakes; D4/D1/X8 reinstalled; beds re-pasted; 154 textures | stopped: fresh 14th for Alamar night glow, D5/D6 rebuilds as blockers land |
| A6 | 12th (ended, ~387k) | af3a9e2016eb2d837 | 23:30 | D5/D6 L1 done → D-49; D1/D4 unsealed, beds in X5/D1/D2/D4, rim glow 1.5 | stopped: fresh session with D-49 |
| S | 7th | a0cadfc8e58f77b69 | 23:30 | stop after each creature another lane must place | stopped (done) |
| A3 | 18th | ad84b7d77d13b8123 | 02:50 | done (~231k): 57/59 clean on MP23; M42 (D-56) hooks + cinematic done event; sky_map_spells scenario | stopped: next after DD-14 reinstall / DD-15 / P5 |
| A3 | 17th | a0f4c1a07b2f2ac2b | 02:35 | done (~285k): segments 63, 65, 67 pass (Act IV complete to the Pyramid key); hooks_x9_xd17, hooks_d5_d6 pass | stopped: next after DD-14 reinstall / DD-15 |
| A3 | 16th | a1880dcede56f933c | 01:20 | ended (~401k): segments 57, 59, 61; Q-D16; D-52/D-53; A5's X9/XD-17 playtests pass with its hooks | stopped: fresh 17th |
| A3 | 15th | aaf4b37e87d32d7c7 | 00:30 | ended (~393k): all D-49/50/51 hooks, sky-fall point, m25.flight move; segment 57 for a fresh 16th after A6's D4 rebuild | stopped |
| A3 | 14th (ended) | aff9a63316fad736c | 23:30 | stopped (~340k): relays, D-47 hooks, 18 side quests; next session when D1/D4 unseal (Q-D6, Q-D22 scenarios) or DD-12/14 (segment 57) | stopped |
| A7 | 16th | ab075aee1869d3e11 | 02:35 | done (~289k): XD-19 ActorIndex re-bake 02:39; phase-6 page `act6_dungeon_graphs_a7.md` Q1–Q37 → D-57 | stopped: fresh 17th with D-57 (FD-03 first) |
| A7 | 15th | ab37d28274bc3aab6 | 02:00 | done (~315k): phase 5 complete (XD-19 installed 02:07), DD-13 trapdoors/hides, NPC words, beds | stopped: phase 6 later |
| A7 | 14th | a70daa998770099a4 | 00:45 | done (~361k): DD-16 field + Corak unkillable, xdthrone v2, XD-19 textures + sword rule, XD-07 book; XD-19 waits on S's xeen_guard | stopped |
| A5 | 16th | ae50d2aff9cfedf80 | 02:50 | done (~286k): P5 L2–L4 built and tested 20/20 in scratch (12 new textures); X6 sphinxes installed 02:51 | stopped: install P5 when FD-03 + S's figure/decorations land |
| A5 | 15th | a270bf3e58e83dc91 | 02:45 | done (~231k): X2 dragons leashed, falls tested, X9 gate into XD-19 (02:16), P5 L1 → D-56 | stopped: resume/fresh with D-56 |
| A5 | 14th (ended, ~330k) | a8ff3928e6b3b0d45 | 00:45 | X9 (01:29), XD-17 (01:45) installed; X7 cleft open; beds pan; terrain_swap fixed | stopped: fresh 15th after D-54 / XD-19 |
| A4 | 12th | aeef8593c497b775f | 00:45 | done (~370k): Xeen completion certificate (new painting, ending text); block added to world.yml by the orchestrator | stopped: fresh 13th next time |
| AU | 4th | ae4aa73487b1008f4 | 01:15 | done (~286k): pan lines, indoor list, 7 new sounds; 27.0k charged / 93.75k committed of 100k | stopped |
| AU | 3rd (ended) | a7f31bea3eacaae2b | 23:55 | stopped (~295k): bed lists for X1–X6, D1–D4 in AUDIO.md; D-47 sounds 62520–62524; next: check pasted beds, apply D-48 | stopped |
| A7 | 17th | a82a4463bb253f3b6 | 03:30 | done (~323k): phase 6 installed — FD-03 04:10, FD-02 04:00, XD-18 04:33, FD-04 04:52; DD-13 cover/embers; DD-06/07 roof stairs | stopped |
| A2 | 12th | a355d62ae3483e401 | 03:30 | done (~255k): D-57 rows/tiers/items, Act VI recount 1.01, optional ledger | stopped |
| A3 | 19th | a84b17927ab3df991 | 03:30 | done (~393k): D-57 (q-f1, q-f2, m40, m41, q-c25), D-59, Roland switch, half of D-58 | stopped |
| A5 | 17th | aeaf98235280dfac4 | 03:30 | MP24 checks (leash, falls, visible certificate); X9 Dragon Clouds + gate exit; X6 fd02 point; P5 install when ready | stopped (done) |
| A4 | 13th | a8c2b74d49c0e54b4 | 03:30 | done (~241k): DD-25 rows 4701–4706, Ormond topic checked | stopped: DD-25 loop after install; FD-04 (installed 04:52) and D7 (installed 04:53) loops; XD-18 trainer after X7 |
| A1 | 21st | a83a88d338adf55b0 | 03:40 | done (~391k): merge point 25 released 03:57 | stopped: fresh 22nd when needed (P5 certificate check, A7 queue, D4 frame cost) |
| A6 | 16th | a2e27277a6581f013 | 03:50 | ended (~444k): D7 installed 04:53, P1 04:56, surface d7_fall points, D1 rope, D4/D6/X5 reinstalls, registry 185 | stopped |
| A2 | 13th | a0e7c2a2659ab736f | 03:50 | done (~265k): D-58 rows, Fire family renamed, element rows 11700–11722, Sky Bandit 11116, key 12377, balance.py counts AddValue; Act IV 1.122 → D-60 | stopped |
| A3 | 20th | a619584627db06088 | 04:05 | done (~282k): D-58's rest (tolls, riddles, bottles, scarabs 8/8/8/16, hatches, lamps, q-d26) | stopped: next when DD-14 reinstalled / DD-15 / P5 / D7 installs |
| A8 | 10th | a0aee2f5ea6aedb8b | 04:05 | stopped (~349k): page `act5_dungeon_graphs_a8.md` with DD-15, DD-17, DD-08 (Q1–Q31) → D-61; DD-25, DD-21, DD-10C, DD-22 not started | stopped: fresh 11th for the other four graphs |
| A8 | 11th | abccf6466756d4db9 | 04:20 | done (~252k): page `act5_dungeon_graphs_a8b.md` Q32–Q55 → D-62 | stopped |
| A8 | 12th | ac2ec511513265ee1 | 04:40 | done (~302k): DD-15, DD-17 (with cinematics), DD-08 installed; 8 textures | stopped: DD-15 floor polish after D-66 |
| A2 | 14th | ac9d1a731e3cd7792 | 04:40 | done (~205k): D-61 rows/factions, D-60 note, D7 ledger; 328 descriptors 0 refused | stopped |
| A3 | 21st | a9f4d5168f9c3a0c9 | 04:40 | failed on an API content-filter error before writing (no files changed after 03:56) | ended |
| A3 | 22nd | ab8dabdcf80d164c5 | 05:00 | done (~370k): D-61/D-62/D-63 text and hooks, Ormond 4571, segments 61/63/65/67 on DD-14's placed actors | stopped: next for segment 69, D7/phase-6 hooks in game |
| A8 | 13th | adcab5e71d4cb5533 | 04:55 | done (~353k): DD-25 installed 05:48 (4/4) | stopped: DD-26 L1, DD-22 L1 after D-65 (fresh session) |
| A2 | 15th | ad0205fbc33892ae5 | 04:55 | done (~179k): D-62 rows and recount (Act V 1.03; Act VI installed 1.02) | stopped |
| A6 | 17th | a1901f1e3256e9e57 | 05:05 | done (~322k): P2 05:15, P3 05:42, P4 05:37 installed; D6 05:18; D7 fall tests re-measured; registry 192 | stopped |
| A1 | 22nd | a827369cc751b9118 | 05:05 | done (~290k): merge point 26 released 05:26 | stopped |
| A7 | 18th | a9fda09f3f78007aa | 05:15 | done (~281k): D-63 in on eight maps (160/160), DD-06/07 roofs to D7 live, DD-16 exit by name, XD-16 smoke | stopped: FD-03 hatch when P5; FD-04 lizard/eggs when S names them |
| A3 | 23rd | aaac09c65a556ae9c | 05:30 | done (~387k): D7/phase-6/X9 hooks in game; segment 69 passes (workaround for D5's door); SkyFalls points fixed | stopped: segment 71 on (M29) next |
| A6 | 18th | a4474848ab7002b9f | 06:10 | done (~332k): D5/D6/D7 doors live, P1 question, P4 above_floor, MP27 on D1/D4/X5/D6 | stopped: DD-22/FD-01 doors, D5 boulder later |
| A1 | 23rd | a4bc5e5d9d2a23135 | 06:10 | done (~245k): merge point 27 released 06:06 (studio only) | stopped |
| A8 | 14th | a7aa5d3d15889c243 | 06:25 | done (~277k): D-67 applied, DD-22 06:43, DD-26 06:47 reinstalled, 4/4 incl. ways in | stopped |
| A2 | 16th | a5f39076246cca5f9 | 06:25 | done (~147k): DD-26 row, P3 MOUNTAIN, installed recount V 1.03 / VI 1.03 | stopped |
| A4 | 14th | aeef7d058f96e7eaa | 06:25 | done (~171k): dd26.yml planned (Cyrano 5614, portrait), D7 built (Olympus 4801–4814, mirror, Town Portal, Lucio's routes), DD-25 and FD-04 loops | stopped: DD-26 after A8's L4; XD-18 trainer after X7 |
| A3 | 24th | a69c90bc2e3dae932 | 06:30 | done (~383k): q-d28; segments 69–77 pass (M28–M33), normal and reload; hooks_d7 asserts | stopped: segment 79 on, hooks_dd26, P5 ending |
| A5 | 18th | ad54abc37e27133b8 | 06:15 | done (~304k): X7 doors, X9, XD-17, X6, D3, X1/X4 mound arrivals; **P5 installed 06:41** | stopped: XD-17 waterfall after S; X1 walk after A7's XD-05 exit |
| A7 | 19th | a50b1a19b0fc09a11 | 06:15 | done (~182k): MP27 on 7 maps, crossword variants, FD-02 exit by name, FD-04 roof Yes/No | stopped: FD-03 hatch when P5 installs |
| S | 8th | a995abe65e0640224 | 06:15 | done (~322k): P5 pieces; planes' pieces 4023–4042 bound; octopod_deep ready | stopped |
| A4 | 15th | a43d57b8dc963c095 | 06:35 | done (~87k): house 4815 written; XD-18 trainer row already in | stopped: DD-26 door check after install |
| A8 | 15th | aaabd9a21591d9b8b | 06:35 | done (~256k): DD-15 rebaked (no glare), DD-17 prompts/buttons/belt/arrival fixed, MP27 on 10 maps | stopped: DD-08/DD-17 throne and statue after S |
| A1 | 24th | adafefc2049dc98c6 | 06:35 | done (~276k): merge point 28 released 06:49 (game only): belts in scenarios, topic Yes/No buttons | stopped |
| A6 | 19th | a6385e38ab7f35c9d | 06:45 | done (~200k): D7 grate → DD-26 (06:44), D6 hatch → DD-22 (06:48), D-66 Yes/No on D7 exits | stopped: FD-01 doors, D5 boulder |
| A3 | 25th | a39a5ad883815ace7 | 06:55 | done (~306k): chain 69–85 (M37) both modes; hooks_dd26, hooks_p5; Cyrano buttons; ending seen in game | stopped: M38 after A6's sleepers, M39 after FD-01; D-68 |
| A7 | 20th | a22e898cacb74cbbc | 07:00 | done (~194k): FD-03 hatch to P5 live, named exits, DD-06/07 roofs Yes/No | stopped: XD-26 sky crack / XD-02 X4 adit names after A5 |
| A2 | 17th | a8e313cd0d48d6fbb | 07:25 | done (~156k): 11474 Octopod E, Pharaoh 230, 9170/9157, dwarves already 3D, recount V 1.03 / VI 1.025 | stopped: FD-01 row after its graph |
| A6 | 20th | ac99b10ffe314c35d | 07:25 | done (~342k): S's pieces on P1–P4 (07:39–07:45), sleepers wired, P4 octopods 11474 | stopped: P4 water fog after A1; S's Ember Font/camp/basket; D5 boulder |
| S | 9th | a65d392f71007e248 | 07:25 | done (~345k): thrones 4043–4045, teal statue 4046, waterfall 4016, Octopod E, dark knight skins, heart jar 4047, dragon egg 4048, ways up retuned | stopped |
| A8 | 16th | afce00dc69ed6a8e3 | 07:35 | done (~314k): FD-01 graph + page Q63–Q72 | stopped: L1–L4 after D-69 |
| A8 | 17th | a46d72cbba0d91be2 | 07:40 | done (~317k): DD-08/DD-17 thrones and statues (D-66 met), XD-12 cloud stair, DD-26 reach step (D-68), DD-21 jar; dd14 root removed | stopped: DD-21 reload 4/4 after A1; Sheltem's look |
| A5 | 19th | a2bf709333f233d01 | 07:50 | done (~208k): P5 couple npcs, X1/X6/X7 reflector button prompts, X1 walk, X4 adit point | stopped: XD-17 waterfall after S |
| A3 | 26th | a95b5cb3721a42ccb | 08:00 | D-68 CONVENTION in 83 + PLAYBOOK §2; M38 after A6's sleepers; hooks_p5 talk | done (~354k, stalled 08:42 waiting on a run): CONVENTION in 83, M38 (87–93 pass both modes), D-69/D-70 hooks | stopped |
| A2 | 18th | aeeb44407fc0835e4 | 08:00 | done (~294k): stat gates 17/17 within D-59, gem budget; FD-01 row 9179; Act VI 1.037 | stopped: FD-01 L4 recount; D-70 |
| A1 | 25th | a883d4f452ec1e1ab | 08:10 | done (~334k): merge point 29 released 08:18 | stopped: A7's two warnings (needs cases), platform step event |
| A5 | 20th | a28e32fd7c5ad194d | 08:20 | done (~142k): waterfall placed 07:57, 8/8, audit 0/0 | stopped: S's look fixes |
| A7 | 21st | a3efcbb210e8e5275 | 08:20 | done (~205k): FD-02 throne, FD-04 eggs, XD-02 exit, XD-19 tray works; 84/84 | stopped: FD-02 lecterns, FD-04 lizard after S |
| S | 10th | a0bdf0245e49a1491 | 08:20 | done (~398k): lizard 4049, boulder 4014, cage bird 4015, lectern 4050, barges 4051–4054, skyboat 4055; waterfall and P1 column fixed | stopped |
| A8 | 18th | ae9978dfa72685ffa | 08:35 | done (~188k): **FD-01 installed 08:28** (7 tests 4/4, audit 0/0) — all 82 maps installed | stopped: way-in test after A6; polish after D-71 |
| A6 | 21st | abfd104c35e3b5f14 | 08:40 | done (~193k): D7 fd01_roof 08:02, FD-01 per_site line, X5 reflector prompt, P1/P3 re-shot | stopped: P4 fog after MP29; FD-01 doors at install |
| A5 | 21st | a2694f470e7769d72 | 08:15 | done (~268k): X9 tonic (08:22), D-70 daily guards on X3/X4/X6/X7/D3 (Lua-only 08:26) | stopped |
| A6 | 22nd | acaae7a7f4ee2d2a0 | 08:15 | done (~182k): D-70 daily on D1, D2, D4, D6 (Lua-only); P4 underwater fog 08:23; P1/P2 unchanged | stopped: FD-01 doors at install; P1 re-shoot after S |
| A6 | 23rd | ae9124e42612acb39 | 08:35 | done (~170k): D6 stair (08:39) and D7 hatch (08:40) into FD-01 live — every door in the world open | stopped: D-72 |
| A2 | 19th | a1e657a82d60d9824 | 08:40 | done (~142k): tonic counted, guard check 35/0 unguarded, every map counted: all acts 1.02–1.15, no trigger | stopped |
| A8 | 19th | ae80a91fe6cd331e1 | 08:45 | done (~339k): FD-01 done to D-71 (08:47), DD-21 4/4, DD-17 Sheltem seen, DD-12 cage birds | stopped: optional polish |
| A5 | 22nd | a0bb3dcbc7207a373 | 08:55 | done (~177k): six X6/X7 prompts as joined buttons (08:59); XD-17 re-shot | stopped: X3/X4/X9 typed prompts to buttons at next rebuilds |
| A7 | 22nd | ae3c04a3b066f5d5f | 09:00 | done (~180k): FD-04 lizard, FD-02 lecterns (09:02); A1 cases given | stopped: DD-16 ladder after MP30 |
| A2 | 20th | af25f43f0d8a076e3 | 09:00 | done (~83k): row 4014 r165/h280 (hand edit; file is S's) | stopped |
| S | 11th | aea0fb9bf3a9c21c7 | 09:10 | Alister has no body (FD-04) + scan for bodiless placed rows; XD-17 lip; optional plane devices | done (~262k): Alister bound (xcle_h), no other bodiless rows, XD-17 lip, P1 font/camp + P2 basket 4056–4058 | stopped: placed checks |
| A1 | 26th | a3124c9d33e9f0b00 | 09:10 | MP30: rotating studio movers, ladder-hole and panel warnings, docs | done (~292k): merge point 30 (studio, 09:24) | stopped: platform landing case from A7 |
| AU | 5th | accb55f97b390f922 | 09:20 | the audio queue (P5 chimes/fanfare, D7 and plane beds, D5 Barrier, dungeon stand-ins) — budget lifted by the user | done (~311k): 25 new sounds installed (62528–62544, 62814–62821); budget 140k; charged 37,791, committed 132,950 | stopped: placed checks |
| A8 | 20th | a3f695ea2b217cd55 | 09:30 | FD-01 levers turn (MP30); panel warnings DD-03, DD-19, XD-12 | done (~244k): FD-01 levers swing, pyramid dark, key racks; DD-03/DD-19/XD-12 panels fixed | stopped |
| A7 | 23rd | ad0e9ffe7fa2090e2 | 09:30 | DD-16 ladder; panel warnings DD-02, XD-02, XD-07, FD-04; platform landing case for A1 | done (~173k): DD-16 ladder; panels DD-02, XD-02, XD-07, FD-04; platform-step case for A1 | stopped |
| A6 | 25th | ad59a99bf4c6d4088 | 09:35 | P1 Ember Font + camp, P2 basket + cache chest | done (~204k): P1 font (daily +20 Fire), camp, light; P2 basket, chest beside it | stopped |
| A5 | 23rd | ac026bab82199b151 | 09:55 | AU paste: P5 chimes/fanfare cues, X1/X2/X4 night lines, X7 volcano bed | done (~187k): P5 chimes + fanfare (checked in game), X1/X2/X4 night beds (checked at night), X7 volcano, X4 camp buttons | stopped |
| A6 | 26th | a52c40b1c36dff62c | 09:55 | AU paste: D7 corners/dragon/sleep, P1–P4 beds, X5 night; D1 sprite refs | done (~200k): D7 corners/dragon/sleep (off on kill), P1–P4 beds, X5 night, D1/X5 bad campfire props → barrels | stopped |
| A8 | 21st | a2e65adac6ce9a82d | 10:05 | AU paste into DD-15/17/21/22/25/26, FD-01; pan: false on 9 maps' beds | done (~223k): AU sounds in 7 dungeons, pan:false on 9 maps, 15 rebaked, 0 stale, 264 runs 4/4 | stopped |
| A3 | 27th | a2c5f8acdb0bb35a3 | 11:30 | the chain to the ending (M39–M41, P5); reruns for buttons; hooks_d7; small items | done (~347k): **chain M1–M42 complete, segments 01–99**; 63–99 pass both modes; buttons; hooks_d7 | stopped |
| A3-side | 1st | a5647fe5a44f4abc2 | 11:45 | standalone scenario for every side quest (`tests/scenarios/xeen/side_quests/`, README); edits only q-c/q-d/q-f files | done (~304k): **every side quest has a scenario — 69 files, 69/69 normal, 69/69 --reload**; D-74 quest changes; README + 37 prep sheets | stopped |
| A3-promo | 1st | a82bab12c7e53fcf4 | 11:45 | `tests/playthrough/xeen/promotions/` chain like MM9's (tier 1, class table, tier 2, racial; Necromancer row check) | done (~332k): promotions chain 13 segments (blocks A–D) pass both modes; 10/24 table rows; Necromancer row; t2-later.yml | stopped: tier 2 rest, racial, tables |
| A4 | 16th | a75e27a7da70d0a0a | 12:05 | D-73: Dodging/Unarmed Expert to Rivercity, plan levels, towns.py order warning | done (~153k): Sparrow 4158 teaches the Experts; plan levels; towns.py order warning; strict clean | stopped |
| A3 | 28th | ac586ef29a14361e0 | 12:15 | whole chain 01–99 normal and --reload on today's world | done (~235k): **whole chain 01–99 passes normal (485 s) and --reload (34 min) on today's world**, no BLOCKER/ISSUE | stopped |
| A1 | 27th | a7e2865492ab04e8a | 12:25 | MP31: hidden monsters counted dead (invisibleAsDead), room step on platform tops | done (~318k): merge point 31 (game + studio) | stopped |
| A3-promo | 2nd | ade323d59df0c3b5b | 12:35 | D-74 invariant; tier 2 rest, racial, class table 24/24; drop seg 31 workaround after MP31 | done (~390k): 38 segments pass both modes; class table 23/24 (quarter blocked by D3's gate) | stopped |
| A5 | 24th | ad8598c40b5f2405d | 13:00 | D3 guild gate → DD-19 (blocks Q-D14 and `quarter`); scan for other sealed doors; D3 buttons | done (~169k): D3 guild gate into DD-19 live (13:05); no other sealed doors on A5's maps | stopped |
| A3-promo | 3rd | aa38829a7059edbf9 | 13:10 | Q-D14 + quarter row (24/24), D-75 log lines + run.py check, full runs | done (~212k): **promotions complete — 41 segments, 24/24 rows, normal and --reload** | stopped: rerun with --start after A3 28th |
| G | 1st | a0e8f4e3fd0aa1870 | 13:30 | the Xeen guide website end to end (MM9 guide's formats; shared generator; publish to jasicek.net/openyamm/xeen-guide/) | done (~535k incl. forks): **guide published https://jasicek.net/openyamm/xeen-guide/**; 82 maps, 109 walkthroughs, 116 teachers, bestiary 286; MM9 guide unchanged | stopped: A3's answers, extra POIs, figures |
| A1 | 28th | a5ee7af65daa932e2 | 13:40 | MP32: GiveItem destroys the cursor item when packs are full | done (~222k): merge point 32 (game, 13:44) | stopped |
| A3-promo | 4th | afaa686622be075f9 | 13:40 | refresh from the new main checkpoints (--start), full runs | done (~99k): refreshed on A3 28th's checkpoints; 41/41 both modes; runner --reload start-copy fix | stopped |
| A3 | 29th | a624b0338f9659a1d | 14:10 | answer G's 44 story questions; fixes; MP32 Songbird rerun | done (~197k): G's 44 answered (5 guide / 12 fixed / 6 map-engine / 1 decide / 8 to A3-side / 12 fine); 57/59 rerun | stopped |
| G | 2nd | a317637dd7c2089b4 | 14:20 | D-76 (fact-only text, map details without dev wording/answers, build check), fold A3's answers, extra POIs, figures, shots, republish | done (~410k): D-76 enforced by a build check; A3's 44 answers + D-77 folded in; ~560 puzzle points; 5 figures; 23 arrival shots redone; republished | stopped: D-79; lines tied to pending fixes |
| A1 | 29th | ae4d5884edeb1ade3 | 14:30 | MP33: magical age cleared on rest (shared), runner clear radii vs storeys, MM9 items in Xeen loot | done (~211k): merge point 33 (game 14:44) | stopped: app-suite case, saving a waiting item |
| A6 | 27th | ae95b42b5758d2c4f | 14:30 | D1 Sardaj hostility at once, X5 Burn? prompt, D1 lettered chests' lines, lamps' second rub, MP31 plane/X5 tests, old bakes | done (~268k): D1 Sardaj at once, tents/X5 Burn? buttons, X5 outpost burns down, Q-D4 lid lines, lamps; plane tests fine; old bakes deleted | stopped |
| A8 | 22nd | a14e78d921fd2f387 | 14:30 | DD-20 outfall one way, DD-10A "an emerald", DD-09 Barkman chest tests, MP30 warnings | done (~182k): DD-10A "an emerald" (14:26); DD-20 two-way (stalkers, no map fault); DD-09 tests fine; MP30 warnings recorded | stopped |
| A3-side | 2nd | a93eaea56d2a2cb85 | 14:50 | q-c16 Burn? step, D-77 tags, close fixed README items, Q-C1 after MP33, full runs | done (~270k): 70 scenarios all pass on MP33 (6 storey-clear fixes); Q-D10 robbery fixed + new scenario; Q-D15 glass; D-77 tags; README current | stopped: Q-D10 mercenary scenario |
| A3 | 30th | a5db58e3df86aa198 | 14:55 | main chain 01–99 rerun on MP33; PLAYBOOK D-75/D-77 bullets; G item 28; Q-D7 smith items | done (~220k): **main chain 01–99 passes on MP33/34, normal and --reload**; storey-clear fixes (57, 61, 63, 77, 95); PLAYBOOK D-75/D-77; G 28 closed | stopped |
| G | 3rd | a94964a56441c3d4e | 15:05 | D-79 clue texts cut + build check, MP33/D-80 shop page, landed fixes, republish | done (~190k): D-79 (85 points cut, solutions check, 0 faults), D-80 shop page, landed fixes; republished | stopped |
| A1 | 30th | af64613bac6527543 | 15:10 | MP34: shop stock candidates pool filter (plain MM9 items in shops?), MM9-loot setting gate for Xeen | done (~210k): merge point 34 (shop pools; MM9 setting not for Xeen) | stopped: waiting given item save; app case |
| A2 | 21st | a26c3a91df9e4f649 | 15:10 | D-80 shop check per Act; D-77 wording; Q-C25 gems in the gem budget | done (~218k): shop check (no DECIDE; Q5 not early; early Darkside Q4 weapons a tier high, noted); D-77 text; Q-C25 gems short 9 | stopped |
| S | 12th | a6b747f09a22a2939 | 15:35 | tier colours match names (Water Dragon blue, Acid green, Fire red; audit every family) | done (~267k): names/looks audit of 308 rows; 27 tiers recoloured (dragons, undead dragons, elementals, Ice Troll, Shadow Ninja, swamp things, Hell Hornet; Devil/hydra rebinds) | stopped: Power/Skeletal Lich |
| G | 4th | a41456f7abbec4bb8 | 16:00 | recapture 31 recoloured portraits (+ any bad ones), republish | done (~196k): all 286 portraits recaptured (capture framing fixed: model size + pitch); republished | stopped |
| Reviewer | 1st | aed71651471ed1056 | 16:15 | review and decide every STATUS G3 row (user's request); `reviews/G3_REVIEW_20261121.md` | done (~231k): 78 rows — 73 accepted, 5 need work; MP31/33/34 changes accepted; follow-ups by lane | stopped |
| A3-promo | 5th | a72c5ceadc7bf1146 | 16:25 | refresh on A3 30th's checkpoints; D-77 tags; drop seg 21 ISSUE | done (~130k): 41/41 both modes on A3 30th's checkpoints; D-77 tags | stopped: D-82 asserts |
| A6 | 28th | a9d041bcde3044890 | 16:45 | review: Olympus facades, P1 crater walls, P1 heat-column vent | stopped at limits (~214k): Olympus + P1 built in scratch, not installed | stopped |
| A8 | 23rd | a901cf990b312aaf5 | 16:45 | review: DD-02 brightness + pan, FD-01 levers/pyramid, DD-10C cold nest, XD-12 shot, DD-14 Queen | stopped (~307k): Reviewer fixes installed (DD-02, FD-01, DD-10C, DD-14 Queen, XD-12 shot); DD-14 playtest stuck (pre-existing) | stopped |
| A7 | 24th | a6290396beb3a3a20 | 16:45 | review: FD-02 blades, XD-19 ceilings, XD-05 line, close Clan Master, placed names if ready | stopped (~230k): FD-02 blades, XD-05 line, Clan Master closed; XD-19 ceilings still open | stopped |
| S | 13th | a4fb2f94d0ef33254 | 16:45 | review: Hell Hornet lift, Guardian of Air gold, Power/Skeletal Lich, optional jar/basket | stopped at limits (~237k): hornet, air guardian, liches done; jar/basket built not installed | stopped |
| A5 | 25th | ab81dfe841659c13f | 16:45 | XD-17 re-shoot, D3 event 93 cottage, X6 amulet line | done (~204k): XD-17 re-shot (rows 26/32 closed), D3 cottage every knock, X6 Sphinx door two clicks (line shows) | stopped |
| A1 | 31st | a1cf76b56ed219bdf | 16:45 | MP35: loader keys height/clear_height, Garrote Gorge regression, waiting item saved | stopped (~198k): merge point 35 released (save v199, PARTY DOWN check, loader keys, Garrote Gorge) | stopped |
| A3 | 31st | a624016b2cad3ccd2 | 16:55 | D-82 end checks + PLAYBOOK, whole chain reruns, D2 Petrify bisect, ending turn-based check, 77 keys after MP35 | stopped at limits (~192k): D-82 check in run.py + PLAYBOOK; ending OK; D2 not reproduced; checkpoints not rewritten; 61 fails under the check (gargoyles) | stopped |

## Relays

Open (to send when the condition holds), rewritten 02:35:

- From A5 25th: next A3-side — Q-C9 scenario (lines 284–291) two clicks on X6 event 81 (first shows the amulet line and stays, second enters XD-15), drop
  the stale ISSUE comment; Q-C22 checks a second knock enters 4647; `q-c9.yml` door hook's `where` → "the map shows this line and stays; the next click
  enters". Next G — Q-C9 "click the door with the amulet, then click again to enter"; Q-C22 drop the first-visit hint.
- Next decider batch: A5's two-click Sphinx door (X6 event 81) vs showing the line after arrival in XD-15 (A7's map) — A5's choice, cheap to undo.

- D-82 → next A3-promo (after A3 31st's reruns and MP35): the end-of-segment check + PARTY report in `promotions/run.py`, per-member asserts before
  hand-ins and class rounds, rerun from the new checkpoints. Next A3-side (after MP35): end-condition logs, per-member asserts, the `side_quest` tag.

- Next A7: XD-05's arrival line (`events/maps/xeen_xd05.lua` line 17 source) names Mayor Gunther — fix (G waits to drop its clause). Next A5: D3 event 93 also
  enters 4647 when qbit 112443 (`q-c22.moved`) is set. MM9 guide owner (user): `tools/mm9_site/capture_monsters.py` has the same pitch fault.

- (sent to A1 31st) `game/scenario/ScenarioYamlLoader.cpp` refuses MP33's new keys (`clear_hostiles` takes only `radius, min`; `walk_to` has no `clear_height`) —
  the PLAYBOOK documents both; then the waiting given item saved with the party; the app case.
- Next A3 (main): ending — confirm the cinematic doesn't leave turn-based mode on (Reviewer row 18); switch segment 77's Lua clears to the step keys once A1's loader takes `height`; apply D-82.

- Next A6 (optional): D1's Yog (actor 29, monster 11103) is in the Sardaj group 60, so the war route's "Battle!" kills him too — fits his line; change only if
  he's meant to survive. Next A3-side: Q-D10 mercenary-route scenario.

- Next A2 (records only): `source/monsters.yml` model/skin records for S 12th's changed families (S.md "Session 12: names and looks").
- Next S: Power Lich and Skeletal Lich (11284/85) their own recolours on a Xeen copy of `mm6_lch`; review G's recaptured portraits.
- D-81 → next A2: `balance.py` promotion-path gem rows count fixed choices (`alternative: true` gem gives, today `q-d27.wish_gems`); Q-C25 row 36 + 1 wish = +1,
  "pass (one gem wish)"; ledger note.

- MP33 follow-ups: **rerun all three test sets** (runner clears now storey-bound; loot changed): next A3 main chain 01–99 both modes; then A3-promo
  `--start` + both modes (drop segment 21's Clan Master ISSUE); A3-side 2nd told (Q-C1 natural, full runs). Next A7: close "XD-22's Clan Master
  dies alone" (runner's open_door clear). Next A8: rerun indoor playtests that used a clear < 5,000 if any fail. A2/A4 per D-80 (shops).

- From A3 29th (G's answers): next A5 — D3 event 93: enter house 4647 when `IsQBitSet(QBit(112443)) or XeenQuests.hook("q-c22.cottage")` (every knock after
  the first does nothing); X6 event 81's "The amulet grows warm..." never shows on arrival. Next A7 — XD-05's arrival line (event 1) drops "Mayor Gunther
  asked you to silence them". Orchestrator: QUESTS §2.2 Q-D7 name the four smith items (ask A3 for the names); M1 row done (D-78). QUESTS §4.2 safes done. Next A3: close G item 28 "final as built (D-78)".

- (sent to A3-side 2nd) README — close DD-20 "one way" (a live stalker, not the map; walk back with `clear_hostiles: 1500`, A8's probe
  `output/studio_cal/a8_s22/probe/dd20_back4.yml`) and DD-10A "a emerald" (fixed 14:26); `q-d20` comment + `prep/q-d20.md` wording; `prep/q-d7.md` line 25.
- D-77 → next A2: wording in `source/map_rows.yml` ~225, `source/monsters.yml` 11654 note, `lanes/A2.md` D7 ledger (16.9k for the party, 4.2k per member);
  next A3-side: four scenarios' `CONVENTION later-member` → `CLASSES test setup later-member …`, README bullet and cells, rerun; next A3-promo: 63, 69
  log form, README item 3 → D-77, rerun; next A3 (main): PLAYBOOK §2 test-setup bullet (with D-75's prerequisite bullet). G 2nd: item 23 answer (sent).

- From A3-side's final report: next A3-promo — segment 21's Clan Master ISSUE is the runner's `open_door()` kill (A1 fixing in MP33), not A7's map;
  `63_hobstadt_tribute.yml` comment still quotes "Troll Hole. Descend?". Next A3 — segment 49's comment about Snog/Alicia hidden on reload looks stale.
  Next A5 — `briefs/x6/L4/playtest.yml` comment: the sphinx-hoard mound has a fail text now. Next A7 — drop the XD-22 Clan Master item (runner cause).

- MP32 follow-ups: next A3 — keep segment 57's packs check or add `pick_up: {item_id: 12526}` to 59 after the topic; rerun 57 and 59 on 13:44. Next A2 —
  E14 `placed_names:` in `source/monsters.yml` (ids 401–499): Mr Wobbles, Mrs Wobbles, Gong Sentry, Schoolmistress, Goblin Warden, Orc Shaman, Tam; then
  next A7 uses `name:` on the placed indoor monsters. Next A1 — the headless `app` suite's `app_npc_granted_item_enters_held_cursor_slot` (fails since MP31
  or earlier); a waiting given item is not saved.

- Next A5 + A8 together (optional): D-42 (4)'s DD-19 return point on D3 (-10496, 22150, 1728) facing south (today (-10752, 22016) facing north); A5 moves
  `entrance:dd19_gate`, A8 rebuilds DD-19's exit Lua.

- (done) D-75 → rewrite segments 25 and 51's log lines to `CONVENTION prerequisite …; proven by <path>`,
  run.py check of each prerequisite line, README names D-75; Q-D14 and the `quarter` row (24/24); 66's line after D25-1; Q-D13's fight ending.
  → next A3 (main, after A3 28th): PLAYBOOK §2's `CONVENTION prerequisite` bullet (exact text in D-75). → next A2: Q-C25's 20 gems in the gem budget.

- MP31 follow-ups: next A8 recheck DD-09's playtests (the Barkman's chest stays shut until he wakes and dies); next A6 rerun P1–P4 tests (group 60 now
  really waits) and X5 waves 2/3 (groups 41/42; X5 is A6's); every L4 owner: 26 rooms on 17 projects get room step on low platforms at the next rebuild
  (`output/xeen_a1/mp31/room_step_tops.txt`).

- (sent) D-74 → A3-side (q-d13, q-d22, q-d23 per points 3–6), A3-promo 2nd session.
- Next A7: DD-11B's `sources: [platform:clay_heap]` no longer needed (MP31); XD-22's Clan Master (actor 2) dies by himself within 4 s of the armoury door (event 12) opening (A3-promo segment 21 ISSUE).

- Next A7: DD-02's `sound:tower_bed` → `pan: false` (D-48); rebuild/rebake.
- Next A8 (at next rebuilds): DD-17's 4 new `ride.no_switch` warnings on the bridge slabs (doors 2–5) and XD-11's 28 `textures.tile_seams` on `xwiron`
  (new with the 09:31 oymap) — fix or NOTES.
- Next AU: update AUDIO.md (all session-5 dungeon lines pasted; A8's still-panned list cleared, DD-02 left for A7).

- AU 5th paste round (AUDIO.md "Session 5 / The lines to paste"): A5 23rd and A6 26th sent. (sent to A8 21st) DD-17 trapdoor sound in
  `evt:trap_t1`–`t6` + klaxon cues at 5 s and 11.5 s; DD-15 `xeen_torch_light` on the four torch levers; DD-22 `xeen_pod_alarm` (loop, no wait) and
  `xeen_log_chirp`; DD-25 `xeen_forge_hall_loop`; DD-21 heart sound (off once `heart_found`); DD-26 tribbles; FD-01 `xeen_stasis_hum` (off with the
  field), shaft grit, optional groan; `pan: false` on the beds of DD-01, DD-02, DD-10A, DD-10B, DD-12, DD-18, XD-11, XD-12 and DD-19's court/hall/sanctum
  (DD-02 is A7's map — check owner). Next A3 (27th): `Xeen.toll` plays `xeen_bandit_whistle` (the Megadragon's sleep sound is already switched off by D7's events 80/81).

- (sent to S 11th) XD-17's fall from the lip itself is still a broad pale band with a straight near edge (`output/studio_cal/xd17/shots/s22_falls/sheet.jpg`).
- (sent to A6 24th) boulders, barges/boat, P1 re-shoot, D-72 buttons, cauldron note.
- D-72 → (sent to A5 22nd) before the next release: X6 80/83, X7 38/40 one Yes/No button prompt with description + source question (no SetMessage);
  playtests assert the question text. Next A6: buttons at next rebuilds on D6 33/95, D4 41/50/74 (74: hook first, no map message), D1 117/121; close
  A6.md next step 1. Next A3: (cancelled: D4 74's question shows under the hook's line with buttons — D-72's rule is met, A6's probe `output/studio_cal/a6/s24/d4_lair_probe.log`; keep the hook text); ORIGINAL_LINES ("Enter Strange Craft?" not used; "Enter the Mine?" row; "Enter
  Castle Xeen?" not shown; X6/X7 joined prompts). Next A1: one sentence in the studio `exit`/`into` docs (outdoor moves immediate; leave window only
  BLV→ODM).

- (sent to A8 19th) FD-01 polish per D-71: P1 ladder (separate rungs off the wall, no merging plate), P2 levers (pivot boss + arm; a rotating mover
  preferred), P3 rebake/reshoot (what is shot 27's pale blue shape?), the statue's later-click line in `playtest.yml` after A3's `else_text`,
  `playtest_in` after A6's D6; also DD-21 reload heal, DD-17 tours with a Soul Box entry.
- (sent to A3 27th) rerun segments 63, 67, 77, 87 (prompts now buttons: D1 121, D4 41, D6 33, D1 117); ORIGINAL_LINES for X6 80/83, X7 38/40 (A5's joined lines in its 22nd report: Basenji aaze0001:19, War Zone aaze0006:4, Volcano Cave
  aaze0017:1, Dragon Cave aaze0017:0) and X6 40 (aaze0001:0) / X7 22 (aaze0018:3); `hooks_d7.yml` for the hatch after m33.done (A6's `output/studio_cal/a6/s23/hooks_d7_fd01.yml` has the steps).
- Next A6: note in D4's NOTES the cauldron is a one-member gamble (D-70 rule 4, D-71).


- (sent to A8 19th) DD-21 `playtest_reload.yml` heal member 0 before `select_member` (`setup_shortcut: {kind: set_member_points, member_index: 0, health: 500}`) → 4/4;
  DD-17 tours with a proper Soul Box entry.
- Next A7: send A1 one current case each for the ladder-through-floor-hole and panel-covers-an-opening warnings.

- (sent to A6 21st, items 1–2) before FD-01's install: D7 `entrance:fd01_roof` at (−18688, 8448, 1536) facing 1024 (D-69 Q67); the ancient kit's `per_site` line
  for FD-01 (`swall4`/`swall2` on `swankdk`, `xahullbn`, no `swll5dk`, no red); re-shoot P1/P3. At FD-01's install: D7 regenerate (`LIVE['fd01']`),
  D6 drop `DUNGEON['fd01'] = False`. With A3 dropping `q-d26.hatch`'s m33.done "gone" state at the same time.

- (sent to A6 21st) re-shoot P1 and P3; P4 water fog after MP29; X5's Earth Reflector (event 119) lacks the "Reflector. Activate?" Yes/No; join message + question into one button prompt (D-66 item 6).
- (sent to A7 21st) XD-02 `exit:x4_adit` → `entrance:xd02_adit` (19968, -15872, 1504) facing 1024 (or keep its point) and update `playtest_x4.yml`; XD-26 `exit:x4_peak` keeps its raw point (ledge centre, A5); check XD-19's gem tray really gives its emeralds (a probe's `GiveItem(183)` on X3 added none; unconfirmed).
- FD-01 built → A3: M39–M41 and the ending in the chain.

- (sent to A5 19th) regenerate X1's walk (XD-05's exit to `entrance:xd05_mouth`, 06:51); answer A7: XD-26's `exit:x4_peak` → X4's
  `entrance:xd26_sky_crack` (-7680, 14848, 3648)? XD-02's `exit:x4_adit` → X4's `entrance:xd02_adit` (20480, -15872, 1504) facing 0 (east, into
  the adit — meant?); XD-17 waterfall when S installs it.

- Next A4: Cyrano's door check (`door:pets_unlimited`, event 12) on the installed DD-26 (06:47).

- MP27 rebuilds (peaceful groups once per fill; only generated Lua changes): A6 D1, D4–D7, X5 (done); A7 19th (done), A5 18th (sent); A8 15th (done).

- (sent to A2 17th) row 11919 (Dragon Pharaoh) collision height 160 → ~230 (S); row 9170 (DD-17) perception back to 15; row 9157 (DD-08) slot `{monster: Xeen Dark Knight, tier: 0, per_marker: [1, 2], weight: 100}`,
  encounter 10, 15/8/15; check music 43 against the card.
- D-66 → S: name a shipped throne (DD-08, DD-17) and DD-17's teal statue — before those maps count as done. Next S batch also: DD-08's thrones (xdthrone blocks stand in) and 11925's look; a knight statue (founder now MM7 `7dec55`); DD-17's
  propaganda statue and Sheltem's look; DD-15 an Egyptian statue decoration.
- Next AU: DD-17's trapdoor clang and klaxon; DD-15's torch, pad and vat sounds (stand-ins now).
- A8 14th installs DD-26 (resumed) → next A6: D7 grate event 104 "Descend into the sewer?" → `entrance:d7_stair`).
- (done by A6 19th) D6 `door:dd22` → `{map: xeen_dd22.blv, arrival: entrance:d6_hatch}` after `d6.sheltem_hatch`/`m33.done` (lift `DUNGEON['dd22']`); D7 grate
  once DD-26 installs; D5 boulder when S has it.
- (sent to A3 25th) segment 79 on (M34, the Cube, M35–M41); hooks_dd26; P5 + sky_map_spells + ending once P5 installs; Cyrano's `ask:` to
  buttons once A1 lands them; rerun 69+ after D5/D6/D7/DD-15/16/17 reinstalls. Also: DD-22 lines map-local (arrival, "The blast door stands open.", couch, cells, generator); DD-26 "Cyrano sells the password." hover,
  "A voice waits behind the grille.", "Climb up to Olympus" — move into quest files if wanted; DD-17's joined lines (A8 15th lists them).
- Next AU: DD-22's alarm `buzzer01` and log chirp `tone2` picked without listening.
- Next A8 (optional): DD-18's exit to `entrance:dd18_shaft` instead of the raw point 512 south of the lid.
- D-66 → next A6: re-tone `xdpyrflr` only if A8 asks.

- Next S batch also: dwarf bodies for the Peasant Dwarves (322, 313, 325, 316) and the 11054 guards' recolour; optional better jar and
  statuette for DD-21 (now `dec97` + green light, `7dec54`).
- Next A4: Ormond's autonote is 4571 (`q-d17.answers`); his topic lives in `q-d17.yml`.
- Next S batch: the planes' pieces at their L1 spots (statues, sleeper and couch — P3's `m38.sleeper_earth` needs it to set 111762 — pedestals, dais, P3's dust column, P4's bell); P4's octopods start on the sea bed at -1,024 — check the swimmer binding rises to the surface; FD-04's lizard and dragon-egg decoration names (`S_LIZARD`/`S_EGG` in `output/studio_cal/fd04/tools/gen.py`); a chair or lectern decoration (FD-02 polish; A7 built a wooden throne); indoor binding of `xeen_lavafall`; the planes' statues, sleeper and couch, pedestal, dais, font, camp, way-up column; D7's
  barges, celestial boat, lamps.

- A5 opens X7's XD-18 mouth → A4 writes Scaldrith's trainer place. A7 installs FD-04 → A4 runs FD-04's loop.

- (sent to A7 20th) P5 installed → FD-03 drops `p5_open`, hatch Yes/No (D-66), exit to X5's `entrance:fd03_door` by name; DD-06/07 roofs at next rebuild.
- Next A4 (D-58): `d7.yml`'s 13 doors and mirror as drawn; `olympus_square` (-4608, 6400, 1792), `olympus_dock` (-640, 3200, 1792); no
  vendor houses. Next AU (D-58): D7 wind bed, corner hums, Megadragon/cloud-dragon calls, bandits' whistle, per-plane beds — budget!

- Next A6: rerun D6's walk (A2 already rewrote edge_spans for D1's moved north_road at 03:0x — check).

- (sent to A4 13th) Roland 4405's greetings are the impostor's ("Still here? How loyal."); add greetings for after `m35.done` (real Roland at
  court and on P5).

- A5 asks before installing P5 → orchestrator adds `xeen_p5.blv` to openAirMaps (under the terrain lock).
- MP24 out: next A5 reruns `playtest_lake_dragons*` and the falls on MP24, rechecks the certificate in a visible P5 run (fade
  `color`, certificate wait in); next A7: DD-13 hides as `cover` panels, embers on `dec24x`; MP25 (fresh A1): hidden chest
  (`hidden: true` on a chest, `{hide|show: chest:x}`) → A5 swaps P5's raised block.
- A8 reinstalls DD-14 with Ambrose/Queen → A3 (segment 61 fly-out by topic, 67 Queen by actor). DD-15 installed → A3 segment 69 (M28).
  A8's phase-5 graphs (DD-15 first) → a decider.
- S: Pegasus decoration row → A8 (DD-05); Enchanted Boulder (row 4014) → A6 (D5); xeen_waterfall → A5 (XD-17); octopod D, Ambrose,
  Queen bindings → A8 (DD-14); elemental, People, Corak, Slick, Lacey, Stumpy, archers, griffin bindings → A2/A7/A6/A5 as named.
- Next AU: P5's four far chimes and the wedding fanfare for `unification` (D-56); D5 Barrier hum points (48.7, 26.05), (57.7, 31.2), (66.7, 33.7), (75.7, 34.2), (84.7, 32.2), (93.7, 28.2); the hold's fire
  (86.5, 46.5); check the re-pasted `pan: false` beds from assets_dev. Budget: 6,250 credits uncommitted — a larger batch needs the user.
- Orchestrator: edit world.yml only under `flock output/studio_cal/a5/locks/terrain.lock`.
- Later: D-38 voiced lines in DD-17 (A8).

Sent:

- A6's report → A7 15th (exits), A2 10th (travel rows), A1 19th (topic map name, outdoor translucent), A4 (D6 loop), A8 (D5/D6
  points, xlsgate), A3 (xd17_pyramid), A5 (xd17_pyramid, terrain_swap world.yml), S (boulder rings).
- D-52 → A2 (fresh 9th), A8, A4, A6, S. MP21 → A7 (XD-19 filter, cinematic leave, DD-13 words), A8 (facing, DD-20 move), A2
  (SlayingDemon), A6 (crust confirmed, beds coming); A1 18th and AU 4th started.
- A8 → A6 (D4 DD-12 door, griffin points), A3 (qbits, segment 57), A4 (Ambrose direct), S (octopod, birds); D-52 started.
  A3 → A6 (D5 qbit fixes, D5/D6 wiring, X8 runes, xd17_pyramid point), A5 (X9/XD-17 wiring), A7 (XD-07 Book of Languages).
- D-51 + D-50 → A7 (fresh 14th), A5 (fresh 14th, with A7's measured XD-19 shell), A4 (fresh 12th), A2, A3, A6, S, A1, A8.
- A7 → A6 (DD-16/DD-24 arrivals, xdgiantd/xdthrone), A1 (exit facing bug, global hook option, actor index, cinematic cues),
  A2 (L4 values), A3 (qbits 118080, 118060–118063, ledger rows, skull text). D-51 started on A7's DECIDE items.
- A5 → D-50 started; A7 (XD-20 facings, XD-16/17 names, XD-19 footprint), A6 (X7 lvdr basalt rule), A1 (stray mp20 logs). A7's
  installs → A5 (X7 door), A6 (D5/D6 return points), A1 (MonsterDamage hook word), A3 (XD-16 qbits), S (xeen_guard first).
- D-49 → A6 (fresh 13th session), A2, A3, S, A1, A7, A8 (phase-5 arrivals noted for later).
- A6 → A5 (D3 `below_deg` 1.5, reshoot), A7 (confirm D5 return point (86, 43) facing south); A3 15th session started with A6's
  tower_rope request and AU's cues.
- AU → A5, A6 (paste bed blocks), A1 (random start/pan pending D-48), A7 (XD-19/DD-16 sound wiring).
- D-47 → A7 (fresh 13th session), A2 (rows + DD-05/DD-20 recount), A3, A5, A6, S, AU, A1.
- A8 DD-05/DD-20 → A6 (D1 doors, D4 doors, plan facings, guild_wrong move), A3 (hooks, guild_wrong, trapdoor line), S (Pegasus
  decoration row), A1 (facing assert; DD-20→D4 MoveToMap headless).
- Merge point 20 → A6 (`below_deg`, D4 captures), A5 (X6 sand-fall loop), AU started.
- A2 row 9121 → A7 (XD-20 passes from assets_dev; drop root_s6's row), A5 (X6 door, sand worm sizes); A2 → A3 (full
  build_world write when quest sources are done); A2 → S (armadillo size wanted).

## Deciders

Next number: **D-83**.

| D | Agent id | Question | Answer file | State |
| --- | --- | --- | --- | --- |
| D-51 | a9461ea3e85cdd0a7 | A7's Act V follow-ups: Corak before waking, XD-16 trap tell, XD-19 choices, xdthrone colour | `mockups/act5_a7_followups_d51.md` | answered; recorded (D-47 Q20 note), relayed |
| D-63 | a084137fc7b5d9492 | A7's phase-6 build choices (14 items) | `mockups/act6_a7_followups_d63.md` | answered; recorded, relayed |
| D-66 | aff77833e946257b0 | A8's DD-15, DD-17, DD-08 build choices + DD-15 floor glare | `mockups/act5_a8_followups_d66.md` | answered; recorded, relayed |
| D-67 | ac9db2b9d80e814e2 | A8's DD-22, DD-26 build choices + body fit check | `mockups/act6_a8_followups_d67.md` | answered; recorded; A8 14th resumed |
| D-68 | aa1eb9c94b0a71c1c | playthrough stat gates (A3) + DD-26 reach step (A8) | `reviews/D68_DECISION.md` | answered; recorded, relayed (A3 26th, A2 18th, A8 17th) |
| D-69 | a880cb4b4b7a2b2d1 | FD-01 graph Q63–Q72 | `mockups/act6_fd01_decisions.md` | answered; recorded (MAPS, QUESTS, MONSTERS_AND_ITEMS, maps.yml), relayed |
| D-70 | ac322e0eba73ba9c5 | M34 Accuracy 60; unguarded temporary wells (X4, D2, D3) | `reviews/D70_DECISION.md` | answered; recorded, relayed (A3 26th, A5 21st, A6 22nd; A2 queued) |
| D-71 | a1be1df2b6747a80c | FD-01 build choices 1–5 + polish; D4 cauldron single drinker | `mockups/act6_fd01_followups_d71.md` | answered; recorded, relayed |
| D-72 | a5d34718d4893e85b | do D6's hatches into BLVs ask (D-24 vs D-66)? | `reviews/D72_DECISION.md` | answered; recorded, relayed |
| D-73 | adebc22dd856b3a3d | teacher order: Dodging/Unarmed M before E, Identify Item GM before M, early GMs at the wizard quarter, town loads, liberation gates | `reviews/D73_DECISION.md` | answered; recorded; A4 16th started |
| D-74 | a7f71cb8b4d662f4a | promote later members (t2-later.yml), Light/Dark crossing, Necromancer text | `reviews/D74_DECISION.md` | answered; recorded, relayed (A3-side), A3-promo 2nd started |
| D-75 | a1611d99651c786a7 | prerequisite qbits as CONVENTION in branch chains (q-c15.done, m20.started, tax gems) | `reviews/D75_DECISION.md` | answered; recorded; queued for A3-promo 3rd, A3 (PLAYBOOK), A2 |
| D-76 | a105fdde41238a78f | the guide: show uncertainty? hide spoilers? | `reviews/D76_DECISION.md` | answered; recorded; G 2nd started |
| D-77 | af1d7ad11b0af5691 | Megadragon XP (party vs per member); later-member stand-in tag | `reviews/D77_DECISION.md` | answered; recorded; D-58 note; relays queued/sent |
| D-78 | a3eb716233aa84c5d | M1's pest kill count (strike from QUESTS or build) | `reviews/D78_DECISION.md` | answered; QUESTS M1 row edited |
| D-79 | a624a6e34c1803023 | guide map points: keep in-game clue texts that spell a non-typed solution? | `reviews/D79_DECISION.md` | answered; recorded; G 3rd started |
| D-80 | a4bd31c96481ec095 | MM9-loot setting in Xeen; enchanted MM6–MM8 stock in Xeen shops | `reviews/D80_DECISION.md` | answered; A1 30th, A2 21st started; G 3rd told |
| D-81 | a31e76d529bf37c3a | Q-C25's 20-gem tax short 9 on fixed gems (accept / place gems / lower tax) | `reviews/D81_DECISION.md` | answered; A2 queued |
| D-82 | aa8497a26b07f2c33 | should the chains assert party health (Dead/Eradicated/Petrified)? | `reviews/D82_DECISION.md` | answered; A1 31st told; A3 31st started; A3-promo/A3-side queued |
| D-65 | abde0e19781725c8a | A8: DD-26 graph Q56–Q62 + four build notes (DD-21, DD-25) | `mockups/act6_a8_decisions.md` | answered; recorded (MAPS, QUESTS, D-62 note), relayed |
| D-64 | a1efb96333c20e9bf | A6: P2's gate as a wind curtain | `reviews/D64_DECISION.md` | answered (curtain stays); recorded, relayed |
| D-62 | a123db176810c028d | A8's graphs DD-25, DD-21, DD-10C, DD-22 (Q32–Q55) | `mockups/act5_a8_decisions_b.md` | answered; recorded (MAPS), relayed |
| D-61 | a5423e646153484ba | A8's phase-5 graphs DD-15, DD-17, DD-08 (Q1–Q31) | `mockups/act5_a8_decisions.md` | answered; recorded (MAPS, D-58 note), relayed |
| D-60 | af2274f6bc9bae9ab | A2: Act IV quest XP 1.122 past D-53's 1.12 trigger | `reviews/D60_DECISION.md` | answered (accept; Act IV closed at 179.5k); recorded |
| D-59 | aa194e49c1d54bc23 | A2: X9 Dragon Clouds device sizes | `reviews/D59_DECISION.md` | answered; recorded, relayed |
| D-58 | aaccbaaac970f8972 | A6's D7 and P1–P4 L1s (D7 Q1–Q10, planes C1–C8 + per plane) | `briefs/d7/L1/D58_DECISION.md` | answered; recorded (MAPS, MONSTERS_AND_ITEMS), relayed |
| D-57 | adf352a79c70fe994 | A7's phase-6 graphs XD-18, FD-02, FD-03, FD-04 (Q1–Q37) | `mockups/act6_a7_decisions.md` | answered; recorded (MAPS, MONSTERS_AND_ITEMS), relayed |
| D-56 | afcd0abd279eb406a | A5's P5 Clouds of the Ancients L1 (10 questions) | `briefs/p5/L1/D56_DECISION.md` | answered; recorded, MAPS edited, relayed |
| D-55 | a1fdb617cc22bbff1 | A6: night glow invisible with Surface materials off (default) | `reviews/D55_DECISION.md` | answered; recorded, relayed to A1 |
| D-54 | af2f7de3dc6e9a99b | A5: X9 fall landing next to X2's trap dragons | `reviews/D54_DECISION.md` | answered; recorded (D-50 note), relayed |
| D-53 | a90c86929c1587304 | A2: Act V quest XP 1.13 (1.19 with every lamp wish as XP) | `reviews/D53_DECISION.md` | answered; recorded, MAPS + WORLD_DESIGN edited; A3/A2 pending (both stopped) |
| D-52 | adf7c83046d2c5e84 | A8's DD-12/DD-14 items | `mockups/act4_a8_followups_d52.md` | answered; recorded, relayed |
| D-50 | aa62451d8144d3ce7 | A5's X9 and XD-17 L1s (8 + 9), D3's signature camera | `briefs/x9/L1/D50_DECISION.md` | answered; recorded, MAPS + WORLD_DESIGN edited, relayed |
| D-49 | a69adeb62eea8cb7c | A6's D5 and D6 L1 mock-ups (8 + 8 questions) | `briefs/d5/L1/D49_DECISION.md` | answered; recorded, MAPS edited, relayed |
| D-48 | a10ba0b627d684d17 | AU: pan outdoor beds? (a) world-wide off, (b) per-sound `pan: false`, (c) keep; random loop start | `reviews/D48_DECISION.md` | answered (b) + random start; recorded, relayed |
| D-47 | ad67d8c9b9822449f | A7's Act V graphs XD-16, XD-19, DD-16, DD-24 (Q1–Q26) | `mockups/act5_a7_decisions.md` | answered; recorded, MAPS edited, relayed |

## Log

- 23:30 Eight lanes started with the handover's §4 work and §4.1 relays in their briefs.
- A2 stopped: row 9121, sand worm bodies, DD-05/DD-20 slots confirmed. Relays sent.
- A7 page `mockups/act5_dungeon_graphs_a7.md` done (Q1–Q26); XD-20 4/4 from assets_dev; decider D-47 started; A7 resumed.
- A7 stopped: XD-01 back to 46 textures (installed, baked, 4/4); `xosoot` was registered in session 6 (no relay).
- A1 released merge point 20 (23:40:17); relayed; AU started; A1 resumed.
- A8 stopped: DD-05, DD-20 installed and baked, 4/4; polish 1 pictures good. Relays sent; A8 resumed.
- D-47 answered (all four approved with changes; Q12 E11 on the map damage hook; Q23 People 38/50/58). Saved, DECISIONS row, MAPS rows; relayed to eight lanes; A7 13th session started.
- A2 stopped: D-47 rows (9142/9144/9169/9177, elementals, People, Corak 11912), Lord Xeen HP, sword keep; recounts 1.04/1.03. Relayed to A3 (113323, quest XP over budget), A7, S, A1.
- A3 stopped: DD-05 qbits, sundial helper (`Xeen.alamarSundial`), x7.idols text, guild_wrong move, all D-47 hooks, 18 side quests pass. Relayed to A6, A8, A7.
- AU stopped: 130 bed entries for 10 maps, desert/Darkside beds redone, D-47 sounds; 23.0k charged / 79.4k committed of 100k. D-48 (panning) started.
- D-48 answered: per-sound `pan: false`, random loop start in all worlds. Relayed to A1, A5, A6.
- A6 stopped (~387k): D5/D6 L1 → D-49 started; D1 (DD-05) and D4 (DD-20) unsealed; AU beds in X5, D1, D2, D4; rim glow 1.5 on D3/D4. A3 15th session started.
- D-49 answered (D5/D6 approved with changes). Saved, DECISIONS row, MAPS rows (bands 30–62, 30–75; Lucio, Freeda out); A6 13th session; relayed.
- A5 reported: idols on X7, X6's XD-20 door and sand-fall, beds on 6 maps, X9/XD-17 L1s → D-50. A7 (state file): DD-16, DD-24, XD-16 installed; XD-19 waits on xeen_guard and a MonsterDamage hook word.
- A7 ended (~495k): three Act V maps installed, XD-19 in root. D-51 started.
- A2 stopped: D5/D6 rows 9112/9113, archers 11104/11105, Tethered Griffin 11913, Last Water +2 Luck, one-route quest XP (Act V 195k of 209k). D6 music settled 11 (MUSIC.md). Relayed to A6, A3, S.
- A5 ended (~374k): X7 door into XD-16 live (00:37). Fresh A5 waits on D-50.
- D-51 answered (Corak in a translucent field, unkillable now; XD-19 blocked on A1, seven textures required; xdthrone redo). D-50 answered (X9, XD-17 approved with changes; D3 keeps its camera + rim_glow view). Recorded; MAPS, WORLD_DESIGN edited; A7, A5, A4 fresh sessions started; relays sent. Note: D-50 assumed a 7,168 × 6,656 XD-19 shell, A7 measured ~10,240 × 10,080: A7 restates, A5 told A7's figure wins.
- A2 stopped (~308k): X9 9107, XD-17 9120, Slick/Lacey/Stumpy 11914–11916; quest XP 1.08 with well kept at 20k. Relayed A3, S, A1 (wander radius, low).
- world.yml `openAirMaps` += xeen_x9.blv, xeen_xd17.blv (A5's request; rows exist; validate-actor-models passes). Slick binding name already matches.
- A8: DD-12, DD-14 installed; DD-20 trapdoor fixed; D-52 started on its DECIDE. A3: Q-D6/Q-D22 scenarios, all D-49/D-50/D-51 hooks, qbits; relays sent. Note: an A8 sub-agent deleted and recreated an empty /tmp/x it did not create (reminded A8).
- A3 ended (~393k). Fresh A3 waits on A6's D4 rebuild.
- A4 stopped: XD-17 doors renamed, `#` check in towns.py, D6 Ambrose/Necropolis confirmed, D3 stables confirmed, reinstalls checked. Relayed to A1 (same-map ride dialog regression), A5, A6, A8.
- D-52 answered and recorded. A1 released merge point 21 (00:57:49) and ended (~433k); A1 18th, AU 4th started; relays sent.
- A6: D4 reinstalled 00:57 (DD-12 Isle door, Blackfang griffin), X8 rhymes gated, X7 crag fix in terrain materials. A4 done incl. D-52. A3 16th started for segment 57.
- A7 stopped (~361k): DD-16, DD-24, XD-07 reinstalled; XD-19 complete in its root (seven textures, sword rule), waits on xeen_guard. Relayed A6 (textures), A5 (XD-19 measured shell), A2 (Lord Xeen 66 blows). Note: scratch roots with old tables fail to load Xeen maps after the openAirMaps change until refreshed (`output/studio_cal/a7/refresh_tables.py <root>`).
- A2 stopped: D-52 rows, monster kinds (73 rows), Slayer Sword SlayingDemon, Lord Xeen 2,200 HP; D5 installed 01:08 (A6) and its travel rows. D-53 started on quest XP. Relayed S, A8.
- D-53 answered: well 15,000, wish 2,000; counted 1.11, most-experience 1.15. Recorded.
- AU stopped: `pan: false` bed lists, indoor bed list, D5/D6/X9/XD-17 lists, 7 new sounds. ElevenLabs 93.75k of 100k committed: tell the user (a larger batch needs a budget decision). Relayed A5, A6, A8, A3.
- A1 released merge point 22 (01:40:33) and ended (~401k). Relayed A5 (npc word for Lacey/Stumpy), A8 (npc word, trapdoor word).
- A6 ended (~440k): D5 and D6 installed with bakes (D-49/50/52), robots placed not markers (for the m33 hide). A7 15th, A2 10th, A1 19th started; A4 resumed.
- A4 stopped: D6 (11 houses, mirror, Town Portal, trainers) and D5 town files built; six planned shops' qualities moved to engine rows (towns.py checks them now). A4's ferry note predates merge point 22's fix.
- A5 (message): X9 installed 01:29, XD-17 01:45:34. Relayed A4 (town loop), A7 (XD-16/XD-19 exits), A8 (XD-12 roof exit), A3 (hooks in game), A2 (recount).
- A3 16th: segments 57, 59, 61 pass (normal + reload); Q-D16 scenario; D-52/D-53 applied; D6 travel rows written. Relayed A1 (ferry still open?, DD-12 load step bug, topic map name not needed), A8, A7, A2, A4.
- A5 ended (~330k): X9, XD-17 installed; X7 cleft open; six maps' beds pan: false; terrain_swap.sh copies back only tool-written files. D-54 started on the X2 landing. A6 14th started. A3 ended (~401k).
- A2 stopped: D-53 line and recount (1.11 / 1.15), Lacey wander, six named edge arrivals walked. XD-17 treasure: keep maps.yml's "-" (0; D-50 gives XD-17 no chests) — tell A5 to align its card. A4 told of the gen_towns failure. A3 17th started.
- A4 stopped: XD-17 town built (15 houses, 8 trainers), Grave Market at 4 (full --check clean but xeen_quests.lua), route place names staged for A1's Name column.
- D-54 answered: landing kept; dragons moved + leashed; rule 5,888. Recorded (D-50 note, D-6.4 marked). A5 15th started; A6 told to retest X8's fall.
- A6 stopped: registry 156/450; Alamar/Barrier night glow via surface maps; D6 reinstalled 02:04 (adit, flight, both edges); X8 fall 2/2 after A5's X2 (01:57:57). D-55 started on night glow with surface materials off.
- A3 stopped: Act IV main line through segment 67 (normal + reload), X9/XD-17 and D5/D6 hook scenarios with amounts. A8 told phase-5 graphs (DD-15 first) are the critical path.
- D-55 answered: per-world glow default field, Xeen only. Relayed to A1.
- A7 stopped: phase 5 complete — XD-19 installed with bake 02:07 (gate + scepter leave to X9), DD-24/DD-16/XD-16 exits live, DD-13 trapdoors (sign right, open-at-load works), NPCs talk. Relayed A5 (X9 gate), A1 (cover panel, audit global, dec24x).
- A5 stopped: X2 dragons moved/leashed (D-54; lake_dragons 2/2), X9 falls with HP checks, X9's gate into XD-19 live 02:16, P5 L1 → D-56. A1 told: leashed flyers leave their circle.
- A1 released merge point 23 (02:31:45) and ended (~471k); A1 20th started for merge point 24; A4 resumed for route names. D-55's field is `surfaceGlowContent: true` (add after MP24).
- 02:35: A7 16th (phase-6 graphs) and A6 15th (D5 Barrier, D6/D1 fixes, phase-6 L1s) started on a quiet machine.
- A4 stopped: route names live ("the Isle of Lost Souls", "Lakeside"), --check clean. Its GetCurrentMapName note is stale (A3's onMap change + MP23 confirmed Ambrose's topics work).
- D-56 answered (P5 approved with changes) and recorded; A5 16th, A2 11th, A3 18th started; A4 resumed for the certificate; A6, A7, A8, S, A1 relayed. A8 checked by its files: DD-19 installed 01:33, DD-14 rebuild in progress.
- A2 stopped: P5 row 9119 + figures 11919–11921; every Act V map with kills installed, Act V 1.03. xafield.png missing → D6/DD-16 bakes stale: told A6.
- S never reported since 23:30; relayed its done items from S.md (Pegasus 4012 → A8, octopod D/Ambrose/Queen → A8, sphinxes 4010/4011 → A5, genie lamp 4013 → A6); asked S to stop and report at its next safe point.
- A4 stopped: certificate art `xeenwinbg` + ending text; orchestrator added the `completion` block to world.yml under the terrain lock (backup output/xeen_o3/world.yml.bak_cert); world loads. Looked at the in-game capture: clean.
- A3 stopped: segments 57/59 clean on MP23, M42 written (cinematic done event 42149), Town Portal/Lloyd checked on sky maps. Relayed A5 (P5 wiring, p5_fall at (-4608, 2560, 1504)); A2 resumed for edge_spans + S's sizes.
- A2 stopped: edge_spans (D6→D1 moved arrival), S's collision bodies applied. DD-16's bake still stale: xafield is now cooked as .oytex (A6's soft-alpha recut at 02:35), the bake recorded the .png path — A6 already told; A7/A6 re-bake DD-16.
- A7 stopped: XD-19 re-baked 02:39 with ActorIndex; phase-6 graphs for XD-18, FD-02, FD-03, FD-04 (258.6k of 249.8k, +3.5 %) → D-57 started.
- A5 stopped: P5 built in scratch (20/20), blocked on FD-03 (D-57), S's Pharaoh and five decorations; X6 sphinxes in (02:51). Relayed A6 (12 textures), A1 (chest show by event, certificate closes the ceremony text), S.
- A1 released merge point 24 (03:13:18). Orchestrator added `surfaceGlowContent: true` to world.yml under the terrain lock (backup output/xeen_o3/world.yml.bak_glow); world loads, edge_spans passes. Relayed A6 (recaptures), A8 (attacked condition).
- D-57 answered (A7's phase-6 graphs approved with changes; rest 0 on all four; X9 Dragon Clouds take Q-F1). Recorded; A7 17th, A2 12th, A3 19th, A5 17th, A4 13th started; A6, A8, S relayed.
- A6 stopped (~374k): D5 Barrier translucent (dark at night: A1), DD-16 rebaked, D1/D6/X5 reinstalled, D-55 recaptures fine, P5 textures registered; D7/P1–P4 L1 → D-58. A1 21st started (MP25).
- A4 stopped: Alister 5705, Roland greet_after. **The Xeen world failed to load (~03:19–03:29): A2 renamed 11284/11285 to Xeen Lich D/E, S's actors.yml still bound the old names. Orchestrator hot-fixed the two descriptor lines in actors.yml (S's file; backup output/xeen_o3/actors.yml.bak_lich); loads, edge_spans passes.** Told S, A2; relayed A4's items to A3.
- A2 stopped: D-57 rows (9143, 9180–9182), tiers, Picard 11922, Alister 11923, items 12375/12376/12505, Act VI recount 1.01. D-59 on X9 device sizes started. Relayed S, A3, A7, A8.
- D-58 answered (D7, P1–P4 approved with changes); recorded; A6 16th and A2 13th started; A3, A7, A8, A5, S relayed.
- D-59 answered (balls Int 60, well +20 until rest daily, crystals 3k/4k/5k); balance.py gap found (quest-file AddValue not counted). Relayed A2, A3, A5.
- A3 19th stopped (~393k): D-57/D-59 quest side, Roland greeting switch, planes' tests and hazards, corners. A3 20th started for D-58's rest. Relayed A7, A5, A6, A2.
- world.yml openAirMaps += xeen_d7, xeen_p1–p4 (A6's request; rows exist; loads, edge_spans passes; backup world.yml.bak_openair2). A2 stopped (D-58 rows, recount: Act IV 1.122, optional 1.10). D-60 started. Relayed A6, A3 (D5 fall point, scarab prices, gem items, ids), S.
- D-60 answered: Act IV 1.122 accepted, Act IV closed at 179.5k. Recorded (DECISIONS, STATUS); A2's note queued for its next session.
- A1 released merge point 25 (03:57:50) and ended (~391k). Its DECIDE (currents carrying monsters) answered from D-58 without a decider (P4's currents push the party only). Relayed A6, A7.
- A3 20th stopped: all D-58 quest hooks; relayed A6 (D7 wiring), A8 and A7 (roof hook names).
- A8's DD-14 helper looked stalled (no files since 00:52); A8 9th told to finish DD-14 only; A8 10th started on the phase-5 graphs (critical path).
- A7 interim: FD-02 installed 04:00 (20/20), FD-03 04:10 (16/16), DD-13 cover panels + embers 03:28. Relayed A6 (X5 door, 5 textures), S (bindings missing for FD-02/FD-03 actors). A5 items queued for its next session.
- A8 10th stopped (~349k): page with DD-15, DD-17, DD-08 (Q1–Q31) → D-61 started.
- A7 interim: XD-18 built in scratch, blocked on A4's town data (A4 resumed). A5's X7 door queued.
- A4 stopped: XD-18 town data in (A7 told to install), D7 door ids aligned. A4's lich-binding note is stale (fixed 03:29).
- D-61 answered and recorded; A8 12th (DD-15 build), A2 14th, A3 21st started; A6, S, A4 relayed. A7: XD-18 installed 04:33 (20/20).
- A4 stopped: XD-18 town loop passes (trainer place waits on X7), FD-04 town data ready, Ormond's topic for A3. Relayed A3, A7.
- A8 11th stopped: graphs DD-25, DD-21, DD-10C, DD-22 → D-62 started.
- A2 stopped: D-61 rows, Sheltem 11924, Voweless 11925, faction split, D-60 in balance.py. Relayed S, A8 12th.
- A3 21st failed on an API content-filter error mid-session (request id req_011ChFPDAndqUH9pnVEQ1H3B); nothing written; A3 22nd started with the same brief.
- D-62 answered and recorded; A8 13th (DD-10C, DD-25, DD-21, DD-26 graph) and A2 15th started; A3, A6, S, A4 relayed. Machine: 66 GB free, load 12.
- A4 stopped: Bosco greet 5407 (A3 adds the switch), DD-25 residences.
- A7 stopped: phase 6 complete (FD-02, FD-03, XD-18, FD-04 installed; DD-13 polish; DD-06/07 roof stairs). D-63 on its cheaper choices. Kept xeen_d7/p1–p4 in openAirMaps (MP25 headless passes). Relayed A6, A3; A5 17th told to wrap up.
- A2 stopped (D-62 rows). maps.yml monster texts for DD-08, DD-21, DD-22, DD-26 updated by the orchestrator; --check clean. D7 and P1 are installed (A6, per A2's recount).
- 05:00 S checked by its files: FD-02 mummies, FD-03 golems and Picard now bound (actors.yml 04:44); world validates. S never reaches a report because relays keep resuming it: batch S's relays from now on.
- A6 16th ended (~444k): D7 installed 04:53, P1 04:56; surface falls on D1/D2/D4/D5/D6; registry 185/450. D-64 (P2 gate), A6 17th (P2–P4), A1 22nd (MP26) started; A3, A8 12th and 13th relayed.
- D-63 answered (11 of 14 accepted; tax throw and shrine to `leave`; FD-03 rows verbatim; FD-02 blades and chair before done). A7 18th started; A3 relayed.
- D-64 answered: P2's wind curtain accepted with flow and opacity tuning. Relayed A6.
- A3 22nd stopped: D-61/D-62/D-63 texts and hooks; DD-14 reinstalled with Ambrose and the Queen (A8 9th) — segments 61/67 use them, 61–67 pass normal and --reload. Relayed A8 12th/13th, A6.
- A1 released merge point 26 (05:26:19): fall-landing fix in shared code (MM6–MM8 behaviour change: ~1 in 11 outdoor falls now damage — flagged to the user). Relayed A6, A3, A7; A5's X9 tests queued.
- A7 18th stopped: D-63 changes on eight maps installed 05:16–05:22, 160/160 from assets_dev; DD-06/07 roofs up to D7 live; DD-16 exit by name; XD-16 trap smoke. FD-02 throne built from wood blocks (no shipped chair).
- A6 17th stopped: all four planes installed (P2 05:15, P4 05:37, P3 05:42); D6 reinstalled (DD-10C adit); D7 falls re-measured after MP26; registry 192/450.
- A8 13th stopped: DD-10C and DD-21 installed; DD-25 built, waiting on A4's rows (A4 resumed); DD-26 graph → D-65. Note: A8's slot.sh queue process is gone; A8 sessions use their own game.lock.
- A4 stopped: DD-25 rows written; A8 13th resumed to install DD-25. A4's notes call FD-04 and D7 not installed — both are (04:52, 04:53): tell A4 next session.
- A3 23rd stopped: D7, FD-02/03/04, XD-18, X9 hooks pass in game; segment 69 (M28) passes with a D5-door workaround. A6 18th (doors) and A1 23rd (MP27) started; A8 12th told DD-17's cinematics file is missing.
- A8 13th stopped: DD-25 installed 05:48 (4/4, audit 0). A6 18th told to open D5's door.
- D-65 answered and recorded; A8 14th (DD-26, DD-22), A2 16th (recount), A4 14th (dd26.yml, loops), A3 24th (q-d28, segments) started.
- A2 16th stopped: Acts V and VI at 1.03 installed, quest XP under every trigger. maps.yml DD-26 text updated (orchestrator). XD-17 treasure "-" vs card 1: left (no chests). Asked A8 12th about DD-17 perception 5 and the cinematics file.
- A4 14th stopped: Olympus town live (D7), DD-25/FD-04 loops done, Cyrano planned. Relayed A8 14th (door name), A3 24th (Cyrano 5614; gen_quests diff).
- A8 12th stopped: DD-08 (06:04), DD-15, DD-17 (cinematics fixed, perception 15) installed, 4/4. D-66 on its build choices. A6 18th relayed (doors, textures).
- A1 released merge point 27 (studio only, 06:06:32). 25 maps need a Lua-only rebuild; relayed A6 and A3; A5/A7/A8 lists queued.
- A5 17th, S 7th had stopped; A5 18th, A7 19th, S 8th started (06:15). AU held (budget 6,250 uncommitted). A8's MP27 list waits for A8 14th to finish.
- S 8th: P5's pieces bound; xeen_p5.blv added to openAirMaps (backup output/xeen_o3/world.yml.bak_p5); A5 18th told to install P5. S asks A6 about D7's Rest Stop hut. S resumed for priority 2.
- D-66 answered (all accepted; DD-15 bake, DD-17 prompts/buttons/belt/throne, DD-08 thrones before done; roof/hatch rule). Relayed A7 19th, S 8th; A8/A1/A3 queued.
- A6 18th done: D5 green door → DD-15 (segment 69 case passes), DD-25, DD-08; D6 DD-21/DD-17 gate/DD-10C; D7 hatch/sky door, Megadragon leash, lamps, benches; P1 asks; P4 octopods mid-sea. Relayed A3 24th (seg 69 workaround, castle_door question, D-66 A3 items), S (no hut), A8 14th (DD-22 hatch).
- A7 19th done: MP27 on XD-04/05/25, DD-16/24, FD-02/04 (Lua only), crossword variants, FD-02 exit name, FD-04 roof Yes/No.
- A8 14th: DD-22 installed 06:27; DD-26 waits on A4. Started A4 15th, D-67, A8 15th, A1 24th (06:35).
- A4 15th: house 4815 written; X7's XD-18 mouth open and its trainer row in. A8 14th resumed to install DD-26.
- A8 14th done: DD-26 installed 06:33 (4/4, baked on DD-03's lower profile). A6 19th started for D7 grate and D6 hatch. Next A4: Cyrano's door check (installed).
- D-67 answered (all accepted; DD-22 sky/red walls/buttons/couch arms; DD-26 exit Yes/No, headboard, reach step). A8 14th resumed for it; A1 24th told the body-size check is backlog.
- A3 24th done: q-d28 written; segments 69–77 pass (main line through M33 Castle Alamar). Relayed A6 19th (D7 hooks), A8 14th (DD-26 wiring), A8 15th (DD-17 arrival re-arm), A1 24th (topic Yes/No buttons). Cyrano's typed yes: no decider (temporary until A1's buttons).
- A5 18th done: P5 installed 06:41, all X7 doors open, mound arrivals fixed. Relayed A3 25th (P5, tower_door line, wedding figures). A7 20th started (07:00): FD-03 hatch, named exits, DD-06/07 roofs.
- A6 19th done: D7 grate into DD-26 and D6 hatch into DD-22 live; hooks_d7 passes. Relayed A8 14th (playtest_in z fix, DD-22 way-in test). Only FD-01's doors remain sealed on D6/D7.
- A1 24th: merge point 28 (game only 06:49:47). Relayed A8 15th (belt asserts), A3 25th (Cyrano buttons).
- A8 14th done: D-67 on DD-22 (red walls, day sky, buttons, couch arms) and DD-26 (exit Yes/No, headboard, reach step); both 4/4 incl. ways in.
- A7 20th done: FD-03's hatch to P5 live (no seals left), XD-02/05/26 exits by name, DD-06/07 roofs Yes/No. A5 questions queued.
- A8 15th done: D-66 on DD-15 and DD-17 (DD-17 waits only on S's throne/statue), MP27 on all 10 maps. Merge point 27 is now in every installed Xeen map with peaceful groups. Relayed A3 25th.
- S 8th done: planes' pieces. Started A2 17th, A6 20th (planes), S 9th (throne/statue first). Relayed A3 25th (m38.plaque_fire).
- A2 17th done (no trigger; Act V complete 1.03). Relayed S 9th (bind 11474; dwarves need nothing), A6 20th (P4 octopods → 11474). A8 16th started on FD-01's graph — the last unbuilt map.
- S 9th interim: thrones 4043–4045 (MM9's carved throne under D-44, recoloured) and teal statue 4046 bound; Octopod E bound (334/84, 0 refused). A8 17th started (07:40) to swap them into DD-08/DD-17 and delete the hard-linked old dd14 root. Stopped the dead S-7 decorations sub-agent (aa760013421b07b1b) — S 9th does the waterfall.
- S 7th's final note: nothing half-installed; waterfall work/root is hard-linked (S 9th told to unlink after install); row 4014 boulder size to ~300 across (S 9th → A2).

- A3 25th done: chain 69–85 (M37) passes, P5 ending seen in game (couple under the pavilion), Cyrano on buttons. D-68 started; A8 17th given XD-12's cloud stair; A5 19th started.
- D-68 answered: CONVENTION tag for chain stat gates (shortfall only, temporary), A2 proves reachability; DD-26 reach step tightened. A3 26th, A2 18th started; A8 17th relayed.
- A8 16th done: FD-01 graph and page (Q63–Q72; default 34 robots 40.81k, group +5.7 %). D-69 started.
- A6 20th done: planes dressed. Relayed A3 26th (M38 unblocked), A8 17th (stale dd08/dd17 bakes), S 9th (P3 column too bright, P1 too faint). A1 25th started for MP29.
- A5 19th done. Relayed A3 26th (hooks_p5 talk, reflector lines). A7 items queued.
- S 9th done. Relayed A8 17th (DD-17 spots, DD-21 heart jar). Started A5 20th (waterfall), A7 21st, S 10th.
- D-69 answered (FD-01 approved with changes). Recorded; maps.yml FD-01 text (backup output/xeen_o3/maps.yml.bak_fd01; --check clean). A8 18th started on FD-01; relayed A3 26th, A2 18th, S 10th.
- A8 17th done: DD-08 and DD-17 meet D-66; XD-12's cloud stair to X9 live. Relayed A1 25th (select_member flake), A3 26th (drop 83's workaround), S 10th (Sheltem invisible in DD-17).
- A5 20th: XD-17 waterfall placed; S 10th told of four look faults (mist rim, strand ends, no source above the notch).
- A2 18th done: stat gates all reachable (M34 Accuracy only with D5's shrine carried); wells stack per click. D-70 started.
- A6 21st done. Relayed S 10th (P1 grey edge), A8 18th (fd01_roof installed).
- S 10th: Sheltem works (A8's tour loaded DD-17 without the Soul Box, so the party was thrown out). Seen with a proper entry: `level_generation/creatures/xeen_tiers_claude/work_s10/sheltem/sheet.jpg`.
- A7 21st done: FD-02's carved throne, FD-04's eggs, XD-02's exit, XD-19's tray confirmed.
- D-70 answered (tonic at X9; every temporary source daily for the party). A5 21st and A6 22nd started; A3 26th relayed.
- A1 25th: merge point 29 released 08:18 (game + oymap). Relayed A6 22nd (P4 fog, P1/P2 rebuild), A3 26th (equip_item, load fix).
- A6 22nd done: D-70 on D1/D2/D4/D6, P4 underwater fog. Cauldron single-drinker queued for the next decider batch.
- **08:28 FD-01 installed: all 82 maps of the world are installed** (checked against maps.yml). A6 23rd (last doors), D-71 started; A3 26th told (hatch state, M39 on).
- A5 21st done (tonic, daily guards). Relayed A3 26th (texts, freed bits, tonic where). A2 19th started.
- D-71 answered (FD-01 polish P1–P3 before done; cauldron confirmed). A3 26th relayed (statue else_text).
- A2 19th done: whole world counted; every act within 0.85–1.15; all stat gates pass; 0 unguarded temporary sources.
- A6 23rd done: FD-01's doors live — every door in the world is open. D-72 started on D6's question-less hatches; A8 19th told to hold playtest_in.
- D-72 answered: outdoor entrances move at once; D6 unchanged; A8 19th told to drop FD-01's answer step; A5/A6/A3/A1 items queued.
- S 10th done (all its queue). Relayed A8 19th (DD-12 cage birds), A5 22nd (XD-17 re-shoot). A7 22nd (lizard, lecterns) and A2 20th (boulder row) started; A6 24th queued after A2.
- A5 22nd: D-72's four prompts done; its DECIDE (X6 40, X7 22) answered from D-72's rule (no new decider) and A5 resumed to apply it.
- A2 20th done. Ownership answer (process, orchestrator's): `worlds/xeen/models/decoration_data.txt` is S's (hand-written with its models); A2 edits rows only on request. A6 24th started.
- A8 19th done: FD-01 meets D-71; DD-21 4/4; Sheltem seen in DD-17; DD-12's cage birds placed. Every A8 map is done.
- A5 22nd done: all six X6/X7 outdoor prompts show their source question with buttons.
- A7 22nd done (lizard, lecterns). **Alister (FD-04, row 11923) has no 3D body — invisible in game**: S 11th binds him and scans for other bodiless placed rows. A1 26th started (MP30: rotating movers, warnings, docs).
- A6 24th done. Its DECIDE (D4 74) settled by the orchestrator as (a): D-72's rule (question on screen with buttons) is met as built, so A3's text change is cancelled — a check of D-72's premise, not a new design call.
- **User 2026-11-21 ~09:20: ElevenLabs credits — "use however much you need (if it makes sense)".** The 100k job cap is lifted; AU 5th started with the whole queue.
- A1 26th: merge point 30 released (studio 09:24). A8 20th and A7 23rd started for its follow-ups. A1's slip: one small studio build overlapped another session's openyamm build (no harm).
- S 11th done: Alister visible; every placed actor has a body. A6 25th started (plane devices). Next A5: optional XD-17 re-shoot (S checked it placed).
- A7 23rd done (MP30 follow-ups). The oymap 09:31:22 vs 09:24:21: built 09:24, copied at release 09:31 (A1's release_studio.sh) — no stray build.
- A6 25th done: the planes' devices placed and wired; nothing blocked on P1/P2.
- AU 5th done: 25 sounds (budget raised to 140k; 37,791 charged, 132,950 committed). Paste round: A5 23rd and A6 26th started; A8 and A3 queued.
- A8 20th done. Its brief overwrite of A7's DD-02 L4 (09:38:46–09:43) checked: the L4 holds A7's values (mouth4 offset 96, bottom 320) and the installed studio revision is A7's 6fbb30c9… — no harm. Next A8 (21st): AU's paste list.
- A6 26th done. Next A6 may delete its superseded bake folders (`output/studio_cal/a6/bake_xeen_x5_013419`, `_024418`, `_024844`, `_025237`, `bake_xeen_d1_012903`, `_024159`, ~1.9 GB; current `bake_xeen_x5_095957`, `bake_xeen_d1_100201`) — orchestrator agrees. Next AU: AmbientSound 1=on/2=off; D7 heights over the void count from the safety floor.
- A5 23rd done: its AU paste complete; the stale bakes are A8's (A8 21st told).
- A8 21st done: AU's paste complete in A8's dungeons; stale bakes 0.
- 11:30 A3 26th found stalled since 08:42 (its A3.md log is complete: M38 done, 87–93 pass). A3 27th started to take the chain to the ending.
- **User 11:40: "create the playthrough scenarios like we have for MM9 — for main campaign, for promotion and for all side quests — for the Xeen world."** Main: A3 27th (to the ending). Started A3-side and A3-promo sub-lanes (11:45) with edit boundaries (m* = A3 27th; q-c/q-d/q-f = A3-side; t1/t2 + Xeen.Promotions = A3-promo; gen_quests writes only when --check shows only one's own change).
- User asked about skill teachers. towns.py --strict: 116/116 offers taught. Plan order scan found 3 oddities → D-73.
- **User 2026-11-21: early Grandmasters are fine** ("it's gated anyway behind the promos … MM6–MM8 also have GMs all over the place"). Told D-73; GM-before-Master not a fault by itself.
- D-73 answered: one real fix (Dodging/Unarmed Expert); the rest fine or the user's call. A4 16th started.
- A4 16th done (D-73). Next A3: Lin/Mei topics check (tables say none); optional Sparrow flavour topic.
- **12:10 A3 27th: the main story chain is complete — every main step M1–M42 in segments 01–99, to the ending (111840).** 63–99 pass both modes. A3 28th started to rerun 01–99 in one go on today's world.
- A3-promo 1st done (13 segments pass). D-74 (late promotions) and A1 27th (MP31: checkMonstersKilled ignores invisibleAsDead — shared code, MM6–MM8 check) started.
- D-74 answered (later members promoted unpaid; no crossing; Q-D13/Q-D22 hooks as states; Q-D23 via Morbius; Necromancers named). Relayed A3-side; A3-promo 2nd started.
- A1 27th: merge point 31 released (game + studio, 12:41/12:43) — changes MM7/MM8 behaviour (flagged in STATUS for the user). Relayed A3-promo 2nd (seg 31).
- A3-promo 2nd done: 38 segments, 23/24 table rows. D3's guild gate never opened into DD-19 → A5 24th. D-75 on prerequisite conventions. A3-side relayed D25-1 and q-d13 lines.
- A5 24th: D3's guild gate live. Relayed A3-side (q-d14 scenario). A3-promo 3rd started.
- **User ~13:28: a Xeen guide like MM9's (same formats, walkthroughs, minimaps, locations, teachers…), also on the server, one agent end to end.** New lane G started (13:30); the user's request covers publishing to jasicek.net/openyamm/xeen-guide/.
- User: G must finish the story walkthrough, consulting the story side (A3's sources, ORIGINAL_LINES, reference/mm4_5_world_of_xeen, quest files, segments); G's questions come as 'QUESTION for A3' in its reports → route to A3 (or a fresh A3 session). G gets more sessions rather than a thin story.

- **13:30 A3-promo 3rd: the promotion playthrough is complete — 41 segments, class table 24/24, every segment passes normal and --reload.** Next: rerun with `run.py --start` once A3 28th's main rerun is final.
- **13:38 A3 28th: the whole main chain 01–99 passes in one go on today's world, normal and --reload, no BLOCKER or ISSUE** (only 83's stat-gate CONVENTIONs). New chain README. A1 28th (GiveItem loses the cursor item — shared code) and A3-promo 4th (refresh) started.
- **User ~13:48: new-game cards renumbered — Xeen first (MM4+MM5), then MM6, MM7, MM8, MM9; Xeen marked Experimental.** Done by the orchestrator: engine and MAW character_selection.yml orders (Enroth 2, Antagarich 3, Jadame 4, Chedian 5; backups output/xeen_o3/*.bak_order), Xeen's continents.yml order 1 + caption "Experimental: begin in Vertigo", `--only gen_towns`, --check 0 differ; TABLES.md example updated. A screenshot check is running.
- A3-promo 4th done: promotions 41/41 normal and --reload on today's main checkpoints.
- A1 28th: merge point 32 (game 13:44). The unit test now follows my card-order change (A1 updated it).
- **14:05 G published the Xeen guide at https://jasicek.net/openyamm/xeen-guide/** (shared front end with MM9's; MM9 output proven unchanged). G broke the ≤2 sub-agent limit (its story writer forked five). A3 29th started on G's 44 questions; D-76 on uncertainty/spoilers.
- D-76 answered (guide states facts; answers stay in walkthroughs; map details cleaned). G 2nd started.
- **14:25 A3-side: every Xeen side quest has a standalone scenario — 69 files, all pass normal and --reload.** All three playthrough sets are now complete. Started D-77, A1 29th (MP33), A6 27th, A8 22nd for its findings.
- A8 22nd done: DD-10A fixed; DD-20's 'one way' was a stalker; DD-09 fine.
- A6 27th done (its side-quest faults fixed; q-c16 scenario needs the Burn? step). A3-side 2nd started.
- A3 29th done: G's 44 questions answered in G.md; 12 quest fixes; relayed A3-side (q-d10 double pay, q-d15 glass, wordings); D-78 on M1's pest count. QUESTS §4.2 fixed.
- G 2nd done: guide republished with D-76 and A3's answers. MM9 guide point `isleofashes a14` ("Fre's Rain: special_passage") shows an identifier — MM9's, told the user. D-79 started.
- A1 29th: merge point 33 (shared magical-age change flagged for the user; Xeen loot MM6–MM8 only; enchanted shop stock). D-80 started; A3-side 2nd told.
- D-79 (clue texts cut) and D-80 (Xeen ignores the MM9 loot setting; enchanted stock intended; possible plain-MM9-in-shops bug) answered. G 3rd, A1 30th (MP34), A2 21st started. D-79's two MM9 guide points (darkpassageway Gemstone angles, Floor plates order) are the MM9 guide owner's — told the user.
- A2 21st done. D-80 note added (deed is 12,000). D-81 started on Q-C25's gems.
- G 3rd done: guide republished with D-79 and D-80. MM9 guide owner items for the user: darkpassageway Gemstone/Floor plates, isleofashes a14 identifier, quest_levels tie-break.
- **User 15:33: tier tints should match names** (Water Dragon is red in the bestiary; water = blue/turquoise, acid = poison green, fire = red; check the other Xeen families). S 12th started; G recaptures portraits after.
- A1 30th: merge point 34 — the plain-MM9-in-shops bug was real (MM6–MM8 too), fixed.
- A3-side 2nd done: 70/70 side-quest scenarios pass on MP33; Q-D10 robbery no longer paid; Q-D15 glass gated.
- S 12th done: 27 tiers recoloured to match their names. G 4th started (portraits, republish).
- **User 16:13: run the review rows through a Reviewer session that reviews and decides.** Reviewer (opus) started on all 66 G3 rows (+ open G0–G2), newest first (tier colours, MP34 shops, MP33 magical age, MP31 hidden monsters). Its follow-ups get relayed to lanes.
- A3 30th done: main chain passes on MP33/34 both modes; checkpoints rewritten → A3-promo 5th refresh. QUESTS Q-D7 reward named. D-82 on chain health checks.
- G 4th done: all bestiary portraits recaptured and republished (framing fixed).
- **Reviewer done: 78 rows, 73 accepted, 5 need work** (`reviews/G3_REVIEW_20261121.md`); MP31/33/34 behaviour changes accepted. Follow-ups relayed: A6 28th, A8 23rd, A7 24th, S 13th, A5 25th, A1 31st; A3 (ending turn-based check) queued with D-82.
- D-82 answered (party health: runner fails when nobody can act; chains assert at segment ends; temple cures). A1 31st told (runner check into MP35); A3 31st started.
- A5 25th done.
- **~17:00 user: near usage limits — all running lanes told to finish at a safe checkpoint and write their handoff into their lane files. HANDOFF_ORCHESTRATOR4.md written for the fourth orchestrator.**
- A3 31st stopped (handoff in A3.md): chain gets D-82 check; next session fixes 61/67's DD-14 walks and reruns.
- S 13th stopped (handoff in S.md).
- A6 28th stopped (handoff in A6.md): Olympus and P1 work in scratch, resume steps written.
- A3-promo 5th done.
- A1 31st stopped: MP35 released. A8 told to rebake DD-14.
- A8 23rd stopped: four Reviewer fixes installed; DD-14 playtest stuck in the Count's hall (likely MP33 clears) — in the handoff.
- A7 24th stopped. **~17:15: every session stopped; 0 stale bakes, build_world --check 0 differ, no game running. Handoff complete: HANDOFF_ORCHESTRATOR4.md.**
