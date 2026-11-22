# DD-16 Corak's Pod: L4 notes (lane A7, thirteenth session, 2026-11-21)

Built by the lane lead from `devdocs/xeen/mockups/act5_graphs/dd16.graph.yml` and D-47
(`devdocs/xeen/mockups/act5_a7_decisions.md`, DD-16 APPROVAL and Q17-Q21). Generator:
`output/studio_cal/dd16/tools/gen.py` (writes L1-L4; never hand-edit the written files; `gen.py --levels` for L1-L3).
Scratch root `output/studio_cal/dd16/root` (hard links, real copies of maps, events/maps and every data table).

## What was built

Escape Pod 1 lying nose-up in D6's lava: 10 rooms, 10 sectors, 5.77 M units² (S: at most 15 and 20), 6 doors, 1 loop,
2 chests T5, 20 distinct textures of 30 (0 new). Three decks: midship 0 (airlock, round main deck, gun deck), the bow
256 (the couch row climbs to the bridge and the stasis alcove), the sunk stern -384 (the stern slope falls to the
engine room, the device bay, the service crawlway, whose ladder climbs through the gun deck's floor hatch: the loop).
Music 46. Family MM7 The Lincoln (7d23): a3b, a1b, a2c/a2d leaves, sfw7a decks, sfw1b reveals, sfpnloff/sfpnlon
consoles; the ancient kit's xahullbn (hatch, breach), xafield (the field, translucent), xaenergy (the devices); lavtyl.

- **Main power (D-47):** the Main Power Console's question ("Main Power Console. Activate?", aaze0087:7 mended).
  Yes: map qbit `power_on` 118080, A3's `m29.power_console`, AU's `xeen_power_up` at the panel; the pod's lights come
  up (eleven white lamps switch on beside the red emergency lamps), every console panel swaps `sfpnloff` to `sfpnlon`,
  the blast door's lamp turns from red to green and the blast door opens. Every later load with the bit: the same.
  Before: the blast door's click calls A3's `m29.blast_door` ("The bridge door is sealed. No power.").
- **The stasis field:** a translucent `xafield` leaf across the stasis alcove, Corak inside. The field's question
  (message aaze0087:0, prompt "To boldly go...", answers "where no man has gone before" with or without a full stop or
  exclamation mark; the game ignores case): right calls `m29.stasis` (111581, 111582) and drops the field, its light
  and its hum (`humming`, AmbientSound2); wrong calls `m29.stasis_wrong`. From m29.done on every load: the field down.
- **Corak** (11912, A2's peaceful placed-only immobile row, his own faction): stands in the alcove. He is
  `npc: 5513` (merge point 22's indoor word): once the field is down, clicking him opens his talk (his m32 topics).
  The bridge console: before m29.done A3's `m29.console` (the phrase in plain words), from m29.done "Stasis field
  deactivated." (aaze0087:24, map-local; the console's `evt.SpeakNPC(5513)` workaround is gone). From m32.done he is hidden (on
  load, and within a second in the visit in which he goes into the box).
- **Logs:** log1, log2 (A3's hooks); the third pages A3's `m29.log_page_1` .. `_5`, each click the next page, wrapping
  round (map variable `log_page`, D-47 Q19).
- **The alien devices:** two in the device bay, each calling A3's `m29.alien_device` (player bit 11352: +1 to all
  seven statistics and five years of age once per member, then "dormant").
- **Gun deck:** phaser and photon ("Fire anyway?" Yes: "Nothing happens.", aaze0087:11, :12, :9, map-local); the weapons
  locker (T5). **Main deck:** the scanning console (aaze0087:22, map-local).
- **The breach (D-47):** a level 128 below the engine room's deck, `floors: lava` (lavtyl, liquid lava), behind a ring
  of torn plates 112 high (a parapet the party cannot step over): off every walking line. Its glow pulses.

## Monsters (D-47 Q17)

7 placed: Floating Eye 11570 x 3, Terrible Eye 11571 x 2, Lesser Elemental 11620 x 2 (fire, by the breach): 4.79k per
member. Rest encounters 10 %, slot `Xeen Eye` Dif 0 [1, 1] (Floating Eye 40 only, D-47 Q21; A2's row 9169).

## Count exceptions

- 7 monsters under S's floor of 15 (D-47 Q17: MAPS's "few"; the group DD-16 + DD-24 is 37 and 25.59k, -4.2 %).

## Exits and arrivals

- **Arrival `entrance:d6_hatch`** (the map's start): room:airlock (-832, 0), floor 0, facing east, 192 inside the hatch.
  D6's door (A6's `m29.pod_door`) names it.
- **Exit to D6 (fifteenth session, 2026-11-21):** `exit:hatch` (256 x 256, `xahullbn`) in the airlock's west wall,
  the `exit` preset (`evt:hatch`, "Exit Escape Pod 1", the game's leave window; aaze0087:6 its meaning) to
  D6's named arrival `entrance:dd16_hatch` by name since the eighteenth session: merge point 25 stands an outdoor
  arrival on a structure's walkable top, so the anchor (5120, -2560) now stands on the crust at 1,466 facing
  south-east (1792). (Fifteenth to seventeenth sessions: the measured coordinates (5076, -2516, 1466), since the
  anchor's old 1,440 burned the party.)
  `playtest_exit.yml`: out (with lava_cooled 111564) and back in through D6's hatch (D6's event 42, `m29.pod_door`).

## Original lines (map-local; A3 records them in ORIGINAL_LINES)

dark/aaze0087:0 (the field's message), :7 (power, typo mended), :9, :11, :12 (gun deck), :22 (scanner), :24 (after
m32), :6 (the exit preset's meaning, once live). The rest are A3's hooks.

## Question exceptions

- `question.answer` (3 warnings): the field's answers are given by A3's `m29.console` hook text (the audit does not
  read hook texts), on the console beside the field.

## Words needed

None (Corak's talk and his index are merge point 22's `npc` and `ActorIndex`).

## Corak before he wakes (D-51 (1), fourteenth session)

- Corak stands inside the closed field from the first load (D-51 corrects D-47 Q20). The field (`xafield` leaf) is
  `translucent: 0.5` (`FIELD_OPACITY` in gen.py): tuned in a capture, Corak reads as a figure and the field as a field
  (`output/studio_cal/dd16/s14/f050/` unbaked; the baked capture `output/studio_cal/dd16/s14/baked/`). It is still a
  solid face: before the phrase Corak cannot be clicked, named or struck.
- **Corak cannot be killed:** a load event `evt:corak_load` runs `evt.SetMm9ActorCanReceiveDamage(<Corak>, false)`
  on every load (the word XD-19 uses for Lord Xeen), his index by `ActorIndex("monster:corak")` (merge point 22). Every hit on him is zeroed. The playtest strikes him 40 times once the field is down (at least one
  hit; 6 hits in the first run): HP 400 of 400, still peaceful, and he talks when clicked after it.

## Blocked on

- S: Corak's own look (a recolour of an installed MM6-MM8 humanoid; A2's row wears Mage C meanwhile, the row's, not
  the map's).

## Checks

- `oymap validate`: no issues; build 0 warnings; `oymap audit --world xeen --reach --solve`: 0 errors, 3 warnings
  (question.answer, above), lights/doors/texture fit clean.
- Playtests in the root: `playtest.yml` (134 steps: hatch, doors, power No/Yes, locker, devices, ladder loop, phaser,
  logs paging and wrapping, the console, the wrong and right phrase, Corak's talk, reload, m32.done),
  `playtest_hostility.yml` (eyes and elementals hostile, no fights among them, Corak peaceful and left alone).
- Installed into `assets_dev` with its bake 2026-11-21 00:13 (profile `tools/lighting/baked_indoors/profiles/xeen_dd16.yml`);
  8 of 8 from `assets_dev` (`output/studio_cal/a7/s13_dd16_four.out`). Pictures (unbaked, root):
  `output/studio_cal/dd16/shots/sheet.jpg`; after them the stern walls became `a3bs` (the bare `a1b` ribs glowed green
  over whole walls) and the couches `sfw1b`.
- (Thirteenth session: the field at `translucent: 1` drew as an opaque blue curtain; D-51 set it to 0.5, above.)
- Fourteenth session (D-51): the field at 0.5 and `evt:corak_load`; rebuilt, installed with its bake 2026-11-21 00:47
  (`output/studio_cal/a7/s14_dd16_install.out`); 8 of 8 from `assets_dev` (`output/studio_cal/a7/s14_dd16_four.out`), the
  strike as `kill: true` again 4 of 4 (`s14_dd16_kill_four.out`).
- D-49 (2026-11-21): D6's way out from the hatch lands on the cooled crust about 384 before the hatch, facing south-east;
  A6 measures and names it while building D6; then the airlock's hatch panel becomes the `exit` preset.
- Fifteenth session (2026-11-21, merge point 22): the hatch opened to D6, Corak `npc: 5513` (clicked in the playtest
  with `interact_actor`), `ActorIndex` for his invulnerability; installed with its bake 01:55:42, 12/12 from
  `assets_dev` (walk 139, hostility 32, exit 23: `output/studio_cal/a7/s15_dd16_four.out`).

## Eighteenth session (2026-11-21, lane A7 lead)

- The exit names D6's `entrance:dd16_hatch` (merge point 25 stands it on the crust at 1,466); `playtest_exit` lands at (5120, -2560) z 1458-1490, still there 6 s later, and goes back in.
- Installed with its bake 05:21:29 (`output/studio_cal/a7/s18/install_queue.sh`), stale bakes 0; audit from `assets_dev` 0 errors, 3 warnings (the kept `question.answer`) (`output/studio_cal/a7/s18/audit/dd16.txt`); **12/12 from `assets_dev`** (playtest 139, exit 23, hostility 32; `output/studio_cal/a7/s18_four.out`, merge point 25/26 binaries).

## Nineteenth session (2026-11-21, lane A7 lead)

- Merge point 27 (oymap 06:06:32): rebuilt; the peaceful-group load event now runs once per fill (map var
  `studio_peaceful_groups`), first of the load events. Only the generated Lua changed (BLV, scene and studio file byte
  for byte the installed ones; `output/studio_cal/a7/s19/`), so no rebake; installed 06:10:39, stale bakes 0. Audit
  from `assets_dev` 0 errors, the kept warnings (`output/studio_cal/a7/s19/audit/dd16.txt`); playtests 2 of 2 from
  `assets_dev` (`output/studio_cal/a7/s19/two_dd16.out`).

## Merge point 30 (2026-11-21, lane A7 twenty-third session)

- `ladder:hatch` moved from y -72 to -90: it now stands 10 inside `open:gun_hatch`'s north edge (hole y -208 to -80;
  the crawlway's north wall at -64), so the rails no longer pass through the floor's rim (merge point 30's ladder-hole
  warning, build warnings 0). The exit point (1024, 16) is unchanged; the ladder loop passes.
