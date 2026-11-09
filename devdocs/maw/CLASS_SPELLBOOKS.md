# MAW class spellbooks

Status (2026-11-09): **the class spellbook pages are built** (§7), presentation only; the user approved the mockup
with that condition. The other parts of §4 (names in the combat log and buff panel, effects) and the decisions of §6
are open.
Mockup: [study](../../level_generation/ui/maw_class_spellbooks_20261108/README.md), interactive preview
`level_generation/ui/maw_class_spellbooks_20261108/index.html` (also published as a private artifact,
https://claude.ai/artifact/NqYr2tJkMUEQxwScNAv7Nb).

The question (user, 2026-11-08): MAW's special classes reuse existing spells, icons and spellbook pages. Since
OpenYAMM is not bound by the original binary, should they get proper schools, spells and icons of their own, and what
would that touch?

## 1. Which classes have their own spells

Only two class lines. Seraphim, Shaman and Elementalist cast the ordinary spells of the ordinary schools (the
Elementalist learns its spells by casting instead of from books, CLASSES_SPELLS_SPEC §5.5). Dragon, Vampire and Dark
Elf already have racial pages of their own.

| Line | Classes (ids) | Schools (the skill underneath) | Spells |
|---|---|---|---|
| Death Knight | Death Knight, Death Lord, Lich King (56-58) | Frost (Water), Blood (Body), Unholy (Dark) | 12. Nine are Death Knight spells on reused spell ids: Icy Touch 26 (Ice Bolt), Frostbite 29 (Acid Burst), Ice Bomb 32 (Ice Blast), Blood Leech 68 (Heal), Asphyxiate 76 (Flying Fist), Superior Blood Leech 74 (Cure Disease), Death Coil 90 (Toxic Cloud), Death Grasp 96 (Dark Grasp), Death Breath 97 (Dragon Breath). Three are the ordinary spells: Water Walk, Regeneration, Vampiric Aura |
| Assassin (reworked Thief line) | Thief, Rogue, Assassin, Spy (34-37) | Combat (Fire), Subtlety (Air), Poisons (Water), Assassination (Earth) | 21. Eight attack spells that deal a share of a melee blow (Fireball, Fire Spike, Chain Lightning, Poison Spray, Acid Burst, Stun, Blades, Mass Distortion); thirteen ordinary spells (Torch Light, Fire Aura, Haste, Wizard Eye, Shield, Jump, Fly, Invisibility, Water Walk, Town Portal, Lloyd's Beacon, Stone Skin, Telekinesis) |

The lists, costs and mastery gates are in `game/rules/maw/MawClassSpells.cpp`; the school renames
(`mawClassSchoolName`) show on the skills screen, the spell renames (`MawSpellRules::spellName`) in tooltips.

## 2. Where the original spells still show

- **Spellbook**: a Death Knight opens the original Water page, with "WATER" painted on the medallion; Icy Touch is
  drawn with the Ice Bolt picture, Death Coil with Toxic Cloud's. Pages are fixed 640×480 paintings and each spell's
  picture sits at a fixed position (`assets_dev/engine/ui/gameplay/spellbook.yml`, `game/ui/SpellbookUiLayout.cpp`).
  The tabs are those of the schools the member has, at their fixed slots (`GameplayPartyOverlayRenderer.cpp:5880`,
  `GameplayScreenRuntime::activeMemberHasSpellbookSchool`), so a Death Knight's three tabs have gaps between them.
- **Combat log and statistics**: `combatLogSpellName` and `englishSpellName`
  (`game/gameplay/GameplayCombatController.cpp:335-348`) read the spell table's name, so the log says "Ice Bolt" for
  Icy Touch and the statistics count it as Ice Bolt. The buff panel does the same (`GameplayBuffHud.cpp:87`). The
  journal's aura page already goes through `SpellRules::spellName`.
- **Spell effects**: the projectile visual is chosen by spell id in code (`game/fx/ParticleRecipes.cpp`). Death Coil
  flies as a Toxic Cloud, Asphyxiate as a Flying Fist, the Assassin's Fireball as a mage's Fireball.

## 3. Rejected: real new skills and spell ids

Frost, Blood, Unholy, Combat, Subtlety, Poisons and Assassination as real skills, plus new spell ids from 133:

- Skills: a column for each in the class skill table for all classes, trainers that teach them, skill descriptions,
  race bonuses, respec, starting skills, test parties. Items with "+Water Magic" would stop raising Frost unless a
  mapping table translated them, which is the adapter layer AGENTS.md rules out. Dozens of MAW rules look the school
  skills up by name (Blood's leech and physical cut, Unholy's magic cut, Frost's attack speed, Assassin energy, the
  Assassination bonus).
- Spell ids: the spell system's 219 per-spell cases (`PartySpellSystem.cpp`) and the effect mapping would need a
  redirect; quick spells in saves need a migration (MAW is released).
- Upstream sync: MAW's Lua names spells 26, 29, ... and the Water, Body and Dark skills, so every port from MAW would
  need translating ([UPSTREAM_SYNC_8fbb48d1.md](UPSTREAM_SYNC_8fbb48d1.md) shows how often that happens).

The rules would play exactly the same; the gain would be only what the player sees.

## 4. Proposal: the class's own presentation over unchanged rules

Skills, spell ids, rules, saves and tables stay as they are. The two class lines get their own spellbook pages,
pictures, names and later effects, defined in ruleset data, and only in MAW. The user's condition (2026-11-08): no
regressions anywhere else; do it only where it is cheap with the existing architecture.

1. **Data**: `assets_dev/engine/rulesets/maw/data/class_spellbooks.yml`. Per class line, its pages; per page the
   skill (Frost is Water Magic), the shown name, page art and tab art; per spell the id, name, picture (normal and
   highlighted), slot and later an effect key. The names now hard-coded in `MawClassSpells.cpp` move here; costs and
   damage stay in code.
2. **Pages per character**: a `SpellRules` hook returns a character's page list. Standard returns none and the
   spellbook keeps today's code path, so Standard and every class without a class book are untouched. MAW returns the
   class pages for these two lines only. The renderer and the input controller
   (`GameplayPartyOverlayInputController.cpp`) both take the list; tabs stack from the top. Layouts for 4, 5 and 6
   spells (Subtlety has six), spells in mastery order.
3. **One name everywhere**: the combat log, statistics and buff panel go through `SpellRules::spellName(caster, ...)`,
   which returns the table's name in Standard. Item tooltips may add the school name for these classes ("Water Magic
   (Frost)"); trainer dialogue the same. To decide: MAW statistics would count "Icy Touch" separately from records
   saved earlier as "Ice Bolt".
4. **Art**: runtime copies at x2 of the study's pages, tabs and pictures. Check that the ruleset package
   (mounted at `/engine/rulesets/maw`) can carry icons; otherwise `engine/icons_x2/` with a `maw_` prefix.
5. **Effects (later, optional)**: class spells carry an effect key looked up in `engine/effects/projectiles.yml`, with
   new effects from `tools/fx/generate_projectile_effects.py` (Death Coil, Asphyxiate, Death Breath, the Assassin's
   bombs and blades).

Checks: a unit test that Standard returns no class pages and that MAW gives a Death Knight its three pages and an
Assassin its four; the class-aware name in a combat log line; a native capture of both books.

## 5. The mockup (2026-11-08)

Made with Codex image generation in the style of the original book (no paid API calls); details in the
[study README](../../level_generation/ui/maw_class_spellbooks_20261108/README.md).

- Seven school pages: the original page with a new medallion scene and the school's name lettered on the banner.
- Seven school tabs: line-drawn when idle, painted when open.
- Twenty new spell pictures: the twelve Death Knight spells and the Assassin's eight attack spells. Codex paints the
  highlighted (colour) state; the normal (sepia) state is derived from it. The Assassin's thirteen ordinary spells
  keep their original pictures.
- A "Today" view of the current book for comparison.

## 6. Open decisions

- **Assassin attack spell names.** The mockup proposes our own (not World of Warcraft's) and MAW keeps the mage names:

  | Id | MAW | Proposed |
  |---|---|---|
  | 6 | Fireball | Firebomb |
  | 7 | Fire Spike | Blasting Trap |
  | 18 | Chain Lightning | Ricochet Blade |
  | 24 | Poison Spray | Poison Darts |
  | 29 | Acid Burst | Acid Flask |
  | 34 | Stun | Sap |
  | 39 | Blades | Throwing Blades |
  | 44 | Mass Distortion | Death Mark |

- **The Death Knight's borrowed spells** (Water Walk, Regeneration, Vampiric Aura): the mockup keeps their names and
  only redraws their pictures, to stay matched with MAW.
- **New spells** to fill the Death Knight's four-spell schools: a balance change away from MAW; kept separate.
- **Elementalist (optional)**: show its locked spells dimmed, with the casting progress each needs.
- **The art**: approval of the pictures, medallions and tabs, or which to repaint.

## 7. Built (2026-11-09)

The user approved the mockup on the condition that it changes only the presentation: no spell handling, no other
engine behaviour, nothing outside these two class lines.

- `SpellRules::spellbookSkin(member)` (`game/rules/SpellbookSkin.h`): Standard returns none, so the spellbook runs its
  existing code path for Standard and every other class. `MawSpellRules` returns `mawClassSpellbookSkin`
  (`MawClassSpells.cpp`): per page the school's first spell id, page and tab art, and each spell's pictures and place
  in the 640 x 480 book. The table is written by the study's `scripts/install_runtime.py` from its layout.
- The spellbook's drawing (`GameplayPartyOverlayRenderer::renderSpellbookOverlay`), clicks and right-click menu
  (`GameplayPartyOverlayInputController`) and hover tooltip (`GameplayHudOverlaySupport`) use the class pictures and
  places when a class look is active. The schools, which spells are known, selection, casting, quick spells and the
  Tab key are unchanged. Helpers: `activeSpellbookSkin`, `activeSpellbookSkinPage`, `spellbookSkinTabs` (class tabs
  stacked from the top, then any other school the member has, such as a racial page, with its standard art) and
  `spellbookSkinScreenRect` (`game/ui/SpellbookUiLayout`).
- Art: 61 PNGs at x2 in `assets_dev/engine/icons_x2/` (`maw_sbdk*`, `maw_sbas*`, `maw_stdk*`, `maw_stas*`), as MAW's
  other images there. The Assassin's ordinary spells use their original pictures.
- Names unchanged: the Assassin attack spells keep MAW's names (§6); the combat log, statistics and buff panel are
  untouched.
- Test: `MawClassTests` "MAW Death Knights and Assassins have their own spellbook pages and nobody else does"
  (Standard and other classes get none, every class spell has exactly one picture inside the book, every file
  exists, tab stacking).
