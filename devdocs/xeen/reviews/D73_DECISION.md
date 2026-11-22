# Skill teachers' order and places: decisions (D-73)

Inputs: `teachers_plan.yml` (116 offers in 25 places, counting the two `extra:` offers), the town files `x2`, `x3`, `x4`, `x5`, `d1`, `d3`, `d4` and `dd03.yml`, QUESTS §1, §2 and §4.2, MAPS level bands, WORLD_DESIGN §5, MM678_CALIBRATION §5, the engine's `class_skills.txt` and `trainer_places.txt`, and the user's answer on finding 3 (relayed by the orchestrator).

## 1. Dodging and Unarmed: the Master is reachable before the Expert

**DECISION:** Move the Expert offers of Dodging and Unarmed to Rivercity, to **Martial Training** (house 4080 on the skill row, which today holds only Flint, the Armsmaster Expert). Add one new resident there who teaches both Experts. Two residents are also fine; A4 picks the name and the portrait in the MM7 style, from X2's NPC block. Castleview keeps the Masters (Brother Otto 4923, Sister Hannah 4924), and Shangri-La keeps the Grandmasters. At Kai Wu's monastery, Brother Lin (4522) and Sister Mei (4523) lose their `teaches` and stay as flavour; Kai Wu keeps Staff Master. The plan changes to `Dodging: [rivercity, castleview, shangrila]` and `Unarmed: [rivercity, castleview, shangrila]`. Rivercity goes from 18 to 20 offers, Castleview stays at 10, and Kai Wu goes from 3 to 1. A4 also adds a level-order check to `towns.py` as a warning: a Master place's level must not be below its Expert place's level. Per the user, it does not check whether a Grandmaster comes before its Master.

**WHY:**
- **A player would plainly be stuck.** The engine sells Master only to an Expert. Castleview's Masters (D1, about level 15–21) show up before the only Expert, at Kai Wu's monastery. That is in X5, which MAPS puts in Act III at 24 → 28, later than the plan's 22.
- **The Monk is the class that gets hurt.** Per `class_skills.txt`, the base Monk can reach Master in both skills, and both are its core skills. The Vertigo roster has a Monk from the start (Grim, 409, Unarmed 2 and Dodging 2). Every other class gets its core Experts in Vertigo or Rivercity (level 1–7), and the Monk's came at 24 or later. Knights, Thieves and Rangers also learn Dodging and Unarmed, so they gain from an early Expert too.
- **Why Rivercity's Martial Training:** WORLD_DESIGN §5.1 names it as part of the hub's skill row, so the place fits the source.
- **Why the Masters stay in Castleview:** it is the smallest change. It leaves Q-D3's Drawkcab monks as they are, and the order becomes 7 → about 18 → 45.

**WHO ACTS:**
- A4: the plan, `x2.yml` (the new resident in 4080), `x5.yml` (drop the two `teaches`), a `gen_towns` run, `towns.py --strict` and the new order check.
- A3: check that Lin's and Mei's topics do not offer teaching.
- No map lane is involved: the house and its door already exist.

**REVERSIBLE:** Yes. This is data only.

## 2. Identify Item: Master at Kalindra, Grandmaster in the wizard quarter

**DECISION:** No change to the offers. Correct the place metadata in the plan so that a later scan reads the real reach levels:
- **A new place, `kalindra_observatory`** (DD-03, Act III, level about 25, `when: "Castle Kalindra stage 2"`), for the Identify Item Master. Astronomer Tycho (5006, The Observatory 4504) opens on `m19.stage2`. Today the offer sits on `kalindra`, which is the stage-4 place at level 40.
- **`wizard_quarter`:** level 32 → 39, Act IV. D-16 moved Q-D14 to level 39.
- **`kaiwu` and `freeda`:** level 22 → 24, Act III, matching X5's band in MAPS.
- **`nightshadow`:** level 24 → 14 (X3 is 13 → 16), with the note that both of its offers are in houses that are open before the liberation.

**WHY:** The real order is already Expert 7 → Master about 25 (stage 2, Act III) → Grandmaster 39, so nothing is inverted. The finding came from the stage-4 place level being applied to an offer that opens at stage 2. Even if a Grandmaster were reachable first, the user has ruled that this is not a fault on its own. The metadata is only fixed so the new order check in finding 1 works from true levels.

**WHO ACTS:** A4 (the plan, and `towns.py` resolving the new place the same way it resolves `kalindra_court`).

**REVERSIBLE:** Yes.

## 3. Early Grandmasters in the wizard quarter (Mind Magic, Identify Item, Alchemy)

**DECISION:** **The user's decision (2026-11-21):** they stay. "I don't mind early grandmasters, it's gated anyway behind the promos … MM6–MM8 also have GMs all over the place." No change anywhere. With D-16 the quarter opens at about 39 anyway, not 32.

**WHY:** It is the user's call, and the reason holds. Grandmaster caps are reached only after a promotion, and the tier-2 promotions are played on Darkside at about levels 23–50.

**WHO ACTS:** Nobody. A4 notes it in the plan's header comment.

**REVERSIBLE:** Yes.

## 4. Other checks

### 4a. Teaching load per place

**DECISION:** No town is overloaded. All stay as they are, with Rivercity at 20 after finding 1.

**WHY:**
- In the engine's `trainer_places.txt`, the busiest MM6–MM8 outdoor maps have 21, 18, 18 and 17 teacher houses. MM9's Thjorgard has 28 and Sturmford 20 (calibration §5).
- Rivercity at 20 is the hub's share. Vertigo's 13 Experts sit in the range of a start town.
- Castleview's 10 fits a second hub.
- Shangri-La's 10 Grandmasters are the hidden town's purpose (WORLD_DESIGN §5.1 and D-5.1).
- The world total of 116 is inside 100–145.

**WHO ACTS:** Nobody.

**REVERSIBLE:** Not applicable.

### 4b. Grandmasters of the classes' core skills

**DECISION:** None is missing. Every core skill has a Grandmaster reachable by the end of Act V or at Olympus. All stay as they are.

**WHY:**
- The Grandmasters come at Lakeside 36, Wizard quarter 39, Kalindra stage 4 at about 40, Shangri-La about 40–45, Bosco 45, Necropolis 50 and Dragon Cave 50.
- Olympus (D7, Act VI, 55) is the latest. It holds Air, Spirit, Light, Spear, Merchant, Regeneration and Identify Monster.
- The class most affected is the Sorcerer, whose Air Grandmaster is the last of its four elements. Its Water, Fire and Earth Grandmasters come at 36 and 45. The Cleric's Spirit Grandmaster is also at Olympus. WORLD_DESIGN §5.2 deliberately gives Olympus its Grandmaster Light and Spirit guilds, and the user accepts Grandmasters spread anywhere. Light at Olympus and Dark at Necropolis mirror the late path cities of MM7.

**WHO ACTS:** Nobody.

**REVERSIBLE:** Not applicable.

### 4c. The four towns "open before its quest"

**DECISION:** All are intended. Nothing moves behind a liberation.

**WHY:**
- **Asp:** the Travel Pit, the Roadside Shrine and Sarah Slither teach nothing. All four of Asp's offers are behind `q-c5.done`.
- **Lakeside:** the Guild, Yachts, Old Gill and the Isle Ferry teach nothing. Its three offers (Leather and Water Grandmasters, Vampire Master) are behind `q-d22.done`.
- **Winterkill:** the Mindmeld Guild teaches nothing. Its three Masters are behind `q-c6.done`.
- **Nightshadow:** the Moon Guild (Mordecai, Dark Magic Expert, open at night) and Du Monay Manor (Vampire Expert) are open before Q-C7 by design. Each cursed town keeps one open house with its guildmaster's joke (WORLD_DESIGN §5.1). These are Experts that come before their Masters (Winterkill 26, Lakeside 36), and the Vampire class from the Castleview roster at level 15 needs that Expert early. All of these are WORLD_DESIGN §5.1's open edge services and joke houses, plus the ferry (D-12.1).

**WHO ACTS:** If `towns.py` reports these houses as warnings, A4 may mark them as open by design (a per-house flag, say `open_before: true`, with WORLD_DESIGN §5.1 as its reason) so the run prints nothing for them. This is optional.

**REVERSIBLE:** Yes.

## SUMMARY ROW

D-73 | 2026-11-21 | Teachers' order and places | Dodging/Unarmed Expert moves to Rivercity's Martial Training (Master was reachable first, Monk core); Castleview keeps Master; Kai Wu's monks become flavour. Identify Item in order (telescope stage 2); plan levels corrected. Early Grandmasters stay (user). Loads, Grandmaster reach, cursed-town houses fine. towns.py warns Master-before-Expert. | A4, A3
