# MAW class spellbooks (2026-11-08), study

Status: **approved and installed natively (2026-11-09)**, presentation only: `python3 -I scripts/install_runtime.py`
copies `runtime_x2/` into `assets_dev/engine/icons_x2` and prints the table in `game/rules/maw/MawClassSpells.cpp`.
Design, open decisions and the native record:
[devdocs/maw/CLASS_SPELLBOOKS.md](../../../devdocs/maw/CLASS_SPELLBOOKS.md).

The Death Knight line (Death Knight, Death Lord, Lich King) and the reworked Thief line (Thief, Rogue, Assassin, Spy)
know their spells by school mastery under renamed schools (`game/rules/maw/MawClassSpells.cpp`). Today the spellbook
still shows them the original Water, Body and Dark (or Fire, Air, Water and Earth) pages, with "WATER" on the
medallion and Icy Touch drawn as Ice Bolt. This study proposes pages of their own: same skills, spell ids, rules and
saves; only the pictures, school names and tabs change, and only for these two class lines in MAW.

Preview: [index.html](index.html) (interactive: tabs turn pages, a pointer lights a spell as the game does, "Today"
shows the current book). Static composites: `previews/<line>_<school>.png`.

## What it shows

- Seven school pages: Frost, Blood, Unholy; Combat, Subtlety, Poisons, Assassination. Each is the original Water page
  with a new medallion scene and the school's name on the banner (the banner's word removed by taking the lightest
  pixel of the twelve original pages; the name drawn along the banner arc in Liberation Serif Bold).
- Seven school tabs (idle line drawing, selected painted coin) in the original tab frames, stacked from the top.
- Twenty new spell pictures: the twelve Death Knight spells and the Assassin's eight attack spells. The Assassin's
  thirteen ordinary spells keep their original pictures. Spells are placed in mastery order in 4-, 5- and 6-spell
  layouts (`SLOTS` in `scripts/build_mockup.py`).
- Proposed Assassin attack spell names (Firebomb, Blasting Trap, Ricochet Blade, Poison Darts, Acid Flask, Sap,
  Throwing Blades, Death Mark); MAW keeps the mage names. Undecided.

## How it was made

- [CODEX_BRIEF.md](CODEX_BRIEF.md) and [art.json](art.json): `scripts/run_batch.sh` runs five parallel `codex exec`
  jobs with the built-in image generation, inputs `refs/refs_vignettes.png` (original highlighted/normal pairs),
  `refs/refs_medallions.png` and `refs/refs_tabs.png`. Raw generations and prompt records in `raw/`, masters in
  `masters/`. Two retries (Death Breath, a Poison Darts caption).
- Codex paints each spell's highlighted (colour) state; `scripts/build_mockup.py` derives the normal state by mapping
  luminance onto the sepia ramp of six original pictures, keeping the cool-green rune ink, as the originals do.
  Medallion scenes are matched to the tones of the original medallions.
- `python3 -I scripts/build_mockup.py` writes `mockup/` (web assets at x2), `previews/` and `index.html` (from
  `scripts/index.template.html`).

Spend: no paid API calls; 41 image generations on the Codex subscription.

## Native integration (2026-11-09)

Presentation only, MAW's Death Knight and Thief lines only; the record is
[devdocs/maw/CLASS_SPELLBOOKS.md](../../../devdocs/maw/CLASS_SPELLBOOKS.md) §7. `scripts/build_mockup.py` also writes
`runtime_x2/` (lossless x2 PNGs and `skin.json`); `scripts/install_runtime.py` copies them into
`assets_dev/engine/icons_x2` and prints the table for `mawClassSpellbookSkin` (`game/rules/maw/MawClassSpells.cpp`).
Checked in the game (MAW, `testparty apply endgame newclasses`): every class page, tab clicks, hover and selection
highlights, the right-click tooltip, and the Seraphim's standard book.
