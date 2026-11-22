## DD-15 Great Pyramid

D5 · L · party 44 → 47 · 42–65 · 70 · treasure 5 · Story M28, M30, M36 (the Dragon Pharaoh); D-58's sky door to D7

![DD-15](act5_graphs/dd15.svg)

The source's Great Pyramid (dark maze0083–0086, aaze0083–0086) has four levels, each a smaller square than the one
below (32, 24, 16 and 8 cells). L1 is "the Royal Pyramid" for visitors: Reception, the Overseer's Office, the Visitor's
Atrium and Information, five talking statues, six torch levers and eight number niches. L2 has four verse statues and
the registry lock (NCC-1701). L3 is a teleport maze. L4 holds the Dragon Pharaoh's apartments: his throne, the Brew of
Pure Power, an ornate bed, a tapestry, a combination wall safe, the Prime Directive book, and a button to Skyroad D2.

Ours is one BLV of four stepped floors, 768 apart (0, 768, 1,536, 2,304). The floors are 10,240, 8,192, 6,144 and
4,096 square, the inside independent of D5's 6,144-square pyramid (D-49 Q6). It has 34 review rooms, about 58 sectors
and about 138 M units², with 21 doors. Class L: 50–75 sectors, 120–200 M units², up to 25 doors.

- **What it is.** The Dragon Pharaoh's pyramid, still kept as the source's tourist monument with its old wardens. The
  party climbs four floors and three puzzles to give the Pharaoh his orb (M28). They come back twice: for the Chosen
  Ones (M30), and after M33/M35 for the finale's errands (M36).
- **Critical path.** The steps are:
  1. The green doors (`entrance:d5_door`, quiet; the welcome statue).
  2. The four torch chapels round the atrium, lit in any order. The plaque by the first, in the north-east chapel,
     says it plainly (`m28.torch_plaque`). The fourth calls `m28.torches`.
  3. The south gallery's stair door, then the grand stair.
  4. On L2, the processional of the four verse statues to the registry door. Its plaque gives "1701" plainly
     (`m28.registry_plaque`); the lock (`m28.registry_lock`) opens the stair up.
  5. On L3, the pad hall (`m28.maze` on the first arrival). The bird pad leads to the bird cell, its second pad to the
     far cell, then the apex stair.
  6. On L4, the apex landing, the antechamber (the Prime Directive book, `m28.prime_directive`) and the great doors
     to the throne hall. There the Pharaoh talks: npc 5453, The orb (M28).
  7. Later visits: the Pharaoh's lift from the grand stair to the antechamber after `m28.done` (DECIDE 4). The
     Pharaoh's "Chosen Ones" (M30) and the M36 topics. The sky door behind the throne opens after `m30.done`.
- **Off the path.** These rooms lie off the critical path:
  - The number hall: eight niches, 3 to 10, opening the Overseer's vault (T5, DECIDE 3). The answer-givers are the
    two rule statues and the Overseer's note.
  - Information's strongbox (T5); the west tomb's grave goods (T5); the embalmers' find.
  - L3's sun cell (T5), and the eye cell with the Overseer's lost map of the pads, which is the maze's answer-giver.
  - The scarab cell's guard post.
  - L4's bedchamber: the wall safe at 20-30-1, from the tapestry (T5, DECIDE 7); the bed; a carved button that opens
    a secret way to the sky corridor.
- **Loops (4).** The ring round the atrium on L1. The atrium's two doors. L2's processional, east tomb, cloister and
  registry. L4's throne hall, bedchamber, secret door and sky corridor.
- **Set pieces (four).** These are:
  - The Visitor's Atrium: a tall sunken court, its four braziers lit one by one with the torches.
  - The processional: four statues speaking the verses, ending at the bronze registry door and its brass plaque.
  - The pad hall: Ancient steel under small ceiling lights, five glyph pads, Ghost Mummies drifting.
  - The throne hall under the apex: green stone and gold, the Pharaoh at his throne, the Brew of Pure Power bubbling
    beside the dais.
- **Monsters and kill XP.** The Pyramid mummies only: Tomb Mummy 42 (11270) × 34, Pyramid Guard 52 (11271) × 24, Ghost
  Mummy 62 (11273, tier D) × 6, Royal Mummy 65 (11272) × 6.
  - XP: **51.92k per member** (207,666 / 4) against MAPS's 50.4k (+3.0 %).
  - Floors: L1 30 (eight of its Tomb Mummies hidden in the torch chapels' niches until their torch is lit, DECIDE 2),
    L2 20, L3 12, L4 8.
  - Groups of 2–3. No boss (MAPS §0).
  - Quiet rooms: the entrance hall, the throne hall, the bedchamber and the sky corridor (D-11.3 for both map doors).
  - The Pharaoh is A2's peaceful placed-only row 11919 (npc 5453, D-56): unkillable, not counted.
  - Rest encounters 10 % from the mummies (DECIDE 10).
- **Treasure.** Five T5 chests: Information, the Overseer's vault, the west tomb, the sun cell and the wall safe. The
  vault also holds the visitors' fees (gold).
- **Original lines.** These are used as follows:
  - aaze0083:0, "Exit the Great Pyramid?": the exit preset's meaning (D-24).
  - aaze0083:6, :7 and :8: the welcome, the torches ("light six torches" becomes four) and the history statues.
  - aaze0083:9–10 and :13–38: the rule statues and the eight niches.
  - aaze0083:12 and :39: "Access denied!" and "The lever is stuck.".
  - aaze0084:1–4 and :7: the four verses and "Incorrect!".
  - aaze0086:0: the Pharaoh's warning at the Brew of Pure Power.
  - aaze0086:3, :19 and :20–29: the bed and the safe's prompts.
  - aaze0086:30–31: the Prime Directive book (DECIDE 8).
  - aaze0086:5, "Access Denied!": at the sky door before M30.
  - The source's spelling "Pharoah" stays only inside quoted statue lines.
- **Door to D5.** The green double door on the pyramid's north face (A6's `xdpyrdor` leaves, `m28.door` with the Key to
  the Ancient Pyramid 12348).
  - **Inside arrival proposed:** `entrance:d5_door` at (0, 4736, 0), in the entrance hall about 384 inside the doors
    (the north wall at y 5,120), facing south (1536). This is D-49's "the green door, facing south" and the name D5
    assumes.
  - **Return:** the exit preset to D5's installed `entrance:dd15_door` (0, -7168, 1248) facing 512 (north, away from
    the door). It matches; nothing for A6 to change.
- **Sky door to D7 (D-58).** Behind the throne, a short Ancient corridor ends at a door in the pyramid's face near the
  apex. It reads "Access Denied!" before `m30.done`; after that `d7.sky_door_dd15` ("Step out onto the Skyroads?")
  leads on to the exit preset to D7's `entrance:dd15_sky`. D7's way in arrives at **`entrance:d7_sky`**, in the
  corridor about 256 inside, facing the throne. Sealed with its line until D7 installs.
- **Hooks.** These are placed as follows:
  - `m28.torch_plaque`: the north-east chapel.
  - `m28.torches`: the fourth torch, any chapel.
  - `m28.registry_plaque` and `m28.registry_lock`: the registry door.
  - `m28.maze`: the pad hall, first arrival.
  - `m28.prime_directive`: the antechamber.
  - `d7.sky_door_dd15`: the sky corridor.
  - The Pharaoh's topics (M28 The orb, M30 Chosen Ones, M36) through `monsters[].npc: 5453` in the throne hall.
  - `m28.door` is D5's.
  - Map qbits (block 117560–117599, provisional): 117560 arrived_once, 117561–117564 the torches, 117565–117572 the
    niches, 117573 the vault, 117574 the safe, 117575 the button, 117576 the maze's first arrival.
- **Textures.** MM6 Tomb of VARN (A6's assign).
  - The VARN set: `egybigb`/`egybiga` blocks, `egywla`/`egywld` hieroglyph walls, `egyflore`/`egyflorc`,
    `egyceila`/`egyceilb`, `egytrma`/`egytrmc`, `egywlj` and `egycol32` pillars, `egydrlgl`/`egydrlgr` great-door
    pairs, `egydrsml`/`egydrsmr`, `egyswbof`/`egyswbon` for the torch levers, `egymeda`/`egymedb`.
  - It reads apart from XD-15 and FD-02, which use the same set, through A6's `xdpyrdor` inside, `xngold5` gilding in
    the throne hall, and the ancient kit's sw set on L3 and the sky corridor (A6's "lower Ancient levels").
  - About 40 of 70, with one new texture: `xdregplq`, the brass registry plaque, a sign placed once.
  - Music 46, map id 9168.

**DECIDE items (DD-15)**
1. **Count and mix.** (a, proposed) 70 Pyramid mummies (Tomb 34, Guard 24, Ghost 6, Royal 6), 51.92k (+3.0 %); (b) (a)
   plus two optional Cloud Dragons 70 (11650, the Darkside dragons' row names the pyramid) in a dragon gallery off L2,
   54.72k (+8.6 %); (c) ten Royal Mummies, about 53.9k (+7 %). Evidence: MAPS §0; the source's L1 held 40 of two kinds;
   D-1.2. Depends: A2's recount.
2. **The torches.** (a, proposed) four torch levers in the four corner chapels (A3's four). Each lit torch lights its
   brazier in the atrium and wakes two Tomb Mummies from the chapel's niches (hidden placed actors shown by the lever,
   DD-14's word). The fourth opens the stair door. (b) Four torches, the eight Tombs placed openly. (c) The source's
   six, with A3's text changed. Evidence: aaze0083:7, A3's m28 hook text "The fourth torch catches"; the source's
   levers also bring monsters.
3. **The number lock** (the source's eight niches, 3–10). (a, proposed) Kept as an optional puzzle opening the
   Overseer's vault. The answer is given by the rule statues (eight in a row, total 52) and plainly by the Overseer's
   note. (b) On the critical path, with the torches (the source's order). (c) Dropped. Evidence: QUESTS M28 names "a
   number lock", which A3 reads as L2's registry; the user's no-unanswered-riddle rule.
4. **The return visits** (M30 and M36 bring the party back twice). (a, proposed) The Pharaoh's lift from `m28.done`:
   two stops, the grand stair and the antechamber, both ways. (b) After `m28.done` the first pad goes straight to the
   far cell. (c) Nothing: the party climbs each time, through cleared floors. Depends: nothing (lifts and qbit gates
   exist).
5. **The wardens after M28.** (a, proposed) They stay hostile, as the source's mindless wardens. The map does not
   refill, so a cleared pyramid stays quiet. (b) A pyramid faction turns peaceful on `m28.done` (relations by qbit, as
   DD-20's coven). Depends: A2 for (b).
6. **The Brew of Pure Power.** (a, proposed) The Pharaoh's warning only; the vat is a set piece. (b) The warning, then
   a second click drinks it: fire damage, "He did warn you.". (c) A once-per-character +2 to a statistic. Evidence:
   aaze0086:0; the vat's source event is unclear.
7. **The wall safe** (the source's 20-30-1; its event was never finished, aaze0086:10). (a, proposed) A T5 chest behind
   the source's three Left/Right prompts, the numbers woven into the tapestry's border (its click shows them).
   (b) A plain locked chest. (c) No safe.
8. **The Prime Directive text.** (a, proposed) The source's three directives (aaze0086:30) without the +1,000,000
   experience; A3 changes `m28.prime_directive`'s text. (b) A3's current text ("No guardian shall interfere with the
   world it guards."). Evidence: MAPS names the book as DD-15's original line.
9. **The sky door's place** (D-58). (a, proposed) Behind the throne on L4, a door near the apex (the source's L4 button
   leads to Skyroad D2). (b) A pad in the L3 maze. Depends: A6 (D7's `entrance:dd15_sky` and its height against the
   apex at 3,600).
10. **Rest encounters.** (a, proposed) 10 % from the mummies (D-39), none in the Pharaoh's rooms; (b) 0.

**Requests to other lanes**
- **A2:**
  - row 9168's slot (lock and trap at D5's 12/6, perception, music 46, a Pyramid mummies slot);
  - the Act V recount: 70 at 51.92k;
  - the Pharaoh 11919 placed here as well as on P5 (D-56).
- **A3:**
  - register map qbits 117560–117576;
  - the Prime Directive text (DECIDE 8);
  - map-local lines for the niches, the rule statues, the Overseer's note, the tapestry, the safe, the eye cell's map
    of the pads and "Access Denied!" at the sky door;
  - confirm `m28.torches` fires from whichever torch is lit last.
- **A4:** nothing; 5453's topics are A3's.
- **A6:**
  - `entrance:d5_door` confirmed, and the outside point matches;
  - D7's `entrance:dd15_sky` near the apex, for `entrance:d7_sky`;
  - register `xdregplq` when made.
- **S:** the Pharaoh's figure (D-56): standing at the throne with a held book; idle only, no attacks. The Lizardman
  stand-in until then.
- **AU:** a torch ignition, the pads' teleport whoosh, the vat's bubbling; VARN beds with `pan: false` (D-48).
- **A1:** nothing new. Hidden actors shown by events, levers, step plates with in-map moves, lifts and
  `monsters[].npc` all exist.

**State and next steps.** Graph, picture and notes written 2026-11-21 (A8 session 10). Nothing is built. Next: the
decider answers the DECIDE items, then the L1. PNG: `output/studio_cal/a8_s10/png/dd15.png` (headless Chrome, looked at).
