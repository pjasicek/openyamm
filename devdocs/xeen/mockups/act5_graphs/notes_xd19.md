## XD-19 Castle Xeen

X9 · L · party 47 → 50 · 42–70, Xeen's Pet 75, Lord Xeen 85 · 70 + 2 bosses · treasure 5 (hoard 6) · Story M35

![XD-19](act5_graphs/xd19.svg)

The source's Xeen's Castle (xeen maze0075–0078, four levels) as one BLV of four floors, 640 apart (0, 640, 1280,
1920). It has 37 review rooms, about 62 sectors, about 130 M units² and 21 doors. The three wide doors (the gate, the
great hall's north doors and the throne doors) are two-leaf pairs.

- **What it is.** Lord Xeen's castle on the clouds. Four elemental generators feed the pylons of one barrier before
  the crown stair. Guard-making machines in the keep keep turning out Xeen's Guards. Above the barrier are the aviary
  with Xeen's Pet, then Lord Xeen's throne with the Sixth Mirror behind it.
- **Critical path.** The route is:
  1. The gatehall (`m35.arrival`), the Hall of Xeendom, the west ward and west gallery.
  2. The cold vault (water generator), the stair hall, the gravel vault (earth generator).
  3. The east gallery and the south-east tower up to its top (air generator).
  4. The upper east gallery, the barrier hall, the upper west gallery, the south-west tower top (fire generator).
  5. Down the tower to the west wall walk, the guard foundry, the keep stair back to the barrier hall, where the field
     is now down.
  6. The crown stair, the crown landing, the aviary, the throne doors (`lord_xeen_sight`) and the throne room
     (`lord_xeen`, `scepter`).
- **Off the path.** These rooms lie off the critical path:
  - Dead ends with chests: the barracks, the armoury, the parts store, the war room, the demons' quarters and the
    keeper's loft (T5 each).
  - The guard bays: a gem find, opened when both machines are destroyed.
  - The treasury behind the dais: the hoard (T6), opened by Lord Xeen's death.
- **Loops (6).** West and east rings round the great hall; the west and east climbs (towers, wall walks, foundry, grand
  stair); the towers loop on floors 1–2; the crown loop round the Pet by the keeper's walk.
- **Set pieces (4).** These are:
  - The guard foundry: two machines, the hidden guard pool and the bays.
  - The barrier hall: four element pylons, each with hover text naming the tower or vault its conduit runs to, so the
    game itself answers the puzzle; one field.
  - The aviary: open sky (`xeencloud`), the Pet held in by two 256-high arches (D-32).
  - The throne room: the dais and the Sixth Mirror in its force field.
- **Monsters (70) and kill XP.** Demon 42 (11630) × 28, Devil 50 (11631) × 14, Screamer 58 (11632) × 4, Xeen's Guard
  60 (11603) × 14 (four hidden in the bays), Lesser Elementals 55 × 8 (fire 11620 and three new tiers 11624–11626,
  two per generator), Greater Elemental 70 (11622) × 2 at the barrier.
  - XP: **54.38k per member** (+2.0 % on 53.3k); with Xeen's Pet 75 (11644) and Lord Xeen 85 (11634) 57.99k
    (+8.8 %).
  - Floor counts: floor 0 27, floor 1 16, floor 2 19, floor 3 8.
  - Quiet rooms (D-11.3): the gatehall, the crown landing and the throne doors.
  - Groups of 2–3. Rest encounters 10 % from the hostile rows (D-39).
  - Flying Feet, Guardian and Carnage Hand are under the band and none is placed.
- **The generators.** Source cold → water and poison → earth, at the L1 north corners in the source and in the floor-0
  vaults here. Fire → fire and electricity → air, at the source's L4 south towers and the tower tops here.
- **Lord Xeen (E11).** The map needs four things:
  - His behaviour bound on load (`evt.SetActorBehavior`).
  - Immobility until the sight line ends (`evt.SetActorImmobile`, then `SetActorTarget` party).
  - An `onDeath` that calls `m35.lord_xeen`.
  - A damage filter that does not exist yet. `onDamaged` only observes (A1, DECIDE 6).
- **First sight.** A step plate across the throne doors' sill inside the leaves calls `m35.lord_xeen_sight` once
  (111709), with the throne straight ahead and lit. A 4 s timer then frees him and his two guards.
- **Original lines.** These are used as follows:
  - aaze0075:0–4 and aaze0078:0–2: the machines' and generators' "Destroy?" questions.
  - aaze0075:6: the exit's meaning.
  - aaze0078:4: the mirror cinematic's subtitles.
  - aaze0078:5: the force field.
  - aaze0027:8–9: X9's "Xeendom" and "Xeen's Aviary" signs.
  - aaze0027:44: after M35.
  - aaze0075:5 and aaze0078:3 ("+200,000 experience") are not used.
- **Door to X9.** A5's `thing:castle_xeen_gate`, two leaves, at the source's (16,29), opened by `m34.gate`.
  - **Inside arrival proposed:** `entrance:x9_gate`, in the gatehall about 256 inside the leaves at about
    (0, −2944, 0), facing north (512).
  - **Return:** the exit preset to the causeway about 512 south of the leaves (the source's (16,28)), facing south
    (1536).
- **Hooks.** The graph places these:
  - `m35.arrival`: the gatehall.
  - `gen_water`, `gen_earth`, `gen_fire`, `gen_air`: the four generator rooms.
  - `barrier`: the barrier hall, called on load and after each generator.
  - `pet`: the aviary.
  - `lord_xeen_sight`: the throne doors.
  - `lord_xeen` and `scepter`: the throne room.

  `m34.gate` is X9's. Map qbits: 118060–118061 the machines, 118062 the barrier down, 118063 the bays open; the rest
  of 118060–118079 are free.
- **Textures.** MM8 Escaton's Palace d35 (black stone, gold friezes, gnecdr1 leaf pairs) with the ancient kit's sw
  panels, xaenergy and xafield for the machines, the barrier and the mirror's field. About 38 of 70 textures; 7 are
  new: four generator cores, the sigil banner, the Sixth Mirror and its shattered frame. Music 22, map id 9144.

**DECIDE items** (options in the graph file; the proposed default first)

1. **Guard machines.** (a) Two destructible machines in the foundry release four hidden placed guards on a 45 s timer
   until both are destroyed. (b) A capped SummonMonstersById. (c) Flavour only.
2. **Destroying a generator.** (a) The source's "Destroy?" question breaks the destructible by event, and blows also
   break it. (b) Blows only.
3. **The barrier.** (a) One field held by four pylons. (b) Four fields in series.
4. **Elemental guards.** (a) New Lesser Air, Water and Earth tiers at 55 (11624–11626). (b) Fire everywhere.
   (c) Demons.
5. **Constructs under the band.** (a) None. (b) Four Carnage Hands in the foundry.
6. **Lord Xeen's immunity.** (a) A1's damage hook in his behaviour. (b) A row field `harmed_only_by`. (c) D-2.3's
   slaying only.
7. **First sight.** (a) A sill step plate, with him immobile until 4 s after the line. (b) The doors' click.
8. **After the scepter.** (a) The cinematic, then a direct leave to X9's gate; X9 shows the castle gone and the gate
   reads aaze0027:44. (b) The castle stays. (c) Vertigo, as in the source.
9. **Machine and generator XP.** (a) None. (b) 2,500 per member each.
10. **Count.** (a) 70 + 2 bosses, 57.99k (+8.8 %). (b) Four Demons fewer.

**Requests to other lanes**

- **A2:** the three elemental tiers 11624–11626 at 55. The Xeen Slayer Sword as an undroppable quest item. The row
  field for DECIDE 6 (b) if chosen. The Act V recount: XD-19 54.38k, 57.99k with the bosses.
- **A3:** generator hook texts that name the "Destroy?" question and the renamed generators. A text for
  `m35.barrier` ("The last pylon goes dark and the barrier falls."). ORIGINAL_LINES rows for aaze0075:0–6,
  aaze0078:0–5 and aaze0027:44.
- **A4:** none.
- **A5 (X9):** the gate door and `m34.gate`; the return point above. The "Xeen's Aviary" sign on the aviary's outer
  wall. For 8 (a): the castle-gone stage and the gate line aaze0027:44.
- **AU:** the generator hums (four), the machines' stamping loop, the barrier crackle, and the mirror shatter and
  castle groan for the cinematic.
- **S:** the `xeen_guard` model before placement (D-19); bindings for the three new elemental tiers (MM6 elementals).
- **A6:** the seven new textures, registered.
- **A1:** a damage filter hook (E11). Confirm that a hidden placed actor can be shown by a timer event and that a
  leave can follow `evt.PlayCinematic`.

**State and next steps.** The graph, the SVG and these notes are written. The render printed no warnings. A PNG
review was not done, because there is no SVG converter on the host (no rsvg-convert, cairosvg or inkscape); the lead
should look at the SVG in a browser. Nothing is built or installed. Next: the decider answers the DECIDE items, then
L1.
