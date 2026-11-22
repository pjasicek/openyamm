## DD-08 Northern Tower

D5 · M · party 49 → 52 · 45–55 (band 40–62) · 45 · treasure 5 · Q-D17 (the Chalice of Protection), Promo Black Knight / Villain

![DD-08](act5_graphs/dd08.svg)

The source's Northern Tower (dark maze0069–0072, four 16 × 16 levels round a central cell; aaze0069–0072) is the
Voweless Knights' tower. Ours is one BLV of four floors stacked round a central stair core, 448 apart (0, 448, 896,
1344). It has 33 review rooms, about 38 sectors, about 32 M units² (each floor about 2,816 square inside D5's
1,024-square tower, larger inside than outside as DD-02, DD-05 and DD-06), 15 doors (the gate and the chapter hall's
doors as two-leaf pairs, two sliding walls, the roof trapdoor).

- **What it is.** The knights who leave the vowels out of everything. Seven books on lecterns show a proverb without
  its vowels and ask for it. On the top floor a voice asks what you seek, and the Chalice of Protection lies behind
  it. Bosco wants the Chalice; the knights will take it back if you swear their oath.
- **Critical path.**
  1. The gatehouse (`entrance:d5_tower`, quiet), the Hall of Arms, the great stair in the core up to L2.
  2. The west armoury, the west wall stair up to L3, the drill hall's west arm, the core's upper flight (the Stair
     of Silence) up to L4.
  3. The chapter hall, the antechamber: the voice's prompt "Wht d y sk?", **Chlc** (`q-d17.voice`), the iron door,
     the chalice room (`q-d17.chalice`).
  4. Dark route: back to the chapter hall's plaque, "Swear the Voweless oath?" (`q-d17.oath`). Light route: out and
     to Bosco (DD-25).
- **Way back.** The Stair of Silence, the drill hall's east arm, the east wall stair, the east armoury, the great
  stair: a different way down. The core is split on purpose: the source's stairs alternate, so L2 and L3 are crossed
  both ways (DECIDE 8).
- **Off the path.** These rooms lie off the critical path:
  - Dead ends with books: the west lectern room and the dormitory (L1), the west and east studies (L3); two more
    books stand on the wall-stair landings of L2 and one at L3's east stair head.
  - Dead ends with chests (T5): the quartermaster's store (L2), the west and east niches behind sliding walls (L3,
    opened by step plates as the party walks up, the source's grinding walls), the west knights' cells (L4).
  - The Hall of Thrones (set piece) and the east cells with the ladder loft.
  - Three wall finds (a T5 shield, helm and cuirass) in the Hall of Arms and the two armouries.
- **Loops (5).** L1's ring round the core; L2's armouries round the core's head; the wall-stair loop across L2 and
  L3; the drill hall's three arms round the core; L4's sanctum ring (chapter hall, antechamber, thrones).
- **Set piece.** The sanctum on L4: the chapter hall with the order's plaque and banners, the voice's mask beside
  the iron door, and the Hall of Thrones. Four thrones of the lows (each gives its condition) stand round the
  Euphoria Throne, with the Throne of the Dunce in an alcove. The L1 pillow note gives the order: "to appreciate the
  highs one must experience the lows" (DECIDE 5).
- **Riddles and their answer-givers.**
  - The voice: Bosco's topic ("C, H, L, C"), autonote 4570, the knights' books on every floor.
  - The seven books: the proverb or its vowels are accepted. The vowels are on the Cliff Notes under L4's seven
    pillows (aaze0072:14–20); the books stay answerable on the way down. The whole proverbs are in Librarian Ormond's
    bound compilation in Castleview (4928, "We sell the Voweless Knights' answers, bound."; the source's Olympus
    scroll aaze0037:5). Ormond has only that greeting so far: A3/A4 request.
  - The thrones: the L1 pillow note.
  - The sliding walls answer themselves: they open as the party walks up.
- **Monsters (45) and kill XP.** Slayer Knight 45 (11150) × 33 and Death Knight 55 (11151) × 12, the source's knights
  only (its 23 + 11), the Death Knights' share rising by floor (L1 0, L2 3, L3 4, L4 5). By floor: 8, 12, 15, 10.
  - XP: **31.14k per member** (124,575 / 4), 78.6 % of the DD-08 + DD-21 row (39.6k). With DD-21 at about 15 +
    Sandro and about 10k (assumed), the group is about 60 + Sandro and **41.1k, +3.9 %**.
  - The source's Doom Knight 75 is over the band and is not placed (DECIDE 2).
  - Groups of 2–3; the drill yard holds two groups. Quiet: the gatehouse (D-11.3), the antechamber, the ladder loft.
  - Rest encounters 10 % from the two knight rows (D-39).
- **Treasure.** Four chests T5 (M: 3–7), three wall finds T5, the Chalice (12525). The source's two Energy Discs on
  L4's walls are not placed: the tower's two are the quest's (DECIDE 9).
- **Original lines.** aaze0069:0 (the exit preset's meaning, D-24); :2 the plaque (the founder's statue on L1 and the
  oath plaque); :3/:5 the dead mirror; the seven books aaze0069:8, :11, aaze0070:2, :5, aaze0071:2, :5, :7 with :18
  and :10 (the slam); :15 the pillow note; aaze0072:2 the voice, :5 "Very Good! Lv Lng nd prspr!" (proposed for
  `q-d17.voice`'s text), :6 (= `voice_wrong`), :7 "Study your lessons."; :8–12 and :21–25 the thrones (rescaled);
  :14–20 the Cliff Notes. Not used: the +500,000 experience lines and "+2 Levels (perm). +5 to all 7 Stats".
- **Door to D5.** D5's `door:dd08`: the tower's south door, two `hkm1dl` leaves, `q-d17.tower_door` with Bosco's key.
  - **Inside arrival proposed:** `entrance:d5_tower` (as D5 assumed), in the gatehouse about 256 inside the leaves at
    about (0, −1152, 0) in the map's frame (tower centre 0, 0; the gate in the south wall at y −1408), facing north
    (512). The leaves' inner face is the same mirrored `hkm1dl`/`hkm1dr` pair.
  - **Return:** the exit preset to D5's installed `entrance:dd08_door` (2560, 11776, 3008), facing 1536. It is 384
    south of the door's centre (the tower spans x 1920–3200, south face y 12160), facing away. **It matches**; D5
    changes only the door's arrival name and drops its placeholder effect when DD-08 is built.
  - **Roof:** the ladder loft's trapdoor, `d7.roof_dd08`, one way up to D7 `entrance:dd08_roof` after `m30.done`;
    "The trapdoor is shut fast." before (D-58). D7's `d7.hatch_dd08` refuses from above.
- **Hooks.** These are placed:
  - `q-d17.voice` and `q-d17.voice_wrong`: the antechamber's mask (the text prompt).
  - `q-d17.chalice`: the chalice room's stand.
  - `q-d17.oath` and `q-d17.oath_again`: the chapter hall's plaque.
  - `d7.roof_dd08`: the ladder loft.

  `q-d17.tower_door` is D5's and `d7.hatch_dd08` D7's. Map qbits:
  - 117640: `dd08_arrived_once`.
  - 117641–117647: the seven books.
  - 117652–117653: the sliding walls.
  - 117654–117656: the wall finds.
  - The rest of 117640–117679 are free; the thrones use map variables.
- **Textures.** The Towers of Mok family, MM8 Castle of Air d27, as DD-05, DD-06 and DD-07. DD-08's accent is the
  knights' rooms in MM7 Castle Gryphonheart 7d33's dark cobble (`dchb1`, `7tfb1`, `7trimd`): the chapter hall, the
  Hall of Thrones and the cells (A6 decides). It also uses the gate pair `hkm1dl`/`hkm1dr` (D-49), `xkmirror` (D-37)
  on the dead mirror, and A6's `xdvowel` once over the chapter doors. About 25 of 45 textures; 2 are new: `xvkban`
  (the Voweless banner, once per face) and `xvkmask` (the voice's mask, once).

**DECIDE items** (options in the graph file; the proposed default first)

1. **Count.** (a, proposed) 45: 33 Slayers and 12 Death Knights, 31.14k; the group about 41.1k (+3.9 %) with DD-21
   at about 10k. (b) 50, the group +11.7 %. (c) 40 under M's floor, −3.9 %. Depends: A2's recount, DD-21's graph.
2. **The Doom Knight 75.** (a, proposed) Not placed (D-4: none over the band); a Death Knight in his place. (b) One
   in the Hall of Thrones, +0.70k (+5.7 %). (c) A knight-commander boss row at 62 (A2, S).
3. **One family.** (a, proposed) Knights only, as the source. (b) Four Onyx Sentries 62 as animated armour in the
   armouries, +1.99k.
4. **The seven books.** (a, proposed) Once per book for the party (map qbits), 1,000 experience per member (7k in
   all). The answer is the proverb or its vowels. (b) The same, once per character (seven player bits). (c) +1 to a
   different statistic per book. (d) Lore only.
5. **The thrones.** (a, proposed) The four lows give Weak, Drunk, Afraid and Insane. The Euphoria Throne after all
   four gives +1 to all seven statistics, once per character (a player bit); the Dunce deals 50 damage. (b) +2 to all
   seven. (c) Dressing only.
6. **The voice.** (a, proposed) "Chlc" calls `voice`; "Chalice" calls `voice_wrong` (the source's reply to the word
   with its vowels); anything else gets aaze0072:7. (b) As (a), and the source's own "aie" also calls `voice`.
   (c) Everything but Chlc calls `voice_wrong`.
7. **The knights and the oath.** (a, proposed) DD-08's knights and rests get their own faction
   `xeen_voweless_knights`: hostile, friendly from `oath` on (D-37's pattern). Four hidden peaceful "Voweless Knight"
   figures (placed only, uncounted) are shown in the chapter hall's niches by the oath, matching its text "The
   knights come out of the walls". (b) The figures only. (c) Neither.
8. **The stair core.** (a, proposed) Split: the great stair L1–L2 and the Stair of Silence L3–L4, with the two wall
   stairs between (the source's alternation). (b) One continuous core.
9. **The loose Energy Discs.** (a, proposed) Not placed: the tower's two disks are the quest's (M18). (b) Two loose
   disks as finds.
10. **Rest encounters.** (a, proposed) 10 % from the two knight rows. (b) 0.

**Requests to other lanes**
- **A1:** nothing. A faction changed by a qbit is D-37's pattern; step plates, prompts and stages exist.
- **A2:** the Act V recount (DD-08 45, 31.14k). For 7 (a): the faction `xeen_voweless_knights` for DD-08's placed
  knights and its rests, and a peaceful placed-only "Voweless Knight" row (the characters block is full at 11923:
  an id from A2). A row only if 2 (c) is chosen.
- **A3:**
  - Map-local texts: the seven books (abridged from aaze0069–0071), aaze0072:7 for the voice.
  - Player bits: the Euphoria Throne (5) and, under 4 (b), the books.
  - `q-d17.voice`'s text could take aaze0072:5. ORIGINAL_LINES rows for the lines above.
  - The disk ledger (9).
  - With A4: Ormond's compilation.
- **A4:** Librarian Ormond (4928) sells or reads the compilation of the seven proverbs: a topic, or a book sold at
  the library (the source's aaze0037:5).
- **A6:** nothing on D5 (the outside point matches). Register `xvkban` and `xvkmask` (proposed names). Add DD-08 to
  `xdvowel`'s and `xkmirror`'s maps. Confirm the 7d33 accent.
- **AU:** optional: a low rumble under the voice's text. The slam and the stone grind are shipped.
- **S:** the dark knights' bodies (`mm6_kni` black and red tiers, MONSTERS_AND_ITEMS). The Voweless Knight figure's
  skin (7 (a)). Five thrones and the Dunce's from shipped throne decorations.
- **D7 lane (phase 6):** `entrance:dd08_roof`, as D-58.

**State and next steps.** The graph, the SVG and these notes were written on 2026-11-21 (phase 5, graphs only;
nothing is built or installed). The render printed no warnings; the PNG
(`output/studio_cal/a8_s10/png/dd08.png`, headless Chrome) has been checked. Next: the decider answers the DECIDE
items, then L1.
