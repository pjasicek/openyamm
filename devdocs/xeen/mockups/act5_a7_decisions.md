# Phase 5, lane A7's graphs XD-16, XD-19, DD-16, DD-24: decisions (D-47)

> Orchestrator note (2026-11-21): Q20's stage line (Corak shown on `m29.done`) is replaced by D-51
> (`act5_a7_followups_d51.md`): Corak stands inside a translucent stasis field from the first load.

Decider D-47, 2026-11-20. This answer wins over the graphs in `act5_graphs/` and over `act5_dungeon_graphs_a7.md` wherever they differ.

**APPROVAL**

All four graphs are approved for L1–L4, each with changes. None needs a redraw. Where this answer and the graphs or the page disagree, this answer wins.

- **XD-16 Volcano Cave: approved with changes.**
  - The stairs are just walked. aaze0047:0–1 and aaze0048:0–1 ("Down Level?" / "Up Level?") go into the ledger as meaning only. No stair inside one map asks a question or shows a sign. The map still has more than three original lines (the altars, the chests, the skull).
  - Every lava basin sunk 128 has an edge the party can step out of. A party that falls in can always walk out burning, and never dies trapped (Q5).
  - The trap chests' tell must be readable in a tour shot from about 3 m (Q2).
  - The way's slab opens during the visit in which the second skull breaks, not only on the next load (Q4).
- **XD-19 Castle Xeen: approved with changes.**
  - **Guard pool.** The four hidden guards stand at the two machines' output chutes in the foundry, not behind the bays' shutters.
    - The timer starts at the party's first step into the foundry.
    - Destroying both machines shows every guard still hidden and opens the bays (the gem find).
    - The count is therefore always 70 (Q7).
  - **Own skins for the two bosses.** Lord Xeen (11634) today wears `demon_c` on `mm6_demon`, the same skin as the Screamers and Barkman. Xeen's Pet (11644) uses the Fire Dragon's look C. Each gets its own recolour skin; no Meshy (D-39, D-42 boss skins).
  - **Lord Xeen's immunity** goes through E11 on the existing map damage hook, not through a new behaviour hook or a row field (Q12). A2 sizes his HP for a single sword-wielder.
  - **The scepter** is a real choice, so it asks a question, because taking it ends the visit (Q14, D-24).
  - **Xeen's Slayer Sword** must not be lost before M35 (see Q12's WHO ACTS).
  - **The aviary's open sky** names the preset `xeen_cloud_sea`, X9's sky.
  - **The keeper's walk round the Pet stays.** The Pet is not a gate: `m35.scepter` needs only `lord_xeen_slain`.
- **DD-16 Corak's Pod: approved with changes.**
  - **The Main Power Console has a visible effect:**
    - the pod's lights come up;
    - panels swap from `sfpnloff` to `sfpnlon`;
    - the blast door's lamp turns from red to green.
    The blast door's refusal names the missing power.
  - **The breach's lava** is `floors: lava`, off every walking line.
  - **Corak cannot be killed** (Q20).
  - **Rest encounters** are eyes at Dif 0 only (Q21).
  - **NOTES exception line** for 7 monsters under S's floor of 15.
- **DD-24 Giants' Hall: approved with changes.**
  - The People's tiers are 38/50/58, not 36/50/62. MAPS's band stays 38–58 (Q23).
  - `q-d16.hall_attacked` is a quest qbit that the relations read. No route gives the party four disks (Q22).
  - The smoke hole's `open_sky` follows D-42's sun-stage rule: `xeen_darkside_failing` in Act V, and `xeen_darkside_day` after M33 if the stage switch reaches indoor maps. Never `xeendark1`.
  - The People rows also serve Gurodel's hold on D5, so the hall and the hold are one faction.

**General rules for all four**
- **Rest encounters** draw only from hostile families inside the band (D-42, D-46):
  - XD-16 and XD-19: demons at Dif 5.
  - DD-16: eyes at Dif 0.
  - DD-24: encounter 0.
  - Never a placed-only or peaceful row, never a construct, never a Gamma Gazer.
- **Every exit** is the `exit` preset (D-24). Every inside entrance is named after the map it is entered from (D-37).
- **No Meshy is required** for these four maps. `xeen_guard` (D-19) is already queued. No binding uses `worlds/mm9/` (D-44).

---

**ANSWERS**

**XD-16 Volcano Cave**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q1 | **(a).** 40 monsters of the demons family: Demon 42 × 20, Devil 50 × 14, Screamer 58 × 6. 27.34k (+2.8 %). One NOTES line for 40 under M's floor of 45. | 40 is MAPS §0's own count for this row. The family's `where` names the Volcano Cave. DD-07 was accepted under M's floor in the same way (D-39). | A2: row 9142 and the Act V recount. A7: placement and the NOTES line. | Yes, cheap until placement |
| Q2 | **(a), sharpened:**<br>- five trap chests, each with a faint ember glow and wisps of smoke (a small decoration or effect under each); the real chest has neither;<br>- all six hover as "Chest";<br>- a trap deals Fire event damage of about 50 to each member (about 10–15 % of a level-48 member's HP, never lethal to a healthy party), once per chest (118055–118059): "The chest explodes!";<br>- after that: "The chest is empty."<br>- one real T5 chest. | MAPS names the exploding chests as the map's feature. A tell the game shows keeps it from being a blind riddle (D-4). Fire damage makes X7's daily Shrine of Fire a real choice (D-40 Q2). Option (c) would push the map to 11 chests, over M's 3–7. | A3: the two map-local lines and the ORIGINAL_LINES rows aaze0046:2 and :6. A7: the chests, the tell, a playtest that opens one trap and the real chest. | Yes, cheap |
| Q3 | **(a).** Four lever stones round the pillar, each lowering one of four slabs across the gate run.<br>- The slabs are in sight of the pillar (the gate run opens off the lever hall).<br>- Each lever's hover names its slab, for example "First slab".<br>- A slab grinds down when its lever is pulled.<br>- One-way. A second click reads "The lever is down." | A visible effect at the lever. Undoing a lever would do nothing, so it stays one-way (D-43). The four slabs keep the source's switches. | A7 | Yes, cheap |
| Q4 | **(a).**<br>- The rock slab is a door. The skull event that sets `q-c26.done` moves it in the same visit. On every load with `done` it stands open (map qbit 118054).<br>- Before `done`, the rock's click gives `q-c26.way`'s `fail_text`.<br>- The hook's `text` ("Beyond the last cave, cool air…") shows at the first step into the cool passage.<br>- The passage's end is the `exit` preset to XD-17's `entrance:xd16_way`.<br>- XD-17's way back arrives at `entrance:xd17_way`. | A3's hook texts already speak of a door ("rock grinds on rock"). A slab needs no new word, and a lift bridge would add a mechanism with no return value. D-40 (3) makes this the only first way in. | A7: slab, plate, exit. A3: confirm where the `way` hook is placed. A5: the two XD-17 names. | Yes, cheap |
| Q5 | **(a).** The lake, the river and the heart are `floors: lava`, sunk 128 with crust edges, and every basin has an edge to step out of. The causeway and the stepping crust are plain floor. | "Lava is lava" (D-40), as XD-03 and the studio's lava already work. | A7 | Yes, cheap |
| Q6 | **(a).** 10 % from the demons at Dif 5. | Screamer 58 is the band's top (42–58). D-39's rule. | A2: row 9142 | Yes, cheap |

**XD-19 Castle Xeen**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q7 | **(a), placed as in the APPROVAL.** Two destructible machines with the source's "Destroy?" question (aaze0075:0–4).<br>- While either machine stands, a 45 s timer (started on the first step into the foundry) shows one of four hidden guards at a chute and sets it on the party.<br>- Both machines destroyed: the shutters open on the gem find, and any guard not yet released is shown.<br>- Kill XP is always 54.38k. | A fixed pool keeps the count and the XP known, using the existing word for showing a hidden actor (D-18). Option (b) has a summon count nobody can know in advance. | A7. A1: only if a timer cannot show a hidden actor. | Yes, cheap |
| Q8 | **(a).** The "X Generator. Destroy?" question breaks the destructible by event, and blows and spells also break it. One `on_destroyed` calls the hook. The same applies to the two machines. | It is a real choice (D-24), and destructibles with `on_destroyed` already exist. | A3: the four hooks' `where` texts naming the renamed generators. A7. | Yes, cheap |
| Q9 | **(a).** One field before the crown stair. Four pylons go dark one by one, and each pylon's hover names its generator's tower or vault. | A3's single `barrier` hook. The pylons answer the puzzle in the game itself. | A3: the `m35.barrier` text. A7. | Yes, cheap |
| Q10 | **(a).** New tiers 11624 Lesser Air, 11625 Lesser Water and 11626 Lesser Earth Elemental, each at 55.<br>- Each is immune to its own element; the family's `fire: imm` does not carry over to them.<br>- Bound to installed models: MM6 `mm6_aie1` (air), MM7's earth and water elementals.<br>- Two per generator. | Elemental generators read through their guards. The models already exist, so no Meshy is needed. | A2: rows. S: bindings and tier skins. | Yes, cheap |
| Q11 | **(a).** None placed. | Flying Feet, Guardian and Carnage Hand are all under 42 (D-4). Xeen's Guard is the castle's construct (D-19). | — | Yes |
| Q12 | **Adjusted (a): A1's E11 on the existing map hook.** The indoor `MonsterDamage` map hook already overrides damage (`evt.SetHookDamage`, used by MM9 maps). A1 adds to its context the striking member's weapon item id and the attack kind: melee, missile, spell or other. That is ROADMAP §7's E11, "the weapon in the damage hook". There is no behaviour `onDamage` and no row field.<br>XD-19's hook does the following:<br>- for monster 11634, it zeroes everything except melee with item 12500;<br>- the first zeroed hit per visit shows "Lord Xeen laughs. Only the Slayer Sword can touch him."<br>D-2.3's `slaying: Demon` lands with E11. | Prefer existing words. Option (a) would make a second damage path, and option (b) is a field with a single use. Option (c) loses the story's point. | A1: E11, the hook context fields and a unit case (outdoors per E11's own schedule).<br>A7: the hook and the playtest (no damage without the sword, damage with it).<br>A3: the zeroed line.<br>A2:<br>- the row note "map damage hook, E11";<br>- Lord Xeen's HP set so that one sword-wielder of about level 50 (double damage on demons counted) needs about 20–30 landed blows; lower `hp_x` 4 if needed;<br>- the sword cannot be sold or dropped: use an existing item word if one covers an equippable relic, otherwise A1 adds one small general flag. | Yes, cheap (map script) |
| Q13 | **(a).** A step plate across the throne doors' sill, inside the leaves, with the throne lit straight ahead.<br>- It fires once (111709).<br>- Lord Xeen and his two guards stay immobile until 4 s after the line.<br>- His damage path also calls the hook if it has not run yet. | D-38's "first sight, once per save". `SetActorImmobile` and `SetActorTarget` already exist. | A7. AU: the take. A3: the `sound:` field. | Yes, cheap |
| Q14 | **(a), with a question.**<br>- The scepter's click asks first, as a real choice (D-24). A3 writes the line, for example "The Scepter of Temporal Distortion lies across the arms of the throne. The whole castle seems to hold its breath. Take it?"<br>- Yes runs the cinematic: the mirror shatters, camera shake, dust, aaze0078:4 as subtitles.<br>- It then leaves directly to X9's causeway return point.<br>- X9 shows the castle gone on `m35.done`, and the gate spot reads aaze0027:44.<br>- The treasury opens at Lord Xeen's death, so nothing on his floor is lost.<br>- XD-19's exit keeps working (for a Lloyd's Beacon set inside).<br>**Fallback:** until A1 confirms that a leave can follow `evt.PlayCinematic`, the party stays in the castle after the cinematic (option (b)). | Burlock's after-line already says "Castle Xeen is a cloud again" (m35 `king_told`). The question lets a party finish looting first. | A1: confirm the leave after a cinematic. A3: the question and the subtitles. A5: X9's castle-gone stage and the aaze0027:44 line. A7: the event chain. | Yes, cheap |
| Q15 | **(a).** No experience for the machines or the generators. The scepter's 35,000 carries M35. | MM6–MM8 sizing. The source's +200,000 is dropped (aaze0075:5 and aaze0078:3 stay as ledger only). | — | Yes |
| Q16 | **(a).** 70 plus the two bosses: 54.38k (+2.0 %), 57.99k with the bosses (+8.8 %). | MAPS's L row says 70 "plus their bosses", and the result is inside ±10 %. | A2: Act V recount. | Yes, cheap until placement |

**DD-16 Corak's Pod**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q17 | **(a).** 7 monsters (Floating Eye 40 × 3, Terrible Eye 50 × 2, Lesser Elemental 55 × 2), 4.79k. One NOTES exception line under S's floor of 15. | MAPS says "few", and the source pod is empty. The group stays inside ±10 % (−4.2 % after Q23). | A2: recount. A7: the NOTES line. | Yes, cheap |
| Q18 | **(a).** +1 to every statistic and five years of age, once per character (a player bit). The source's lines are rescaled. | D-27's barrel pattern, with the age joke kept larger. Age by event was already covered for DD-09. | A3: the player bit and text. A2: the Act V ledger (the third +1-all device, after DD-09 and DD-07). | Yes, cheap |
| Q19 | **(a).** A third log computer pages the source's entries 1–15, abridged by A3 into about five pages. Each click shows the next page ("Entry 3 of 5") and the pages wrap round. A3's two short logs stay. | MAPS lists the pod logs as this map's lore, and paging a computer needs no new word. | A3: the pages as ORIGINAL_LINES rows (aaze0087:13, :25–31). A7: the paging variable. | Yes, cheap |
| Q20 | **(a), protected.** A peaceful, placed-only, immobile row "Corak": NoArena, not counted, his own friendly faction, as Gettlewaithe's (D-37).<br>- Shown on `m29.done`, hidden on `m32.done`.<br>- The map's `MonsterDamage` hook zeroes all damage to his row.<br>- He talks from the console (`evt.SpeakNPC(5513)`). Once A1's queued studio word "NPC on a placed indoor monster" lands, his body talks too.<br>- His look is a recolour of an installed MM6–MM8 humanoid: no Meshy, no MM9. | D-25 and D-42: peaceful figures are their own rows. He must not be killable while his voice keeps talking from the console. | A2: row. S: look. A7: hook, stage, a playtest that strikes him once. A1: the queued word (no new item). | Yes, cheap |
| Q21 | **(a) at Dif 0.** 10 %, Floating Eye 40 only. | Dif 1 and above can roll the Gamma Gazer 65, over the band (D-46's table, D-4). | A2: row 9169 | Yes, cheap |

**DD-24 Giants' Hall**

| # | DECISION | WHY | WHO ACTS | REVERSIBLE |
| --- | --- | --- | --- | --- |
| Q22 | **(a), with three fixes.**<br>1. `q-d16.hall_attacked` is a Q-D16 quest qbit (for example 113323). D-37's timer pattern (a People actor struck or turned) calls the hook. The hook sets the bit and closes Gurodel's topics, like `war`. A2's relations read it together with 113321, 113242 and 113244.<br>2. The throne gives its two disks and 14,000 only to a party without `friends`. A party that took Gurodel's gift and then fights gets the hoard but no second pair of disks.<br>3. The People rows also serve D5's hold, so one blow anywhere turns both.<br>The larder chest opens at peace. The throne and the hoard refuse at peace ("Gurodel would notice."). The war line :33 shows once per war at the threshold. | D-25's peaceful-group rule and DD-13's pattern of peace and war. Without fix 2, the disks could be taken twice. | A2: rows, faction, relations. A3: bit, hook, the throne's `friends` state, map-local lines. A7: timer, playtests. A6: D5's giants on the People rows. | Yes, cheap |
| Q23 | **Adjusted (a).** The People's own rows 11083 Cyclops **38**, 11084 Giant 50, 11085 Elder Giant **58**, with A7's mix 9 / 17 / 4: 20.80k. The group is 37 monsters and 25.59k (−4.2 %). MAPS's DD-24 row stays 38–58. | No monster over the band (D-4). D-42 lowered Morgana rather than raise a band. These are new rows, so their levels are free. A shared display name across acts is accepted (D-42's Head Witch). Option (b) would be 30 identical giants. | A2: rows and recount. Orchestrator: no band change. | Yes, cheap |
| Q24 | **(a).** MM8 Cyclops Larder d14, plus 2 new textures: `xdgiantd` (one wing, mirrored on the pair) and `xdthrone`. About 16 of 30. | It is the cyclopes' own home, unused elsewhere in Xeen. Options (b) and (c) are already seen on other maps. | A6: dungeon_families line, register both textures. A7. | Medium after build |
| Q25 | **(a).** Encounter 0. | D-33 and D-34: no rest slot that can reach a peaceful row. | A2: row 9177 | Yes, cheap |
| Q26 | **(a), for every giant row on the cyclops stand-in** (11080–11085): body height about 300. | It matches the drawn model (about 310). A low opening holds them back (D-32), and the 128 × 256 crack then keeps giants out. | A2: descriptors. A7: a playtest that the crack stops a giant and the 512 doors pass one. | Yes, cheap |

---

**ROWS AND NUMBERS**

| Map | Monsters | Kill XP per member | MAPS | Rest | Chests |
| --- | --: | --- | --- | --- | --: |
| XD-16 | 40 (Demon 20, Devil 14, Screamer 6) | 27.34k | 26.6k, +2.8 % | demons Dif 5, 10 % | 5 T5 (+5 traps) |
| XD-19 | 70 + Xeen's Pet 75 + Lord Xeen 85 | 54.38k; 57.99k with bosses | 53.3k, +2.0 % / +8.8 % | demons Dif 5, 10 % | 6 T5 + hoard T6 |
| DD-16 | 7 | 4.79k | group below | eyes Dif 0, 10 % | 2 T5 |
| DD-24 | 30 (People 38 × 9, 50 × 17, 58 × 4) | 20.80k | group below | 0 | 2 T5 |
| DD-16 + DD-24 | 37 | 25.59k | 26.7k, −4.2 % | — | — |

A7's Act V total is 107.31k against MAPS's 106.6k (+0.7 %), and 110.92k with XD-19's bosses (+4.1 %).

Orchestrator, MAPS changes:
- **§0 rows:**
  - XD-16: "40 (under M's 45, D-47)", 27.34k (+2.8 %).
  - XD-19: 54.38k (+2.0 %), 57.99k with the bosses.
  - DD-16 + DD-24: "37 (7 + 30), 25.59k (−4.2 %)", band unchanged at 38–58.
- **Dungeon list:**
  - DD-24: "38–58 (the People: 38/50/58)".
  - DD-16: "40–55 (few: 7)".
  - XD-19: add "elemental guards of four elements".

---

**RELAYS**

- **A1:**
  - E11: the weapon item id and attack kind in the map `MonsterDamage` hook context, with D-2.3's `slaying`.
  - Confirm that a leave can follow `evt.PlayCinematic`, and that a timer can show a hidden actor.
  - The sword's no-sell/no-drop flag, only if no existing word covers it.
  - The queued indoor talking-monster word is now also wanted for Corak.
- **A2:**
  - Rows 9142 and 9144 (demons Dif 5, 10 %), 9169 (eyes Dif 0, 10 %), 9177 (encounter 0).
  - Elementals 11624–11626 at 55, each with its own immunity.
  - The People 11083–11085 (38/50/58), faction `xeen_giants_people`, relations on 113321, 113242, 113244 and `hall_attacked`.
  - The Corak row (peaceful, placed-only, NoArena, not counted).
  - Body height of about 300 on 11080–11085.
  - Lord Xeen's HP for one sword-wielder; the Slayer Sword unsellable.
  - The +1-all device in the ledger; the Act V recount from the table above.
- **A3:**
  - **Q-D16:** `q-d16.hall_attacked` (bit and hook) and the throne's no-second-disks state.
  - **M35:** the scepter question, the cinematic subtitles, the zeroed-hit line, the `m35.barrier` text and the four generator `where` texts.
  - **DD-16:** the device's player bit and text; the abridged log pages; the blast door and power lines.
  - **XD-16:** the trap chest and lever lines; `q-c26.way` text at the cool passage.
  - **DD-24:** the hoard and law-stone lines.
  - **ORIGINAL_LINES rows:**
    - aaze0046:0–2, :4–6;
    - aaze0047/48:0–1 (ledger only);
    - aaze0075:0–6, aaze0078:0–5, aaze0027:44;
    - aaze0087's rows;
    - dark/aaze0013:26, :33, :34.
  - D-38's `sound:` fields.
- **A5:**
  - X7: `door:xd16` into `entrance:x7_mouth`.
  - XD-17: `entrance:xd16_way`, with its way back to XD-16's `entrance:xd17_way`.
  - X9: the gate, `m34.gate` and the causeway return point; the castle-gone stage on `m35.done` with aaze0027:44; the "Xeen's Aviary" sign.
- **A6:**
  - D6: the pod hatch with `entrance:d6_hatch` and its return point.
  - D5: the great doors (two leaves, 384 × 512) with `entrance:d5_hold` and its return point clear of Gurodel; D5's giants on the People rows.
  - DD-24's d14 dungeon_families line.
  - Register XD-19's seven new textures, `xdgiantd`, `xdthrone`, and `xvskull` if it is made.
- **S:**
  - `xeen_guard` before XD-19's placement (D-19).
  - Bindings and skins for 11624–11626 (MM6 air, MM7 earth and water).
  - Own recolour skins for Lord Xeen and Xeen's Pet.
  - Corak's look as a recolour of an installed MM6–MM8 humanoid.
  - No Meshy and no MM9 for any of these.
- **AU:** XD-19's four generator hums, the machines' stamping loop, the barrier crackle, the mirror shatter and the castle groan; D-38's two Lord Xeen takes; DD-16's stasis hum and power-up whine (optional). Use shipped sounds first.
- **A7:** build all four on these answers.
  - **NOTES lines:** XD-16's 40 under M; DD-16's 7 under S.
  - **XD-16 playtests:** one skull then the shut rock, then the second skull and the rock open; one trap chest; walking out of the lava.
  - **XD-19 playtests:**
    - the barrier with three generators down, then four;
    - the guard pool;
    - Lord Xeen without the sword and with it;
    - the scepter: No, then Yes, and the leave.
  - **DD-16 playtests:** the blast door before and after power; a wrong stasis phrase, then the right one; striking Corak.
  - **DD-24 playtests:** walking through at peace; the throne and hoard refusing; a blow turning the hall; the throne at war; the crack against a giant.

---

**SUMMARY ROW**

A7's Act V graphs (XD-16, XD-19, DD-16, DD-24): all four approved with changes; A7's default on every question except Q12 and Q23. XD-16 has 40 demons (27.34k), Fire-damage trap chests with a visible tell, four one-way lever slabs, and a slab that opens when the second skull breaks. XD-19 has a fixed pool of 4 hidden guards (always 70 monsters), one barrier fed by four generators, new Air/Water/Earth elementals at 55, and Lord Xeen harmed only by the Slayer Sword through A1's E11 on the existing map damage hook. Taking the scepter asks first, then the castle is gone. DD-16 has 7 monsters, +1 all and 5 years, and Corak can't be killed. DD-24's People are 38/50/58 (MAPS band stays 38–58), with no second pair of disks.
