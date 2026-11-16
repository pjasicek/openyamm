# Solo run: talent tree v3. Mockups, 15 November 2026

Design only: a bigger talent tree for the MAW solo run, its point budget, what every node does, and how the result
stands against a party of five. Asked for by the user after the solo simulation was fixed
([direction](../../../devdocs/solo_action/POWER_CURVE_DIRECTION.md) §7,
[curve results](../../../devdocs/maw/solo_sim/CURVE_RESULTS.md)). Nothing here is in the game.

Viewer (every mockup live, its notes and captures): `viewer.html`, published privately at
<https://claude.ai/artifact/BAHdNVgqL1aTPqvLiD4fFs>. Republish it with the files of this folder (the three
`mockup_*.html`, `tree.css`, the four `.js`, `fonts/`, `art/`, `previews/`) after any change.

## The mockups

All three are fixed 1280 × 720 screens scaled to the window, and read the same data.

| File | What it shows |
| --- | --- |
| `mockup_tree.html` | **A, columns:** the planner as five columns of rows, the built Talents page extended. Class, difficulty and level at the top; click a row to learn a rank, right click to take it back; the side shows the hovered node, what the build does, the build against a party of five, and the keystone sockets. |
| `mockup_web.html` | **B, constellation:** the same planner as a wheel: Second Wind at the hub, a path per arm, a ring per tier. |
| `mockup_curve.html` | **C, the party line:** solo strength ÷ party strength by level for a class and difficulty (MAW alone, with the early cut, with an ordinary build's talents) and the budget table: points, keystone slots, cut, talent strength, and how much stronger a solo's monsters would have to be to keep "never stronger than a party". |

URL parameters: `class` (a build id of `tree_data.js` `classes`, or `typical` in C), `diff` (`maw`, `nightmare`,
`doom`, `insanity`, `madness`), `level`, `build=empty` (A and B start without ranks), `tip=<node id>`.
`./shoot.sh` writes the captures of `previews/` with headless Chrome.

## The draft

`tree_data.js` is the design; change it there and every mockup follows.

- **Points:** one every 2 levels up to level 20, then one every 5: 10 at level 20, 26 at 100, 106 at 500, 166 at
  804 (the simulated end of Beyond Madness), 206 at 1,000.
- **Second Wind:** free at level 1. Regeneration, strong out of combat (4 % of HP and SP a second) and weak in it.
- **Five paths, five tiers each:** Arms (melee), Archery (bows), Arcana (magic), Bulwark (any class: staying alive),
  Lore (any class: skill unlocks and tricks). A tier opens with 5, 15, 30 or 45 points in the tiers below it.
- **75 nodes, 395 ranks:** the 19 built talents and 56 new nodes. Kinds: active skills (16 new: Ground Slam, War
  Cry, Rend, Bladestorm; Rain of Arrows, Hunter's Mark, Leap Back, Barrage; Arcane Ward, Mana Tide, Stasis;
  Recuperate, Deflect, Stone Form; Lure, Smoke Bomb), passives, notables (three ranks), small nodes (10 to 20 ranks,
  about 1 % a rank) and skill unlocks (Bow, Dodging, Armsmaster, Meditation, Shield, Hedge Magic: any class trains
  the skill to Expert, Master, Grandmaster).
- **Keystones:** a slot per 150 levels (six by level 900), no points. Cheat Death and Unbroken (built) and six new
  trades: Glass Cannon, Juggernaut, Blood Pact, Duelist, Spellblade, Wayfarer.
- **What the user named:** Deflect answers homing missiles, Lure pulls one monster out of a group, Recuperate and
  Second Skin replace potion spam, Bow Training gives every class the bow opener.
- **The early cut** (`earlyCut`): monster HP and damage divided by 2.5 up to level 5, 2.0 at 10, 1.7 at 20, 1.55 at
  30, 1.3 at 50, nothing from 75.

## The build model

`tree_core.js`. A node's effect (`e` in the data) is a fraction per rank on damage, speed, area hits, HP, damage
taken, other toughness or sustain. A build's damage and toughness multiply up from its ranks, and its strength is
the root of damage × toughness: the simulation's unit, monster HP and damage both scaled by that factor. The solo's
standing against the party is the simulation's ratio for the class at that level (`party_line_data.js`, written
from `output/maw_solo_sim_v2/party_line.json`) × the early cut × the build's strength.

The values of actives, area hits and sustain are cautious guesses. The ordinary builds (`plans`) come out at about
×1.1 at level 20, ×1.3 at 100, ×2.3 at 500 and ×3.3 at 804.

## What the mockups show

- With the cut, a typical solo stands at the party line from the start to level 50 on MAW and Nightmare, and a little
  under it on Doom and above.
- MAW alone puts a typical solo at 1.3 to 1.7 times a party from level 150 on. With an ordinary build of this tree it
  is 1.7 at level 150, 2.8 at 300 and 3 to 4.5 after: the tree as drafted breaks the rule unless a solo's monsters
  grow by that factor (the last table column of C), the nodes shrink to trades, or the rule only binds the solo
  run's own additions where MAW has not already put the solo ahead.
- Classes differ far more than the tree moves them: a Dragon at 4 to 10 times a party, a Priest at 0.2 to 0.5.

## Open

The four decisions listed in the viewer: how the rule is kept, the class spread, columns or constellation, and the
node values (to be measured by the solo simulation before anything is settled). Icons for the new nodes are
monograms; the built talents use their game icons (`art/`, copied from `assets_dev/engine/icons_x2/`).
