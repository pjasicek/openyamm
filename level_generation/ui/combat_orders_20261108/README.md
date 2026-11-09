# Battle orders: study, 8 November 2026

This study comes from a Discord request (puzzleR1, with Tyrkys agreeing; not yet in the triage ledger):
- A per-character priority for what an attack does. For example, a Paladin uses Light Bolt at range and the sword in
  melee, keeping mana for heals. A healer heals when someone needs it and otherwise casts Flying Fist.
- The follow-up spelled out a full chain: heal a friend low on HP → Shrapmetal if an enemy is in melee range →
  Dragon's Breath if there is mana → Lightning Bolt if there is mana → bow.
- As an alternative: key combinations for the quick spells, such as Shift+LMB.

The user also asked for a better way to assign and see the attack and quick spells. It should start from the
spellbook, which would drop its stack of assignment buttons.

**Decision (8 November 2026): A, the orders window.** B and C stay below for reference. Revision 2 of A follows the
user's notes:
- the frame is sliced so its corners stay sharp;
- the window no longer evaluates the party's current state;
- every condition value is set with a slider, including the target distance;
- the "foes caught in the blast" condition is removed;
- the last row can hold instead of attacking with the weapon;
- each order can be switched off without losing its settings;
- the Quick Reference gets an Orders row.

Nothing is built natively.

Open [index.html](index.html) through the local server
(`http://127.0.0.1:8917/level_generation/ui/combat_orders_20261108/index.html`; the fonts do not load from `file://`).
- The buttons at the top switch views and members. Rows and cards can be clicked.
- `?view=today|entry|a|qr|b|c&m=0..4&row=N&export=1` gives the captures in [previews/](previews/).

The mockups are drawn over the native spellbook capture. They use the real spell illustrations (cropped by the study,
in `art/spells/`), the Carved Obsidian menu art, the Fondamento, Arrus and Lucida fonts, and the party faces from the
basebar capture.

## The model

- **Attack** (F, left click, smart left click, and the acting member in turn-based combat) walks the member's
  **orders** from top to bottom. It does the first order whose ticked conditions all hold right now.
- An order is **a spell or a weapon, plus optional conditions**. Each condition has a slider with a sensible range:

  | Condition | Slider | Notes |
  | --- | --- | --- |
  | Target distance | 0–5120 game units, two handles; the right end means "any" | Presets: *In melee reach* (0–407), *Beyond melee reach* (407 and up), *Custom*. The red zone is the weapon reach the game already uses (407.2 units). The first half of the slider covers 0–1024 units, where melee and spread spells such as Shrapmetal are decided. 5120 is the ranged attack distance. Shown in game units, not metres (user, 2026-11-08). |
  | An ally's HP is below | 10–90 % | Heal and similar spells. |
  | Keep SP after casting, at least | 0–80 % | Spells only. Keeps mana for the heals. |

- With no condition ticked, the order is "always".
- Some checks are automatic and need no setting:
  - an order without enough SP is passed over;
  - a cure is cast only when someone has that condition;
  - a buff only when the party lacks it, a debuff only when the target lacks it;
  - Sunray only outdoors by day;
  - Heal goes to the most wounded member;
  - a melee order needs the target in the weapon's reach.

  A heal with nobody to heal falls through to the next order. Today (OY-190) it does nothing and says "Nobody needs
  Heal".
- **The last row is always there and says what happens when no order fits:**
  - **the weapon** (melee in reach, the bow beyond) is the default;
  - **hold** is for pure healers.
- **Hold** does nothing, at the cost a player pays to do nothing by hand:
  - **Real time:** no recovery; the member stays ready. The press goes on to the next ready member, which is what
    clicking that portrait does today. Each member is checked at most once per press, so the press never loops. If
    nobody else is ready, the press does nothing and the status line says "Thalia holds". A 5-tick recovery was
    considered, but it would be a cost that exists nowhere else in the game.
  - **Turn-based:** the queue waits for whoever is at the front, so a holding member must spend the turn. That is the
    existing Pass (`TurnBasedCombatRuntime::passTurn`), which costs the member's melee recovery, as in the original.
- **Hold with Attack held down (cost and responsiveness):**
  - A held Attack does not repeat every frame. It repeats after 0.5 s, then every 0.14 s
    (`HeldActionFirstRepeatDelaySeconds`, `HeldActionRepeatDebounceSeconds`). A holding healer with everyone else in
    recovery adds about seven checks a second; each scans at most five members' HP and SP against a few rows.
    Target finding is unchanged: an attack press already does it.
  - It must not repeat anything audible or visible: no status flash, sound or speech on each repeat. Only the first
    press says "Thalia holds".
  - Correction (implementation): the fast repeat's "a member became ready" trigger reads `hasReadyMember`, which
    ignores recovery (`Party::hasSelectableMemberInGameplay`) and was already true while anyone could act. A holding
    member changes nothing there, and no fix was needed.
- **Quick Cast (Q)** and **Quick Spells 1–4 (F5–F8)** stay single spells with no conditions. They are shown and filled
  in the same window.
- Starting plans (Fighter, Archer, Caster, Healer) and "copy from another member" save typing for five characters.
- Revision 1 showed live "NOW" and "skip: …" states and an "if X attacked now" line. These are **dropped**: the window
  edits rules and does not track the party's current state.
- **Migration:** today's single attack spell becomes one order with no conditions, followed by the weapon. That behaves
  exactly as now. A member with no attack spell gets only the weapon row.

## Where it is opened

| Today | Proposed |
| --- | --- |
| ![Today](previews/today.jpg) | ![Entry](previews/entry.jpg) |

- **Today:** six assignment buttons sit above Close (Attack Spell, Quick Cast and the MMMerge quick spells 1–4). You
  pick a spell on the page, then click a button.
  - The Quick Reference shows the Quick Cast spell.
  - Nothing shows the attack spell or slots 1–4.
  - Correction: the Quick Spell 1–4 keys can be rebound in Settings › Keyboard. `KeyboardBindingPage::Hidden` only
    keeps them off the old two-page keyboard overlay.
- **Proposed:** the spellbook's left column keeps only Close and one **Battle Orders** button (①, new art in the
  style of the existing tiles).
  - **Right-clicking a spell** (②) opens a short menu: Set as Quick Cast, Put on Quick Spell 1–4 (each line shows
    what it replaces), Add to the attack orders, Open Battle Orders.
  - Left click still selects, and a double click casts.
  - The window opens on the member whose book it is; the other members are one click away.
- **Also:**
  - a keyboard action, *Battle Orders* (O is shown; any free key will do, or none by default);
  - Android reaches it through the spellbook as well.

## A · Orders window (chosen), revision 2

![A](previews/a.jpg)

| Ariel: Light Bolt beyond melee reach, keeping 30 % SP | Lys: Incinerate keeping 20 % SP |
| --- | --- |
| ![A Ariel](previews/a_ariel.jpg) | ![A caster](previews/a_caster.jpg) |

| Thalia: Heal below 60 %, otherwise hold | Gerrard: no spells |
| --- | --- |
| ![A healer](previews/a_healer.jpg) | ![A Gerrard](previews/a_gerrard.jpg) |

- Member tabs sit at the top, each with the oval basebar portrait and SP.
- The left side is the numbered order list. Each row shows its conditions as chips, with move and remove buttons
  beside it (rows can also be dragged by the grip). Each order has an on/off tick: an order that is off is skipped but
  keeps its settings (Kestrel's Lightning Bolt in the first capture). The last row has a Weapon/Hold switch. The starting plans are
  under the list.
- At the right, the selected order's conditions are listed: a tick, a slider and the value, in the style of the
  Settings sliders. Conditions that don't apply to the order say so ("spells only"), and a melee
  order's distance is fixed to the weapon's reach.
- Below the conditions is the palette of the member's spells and weapons; a click adds one.
- The quick keys run along the bottom.
- **Frame:** this uses the Settings frame (`omenu_frame.png`) as a nine-slice. The corners and their ornaments are drawn
  at 1:1 and only the plain edge runs and the centre stretch, so nothing blurs at any window size. Revision 1 stretched
  the small `omenu_modal.png` to 2.2× its size, which blurred it. The buttons are sliced the same way. Natively,
  `MenuDesignScreen::skin` can already slice, but with a fixed 8–18 px edge; the frame needs a 120 px edge for its
  corner ornaments.

## Quick Reference: an Orders row

![Quick Reference](previews/quick_reference.jpg)

- **Why not text:** a line like "Heal <60 % → Cure Poison → Flying Fist → hold" does not fit a member column (about 108
  logical units wide).
- **The row:** a new **Orders** row under QSpell shows each member's orders that are switched on, as small spell
  icons in order. The last mark is a faint sword for "otherwise the weapon" or ‖ for hold. A member with no orders
  shows "Weapon".
- **Making room:** the rows below Name move closer together, from 20 to about 18.5 logical units. The table keeps its
  height, so Reputation, Fame and Exit do not move.
- **Details:** hovering over a member's Orders cell (or holding the right button on it) opens the full list: each
  order's conditions, the ones switched off (dimmed) and the quick keys Q and F5–F8.
- **Data:** the mock is drawn over the native capture. Its names, classes, QSpell and Orders rows show the study's
  party; the stats are the capture's.

## B · Order pages in the spellbook (not chosen)

| Kestrel | Ariel |
| --- | --- |
| ![B](previews/b.jpg) | ![B Ariel](previews/b_ariel.jpg) |

- The Battle Orders button turns the book to an extra spread:
  - the left page has the orders, written in ink with the spells' sepia vignettes; the order firing now is in colour
    and circled, and passed-over lines carry a red margin note;
  - the right page holds the quick spells as framed vignettes.
- The school tabs become the party's portrait medallions, so you switch members there. "Back to spells" returns to
  the schools.
- Adding an order or filling a frame turns the book to the school pages in "choose a spell" mode, so the book itself
  is the picker. Clicking the dotted condition words changes them.

## C · Party board (not chosen)

![C](previews/c.jpg)

- All five members side by side: each column has the member's orders as cards, a plan menu (Custom, Fighter, …) and
  the quick keys.
- The card that would fire now glows green, and skipped cards say why.
- Dragging a card reorders it, or copies it to another member. The drawer at the bottom edits the selected card's
  conditions.

## Comparison

| | A · window | B · book pages | C · party board |
| --- | --- | --- | --- |
| Editing conditions | roomy, all options visible | in-text popovers, least room | drawer, one row of chips |
| Seeing the whole party | one member at a time | one member at a time | everything at once |
| Fits the game's look | Obsidian, like Settings | most in character | Obsidian |
| Long lists (6+ orders) | fits | page fills at about 6 | columns fill at about 6 |
| Native work | new overlay, standard widgets | spellbook page mode, ink layout, picker mode | widest; drag and drop |

**Chosen:** A, with the spellbook entry and the right-click menu.

## Open points

- **Key combinations** (the alternative in the request): make Quick Spell 1–4 visible on the keyboard settings page and
  allow modifier + mouse bindings (Shift+LMB, Ctrl+LMB). Whether bindings already take modifiers is not checked yet.
- **Data:** each character's `attackSpellName` becomes an order list (saved per character), with the migration
  described above. `quickSpellName` and `extraQuickSpellNames` stay as they are.
- **Hirelings** (MM9) keep their own attack and are not in the window.
- **MAW:** the checks are rules-neutral. SP and refusals go through the same `castRefusal` and `manaCost` paths that
  `cannotCastAttackSpell` uses today.
- The SP costs and spell lists in the mockups are illustrative.

## Implementation (2026-11-09)

Layout A is implemented natively; see [Battle orders](../../../devdocs/BATTLE_ORDERS.md). Distances are in game units.
The mockup page still shows metres. The previews here are the study's; native captures are in [native/](native/).

Native captures (MM8, the default one-member party, 1600 x 900):

| Window (readable text, larger palette) | Spellbook spell menu (quick right click) |
| --- | --- |
| ![Window](native/window_slider.jpg) | ![Spell menu](native/spell_menu.jpg) |

| Quick Reference Orders row | Its pointed member's list |
| --- | --- |
| ![Orders row](native/quick_reference_orders.jpg) | ![Tooltip](native/quick_reference.jpg) |
