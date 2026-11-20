# Combat log — study, 24 October 2026

Browser study for MAW H.3 ([GAPS](../../../devdocs/maw/GAPS.md) §11 D.15: "H.3 as a scrolling combat-log overlay
after an approved browser mockup"). The docked log (A) is native since 2026-10-24; see "Native" below.

**User decision, 2026-10-24: both, native work deferred (TBD).** The docked log (A) is the default and a setting
turns it off; its "+" opens the log window (B) on demand. The user is wary of the cost in play, so the native log
must cost nothing while it is off (no stage records kept) and stay cheap while on (a capped list, built only from
hits that happen). Native implementation waits until it is scheduled.

Open [index.html](index.html) directly. The buttons at the top switch between the two layouts (or show both);
click a line or a row to see its damage stages, and the chips filter. `?view=docked|window&export=1&open=N&select=N`
gives the captures in [previews/](previews/).

## What the log shows

One entry per hit the damage rules resolve: who hit whom, with what, for how much, a critical hit and a kill, in
the status line's words (the H.4 line); the colours are this study's proposal (party members ivory, monsters coral,
amounts yellow, CRIT! orange, kills red). Each entry keeps its **damage stages** (`DamageStageRecord` from `DamagePipeline::run`): the
rolled amount, then every stage that ran with what it changed, named for the player ("Monster resistance",
"Armour and resistances", "Boss affix", "Dimension affix", "Cover", "Mist form"...). Today these records exist only
in the combat trace (`CombatRules.cpp` `runRecorded`); the native log would keep the last 200 per map.

## A · Docked log

A translucent obsidian panel above the party frame on the left, over play. The newest line is at the bottom, the
wheel scrolls back, and clicking a line opens its stages underneath ("Rolled 612 → Monster resistance −92 →
Dimension affix −8 → 512"). All / Dealt / Taken filter. A key (a new "Combat log" action) shows and hides it; it
stays open while playing.

![Docked log](previews/docked.png)

## B · Log window

A modal window over play (the pause menu's modal art), opened by the same key and closed with Escape: hits newest
first with time, line and amount (✦ a critical hit, ✝ a kill), All / Dealt / Taken / Kills, and on the right the
chosen hit's stages as bars, rolled amount first, red where a stage took damage away and green where it added.
Clear empties the log.

![Log window](previews/window.png)

## Open questions for the choice

- A, B, or both (A for play, B for a closer look at one hit)?
- Which stages to name and which to fold into one row (MAW runs up to nine on a monster hit on a party member).
- Whether heals, leeches and conditions also go in the log, or damage only (this study shows damage only).
- MAW's damage recount (H.5) is not ported (D.15).

## Native (2026-10-24)

The docked log (A) is built for both rulesets; the log window (B) is not yet.

- Opened and closed by a sword tab beside the followers' head (`CombatLogToggle` in `gameplay.yml`); the Interface
  setting "Combat log" (`combat_log`, on by default) hides the tab and stops recording.
- The panel sits in the bottom-left corner (`CombatLogPanel`), narrowed to end beside the party frame's left
  ornament; when less than 150 units are left there (a narrow screen), it lifts above the frame instead. It keeps the
  study's look: dark glass with a thin brass border, the title "Combat log", the filter chips All / Dealt / Taken, the
  hits newest at the bottom and a scrollbar on the right. The mouse wheel scrolls back; a click on a line opens its
  damage steps under it, wrapped and indented behind a gold rule: rolled, each stage that changed the amount (named
  for the player, losses coral, gains green), final.
- Lines are short for the corner (user, 2026-10-24: no time, no "for ... damage"): "Thalia hits Goblin 197",
  "Kestrel shoots Goblin 928!" (orange "!" for a critical hit), "Lys Fire Bolt on Goblin 96"; a killing blow says
  "kills" in red ("Thalia kills Goblin 197", "Lys Fireball kills 3 monsters 512"). The party's names are ivory,
  monsters coral, spells blue, amounts yellow. An area spell is one line with its total and no steps. Misses, heals
  and conditions are not logged.
- Compact rows (user, 2026-11-10: the lines were cut off before their amount nearly every time): a hit is one row of
  who, how and whom, with the amount right-aligned at the panel's edge so it is never cut. A sword or bow glyph
  stands in for "hits" and "shoots"; a cast keeps its spell's name in blue (the spellbook's icons are a smear at line
  height); a killing blow puts a red skull before the amount ("Kestrel <bow> Goblin   928!", "Lys Fireball
  3 monsters <skull>512"). When a row is still too long, the widest name takes its next shorter form, "Skeleton
  Warrior" -> "S. Warrior" -> "Warrior", until it fits, and only then is cut with "...". A click opens the whole
  sentence above the damage steps. The glyphs are drawn by [make_glyphs.py](make_glyphs.py)
  (`engine/icons_x2/combat_log_{melee,shoot,kill}.png`, white, tinted by the panel); loot lines are unchanged.
- Cost: with the setting off nothing is recorded or worded. With it on the damage rules copy each hit's stage list,
  and the panel lays its text out into glyph quads only when a line arrives, the view scrolls, a line opens, the filter
  changes or the panel moves. Other frames resubmit two cached batches: the fills in palette colours (one draw) and
  the text with every shadow first and the glyphs grouped by colour (about a dozen draws; drawn segment by segment it
  was about 120 and cost the user 1350 -> 1100 FPS). Measured 2026-10-24, open against closed: within the
  5-10 us per-frame noise of the UI pass.
- Console: `combatlog` toggles the panel, `combatlog expand` opens the newest line (for tours: mouse look keeps HUD
  clicks off in scripted runs).
