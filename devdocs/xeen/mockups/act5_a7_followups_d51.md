# Act V dungeons, A7's follow-ups: decisions (D-51)

Decider D-51, 2026-11-21. These answers follow on from D-47 (`mockups/act5_a7_decisions.md`). Where the two differ, this file wins.

---

**1. Corak before he wakes (DD-16)**

- **DECISION:** Keep what A7 built: Corak stands inside the closed stasis field from the first load. This corrects D-47 Q20.
  - The field drops on `m29.stasis`.
  - He is hidden on `m32.done`, as D-47 said.
  - **The field becomes translucent.** The `xafield` leaf gets `translucent` with an opacity of about 0.5. A7 tunes the value in a capture until Corak reads as a figure and the field still reads as a field.
  - It is still a solid face, so before the phrase Corak cannot be clicked, named or struck.
  - XD-19's barrier, also `xafield`, gets the same treatment, so the crown stair shows behind it.
  - **Corak can't be killed, starting now.** A load event sets `evt.SetMm9ActorCanReceiveDamage(<Corak>, false)`. This is the existing word XD-19 already uses for Lord Xeen. It zeroes every hit, which is exactly what Corak needs for good. He no longer waits on the indoor `MonsterDamage` wiring word, and no hook is needed for him.
- **WHY:** The source line ("a figure suspended within it"), A7's graph and A3's wake text all describe a figure inside the field. An empty field before the phrase would contradict all three. A field `translucent: 1` multiplies the texture's own alpha by 1, so the opaque `xafield` texture draws solid (A1, merge point 12). An opacity below 1 is the documented fix.
- **WHO ACTS:**
  - **A7:**
    - Set the field's opacity in DD-16's `gen.py`, and do the same for XD-19's barrier field.
    - Add the load event that makes Corak take no damage, reading his actor index from the built scene as XD-19 does.
    - Run the playtest that strikes Corak once after the field is down: no damage, and he stays peaceful.
    - Take a capture of the closed field with Corak visible.
    - Delete "Words needed: a damage filter" from DD-16's NOTES, but keep the talking-actor word (A1's queued "NPC on a placed indoor monster").
  - **A3:**
    - Make `m29.stasis` and its `else_text` fit a figure standing in the alcove. Today they say "sits up" and "sits by his console". For example, "The field flickers out. The tall figure inside it, in a guardian's armour, opens his eyes." and "Corak stands by the dead field, very still. 'Find me a Soul Box.'"
    - Fix `m32.yml`'s header comment ("places … once m29.done is set").
  - **Orchestrator:** record that D-47 Q20's stage line is replaced by this answer.
- **REVERSIBLE:** Yes, cheap. It is one load condition and one opacity value.

---

**2. XD-16's trap-chest tell**

- **DECISION:** Accept the tell as it is: dark ember-cracked stones with a faint pulsing light under the five trap chests, and the real chest on bare ash.
  - Smoke is not a condition for the map to count as done.
  - If A1 ever adds an indoor smoke emitter, A7 adds the wisps in the same `gen.py` as a polish pass.
  - Once the lead bakes the map, the vault is captured again from about 3 m. The stones must still read, and they will, because the tell lives in the geometry and the texture, not in the light.
- **WHY:** In `11-vault-3m.png` the five dark plinths and the one bare chest stand apart at a glance, so D-47 Q2's real test (readable from about 3 m, not a blind riddle, D-4) is met. Smoke would only reinforce a tell that already reads, and it needs a new engine word that A1 holds at low priority. Holding a finished map for it would be gold-plating.
- **WHO ACTS:**
  - **A7:**
    - Take the baked re-capture of the vault.
    - In NOTES, change "Words needed: smoke indoors" to "optional polish (D-51)".
  - **A1:** the indoor smoke emitter stays low priority and does not block anything.
- **REVERSIBLE:** Yes. Adding smoke later is additive.

---

**3. XD-19, the sub-agent's choices**

**(a) Lord Xeen fully invulnerable for now**

- **DECISION:** Accept this as a blocked state, with no stand-in.
  - XD-19 counts as "built, blocked", not done. The "with the sword" playtest is the gate to done.
  - The Xeen world is not released while he is in this state.
  - A1 makes two things its next work, in this order:
    1. a studio wiring trigger for the indoor `MonsterDamage` hook, registered when the script loads and filtered to a monster row or a placed actor;
    2. E11's `attack` and `weaponItemId` context fields.
  - After item 1 above, only XD-19 needs this word.
- **WHY:** Any stand-in would be throwaway logic that hides the E11 gap. Examples are "any weapon hurts him" or "hurtable while someone carries the sword". AGENTS.md rules out that kind of masking fallback. Nobody can reach the map until X9's gate exists, so being blocked costs players nothing today.
- **WHO ACTS:**
  - **A1:** the wiring word, E11 and a unit case.
  - **A7:**
    - When both land, wire the sword branch, the `m35.untouchable` line and the sight hook on his damage path.
    - Remove the load-time `SetMm9ActorCanReceiveDamage` for Lord Xeen.
    - Write and run the "with the sword" playtest 4 of 4.
  - **Orchestrator:** keep XD-19 on STATUS's blocked list against A1.
- **REVERSIBLE:** Yes. Everything is in the map script.

**(b) The open inner arch to the great hall**

- **DECISION:** Accept. The graph's "two leaves" on `link:gate_hall` is the castle gate. The inner opening stays an open arch.
- **WHY:** The graph's own gatehall entry says "behind the two gate leaves … Lord Xeen's sigil over the inner arch". Its door count also names exactly three two-leaf pairs: the gate, the great hall's north doors and the throne doors. All three are built as pairs, so the double-door rule holds.
- **WHO ACTS:**
  - **A7:**
    - Fix `link:gate_hall`'s label in `xd19.graph.yml` to "Arch (the gate's two leaves are X9's)", so the graph matches the map.
    - The sigil over the arch comes with the banner texture in (c).
- **REVERSIBLE:** Yes, cheap.

**(c) The seven new textures**

- **DECISION:** Require all seven before XD-19 counts as done: the four generator cores, the sigil banner, the Sixth Mirror and the shattered frame.
  - The shipped stand-ins stay until then.
  - A7 makes them in one Codex batch through the already prepared `xtex.py --project output/studio_cal/xd19/tex`.
  - Once the shattered frame exists, the cinematic swaps the mirror to it.
- **WHY:** In the sheets the water, earth and fire cores are the same teal `xaenergy` panel, and the element-coloured lights do not carry that difference unbaked. Since the pylons point the party at "its generator", the generators must read apart. The Sixth Mirror is the goal of the whole game, and today it is a blank white rectangle behind Lord Xeen (shot 16). Seven textures against about 147 used out of 450 is no budget pressure, and D-47 already asked A6 to register them.
- **WHO ACTS:**
  - **A7:**
    - Make the seven textures (specs, Codex, checks) and install them.
    - Lay them on the cores, the banners, the sigil over the inner arch and the mirror.
    - Swap the mirror to the shattered frame on `m35.done` and in the cinematic.
    - Rebake.
  - **A6:** register them, as D-47 already relayed.
- **REVERSIBLE:** Yes. Textures can be swapped back at any time.

**(d) The keeper's loft "ladder" as six steps**

- **DECISION:** Accept the six steps.
- **WHY:** The graph's link already says `kind: stair`; only the prose says "ladder". Steps let the loft's three monsters path in and out, and a loft one short flight up reads well enough.
- **WHO ACTS:** A7 changes "up a ladder" to "up six steps" in the graph's purpose text.
- **REVERSIBLE:** Yes, cheap.

---

**4. DD-24's `xdthrone`**

- **DECISION:** Redo it once, darker.
  - **Target:** near-black wood, mean luma about 20–25, saturation well down (about 120 or less), with the old blood as the only clearly red in it.
  - Keep the plank-and-peg structure and the seam pass.
  - Choose between the two versions with an in-game capture of the throne against the hall's walls and plank roof.
  - If the dark version does not read as wood there, keep v1 and record why in NOTES.
- **WHY:** The brief and the spec ask for "very dark, almost black" wood with blood soaked in. v1 came out with luma 38 and saturation 199, the same warm brown as d14's planks, the cave rock and the roof. The bloody throne is the map's set piece and its goal, so it has to stand out from that warm room. It is one cheap Codex texture.
- **WHO ACTS:**
  - **A7:**
    - In `level_generation/textures_xeen/a7_dd24_giant/specs.yml`, set `tone.factor` to about 0.35 and desaturate.
    - Generate v2, run the checks and capture the throne.
    - Install the chosen version (`xtex.py install`) and rebake.
  - **A6:** nothing new, since the name is unchanged.
- **REVERSIBLE:** Yes. v1 stays in `raw/`.

---

**SUMMARY ROW**

A7's Act V follow-ups: Corak stands inside the stasis field from the first load (corrects D-47 Q20), the field is translucent (about 0.5) so he reads, and `SetMm9ActorCanReceiveDamage` makes him unkillable now. XD-16's ember-stone tell is accepted; smoke is optional polish. XD-19: Lord Xeen stays invulnerable, blocked on A1's MonsterDamage wiring word and E11, with no stand-in. The open inner arch and the six-step loft are accepted, and the seven textures are required before done. `xdthrone` is redone near-black.
