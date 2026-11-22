# A8's build choices DD-22, DD-26: decisions (D-67)

Decider D-67, 2026-11-21. I read D-62, D-63, D-65, D-66, the lane rules, both L4 NOTES, both graphs, the L4 `rooms.yml`, `objects.yml` and `wiring.yml` of both maps, `xeen/rendering/sky/sky.yml`, `xeen_common.lua`'s sky stages, Xeen's `world.yml` (`levelRadiusLimit`), the DD-22 texture sheet (`dd22/tex/sheet1.jpg`) and the tours `dd22/shots/rooms1_1`, `baked1_1..3`, `things3_1..3`, `dd26/shots/things1_1..3` and `fix1_1`.

Every DECIDE item of both maps is accepted. The oculus is accepted, but its sky preset changes. The other changes come from four places:
- the user's note on DD-22's colour;
- D-66's Yes/No rules, which DD-22's three prompts and DD-26's grate do not yet follow;
- two pieces of furniture that carry a title and do not yet read right (D-66's standard);
- one runtime step for the Water Elemental.

**DD-22 Sheltem's Pod**

1. **Accept** the two lifts as the spine (A from deck 1 to 2, B from deck 2 to 3), with open wells and no gates.
   - WHY: A studio lift has two stops. Using the middle ring and the landing as the landings keeps one shaft room. An open well is DD-17's lift-core pattern. A fall costs hit points, not progress, because lift A's button is at the foot.

2. **Accept** the open oculus as the viewport. **Change** its preset from `xeen_darkside_fading` to `xeen_darkside_day`.
   - WHY:
     - The pod opens only after `m33.done` (D-62 Q52).
     - At M33, `xeen_common.lua` sets the Darkside back to `xeendark1`, which is `xeen_darkside_day` (the sun restored).
     - `fading` is the sun of Acts III–IV. The oculus would show a dimmer sky than the one over D6 outside the hatch.
   - WHO ACTS: A8.
     - In gen.py's atmosphere: `open_sky: {mode: open, preset: xeen_darkside_day}`.
     - Rebuild and rebake (the sky face lights the bridge), then reshoot `25-oculus`.

3. **Accept** the blast door as one `swdoora` picture split over two leaves that part in the middle.
   - WHY:
     - `swdoorb` is a different door design, not a mirror of `swdoora` (texture sheet). The graph's pair would show two halves that do not match.
     - One picture parting down the middle is how a sliding blast door reads. DD-17's door uses this and passes the doors audit.
     - The double-door rule is about winged doors.

4. **Accept** the riveted metal lockers (`swgirder` chests).
   - WHY: On a starship, a riveted steel box with the title "Chest" reads as a strongbox, so it meets D-66's standard. A wooden chest would look out of place here. DD-16's and DD-17's defaults are not reopened.

5. **Accept** 8.34 M units² of floor.
   - WHY: It is inside S's band of 7–20. The graph's "about 10" was an estimate.

6. **Change: the walls change from teal to the assigned red accents (USER).** This is required before DD-22 counts as done. It does not block A6's hatch door or A3.
   - WHY:
     - A6's assign uses the Control Center "in its red accents only", so the pod reads apart from the teal of DD-17 and FD-01.
     - Today `swll4dk`'s teal panels cover the airlock, the lower ring, the shaft's foot, the stores, the ladder, the middle ring, the gun deck and the landing. Deck 2's pale `swankdk` ceilings and the pale door reveals add more teal (baked1 01–06, 10–13, 16).
     - Red shows only on the floors and the bridge.
     - The drive, brig, security post and bridge (`swll5dk` with red pilot lights) already read right.
   - WHO ACTS: A8, in gen.py's themes, with 0 new textures.
     - `swll5dk` becomes the main wall of every room except the airlock. The airlock keeps `swll4dk` as the hull's inner skin, matching D6's outside.
     - Deck 2's `swankdk` ceilings become `swceilf`.
     - The pale `swankdk`/`swgirder` door reveals and well and hatch linings become a dark face of the sw set (for example `swll5dk`).
     - `swared` accent panels on the rings' long walls are allowed, once per face and whole (texture-fit rule).
     - Rebake and check that the rings' floors stay readable: no room may be darker than the drive in the same tour.
     - Reshoot `baked1` and give the user the sheet in the report.

7. **Change: the three yes/no prompts become Yes/No buttons.**
   - WHY:
     - D-66 item 6 says a typed "Yes" gives no hint of the answer. Phaser, Photon and the security console use a typed `question` with answers Yes/Y.
     - B1 still holds:
       - the weapons' message ends on "Fire anyway?";
       - the console's own text is its question, with no message before it.
   - WHO ACTS: A8.
     - In dress.py, use `AskChoiceWithAnswerSteps` as DD-08 and DD-15 do.
     - The playtest answers by button and still asserts the console's text.
     - Rerun 4 of 4 from assets_dev.

8. **Change: the command couch needs arms before done.**
   - WHY:
     - It carries a title and a click line ("…The harness hangs open."). Today it is a low slab under a back with a console face, and from the landing it reads as machinery.
     - This is the standard of D-63 item 14 and D-66 item 8: a seat built from blocks needs a seat, a back and arms.
   - WHO ACTS: A8.
     - Add two arm blocks, about 32 wide and 48–64 above the seat. Keep the couch facing the nose and the locker behind the back.
     - Check the couch in the baked bridge shot.

**DD-26 Olympus Sewer**

1. **Accept** the scroll as a wall panel with the shipped `scroll` picture.
   - WHY:
     - No shipped note or scroll decoration has an indoor model.
     - The parchment, placed once and whole by the stair's foot, reads as a pinned scroll (things1 04).
     - It carries D-65's "Scroll" hover (:10) and its click (:11), and it is XD-14's pattern. That meets the intent of D-65 change 1.

2. **Accept** 4 doors (the vault's inner grille is left out).
   - WHY: The bronze pair alone keeps the vault behind the password (117805 and the load event). A grille opened by the same event would add a moving part and no choice. 4 is inside S's 3–8.

3. **Accept** the standing statue (`7dec55`).
   - WHY: It is dressing, with no click or title. "Toppled" was the graph's colour, and no shipped decoration lies down. D-66 already accepted `7dec55` as a statue (DD-08 item 1).

4. **Accept** the sloped ends of the channels and the basin.
   - WHY: Anyone who falls in, party or elemental, walks out with no climb word, so nothing soft-locks. The long sides stay upright, so it still reads as a channel, as in B2.

5. **Accept** 13.4 M units² of floor.
   - WHY: It is inside S's cap of 20. The extra floor is the walking room that change 3 asked for. B2 accepted 17.7 on DD-21.

6. **Accept** the empty hanging cages (`7dec05`).
   - WHY: Empty cages suit a pet shop. MM7's other two cages hold a skeleton and a prisoner. Hung from the vault, they clear the counters and the walking lines (fix1).

7. **The walking room is met by construction. Add one runtime step. No A1 check.**
   - WHY:
     - Xeen caps every indoor body's radius at 60 (`levelRadiusLimit`, D-32, `world.yml`), so the Water Elemental moves as a body 120 wide.
     - Width can never bind against walkways and openings of 256 or more. Its height of 202 is the only number that can bind.
     - The lowest opening on a walking line is 320, and every ceiling is 448 or more.
     - A body-size reach check in the audit would only test that one number. It stays an A1 backlog item, for a later map that keeps monsters in by height (D-32) and wants proof.
   - WHO ACTS: A8.
     - In the NOTES, replace "the audit walks the party's body only" with this reasoning, and name the lowest opening on a walking line (320).
     - Add one step to `playtest_hostility.yml`: a Water Elemental 11710, spawned at the far end of a culvert, reaches melee range of the party on the cistern's walkway.

8. **Change: the grate at the stair's top asks the map's own Yes/No, "Climb up to Olympus?".**
   - WHY:
     - It is a hatch exit into a BLV (D7). D-66's rule is to ask the map's own Yes/No, as DD-08 and DD-15 do.
     - Today one click moves the party.
     - D7's way down already asks "Descend into the sewer?", and D-65 relayed "Climb up to Olympus?" to A3 as this exit's text.
   - WHO ACTS: A8.
     - Use `AskChoiceWithAnswerSteps`, with Yes moving to D7's `entrance:dd26_stair`.
     - `playtest_exit.yml` answers Yes and asserts the question's text.
     - The hover stays "Climb up to Olympus".

9. **Change: the bed needs a headboard.**
   - WHY: It carries the "Bed" hover and the find's click. At eye height it reads as a plank crate with a pale top (things1 08). This is the standard of D-66: a stand-in with a title must read right.
   - WHO ACTS: A8.
     - Add a plank headboard (about 32 thick, about 128 above the sheet) at the wall end. No new texture.
     - Do this before install, since install waits on A4's house 4815 anyway.

**SUMMARY ROW**

| D-67 | 2026-11-21 | A8's build choices DD-22, DD-26 | All DECIDE items accepted (DD-26 elemental fit by D-32's radius cap). Changed: DD-22 oculus sky `xeen_darkside_day` (post-M33); teal walls to `swll5dk`, airlock excepted (user); Yes/No buttons; couch arms. DD-26: exit grate asks Yes/No (D-66 rule); bed headboard; culvert reach playtest step. Detail: `mockups/act6_a8_followups_d67.md` | A8 |
