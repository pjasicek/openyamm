# Solo run: Talents page for talent tree v2. Study, 14 November 2026

Design only. These are two layouts of the Talents page for the proposed
[talent tree v2](../../../devdocs/maw/solo_sim/proposals/TALENT_TREE_V2.md): new rows, a shared Bloodthirst row,
five keystone slots and the innate Lone Discipline. The three trees are **Arms**, **Archery** and **Arcana**. Both build on the page that exists now
([TALENTS.md](../../../devdocs/solo_action/TALENTS.md), Stage 4: layout A from
[the first study](../solo_talents_20261113/README.md)) and use the approved
[Carved Obsidian overlays](../obsidian_overlays_20260928/README.md).

Open `mockup_a.html` or `mockup_b.html` from disk. Each file is self-contained (inline CSS and JS, with art and fonts in
this folder) and scales the fixed 1024 × 768 screen to the window. Hovering a row, a socket, the points or Lone
Discipline shows it in the detail card under the trees (the rank's effect now and at the next rank); a click keeps it
there. URL parameters: `?tip=row:sweeping` (or `row:cleave`, `ks:3`, `points`, `lone`) keeps an entry in the card, and
`?slot3=open` leaves keystone slot 3 to be chosen (`row:multishot` shows Multishot, `row:frenzy` Onslaught). In B, `?view=trees` opens the Trees sub-page and `?pick=0..4` opens
the picker on a slot. `./shoot.sh` writes the captures to [previews/](previews/) with headless Chrome. `prepare_art.py`
copies the existing art: the native Skills page capture (revision 03) for the frame, paperdoll and portrait row, the
skills surface, tab buttons, frame9, the solo HUD study's icons, its end-cap socket (masked round, used as the keystone
socket) and seal, and the Lich portrait `pc27-01`. Multishot uses the Shrapmetal spell icon (`spell_shrapmetal`, already copied), a spread of
projectiles. The fonts are the game's Create, Lucida, Smallnum and Fondamento.

**The user's decisions of 2026-11-14,** applied to both mockups the same day:
- No Legend lines and no Legend points. Talent points come only from levels (one per 10 levels then; one per 15
  since the third round, below).
- Whirlwind is dropped from the Arms tree (then called melee).
- Cleave strikes in a 120° arc in front (±60°), and Sweeping Blows uses the same arc. The cards say so.

The space the Legend panel took gives A its fixed detail card back (B's Trees sub-page has the same card).

**The user's further decisions of 2026-11-14,** applied to both mockups the same day:
- **The trees are renamed** for what they train, because a character can and will combine them: Melee is now
  **Arms**, Ranged **Archery** and Caster **Arcana**. "Any tree" stays (Bloodthirst, Lone Discipline). The mockups
  use no "role" wording.
- **Keystones are gated by tree points, not by class:** Warlord needs 10 points in Arms, Deadeye 10 in Archery,
  Archon 10 in Arcana; Unbroken is for anyone; the Oath stays the class's own (the Death Knight has none since the
  fourth round, below). Every
  keystone card and picker entry shows the requirement and whether this character meets it ("needs 10 points in
  Arcana: you have 13 — available"). Vardis meets Arms (17) and Arcana (13), so Archon is open to him; Deadeye needs
  10 more points in Archery (he has none).
- **Multishot replaces Volley** (Archery, active, 3 ranks): a shotgun of 2 / 3 / 4 bow attacks at once across a ±30°
  cone, 75 % each (with Grandmaster Bow each carries its extra arrow). Every arrow hits the first monster in its line:
  point-blank all land on the target, against a spread group they split. Cooldown 12 / 10 / 8 s.
- **Steady Aim** is +5 % Luck per rank while standing still (was 3 %).
- **Purify and Mana Font are removed** from the Arcana tree (rows and cards). Vardis's 5 points from them went to
  Attunement (4 → 5) and Overload (0 → 3), with 1 left unspent; his spending was redone in the third round (below).
- **Frenzy becomes the passive Onslaught (Arms):** each kill gives a stack of +1 % attack speed, up to 10 / 20 / 30 stacks
  by rank (+10 / 20 / 30 %); the stacks last 30 s (user, 2026-11-14) and every kill refreshes them. Its row is drawn as a passive and it has no
  action-bar key. Vardis's actives sit on keys 1 to 3: Cleave, Charge, Blink (Disengage is unlearned since the third
  round).

**The user's decisions of 2026-11-14, third round,** applied to both mockups the same day:
- **One talent point per 15 levels** (was 10). The level-500 Death Knight has 33 points; the next comes at level 510.
  All rows together cost 65 points, level 975 at this rate. The points card says so.
- **Keystone slots stay one per 150 levels** (150 / 300 / 450 / 600 / 750). The points card, a locked slot's card and
  B's picker on a bound slot say "one per 150 levels".
- **Archery is bows only:** Multishot, Piercing Arrows, Pinning Shot, Disengage and Deadeye never affect a Dragon's
  breath. Deadeye reads "+30 % bow damage (not a Dragon's breath); Piercing Arrows at 75 %". The Archery column header
  carries "bows only", and every Archery card's kind line reads "Archery (bows only, never a Dragon's breath)".

**The user's decision of 2026-11-14, fourth round,** applied to both mockups the same day:
- **Lichborne is removed entirely.** The Death Knight has no Oath keystone any more; the other classes keep theirs.
  Lichborne is gone from both mockups, B's picker and every card. Where the keystones left are listed (an open or
  locked slot's card in A, B's picker), a last line says "Oath: the Death Knight has none (the other classes
  each have their own)". Its icon (`spell_toxiccloud`) is still copied by `prepare_art.py` but no longer used.
- **His keystones are now Unbroken (slot 1), Warlord (slot 2, 17 in Arms) and Archon (slot 3, 13 in Arcana).**
  Archon is bound rather than slot 3 left open, because it shows how a card warns about a keystone that does little
  for this character: its "For you" line is red ("nothing: it works only through Mana Shield, which a Death Knight
  does not train") with "In practice a weak pick for him; it costs no points". It is the only keystone left that he
  can bind (Deadeye needs 10 points in Archery), so he takes the free slot. The `?slot3=open` variant still shows
  slot 3 waiting, with Archon offered and the same warning.

**The character in both mockups:** Vardis, a Death Knight (Lich King), level 500, on Beyond Madness. He has 33 points,
all from levels, and has spent all 33: Arms first, 17/20 (Weapon Training 5, Cleave 3, Sweeping Blows 3, Onslaught 3,
Charge 3; no Shield Wall, because he fights with a two-handed sword), then Bloodthirst 3/3, then Arcana 13/22
(Attunement 5, Resolve 5, Blink 3), which keeps him above Archon's gate of 10. Archery is 0/20 and Overload 0/3.
Nothing is left to spend, so no row is teal and the cards say "No points left: the next at level 510". His keystones are
Unbroken (slot 1, level 150), Warlord (slot 2, level 300) and Archon (slot 3, level 450; a weak pick, see above); slots
4 and 5 open at levels 600 and 750, and only Deadeye is left for them. A Death Knight has no Oath. Spell Surge is
locked (no magic school at Master) to show the locked state. All numbers come from the proposal's first values. Icons are existing game art standing in.

## Mockup A: the built layout, extended

![A](previews/a.png)

This is the page as built, top to bottom: a header with the points; a **keystone strip** with a label and five
sockets (filled gold, open teal with a pulsing "+", locked grey with a padlock and its level); the three tree columns,
unchanged in kind (icon with actives double-rimmed, name, rank pips, n/max); an **Any tree** line with Bloodthirst and
Lone Discipline; and the **detail card** of today's page, a frame9 card across the page under the trees. It shows the
hovered entry (name, kind and rank on one line, then the effect now, at the next rank, a keystone's change, a refusal
and the click hints); a click keeps an entry there, and with nothing hovered it shows the points. The paperdoll and
portrait row stay.

Captures: [a](previews/a.png) (the card shows the points); [Sweeping Blows](previews/a_tip_sweeping.png) (the
120° arc, the rank's effect and Warlord's change); [Cleave](previews/a_tip_cleave.png) (the 120° arc in front);
[Onslaught](previews/a_tip_frenzy.png) (now a passive: attack-speed stacks on kills);
[Multishot](previews/a_tip_multishot.png) (the next rank's cone of bow attacks); [slot 4](previews/a_tip_slot4.png)
(locked; only Deadeye is left and needs 10 more points in Archery; the no-Oath line);
[Archon](previews/a_tip_archon.png) (bound in slot 3, its red "For you" line: nothing without Mana Shield, a weak
pick); [slot 3 open](previews/a_slot3_open.png) (Archon available "but it does nothing without Mana Shield", Deadeye
10 points short, no Oath).

The strip labels a bound keystone by its gate (Anyone, Arms, Arcana; a class with an Oath would read "Oath"). A
keystone's card adds its requirement line ("needs 10 points in Arms: you have 17 — bound in slot 2"); an open or
locked slot's card lists the keystones left, the available ones in green and the others in red with the points still
missing, then the line that the Death Knight has no Oath.

Decisions this implies:
- The header shows the points from levels, the points spent and the points left to spend. The next point's level,
  the spending by tree and what every row together costs are in the points card.
- Sweeping Blows sits under Cleave, indented with a hook, because it needs Cleave. It is the only dependency the
  proposal states, so it is the only indented row.
- Bloodthirst gets an "Any tree" line of its own rather than a fourth column.
- Lone Discipline is a row with an INNATE tag, no pips and no n/max. It cannot be clicked to learn.
- A row is teal only while a point could buy it; with none to spend, Vardis's page has no teal. Shield Wall's card
  says in red that a two-handed fighter has no shield to raise.
- Each tree has six rows now (Arcana lost Purify and Mana Font), so two row heights stay empty above the Any tree
  line; the layout is unchanged and could take two more rows per tree. The detail card has room for five lines,
  which every entry fits.

## Mockup B: keystones get a page of their own

![B](previews/b.png)

The Talents page gains two sub-tabs: **Trees** and **Keystones · 3/5**. The Keystones sub-page hides the paperdoll and
uses the whole 4:3 page. On the left, the five sockets sit on a ring around the character's portrait. The ring is also
the level track from 150 to 750: it is gold up to the current level (a "level 500" marker), with ticks every 50 levels
and a dashed gap with the seal before the first slot. Lone Discipline is shown under the portrait as the innate
"socket you start with". On the right is the **keystone picker** for the selected socket. It lists Unbroken, Warlord,
Deadeye and Archon, each with its requirement beside its name ("for anyone", "needs 10 points in Arcana: you have
13") and its effect, and under them the line "Oath: the Death Knight has none (the other classes each have their
own)"; for another class its Oath would be an entry of its own. Each entry is tagged THIS SLOT, SLOT n
(bound elsewhere), AVAILABLE (CHOOSE when it is offered for an open slot) or NEEDS n MORE (greyed, with the requirement
in red), and the highlighted entry adds a green "For you" line with the effect on this character (red when it does
little for him, as Archon's), or, when the gate is not met, the points still to spend in that tree.
The Trees sub-page is A without the strip (rows a little taller), with five small sockets beside the sub-tabs as a
reminder (clicking one opens the picker on that slot) and A's detail card under the trees.

Captures: [b](previews/b.png) (slot 3 selected, Archon bound with its red "For you" warning, Rebind dim);
[b_choose](previews/b_choose.png) (slot 3 open: the sub-tab carries a "new" badge, the empty socket glows, Archon is
offered with its warning and the button reads "Bind Archon"; Deadeye needs 10 more); [b_slot4](previews/b_slot4.png)
(the picker on locked slot 4: nothing available, Deadeye needs 10 more points in Archery); [b_trees](previews/b_trees.png) (the card shows the points);
[b_trees_tip](previews/b_trees_tip.png)
(Sweeping Blows in the card).

Decisions this implies:
- A keystone is a deliberate act ("Bind"), not a click on a row. Binding is for the whole run. Rebinding at a training
  hall is shown as an open rule.
- A new slot announces itself (a "new" badge on the sub-tab and a glowing socket), like the "new" Talents tab of the
  first study.
- Keystones whose tree gate is not met are listed but cannot be chosen, with the points still missing, so the player
  sees what 10 points in another tree would open.
- The ring sets keystones apart from ranks visually. It also leaves room to grow: a longer list, longer effect texts,
  or a sixth slot.

## Recommendation

Use B's Keystones sub-page with A's Trees page (B's Trees sub-page is that). The keystone choice comes five times in a
run and is the largest effect, so it deserves the full width and a "For you" line. The ranks are bought often and
read best all at once. A's strip is enough for a summary, but its detail card cannot hold a list of four or five
keystones to compare.

## Awkward to show (feedback on the proposal)

- **Five slots, four keystones for a Death Knight.** With the tree gates, a character of a class with an Oath and
  10 points in each tree can fill all five slots (Unbroken, its Oath, Warlord, Deadeye, Archon). Without Lichborne a
  Death Knight has only four keystones for five slots, so his fifth slot can never be filled: should it offer
  something else, or should the page show it as "no keystone left"? Vardis has three bound, one of them Archon, which
  does nothing without Mana Shield; Deadeye waits on 10 points in Archery. A gate that the class can meet but cannot
  use (Archon without Mana Shield) is worth a second look too. Open: does a respec at a training hall that
  drops a tree below 10 unbind its keystone, or refuse the respec? And is "points in a tree" counted with Bloodthirst
  (any tree) or without? The mockups count tree rows only.
- **The Dragon and Archery.** Archery is bows only now, so no talent raises a Dragon's breath. Open: does the Dragon
  need a breath row of its own (Arcana, or its Oath), or is the breath meant to grow with skill alone?
- **Points against rows.** All rows together cost 65 points (Arms 20, Archery 20, Arcana 22, Bloodthirst 3), the
  budget of level 975 at one point per 15 levels. The proposal expects the end of Beyond Madness at about level 800,
  53 points, so a character finishes with about 12 rows' worth unbought: the old surplus is gone and choices stay
  real. A point comes every 15 levels, so the page shows "0 to spend" most of the time; whether a new point deserves
  the same "new" badge as a new keystone slot is open.
- **Two respec rules on one page.** Tree ranks are reset at a training hall, and the proposal does not say how
  keystones are rebound. The page has to show each rule where it applies.
- **Effects that depend on live numbers.** Sweeping Blows depends on the weapon skill (40 % + 0.25 % per point),
  a class's Oath may depend on its stats, and the shared ×0.25 clamp on Oath × Shield Wall × Unbroken's share (a Death
  Knight has no Oath term). Each card has to compute these for the character.
  Unbroken is not a multiplier (it halves part of a hit), so "its part" of the clamp product cannot be shown as a
  number.
- Sweeping Blows needing Cleave is the only dependency, so the indent is used once. Piercing Arrows might be expected
  to need Multishot in the same way; the cards also do not say whether Multishot's arrows pierce.

## Files

`mockup_a.html`, `mockup_b.html` (self-contained), `previews/` (1024 × 768 captures), `shoot.sh`, `prepare_art.py`,
`art/` and `fonts/` (copied existing art; Fondamento is under the OFL, `fonts/fondamento_ofl.txt`).

## Viewer

`viewer.html` shows both mockups live (scaled to fit), switches between their views with tabs and lists what each
shows, with the captures. It loads `mockup_a.html`, `mockup_b.html`, `art/`, `fonts/` and `previews/` by relative
path, so it works opened from disk. Published: https://claude.ai/artifact/EjMzyhyiBgqNZqTEWSovkR (private to the owner).
