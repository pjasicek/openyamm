# Phase 4, lane A8's graphs DD-05, DD-12, DD-14, DD-19, DD-20: decisions (D-42)

Decider D-42, 2026-11-20. Wins over the graphs in `act4_graphs/` and `act4_dungeon_graphs_a8.md` where they differ.

**APPROVAL**

All five graphs are approved for L1–L4, each with changes. Where this answer and the graphs or `act4_dungeon_graphs_a8.md` disagree, this answer wins.

- **DD-05 Western Tower of Mok: approved with changes.**
  - Humble and Pious get two named peaceful rows, not one shared "Penitent Cleric" (Q4).
  - The Cult Leader gets his own recoloured skin, distinct from the Heretic Lord's `xcle_f`. He is the same level, so only his skin and hp_x 3 set him apart.
  - The four fountains (+5 Water, Body, Fire, Air) are once per character. They need four player bits from A3, which A8's request list left out.
- **DD-20 Lakeside Coven and Sewer: approved with changes.**
  - The Guild uses the back cellar door (Q4 (b)). D4's L4 has already built it as a hatch in the Guild's west wall.
  - That door's return point moves beside the hatch.
  - The Head Witch gets her own skin.
- **DD-12 Dungeon of Lost Souls: approved with changes.**
  - The maze's SHELTEM letters must read on the automap at L1. If they do not, it becomes a plain labyrinth.
  - Rename nothing. The tower stays where D4 built it (see Q-extra).
- **DD-14 Castle Blackfang: approved with changes.**
  - The landing's arrivals follow D-37's naming: `entrance:d6_griffin` from D6's `m25.flight` and `entrance:d4_griffin` from D4's gate. They may share one spot on the landing. `entrance:griffin_walls` is dropped.
- **DD-19 Wizard Quarter: approved with changes.**
  - Morgana drops to 60 (Q1).
  - The ward's click must name the two lamps, so the door is not an unanswered puzzle.

**General rules for all five**
- **Rest encounters** are 10 %, drawn only from families whose rows are hostile and inside the band. Never a placed-only or peaceful row (D-33, D-34, D-39). The families per map:
  - DD-05: heretics.
  - DD-20: sewer stalkers only.
  - DD-12: minotaurs.
  - DD-14: vampires.
  - DD-19: sorceresses, not the wizards (Master Wizard 60 is over the band).
- **Open sky on the Darkside.** DD-19's court, DD-14's courtyard and DD-12's broken roof use the preset `xeen_darkside_fading`, which is the sun in Act IV before M27, and never `xeendark1`. If A3's `Xeen.Stages.darkside_sun` can switch an indoor map's `open_sky` preset the way it switches D3's sky, these switch to `xeen_darkside_failing` after M27. No A1 work is asked for.
- **Act IV kill XP** after this answer is about +2.5 % on the act's MAPS rows, well inside the 15 % gate.

---

**DD-05 + DD-20 group**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| G | **45 each, at the M floor.** The group is DD-05 45 (14.29k), DD-20 45 (13.42k) and DD-23 15 (5.13k): 105 monsters and **32.84k, +7.7 %**. That is D-39's figure exactly; A8's 33.0k used 5.3k for DD-23. | Cutting to MAPS's 100 would leave two M dungeons at about 33 monsters, under the M class floor. That breaks WORLD_DESIGN §6 to save 2.3k XP, and the group stays inside ±10 %. | A2: Act IV recount. Orchestrator: MAPS §0 row note "105 monsters, 32.84k (+7.7 %)". | Cheap until placement |

**DD-05 Western Tower of Mok**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| 1 | As G. | — | — | — |
| 2 | Golems as Mok's guardians (a): Stone Golem 26 (5) and Iron Golem 40 (3). No relation between heretics and golems; each family is only hostile to the party. | The warded door and the fountains get a reason, and the floors read apart from the clerics' floors. Inside the band. | A2: add the Western Tower to `material_golems`' `where`. A8: check the Iron Golem fits under the door hall's ceiling. | Cheap |
| 3 | The Cult Leader is a new heretics boss row **11223 "Cult Leader"**, level 45, look C, hp_x 3, Psychic Shock and Harm, key `mok_cult_leader`. He is not XD-14's Basenji Cult Leader 11198. He gets his own recoloured skin on `xeen_cle`, for example white-and-gold vestments daubed with the heretics' sign. | The quest kill must be in reach of a party of 35–39 arriving on his floor, and the source's 55 is over the band (D-4). D-39 already named the other one "Basenji", so the source name stays here. | A2: the row. S: the skin. A8: place him with his group in the chapel. | Cheap |
| 4 | Humble and Pious stand in cells behind doors, as **two named peaceful rows** in the characters block: **11910 "Humble the Cleric"** and **11911 "Pious the Cleric"** (11906–11909 go to DD-20's prisoners). Each has its own friendly `character_<key>` faction, the heretics' cleric body (A2 picks the stand_in, not a peasant), is immobile and is not counted. Clicking either runs the map's question. Either answer hides him for good, with no XP. | D-25 and D-27: peaceful figures are their own rows, and DD-09's prisoners are named. A3's texts call them by name, so the hover should too. | A2: two rows and factions. A8: cells, doors and a playtest of No and Yes for each. | Cheap |
| 5 | Discs (a): the first disc alcove clicked runs `q-d6.l1_alcoves` (2 disks). Both pictures clear and both alcoves read "The alcove is empty." | A3's hook already gives two, and its text speaks of "the alcoves". | A8 | Cheap |
| 6 | The inside is larger than the outside (a). | As DD-02, DD-06 and D-39's XD-14 and DD-07. | — | Cheap |
| + | D1 changes:<br>- a window (`hkm3elw`) directly above the rope's top on the north face;<br>- the rope's return point faces **512**, away from the wall;<br>- a column of arrow slits above the rope if a shipped slit texture fits D1's kit, otherwise A3 drops "past the arrow slits" from `tower_rope`.<br>Fountains are once per character, +5 each. | The climb's text must match what the player sees. | A6: window, facing, slits and registering `xmoktap`. A3: four player bits and fountain texts (and the rope line if needed). A2: +5 × 4 in the Act IV ledger. | Cheap |

**DD-20 Lakeside Coven and Sewer**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| 1 | As G. | — | — | — |
| 2 | **11173 "Head Witch"**, a coven boss at 45, look C, hp_x 3, DrainSP and Mind Blast, key `coven_head_witch`. Her group is three. She gets her own skin on the witch model, distinct from the coven tiers. She shares a display name with XD-04's 11163; the two never share an act. | The quest kill must be in reach of a party of 35–39, the source's 60 is over the band, and A3's texts say "Head Witch". | A2: the row. S: the skin. | Cheap |
| 3 | The four prisoners are named peaceful rows **11906–11909**: Camilla the Captured, Aretha the Helpless, Isabella the Victim, Rhett the Wimp. They use peasant bodies, are immobile and friendly, and are not counted. The cage's click runs the hook. Each is hidden by its freed bit at once and on load. | DD-09's pattern (D-27). | A2: rows. A8: cages and playtest. | Cheap |
| 4 | **(b), the back cellar door.** D4's built west-wall hatch is `door:dd20_guild` and arrives at `entrance:d4_guild`. Before `riddle_answered` it reads "A cellar door. The front door asks first." Its return point moves **beside the hatch, facing west**. The front double door stays the house, the riddle and the trapdoor (`entrance:d4_trapdoor`, one way, no return). The jetty shaft stays as built (`door:dd20_sewer` to `entrance:d4_shaft`, D-36). | One door per destination, as MM6–MM8 towns do, and A6 has already built it. A choice prompt on a house door would be a new pattern. | A6: move the return point, check the hatch's sealed text, playtest. A3: `guild_right` adds that members use the cellar door round the back. A8: the three arrivals as named. | Cheap |
| 5 | Joseph is left out (a); his line goes to the ORIGINAL_LINES ledger. | Teachers follow A4's plan, and the sewer has its dead men. | A3: ledger. | Cheap |
| 6 | The brewery's three cauldrons give +2 Personality, Endurance and Speed, once per character. "You have had your fill." after. | D-4's size, and one permanent-effect device for an M dungeon. | A3: three player bits and texts. A2: Act IV ledger. | Cheap |
| 7 | The cross's ambush: five hidden, shown on the first step, kept after reload (D-18). | The journal's "out of nowhere". | A8: a playtest step. | Cheap |
| + | Two plain street grates on D4's square over the sewer's lit grates, with no event and not counted as POIs, if they fall on open paving. | The daylight inside should have a source outside. | A6 (optional) | Cheap |

**DD-12 Dungeon of Lost Souls**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| 1 | Minotaurs only (a): 30 / 12 / 3, 23.79k (+1.2 %). | The gorgons' bronze tier and Stone touch already vary the fights, and the story makes them the coven's rejects. | A2: confirm the mix and the `where`. | Cheap |
| 2 | Two-stop lift (a), in a closed shaft from the aviary to L1's lift head. It runs only once `m24.bird_freed` is set, so it can never skip a gate going down. | Five floors back with nothing left to do is dead time, and it needs no second Isle door. | A8 | Cheap |
| 3 | SHELTEM in the maze's walls (a), the throne in the L. **If the letters do not read on the automap at L1, build (b)**, a plain labyrinth. | It is the source's identity and an optional third answer-giver for M33, and it spoils nothing before M28. | A8: an L1 automap capture. | Cheap at L1 |
| 4 | **Six stat birds at +2 each** (a). Each is freed once (a map variable) for the members present: +12 per member. | D-4's size. XD-08's seven juices (+14) set the precedent, and it is the reward for the deepest walk. | A2: +12 in the Act IV ledger. A8: the aviary's events. | Cheap |
| 5 | **Soul Waters as experience** (a): once per drinking member, L3 1,000 and L4 2,000 (3k per member). | It keeps the source's joke as a small real reward. Act IV already gives +40 resistance points per member (XD-14 and DD-05), so more resistances would pile up. | A3: two player bits and texts. A2: ledger. | Cheap |
| 6 | A No at a gate (a): the gate stays shut and asks again; no wave. | The joke is the question, and the count stays 45. | A8: playtest of No then Yes at gate 1. | Cheap |
| + | Q-D25's level goes **32 → 38** (M24's). D4's `door:dd12` names `arrival: entrance:d4_isle`. Without the key it reads "Locked. Two iron-bound leaves, and a keyhole." The tower stays where D4 built it (the path over the knoll is fine), provided it is at least ~1,000 across, roofless and reads as a ruin. | — | A3: Q-D25 level and the refusal line. A6: arrival, width check, registering `xlsplaque`, `xlsgate`, `xlsglass`. | Cheap |

**DD-14 Castle Blackfang**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| 1 | **(a) Ambrose waits on the walls and flies both ways**, from `m25.done` on with no end. The gate itself never opens.<br>- **On D4:** after `m25.done`, a click on the gate asks aaze0021:9, "Would you like my griffin to fly you inside?" Yes goes to `entrance:d4_griffin`.<br>- **On the landing:** Ambrose (5512) stands beside his griffin and asks aaze0045:1, "Are you ready to leave this awful place, friends?" Yes sets the party down at D4's **`entrance:dd14_griffin`**, cell (76, 54), facing west.<br>- **D6:** keeps its Ambrose and the flight.<br>- **The griffin:** the same figure D6 uses, placed only and not counted.<br>- **After the cure:** `m27.ambrose_return` from the Queen's crown topic still flies everyone to D1. | Without it, the two visits M27 needs (the Queen, then the crown) have no way out but spells. It is the source's loop, keeps the castle griffin-only (D-36) and needs no new geometry. | A3:<br>- `m25.flight`'s text becomes "Ambrose sets his griffin down on the walls and waits.";<br>- two new hooks, for example `m25.gate_flight` (D4) and `m27.fly_out` (DD-14);<br>- the crown topic's `do` calls `m27.ambrose_return`.<br>A4: Ambrose placed on DD-14's landing, shown from `m25.done`, with the leave topic.<br>A6:<br>- D4's set-down point;<br>- the gate's second state;<br>- the D4 playtest step;<br>- D6's flight targets `entrance:d6_griffin` (phase 5);<br>- register `xbfcrest`.<br>A8: both arrivals, the griffin figure, a playtest both ways. | Cheap |
| 2 | Royal Vampire 58 (a): vampires tier D **11295**, look C, Curse, placed only (DD-14). He is the Count's three guards. 40.91k (+4.4 %). | The source's elite tier, inside MAPS's 36–58. | A2: row and recount. S: a tier skin when the vampires are bound. | Cheap |
| 3 | Gargoyles on the walls (a): Sentinel 38 (10) and Overlord 45 (2). | Stone on the battlements against the bat storm reads at once, and 51 vampires alone would read alike. | A2: add Castle Blackfang to `gargoyles_mm`' `where`. | Cheap |
| 4 | Octopods stationary in the cistern (a), D-36(2)'s own fallback. The playtest asserts each can be reached and can hit back. Swimmers later, only if A1's water facts come to cover BLVs. | No A1 work now. | A8 | Cheap |
| 5 | Sleepers still rise after the Count's death (a); the lids slam as flavour. | One rule for every coffin. | — | Cheap |
| 6 | The source's refusal (a): aaze0047:0, "A force like wind pushes you back … You are unable to descend." The bar is a plain iron leaf. | The landing's note ("The Count's magic keeps us from descending") answers it, and A3's text put him "above". | A3: `m27.dungeon_stair` `fail_text`. | Cheap |
| 7 | The roof trapdoor is drawn now (a), bolted ("Wind howls over it."). The D7 lane decides in phase 6. | One leaf now spares a later rebuild. | A8 | Cheap |

**DD-19 Wizard Quarter**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| 1 | **Morgana 60, not 65.** MAPS reads "32–55, Xenoc 60, Morgana 60". 24.7k (+3.8 %). | D-4: no monster over the band, and Xenoc 60 is the listed top. Both are required kills at quest level 39, so the two guild heads stand equal. Her blink and own skin still mark her. | A2: row 11183 level 65 → 60. Orchestrator: MAPS. | Cheap |
| 2 | Casters, Carnage Hands (12) and four Iron Golems in the vault (a). No fighting among the four families. | Not every fight is a caster duel. Casters alone would need rows under or over the band. | A2: no-infighting relations, and fix the stale `stand_in: Druidess` in the sorceresses' header. | Cheap |
| 3 | The court is under open sky (a), with the general preset rule above. | The gate opens onto the quarter the city promised. | A8 | Medium after build |
| 4 | **D3 shows the precinct (a):**<br>- north of the city wall between x 40 and 47, a walled precinct with two gabled pink hc hall roofs and the bridge's roof over a court wall;<br>- no entry from outside;<br>- if the dunes there are not clear, the nearest clear spot behind the gate.<br>D3 is then rebaked. | Otherwise the gate in the outer wall plainly opens onto empty dunes, which a player walking round sees. | A5: D3 edit, rebake, re-shot. Also `door:dd19`'s arrival `entrance:d3_guild_gate` facing north, and the return point at about (−10496, 22150, 1728) facing south. | Medium |
| 5 | Blastem is a talking actor (a). "The lesson" turns him into Sorcerer 11191, the Valio pattern. "Boots licked" gives aaze0031:112 and a hint at the mirror. | A second answer-giver for the mirage wall, in the source's voice. | A4: NPC row and portrait (greeting aaze0031:51). A3: topic and swap. A8: place him. | Cheap |
| 6 | Two ward lamps feed the ward (a), with XD-25's `xufield` reused (no new texture). The ward's click names both lamps, for example "The ward draws on two lamps, one above and one below." One lamp out: "The ward thins, but holds." | It gives the HQ its errand, and the door's own text answers it (D-39's DD-07 pylons). | A8 | Cheap |
| 7 | The font refills spell points and is repeatable (a). | MM wells next to the hardest fights, as XD-13's YOUR well. | A8 | Cheap |
| 8 | Nothing changes inside after `q-d14.done` (a). | The living guilds are D3's five houses. | — | Cheap |
| + | The Orange (+2 Intellect) and Purple (+2 Speed) potions are once per character. | D-4. | A3: two player bits and texts. A2: ledger. | Cheap |

**Orchestrator (MAPS)**
- §0 rows:
  - DD-05+20+23: note "105, 32.84k (+7.7 %)", band "24–45, Cult Leader 45, Head Witch 45".
  - DD-12: 23.79k (+1.2 %).
  - DD-14: 40.91k (+4.4 %).
  - DD-19: "32–55, Xenoc 60, Morgana 60", 24.7k (+3.8 %).
- Dungeon list rows:
  - DD-05: "25–45, Cult Leader 45".
  - DD-20: "25–45, Head Witch 45".
  - DD-14: add "Ambrose's griffin both ways (D4's gate)".
  - DD-19: "Xenoc 60, Morgana 60".
- **A1:** nothing required.
