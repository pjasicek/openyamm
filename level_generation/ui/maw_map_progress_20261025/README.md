# Map progress bar above the party frame — study, 25 October 2026

Browser study for showing MAW's map completion as a bar in the strip above the split-arc party frame, as the MAW
author (Malekith) asked: a purple-ish bar about the frame's width with the percentage and the count in small text.
Today MAW games show only a small "0%" plate under the minimap (`MonsterRules::mapProgressText`,
`MawMonsterRules.cpp`; `ObsidianMinimapProgress` in `gameplay.yml`). Nothing is built natively.

Open [index.html](index.html) directly. The first buttons pick the option, the second row the state; the checkboxes
show the status message, today's minimap plate and the hover popup. Below the scene every option is shown in every
state. `?option=A|B|C|D&state=fresh|partial|safe|complete|dimension|arena|empty&status=0|1&plate=0|1&hover=0|1`
with `&export=stage` (1600x900) or `&export=sheet` (one option's states with `&option`, all four without) gives the
captures in [previews/](previews/), taken with `google-chrome --headless --screenshot`.

The scene is the native 1600x900 split-arc capture of the [potion study](../maw_potion_radial_20261025/README.md)
(HUD scale 1.875: frame body x 384–1216, ornaments 340–1258, top edge y 706, stone band 707–713). The bars use the
frame's compact end ornament (`obsidian_curved_portraits_20260929/native/art/obsidian_party_endcap_compact.png`),
the status plate its own art (`obsidian_hud_status_plate.png`); small text Alegreya SemiBold, titles Fondamento,
status text Lucida as in the game.

## What counts (our code and MAW `ef23ee17`)

From `mapKillProgress` (indoor and outdoor runtimes), `mawMapCompletion` (`MawMonsterRules.cpp`) and MAW's
`checkMapCompletition` (`zzMaw-Monsters.lua:2568-2640`):

- **Counted monsters** n = every slain monster plus every **living hostile** one. Friendly monsters (and, in MAW's
  multiplayer, player-controlled ones) are left out; a **risen** monster counts as slain, alive or not, so a Nightmare
  revival does not undo progress. Living hostiles the map **hides** (invisible, MAW's AI state 19) are counted apart.
  The Lich of mdt15 counts one fewer. n can change while playing: summons and dimension "summon on death" add living
  hostiles, an event turning a friendly group hostile adds them.
- **Threshold**: the map is complete once slain / n ≥ **0.99^floor(n / 100)**: 100 % under 100 monsters, 99 % for
  100–199, 98.01 % for 200–299, 97.03 % for 300–399 and so on. In Road to Insanity and Beyond Madness an outdoor map
  needs 100 %. A map whose remaining hostiles are all hidden counts as complete.
- **The number MAW shows** is normalised to that threshold: min(round(share × 1000 / required) / 10, 100) %, so it
  reads 100 % exactly when the map completes (one decimal, e.g. 38.5 %). The matching count is therefore **slain /
  needed** (needed = ceil(required × n)): 112 / 292 for 300 monsters is the 38.5 %; 112 / 300 would read as 37 %
  next to it.
- **No counted monsters** (empty maps such as the Alvar merchant house d09, or all monsters still friendly, as the
  School of Sorcery before its event): no share and no text. **The Arena (d42)** is never complete; MAW shows the
  Endless Arena's wave level and progress there instead ("L5 60%").
- MAW checks on a timer and on every kill, so a kill by anyone counts; ours checks once a second.
- **MAW's colours** today: green once completed (until the monsters refill); in a dungeon red until it is safe from
  revival (from Nightmare up: 65 % of the counted slain; below Nightmare our port keeps red until cleared), else
  yellow (outdoor maps always yellow). From Nightmare up, leaving a dungeon before 65 % raises all its dead on return
  (`MawMonsterRules` map load); the 65 % is the raw share, not the normalised one.

**The completion reward** (`MawExperienceRules::rewardMapProgress`), once per map: experience (slain^0.7 scaled by
the map's level band and bolster, ×5 / party size for each member), gold, a continent-bank deposit, and — except in
Austerity — a Crafting Cube and two gems of the map's tier; the status line says "Map Completed! You gain N Exp, M
Gold and Crafting Materials". Re-clearing after a refill marks the map cleared again (the reset offer, bounty gate and
free Nightmare save read it) but pays nothing. A **dimension run** (always on an already completed dungeon) pays no
experience or gold: it says "Dungeon Completed!", counts for the Dimensional Maps quest and, once that quest is done,
gives the next Dimension Map (`completeDimensionRun`). Only in Beyond Madness does a run pay the full reward, at the
run's power × 10, plus one crafting item by its affix count.

## The options

| | Option | Height above the frame | Text | Status plate |
|---|---|---|---|---|
| A | Inlaid channel | none (in the frame's stone band) | tab at the right end | unchanged |
| B | Carved bar, centred text | 24 px bar, ornaments to y 663 (y 674–698) | centred inside | lifts 39 px |
| C | Threshold ticks, text beside | 22 px bar, ornaments to y 665 (y 676–698) | plate on the right | lifts 37 px |
| D | Thin rim, minimap keeps the number | 7 px (y 699–706) | none (hover only); minimap plate stays | lifts 8 px |

| A · Inlaid channel | B · Carved bar |
|---|---|
| ![A](previews/stage_A.jpg) | ![B](previews/stage_B.jpg) |
| **C · Threshold ticks** | **D · Thin rim** |
| ![C](previews/stage_C.jpg) | ![D](previews/stage_D.jpg) |

- **A** sets a 5 px glowing channel into the frame's own top stone band and puts the numbers on a small tab rising
  from the right corner (clear of the 620 px maximum status plate). No screen cost and the status plate keeps its
  place, but the line is thin and the frame's carving changes.
- **B** is the author's request: a brass-rimmed 24 px bar between two small copies of the frame's end ornaments, the
  numbers centred inside on the fill.
- **C** fills by the **raw** slain share with ten-percent ticks and a gold notch where the map completes (97 % here),
  so the gap to the threshold is visible; the numbers stand on a plate to the right. Honest about the threshold, but
  the fill and the "38.5 %" beside it disagree (the bar is at 37 %).
- **D** is a 7 px rim flush on the frame's top edge, no text; the minimap plate keeps the number and the hover gives
  the count. The quietest, but the count is never on screen.

### States (every option)

Each sheet shows 0 %, partial (Nightmare dungeon, revival mark red), past 65 % (mark ivory), complete (gold), a
dimension run (teal-violet fill, "Dimension · Power 12"), the Arena (wave level) and a map without counted monsters
(no bar). Full scenes: [B on a dimension run](previews/stage_B_dimension.jpg), [B with today's minimap plate
kept](previews/stage_B_plate.jpg).

| A | B |
|---|---|
| ![A states](previews/states_A.jpg) | ![B states](previews/states_B.jpg) |
| **C** | **D** |
| ![C states](previews/states_C.jpg) | ![D states](previews/states_D.jpg) |

Rules shared by all options:

- **Fill**: violet while in progress, **gold** once complete (it stays full and gold until the monsters refill, as
  MAW's green 100 %), teal-violet on a dimension run. MAW's red/yellow is replaced by the **revival mark**: a small
  diamond and line at 65 % of the counted (raw share), red until passed, then ivory, drawn only where the dead can
  rise (dungeons from Nightmare up, and the challenge modes); gone once complete.
- **Text**: "38.5 % · 112 / 292" (percent as MAW rounds it, slain / needed); "Cleared · 292 / 300 slain" once
  complete; "Dimension · Power 12 · …" on a run; "Endless Arena · Level 5 · 60 %" in d42.
- **Hidden** when the map has no counted monsters (as MAW), in Standard games, and while a full-screen overlay is up.
- **Status plate**: today it sits six logical units above the basebar and grows upward; with B, C or D it sits six
  units above the bar instead (the same kind of exception the renderer already makes for the turn-based dock).
  Complete state with the reward message:

  ![Complete](previews/stage_B_complete.jpg)

- **Hover popup** (any option): slain of counted, needed and the threshold, alive and hidden, the revival line and the
  first-completion reward (or "Paid"); on a dimension run its power and affix count; in the Arena the wave.

  ![Hover](previews/hover_B.jpg)

- **Potion ring and combat log**: the potion ring opens above a portrait and draws over the bar while open (it is
  modal for the mouse anyway); the portrait potion buttons are inside the frame and unaffected. The docked combat log
  ends beside the frame at the left (x < 340 here); only when it lifts above a frame that leaves it under 150 units
  (narrow screens, five members) could it reach the bar's left end, and then it should lift above the bar too.
- **Party size**: the frame is 46 + 80 n logical units wide. The bar follows the frame body; for one or two members
  (236 / 386 px at 1600x900) B's centred text no longer fits beside the ornaments and needs either a minimum width
  (the three-member frame, about 540 px) or the percent alone.

## Recommendation

**B, Carved bar with centred text**, with the revival mark and the gold complete state above, the count as **slain /
needed** (the total in the hover), and the **minimap plate dropped in MAW games** while the bar is shown (one place
for one number; the Arena moves to the bar too). It is what the author asked for, it is readable at 1600x900, and it
keeps the frame's carving untouched. The cost is about 40 px of play view and the status plate lifting above the bar;
if that strip is too much, A is the fallback with no height cost. C's threshold notch is worth having only if players
should see the 97 % rule; the normalised fill of B already ends at completion.

Native notes (after approval): a `MapProgressBar` group in `gameplay.yml` anchored `center_above`
`OutdoorGameplayBasebar`, sized from the frame body; a structured `MonsterRules::mapProgress(world)` (state, percent,
slain, needed, counted, hidden, revival threshold and whether it is passed, dimension power, arena level) in place of
the colour-coded text, which the minimap plate could keep using in Standard if ever needed; the status-plate placement
in `GameplayHudRenderer` reads the bar's top when it is drawn; the hover popup reuses the HUD tooltip.

## Open questions

1. B (bar, ~40 px) or A (no height cost)? And should the minimap plate go, stay, or become a setting
   ("Map progress: bar / minimap / off")?
2. Count as **slain / needed** (matches MAW's percent) or **slain / total** as in the request (112 / 300 next to
   38.5 %)?
3. After completion: keep the gold bar until the refill (as MAW keeps 100 %), or fade it to a slim gold rim after a
   few seconds?
4. Keep MAW's red/yellow dungeon colours (red below Nightmare means only "not cleared yet") or replace them with the
   revival mark only where the dead can rise?
5. One and two member parties: minimum bar width, or percent only?
6. Should a re-clear after a refill say something ("Map cleared again")? MAW's "Dungeon Completed! Reset is possible
   again." is not shown by our port (PHASE9_SCOPE P9.I1).

## Native integration (2026-10-25)

The user approved **option A, the inlaid channel**, with these answers to the open questions: the count as
slain / needed (the totals in the popup); the minimap plate dropped (the Arena's wave moves to the bar); the bar stays
full and gold until the monsters refill; MAW's red/yellow replaced by the revival mark, drawn only where the dead can
rise; percent only when a one- or two-member frame leaves the tab too little room; no "Map cleared again" message.

- **Rules**: `MonsterRules::mapProgress(world)` returns a `RulesetMapProgress` (kind map / dimension run / arena,
  percent, complete, slain, counted, needed and the required share, hidden, revival line and whether it is passed,
  reward or paid, dimension power and affix count, arena level) in place of the colour-coded `mapProgressText`.
  Standard returns none, so nothing is drawn. MAW (`MawMonsterRules::mapProgress`) reads the kills, the weakened mark,
  `clearedSinceRefill`, `completedMaps`, the dimension run and the Arena globals into the pure
  `mawMapProgress(progress, MawMapProgressFacts)` (`game/rules/maw/MawMonsterRules.cpp`).
- **Layout**: `MapProgressChannel` in `gameplay.yml`, a child of `OutdoorGameplayBasebar` (offset 10.67 / 1.6, height
  2.67 units: x 402-1198, y 708-713 at 1600x900); `GameplayScreenRuntime::resolveHudLayoutElement` narrows it with the
  frame for smaller parties. `ObsidianMinimapProgress(Plate)` are gone; the Beyond Madness death timer moved up into
  their slot.
- **Drawing**: `game/ui/GameplayMapProgressBar.cpp` (texts in `GameplayMapProgressText.cpp`), called from the HUD
  renderer on plain gameplay only (no full-screen overlay, dialogue or house screen). Palette-quad batch: the track, a
  faint glow and the per-pixel-row gradient fill (violet, gold when complete, teal-violet on a dimension run), the
  revival line and diamond, the tabs (dark plate, lit brass top, shadow), then the tab text in Alegreya SemiBold.
  The right tab reads "38.5 % · 112 / 292", "Cleared · 292 / 300" or "Endless Arena · Level 5 · 60 %"; a dimension run
  adds "Dimension · Power 12" on a left tab. Each tab may use half of the frame; when the text does not fit it falls
  back ("Arena L5 · 60 %", then the percent alone; "Power 12" on the left).
- **Popup**: hovering the channel or a tab fills the shared buff-inspect tooltip (`BuffInspectOverlayState`, new
  `above` placement: right-aligned with the channel, above it): slain of counted, needed and its share, alive and
  hidden, the revival line, the reward ("paid" once given; a dimension run's quest count), the run's power and
  affixes, or the Arena's wave.
- **Tests**: `tests/MawMapProgressTests.cpp` (percent, needed, threshold, revival line, cleared-stays-full, insanity
  outdoors, empty maps, reward lines, dimension runs, the Arena, the popup text, Standard none) and MON-16 in
  `MawMonsterItemAuditTests.cpp` (revival only from Nightmare up).

Captures at 1600x900 (`native/`, MAW save `maw_classic_heroes`, mm6 6d05 at Nightmare; console `actor kill`; the
Arena through `goto 53` and `global set MawArenaLevel 5` / `MawArenaProgress 60`):

| Fresh | Partial (revival mark red) |
|---|---|
| ![fresh](native/fresh.jpg) | ![partial](native/partial.jpg) |
| **Hover popup** | **Complete (paid)** |
| ![hover](native/hover.jpg) | ![complete](native/complete.jpg) |
| **One member (oute3)** | **Endless Arena** |
| ![one member](native/one_member.jpg) | ![arena](native/arena.jpg) |
| **Arena, one member (percent only)** | |
| ![arena one member](native/arena_one_member.jpg) | |

Differences from the study: the tab's corners are square (no rounded path); the tab text is drawn at the font's
21 px line so its letters match the study's 17 px; the popup is the shared tooltip, so its lines are single-colour
SMALLNUM text ("Label: value") instead of the study's coloured right-aligned columns, and the reward line is
shortened ("experience, gold, materials") to fit its width. Not captured natively: a dimension run (covered by the
unit tests).
