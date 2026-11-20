# MAW mod: UI, settings, infrastructure, NPCs/quests/maps, assets

First-pass overview. Corrected on 2026-10-22 against the verified specs listed in [README.md](README.md); where they
differ, the spec documents win.

Scope: everything in MAW (`/home/pjasicek/github/Maw-Mod-MMMerge`, HEAD `ef23ee17`) that is not item
generation, combat math, or skills/spells/alchemy. Paths below are relative to the MAW root unless they start with
`base:` = `/home/pjasicek/github/OpenYAMM/reference/mmmerge/` (Rodril nightly) or `forus:` =
`reference/mmerge_data_forus/`. Diffs were taken with `diff --strip-trailing-cr -w` (MAW uses CRLF; raw diffs look
like whole-file rewrites but are not).

LOD contents were listed with a throwaway Python lister (not kept). Format notes for re-creating it:
(MMVI 32-byte entries; MMVIII 0x4C-byte entries with 64-byte names; MM8 language records have a 0x60 header,
packed size at +0x44, zlib payload at +0x60).

---------------------------------------------------------------------------------------------------------------------

## 0. Headline findings

1. **MAW is always on once installed.** There is no master switch. It is a file overlay on MMMerge + Rodril patch +
   the *multiplayer branch* (README.md:20-29). Difficulty/ruleset is chosen through four separate, poorly signposted
   places: a "Mode" spinner at the top-right of party creation, a "Randomizer" tumbler on party creation, the
   repurposed MMMerge "Extra settings" page, a second "MAW SETTINGS" page, plus a `MAWSettings.lua` text file in the
   game folder for hotkeys and toggles. A new-game ruleset screen in OpenYAMM would replace all of these.
2. **The "Bolster monsters" tumbler is mislabeled.** MAW permanently disables MMMerge's monster bolster
   (`General/zzMaw-Monsters.lua:2133-2137`) and wires the first tumbler on the stock `ExSetScr` background (whose
   painted label still reads "Bolster monsters") to `Game.freeProgression` (`General/MenuExtraSettings.lua:162,233`).
   The README even tells users "Free Progression (set monster bolster to on)" (README.md:223). "Bolstering power"
   is now the MAW difficulty (Easy..Nightmare), not a percentage.
3. **MAW's "MAW SETTINGS" page only exists if the multiplayer module is installed**: it is created in
   `events.MultiplayerInitialized` and uses `Multiplayer.utils.UI.CustomNumeric`
   (`General/AdaptiveMonstersStats.lua:432-447`, `General/zz_Maw-initialize.lua:546-579`). Single-player users still
   need the multiplayer branch; otherwise a `debug.Message` warns "settings page not registered".
4. **Several MAW map-script overrides are stale copies of older MMMerge files and silently drop later base fixes**
   (7out02 Judge Grey/Arbiter messenger, 7d24 throne-room QBit check and Dwarf-king QBit unstick, 7d29
   Cross-Continents completion flag, d19 invisibility path). OpenYAMM must merge "base fixes + MAW additions", not take
   MAW files as-is.
5. **Many hotkeys exist only in a PNG and in a text file**; several clash by screen (R = sort bag / reroll shop /
   remove buffs / elementalist rotation / map-damage reset; G = HP potion and party multi-bag sort; E = charge and
   alchemy-sort owner). Yes/no confirmations are typed text answers (`Question()` + "yes"/"Y").
6. Most odd code in the core/hook files is vanilla-engine workaround (16-bit facet refs, 16-bit monster HP, 255 skill
   cap, PlaceMon name slots, register clobbering in the UI loop, Town Portal click-through, divide by zero in temple
   UI). A native engine needs none of it.

---------------------------------------------------------------------------------------------------------------------

## 1. Catalogue of every new or changed UI element, screen, message and hotkey

Legend for "Where": Map = gameplay screen (0); Inv = character screen inventory tab (7/103); Skills = character
screen skills tab (7/101); Stats = character stats tab (7/100); Book = spellbook (8); Party = party creation (21);
ExtSet = Esc > Controls > Extra settings pages; House = house dialogue (13).

### 1a. Hotkeys (configurable ones read from `MAWSettings.lua`, see §2.2)

| Key (default) | Where | What it does | file:line |
|---|---|---|---|
| E (`chargeKey`=69) | Map, solo party only, Knight classes 16-19 | "Charge": rushes the party to the targeted monster (500-3000 range), 25-tick cooldown | General/zzMAW-Skills.lua:953-1000 |
| G (`healthPotionKey`=71) | Map, solo only | Drinks best Cure Wounds (item 222) from backpack, heals bonus^1.4+10, cooldown | General/zzMAW-Skills.lua:1042-1083 |
| V (`manaPotionKey`=86) | Map, solo only | Drinks best Magic Potion (223) | General/zzMAW-Skills.lua:1086-1120 |
| K (`teleportDeadMonstersAndCraftingKey`=75) | anywhere (no screen check) | Pulls up to 30 corpses (AIState 5) and 30 crafting items / map items (290) to the party; status text "Teleported N monsters and M crafting items" | General/zzMaw-Monsters.lua:4432-4464 |
| O (hard-coded 79) | Map | Toggles `disableBow` (melee-only challenge): "Bow Disabled/Enabled"; also strips dragon ranged attack | General/zz_Maw-initialize.lua:643-663 |
| L (hard-coded) | Map | "Get unstuck": Party.Z += 100, 5 game-minute cooldown (`vars.lastUnstuck`) | General/zzMAW-Skills.lua:2502-2510 |
| R (`currentBagSortKey`=82) | Inv | Sort current bag, "Inventory sorted" | General/zzMaw-Item-Sorter.lua:39-44 |
| T (`partyBagSortKey`=84) | Inv | Sort all party members' current bags | General/zzMaw-Item-Sorter.lua:44-47 |
| E (`AlchemyBagKey`=69) | Inv | Toggle "this player takes alchemy/crafting items when sorting" (`vars.alchemyPlayer`) | General/zzMaw-Item-Sorter.lua:47-56 |
| C (`multiBagSortKey`=67) | Inv | Sort all of current player's bags (multi-bag) | General/zzMaw-Item-Sorter.lua:427-450 |
| G (`partyMultyBagSortKey`=71) | Inv | Sort all bags of all party members (slow) | General/zzMaw-Item-Sorter.lua:674-700 |
| 1-5 (solo) / Shift+1-5 (party) | Inv, chest inventory (15), House (13), Adventurer's Inn (29) | Switch multi-bag tab 1-5; solo Shift+1-5 switches bag page (100s) | General/zzMaw-MultiBag.lua:38-67 |
| Shift+B | Inv | Toggle current bag as "crafting bag" (marked with a yellow "C" over the bag button) | General/zzzMaw_CraftingBag.lua:49-55, marker 81-93 |
| U, then U again | Inv | Two-step gem upgrade: first press shows "Convert X into Y? (U)", second combines 3 gems into the next tier; any other key cancels | General/zzMaw-Items.lua:4207-4275 |
| R | House shop (BuyStandard 2 / BuySpecial 95) | Reroll shop stock for gold ((tier+strength)^2*250) | General/zzMaw-Items.lua:3922-3960 (no screen check in the key handler itself, `refreshItems` checks HouseScreen) |
| Alt (hold) | Item / monster tooltips | Show possible enchants (items) or unreduced base damage (monster info) | General/zzMaw-Items.lua:1665-1679; General/zzMaw-Monsters.lua:1858-1869 |
| (setting) Alt+Tab per PNG | Item tooltips | Actually the MAW SETTINGS switch "Extra Item Tooltip" makes the Alt view permanent; the PNG's "ALT+TAB" refers to that | General/zzMaw-Items.lua:1665-1669 |
| R (`removeBuffsKey`=82) | Book | Clears all MAW buffs (`vars.mawbuff={}`), "All buffs have been removed" | General/zzMaw-Spells.lua:22-27 |
| Tab | Book | Cycles spellbook pages through schools the player knows | General/zzMaw-Spells.lua:3539-3560 |
| P | Skills | Toggle "Cover" (plate/shield guard) for current player | General/zzMAW-Skills.lua:2235-2246 |
| M | Skills | Toggle "Mana Shield" | General/zzMAW-Skills.lua:2247-2258 |
| R | Skills, Elementalist classes | Toggle elementalist auto-rotation | General/zzMAW-Skills.lua:2259-2276 |
| R then Y | Stats | Reset per-map damage tracking counters ("Map data reset, press Y to continue...") | General/zzMaw-Stats.lua:21-50 |
| Ctrl+F1 / Alt+F1 | anywhere, when "challenge" or Insanity is active | Swallowed; MMExtension console/editor use is logged into the save (`vars.q1`, `vars.r1`, console code into `vars.s1`) | General/zzMaw-Monsters.lua:3242-3315, 3750-3763 |
| F9 (+Ctrl/Alt/Shift) | — | Boss debug dump; handler body is commented out (returns immediately) | General/zzBossSync.lua:536-562 |
| Return | Map, in multiplayer | Turn-based mode disabled ("Turn-based mode is not available in multiplayer.") | Modules/Multiplayer/Synchronization/TurnBased.lua:23-29 |
| 1..N, P | Map/SelectTarget, in multiplayer | Select remote player N / toggle remote-players panel (registered on the base Keybinds page) | Modules/Multiplayer/UI/RemotePlayers.lua:464-480 |
| F5-F9, 0, 6-9 (in PNG) | Map | Extra quick-spell slots, NPC panel, NPC 1-4: **base MMMerge** (ExtraQuickSpells / NPCFollowers keybind page), not MAW | General/ExtraQuickSpells.lua:175-190 (base) |
| Esc on ExtSet pages | ExtSet | Leaves (base) | General/MenuExtraSettings.lua:28-31 |

Shortcut sheet `MAW_Guidebook/Might and Magic MAW Mod_Shortkeys_06.02.png` lists exactly: E (map: knight charge, solo;
inventory: alchemy owner), K, G (map HP potion), V, R (inventory sort / skill tab elementalist rotation / shop refresh /
spellbook remove buffs), R then Y (stats: reset map damage), T, C, G (inventory: all bags of all players), Shift+1-5,
O, P, Alt, Alt+Tab, M, L ("10 second cooldown"; code says 5 game minutes), U, F5-F9, 0, 6-9. Missing from the sheet:
Shift+B (crafting bag), Tab in spellbook, the Doom/DK attack-spell toggles (below), multiplayer keys.

### 1b. Mouse-driven toggles hidden in existing UI

| Element | Where | What it does | file:line |
|---|---|---|---|
| Click on spell 68/74/96 in book (Death Knight classes) | Book | Toggles "<spell> on attack activated/disabled" (`vars.dkActiveAttackSpell`) | Modules/MawCore/Classes.lua:843-858 |
| Quick-cast button (Death Knight) | Map | Same toggle for the quick spell | Modules/MawCore/Classes.lua:860-875 |
| Spellbook click (Elementalist/Assassin) | Book | Binds rotation / spell sets; "Elementalists learn their spells through practice" | Modules/MawCore/Classes.lua:458-627; General/zzClasses.lua:534,615,628,634,689 |
| Click a shared skill (Id Item/Monster, Repair, Merchant, Disarm) | Skills | "Share to all party" (README.md:132-133) | General/zzMAW-Skills.lua (Action 121 at :348) |
| HP/SP bar hover | Map | Tooltip replaced: "HP xx%" / "Mana xx%" of MAW pools (GlobalTxt 108/212 rewritten on hover) | General/zzMaw-Stats.lua:827-845 |
| Stat right-click | Stats | Per-stat extra bonus text (Might %, Int crit, etc.) | General/zzMaw-Stats.lua:300+ (BuildStatInformationBox), :947 |
| Monster right-click | Map | Rewritten monster info box (level, MAW damage, resists, debuffs) via new `BuildMonsterInformationBox` event | General/zzMaw-Monsters.lua:1965; Structs/extraEditableDescriptions.lua/.md |
| Item right-click | everywhere | MawCore tooltip pipeline (13 sections) | Modules/MawCore/Tooltip.lua |
| Skill hint | Skills | MawCore per-player skill tooltips, extended-skill rows (Skillz.dll port) | Modules/MawCore/SkillTooltip.lua, SkillsUI.lua |

### 1c. New buttons, text widgets and screens

| Element | Screen / position | What it does | file:line |
|---|---|---|---|
| **Mode spinner** "Normal / Doom / Road to insanity / Beyond Madness / Austerity" (arrows + 70-px text) | Party creation, X=520 Y=20 | Picks `Game.Mode` 0/2/4/6/8; committed to vars at new game | General/MenuExtraSettings.lua:237-247 |
| **Randomizer tumbler** + " Randomizer" label | Party creation, X=485 Y=55 (label X=380) | `Game.RandomizerMode`; shuffles artifacts/keys between maps and shuffles map monster pools | General/zzzzMalekith-Randomizer.lua:374-401 |
| Survival tumbler | Party creation X=530 Y=10 | **Commented out** (dead). `Game.Mode==1` survival is unreachable because the Mode spinner steps by 2 | General/zzMaw-Survival.lua:5-19, :124-129 |
| Free class selection (base `tab2a` button at 588,54) | Party creation | **Removed**; free race/class/portrait selection is now always on (only "must be unpromoted" remains). README still says "press the icon top right" | General/MenuChooseCharacter.lua:170-183, :424 (base: base:Scripts/General/MenuChooseCharacter.lua:351-371) |
| ExtSet page 1 "General settings" (stock `ExSetScr` art) | ExtSet | Tumbler 175 = **freeProgression** (label says "Bolster monsters"); regulator 220 = **MAW difficulty** Easy/Norm./MAW/Hard/Hell/Night-mare (0..250 step 50); tumbler 251 weather; regulator 295 frame limit; tumbler 326 improved pathfinding | General/MenuExtraSettings.lua:159-334 |
| ExtSet page "MAW SETTINGS" (stock `ExSetScr2` art, header text) | ExtSet, only with multiplayer module | Six text switches `< value >`: Buff Rework ON/OFF, M&M6 Projectiles ON/OFF, Homing Projectiles ON/OFF, Damage on Friendly Units ON/OFF, Loot Filter OFF/Common/Uncom./Rare/Epic/Ancient/Primordial, Extra Item Tooltip OFF/ON. Base "Bolster multipliers" numeric rows are commented out | General/AdaptiveMonstersStats.lua:432-455; General/zz_Maw-initialize.lua:536-579 |
| Multi-bag buttons (10: 5 bag tabs + 5 page tabs using `SlChar1-5U/D` art) | Inv/House/Chest/Inn, X=455+i*30, Y=372 and 445 | Switch bag / page; hidden during Arcomage | General/zzMaw-MultiBag.lua:68-115 |
| Crafting-bag "C" markers | Inv/House, above bag buttons | Shows which bags are crafting bags | General/zzzMaw_CraftingBag.lua:81-93 |
| Map completion % text | HUD screen 0, X=500 Y=377 | Green = completed, yellow = cleared/outdoor, red = not; also used by Arena for wave progress | General/zzMaw-Monsters.lua:2265-2287; Global/zzMaw_Arena.lua:44-50 |
| Madness death timer (red/green seconds) | HUD, X=500 Y=450 | Beyond Madness: seconds until combat "cools down"; loading while red = death | General/zzMaw-Monsters.lua:2490-2516 (hex-obfuscated strings via `_H`) |
| "Death Count: N" | Character screen, X=470 Y=1 | Beyond Madness run-wide death counter (shared across saves) | General/zzMaw-Monsters.lua:2495-2512 |
| Elementalist stack counters (5) | HUD, X=5+i*96 Y=387 | Per-portrait stacks | General/zzClasses.lua:640-651 |
| Assassin stack counters (5) | HUD | Per-portrait stacks | General/zzClasses.lua:693-705 |
| Multiplayer: remote-players panel toggle (`tab5a/b`), remote player widgets (HP/SP/range/TB phase), "Show players location" on map screen, players-in-house list, lobby/server list UI | Map / Info / House | Multiplayer module UI | Modules/Multiplayer/UI/RemotePlayers.lua:439-560, GlobalMap.lua:96-115, House.lua, Lobby.lua, ClientsTable.lua |

### 1d. Modal messages, confirmations and notable status texts

| Message | Trigger | file:line |
|---|---|---|
| Intro: "Greeting adventurer! ... check the difficulty settings (ESC-->Controls-->Extra Settings(on the top)-->Bolstering Power)" | first time, polled | General/zzMaw-Monsters.lua:2836-2839 (polled every 0.5 s via `MawAddTimer("nightmare",...)` General/zzMaw-Timers.lua:93) |
| Beyond Madness warning (long rules text) | first time in Madness | General/zzMaw-Monsters.lua:2801-2805 |
| Nightmare activation: typed "yes/no" Question; yes = permanent True Nightmare (BolsterAmount 300), no = "Difficulty reverted to Hell" | BolsterAmount set to 250 | General/zzMaw-Monsters.lua:2819-2834 |
| "Not enough food" (save costs 2/3/10 food in Nightmare/Doom); "Can't teleport now" (Lloyd near enemies) | CanSaveGame / CanCastLloyd | General/zzMaw-Monsters.lua:2139-2196 |
| "Loading now will count as death, are you sure to proceed?" (first press blocked) | Madness, load/menu with red timer | General/zzMaw-Monsters.lua:2519-2534 |
| Dungeon reset typed yes/no ("...reset it and attempt it once more with even harder monsters...") then "Entering will reset the dungeon" | entering a completed dungeon | General/zzMaw-Maps.lua:191-238 |
| Dragon hatchling: feeding progress, days left, "needs 5 food", "Release the dragon" topic with typed Y/N | Quest_DragonHatchling | Global/Quest_DragonHatchling.lua:9-14, 120-200 |
| Doom mode NPC refusal "I wouldn't join in your reckless adventure, not even for all the wealth in the world." and hire topic renamed "Following you would be foolish" | Doom mode hire attempt | General/NPCFollowers.lua:248-253, 490-497 |
| "Access have been destroyed" (Doom) / "You must prove your worth first" (needs lvl 255 or difficulty <= MAW) | outb3 event 92 (to znwc) | Maps/outb3.lua:56-68 |
| Respec dialogue: "Skill reset info" / "I want to reset" topics, 1000 gold/level | NPCs 314, 413, 794 | Global/zzMAWRespec.lua:1-125 |
| "Dimensional Maps" topic texts (too low / give / not cleared / reward) | NPCs 314, 413, 794 (slots 4/4/0) | Global/zzMaw_DimensionalMapsQuest.lua:29-32, 145-154 |
| Ambush/boss texts: "It's a trap!", "Queen Arrived!", "Monsters swarming...", "Noises from the throne room", "It's an ambush!", "Goblin Reinforcements", "The night is dark and full of terrors", "In the night the deads rise" | map scripts | Maps/7d21.lua, 7d24.lua, 7d29.lua, 7out02.lua, 7out05.lua |
| "Resistance Ignored" | map affix 8 | Global/zzMaw_Mapping.lua:1-6 |
| Multiplayer all-down status line "Health: x/y Mana: x/y" | multiplayer | General/zzzOnlineVariableSender.lua:318-330 |
| Missing MAW settings page warning (debug.Message) | multiplayer module absent | General/zz_Maw-initialize.lua:551-556 |

---------------------------------------------------------------------------------------------------------------------

## 2. Settings: what MAW adds, where, defaults, storage

### 2.1 In-game settings (saved per save game)

| Setting | Screen | Values / default | Runtime var | Saved as | file:line |
|---|---|---|---|---|---|
| Game mode | Party creation spinner | 0 Normal (default), 2 Doom, 4 Road to Insanity, 6 Beyond Madness, 8 Austerity | `Game.Mode` | At new game: `vars.Mode` (+ `vars.insanityMode`, `vars.madnessMode`, `vars.AusterityMode`, `vars.DoomPartyNeedInit`); also mirrored in `vars.ExtraSettings.Mode` | General/MenuExtraSettings.lua:237-271 |
| Mode mapping | — | 2 -> Mode 2; 4 -> Mode 2 + insanityMode; 6 -> Mode 2 + insanity + madness + freeProgression=false + party reset to level 1, skills to 1; 8 -> Mode 8 + AusterityMode | | | General/MenuExtraSettings.lua:249-301 |
| Doom start bonus | — | Party.Gold=5000, +10000 XP split (only for Doom-family modes) | | | General/MenuExtraSettings.lua:297-300 |
| Randomizer | Party creation tumbler | off | `Game.RandomizerMode` | `vars.RandomizerMode`, `vars.Randomizer`, `vars.OriginalItemOrder`, `vars.ItemFound`, `vars.MonsterShuffleList`, `vars.RandomizerFixed` | General/zzzzMalekith-Randomizer.lua:18-25,110-160,374-406 |
| Free progression vs horizontal | ExtSet p1 tumbler (labelled "Bolster monsters") | nil -> true on load (`(ExSet[v]==nil) and true`) | `Game.freeProgression` | `vars.ExtraSettings.freeProgression`, `vars.freeProgression`, `vars.storedMasteries` (masteries removed when switching to horizontal, restored on switching back) | General/MenuExtraSettings.lua:162,233,367-369; General/zzMAW-Skills.lua:1975-2010 |
| Difficulty ("Bolstering power") | ExtSet p1 regulator | 0 Easy, 50 Norm. (fresh `Game` default), 100 MAW (default for old saves without the key), 150 Hard, 200 Hell, 250 Nightmare (-> confirmation -> 300 True Nightmare, locked); 600 forced in Doom/Madness | `Game.BolsterAmount` | `vars.ExtraSettings.BolsterAmount`, `vars.trueNightmare` | General/MenuExtraSettings.lua:307-317,362; General/zzMaw-Monsters.lua:355-375, 2799-2834 |
| Frame limit | ExtSet p1 | none/30..360 | `Game.FrameLimit` | Windows registry `m_framelimit` (base) | General/MenuExtraSettings.lua:319-334 |
| Weather, Improved pathfinding | ExtSet p1 | base | | `vars.ExtraSettings` | base |
| MMMerge monster bolster | — | **forced off every map load** | `Game.UseMonsterBolster=false` | | General/zzMaw-Monsters.lua:2133-2137 |
| Bolster multipliers (base page 2) | — | rows commented out; values still saved | | `vars.BolsterMultipliers` | General/AdaptiveMonstersStats.lua:420-447 |
| Buff Rework | MAW SETTINGS | ON | `vars.MAWSETTINGS.buffRework` | `vars.MAWSETTINGS` (commit on any Exit action 113, reload on LoadMap) | General/zz_Maw-initialize.lua:536-622 |
| M&M6 Projectiles | MAW SETTINGS | ON | `restoreProjectiles` | same | :538, use General/zzMaw-Monsters.lua:3850 |
| Homing Projectiles | MAW SETTINGS | ON | `homingProjectiles` | same | :539, use General/zzMAW-Skills.lua:737 |
| Damage on Friendly Units | MAW SETTINGS | OFF | `friendlyDamage` | same | :540, use Modules/MawCore/Damage.lua:1199 |
| Loot Filter | MAW SETTINGS | OFF | `lootFilter` | same | :541, use General/zzMaw-Items.lua:930-969,1346 |
| Extra Item Tooltip | MAW SETTINGS | OFF | `extraItemTooltip` | same | :542 |
| (hidden) buffRadius, blockSpells | — | 20000, spell 8 blocked in MP | `vars.MAWSETTINGS` | same | General/zzMaw-Multiplayer.lua:14-21 |

Note: the six MAW SETTINGS switches are only committed to `vars.MAWSETTINGS` on action 113 (Exit) and read back in
`LoadMap`; they are effectively per-save, but the in-memory table is shared across saves loaded in one session.

### 2.2 `MAWSettings.lua` (per installation, game root; not in saves)

Created with defaults on first run (`General/zz_Maw-initialize.lua:4-239`), loaded with `dofile` (:241-268), copied to
globals (:274-295) and also dumped into every save as `vars.MAWINITSETTINGS` (:298-300).

| Key | Default | Meaning |
|---|---|---|
| autoTargetHeals | true | Healing quick-casts auto-target lowest-% HP member (General/zzMaw-Spells.lua:1264) |
| disableBow | false | Melee-only challenge (also toggled by O) |
| enableDisintegrate | true | Insanity: overkill disintegrates characters (MawCore/Damage.lua:1928) |
| ColouredStats | true | Coloured stats menu |
| showDeathCounter | true | Beyond Madness HUD counters |
| disableCompletitionMessage | false | Suppress dungeon completion messages |
| disableSpellBookRework | false | Keep vanilla spellbook item art (zVex icons) |
| removeBuffsKey 82, chargeKey 69, healthPotionKey 71, manaPotionKey 86 | R, E, G, V | Hotkeys |
| currentBagSortKey 82, partyBagSortKey 84, multiBagSortKey 67, partyMultyBagSortKey 71, AlchemyBagKey 69 | R, T, C, G, E | Sorting hotkeys |
| enableAllTrainers | true | Moves trainer NPCs into other houses for five skill groups (racial, Dodging, Unarmed, ID Monster, Regeneration); the rest relies on base teachers (Global/zzMAW_MoveTrainers.lua) |
| onlineQualityOfLifeFeatures | true | In MP: training/travel time 0, coaches/ships/shops always open ("ChallengeMode") |
| teleportDeadMonstersAndCraftingKey | 75 (K) | Corpse/material pull |
| fasterStrafing / slowerBackpedaling | true / true | Movement asm patches (General/zMaw-hooks.lua:39-163) |
| crashDiagnostics | (absent = on; "full" or false/"off") | MawDiag.txt profiler/crash log (General/zzzMaw_CrashDiag.lua) |

The default file also embeds a full virtual-key-code list (lines 44-226): key rebinding is by editing numbers.

### 2.3 Other persisted side files

`Data/Tables/Character selection.txt` (base, now ignored by MAW's selection logic), `MawRegisterGuard.log`
(General/zMaw-hooks.lua:212-229), `MawDiag.txt`/`MawDiag.old.txt` (CrashDiag), registry `m_framelimit`.

---------------------------------------------------------------------------------------------------------------------

## 3. Per-file summaries (vs base MMMerge)

### Menus
- **General/MenuExtraSettings.lua** (base:Scripts/General/MenuExtraSettings.lua, 93 changed lines). Adds `Width` param
  to `NumberRegulator` (:96,110) and boolean guard (:135-137); `VarsToStore` += `freeProgression`, `Mode` (:162);
  first tumbler rebound to freeProgression (:233); Mode spinner on party-creation screen 21 (:237-247) with new-game
  commit (:249-271) and Doom/Madness party init in `BeforeLoadMap` (:272-301); Mode reset to 0 on main-menu actions
  124/132 (:302-306); bolster regulator relabelled with `MAWBOLSTER` names, range 0..250 step 50, default 50
  (:307-317); restore moved from `LoadMapScripts` to `BeforeLoadMap` and restores `Mode` (:354-371).
- **General/MenuChooseCharacter.lua** (37 changed lines). Deletes the FreeSelection toggle button and its tooltip;
  `ClassAvailable` ignores race/continent (only base unpromoted class) (:170-183); every portrait with a race is
  `AvailableAtStart` (:424). The per-continent tables from `Character selection.txt` are still loaded but unused.
- **General/AdaptiveMonstersStats.lua** (in scope only for UI): settings page renamed "MAW SETTINGS", built on
  `MultiplayerInitialized` with multiplayer UI utils, numeric bolster-multiplier rows commented (:432-455); local
  SimpleText/CustomNumeric helpers deleted. Remaining diffs are monster math (out of scope).

### Hooks / core / init
- **General/zMaw-hooks.lua** (new). `MonsterSpriteScale` event via 4 autohooks (bigger bosses) (:2-36, with
  signed/unsigned pointer fix :3-17); strafe = half forward speed regardless of run, x2 running, x4 flying-running
  (:39-95, gated by `fasterStrafing`); slower backpedal (:127-163, `slowerBackpedaling`); an unused "faster
  backpedal" block under `if false` (:100-125); replaces the melee hit roll at 0x4256DB with
  `MawCore.Formulas.mawPlayerHitChance` + `PlayerHitOrMiss` event (:176-197); temple UI divide-by-zero guard at
  0x4b5d84 (:199-206); UI message-loop register guard at 0x4331aa restoring ebx/esi/edi and logging (:208-229).
- **General/zz_Maw-initialize.lua** (new). MAWSettings.lua loader (§2.2); `Game.PatchOptions.FixMonstersBlockingShots`
  (:303); `isRedone` detection = "MM7 Redone/Community" item table (`ItemsTxt[1466].Name=="Emerald Island"`)
  (:305-308); global helpers `round`, `shortenNumber` (K/M/B colour), `RunNextTick`, `GetMaxHP` (MAW HP pool)
  (:314-458); MAW SETTINGS switches (:460-622); "inv+exit" double-action guard for action 168 (:625-641); O key
  (:643-663).
- **General/zzzzzMaw_Core.lua** (new): `require "MawCoreMain"; MawCore.start()` — five z's so all MawCore handlers
  register after legacy ones. MawCore = 20 ordered modules (Modules/MawCoreMain.lua:39-61); `vars.MawCore` is a
  "greenfield save" stamp (Modules/MawCore/Save.lua) for a planned clean break requiring a new game.
- **General/zzMaw-TownPortalClickFix.lua** (new): clears engine mouse-pressed byte 0x1006140 when the Town Portal window
  constructor runs (0x4D0FDC, signature-checked :11-14, hook :16-18). Fixes double-click casting auto-selecting the
  central town.
- **General/zSERIOUSMAW.lua** (new, 19 lines): writes boss names into `Game.PlaceMonTxt[200..205,304]` (Serpent
  Mother, Captain Sharp-Tooth, Captain Strong-Scale, Captain Finch, Mountain Man, Naga Empress, Huge Orc).
- **General/MiscTweaks.lua** (21 lines): comments out base unarmed-GM dodge (:599-606), MM7-style regeneration
  (:637-657) and meditation SP regen (:667-668) because MAW reimplements them; catalyst mixing now
  `max(T+M/2, T/2+M)` capped by alchemy skill*mastery/2 (:781-788); disables MM6 random map music (:791-823).
- **General/ExtraEvents.lua** (based on the older forus copy, not latest base): Space-bar pickup compares
  `obj.Index % 0x2000` because the engine object ref is 16-bit (index*8+kind) and maps exceed 8191 facets (:253-259);
  removes the base feature that temporarily overrides the caster's school skill for scripted spells with a preset
  skill (forus :809-897). Relative to latest base it also lacks `SkillBySpell` (Blaster 135 / Dragon breath 137 skill
  mapping), keeps `mov word` / `cmp edx, 32` / `spell_id > count` (latest base fixed these). Treat as a regression risk.
- **Scripts/Core/events.lua**: single line `if not slot then slot=0 end` in the HitPlayer handler (:2613) — crash
  guard for nil player slot.
- **Global/GLOBAL.lua** (new; no base file — base global behaviour lives in compiled global.evt + StdQuests*):
  quest gold reward bonus `gold*(1+partyLevel/100)+250*partyLevel` when a topic gave gold and XP (:1-75); action 405
  (training) level-display hack (:19-37); Insanity: trading quest items disables that NPC's topic (:38-50);
  **global teleport events** 2666 -> New Sorpigal, 1777 -> Harmondale (QBit 527) else Emerald Island, 1888 ->
  Ravenshore (QBit 93) else Dagger Wound (:77-96); removes and rewrites global events 181/203/212/234/244/246 (black
  potion reagent quests accept MM6/MM7/MM8 reagent id ranges, Galvinus QBit shift fix :250-290), 207/571-576 (Rust
  fire-resistance potion deliveries), 1442-1447 (MM7 circus pyramid/keg trades, capped at 10 per map) (:98-797);
  Doom removes NPCs 1109, 1165, 1166, the circus traders (:799-803).
- **Scripts/Structs/After/RemoveSkillValueLimits.lua**: skill value cap 0xFF -> 0x3FF, base 0x50 -> 0x1F4 (500),
  mastery bits via named constants, own `get_player_from_ptr` (diff vs base, 103 lines). Engine-limit workaround.
- **Scripts/Structs/RacialSkills.lua**: empty file — disables MMMerge racial skills (MAW has its own).
- **Scripts/Structs/extraEditableDescriptions.lua/.md** (new): new MMExt events `BuildMonsterInformationBox`,
  `BuildItemInformationBox`, editable skill mastery descriptions, `StrFormatGame` — engine extension to rewrite
  tooltip boxes.
- **Global/ExtraArtifacts.lua**: emptied on purpose (overrides base artifact system; logic moved to MAW files).
- **Global/zzzzzMaw_Damage.lua**: registers the MawCore damage pipelines per playthrough.

### NPCs / quests
- **General/NPCFollowers.lua** (14 lines): Doom mode refuses all hiring except in two houses (2DEvents 1466/1486)
  (:248-253) and renames hire topics (:490-497).
- **Global/NPCFollowersSkills.lua**: profession bonuses take the max instead of stacking (:46); init
  `vars.NPCFollowers` (:190).
- **General/NPCMercenaries.lua** (53 lines): mercenary class kinds per continent now include MAW classes in Enroth
  (:13-18); merc skill points follow MAW's per-level curve `4+floor(i/10+1)` (:196-199); Master-of-Elements index
  clamp (:252-253); generated merc items lose expiry and one of two enchant kinds (:349-356); `ClassStages`
  normalisation and manual `ClassTypesByContinent` respected; continent-check bugfix (:673-675); no default
  Knight/Cleric/Sorcerer fallback (:691-692); removal-by-kind fix (:716-717); **Beyond Madness disables the
  Adventurer's Inn mercenary system entirely** (:562, 586, 667, 728, 768).
- **Global/Quest_DragonHatchling.lua** (76 lines): feedback messages and days-left (:9-14,120-135); dialog redraw fix
  `RefreshTopics` (:15-22); grown dragon dismissed to the Adventurer's Inn and visible on all continents
  (`ContinentChange3`, :66-79) instead of being forced back into NPC followers; new "Release the dragon" topic with
  Y/N (:184-200).
- **Global/Quest_SavingGoobers.lua**: Philosopher's Stones needed 10 -> 1 (:472) and fixes `or/and` precedence so the
  loop stops at 0 (:482).
- **Global/zzMaw_DimensionalMapsQuest.lua** (new): "Dimensional Maps" topic on NPCs 314 (Oracle), 413 (Judge Grey,
  Harmondale) and 794 (The Seer); slot E on 314/413 but slot A on 794, which hides Pilgrimage; hands out map items (290)
  by party-level tier (100, +20 to 140, +15 to 200, +10 after; done at 500), seeded roll, reward level*1000 gold+XP when
  the rift is cleared (detected on LeaveMap with `mapvars.completed`).
- **Global/zzMAW_DruidCircletQuest.lua** (new): Dantillion (NPC 41, Murmurwoods) slot B, QBit 299, bring Druid Circlet
  of Power (638) from Druid Circle chest; 3000 gold, 10000 XP, identified MAW-rolled amulet.
- **Global/zzMaw_Mapping.lua** (misnamed; new): runtime effects of dimensional-map affixes 8 (status-effect
  resistance ignored), 25 (party movement drag near enemies), 26 (attack delay), 33 (buff power nerf; resets the
  global `buffPower` table otherwise).
- Related content outside the named list: **Global/zzMAWRespec.lua** (skill reset at NPCs 314/413/794, 1000 gold per
  level, masteries remembered in `vars.oldPlayerMasteries`), **Global/zzMAW_MoveTrainers.lua** (`evt.MoveNPC` of 21
  distinct trainer NPCs, 64 entries (43 moves, 21 restores) on 19 maps, when `enableAllTrainers`; NPCs listed on several
  maps follow the party; the guidebook PDF covers them only partly, §4.3), **Global/zzMAW_PotionQuests.lua** (removes
  duplicate StdQuestsFunctions handlers for events 181/203/212/234/246), **Global/zzMaw_Arena.lua** (wave arena at d42
  via NPC 313, rewards level*20000 gold, `vars.highestArenaWave`, multiplayer-aware), **General/zzMaw-Maps.lua**
  (dungeon completion keyed by file name, dungeon reset prompt; the dungeon-reset rewrite also drops the Hive lock
  (outa1 90) and sends Barrow VII to `mdr01.blv` (out11 505); dimensional-map item use teleports into a re-rolled
  dungeon with up to 4 affixes / 33 affix types, monster pools, barrel fixes, MM6 sprite restore, outdoor respawn
  tweaks), **General/BountyHunt.lua** (reward scales with party level; text names the map; uses free Map.Notes; Insanity
  shows other-map hunts), **General/ZombiePlayers.lua** (conditional zombie portraits for dragons/minotaurs/trolls and
  expression reset), **General/zzMaw-BookSwitches.lua** (clickable book switches in 7d12 and 7d37),
  **General/pseudoSpawnpoint.lua** (spawn helper used by map scripts).
- The quest side of **Global/GLOBAL.lua** (listed under Hooks above): potion quest rewards changed to MAW potion ids,
  Galvinus QBit fix, MM6/MM7 reagents accepted, Rust potions use item 249, circus trades capped at 10, Doom removes the
  circus traders, quest gold scaled by party level. Full spec: [MAPS_CONTENT.md](MAPS_CONTENT.md) §4.1.

### Maps (Scripts/Maps; a same-named file replaces base; a new file runs alongside the map's compiled .evt)

| File | Status | Change |
|---|---|---|
| 6d05 | new | Snergle door 9: the key requirement (2108) and the 18 guards summoned on opening are base behaviour; MAW drops the QBit 1051 lock and the key consumption, which makes the summons repeatable |
| 6d18 | new | MP lava mapvar not synced; lever 35 also toggles facet 2255 visibility |
| 7d06 | override | adds one-time pseudo-spawn of monster 397 (3 + 1 stronger) |
| 7d11 | new | opens doors 1/2 if MapVars 15-17 set (stuck-door fix) |
| 7d20 | new | rewritten Wine Rack (196) loot table |
| 7d21 | new | two scripted ambushes ("It's a trap!", "Queen Arrived!") with a boss |
| 7d24 | override | **drops base fixes** (throne room via QBit 647, Dwarf-king QBit 658 unstick); adds swarm ambush with 20 waves and a caster boss dropping item 405/410 |
| 7d29 | override | **drops base `Quest_CrossContinents.ContinentFinished[2]` hook**; adds "Goblin King" (PlaceMon 300) boss + adds once group 56 is dead |
| 7d32 | new | event 4 always opens door 7 (base required QBit 547) |
| 7d34 | override | event 151 toggling doors 1/2 is base; MAW removes its `Counter4` guard |
| 7d37 | override | adds one-time boss (monster 307, drops 171/174) |
| 7out01 | override | Redone only: Emerald Island tavern topics, wells 221/222 rewritten, "return to EI" invasion of ~130 monsters + Cristalyn. With non-Redone data (OpenYAMM's) the whole file is inert and the base no-Arcomage tavern filter is lost: a dropped base fix, not a MAW feature |
| 7out02 | override | **drops base Judge Grey 6-month death and Arbiter messenger logic**; adds goblin ambush, fort lieutenant (PlaceMon 301) with reinforcements, **teleporters 2666 "Enroth" (or Emerald Isle in survival) and 1888 "Jadame"**, Redone teleportal hub/key events 303-305 |
| 7out05 | override | Deyja night undead waves (22:00-04:00), Redone Erathia portal 505 |
| BrBase | override | multiplayer maze sync (level change/trap broadcast/locking); monster level filter commented (:426) |
| d05 | new | MP-friendly floor-trap timer and button 45 |
| d07 | override | wererat group 8 no longer made visible when hostile (one line commented) |
| d19 | override | rewritten door 15 / transformer 131: requires Dyson Leyland in party or NPC 11 hireling hack; **drops the base invisibility path, the Necromancer-alliance (QBit 19) path and the transformer relaxation** |
| d22 | new | MP brazier button visibility; dimensional-map runs (`mapvars.mapAffixes`) force hostile clerics and open door 452; also drops the Dyson Leyland requirement for the secret button and door 452 |
| d26 | new | Sarcophagus of Korbu pickup made once per game (`vars.sarcophagus`) |
| out01 | override | pirate respawn timer 463, capped at 25 waves in Insanity |
| out02 | override | MP Breach/Alvar travel broadcast; **teleporters 2666 "Enroth", 1777 "Antagarich"** |
| out03 | new | overdune-witness event 197 rewritten (alliance quest bits, 10000 XP, 4000 gold) then enters guild 773 |
| outb1, outb2, outc1, outc2, outc3, outd1, outd2, outd3, oute1, oute2, oute3 | override/new | MM6 stat/resist shrines (event 261) usable any month (the original `MonthIs` check removed; QBit 1230 still limits to one per month); outb1: the Kriegspire XP well (-5000 gold, +5000 XP) is base; MAW only exempts its XP from MAW's XP scaling and adds a monthly refill back to 10 uses |
| outb3 | override | event 92 to znwc: Doom "Access have been destroyed"; otherwise level 255 or difficulty <= MAW |
| oute3 | override | **teleporters 1777 "Antagarich", 1888 "Jadame"**; event 104 sends Doom players elsewhere in outb3; Redone Tarent Hovel door |
| pyramid | override | radiation damage timer 12: the Crystal Skull (2086) protection is base; MAW changes the damage elements (Magic → Earth) and checks the skull on the current member |
| znwc | new | potion vendor 61 rewritten; after 50 purchases the seller says "empty" but still sells |

The teleporter sites are bmodel copies in `Data/zMaw.games.lod` for out02 (Ravenshore) and 7out02 (Harmondale), and
decorations plus terrain, not faces, in oute3 (New Sorpigal) ([MAPS_CONTENT.md](MAPS_CONTENT.md) §2.2). README.md:242
calls them "teleporters conveniently placed in starting cities".

---------------------------------------------------------------------------------------------------------------------

## 4. Content and data assets

### 4.1 LODs

- **zMaw.games.lod** ("GameMMVI" header, `maps` dir, 24 entries): edited map files for 12 maps, each with its delta
  file: d12 Ogre Fortress, d18 Naga Vault, 7d33 Castle Gryphonheart, elemf Plane of Fire, oute3 New Sorpigal, out02
  Ravenshore, 7out02 Harmondale, d08 Dire Wolf Den, out05 Garrote Gorge, d04 Temple of Baa, mdt09 Wromthrax's Cave, d42
  Arena. Decompressed and compared with forus `mm6/7/8.games.lod`: none identical. Only out02 and 7out02 gain geometry
  (teleporter bmodel copies); oute3's teleporters are decorations plus terrain. Size drops are editor re-save
  (face-extra compaction, unused vertices, zero-vertex faces). 7d33, d04, mdt09 and out05 change only actors; d12, d18
  and elemf spawns; d42 face flags. No new maps. Full spec: [MAPS_CONTENT.md](MAPS_CONTENT.md) §2.
- **zMaw.T.lod** (MMVIII `language`, 9 text tables): class.txt (adds 12 class names: Seraphim/Angel/Archangel, Death
  Knight/Death Lord/Lich King, Shaman/Sekhem/Marabou, Elementalist/Elemental Adept/Master of Elements), ITEMS.txt,
  rnditems.txt, SPCITEMS.TXT, POTION.TXT, POTNOTES.TXT, MONSTERS.txt (out of scope), **mapstats.txt** (treasure level
  column set to 6 on 129 of 207 maps; Mon1/2/3 pictures, difficulty and counts changed on ~50 maps, e.g. MM6 Barrows,
  Silver Helm Outpost, Castle Darkmoor; one rename "The Abandoned Temple"), **Placemon.txt** (161 -> 1000 rows; rows
  162+ are numeric placeholders so scripts can assign boss names at runtime: an engine-table-size workaround).
- **zMaw.icons.lod** (3): `2hm`, `2hmace2`, `2hmace_indexed` (65x276 paperdoll two-hander art).
- **zVex.icons.lod** (85): `sb<school>1-4` + `sb<school>u` (9 schools, 74x56/64x60) = re-skinned spellbook *item*
  pictures used unless `disableSpellBookRework` (General/zzMaw-Spells.lua:3636-3660); `vCraft1-13` and `vCraft*Asc`
  crafting gems/materials (General/zzAlchemy.lua:1239); `vCelest1`, `vEternal1/2`, `vEye1`, `vHour1`, `vMirror` new
  item art; `zv01*/zv02*` weapon icons.
- **zMaw.sprites.lod** (1): `obj039` (128x128) replacement object sprite.
- The settings backgrounds `ExSetScr`, `ExSetScr2`, `ExtSetUp/Dw` are base MMMerge art (forus mmmerge.icons.lod);
  MAW does not relabel them, hence the "Bolster monsters" mismatch.

### 4.2 Data/Tables

- **SFT.txt**: scale changes for projectile `air07` (32768 -> 65536), explosions `earthX10` (884736 -> 65536),
  `mslX04`/`mslX05` (42598 -> 21299); `mcryst01-06` crystal frames gain light radius 150-300; 32 new frames
  `na1g..nd2g` (groups na/nb/nc/nd, 4 frames each, two scales 8192/24576).
- **ObjList.txt**: `Arrow` sprite name case fix; 44 new object types 700-743: 700-707 `nb1a..nd2o` using the new
  `n*` SFT groups (not referenced by scripts), 708-743 MM6-style projectile and impact objects (MindBlast, FireBolt,
  FireBall, Meteor, Cold, Blades, ElecBall, DarkBall, LightBall, EnchantedArrow, ...X impacts) used by the "M&M6
  Projectiles" setting (General/zzMaw-Monsters.lua:3810-3870).
- **Character portraits.txt**: race column fixes for conditional portraits 67-70 (Lich/Ghost dragon -> race 5,
  Minotaur lich/zombie -> 3), Zombie Troll 1 made available at start with class 56, **new portrait 77 "Lich Troll 1"**.
- **Complex item pictures.txt**: identical to the latest base MMMerge (`reference/mmmerge`). It differs from the older
  `mmerge_data_forus` copy, which OpenYAMM's `complex_item_pictures.txt` matches, by 1-pixel paperdoll offset fixes on
  ~25 armours (Erudine Chainmail, MM7 leather/chain/plate, Yoruba, Pellinore, Zeus...). Those are base MMMerge fixes,
  not MAW changes, and belong in the Standard tables.
- **House rules.txt**: two spellbook-shop quality tiers bumped (+1). Spells2.txt, Potion settings.txt and the Class/
  Race skill tables are out of scope (skills/alchemy).

### 4.3 Guidebook
- Shortcut PNG: see §1a.
- `new_trainer_location_24.10.pdf` (pdftotext): Enroth race-skill E/M/GM at Blades' End (New Sorpigal), Duelists'
  Edge (Free Haven), Paradise Valley tavern; Unarmed/Dodge/ID Monster/Regen E/M/GM at Buccaneers' Lair, Smugglers'
  Guild, Sparring Grounds; Alchemy E Castle Ironfist, M Free Haven, GM Castle Stromgard; Armsmaster Free Haven;
  Ascension E New Sorpigal/Castle Ironfist, M+GM Silver Cove. Antagarich: Regen E/M/GM temples of Harmondale/Erathia/
  Nighon; race skill E Tatalia temple, M Evenmorn tavern, GM Applied Instruction (Nighon); Ascension E Deyja/Bracada,
  M Nighon, GM Evenmorn. Jadame: Unarmed & Dodge E Ravenshore temple, M Garrote Gorge temple, GM Pirate's Rest
  (Regna); Ascension E Murmurwoods, M Shadowspire, GM Garrote Gorge. Only the racial, Dodging, Unarmed, ID Monster and
  Regeneration lines are implemented by Global/zzMAW_MoveTrainers.lua (data table :7-67) behind `enableAllTrainers`;
  the Alchemy, Armsmaster and Ascension lines are base teachers, and "Alchemy Master Free Haven" matches no NPC
  ([TRAINERS_SKILLS.md](TRAINERS_SKILLS.md) §1.4).

---------------------------------------------------------------------------------------------------------------------

## 5. Multiplayer and diagnostics

- **Scripts/Modules/Multiplayer/** (≈13.6k lines) is a vendored, partially patched copy of Rodril/Eksekk's MMMerge
  multiplayer branch (`Multiplayer.VERSION="30.09.2024/1"`, MultiplayerMain.lua:2). It is incomplete on its own
  (requires `SessionId.lua`, `UI.lua`, `UI/UtilsUI.lua`, `UI/Keybinds.lua`, `Network/Lobby.lua` from the branch
  install). UDP P2P with STUN/relay, lobby/server list, host = lowest client id, sync of monsters, objects, chests,
  shops, evt, rest screen, save/load/exit, spells, positions; turn-based disabled; max 2 players by default. MAW
  edits are small (MAW references in Spells.lua, Monsters/DamageReceived.lua, Players/Experience.lua).
- **General/zzMaw-Multiplayer.lua** ("Buff share - by Rafiki59"): shares MAW buff pool across clients by radius,
  conflict resolution, weak-condition guard, time sync, block spell 8 in MP.
- **General/zzzOnlineVariableSender.lua**: HP/mana snapshot diffs to the host, `SendHeal`, mapvars sharing,
  boss-data sync, and the "online QoL" Challenge Mode (always-open transport/shops, zero training time, NPC 1177
  topic change) while in a multiplayer session.
- **General/zzBossSync.lua**: host->client boss mapvars sync; defines the global `mawmapvarsend` used by many map
  scripts (map scripts therefore depend on a General file).
- MawCore `Sync.lua` declares the host-owned game state: vars `Mode, insanityMode, madnessMode, AusterityMode,
  trueNightmare, freeProgression, MAWSETTINGS, MMLVL, EXPBEFORE, LVLBEFORE, Randomizer*, ItemFound,
  MonsterShuffleList, highestArenaWave` and Game `Mode, BolsterAmount, freeProgression` (Modules/MawCore/Sync.lua:43-52).
- Characterisation: **separable from MAW gameplay**, but MAW has grown hard couplings: the MAW SETTINGS page,
  `mawmapvarsend` in map scripts, `Multiplayer.PUPPET_AITYPE` checks, BrBase/d05/d22/6d18/out02 MP hooks, arena
  events. For OpenYAMM single-player MAW, all of it can be dropped; only the list of difficulty keys (which must be
  host-authoritative) is a useful design note.
- **General/zzzMaw_CrashDiag.lua**: LuaJIT-ffi tick profiler/crash breadcrumb logger to `MawDiag.txt` (3 MB rotate,
  heartbeat 60 s, trail 512, records git HEAD of a dev checkout). Pure diagnostics for the Lua/x86 host; irrelevant
  to a native engine.

---------------------------------------------------------------------------------------------------------------------

## 6. How MAW is enabled today; save-game implications

- Enabled by installation only (file overlay; README.md:20-29: MMMerge, Rodril nightly, multiplayer branch, then
  MAW, in that order). No vars flag says "this is a MAW save". `vars.MawCore.version` (Modules/MawCore/Save.lua)
  marks the in-progress greenfield core; `isRedone` adapts to the MM7 "Redone" data set.
- Per-game ruleset flags in `vars`: `Mode` (0/2/8), `insanityMode`, `madnessMode`, `AusterityMode`,
  `DoomPartyNeedInit` (transient), `trueNightmare`, `freeProgression` (+ `storedMasteries`), `RandomizerMode` (+
  shuffle tables), `SuvivalMode` (dead), `ChallengeMode` (set only while in MP), `ExtraSettings` {UseMonsterBolster,
  BolsterAmount, ShowWeatherEffects, ImprovedPathfinding, freeProgression, Mode}, `MAWSETTINGS` {6 switches +
  buffRadius/blockSpells}, `MAWINITSETTINGS` (copy of the per-install file), `BolsterMultipliers`.
- Mode semantics found in code: Doom (Mode 2): BolsterAmount forced 600 (the "+4 monsters per group" rule in
  `SetMonsterDensity` only runs when the Randomizer builds its pool, zzzzMalekith-Randomizer.lua:119,285), hiring only
  in two houses, unidentified items not wearable, chests need lockpicking skill, identify/repair priced by skill^2,
  half monster loot, stronger starting items, znwc locked, Doom skill costs, NPCs 1109/1165/1166 removed.
  Insanity: Doom + harder learning requirements, food cap indoors, no dungeon reset/respawn (RefillDays 1e9),
  console locked, pirate wave cap. Beyond Madness: Insanity + level-1 reset, no free progression, no mercenaries,
  per-run death counter with anti-savescum timer. Austerity: no legendaries/shop specials, armour/shield AC rules,
  alchemy limits, respec grants Identify Monster GM. Nightmare (250) -> True Nightmare (300): no saving/Lloyd near
  enemies, food cost per save, monsters respawn if the dungeon is left early.
- Save size/compat: dozens of MAW top-level vars keys (~200 distinct `vars.`/`mapvars.` names across the tree),
  item fields reused for MAW data (map items pack affixes into Bonus/Bonus2/Charges/BonusExpireTime/MaxCharges),
  PlaceMon slots 162-999, per-map `mapvars.completed/completition/mapAffixes/MawMonsterHP`. MAW saves are not
  loadable as vanilla MMMerge saves in a meaningful way and vice versa; MAW's own roadmap already accepts a clean break.
- Implication for OpenYAMM: store the ruleset as one explicit, immutable-at-start record (ruleset id + mode +
  sub-flags + difficulty) in the save header so loaders, UI and tooltips can branch on it; keep difficulty changes
  (where allowed) as explicit save state, not derived from `Game.*` globals.

---------------------------------------------------------------------------------------------------------------------

## 7. Cheap, high-value improvements for a native re-implementation

### 7.1 One "New game ruleset" screen (replaces four scattered places)
- Ruleset: Vanilla MMMerge / MAW. Under MAW: **Mode** (Normal, Doom, Road to Insanity, Beyond Madness, Austerity),
  **Progression** (Free = bolster on continent change / Horizontal = fixed map levels), **Difficulty** (Easy..Hell,
  Nightmare with its irreversible rule spelled out in place, instead of a polled typed "yes"), **Randomizer**
  checkbox, and the six MAW SETTINGS switches. Each option gets a one-line description from the README (sections
  "Bolster & Difficulty", "Solo") and the code facts in §6, so players no longer need the Discord.
- Lock what MAW locks (Mode, Randomizer, True Nightmare, Madness) and show it read-only in an in-game "Ruleset"
  panel; allow the mutable ones (difficulty except locked tiers, progression, presentation toggles) in Settings.
- Fix the label: "Free progression" not "Bolster monsters"; difficulty names not percentages.
- Drop the dead Survival mode and the obsolete free-class toggle (selection is always free in MAW).

### 7.2 Hotkeys -> visible controls plus real keybinds
- Inventory toolbar: Sort bag, Sort party, Sort all bags, Sort party bags, "Alchemy owner" toggle, crafting-bag
  toggle, Upgrade gems (with a preview list instead of the two-press U prompt). Shops: a "Reroll stock (cost)"
  button. Spellbook: "Clear buffs" button; Tab cycling is fine as a keybind.
- Skills tab: Cover / Mana Shield / Elementalist rotation as checkboxes on the relevant skill rows with tooltips.
- Map: "Unstuck" in the Esc menu; corpse/material pull as a keybind with a HUD hint; solo-only Charge/potion keys as
  keybinds that appear only when the party has one member.
- Put all of them in the existing keybinding screen (no `MAWSettings.lua` key codes), resolving the R/G/E overloads
  per screen explicitly.
- Replace typed `Question()` yes/no prompts (Nightmare, dungeon reset, dragon release, respec, map-data reset) with
  button dialogs.

### 7.3 HUD and tooltips
- Map completion % and the Madness death timer/counter deserve proper HUD slots (they are free-floating text at fixed
  640x480 coordinates today); elementalist/assassin stacks as portrait badges.
- "Extra item tooltip" and Alt-to-compare can be a standard modifier with a visible hint line.

### 7.4 Things that exist only to work around the vanilla engine (do not port)
- 16-bit object refs vs >8191 facets (ExtraEvents.lua:253-259); 16-bit monster HP ledger (MawCore/MonsterHP.lua);
  skill caps 255 -> 1023 (Structs/After/RemoveSkillValueLimits.lua); PlaceMon placeholder rows 162-999 for runtime
  boss names (zMaw.T.lod Placemon.txt, zSERIOUSMAW.lua); register clobber guard in the UI loop and the temple
  divide-by-zero (zMaw-hooks.lua:199-229); Town Portal click-through (zzMaw-TownPortalClickFix.lua); signed/unsigned
  pointer fix in sprite-scale hooks; `inv+exit` double action guard (zz_Maw-initialize.lua:625-641); Arcomage button
  shove (zzMaw-MultiBag.lua:101-120); asm strafe/backpedal patches (movement speeds can be data);
  `FixMonstersBlockingShots`; the HitPlayer nil-slot guard (Core/events.lua:2613); CrashDiag; the hex-obfuscated
  strings and the console lock/tamper log (`vars.q1/r1/s1`) which exist because MMExtension exposes a Lua console.
- Hidden settings in a Lua file because MMExtension has no settings UI; registry-stored frame limit.
- Polling (`MawAddTimer("nightmare", 0.5)`, Tick-driven settings) instead of events on settings change.
- MAW overriding whole map scripts to add a few events: in OpenYAMM use explicit per-map overlays so base fixes are
  never lost (see the dropped fixes in 7out02, 7d24, 7d29, d19 and ExtraEvents.lua).

### 7.5 Content worth keeping as data
- Teleporters in New Sorpigal/Harmondale/Ravenshore (events 1777/1888/2666) — needs the out02/7out02 bmodel copies and
  the oute3 decorations, or an OpenYAMM-side decoration/event-face overlay instead of shipping edited ODMs.
- Trainer relocation table (zzMAW_MoveTrainers.lua) as a YAML overlay; MM6 shrines without month gate; Druid Circlet
  and Dimensional Maps quests; respec NPCs; arena waves; scripted ambushes/bosses (pseudoSpawnpoint calls) as
  map-local event overlays; class names; new portrait 77; paperdoll offset fixes (usable even outside MAW).
