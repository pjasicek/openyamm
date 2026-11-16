# Concrete solo rules, port checks and the leech floor (2026-11-14)

Follows [DISCORD_DISTILL.md](DISCORD_DISTILL.md) and the four proposals. The numbers come from
[solo_rules_check.py](solo_rules_check.py): realfight, real route groups, stage 500, five seeds, median, no potions.
Its output is `$SOLO_SIM_DIR/solo_rules_check.md` and `.json`. Nothing here is built.

## 1. Port checks against MAW

MAW source: `~/github/Maw-Mod-MMMerge` at `8967ae88` (2026-11-12), the commit the port is synced to. The checks
read it directly.

| Question | MAW | Port | Simulation | Verdict |
| --- | --- | --- | --- | --- |
| XP penalty past level 100 | `expStep = 1000·L·max(1 + (L−100)·0.005, 1)` (`zzzMaw_Experience.lua:7-9`). It was 0.01 until `ba572ec2` "reduced experience to level up" on 2026-11-10. | `MawExperienceCurve.cpp:16`, 0.005 | 0.005 | **Port is current.** The Discord example (150→151 = 225K) is the old 1 % curve. Players who finished before 2026-11-10 played 1 %. |
| Solo XP bonus | None as such. Kill XP is split among the living members (`t.Exp/partyCount`, line ~196), so a solo takes the whole kill. The monster level bank gets the sum ÷ 5 for any party size. One kill gives at most (level + 1) × 1000. Quest XP is × 5 ÷ party size. | `MawExperienceRules.cpp:85-87, 170, 191` | yes | **Matches.** 5.0 did not remove anything: the "solo bonus" is that the kill is not split. See the level table below. |
| Speed gives dodge | A monster's swing lands with `chanceToBeHit = 1/(1 + Speed/(100 + expectedStat(monster level)) × 0.5)` (`Formulas.lua:77-80`, hooked in `zzMaw_MonsterHit.lua`). Missiles roll twice. "Skilled" bosses never miss. Grandmaster Dodging adds its own `1 − 1/(1 + skill/200)`. | `mawChanceToBeHit`, `MawCombatRules.cpp:3885-3911` | `hit_on_me`: hit, or hit² for missiles | **Matches.** At stage 500 BM the solo is hit 61–78 % of the time. |
| Player resistance and armour feeding monster damage | Monster damage = expected player vitality(level of the B tier) ÷ hits to kill [14, 10, 7, 6.5, 6, 5.5, 5, 4.5, 4] by difficulty, then × tier and boss multipliers (`Estimates.lua:457-497`). Vitality = expected HP ÷ (expected damage taken × expected hit chance × legendary cut) × the Cover multiplier, which uses the solo Cover rate for a party of one. | `MawBalanceModel` | `mon_dmg_b` from the model | **Matches.** Only the model's assumptions feed monster damage, never your own gear. Buying resistance helps you; changing what the model assumes is what moves monsters. This is why solo power must stay outside the model. |
| +50 % weapon-skill model bug (2026-11-04) | `ca376629` "better assumptions" dropped `SKILL_ENCHANT_MULT` (×1.5) from the expected melee skill. It stays on the Armsmaster estimate. | `MawBalanceModel.cpp:761-763`: melee skill = estimate + 10·ramp, Armsmaster × 1.5 | yes | **Port has the fix** (synced past it). |
| Leech | §2 | `MawCombatRules.cpp:3361-3420` | `realfight.py` heal per blow | **Matches, floor included.** |
| Known deviation | | Seraph/Shaman flat cut misses MAW's chanceToBeHit × legendaryDamageTaken (`mawClassDefense`) | uses the port's | Port bug, 25–40 % too generous. Still open. |

**What the solo level lead buys now.** A solo's experience is five times a party member's, and the monster bank
follows the party member. So the solo's level against the monster bank level is:

| Monster bank level | 100 | 150 | 200 | 250 | 300 | 400 |
| --- | --- | --- | --- | --- | --- | --- |
| Old linear curve (level × 1000) | 222 | 334 | 446 | 558 | 670 | 893 |
| 5.0 before 2026-11-10 (1 %) | 191 | 265 | 347 | 430 | 515 | 685 |
| 5.0 now (0.5 %) | 202 | 285 | 371 | 456 | 542 | 714 |

The lead fell from ×2.2 to ×1.8. Monster damage depends only on monster level, so the lead is all a solo has, and
each extra level buys less above 500 (POWER_GAP.md: L³, not L⁶).

## 2. The leech floor, explained

MAW's leech (`Damage.lua:1207-1290`, ported in `MawCombatRules.cpp:3361-3420`) heals on every blow that does damage,
taking the larger of two terms:

1. **Proportional:** heal = your max HP × leech % × (damage dealt ÷ max HP of the B-tier version of that monster).
   - Overkill does not count.
   - The physical part heals at your melee or ranged leech, the elemental part (weapon enchantments, auras) at your
     spell leech.
   - Dealing a whole B monster's HP heals your whole leech % of max HP.
   - Map affix 32 cuts this term.
2. **Floor:** heal = your max HP × leech % ÷ 5 × recovery of that attack ÷ 100.
   - Recovery is the attack's or spell's delay in ticks. The port counts 60 ticks per second, so 100 recovery is
     about 1.7 s.
   - Area spells divide the floor by 2.5. Fire Spike, Meteor Shower and Starburst divide it by 4.

**The floor does not depend on attack speed**, because slower blows get a larger floor. Per second it is about
**0.12 × leech % of max HP** (10 % leech → 1.2 % of max HP per second). The proportional term per second is
(DPS ÷ B monster HP) × leech % of max HP. **It is larger than the floor whenever you kill a B monster in under about
8 s.** So the floor only helps slow killers: casters, and anyone fighting monsters far above their level. It answers
Malekith's 2025 "fighting higher level monsters less punishing". **It is already in 5.0**; DISCORD_DISTILL.md first
listed it as unbuilt.

**Worked example: Death Knight (Minotaur), BM stage 500.**

| Quantity | Value |
| --- | --- |
| Max HP | 13.6k |
| Leech | 10 % (Blood) |
| Melee DPS | 14.7k |
| B monster HP | 70k |
| Proportional term | 14.7k ÷ 70k × 10 % = 2.1 % of max HP per second (286 HP/s) |
| Floor term | 1.2 % per second (163 HP/s) |
| Regeneration | 635 HP/s, 4.7 % |

Against that, BM monsters are sized to kill the expected character in 4 landed hits each, and a pull of four swings
every ~2 s. To win on sustain alone, regeneration would have to restore **48–180 % of max HP per second**
(POWER_GAP.md). Leech of any reasonable size gives 2–5 %.

**Leech is a feel and edge lever, not the answer to BM.** Both terms are a share of max HP, so more HP scales leech
too, but never relative to the incoming damage. Doubling the floor (R2 below) moves pulls of four by 2–10 points.

## 3. The concrete solo rules

All of these apply to a party of one only, like MAW's existing solo rules (`MawSoloMasterySkills`, solo Cover,
doubled buff durations). None of them enter `MawBalanceModel`. The DISCORD_DISTILL caveat stands: MAW means
Beyond Madness to be barely clearable, so these are OpenYAMM's own solo rules.

### Rules for every solo, from the start

| # | Rule | Exact change | Source | Hook |
| --- | --- | --- | --- | --- |
| R1 | **Lone Discipline** | Bodybuilding one mastery above the class cap at the first promotion and Grandmaster at the final one. HP: Death Knight and Seraph ×2.4, Arch Mage ×1.6. | MAW lifts mastery caps for a solo already. The Discord thread: ">70 Bodybuilding still one-shot". | `soloMastery` (`MawTrainerHints.cpp:168, 251`), `applyProgressionMasteries` |
| R2 | **Lone Leech** | Every solo has +5 % leech on melee, ranged and spells. The leech floor uses ÷2.5 instead of ÷5 (2.4 % of max HP per second at 10 %). | Malekith on the solo Dragon: "no leech is very limiting in solo… leech would really make sense". | `mawLeech`; the floor at `MawCombatRules.cpp:3405, 3410` |
| R3 | **Unbroken** | The part of one landed hit above 30 % of max HP is halved, after the floor. It never applies below that, so the 90 % reduction cap holds for ordinary hits. | "you can't escape oneshots" (Malekith, 2026-01-20); "randomly one shotted" (2026-11-14). | a `m_damageToCharacter` stage after "solo-cover" (`MawCombatRules.cpp:1177`) |
| R4 | **Lone Guard** | A class's own earned cuts act after the floor: the Death Knight's Body/Dark (×0.59 at 70), the Shaman's Air, a Grandmaster shield (×0.85). The total stays inside the shared ×0.25 after-floor clamp. | TALENTS M1. The 90 % cap is MAW's; this is the one rule that goes around it, so it stays small and earned by class. | the mitigation flag, `legendaryDefense` |
| R5 | **Sweeping Blows** | Every melee swing also strikes up to 1/2/4 more monsters within reach (one-handed, dual, two-handed) for 40 % + 0.25 % per weapon-skill point, at most 75 % (about 60 % at stage 500). The Seraph's Body heal applies per target at that share. | TALENTS M3. Melee is single-target, and a solo has one action against five. | `talentExtraBlow` / `pickTalentTargets` |
| R6 | **Solo skill points** | A solo character gets +50 % skill points per level. Skill caps (Mana Shield 50, Alchemy) stay. | Malekith accepted "solo at party level with more skill points" (2026-08-22/24) and has not built it. | the level-up skill points (needs a harness run; not measured here) |
| R7 | **Cheaper late training** | Master and Grandmaster teacher prices for a solo on Road to Insanity and Beyond Madness ÷ 3. | A player proposed it; Malekith: "this could work". Gold was the solo bottleneck. | `MawSkillFormulas.cpp:143-151` |

### What a solo earns by grinding: Road to Insanity, Beyond Madness and dimension maps only

| # | Layer | Exact change | Source |
| --- | --- | --- | --- |
| G1 | **Legend points** | TALENTS M5: one point per 2 levels above 200 on BM and per 4 on Road to Insanity, plus one per first dimension map of a new Power. Lines: Vitality +1 % HP, Ferocity +1 % damage, Warding ×0.995 after the floor (150 at most), Alacrity +0.5 % speed (50 at most). About 150 points at stage 500 and 300 at the end of BM. | Malekith's ring of your choice per completed game (2025-06-16) is the same idea at a coarser grain. |
| G2 | **Cubes past +20 %** | A Crafting Cube keeps raising an item's base past 20 % at a rising cost (ITEMS Ascension), about ×1.8 weapon damage at full. | 5.0 cubes already give +20 %. |
| G3 | **Flat-stat gems in sockets** | Malekith's unfinished 5.0 plan: one socket per item, the gem tier from the dimension map's Power. | "Still need to add the gem system". |
| G4 | **Choosing the enchant** | A Pearl of Memory rerolls one chosen enchant, choosing between three rolls. It works on items above tier 16. | Players' main 5.0 complaint (late gear stops improving); MAW's own "crafting is close to deterministic". |
| G5 | **The farm** | MAW's dimension maps and Emeralds of Power (`MawDimensionMaps.cpp`), available to a solo on BM from stage 300. Repeat clears give a quarter of the XP. The next map comes from currency, not from a map drop. | Malekith: no maps that drop maps; arena gold already makes emeralds unlimited. |

## 4. What the rules do (realfight, stage 500)

Each cell: groups beaten pulled four at a time % / seconds per monster; whole groups at once %. Columns are
cumulative; LP = the Legend points of G1 (150 at stage 500, 300 at the end of BM, proxied as HP, damage and
after-floor cut).

**Beyond Madness**

| Build | Today | R1 | +R2 | +R3 | +R4 | +R5 | +LP 150 | +LP 300 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Champion, sword and shield | 1 / 3.6; 0 | 1 | 3 | 3 | 4 | 11 / 2.4; 7 | 58 / 2.1; 44 | 89 / 1.8; 78 |
| Champion, two-handed | 3 / 3.2; 1 | 3 | 6 | 7 | 7 | 13 / 1.9; 8 | 72 / 1.7; 54 | 90 / 1.5; 86 |
| Minotaur Lord, dual | 10 / 3.5; 4 | 10 | 12 | 12 | 12 | 22 / 2.2; 16 | 82 / 1.9; 67 | 94 / 1.6; 90 |
| Troll-race Champion | 4 / 3.9; 2 | 4 | 6 | 6 | 6 | 10 / 2.5; 6 | 59 / 2.3; 41 | 90 / 2.0; 77 |
| Vampire Knight | 6 / 2.9; 3 | 6 | 10 | 10 | 10 | 23 / 1.9; 16 | 76 / 1.6; 57 | 91 / 1.4; 89 |
| Master (Monk) | 2 / 3.6; 1 | 2 | 3 | 4 | 4 | 7 / 2.5; 4 | 49 / 2.2; 33 | 85 / 2.0; 67 |
| Lich King (DK, Vampire) | 1 / 3.8; 0 | 22 | 32 | 33 | 63 | 65 / 4.2; 51 | 94 / 3.0; 90 | 100 / 2.3; 95 |
| Lich King (DK, Minotaur dual) | 3 / 2.2; 1 | 24 | 28 | 29 | 61 | 81 / 2.3; 56 | 94 / 1.7; 90 | 100 / 1.3; 94 |
| Archangel (Seraph) | 47 / 4.8; 29 | 64 | 69 | 75 | 75 | 78 / 3.4; 50 | 89 / 2.5; 86 | 100 / 1.9; 90 |
| War Troll | 57 / 16.7; 26 | 57 | 62 | 62 | 62 | 58 / 10.7; 28 | 89 / 7.5; 71 | 100 / 5.9; 87 |
| Great Wyrm (Dragon) | 84 / 2.0; 60 | 84 | 84 | 87 | 87 | 87 / 2.1; 64 | 95 / 1.4; 87 | 100 / 1.0; 92 |
| Archer | 1 / 1.8; 0 | 1 | 2 | 3 | 3 | 3 / 2.1; 1 | 24 / 2.0; 9 | 75 / 1.7; 40 |

**Melee builds (Dragon and Archer excluded), minimum and median of pulls of four:**

| Difficulty | Today | R1–R5 | +LP 150 | +LP 300 |
| --- | --- | --- | --- | --- |
| Beyond Madness | 1 / 4 | 7 / 23 | 49 / 79 | 85 / 92 |
| Road to Insanity | 44 / 60 | 69 / 88 | 99 / 100 | 100 |
| Doom | 55 / 82 | 85 / 100 | 100 | 100 |
| Nightmare | 96 / 100 | 100 | 100 | 100 |

**Reading:**
- **R1 and R4 rescue the classes MAW's own caps make weak** (Death Knight 1 → 63 %, Seraph 47 → 75 %). R5 cuts every
  melee build's time per monster by about 40 % and raises Road to Insanity the most.
- **R2 and R3 move little in this model.** R2 is the leech arithmetic of §2. R3 helps only where single hits exceed
  30 % of HP, and realfight averages hits, so it cannot show variance: R3's real value is that a bad roll or a boss
  no longer one-shots. It needs a variance check (a per-hit fight model, or the harness) before its number is tuned.
- **Grinding is what carries Beyond Madness**, as the goal asks. The rules give 7–81 %; 150 Legend points give
  49–94 %; 300 give 85–100 % with whole groups at 67–95 %. That is the "roll through" end of POWER_GAP's targets for
  every melee build except the Monk and the sword-and-shield Champion.
- **Lower difficulties for a solo:**
  - Road to Insanity becomes winnable for every melee build from the rules alone (69–100 %).
  - Doom and Nightmare were already won; they get faster.
  - Legend points are earned only on Road to Insanity and BM, so they never touch Nightmare or Doom runs.

  This is the price of the rules being solo-wide rather than BM-only. A solo on Road to Insanity is today 44–69 %
  (Discord: "melee in the gutter"), so it is intended.
- **The Archer gains nothing from the rules** (its gap is range, which realfight does not model). Neither do casters
  (not in this table; see TALENTS §1.6). Both need the ranged and crowd-control model first.

## 5. Order of work

1. **Port bug:** the Seraph/Shaman flat cut (`mawClassDefense`); it lowers the Seraph rows a little.
2. **R1, R6, R7:** trainer and level-up rules, small and in MAW's own spirit. Then rerun the harness, since R6 needs
   it.
3. **R4 and R5**, the measured big movers, with the shared after-floor clamp.
4. **R2, R3,** then a per-hit variance check of R3.
5. **G1 Legend points, then G4, G2, G3, G5** with the rift phase of ENDGAME_LOOP §3 to measure hours.

Decisions: are R1–R7 always on for a solo, or a "Lone Wanderer" option at character creation that stays off for MAW
purists? And should R4, the only rule that goes around MAW's 90 % cap, be in the first set? The measured case for it
is the Death Knight (33 → 63 %).

## 6. Direction after review (user, 2026-11-14)

The user's decisions:
- The rules become **talents of the solo run** (`assets_dev/engine/data_tables/talents.yml`, devdocs/solo_action/TALENTS.md). A
  character earns them with talent points as it levels, so early play runs without them and they arrive about when
  the content needs them.
- **Grinding is not gated by difficulty.** It works across the whole MAW solo run.

### Where each rule came from

Checked against [discord_notes/](discord_notes/).

| Rule | Origin | What the Discord has |
| --- | --- | --- |
| R1 Bodybuilding to Grandmaster | **Ours** (TALENTS M2) | Nobody proposed it. The precedent is Malekith's: a solo masters the utility skills regardless of class (2024-03-03), and he considered Grandmaster Cover/Bodybuilding for the Dragon (2024-09-19). Players: "randomly one shotted ... with over 70 points in BB" (2026-11-14). |
| R2 Solo leech | **Half** | Malekith on the solo Dragon: "no leech is very limiting in solo ... leech would really make sense, I'm just not sure how to do it" (2026-06-23). The +5 % and ÷2.5 are ours. |
| R3 One-shot guard | **Ours** | It answers a complaint both sides raise: "in solo you are much tougher, but you can't escape oneshots" (Malekith, 2026-01-20). |
| R4 Class cuts after the floor | **Ours** (TALENTS M1) | It goes against the developer's 90 % cap (2026-08-08). |
| R5 Sweeping Blows | **Ours** (TALENTS M3) | The problem is his: "most melee in solo with no AoE are a bit sad" (2026-08-29). The run's Cleave and Whirlwind are actives on cooldowns; R5 is the passive version. |
| R6 Solo skill points | **Community** | Keyen: "make solo same level as party but with a skillpoint multiplier"; Malekith: "will work on this" (2026-08-22/24). Before that, Malekith's own "double skill points" for solo (2026-08-15). |
| R7 Cheaper late training | **Community** | BootsandCats; Malekith: "this could work" (pre-5.0 Madness). |

### As talents

The table today: 17 talents, 61 ranks, one point per 10 levels (50 points at level 500, full near level 610).

| Talent | Tree | Ranks | Per rank | From |
| --- | --- | --- | --- | --- |
| Bloodthirst | all | 3 | +2 % leech on melee, ranged and spells (MAW keeps three leech values; the elemental part of a weapon hit uses the spell one); the floor's ÷5 becomes ÷4, ÷3, ÷2.5 | R2 |
| Unbroken (**keystone**) | all | 1 | The part of one hit above 30 % of max HP is halved | R3 |
| Class Oath (**keystone**) | per class | 1 | The class's own cuts act after the floor, inside the ×0.25 clamp (TALENTS M4) | R4 |
| Sweeping Blows | melee | 3 | Every swing also strikes 1 / 2 / 4 more monsters at 40 % + 0.25 % per weapon-skill point (at most 75 %). It needs Cleave. | R5 |
| Legend lines | all | no limit | Vitality +1 % HP, Ferocity +1 % damage, Warding ×0.995 after the floor (150 at most), Alacrity +0.5 % speed (50 at most) | G1 |

**Innate, not a talent (user, 2026-11-14): R1 Lone Discipline.** Every solo character trains Bodybuilding one mastery
above its class cap after the first promotion and to Grandmaster after the final one. As a talent it would be a
dead pick for the classes that already have Grandmaster; as a rule it only lifts the classes MAW caps.

**Keystones.** Unbroken and the Oaths are worth far more than a rank of anything else (R4 alone: Death Knight
33 → 63 %). They are keystones: one keystone slot per 100 levels (or per world promotion), chosen from a short list,
not bought with ordinary points. Their numbers are set only after the calibration below.

**Leech with area hits.** The proportional term counts each struck monster, so a Sweeping Blow on five monsters
leeches about 3.4× a single blow. MAW only divides the *floor* for area spells (÷2.5). Calibration has to choose
whether extra blows leech at their share, at a reduced rate, or not at all.

**Calibration before release.** No talent numbers ship until:
- the harness runs with the real talent effects of a solo run;
- R3 is checked against a per-hit (variance) fight model;
- the keystone combinations are swept for outliers (Dragon or Troll with Unbroken and an Oath; leech with Sweeping
  Blows);
- Nightmare and Doom stay within agreed time-per-monster bounds.

R6 and R7 stay base rules of the solo run, not talents: they are the economy the talents sit on. R6 overlaps with
the talent points, so the harness should check whether a solo still lacks skill points before it is built.

**When they are needed.**
- Below level 200, every difficulty is 86–100 % without them, and Nightmare and Doom stay winnable to level 500
  (Doom's melee minimum is 55 %).
- The new rows matter from about level 300 on Road to Insanity and Beyond Madness.

So the talent timing fits, but the point budget does not:
- Bloodthirst and Sweeping Blows above add 6 ranks (about 67 points for the whole tree); keystones are separate.
- The measured Beyond Madness line needs about 150 Legend points at level 500 and 300 at the end.

Levels alone give 50 points by level 500.

**Points.** The grinding layer pays talent points:
- one per 10 levels, as now;
- one per Legend threshold of experience past level 200;
- one per first clear of a dimension map of a new Power.

Surplus points flow into the uncapped Legend lines.

### Grinding without a difficulty gate

Earlier proposals gated grinding to Road to Insanity and Beyond Madness, so that a flat buff would not trivialise
Nightmare to Insanity (POWER_GAP). Ungated grinding still keeps lower difficulties sensible, for two reasons:
- **Points follow levels and experience.** Each difficulty ends at its own level (Doom around 250, Beyond Madness
  around 500, MAW's 2026-08-17 numbers), so a Doom run earns fewer points than a Beyond Madness run without a gate.
- **Over-levelling a difficulty by grinding is the player's choice,** in the solo run only. MAW's balance model never
  sees the points.

The rates should be checked once the rift phase of ENDGAME_LOOP §3 exists, against "about 40 h to beat pulls of four,
about 100 h to mash" on Beyond Madness.
