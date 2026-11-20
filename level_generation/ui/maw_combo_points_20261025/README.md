# Combo points and stacks on the portrait — study, 25 October 2026

Browser study for MAW's portrait class counter. Today an Assassin's combo points and an Elementalist's stacks show
as one small gold number at the portrait's upper left, just outside the HP arc (`ClassRules::portraitCounter`, label
`ObsidianPcNCounter` in `engine/ui/gameplay/gameplay.yml`, drawn in `GameplayUiRenderer.cpp`). The user wants to see
**how many** points there are at a glance instead. The user approved **B** with smaller gems closer to the HP arc;
it is built natively, see [Native integration](#native-integration).

Open [index.html](index.html) directly. The buttons switch the option, the sliders set Alexis's combo points (0-5 in
half steps) and Zoltan's stacks (0-24), the checkbox hides the potion quick-slot buttons. `?option=now|A|B|C|D
&combo=N&stacks=N&buttons=0&hover=1&export=1|closeups` gives the captures in [previews/](previews/).

The scene is the native 1600x900 split-arc capture of the [potion study](../maw_potion_radial_20261025/README.md)
with the arcs redrawn in the engine's geometry (code from the [reserve study](../maw_aura_reserve_20261025/index.html)).
The potion slot buttons are drawn at their native place (upper right, see the potion study's `native/buttons.jpg`)
to check clearance. Alexis (headband) plays the Assassin, Zoltan the Elementalist.

## What the pips count

- **Assassin combo points**: 0 to 5 (`min(5, ...)` in `MawCombatRules.cpp`), +1 per paying blow or kill, **+0.5 per
  arrow**, so a pip can be half full. Spells spend 3, 4 or 5 (Blades, Stun, Mass Distortion, Fireball...). Five pips.
- **Elementalist stacks**: no cap (+1 per offensive cast, halved after the idle window, `MawClassRules.cpp`). At 10
  the cast delay is back to normal and the damage doubled (CLASSES_SPELLS_SPEC §5.5), so the pips count to **10**;
  past 10 the lit pips turn pale gold and fill again from the bottom as a second lap, and the exact number stays in
  a small badge (A, B; D keeps the number anyway).

## The options

![Close-ups](previews/closeups.jpg)

| | Option | Seen in | What it is |
|---|---|---|---|
| — | Today | `ObsidianPcNCounter` | One gold number at the upper left |
| A | Segment arc | our arc language | A thin arc outside the upper-left of the HP arc (160°-238°), 5 (10) segments filling upward |
| B | Gems | World of Warcraft | 5 round sockets on an arc around the upper left, a ruby lights per point; 10 smaller ones for stacks |
| C | Pip row | Diablo III | Small diamonds in the basebar under the face, between the aggro diamond and the buff star |
| D | Socket ring | today's place, cooldown rings | Today's number inside a round socket whose ring is cut into 5 (10) segments |

| Today | A |
|---|---|
| ![Today](previews/stage_now.jpg) | ![A](previews/stage_A.jpg) |
| **B** | **C** |
| ![B](previews/stage_B.jpg) | ![C](previews/stage_C.jpg) |
| **D** | **A, full (5 points, 17 stacks)** |
| ![D](previews/stage_D.jpg) | ![A full](previews/stage_A_full.jpg) |

B full and B with the hover popup (hovering the pips names the count, the next spell's cost and how points come):
[stage_B_full.jpg](previews/stage_B_full.jpg), [stage_B_hover.jpg](previews/stage_B_hover.jpg).

All options leave the selection diamond (top), the potion button (upper right), the aggro diamond and the buff star
(lower corners) and the HP arc itself alone. A and B sit in the gap between a portrait's HP arc and its left
neighbour's mana arc; B's lower gems come within about 15 px of the neighbour's arc. C is the most cramped: ten
stack pips are 7 px diamonds, too small at 1600x900, and there is no room for a number there.

## Recommendation

**B, Gems**, for the Assassin: it is the request's own reference, five separate sockets count at a glance even in
the corner of the eye, and a half-lit ruby reads as an arrow's half point. For the Elementalist the same arc with
ten smaller amber gems and the number badge, or, if ten gems feel busy, **A** for both (one thin segmented arc,
calmest in the arc language, and the half point reads well). D is the fallback if the number itself matters most.
Native cost: a pip draw (gem sprite or arc segments) at angles from the `ObsidianPcNHealth` element in
`GameplayUiRenderer`, fed by a new `ClassRules` call returning `{amount, pips}` instead of the string; nothing drawn
for other classes.

## Open questions for the user

- B or A (or B for combo points, A for stacks)?
- Ten pips plus a badge for Elementalist stacks, or five pips worth two stacks each?
- Should the Assassin's Subtlety stacks (0-5, attack speed, four minutes) get pips too, e.g. a second smaller row?
- Red for combo points (WoW) and amber for stacks, or one colour for both?

## Native integration

Built 2026-10-25: option B with the user's tweak (the study's red gems were too big and too far left, reaching into
the space between the portraits).

- **Rules**: `ClassRules::portraitCounter` returns a `PortraitCounter` (`game/rules/ClassRules.h`): kind (none,
  combo points, stacks), amount, pip count, and the popup's title and lines. Standard: none, so nothing is drawn.
  MAW (`MawClassRules.cpp`): the Assassin line 5 pips with the amount in halves; the Elementalist line 10 pips; the
  Subtlety stacks get none. The popup names the count, the known combo spells grouped by cost with "(ready)" on
  those affordable, and how points come (+1 per paying blow or kill, +0.5 per arrow); for stacks the count, the
  damage and cast delay they give, and how they build and fade.
- **Geometry and fills** (`game/ui/GameplayPortraitGems.h`, pure, unit-tested): gems on an arc just outside the HP
  arc's outer edge (stroke/2 + 0.15 + the gem's outer radius from the arc's centre line), 162°-234° for five gems of
  3.5 units outer radius (the study: 4.4 at 10.8 units out), 165°-243° for ten of 2.55 (study 3.3). The first gem is
  the lowest; a half point lights the lower half of a stone. Past 10 stacks every gem stays lit and the first
  (stacks - 10) turn pale gold. The Elementalist's number sits in a small pill badge between the first gem and the
  aggro diamond, its right edge just outside the HP arc.
- **Drawing** (`game/ui/GameplayPortraitGems.cpp`): procedural 32 px BGRA textures made once (socket with bronze
  and black rims; ruby, amber and pale-gold stones with a radial light and a glint; the pill), no asset files. The
  renderer calls it at the old counter's place with the `ObsidianPcNHealth` (or `ObsidianOverlayPcNHealth`) arc;
  the `ObsidianPcNCounter` elements now only give the badge's text style.
- **Popup**: hovering the gems fills the shared buff inspect popup (`updateBuffInspectOverlay`, shown above the
  gems), as the study's hover.
- Debug console: `ruleset counter <member 1-5> <amount>` sets an Assassin's combo points or an Elementalist's stacks
  (the stacks then wait 30 s before they fade).

Native captures at 1600 x 900 (`build-ui`, `--ruleset maw:hell:horizontal`, `testparty apply mid newclasses`, member 4
Ixa the Elementalist, member 5 Shade the Assassin; tour [native/tour.yml](native/tour.yml)):

| Capture | State |
| --- | --- |
| [native/combo35_stacks7.png](native/combo35_stacks7.png) | 3.5 combo points (half-lit fourth ruby), 7 stacks |
| [native/combo35_stacks14.png](native/combo35_stacks14.png) | 3.5 combo points, 14 stacks (second lap: four pale gold) |
| [native/combo5_stacks0.png](native/combo5_stacks0.png) | 5 combo points, no stacks (empty sockets, no badge) |
| [native/hover_combo.png](native/hover_combo.png), [native/hover_stacks14.png](native/hover_stacks14.png) | The popups |
| [native/closeups.png](native/closeups.png) | The three states enlarged |

Checks with five members: the gems stay on their own portrait's side of the gap between the HP arc and the left
neighbour's mana arc (also a unit test), about 2 px outside the HP
arc's edge; the left neighbour's mana arc stays clear by about 25 px at the gems and about 5 px at the two-digit
badge, the closest point. The potion buttons (upper right of each portrait) and the selection diamond (top centre)
are untouched: the top gem ends about 14 px left of the diamond.

### Sharper gems (2026-10-25)

The gems were drawn from 32-pixel textures shrunk to about 13 pixels at sub-pixel positions, which blurred the socket rims.
They are now made at the exact pixel size they are drawn at (one texel per pixel, whole-pixel positions), with the black
ring and the bronze rim a pixel each: [sharp_combo35_stacks7_crop.png](native/sharp_combo35_stacks7_crop.png),
[sharp_empty_crop.png](native/sharp_empty_crop.png) (2× nearest-neighbour crops of a 1600x900 capture).
