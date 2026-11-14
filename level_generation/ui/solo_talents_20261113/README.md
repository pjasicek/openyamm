# Solo run: the Talents page — study, 13 November 2026

Design only. The approved talent trees of [BALANCE_AND_TALENTS.md §5.0](../../../devdocs/solo_action/BALANCE_AND_TALENTS.md)
(melee, ranged, caster with support merged in; passives up to five ranks, actives up to three; one point per 10 levels;
only in an augmented solo run under MAW) on the fixed 4:3 Obsidian character screen beside Stats and Skills. The HUD
side (action bar, unit frame) is [the solo HUD study](../solo_action_hud_20261113/README.md) and
[HUD.md](../../../devdocs/solo_action/HUD.md).

**Chosen (user, 2026-11-13): layout A with C's two habits.** A whole-row click learns the next rank, and the hover card
doubles as the held right-click popup. It is entered by a Skills / Talents switch on the Skills page (C's entry), not a
sixth tab. Still open: the unlock rule, respec, and auto-placing a new active on the bar.

Open [index.html](index.html) from disk. `?view=a|b|c|std&export=1` (and `&tree=0|1|2` for B) shows one view at
1600 × 900; `./shoot.sh` writes them to [previews/](previews/). `prepare_art.py` copies the existing art: the solo HUD
study's icons and frame9, the Obsidian tab buttons and skills surface from `assets_source/engine/icons_x2`, the native
Skills page capture of the approved overlay collection (revision 03) as the frame, paperdoll and portrait row, and the
game's fonts (Create, Lucida, Smallnum, Arrus, Fondamento).

| Variant | Entry | Layout | Detail | Bar |
|---|---|---|---|---|
| A · Three columns | a sixth tab, Talents | all three trees on the left page, one row per node (icon, name, pips); paperdoll kept | hover card | right-click: put on bar or move |
| B · Tabs and detail | a sixth tab, Talents | one tree at a time, passives and actives in two rows of large icons; the paperdoll gives way to a detail panel | always-on panel | a ten-key strip in the panel |
| C · Skills-page list | Skills \| Talents toggle in the Skills header (five native buttons) | rows like the skill rows: pale blue learnable, grey locked, n/max | held right-click inspect popup | drag the row, or a number key while inspecting |
| Standard / party | — | unchanged screen, no Talents anywhere | — | — |

Shared: round icons are actives, square passives; gold rim learned, teal learnable now, gold with teal learned with a
rank left to buy, grey with a padlock locked; diamond pips per rank (teal outline: the next rank); the header shows
the points to spend and the next point's level; a Reset button (rule open). The locks are this study's proposal:
passives always open, actives need the matching MM skill at Expert (Whirlwind and Spell Surge at Master).

**Recommendation: A**, with C's habits: whole-row click learns (as Skills does), the hover card doubles as the held
right-click inspect, and right-click places an active on the bar. All 17 nodes fit at a glance with their icons (which
the player then meets on the action bar), the paperdoll and the screen's structure stay, and the only new chrome is one
tab. B is better on Android (no hover) and for larger trees; it can be A's touch layout.

Icons: all 17 are placeholders from existing game art (item, spell and buff icons); every talent needs its own icon.

Decisions: A, B or C (and B for Android?); a sixth tab or a Skills sub-page; the locks (by MM skill and mastery, or
none); the respec rule (free, gold, at a trainer, once per level band); whether learned actives go to the first free
bar key automatically.
