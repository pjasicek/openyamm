# Reserved mana on the portrait arcs — study, 25 October 2026

Browser study for the aura-reserved share (MAW [HANDOFF](../../../devdocs/maw/HANDOFF.md) §0.5): in MAW a held
buff aura locks part of its caster's mana (or hit points, with Legendary 32) for as long as it is held, and the
current pool can never fill that part. Today the split arcs just look "not full". Nothing is built natively.

Open [index.html](index.html) directly. The buttons switch the option; the sliders set Zoltan's reserved share and
how full his free pool is; the checkboxes move the reservation to the HP arc and show the hover popup. The other
members carry fixed reservations (0-20 %) so the whole party frame can be judged. `?option=A|B|C|D&reserved=N&current=N
&health=1&hover=0&export=stage|closeups` gives the captures in [previews/](previews/).

The scene is the native 1600x900 split-arc capture of the [potion study](../maw_potion_radial_20261025/README.md),
with the arcs redrawn in the engine's geometry (`gameplay.yml` `ObsidianPcN{Health,Mana}`: 60.4 x 76.8 units, stroke
4.6, HP 100 → 260°, mana 80 → −80°) and colours (`GameplayUiSkin::renderArc`).

## The options

![Close-ups](previews/closeups.jpg)

| | Option | Seen in | What it does |
|---|---|---|---|
| A | Locked cap | Path of Exile, Diablo IV | The reserved end of the arc is a dark hatched band with a gold mark where the free pool ends |
| B | Dimmed cap | Grim Dawn, Last Epoch | The reserved end in a greyed, darker shade of the gauge colour, a thin ivory mark at the cap |
| C | Outer rim | our personal energy shield rim | The arc is unchanged; a thin gold rim with a diamond outside it spans the reserved share |
| D | Shorter gauge | Torchlight, many MMOs | The track ends at the cap with a gold end mark; a faint dotted line traces the locked span |

| A | B |
|---|---|
| ![A](previews/stage_A.jpg) | ![B](previews/stage_B.jpg) |
| **C** | **D** |
| ![C](previews/stage_C.jpg) | ![D](previews/stage_D.jpg) |

With Legendary 32 the same treatment moves to the HP arc (green hatching for A):

![HP reserved](previews/stage_A_health.jpg)

## The hover popup (all options)

Hovering a portrait's arc shows the pool, what the auras hold, MAW's "Mana xx %" (or "HP xx %") line of what is
left free, and each held aura's share. The same lines would go on the stats page.

## Recommendation

**A, Locked cap.** It reads as "locked" at a glance, stays distinct from an empty track at small reservations
(B's weakness), keeps every arc the same length (D's weakness) and does not add a second ring beside the shield rim
(C). Native cost: one hatched arc material and one tick per gauge in `GameplayUiRenderer`, fed by
`SpellRules::reservedSpellPoints` / `reservedHitPoints`; nothing drawn when nothing is reserved.

## Decision and native work

The user chose **A** on 2026-10-25. Native: `GameplayUiSkin::renderReservedArc` (a wrapping 32x32 hatch tile along
the held span, slate on mana, green on HP, `submitHudTexturedArc`'s `uRepeat`) and `renderReservedMark` (the gold
mark, drawn over the fill), called from the portrait gauge loop in `GameplayUiRenderer.cpp` with
`SpellRules::reservedSpellPoints` / `reservedHitPoints` (Standard: 0, so nothing is drawn). The portrait popup's
Hit Points and Spell Points lines add "(N held)" instead of the study's separate popup. The debug console's `ruleset aura <member> <spell>`
holds an aura at once (used for these captures: `testparty mid casters hell`, then Haste and Shield on member 1,
Hour of Power on 2 and the resistance auras on 3-5).

![In game](native/party_auras.jpg)
![Close up](native/party_auras_zoom.jpg)

The same pass moved the potion-slot button (the radial's) to sit outside the mana arc at the portrait's upper right,
at 0.13 of the face height (was 0.16, and its centre lay on the arc): `buttonCircle` in `GameplayQuickItems.cpp`.

HP reserve (Legendary 32, 2026-10-25, 1600x900): `testparty apply mid casters` on out05, a Legendary 32 belt on member 1
and `ruleset aura 1 5` (Haste): the HP arc's held end is the green hatched band with the gold mark.
![HP reserved in game](native/hp_reserve.jpg)
