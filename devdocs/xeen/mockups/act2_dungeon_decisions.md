# Act II dungeons: decisions on the graphs' open questions

Decider D-4, 2026-11-20 (devdocs/xeen/DECISIONS.md). The build reference for the map lanes beside
[act2_dungeon_graphs.md](act2_dungeon_graphs.md); where the two differ, this file wins.

## XD-07 Castle Burlock
1. Hostile wing in a friendly castle: the King's Guard peaceful to the party by a relation row; a closed door at the foot of the west tower separates the fools and gargoyles from the court; factions otherwise at default.
2. Mad Fool 8 under the band: fill from the Madmen tiers, mostly Raving Lunatic 12 with Mad Fool 8 mixed in; no new tier.
3. Ice Troll at 18: use the Trolls A row (Troll 18) unchanged; the room is "Old cistern"; nothing calls them ice trolls.
4. Caged Fire Dragon 75: optional fight kept, family's Fire Dragon row; the lever raises a portcullis at the foot of a narrow, low stair from the pit gallery into the pit, lower than the dragon's body (it is 487 tall; D-32's radius cap lets it through 128-wide gaps) so it never leaves the pit; "Do not pull" sign kept.
5. The throne throws the party onto X4, about 1,000 above the ground beside the west tower outside the walls, ordinary fall damage.

## XD-25 Asp Undercroft
1. Pedestals on X4 round Asp's well (Q-C5 as written): eight, each red/blue on touch; solved when the south-west one and every second one round the ring are red; the rule stone stands by the undercroft stair; one qbit across maps.
2. The rhyme: Eve's Transformer topic also says it outright ("Start with the south-west stone, make it red, then every other one red all the way round").
3. Guardian Asps (30) left out; the keeper's cell holds Snake men C (26).
4. Caged half-turned townsfolk kept: peaceful peasants behind barred doors, released when the machine dies ("Thank you for saving us!"), hidden by qbit on the next entry.
5. The door of light as XD-04's ward: a door leaf with a generated translucent light texture, opened by the pedestals' qbit.

## XD-26 Gargoyle Eyrie
1. Carlawna's theft line on the fence's tag, her thanks, the stock "The chest is empty." — accepted.
2. The fence's tags kept ("Deliver to Asp: one scarab").
3. Flying monsters across the shaft: the L4 playtest spawns a gargoyle on each ledge and asserts it reaches the party across the shaft; no gargoyle in a nook or shelf opening; if they stick, more on ledges, fewer in the air.

## XD-13 Newcastle Keep
1. Stage 3 is quiet: the cellar 6 swamp things (Bog Thing 26, Marsh Horror 32); the laboratory and vault door one group of 4 Iron Golems 40; 10 monsters, 25 over all stages; their XP counts in Act IV.
2. Crodo's M21 speech adds "The vault's word is 'laboratory'"; an M23 autonote records it; Elona keeps her joke.
3. Syllable notes numbered "1: la" … "5: ry".
4. Services inside the keep as BLV house doors by stage.
5. YOUR well: +20 AC temporary (raised to 20 if lower, until rest), free and repeatable.

## XD-08 Tomb of a Thousand Terrors
1. Tomb Terror 40 left out; the Hall of a Thousand Terrors is guarded by Tomb Guards 26.
2. Tomb juices: +2 permanent, once per character per colour; seven colours, one stat each; later drinks "The liquid is powerless."
3. Megacredits: 5 (Yak 6 + Tomb 5 + Golem 5 = 16 for 15 needed).
4. The cage as a lift: one mover of the cage floor plus its see-through bar panels (XD-04's method); if the bars cannot ride, the bars line the shaft and only the floor moves.
5. The coffin's Might check: the clicking member needs Might ≥ 30, potions and spells counting; the barracks chest holds two fixed Might potions.

## XD-09 Golem Dungeon
1. Master of Golems: the party award plus 3,000 experience; no level.
2. Kill XP: swap 2 Iron Golems for 2 Stone Golems (23 wood, 16 stone, 5 iron, the boss; 45 monsters; about 7 % over).
3. The block field: nine two-state blocks, each sliding one block's width into its own recess; six hide glowing rocks; each bared rock lights a lamp over the Iron door.
4. Boughs and tumblers: indoor destructibles whose events update the plaque's count; two-way levers whose bolts move visibly.
5. Its door on X5 near the east edge, within easy reach of the X3 arrival, only A-tier monsters nearby.

## XD-10 Cave of Illusion
1. Mirages: door faces flagged clickable and touch, with a visibly shimmering wall texture; a click or a touch gives "The mirage dissipates with your touch." and opens it at once; no walk-through faces.
2. Draining: the water surface is one door mover sinking about 640 over about 6 s; everything below stays closed by its own stone sluice gates opened by the same event; the ledge is railed. If A1 finds the moving fluid face drawn or colliding wrongly, swap two face sets by qbit behind a fade ("The water roars away down the sump.").
3. The plug's Might check: Might ≥ 30 on the pulling member, potions counting; a fixed potion behind the mirage.
4. Gems and stat rises: the key 10 gems; once per character: upper skulls +2 for 3 gems, deep skulls +3 for 5, the grotto +5 (Might, Endurance or Accuracy) for 10; a fixed cache of 15 gems in the echo cave.
5. Arrival: the north mouth; the south mouth leaves to the Troll Forest side of X5; X5's south-mouth door enters by explicit coordinates until A1 adds more than one arrival per dungeon.
6. Both mouths on X5 near the east edge.

## XD-11 Tower of High Magic
1. Brews: +5 permanent resistance, once per character per brew: Fire → Fire, Electric → Air, Cold → Water, Poison → Body, Energy → Earth, Magic → Mind.
2. The Art of Magic is a readable lore book only; a Prismatic Light spellbook item in the library instead of Mysteries of Light teaching by event.
3. Carnage Hand kept for Darzog's Tower; Sorceress 30 tops the tower; the Head Sorceress a named row at 32, whose death drops the Librarian's Key.
4. The lift: three stacked short lifts in one shaft (0–1, 1–2, 2–3), each running once its floor's landing lever is pulled; one cage if A1 adds a multi-stop lift before L3.
5. The source's fire dragon left out.

## Other lanes
- A2: King's Guard relation row; Head Sorceress row (level 32, drops the Librarian's Key); the Fire Dragon's height (487) higher than XD-07's stair (D-32); values (juices +2 × 7 stats, brews +5 × 6 resistances, YOUR well AC 20); fixed items (Might potions in XD-08 and XD-10, Prismatic Light spellbook in XD-11, XD-10's 15-gem cache); skull prices; kill XP recount (XD-09's mix; XD-13's stage 3 in Act IV).
- A3: Eve's plain pedestal rule; Crodo's "laboratory" line and the M23 autonote; XD-10's skull hook texts at these prices; Artemus's Dungeon Key line says "trolls".
- A4: the King, Artemus, Emerson and Roxanne as house doors in XD-07; Newcastle's keep services as BLV house doors by stage.
- A5 (X4): the eight pedestals and the rule stone round Asp's well; the throne's landing point; the eyrie's sky-crack ledge. A6 (X5): XD-09's door and XD-10's two mouths near the east edge, A-tier monsters nearby.
- A1: does a moving fluid face indoors draw and collide right (XD-10); more than one arrival per dungeon; optionally a multi-stop lift; does an actor's radius keep a large monster out of a narrow passage (XD-07).
