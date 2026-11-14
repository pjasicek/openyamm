# Solo action mode: HUD study, 13 November 2026

A possible mode in which the player controls **one character** in first person, with a sword and shield drawn on
screen, and fights by pressing keys: swing, cast, buff, heal, use abilities. The references we settled on are Skyrim
(one character, perks, a minimal HUD), Dark Messiah of Might and Magic (first-person sword and shield, kick, block),
Vermintide 2 (crowd melee, one career skill with a recharge bar) and Avowed (a clean modern first-person RPG HUD;
criticised for only six ability keys and a radial menu that pauses combat). The user likes WoW's unit frame
(portrait circle with a level badge, name bar, green HP and blue mana bars with numbers, buffs under it).

This is a design study. Nothing is built natively and nothing in `assets_dev` changes.

Open [index.html](index.html) directly from disk (Chrome loads the fonts from the `fonts/` folder beside it).
The tabs switch views; `?view=a2|r|a|b|c|d|today|bar|talents|portrait&export=1` shows one view alone at 1600 × 900, and
`./shoot.sh` writes all of them to [previews/](previews/) with headless Chrome. The HUD views have a switch for the
placeholder sword and shield and a slider for the crosshair's recovery brackets.

## Left bar and self combat text (user, 2026-11-13)

After seeing the native 2 × 5 bar the user asked to move the bar under the unit frame, as one column of 1–0 with bigger
slots, and to consider WoW's scrolling text about the player. `?view=a3` (the default tab, `Left bar`):

- `lbar=corner|knobs|split|frame`: the potion and scroll sockets on the medallion's upper-left rim (mirroring the
  level coin), beside the column's foot, outside the column at the split between 5 and 6, or on the unit frame's right
  end.

**Chosen (user, 2026-11-13): the left bar (`view=a3`) with the sockets on the medallion's upper-left rim
(`lbar=corner`).** Slot size and the self text placement are still open; the defaults shown are 58 px and by the
crosshair. **Built in game on 2026-11-13** (devdocs/solo_action/HUD.md, "Left-bar layout"; captures `native/left_*.png`),
with the clock as a small plate on the minimap's lower rim (the user's change) instead of hidden.

`topbar=right|left`, `clock=below|off` (user, 2026-11-13): the top bar (gold, food, the menu icons) moves to the
top-right corner, the minimap goes under it without its clock, and the clock becomes a small plate on the minimap's bottom rim, as WoW shows it (`clock=rim`, the user's pick; `off` and `below` for comparison). The unit
frame, its sockets and the column rise by 46 px into the freed top-left corner, so the column also fits 64 px slots
(`lslot=64`); with the top bar at the top left only 52 and 58 fit.
- `lslot=52|58`: slot size. 64 px does not fit ten high at 900 px.
- MAW's map progress moves into the unit frame's bottom band, with its tab at the box's right end. Only the status
  line stays at the bottom centre.
- `sct=center|frame|off`: the self combat text (heals green, damage taken red with what was blocked or resisted,
  SP blue, conditions amber, fading grey). It sits by the crosshair (below right, where WoW draws it on the
  character) or under the buffs. Solo only.

## A refined (user's pick, 2026-11-13)

**Chosen 2026-11-13:** the unit frame (`frame=wow`): single brass ring, the whole head in the medallion. Not to be
implemented yet; the attacks come first. The basebar layout is still open. The implementation plan is
[devdocs/solo_action/HUD.md](../../../devdocs/solo_action/HUD.md).

The user chose **A** (the unit frame top-left) with three asks: the whole portrait visible, the face joined to its HP
and mana bars in the Obsidian style, and a narrower basebar (two rows, or slimmer sides) that keeps MAW's map progress.
The `A · Refined` tab (`?view=a2`, the default) answers them with switches:

- `frame=wow|full|arcs`: the **unit frame** (default since the user's WoW references: one box in the native frame pieces, `art/frame9.png` from `make_frame9.py`, with name, HP and SP bars and centred numbers, the oval portrait medallion overlapping its left end, the level on a coin), **Portrait panel** (one Obsidian panel holding the whole portrait at the party frame's size in
  its oval rim, the level on the rim's top diamond, name, HP and SP bars with numbers and the buffs) or **Arcs and
  plate** (the approved split-arc portrait cell, unchanged, with a plate joined to its right for name, exact numbers
  and experience).
- `bar=rows5|slim|rows10`: **2 × 5** (keys 1–5 over 6–0, 330 px wide, full-size sockets), **one row with slim
  sides** (9 px border, sockets scaled to the bar), or **2 × 10** (a Shift row).
- `maw=0|1`: MAW's installed map progress (GameplayMapProgressBar: violet channel in the top stone band, the tab with
  `38.5 % · 112 / 292` on the right corner, the red revival notch); the status line moves above the tab.
- `echo=0|1`: the thin HP/SP strip on the bar.
- `arms=...`: the drawn placeholder or in-game captures of the same scene with the private Oblivion arms (sword and
  shield idle, swing, block, claymore, cast). Those captures live in the git-ignored
  `reference/oblivion_poc/preview/hud_scene/`; `oblivion/` here is a local symlink to it, excluded through
  `.git/info/exclude`. Never copy them into this folder.

## Recommendation (first round)

**R: keep the face, but small and top-left.** A compact unit frame in the upper left (the approved oval portrait and
rim, the level in the diamond, name, HP and SP bars with numbers, one buff list under it), the ten-slot action bar
bottom-centre in the basebar's Obsidian panel with the potion and scroll sockets at its ends, a thin HP/SP echo on top
of the bar, and recovery brackets around the crosshair.

![R](previews/r.png)

Answers to the four questions:

1. **Do we need the portrait?** Yes, but not as the bottom centrepiece. In Might and Magic the face *is* the
   character, and the game shows conditions (poisoned, asleep, afraid, insane, cursed) on it. Dropping it (B, D)
   loses that; a large one at the bottom (C) costs the most screen where a first-person fighter needs it, between the
   weapon, the shield and the enemies' feet. A WoW-like frame top-left (A, R) keeps it for 110 px of the corner.
2. **HP and mana:** horizontal bars with numbers in the unit frame, plus a slim echo on the action bar so "low" is
   visible without looking away from the fight. Not orbs: they read fastest but are foreign to MM, need new art and
   their red liquid contradicts the approved green/amber/red HP bands. The split arcs (C) stay the party HUD's language.
3. **Action bar:** yes, it makes sense for a solo action character. Bottom-centre, ten slots on 1–0, optional second
   row on Shift. It replaces the party basebar in this mode and keeps the basebar's panel and sockets, so the mode still
   looks like OpenYAMM. Mouse buttons, Q, E, R and F stay free for attack, block, kick, the signature skill and interact.
4. **Special skills:** actives go on the bar and show cooldowns; passives need no button and show only when they fire
   (a gold glow on the button they feed and a gold-rimmed buff). Always-on passives live in the Special Skills screen
   and the character sheet's numbers.

## The variants

All five HUD views use the same scene, values and common parts: the installed top bar and minimap (cut from a native
capture), the crosshair, the targeted Goblin Lord's world-space bar as it is drawn today (frame, value, damage trail,
effect icons with the clockwise sweep), floating damage numbers and the status plate.

| | Variant | Preview |
|---|---|---|
| A | **Unit frame top-left, bar bottom-centre.** WoW-style round portrait with level badge, name, HP/SP bars with numbers; buffs and debuffs under it; the hero/skull panels go (with one character, party and personal buffs are one list). | [a.png](previews/a.png) |
| B | **Minimal (Skyrim / Avowed).** No portrait or name. Slim HP and SP bars at the action bar's height, level and weapon at the start of the HP bar, debuffs over HP, buffs over SP. Floating slots, no panel. | [b.png](previews/b.png) |
| C | **The approved split-arc portrait, enlarged, with the bar as wings.** About 1.3× the party portrait; HP arc left, SP right, aggro gem and personal-buff medallion kept; the selection diamond becomes the level badge; slots 1–5 left, 6–0 right; hero/skull panels as today. | [c.png](previews/c.png) |
| D | **Diablo-like orbs.** HP and SP orbs in brass rings flank the bar; the level sits on the HP orb; potions and scrolls move onto the bar. | [d.png](previews/d.png) |
| R | **Recommended:** A with the approved oval rim and level diamond, the HP/SP echo on the bar and a passive proc shown. | [r.png](previews/r.png) |
| | Today: the installed HUD with a one-member party at the same place. | [today.png](previews/today.png) |

The comparison sheet ([portrait.png](previews/portrait.png)) scores the four on identity, conditions, HP near the
crosshair, exact numbers, buffs, screen kept free at the bottom and fit with the approved kit.

![Comparison](previews/portrait.png)

## Action bar

![Action bar](previews/bar.png)

- **Slot:** 52 px at 1600 × 900. Key top right (SMALLNUM), SP cost top left on a small blue tab, charges or stack
  bottom right, cooldown seconds in the centre (Alegreya, as the combat numbers).
- **States:** ready; cooldown (a dark wedge that clears clockwise, seconds only above 1.5 s); recovering (the shared MM
  recovery after any action, a lighter wedge without a number); not enough SP (blue veil, cost in red); out of range
  (red veil, key in red); active toggle or aura (gold rim and underline); proc (a passive fired: gold glow and spark);
  charges (count and pips); item stack; empty (engraved socket that keeps its key); drag target (dashed gold);
  unusable (greyed: Shield Bash with no shield).
- **Rows:** 1–0, and optionally a second row on Shift (shown) or Ctrl in the same panel; the bar grows one row upward.
- **Tooltip:** name, school and rank, cost and range, recovery and cooldown, effect, key. Talents say "Special skill"
  in gold.
- **Crosshair recovery brackets:** two short arcs either side of the installed ivory cross fill after each swing or
  cast and stay faint when ready, so the mash rhythm can be read without looking down.
- **Optional signature skill:** one Grandmaster talent on R with a recharge bar that fills from hits and kills, like a
  Vermintide career skill.

## Special skills (talents)

![Special skills](previews/talents.png)

A layer on top of MM's skills, in the Carved Obsidian 4:3 overlay beside the Skills and Spells pages.

- **MM skills are unchanged.** Skill points raise the skill; trainers sell Expert, Master and Grandmaster.
- **Each school has three tiers** of special skills, one per mastery rank above Normal. Schools are the weapon skills
  (Sword, Axe, Mace, Dagger, Spear, Staff, Bow, Unarmed), the armour and defence skills (Shield, Leather, Chain, Plate,
  Dodging, Armsmaster) and the magic schools (Fire, Air, Water, Earth, Spirit, Mind, Body, Light, Dark).
- **Mastery opens a tier; points choose within it.** The trainers stay the gate, as in MM.
- **Free with mastery:** each school's first Expert active is learned free on reaching Expert, so a new character has
  buttons before its first point.
- **Active** special skills are round in the tree, go on the action bar and have cooldowns. **Passive** ones are
  square and need no button.

### Point gain

A solo character gets the whole party's experience. MM's experience for a level grows with the square of the level
(level *L* needs about 1000 · *L*(*L*−1)/2), so four times the experience is about twice the level: a party member
who finishes MM6 near 50 is a solo character near 100, and a long MMerge run ends well past 150.

| Final level | every 5 levels | every 10 levels | every 10 + 2 promotions |
|---|---|---|---|
| 50 | 10 | 5 | 7 |
| 100 | 20 | 10 | 12 |
| 150 | 30 | 15 | 17 |
| 200 | 40 | 20 | 22 |

With two or three active tiers in each of the six to eight schools a character trains, there are 40–60 special skills
within reach. **Recommended: one point every 10 levels plus one at each promotion, and the free Expert active per
school.** One per 5 levels fills every tree by the end of a long run and the choice stops mattering.

### Example tree

Proposed content, for discussion. A = active (cooldown), P = passive.

| School | Expert | Master | Grandmaster |
|---|---|---|---|
| Sword | Riposte (P: after a block, the next swing +50 %) | Whirlwind (A, 12 s: hit everything in reach) | Blade Frenzy (P: kills cut cooldowns by 2 s; lights Whirlwind) |
| Axe | Cleave (P: swings also hit a second foe for half) | Sunder (A, 15 s: armour halved for 10 s) | Executioner (P: double damage below 20 % HP) |
| Mace | Concussion (P: 10 % stun chance) | Skull Crack (A, 20 s: stun 3 s) | Earthshaker (A, 40 s: knock down everything within 4 m) |
| Dagger | Backstab (P: triple damage from behind) | Flurry (A, 10 s: three quick stabs) | Venom (P: hits poison) |
| Bow | Quick Shot (A, 6 s) | Volley (A, 20 s: five arrows in a cone) | Deadeye (P: crits pierce) |
| Shield | Shield Bash (A, 8 s, free), Brace (P) | Shield Wall (A, 45 s: −60 % from the front for 8 s), Spell Ward (P), Shield Charge (A) | Bulwark (P: blocked missiles reflect), Rally (A, 90 s), Aegis (A) |
| Armsmaster | Kick (A, 4 s: push back, as in Dark Messiah) | Charge (A, 15 s: rush to the target, knock down) | Battle Trance (A, 90 s: recovery halved for 10 s) |
| Dodging | Sidestep (A, 6 s: dash) | Evasion (P) | Untouchable (A, 60 s: 3 s of dodging everything) |
| Fire | Kindling (P: a Fire Bolt hit makes the next Fireball free) | Flame Ward (A) | Inferno (signature) |
| Air | Blink (A, 10 s: 10 m forward, free) | Static Charge (P: melee hits chain sparks) | Storm Call (A) |
| Water | Frost Nova (A, 20 s: freeze everything near for 2 s) | Ice Barrier (A) | Shatter (P: frozen foes take double) |
| Earth | Stone Hide (A, 30 s: −30 % damage for 12 s, a Barkskin) | Tremor (A) | Stone Form (A) |
| Spirit | Spirit Tide (A, 120 s: 30 % SP over 8 s, an Innervate) | Guardian Spirit (P) | Resurgence (P) |
| Mind | Clarity (P: spells cost 10 % less) | Terrify (A) | Iron Will (P: immune to fear and insanity) |
| Body | Second Wind (P: regenerate below 30 % HP) | Lay on Hands (A, 60 s) | Undying (P: once in 5 min, survive a killing blow) |
| Light, Dark | Radiance (P), Drain (P: weapon hits leech) | Smite (A), Shadow Step (A) | Sun's Wrath (signature), Soul Harvest (P) |

### How active and passive special skills show on the HUD

- **Active:** an action bar slot with the cooldown sweep and seconds; the tooltip says "Special skill" in gold.
- **Toggle or aura:** gold rim and underline on the slot while on, and a buff tile without a timer.
- **Passive with a trigger (proc):** nothing until it fires; then the button it feeds glows and a gold-rimmed buff
  with its timer joins the buff list (R shows Blade Frenzy lighting Whirlwind).
- **Always-on passive:** no HUD at all; it is in the Special Skills screen and in the character sheet's numbers.
- Colours: gold = special skills, the usual brass = spell buffs, red rim = debuffs and crowd control, blue = SP.

## Open decisions for the user

1. Portrait: R (small, top-left) as recommended, or C (the approved arcs, enlarged, bottom-centre)?
2. HP/SP echo on the action bar: always, or only below 50 % HP? And a red screen-edge vignette at low HP?
3. Second bar row on Shift or Ctrl, or none (ten slots plus R)?
4. Hero/skull panels in solo mode: gone (one buff list under the frame) or kept for long party buffs?
5. Talent points: every 10 levels plus promotions (recommended) or every 5? Solo experience: the whole party's
   (levels about twice as high) or a solo curve?
6. Do magic schools get special skills too, or only weapons and armour? Respec at trainers, free or for gold?
7. Signature skill on R with a Vermintide-style recharge: yes or no?
8. Should special skills exist in party mode as well (one tree per member)? The screen works for both.

## Sources

- **Scene:** `art/bg_goblins.jpg` is a native OpenYAMM capture (MM6 New Sorpigal, start pose, HUD switched off with
  `render hud off`, three goblins and a Goblin Lord spawned and held with `actor spawn` / `actor immobile`), made by
  [tours/background.yml](tours/background.yml). `art/native_today.jpg` is the same with the HUD on; the top bar,
  minimap and hero/skull panels are cut from it by [prepare_art.py](prepare_art.py) `--captures`.
- **Sword and shield:** a neutral placeholder drawn as SVG by `app.js`. No Oblivion (Bethesda) art is used anywhere in
  this folder; the prototype's `reference/oblivion_poc/preview/` captures were looked at only.
- **Interface art:** copied unchanged or downscaled by `prepare_art.py` from `assets_source/engine/icons_x2`
  (`obsidian_party_endcap_socket`, `obsidian_hud_portrait_rim_*`, `obsidian_hud_status_plate`,
  `obsidian_enemy_health_frame`, `obsidian_skills_surface`, `obsidian_personal_buffs`, the glyph-free
  `obsidian_buff_*` and `obsidian_debuff_*` icons) and `assets_dev/engine/hud_x2/menus` (`omenu_frame`,
  `omenu_button_small_*`, `omenu_keycap`).
- **Slot art:** the glyph-free spell crops of the [Battle Orders study](../combat_orders_20261108/README.md)
  (`art/spells/`), item icons from `assets_dev/engine/icons_x2` (`item178`, `item177`, `item199`, `lshield1`,
  `lshield2`, `7item115`, `item004`, `7item024`) and the face `pc03-01`. Special skills reuse these as stand-ins; real
  talent icons would be new art.
- **Fonts:** `assets_dev/engine/fonts/truetype` (Fondamento, the faithful Arrus, Lucida and SMALLNUM, and Alegreya
  for combat numbers), copied to `fonts/`.
- Images, fonts and captures stay local (level_generation tracks only the page, the scripts and this README).
