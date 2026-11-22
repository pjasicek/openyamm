# Phase 6, A7's build choices: decisions (D-63)

Decider D-63, 2026-11-21. Read: D-57 (`mockups/act6_a7_decisions.md`), the four L4 NOTES, A7's State, D-11.3, D-24, D-32, D-43, D-51, the lane rules, the source text `reference/mm4_5_world_of_xeen/unpacked/text/dark/aazex113–116.txt.json`, and these tour pictures: `fd02/shots2_sheet.jpg`, `fd03/shots3/01-seal-3m-030b.png` and `fd04/sheet1.jpg`.

Eleven choices are accepted as built: 1–3, 5–8 and 10–12. Choices 4 and 9 are changed. In 13 the dust is accepted but the throw is changed. In 14 the blades and the chair must be fixed before FD-02 is done, and the lecterns can wait.

**FD-02 Southern Sphinx**

1. **Accept** the pair of leaves (`egydrsml`/`egydrsmr`) at the foot of the breast steps.
   - WHY: Without them, eight Ghost Mummies reached the party and cut the knight from 335 to 113 HP. With them, the party stands 10 s unharmed. D-57 made FD-03's east way a door for the same reason. 6 doors is inside S's 3–8, and a matched wing pair meets the double-door rule.

2. **Accept** that the paid clue is offered on the mask's next click.
   - WHY: Asking the question right after payment replaced A3's payment line. The 500 price and the wording stay as D-57 Q9 set them.

3. **Accept** the crypt stair as a gallery inside the 288 arch plus a 32-step flight inside the crypt.
   - WHY: It saves a room (13 rooms against S's 15) and keeps D-57's 288 arch. `playtest_crypt` passes 4/4 with the Dragon Mummies kept in.

**XD-18 Dragon Cave**

4. **Change.** The tax throw uses `leave`, which moves the party at once, not the `exit` window. It lands on X7's `entrance:xd18_mouth` as it does today.
   - WHY: The click has already decided the outcome, and A3's fail line already says "you are outside on the mountain". If the window is cancelled, the party stays in the hall against that line, which is the fault D-24 fixed in XD-07. D-57 Q2's own WHY calls this "a throw (D-24)". Its `{exit: x7}` was shorthand.
   - WHO ACTS:
     - A7: change the one word in `gen.py`. In `playtest_tax`, the party lands with no window and the cancelled branch is dropped. Rebuild, reinstall, then 4/4 from `assets_dev`.
     - A3: change the hook's `where` text in `q-c25.inner_door` from `{exit: x7}` to `leave` (text only).

5. **Accept** that the graph's ledge pair stands in the bone hall by the dragon road.
   - WHY: A dragon of radius 238 cannot stand on a 384 ledge behind a 128 lip. The pair still guards the road onto the ledge, and the count does not change.

6. **Accept** the King's door at 384 wide and 288 high.
   - WHY: Under D-32 the 288 height keeps 487-tall dragons in, and width plays no part. 384 matches the cave's other pairs, and the wing pictures fit without the squash warning (texture-fit and double-door rules).

**FD-03 Darkstone Tower**

7. **Accept** L3's riser plus slab.
   - WHY: It shows D-57's states. After one gong the ground stands at half height (448). After both it is flush (768). `playtest_fall` walked both cases 4/4, and the one-second timer lag is acceptable.

8. **Accept** the roof stair's head as a platform in `room:roof_stair`.
   - WHY: `entrance:p5_stair` still stands on the top under the hatch, facing down the stair (D-56). A separate room would add a sector for nothing.

9. **Change.** All sixteen rows must be verbatim from `dark/aazex113–116:3–6`, not derived.
   - WHY: The NOTES say only one row was available, but the reference holds all sixteen, and eight of the built rows are wrong:
     - Four plaque rows drop the source's trailing `-`: L2's 3rd and 4th, L3's 3rd and 4th.
     - All four heads differ. For example, the source has `T-MEOE-FENN-TEAO` and the build has `T-MEOE-FENN-TSYO`. The derivation also inserted a `.` and wraps each row in extra quotes.
     - Read down, the source gives exactly the four messages ("…OF THE DUNGEON OF DEATH SEE YA SOON!"). A3's summaries keep D-57's wording.
   - WHO ACTS: A7. Copy the rows into `gen.py` as text, keep the source's form ("Head 13 speaks: …" without added quotes), rebuild, reinstall, then 16/16 from `assets_dev`.

10. **Accept** the seal `xdseal` at 0.3 with the re-toned texture. No further raise.
    - WHY: 0.3 is the most D-57 allowed. The source calls it an invisible seal. The faint veil seen from 3 m plus the touch line is the tell D-51 asks for.

**FD-04 Dragon Tower and the Dungeon of Death**

11. **Accept** the three walked ramps.
    - WHY: They are 288 high, so they are dragon-proof (D-32). In the tour they read as a stair winding in the wall, and `playtest_dragons` passes 4/4.

12. **Accept** the crossword clues as clicked wall plaques at each word's row or column.
    - WHY: Walking the hall never brings up a question, which is how MM6–8 present clues on walls. Reusing FD-03's `xdplaque` costs no new texture.

13. **Accept** the dust as a camera shake and a stone sound. **Change** the throw that follows to `leave`, not the `exit` window.
    - WHY: The party already answered the shrine's question with its tell. A second "leave?" window after the ceiling falls is D-24's fault again, the same as item 4. A short dust puff with merge point 25's `smoke` word is optional polish.
    - WHO ACTS:
      - A7: change `{exit: exit:x7_gate}` to `leave` in `gen.py`, drop the window step from `playtest_shrine`, reinstall, then 4/4.
      - A3: change the hook's wording if it names `exit`.

**FD-02 polish**

14. **Split.** The blades and the chair are required before FD-02 counts as done. The lecterns are polish for later.
    - WHY:
      - The blades are the death runs' tell (D-57 Q9). In the tour they read as two teal slabs, not as blades.
      - The chair carries the "Throne of Legends" hover. D-57 Q12 asked S for a shipped chair or throne decoration, so two blocks are a stand-in, which the lane rules do not allow in done work.
      - The lecterns are background dressing.
    - WHO ACTS:
      - A7: make each blade thin (32 thick or less) with a grey steel texture already shipped in MM6–8 that reads as metal under the bake (no new texture). Check it in a baked shot from a run's mouth and re-bake. Place S's chair.
      - S: name the shipped chair or throne decoration. If MM6–8 have none, A7 shapes a recognisable throne (seat, back, arms, footstool) from wood-textured blocks.
      - A7 and S, polish list: replace the lecterns with a shipped decoration when one is found.

**SUMMARY ROW**

| D-63 | 2026-11-21 | A7's Act VI build choices (FD-02, XD-18, FD-03, FD-04) | 11 of 14 accepted. Changed: XD-18's tax throw and FD-04's Ultimate shrine throw use `leave` (immediate, D-24), not the `exit` window; FD-03's sixteen plaque and head rows copied verbatim from `dark/aazex113–116:3–6` (eight derived rows were wrong). FD-02: blades must read as steel and the chair as a chair before done; lecterns are polish. Detail: `mockups/act6_a7_followups_d63.md` | A7, A3 (hook wording), S (chair) |
