# MM9 formation builder (study, 2026-11-06)

**Accepted by the user on 2026-11-06.** This is the design to implement (phase 10 of the hireling plan).

[Gallery](index.html) · images in [images/](images/) · re-render with `./render.sh` (headless Chrome; the backgrounds
are the hireling study's revision 2 renders, `../mm9_hirelings_20261106/images/R2_*.png`).

The user asked for MM9's formations (2026-11-06): a button under the minimap, MM9 world only, opening a formation
builder, a 3 × 3 grid onto which the members are dragged. MM9's own screen and rules are in
`devdocs/mm9/MM9_HIRELINGS.md` section 10 (art `INTERFACESCREENS/FORMATION/`, `PARTYORDERCOORDS.txt`); the
implementation is phase 10 of `devdocs/mm9/MM9_HIRELINGS_PLAN.md`.

- **Panel:** the basebar's Obsidian panel (the same frame pieces and stone), centred, the game dimmed behind it; title
  "Party Formation"; Fondamento for the title, the rank names and the Cancel / Accept buttons
  (`obsidian_button_tab_*`).
- **Grid:** MM9's: front, middle and rear rank, left to right, one member a cell; 54 × 66-unit cells with the members'
  oval faces (40 × 54, as the hireling rail's), the PCs and the hirelings alike (a hireling's cell has the small brass
  mark in its corner). Under each rank name the chance a monster's blow lands there (70 / 20 / 10 %, MM9's).
- **Placement:** members join on the lowest free cell (five PCs and three hirelings shown, MM9's order). A portrait is
  dragged onto an empty cell (no swaps, as MM9); Accept refuses, and says so in the instruction line, a layout with
  someone behind an empty cell in the same column. Cancel or Escape keeps the old layout. Pointing at a face shows the
  member's name (MM9).
- **Button:** the MM9 world's formation button takes the first place of the row under the minimap (the combat-log and
  followers buttons are hidden in MM9): a carved slab with a 3 × 3 grid of brass diamonds, the front rank gold.
  MM9 opens the screen with F as well; the keyboard binding is part of the implementation.

The screen pauses the game, as the other Obsidian overlays (MM9's behaviour was not traced; the proposal stood).
