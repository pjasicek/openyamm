## DD-16 Corak's Pod

D6 · S · party 45 → 47 · 40–55 (few) · 7 · treasure 5 · Story M29, M32 (Corak)

![DD-16](act5_graphs/dd16.svg)

The source's Escape Pod 1 (dark maze0087 + 0163, 32 × 16, aaze0087) has no monsters: a narrow bow with the stasis
field and its consoles, six couches midship, the phaser and photon controls at the waist, the round main hull with the
hatch, the main power console and two alien devices at the stern. Ours lies nose-up, half sunk in D6's lava: the hatch
midship, the bow 256 up, the stern 384 down and breached. 9 review rooms, about 11 sectors, about 8 M units², 5 doors
(S: at most 15 sectors and 20 M units²).

- **What it is.** Corak's crashed pod. The Pharaoh cooled the lava (m28); the party wakes Corak with the phrase the
  console shows in plain words, then brings him the Soul Box (M32).
- **Critical path.** The airlock; the main deck; down the slope to the engine room, where the Main Power Console opens
  the bridge's blast door (map qbit 118080); back up the tilted couch row; the bridge: the logs, the console, the field's
  prompt "To boldly go..." (`m29.stasis`). Later visit: Corak by his console (`evt.SpeakNPC(5513)`, m32).
- **Off the path.** The gun deck (phaser and photon "Fire anyway?" → "Nothing happens."; the weapons locker, T5); the
  device bay (the alien device, rescaled, DECIDE 2); the engine room's stores locker (T5).
- **Loop (1).** Main deck → stern slope → engine room → service crawlway (ladder) → gun deck → main deck.
- **Set piece.** The bridge: the stasis field (`xafield` column, pulsing light) with a figure hanging in it; after
  `m29.done` the field off and Corak standing (stage by qbit), hidden after `m32.done`.
- **Monsters and treasure.** Things that crossed the lava through the stern breach: Floating Eye 40 (11570) × 3,
  Terrible Eye 50 (11571) × 2, Lesser Elemental 55 (11620) × 2 (MAPS's "lava dwellers": A2 has no such row; the fire
  elementals stand in). 7 monsters, **4.79k per member** (19,150 / 4). With DD-24's 30 (20.94k) the group is 37 monsters
  and 25.73k against 45 and 26.7k (−3.6 %). The bridge and the airlock are quiet. Chests T5 × 2. Rest encounters 10 %
  from the eyes.
- **Original lines.** aaze0087:0 (the field), :6 "Exit Escape Pod 1?" (the exit preset's meaning, D-24), :7 the power
  console, :8/:5/:10 the device (rescaled), :11/:12/:9 phaser and photon, :22 the scanning console's X.E.E.N. readout,
  :13 and :25–31 the log entries (DECIDE 3), :24 "Stasis field deactivated." after M32. Corak's lines :2–4 are A3's.
- **Door to D6.** The hatch (D6's `m29.pod_door`, A6, not built) on the cooled crust of the lava lake. **Inside arrival
  proposed:** `entrance:d6_hatch`, in the airlock about 192 inside the hatch, facing into the pod. The way out returns
  to D6 on the crust about 384 before the hatch, facing away from it.
- **Hooks.** `m29.log1`, `m29.log2`, `m29.console`, `m29.stasis`, `m29.stasis_wrong` (the bridge); Corak's m32 topics
  (Soul Box, voiced `xeen_vo_corak_soulbox`, D-38; Sheltem) from his console; `m29.pod_door` is D6's.
- **Textures.** MM7 The Lincoln 7d23 (A6's assign): a3b/a2b/a2d/a3bs, sfw7b/sfw1a, sfw7a/a2j, sfw trims, a2c, a1b,
  sfpnlon/sfpnloff; the ancient kit's `xahullbn` (hatch, breach) and `xafield` (field); MM8 lava in the breach. About
  17 of 30, 0 new.

**DECIDE items (DD-16)**
1. **Count.** (a, proposed) 7 in the pod, 30 in DD-24: group 37 and 25.73k (−3.6 %), a NOTES exception line for S's
   15 floor (MAPS "few"); (b) 15 in the pod (+15 % XP); (c) an empty pod.
2. **The alien device.** (a, proposed) +1 to every statistic and five years of age, once per character (DD-09's
   barrel pattern, D-27); (b) exactly DD-09's +1 all, one year; (c) dressing only.
3. **The pod logs.** (a, proposed) a third log computer paging the source's entries 1–15, abridged by A3 into about
   five pages; (b) A3's two short logs only.
4. **Corak's body.** (a, proposed) a peaceful placed-only row "Corak" (NoArena, not counted, S's look) shown on
   `m29.done`, hidden on `m32.done`, talking from the console; (b) a decoration figure only.
5. **Rest encounters.** (a, proposed) 10 % from the eyes; (b) 0.

**Requests to other lanes**
- A2: Act V recount (pod 7, 4.79k); the peaceful placed-only "Corak" row; note that no lava-dweller row exists (Lesser
  Elemental 55 stands in; "D6" already in the elementals' `where`).
- A3: player bit and text for the device (DECIDE 2); abridged log pages as ORIGINAL_LINES rows (DECIDE 3); the blast
  door's "The bridge door is sealed. No power." and the power line as map-local lines.
- A4: nothing (5513 exists).
- A6: `entrance:d6_hatch` and the return point on D6; the hatch's place on the lava lake.
- AU: optional stasis hum and power-up whine; else shipped hums.
- S: Corak's look (a tall figure in a guardian's armour).
- A1: nothing.

**State and next steps.** Graph, picture and notes written 2026-11-20 (phase 5, graphs only; nothing built or installed). Next: the decider answers the DECIDE items, then L1. The scratch PNG (ImageMagick) drops the link strokes; the SVG is the reference.
