# X9's Dragon Clouds devices (D-59)

Quest experience on the counted route, per member:
- **Before the devices:** the optional ledger is Q-C25 24.0k + Q-F1 17k (Alister 5k, the Tome 4k, the Eye 8k) + Q-F2 24k (D-57 Q32's split) = **65k of 70k (0.93)**. A2's 64k used D-57's rounded "40k" for Q-F1 + Q-F2. The exact sum is 41k.
- **With the devices:** the crystals add 12k, which gives **77k (1.10)**.

## 1. The crystal balls (Mind, Past, Future of the Dragon)

**DECISION:**
- Each ball checks the clicking member's **current Intellect ≥ 60** (`ActualIntellect`, so items and buffs count). The source's check is 200.
- **Success:** the ball's own source passage and its phrase: "The knowledge is limitless." / "The history is endless." / "The possibilities are unlimited." (`dark/aazex128:23, :25, :27`).
- **Failure:** **70 Mind damage** and **Weak** on the clicking member only, as A3 has written. This is never lethal to a member at full hit points, the same reading as the Eye's "Die fools!".
- No player bit, no limit, retries allowed. No experience, no stat and no item either way.

**WHY:**
- 60 is Act VI's check size: FD-02's sarcophagi use Might ≥ 60 with buffs counting. The Well of Fantastic Skill, on the same cloud, is the fixed help (D-22's rule).
- A caster at about 45 base Intellect (25–30 at creation + 15 from the ledger) passes after the well or with one item. A fighter at about 25 fails and lives.
- The balls only hint at INFINITY, which the books and the "forever" note already give, so failing costs nothing on the path. The ledger stays at 0.

**WHO ACTS:**
- **A3:** `q-f1.yml` `ball_mind` / `ball_past` / `ball_future`: change `IsAtLeast(ActualIntellect, 50)` to `60`, remove the "D-59 pending" markers and regenerate. The texts stay.
- **A2:** ledger row "X9 crystal balls: check only (Intellect ≥ 60), none".
- **A5:** each `deco:ball_*` (dec57 on its plinth) is a click to its hook. The playtest needs two members:
  - one below 60, who takes damage, is Weak and lives;
  - one at 60 or more after the well, who hears the phrase.

**REVERSIBLE:** Yes. It is one number in three hooks.

## 2. The Well of Fantastic Skill

**DECISION:**
- **+20 to Might, Intellect, Personality, Endurance, Accuracy, Speed and Luck** as bonus (temporary) stats until rest, for every member present.
- **Once a day for the party** (`Xeen.usedToday("x9_well")`). A second drink that day gives "The water is cool and refreshing." and nothing else.
- Nothing permanent and no experience. It adds to other buffs, D5's shrine included, as any two buffs do.

**WHY:**
- It continues the temporary all-stat ladder: D1's prayer shrine +10 (Act III), D5's Shrine of Great Power +15 (Act V, D-49 Q8), and X9 +20 (optional, levels 55–70).
- It matches D5's Fountain of Might (+20 to one stat until rest). QUESTS forbids +20 only as a permanent gain.
- It is also the balls' fixed help. Its ledger size is "temporary", outside the 70k.

**WHO ACTS:**
- **A3:** `q-f1.well` as written. Remove the "D-59 pending" marker.
- **A2:** permanent-stat ledger, Act VI row: "X9 Well of Fantastic Skill: +20 all seven stats until rest, daily (not permanent)".
- **A5:** `platform:well_water` and its curb click call `q-f1.well`. Playtest:
  - the stats rise by 20;
  - a second drink the same day gives no gain;
  - after rest the stats are back to their earlier values.

**REVERSIBLE:** Yes. It is one number in one hook.

## 3. The Dragon Power Crystals

**DECISION:**
- Three crystals, each paying the clicking member experience **once per character**:
  - **crystal_1: 3,000** (bit 11362);
  - **crystal_2: 4,000** (bit 11363);
  - **crystal_3: 5,000** (bit 11364).
- Each first touch also deals **70 Energy damage** to the clicking member (the surge), never lethal to a member at full hit points.
- A member's second touch gives "Dragon Power Crystal. It has nothing more for you." and no damage.
- That is 12,000 per character in all. The source's 3:4:5 order is kept.

**WHY:**
- Scaled by L(L+10) from Act V's Books of the Dead (3k at about level 50), one crystal is worth about 4.5k at Q-F1's level 62. The three average 4k.
- Q-F1 then pays 29k per member, about 0.47 of a level against QUESTS' 0.75 cap (46.5k at level 62).
- The optional line becomes 77k of 70k (1.10): inside the 15 % gate and under D-53's 1.12 trigger, with about 1.4k of margin left.

**WHO ACTS:**
- **A3:** `q-f1.yml` `crystal_1`–`crystal_3` as written. Remove the "D-59 pending" markers, and add "X9's crystals 12,000 once per character; the well +20 all stats until rest, daily" to `rewards.stats`.
- **A2:**
  - Ledger rows "X9 Dragon Power Crystals: 3k / 4k / 5k once per character, 12k". Optional quest XP 65k → 77k (1.10).
  - **Fix `balance.py`:** `quest_xp_by_act()` counts only `xp:` keys. Unlike `npc_xp_by_act()`, it skips `lua: AddValue(Experience, n)`, so it misses the Tome's 4k and the crystals' 12k (Q-F1 reads 13k, not 29k).
  - It also misses DD-12's Soul Waters in `m24.yml` (1k + 2k, Act IV).
  - Make it count those lines, recount, and publish the optional and Act IV figures.
  - If Act IV then goes past 1.12, or the optional line past 1.12 once Q-F2's hooks land, take it to a decider rather than absorbing it (D-53's rule).
- **A5:** `deco:crystal_1` (crys5, [20600, 19600]), `deco:crystal_2` (crys6, [21950, 19400]) and `deco:crystal_3` (crclstr, [22350, 18950]) are clicks to `q-f1.crystal_1`–`3`. Playtest:
  - the first touch pays and damages;
  - the same member's second touch gives the "nothing more" line;
  - another member is still paid;
  - nobody dies from full hit points.

**REVERSIBLE:** Yes. It is three numbers in three hooks and a recount.

## SUMMARY ROW

| D-59 | 2026-11-21 | X9's Dragon Clouds devices (D-57 Q36) | Balls: Intellect ≥ 60 (buffs count) gives the clue, else 70 Mind damage and Weak; no reward, retry. Well: +20 all seven stats until rest, daily. Crystals: 3k/4k/5k once per character, 70 Energy surge. Optional 77k of 70k (1.10). balance.py to count quest-file `AddValue(Experience)` | A3 (q-f1.yml), A2 (ledgers, balance.py, recount), A5 (X9 clicks, playtests) |

---

Notes for the caller:
- **The device text is already written.** A3's `/home/pjasicek/github/OpenYAMM/assets_dev/worlds/xeen/source/quests/q-f1.yml` has A2's three proposals marked "D-59 pending". The one real change is the balls' Intellect check, from 50 to 60.
- **There is a counting gap in `balance.py`.** In `/home/pjasicek/github/OpenYAMM/tools/xeen/balance.py`, `quest_xp_by_act()` does not count Lua `AddValue(Experience, n)` in quest files, so the Tome (4k), the crystals (12k) and DD-12's Soul Waters in `m24.yml` (3k, Act IV) are left out.
  - If the published Act IV figure of 176.5k leaves the Soul Waters out, Act IV is really 179.5k of 160k (1.12), right at D-53's trigger. A2 should confirm.
- **Optional quest XP was off by 1k.** A2's 64k used D-57's rounded 40k for Q-F1 + Q-F2; the exact sum is 41k, so it is 65k before the devices and 77k (1.10) with them.
- **Source detail:** the source puts about 21 crystal tiles on one random +3/+4/+5-level event (`mazex128`). A5 built three crystals, which matches A2's reading of 3k/4k/5k.
