# MAW developers in #balance-discussion before 5.0 (2023-08 to 2026-07): design notes for a solo power path on Beyond Madness

Source: `out/chunk_old_dev.txt` (all 1551 lines read), with spot checks in `out/flat.txt`. Malekith is the main developer and Rawsugar is the second (spells, classes, Austerity). Quotes are exact but shortened. Each "→" line is my reading.

## 0. Difficulty and mode timeline (as the chat shows it)

- 2023-08 to 2024-03: Normal, Hard, Hell, Nightmare (NM). 2023-08-09 Hell design: "monsters will do 2x damage, players will do -45% damage, -45% healing", with stat effects halved and enchants +50%.
- 2024-mid: Doom is the top difficulty ("Doom isn't the only relevant game mode, but the most important to balance", 2024-07-05).
- 2024-10-21: **Road to Insanity (RTI / Insanity)** is announced as the new top difficulty.
- 2025-01-05: **Austerity** (Rawsugar): "weaker items, far less crafting materials, stronger monsters", "a minimalist experience rather than massive numbers and combining gear".
- By 2025-08-30: **Madness / Beyond Madness (BM)** exists ("cow run on BM", flat.txt). By 2025-09-08: "intended content now is lvl 1000".
- 2025-10-16: "once I feel like we have a completely stable madness I'll release 4.0". On 2025-11-07: "if you can get kinda precisely to level 1000 I'd say madness is ready for official release".
- 2025-12-02: a "limited resources" game mode is proposed (no passive regeneration, closer to MM6). "there is no point in increasing numbers further when you have madness".

## 1. Intent for each difficulty and for the top difficulty

- 2024-02-01 M: "current scaling makes so that players grow stronger than monsters on the long run, allowing eventually to increase the difficulty further". → Early design expected players to outgrow monsters and then step up a difficulty.
- 2024-02-01 M: "I'll make nightmare 2 very hard, expecting players to use crafting system and having a meta party. Nightmare 3 might not be needed, as by that point players should have already completed the game and went into end game system." → He planned an endgame system after the top difficulty instead of more difficulties.
- 2024-03-11 M: NM's problem is that it is "too hard early and too easy as you go on". R: "if it should be frustrating id want it at endgame rather than early".
- 2024-08-06 (Doom): a player said it "feels about as close to impossible". M: "which is kinda close to the goal". M: "you are supposed to be able to proceed even without farming, given a good party".
- 2024-08-07 R: "im also of the school that highest difficulty shouldnt be playable by sane people".
- 2024-10-04 R: "doom should be a struggle to play even minmaxed and powerful ... at no point should doom be an easy laidback experience".
- 2024-10-21 M (Insanity): "not supposed to be relaxing, but only pushes the game to the extremes, so it is NOT for everyone. Nerfs are very likely NOT to happen." It removes dungeon resets, gives more items (+30 %), +50 % legendaries and twice the crafting drops. On getting "stuck exp wise", M says "that's the whole point".
- 2024-11-14 M: "insanity is indeed accounting for people clearing all of them" (all three continents in order). 2024-10-26: maps locked to level 300 "because otherwise free farming ... intended for you to clear all the games before".
- 2024-11-27 R: "the final difficulty should be one where the monsters get a sizable buff but the player gets nothing or very little", and he complains that drops let players "almost keep up".
- 2024-12-15 M: "insanity is designed so that you might not be able to Clear it if too unoptimal".
- 2025-02-23 R: "insanity should be nigh impossible, there's no point in having a highest difficulty that can be conquered w a bit of tenacity".
- 2025-02-24 M: "Insanity is indeed the ultimate difficulty, where min-maxing is needed to clear the game. I'm not surprised you can barely keep up with monster level pacing, and that's intended by design." Also: "in insanity, not all party are viable."
- 2025-08-30 M: "Even road to insanity was meant to be uncompleteable with some chara[cters]" (reply on Madness gating: "from lvl 100+ sounds good").
- 2025-11-17 M (Madness): "it's supposed to be an unforgiving challenge, not a tasklist of cheese to skip the first 50 levels."
- 2025-11-18 M: asked whether Madness is beatable with any party, he answered "never said such thing". He also said that some legendaries being needed is "maybe a bit too much on the heavy side, but I think it's ok".
- 2026-01-20 M: "solo madness is very hard on an absolute scale".
- → Summary: the top difficulty is meant to be clearable by a min-maxed build of the right kind, not by every build. It should be at most just clearable, never comfortable. No developer says a maxed character should roll over the top difficulty. "Too easy late" is treated as a bug (NM 2024-03, Insanity 2024-12).

## 2. Systems that gave power past the curve: history and reasons

### Artifacts and relics
- 2023-09-06: artifacts start scaling with player level: "at Level 80 they have the vanilla stats ... at level 160 and 240 ... up to triple". Magic-boosting items stop stacking. Collecting every artifact raises the chance of ancient and primordial items.
- 2024-03-05 to 03-06: the plan becomes "fixed level but much stronger / droppable multiple times / unique effects (later)". Reason given: "The 1 time only not scaling artifact create an unpleasant fomo effect".
- 2024-10-12: artifacts get rarities from rare to legendary: "super rare, being very very strong, but not changeable with crafts", with artifact powers added on top of the enchants.
- 2025-12-02 and 2025-12-07 M: "solo artifacts are broken, as you get around 2.2x levels, so they have around double the power". He says this "needs nerf (aka artifacts/celestials fully scaling with level)". 2026-02-02: celestials "scale with level ... not intended to". He considers a solo nerf for celestials.
- → Items that scale with level are already too strong for solo, because a solo character reaches about twice the level. Any new solo power should not grow with raw character level.

### Legendaries
- 2024-07-14: legendaries drop more often but have to "absorb" a legendary power first, "this way you can craft items more reliably".
- 2024-07-22 M: "legendaries are supposed to be very rare", "starting a new game and BOOM random legendary is not my vision", "I have plan with the extra content to add some more reliable form of legendary farming".
- 2024-09-19: higher difficulty makes legendaries more common. Insanity gave +50 %. Bosses give a guaranteed legendary (2025-03-18).
- 2024-10-12: legendary effects do not stack. "the goal is to not make feel the +50% enchant power mandatory".
- 2024-12-20 M: "having to choose between which legendary to use is good". The list includes 2 % of current monster HP per hit, -10 % damage taken, divine protection, +1 ascension, doubled armour AC, crit chance over 100 % adding damage, and resistance shred.
- 2025-04-09 M: "once you have a legendary, now you are basically guaranteed to not be able to find any upgrade". Rolls range from 50 to 166 %, and gems can still be applied.
- 2025-06-16 M (idea): "for each time you complete the game, you can get an unenchanted ring with a legendary effect of choice when doing a new game" (Insanity only: 2 legendaries for Insanity, 1 for Doom, 0.5 for anything else).
- 2025-09-08 M: "30% is probably the highest between legendaries". R (2024-11-01): "there should be no legendary combo that quadruples damage".
- → A legendary is a capped sidegrade that forces a choice. It is not meant to stack without limit.

### Crafting (gems, cubes, hourglass, eye, emeralds, scouring, bomb, mirror)
- 2024-04-10 M: "the idea is to mitigate luck and having an extra game system to play with."
- 2024-06-25 M: "You don't need set legendaries to fully clear the game / Crafting is already there to help". Solo gets "a power spike mid, where you can upgrade weapons and armors with cubes and get full legendary".
- 2024-07-25: gems reroll enchants. Cubes upgrade item base power. 2024-11-08: the hourglass removes the second base enchant and the eye removes the special enchant.
- 2024-11-29 M: "The reason solo it's easy I bet it's because you can abuse crafting cubes."
- 2025-04-09 M: "in PoE/le crafting is super random, here you can easily get what you want". "gems upgrading enchant isn't something we have in PoE/last epoch, and it's super strong".
- 2025-04-11: enchant power rolls widened from 67–100 % to 1–167 %.
- 2025-05-03 M: "I could probably also make all the loot 100% deterministic, but that's not the goal".
- 2025-10-16 M: ultra-late crafting materials: "I think they are too much". He likes the idea of showing "the max amount possible of each stat via crafting".
- → Crafting is close to deterministic and is the main way to make power predictable. It is capped by the item-level ceiling, not by randomness.

### Maps and dimension maps
- 2024-07-15 M: three options to stop players farming the same dungeon: "resets to increase monster level each time", bounty quests, and droppable "maps" that teleport into a dungeon with a name, level and modifiers.
- 2024-10-26: maps are locked behind level 300 in Insanity ("otherwise free farming").
- 2025-08-31: "you can also find a dimension map that takes you there".
- 2025-10-02 M: "I could remove map rewarding with other maps and give exp+crafting instead".
- 2025-10-09 M: "I don't want to have you being able to farm maps endlessly without ever needing to clear content".
- 2025-10-21: map crafting. "cubes increasing map level / eye/hourglass give 1 affix / ascension emerald changes maps".
- 2025-10-24: inside a map, map drops are cut to about zero. Rewards depend on affixes: 4 affixes give an ascension emerald, 3 an hourglass, 2 an eye, 1 a cube. "maps run on ascension to increase level". He worries about "the exploitability of overworld maps".
- 2025-10-25: XP for completing a map is a quarter of the first completion. 2025-10-28: 15 maps is "a shittons of farming", so map XP is cut by 10–15 %.
- → Maps are a PoE-style atlas that pays out crafting materials. They are deliberately not self-sustaining, and they come after the campaign.

### Arena, bounties and resets
- 2024-07-25 R: "Intended is no reset. Reset is a panic button if youre stuck". M: chest dungeons farmed forever are "the fastest way to farm for legendaries, which isn't intended, as it's boring/repetitive gameplay". "I'm coding arena, which will give unlimited content to farm."
- 2025-05-15 M: Insanity bounties are limited to one a month. "insanity isn't supposed to give an easy way of farming", yet "as there are other form to farm experience (such a arena), I think theoretically infinite farming is an ok thing to have."
- 2025-08-30 M (Madness): "you farm endless for the gold, bounty for gold and exp from quest". Endless arena is the fix for solo gold shortages (2025-10-04, 2025-10-11).
- 2024-07-15 M: "latest oracle orb change made the game breakable, given enough farm"; "with the Oracle orb changes I'm pretty sure that solo players can easily break the game."

### Talents
- No talent tree appears in the dev lines before 5.0, apart from 2026-02-17 M: "I was thinking to make GM talent to make 10% of party damage from allies to the paladin". Malekith's own roguelike plan (2025-03-06) has "a talent tree" and "maw like itemization (a bit more deep and less power creeping, similiar to POE but up to 4 enchants, not 6)".
- → Talent trees are new territory, but he likes PoE-style depth with less power creep.

### Other levers
- 2024-05-30 and 2024-07-11: PoE-style buffs that reserve mana. Each buff is about 15 % base plus 0.3 % per skill point, permanent while it stays reserved. R and M (2025-02-23): solo players should turn the buff rework off.
- 2024-03-03: in solo, all misc skills can be learned up to GM. 2025-03-16: an effect stays at 100 % but is "halved for solo". 2025-10-09: guaranteed-hit CC gets "high cost, high recovery (halved in solo)".
- 2024-12-15 M: "alchemy is op in solo". 2025-12-02: solo characters without healing should use alchemy ("get to 7 and craft a lot of white potions").

## 3. Monster scaling, mitigation, HP, Bodybuilding (BB) and XP

- **Design horizon:** 2024-08-02 ascension was "balanced for monsters up to Level 300". 2024-10-04 "formula was balanced around level 300 items. Now items go up to level 600". 2024-10-19 "natural progression when going from 300 as intended max level, to 600". 2025-09-08 "intended content now is lvl 1000". 2025-10-28 "Items scale up to Level 1000". 2025-08-28 "After level 700 things kinda get messy as items don't get better anymore and there are some 'winner', but I don't expect people to grind that much."
- **Monster HP formula (2025-09-30):** it "extimates player damage at x level and y difficulty / adds a multiplier depending on intended seconds necessary to kill a monster depending on difficulty / ... monster tier (green, blue, red) / ... bosses". → Monster HP is computed from the expected damage of a player at that level. A player whose power grows faster than this estimate is the only way to "roll" through.
- **Hits to kill (2025-09-07):** "a blue goblin of the same player level, die in 6 hits early on ... stable until around level 400, then it gradually explode into 17 hits at level 1000 ... a boss would require around 300 hits. This because of resistances." → Late-game durability of monsters was a known problem he wanted "more stable".
- **Exponential vs linear:** 2024-08-02 spells moved from `damage*a^x` to `damage*x^a`. "making weapon skill doing damage x 1.05^weaponSkill ... it's an huge powercreep". Spear (2024-10-04) was "designed for level 300, not 700", so it became non-exponential. 2024-12-05: "with scaling so fast ... it becomes either too easy or too hard to quickly by changing just a couple of Levels. Also older equipment gets invalidated too fast." 2024-12-01: enchant power -37 %, Insanity item power 66 % → 40 %, packs 5–7 → 4–5. 2024-12-07: "everything was nerfed, even monsters". 2025-01-02 R: the latest changes "finally reduced powercreep which has tamed the difference in power between slightly lower and higher level monsters".
- **Damage reduction:** 2024-09-03 resistances got diminishing returns "with breakpoints every 50% reduction ... increasingly reduced up to 87.5%, after that it's flat". 2024-09-03 M: "balance difficulty around 99.6% damage reduction? ahahah". 2024-10-04: "having above 99% reduction is not intended". 2025-05-05: "995 resistances (which is the cap), reduce damage by 99.9%". 2025-07-07: "Each 100 resistance is half damage". 2025-10-07: "150 AC reduce the same amount of 100 resistance", and "AC is divided by bolster amount, which is 1 baseline, 6 for madness". 2025-02-24: the stat-screen mitigation "accounts for monsters being the same level as you ... specially in solo, the actual damage reduction is much more". → Reduction depends on the monster's level relative to yours. No explicit "10 % floor" appears in these lines (the floor in our simulation is a 5.0 rule), but the trend toward a hard ceiling is clear.
- **Immunities:** 2025-02-23 R: "taking no damage would be a prime example of bad gameplay". 2025-02-24 M: "mistform immunity needs to be removed". 2025-10-05 M: "reduce that to -75% damage taken, preventing some cheesing". 2025-10-07 M lists his dislikes: "immunities", and "physical damage being increasingly spiky".
- **HP and BB:** 2024-09-03 "BB now increases 2% per skill point". The goal is "to move some value from resistances to HP", "possible to have a shittons of HP to tank a lot of damage, but make it harder to heal"; "goal 1: make BB good / goal 2: lessen the difference between tank and non tank". 2025-08-28: "+hit points items are a bit too good and body building scaling exponentially makes numbers bigger than I'd wish ... nerfing both of them and reduce monsters exponential damage might be an idea". 2025-09-08: "damage scales exponentially faster compared to player health"; endgame mino 1000k HP, a full tank about 5000k; "I need to account also HP scaling at different rates depending on difficulty". 2025-10-20: thief has "-37.5% HP BASELINE / BB expert ... +3% per skill instead of +5% flat amount x 2 instead of x 5". 2025-11-18 R: "current balance favors BB users (mastery) a bit too much"; "a slight nerf to AOE, big nerf to BB". M: "Current numbers are a nerf compare to before, as it used to be 2% exponential". 2025-11-18 M: eradication's purpose is "to prevent 100% glass cannon without any drawbacks".
- **Cover cap (2024-08-05):** cover capped at 40 % so monster damage does not have to kill a tank with "milions of vitality".
- **XP:** 2024-06-03 new XP system ("Level taken in account isn't character level, but level gained"). R: "Previously grinding allowed player to basically bypass difficulty setting, the new xp system makes this much harder". 2024-07-07: "exp formula is going to limit the benefit you get from farming anyway". 2025-07-30: "doom/insanity make monsters give you less exp, as there are more of them"; "solo basically uses bolster level as a reference level". 2025-09-30: XP is "exp*monsterHP/averageMonsterHP of your level", and experience overflows 2^32 at about level 2700. 2025-09-12: in Madness, quests scale with map level, not bolster, and do not count toward bolster. 2025-09-14: idea to "remove cap of experience gained from higher level monsters". 2025-10-30: "lower level monsters giving high exp is totally fine, considering you can't farm them". 2025-09-12 M on XP potions: "It's grindy enough I can balance ignoring it". 2025-10-04 M: "I'm happy with people having a goal even after getting all the skills to the required amount."

## 4. Solo mechanics and the developers' stance

- 2024-01-12 M: "difficulty is the same, but you get 5x experience and you can focus all the good loot and barrels on 1 character".
- 2024-03-01 M: MAW custom classes are "best for solo, balanced at most for 5 man"; "any Class with healing spell/regeneration can solo".
- 2024-03-11 M (NM): "Solo it's even harder early, but eventually you get so much good gear and experience it becomes around the same difficulty."
- 2024-06-25 M: "A well build party will always outperform a solo player, but will require much more micromanagement". "Solo has a power spike mid ... After that solo falls off."
- 2024-07-15 M: "we can also separate solo with full party category" (leaderboards and completion records).
- 2024-10-19 M: "Solo basically gets 2.2 times levels". R: "solo is too easy vs party lategame ... could maybe add a solo modifier".
- 2024-11-29 R: "Its hard to gauge solo ... what party level does solo correspond to".
- 2024-12-14 R: "starting out you are super super weak ... in a game that is balanced to already be harder at level 1 than level 500, after 15 levels you triple the power ... after 50 you about double that."
- 2025-02-23 R: "solo is only mostly balanced ... we havent made any changes or only very few in order to balance solo"; "my experience is solo is stronger than party"; "solo you are roughly double level vs party".
- 2025-08-30 M (after the late-2025 HP and mitigation changes): "solo it's something unfeasable now probably" (in context, of a troll on Madness). 2025-09-07: fixed-location Madness bosses "wouldn't work for solo tho".
- 2025-12-02 M: "Regeneration is the way to go for solo"; "the tools are there, they require extra steps". 2025-12-19: "for solo regeneration is the only way to go". 2026-06-23: "no leech is very limiting in solo".
- 2026-01-20 M: "solo is indeed a bit easier, there is much less decision making, micromanaging and less bad luck"; "in solo you are much tougher, but you can't escape oneshots"; "solo: easier execution, easier building, more planning required / party: hard execution, harder building". He also says "solo madness is very hard on an absolute scale".
- → The developers treat solo as an accepted challenge mode. It is never tuned specifically: it is balanced through a reference level (bolster) and gets a few halved or doubled effects. They saw the solo curve as weak early, strong in the middle, and falling off late. By 2026 the one-shot problem (not attrition) is what kills solo.

## 5. Constraints to respect, and wishes he never implemented

**Avoid:**
- Power creep that makes items outshine skills. 2024-05-01: "useless powercreep that made items heavily outshine skills". 2025-10-21: "you risk powercreeping".
- Exponential scaling. Every `a^x` term was replaced with a polynomial one (spells, spear, healing crit kept off because crit "means multiplying that amount by 5", 2025-09-08).
- Immunity or near-100 % reduction. Facetanking: "melees are supposed to tank a couple of hits, but not facetanking" (2025-08-30).
- Endless farming of one source: "boring/repetitive gameplay" (2024-07-25), maps that feed themselves (2025-10-09), cheese that skips content (2025-11-17).
- Reliance on luck: crafting exists to mitigate it, but fully deterministic loot is "not the goal".
- A legendary at the start of a game, or legendaries that stack.
- Items that scale with character level being doubled by solo's 2.2x levels.

**Accepted:**
- Optional farming that makes things "a bit easier" (R, 2025-02-05).
- Arena and theoretically infinite XP farming.
- A goal after all skills are maxed.
- Separate solo records.
- Solo-specific halving or doubling of single effects.

**Wanted but not done (in these lines):**
- "plan with the extra content to add some more reliable form of legendary farming" (2024-07-22).
- Legendary ring of choice per game completion (2025-06-16).
- Legendaries you have never found becoming more likely (2024-10-19).
- Unique-effect artifact redesign "with some design idea behind" (2024-03).
- A solo modifier for damage reduction (R, 2024-10-19).
- A solo archer "disengage" skill (2025-10-23).
- Crit damage scaling with level (2025-09-09).
- Making fights against higher-level monsters "less punishing" (2025-09-03).
- Stable hits-to-kill late (2025-09-07).
- A PoE-like endgame: "Poe has nailed endgame ... not sure what we will end up having" (2024-02-02).

## Most relevant for the solo-BM goal (top 10)

1. **The top difficulty is meant to be barely clearable, never rolled.** Insanity is "the ultimate difficulty, where min-maxing is needed ... barely keep up with monster level pacing, and that's intended by design" (2025-02-24). Madness is "an unforgiving challenge" (2025-11-17), and "solo madness is very hard on an absolute scale" (2026-01-20). A path that lets a maxed solo character roll through BM goes against stated intent, so make it an explicit opt-in or post-campaign layer.
2. **He did plan an endgame beyond the top difficulty.** "Nightmare 3 might not be needed, as by that point players should have ... went into end game system" (2024-02-01), plus the PoE endgame remark (2024-02-02). Maps and an atlas with crafting rewards were that start. A solo power path that lives in post-campaign dimension maps fits his vision best.
3. **Monster HP is computed from the expected player damage at that level and difficulty** (2025-09-30), and XP is scaled by monster HP relative to monsters of your level. Outscaling therefore needs power that grows faster than the formula's player model: for example solo-only multipliers outside the "expected damage" estimate, not more levels.
4. **Solo already gets about 2.2 times the levels** (2024-10-19, 2025-12-07), and level-scaling artifacts and celestials were judged "broken" in solo. Give solo power from sources that do not grow with character level: talents bought with tokens from map or boss clears, crafted affixes, capped sidegrades.
5. **Hits to kill grow from 6 to 17 for a same-level blue monster at level 1000 (about 300 for a boss) because of resistances** (2025-09-07), and he wanted this stable. Solo resistance shred or penetration is a fix he would agree with in principle (spear, the shred legendary and "each attack reduces resistances" were all his ideas).
6. **Mitigation is capped on purpose.** Immunities are cut to -75 % (2025-10-05), above 99 % is "not intended", the diminishing curve flattens at 87.5 %, and "melees ... not facetanking". Since solo deaths come from "you can't escape oneshots" (2026-01-20), solo power should come from HP and recovery (BB, regeneration, leech, divine-protection effects) and from killing faster, not from removing the damage floor.
7. **No exponential terms.** Every `a^x` was replaced with a polynomial and every combined multiplier was nerfed ("no legendary combo that quadruples damage", R). A PoE-like curve should come from many additive or polynomial nodes with visible caps (he likes "the max amount possible of each stat via crafting", 2025-10-16), not from compounding multipliers.
8. **Farming is fine when it is optional, varied and not self-feeding.** Arena and "theoretically infinite farming is an ok thing to have" (2025-05-15). Maps must not drop maps, and map XP is a quarter of the first clear. He rejected repetitive chest dungeons. Optional BM dimension farming should pay crafting materials and solo talent currency, with diminishing XP.
9. **Crafting is the intended way to beat luck and is close to deterministic.** "in PoE/le crafting is super random, here you can easily get what you want" (2025-04-09). Rolls run 1–167 %, and solo already gets "a power spike mid ... with cubes". A solo crafting tier above the item-level cap (for example extra affix slots, or cube levels past 640 that only maps give) extends a system he already uses for power.
10. **Precedent for solo-only rules exists, but they are minimal and targeted:** misc skills to GM in solo (2024-03-03), effects "halved for solo" (2025-03-16, 2025-10-09), separate solo records (2024-07-15), solo XP from bolster level (2025-07-30), and R's suggested "solo modifier" (2024-10-19). He also floated a reward that carries over between games: a legendary ring of choice per completion, scaled by difficulty (2025-06-16). That gives a design anchor for solo talent points earned on BM.
