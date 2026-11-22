## DD-19 Wizard Quarter

D3 · M · party 38 → 41 · 32–55, Xenoc 60 (Morgana 65) · 50 · treasure 4 (hoard 5) · Q-D14, Promo Spy

![DD-19](act4_graphs/dd19.svg)

The source has no wizard-quarter map of its own. The quarter was a corner of Sandcaster (dark maze0031). Its labels
were the Sorceress HQ, the Mirage Guild, ten Guild Quarters, two Guild Commons and Weights and Measures, and about 47
hostile casters lived there. The graph builds it as the precinct behind D3's guild gate:

- an open-sky guild court in the quarter's pink hc stone;
- Xenoc's **Mirage Guild** to the west and Morgana's **Sorceress HQ** to the east, two storeys each;
- a covered bridge between their upper floors;
- the guilds' quarters, alembic cellar and vault in an undercroft below the court.

Size: 27 review rooms on three levels (upper floors 640, court 0, undercroft −512), about 32–36 sectors. 13 doors.
The footprint is about 5,000 × 3,000, roughly 45 M units².

- **Monsters (50):**
  - Wizard 36 (16), Sorcerer 45 (4) and Xenoc 60 (11196) in and under the Mirage Guild.
  - Enchantress 40 (10), Grand Sorceress 55 (2) and Morgana 65 (11183) in and under the HQ. These rows use S's
    `xeen_sorc` model (D-32). Morgana wears her own skin, bound as `sorc_m` in actors.yml (D-32's "e.g. xsorc_m").
  - Carnage Hand 35 (12): the guilds' conjured servants, on `xeen_hand`.
  - Iron Golem 40 (4): the wardens of the vault.
  - Blastem the Wizard is a talking actor and is not counted.
  - Groups of 2–3. The court is empty (D-11.3).
- **Path:**
  - Through the court's west double door into the Mirage Guild.
  - The hall of illusions, then the stair up to the mirror gallery. The tall mirror shows a door in the blank wall
    opposite. That wall is the mirage (XD-10's illusory wall), and Xenoc's Hall of Mirages is behind it.
  - Xenoc's study holds a chest (T4) and the vault lever.
  - Draw the bridge bolt, cross over the court to the HQ's scrying room and snuff ward lamp 1.
  - Go down to the robing room and snuff ward lamp 2. The ward on Morgana's door fades.
  - Morgana's sanctum, then her wardrobe (T4). Back to the court by the HQ stair.
  - The two can be done in either order. From the HQ side the bridge door is bolted, and Xenoc's voice answers
    through it.
- **Off the path:**
  - The Guild Common: Blastem, and the font of spell points.
  - Weights and Measures: the tax chest (T4).
  - The undercroft:
    - the potion alcoves (Orange +2 Intellect, Purple +2 Speed, once per character);
    - the wizards' quarters, whose chest (T4) springs "Ambush!" (four hidden wizards shown, D-18's pattern);
    - the sorceresses' quarters (T4) and the alembic cellar;
    - the vault (four Iron Golems, the hoard T5), behind an iron door worked by the lever in Xenoc's study.
- **Loops (3):**
  - over the court by the bridge, once Xenoc's bolt is drawn;
  - under the court into the HQ by its back stair;
  - under the court into the Mirage Guild by its stair's foot.
- **States:**
  - the mirror and the mirage wall (no state; always passable);
  - the bridge bolt (two-state, Xenoc's side);
  - two ward lamps (two-state map variables): both out opens Morgana's door, one out "The ward thins, but holds.";
  - the vault lever (two-state);
  - the ambush (a map variable, once);
  - Blastem's two answers;
  - the two kills.
- **Exit (the `exit` preset, D-24):**
  - The guild gate's inside face, both ways.
  - The inside arrival is **`entrance:d3_guild_gate`**: the court's south side, about 384 inside the gate, **facing
    north** (MoveToMap 512), into the court, with the gate at the party's back.
  - The way out returns to D3 about 300 south of the gate, facing south (1536): about (−10496, 22150, 1728), A5's
    choice.
  - The gate is a fixed exit face, not a moving door, so the inside face takes MM6's `hclgdr` once (the double-door
    picture made for 256), as outside.
- **Hooks (all placed):**
  - `q-d14.xenoc`: the Hall of Mirages, on Xenoc's death (once).
  - `q-d14.morgana`: Morgana's sanctum, on her death (once).
  - `q-d14.quarter_gate`: D3's (A5's `thing:dd19_gate`, "Enter?", open from the start). This map holds its arrival.
- **Textures:** about 40 of 45, 0 new.
  - The court, the Common and both foyers: the town kit's MM6 hc set (pink ashlar, gothic windows, statue niches,
    `t1f1`/`t1f2` marble). The gate then opens onto the stone the quarter shows outside.
  - The Mirage Guild: MM6 Icewind Keep 6d15 (grey-blue brick with red bands, beam ceilings, the `orair32` shimmer).
  - The HQ and the undercroft: MM6 Corlagon's Estate 6d11 (dark brick, skull niches). The two halls read apart.
  - The two great-hall doors are double doors: two leaves, MM8 `t07c03c` and `t07c03d`, one wing picture each, in
    `hcw1le`/`hcw1re` pilaster frames.
  - The mirror is DD-02's `glass2`. The ward leaf is XD-25's `xufield`, reused.
- **Dressing and lights:**
  - Hanging lamps from the beams in the halls, sconces on the walls elsewhere.
  - The ward lamps are a floor brazier (scrying room) and a wall bracket (robing room).
  - Benches, robe chests and the alembic's still stand against the walls.
  - The court has no props on its lines between the four doors and the gate.
- **Lines** (dark/aaze0031):
  - Blastem's insult (:51), his two answers (:110) and his humble reply (:112).
  - Wrathmont's "Begone, children, lest I blast you to ash and scatter you to the winds." (:37), as Xenoc's voice
    through the bolted bridge door.
  - "Ambush!" (:56); the Orange and Purple Potions (:57–60, +10 rescaled to +2); "+2000 spell points." (:61); "Alcove",
    "Bed", "Nothing here." (:55, :52, :53).
  - The signs: Sorceress HQ, Mirage Guild, Guild Quarters, Guild Common, Weights and Measures (:82, :95, :89, :100,
    :98).
  - A3's hook texts for the two deaths.

**Kill XP against MAPS §0** (DD-19 23.8k per member):

- 16 × 1,656 + 4 × 2,475 + 10 × 2,000 + 2 × 3,575 + 12 × 1,575 + 4 × 2,000 + Xenoc 4,200 + Morgana 4,875 = 99,521.
- That is **24.9k per member, +4.5 %**.
- With Morgana at 60: 24.7k (+3.8 %). With Blastem fought (Sorcerer 45): 25.5k (+7.1 %).

**Outdoor door check (D3 L4, `briefs/d3/L4/DOORS.md`).**

- **Matches:**
  - The gate `thing:dd19_gate` is at (−10496, 22451, 1728), in the quarter's north wall, with its face to the south.
  - It is 256 × 256 with `hclgdr`, behind A3's `q-d14.quarter_gate`, open from the start.
  - The graph's arrival and exit fit it: A5 points the gate at `entrance:d3_guild_gate`, facing north (512).
- **Mismatch:** the quarter's north wall is also the city's outer wall (the terrace ends at y 20), so on D3 the gate
  leads to the open dunes. Proposed, for A5: north of the wall, between x 40 and 47, a walled guild precinct with two
  pink hc hall roofs (two storeys, gabled) and the bridge's roof over a court wall, if the dunes there are clear. The
  alternative is no change (open question 4).

**Open questions** (options and recommendations in the graph file):
1. Morgana 65 over the band: keep it, and MAPS writes "Xenoc 60, Morgana 65" (proposed), or 60.
2. Monsters: casters with Carnage Hands and four vault golems (proposed), or casters only.
3. The court under open sky (proposed), or a roofed court hall.
4. D3's outside behind the gate: A5 adds the guild precinct's roofs (proposed), or no change.
5. Blastem as a talking actor with the source's insult, a fight or a hint (proposed), or left out.
6. Morgana's door: a ward fed by two lamps with `xufield` reused (proposed), a new ward texture, or a key.
7. The font: a repeatable spell-point refill (proposed), once a day, or none.
8. After `q-d14.done`: no change inside (proposed), or peaceful survivors in the Common.

**Requests:**
- **A2:**
  - Confirm Morgana's level (question 1).
  - Wizards, sorceresses, constructs and golems must not fight each other in DD-19.
  - The sorceresses' family header still says `stand_in: Druidess`, while actors.yml binds `xeen_sorc` (D-32).
  - Recount Act IV.
- **A4:** Blastem the Wizard (NPC row and portrait; greeting aaze0031:51) if question 5 stands.
- **A3:** Blastem's topic with the two answers and the swap to 11191. The lines above go to the ORIGINAL_LINES ledger.
- **A5:** the inside arrival `entrance:d3_guild_gate` (facing north) for `door:dd19`; the return point; question 4.
