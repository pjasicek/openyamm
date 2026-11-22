# Phase 6, lane A7's graphs XD-18, FD-02, FD-03, FD-04: decisions (D-57)

Decider D-57, 2026-11-21. This answer wins over the graphs in `act6_graphs/` and over `act6_dungeon_graphs_a7.md` wherever they differ.

**APPROVAL**

All four graphs are approved for L1–L4, each with changes. None needs a redraw. The order of the L1s is the one on the page: FD-03, FD-02, XD-18, FD-04.

- **XD-18 Dragon Cave: approved with changes.**
  - **Rest encounters 0** (Q5 (b)), not 10 %. At Dif 5 the cloud dragons' slot rolls tiers A/B/C: Water 60 (10 %), Acid 66 (50 %) and Fire 75 (40 %). Frost is tier D and is never rolled, so the graph's "Fire, Frost; never the Water Dragon" cannot be had. More importantly, a 487-tall dragon brought in by a rest would land in the tax hall (384 high), the waiting room, the antechamber or a 288 passage.
  - **Starwell check.** The headless check of Q4 also flies a Frost Dragon against the starwell's `sky: true` slot and shows that it cannot leave the map through it.
  - **Roost ledge.** The ledge's 128 lip must stop a walking party. The same check walks into it; if the party steps over, raise the lip to 192, as FD-03's parapet. A party that does fall lands in the roost and is not trapped, so this is a polish item, not a blocker.
  - **`xdhoard`.** Made only if the dais, bare `t68a02a` dressed with shipped gold and chest decorations, does not read as a hoard in the tour shot.
- **FD-02 Southern Sphinx: approved with changes.**
  - **X6's return point is wrong.** DOORS.md puts the breast's face at (−12544, −10240, 1536), facing east. The page's (−12800, −10240) is 256 inside the sphinx. `entrance:fd02_door` goes to about **(−12144, −10240, 1536)**, about 400 in front of the leaves, facing east (0). A5 confirms it against the carrier block.
  - **Dragon Mummy size.** By its descriptor the Dragon Mummy (11672, `Xeen Bone Dragon C`) is 450 high with radius 120, not about 512 and 300, and it flies. The crypt steps' arch is therefore **288 high** (D-32's tested height), not 384. Add a headless check that a Dragon Mummy stays in the crypt and the stalls.
  - **Trap damage.** Unprotected, one crossing of a run deals at most about 25 % of a level-59 member's HP in all: about 6 % per Swinging blade and about 8 % per Chopping blade, Physical, never lethal to a healthy party. The graph's 12 % per blade came to 48 % for the Swinging run.
  - **Might Boosts.** Two event-given Might Boosts sit on the hall of embalming's table, once per game (map qbit 118119, the spare), as D-22 and D-39 Q4 did for XD-15. A3 writes the line.
  - **Mummy skins.** Ghost and Phase Mummy are recolours on `xeen_mummy.glb`, the Xeen copy, never MM9 (D-44).
  - **Rest encounters 0** (Q13 (b)).
- **FD-03 Darkstone Tower: approved with changes.**
  - **The gongs' geometry (Q15).** The page's "ends 640 short" contradicts 24 × 32 = 768 and is a slip. Each stair room is a stairwell open from its storey's floor to the storey above:
    - The flight climbs the outer wall to a 512 × 512 gap where its top landing belongs, over the stairwell's open floor and not over the flight.
    - The landing is the slab. Sunk, it stands as a dais 128 high on the stairwell's floor directly under the gap. The gong raises it 640, flush with the storey above. L3's twin gongs raise it 320 each.
    - A party that walks off the top step drops onto the dais, with light falling damage, and walks off it. It is never stuck, and the same holds at L3's half height of 448.
  - **Quiet arrival.** The door hall's east way into the east arc becomes a door (one leaf; 12 doors in all), so that the three Sentries of an open arc cannot walk into the arrival (D-11.3).
  - **The vault's force** reuses `xafield` at about 0.5 (D-51), not a new texture. The seal keeps `xdseal`. Its 0.15 opacity must read as a tell in a tour shot from 3 m; if it does not, raise it toward 0.3.
  - **L4 summary.** The fourth head read on L4 also writes an autonote with the summary line (Q35).
  - **The hatch** has `open_sky` with P5's sky preset (D-56 Q9).
- **FD-04 Dragon Tower and the Dungeon of Death: approved with changes.**
  - **Quiet gate hall.** The scorched hall's low opening is out of the line of sight from `entrance:x7_gate`, round a turn in a short passage, and its Acid pair stands at least 1,024 from that opening. The arrival stays quiet against breath attacks (D-11.3).
  - **The gong hall's gongs show their state.** A lamp or glow under each gong lights when it is rung and goes out when the chest resets them, with A3's line "The gongs fall silent." This is a mechanism with a visible effect (D-43).
  - **Alister** is hidden, and the lizard shown, when his paying talk closes, not on the next load. Both stay so on every load with 118147.
  - **Crossword clue 42 Down** ("Tower located in Troll Forest", Darkstone) is untrue in our world: Darkstone stands in X5's frozen mere, apart from the Troll Forest zone. It is replaced by the source's **45 Down "City of Ghosts" (Winterkill)**, X5's ghost town (Q25).
  - **The main terminal keeps the source's code prompt** (Q35 (a)).
  - **Rest encounters 0** (Q31 (a)).

**General rules for all four**

- **Rest encounters 0 on all four maps** (rows 9143, 9180, 9181 and 9182). No slot can roll in-band tiers without bringing in tall flyers or tiers under the band (D-43: no tier range per slot). This is the same reasoning as D-47's DD-24 and A7's own FD-03 and FD-04.
- **Exits and entrances.** Every exit is the `exit` preset (D-24). Inside entrances are named after the map they are entered from (D-37). Every first room is quiet (D-11.3).
- **No Meshy, no MM9.** Every new look is a recolour on an installed Xeen or MM6–MM8 body (D-44).
- **No new equipment items or icons.** The Dragon Egg reuses MM7's `7item291`, and the Key to the Dragon Tower reuses a shipped key picture. Q-F1's artifact is an existing artifact row, for example an Elder weapon not yet placed, whose skin is an MM6–MM8 engine item.
- **New textures:** XD-18 0–1, FD-02 2, FD-03 3, FD-04 2. That is at most 8, so the world goes from about 169 to at most 177 of 450.

---

**ANSWERS**

**XD-18 Dragon Cave**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q1 | **(a).** Acid 66 × 9, Fire 75 × 17 and Frost 85 × 14, plus the Dragon King 110: 66.64k (+3.2 %), 69.94k with the King (+8.3 %). One NOTES line for 40 under M's 45. | This is MAPS's own count and the source's dragons. With the boss it stays inside 10 %, as XD-19's +8.8 % did (D-47). | A2: Act VI recount. A7: placement and the NOTES line. | Yes, cheap until placement |
| Q2 | **(a).** The inner door's click calls `q-c25.inner_door`. With `tax_paid` it opens for good (118100). Without it, the fail_text plays and `{exit: x7}` moves the party to `entrance:xd18_mouth`. The office stays open to all, and the door always opens from inside. | This is the source's ejection as one click. The leave comes after the event has decided, as a throw (D-24). | A3: the fail_text and the urn line before payment. A7. | Yes, cheap |
| Q3 | **(a).** His own recolour skin `xcdr_king` on `xeen_cdr1` (black scales with gold edges), no Meshy. | Every boss gets its own skin (D-39, D-47). Today the King looks like a Fire Dragon. | S. A2: bind 11645. | Yes, cheap |
| Q4 | **(a), plus the starwell check (APPROVAL).** Every party passage is 288 high. The 768 dragon roads join only the roost, the ledge, the ember gallery and the starwell. The headless check covers a Fire Dragon staying in the roost and a Frost Dragon against the slot. | D-32. The descriptor gives the dragons as 487 high. | A7. A1 only if a `sky: true` face lets a flyer through. | Yes, cheap |
| Q5 | **(b) 0.** | Dif 5 rolls Water, Acid and Fire, never Frost, and a 487-tall dragon brought in by a rest cannot fit the 288–384 rooms where a party rests. | A2: row 9143, encounter 0. | Yes, cheap |
| Q6 | **(a).** d17's rock for the caves, and MM8 d16 for the office, the waiting room, the library and the King's door. `wtrtyl` for the pools. `xdhoard` only as the APPROVAL says. About 15 of 45. | A6's assignment kept. The worked rooms read as the clerks' and the library's. XD-10 is far away. | A6: the d17 line with the d16 area; `xdhoard` if made. A7. | Medium after build |

**FD-02 Southern Sphinx**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q7 | **(a).** FD-02 has 26 monsters (Ghost 16, Phase 4, Dragon Mummy 6), 31.07k. FD-01 plans 34 monsters at 36.93k, so the row is exactly 68.0k. A8 may move FD-01 anywhere that keeps the combined row within ±10 % (61.2k–74.8k, so FD-01 30.1k–43.7k). If FD-01 stays under M's 45, it carries a NOTES exception line, as XD-16 and XD-18 do. | The source's three families in its proportions, inside S's band, with no change to the drawn graph. Every split leaves FD-01 under 45 unless FD-02 drops to S's floor, so the exception is the cheaper fix. | A8: FD-01's graph. A2: recount. Orchestrator: MAPS. | Yes, until FD-01's L1 |
| Q8 | **(a).** New pyramid-mummy tiers D and E: 11273 Ghost Mummy 62 (Age) and 11274 Phase Mummy 72 (DrainSP). Recolours on `xeen_mummy.glb`, not MM9. | They are the source's monsters, at the band. Both special attacks exist in MM. MONSTERS_AND_ITEMS's "Reuse MM9 mummy" breaks D-44. | A2: rows. S: two skins. | Yes, cheap |
| Q9 | **(a).** Each mask offers its run's protection for 2,000 gold: the blades stop for good (118116 / 118117). No gives "Begone, then!" and no throw. After paying, the clue costs 500 more: "There's one born every minute." Damage as the APPROVAL says. | The joke at a price that stings. The blades are the tell, and the runes answer the name. | A3: lines and sums. A2: gold ledger. A7. | Yes, cheap |
| Q10 | **(a)** Might ≥ 60 on the clicking member, buffs counting, with one T6 chest per sarcophagus, **plus** the two fixed Might Boosts (118119). | This repeats D-39 Q4's pattern for XD-15 (Might 40 with event-given boosts). The game supplies what the check needs. | A3: the table's line. A2: the check and the boosts in the ledger. A7. | Yes, cheap |
| Q11 | **(a).** The pyramid set's other half: no striped columns, drifted sand, two new textures (`xsshelf`, `xsrunes`). About 24 of 30. | One family, but it reads apart from XD-15. | A6: accent line, register both textures. | Medium after build |
| Q12 | **(a).** His very good chair hovers "Throne of Legends", with no reward. | XD-15 already has a throne of legends; a second +2 would repeat it. | A3: hover. S: a shipped chair or throne decoration. | Yes |
| Q13 | **(b) 0.** | The pyramid mummies' slot rolls Tomb Mummy 42 and Pyramid Guard 52 (60 %, under the band). Ghost and Phase are tiers D and E and are never rolled. The undead dragons' slot rolls 450-tall flyers into 640-high rooms and Bone Dragons 45. | A2: row 9180, encounter 0. | Yes, cheap |

**FD-03 Darkstone Tower**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q14 | **(a).** New material-golem tiers 11585 Onyx Sentry 62 and 11586 Onyx Warden 72, as recolours of `xgol_e` on `xeen_m254`. Sentry 20, Warden 16, Sky Golem 8 and the Onyx Golem 85 once: 60.70k (+3.1 %). | The source's single family, inside 10 %. | A2: rows and recount. S: two skins. | Yes, cheap |
| Q15 | **(a), with the stairwell-and-dais geometry of the APPROVAL.** Qbits 118120–118123 raise the slabs on every load. | The source's "no ground" made literal and walked, with no possible trap, using doors and qbits only. Unlike DD-06, the gongs raise ground rather than open doors. | A7: geometry and a playtest that walks off an unraised top step and out, then rings the gong and climbs. | Yes, cheap |
| Q16 | **(a).** Two hidden guards per gong, shown by its ring. Eight of the 45, always met. | The source's summons, using D-18's show-actors word. | A7 | Yes, cheap |
| Q17 | **(a).** The rows on each click. The fourth read on a storey adds the columns read down (map variables). On L4 that line is also written as an autonote. No reward. | The game gives the answer, and the autonote keeps the L4 line for FD-04 (Q35). | A3: four summary lines and the autonote. A7. | Yes, cheap |
| Q18 | **(a).** The skull is silent. The vault's force (`xafield` at about 0.5) drops at the Onyx Golem's death (118124) and holds a T6 chest. | A3 dropped the riddle, and the Gold ID Card has no use here. Reusing the texture costs no new one. | A7 | Yes, cheap |
| Q19 | **(a).** Radius 2,048, storeys 768 apart, rotundas 640 high, about 38 M units². | M's band. Interiors larger than their shells are precedent (D-39 Q6/Q7). | A7 | Medium after build |
| Q20 | **(a).** An open hatch (`open_sky`, P5's preset). The exit preset leads up to P5's `entrance:fd03_roof` (4608, −3968, 0), facing 512. P5's way down arrives at `entrance:p5_stair` on the top step, facing down. | D-56. A3's "Cloud light comes down it" wants a lit opening. | A3: the up-exit's line ("Climb to the Clouds of the Ancients?" or the like). A5: P5's `door:fd03`. A7. | Yes, cheap |
| Q21 | **(a).** A translucent leaf of about 0.15 with `xdseal`, raised toward 0.3 if it does not read. Opened by `m41.seal` in the same visit and on every load. | It must be "invisible" yet still a tell (D-51). | A6: register `xdseal`. A7. | Yes, cheap |

**FD-04 Dragon Tower and the Dungeon of Death**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q22 | **(a).** The tower holds 26 (Acid 6, Fire 8, Frost 6, Phase 5, Energy Dragon 100). The dungeon holds 34 (Lich Lord 10, Power Lich 6, Skeletal Lich 8, Doom Knight 4, Autobot 6). 100.22k (+3.5 %). | Only rows in the band, the source's families, inside 10 %. | A2: recount; FD-04 in the `where` of the dark dragons, liches, dark knights and robots. | Yes, cheap until placement |
| Q23 | **(a).** A new quest item, "Key to the Dragon Tower", with a shipped key picture. A8 places it on or beside FD-01's critical path, so that every party that finishes M39 carries it. X7's `door:fd04` needs it. A3's hook gives a refusal that names the key. | The source's place and order. It keeps the optional finale after M39, at MAPS's 62 → 66, and keeps the Dungeon of Death behind it. If A8 cannot place it, fall back to (b). | A8, A2 (item), A3 (hook), A5 (door) | Yes, cheap |
| Q24 | **(a).** The black iron door in the cellar well. Item 12354 opens it for good (118130) and the key is kept. Without the key, a refusal names it. From below the door always opens. | Q-D23. Keys are kept (D-4). | A3: `q-f2.door`. A7. | Yes, cheap |
| Q25 | **(a), with 42 Down replaced by 45 Down "City of Ghosts" (Winterkill).** The twelve gate the descent and pay the reward once. A3 checks each answer against our world and accepts spelling variants (Sceptre, Kalindra's, and so on). The lit strips need not form a true grid, but where two cross, the shared letter matches. | Every answer is a name the game has said before FD-04 opens. The source's Troll Forest clue is false in our X5. | A3: the twelve prompts and the reward. A7. | Yes, cheap |
| Q26 | **(a).** The question carries a tell. Yes brings camera shake, dust, Fire damage of about 20 % (never lethal) and `{exit: x7}` to `entrance:fd04_door` with the source's line. The shrine stays broken (118148), with no experience. | The joke is kept as a real choice that asks first (D-24). | A3, A7 | Yes, cheap |
| Q27 | **(a), same visit.** Alister takes the egg, pays (Q32) and says "…Now I'll just drink this egg potion and…". When the talk closes he is hidden and the lizard decoration is shown (118147, kept on load). He is peaceful, placed-only and unkillable (load event, D-52). | Q-F1's fraud. A visible effect at once (D-47 Q4). | A3, A2 (peaceful row, the Dragon Egg on `7item291`), A4 (NPC id), S (body, lizard), A7. A1 only if a topic's done event cannot hide the actor mid-visit; then use the next load. | Yes, cheap |
| Q28 | **(a).** The tower in MM6 6d04's vlc block, Sandro's halls and the crossword in MM8 d19, the machine floor in sci-fi.blv with XD-19's core textures. New: `xfgrid` and `xfword`. About 36 of 45. | One shipped family per area. The black vlc block echoes X7's shell, and d19 is the necromancers' own. | A6: towers and dungeon_families lines, register both textures. | Medium after build |
| Q29 | **(a).** Larger than the shell. Every opening off a dragon hall is 256 × 288. A headless check that a dragon stays on its floor. | D-32, D-39 Q6. | A7 | Medium after build |
| Q30 | **(a).** Own recolour skins for the Energy Dragon (violet-white on m492), the Power Lich and the Skeletal Lich (on the lich body, not MM9). A2 makes 11284 and 11285 **ordinary tiers D and E with ordinary HP** (L²/10 + 3L: 788 and 978, not 2,364 and 2,934). | Fourteen boss-HP liches would be a wall. The three lich tiers must read apart in one hall. | A2, S | Yes, cheap |
| Q31 | **(a) 0.** | The liches' slot rolls 35 and 50; the dragons cannot fit the dungeon's rooms. | A2: row 9182 | Yes, cheap |
| Q32 | **(a).** +2 Endurance once per character (a player bit). Fixed experience, with Q-F1 and Q-F2 together at about 40k per member of the optional 70k. Suggested split, which A3 may move inside 40k:<br>- **Q-F1** (17k): Alister 5k, the Tome 4k (once per character), the Eye 8k (on X9).<br>- **Q-F2** (24k): crossword 6k; shrines Minor 1k, Lesser 2k, Great 3k, Ultimate 0; machine 10k; the code 2k.<br>The source's numbers go to the ledger. | D-4 and QUESTS: no levels and no millions. This leaves room for Q-C25's 12k and the rest of the optional content. | A3: amounts. A2: Act VI and optional ledgers, plus the permanent-stat ledger. | Yes, cheap |
| Q33 | **Superseded by Q35 (a).** | The page's own evidence: a code exists, and FD-03 gives it. | — | — |
| Q34 | **(a).** The coffins stay shut and the vampires never wake: flavour and a chest. | No new row for a joke the note already tells. | A7, A3 (lines) | Yes |

**Across maps**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q35 | **(a).** The main terminal asks "Main Terminal / Enter Code" (`dark/aazex124:12–13` in the raw text). "Computer", in any case, pays 2k once and a line. The first wrong answer gives "You are a Goober!", a second "You are a SUPER Goober!". FD-03's L4 summary says the source's "TYPE "COMPUTER" ON LEVEL 4 OF THE DUNGEON OF DEATH. SEE YA SOON!" and writes it as an autonote. "Level 4" stays: the only code prompt sits on the machine floor (the source's level 4), and the prompt makes the link. | The source's two halves joined, with the answer given in the game on the main path. Option (c) breaks the riddle rule; option (b) throws the joke away. | A3: terminal lines, the code's reward, the autonote. A7: both maps. | Yes, cheap |
| Q36 | **(a).** The roof leads to X9, and the Dragon Clouds take the end of Q-F1:<br>- the Eye's "What is the secret of the Dragon?" (INFINITY); a wrong answer gives "Die fools!" as event damage of about 20 %, never lethal, and may be retried;<br>- four Ancient Books with IN / FI / NI / TY;<br>- the crystal balls, the well and the crystals rescaled to D-4 sizes, never lethal, each in the ledger;<br>- an existing artifact row (no new icon).<br>**The one point:** `entrance:fd04_roof` at objects.yml's **[20352, 17280], floor 2,048**, on the cloud about 900 south of the snout. plan.yml's (20864, 18304) is the room's centre and lies inside the dragon skull's footprint; its note is corrected. The arrival faces **north (512)**, toward the dragon-head rock. The way down is a door in the rock's south face with the exit-preset meaning "Descend into Dragon Tower?" (`dark/aazex128:0`), to FD-04's `entrance:x9_clouds`, as D-56's stair house works. | D-50 Q8 built the Clouds empty for exactly this. The source puts the Eye there, and FD-04's notes point to it. | A5: X9 rebuild, point, door, content. A3: `q-f1.eye`, `q-f1.runes`, lines. A2: artifact, ledger. S: shipped decorations, no model. | Yes, cheap |
| Q37 | **(a).** No monsters on the Dragon Clouds. The five Phase Dragons stay under FD-04's roof. | X9's band is 35–55. A dragon of 90 there would be D-1.2's trap pattern on a map walked at 46–48. | — | Yes |

---

**ROWS AND NUMBERS**

| Map | Monsters | Kill XP per member | MAPS | Rest | Chests |
| --- | --: | --- | --- | --- | --: |
| XD-18 | 40 (Acid 9, Fire 17, Frost 14) + Dragon King 110 | 66.64k; 69.94k with the King | 64.6k, +3.2 % / +8.3 % | 0 | 5 T6 |
| FD-02 | 26 (Ghost Mummy 16, Phase Mummy 4, Dragon Mummy 6) | 31.07k | share 29.47k, +5.4 % | 0 | 3 T6 |
| FD-03 | 45 (Sentry 20, Warden 16, Sky Golem 8, Onyx Golem 1) | 60.70k | 58.9k, +3.1 % | 0 | 4 T6 |
| FD-04 | 60 (tower 26, dungeon 34) | 100.22k (tower 46.39k, dungeon 53.84k) | 96.8k, +3.5 % | 0 | 5 T6 |
| FD-01 (A8, planned) | 34 | 36.93k | rest of the row | — | — |

A7's Act VI total is 258.63k against 249.77k (+3.5 %), or 261.93k with the King (+4.9 %). Act VI proper (FD-02 and FD-03) is 91.77k against 88.37k (+3.8 %). New rows: 11273 and 11274, 11585 and 11586, peaceful Picard and Alister, the Dragon Egg and the Key to the Dragon Tower. 11284 and 11285 move from boss rows to ordinary tiers D and E.

**Orchestrator, MAPS changes:**
- **§0 rows:**
  - XD-18: "40 (under M's 45, D-57)", 64.6k (66.64k, +3.2 %; 69.94k with the King, D-57).
  - FD-01, FD-02: "60 (FD-02 26, FD-01 34 planned, D-57)", 68.0k (FD-02 31.07k).
  - FD-03: 58.9k (60.70k, +3.1 %, D-57).
  - FD-04: 96.8k (100.22k, +3.5 %, D-57).
- **Dungeon list:** FD-02 "55–75 (62–72 placed)"; FD-03 "60–85 (onyx golems 62/72, Onyx Golem 85)".
- **MONSTERS_AND_ITEMS:**
  - Pyramid mummies gain Ghost Mummy 62 and Phase Mummy 72, and "MM9 mummy" becomes `xeen_mummy` (D-44).
  - Liches: Power Lich and Skeletal Lich become ordinary tiers D and E, with "MM9 lich king" dropped.
  - Material golems gain Onyx Sentry 62 and Onyx Warden 72.
  - Cloud dragons: "MM9 dragon king" becomes `xeen_cdr1` with its own skin.

---

**RELAYS**

- **A1:** Nothing is required. Act only if A7's tests fail:
  - a `sky: true` face that lets a flying actor through (the XD-18 slot, the FD-03 and FD-04 hatches);
  - a topic's done event that cannot hide a placed talking monster in the same visit (Alister).
- **A2:**
  - Rows 9143, 9180, 9181 and 9182, all encounter 0.
  - 11273 Ghost Mummy 62 (Age) and 11274 Phase Mummy 72 (DrainSP), tiers D and E.
  - 11585 Onyx Sentry 62 and 11586 Onyx Warden 72.
  - 11284 and 11285 as ordinary tiers with HP 788 and 978.
  - Peaceful, placed-only, NoArena, uncounted rows for Picard (npc 5704) and Alister.
  - Items: the Dragon Egg (`7item291`) and the Key to the Dragon Tower (a shipped key picture).
  - Q-F1's artifact from an existing row.
  - FD-04 added to the `where` of the dark dragons, liches, dark knights and robots.
  - Ledgers:
    - the Might 60 check and the two boosts;
    - the toll sums;
    - +2 Endurance and the X9 devices;
    - Q-F1 and Q-F2 at about 40k.
  - The Act VI recount from the table above.
- **A3:**
  - Register qbits 118100–118149, with 118119 as FD-02's boosts.
  - Write `q-f1.yml` and `q-f2.yml` with the hooks on the page, plus the X7 tower-door hook (key refusal), `q-f1.eye` and `q-f1.runes`.
  - Write the lines:
    - the twelve crossword prompts with Winterkill for 42 Down, and their variants;
    - the terminal (Q35) and the L4 autonote;
    - the four plaque summaries and P5's up-exit line;
    - the six rune stones as the source's lessons (aazex127:2–7);
    - the mask lines and sums, the embalming table line;
    - the Ultimate shrine's tell, the gong reset line, Sandro's door refusal;
    - the urn line before payment, the knight's receipt;
    - confirm `q-c25.inner_door`'s `{exit: x7}`.
  - ORIGINAL_LINES rows for aaze0017:0, aaze0050, aazex113–129 as cited.
- **A4:**
  - An NPC id for Alister (for example 5705) in `towns/fd04.yml`, house none, placed in the gate hall's west alcove.
  - Confirm `door:tax_office` (4852, XD-18's tax hall), `door:wyrm_hall` (4853, FD-04 floor 3) and Picard 5704.
- **A5:**
  - X7: `door:xd18` to `entrance:x7_mouth`; `door:fd04` to `entrance:x7_gate`, with the key check. Confirm that the FD-04 return clears the leaves.
  - X6: `door:fd02` to `entrance:x6_door`, and move `entrance:fd02_door` to about (−12144, −10240, 1536), facing east.
  - P5: `door:fd03` to `entrance:p5_stair`.
  - X9: `entrance:fd04_roof` at [20352, 17280], floor 2,048, facing north; correct plan.yml's note; the way-down door to `entrance:x9_clouds`; Q-F1's content with A3; no monsters.
- **A6:**
  - X5: neighbour `door:fd03` to `entrance:x5_door`, replacing the sealed line at FD-03's install.
  - X5's return `entrance:fd03_door` at (−4608, 2304, 1504), facing 512. It does not collide with `entrance:p5_fall` (−4608, 2560, 1504): they are two named points 256 apart on the same terrace, both inside the keep-clear.
  - Family lines: XD-18's d17 with the d16 area; FD-02's accent half; FD-03's d29 with `xafield` reused; FD-04's three areas.
  - Register `xsshelf`, `xsrunes`, `xdplaque`, `xdhead`, `xdseal`, `xfgrid`, `xfword`, and `xdhoard` if it is made.
- **A7:** Build in the order FD-03, FD-02, XD-18, FD-04 on these answers.
  - **NOTES line:** XD-18's 40 under M's 45.
  - **Headless checks:**
    - the roost dragon, the starwell slot and the ledge lip (XD-18);
    - the crypt dragon (FD-02);
    - a dragon on each FD-04 floor.
  - **Playtests:**
    - FD-03: the unraised step and the gong;
    - FD-02: the tax-free… no: the name wrong, then right;
    - XD-18: the tax ejection;
    - FD-04: the gong reset, the crossword, the code, Alister's vanish, the Ultimate shrine.
- **A8:**
  - FD-01's share: 34 monsters at 36.93k (room 30.1k–43.7k inside the row's ±10 %), with a NOTES exception if under M's 45.
  - The Key to the Dragon Tower on or beside FD-01's critical path (Q23 (a)).
- **S:**
  - Recolour skins: `xcdr_king`, the Energy Dragon, the Power Lich, the Skeletal Lich, two mummy tiers on `xeen_mummy.glb`, two onyx tiers on `xeen_m254`.
  - Picard (an old scholar) and Alister (a druid) as recoloured installed MM6–MM8 bodies.
  - The lizard, the chair and the eggs from shipped decorations.
  - No Meshy, no MM9.
- **AU:** Nothing is required. Shipped gong, hum, wind and coin sounds; the seal's crack is optional.
- **Orchestrator:**
  - The MAPS and MONSTERS_AND_ITEMS edits above and the DECISIONS row.
  - D-56 check: FD-03's roof stair (top step `entrance:p5_stair`, exit to `entrance:fd03_roof`) is the one P5's L2 waits on. Confirmed.

---

**SUMMARY ROW**

| D-57 | 2026-11-21 | A7's Act VI graphs (XD-18, FD-02, FD-03, FD-04) | All four approved with changes; A7's default except rest encounters (0 on all four: no slot rolls in-band tiers that fit) and Q33 (superseded). XD-18: 40 cloud dragons plus the King, the tax door ejects. FD-02: new Ghost and Phase Mummy tiers on `xeen_mummy`; X6 return point corrected; crypt arch 288; traps ≤ 25 % per run; two event-given Might Boosts. FD-03: new onyx tiers; gongs raise a dais in an open stairwell. FD-04: Dragon Tower key in FD-01; crossword 42 Down → Winterkill; terminal code COMPUTER answered by FD-03's heads; ordinary-HP liches. X9: `entrance:fd04_roof` at [20352, 17280], Q-F1 there, no monsters. Detail: `mockups/act6_a7_decisions.md` | A7, A2, A3, A4, A5, A6, A8, S, orchestrator |
