# Localization

Showing OpenYAMM in other languages. Status (2026-11-08): the runtime, the tool, every text hook, the release
language packs and seven languages (cs, de, es, fr, pl, ru by import plus Claude drafts; zh-cn by its translator) are
done and committed; review of the drafts, a few new texts and a visual pass are next ([Status](#status)).

This is our own design and code. Two outside proposals were reviewed (PR #25 with a Russian translation, and a patch
series from Discord, `text-tables-and-language-packs.mbox`); we take ideas and content from them where listed under
[What we take from the proposals](#what-we-take-from-the-proposals), not their mechanisms.

## Requirements

1. **English never breaks.** The English game runs exactly as it does without localization, and nothing a language
   pack contains can break it.
2. **Updates are easy.** One tool, run by hand before a release, scans every text source and lists what is new,
   changed or missing in each language, with file and line.
3. **No heavy dependencies.** No ICU, libintl, Fluent or similar; our own small loader, and a Python tool that needs
   only PyYAML like the other repository tools.
4. **Development is not slowed down.** Adding content (scripts, tables, layouts, features) needs no translation
   bookkeeping. Keeping 100% coverage is a release-time task, not a per-change task.

## Core idea

**The English text is the key, and text is translated only when it is shown.**

Developers keep writing English as today. A language's translation files map English text to the translated text.
A missing translation shows the English. There are no key names to invent and no table to register a new text in.

This is the gettext model. We use gettext's `.po` file format (translators get Poedit and Weblate for free, with
review flags and source references), but not the gettext library: the loader is ours.

## Rules

### English is the identity, translation is display only

Saves, scripts, lookups and comparisons keep using English names: `className == "Knight"` (`game/party/Party.cpp`),
`SpellTable::findByName`, `quickSpellName` stored in saves, NPC and chest lookups by name. Translation happens only
on the way to the screen. A translated text is never stored, compared or used to look anything up. Data tables are
never replaced by translated copies, so table edits and ruleset patches can never be undone by a stale translation.

### With no language selected, nothing runs

`tr()` and the display hooks return their input unchanged (placeholder formatting still happens, through the same
code English already uses). English has no translation file.

### A missing or stale translation shows English

When an English text changes, its old translation no longer matches and the new English shows until the translation
is updated. The game never shows a key, a placeholder name or an empty text in its place.

### A bad translation entry is rejected at load

An entry whose translation drops, adds or renames a placeholder (`{item}`), a story code (`%01`–`%34`), a colour
code or a printf value is refused, logged once, and English is used for it. A malformed file is logged and left out;
the language's other files still load. Nothing in a pack can garble or crash the game.

### Text is never assembled from translated pieces

A sentence is one entry with named placeholders, so a translation can reorder it: `"Sold {item} for {price} gold."`,
never `"Sold " + item + " for " + price + " gold."`. A word that depends on a number uses the plural form.

## Text sources and where each is translated

| Source | Translated at | Context | Cost to developers |
|---|---|---|---|
| Lua event scripts: generated MM6–MM8, MM9, custom worlds | The `evt` bindings: `luaStatusText`, `luaSimpleMessage`, `luaQuestion`, `luaSetMessage` and the other text-taking ones in `game/events/EventRuntime.cpp`; house and target names from `SetMapMetadata` | the map (`map:oute3`), then none | none for whole sentences; `tr()` for joined ones ([Lua text](#lua-text)) |
| Data tables: items, spells, skills, classes, races, stats, monsters, NPC text, greetings, news, topics, quests, autonotes, history, awards, books and scrolls, potion notes, transport, merchant lines | Where the UI shows the text: `localize(entry.name)`; the tables keep only English (not built yet) | none by default; the world's | none |
| Ruleset texts (MAW `texts.yml`, `ruleset.yml` names and descriptions) | The ruleset text loader | `ruleset:<id>` | none |
| UI layout YAML, settings catalogue | The layout loader, for labels and option names | `ui`, then the element id for a control too narrow for the usual translation | none |
| World presentation (`world.yml` names, cinematic subtitles, certificates) | Their loaders | the world (`world:mm7`) | none |
| MM9 dialogue and journal (`worlds/mm9/dialogue/rude/*.rude`, `worlds/mm9/journal/JOURNAL.txt`) | Their loaders | `world:mm9`, then the file | none |
| Engine data YAML with display text (`character_selection.yml`, `teacher_ledger.yml` and similar) | Their loaders | the file | none |
| C++ code | `tr()` at the place the text is written | optional explicit context | write `tr("...")` |

Event scripts keep their English literals. The Lua exporter does not change, and generated files are not touched.
Text the original tables hold as Windows-1252 bytes is converted to UTF-8 before lookup.

### Lua text

An `evt` binding looks up the whole text it receives, so a script that passes one complete English sentence needs
nothing (nearly all generated calls). Two cases need care, mostly in hand-written scripts (MM9, MAW,
`event_support.lua`):

- **Sentences joined in Lua** (`"Contestant from the " .. side`, about 37 calls at the time of writing) match no
  entry and show in English. They use the Lua `tr` with named placeholders, as in C++:
  `evt.StatusText(tr("Contestant from the {side}", {side = side}))`. The binding's own lookup of an already
  translated text finds nothing and passes it through, so nothing is translated twice.
- **Text held in a variable or table** before the call works at runtime, but `extract` only sees literals passed
  directly to `evt` functions. The extractor also collects sentence-like string literals of event files; the
  missing-text log and `qps` catch the rest.

Diagnostic texts meant for developers (`"Invalid MM9 quest key: "`) stay English.

### Contexts

A lookup tries the most specific context first and falls back to the next, ending at no context:
`map:7out01` → `world:mm7` → none. So one shared translation covers a text everywhere, and a map, world or
control can override it where the same English needs a different translation (Celeste reads differently in MM7).
Contexts are `msgctxt` in the `.po` file.

A text found in none of these is looked up last in the other worlds' files (`TextCatalog::findInWorldFiles`, in the
files' name order): a world's own text is also shown outside its world, as when the party carries an MM9 item to
Jadame or MAW puts MM9's items into every world, and its translation exists only in `text/mm9.po`.

## C++ API

```cpp
tr("Not enough gold.")
tr("Sold {item} for {price} gold.", {{"item", itemName}, {"price", price}})
trn("{count} day", "{count} days", days, {{"count", days}})   // plural form chosen by the language
trc("button", "Close")                                         // explicit context
```

- Placeholders are named and braced, the same style as MAW's `texts.yml`. Values that are themselves display text
  (an item's name) are passed already translated by their own source.
- `tr()` returns English when no language is active or the entry is missing.
- The functions live in `engine/Localization.h` (namespace `OpenYAMM::Engine`); `engine/TextCatalog.h` holds the
  `.po` reader, plural rules, entry checks, formatting and `qps`. Lookups do not lock: the language is set at start,
  before anything localizes.
- Text the player typed (character names, save names) is never passed through `tr()`.
- Hot paths may cache a translated text; the cache is cleared when the language changes.

Rule for `AGENTS.md`: player-visible text in C++ goes through `tr()`/`trn()` with named placeholders; never build a
sentence from pieces.

## Language packs

A language pack is a folder `languages/<id>/` in the mounted assets. Besides its text it mirrors the game's tree like
the `mods` folder ([Modding](../packaging/MODDING.md)), but only its `fonts/`, `audio/`, `videos/` and `icons_x2/`
folders are mounted, in front of the English ones:

```
languages/ru/
  language.yml                # name: Русский, english_name: Russian
  text/
    engine.po                 # C++, menus, Settings, shared tables, rulesets, global events
    engine-pending.po         # imported translations of texts no template has yet (C++ not wrapped in tr())
    mm6.po  mm7.po  ...       # a world's map events and presentation
  engine/fonts/truetype/...   # faces that have the language's alphabet
  engine/audio/...            # optional: sounds and voices in the language
  engine/videos/...
  worlds/mm7/audio/...        # optional: a world's voices and videos
  worlds/mm7/videos/...
  engine/icons_x2/...         # optional: images with text in them (the Arcomage card sheet sprites.pcx)
  worlds/mm7/icons_x2/...     # optional: a world's such images
```

- An image in `icons_x2/` replaces the game's icon of the same file name and format in that package
  (`engine/icons_x2/sprites.pcx`, the Arcomage cards). Icon requests name their package, so these mount at
  `/engine/icons_x2` and `/worlds/<world>/icons_x2` in a release and in a development root alike (OY-579).

- `text/engine*.po` serve every world; `text/<world>.po` entries without a context get `world:<world>`, so they win in
  that world only.
- Development packs live in `assets_dev/languages/<id>/`; a player's own pack goes into a `languages` folder in the
  game folder (`<user data>/languages`, mounted at `languages/` in front of the shipped ones).
- Mount order (`AssetFileSystem::mountLanguagePack`): base content, then the active pack's overlay folders, then
  `mods` (a player's mod still wins). A release mounts them at their package path (`/engine/fonts`,
  `/worlds/mm7/audio`), a development root at the merged folders (`/fonts`, `/audio`) where only the active world's
  overlay mounts. PhysFS mounts a folder once, so each overlay takes exactly one mount point.
- A pack never replaces data tables, scripts or layouts: those folders are not mounted, and the game logs anything
  in the pack besides `language.yml`, `text/`, `engine/` and `worlds/`. Text goes through the `.po` files only.
- `settings.ini` `[gameplay] language=<id>` (English `en`, the pseudo-language `qps` or a pack's id), shown in
  Settings → Interface → Language with the installed packs added to the catalog's options. A change takes effect at
  the next start: the pack's overlays mount with the assets and fonts load once. Switching during a run can come later.

### Releases: languages as optional downloads

English always installs. A language's **text** (`language.yml`, `text/*.po`, a few MB) ships with every release, so
the Language row lists every language the release has, offline. Its **fonts, sounds, voices and videos** are optional
packs, downloaded only for a language the player chooses and kept current by the updater like every other pack
([Incremental updates](../packaging/UPDATER_PLAN.md)):

- **Packager** (`tools/package_runtime_assets.py`, `tools/runtime_packs.py`, `tools/packaging/packs.yml`): the text of
  `assets_dev/languages/<id>/` goes into the engine package's `languages` pack (mounted at `/engine/languages`, so
  `languages/<id>/...` resolves as in development). The overlay folders become packs
  `lang-<id>.<package>.<folder>[.<bucket>]` with a `language: <id>` field in `index.json` and the release manifest,
  mounted at the folder they overlay (`/engine/fonts`, `/engine/audio`, `/worlds/mm7/videos`); bucket counts are in
  `packs.yml` under `languages.overlays`. Files of worlds the release does not ship are left out; a file in any other
  folder of a pack fails packaging. `packaging/publish_release.py` carries the field into the manifest.
- **Mounting** (`AssetFileSystem::mountContentPacks`): packs with a language field mount only for the interface
  language, in front of the base packs and behind `mods`; the others stay unmounted. A missing language pack is no
  error (`validateAssetPackFiles` skips it): the game starts in English and `languagePacksMissing()` tells it the
  updater still has to fetch them. A pack in the player's own `languages` folder mounts in front of the shipped ones.
- **Updater** (`AppUpdater::setLanguages`, `planUpdate`): an update downloads the optional packs of the languages kept
  installed (any whose packs are in the store, and the one chosen in Settings) and no others. Choosing a language whose
  packs are missing downloads them as a content-only update of the installed version, then asks for a restart.
- **Settings**: the Language row lists the release's languages, with the download size of those not installed.
- Updaters of releases before 2.0 do not know the field, so every manifest and the release's `index.json` list the
  language packs apart, under `language_packs`, which they do not read (`packaging/publish_release.py`,
  `engine/update/ReleaseManifest.cpp`, `engine/AssetPackIndex.cpp`): an update from 1.21 or earlier downloads no
  language's packs, and the game then fetches the chosen language's as above. (Listed among the packs, they made the
  old desktop updaters refuse the new version, whose index lists packs they never downloaded; and the old Android
  updater would record them without their language, so the game would mount every language's fonts.)
  Until 2.0 releases shipped each language's text and fonts only (`ship: false` on the `audio` and `videos` overlays in
  `packs.yml`); from 2.0 the dubbed sounds and videos ship too (the user's decision, 2026-11-11). Removing an
  installed language's packs is not implemented yet (they stay until a release drops them).
  Android: the in-app updater (`OpenYammUpdater.java`) downloads every language's packs (fonts only: the dubbed sounds
  and videos are not packed for Android) and records their language. A phone updated by an updater before 2.0 has
  none; the 2.0 app offers the installed release's missing packs as an update.

### Fonts

The renderer is UTF-8 throughout since 1.21, and Unicode faces pack large character sets (CJK included). The
"faithful" legacy faces have no Cyrillic or CJK glyphs, so a pack replaces their descriptors under
`engine/fonts/truetype/` with faces that do (Alegreya, already in the repository under the SIL OFL, covers
Cyrillic). No code-page conversion is needed; PR #25's windows-1251 path is obsolete.

The Settings language list and the Language row draw every language's own name (Čeština, Русский, 简体中文) with
`menu_language_names`, whatever the interface language: a renamed subset of LXGW WenKai (SIL OFL) in
`engine/fonts/truetype/`, holding Latin, Latin Extended-A, basic Cyrillic and the packs' names and translations of the list's texts.
`tools/language_names_font.py` (needs fontTools) builds it; run it again after adding a pack or renaming one.

### Atlas memory for large character sets

A CJK pack makes font atlases the main cost. Today (checked 2026-11-07):

- Each Unicode face builds a main and a separate shadow texture, both BGRA, with mip chains (the `SmoothText` filter,
  `game/render/TextureFiltering.cpp`), plus a white tint copy when its glyphs are not white.
- Atlases are shared by descriptor name and raster height (`unicodeAtlasKey` in `game/ui/GameplayHudCommon.cpp`), so
  descriptors that point at one font file still build separate atlases.
- A face drawn at its logical size rasterizes at three times that height, up to 48 px (`unicodeRasterHeight`).

Estimated from the code (to be measured with the `[GpuFrameResources] texture_bytes=` log line): about 4,300 CJK
glyphs at 48 px take roughly 70 MB per texture, 150–200 MB per face and raster height with the shadow and mips.
Changes, cheapest first:

1. Share atlases by font file and raster height, not descriptor name. Per-face size adjustments (the Chinese pack's
   `glyph_scale`) are applied when drawing, so they do not split the atlas. **Done**: the key is the font file,
   character list, weight and raster height; a face sharing an atlas shifts its glyph placements by its own baseline.
2. Draw the shadow from the main atlas if it is only an offset copy, removing the second texture. **Done** for
   Unicode faces, whose shadow mask was an exact copy.
3. Store glyph coverage in one channel (R8) instead of BGRA: four times smaller.
4. Subset a pack's font files to the characters its `.po` files use (download size only); `l10n.py check`
   produces the character list.
5. Rasterize glyphs on first use into atlas pages. The largest saving, and the most complex; decide after
   measuring 1–3.

Mipmaps stay: small labels alias without them.

### Fonts in the packs

- **Simplified Chinese** draws every face with LXGW WenKai (SIL OFL; descriptors with `encoding: utf-8` and a
  `characters_file`), shipped unsubset (25.8 MB: disk only). Its character list is generated:
  `l10n.py check zh-cn --charset .../lxgwwenkai.charset.txt` (the characters the translations use plus every
  Windows-1252 character, 3,391 against the original pack's 4,280), which keeps the atlases small. The pack's
  `glyph_scale` key is not implemented and is ignored.
- **Russian** draws every face with Alegreya (already in the repository, SIL OFL, with Cyrillic) at the face's own
  logical height and baseline, weight 500 or 600, from `alegreya_cyrillic.charset.txt`.
- Measured GPU texture memory in the menus (2026-11-08, `[GpuFrameResources] texture_bytes`): English about 160 MB;
  Chinese 800 MB before, about 280 MB after changes 1 and 2 below; Russian about 40 MB at the trace's peak. The
  rest of the Chinese cost is mostly the 96 px atlas of the main menu title (8192×3427).

### Plurals

Each `.po` file's header carries its language's `Plural-Forms` formula (`nplurals=3; plural=(n%10==1 && n%100!=11
? 0 : ...)`). The loader evaluates it with a small expression evaluator (ternary, comparison, `%`, `&&`, `||`), so
the game needs no built-in knowledge of any language.

### Typed answers

A riddle or password question accepts the English answer and the translated answer of its catalogue entry. Case
folding covers the alphabets of installed packs.

## Code that works on text

Translating what is shown is not enough where code handles the text itself:

- **Names built from parts.** An item's name with its enchantment ("Long Sword of Fire"), an NPC's name with a
  profession, a monster's name with a tier: each is a `tr()` template (`"{item} of {enchantment}"`) so a language
  can reorder or inflect it, with the parts translated by their own sources.
- **Dates and times.** Day and month names, am/pm and the order of a date come from `tr()` templates.
- **Search.** Inventory, recipe and journal searches match the player's typed text against the displayed (translated)
  text, not the English identity.
- **Case conversion.** Code that changes the case of displayed text (titles, case-insensitive comparison of typed
  answers) uses a Unicode-aware helper; ASCII `toupper` leaves Cyrillic and accented letters unchanged.
- **Sorting.** Lists sorted by name for the player sort by the displayed text.
- **Line breaking.** `Utf8::wrap` already breaks around characters that need no spaces (CJK).

Not handled through text lookups:

- Text painted into images, spoken audio and video: a pack replaces those files (see Language packs).
- SDL key names, credits names, and anything the player typed.
- Text outside the game screens: the window title, startup error dialogs, the updater and the Android app name.
  Translating these is separate work if wanted.

Completeness does not depend on the source list being perfect: anything missed shows as English under `qps` and in
the missing-text log, never as broken text.

## Pseudo-language `qps`

Built in, no files: `[gameplay] language=qps` or `--set gameplay.language=qps` (Settings → Interface → Language lists it
only while it is the active language, so players never see it). Every text that goes through a lookup
comes back marked, accented and a third longer: `Settings` → `[Séttíñgs···]`.

- Plain English on screen is text that bypasses the lookups (a missing `tr()` or hook).
- A cut-off `]` is a control too narrow for a longer language.
- It also guards requirement 1: scenario tests run under `qps` must behave exactly as in English. A difference means
  some code used a displayed text as an identity.

## Tool: `tools/l10n.py`

Python with PyYAML, like the other repository tools (the standard library has no YAML reader). Run by hand before a
release; `python3 tools/l10n.py --help` lists the options.

| Command | What it does |
|---|---|
| `extract` | Scans every source below and writes `assets_dev/languages/templates/<domain>.pot`: each English text with its source references (`file:line`). A text the shared template has is left out of the world templates |
| `update [lang]` | Merges the templates into each language's `.po` files: translations are kept (also when a text moved between files or arrived from an import), new texts come untranslated, a changed English takes the closest old translation marked fuzzy (`#|` shows the old English), removed texts become obsolete (`#~`), and imported translations of texts no template has yet wait in `engine-pending.po` |
| `report [lang] [--list]` | Translated, fuzzy and missing counts per language and area (C++, menus and HUD, settings, each table, ruleset, world maps); `--list` prints every untranslated entry with its source |
| `check [lang] [--charset FILE] [--cpp [--list]]` | Translations that change placeholders, printf values, story or colour codes; how many characters each face lacks; Lua sentences joined with `..`; with `--cpp`, English sentence literals in game code outside `tr()`. `--charset` writes the characters a language uses, for font subsetting |
| `import tsv FILE... --lang ID [--context CTX]` | English`<TAB>`translation pairs (PR #25's catalogue) |
| `import pack DIR --lang ID [--base REV]` | Translated copies of the game's files (the Chinese pack), paired with the English files of the release `REV` they were made from |

Import keeps only texts the templates know or that wait for C++ (`ui_text.txt`), refuses entries that change their
English's codes, takes the most common translation when there are several, and writes everything it could not place
or chose between to `output/l10n/<lang>-import-review.txt` (outside the pack).

Sources the extractor reads:

- C++ (`game/`, `engine/`): `tr`, `trc` and `trn` calls with string literals.
- Lua (`engine/events`, `engine/scripts`, ruleset events, `worlds/*/events`): string literals of the text-taking
  `evt` functions, `Register*Event` titles and hints, `targetName`/`title`/`hint` fields and `tr()` calls. Literals
  joined with `..` are left out and listed by `check`.
- Data tables: the player-visible columns in `TABLE_TEXT_COLUMNS` (identifier and note columns stay out), ruleset
  tables and patch files (`PATCH_TEXT_COLUMNS` by column name, and columns given by position, `#1`, that are text
  columns of the patched table). A ruleset's `ruleset.yml` says which table each of its files patches or appends
  rows to (`quests_maw.txt` holds rows of `english/quests.txt`); appended rows have no header lines.
- YAML: layout labels (`text: value:` under `engine/ui` and `worlds/*/ui`), the Settings catalog (names,
  descriptions, units, groups, option labels), ruleset `texts.yml` and `ruleset.yml`, world presentation
  (`world.yml`, cinematics), certificates and engine data YAML.
- Single identifier-like words ("SunButton4", "DB_CeilingLeft": object names some MM9 scripts use as event titles)
  are skipped.
- Not yet: MM9's `.rude` dialogue files and journal.

Runtime help for what a static scan cannot see:

- `OPENYAMM_UNTRANSLATED_TEXT_LOG=<file>` appends each text an active language lacks (with its context), once.
- A run under `qps` (`./tools/run_game.sh --isolated <name> --world mm6 --menu --set gameplay.language=qps` with a
  menu tour) shows any English left on screen and controls too narrow for longer text.

## Not in scope

- Right-to-left scripts (Arabic, Hebrew): bidirectional layout and glyph shaping.
- Text painted into original images, unless a pack replaces the image.
- Grammatical case or gender of names inserted into sentences.

## What we take from the proposals

- **PR #25:** the Russian translation (about 17,000 entries for all three worlds), converted to `.po` by script;
  it is already keyed by English. Review its licence (short names follow the Russian editions and MMMerge's Russian
  translation) and quality (about 258,000 words of new translation) before shipping. Also: the missing-text log
  and translated riddle answers.
- **Discord series:**
  - The `qps` pseudo-language and the language-switch check.
  - Its list of C++ call sites, as a map of what to wrap in `tr()`.
  - Patch 1 (a menu label losing its second line in a rect that cannot hold it) is a bug fix on its own.
  - Patches 6 and 7 (party creation layouts for longer text) for the layout pass.

- **Simplified Chinese** (`jimmyownd-hash/EET-CHN-Voiceover`, branch `openyamm-zh121`, folder
  `localization/zh-CN/`): translated copies of our v1.21 files plus `data_tables/english/ui_text.txt` (7,140
  English→Chinese lines for text drawn by C++). See
  [Importing the Chinese translation](#importing-the-chinese-translation).

Not taken: draw-time interception with printf pattern matching (PR #25, and the Chinese branch's `UiText`), named
keys in place of English, separate term and script-text formats, and replacing whole tables (Discord series).

## Importing existing translations

Both outside translations convert to `.po` by script (`l10n.py import`), because both are keyed by, or line up with,
the English text. The import writes entries marked fuzzy where it is unsure and a review list of everything it could
not place.

### Importing the Russian translation (PR #25)

The `.tsv` files are already English→Russian pairs: each becomes a `.po` entry; `world_strings.tsv` entries take the
world's context. Entries matched through printf patterns become `tr()` templates once the C++ has them.

### Importing the Russian translation (three sources)

The Russian pack (`assets_dev/languages/ru/`) combines, in this priority:

1. **The MMMerge Russian localization** (LocRU by Maslyonok: `Text localization/RU_*.txt`, `zz LocRU.T.lod`,
   `zz LocRU.D.lod`, `Anims/*.vid`), imported with `l10n.py import mmmerge DIR --lang ru --audio --videos`: the
   established human translation of the games' text (item, NPC, topic, greeting, news, quest, autonote, award, map,
   monster, class, scroll, spell, skill and stat tables, and the map strings of 199 of 213 `.STR` files, paired with
   the English ones of `reference/mmerge_data_forus/Data/mmmerge.T.lod`), 5,290 sounds (every one matches one of
   ours by name) and 31 cutscenes (only `videos/Cutscenes`; transcoded with `tools/transcode_bik.sh`/`_smk.sh`).
   Each table mapping was checked against PR #25's translation (names agree; long texts are worded differently).
2. **PR #25** (`strings.tsv`, `game_text.tsv`, the worlds' `world_strings.tsv` with their world context): the
   interface, and the game text the first source lacks. Where both have a translation the first one stays; the
   differences are listed in `output/l10n/ru-import-review-pr25.txt`.
3. **The Discord series** holds no translation (its author kept his packs out for licensing reasons).

The MMMerge archive's interface bitmaps and Cyrillic FNT fonts are not used: the overlays take only fonts (TTF faces),
sounds and videos. Coverage on 2026-11-08: 84 % of the templates (MAW's own texts and MM9 are the gaps).

### Importing the other MMMerge localizations

Czech, German, Spanish, French and Polish come from the MMMerge localizations of the same kind (`LocCZ.7z`,
`LocGR.7z`, `LocSP.7z`, `LocFR.7z`, `LocPL.7z`, 2026-11-08), imported with the same command:

| Pack | Archive | Code page | Text | Sounds | Cutscenes | Font overlay |
|---|---|---|---|---|---|---|
| `cs` | LocCZ | 1250, some lines already UTF-8 | yes | — | — | Alegreya (č, ř, ů and others) |
| `de` | LocGR (German) | 1252 | yes | 5,267 | — | none (Windows-1252) |
| `es` | LocSP | 1252 | yes | 6,696 | 18 | none |
| `fr` | LocFR | 1252 | yes | 5,264 | — | none |
| `pl` | LocPL | 1250 | yes | 4,409 | — | Alegreya (ą, ł, ż and others) |

`import mmmerge` finds its files at any depth (LocSP nests them under `Data/` and `Anims/`), reads a
`*LocalizeTables.txt` file of several tables (`MMMERGE_STRUCT_TABLES`), and decodes each line as UTF-8 when it is
valid and has no far characters, otherwise in the archive's code page (LocCZ mixes both). Each import's open points are
in `output/l10n/<id>-import-review.txt`. The legacy faces draw Windows-1252 only, so Czech and Polish get the Russian
pack's Alegreya descriptors with their own `alegreya_latin.charset.txt` (from `l10n.py check <id> --charset`).
MMExtension's own strings (`mm8lang.ini`) are not imported.

LocCZ comes from another MMMerge version: its class names and descriptions follow a different class order, and its
monster names from id 470 on are one row off ours. Those rows are left out of the import (the names show in English
until translated); `glossary cs` was checked for them. The other archives' monster and class rows were compared with
English and Polish and line up.

### Importing a localized MM9

The official MM9 localizations (CD Projekt's Czech and Polish releases of 2002; a German retail version existed too)
ship the same data tables as the English game with the texts translated. Extract the release's `DATA.REZ` and
`RUDE.REZ` with `tools/mm9_import_discovery/extract_rez.py <file>.REZ <dir>/DATA` (and `<dir>/RUDE`), then
`l10n.py import mm9 <dir> --lang LANG --encoding cp1250 --label "the Czech MM9 (CD Projekt, 2002)"`: it pairs every
file with `mm9/extracted` row by row and cell by cell (conversation rows and books by their ids) and replaces the
`mm9.po` machine drafts (human translations stay unless `--replace`). Texts the MM9 rework wrote itself (quest
overlays, map scripts, cinematics) have no official counterpart and stay drafts.

### Machine translations

For a human translator: `l10n.py todo LANG --po [--skip-domain mm9] --out FILE.po` writes the language's
untranslated texts as a .po file with its plural header; the filled file comes back with
`l10n.py import po FILE.po --lang LANG` (refusing entries that change placeholders or codes).

Texts no human translation covers can be drafted by a model and marked for review:

- `l10n.py todo LANG [--refs REGEX] [--limit N] --out FILE`: the untranslated texts with their source references.
- `l10n.py glossary LANG --out FILE`: the language's established short terms (classes, skills, spells, stats, the
  original interface's words), so a draft uses the human translators' words.
- `l10n.py import machine FILE --lang LANG [--label NAME]`: writes the drafts (`[{context, msgid, msgstr}]`, a list
  of forms for plural texts) with the translator comment `machine translation (NAME), review`, refusing any entry that
  changes placeholders or codes. `report` counts these apart; a human translation replaces them.

### Importing the Chinese translation

Checked on 2026-11-07 against our `v1.21` tag, then rechecked at the branch's commit `992b6cb`, which fixed the zero
cells (410 quest and autonote rows, item 0), the MAW assassin indentation, the name dot and untranslated name fragments
in `Global.lua`, and the multi-line cells that split rows. The pack's files are copies of ours with the text replaced,
so the import pairs each English text with its Chinese by comparing the two copies:

| Their copies | Line up with our English |
|---|---|
| Event Lua (286 changed files) | 285 literal for literal; only comments differ |
| Data tables (69 changed) | 64 cell for cell; `npc_topic_text`, `npc_topic`, `npc_greet`, `scroll` and `mm7_history` by row id |
| YAML (57 changed) | 41 by key path; the rest are their fonts, two restructured layouts and MAW `texts.yml` |
| `ui_text.txt` | already English→Chinese |

About 17,000 distinct English texts get a translation. Files the pack copies unchanged (textures, terrain, liquids,
many fonts and tables) are ignored. Points the import and review must handle:

1. **Composed text.** `ui_text.txt` has 655 placeholder patterns (`Join guild for {cost} gold`), usable once the C++
   has a `tr()` template with the same English (placeholders renamed to ours), and 95 prefix patterns
   (`Leave the *`) that need templates. `Global_maw.lua` was translated piece by piece around a joined sentence.
2. **One English text, several translations.** About 3,900 English texts (an upper bound: the count includes
   encoding noise) have more than one Chinese version (`Master Alchemy` → 炼金术大师 / 大师级炼金术). Unify the
   wording drift; keep genuine differences as map or table contexts. Some look mispaired (`Rotted Corpse` → 腐尸
   and 巨石) and go to the review list.
3. **Changes that are not translation** are dropped. Open: `house_data.txt` row 326 (a temple) changes column A from
   `2` to `2.5`. An English text of `0` is never a translation key.
4. **Riddle answers** stay English in 24 of 26 questions; Chinese answers need adding.
5. **Encoding.** Some lines hold single Windows-1252 bytes inside UTF-8. After the fixes these lines are inherited
   from our own English files (our `Global.lua` has 343 such lines); the import decodes character by character, as
   `Utf8::decode` does.
6. **Table shape.** Every translated table parses to the same rows and cells as the English one under the engine's
   table reader. Topic 2164 in `npc_topic_text.txt` holds its first paragraph twice (an older translation on the id
   line and a newer one on the continuation line).
7. **Fonts.** LXGW WenKai (SIL OFL) works with our `characters_file`. Their descriptors also use `glyph_scale`
   (glyphs drawn smaller within the same line height), an engine change we do not have. The 25.8 MB TTF ships
   unsubset (decided 2026-11-08: the download is only for players who choose Chinese).
8. **Layouts and names.** Packs do not replace layouts. Decided 2026-11-08: the title stays OpenYAMM in every
   language; Chinese uses 魔法门重生 as the subtitle ("Universe of Might and Magic"), 整合版 for MMMerge and 重铸版
   for MAW wherever the interface names the rulesets; the credits keep the project names MMMerge and MAW.
9. **Permission.** We have permission to ship the translation (2026-11-07). No translator credit: they did not ask
   for one (their branch's 汉化：考拉粑粑, in place of the "OpenYAMM on GitHub" label, is not taken).

English texts changed since 1.21 come out of the import as untranslated or fuzzy, the normal `update` workflow.

## Status

Done (2026-11-07 and 08):

- Runtime: `engine/TextCatalog.*` and `engine/Localization.*` (reader, plural rules, entry rejection, contexts,
  formatting, `qps`, the missing-text log, `localizeKnown`, `trNoop` for English kept in tables of the code), unit
  tests in `tests/LocalizationTests.cpp`. Shared text helpers: `game/ui/CalendarText.*` (weekdays, months, dates with
  the month's in-date form, clock), `game/gameplay/ActorNameText.*` (composed MAW monster names),
  `Engine::Utf8::capitalizedFirst`.
- Language setting and packs: `[gameplay] language`, Settings → Interface → Language (with the download size of a
  release language not installed), pack discovery, the font, sound and video overlays, the player's `languages`
  folder, and the release packs ([Releases](#releases-languages-as-optional-downloads)).
- C++ text: every player-visible text of `game/` outside MM9 goes through `tr`/`trn`/`trc` or a data lookup (a pass
  over every file on 2026-11-08: houses and dialogue, party and items, world and combat, menus and journal, MAW).
  Left English on purpose: logs and diagnostics, identifiers and texts compared in code, stored texts (statistics,
  save names, notes), MM9 code, the launcher, first-run setup and updater windows.
- Data hooks: NPC dialogue, items, enchantments, classes, skills and stat descriptions, spells, monsters (combat
  messages, hover, inspect), map names, quests, autonotes, history, awards, house services, transport, trainer pages,
  certificates and world/ruleset texts, cinematic subtitles, MAW's texts and YAML data.
- Layouts: menu labels shrink to 60 % before an ellipsis; party creation's labels, voice lines, legend and class table
  fit longer languages (the Discord series' patches 6 and 7).
- Fonts: atlases shared per font file; one texture per Unicode face; `max_raster_height` (64 in the Chinese pack).
- `tools/l10n.py`: `extract` (also MAW YAML texts, behaviour `say()`), `update`, `report`, `check`,
  `import tsv|pack|mmmerge`.
- Packs: Simplified Chinese, Russian, Czech, German, Spanish, French, Polish. On 2026-11-08 every text the MMMerge
  archives lack (interface, MAW, the story and event texts of MM6–MM8, all of MM9 with its RUDE conversations) was
  drafted by Claude (`import machine`, marked `machine translation (Claude), review`). Coverage: cs, de, es, fr, pl
  and ru 100 % of 25,348 texts (9,979–15,678 of them machine drafts per language); zh-cn 73 %, its translator fills
  `output/l10n/zh-cn/` (round 2: 153 texts plus 6,601 of MM9).
- Extractor fixes of the same day: NPC topics and greetings whose text continues on lines without an id are one text,
  joined as `NpcDialogTable` reads them (before, the game looked the whole paragraph up and found nothing); ruleset
  patch files (`key column value`) give their text values, not their column names; titles of timers, load events and
  hooks are left out (only event titles show, as the indoor hover fallback); `npc_names.txt` (random peasant names),
  the Settings keyboard labels, the ledger's `topic`, and C++ patterns of placeholders only (`{day} {month} {year}`:
  languages order them) are extracted. Imports update every world file that holds a text, and a cell's surrounding
  spaces or line breaks no longer hide its translation at runtime (`localize` retries the trimmed text).
- Address and pairing pass (2026-11-08, later): every text that speaks to the player or the party addresses them in
  the plural (cs "vy", pl "wy", ru "вы", de "Ihr/Euch", fr "vous", es "vosotros"), fan translations included (3,943
  entries; a changed human entry carries `address made plural (Claude)`); letters to one named person, speech
  between other characters and the party's own lines stay singular. Decimals keep the English point in every
  language (`check` reports a decimal comma). Pairings repaired: `scroll.txt`'s MMMerge letters 770–774 spanned
  lines unquoted (the game showed their first line; each is one quoted cell now, which also re-aligned the scroll
  import), short lines that still held a whole paragraph from the line-by-line extraction ("No.", "Welcome!"), and
  the German archive's hireling texts, shifted by one id (2267–2316). Data fixes: MM9's spell-book notes lost their
  doubled quotes (`mm9_spellbooks.py` unquotes the copied MM8 cells), and the MAW leech line says "half as much as a
  Vampire". A political insult the Czech fan translation had put into a trainer text is gone.
- Fan-text corrections (2026-11-08, later): human entries whose numbers differ from the English (prices, ranks,
  stats, counts) and the errors the address pass noted were corrected against the English (834 entries, comment
  `fan text corrected (Claude)`); French potion names that were fan placeholders (`_potion/réactif272`, now refused
  on import) are translated. English data fixed: the six "Essence of Luck" recipe scrolls name their own essence,
  and the Will'o'Wisp quest asks for 5 hearts. MAW boss affixes have the context `monster affix` (`trcNoop`), apart
  from item suffixes ("Swift" was "of Swiftness"), translated as gender-free labels in `{monster} ({affix})`.
  An MM9 line said by the party and also by an NPC has the context `said by the party` where the party says it
  (prompts are looked up with it, falling back to the plain entry). The arena, boat race, rune and mirror status
  lines of the MM9 rework are whole `tr()` sentences (in their generators too).
- Czech MM9 (2026-11-08, later): the official CD Projekt translation (`mmix_cz_data.zip`, the 2002 release's
  data for GOG 1.3) replaces 5,951 Czech MM9 drafts (`import mm9`). It treats the party as one person; its NPC lines
  now address the party in the plural and the party's "we" lines speak in the plural, the wording kept. The
  remaining Czech MM9 drafts (the rework's own texts) use its names. No other MM9 localization was found online:
  Polish (CD Projekt) and German existed only on retail discs; none for ru, es, fr or zh.
- Simplified Chinese round 2 (2026-11-08, evening): the translator's `zh-cn-todo-2.po` and `zh-cn-todo-mm9-2.po`
  are imported (6,510 texts, MM9 included); zh-cn is at 98 %, the 274 left empty on purpose (internal ids, debug
  labels, ciphers, typed riddle answers). `import po` now takes placeholder-only patterns (`{year}年{month}{day}日`).
- The Chinese translator's review (2026-11-08, night): short texts the pack import had crossed got contexts and
  correct data (`trc("turn-based button", "End")` was taking the stat abbreviation, `trc("mastery letter", ...)` the
  monster spell mastery letters, which had imported as "0"). The mastery letters are 普/专/智/宗 for N/E/M/GM (first
  character of 普通/专家/智者/宗师; chosen by Claude as the translator did not answer, marked for review). Party
  creation's wrap (`NewGameScreen::wrapTextToWidth`) now uses `Utf8::wrap`, which never cuts a colour code between
  CJK characters (it showed the code's digits), and justified HUD lines carry an open colour code to each word.
  Every character the pack uses is in its charset. Names: see item 8 of the Chinese import.
- New 2.0 texts and the Chinese 2.0 review (2026-11-11): the 182 texts added since 11-08 (Battle Orders, MAW guard
  and skill lines, promotion and bounty dialogue, MM9) were drafted in every language; zh-cn skips the internal MM9
  event titles. Russian "Normal"/"Expert" were the fan pack's "[Н]"/"[С]" and now read Обычный/Эксперт (the plain
  entry is shared with the Normal difficulty). The zh-cn translators' review (`EET-CHN-Voiceover`, branch
  `openyamm-zh121`, `upstream-patch/06-v2.0-review`, copy in `output/l10n/zh-cn-review-06/`) is imported with
  `import po --replace`: their current terms (2,196 entries; Master 大师, letter 大), owner-matching names, the plain
  wording for the 20 texts that are both a potion and a stat or spell, doubled characters, Escaton's riddles accepting
  the numbers their question text asks for, and their review of every machine draft (no zh-cn draft is left to
  review). `import po` now replaces a machine draft and drops its mark. The monster attack types (`monster_data.txt`
  Type columns: Phys, Ener, Pois) are extracted and translated. The charset was regenerated for the new wording.
- The zh-cn translators' 2.0 gap report (2026-11-12, issue #31, `upstream-patch/07-v2.0-gap-patch`): the texts that
  stayed English were shown without a lookup and are fixed (MAW's spell description, translated before its recovery
  and aura lines are added; the journal's map title; a street NPC's "name the profession"; the house title while
  talking to a resident; the trainer page's continent tabs; the Battle Orders plan chips, which the extractor could
  not see). Their corrected texts are imported (`import po --replace`), and their 6,850 MM9 entries copied to the
  shared context are not needed: the lookup now ends in the other worlds' files ([Contexts](#contexts)). The
  extractor reads MAW's appended rows and positional patch columns (49 texts no language had: the Ascension topics,
  Cover, Mana Shield, Enlightenment and Retaliation, MAW's monster names). The effects shown after a known event's
  hover name ("Green Barrel (+2 Endurance)", the fountains) were looked up but untranslated in every language: they
  are their status messages without the full stop, filled from those. The 49 MAW texts and the skill names
  Ascension (`ruleset.yml` `skillNames`, now extracted), Enlightenment and Retaliation (`trNoop` in `SkillData.cpp`)
  are drafted in cs, de, es, fr, pl and ru. Their Chinese party voices are installed under our file names (828 in
  `languages/zh-cn/engine/audio`, 18 in `worlds/mm6/audio`; 5 files that replace no sound of ours are left out).
  Not taken: their translated copies of `roster.txt`, `npc_names.txt` and `npc_professions.txt` (packs do not
  replace tables), the Arcomage sheet (packs mounted no images then; since OY-579 it can go in
  `languages/zh-cn/engine/icons_x2/sprites.pcx`) and `glyph_scale`.
- Committed: the engine code in `176043355`, the packs (text, fonts, templates of all seven languages) in
  `e1d261a1b`. Not in git: `languages/*/text/mm9.po` and `templates/mm9.pot` (the MM9 world is gitignored and
  they stay with it). The dubbed `audio/` and `videos/` overlays of de, es, fr, pl and ru (about 700 MB from the
  MMMerge archives) are committed since and ship from 2.0 (see Releases).
- Sizes, accepted as they are (2026-11-08): all languages' text goes into the one always-installed `languages` pack
  (about 14 MB zipped; any text change downloads it again), and the Chinese font is not subset.
- In-game sweep (2026-11-08): scripted tours (`debug.menu_input_tour_path`) through the title, Settings, credits,
  party creation, HUD, map, quick reference, statistics, rest, inventory, spellbook, a shop, a temple and a tavern in
  every language, with `OPENYAMM_UNTRANSLATED_TEXT_LOG` collecting lookups the language lacks: none left in cs, de,
  es, fr, pl and ru apart from names that stay (OpenYAMM, credits); the Chinese gaps are in its round-2 files.

Next:

0. **New texts.** At the end of 2026-11-08 every language lacked 21 texts (9 C++ and 12 MM9 texts other sessions
   added; zh-cn 296, mostly the ones left empty on purpose): run `extract`, `update`, then `report --list` and draft
   them (`todo` / `import machine`) before a release.
1. **Review** of the machine translations (`report` counts them; a reviewer edits the `.po` entry and removes the
   comment). Known points: MM9 names rendered differently across packets in some languages; random peasant names
   stay English in the Latin-script languages (names, on purpose).
2. **Thousands separators** differ between corrected fan texts (de/es "5.000", cs/pl/fr "5000" or "10 000", ru
   "50,000" as in English); decimals are settled (the point everywhere). Recommended: each language's own style.
3. **Fonts**: single-channel atlases, glyphs on demand.
4. **Releases**: a `qps` scenario in the release checks; Android language downloads; removing an installed language.
5. A visual pass in each language for texts that do not fit (Settings rows, house service lists, tooltips).
