# What the MAW Discord says about solo and Beyond Madness (2026-11-14)

Source: the MAW Community #balance-discussion export (52,539 messages, 2023-08-02 to 2026-11-14, kept outside the
repository). Six readers went through it:
- three of the 5.0 era (2026-08 to 2026-11, every message);
- two of older threads on solo, Madness and Insanity (with context);
- one of the developers' own design statements before 5.0.

Their notes, with dates and quotes, are in [discord_notes/](discord_notes/). The slices came from
[scripts/discord_flatten.py](../scripts/discord_flatten.py) and [scripts/discord_context.py](../scripts/discord_context.py).

"Madness" in the chat is the top difficulty, our Beyond Madness (BM). Malekith is the MAW developer; Rawsugar is the
second developer.

## The short version

- **The simulation's wall is real and known.** It is the same one solo players describe:
  - In 5.0, only a Dragon has soloed BM (2026-11-14).
  - A solo Knight was given up.
  - Everything else gets "randomly one shotted", even with over 70 points in Bodybuilding.
  - Before 5.0, solo melee had the same complaint at Insanity (2024-12, 2025-02) and in old Madness (2025-10).
- **The 10 % floor is deliberate.** On 2026-08-08 Malekith set damage reduction to "hard cap to 90% now", after a
  Death Knight's damage taken spread from 1 % to 8.3 %. Earlier he had cut immunities to −75 % and called reduction
  above 99 % "not intended".
- **The top difficulty is meant to be barely clearable.** Malekith (2025-02-24, on Insanity): "barely keep up with
  monster level pacing, and that's intended by design". Rawsugar wants the top mode "nigh impossible". In 5.0 terms
  (2026-11): "you can get overpowered as you want up to doom", while BM "requires absolute minmax". A solo who rolls
  through BM is therefore an OpenYAMM choice beyond MAW's intent. It should be named and opt-in as such, not
  presented as MAW balance.
- **The developer likes players getting strong and dislikes scaling monsters to them.** 2026-08-17: "I promised
  myself I will never ever ever do 'monsters scale with you' stuff" and "my goal in games is to minmax and become
  strong". In 2024-02 he wanted an endgame system after the campaign ("Poe has nailed endgame"), and his own next game
  has a talent tree and Path of Exile–like items. The user's goal matches his taste; it only disagrees about where
  BM sits.
- **Solo-only rules are normal in MAW.** Examples:
  - every misc skill to Grandmaster;
  - Alchemy that trains itself;
  - endless travel scrolls;
  - twice-as-long buffs;
  - a solo Cover stand-in ("40% chance… reduce damage by 40%", 2026-08-05);
  - faster Dragon recovery solo;
  - effects "halved for solo".

  Malekith (2026-08-27): "game is balanced around party play, not single player", and he "might … change monster
  stats to account for solo a bit more". The power gap is solo tuning he admits is missing.

## What changed in 5.0 that matters here

- **Experience.**
  - Before 5.0, a level cost level × 1000 XP and solo was a steady ~2.2× party levels; runs ended at levels
    1600–2025 in old Madness.
  - 5.0 added a penalty past level 100. BM ends around level 500, with main skills around 80 at level 500 and around
    50 at level 300.
  - Malekith said on 2026-08-15 he would "probably remove exp bonus from solo". Solo would get double skill points
    and "more stuff per level" instead.
  - A player (2026-11-14) says solo "is getting fucked twice as hard by the exp req penalty".
  - **Size (checked, SOLO_RULES.md §1):** 1 % per level past 100 until MAW `ba572ec2` (2026-11-10), 0.5 % since. The
    player's example (150→151 = 225K) is the old curve. Our port has the current 0.5 %.
- **Monsters come from a model of the expected player** (2025-09-30, 2026-08-27, 2026-11-04):
  - monster HP = expected player damage × a target time-to-kill × tier and boss multipliers;
  - monster damage uses an expected player HP (`getPlayerEstimatedHealth`, skill^1.4);
  - XP is scaled by monster HP over the average at your level.

  Mastery levels are inside that model, so unlocking masteries earlier makes monsters stronger earlier. On
  2026-11-03 he said a higher player resistance or armour class in the model raises monster damage of that type.
  On 2026-11-04 he fixed a model bug that assumed a +50 % weapon-skill enchant which does not exist. **Consequence:
  solo power must sit outside the model**, or the next rebalance scales it away. ENDGAME_LOOP already pins the model
  with a test; keep that.
- **Crafting.**
  - Item power now follows drop level.
  - Enchantments cap at 150 (120 base, ×1.25 primordial).
  - Legendaries lost their +50 % stats: "that alone is responsible for almost 10x damage".
  - Cubes raise a weapon's or armour's base by up to 20 %.
  - Gems are to become flat stats you can stack ("Still need to add the gem system", unfinished in 5.0).
  - Emeralds reroll at random; pearls of memory are scarce; items above tier-16 material cannot be rerolled.
  - Players ask for a pick-your-enchant NPC or orb-style transfer, and keep upgrading old low-level items because
    nothing else works late.
- **Farming.**
  - Dimension maps were removed on 2026-08-11 ("it becomes a grindfest"). On 2026-08-17 he said he would "probably
    add maps" back with a loot nerf, or one map every 50 levels.
  - In the release, maps are the only real farm. Players run them with four modifiers and raise their level with
    Emeralds of Power (26 emeralds took a Murmurwoods map to level 1700).
  - Arena gold is unlimited, so emeralds are too ("Limit are emeralds"). Even so the best BM party stopped near
    level 416.
- **Defence.**
  - Speed gives dodge again in 5.0 (casters stack 40–50 %).
  - Mana shield is capped at skill 50.
  - Monster bolster resistances are gone.
  - The density multiplier (about ×3 damage) was removed in the beta, and bosses were nerfed after a solo tester
    could not survive one devil-king hit.

## What carried solo runs, every version

Self-sustain decides solo, not damage. Malekith: "Knight can't because has no self sustain"; "Regeneration is the
way to go for solo"; "attacking fast in solo is very important indeed". A solo Vampire Knight at Insanity put it
like this (2025-02-23): with one action a turn instead of five, you die in a spiral as soon as damage taken
outpaces healing. "What is the point of level stacking then, if you never ever feel powerful?"

| Build | Why it worked |
| --- | --- |
| Dragon | About 7 %/s regeneration, ignores resistances, never misses, needs few crafting materials. The only 5.0 BM solo. Malekith (2026-11-06): "I need to go a bit harsher on dragons". |
| Troll | Grandmaster regeneration (about 1,100) and a 3 % max-HP heal on Cover. A Troll with the %-HP damage legendary as its only damage cleared old Madness. |
| Shaman | The most mitigation sources (Water reduction capped at 75 %, Air plus Water about 80 %). A Seraphim player had 0 deaths with a Shaman against 10 with his solo Seraphim. |
| Seraph / Knight | Cover and Retaliation solo (about 16–20 % less damage on average). The spear Knight is "the hidden op". |
| Vampire, Archer, Death Knight | Leech. |

This is the simulation's Dragon, Troll and Seraph ranking.

**Physical damage was the wall even at level 1079.** A solo Seraphim in old Madness (2025-10-06) had 378k HP and
95–96 % resistances. Magic was trivial for him, but physical hits from monsters 400 levels lower took 10–20 % of
his HP, and bosses killed him in two or three hits. **In 5.0 BM it is magic**: our run has 74 % of real damage as magic,
the Seraph's magic hit lands for 84 % of its HP, and a player (2026-11) says tanks reach the resistance cap only
around level 350.

## Ideas from the chat that fit the goal

Ones the developer himself proposed or accepted (the safest ground):

1. **A solo mode chosen at character creation**: party level, more skill points (a player proposed it; Malekith
   "will work on this", 2026-08-22/24). It isn't built.
2. **A leech floor**: leech always heals at least leech% ÷ 5 of max HP per 100 recovery (2025-09-03). It was his
   answer to "monsters are much higher level … I will think of something to make fighting higher level monsters less
   punishing". **It is in 5.0 and in our port** (SOLO_RULES.md §2 explains it): the proportional term, max HP ×
   (damage ÷ B-monster HP) × leech %, falls off against high-level monsters, and the floor catches it.
   - On the solo Dragon (2026-06-23): "no leech is very limiting in solo … leech would really make sense, I'm just
     not sure how to do it".
   - He said the 5.0 monster HP cut made leech "much stronger".
3. **Hit chance capped at 50 %, the rest as extra reduction** (2025-10-07, for physical hits; Madness divides AC by
   6). It is a mitigation shape of his own that keeps a floor.
4. **A legendary ring of your choice for each completed game**, scaled 3-2-1 by difficulty (2025-06-16). This is a
   new-game-plus anchor for Legend points.
5. **Flat-stat gems in sockets** (his unfinished 5.0 plan) and **cubes past +20 %** (cubes already do +20 %; our
   Ascension continues them).
6. **Resistance shred** (spear, the shred legendary, "each attack reduces resistances"), against the late climb in
   hits to kill (6 hits early, 17 at level 1000, about 300 for a boss, 2025-09-07).
7. **Cheaper Master/Grandmaster training costs for Madness** (a player proposed it; Malekith: "this could work").
   Gold and training cost were the solo late bottleneck in 4.x.

Player ideas without a developer answer:
- a higher resistance cap from armour mastery (Master leather +1 %, Grandmaster chain +2 %, Master plate +3 %,
  Master shield +1 %);
- a pick-your-enchant or reroll-the-seed NPC;
- more legendary transfer orbs;
- maps that start at level 50 and stay infinite.

What the developers rejected (constraints for our layer):
- monsters that scale with the player;
- buffs that stack ("madness becomes trivial");
- immunity of any kind (dodge has a multiplicative cap; the Vampire's mist-form physical immunity was removed);
- exponential formulas ("no legendary combo that quadruples damage"; every `a^x` became a polynomial);
- class artifact sets ("once you find them you never replace that item slot");
- generous crafting materials without level limits;
- loot that grows with character level for solo (solo artifacts and celestials would have "around double the
  power" at ~2.2× levels);
- maps that drop maps;
- full XP on repeat clears (repeat map clears give a quarter);
- repetitive chest farming ("boring").

He accepts "theoretically infinite farming", and calls himself "not particularly attached to anything" in 5.0.

## How this changes the recommendation

The direction in [README.md](README.md) holds. These points adjust it.

1. **Label the layer as OpenYAMM's own, opt-in, solo.** MAW intends BM to be barely clearable. Call it, for example,
   a "Solo Ascendant" option at character creation. With it off, a solo plays MAW's rules exactly. This also
   settles decision 2: everything in it is solo-only.
2. **Start with what Malekith proposed or accepted.** Build these before our own inventions:
   - the solo mode with more skill points;
   - a stronger solo leech (the floor already exists);
   - flat-stat gems;
   - cubes continuing past +20 % (our Ascension);
   - the ring-per-completion (our Legend points);
   - cheaper late training.
3. **Defence: prefer sustain to cuts after the floor.**
   - The 90 % cap is deliberate. So weigh first:
     - HP (Grandmaster Bodybuilding);
     - regeneration and leech (measured: a feel lever only, SOLO_RULES.md §2);
     - higher resistance caps against magic (74 % of BM damage);
     - his 50 %-hit-chance shape;
     - a once-per-fight cheat death.
   - Keep cuts after the floor (talents M1, the Ward) small and inside the ×0.25 clamp, or drop them if sustain
     measures enough. The simulation should compare both, since M1 was the largest single gain for the Death Knight.
4. **Rift Atlas without maps that drop maps.**
   - Build on MAW's own dimension maps and Emeralds of Power (`MawDimensionMaps.cpp`, `MawCraftingRules.cpp`).
   - Pay mainly in crafting currency, with repeat XP at a quarter.
   - Get the next map from currency or a fixed ladder (his "map every 50 levels"), not free from each clear.
   - Keep loot from scaling with character level.
5. **Many additive pieces with visible caps.** Show the reachable maximum of each stat, as he likes to. Avoid
   multiplicative stacks; the ×14/×120 has to come from several additive layers (HP × damage × sustain), each
   clamped.
6. **Port checks raised by the chat:** done in [SOLO_RULES.md](SOLO_RULES.md) §1. The port matches MAW `8967ae88` on the XP
   curve, solo XP, Speed dodge, the monster model and its 2026-11-04 fix, and leech with its floor. The only deviation
   is the known Seraph/Shaman flat-cut bug. The concrete solo rules, measured, are in SOLO_RULES.md §3–4.
