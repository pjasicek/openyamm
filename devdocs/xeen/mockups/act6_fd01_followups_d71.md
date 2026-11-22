# FD-01's build choices and D4's cauldron: decisions (D-71)

Decider D-71, 2026-11-21. **Read:**
- D-69, and FD-01's L4 NOTES and graph.
- D-70 Q2, D-66, D-67 and D-63, and `lanes/README.md`.
- `m39.yml` (the `statue`, lever and `roland` hooks; `once` with `else_text` is already used by the levers, the warden's chest and the coffin).
- D4's `gen.py` (`daily()`, `thing:reed_cauldron`), `xeen_d4.lua` event 79, and `Xeen.usedToday`.
- The source text `dark/aaze0052`.
- The baked tour `things1_1..4.jpg`, and full size the shots 10 (shaft arrival), 12 (ladder), 19 (west lever), 23 (pyramid), 27 (key vault box) and 33 (coffin), plus `fix1/08-27`.

## Part A: FD-01 Alamar Depths

1. **The stasis vault lies east of the lift foot.**
   - **DECISION:** Accept.
   - **WHY:** The player never sees which way the graph draws the vault. Built east, the vault lies under no room, and the lift, the pair and the path are the same. It costs one line in `geo.py` to reverse. D-69's page wins over the graph, so the graph is not redrawn, and the NOTES already record it (DECIDE 1).
   - **WHO ACTS:** none.

2. **The stasis field is four translucent `xafield` sheets with no roof.**
   - **DECISION:** Accept.
   - **WHY:** A roof sheet would pass through the coffin as the field sinks, which is the fault that D-69 change 2 avoided. The sheets carry the "Coffin" click, so a click on the field is not lost. The open top shows only from the tour's raised camera (33). At the party's eye height the sheets reach above sight.
   - **WHO ACTS:** none.

3. **The shaft's ladder is built in geometry.**
   - **DECISION:** Accept the method. **Change** how it looks, as polish item P1, which is required.
   - **WHY:** `bemv` reads as a pole and `d1ladder`'s stone fights `xahullbn`, so building it in geometry is right. But as built, the rails, the rungs and the backplate are all the same riveted `swgirder`. From the arrival (10) and up close (12) they merge into one riveted strip up the wall. It carries the "Ladder" hover and is the click, so D-66's standard applies.
   - **WHO ACTS:** A8 (P1).

4. **The chests are riveted steel lockers.**
   - **DECISION:** Accept.
   - **WHY:** This is D-67 item 4's precedent. In the shots of the warden's room and the stasis vault (28, 33 and 34) they read as strongboxes. Wooden chests would look out of place in Alamar's machine undercroft.
   - **WHO ACTS:** none.

5. **Alamar's statue after the boast.**
   - **DECISION: Change.** Later clicks show a short line on the status bar.
   - **WHY:** A titled object that answers nothing looks broken, and the audit flags it (`click.silent`, event 36). Every other once-only thing in this map answers later clicks:
     - the key box ("Nothing here.");
     - the levers ("The lever won't budge.");
     - the warden's chest (the empty cushion);
     - the coffin (the empty line).

     The plate stays silent, because the map's guard on 117840 already stops it.
   - **WHO ACTS:**
     - **A3:** add `else_text` and `else_status: true` to `m39.statue`, for example "The statue says nothing more. Alamar has had his say.", and regenerate.
     - **A8:** in `playtest.yml`, after the boast the plate shows nothing and the click shows this line on the status bar. Rebuild only if the map's Lua changes, then run 4 of 4 from assets_dev. The audit info on event 36 should then be gone.

### Polish

**Required before FD-01 counts as done (D-66's standard):**

- **P1. The ladder reads as a ladder.**
  - Make the rungs separate bars, about 24 thick and 96–128 apart, standing well off the wall, with the two rails proud of the rungs.
  - Drop the riveted backplate, or set it back in a darker face, so that the gaps between the rungs show dark. The shaft's own `xahullbn` behind the ladder is enough.
  - The click moves to the rails, the rungs and the wall strip behind them. The hover stays "Ladder".
  - No new texture. Check it in baked shots 10 and 12.
  - **WHO ACTS:** A8.
- **P2. The levers read as levers.**
  - Today each is a riveted plate with a small orange slot (19), which reads as a wall box. Each is titled "Lever", and the source has two big levers.
  - Build a pivot boss on the plate and a steel arm about 32 square and 160–192 long with a grip, in shipped Ancient steel, so that it reads from the middle of the lever hall.
  - Preferred, but not required: make the arm a rotating mover (`devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md` covers levers) that throws down on the pull and stays thrown on every load by 117841 and 117842. That shows on the spot that the pull did something (D-43).
  - **WHO ACTS:** A8.
- **P3. Rebake and recheck after P1, P2 and item 5.**
  - Rebake, run 4 of 4 from assets_dev, and reshoot `things1`.
  - In the reshoot, say what the pale, flat blue shape in the foreground of baked shot 27 is. It is absent from `fix1/08-27`, so it is probably a robot clipped by the camera. If it is an untextured face or object, fix it.
  - **WHO ACTS:** A8.
- **Gates that still stand:**
  - `playtest_in.yml` after A6 rebuilds D6 (D-69 relay).
  - D-69 change 8's statue is met: S's teal statue reads right in shot 04. A8 takes it off "Waiting on".

**Not required (later polish, no blocker):**

- **The pyramid's pale tone.**
  - It reads clearly as a pyramid (23).
  - It wears its working twin's cladding on D6, which suits "Its twin stands outside the gate."
  - "Its light is out" needs no dark texture.
  - If A8 wants it darker, use no new texture: a darker shipped Ancient face, or no light near it.
- **Racks in the key vault.** If they are added, they are untitled, on the east and west walls only. The titled box stays the only box on the south wall, so the critical-path click does not turn into a hunt among the racks.
- **The lever throw as a mover** (the preferred part of P2).

## Part B: D4's coven cauldron

- **DECISION:** Confirm A6's build: once a day for the party, tasted by the active member only (`everyone=False`). No change.
- **WHY:**
  - D-70's "all members" rule is for temporary bonuses (rule 1). The cauldron gives none. Its gain is +100 spell points, a restoration capped at maximum, which rule 4 exempts. It uses the daily helper only because its text says "Tomorrow." (rule 4's last clause).
  - Its downside is poison. Run for every member, one coin flip would either refill everyone's spell points or poison the whole party at once. That turns a witch's single taste into a party draught.
  - A2's planned guard check does not flag it, because SP is not a `*Bonus`, `ArmorClassBonus`, resistance or level.
- **WHO ACTS:** A6 only notes the exception in D4's NOTES: "the cauldron is a one-member gamble, so D-70 rule 4 applies, not rule 1 (D-71)". No regeneration.

## SUMMARY ROW

| D-71 | 2026-11-21 | FD-01 build choices; D4 cauldron | Accepted: vault east, field without roof, ladder built in geometry, steel lockers. Changed: statue's later clicks get A3's status line. Before done: ladder reads as ladder (rungs off the wall, no merging plate), levers get real arms; reshoot. Later: pyramid tone, key-vault racks. D4 cauldron stays daily, active member only (a restoration gamble, rule 4). Detail: `mockups/act6_fd01_followups_d71.md` | A8, A3, A6 |
