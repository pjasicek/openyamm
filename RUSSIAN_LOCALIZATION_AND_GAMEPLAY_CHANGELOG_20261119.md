# Russian localization and gameplay changes, October–November 2026

This record covers the localization effort beginning on 19 October 2026 and the gameplay,
content and tooling fixes made during playtesting through 19 November 2026. It was assembled
from the available Codex chat history, existing commits, the working-tree diff and retained
audit/repair records. Earlier commits remain intact; the accompanying commit records the
pending work after `864b9168f`, together with this cumulative account.

## Delivery history

| Period | Work already recorded in Git |
| --- | --- |
| 19 October | UTF-8 and Russian localization foundation; character progression; spell, equipment and item names/descriptions; initial MM8 dialogue. |
| 20 October | NPC greetings, gameplay events and remaining UI; MM8 dialogue, journal, alchemy and history. |
| 21 October | Remaining dialogue and character text; journal proofreading; scrolls, transitions and alchemy tables; professions, random names and MM7 history. |
| 24 October | Cyrillic font advances, Russian character tooltips and UI fitting; spellbook double-click; animated gauntlet cursor while holding items. |
| 26 October | Player map pins and UTF-8 labels with save persistence; further localization, dialogue fitting, asset lookup and gameplay fixes. |
| 31 October | Shared mechanics, persistence, MM6 event repairs and another localization pass. |
| This checkpoint | Remaining October–November playtest fixes, localization audits, map/event repairs, water depth, storage and lighting repairs described below. |

Key existing commits are `5f435bb76`, `185d4058b`, `4aa4e940c`, `9db3a73bd` and
`864b9168f`. This checkpoint does not squash or reapply them.

## Localization architecture and translation workflow

- Russian UI and runtime phrases live in `assets_dev/engine/localization/ru/ui.yml`,
  `gameplay.yml` and `events.yml`. Entries map complete English source strings to Russian
  text; templates retain named placeholders for values supplied by gameplay.
- Localized gameplay tables live in `assets_dev/engine/data_tables/ru/`. Full TXT tables
  and keyed `.overlay.yml` files supply translated names, descriptions, dialogue and journal
  entries while retaining authoritative gameplay records.
- English source literals remain in C++ where used as localization keys. The translation
  itself is data, loaded through the shared catalog. Changing a translated entry does not
  require recompiling C++, although runtime asset packages must contain the updated files.
- Added and repaired localization call sites for tooltips, context actions, house/map names,
  dialogue titles, input prompts, inventory details, recruitment and event messages.
- Registered original map names against localized table names so map-event hints and
  transition captions can reuse the same translations.
- Used English game tables, legacy event intent and existing Russian terminology to review
  translations. Some earlier translation batches used DeepL; later passes corrected meaning,
  terminology, grammatical agreement and playable puzzle clues against the game data.
- Kept event-specific fixes in explicit supplements/overlays rather than modifying generated
  legacy EVT Lua. Control Center overlays now supply UTF-8 punctuation matching catalog keys
  for three terminal messages whose legacy CP1252 text prevented exact lookup.

## Translation coverage and editorial corrections

- Covered character stats, skills, mastery ranks, classes, promotions, equipment, spells,
  enchantments, potions, recipes, NPC professions/names, greetings, dialogue, news, quests,
  awards, autonotes, history, travel, house names and interaction captions.
- Standardized recurring Russian attribute and combat terms, including Personality,
  Accuracy, petrification, resistances and Ancient Weapons. Corrected misleading item and
  enchantment descriptions, including Medusa's Mirror and ranged-damage protection.
- Reviewed promotion and story dialogue, including Verdant, Judge Sleen, the MM7 advisors,
  William Setag and the dwarf-rescue reward. Corrected pronouns, who receives respect or
  rewards, literal mistranslations and inconsistent class names.
- Clarified Genie Lamp reward messages, travel-day/price templates and full Ancient Weapons
  inspection text. Added translations for special dungeon objects and previously missed
  entrance/exit labels, including Emerald Island, the Hive, VARN, the Oracle, the Control
  Center, Darkmoor, the Shadow Guild and other MM6–MM8 locations.
- The retained dungeon audit covers 161 BLV maps: 51 MM6, 63 MM7 and 47 MM8. That pass added
  148 catalog entries and corrected 42 table strings. Its checked static captions/messages
  had no remaining gaps. This is scoped coverage, not a claim that every possible dynamic
  phrase or literary issue in the game has been exhaustively verified.
- A subsequent transition pass checked 204 MM7/MM8 dungeon transitions and filled 66 missing
  Russian captions. Incorrect transition-description IDs were tracked and repaired separately.
- Added a reusable source/data audit tool and retained the detailed dungeon and puzzle audits
  at the repository root.

## Riddles, text input and encoded clues

- Input prompts count and edit UTF-8 characters instead of bytes. Backspace and the maximum
  answer length no longer corrupt or prematurely truncate Cyrillic input.
- Shared answer matching accepts the original English answer and its localized counterpart,
  ignores case for Latin/Cyrillic letters and trims surrounding whitespace. Empty input does
  not count as an answer; existing event branches and rewards remain authoritative.
- Added Russian alternatives to the four MM6 password-door riddles and the Kriegspire
  yes/no exchange, retaining English answers.
- Reworked all three Escaton riddles, their hints, answer topics, scroll and journal states.
  Russian answers now match the corrected questions.
- Made the MM7 Wave Scroll, its keyword and encrypted scroll form a solvable Russian puzzle.
  The cipher uses the 33-letter Russian alphabet, including yo, with matching textbook rules
  and a reversible worked example. The decoded button order matches map events.
- Translated MM7 and MM8 obelisk fragments while preserving their respective column-reading
  and sequential-concatenation schemes. Corrected the relevant journal/catalog entries together.

## Interface and inventory interaction

- Fixed excessive spacing between Cyrillic glyphs and connected translated character-creation
  headings. Expanded Settings controls and adjusted status text to fit Russian labels.
- Fitted long dialogue topics and titles, including unbroken words, to their allocated panels.
  Earlier changes also fitted transition descriptions around their buttons.
- Character skill names and numeric levels now share one fitted Lucida size across all four
  skill groups. Fitting includes all skills/masteries so switching characters does not change
  text size according to the selected character's learned subset. Adjusted the armor heading.
- Generalized the spellbook double-click gesture to usable inventory items: drinkable potions,
  horseshoes, Genie Lamps, spell/message scrolls, the Deck of Fate, apples and Tobersk fruit.
  Application targets the inspected character and preserves the normal spell-targeting path.
- Letters and recipes opened by double-click remain readable until dismissal. Unconsumed items
  return to their original inventory cells. Movement, timeout, member changes and touch dragging
  cancel the pending gesture.
- Genie Lamps are recognized by canonical item ID, independently of localized names. A held
  lamp can be applied to a portrait instead of being treated only as an inventory transfer.
- Apples and fruit also use explicit item IDs rather than English name matching.
- Earlier checkpoints added F5/F9 quicksave/quickload, auto-run, 24-hour clock presentation,
  editable map pins and persistent labels. The release settings template now includes `auto_run=T`.
- Corrected journal map-background selection and hidden character-tooltip handling while using
  other overlays. Kept the established shared Obsidian UI geometry and interaction model.

## Items, rewards and shared gameplay

- Gold recognition uses the merged item table's Gold category instead of the MM8-only ID range.
  Gold from chests, corpses, containers and outdoor placements retains its amount and goes to
  the party wallet. Old outdoor snapshots recover lost gold metadata only when an unambiguous
  matching authored placement exists.
- Item names obey the actual identification requirement. Equipment checks Might/Accuracy only
  when that item declares a positive requirement, so a negative stat does not reject unrestricted gear.
- Added a base `item_effects.txt` contribution for the Villain's Blade's vampiric effect.
- Restored Clanker's Amulet's +15 effective Alchemy bonus and made both the bench and manual
  mixing use equipment bonuses without increasing learned mastery.
- Restored Sun/Moon Cloak bonuses: half the learned Light/Dark Magic rank, rounded down,
  while the cloak is equipped and intact. Updated English and Russian descriptions together.
- Implemented permanent Dragon Slaying enchantment from the Slaying Potion on eligible ordinary,
  intact, otherwise unenchanted weapons. Rejected targets do not consume the potion.
- Earlier fixes moved known alchemy recipes from map state to party state and migrated surviving
  old-save records; map changes no longer clear the learned recipe library.
- Earlier shared fixes addressed healing versus death, recovery during paused targeting,
  spell/projectile behavior, rest/conditions, arena rewards and MM6 movement/event behavior.
  Ordinary healing does not replace resurrection; completed rest wakes sleeping members without
  silently curing unrelated permanent conditions.
- Bound the class-resource multiplier table to its owning GameSession and clear that binding on
  teardown. This fixes the reproduced dangling-table access between sequential sessions/tests.

## Dialogue, lodging and progression

- Centralized pending inn-rest execution in shared gameplay so paid lodging works indoors and
  outdoors. The dialog closes before the normal rest screen starts; normal inns finish at 06:00,
  with the existing additional delay for the three designated night-oriented inns.
- Fixed Arcomage action handling to retain changes to the real party instead of losing the
  first-win gold reward in a temporary state copy.
- Added data-driven free lodging for the Harmondale throne-room butler. His dialogue invokes
  normal inn rest without charging gold or consuming food.
- The MM7 Ancient Weapons lesson checks each member independently and only teaches members
  who lack the skill. Repeated conversations preserve existing ranks and mastery.
- The lich ritual requires one personal soul jar for every active party member before it consumes
  jars or completes the quest. Four-member and five-member parties are both supported; spare jars
  remain. Successful wizard promotion uses the lich portrait/voice transformation.
- Added a fifth jar to the Walls of Mist chest and an explicit one-time migration for old chest
  snapshots, including already materialized inventories, without refilling other looted contents.
- Corrected Alice Hargreaves' greeting selection for kidnapping versus rescue while preserving
  repeat-greeting progression. Exposed the current NPC greeting to the Lua event API.
- Repaired Don Quixote follower visibility for affected older Erathia snapshots.

## World interaction, geometry and water

- Outdoor interaction excludes hint-only events from activatable face candidates. Decorative
  facade hints no longer intercept use of an aimed shop/guild door. Keyboard use tries a valid
  aimed target before the nearby-object search and respects effective saved face attributes.
- Reset cached world-space picking triangles when a model instance slot is reused, preventing
  displaced hit tests for loot bags and other models.
- Horizontal ceiling portals can define indoor sectors over open pits without becoming solid
  floors. This restores walking/falling into the Shadow Guild spike pit.
- Clamp sloped ceiling sampling to the face's real vertical bounds so edge tolerance does not
  invent a collision above a boat's high edge.
- Repaired the three Castle Gloaming boat decks/slopes and the lava collision beneath them.
  Added an explicit old-save face-attribute migration so standing on a boat no longer burns the
  party and the dock can be reached on foot.
- Added CPU water-depth data shared with terrain configuration and rendering. Outdoor movement,
  drowning classification and pathfinding distinguish shallow wading water from deep water;
  the wading threshold is 96 native units. Water Walk retains surface support. Data loads for
  headless gameplay too, independently of renderer initialization.
- Split terrain-material configuration from GPU material ownership so physics uses the same
  shore/seabed parameters as the visible terrain rather than a separate visual-only estimate.

## Map-local content and repairs

- New Sorpigal now has two permanent storage containers behind the tavern, with a native-style
  sign whose unreadable painted marks are interpreted through the normal Storage hint.
  Storage retains chest IDs 2/3, preserving deposited items in existing saves.
- Restored ordinary map-refill behavior to the two bridge containers toward Castle Ironfist;
  they use chest IDs 0/19. Other chest refill policies remain unchanged.
- Added explicit storage events/metadata, authored geometry, placement/check tooling and a
  persistence scenario. Ordinary aimed interaction was checked after direct event invocation
  alone proved insufficient to validate opening the new containers.
- Moved the unreachable Paradise Valley chest inside the playable map while preserving contents
  and opening behavior. Paired the ODM repair with a focused lighting merge.
- Corrected MM6's Supreme Temple of Baa earth-shrine reward to permanent Earth Resistance.
  Restored the Free Haven sewer bed hint without changing the rescue condition.
- Standardized 63 magic-guild halls across MM6/MM7/MM8 by school and actual spellbook stock
  tier. Updated shared names, presentation records and entrance/sign hints on 28 maps.
- Repaired Bracada's shared/mislabeled teleport plates: separated Temple of Light and Shops,
  retained return routes, and named the Celeste Gate and Random Teleporter plates.
- Restricted the Tularean Forest Clanker event to its intended archways instead of the whole
  tower. Added MM7 seasonal-tree overlays.
- Corrected merged transition records for the Lincoln, Grand Temple of the Moon, Thunderfist
  Mountain, Eeofol tunnels and adjacent Nighon tunnels, restoring the appropriate description
  and, where applicable, transition-video selection.

## Lighting assets and production tools

- Fixed coincident oriented surfaces in the outdoor bake producer by sharing charts when
  geometry and texture sampling match, preserving native face/receiver identities.
- Removed a partial overlapping wall at Harmondale's bell tower and an overlapping dock
  triangle in Tularean Forest. Retained geometry IDs and verified that no holes were introduced.
- Installed matching ODM/lighting/recipe revisions for those repairs. Numerical samples on the
  remaining bell-tower sill and repaired dock no longer contain the original black samples.
- Added a focused Hidden Tomb light repair with authored live point lights and receivers for
  the initially hidden passage, retaining existing sun/sky pages. Paired-source outdoor surfaces
  now receive those point lights at runtime, including at night.
- Extended bake tooling for cooked runtime materials, helper-interpreter selection and explicit
  source dependency resolution. Kept focused repair tools and their production notes.
- Baked the revised New Sorpigal storage geometry and installed its matching recipe/lighting.
- At this checkpoint, regenerated Bracada's lighting with its existing 64-sample profile in
  Blender 5.3 CPU after the mandatory check found its edited scene dependency stale. Installed
  the new lighting/recipe pair; the repository-wide check now reports zero stale outdoor bakes.

## Validation and limits

Checks repeated for this checkpoint, without compiling or rebuilding the game:

- Existing Windows unit executable: 68 selected tests, 4,852 assertions, all passed. Selection
  covers localization, item double-click/use, Genie Lamps, alchemy, gold, water depth, class-table
  lifetime, Ancient Weapons, greetings, boats and lodging. The executable predates some latest
  source edits, so this does not certify every committed C++ change as freshly compiled.
- Nine lighting geometry/compression tests passed.
- Syntax parsing passed for all 12 changed/new Python tools.
- Parsed all 32 changed/new YAML and JSON files successfully.
- New Sorpigal placement/persistence bindings passed the producer's `--check` validation.
- The existing Windows executable's Bracada headless map-load command exited successfully.
- Git whitespace checking passed with CRLF and structural TXT trailing columns allowed.
- Mandatory lighting dependency check: zero stale outdoor bakes after the Bracada rebake.

Earlier chats record authorized Windows Release builds, focused unit/headless runs and native
visual checks for individual fixes. In particular, a later boat-fix run reported 1,763 passing
tests and 17 skipped, and all three boats were exited on foot. Earlier runs also exposed an
intermittent runtime-suite access violation: the reproduced stale class-table pointer was
fixed, but one combined CTest run still failed while the separate runtime run passed. This
checkpoint does not claim that intermittent failure has been conclusively eliminated.

Source/data audits do not replace complete gameplay or visual acceptance. Bracada's refreshed
bake has not received a new desktop visual review at this checkpoint. Historical save edits
used for user-requested recovery/testing, backups, screenshots, logs, build outputs and bake
intermediates remain local and are not included as game source changes.

No game/Vulkan build, branch switch, push or history rewrite is part of this checkpoint.
The development settings retain the current MM6 start-world selection.
