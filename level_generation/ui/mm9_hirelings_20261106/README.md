# MM9 hirelings at the right screen edge (study, 2026-11-06)

[Gallery](index.html) · images in [images/](images/) · re-render with `./render.sh` (headless Chrome)

Requested by the user on 2026-11-06 for the MM9 hireling system (research: `devdocs/mm9/MM9_HIRELINGS.md`). MM9 shows
its hirelings at the right screen edge, a portrait with an HP bar each, in Celtic frames. This study places them beside
the current Obsidian HUD with a party of five, at 16:9 (1920 x 1080) and 4:3 (1440 x 1080). **At most two hirelings**
(the user: the party already has five).

The backgrounds are real captures of the current HUD (five-member fixture of the curved-portraits study, Sturmford
City). Only the hireling frames are drawn by the study page (`index.html`, HUD units of 1/480 of the screen height,
2.25 px at 1080p).

| | Common to the first round (revision 1 below changes Ability and Place) |
| --- | --- |
| Faces | MM9's own NPC portraits (`mm9/extracted/ART/ART/NPCPORTRAITS/NPCnn`, 60 x 80, upscaled here; the game would use x2 restorations as the MM9 PC portraits); 40 x 54 units, 84 % of a party face; ellipse clip and rim as the party's |
| HP | HP only, no mana; the party's HP colours (green ≥ 66 %, amber > 33 %, red ≤ 33 %) |
| Ability | the cross medallion (the personal-buff medallion's place) marks a daily ability ready, e.g. the healer's heal once a day |
| Text | no names under the faces, as for the party; clicking a face would open the hireling's dialogue |
| Place | right edge, from below the quick buttons (sword, head) down; never over the minimap or the basebar |

## Revision 2 (current, 2026-11-06)

The user: up to three hirelings as MM9 (two paid plus Forad or Tamur), the combat log hidden in MM9 and in the
Standard ruleset, and the rail a bit lower so a combat log switched on in the settings still fits. Images
`R2_16x9.png`, `R2_4x3.png` (three), `R2_16x9_buttons.png` (the combat-log row shown), `R2_4x3_two.png`.

- The rail starts 6 units under the combat-log/followers row (y 178; the row ends at 172).
- Three slots must end above the basebar's right ornament at 4:3 (its top at 377 units, its outer edge at 579, so
  the rail cannot pass beside it): faces 34 × 46 (72 % of a party face), the arc 4 units out and 3.6 wide, 58 units
  a slot, 2 between, a 70-unit rail; three end at y 372.
- Everything else as revision 1 (the basebar's panel, the symmetric slots, the aggro diamond and buff medallion).

## Revision 1 (2026-11-06)

The user chose A and asked for: symmetric slots, the aggro/recovery indicator, a border like the basebar's, no (or
better) end ornaments, and no combat-log/followers buttons in MM9 so the rail can move up. Images `R_16x9.png`,
`R_4x3.png`, `R_16x9_one.png`.

- **Frame:** the basebar's own panel: `GameplayUiSkin` `renderPanel` (the `obsidian_frame_*` pieces at border scale
  0.75 over `obsidian_reading_surface`), so the game needs no new art for it. No end ornaments.
- **Slot:** 76 units wide rail, 70 units per slot, 4 between. The face (40 × 54) and its HP arc are centred as a group:
  the space from the rail's inner edge to the arc on the left equals the space from the rim to the inner edge on the
  right.
- **Indicators:** the party's aggro diamond under the arc's foot with its recovery arc (the second hireling is
  recovering), the buff medallion at the rim's foot (the first is buffed). The daily-ability badge of the first round
  is dropped (the medallion's place); a hireling's ability is offered in its dialogue.
- **Place:** the rail's top 10 units under the minimap's zoom buttons (y 146); two hirelings end at y 310, far from the
  basebar at both aspects.

## First round: variants

- **A. Rail over the right edge.** One Obsidian rail (the basebar's stone and brass, its compact end ornament lying
  down as the caps), flush with the right edge; its foot level with the basebar's top, so it never meets the basebar,
  whatever the aspect and party size. HP on the party's left arc. Two hirelings: 160 units high (y 210-370).
- **B. Medallions.** Each hireling its own framed plate, the HP as a bar under the face (MM9's layout), same band as A.
  Lighter, reads as MM9; less of one piece with the basebar.
- **C. Corner rail.** A's rail flush with the right and bottom edges, next to the basebar. Ties to the basebar at
  16:9, but **at 4:3 with five members it touches the basebar's potion socket** (the bar ends 87 units from the edge,
  the rail is 70 wide plus its frame): C would need a narrower rail or a shift up there.

Recommendation: **A**. It fits at both aspects with a full party, keeps the party's HP arc language and the basebar's
materials, and leaves the bottom right free.

Open for the user: the variant; HP arc or bar; whether the daily-ability medallion is wanted; whether an unconscious or
dead hireling stays shown (greyed) or leaves the rail.
