# Upstream integration, 2026-11-20

This merge brings `origin/main` at `519b6c8a273faaad2445f6ce4b14c44b89d7f882`
into `codex/russian-localization-gameplay-fixes`. The common ancestor is
`4af3efd837e2d3a63dee646cec83a7ea35d45a7f`: 179 upstream commits and 21 local
commits follow that ancestor. The pre-integration local checkpoint is `7429884d0`,
also retained by `ru_local`.

The earlier work is documented in
[Russian localization and gameplay changelog](RUSSIAN_LOCALIZATION_AND_GAMEPLAY_CHANGELOG_20261119.md).
That document describes its historical checkpoint. The integration decisions below
supersede its implementation details where upstream has replaced those systems.

## Localization and text

- Adopt upstream's English gameplay tables and display-only PO language packs.
  Remove the duplicate `game/localization` implementation, per-language table
  replacement files and the retired UTF-8 implementation. Gameplay identifiers,
  spell matching, enchantment kinds and ruleset data remain English and canonical.
- Import 12,609 translations from the local catalogs/table overlays and 815
  character-name translations into `assets_dev/languages/ru/text`. Retain upstream
  translations for new content. Character names use a dedicated context so names
  such as April cannot replace calendar month names.
- Preserve translated dungeon captions, NPC dialogue, riddles, cipher instructions,
  obelisk notes, shops, skills, items and event messages. Keep AI-assisted provenance
  and machine-review marks; playtesting was partial, not a full editorial review.
- Update the Pure Luck recipe descriptions to the current authoritative reagent
  counts: four red, three blue and two yellow. Repair an accidental mixed-script
  residence name and invisible characters. Extend the Cyrillic font character list
  with missing uppercase letters and the mathematical minus sign.
- Restore the HUD's floating-point fit tolerance and avoid font-scale snapping
  that clips fitted labels. Retain one fitted reading scale across skill groups,
  including Technology, while preserving upstream cost tags, switches and scrolling.
- Use upstream Unicode fonts, translated input handling, bindable QuickSave and
  QuickLoad, AutoWalk and persistent party-owned journal pins. Port regression
  coverage to these APIs rather than retaining obsolete parallel implementations.
- Fix Lua extraction to distinguish nested lookup identifiers from displayed
  strings. Register the New Sorpigal storage caption as English `Storage` with a
  Russian PO translation.

## Gameplay and shared code

- Preserve condition-dependent primary statistics, resource effects, living-target
  healing, rest wake-up behavior and world/recovery pause gates. Keep the class
  resource table binding owned by its GameSession. Avoid applying worn level
  bonuses twice: upstream already includes them in equipment resource bonuses.
- Express permanent Dragon Slaying as an explicit potion-table action. Ordinary
  weapon potions retain timed enchantments; broken, rare and already enchanted
  targets retain their rejection behavior.
- Load the shared base `item_effects.txt` before world contributions, preserving
  Villain's Blade's vampiric effect. Use canonical built-in enchantments for
  Clanker's Amulet and the Sun/Moon Cloaks instead of adding duplicate hardcoded
  bonuses. Tests now materialize those built-in enchantments.
- Keep the Harmondale butler's free lodging action on the current shared rest API.
  Retain inventory double-click use, persistent readable-scroll dismissal and the
  pointer-specific Genie Lamp action with current bag/implant handling.
- Preserve shared CPU shore/seabed water depth for movement, jumping and hazards.
  Keep the 96-unit wading threshold, native shallow BModel pools, levitation and
  turn-based hazard timing. Reuse upstream's terrain material schema and parser;
  separate image loading from CPU water calculations compiled into the shared core.
- Preserve aimed interaction priority, hint-only filtering, effective saved face
  attributes, old placed-gold repair and indoor ceiling/portal corrections.
- Retain upstream's equivalent fixes for recycled model picking/rotations, positive
  item requirements, identification, effective Alchemy, live-party Arcomage state
  and hostile projectile interaction with summons.

## World data and assets

Keep the local MM6/MM7 event and geometry repairs, storage chest persistence and
save migrations, including New Sorpigal storage, Gloaming boats/lava, Paradise
Valley, Harmondale, Tularean docks, Hidden Tomb, MM7 transition/event fixes and the
Lich/Alice quest corrections. Resolve gameplay registries against upstream's newer
ownership/schema and guild data. Event supplements remain explicit overlays;
generated legacy event files are not hand-edited by this integration.

Update `assets_source` to upstream's pinned `7559443d3f9382b23f459b19b3239f10bf8401f8`.
Its previous local head `2f206e9` is retained in the submodule branch
`codex/pre-upstream-integration-20261120`.

Retain matching lighting/recipe pairs for the repaired maps. Validate nonvisual
upstream changes explicitly: the four affected MM7 scenes differ only in initial
actor hostility, and the liquid registry only appends MM9-scoped definitions.
`tools/lighting/revalidate_upstream_nonvisual_changes.py` checks those restrictions
and records provenance while retaining the light pages, probes, geometry and all
other binary data. Scene/recipe files retain exact bytes across Git checkouts to
avoid Windows line-ending changes invalidating their hashes.

## Importing old ru_local saves

The branch reused versions 89/90 for a layout different from upstream 89/90.
Ordinary saves must not be guessed by version alone. To import a save known to
have been written by `ru_local`, create a separately tagged copy:

```text
python tools/migrate_ru_local_save.py old.oysav imported.oysav
```

The utility refuses an existing output or an in-place conversion. Only the magic
header changes; version and payload bytes are preserved. The engine's explicit
tagged reader imports the old party autonotes and personal map-note metadata,
then applies upstream migrations. The next normal save uses the current format
(197). Original files remain intact. Full reader/runtime validation awaits the
user's resumption of builds.

## Validation before builds resumed

- No game, unit-test or Vulkan builds were run: the user's build pause remains in
  force. No previous executable is presented as validation of these merged sources.
- Run Python geometry, save-tagging and localization-extraction tests; check changed
  Python syntax, CMake source paths, retired API references and conflict markers.
  Compare C++ parser diagnostics with upstream, accounting for doctest macros.
- Current localization templates: 26,879/26,879 translated, no fuzzy or missing
  entries. This measures coverage, not editorial quality. The localization checker
  still reports whole-catalog coverage against the intentionally restricted
  `combat_numbers` and `menu_language_names` fonts, plus existing joined MM9
  diagnostic strings. General reading fonts cover the imported characters.
- Run `tools/lighting/stale_bakes.py`: no stale MM6/MM7/MM8 dependencies remain.
  The remaining 44 entries belong to the optional local MM9 payload and refer to
  absent native source BMPs. Those MM9 sources are not present in this checkout or
  its pinned optional source-asset submodule; they have not been fabricated or
  replaced. MM9 rebaking/runtime validation remains outstanding.
- Compilation, linked unit tests, actual tagged-save loading and desktop visual
  checks remain outstanding until builds resume.

This integration does not publish or push directly to the upstream repository.

## Follow-up after builds resumed

The user resumed builds and tests on 2026-11-20. The Windows Release game and all
three test executables were built with the existing MinGW/Ninja configuration in
`build-windows-release`, using 25 compile jobs. Vulkan remains disabled.

Compilation and execution exposed additional integration issues, now corrected:

- Store patches with LF so Git can apply the pinned bgfx patches on Windows.
  Compare filesystem path components portably in the shared editor compiler and
  link WinHTTP into the Windows unit-test target that compiles the updater.
- Finish retiring old language parameters and menu constructors, fix the journal
  edit-state field and normalize submitted event answers before comparing them.
  A removed language argument must also not become a load-warning message.
- Use the map width in the separated water-depth loader, and use the current
  mover, trainer and item-generator APIs in regression fixtures.
- Correct the potion action values in YAML. Dispatch Recharge Potion's wand
  action only for wand targets so ordinary potion mixing works in both orders.
- Cure conditions before restoring NPC-healer health: removing poison can raise
  maximum HP, so healing against the previous maximum left the party short.
- Bind actual enchantment tables in the Clanker fixture. Keep the authoritative
  five-member soul-jar case, class learning limits and Normal 1 Blaster grant.
- Port legacy translated-table tests to display-only PO checks. Update the old
  clock/language expectations, preserve the original settings migration fixture,
  and make filesystem/archive, URL and source-newline assertions portable.
- Initialize settings in the Lifedrain runtime fixture. GDB traced its crash to
  the solo-HUD check reading unbound settings. Correct the legacy HUD fixture's
  metric array; it had incorrectly indexed an empty Unicode metric vector.
- Use the current chest trace's English map name in the New Sorpigal scenario.
- Account for Chedian's declared Sorcerer start in the continent test. Explicitly
  activate Standard in the Standard party-sheet fixture so an earlier MAW test's
  Ascension display-name override cannot leak into its Learning assertions.

The old build-pause limitation above is historical; the results below supersede it.

### Executed validation

- Release game and all three test targets compile successfully; Vulkan is OFF.
- Unit suite: 3,149 cases and 4,447,456 assertions passed.
- Runtime suite: 80 cases and 5,463 assertions passed, with no failures or skips.
- Video streaming suite: 2 cases and 132 assertions passed.
- Eight headless scenarios passed: release save/load roundtrip, rebuilt-map save,
  MM6 New Sorpigal storage, MM7 Hidden Tomb password, MM7 Stone City inn rest,
  MM8 Jadame teacher ledger, and both tagged Russian-branch save imports (v89/v90).
  The two imported saves were loaded and rewritten with the normal v197 header;
  SHA-256 checks confirm that both original saves remain unchanged.
- The earlier 22 Python tests passed (17 lighting geometry, 3 save tagging,
  2 localization extraction). Diff whitespace and added C++ line-length checks pass.
- The lighting audit still reports only the 44 optional MM9 bakes with missing
  source BMPs described above; no MM6/MM7/MM8 stale dependencies were reported.
  These runs validate headless behavior, not desktop GPU rendering or performance.

The full CTest run passed unit and video suites. Runtime fixtures were then
corrected and the runtime suite rerun independently. Build/test logs and isolated
scenario artifacts are retained locally under the ignored `output/` directory.

Reproduce the Windows Release build in PowerShell with the existing UCRT64 tools:

```powershell
$env:PATH = 'C:/msys64/ucrt64/bin;C:/msys64/usr/bin;' + $env:PATH
$env:MSYSTEM = 'UCRT64'
cmake --build build-windows-release --target openyamm openyamm_unit_tests openyamm_runtime_tests openyamm_video_streaming_tests -j25
ctest --test-dir build-windows-release --output-on-failure --timeout 1800
```
