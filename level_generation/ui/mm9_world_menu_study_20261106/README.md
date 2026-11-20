# MM9 in the menus: concept study (2026-11-06)

Concepts and art for bringing MM9's world into the shared menus. MM9's continent is **Chedian** (`worlds/mm9/world.yml`
`completion.continent`). Nothing here is installed; the integration notes list what each part would change.

## 1. New game: four worlds

[`final/new_game_four_worlds.png`](final/new_game_four_worlds.png) (drawn by `newgame_mockup.py` over the approved
menu study's capture `menu_study_20260928/previews/r03-worlds.png`): Choose Starting Continent with four cards of 302
instead of 403 pixels (at 1600x900): Enroth, Antagarich, Jadame, Chedian, the same globe, game line, name and start
line as today. The fourth card says "Might and Magic IX · Chedian · Begin on the Isle of Ashes".

New art: [`final/omenu_continent_chedian.png`](final/omenu_continent_chedian.png) (444x444, like the other
`hud_x2/menus/omenu_continent_*.png`), the Chedian globe in the same gold frame and glass: fjords, a snowy north, green
inlets in the south and the volcanic Isle of Ashes off the south-west coast (`raw/chedian_globe_v2.png`; v1 is the
alternative). Replaced the same day (user) by `raw/chedian_globe_map_v2.png`, drawn from MM9's own world map
(`refs/chedian_map_mm9.png`: Chedian, Framon, Sturmford/Drangheim, Guberland, the Isle of Ashes); the first globes'
invented coastline is kept in `raw/` only.

Integration: `engine/ui/gameplay/continent_selection.yml` gets a fourth `…Button / Illustration / Name / Game / Start`
group and narrower card widths; the card is shown only when the MM9 world is mounted and offered as a start (the plan is
to offer it once MM9 is finished). `worlds/mm9/world.yml` `start` is `guberland.blv` today; the card's start line follows
whatever it is when MM9 is offered (MM9 itself starts on the Isle of Ashes).

## 2. Dimension Door: four portals

Today `ui/gameplay/dimensional_travel/tpglobal.bmp` (640x480) is one portal, split into three hover zones in
`GameplayUiRuntime.cpp` `resolveDimensionDoorDestinationOverride` (Jadame 0-213, Enroth middle, Antagarich 427-640);
hovering draws `tpjadam1` / `tpenroth1` / `tpantag1` (the portal showing that place) from
`town_portal_switch.txt`. The concept redraws the screen with **four portals in a row**, one per continent:

- [`final/dimension_door/tpglobal4.png`](final/dimension_door/tpglobal4.png): the base, all four portals misty
  (1280x960, x2 of 640x480; `raw/door_base_v2.png`, generated from the original screen with a four-portal layout guide).
- `final/dimension_door/tp{jadame,enroth,antagarich,chedian}4.png`: the hover pictures, each its portal lit with its
  destination; [`all_lit.png`](final/dimension_door/all_lit.png) shows all four at once. Jadame, Enroth and Antagarich
  reuse the original views (`tpjadam1`, `tpenroth1`, `tpantag1`, soft-edged into the new portals); Chedian's view is new
  (`raw/chedian_vista_v1.png`: a fjord town with a longship under an aurora).
- [`final/dimension_door/zones.json`](final/dimension_door/zones.json): per destination its hover picture's native box
  and its hit zone, four columns of 160 (Jadame, Enroth, Antagarich, Chedian, left to right).
  [`review/door_hover_chedian_zones.png`](review/door_hover_chedian_zones.png) shows the hover over Chedian and the zones.
- `door_compose.py` builds all of it from the base, the measured portal ellipses and the four views.

Integration: a fourth Dimension Door destination (Chedian) in `town_portal_switch.txt`, and the hit zones moved out of
the hard-coded `resolveDimensionDoorDestinationOverride` into data (the zones above). With MM9 not mounted the screen
keeps today's three-way portal and pictures, so MM6-MM8 alone see no change. Optional polish: repaint the three old
views at the new resolution (they are upscaled 640x480 originals and look softer than Chedian's).

## 3. Party creation: a world filter in the portrait picker

[`final/portrait_picker_world_filter.png`](final/portrait_picker_world_filter.png) (drawn by `picker_mockup.py` over the
party creation study's `shots/popup-portraits.png`): beside All / Male / Female, a WORLD group: All worlds · Enroth ·
Antagarich · Jadame · Chedian. Shown with Chedian selected: MM9's 16 playable portraits (`9pc01`-`9pc16`, rows
9001-9016) by race (Human, Elf, Goblin for MM9's half-orcs, Dwarf). The four liches (9019, 9020, 9023, 9024) are not
offered at start today and would appear once they are. The two filters combine (Chedian + Female).

Integration: each `character_data.txt` row needs its world. Only some of it follows from the face prefix (`7pc` MM7,
`9pc` MM9); the `pc`, `malea`-`maleh`, `girla`-`girld` and other rows need checking one by one, so an explicit `world`
column, filled once, is simpler and safer. The chips list only mounted worlds; "All worlds" stays the default.

## Implemented (2026-11-06)

The user approved the concept and asked for it to be implemented with MM9 as a fixed part of OpenYAMM (not optional).

- **New game:** `engine/ui/gameplay/continent_selection.yml` is the four-card screen (cards 158 wide, gap 12, the three
  cards' old span); `NewGameScreen::drawContinentSelection` draws Enroth, Antagarich, Jadame, Chedian. A card is
  selectable when `continentOffered` finds its `character_selection.yml` row, its `continent_settings.txt` start map and
  that map in its world's package. Chedian: selection row 5 `chedian` (every base class but the Necromancer, every race
  but the undead), continent row 5 starting in Ravensford's training camp (`bootcamp.blv` StartPoint0, 323 -8494 1291,
  yaw 1530), card line "Begin in Ravensford", globe `hud_x2/menus/omenu_continent_chedian.png`. A new game may now start
  on an indoor map (`startNewSessionFromCharacterCreation` checks for any scene runtime, as the debug start does).
- **Dimension Door:** `ui/gameplay/dimensional_travel/tpglobal4.png` and `tp{jadame,enroth,antagarich,chedian}4.png`
  replace `tpglobal.bmp` and the three hover pictures; `town_portal_switch.txt` TPGlobal rows carry the hover pictures'
  native boxes and a Chedian row (6); `resolveDimensionDoorDestinationOverride` gives each portal a 160-wide column.
  Chedian lands on the Isle of Ashes (its start point) until MM9 key 28 (qbit 90028: the cinema has sailed the party
  away), then at Sturmford where the boat lands (4992 -17546 247, facing 180).
- **Portrait picker:** `character_data.txt` has a `World` column (mm6 for `male*`/`girl*`, mm7 for `7pc`, mm9 for
  `9pc`, mm8 for the rest, MMerge's own MM8-style additions included); `CharacterDollEntry::worldId`; the picker shows
  WORLD chips (All worlds, then each world with offered portraits) beside All / Male / Female, combined with them.
- Checks: unit tests (continent rows, Chedian selection, four door destinations with zones and pictures, portrait
  worlds); real-game menu tours (four cards, Chedian party creation, the picker filtered to Chedian, a Chedian start in
  the training camp). The Dimension Door screen itself was checked through its data and the composed art, not in a
  game capture.
