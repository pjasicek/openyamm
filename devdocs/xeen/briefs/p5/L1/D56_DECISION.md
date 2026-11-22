# P5 Clouds of the Ancients L1: decisions (D-56)

Decider D-56, 2026-11-21. Where this file differs from `briefs/p5/L1/` (NOTES.md, plan.yml, project.yml, atmosphere.yml) or the board, this file wins. Geometry (L2) may start once A5 has applied the changes below and A2's row 9119 and A7's FD-03 roof stair have landed. L4's tests from `assets_dev` also wait on A3's lines, S's figures and A4's certificate (no stand-ins).

Checked against the source: the decoded `mazex129.evt.json` puts the Pharaoh's note at (29,7), five squares from the descent door at (29,2). It puts the eight Rest Stop signs at (3,2) to (31,26), and the shrine at (13,15). `aazex129` spells the board "Planets Edge" and the refusal "Sceptor".

---

## APPROVAL

**Approved with changes.** A5's recommendation stands on 9 of 10 questions. Q10 follows A5's (b), which differs from the option order in the brief.

1. **One ring, no monsters, falls to X5 (Q1–Q3)**, as drawn.
2. **The note moves to the start (Q4).** It stands on its post at (4096, -4224), 544 from the stair house's door, as the source has it. A3 moves `m42.pharaoh_note`'s `where`.
3. **Three peaceful, placed-only, uncounted, unkillable figures (Q5, Q6):**
   - the Dragon Pharaoh (shared with DD-15);
   - Prince Roland;
   - Queen Kalindra in her wedding look.
   - Kalindra is a **new row**, not 11918, because 11918 is the cursed vampire body in DD-14 (`xeen_sorc` skin `sorc_k`). The new row keeps npc 5001.
   - All three are made unkillable by the map's load event, `SetMm9ActorCanReceiveDamage(false)`, as Corak (D-51) and Kalindra in DD-14 (D-52).
4. **The Cube and the Scepter in the hands** are the installed ground-item models (`item_xeen_12365.glb`, `item_xeen_12366.glb`) bound again as scaled world decorations, hidden until `state:wedding`. No new model.
5. **The ending runs in this order.** The click takes the items, sets `m42.done`, gives the award and the 40,000 experience, and starts `unification`. When the cinematic ends (played or skipped), the done event shows the hook's narrative text once. When that window closes, the completion certificate follows.
   - The Pharaoh's voiced line plays once, from the cinematic's cue, not also from the click.
   - The certificate must not appear during the cinematic: A1, relay 3.
6. **The fade to white.** The fade cue gets an optional colour (A1, small and general). If A1 declines, the cinematic fades to black, and that is accepted as final, not as a stand-in.
7. **The wedding state also shows a cloud-stone disc by the pavilion (Q10).** It moves the party to `entrance:fd03_roof` and is one POI. It stands off the walking line, beside the pavilion's open south side, not in front of it.
8. **Textures (Q8).** P5 is classed **Dungeon M** (cap 45) with a named exception of **at most 13 new** textures (ROADMAP §5.2 allows 8). The exception covers:
   - the blank board;
   - ten lettered faces;
   - the REST STOP sign;
   - a pale-gold shrine stone if no shipped stone fits.

   Rules for the lettering:
   - It is set by script in a typeface with an OFL or similar free licence. No letters come from Codex.
   - No logos and no box art, only the names as text.
   - The source's spellings stay, so the board reads "Planets Edge".
   - Each face shows its name once, whole (the texture-fit rule).
   - Hover and click give the same name as the map's text.
9. **Concept corrections at L3 (the plan wins):**
   - The shrine's cloud is 512 above the start, and its underside shows.
   - The observatory stands on the road's widening, not on its own cloud. It is drawn once, with no banners.
   - The hands stand on the 64-high dais, not on tall columns.
   - The Pharaoh stands behind the dais, and the couple stand under the pavilion.
   - The causeway is cloud road with the flagstone centre line, not a paved plaza.
   - The hut is at the plan's scale.
   - Each board face may have its own ground colour, as in the walk concept.
10. **The falls are tested in the shape of D-54:**
    - from the ring, from the causeway and from the shrine;
    - each must land at `entrance:p5_fall`;
    - after 20 s on X5 every member's HP still equals its value just after the fall;
    - a healthy level-61 party survives the fall damage (D-6.2's third-of-HP rule);
    - two runs each.

---

## ANSWERS

**Q1 Walk length**
- **DECISION:** (a) One ring: 29,137 from the arrival to the dais, three Rest Stops, the observatory, no short cut.
- **WHY:** At 76 s walking or 38 s running it is long enough to feel like a pilgrimage and short enough not to drag, and the shrine is in sight all the way. A ring and a half would add a dull lap; three-quarters would lose the start at the crown.
- **WHO ACTS:** A5.
- **REVERSIBLE:** Yes, until L2.

**Q2 Monsters**
- **DECISION:** (a) None.
- **WHY:** The source has none, and FD-03's 45 monsters are the last fight. The finale must feel like an ending, not a dungeon. The note's "recast your spells" stays the Pharaoh's joke.
- **WHO ACTS:** A2 (row 9119 with no slots), A5.
- **REVERSIBLE:** Yes.

**Q3 Falls**
- **DECISION:** (a) To X5's `entrance:p5_fall` (-4608, 2304, 1500), facing the tower door (south, 1536), with falling damage, tested as in change 10.
  - A6 confirms that the point stands on flat rock top with at least 256 to every edge, and that a party there is never stuck: it can enter FD-03, which is open after M41, or step down the 700 to the ice.
- **WHY:** WORLD_DESIGN §3 makes the fall the sky maps' edge, and X8 and X9 follow it. Darkstone's door is the way back up, ten steps away. An invisible wall would make this the one sky map with walls.
- **WHO ACTS:** A6 (X5 point and keep-clear), A3 (`Xeen.skyFall` for P5), A5 (P5 rule and tests), A7 (gong floors stay raised).
- **REVERSIBLE:** Yes (one point).

**Q4 The Pharaoh's note**
- **DECISION:** (a) At the start, on a post by the stair house's door.
- **WHY:** The source has it at (29,7) before the first stop, and "It's a long road ahead" is a send-off, not a sign by the last stop.
- **WHO ACTS:** A3 (m42 `where`), A5, orchestrator (MAPS row).
- **REVERSIBLE:** Yes.

**Q5 The Pharaoh's figure**
- **DECISION:** (a) A peaceful, placed-only, unkillable, uncounted, NoArena figure behind the dais, shared with DD-15. The shrine stays the click until A1's NPC-on-placed-monster word (D-47) lands; then a click on him opens npc 5453.
  - Body: S first tries a shipped reptile-headed humanoid with a headdress attachment and the portrait's gold and blue.
  - If that does not read as the portrait (npc15453), S may spend up to 30 Meshy credits on him. He is the finale's officiant and DD-15's quest giver, so a stand-in will not do in either place.
- **WHY:** The cinematic needs an actor to turn to the couple, and a figure at the shrine for the whole walk makes the hands read as his.
- **WHO ACTS:** A2 (row), S (figure), A5 (placement), A8 (DD-15 reuses him), A1 (D-47 word).
- **REVERSIBLE:** Yes.

**Q6 Roland and Kalindra**
- **DECISION:** (a) Placed, peaceful, immobile, unkillable, uncounted. They are hidden until the cinematic's event cue shows them, and every load after `m042.done` shows them too. They have no lines until D-47's word lands; then A3 writes one short after-line each.
  - Roland: `xeen_kni` with a new skin (bright plate, royal-blue cloak, gold circlet).
  - Kalindra: a new row on `xeen_sorc` with a new skin (purple gown, silver tiara, living skin tone).
  - Both follow A4's portraits npc14405 and npc15001. No Meshy.
- **WHY:** The wedding should be standing on the cloud after the ending, not only described in a subtitle. Lines can wait for the general mechanism instead of a one-off.
- **WHO ACTS:** A2 (two rows), S (two skins), A5, A3 (lines later), A1 (show mid-visit, D-47 word).
- **REVERSIBLE:** Yes.

**Q7 Treasure**
- **DECISION:** (a) One treasure-6 chest, the wedding gift, in the pavilion. It is shown with `state:wedding` and stands against the pavilion's back, clear of the couple and the walking line.
- **WHY:** It fills MAPS's treasure 6 with one chest that has a reason. Caches at the Rest Stops would make the walk a loot run.
- **WHO ACTS:** A5, A2 (row 9119 treasure 6).
- **REVERSIBLE:** Yes.

**Q8 The ten boards**
- **DECISION:** (a) Lettered faces, under change 8's rules and the Dungeon M exception of at most 13 new textures.
- **WHY:** Reading NWC's game names as you walk past is the map's own joke, and ROADMAP §5.2 names signs as a reason for new textures. The world goes from about 156 to at most 169 of 450.
- **WHO ACTS:** A5 (lettering script), A6 (registration), A1 (`texture_budget.py` class and exception).
- **REVERSIBLE:** Yes. Falling back to the blank board drops 10 textures.

**Q9 Sky**
- **DECISION:** (a) `xeencloud` with X9's daylight block, no weather, `view_distance_scale` 1.5.
- **WHY:** This is the lanes' rule for sky maps. The ending's change of mood belongs to the cinematic's fade, not to a preset nobody sees again.
- **WHO ACTS:** A5.
- **REVERSIBLE:** Yes (one line).

**Q10 Way out after the ending**
- **DECISION:** (b) The stair house both ways (the `exit` preset, meaning "Descend into Darkstone Tower?"), plus the disc after `m42.done`, which moves the party to `entrance:fd03_roof` with A3's line. Town Portal and Lloyd's Beacon stay allowed on P5; only Fly is off.
- **WHY:** After the ending the party should not have to walk 29,000 back. The source's way down stays the map's only exit, and the move stays inside the map, so no new travel link is made.
- **WHO ACTS:** A5 (disc, event), A3 (line, check that nothing blocks the spells).
- **REVERSIBLE:** Yes.

---

## ROWS AND NUMBERS

| Item | Value |
| --- | --- |
| Map row | 9119 `xeen_p5.blv`: encounter 0, treasure 6, lock 0, trap 0, perception 0, refill 672, music 15, plains. No slots, no bolster. |
| Monsters | 0 hostile. 3 peaceful placed-only, uncounted (Pharaoh, Roland, Kalindra), hidden until the wedding except the Pharaoh. |
| Kill XP | 0 |
| Quest XP | 40,000 per member (m42), unchanged; A2 confirms it is in Act VI's ledger. |
| POIs | 19: 10 boards, 3 Rest Stops, the note, the way down, the observatory door, the shrine, the gift, the disc. |
| Chests | 1 at treasure 6 (after `m42.done`) |
| Textures | Dungeon M (cap 45); about 31 distinct; at most 13 new (exception, D-56). World about 156 → at most 169 of 450. |
| Walk | 29,137 arrival to dais; shrine sky gap at least 1,155; crown to last stop 1,445 across and 448 up (no short cut). |

**MAPS (orchestrator), P5 row:**
- Content becomes: "The finale: one ring of cloud road (29,137 to the shrine) past three Rest Stop huts, ten billboards naming New World Computing's games and the closed observatory; the Pharaoh's 'long road' note at the start by the stair house; the Pharaoh's shrine; after the ceremony the wedding pavilion (Roland, Kalindra, a treasure-6 gift, a disc back to the crown) (D-56)".
- Monsters stay "none".
- Size stays "small".
- Notes: "Open-air BLV; ending cinematic `unification` (`evt.PlayCinematic`), then the completion certificate; falls to X5's `entrance:p5_fall`".

---

## RELAYS

- **A1:**
  1. Confirm that a cinematic `event` cue can show, mid-visit on an open-air BLV, hidden faces (`evt.SetFacetBit`), hidden placed actors, decorations and a chest. X9's castle-gone only runs on load.
  2. Add an optional colour to the `fade` cue (default black), a small general change.
  3. Make sure a completion recorded during a cinematic waits for its end, and for an open message window, before `WinGameScreen` shows. Small and general if it does not already.
  4. The NPC-on-placed-monster word (D-47) now also covers the Pharaoh, Roland and Kalindra.
  5. `texture_budget.py`: P5 is Dungeon M with D-56's exception of 13 new.
- **A2:**
  - Row 9119 as in ROWS.
  - Three peaceful rows, placed-only, `move: stand`, uncounted, NoArena:
    - the Dragon Pharaoh (npc 5453, shared with DD-15);
    - Prince Roland;
    - Queen Kalindra, wedding (npc 5001, separate from 11918).
  - Confirm M42's 40,000 in Act VI's ledger.
- **A3:**
  - `m42.pharaoh_note` `where`: the post by the stair house's door at the start.
  - aazex129:0–10 as the map's text for the Rest Stop signs and the ten boards, in source spelling ("Planets Edge").
  - ORIGINAL_LINES rows for aazex129:0–11 and :14 (:14 as the `exit` window's meaning).
  - `m42.shrine` true calls `evt.PlayCinematic("unification", <done event>)`. The done event shows the hook text once; the certificate follows. The voice plays only from the cinematic cue.
  - `Xeen.skyFall` for P5 to X5's `entrance:p5_fall`.
  - The disc's line.
  - Check that Town Portal and Lloyd's Beacon work on P5.
  - Roland and Kalindra after-lines only when D-47's word lands.
- **A4:** The completion certificate in `world.yml` `completion` on `m42.done` (111840), following `level_generation/ui/certificates_20261031/README.md`: the original World of Xeen ending art restored at x2 if the source has one, otherwise a new painting in the originals' layout; headline and ending text.
- **A5:**
  - Apply changes 1–10 and the answers.
  - L2 after row 9119 and A7's stair.
  - At L4:
    - `xeen_p5.cinematics.yml` `unification`, every gameplay step an `event` cue;
    - the wedding load event on `m42.done`;
    - the disc.
  - Playtests from `assets_dev`, two runs each:
    - the walk;
    - the shrine refusal without the items;
    - the shrine with the items, played out;
    - the shrine with the items, skipped;
    - a reload after the ending (state shown, certificate once);
    - the disc;
    - three falls in D-54's shape;
    - `playtest_hostility.yml`.
- **A6:**
  - X5:
    - `entrance:p5_fall` (-4608, 2304, 1500), facing 1536, with a keep-clear;
    - confirm 256 of flat rock round it and a way off the rock (FD-03's door or the drop to the ice).
  - Textures:
    - reuse X8's `xccloud`/`xccloudsd`, X9's cloud-stone and X5's `gtrlwal1`, `hkm3b`, `xtslate`, `7solid01`;
    - shipped hut, observatory and pavilion textures first;
    - register the new ones (board, ten faces, REST STOP, pale-gold stone if needed) in `source/textures.yml`.
  - No finale sky preset.
- **A7:**
  - FD-03's roof stair: its top is `entrance:p5_stair`, facing down the stair.
  - The seal's way up leads to P5's `entrance:fd03_roof` (4608, -3968, 0), facing 512.
  - The gong floors stay raised once rung.
  - The stair house copies X5's crown; no change is needed.
- **A8:** If DD-15 places the Dragon Pharaoh as an actor, it uses the same row and model. Also send S DD-15's needs (a pose, a book) so one figure serves both maps.
- **S:**
  - The Pharaoh figure: a shipped body plus headdress first, Meshy up to 30 credits only if that does not read; held book.
  - Roland's skin on `xeen_kni` and Kalindra's wedding skin on `xeen_sorc`; no Meshy.
  - The shrine's stone hands: one hand mirrored, as the Xeen feet were; Meshy up to 30 credits only if a built mesh will not do.
  - The Cube and the Scepter as scaled decorations from the item GLBs.
  - A cake on a table, and a Rest Stop bench (shipped first).
- **AU:**
  - X8's wind bed (`pan: false`).
  - Four far chimes (the sleepers) and a short wedding fanfare, CC0 or our own.
  - The Pharaoh's line is D-38's `xeen_vo_pharaoh_unification`.
  - Music 15.
- **Orchestrator:**
  - Add `xeen_p5.blv` to `world.yml` `openAirMaps` when it installs.
  - The MAPS P5 row above.
  - The DECISIONS row.
  - Close A5's DECIDE items.

---

## SUMMARY ROW

| D-56 | 2026-11-21 | P5 Clouds of the Ancients L1 | Approved with changes; A5's default on all ten. One ring (29,137), no monsters, falls to X5's `entrance:p5_fall` (tested as D-54). The Pharaoh's note at the start (source). The Pharaoh is a peaceful placed figure shared with DD-15 (Meshy up to 30 credits only if a shipped body will not read). Roland and a new wedding Kalindra row stay hidden until the cinematic's event cue. One treasure-6 gift; lettered boards (Dungeon M, at most 13 new textures); `xeencloud`; stair house plus a disc to the crown after `m42.done`. Order: click, cinematic, text, certificate. A1: show mid-visit, fade colour, certificate waits. Detail: `briefs/p5/L1/D56_DECISION.md` | A1, A2, A3, A4, A5, A6, A7, A8, S, AU, orchestrator |
