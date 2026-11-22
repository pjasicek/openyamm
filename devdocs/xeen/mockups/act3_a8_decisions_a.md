# Phase 3, lane A8's graphs DD-01 to DD-04: decisions (D-26)

Decider D-26, 2026-11-20. Wins over the graphs in `act3_graphs/` (dd01–dd04) and `act3_dungeon_graphs.md` where they
differ. DD-09, DD-10, DD-18 are D-27's (`act3_a8_decisions_b.md`).

## Approval

- **DD-01 Castleview Sewer**, with changes: the 21 Bat Queens become the new Dire Rat (Q2); the drowned cellar's way up
  into the east drain becomes a floor grate bolted from below (opens once from the cellar side; from above "The grate is
  bolted from below."), so the sluice stays the way in; no monster below the culvert's high-water line (Q5); Felix with
  a changed line (Q4); the outfall and street grates on D1 (Q1).
- **DD-04 The Gremlin Court**, with changes: band 14–22, Gettlewaithe 24; the court side peaceful until `court_hostile`
  (attacking Gettlewaithe or any court-side gremlin sets it); the challenge is his first greeting; court and cellar in
  D1's t09 grey ashlar; the "stooping" tiny door is only a look (the passage clears the party's collision height; the
  audit decides).
- **DD-02 Ellinger's Tower**, with changes: the Book per Q1; the dead mirror gives messages only (Q4); the crate room is
  a real storeroom (8+ containers or `store: true`) or loses its clump; the lift shaft has no openings on floors 1–3.
- **DD-03 Castle Kalindra**, with changes: each stage's monsters placed hidden and shown when their stage qbit is set
  (D-18's pattern); every stage gate a door leaf that blocks monsters too (the stair's step event carries the mist
  line, the stair itself closed); three liches take the source's names; the old well holds 2 named Bone Dragons (the
  castle 54 monsters); A4 adds Carl the Mason; the phase wall shares one texture with D1's ghost castle; stable coaches
  arrive at `kalindra_gate`.

## Decisions

| Map | Question | Decision | Who acts |
| --- | --- | --- | --- |
| DD-01 | Shafts | One working hatch (66, 57); four ladders up to grates bolted from above, each foot with its find; the outfall a two-way exit once its bar is lifted from inside. On D1: the outfall grate in the mill gorge's west wall within 400 of the burnt mill (merges into the mill's POI), refusal before the bar "An iron grate, barred from inside."; four plain street grates (no event, not POIs) at guild row, gate passage, temple, market | A6 (D1 door, arrival, grates), A8 (exits on the `exit` preset, the bar a two-state lever), A3 (qbit "outfall unbarred") |
| DD-01 | Rat rows | Rename: rats B "Rooka 6" → **Plague Rat**, rats C "Sewer Stalker 9" → **Giant Rat**, sewer stalkers A "Rooka 18" → **Wererat**; the boss "Rooka the Rat Queen" stays; new row **11393 Dire Rat**, rats tier D, level 10, Disease1, replacing all 21 Bat Queens (the 8 Vampire Bats stay); kill XP 4.03k (+9 %) | A2, S (one colour tier `xrat_d`, scaled past the Giant Rat), A8 |
| DD-01 | Rooka at 24 | Kept; MAPS writes DD-01's band "10–20, Rooka the Rat Queen 24" (§0 and the dungeon list); Valio (45) counts in Act III (D-1.2, ~0.62k per member) | A2 (MAPS rows, count) |
| DD-01 | Felix | A flavour talking actor at the end of his tunnel, sells nothing: "I helped invent the compass! These days I mostly invent tunnels. The gremlins wedged the town sluice open with the mill's gears; shut it and the old culvert drains, rats and all." | A4 (NPC in d1.yml, portrait), A8 (place) |
| DD-01 | Sluice | Sinking water door mover (XD-10's route); the nest culvert's 4 monsters stand above the high-water line on the nest side, or are a hidden group shown on the first step into the drained culvert; playtest refused while flooded, open after "Close", flooded after "Open" | A8 |
| DD-04 | Guards at 22 | Three Gremlin Guards 22 stay; band "14–22, Gettlewaithe 24" in both MAPS tables | A2 (MAPS) |
| DD-04 | Talking party | Burrow, hall of pranks and waiting room peaceful (groups following `court_hostile` with the guards); cellar, larder and the army below always hostile; attacking Gettlewaithe or a court-side gremlin sets `court_hostile`; after `court_peace` all friendly (A2's relation) | A8, A3 (the `gettlewaithe` hook or the swap to monster 11023 also sets `court_hostile`), A2 (relations) |
| DD-04 | Challenge | Gettlewaithe's first greeting (NPC 4955 `greet[0]`, aaze0029:83); the second greeting "Back to petition the king?" stays; no step message | A4 (d1.yml) |
| DD-04 | Textures | Court, waiting room and wall cellar in D1's t09 grey ashlar with shipped floors and ceilings; burrows, barracks, sappers' tunnel in MM7 Tularean Caves 7d08; one new picture: the Mayor with a moustache behind the throne; the throne's `else_text` "Under the throne: crumbs. Above it, the Mayor's portrait, with a moustache added." | A6 (`dungeon_families.yml`, the picture), A3 (else_text) |
| DD-04 | Link to DD-01 | None; the tunnel ends at water: "Beyond the mud you hear water running: the town's drains." | A8 |
| DD-02 | Book of Sorcerer's Knowledge | Current Intellect ≥ 20 (potions and items count): +2 Intellect once per character; below 20: the source's headache text and ~10 % HP damage, nothing used up; texts aaze0056:5–7 with "+25" rescaled to "+2" | A8 (event, clicking member), A3 (bit), A2 (record) |
| DD-02 | Monsters | Ellinger's wards (Flying Feet, Guardians), waking gargoyles, bats incl. beholder bats | A8 |
| DD-02 | Outside on D1 | Five storeys: five rows of windows with string courses, a slate cone, ~1,800–2,200 to the eaves, the tallest thing in Castleview | A6 (D1; triangles at L4) |
| DD-02 | Dead mirror | Flavour only, no prompt: before stage 4 "The mirror does not respond."; after `m26.stage4` "The mirror shows Ellinger's study, and a small sign: 'Private. Use the one in the square.'" | A8 |
| DD-02 | Lift | Two stops (ground floor, study), shaft closed on floors 1–3 | A8 |
| DD-03 | Stages and acts | Stages 1–2 in Act III (24 monsters, 26–40), stages 3–4 in Act IV; MAPS row "III–IV, 24 → 40, 26–45 (Scraps 70 optional), 54", split like XD-13; Scraps counts in Act IV (D-1.2, ~1.4k); DD-03 ~20.9k (+1 %) | A2 (MAPS, split, recount) |
| DD-03 | Who is where | Spirits in the parts still out of phase, liches and bone dragons in the dungeon, Blackfang's vampires on the Queen's floor | A8 |
| DD-03 | Liches | Five Liches 35; three named Vexor the Black, Clemon the Dead, Saxar the Permanent, two more by A3 in that form; the `t2-a.cells` ledger quotes the source's list incl. the dragons: the well's two Bone Dragons Iron Vithnipravad and Argonax, and Scraps "Drothnavod the Weighty"; new hook `t2-a.liches` sets `liches_slain` when the cell block's group is dead | A3 (hook, names, ledger), A8 (names on actors if shown) |
| DD-03 | Safes | Stage-1 `m19.safes` trapped locked chests any party opens; the guessed ground-floor safes out; two optional tougher safes (armory, dungeon vault) at 10-11-12, armory fail text "A tougher safe than the others. Three dials." (Guido's tip from stage 3) | A8, A4 (Guido's greeting as written) |
| DD-03 | Throne room | Walkable; the throne itself is house 4501's door (`thing:kalindra_throne`) | A4 (dd03.yml), A8 |
| DD-03 | Phase wall | One shimmer texture shared by D1's ghost-castle exterior and DD-03's phase walls (not `xufield`) | A6, A8 |
| DD-03 | Scraps | Behind a kennel portcullis worked by the lever under "Don't let Scraps out!", at the foot of a stair lower than his body (288 or less; XD-07's method, D-32); XP in Act IV | A8, A2 |
| DD-03 | Stable yard | Open-sky yard inside the castle (`sky`/`open_sky`) with stables 4510 and mirror 4512 behind the stage-4 phase wall; coaches arrive at D1's `kalindra_gate`; the `kalindra_stables` arrival dropped | A4 (arrivals, routes), A8 |
| DD-03 | James the Spy | Left out (his Roland line spoils M21); A4 adds **Carl the Mason**, a stage-1 talking actor in the kitchen with aaze0041:35 ("just keep walking"), the one answer to the coat closet's illusory wall; the cook Audrey optional | A4 (NPC in dd03.yml), A8 (place) |
