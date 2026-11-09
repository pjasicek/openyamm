# MAW class icons (GAPS L6.7), study

Status: **approved by the user and installed natively (2026-10-25)**, see [Native integration](#native-integration).
Preview: [index.html](index.html).

## Which classes need an icon

MAW adds twelve classes (ids 53-64 of `CanonicalClassNames`, `game/party/SkillData.cpp:48`): Seraphim, Angel,
Archangel, Death Knight, Death Lord, Lich King, Shaman, Sekhem, Marabou, Elementalist, Elemental Adept, Master of
Elements. The Assassin rework changes the existing Assassin (id 36, a Thief promotion) and adds no class.

Class icons exist only for classes that can be chosen at party creation: the sixteen first-step classes in
`assets_dev/engine/hud_x2/menus/classes/<token>.png` (128 x 128 RGBA, made in
`level_generation/ui/menu_study_20260928/class_icons_simple_20261006/`). No promotion has an icon and nothing draws one
after creation, so of the twelve only the four first steps need art. Today they borrow
(`classIconTextureName`, `game/ui/screens/NewGameScreen.cpp:229-242`):

| Class (id) | Borrows today | New icon | Promotions (no icon surface) |
| --- | --- | --- | --- |
| Seraphim (53) | paladin.png | white feathered wings | Angel, Archangel |
| Death Knight (56) | knight.png | frost-rimed blackened great helm | Death Lord, Lich King |
| Shaman (59) | druid.png | painted wooden spirit mask | Sekhem, Marabou |
| Elementalist (62) | sorcerer.png | crystal orb of fire, water, wind and stone | Elemental Adept, Master of Elements |

The same map borrows `lich` → `necromancer` for the Lich portrait's class (MMerge, not MAW); that is left as is.

## Where the icon is drawn

All three are on the party creation screen, with the texture from `classIconTextureName`:

- Choose Class grid, 28 design units (`NewGameScreen.cpp:2780`, drawn by `MenuDesignScreen::drawConfirmation`,
  `game/ui/MenuDesignScreen.cpp:781`).
- Beside the selected portrait, 34 units (`NewGameScreen.cpp:2840`, layout `CharacterCreationClassEmblem`,
  `assets_dev/engine/ui/gameplay/character_creation.yml:115`).
- Above each party slot, 20 units (`NewGameScreen.cpp:2980-2983`).

At 1600 x 900 a design unit is 1.875 px: 52, 64 and 38 px.

## How they were made

The crafting-icons pipeline (`level_generation/ui/maw_crafting_icons_20261023/`): a Codex brief run by
`codex exec` with the built-in image generation tool.

- [CODEX_BRIEF.md](CODEX_BRIEF.md) uses the common prompt of the existing sixteen icons, so the new ones share their
  one-object, soft-lit painted style; [classes.json](classes.json) holds each class's identity (from the MAW class
  descriptions in `assets_dev/engine/rulesets/maw/content/class_patch.txt`) and the emblem subject. No MAW art or
  Lua was used.
- [refs_class_icons.png](refs_class_icons.png): the sixteen existing icons, the style input.
- `scripts/run_batch.sh`: two parallel Codex runs. Records: `raw/runs_<class>.json` (prompts, selection reasons),
  every raw generation in `raw/`, run logs `raw/batch_*`. Five generations: one each, plus one retry of the Shaman
  (the first mask's feather fan was too tall to read at 20 px). `raw/check_positions_3_4.png` is Codex's own check
  sheet. The two run logs were first written by a run stopped at once to add the common prompt, then overwritten.
- Masters: `masters/<class>.png`, 512 x 512 RGBA.
- `scripts/build_previews.py`: exports `runtime_x2/<class>.png` (128 x 128, object scaled to 116 px on its longer
  side, the median of the existing sixteen) and builds `previews/` (sizes sheet and two composites over the
  2026-10-06 native captures in `output/screenshots/class_icons_simple_20261006/`; they are mockups, not captures).

Spend: no paid API calls; about 95,000 Codex tokens and five image generations on the Codex subscription.

## Native integration, once approved

1. Copy `runtime_x2/{seraphim,deathknight,shaman,elementalist}.png` to `assets_dev/engine/hud_x2/menus/classes/`
   (lowercase, mode 0644; the names are what `canonicalNameToken` gives for the class names).
2. Drop the four MAW entries from `BorrowedIcons` in `classIconTextureName` (keep `lich`).
3. Native check: a MAW new game at 1600 x 900, the Choose Class grid and a party with the four classes, no missing
   texture in the log. Note for that check: with free selection MAW's grid has 20 classes, and the two-column grid
   is 172 + 46 x rows = 632 design units tall against a 480-unit canvas, so it may run off the screen; that is
   separate from the icons.
4. Close GAPS L6.7 and the "class icons of their own" item in HANDOFF §6.

## Native integration

Done 2026-10-25, steps 1-4 above:

- `runtime_x2/{seraphim,deathknight,shaman,elementalist}.png` copied to `assets_dev/engine/hud_x2/menus/classes/`
  (mode 0644). `classIconTextureName` (`game/ui/screens/NewGameScreen.cpp`) borrows only `lich` → `necromancer` now.
- The overflow: the Choose Class grid (`MenuDesignScreen::drawConfirmation`) uses three columns when two would run
  off the 480-unit canvas (more than 12 choices, so MAW's 20 classes with free selection); the panel widens from 600
  to 720 units and the rows close up from 46 to 42 units (34-unit buttons) to fit: 7 rows, 466 units. Standard's
  grid (at most 10 classes per race) keeps two columns and 46-unit rows. The longest labels in the grid ("Necromancer",
  "Elementalist", "Death Knight") fit at full size in the 208-unit columns; `textInRect` would shrink a longer one to
  85 % and then cut it with an ellipsis, but promoted names such as "Master of Elements" never appear in this grid.
- GAPS L6.7 and the HANDOFF §6 row are closed.

Native captures at 1600 x 900 (`build-ui`, isolated menu tour: New Game, MAW, Enroth, the class box):

| Capture | What it shows |
| --- | --- |
| [native/choose_class_maw_1600x900.png](native/choose_class_maw_1600x900.png) | MAW's 20 classes in three columns, the four new icons |
| [native/choose_class_standard_1600x900.png](native/choose_class_standard_1600x900.png) | Standard's grid, unchanged (two columns) |
| [native/party_four_classes_1600x900.png](native/party_four_classes_1600x900.png) | A party of Seraphim, Death Knight, Shaman and Elementalist: the slot icons and the 34-unit emblem |

The log has no missing texture for the four classes. One pre-existing gap remained: **Peasant** (MAW's twentieth
class) had no icon, so its grid button showed none and the log repeated `could not resolve texture:
hud_x2/menus/classes/peasant.png` every frame while the grid was open. See [Peasant](#peasant).

## Peasant

Added 2026-10-25 by the same pipeline: `classes.json` position 5, Codex batch c (`raw/batch_c_*`, run alone with the
command of `scripts/run_batch.sh` so the a/b logs stay), `raw/runs_peasant.json`, `raw/peasant_1.png` (one
generation, selected, about 44,000 Codex tokens, no paid API), `masters/peasant.png`, `runtime_x2/peasant.png` from
`scripts/build_previews.py` (the other four exports came out byte-identical).

- Peasant (class id 48) has no MAW or MMerge class description; its class tables make it the humble start with no
  magic, Learning and the everyday trade skills (Repair, Merchant, Alchemy, Identify Item and Monster, Disarm Traps,
  Bodybuilding).
- Emblem: **a wide-brimmed straw hat** (warm straw, faded brown band). Its broad flat oval and wheat colour read at
  20 px and match nothing in the set; a pitchfork, scythe or hoe would be thin diagonal shafts at 20 px, too close to
  the bow, sword, dagger and club, and a scythe reads as Death.
- Installed as `assets_dev/engine/hud_x2/menus/classes/peasant.png` (0644); `canonicalNameToken("Peasant")` is
  `peasant` and `BorrowedIcons` has only `lich`, so no code change.
- Native check (`build-ui`, isolated menu tour as above, then the Peasant button):
  [native/choose_class_maw_peasant_1600x900.png](native/choose_class_maw_peasant_1600x900.png) and
  [native/peasant_selected_1600x900.png](native/peasant_selected_1600x900.png) (portrait emblem and party slot icon).
  The run's log has no `could not resolve texture` line.
