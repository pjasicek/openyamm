# D-185 to D-190: the fourth pin round's open questions (decider, 2026-11-26)

Context: [PLAYER_FEEDBACK_20261126.md](PLAYER_FEEDBACK_20261126.md) (F70–F77 and both Results sections),
[DECISIONS.md](../DECISIONS.md) (D-32, D-154, D-156, D-181), [AGENT_GUIDE.md](../AGENT_GUIDE.md) §6 (lane ownership).
The decider edited nothing but this file. Both checks were run on the installed maps (scratch cache only, through
`tools/heavy.sh 4`); the pictures were read at full size.

## D-185: two overlapping F75 gates

### What the two tools count today

| | `check_monster_fit.py` (A7's sub-agent) | `check_body_fit.py` (the engine agent) |
| --- | --- | --- |
| Run | 11 s, 69 maps: **65 stuck (errors), 56 squeeze (warnings), 3 kept, exit 1** | 6 s, 69 maps: **65 penned (warnings), exit 0** |
| Where | XD-09 62 (golem spawn markers and the Iron and Diamond Golems vs the two tumbler slots, 256 × 112); XD-02 3 (the Clan Guard, h 181, vs the three 192 × 160 bunk niches). Squeeze: DD-09 18, XD-07 16, DD-21 8, XD-03 8, XD-04 6. Kept: XD-01's counter window ×3 | XD-18 26, FD-04 26, DD-02 4, DD-03 3, XD-19 2, DD-21 1, XD-07 1, XD-12 1, XD-26 1 |
| Body | radius capped at `levelRadiusLimit` 60 for passing (as the engine does), height uncapped | the full radius (2r against the opening's width) and the full height |
| Way | follows the openings from the post, as far as the leash reaches; spawn markers by every row they roll | only the actor's own sector's openings; no leash; no spawn markers |
| Who | hostile placed actors and spawn markers, **but not hidden (staged) actors** | every placed actor, NPCs too |

The two 65s are a coincidence. `check_body_fit.py` still gives the engine agent's pre-fix count because it ignores
leashes: the 52 XD-18 and FD-04 dragons it lists are the ones the dungeon agent leashed, and none of them reaches a
low opening now.

**The XD-26 disagreement is not about the fixed opening.** `check_body_fit.py` flags actor 0, the Obsidian
Gargoyle `monster:fence_guard` (11542, r 103, h 244) in `room:fence_cache`, whose only opening is
`open:ledgee_fence`, 192 × 256 (`xd26/gen.py` line 196). The dungeon agent raised a different opening:
`open:high_hidden` behind the moss, 160 × 224 → 256 (line 207). In the game the fence guard passes its door: the
engine plans and moves an indoor body at `min(radius, 60)` (`GameplayActorService::levelCollisionRadius`, used for the
path object and the move in `IndoorWorldRuntime.cpp` ~11118/11240), so a 192-wide, 256-high door passes a 120-wide,
244-high body. `check_body_fit.py`'s width test (206 > 192) is wrong for this engine. The same false width test is
behind its DD-02 (4), DD-21, XD-19 (2) and XD-12 (Crodo, 132 vs 128) lines.

**Each tool misses something.**
- Its one real find that `check_monster_fit.py` misses is **DD-03**: Scraps (11673, h 450) and the old well's two Bone
  Dragons (11670, h 450), no leash, behind 256-high openings. `check_monster_fit.py` skips them because
  `check_arrivals.hostiles()` drops actors with the hidden attribute (0x10000), and DD-03's groups 34 and 35 are
  hidden until `m26.stage3`. Counted (the decider re-ran the check in memory with the hidden flag ignored), DD-03 gets
  **5 new `fit.stuck`** errors: Scraps at the kennel stair (256 × 256, 968 from his post) and both Bone Dragons at the
  well's 320 × 256 opening (640 and 1,048). This is the XD-07 p1 case that D-154 fixed with a leash: a staged monster
  chases like any other once it appears. No other map changes when hidden actors are counted.
- **XD-09's 62 errors are false.** Each tumbler slot joins the same two rooms as a full doorway beside it in the same
  wall: `open:tn_slot` 256 × 112 beside `open:tn_lock` 256 × 448 (lock hall ↔ north tumbler), `open:te_slot` beside
  `open:lock_te` 192 × 448 (lock hall ↔ east tumbler). Both doorways are `kind: open` links (`briefs/xd09/L4/plan.yml`)
  that every golem (h 215) passes. The planner finds the full route through the doorway, so a golem never ends up at
  the slot. A direct walk toward a target seen through the slot is tested against the body's height, and a failed one
  is suppressed (`suppressDirectPathUntilSeconds`). XD-09 needs no map change.

### DECISION

1. **`tools/xeen/check_monster_fit.py` is the gate.** `fit.stuck` is an error. A lane may not install a Xeen BLV with
   an unkept `fit.stuck` on that map: run `check_monster_fit.py --maps <stem>` (or `--mount <stage>`) before every
   install. `fit.squeeze` stays a warning, printed for the map's lane to look at.
2. **Two corrections to it first (A7):**
   - **Count hidden (staged) actors.** Every hostile placed actor counts, the hidden ones too, at its post. A hidden
     actor that never chases goes in `KEPT` with its reason.
   - **The way round.** A low opening between rooms A and B is not `fit.stuck` when the body passes another opening
     between the same two rooms that has no door leaf and lies within its reach (leash + radius + 64 of the post).
     Add a doctest-style self-test with XD-09's two slot pairs: the slot is not counted, and it is counted again when
     the doorway is taken away.
   After both corrections the world reads **XD-02 3 + DD-03 5 = 8 errors** (XD-09 0). A7 confirms this by running the
   corrected tool.
3. **`tools/xeen/check_body_fit.py` is retired** (deleted, not folded in). Its width test gives false hits for this
   engine. Its height test is what `fit.stuck` already checks, with leashes. "Penned in its room" is not a fault in
   itself: D-32 keeps big monsters in by low openings on purpose. Its one real find (DD-03) comes into the gate through
   the hidden-actor correction. The lane logs and NOTES that name it stay as history.
4. **It joins `tools/xeen/regressions.sh`** (in the map-gate loop with the other four) once the world count is 0, that
   is when A7's XD-02 niches and A8's DD-03 leashes are installed. Until then the per-map install rule above holds.
5. **The rule for "fits"** (written into the tool's docstring, which already says most of it):
   - Body: the actor's own `radius`/`height` (else the descriptor's), at its post; a spawn marker by the widest and
     tallest row it can roll. Capped radius `c = min(radius, levelRadiusLimit)` (60 in Xeen).
   - An opening **passes** the body when its width is at least `2c` and its height at least the body's height (no
     extra margin: that is the engine's test). When a lane raises an opening for a monster, it uses the next multiple
     of 32 at or above the height. Walkers use only wall openings whose foot is within a step (56) of their floor.
     Flyers also use floor and roof holes.
   - An opening narrower than `2c` is a wall to the planner and is not counted.
   - **`fit.stuck` (error):** an opening at least `2c` wide but lower than the body, whose nearest point is within
     **leash + radius + 64** of the post (2D; no leash means everywhere the body can walk or fly to; `immobile` means
     leash 0), with no way round (above). Fix it, in this order: a leash that keeps the leash circle radius + 64 clear
     (D-154, at most 1,536); a post deeper in the room; an opening the body fits; a `KEPT` line with a reason.
   - **`fit.squeeze` (warning):** a passing opening narrower than `2 × radius − 64`.
   - **Leashes are counted** (`leash_radius` of the placed actor, 2D about its post, as `keepStepOnLeash`). At the
     leash a pursuing actor stands facing its target (`tacticMoveLeavesLeash` → `AI_TacticStandFacingTarget`).

### WHY

Only `check_monster_fit.py` models what the engine does: the capped radius for passing, the uncapped height, the
route and the leash. Its two gaps (hidden actors, ways round) are cheap to close in the tool and turn 62 false errors
into 0 and 0 missed real faults into 5. Keeping both tools means two counts that disagree on every run, and a
warning list that is mostly leashed dragons and false widths nobody can act on.

### WHO ACTS

- **A7:** the two corrections in `check_monster_fit.py` and its self-test; delete `tools/xeen/check_body_fit.py`;
  XD-02's three bunk niches 160 → 192 high (the Clan Guard is 181), rebuild, install, bake, playtests; report the
  world count.
- **A8:** DD-03: leashes for Scraps and the two well Bone Dragons from `check_monster_fit.py --suggest --maps dd03`
  (after A7's fix), in DD-03's generator as D-154 did. Rebuild, bake, add a playtest step (stage 3, party beyond the
  well's opening: each dragon at least radius + 64 from it). XD-09: **nothing on the map**; withdraw the
  "leash or raise the slots" request.
- **Orchestrator:** add `check_monster_fit.py` to `regressions.sh`'s map-gate loop when the world count is 0. Relay
  D-185 to A1 (its `check_body_fit.py` log line is superseded).

### REVERSIBLE

Yes, cheap: tool-only and per-map leashes. Confidence **85 %**. Less sure: the way-round rule assumes the planner
never falls back to a partial path while a doorless way round exists. If a playtest ever shows a body pressing into a
slot that has a way round, the rule drops back to counting every low opening, and XD-09's slots get `KEPT` lines.

**SUMMARY ROW**

`| D-185 | 2026-11-26 | Two F75 gates: check_monster_fit.py vs check_body_fit.py (decider) | check_monster_fit.py is the gate: fit.stuck blocks a map's install; joins regressions.sh when the world is 0. Fits = width ≥ 2×min(r, 60) and height ≥ body height; stuck = a lower opening within leash + r + 64 with no doorless way round between the same rooms; squeeze (warning) = width < 2r − 64; leashes counted; hidden (staged) actors counted. check_body_fit.py retired (its full-radius width is wrong for the engine: XD-26's flag is the fence guard's 192 × 256 door, which it passes; the moss opening was fixed). Result: XD-09 62 → 0 (way round), DD-03 +5 (Scraps, 2 Bone Dragons), XD-02 3. 85 % | A7 (tool, XD-02 niches 192), A8 (DD-03 leashes), orchestrator (regressions.sh) |`

## D-186: FD-04's second hatchery pair at leash 32

### Premises checked

- `fd04/gen.py`: `room:hatchery` is `rect(768, -768, 1536, 960)`, 768 wide and 1,728 long. Its two openings are both
  `DRAGON_OPEN` 256 × 288: `open:hatch_nest` in the west wall at y 96–352 and `open:l2_hatch` in the north wall at
  x 1,024–1,280. The Fire and Frost Dragons are r 238, h 487 and fly (`monster_data.txt` rows 11642/11643), with
  breath missiles (Fire, Water) and spells.
- A body's middle can only stand in x 1,006–1,298, a band 292 wide. Keeping r + 64 = 302 clear of both openings
  leaves no spot in the room's north half with a leash ≥ 224 (`output/xeen_fb/p5_dungeon/f75/fd04_posts.txt`:
  "NO SPOT in its sector" for both). The posts (1,120, 250) and (1,290, 600) are 352 and 360 from the nearest
  opening, so the largest leash is 50 and 58, which rounds to 32. The room is too narrow, as the agent said.
- At the leash a pursuing dragon **stands facing the party** and fights from there (`tacticMoveLeavesLeash`). It does
  not shuffle along the leash circle. Both are ranged breathers, so standing guard costs them little.
- **No hatchery capture exists**: `output/xeen_fb/p5_dungeon/after/fd04/` holds only `01-basin.png`. The brief's
  evidence for the room's look is missing. `playtest_dragons` passes 105/105.
- Bodies collide with the level and with each other at the capped radius (60). At rest the pairs are 389–393 apart
  centre to centre (radius 238), so their drawn bodies may touch.

### DECISION

**Accept leash 32 for the second pair, with one capture check.** The room and the "four dragons" hatchery stay
(PLAN: "Four dragons; a note"). The first pair (leash 320) does the chasing in the south half. The second pair holds
the north half as guards, 350+ in from both doors, and breathes on a party that comes in from either side.
A7 takes two captures, from `open:l2_hatch` and from `open:hatch_nest`, with the dragons at their posts (alive, not
yet aggroed) and after a short fight. If two dragons' drawn bodies run through each other at rest, move group 25 (the
second pair, both rows) to the nest's free south-west quarter, with posts and leashes from
`check_monster_fit.py --suggest`. That keeps the map's dragon counts (the `COUNTS` assert) and leaves two dragons in
the hatchery. Do not widen the room or raise its openings: the tower's outline (nest west, landing north) leaves no
width, and dragon-high openings would let both rooms' dragons out onto the second landing, the party's stair. D-32
rules that out.

### WHY

The geometry rules out any leash over about 50 for a second pair in this room. A standing pair of ranged dragons at
the doors is an ordinary MM indoor guard and is not a visible fault. The real risk is crowding (four 476-wide bodies
in a 768-wide room). No capture shows it either way, so the fallback is tied to a look, not to a guess.

### WHO ACTS

**A7:** the two captures (`output/xeen_fb/p5_dungeon/after/fd04/hatchery_*.png`) and one line in FD-04's NOTES.md.
If the bodies intersect, apply the fallback (rebuild, bake, `playtest_dragons`, `check_monster_fit.py --maps fd04` 0).

### REVERSIBLE

Yes: one generator table (`PLACED`, `LEASH`). Confidence **75 %** (lower until the capture is seen).

**SUMMARY ROW**

`| D-186 | 2026-11-26 | FD-04: the hatchery's second dragon pair at leash 32 (decider) | Accept: the hatchery (768 wide, two 256 × 288 doors) has no spot for a leash ≥ 224 in its north half; at the leash a dragon stands facing the party and breathes (ranged), 350+ in from both doors. No room or opening change (D-32). A7 captures the hatchery from both doors (none exists yet); if two dragons' bodies run through each other at rest, group 25 moves to the nest's free south-west quarter with --suggest leashes (counts kept). 75 % | A7 |`

## D-187: XD-12's roof posts

### Premises checked

- Pin p4 (`briefs/xd12/L4/.oymap/pins/pictures/p4.png`): on the keep's roof, a low wall of light tan stone in a
  different texture, standing alone on the dark paving. The player calls it "a separate stone block".
- After (`p4-r1.png`, `output/xeen_fb/p5_dungeon/f76/after/xd12b/04-p4.png`, `05-skystair_down.png`,
  `06-roof_posts.png`, `07-island_view.png`): the block is gone. The gallery and the roof are open to each other. In
  its place stands one square keep-stone post (64 × 62, rise 160), in the same stone as the parapet, where the low
  gallery wall meets the roof. From the pin's pose it reads as the pier that ends that low wall. Up close (`07`) it is
  a plain buttress-like pier against the battlement. NOTES (2026-11-26, f76) say why it exists: the studio keeps 16 of
  wall between two openings at y ±1,024, and the post covers that stub. `check_clipping.py` `piece.free` 6 → 2.
- The lighter grey slabs on the far battlement in both pictures are the east battlement's two end posts. They are kept
  in `tools/xeen/check_clipping.yml` (the sky-reveal trade-off of 2026-11-25) and are not part of p4.

### DECISION

**Accept the two posts as built. Do not redraw the roof rooms.**

### WHY

The fault the player saw is gone: a free-standing slab in a foreign texture on the roof. What replaced it is a pier
in the parapet's own stone at a wall's end, a normal castle-roof shape. It closes the studio's 16-unit stub without
special cases. Redrawing roof_n, roof_s, roof_e and the sky stair as fewer rooms means a shell rework, rebuild, bake
and playtests on a map that just passed 6/6, to remove two posts nobody has objected to.

### WHO ACTS

Nobody (already installed). If a player pins the posts, A8 tries the cheap step first: lower them to the low gallery
wall's height plus one course (a newel, not a pier) before any room redraw.

### REVERSIBLE

Yes. Confidence **80 %**.

**SUMMARY ROW**

`| D-187 | 2026-11-26 | XD-12 p4: the two 64 × 62 posts on the keep roof (decider) | Accept as built: the free-standing tan slab is gone; the post is a pier in the parapet's stone where the low gallery wall meets the roof and covers the studio's 16-unit stub between the two openings. No roof-room redraw. If ever pinned: lower the posts to the gallery wall + one course first. 80 % | — |`

## D-188: Winterkill's mirror before Ghosts of Winterkill

### Premises checked

- `assets_dev/worlds/xeen/source/towns/x5.yml` house 4256, The Mirror of Winterkill: `opens: q-c6.done`,
  `closed_text: "A pale face looks back from the mirror. It is not yours."`, `mirror: {..., qbit: 119004}`. Until
  Q-C6 is done, touching it records nothing, so Winterkill appears on no mirror and on no Town Portal page. After
  Q-C6, one touch adds it (`tests/scenarios/xeen/x5_winterkill_mirror_opens.yml`).
- Q-C6 (`source/quests/q-c6.yml`, QUESTS §2.1): Mayor Randon (4502) stands on Winterkill's square by the gongs, the
  same square as the mirror (`winterkill_square`). He asks the party to drive out three waves of ghosts.
- The other closed mirrors are short atmosphere lines, and one already says who opens it: Newcastle, "Emerson will
  hang the glass when there is a keep to hang it in." Winterkill's closed houses already show ghosts.
- The player's pin (X4 p13) was at Castle Burlock's mirror, whose list cannot explain a missing town. The only place
  a hint can go is Winterkill's own mirror. A party reaches it standing a few steps from Randon.

### DECISION

**Yes, hint at the quest, plainly.** New `closed_text` for house 4256:

> A pale face looks back from the mirror. It is not yours. The dead hold Winterkill, and its glass with them. Mayor
> Randon, by the gongs, wants them driven out.

One line for every state before `q-c6.done` (no per-step variants). The first two sentences stay word for word, so the
existing test's `text_contains` still passes.

### WHY

A player who touches the mirror and gets nothing has no way to learn that a quest opens it. The program's rule is no
riddles the game does not answer. The line keeps the ghost image, says what is wrong (the ghosts) and who to see
(Randon, by the gongs, within sight). It names no reward, so nothing in it can go stale.

### WHO ACTS

**A4:** `source/towns/x5.yml` (house 4256's `closed_text`), regenerate with `gen_towns`, `towns.py` 0 errors,
`build_world.py --check` 0 differ. Extend `x5_winterkill_mirror_opens.yml` to assert "Mayor Randon, by the gongs".
The localization templates pick up the new string through the usual `tools/l10n.py` run (the zh-cn line goes fuzzy
until translated).

### REVERSIBLE

Yes, one text field. Confidence **85 %**.

**SUMMARY ROW**

`| D-188 | 2026-11-26 | X4 p13: Winterkill's mirror before Q-C6 (decider) | Hint at the quest: closed_text "A pale face looks back from the mirror. It is not yours. The dead hold Winterkill, and its glass with them. Mayor Randon, by the gongs, wants them driven out." (one line until q-c6.done; first two sentences kept so the test still matches). The mirror stays shut until Q-C6, as built. 85 % | A4 |`

## The dungeon agent's visual notes

**X9's carnival booths "well inside the plaza": no change.** `booth_shifts()` moves the Might, Speed and Endurance
booths along their facing toward the plaza's middle by 704, 496 and 800 (Accuracy unchanged). The plaza is
6,144 × 4,608 (paved at 82 %). Measured from the design's points, the booths stay roughly 1,250–1,400 from the middle
and 1,840–2,700 apart, against the design's minimum of 1,024. The middle and the walking lines stay open. The after
capture of p1 (`after/x9/01-p1.png`) shows the booth's back on the flags with a strip of plaza and the cloud rim
beyond. That is what the player asked for ("move it more right") and reads as a fairground set back from a drop.

**The 16 × 16 rail posts on X9, X8 and D7: no change.** At the party's scale 16 units is a slim timber: a bridge-head
post is normally the thickest member, and the rail is the thinner one beside it. They look heavy only in the
captures, which stand within about 100 of the posts (`after/x9/07-p7.png`, `after/x8_statue/02-garden_bridge_posts.png`,
`after/d7/01-stranded_bridge_posts.png`). At the far ends of the same pictures they read as slim posts. They also give
F70 its fix (rails no longer end in the air, `check_beam_ends.py` 76 → 0). If a player pins them as heavy, the cheap
change is 12 × 12 in the three generators' `rail_posts()`, not removing them.

## D-189: built doorways on the outdoor maps with a flat black face

### Premises checked

- The outdoor agent's Results (F71, X3 p10/p8) give a count of 12 but no list, and no check prints one. The decider
  rebuilt the list from the generators: every `kind: doorway` and every building part with `door: '7solid01'`.
  Cave mouths (shells), pits, hatches and culverts are a different kind and are left out. That gives exactly 12:

  | Map (lane) | Thing | What it is |
  | --- | --- | --- |
  | X1 (A5) | `thing:warehouse_door` | Joe's Warehouse loading door in a stone frame (`sheet_doors.jpg`, top right: a black slab in a half-timbered wall) |
  | X1 (A5) | `thing:witch_tower_door` | the Witch Tower's pointed door in the tower's grey stone (gated, m4.tower_door) |
  | X2 (A5) | `thing:den_door` | the Robbers' Den's round-arched door in the quay wall |
  | X2 (A5) | `thing:darzog_tower` | Darzog's Tower, its door in the round base |
  | X5 (A6) | `thing:xd09_door` | "the slab door in the Golem Rocks' north face; opens with the Golem Stone" |
  | X5 (A6) | `thing:darkstone` | Darkstone Tower's door |
  | D1 (A6) | `thing:dd01_outfall` | the sewer's outfall, titled "An iron grate", barred until m16.outfall |
  | D1 (A6) | `thing:dd10a_adit` | "A timbered adit" (Gemstone Mines) |
  | D2 (A6) | `thing:dd10b_adit` | the Gemstone Mines' second adit |
  | D2 (A6) | `thing:dd13_west`, `thing:dd13_east` | Graalg's two fort gates, "barred from inside" |
  | D2 (A6) | `thing:southern_tower` | the Southern Tower's door |

- F12 (`USER_FEEDBACK_20261121.md`, `check_exits.py`) is about the **inside** of a dungeon: its way out is a black
  face, as in MM7 and MM8. It does not cover outdoor façades, and nothing here changes it.
- The player has reported the X3 tomb's black door as "texture missing" twice (2026-11-23 p8, 2026-11-26 p10). The
  tomb's face was 16 behind its frame. Seen straight on, the X1 warehouse door (384 deep) reads the same way: a flat
  black rectangle in a lit wall. Five of the 12 are shut or barred in the story (witch tower, Golem slab, outfall
  grate, both fort gates). A black void contradicts their own click text ("barred from inside", "slab door").
- Not checked: no measurement of MM7/MM8 outdoor façade doors was made. From memory of the originals, built entrances
  (castles, temples, towers) show a door picture and mines and caves show darkness. The X1 generator comment says
  "as every MM7 dungeon door" without a measurement.

### DECISION

**A built door shows its kit's door picture. An opening into rock or earth stays dark.**
- **Door picture (10):** X1 warehouse and witch tower; X2 den door and Darzog's Tower; X5 Golem slab (a stone slab
  door picture; the rock face has no kit, so use the tower kit's stone door or the one XD-09 uses inside) and
  Darkstone Tower; D1 outfall (a grate or portcullis picture if a kit has one, else the iron door); D2 both fort gates
  (the kit's wing pair, a barred gate) and the Southern Tower. As X3's tomb: the leaf at most 128 behind the frame's
  face (shorten `depth` where it is 384–512), so it reads as a shut door and not as a picture at the end of a tunnel.
  The three towers take their door size from D-180/D-190 in the same rebuild.
- **Stays dark (2):** the two Gemstone Mines adits (D1 `dd10a_adit`, D2 `dd10b_adit`). Timbered mine mouths are open
  holes, like the cave mouths, and black is how MM shows a mine.
- **Rule and check** (`door_check.py`, new `doors.black_built`, an error): a `doorway` or building door with a
  `7solid01`/`solid01`/`solid10` face is an error unless the thing is an adit, cave mouth, pit, hatch or culvert (by
  kind, or a `dark: <reason>` field on the thing for a deliberate exception).

### WHY

The player's two reports show that a flat black face in a built wall reads as a missing texture, not as darkness
beyond. A shut, gated door should look shut. The tomb fix (`xvtdoor`) is the tested pattern. Mines and caves keep
the MM look, where dark means a hole you can walk into.

### WHO ACTS

**A5:** X1 (2), X2 (2); `door_check.py` `doors.black_built` with its exceptions; rebuilds, bakes, playtests.
**A6:** X5 (2), D1 (1 + the adit kept), D2 (3 + the adit kept), done in the D-180 tower rebuilds where they coincide
(Darzog's, Darkstone, Southern Tower wait on R4 for height only, not for the picture).

### REVERSIBLE

Yes: one texture field and a depth per thing. Confidence **70 %**, lower because MM7/MM8's outdoor façades were not
measured. If a measurement (`oymap things` on MM7/MM8 ODMs, the faces of entrance events) shows built entrances
mostly black, keep black on the ungated ones and give a picture only to the five shut or barred doors.

**SUMMARY ROW**

`| D-189 | 2026-11-26 | Built doorways outdoors with a flat black face (X3 p10/p8 "texture missing"; 12 sites) (decider) | A built door shows its kit's door picture, its leaf ≤ 128 behind the frame (as X3's tomb xvtdoor): X1 warehouse, witch tower; X2 den door, Darzog's Tower; X5 Golem slab, Darkstone; D1 outfall (grate/portcullis); D2 both Graalg fort gates, Southern Tower. Mine adits (D1 dd10a, D2 dd10b), cave mouths, pits, hatches, culverts stay dark. F12 (black exits inside BLVs) unchanged. door_check.py doors.black_built. 70 % | A5 (X1, X2, check), A6 (X5, D1, D2) |`

## D-190: the reading of D-180's rule (b)

### Premises checked

- D-180 (b): "temples, castles, keeps, gatehouses, guild halls, towers, or walls ≥ 640 with a front ≥ 1,024: kit
  wing pair, bay 384, height 384 (448 for walls ≥ 896 or (a)); town houses keep 128 × 256".
- `door_check.py` builds it as: big = wall ≥ `BIG_WALL` 640 **and** front ≥ `BIG_DOOR` + 128 = 512 **and** (a
  type word in the id or title **or** front ≥ `BIG_FRONT` 1,024). So the 640 also applies to the type words, and a
  front under 512 drops out of (b).
- D-180's text has no 512. The text, read literally, takes every tower whatever its size. But a 384 bay with two 64
  jambs cannot stand in a front under 512. Xeen's round towers have 10–12 facets, each about 336 at Darkstone's
  radius 544, so this matters. Rule (a) still covers each slim tower that has a dungeon behind it:
  `sub_b/d180_sites.txt` lists Darzog's, Darkstone, Ellinger's, Western, Southern and Eastern towers under
  `doors.inside_mismatch`.

### DECISION

**Confirm the reading, with one correction for slim fronts that (a) does not reach.**
1. Wall ≥ 640 applies to the whole of (b), the type words included. A temple or guild at house scale (walls under 640)
   keeps MM6–MM8's 128 × 256, as D-180's last clause means.
2. A front under 512 (the bay and its jambs) cannot take (b)'s pair, so (a) governs it. That is the sub-agent's
   reading, and it is correct.
3. **Correction:** a building that (b) would take but for a slim front, and that leads nowhere (so (a) does not apply),
   does not fall back to 128 × 256. It takes one leaf as wide as its front holds with 64 jambs, at most 384 and at
   least 192, and at least 320 high (384 on walls ≥ 896). A 1,280-high tower with a cottage door is the same complaint
   as X2 p14. `doors.small_for_building` says so for this case.
4. "Front" is the face the door is cut in (one facet of a round tower), as the tool measures it now.

### WHY

The tool's thresholds are the only buildable reading of (b): a pair that does not fit its wall is not an option,
and (a) already sizes the towers that have a dungeon behind them. Point 3 closes the one gap where the old house door
would come back on a tall tower.

### WHO ACTS

**A5:** `door_check.py` docstring (state the 512 and point 3) and the point-3 branch. **A5/A6:** no extra sites today.
Every slim tower in `d180_sites.txt` has a dungeon behind it and is sized by (a). The point-3 check guards future
towers.

### REVERSIBLE

Yes, a check rule. Confidence **85 %**.

**SUMMARY ROW**

`| D-190 | 2026-11-26 | Reading of D-180 rule (b) for low walls and slim towers (decider) | Confirmed: wall ≥ 640 applies to all of (b) (house-scale temples and guilds keep 128 × 256); a front under 512 (384 bay + 64 jambs) cannot hold the pair and falls to (a) — every slim tower in d180_sites.txt has a dungeon behind it, so (a) sizes it. Added: a slim-front big building with no dungeon behind takes one leaf 192–384 wide (what the front holds with 64 jambs), ≥ 320 high (384 on walls ≥ 896), never 128 × 256. "Front" = the face the door is cut in (a facet). 85 % | A5 (door_check.py) |`

## Summary rows (for DECISIONS.md)

| D-185 | 2026-11-26 | Two F75 gates: check_monster_fit.py vs check_body_fit.py (decider) | check_monster_fit.py is the gate: fit.stuck blocks a map's install; joins regressions.sh when the world is 0. Fits = width ≥ 2×min(r, 60) and height ≥ body height; stuck = a lower opening within leash + r + 64 with no doorless way round between the same rooms; squeeze (warning) = width < 2r − 64; leashes counted; hidden (staged) actors counted. check_body_fit.py retired (its full-radius width is wrong for the engine: XD-26's flag is the fence guard's 192 × 256 door, which it passes; the moss opening was fixed). Result: XD-09 62 → 0 (way round), DD-03 +5 (Scraps, 2 Bone Dragons), XD-02 3. 85 % | A7 (tool, XD-02 niches 192), A8 (DD-03 leashes), orchestrator (regressions.sh) |
| D-186 | 2026-11-26 | FD-04: the hatchery's second dragon pair at leash 32 (decider) | Accept: the hatchery (768 wide, two 256 × 288 doors) has no spot for a leash ≥ 224 in its north half; at the leash a dragon stands facing the party and breathes (ranged), 350+ in from both doors. No room or opening change (D-32). A7 captures the hatchery from both doors (none exists yet); if two dragons' bodies run through each other at rest, group 25 moves to the nest's free south-west quarter with --suggest leashes (counts kept). 75 % | A7 |
| D-187 | 2026-11-26 | XD-12 p4: the two 64 × 62 posts on the keep roof (decider) | Accept as built: the free-standing tan slab is gone; the post is a pier in the parapet's stone where the low gallery wall meets the roof and covers the studio's 16-unit stub between the two openings. No roof-room redraw. If ever pinned: lower the posts to the gallery wall + one course first. 80 % | — |
| D-188 | 2026-11-26 | X4 p13: Winterkill's mirror before Q-C6 (decider) | Hint at the quest: closed_text "A pale face looks back from the mirror. It is not yours. The dead hold Winterkill, and its glass with them. Mayor Randon, by the gongs, wants them driven out." (one line until q-c6.done; first two sentences kept so the test still matches). The mirror stays shut until Q-C6, as built. 85 % | A4 |
| D-189 | 2026-11-26 | Built doorways outdoors with a flat black face (X3 p10/p8 "texture missing"; 12 sites) (decider) | A built door shows its kit's door picture, its leaf ≤ 128 behind the frame (as X3's tomb xvtdoor): X1 warehouse, witch tower; X2 den door, Darzog's Tower; X5 Golem slab, Darkstone; D1 outfall (grate/portcullis); D2 both Graalg fort gates, Southern Tower. Mine adits (D1 dd10a, D2 dd10b), cave mouths, pits, hatches, culverts stay dark. F12 (black exits inside BLVs) unchanged. door_check.py doors.black_built. 70 % | A5 (X1, X2, check), A6 (X5, D1, D2) |
| D-190 | 2026-11-26 | Reading of D-180 rule (b) for low walls and slim towers (decider) | Confirmed: wall ≥ 640 applies to all of (b) (house-scale temples and guilds keep 128 × 256); a front under 512 (384 bay + 64 jambs) cannot hold the pair and falls to (a) — every slim tower in d180_sites.txt has a dungeon behind it, so (a) sizes it. Added: a slim-front big building with no dungeon behind takes one leaf 192–384 wide (what the front holds with 64 jambs), ≥ 320 high (384 on walls ≥ 896), never 128 × 256. "Front" = the face the door is cut in (a facet). 85 % | A5 (door_check.py) |
