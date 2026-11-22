# Phase 4, lane A7's graphs XD-14, XD-15, XD-20, DD-23, DD-07: decisions (D-39)

Decider D-39, 2026-11-20. Wins over the graphs in `act4_graphs/` and `act4_dungeon_graphs.md` where they differ.

**APPROVAL**

All five graphs are approved for L1–L4, each with changes. Where this answer and the graphs or the page disagree, this answer wins.

- **XD-14 Castle Basenji: approved with changes.**
  - The Cult Acolyte and the Basenji Cult Leader each get their own skin on `xeen_sor1`, made by recolouring. The Leader must not wear Valio's `xsor_b` (D-10, D-32 Morgana).
  - Curse scrolls hit only the member who reads them.
- **XD-15 The Sphinx: approved with changes.**
  - The belly hall shows two carved throne doors, the crown and the veil. The mask is carved on the Queen's loose panel, which stays the secret way to the Thieves' throne. As drawn, a third sealed door opened onto nothing.
  - The drop cell's door stays open once opened from inside.
  - The drop's damage comes from the event (see Q5).
  - Starburst is an Air spell, not Light: label the two books correctly.
  - The Might potions follow D-22's event pattern (see Q4).
- **XD-20 The Warzone: approved with changes.**
  - The booth window on the floor is low enough to click from the sand. The playtest clicks it from the floor.
  - The sky faces sit at least 1,280 above the sand.
  - The victors' gate works at any time. Leaving before the win forfeits that challenge.
- **DD-23 Gargoyle Lair: approved with changes.**
  - `open_sky` names a Darkside preset, never `xeendark1` (lanes rule).
  - There is no falling snow, because indoor maps have no weather. Snow is a floor texture under the crack.
  - The doorless S band goes as an exception line in NOTES.md.
- **DD-07 Eastern Tower: approved with changes.**
  - The Book of Great Power's refusal must read as final, so nobody goes looking for a key.
  - The playtest asserts that a floating mage engages the party across the well (D-4's XD-26 pattern).
  - The two new tiers get looks and skins distinct from the Mystic Mage.

General rule for all five: rest encounters are 10 % from each map's own hostile rows, and 0 in XD-20 (D-33/D-34). No placed-only or peaceful row may ever be picked for a rest encounter.

---

**XD-14 Castle Basenji**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| 1 | Option (a): 45 monsters, including 16 Cult Acolytes (level 24, new wizards row 11197, Fire Bolt E). Kill XP 14.00k; the XD-14+15 group is 26.85k, +6 %. | The cult needs rank and file inside the 22–45 band. Wolfman 20 is under the band, and 38 monsters is under the M floor. +6 % is inside the act rule. | A2: row 11197, add Basenji to the wizards' `where`, Act IV recount. S: acolyte skin (recolour, `xsor_d` for example). A7: place them. | Cheap until placement |
| 2 | Option (a): a new wizards boss row 11198, "Basenji Cult Leader", level 45, hp_x 3, IceBlast and Fireball, blink 0.2, own skin. | It is a different cult from DD-05's heretic "Cult Leader" 11223, and each named boss gets its own row (ROADMAP §0). | A2: row. S: skin (dark robe with wolf-grey trim, no Meshy). A7: place him in the study. | Cheap |
| 3 | Option (a), as proposed. Blessings once per character: +2 Intellect, Personality, Speed; +5 Fire, Air (Electricity), Mind (Magic), Earth (Energy). That is 7 player bits. Curses on every read, on the reading member only: Depression → Afraid, Confusion → Drunk, Insanity → Insane, Weakness → Weak, Death → Unconscious, Aging → ten years. The second Magic scroll reads "The writing has faded." | D-4's sizes. Names show on hover, so reading is a choice, not a trap. Thaddeus's fountain gives the years back after Q-D18. Dead and 25 years would be beyond the curve. | A3: 7 bits from the free block after 11317, the condition and age lines. A2: values in the Act IV ledger. A7: place the scrolls. | Cheap |
| 4 | Option (a): new madmen row 11233 "Trapped Peasant" (level 4, Insane Beggar look, faction `basenji_prisoner`, friendly, placed only, NoArena, not counted). He talks through the bars at any time (`q-c8.peasant`). After the jailers' lever, a click frees him: "Thank you for saving me!", 500 experience per member once, through a new hook `q-c8.peasant_freed`. He is hidden on every later load. | D-25: a peaceful figure is its own row. Freeing him matches the source and D-27's prisoners. It gives the dungeon an errand and a second source for the password. | A2: row and faction. A3: hook and 500 XP in the Act IV ledger. A7: bars, lever, playtest. | Cheap |
| 5 | Option (a): the dormitory door is barred from inside. From the landing: "The door is barred from the other side." Opened from the dormitory, it stays open. | The wing is entered by the password. The tower loop stays open without it, and the wing loop works after. | A7 | Cheap |
| 6 | Option (a): the interior is larger than the X6 shell. | As in shipped interiors and DD-02, DD-05, DD-06. | A7. A5: nothing. | Cheap |

**XD-15 The Sphinx**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| 1 | Option (a): +2 per throne, once per character (bits 11300–11303). The prize is four thrones plus the award. | D-4's rule for permanent rewards. +5 would break the rule for one map. | A3: four throne texts, the Q-C9 header and rewards line. A2: Act IV values. | Cheap |
| 2 | Option (a): five clue walls, one clue each (drop cell, west hall, east hall × 2, library), plus A3's whole text as the library's end-wall summary. Each plaque is used once per face. | The dungeon gives the answer as the source does. A party that came by the stair still finds all five in the library. | A3: ORIGINAL_LINES rows as map-local signs. A7: place them. | Cheap |
| 3 | Option (b): Starburst (Air) and Divine Intervention (Light) spellbooks on the legend throne's lecterns. Teleport and Item to Gold are dropped for two fixed T4 gem finds in the library. | MM7 has both spells. The other two don't exist in MM7, and Town Portal or Lloyd's Beacon come too late to matter. | A2: fixed items and gem sizes. A7: lecterns and finds. | Cheap |
| 4 | Option (a), the D-22 way: Might ≥ 40 on the clicking member, potions and spells counting. On the haunch vault chest's first opening, an event gives two Might Boosts (`evt.SetHeldItem(240, {bonus = 10})` twice, once per game behind a map qbit, "Two flasks of red draught …"). The chest holds no random Might Boosts. | One Might rule with fixed potions, scaled from XD-08's 30 for party levels 15–17. The "placed potion" wording is replaced by D-22's event. | A7: event and qbit. A2: record the fixed potions. | Cheap |
| 5 | Option (a): the disc sinks with `xeen_sphinx_stir`, the party is moved to the drop cell, and the disc rises after 2 s. Damage is a fixed event amount of about 10–15 % of a level-31 member's HP, never lethal to a healthy party. The disc asks again on every step until the name is given. | A move inside the map gives no physical fall, so the event must deal the damage. A visible drop answers "the floor agrees with it". | A7: event, playtest of a wrong name then the climb back. A1: only if the move is lost after the door event. | Cheap |
| 6 | Option (a): XD-15's dungeon row becomes 22–45, keeping Sand Golem 22 and Stone Golem 26. | §0's group row is the governing table. X6's own golems are the source's "Stone and Earth Golems". | Orchestrator: MAPS dungeon row 28–45 → 22–45. | Cheap |

**XD-20 The Warzone**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| 1 | Option (a): the arena range is 11010–11699. NoArena goes on every boss, every peaceful or placed-only tier (King's Guard, Clan Survivor, Hobstadt's Guard, Inner Circle Guard, Kennel Sabertooth, Trapped Peasant …), the octopods and the Kraken, and any row taller than about 1,000. | Like MM7's arena, it draws from the whole bestiary. The coach serves both faces. The engine already skips NoArena and Peasant rows. | A2: the NoArena kind on those rows. A7: the scene's `arena` block with 20+ marks. | Cheap |
| 2 | Option (a): kill XP is not counted in any act. Gold follows the engine's tiers, and the awards are 46–49 with Xeen wording. | MM7 style (D-8.1). The gold is the reward. | A3: award rows 46–49 (for example "Won a Page's battle in the Warzone"). | Cheap |
| 3 | Option (a): A4 adds an X6 NPC with a personal name and the title "Arena Master" (D-21's title column), topic 704, greeting aaze0085:0 and decline :1. The lodge's and the floor's booth windows both call him. | The engine needs an NPC with topic 704. The line "No. Goodbye..." has no source. | A4: NPC. A3: ORIGINAL_LINES aaze0085:0–4 and the adapted victory line. Orchestrator: MAPS line 439 → aaze0085:0–4. | Cheap |
| 4 | Option (a): no gong for now. The engine's 14060 stays. | A step-event gong would also ring after a win. Only a start hook would do it right. | A1: nothing now. AU: the gong waits for a start hook. | Cheap |
| 5 | Option (a): an open-sky crater floor (`sky: true` with X6's clear preset). Ring wall 512, sky faces at least 1,280 above the sand. | Dragons at Knight and Lord need room. A roofed hall would push the dragons out of the pool. | A7 | Medium after build |

**DD-23 Gargoyle Lair**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| 1 | Option (a): 15 monsters, 5.13k. The group is 105 monsters and 32.84k, +8 %. | The S floor, as A8 assumed. The group stays inside 10 %. | A2: Act IV recount. | Cheap |
| 2 | Option (a): one Gargoyle Overlord 45 on the highest rock, no boss row. | D4's own top tier, inside the group's 24–45. The roost wants one big one. | Orchestrator: MAPS DD-23 dungeon row 24–40 → 30–45. | Cheap |
| 3 | Option (a): MM7 7d07 grey rock, MM6 straw on the nest, snow as a floor texture under the crack. | Distinct from XD-26's brown 7d36. | A6: dungeon_families line for DD-23. A7. | Cheap |
| 4 | Option (a): no doors. A natural cave with D4's open mouth, plus one exception line in NOTES.md. | The doors band is for built dungeons. XD-26's caves are the precedent. | A7 | Cheap |
| 5 | Option (a): the rocks stay broken and the remaining gargoyles stay. No stage. | One quest, one map. Nothing in the source thins them. | — | Cheap |

**DD-07 Eastern Tower**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| 1 | Option (a): new rows Floating Adept 28 (11203) and Floating Magus 38 (11204), Mystic Mage 45 on top, and two Floating Eyes 40. `fly: Y` on the whole floating-mage family. The new tiers have looks distinct from each other and from the Mystic Mage. | Floating is the tower's character. The Gamma Gazer at 65 is far over the band. | A2: rows, fly flag, the Eastern Tower in the eyes' `where`, recount 11.57k. S: two colour tiers when the family is bound (D-10). A7: playtest of mages across the well. | Cheap |
| 2 | Option (a): M by size, with D-9.3's 30 monsters. | D-9.3 stands. Four floors and a well need M size. | — | Cheap |
| 3 | Option (a), with one change. The fountain gives +1 to every statistic, once per character. The Book of Fantastic Knowledge gives +2 Intellect once ("Your intellect is already fantastic!" after). The Book of Great Power refuses with a final line, for example "A magic aura pushes you back. The book answers to no one living." The vat is dressing. The Fountain of Life heals. | MM6–MM8 sizes (D-27's +1 all). A refusal that sounds conditional would be a riddle the game never answers. | A3: two player bits after 11317 and the lines. A2: Act IV values. | Cheap |
| 4 | Option (a): a door of light fed by two destructible pylons, with XD-04's light texture. The door's click explains both beams. | The pylons give L3 its errand and its loop. Nothing to carry, and the door's own text answers the puzzle. | A7 (destructibles exist) | Cheap |
| 5 | Option (a): the mirror is flavour only, with `xkmirror`: "The mirror does not respond." | Consistent with DD-02 (D-26, D-37). | A7 | Cheap |
| 6 | Option (a): MM7 7d14 for the L4 laboratory and study. | A mage's laboratory on the other face from XD-12. DD-02's 6d19 is on the same face. | A6: dungeon_families line. A7. | Cheap |
| 7 | Option (a): the interior is larger than the shell. | Same as XD-14 Q6. | — | Cheap |

**Other lanes, in short:**

- **A5:** the inside arrivals and return points `entrance:x6_gate`, `entrance:x6_paws`, `entrance:x6_yard` and D3's `entrance:d3_door`, as on the page. Doors stay sealed until each map is installed.
- **A6:** `entrance:d4_mouth` and its return point, plus the three dungeon_families lines (7d07, 7d14, 7d05).
- **Orchestrator (MAPS):**
  - XD-14's dungeon row becomes "24–45, Basenji Cult Leader 45".
  - XD-15's dungeon row becomes 22–45.
  - DD-23's dungeon row becomes 30–45.
  - The XD-20 line (439) becomes aaze0085:0–4.
  - Record the recounts: XD-14+15 26.85k (+6 %), DD-05+20+23 32.84k (+8 %), DD-07 11.57k (+3 %).
- **A1:** nothing required.
