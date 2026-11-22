## DD-22 Sheltem's Pod

D6 · S · party 56 → 60 · 50–62 (band 48–65) · 20 · treasure 6 · optional lore (Act VI; ROADMAP phase 6)

![DD-22](act5_graphs/dd22.svg)

The source's Escape Pod 2 (dark maze0088, aaze0088) is the twin of Corak's pod (maze0087). It has the same plan and
no monsters, chests or stasis field. Its consoles are dead, its weapons disarmed and its two alien devices dormant.
The log computer still holds Sheltem's own account, from his break with the Ancients to the crash on Xeen.

On D6 the pod stands upright in its crater in the Ancient field (sketch (78, 38), `swll4dk` hull, round hatch at the
base facing south). Ours is therefore three decks stacked round a lift shaft, 448 apart, with the hatch on the lowest.
It is larger inside than outside, as DD-08 is: the hull is 1,280 across, each deck about 1,900. The map has 12 review
rooms, about 13 sectors, about 10 M units² and 8 doors (S: at most 15 sectors and 20 M units², 3–8 doors).

- **What it is.** The other ship's log (MAPS). Sheltem left the pod to conquer Xeen and left his guard machines in
  it (his "security systems", aaze0088:14–15). It is optional, for Act VI parties.
- **Critical path.**
  1. The airlock (`entrance:d6_hatch`, quiet), the lower ring, the lift to deck 2.
  2. The brig, the security post: "Security lockdown: bridge sealed. Release?" Yes opens the bridge's blast door,
     one way (D-43; map qbit 117761).
  3. The lift to deck 3, the blast door, the bridge: the log computer.
- **Way back.** The lift down to deck 2, then the gun deck's ladder down to the lower ring: a different way down.
- **Off the path.** The drive room (the dormant devices and the cold stasis generator, DECIDE 3). The stores, a dead
  end with a chest (T6). The gun deck (phaser and photon "Fire anyway?", "Nothing happens.", as DD-16 under D-47).
  The brig's two dark stasis cells, where Sheltem shut the Ancients' agents, one of them Corak (log XL70I), with
  the guards' locker (T6).
- **Loop (1).** Up by the lift and down by the ladder: two ways between decks 1 and 2.
- **Set piece.** The bridge in the nose: Sheltem's empty command couch under a domed viewport of dark steel ribs,
  the main and scanning consoles flickering red ("The computer seems to be malfunctioning."), and the log computer
  still paging his entries (DECIDE 4). His locker under the couch holds a T6 chest.
- **Monsters (20) and kill XP.** Patrol 50 (11610) × 14 and Annihilator 62 (11611) × 6: Alamar's machines, which
  are Sheltem's own (DD-17's rows). By deck: 7, 9, 4.
  - XP: **17.20k per member** (68,784 / 4). That is 51.3 % of the DD-22 + DD-26 row (40 at 48–65, 33.5k); half of
    the row is 16.75k, so DD-22 is +2.7 %. DD-26 (Olympus Sewer, phase 6, A8) keeps 20 monsters at about 16.3k.
  - Groups of 2–3. Quiet: the airlock (D-11.3), the middle ring, the lift shaft.
  - Rest encounters 10 % from the Patrol only (DECIDE 5).
  - D-32: nothing large is kept in by an opening (every door is 256 high or more).
- **Treasure.** Three chests T6 (S: 0–3): the stores, the brig's locker and Sheltem's locker.
- **Original lines.** "Exit Escape Pod 2?" (aaze0088:1, the exit preset's meaning, D-24); the dormant device (:0);
  Phaser and Photon Control (:2, :3); the main and scanning consoles (:5, :6); the log entries (:4, :7–17, abridged).
  No voiced line: D-38 gives Sheltem's two voiced lines to DD-17.
- **Door to D6.** D6's `door:dd22`, Escape Pod 2's hull door. Its effect is A3's `d6.sheltem_hatch` ("sealed from
  inside ... not answering the door").
  - **Inside arrival proposed:** `entrance:d6_hatch` (D-37: entered from D6), in the airlock about 192 inside the
    hatch at about (0, −832, 0) in the map's frame (lift shaft at 0, 0; the hatch in deck 1's south wall at y −1024),
    facing north (512). DD-16 also has an `entrance:d6_hatch`, but entrance names are per map, so the two do not
    clash. The brief's alternative `entrance:d6_hatch2` is not needed.
  - **Return:** the exit preset to D6's installed `entrance:dd22_hatch` (7168, 12288, 1952) facing 1536. The pod's
    centre is (78, 38) = (7168, 13312), so the point is 1,024 south of it and 384 off the 640-radius hull, facing away.
    **It matches.** D6 drops `listed_only` and names the arrival once DD-22 is built.
  - **Opening:** once `m33.done` (DECIDE 2); before that, the hook's sealed line.
- **Hooks.** `d6.sheltem_hatch` is D6's (listed for the pair). No quest hook names DD-22. Map qbits:
  - 117760: `dd22_arrived_once`.
  - 117761: `lockdown_released`.
  - The rest of 117760–117799 are free. The log's page is a map variable.
- **Textures.** A6's assignment in `dungeon_families.yml` (pods): MM6 Control Center (`sci-fi.blv`) in its **red
  accents** (`swrdk2`, `swared`, `swfloor5a`), with walls `swll4dk`/`swll5dk` matching the hull outside. Doors are
  `swdoora`/`swdoorb` (the blast door a mirrored pair), girders `swgirder`, consoles `trekscrn`/`swor2`. It reads
  apart from DD-16's green MM7 Lincoln and from DD-17's teal main set. About 18 of 30, 0 new.

**DECIDE items** (options in the graph file; the proposed default first)

1. **Count.** (a, proposed) 20 robots, Patrol × 14 and Annihilator × 6: 17.20k, +2.7 % on half the group; DD-26 keeps
   20 at about 16.3k. (b) 15 at S's floor (Patrol 10, Annihilator 5): 13.08k; DD-26 25 at about 20.4k. (c) 7, "few"
   like DD-16 (6.35k), with a NOTES line under S's floor; DD-26 33 at about 27.2k (M). Evidence: MAPS gives DD-22 no
   "few", and the source pod is empty. Depends: A2's recount and DD-26's graph.
2. **When the hatch opens.** (a, proposed) Once `m33.done`: Sheltem is beaten and his pod's lock dies with him. The
   hook moves the party in; before that, its sealed line. An Act V party cannot walk into Act VI's robots, and the log
   reads as an epitaph. (b) Always open once built. (c) Once `m35.done`. Depends: A3 (the hook), A6 (D6's door).
3. **The dormant devices.** (a, proposed) Dressing with the source's line, no reward: DD-16's device is the pods' one
   (D-47 Q18). (b) DD-16's +1 all and five years again. (c) They wake on the lockdown release: +5 to the four
   resistances, once per character. Depends: A2/A3 only under (b) or (c).
4. **The log.** (a, proposed) The log computer pages A3's abridgement in about six pages ("Entry N of 6", wraps round;
   D-47 Q19's pattern). Lore only; the last page sets an autonote "Sheltem's log". (b) The same, and the first full
   read gives 5,000 experience to every member once. (c) All twelve entries unabridged. Depends: A3.
5. **Rest encounters.** (a, proposed) 10 % from the Patrol only, at a difficulty that cannot roll the Autobot 75
   (D-47 Q21's way). (b) 0. Depends: A2's encounter row.

**Requests to other lanes**
- **A1:** nothing. Lifts, one-way levers, load events by qbit and paged texts exist.
- **A2:** the Act VI recount (DD-22 20 at 17.20k; the group with DD-26). The map card's encounter row (5). Map row
  9175 is in `maps.yml` (Act VI, party 56–60, treasure 6, music 46).
- **A3:**
  - `d6.sheltem_hatch`: `requires: {qbit: m33.done}`, an opening line that moves the party to DD-22's
    `entrance:d6_hatch`, and the present text as its fail text (2).
  - The log's six pages abridged from aaze0088:4, :7–17 as ORIGINAL_LINES rows, plus the autonote (4).
  - Map-local lines: the security console's prompt, the sealed blast door and "Nothing happens.".
- **A6:** D6's `door:dd22` names `arrival: entrance:d6_hatch` and drops `listed_only` at DD-22's install. The outside
  point matches. Confirm the red-accent Control Center assignment.
- **AU:** nothing new: shipped sci-fi hums, an alarm and a computer chirp.
- **S:** nothing new. The Patrol and Annihilator are DD-17's and D6's bound rows.

**State and next steps.** The graph, the SVG and these notes were written on 2026-11-21 (graphs only; nothing is built
or installed). The render printed no warnings, and the PNG (`output/studio_cal/a8_s11/png/dd22.png`, headless
Chrome) has been checked. Next: the decider answers the DECIDE items. DD-22 is a phase-6 map (ROADMAP §6), so its L1
follows DD-26's graph for the group split.
