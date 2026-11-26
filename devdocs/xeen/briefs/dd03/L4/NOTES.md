# DD-03 Castle Kalindra, staged (L4): notes

Lane A8 (agent `agent:xeen-a8-dd03`), phase 3, 2026-11-20. Built from the MU-6 graph
(`devdocs/xeen/mockups/act3_graphs/dd03.graph.yml`) with decider D-26 (`mockups/act3_a8_decisions_a.md`), which wins
where they differ, D-30 (the outside's parts by stage, A6) and D-32 (low openings). One script,
`output/studio_cal/dd03/tools/gen.py`, writes all four levels (L1-L4) and `atmosphere.yml`; the playtests and this file
are written by hand. `output/studio_cal/dd03/cycle.sh` generates L4 (`LEVELS="L1 L2 L3 L4"` for all), formats,
validates, builds, installs into the scratch root `output/studio_cal/dd03/root` and audits. The map's top-level notes
(the stage map for A6) are `devdocs/xeen/briefs/dd03/NOTES.md`.

## What was built

Map 9152, `xeen_dd03.blv`, class M staged, on D1 Castleview Vale. Story M19 (the throne room's safes), M24 (the disk
safes), M26 (the mirror switch), M27 (the crown safe), T2-A (the liches); A4's houses 4501-4512. Party 30-40, levels
26-45 (Scraps 70 optional), 54 monsters, treasure 4 (the kennel's hoard 5), music 29. Acts III (stages 1-2) and IV
(stages 3-4).

34 rooms on four floors: the dungeon at -640 (Scraps' kennel -1152), the ground floor 0, the second floor 640, the
third floor 1280. Frame x east, y north; the gate in the west. Every room's ceiling stays at least 64 under any room
above it. **52.8 M units²** of floor (`oymap metrics`), 34 sectors.

| Floor (stage) | Rooms (texture family) | Monsters |
| --- | --- | --- |
| 0 (stage 1) | Gate passage (arrival, exit, portcullis, crest; ashlar), entrance hall (banners), throne room (the Empty Throne on its dais, two safes behind tapestries, pillars), coat closet (illusory back wall), Cloud Stairs' foot (royal marble); North Wing, banquet hall, kitchen (Carl), South Wing, armory (tougher safe) (7d33 cobble, shimmer patches) | NW 4 Tomb Guard, banquet 4 Tomb Guard, SW 4 Ghost Rider |
| 0 (stage 4) | Stable yard, **open to the sky** (ashlar, windows, crest; stables 4510, the mirror 4512, a trough) | — |
| 640 (stage 2) | Cloud Stairs' head, upper stair foot, Captain's corridor (4502-4504), Sleeping Chambers (beds), vaults (disk safes) (royal marble); phase gallery (cobble, shimmering walls) | sleeping 4 Ghost Rider + 2 Tomb Terror; gallery 4 Tomb Guard + 2 Tomb Terror |
| 1280 (stage 4) | Third-floor landing, the Queen's gallery (tapestries, banners), Royal Bed Chamber (bed, two brews, mirror and crown safe, mirror switch), the Queen's court (4506-4509, 4511) (royal marble); bell tower (ashlar, beams); shimmering attic (cobble, rafters) | gallery 4 Vampire + 2 Tomb Terror; bell tower 4 Vampire + 4 Gnome Vampire; attic 3 Tomb Terror |
| -640 (stage 3) | Guardroom (ledger), cell block (five bays), Maximum Security (Guido 4505, the lever, three notes), dungeon vault (tougher safe, secret door), old well (7d33 dark cobble); kennel stair and Scraps' kennel at -1152 | cells 5 Lich (named); maxsec 4 Tomb Terror; guardroom 2 Tomb Terror; well 2 Bone Dragon (named); kennel Scraps |

The stairs are rooms of their own (flights of 20 steps, 1,024 long): the Cloud Stairs (0 to 640), the upper stair (640
to 1280), the dungeon stair (0 to -640) and the kennel's low stair (-640 to -1152, 16 steps, 288 clear).

**Critical path** (the graph's): gate, entrance, throne room (safes), north wing, Cloud Stairs, second floor, Captain's
corridor, Sleeping Chambers, phase gallery, vaults. **Loops**: round the banquet hall by the servants' passage; through
the coat closet's illusion (throne, closet, armory, South Wing); the top floor by the roof walk (bell tower, attic,
court, gallery); the dungeon by the vault's secret door (guardroom, cells, Maximum Security, vault, well).

**Counts:** 34 sectors (20-45), 52.8 M units² (30-90), 54 monsters + Scraps (45-75), 5 chests (3-7), 16 doors (6-16):
four phase leaves (Cloud Stairs, dungeon stair, upper stair, the yard's wall), the gate's portcullis, the kennel's
portcullis, seven double doors (throne room, banquet hall, closet, armory, Sleeping Chambers, bedchamber; the vault's
iron pair), the illusory wall, the vault's secret door. The audit counts 22 "doors": the five second leaves of the
doubles and the two switches. No spawn points.

## Stages (D-26, D-18's pattern)

Built with every stage gate shut and the stage-2 to stage-4 monsters placed **hidden** in their own groups. Load events
on A3's qbits (`Xeen.Stages.kalindra`):

| Stage | Qbit | Load event | Groups shown |
| --- | --- | --- | --- |
| 1 | m19.stage1 111381 | the gate's portcullis up; the closet's illusion made passable | (stage 1's 1-3 are not hidden: D1's gate refuses before stage 1) |
| 2 | m19.stage2 111382 | the Cloud Stairs' leaf open | 21 sleeping, 22 phase gallery |
| 3 | m26.stage3 111521 | the dungeon stair's leaf open | 31 liches, 32 Maximum Security, 33 guardroom, 34 the well's dragons, 35 Scraps |
| 4 | m26.stage4 111522 | the upper stair's leaf and the yard's phase wall open | 41 the Queen's gallery, 42 bell tower, 43 attic |

Every stage gate is a door leaf of A6's `xkshimmer` (slide-up, shared with D1's ghost castle), so it blocks monsters too.
Before its stage a step plate in front of each stair's leaf shows the source's mist line ("Your foot passes through the
stairs as though they were mist. This level is out of phase and inaccessible.", aaze0041:10), and a click on the leaf
the same (the dungeon stair: "The dungeon stair ends in shimmering nothing."; the yard: "The wall shimmers like heat
over a road. Beyond it horses stamp, and you cannot reach them."). The stair itself stays closed.

Patches of `xkshimmer` on the wings' walls (North Wing, South Wing, phase gallery) show parts still out of phase.

## Mechanisms and hooks

- **Arrival:** a one-shot timer when stage 1 is set and `arrived_once` (117320) is not: A3's `m19.first_entry`. Every
  entry: the status line "Castle Kalindra.".
- **The throne room's safes** (`m19.safes`, D-26: trapped chests any party opens, trap 4): the first use of either safe
  runs the hook (its text, `safes_opened` 111383) and the map gives the two Energy Disks (12334, `map_gives`); from the
  next use it opens as a chest. `AddValue(InventoryItem)` puts a disk on the cursor (the game's usual give).
- **The disk safes** (`m24.disk_safes`, the vaults' iron door): before Dimitri's `m24.done` (111481) the hook's fail
  text; after it a combination prompt ("A combination safe. Six dials."); 64-52-31 or 645231 runs the hook and the map
  gives four disks; a wrong answer: "The dials click round and the safe stays shut."; afterwards the hook's else text.
- **The crown safe** (`m27.crown_safe`, behind the Queen's mirror): before `m26.stage4` and `queen_found` (111543) the
  fail text; then 3-31-62 or 33162 gives the crown (12374, A3's hook). The mirror is a framed glass panel.
- **Activate Mirror Portals?** (aaze0043:16, a button by the bed): Yes runs `m26.mirror_switch`.
- **The tougher safes** (armory, dungeon vault; D-26): a prompt "A safe with three dials."; 10-11-12 or 101112 opens the
  chest for good (a map variable each); a wrong answer: "A tougher safe than the others. Three dials." (the armory's
  fail text, used on both). Guido's greeting gives the numbers (A4). No trap on these two: a trapped chest that goes off
  ends the event script before its variable is set (found in testing), so the combination would be asked again.
- **The brews** (two barrels in the bedchamber, aaze0043:5-8): Queen's Brew +2 base Personality, Knight's Brew +2 base
  Might, once per character (player bits **11320**, **11321**, provisional), the clicking member; again "… You have
  had your fill."
- **The prisoner ledger** (the guardroom's desk): `t2-a.cells` (A3's list, the source's aaze0044:8 with the two added
  liches and the dragons).
- **The liches** (group 31, named Vexor the Black, Clemon the Dead, Saxar the Permanent, Morgrath the Grey, Ulvane the
  Unrepentant): a 2-half-minute timer runs `t2-a.liches` (114521) when the group is dead. Played: the qbit is set; its
  window did not show as an open dialog in the headless run (the playtest checks the qbit).
- **The two Bone Dragons** in the old well carry the names Iron Vithnipravad and Argonax.
- **Scraps** (11673, optional): behind the kennel's portcullis (door 11), worked by the lever (event 33, toggles) under
  three notes "A note reads: Beware of Scraps!" / "Don't feed Scraps." / "Don't let Scraps out!" (aaze0044:49-51). The
  portcullis is 256 wide and 288 high, the stair below it 320 wide with 288 clear over every step, its mouth 256 high
  (D-32). The castle's hoard (treasure 5) lies in the kennel.
- **The coat closet's illusion:** the closet's back wall is a door leaf of the wall's cobble (its doorway lined in the
  same cobble, no frame) made passable by the stage-1 load event: the party walks through it into the armory. Carl the
  Mason's greeting is the answer ("If you ever come to a dead end in the castle, just keep walking.").
- **Carl the Mason** (NPC 5014, D-26): stands at his bench in the kitchen (the engine's peaceful Peasant 364, group 50,
  immobile); the bench speaks for him (`evt.SpeakNPC(5014)`, Words needed).
- **The houses** (A4's `source/towns/dd03.yml`): each door runs `evt.EnterHouse(<id>)` from its stage, A4's closed text
  before. The Empty Throne 4501 is the throne block (A4's `thing:kalindra_throne`, here `platform:kalindra_throne`);
  4502-4504 on the Captain's corridor, 4505 Guido's cell (iron door) in Maximum Security, 4506-4509 and 4511 round the
  Queen's court (4507 the treasury an iron door), Stables 4510 in the yard. The oak house doors are whole pictures: the
  left wing `chb1dl` carries A4's door id, the right wing `chb1dr` a `panel:<id>_r` with the same event. The mirror 4512
  is a framed glass panel on the yard's south wall (`panel:kalindra_mirror`), `Xeen.useMirror(4512, ...)`.
- **The exit:** `exit:d1_gate`, the gate face on the gate passage's west wall (`hclgdr`, a double gate drawn whole),
  the `exit` preset ("Exit Castle Kalindra", D-24), live to A6's return point on D1.

## Monsters and kill experience

All placed, on the world's rows (D-26), groups by room:

| Row | Id | Level | Count | Stage (rooms) | XP each |
| --- | --- | --- | --- | --- | --- |
| Tomb Guard | 11261 | 26 | 12 | 1: NW 4, banquet 4; 2: phase gallery 4 | 936 |
| Ghost Rider | 11263 | 27 | 8 | 1: SW 4; 2: sleeping 4 | 999 |
| Tomb Terror | 11262 | 40 | 15 | 2: sleeping 2, gallery 2; 3: maxsec 4, guardroom 2; 4: Queen's gallery 2, attic 3 | 2,000 |
| Lich | 11280 | 35 | 5 | 3: cells (named) | 1,575 |
| Bone Dragon | 11670 | 45 | 2 | 3: well (named) | 2,475 |
| Vampire | 11291 | 40 | 8 | 4: Queen's gallery 4, bell tower 4 | 2,000 |
| Gnome Vampire | 11290 | 32 | 4 | 4: bell tower | 1,344 |
| Scraps | 11673 | 70 | 1 (optional) | 3: kennel | 5,600 |

Kill XP: 83,425 = **20.86k per member** of four (MAPS 20.9k): Act III (stages 1-2, 24 monsters) 27,224 = 6.81k; Act IV
(stages 3-4, 30 monsters) 56,201 = 14.05k; Scraps 1.4k in Act IV (D-1.2).

The map card's slots (A2's row; encounter chance 0, all placed):

- `Xeen Spirit`: tier b, 2-3, weight 40;
- `Xeen Lich`: tier a, 1-2, weight 25;
- `Xeen Vampire`: tier b, 2-3, weight 35.

The scratch root carries a test row 9152 in this form (copied from 9151's columns: treasure 4, music 29).

**Measured heights for A2's Act IV region:** stage 3's monsters stand on the dungeon floor **z -640** (the dungeon's rooms
span z -640 to -128, the old well's shaft to 384), Scraps at **z -1152** (the kennel, -1152 to -128); stage 4's on the
third floor **z 1280** (rooms 1280 to 2304). Stage 2's Tomb Terrors (Act III) stand at z 640, stage 1's at z 0. So: a
monster of the map at z < -100 or z > 1200 is Act IV.

## Qbits, player bits, items

| Name | Number | Use |
| --- | --- | --- |
| `arrived_once` | 117320 | the map's own (provisional block 117320-117359); the only map qbit used |
| `m19.stage1` / `m19.stage2` | 111381 / 111382 | read: stages 1, 2 |
| `m26.stage3` / `m26.stage4` | 111521 / 111522 | read: stages 3, 4 |
| `m19.safes_opened` | 111383 | read (the safes' chest state); set by A3's hook |
| `m24.safes_opened` | 111483 | read (the disk safes' prompt); set by the hook |
| `m27.crown` | 111541 | read (the crown safe's prompt); set by the hook |
| `m24.done`, `m27.queen_found` | 111481, 111543 | read only through the hooks' `requires` |
| `t2-a.liches_slain` | 114521 | set by the hook at the liches' death |
| player bit | **11320** | the Queen's Brew (+2 Personality), provisional |
| player bit | **11321** | the Knight's Brew (+2 Might), provisional |

Map variables: `armory_safe`, `vault_safe`, the studio's `once.*`. Items: Energy Disk 12334 (the map's gives), the crown
12374 (A3's hook).

## Exit and arrival

`exit:d1_gate` leads to **D1 at (-9728, -3072, 1664) facing west** (game 1024, studio 180), A6's return point for event
123; **measured** with `playtest_exit.yml`: the party stands at (-9728, -3072, **1665**) and walks off west.

**D1's gate into this map** (A6's `entrance:dd03_gate`, event 123): the start point is **(-1600, 0, 0), facing east**
(studio 0, game 0), inside the gate. D1's gate refuses before `m19.stage1` (`m19.ghost_castle`).

## Textures (43 distinct, 0 new; cap 45, ≤ 8 new)

- Royal kit restored (MM7 7d09 marble): t3s2b1, t3s2b (the knotwork dado as a band), t3s2fl1, tfb09, t3s2c, 7tws1fa,
  t5d1 (iron doors: vault pair, Guido, treasury, disk safe), t3elr (pillars, throne, reveals); tapestries tap1, tap4,
  tap7.
- Kalindra's own (A6, installed): xkkalcrst, xkkalban, xkportc, xkarrow, **xkshimmer** (every phase leaf and patch).
- Castle Ironfist (gate, yard, bell tower): hcwall, hcwindo, cstyl; the exit's gate picture hclgdr.
- MM7 Castle Gryphonheart 7d33 (wings, attic, dungeon): chb1, dchb1, 7tfb1, tfb2, 7tfb11, 7trimd (planks, beams,
  frames), the oak door pair chb1dl/chb1dr (always both wings together).
- Furniture and the rest: sign128 (signs and notes), glass2 (the two mirrors, framed in 7trimd), deskside, desktop,
  7t1beds; the ch4 chest family; the lever and button pictures.
- `python3 tools/xeen/texture_budget.py --root output/studio_cal/dd03/root`: **DD-03 M 43/45, 0/8 new**. Nothing waits on
  A6.

## Original lines

- "Exit Castle Kalindra?" (dark/aaze0041:0): the exit's title.
- "Your foot passes through the stairs as though they were mist. This level is out of phase and inaccessible."
  (aaze0041:10): the stairs' plates and leaves.
- Signs (aaze0041:1-9, aaze0042:2, :31, aaze0043:0, aaze0044:0): Throne Room, North Wing, Banquet Hall, Cloud Stairs,
  Kitchen, South Wing, Armory, Sleeping Chambers, Vaults, Royal Bed Chamber, Maximum Security.
- "Queen's Brew" / "Knight's Brew" (aaze0043:5-8, +10 rescaled to +2), "Activate Mirror Portals?" (aaze0043:16).
- "A note reads: Beware of Scraps!" / "Don't feed Scraps." / "Don't let Scraps out!" (aaze0044:49-51).
- A3's hooks carry the prisoner list (aaze0044:8) and A4's Guido carries "Try 10,11,12 on the tougher safes" (:47).

## Presentation

Music 29 (map_stats). Placed sounds: the phase walls humming (entrance, phase gallery), a pot in the kitchen
(`bubbling cauldron01`), wind in the bell tower, the open yard and down the old well's shaft. The stable yard is open
to Darkside's sky: its ceiling's faces are sky faces and `atmosphere.yml` has `open_sky: {mode: open, preset:
xeen_darkside_fading}` (D-22.6's route as XD-13; the yard opens at stage 4, between M17 and M27). 32 lights: lamplit
marble, violet-grey light in the half-phased wings (the phase gallery's pulses), torches below. Fixtures: chandeliers
hang from ceilings, sconces and torches on walls, candelabras on tables; no fixture on a leaf or in a doorway. **No
bake** in the scratch root (the lane lead bakes after install); the scratch pictures are unbaked.

## Pictures looked at

`output/studio_cal/dd03/look1_1.jpg` to `look1_7.jpg` (62 shots: every room, the doors closed and open, the stairs,
the leaves, the yard's sky) and `look2_1.jpg` to `look2_3.jpg` (26 shots after the fixes). Fixed after look1:

- The oak doors: `chb1dl` and `chb1dr` are the two halves of one arched double door. Single leaves showed half a door
  (the user's double-door rule); every oak door is now two leaves (or two panels for the house doors), both wings.
- The coat closet's illusion showed a plank frame round a cobble leaf; its doorway is now lined in cobble.
- The vault's secret door showed a plank frame; the dungeon's doorways are lined in dark cobble.
- The closet's door stood beside the throne's back; the closet moved north.
- The mirrors (glass2) met the marble bare; they have oak frames (the texture-fit rule). The yard's mirror is a wall
  panel now, not a standing block.
- Banners, crest and iron doors resized to their pictures' shape (no squashed pictures); the throne room's braziers
  (a hanging fixture) became wall sconces.

## Checks (scratch root, `--world xeen`)

- `oymap validate` L1-L4: no issues. `fmt --check` L1-L4: clean.
- `oymap build`: 7 warnings, all the named monsters (below). `output/studio_cal/dd03/build.log`.
- `oymap audit --reach --solve`: no error; 8 warnings `question.answer` (the combinations come from NPC topics, which
  the audit does not read); infos: the illusion leaf and the mirror button never move, the house doors show nothing the
  audit sees (A4's houses are not generated yet). 34 of 34 sectors reached with every door out of the way (1 as built:
  the portcullis is down until stage 1). Dressing: 0 findings. `output/studio_cal/dd03/audit.txt`.
- Playtests (`output/studio_cal/dd03/four.sh`, 4 of each, `four1.out`, logs `run/four_*`):
  - `playtest.yml` (213 steps): stage 0 to 4 as the header says, three reloads and a last one;
  - `playtest_hostility.yml` (47): every stage shown, every kind hostile, Carl peaceful, no fights among them, a reload;
  - `playtest_exit.yml` (16): the gate onto D1;
  - `playtest_dragon.yml` (24): Scraps and the well's dragons stay in with the kennel's portcullis up for 40 s (D-32).

## Words needed

1. **`monsters[].npc` indoors** (as DD-01, DD-02, DD-04): Carl talks through his bench. (A1)
2. **Names on placed monsters** need rows in `engine/data_tables/english/place_mon.txt` to show on the living monster;
   without them the names show on the corpses only and the build warns (7 warnings). A world-owned place_mon table or
   rows for Xeen would fix it. (A1/A2)
3. **A trapped chest behind a question**: the trap going off ends the event script, so effects after the preset's
   `OpenChest` (a map variable) do not run. Workaround: the tougher safes have no trap. (A1)
4. **A timer's message window** (the liches' hook) did not show as an open dialog in the headless run, though the hook
   ran; checked by the qbit. (A1, if it matters)

## Dressing exceptions

None (the audit has no dressing finding). The build's warnings are the named monsters (Words needed 2).

## DECIDE

- **Stage 1's monsters not hidden.** As built, the stage-1 spirits stand from the start (D1's gate refuses before
  stage 1, so the map is never seen without it); D-26 says each stage's monsters hidden until its qbit. Cheaper to
  reverse: one line in gen.py (`hidden` for stage 1 and a `show_actors` on the stage-1 load event).
- **The mirrors.** No shipped mirror texture; glass2 in an oak frame reads as a window of blue glass. A new
  `xkmirror` (A6) would replace both in one line.
- **The Empty Throne** is a block of t3elr marble with a tall back on a dais (A4's house door). A throne model or a
  carved picture could replace it.

## What the user should look at

- The phase leaves: violet-white masonry in the doorways; before their stage a step at a stair's foot says the stair is
  mist. After the stage the leaf rises into the lintel (a shimmering strip shows above the doorway).
- The coat closet: walk straight through its back wall into the armory (Carl's hint).
- The throne room's safes are trapped: the first one opened gives the disks and A3's text, then it opens as a chest.
- The stable yard (stage 4) has the sky over it; the stables' door and the mirror are on its west and south walls.
- Scraps waits below a low stair; raise his portcullis with the lever and he still cannot come up.
- The portcullis picture (xkportc) shows magenta specks round its bars (its transparent holes' edges), most visible on
  the kennel's: A6's texture.

## State and next steps

L4 is complete in the scratch root. The lane lead installs into `assets_dev` and bakes; A2 writes row 9152 from the slot
lines (the scratch root carries a test row); A4 makes houses 4501-4512 (the doors are drawn; entering them waits on
A4's rows); A3 registers the player bits 11320/11321 and `arrived_once` 117320.

## Installed (lane lead, A8 session 5, 2026-11-20)

- Rebuilt on the merge point 14 oymap (byte for byte the agent's build), installed into assets_dev by temp file and
  rename (`output/studio_cal/a8_s5/rebuild.sh dd03`), baked (profile `tools/lighting/baked_indoors/profiles/
  xeen_dd03.yml`, XD-08's values). Baked pictures `output/studio_cal/dd03/shots/baked_a.jpg` (31 of 62, looked at):
  it reads as a castle (banners, crests, double oak doors, phase walls in `xkshimmer`, the dungeon's rough stone);
  the white ashlar of the gate passage and entrance hall comes out near white under the bake: a lower `max_lighting`
  or `direct_scale` in this map's profile is the first polish step.
- **Waiting on:** A2's row 9152 (tests from assets_dev: `ASSETS=$PWD/assets_dev output/studio_cal/dd03/four.sh`);
  A4's houses 4501-4512 (`source/towns/dd03.yml` still planned); `place_mon` rows for the named liches and dragons
  (names on corpses only until then).

## From assets_dev and A4's houses (A8 session 6, 2026-11-20)

- A2's row 9152 and A4's houses 4501-4511 and mirror 4512 landed. The four tests 4 of 4 from assets_dev (213, 47, 16,
  24 steps; `output/studio_cal/a8_s6/item1.out`, logs `output/studio_cal/dd03/run/four_195548`).
- New `playtest_houses.yml` (51 steps): all four stage qbits, a reload, then every house door's event (both wings of
  the double doors) opens its house: the throne 4501, the chapel 4506, treasury 4507, proving hall 4508, forge 4509 and
  stables 4510 as house dialogs; the one-resident houses go straight to their resident (4502 Dimitri 5004, 4503 Megan
  5005, 4504 Tycho 5006, 4505 Guido 5007, 4511 Sir Roderic 5013); the mirror answers. 4 of 4 from assets_dev
  (`run/four_195820`); `four.sh` runs it by default now. A4: the stables list "Groom Wendell" twice (coach and NPC);
  travel tests pick `action_id: 4510`.
- The scratch root's data tables are real copies now (A4's rule: no hard links into generated tables).
- Audit on the installed map (oymap 19:17): no light or dressing finding; 8 `question.answer` warnings (the
  combinations come from NPC topics).
- **Player bits renumbered** (lead, 20:03): the brews' provisional 11320/11321 are D3's registered bits
  (`quests.py`), so the Queen's Brew is 11304 and the Knight's Brew 11305 (`tools/gen.py`, copy before
  `gen_before_bits.py`); rebuilt and installed (`b_200306`; the blv unchanged, the bake stays valid). In the root,
  `playtest`, `playtest_hostility`, `playtest_exit`, `playtest_dragon` 4 of 4 again (`four_bits.out`);
  `playtest_houses.yml` fails at step 14 (house 4502 opens with the house as the dialog's source, not Dimitri 5004):
  A4's houses 4501-4512 are not final; rerun when A4's dd03 town file is done.
- **D-37 (2):** stage 1's monsters stay visible (the DECIDE above is closed). There is no way in before stage 1: D1's
  gate refuses the party until `m19.stage1`, the mirror 4512 opens only at stage 4, the coaches land outside at D1's
  `kalindra_gate`, and the map has one exit. If a way in before stage 1 ever appears, stage 1's groups become hidden
  and shown by `evt:stage1` (one line in `tools/gen.py`). Mirrors: `xkmirror` (A6) replaces `glass2` on the Queen's
  mirror and the yard's mirror 4512 once it exists.

## Session 7 batch (mirrors, phase sounds, texture fit)

Lane A8 session 7, 2026-11-20 (`agent:xeen-a8-dd03`). Generator `output/studio_cal/dd03/tools/gen.py` (copy before:
`gen_before_s7.py`); before the change the generator reproduced the installed L4 byte for byte (snapshot
`output/studio_cal/a8_s7/snap/dd03/`).

- **D-37 (2) mirrors:** A6's `xkmirror` (128 x 128 seamless tile, its own size) replaces `glass2` on the Queen's mirror
  (`panel:queens_mirror`) and the yard's mirror 4512 (`panel:kalindra_mirror`). First install: in the oak `7trimd`
  frames both glasses baked to pure white (255 in the pictures; the walls round them read about 1.36 times their
  texture, so the pale 206 glass clips) and the oak baked as pale as the stone: a white sheet on the wall, as DD-02
  found. Second install: the frames are 32 wide in the castle's dark pillar marble `t3elr` (the map's reveals and
  pillars, in both the yard and the royal rooms; `mirror()` in gen.py). The frame now reads dark and carved, but the
  glass still clips to a flat white pane. A lower `max_lighting` alone would not fix it (at 1.2 the glass is still
  about 247). **Request to A6:** a darker `xkmirror` (mean near 120-140, with some reflected shading) for baked
  interiors; it would replace both mirrors here with no change to the map.
- **Sounds:** the two `humming` beds by the phase walls became `xeen_phase_loop` (0.35), and five loops were added:
  by the Cloud Stairs', dungeon stair's and upper stair's leaves (0.35) and in the North and South Wings by their
  shimmering patches (0.3); radii reach the wall's room only. A stage's load event switches off the loops of the leaves
  it opens (`evt.SetMapVar('AmbientSound<n>', 2)`: 7 at stage 2, 8 at stage 3, 3 and 11 at stage 4; numbers from
  ids.lock.yml, read by gen.py). The wings' and the phase gallery's loops stay (their patches stay).
  `xeen_phase_shift` plays at the party a second after the first entry that finds a new stage (timer events
  `evt:phase_shift1`-`4`, map vars `phase_seen1`-`4`; only the highest stage set, so one shimmer per entry).
- **Texture fit:**
  - `xkkalcrst` cut on the yard (error): the crest was 192 wide over the mirror, so the frame's columns split it into
    five faces. It is now 128 x 256 (its own shape), as wide as the glass: one face, shown once.
  - `desktop` (a writing desk with inkwell and paper, meant once) was tiled over the banquet and kitchen tables, Carl's
    bench and the armory racks (6 `tile_seams`): those tops are now `7trimd` planks (seamless). The ledger desk is now
    256 x 128 against the guardroom's east wall, its top the desk picture once (`scale: 2`, `offset: [0, 32]`; a
    platform top takes no `fit`).
  - `sign128` on the cream marble (6 `feature_border`): the six marble-wall signs (Throne Room, North Wing, South
    Wing, Sleeping Chambers, Vaults, Royal Bed Chamber) have a 16-wide `7trimd` frame (`framed()` now takes any size).
  - `t3s2b1`/`t3elr` (4 `family_switch`): the dark pillar marble was the reveal of the two flights' full-width heads,
    in the plane of the flights' walls. Those openings now take `reveal: t3s2b1` and `threshold: tfb09`.
- Monster names: the build shows no "named only on the corpse" warning (A2's `place_mon` 401-407 are live). The build
  log (`output/studio_cal/dd03/b_221406.build.log`) has no warnings, including none for one texture with two sizes.
- **Audit** (`--reach --solve`): before 1 error, 24 warnings; after 0 errors, 15 warnings (7 `family_switch` at the
  mirrors' frames, 8 `question.answer`, both kept below). New infos: `state.never_read` for the four `AmbientSound` variables
  (the sound runtime reads them, the audit does not).
- **Playtest:** `playtest.yml` now checks each stage's shimmer (`mapvar(4..7)`) and the loops switched off
  (`mapvar("AmbientSound7")` and the rest), and that the yard wall's loop is still on at stage 2.

### Texture fit exceptions

- The mirrors' `t3elr` frames (`family_switch`: 4 between `xkmirror` and the frame, 153 apart (81 since A6's darker `xkmirror` v2), on both mirrors; 3
  between the bedchamber's `t3s2b1` and the frame, 95 apart): the frame is the trim between the glass and the wall.
  The check counts the glass and the frame as tiles, by class. A dark frame is what makes the glass read as a mirror
  under the bake.

### Question exceptions

- The tougher safes' "10-11-12" / "101112" (events 1 and 70, the armory and the dungeon vault): Guido's greeting gives it
  (A4, house 4505, "Try 10,11,12 on the tougher safes").
- The disk safes' "64-52-31" / "645231" (event 8): Dimitri's topic gives it (npc_topic_text 41201, autonote 4124).
- The crown safe's "3-31-62" / "33162" (event 7): the Queen in Castle Blackfang gives it (quest 111543's text,
  autonote 4127).

### Session 7 tests and pictures

- Two installs (`b_221406`, then `b_222204` with the dark frames), each baked straight after (`post.sh`; stale check:
  none). Tests from assets_dev 4 of 4 after each: `playtest` 213, `playtest_hostility` 47, `playtest_exit` 16,
  `playtest_dragon` 24 and `playtest_houses` 51 steps (`output/studio_cal/dd03/s7_post_1.out`, `run/four_221834`;
  `s7_post.out`, `run/four_222515`).
- Pictures `output/studio_cal/dd03/shots/s7/` (`sheet_1-3.jpg`, 18 shots, first install) and `shots/s7/b/`
  (`sheet_b.jpg`, the mirrors after the second install), looked at:
  - the yard's south wall: the crest whole once over the mirror, the windows; the Queen's mirror over the bed;
  - the phase walls: the yard's leaf from the entrance hall, the North Wing's patch, the Cloud Stairs' leaf;
  - the six framed signs (oak board in an oak frame on the marble), the banquet and kitchen tables and Carl's bench in
    planks, the armory racks, the ledger desk with the desk picture once against the guardroom's east wall;
  - the two flights' heads: the marble runs on into the landing, with no dark pillar strip.
  - Still wrong: the mirrors' glass is a white pane (above, A6's texture).

## Session 8: rebake (darker xkmirror, lower profile)

Lane lead (A8 session 8). A6's `xkmirror` v2 (luma 204 -> 134) made DD-02's and DD-03's bakes stale; both rebaked
22:59-23:01 (`output/studio_cal/a8_s8/rebake_mirrors.out`; `stale_bakes` none). DD-03's profile lowered for the
near-white ashlar: `direct_scale` 2.0 -> 1.6, `max_lighting` 1.5 -> 1.25 (before: `output/studio_cal/dd03/
xeen_dd03_profile_before_s8.yml`). **Not yet done:** baked pictures (`a8_s8/tour_dd03.yml`: the gate passage, entrance
hall, both mirrors) and the tests 4 of 4 from assets_dev (`a8_s8/queue_polish1.sh`).

**Session 9 (lane lead):** done. Pictures `output/studio_cal/dd03/shots/s8/` (11 shots; sheets `output/studio_cal/a8_s9/
dd03_s8a.jpg`, `dd03_s8b.jpg`): the ashlar reads warm sand, no longer near white; both mirrors dim pewter in whole
frames; the yard under the fading sky. Tests from assets_dev 4 of 4 (playtest 213, playtest_hostility 47, playtest_exit
16, playtest_dragon 24, playtest_houses 51 steps; `output/studio_cal/dd03/run/four_232934`).

## Merge point 30 panels (A8 session 20, 2026-11-21)

Merge point 30's "panel over part of a doorway" check flagged four panels; all moved in `tools/gen.py` (before:
`output/studio_cal/a8_s20/dd03_gen_before_s20.py`), none kept. The bedchamber's "Royal Bed Chamber" sign and its oak frame
32 north on the west wall (centre y 5408): the frame's top, bottom and left strips reached 16 into `open:gallery_bed`'s
doorway; now 16 clear of it. The throne room's two east banners from y ±512 to ±384 (still a pair either side of the
throne): `panel:banner_throne` stood 96 over the coat closet's door (y 512-768) and 64 down into its lintel. Rebuilt with
oymap 09:24, installed and baked; audit 0 errors / 15 warnings (as before: 8 `question.answer`, 7 `textures.family_switch`).

## Session 25 (A8): warnings checked

`oymap audit` (oymap 12:46:47) on the installed map: 0 errors, 15 warnings, every one listed above: the 7
`textures.family_switch` under "Texture fit exceptions" (the mirrors' frames: 4 at `xkmirror`, now 81 apart, 3 at
`t3s2b1`, 95 apart) and the 8 `question.answer` under "Question exceptions". No map change
(`output/studio_cal/a8_s25/audit/dd03.txt`).

## Session 26 (A8): F13 status lines

- `evt:knights_brew` and `evt:queens_brew` (+2 Might / Personality once per character) wrote their text with
  `evt.SimpleMessage` (a window). `tools/gen.py` `brew()` now writes `evt.StatusText(text, 4)` for both the gain and
  "You have had your fill." (new helper `status_line()`: the seconds rule max(2, min(6, 2 + len // 15)) over 30
  characters). Before: `output/studio_cal/a8_s26/before/dd03/`. Only the map Lua and studio file changed.
- Tests (hand-written): `playtest.yml` checks the brews' status lines instead of windows, and the two safes' fail text
  "Six dials, and no idea" as a status line (A3's hooks moved it there, `failStatus`); `playtest_houses.yml`: houses
  4506-4510 each have one resident, so the door opens that NPC (5008-5012) with the services in the NPC's window, as
  4502-4505 and 4511 already did.
- Installed 00:24 (no bake: neither .blv nor scene changed), audit 0 errors / 11 warnings (as before), check_exits 0,
  check_drops 0; tests from assets_dev 4 of 4 (20 of 20, `output/studio_cal/a8_s26/run/dd03/t002727`).

## D-185 (2026-11-26, agent:xeen-fb5-dungeon2)

The stage-3 dragons are hidden until m26.stage3 and chase like any other once shown, so `check_monster_fit.py` now
counts them: 5 `fit.stuck` (Scraps at the kennel stair's 256-high mouth, both Bone Dragons at the well's two 256-high
openings). gen.py `LEASH` (from `--suggest`, rounded down to 32): Iron Vithnipravad 256, Argonax 448, Scraps 768;
posts unchanged. `playtest_dragon.yml` adds three waits just beyond each opening (no dragon's middle within radius + 64
= 184 of it). Fit 5 -> 0, audit 0 errors, playtests 5 of 5 from the stage, installed and baked, MAW reserve rerun.
