# DD-12 and DD-14, A8's follow-ups: decisions (D-52)

Decider D-52, 2026-11-21. This answer builds on D-42 (`mockups/act4_a8_decisions.md`). Where the two differ, this one wins.

---

**1. DD-14's rest encounters**

- **DECISION:** One rest slot, vampires at **Dif 5, [2, 3], weight 100**, encounter 10 %. The second slot (Dif 1, [1, 2]) is dropped.
  - The indoor table gives Dif 5 as 10 / 50 / 40 for tiers A / B / C: Gnome Vampire 32 / Vampire 40 / Vampire Lord 50.
  - Today's Dif 0 w75 + Dif 1 w25 draws the Gnome Vampire about 97.5 % of the time. He is under the 36–58 band and is placed nowhere in the castle.
  - The remaining ~10 % Gnome Vampire is accepted as a named exception, as in D-43 and D-46.
  - Dif 4 is not chosen: it leaves 30 % of rest draws under the band.
- **WHY:** D-42's rule is in-band hostile rows only. The engine has no tier range per slot and Dif 5 is the highest, so this is as close as the table gets, exactly as D-46 settled DD-20. The Vampire and the Lord are the castle's own placed tiers, so a rest fight looks like the castle.
- **WHO ACTS:**
  - A2: row 9167's slots become `Xeen Vampire` Dif 5 [2, 3] w100 with no second slot, and a note on the row: "Gnome Vampire 32 in ~10 % of rests accepted, D-52".
  - A8: change the slot lines in `project.yml` to match the row, and point NOTES DECIDE 4 at D-52.
- **REVERSIBLE:** Cheap (one table row).

**2. DD-12's gates**

- **DECISION:** Keep the qbits 117441–117445 as built. A gate answered "Yes" stays open after the dungeon refills.
- **WHY:** By D-43's rule, a mechanism gets two states only when going back does something. Asking the same question again after a refill only repeats the joke, and nothing new lies behind the gate. The lift passes the gates once `m24.bird_freed` is set, and each gate already opens by hand from beyond. D-18's "map variable, never a qbit" was about hidden monster guards that must come back with a refill, not about doors.
- **WHO ACTS:**
  - A3: register 117441–117445 (gate1–gate5) in DD-12's block. This is already listed as open in the NOTES.
  - A8: point NOTES DECIDE 4 at D-52.
- **REVERSIBLE:** Cheap. Switching to map variables only changes five tests in the generator.

**3. DD-12's Negative Soul Waters**

- **DECISION:** Accept the fixed 25 HP and 10 SP with the never-kill guards as built. Do not ask A1 for a read of current HP or SP.
- **WHY:** At the party's level of 37–39, 25 HP is about a tenth of a typical member's HP, so the source's intent survives. The waters are flavour beside the T4 chest, and D-42 asked nothing of A1. The engine already compares current HP and SP (`IsAtLeast(HP, …)`), so an `IsAtLeast` ladder could approximate a tenth later without any A1 work, if a playtest ever shows it is needed.
- **WHO ACTS:** A8: point NOTES DECIDE 6 at D-52. No one else.
- **REVERSIBLE:** Cheap.

**4. DD-12's NOTES DECIDE, the four layout-only choices**

- **DECISION:** All four are accepted as built.
  - **(1)** The lift head stays at the west end of the hall of storage. The shaft has to sit at the maze's west end so the letters stay clear of the other floors, and D-42 (2) asked only for a closed shaft from the aviary to L1.
  - **(2)** The maze's two halves meet once, through the L, with the throne on the path. A second meeting would draw a stroke across the letters, which D-42 (3) made the condition for the maze. Every party now passes Q-D25's throne, which helps an optional answer-giver.
  - **(3)** The three cells sit off the south walk, one set of bars per lever. That is a clearer cause and effect than the graph's cell block.
  - **(5)** The birds, hourglasses and levers act on a click, with no question. None of them has a downside or a cost. The question as gameplay is the gates' joke and should stay theirs alone.
- **WHY:** Each choice is cheaper and keeps what D-42 required: the letters read, the lift cannot skip a gate, and the gates keep their question. None changes a count, a reward or a route.
- **WHO ACTS:** A8: mark DECIDE 1, 2, 3 and 5 "accepted, D-52" in NOTES. Nothing to rebuild.
- **REVERSIBLE:** Cheap. 1 to 3 are medium after the bake.

**5. DD-14's octopods**

- **DECISION:** (a). A2 makes a placed-only indoor octopod row without the swimmer AI; A1 adds nothing. The row:
  - **11473 "Octopod"**, in the octopods family block, with 11470's numbers: level 50, 3,000 XP, Paralyze, Water attack.
  - **No** swimmer or `movement: swim` modifier, whether from the family or the tier.
  - `stand` (immobile), `no_arena` as the family, and the same model descriptor as 11470.
  - The kill XP is unchanged, so 40.91k holds.
- **WHY:** This is D-36 (2)'s fallback and what D-42 (4) asked for. Octopods appear only in D4's lake and in this cistern (MONSTERS_AND_ITEMS), so no other dungeon needs indoor swimmers. The engine already runs MM9's indoor swimmers inside `water_volumes`. Their rule is to engage only targets that are themselves in water, and a 96-deep cistern can never satisfy it unless the party swims, so (b) would be engine work aimed at the wrong behaviour.
- **WHO ACTS:**
  - A2: row 11473 as above. Make sure the generator does not copy the family's swimmer modifier onto it.
  - A8:
    - swap the five cistern actors from 11470 to 11473;
    - stand them where a melee blow from the banks and ledge reaches them;
    - run `playtest_octopods.yml` (reach, hit back, hurt by the party) and add it to `four.sh`'s default list.
  - A1: only if the non-swimmer row still takes no damage from the party's attacks. That is a bug to report with the trace, not a design question.
  - S: the octopod model must stand on a pool bed as well as swim at D4. If the swimmer binding centres the body (the swimmer rule), give 11473 a second descriptor with its origin on the ground.
  - The Sea Monster figure is a stand-in, so DD-14 is not done until S's octopod is bound (lane rule).
- **REVERSIBLE:** Cheap. If indoor swimmer water facts ever land, the five actors go back to 11470.

**6. DD-14's peaceful rows for Ambrose and the Queen**

- **DECISION:** Confirmed. Both get placed-only, immobile, peaceful, uncounted, NoArena rows with their own friendly factions. Both are talking actors carrying their NPC ids, and both are made to take no damage.

  **Ambrose: row 11917 "Ambrose"**
  - Faction `character_ambrose`.
  - A knight's armoured body, not a peasant (A2 picks the stand-in; S's skin comes later).
  - One row serves both of his maps:
    - **D6:** it replaces the sketch's Peasant stand-in, carries npc 5512, and is hidden after `m25.done` (D-49 change 6).
    - **DD-14's landing:** shown from `m25.done` and never hidden (D-42 (1)).
  - On DD-14, 5512 gets a topic from `m25.done` that asks aaze0045:1, "Are you ready to leave this awful place, friends?".
  - That topic and the griffin's perch click both call `m27.fly_out`, which now holds the move to D4's `entrance:dd14_griffin`, so the destination is written once.

  **The Queen: row 11918 "Queen Kalindra"**
  - Faction `character_queen`.
  - A pale, regal vampire body, since she is cursed until the crown (M24, M27).
  - Carries npc 5001, so a click opens A3's "The crown" topic directly.
  - Hidden on load once `done` 111542 is set. The bench's "The Queen has gone home." stays.
  - Vampires and gargoyles do not fight her.

  **Both:**
  - A load event calls `SetMm9ActorCanReceiveDamage(<actor>, false)`, D-51's existing word for Corak.
  - Ambrose is the only way out without spells, and the Queen is M27's quest giver.
- **WHY:**
  - D-25 and D-42 (DD-05 (4)): placed peaceful figures are their own named rows and factions.
  - D-49 (the tethered griffin and Ambrose shown or hidden by stage) and D-50 (Slick placed-only, immobile, uncounted, NoArena) set the rest of the shape. Unlike Slick, these two need their NPC ids, because their topics are the content.
  - Placed indoor actors with an `npc_id` already talk (XD-22's Shinobu, DD-19's Blastem, the Master Thief 5109), so A8's word "a talking placed indoor monster" needs no A1 work.
- **WHO ACTS:**
  - **A2:**
    - rows 11917 and 11918;
    - factions `character_ambrose` and `character_queen`, with no infighting with vampires, gargoyles or the griffin;
    - the bodies.
  - **A3:**
    - 5512's DD-14 topic, from `m25.done`, aaze0045:1;
    - `m27.fly_out` takes the `evt.MoveToMap(6144, 5120, 1216, 1024, …, "xeen_d4.odm", {direct = true})`;
    - `m27.queen_cell` becomes the cell door's or entry's first text, not the bench's.
  - **A4:** in `d6.yml`, 5512's `actors:` names row 11917 on both maps; 5001's `place` names row 11918 in DD-14's cell. Also add `{direct = true}` to D6's flight (DD-14's NOTES, Open).
  - **A6:** D6's sketch line for Ambrose changes from Peasant to 11917.
  - **A8:**
    - place both, with their npc ids;
    - the load events: no damage for both; hide the Queen after 111542;
    - the perch calls `m27.fly_out`;
    - playtest: talk to Ambrose and fly out; strike each once (no damage, stays peaceful); the Queen's topic; after `done` and a load, the Queen is hidden;
    - remove "Words needed 2" from NOTES.
  - **S:** an Ambrose skin and a cursed-Queen skin.
- **REVERSIBLE:** Cheap.

---

**SUMMARY ROW**

| D-52 | 2026-11-21 | A8's DD-12 and DD-14 follow-ups | DD-14 rests: vampires Dif 5 [2,3] w100, ~10 % Gnome Vampire accepted (as D-46). DD-12: gates keep qbits 117441–117445 (D-43); Negative Soul Waters fixed 25 HP/10 SP, no A1 read; DECIDE 1, 2, 3, 5 accepted. Octopods: indoor row 11473 without swimmer AI, stationary; S grounds the model; no A1. Ambrose 11917 (D6 and DD-14, npc 5512, leave topic → `m27.fly_out`) and Queen Kalindra 11918 (npc 5001, hidden after done): peaceful, placed-only, unkillable. Detail: `mockups/act4_a8_followups_d52.md` | A2, A3, A4, A6, A8, S, A1 (bug only) |

---

Checks behind these answers:
- The indoor Dif table is in `game/indoor/IndoorWorldRuntime.cpp`: Dif 0 is 100/0/0, Dif 5 is 10/50/40.
- Row 9167 in `assets_dev/worlds/xeen/data_tables/map_stats.txt` is the source of today's 97.5 % Gnome Vampire.
- MM9's indoor swimmers and their only-in-water rule are described in `devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md`.
- Rows 11473, 11917 and 11918 are free in `monster_data.txt`.
- The four layout choices come from `devdocs/xeen/briefs/dd12/L4/NOTES.md` and the octopod, Ambrose and Queen requests from `devdocs/xeen/briefs/dd14/L4/NOTES.md`.
