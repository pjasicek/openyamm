# Aura panel — study, 25 October 2026

Browser study for the last open screen of MAW H.6, the aura panel ([GAPS](../../../devdocs/maw/GAPS.md) H.6, §11 D.16:
every piece gets a browser mockup in the approved Obsidian style and the user's approval before native work).
Nothing is built natively.

Open [index.html](index.html) directly. The buttons switch the option (and a page on how it opens); the checkboxes
knock Lys unconscious and open A's Move-to menu; clicking an aura selects it. `?option=A|B|C|open&sel=SPELL&down=1
&menu=1&export=1` gives the captures in [previews/](previews/).

The scenes are drawn over native 1600x900 captures: the Journal's 4:3 frame (from the
[Progress study](../maw_loot_progress_20261025/README.md), emptied, `frame_backdrop.jpg`) for A and B, and the
split-arc gameplay capture of the [potion study](../maw_potion_radial_20261025/README.md) for C. Faces are cut from
that capture. Art: the Obsidian menu buttons (`hud_x2/menus/omenu_*`), the spellbook icons (`icons_x2/sb??NNa`),
Fondamento titles and Alegreya SemiBold text.

## What MAW shows, and why a panel

MAW (ef23ee17) has no aura screen. A buff spell's tooltip says "Mana Reserved: x %" and "Active (name)" or "Not
Active" (`zzMaw-Spells.lua`:2440-2490), hovering a portrait's mana shows "Mana xx %" of the pool left
(`zzMaw-Stats.lua`:825-860), casting toggles ("Buff Disabled"), and R in the spellbook removes everything. Our port
does the same (`MawSpellRules::spellTooltip`, `heldBuffText`, `removeAllBuffs`); the buff panels' hover popup
lists "Held by NAME". Nothing shows the party's auras together, what each costs, which ones a stronger source makes
useless, or lets a player move one without hunting through nine spellbook pages.

## What the panel does (all options)

- **Who holds what**: every held aura with its holder, plus the fixed temple, scroll and pedestal auras ("Blessing"
  - fixed caster skill 7, Master, level 40, reserves nothing; it ends on the next map or another outdoor map).
- **Reservation**: per aura the percent of the holder's maximum (`cost / (class SP factor + Enlightenment / 2)`) and
  the points; flat points for Torch Light, Wizard Eye, Water Walk (`round(cost (1 - Enlightenment / 10))`); per member
  the total, drawn as the same hatched locked cap with a gold mark as the approved portrait arcs (reserve study A),
  green for a Legendary 32 wearer, whose auras hold hit points (`reservedHitPoints`). Death Knights and the Thief
  line reserve nothing. Totals for the party in the title line.
- **Strength**: each aura's effect at its holder's base school skill (capped 50, 75 for Day of the Gods, Day of
  Protection, Hour of Power), mastery and level, by our formulas (`MawAuras.cpp`, the update pass in
  `MawSpellRules::updateAuras`).
- **Who benefits**: a row per member with what they actually get. This is where the panel earns its place: auras
  never add up, each part takes the stronger source (Hour of Power's parts at skill / 1.5, Day of the Gods' stat
  part, Day of Protection against single resistances, a member's own potion). States: **Active**, **Partly used**,
  **Adds nothing** (the example: Lys's Stone Skin +60 under Serena's Hour of Power +60.2 holds 123 SP for nothing),
  **Suspended** (the holder is unconscious, dead or stoned: the effect is off, the reservation stays and the aura
  returns on recovery, as MAW), **Blessing**.
- **Release**: per aura, free and without recovery (A7.11), and **Release all** (= R in the spellbook).
- **Move to**: lists the other members who know the spell, what it would reserve for them and whether it fits their
  free pool; choosing one casts it as that member (their recovery, they must be ready and conscious, as a spellbook
  cast; the old holder's reservation is released; the strength follows the new holder).
- **Opening** ([opening.jpg](previews/opening.jpg)): a click on the party buff panels at the upper left, whose hover
  popup gets a "Click: open the aura panel" line; a new key **Open Auras** in the MAW key group (unbound, keys are
  scarce); optionally an Auras button on the spellbook beside R. MAW games only.

The example party: Fredrick, Crusader 85 (Legendary 32: Bless reserves 15 % = 273 HP); Alexis, Champion (no mana,
holds nothing); Serena, Priest of Light 92, Enlightenment Expert (Hour of Power 42.9 %, Day of the Gods 28.6 %,
Regeneration 17.1 % = 1,196 of 1,350 SP); Lys, Arch Druid 80 (Fire and Earth Resistance, Stone Skin, Meditation =
515 of 980 SP); Zoltan, Arch Mage 120, Enlightenment Grandmaster (Haste, Fire Aura, Immolation, Shield, Torch Light,
Wizard Eye = 600 of 1,460 SP); Water Walk from a pedestal.

## A · Ledger (full screen, pauses)

![A](previews/A_ledger.jpg)

The Journal's 4:3 Carved Obsidian frame. Five member cards with their pools across the top, the held auras as a
list (icon, holder, reserved, state), and the chosen aura's details on the right: holder, skill and level, what it
reserves, its effect and the stronger sources, the party's benefit row by row, Release and Move to. Release all and
the Spellbook on the right rail, with the state legend.

| Hour of Power, partly used | Lys unconscious, moving Meditation |
|---|---|
| ![HoP](previews/A_hour_of_power.jpg) | ![Move](previews/A_unconscious_move.jpg) |

## B · Grid (full screen, pauses)

![B](previews/B_grid.jpg)

Every aura someone in the party can hold (rows, by school) against the members (columns): gold for the holder with its
reservation, green where it would fit that member's free pool, red where it would not, a dash where they cannot cast
it; the last column is the strength in effect. Click a gold cell to release, another member's cell to move it there;
the hover popup has the effect and the party rows. Best for planning who should hold what; at 26 rows the text is
the smallest of the three and the benefit detail lives only in the popup.
[Lys unconscious](previews/B_grid_unconscious.jpg).

## C · Drawer over play (does not pause)

![C](previews/C_drawer.jpg)

A panel under the buff panels that opens on their click and leaves the game running: one row per holder with the
pool bar and the held auras' icons, one holder expanded with its auras, states and a release × per row, the chosen
aura's effect in two lines. Quick to release in a fight, but no room for the party's benefit rows or moving.
[Lys unconscious](previews/C_drawer_unconscious.jpg).

## Recommendation

**A, the Ledger.** It is the only option with room for what the panel is for - each member's actual benefit and the
"adds nothing" cases, next to the reservation it costs - while staying readable at 1600x900, and it reuses the
Journal frame, the list and detail layout of the approved Progress tab and the hatched reserve bar of the approved
portrait arcs. B's grid fits as a later "Plan" toggle inside A if the Move-to menu proves too slow; C's quick release
is mostly covered by recasting from the quick spell or the spellbook. Native cost: one screen (`GameplayAuraPanel`)
over `SpellRules` reads that exist (`reservedSpellPoints`, `reservedHitPoints`, `heldBuffText`, the aura sources of
`updateAuras`) plus a new pure `auraReport(party)` in `MawSpellRules` returning holder, reservation, strength lines,
per-member benefit and state, so the screen formats only. Release maps to the existing toggle; Move to to a cast by
the chosen member.

## Open questions for the user

- A, B or C (or A with B's grid as a toggle)?
- Should the panel release and move auras, or only show them (MAW changes them only by casting and R)? Releasing
  from the panel is a convenience MAW lacks; moving casts as the new holder, so it costs the same as in the spellbook.
- May a release happen while its holder is unconscious (MAW: only R, or the holder recasting after waking)?
- Where it opens: the buff panels' click and an unbound key, or also a spellbook button?
- Should the "adds nothing" state also show in the spellbook tooltip and the portrait reserve popup?
- No fresh native capture was needed; a capture with real held auras (a MAW save with five casters) would help the
  native pass compare numbers.

## Native integration (2026-10-25)

The user chose **A, the Ledger**, with these answers to the open questions: no B grid toggle; the panel releases
(per aura, free, no recovery: the holder's own toggle `SpellRules::castAura`), releases all (R in the spellbook,
`SpellRules::removeAllBuffs`) and moves (a cast by the chosen member: they must be ready and conscious, pay its
recovery, and the old holder's aura is released, as a spellbook cast); releasing works while the holder is down; it
opens from a click on the party buff panels (their hover popup ends with "Click: open the aura panel") and the
unbound key **Open Auras** (MAW key group), with no spellbook button; "adds nothing" shows only in the panel. MAW
games only.

- Rules: `SpellRules::auraReport(party)` (`game/rules/AuraReport.h`), empty for Standard. MAW's
  (`game/rules/maw/MawAuraReport.cpp`) gives each held aura's holder, reservation (`MawSpellRules::auraCost`, as
  `castAura` reckons it), strength (school skill to its cap, mastery, level; blessings 7, Master, 40), its effects at
  that strength set against the party's other auras (Hour of Power at skill / 1.5, Day of Protection at / 1.4, Day of
  the Gods' stat part) and each member's own potion copies, what each member gets, the state (Active, Partly used,
  Adds nothing, Suspended, Blessing) and who it could move to. The screen formats only. Tests:
  `tests/MawAuraReportTests.cpp`.
- Screen: a Journal view (`JournalView::Auras`, not a tab) in the Journal's frame, so it pauses and keeps Close:
  `game/ui/GameplayJournalAuras.cpp` in `JournalAuraPage` (`journal.yml`). The pool bars use the portrait arcs'
  hatch colours and gold mark; the buttons are the study's `omenu_button_small` / `danger` plates.
- Captures (1600x900, the `casters` test party at `endgame`, auras held with `ruleset aura`):
  [ledger](native/ledger.jpg), [Hour of Power partly used](native/hour_of_power.jpg),
  [Move-to menu](native/move_menu.jpg), [after moving Stone Skin to Oruna](native/moved.jpg),
  [after Release all](native/released_all.jpg), [buff panel popup](native/buff_popup.jpg).

Differences from the study: the effect lines are generic per effect (the study wrote some by hand, such as
Regeneration's and Meditation's formulas, Fire Aura's floors and Bless's hit chance per member); text-only effects
(Torch Light, Meditation, Regeneration and the like) read "Light around the party power 5" or "Spell points regained
over time" on each member's row. Day of the Gods and Day of Protection list one line per stat or resistance. The
state pills are square-cornered. A Legendary 32 wearer's card, list and details read HP. The "Suspended" state is
unit-tested but not captured: the console has no command to knock a member out. Clicking outside the open Move-to
menu leaves it open (Escape, Move to or a choice closes it).

![Ledger](native/ledger.jpg)
