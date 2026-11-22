# Act V, A8's build choices DD-15, DD-17, DD-08: decisions (D-66)

Decider D-66, 2026-11-21. Read: D-61 (`mockups/act5_a8_decisions.md`), the three L4 NOTES, D-24, D-43, D-63, D-65 (B1 and its rule), the lane rules, A8's session-12 log, the generated map Lua (`assets_dev/worlds/xeen/events/maps/xeen_dd15|dd17|dd08.lua`), `game/events/EventRuntime.cpp` `luaAskQuestion`, the source lines `dark/aaze0050`, `aaze0084` and these pictures: `a8_s12/dd15_baked_1.jpg`, `dd15_baked2_1.jpg`, `dd15/shots/baked2_rooms/01-ante_n-a.png` and `06-atrium_ne-a.png`, `a8_s12/dd08_baked.jpg`, `dd08/shots/baked_things/25-25-thrones.png`, `dd17/shots/look1_4.jpg`.

Every DECIDE item of the three maps is accepted. Changes come from four places:
- DD-15's brightness;
- DD-17's prompts, which break D-65's rule (the engine drops a question's own text after `evt.SetMessage`; this is confirmed in `luaAskQuestion`);
- DD-17's belt ride, which A1's confirmation shows does not work;
- the seats and statues that are still stand-ins (D-63 item 14's standard).

**DD-15 Great Pyramid**

1. **Accept** the green doors as a click exit that never opens, with a closed porch behind them.
   - WHY: The two mirrored `xdpyrdor` leaves meet the double-door rule. The click uses the game's leave window (D-24), as every Xeen dungeon mouth does.
2. **Accept** the talking statues as relief figures in `egywlspb` niches with step plates.
   - WHY: The figures come from MM6's own VARN kit and read as statues, so they are not a stand-in. A 3D statue from S later is optional, and the event ids stay.
3. **Accept** that the welcome statue speaks once by itself on the first arrival (117560), then on a click.
   - WHY: It is the source's greeting at the door, and it fires only once.
4. **Accept** that the sky door asks with the map's own Yes/No and then moves to D7 at once.
   - WHY: D7 is a BLV, so the game shows no leave window. Stepping out into the sky is D-24's real-choice case, like a climb.
   - It meets D-65: no hook text comes before the question, and the hook runs after Yes.
5. **Accept** 400 gold as the embalmers' find.
   - WHY: There is no "embalming salts" item, and a token purse with the jar line keeps the dead end rewarded without touching a ledger.
6. **Accept** 51 sectors and 60 of 70 textures.
   - WHY: Both are inside class L's band and cap. The graph's 58 and 40 were estimates.
7. **Accept the registry door as built.**
   - WHY: The engine drops "Registry?", but the message on screen ends on the source's own prompt, "STARFLEET REGISTRY NUMBER NCC" (aaze0084:5), so it meets D-65.
   - A8 may delete the unused "Registry?" argument at any rebuild. It is not required.
8. **Change: the brightness polish is required before DD-15 counts as done.** It does not block segment 69 (it passes), A3 or A8's next maps.
   - WHY:
     - The user flagged it. Lowering the profile at the end of a build is the precedent DD-02, DD-03 and DD-05 set.
     - The textures are not the cause: `egyflora` has a mean luma of 113, `egyflore` 132 and `egyflord` 147. It is the bake that pushes the floors and the white grout to clipping (the antechamber, the throne hall and the bedchamber use `egyflora`).
     - So the fix is the profile and no new texture.
   - WHO ACTS: A8.
     - Lower `profiles/xeen_dd15.yml` to `max_lighting` 1.0 and `direct_scale` 1.2 (leave the rest), rebake, run 4 of 4 from assets_dev, and shoot the same `baked2_rooms` tour.
     - Target: in the antechamber, throne hall, atrium and galleries, the floor patch just above the portrait frame is within about 15 % of its texture's mean luma, with no clipped patch (≥ 250) outside lamp hotspots.
     - If `egyflora` still glares at that profile, A6 re-tones a copy, `xdpyrflr` (darker and less saturated, the same pattern; DD-15 then has 2 new textures). A8 swaps it into the Pharaoh's rooms and rebakes.

**DD-17 Castle Alamar**

1. **Accept** the island as a platform in the dial hall, with the U-shaped chasms and the lift core beyond the gate in the east wall.
   - WHY: The dials, slabs and gate can still be seen from the lip, and the audit solves the gate only through the dials.
2. **Accept** that the trapdoors and falls land on the chasm floor, which leads out to the sump through the radial cut.
   - WHY: A fall still costs hit points and a climb, not progress. The island's 640 walls keep the cut from becoming a bypass.
3. **Accept** the 1.3 enlargement to reach class L (51 sectors, 131 M units²).
   - WHY: The counts, the XP and the heights are unchanged. Only the plan grows.
4. **Accept** that the hatch is live, before `m33.done` (D-61 Q14 (a)). Its prompt changes in item 6.
5. **Change: the four Heads and the true-name gate.**
   - WHY: Each event calls `evt.SetMessage`, then `evt.AskQuestion`, so the engine drops the question.
     - At the Heads the player sees only "Air power field operational." over an empty text box.
     - At the gate the player sees only "The time is right.".
   - WHO ACTS: A8, with no `SetMessage` before either prompt.
     - Each Head becomes one Yes/No prompt whose own text is `The Head speaks: "<Element> power field operational." Shut the field down?`.
     - The gate's typed prompt becomes the source line whole: "The time is right. What is Alamar's true name?" (aaze0050:19).
     - Update the playtests. A3: record the joined lines in ORIGINAL_LINES.
6. **Change: typed "Yes" becomes Yes/No buttons** on the Heads, the dais ("Before the throne. Open the Soul Box?"), the hatch ("Climb up through the hatch?") and the vault release.
   - WHY: A text box gives no hint that "Yes" is the answer. The yes/no prompts in A8's other two maps (DD-15's sky door, DD-08's roof and oath) and D-18 use `AskChoiceWithAnswerSteps`. Typed prompts stay for the real riddle (the gate).
   - WHO ACTS: A8, in `dress.py` and the playtests.
7. **Change: the belt ride is blocked on A1, and DD-17 is not done until it is fixed.**
   - WHY: A1's check 1 failed:
     - With the forward key held, which is how everyone walks, the line shows and the party walks on with no ride.
     - A short press does ride, but the party lands facing 0, not 512, and keeps drifting.
   - D-61 Q11 depended on this check. Meanwhile the belts are walkable halls, so nothing soft-locks and no map change is made.
   - WHO ACTS:
     - A1: make an in-map move from a step event happen even while movement is held, take the facing it is given, and leave the party at rest.
     - A8: add a playtest step that crosses a belt plate with forward held and asserts the landing spot and facing 512.
8. **Change: the throne and the statues must not be stand-ins at done.**
   - WHY: The throne carries a click line and is a tall girder block. The propaganda and true-name statues are MM6's white fountain `sta1a`. This is D-63 item 14's standard. The grey dial plinths are background polish.
   - WHO ACTS:
     - S: the teal statue (D-61), and name a shipped throne.
     - A8: swap them in. If MM6–8 have no throne, A8 shapes a recognisable steel throne (seat, back, arms, footstool) from shipped Ancient steel.
     - Sheltem's look is already bound (S's log, `xsor_h`). A8 removes it from "Waiting on" once it has been seen in game.

**DD-08 Northern Tower**

1. **Accept** MM7's `7dec55` armoured statue on a plinth as the founder's statue.
   - WHY: It is a shipped knight-like statue with the source's plaque line, so it is not a stand-in.
2. **Accept** stair rooms that hold both of their floors (33 rooms become 31).
   - WHY: The graph counted each split hall twice. 31 sectors and 38.4 M units² are inside class M.
3. **Accept** that the roof asks with the map's own Yes/No and then moves straight to D7.
   - WHY: D7 is a BLV with no leave window, the roof is one way, and a misclick would strand the party on the Skyroads. It meets D-65 (no text before the choice).
   - **Rule for roof and hatch exits into a BLV:** ask the map's own Yes/No, as DD-15 and DD-08 do.
   - WHO ACTS: A7 brings DD-06's and DD-07's roofs and FD-03's and FD-04's roof hatches into line at their next rebuild. It is not a reopen.
4. **Accept** that the gate never opens and its click is the exit (D-24's window). It is the same pattern as DD-15 item 1.
5. **Accept** the three hung finds as random T5 items of kind shield, helm and armour, once each (117654–117656).
   - WHY: They match the source's "Shield", "Helm" and "Armor" titles and the map's T5 chests. D-61's table already counts "3 wall finds".
6. **Accept** 36 of 45 textures, 2 new.
   - WHY: Inside class M's cap and its new-texture limit. The graph's 25 was an estimate.
7. **Change: the six thrones must read as thrones before done.**
   - WHY:
     - Each seat has its own effect and title (aaze0072:8–10), and today each is a plank block with a back.
     - The seats are the D-63 item 14 case, the same as DD-17 item 8.
     - The founder's statue, the knights and the figures are fine.
   - WHO ACTS:
     - S: name a shipped throne decoration (D-61's relay).
     - A8: swap it in. Without one, add arms and a footstool, and set the Euphoria Throne apart by its dais.
   - Note for A3 (no decision): after `q-d17.oath` the second Energy Disk lands on the cursor. Both disks are given; A3 checks whether that is intended.

**SUMMARY ROW**

| D-66 | 2026-11-21 | A8's build choices DD-15, DD-17, DD-08 | All DECIDE items accepted. Roof and hatch exits into a BLV ask the map's Yes/No (A7 aligns DD-06/07, FD-03/04). DD-15: lower bake required before done (max 1.0, direct 1.2; `xdpyrflr` only if still glaring). DD-17: Heads and gate prompts fixed per D-65; Yes/No buttons; belt blocked on A1; throne and statues before done. DD-08: thrones before done. Detail: `mockups/act5_a8_followups_d66.md` | A8, A1, A3, A6, A7, S |
