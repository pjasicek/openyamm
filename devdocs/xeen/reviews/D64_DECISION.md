# P2's gate (D-64)

**DECISION**
- **Accept the wind curtain** as P2's gate under D-58 C4. Do not build a door or a second room.
  - The lanes' double-door rule covers wide doors that read as double-winged. A curtain of wind is not a door, so the rule does not apply.
- **It reads as a gate: yes.**
  - The curtain stands on the Eye's floor between two of its twelve stones, at the foot of the Stair of Wind.
  - Its click is titled "A wall of wind" and gives "…throws you back."
  - On qbit 111765 it is hidden and made passable, with "The wind between the stones falls still." The same happens on load, through `evt:passed_load` (P-1).
  - Two required changes so the wind reads as wind:
    - Give the curtain's faces `flow: up`. If the flow bit does not draw on a translucent face, a static curtain is accepted, with no engine work.
    - Tune the curtain's opacity (or `tint`) in a capture, as D-51 did for `xafield`. The pale blue `xcwisp` at 0.55 may vanish against `plane_air` and the pale stair. It must read as a sheet from the test pedestal and at the gate.
  - The tour shows the gate before and after the test.
- **Missiles and sight: correct as built.**
  - Before the test, the curtain is an ordinary solid translucent face. It collides and blocks line of sight, missiles and picking, as glass does (`devdocs/INDOOR_TRANSLUCENT_FACES.md`).
  - No hostile stands behind it. The guardians and groups 9 and 10 are all on the Eye's side.
  - After the test, the curtain is untouchable and invisible.
- **P-2 holds on paper; L4 must prove it.**
  - The curtain rises 576 from the Eye's floor (256), with no gap under it. It overlaps each 640-high stone by 32 at the base and 8 at the top.
  - The cheeks stand 288 over the Eye at the foot and about 260 over the first step. They narrow to about 213 at the last step's start, which is above 192.
  - The aerie (768) is the highest floor, so no drop reaches it.
  - The planned `playtest_bypass` must also push straight into the curtain before the test: the party stays on the Eye.
  - `notes.py` reports the measured minimum lip.

**WHY**
D-58 approved P2's L1, whose `gate:sleeper` is already "a curtain of roaring wind between two stones … stilled once the test is passed", so the curtain is what C4 approved, not a deviation. The studio needs a wall for a door (P1's NOTES), and a second room's sky walls would hide the aerie, which is the plane's goal in view. Hiding a platform and making it passable on a qbit is the existing word, the same as the dais, so it needs no new engine work. The only weak point is how it looks: a static pale-blue sheet at 0.55 may not read against a blue sky. That is fixed by streaming the texture and tuning the opacity, not by changing what the gate is.

**WHO ACTS**
- **A6 (P2):**
  - `flow: up` and an opacity or tint tuned in a capture.
  - Before and after tour shots.
  - `playtest_bypass` adds the push into the curtain; `playtest_test` proves the curtain passable after the qbit and after a reload.
  - The measured minimum cheek lip in L4's NOTES.
  - One deviation line: "the gate is a curtain platform, not a door (D-64)".
- **No one else.**

**REVERSIBLE**
Yes, cheaply. It is one platform, two surface keys and the wiring already written. If a capture shows it cannot read as wind, the fallback is a field leaf in a wall, which reopens the second-room question. That fallback is not expected.

**SUMMARY ROW**
P2's gate stays a wind curtain: the approved L1 form, and it needs no wall or room. Solid translucent face blocks sight and missiles; hidden and passable on 111765. A6 adds `flow: up`, tunes opacity in a capture, and adds the curtain push to the bypass test. P-2 holds (minimum lip about 213).
