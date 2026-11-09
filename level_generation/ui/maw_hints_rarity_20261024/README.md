# Hints and rarity — study, 24 October 2026

Browser study for the first pieces of MAW H.6 ([GAPS](../../../devdocs/maw/GAPS.md) §11 D.16: "every piece gets a
browser mockup in the approved Obsidian style and the user's approval before native work").

**User picks, 2026-10-24:** save cost **A + C**, skill cost **C**, item icons **C** (corner gem, none for
Common; later the same day replaced by a rarity glow around the item, see Native), ground loot **B** (name on hover). All four are native (2026-10-24); see [Native](#native) below.

Open [index.html](index.html) directly. The first row of buttons picks the piece, the second its option; the line
under them says what MAW does and what the option shows. Options are drawn over native 1600×900 captures of the
current game ([captures/](captures/): a MAW Nightmare party built for the study), in the native fonts.
`?piece=save|skill|icons|ground&option=A|B|C&export=1` gives the captures in [previews/](previews/).

## Save cost (Nightmare and up)

MAW: saving costs food, indoors 2 (10 with enemies near), outdoors nothing (3 with enemies near), free on a cleared map
and for autosaves; it says nothing beforehand, only "Not enough food". OpenYAMM charges the same
(`MonsterRules::saveFoodCost`) and says the same.

| A · in the save details | B · on the footer | C · quicksave line |
|---|---|---|
| ![](previews/save-A.png) | ![](previews/save-B.png) | ![](previews/save-C.png) |

## Skill cost

MAW: raising a magic school charges the new level, then refunds part of it when shared schools are already there; the
real cost, `ceil(new level / n)`, is never shown. OpenYAMM charges the real cost directly
(`MawSkillRules::skillRaiseCost`). The study's sorcerer: Fire and Air 10 → 11 cost 11, Water 7 → 8 costs 3, Earth
4 → 5 costs 2.

| A · cost on every row | B · on hover (status line) | C · both |
|---|---|---|
| ![](previews/skill-A.png) | ![](previews/skill-B.png) | ![](previews/skill-C.png) |

## Rarity on item icons

MAW colours only the item's name in its popup (OpenYAMM too: `MawItemRules::nameColor`): Uncommon green, Rare blue,
Epic purple, Ancient orange, Primordial red, Legendary yellow, Celestial cyan. Icons carry no mark. The rarities in
the study are assigned for show.

| A · tinted cell | B · rim | C · corner gem |
|---|---|---|
| ![](previews/icons-A.png) | ![](previews/icons-B.png) | ![](previews/icons-C.png) |

## Rarity on ground loot

MAW: none. Ground items are sprites or models depending on the item, so the marker does not depend on the model.

| A · glow on the ground | B · name on hover | C · beam (Epic and up) |
|---|---|---|
| ![](previews/ground-A.png) | ![](previews/ground-B.png) | ![](previews/ground-C.png) |

The progression and aura panels, the rule-based loot filter and potion quick-slots get their own studies after these
picks (D.16).

## Native

Built on 24 October 2026 at the user's go-ahead. Every piece is a rules hook with a Standard default that shows
nothing, so Standard games are unchanged. Captures at 1600×900 from desktop runs (MAW Nightmare, the study party; the
quicksave lines in MM6's 6d05 with a new Nightmare party):

| Piece | Where | Capture |
|---|---|---|
| Save cost A | A row under the save name: "Saving here costs N food, you carry M" ("is free now" at 0), and "With enemies near: X food" when that costs more. Red, with Save Adventure disabled, when the party carries too little. `LoadGameScreen::configureSave`'s `SaveFoodCost` from `GameApplication::saveFoodCost` (`MonsterRules::saveFoodCost` with and without enemies near); `save_game.yml` `SaveGameFoodCost` | [save_screen.jpg](native/save_screen.jpg) |
| Save cost C | Quicksave says "Game Saved! N food (M left)", or "Not enough food: saving here costs N" | [quicksave.jpg](native/quicksave.jpg), [quicksave_refused.jpg](native/quicksave_refused.jpg) |
| Skill cost C | A small "N pts" tag left of each level, green when shared skills lower it, and the hover line "Water Magic 7 to 8: 3 skill points (8, shared with Fire Magic and Air Magic)", plus ", you have N" when short. `SkillRules::skillRaiseCostDetail` (Standard none); the hover covers rows that cannot be raised too | [skills.jpg](native/skills.jpg) |
| Icons, revised | First the corner gem (C, [inventory_gems.jpg](native/inventory_gems.jpg)); on the user's later request (2026-10-24, through session A) a glow in the rarity colour that follows the item's own outline instead: the icon's silhouette in that colour (`ensureHudTextureColor`), shifted eight ways in a strong inner and a faint outer ring, drawn before the icon in one batch of 16 quads. None for Common. Inventory, chest and corpse grids and the shop's sell/identify grid, compact bags too; Interface setting "Item rarity glow" (`gameplay.rarity_glow`: Off, Hold key, Always (the default); it changes nothing in rulesets without rarities). Hold key shows it while the rebindable MAW key "Show item rarity (hold)" is held, Left Alt by default (Alt does nothing else on these screens); [glow_hold_alt.jpg](native/glow_hold_alt.jpg): released, held, released. `GameplayHudOverlaySupport::renderItemRarityGlow`; the gem and its texture are gone | [inventory_glow.jpg](native/inventory_glow.jpg), [inventory_glow_compact.jpg](native/inventory_glow_compact.jpg) |
| Ground B | The hovered ground item's name on a status plate just above the crosshair or pointer (the item is under it), in its rarity colour, while the status bar says "Get …"; nothing for Common, gold or Standard | [ground_label.jpg](native/ground_label.jpg) |

The ground label is anchored to the pointer rather than the item's top, as in the mockup, because the HUD has no
world-to-screen projection and the hovered item is always the one under the pointer. `item roll <level> [count]
[drop level] ground` (debug console) drops rolled loot in front of the party for reviewing it.

