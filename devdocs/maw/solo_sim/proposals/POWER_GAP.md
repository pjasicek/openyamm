# Power gap: how much more a solo needs for Beyond Madness

Balance proposal input, 2026-11-14. It answers one question with the existing solo simulation
([README](../README.md), [RESULTS](../RESULTS.md)): how much stronger a solo MAW character at stage 500 has to be
before Beyond Madness can be cleared, and which part of that strength matters. Nothing in the game or its data was
changed. The sweep script is [power_gap_sweep.py](power_gap_sweep.py).

## Summary

- **Pulling four at a time** (ok4 ≥ 90 %), a maxed melee or bow solo at Beyond Madness L500 needs about **×14
  effective power** (EHP × DPS; range ×9–22 over the seven melee/bow builds). Split evenly: **magic damage taken
  ×1/2.75, HP ×2.75, damage ×2.75** (median k = 2.72, range 2.4–3.4).
- **Whole groups at once** (ok ≥ 90 %) needs about **×120 effective power** (range ×68–169): **×7 on each of magic
  mitigation, HP and damage** (median k = 6.75, range 5.3–8.3). The mash pace (≤ 1 s or one swing per monster)
  comes almost free on top: k ≈ 7.6 (range 6.0–8.4). Weapons near or above 1 s per swing (two-handers, dual
  minotaurs, death knights) mostly cannot reach a literal 1 s per monster against single targets at any power, so
  the tables also give "one swing per monster".
- Monster-side equivalent: dividing the Beyond Madness L500 monsters' HP and damage by **~3.75** (range 2.9–4.25)
  gives ok4 ≥ 90 %; whole groups need **÷11** (range 7.8–16.5).
- **No single player lever is a good fix.** HP alone works but needs ×9.5–19 (pulls) and ×44–137 (whole groups).
  Damage alone hits a burst wall (a group kills the solo before one swing per monster is over) for four of the seven
  builds even at ×1000. Magic mitigation alone can never do it: magic is ~70 % of the incoming damage, so removing
  all of it raises EHP only ×1/0.3 ≈ ×3.3. Regeneration would have to restore 48–180 % of max HP per second.
- **Where the gap is:** the Beyond Madness L500 monsters are level ~321, against ~226–240 on every other difficulty
  at the same stage. Compared with Road to Insanity they have ×3.4 HP, ×3.0 physical and ×3.4 magic damage, so the
  power gap is about ×11 (3.4 × 3.2) before group size. A typical group kills a knight in ~2 s (insanity: ~5–6 s)
  while each monster takes ~5–7 s to kill (insanity: ~2.5 s). Mitigation is not the gap: the melee builds already
  take 10–24 % of a hit, and the sword-and-shield knight sits on MAW's 10 % floor for every damage type
  (`mawMitigatedDamage` in `game/rules/maw/MawCombatFormulas.cpp`).
- **Sanity check: any player-side buff of this size trivialises the lower difficulties.** ×2.75 on HP, damage and
  magic mitigation already gives every melee and bow build Nightmare L500 100 % / 100 % at 0.6–1.1 s per monster,
  and Doom/Insanity L500 ok4 = 100 % (whole groups 83–96 %). At ×7 every melee and bow build clears whole groups
  below Beyond Madness at 0.5–1.1 s per monster. The one change that buys the most without touching the other
  difficulties is a **Beyond-Madness-only cut of monster HP and damage at high stages** (÷3.5–4 for pull-four
  play, or a lower Beyond Madness level boost at stage 500). A player-side alternative has to scale with the
  monster's level above the character's level, so that it does nothing on Nightmare–Insanity.

## Method

- Input: the harness copy of 2026-11-14 (`pool_out_<difficulty>.jsonl`, `pool_meta.json`, `fights.json`,
  `monsters.json`) and `realfight.py` unchanged. The sweep script `exec`s realfight.py up to its `__main__` block
  and calls its `fight()` on scaled copies of the character rows.
- Cases: builds knight_sns, knight_2h, minotaur_dual, vamp_knight, dk_vampire, dk_minotaur_dual, archer, archmage,
  with dragon, seraph and troll as references; Beyond Madness, Road to Insanity and Doom at stage 500, and Beyond
  Madness at stage 200; five seeds each, each seed fighting every group of the 5 last-cleared and 5 next maps.
- Outcomes as in agg_real.py, without potions: **ok4** = share of monsters in groups beaten pulling four at a time
  (rest to full between pulls); **ok** = share in groups beaten all at once. **mash** = ok ≥ 90 % and at most 1 s
  of fighting per monster over the beaten whole groups; **mash 1 swing** relaxes that to max(1 s, 1.1 × the
  fastest attack's recovery).
- Levers (k ≥ 1 is always stronger): **HP** max HP × k (regeneration and potions stay absolute; leech heals scale
  with max HP as in realfight); **dmg** melee, breath, bow and spell damage × k; **magic** damage taken from all
  non-physical types × 1/k (grid columns Fire–Energy); **phys** physical damage taken × 1/k; **sustain** existing
  regeneration and leech × k; **regen** adds k % of max HP per second. Combinations: **A** HP, dmg ×k and magic
  taken ×1/k; **B** as A plus physical taken ×1/k; **C** magic taken fixed ×1/2 (magic at physical parity) with
  HP and dmg ×k; **mon** dmg ×k and all damage taken ×1/k, which is the same as dividing the monsters' HP and
  damage by k.
- Thresholds: log-space bisection between 1 and 1000 (11 steps, 0.3 % resolution) per seed; reported is the
  median over the five seeds. A seed's beaten share is monotone in k, so this equals the multiplier at which the
  median seed reaches the target. "ok" = already there today; "—" = not reached at ×1000 (or 1000 %/s).
- **Effective power P** = EHP multiplier × DPS multiplier, the product that decides an expected-value fight of a
  solo against a group (time to kill × incoming damage per second ≤ effective HP). EHP uses the build's physical
  share s of today's incoming damage: HP k → P = k; dmg k → k; magic k → 1/(s + (1−s)/k); A → k²/(s + (1−s)/k);
  B → k³; C → k²/(s + (1−s)/2); mon → k². The model bears this out: knight_sns needs HP ×137 alone or A at k = 7.52
  (P = 144) for whole groups.

## Results

Each cell is the multiplier k; in the combination tables P follows in brackets. Physical share = physical part of
today's expected incoming damage over all groups.

### 1. Single levers

HP, dmg, magic, phys and sustain are multipliers; regen is % of max HP restored per second.

#### madness L500: single levers

| build | phys share | HP ok4 | HP ok | dmg ok4 | dmg ok | magic ok4 | magic ok | phys ok4 | phys ok | sustain ok4 | sustain ok | regen %/s ok4 | regen %/s ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| knight_sns | 30 % | 16.7 | 137 | 18.0 | — | — | — | — | — | — | — | 48.3 | 211 |
| knight_2h | 28 % | 12.0 | 102 | — | — | — | — | — | — | — | — | 74.1 | 265 |
| minotaur_dual | 31 % | 9.55 | 63.8 | — | — | — | — | — | — | 21.5 | 96.9 | 48.6 | 174 |
| vamp_knight | 27 % | 11.5 | 43.9 | 11.2 | — | — | — | — | — | 88.8 | — | 68.8 | 174 |
| dk_vampire | 30 % | 17.8 | 75.8 | — | — | — | — | — | — | 25.4 | 77.6 | 156 | 400 |
| dk_minotaur_dual | 28 % | 18.2 | 66.2 | — | — | — | — | — | — | 29.3 | 103 | 181 | 527 |
| archer | 32 % | 19.0 | 128 | 24.8 | — | — | — | — | — | — | — | 91.2 | 342 |
| archmage | 30 % | — | — | — | — | — | — | — | — | — | — | 909 | — |
| dragon | 35 % | 2.56 | 5.80 | 2.32 | 2.92 | 1.97 | — | — | — | 3.35 | 11.7 | 19.2 | 87.7 |
| seraph | 18 % | 22.9 | 270 | — | — | 2.90 | — | — | — | — | — | 196 | 671 |
| troll | 37 % | 10.7 | 200 | 9.74 | — | — | — | — | — | 2.07 | 6.24 | 10.7 | 55.3 |

#### insanity L500: single levers

| build | phys share | HP ok4 | HP ok | dmg ok4 | dmg ok | magic ok4 | magic ok | phys ok4 | phys ok | sustain ok4 | sustain ok | regen %/s ok4 | regen %/s ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| knight_sns | 42 % | 2.07 | 7.34 | 2.11 | 8.93 | 13.4 | — | — | — | 5.08 | 18.7 | 8.22 | 54.4 |
| knight_2h | 38 % | 2.48 | 11.7 | 2.81 | — | 11.3 | — | — | — | — | — | 10.1 | 60.5 |
| minotaur_dual | 38 % | 2.24 | 10.3 | 2.46 | — | 3.21 | — | — | — | 4.17 | 25.6 | 7.39 | 57.5 |
| vamp_knight | 37 % | 1.85 | 6.68 | 1.90 | — | 3.45 | — | — | — | 7.59 | 25.1 | 11.0 | 61.2 |
| dk_vampire | 40 % | 2.63 | 10.7 | 3.04 | — | — | — | — | — | 4.04 | 17.9 | 25.0 | 128 |
| dk_minotaur_dual | 38 % | 3.04 | 11.3 | 2.83 | — | — | — | — | — | 6.18 | 29.3 | 39.2 | 178 |
| archer | 38 % | 2.95 | 10.7 | 3.17 | — | — | — | — | — | 14.9 | 57.1 | 23.7 | 109 |
| archmage | 38 % | 202 | — | — | 30.7 | — | — | — | — | — | — | 290 | 776 |
| dragon | 51 % | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok |
| seraph | 21 % | 1.15 | 5.10 | 1.17 | 5.62 | 1.03 | 2.10 | — | — | — | — | 3.64 | 43.7 |
| troll | 47 % | ok | 9.39 | ok | 10.1 | ok | — | ok | 3.38 | ok | 2.02 | ok | 12.1 |

#### doom L500: single levers

| build | phys share | HP ok4 | HP ok | dmg ok4 | dmg ok | magic ok4 | magic ok | phys ok4 | phys ok | sustain ok4 | sustain ok | regen %/s ok4 | regen %/s ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| knight_sns | 44 % | 1.41 | 5.27 | 1.41 | 6.52 | 1.69 | — | 2.63 | — | 4.11 | 12.3 | 2.10 | 27.4 |
| knight_2h | 38 % | 1.66 | 8.46 | 1.65 | — | 2.66 | — | — | — | — | — | 7.15 | 40.8 |
| minotaur_dual | 41 % | ok | 6.93 | ok | — | ok | — | ok | — | ok | 14.8 | ok | 28.3 |
| vamp_knight | 39 % | 1.36 | 4.40 | 1.39 | 4.35 | 1.86 | — | — | — | 3.04 | 12.9 | 4.77 | 36.3 |
| dk_vampire | 40 % | 2.47 | 7.67 | 2.09 | — | 3.15 | — | — | — | 3.88 | 11.9 | 25.3 | 90.7 |
| dk_minotaur_dual | 37 % | 2.29 | 7.77 | 2.22 | — | 3.00 | — | — | — | 3.80 | 13.5 | 23.7 | 81.5 |
| archer | 45 % | 2.24 | 8.18 | 2.12 | — | 4.86 | — | — | — | 9.91 | 30.9 | 10.5 | 53.8 |
| archmage | 42 % | 102 | 676 | 9.84 | 17.9 | — | — | — | — | — | — | 233 | 573 |
| dragon | 52 % | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok |
| seraph | 24 % | ok | 1.69 | ok | 1.89 | ok | 1.07 | ok | — | ok | — | ok | 11.0 |
| troll | 48 % | ok | 2.50 | ok | 2.33 | ok | 2.06 | ok | 1.31 | ok | 1.24 | ok | 2.66 |

#### madness L200: single levers

| build | phys share | HP ok4 | HP ok | dmg ok4 | dmg ok | magic ok4 | magic ok | phys ok4 | phys ok | sustain ok4 | sustain ok | regen %/s ok4 | regen %/s ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| knight_sns | 100 % | ok | 14.5 | ok | — | ok | — | ok | 9.08 | ok | — | ok | 33.9 |
| knight_2h | 100 % | 1.02 | 18.8 | 1.04 | — | — | — | 1.02 | 11.1 | — | — | 0.07 | 40.1 |
| minotaur_dual | 100 % | ok | 16.3 | ok | — | ok | — | ok | 7.32 | ok | 24.1 | ok | 59.5 |
| vamp_knight | 100 % | ok | 7.27 | ok | — | ok | — | ok | 6.14 | ok | 20.4 | ok | 40.6 |
| dk_vampire | 100 % | ok | 6.95 | ok | — | ok | — | ok | 4.37 | ok | 6.79 | ok | 50.8 |
| dk_minotaur_dual | 100 % | ok | 7.34 | ok | — | ok | — | ok | 4.93 | ok | 8.63 | ok | 72.4 |
| archer | 100 % | ok | 14.5 | ok | — | ok | — | ok | 10.2 | ok | — | ok | 61.5 |
| archmage | 100 % | 2.68 | 160 | 1.34 | 3.15 | — | — | 1.26 | 3.33 | — | — | 3.20 | 139 |
| dragon | 100 % | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok |
| seraph | 100 % | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok |
| troll | 100 % | ok | 20.6 | ok | — | ok | — | ok | 3.31 | ok | 4.15 | ok | 39.9 |

Reading the Beyond Madness L500 table:

- HP alone reaches ok4 at ×9.5–19 for the melee and bow builds (median ×16.7) and whole groups at ×44–137.
- Damage alone reaches ok4 only for builds with fast attacks (knight_sns ×18, vamp_knight ×11, archer ×25); for
  two-handers, dual minotaurs and death knights a pull of four kills the solo before four swings at ~1 s each are
  done, whatever the damage. Whole groups are out of reach by damage alone for every build except the dragon.
- Magic or physical mitigation alone never gets there (except dragon and seraph pulls): the other part of the
  incoming damage alone still kills. Regeneration would have to be 48–180 % of max HP per second (the troll's real
  regeneration is ~12 %/s), and multiplying the existing leech/regeneration needs ×20–90 where there is any.
- Archmage: no single lever works; it trails the melee builds by an order of magnitude everywhere (Results 3).

### 2. Balanced combinations and the mash pace

A = HP ×k, damage ×k, magic taken ×1/k. B = A plus physical taken ×1/k. C = magic taken ×1/2 fixed, HP and
damage ×k. mon = monster HP and damage ÷k. "mash 1 s" = whole groups at ≤ 1 s per monster; "mash 1 swing" =
≤ max(1 s, 1.1 × fastest attack recovery).

#### madness L500: combinations, k (P)

| build | A ok4 | A ok | A mash 1 s | A mash 1 swing | B ok4 | B ok | C ok4 | C ok | mon ok4 | mon ok | mon mash 1 swing |
|---|---|---|---|---|---|---|---|---|---|---|---|
| knight_sns | 2.86 (15) | 7.52 (144) | 8.40 (184) | 8.40 (184) | 2.49 (16) | 5.22 (142) | 3.22 (16) | 10.2 (161) | 3.75 (14) | 11.3 (128) | 11.3 (128) |
| knight_2h | 2.64 (13) | 6.46 (106) | — | 8.18 (181) | 2.29 (12) | 4.88 (116) | 2.64 (11) | 8.34 (109) | 3.66 (13) | 14.1 (198) | 14.1 (198) |
| minotaur_dual | 2.37 (9.4) | 6.10 (89) | — | 6.33 (96) | 2.15 (9.9) | 4.38 (84) | 2.42 (9.0) | 8.37 (107) | 2.90 (8.4) | 10.1 (102) | 10.1 (102) |
| vamp_knight | 2.46 (11) | 5.26 (68) | 6.02 (93) | 6.02 (93) | 2.22 (11) | 3.65 (49) | 2.66 (11) | 6.48 (66) | 3.47 (12) | 7.83 (61) | 7.83 (61) |
| dk_vampire | 3.37 (22) | 7.34 (135) | — | 7.59 (146) | 2.54 (16) | 4.40 (85) | 3.43 (18) | 10.5 (169) | 4.18 (17) | 10.3 (106) | 10.3 (106) |
| dk_minotaur_dual | 2.72 (14) | 6.75 (119) | 8.57 (204) | 6.75 (119) | 2.54 (16) | 4.53 (93) | 3.27 (17) | 10.9 (185) | 4.15 (17) | 16.5 (272) | 16.5 (272) |
| archer | 3.02 (17) | 8.29 (169) | 8.29 (169) | 8.29 (169) | 2.62 (18) | 5.49 (166) | 3.25 (16) | 10.6 (170) | 4.25 (18) | 13.0 (168) | 13.0 (168) |
| archmage | 13.9 (559) | 21.2 (1357) | 21.2 (1357) | 21.2 (1357) | 6.16 (234) | 12.0 (1733) | 21.2 (691) | 35.6 (1953) | 7.91 (63) | 12.5 (155) | 12.5 (155) |
| dragon | 1.17 (1.5) | 1.92 (5.3) | 1.92 (5.3) | 1.92 (5.3) | 1.16 (1.6) | 1.69 (4.8) | 1.00 (1.5) | 1.92 (5.4) | 1.22 (1.5) | 2.16 (4.7) | 2.16 (4.7) |
| seraph | 1.93 (6.1) | 4.67 (61) | 8.04 (226) | 8.04 (226) | 1.93 (7.2) | 2.80 (22) | 1.87 (5.9) | 10.8 (198) | 2.18 (4.8) | 3.04 (9.3) | 7.85 (62) |
| troll | 2.11 (6.7) | 7.44 (121) | 40.5 (4223) | 22.2 (1230) | 1.65 (4.5) | 4.10 (69) | 2.16 (6.8) | 10.4 (157) | 1.84 (3.4) | 5.66 (32) | 22.2 (492) |

#### insanity L500: combinations, k (P)

| build | A ok4 | A ok | A mash 1 s | A mash 1 swing | B ok4 | B ok | C ok4 | C ok | mon ok4 | mon ok | mon mash 1 swing |
|---|---|---|---|---|---|---|---|---|---|---|---|
| knight_sns | 1.32 (2.0) | 2.61 (11) | 3.29 (18) | 3.29 (18) | 1.27 (2.1) | 1.98 (7.8) | 1.25 (2.2) | 2.61 (9.5) | 1.42 (2.0) | 2.74 (7.5) | 3.33 (11) |
| knight_2h | 1.41 (2.4) | 2.95 (15) | 3.31 (19) | 2.95 (15) | 1.31 (2.2) | 2.34 (13) | 1.29 (2.4) | 3.16 (14) | 1.57 (2.5) | 3.52 (12) | 3.52 (12) |
| minotaur_dual | 1.30 (2.0) | 2.94 (15) | 6.75 (96) | 2.94 (15) | 1.29 (2.1) | 2.05 (8.6) | 1.11 (1.8) | 3.18 (15) | 1.34 (1.8) | 3.17 (10) | 3.17 (10) |
| vamp_knight | 1.35 (2.2) | 2.41 (9.2) | 2.58 (11) | 2.58 (11) | 1.27 (2.1) | 1.96 (7.5) | 1.13 (1.9) | 2.50 (9.2) | 1.35 (1.8) | 2.58 (6.7) | 2.58 (6.7) |
| dk_vampire | 1.46 (2.6) | 2.68 (11) | 5.96 (70) | 2.68 (11) | 1.35 (2.4) | 2.25 (11) | 1.31 (2.5) | 3.02 (13) | 1.61 (2.6) | 3.16 (10.0) | 3.16 (10.0) |
| dk_minotaur_dual | 1.60 (3.3) | 3.65 (24) | 6.24 (82) | 3.65 (24) | 1.51 (3.5) | 2.20 (11) | 1.60 (3.7) | 4.12 (25) | 1.72 (3.0) | 4.38 (19) | 4.38 (19) |
| archer | 1.48 (2.8) | 3.19 (18) | 3.19 (18) | 3.19 (18) | 1.41 (2.8) | 2.31 (12) | 1.37 (2.7) | 3.53 (18) | 1.68 (2.8) | 3.88 (15) | 3.88 (15) |
| archmage | 6.12 (78) | 16.2 (633) | 16.2 (633) | 16.2 (633) | 3.44 (41) | 6.68 (298) | 8.81 (113) | 16.4 (392) | 3.85 (15) | 7.03 (49) | 7.03 (49) |
| dragon | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok |
| seraph | 1.02 (1.1) | 1.49 (3.0) | 2.87 (17) | 2.87 (17) | 1.02 (1.1) | 1.31 (2.2) | 1.00 (1.7) | 1.01 (1.7) | 1.02 (1.0) | 1.36 (1.9) | 2.87 (8.3) |
| troll | ok | 2.44 (8.7) | 12.3 (296) | 10.7 (222) | ok | 1.60 (4.1) | ok | 2.53 (8.7) | ok | 1.74 (3.0) | 10.7 (115) |

#### doom L500: combinations, k (P)

| build | A ok4 | A ok | A mash 1 s | A mash 1 swing | B ok4 | B ok | C ok4 | C ok | mon ok4 | mon ok | mon mash 1 swing |
|---|---|---|---|---|---|---|---|---|---|---|---|
| knight_sns | 1.14 (1.4) | 2.25 (7.4) | 3.17 (16) | 3.17 (16) | 1.14 (1.5) | 1.76 (5.5) | 1.00 (1.4) | 2.29 (7.3) | 1.20 (1.4) | 2.36 (5.5) | 3.17 (10) |
| knight_2h | 1.21 (1.6) | 3.22 (18) | 4.12 (32) | 3.22 (18) | 1.17 (1.6) | 2.02 (8.3) | 1.10 (1.8) | 3.50 (18) | 1.25 (1.6) | 3.83 (15) | 3.83 (15) |
| minotaur_dual | ok | 2.57 (10) | 3.36 (19) | 2.57 (10) | ok | 1.73 (5.2) | ok | 2.70 (10) | ok | 2.63 (6.9) | 2.63 (6.9) |
| vamp_knight | 1.16 (1.5) | 2.04 (6.1) | 2.36 (8.6) | 2.36 (8.6) | 1.13 (1.4) | 1.64 (4.4) | 1.00 (1.4) | 2.05 (6.1) | 1.21 (1.5) | 2.16 (4.7) | 2.36 (5.5) |
| dk_vampire | 1.31 (2.0) | 2.78 (12) | — | 2.78 (12) | 1.31 (2.2) | 1.93 (7.2) | 1.21 (2.1) | 2.92 (12) | 1.42 (2.0) | 2.85 (8.1) | 2.85 (8.1) |
| dk_minotaur_dual | 1.30 (2.0) | 3.15 (17) | 3.83 (27) | 3.15 (17) | 1.25 (2.0) | 1.90 (6.9) | 1.11 (1.8) | 3.36 (16) | 1.35 (1.8) | 3.16 (10.0) | 3.16 (10.0) |
| archer | 1.37 (2.2) | 2.58 (10) | 2.58 (10) | 2.58 (10) | 1.29 (2.2) | 2.16 (10) | 1.16 (1.9) | 2.67 (9.8) | 1.43 (2.0) | 2.94 (8.7) | 2.94 (8.7) |
| archmage | 3.22 (17) | 13.7 (406) | 13.7 (406) | 13.7 (406) | 2.85 (23) | 4.82 (112) | 3.89 (21) | 13.7 (263) | 3.04 (9.3) | 5.40 (29) | 5.40 (29) |
| dragon | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok |
| seraph | ok | 1.06 (1.2) | 3.55 (28) | 3.55 (28) | ok | 1.06 (1.2) | ok | 1.00 (1.6) | ok | 1.07 (1.1) | 3.55 (13) |
| troll | ok | 1.32 (2.0) | 12.5 (300) | 8.37 (129) | ok | 1.15 (1.5) | ok | 1.03 (1.4) | ok | 1.16 (1.4) | 8.37 (70) |

#### madness L200: combinations, k (P)

| build | A ok4 | A ok | A mash 1 s | A mash 1 swing | B ok4 | B ok | C ok4 | C ok | mon ok4 | mon ok | mon mash 1 swing |
|---|---|---|---|---|---|---|---|---|---|---|---|
| knight_sns | ok | 4.53 (21) | 4.53 (21) | 4.53 (21) | ok | 2.45 (15) | ok | 4.53 (21) | ok | 3.93 (15) | 3.93 (15) |
| knight_2h | 1.02 (1.0) | 5.62 (32) | — | 5.62 (32) | 1.01 (1.0) | 2.70 (20) | 1.02 (1.0) | 5.62 (32) | 1.02 (1.0) | 4.52 (20) | 4.52 (20) |
| minotaur_dual | ok | 8.32 (69) | — | 8.32 (69) | ok | 2.61 (18) | ok | 8.32 (69) | ok | 4.90 (24) | 4.90 (24) |
| vamp_knight | ok | 3.06 (9.4) | 3.06 (9.4) | 3.06 (9.4) | ok | 2.02 (8.2) | ok | 3.06 (9.4) | ok | 2.99 (9.0) | 2.99 (9.0) |
| dk_vampire | ok | 2.79 (7.8) | — | 2.93 (8.6) | ok | 1.96 (7.6) | ok | 2.79 (7.8) | ok | 2.70 (7.3) | 2.93 (8.6) |
| dk_minotaur_dual | ok | 2.96 (8.8) | — | 2.96 (8.8) | ok | 1.90 (6.8) | ok | 2.96 (8.8) | ok | 2.56 (6.6) | 2.56 (6.6) |
| archer | ok | 6.24 (39) | 6.24 (39) | 6.24 (39) | ok | 2.52 (16) | ok | 6.24 (39) | ok | 5.07 (26) | 5.07 (26) |
| archmage | 1.19 (1.4) | 2.71 (7.4) | 2.71 (7.4) | 2.71 (7.4) | 1.16 (1.5) | 1.79 (5.7) | 1.19 (1.4) | 2.71 (7.4) | 1.16 (1.4) | 1.79 (3.2) | 1.79 (3.2) |
| dragon | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok | ok |
| seraph | ok | ok | 2.76 (7.6) | 2.76 (7.6) | ok | ok | ok | ok | ok | ok | 2.76 (7.6) |
| troll | ok | 5.35 (29) | — | 5.78 (33) | ok | 2.27 (12) | ok | 5.35 (29) | ok | 2.70 (7.3) | 4.24 (18) |

Per build at Beyond Madness L500 (combination A, median of five seeds):

| build | pulls of four: k (P) | whole groups: k (P) | whole groups at mash pace (1 swing): k |
|---|---|---|---|
| knight_sns | 2.86 (15) | 7.52 (144) | 8.40 |
| knight_2h | 2.64 (13) | 6.46 (106) | 8.18 (swing 0.95 s) |
| minotaur_dual | 2.37 (9) | 6.10 (89) | 6.33 (swing 1.03 s) |
| vamp_knight | 2.46 (11) | 5.26 (68) | 6.02 |
| dk_vampire | 3.37 (22) | 7.34 (135) | 7.59 (swing 1.0 s) |
| dk_minotaur_dual | 2.72 (14) | 6.75 (119) | 6.75 (swing 1.08 s) |
| archer | 3.02 (17) | 8.29 (169) | 8.29 |
| **median** | **2.72 (14)** | **6.75 (119)** | **7.6** |
| archmage | 13.9 (559) | 21.2 (1357) | 21.2 |
| dragon | 1.17 (1.5) | 1.92 (5.3) | 1.92 |
| seraph | 1.93 (6.1) | 4.67 (61) | 8.04 |
| troll | 2.11 (6.7) | 7.44 (121) | 22.2 (slow kills) |

The required power is the same whichever way it is split: A at k = 7.52 (P 144), B at k = 5.22 (P 142) and HP
alone ×137 all put knight_sns at ok = 90 %. Pace is a separate damage requirement, but at Beyond Madness the
survival requirement already supplies enough damage: only the troll (mash k = 22 against survival k = 7.4) needs
much more damage for pace than for survival.

At Insanity and Doom L500 the same builds need A at k = 1.1–1.6 for ok4 (most already pass Doom) and k = 2.0–3.7
(P 6–24) for whole groups. At Beyond Madness L200 pulls of four already pass; whole groups (undead crowds of up to
38, all physical) need k = 2.8–8.3 (P 8–69, where P = k² as nothing there is magic).

### 3. Where the gap is

| difficulty | build | phys share | HP | incoming %HP/s (median group) | time to die, s | time to kill, s per monster | TTK/TTD median group | TTK/TTD groups of 5+ |
|---|---|---|---|---|---|---|---|---|
| madness L500 | knight_sns | 30 % | 33912 | 42 | 2.4 | 6.9 | 13.8 | 20.8 |
| madness L500 | knight_2h | 28 % | 44245 | 50 | 2.0 | 6.2 | 11.3 | 20.5 |
| madness L500 | minotaur_dual | 31 % | 75464 | 39 | 2.5 | 5.7 | 11.6 | 17.9 |
| madness L500 | vamp_knight | 27 % | 49626 | 41 | 2.5 | 4.7 | 9.1 | 15.1 |
| madness L500 | dk_vampire | 30 % | 15003 | 90 | 1.1 | 7.6 | 28.4 | 44.4 |
| madness L500 | dk_minotaur_dual | 28 % | 13506 | 117 | 0.9 | 4.6 | 21.6 | 34.6 |
| madness L500 | archer | 32 % | 26390 | 71 | 1.4 | 3.9 | 13.2 | 20.2 |
| madness L500 | archmage | 30 % | 8837 | 525 | 0.2 | 36.7 | 948.3 | 1422.3 |
| madness L500 | dragon | 35 % | 75064 | 38 | 2.7 | 1.6 | 2.1 | 2.8 |
| madness L500 | seraph | 18 % | 10657 | 111 | 0.9 | 6.6 | 27.2 | 47.7 |
| madness L500 | troll | 37 % | 64900 | 26 | 3.9 | 19.0 | 24.1 | 38.0 |
| insanity L500 | knight_sns | 42 % | 29443 | 17 | 5.9 | 3.0 | 1.6 | 3.6 |
| insanity L500 | knight_2h | 38 % | 35483 | 19 | 5.3 | 2.4 | 1.4 | 3.2 |
| insanity L500 | minotaur_dual | 38 % | 53654 | 18 | 5.4 | 2.4 | 1.5 | 3.1 |
| insanity L500 | vamp_knight | 37 % | 35728 | 20 | 5.0 | 2.4 | 1.6 | 3.4 |
| insanity L500 | dk_vampire | 40 % | 12059 | 39 | 2.5 | 2.5 | 3.7 | 7.6 |
| insanity L500 | dk_minotaur_dual | 38 % | 12167 | 50 | 2.0 | 2.1 | 3.3 | 8.3 |
| insanity L500 | archer | 38 % | 19163 | 31 | 3.2 | 2.1 | 2.1 | 4.7 |
| insanity L500 | archmage | 38 % | 9719 | 172 | 0.6 | 17.4 | 85.5 | 213.9 |
| insanity L500 | dragon | 51 % | 62055 | 18 | 5.5 | 0.5 | 0.3 | 0.6 |
| insanity L500 | seraph | 21 % | 8469 | 22 | 4.5 | 2.6 | 2.1 | 5.1 |
| insanity L500 | troll | 47 % | 50781 | 11 | 9.1 | 9.5 | 2.9 | 6.5 |
| nightmare L500 | knight_sns | 70 % | 34955 | 4 | 23.0 | 2.7 | 0.2 | 2.8 |
| nightmare L500 | knight_2h | 58 % | 39667 | 5 | 18.7 | 1.7 | 0.2 | 2.7 |
| nightmare L500 | minotaur_dual | 65 % | 62542 | 4 | 22.4 | 2.0 | 0.2 | 1.9 |
| nightmare L500 | vamp_knight | 56 % | 41157 | 5 | 19.7 | 1.7 | 0.2 | 2.5 |
| nightmare L500 | dk_vampire | 67 % | 14007 | 10 | 9.8 | 1.9 | 0.5 | 5.0 |
| nightmare L500 | dk_minotaur_dual | 62 % | 12153 | 13 | 7.6 | 1.7 | 0.5 | 5.8 |
| nightmare L500 | archer | 69 % | 19846 | 9 | 10.6 | 1.5 | 0.2 | 2.9 |
| nightmare L500 | archmage | 64 % | 9419 | 51 | 1.9 | 5.3 | 4.3 | 103.5 |
| nightmare L500 | dragon | 77 % | 65913 | 5 | 18.3 | 0.3 | 0.0 | 0.2 |
| nightmare L500 | seraph | 55 % | 9024 | 4 | 22.8 | 2.4 | 0.2 | 3.4 |
| nightmare L500 | troll | 67 % | 62095 | 3 | 38.7 | 9.0 | 0.5 | 5.4 |
| madness L200 | knight_sns | 100 % | 3366 | 12 | 8.3 | 2.7 | 2.2 | 4.0 |
| madness L200 | knight_2h | 100 % | 3682 | 14 | 7.4 | 3.4 | 3.0 | 5.1 |
| madness L200 | minotaur_dual | 100 % | 3547 | 21 | 4.8 | 2.3 | 3.2 | 6.1 |
| madness L200 | vamp_knight | 100 % | 3676 | 15 | 6.5 | 2.3 | 2.4 | 4.1 |
| madness L200 | dk_vampire | 100 % | 1963 | 20 | 5.1 | 3.3 | 4.4 | 7.8 |
| madness L200 | dk_minotaur_dual | 100 % | 1968 | 28 | 3.6 | 2.3 | 3.5 | 5.8 |
| madness L200 | archer | 100 % | 2499 | 22 | 4.6 | 1.5 | 2.2 | 3.9 |
| madness L200 | archmage | 100 % | 1494 | 39 | 2.5 | 5.9 | 5.0 | 17.3 |
| madness L200 | dragon | 100 % | 3598 | 16 | 6.3 | 0.3 | 0.2 | 0.3 |
| madness L200 | seraph | 100 % | 1572 | 8 | 12.8 | 2.5 | 1.3 | 2.3 |
| madness L200 | troll | 100 % | 4043 | 16 | 6.3 | 4.9 | 5.2 | 9.2 |

Time to die = max HP / the median group's expected incoming damage per second with every member alive; time to
kill = seconds per monster when the solo cannot die. Their ratio is the power the group asks for, before the
sequential-kill bonus (dead monsters stop hitting).

- **Kill time and death time both moved ×2.5.** Against Road to Insanity at the same stage, a Beyond Madness group
  kills the knights in ~2–2.5 s instead of ~5–6 s, and each monster takes ~5–7 s instead of ~2.5 s. The ratio goes
  from ~1.5 to ~9–14 (median group) and ~15–21 (groups of five or more) for the plate builds, 22–28 / 35–44 for
  the death knights with their ~12–15 k HP.
- **The monsters, not the character, made the jump.** The median monster of the maps around stage 500 is level
  321 on Beyond Madness and 226–240 on every other difficulty. Its HP is 86 k (Insanity 25 k, ×3.4), its physical
  attack 46 k (×3.0) and its magic attack 91 k (×3.4). Beyond Madness L200 monsters (level 93) are in line with the
  other difficulties, so the jump is in the level boost at high stages.
- **Magic is 68–73 % of the incoming damage** for the melee and bow builds at Beyond Madness L500 (Insanity
  58–63 %, Nightmare 30–44 %). The
  magic base is 2.0 × the physical base there (1.7 × at L500 on the other difficulties), and the casters among the
  level-300+ monsters (Warlocks, Maddening Eyes, Liches, Sea Monsters) attack with magic types.
- **Mitigation is already near its ceiling.** At attacker level ~321 the melee builds take 10–24 % of a hit for
  every type (knight_sns 10 % on all of them, the death knights 10–15 %); the hit chance on the solo is 0.7–0.8.
  MAW floors every hit at 10 % of its input, so "magic taken ×1/2.75" cannot be reached through gear and
  resistances for the plate builds: it means a lower floor or a new damage cut.
- **What one change buys the most:** a Beyond-Madness-only cut of the monsters' HP and damage at high stages.
  ÷3.75 (about the Insanity numbers) brings pull-four play to ≥ 90 % for every melee and bow build without
  touching Nightmare–Insanity. A player-side change of the same size (HP, damage or mitigation ×2.75 each) would
  make the other difficulties trivial (Results 4). Whole groups at once on Beyond Madness (÷11 on the monster side)
  is a much bigger ask; even Doom and Insanity do not offer it today (ok 39–63 %).

### 4. Sanity: the same multipliers on the other difficulties

Combination A at k = 2.75 (the pull-four target), 4, 7 (the whole-group target) and 8.5. Cells: ok4 % / ok % /
seconds per monster over the beaten whole groups.


#### nightmare L500

| build | today | ×2.75 | ×4 | ×7 | ×8.5 |
|---|---|---|---|---|---|
| knight_sns | 96/91/2.2 | 100/100/1.0 | 100/100/0.7 | 100/100/0.5 | 100/100/0.4 |
| knight_2h | 98/90/1.7 | 100/100/1.0 | 100/100/0.9 | 100/100/0.9 | 100/100/0.9 |
| minotaur_dual | 100/95/1.9 | 100/100/1.0 | 100/100/0.9 | 100/100/0.7 | 100/100/0.7 |
| vamp_knight | 100/95/1.7 | 100/100/0.7 | 100/100/0.6 | 100/100/0.5 | 100/100/0.5 |
| dk_vampire | 98/93/1.8 | 100/100/1.1 | 100/100/1.1 | 100/100/0.9 | 100/100/0.9 |
| dk_minotaur_dual | 96/91/1.6 | 100/100/1.0 | 100/100/0.9 | 100/100/0.8 | 100/100/0.8 |
| archer | 94/88/1.2 | 100/100/0.6 | 100/100/0.5 | 100/100/0.4 | 100/100/0.4 |
| archmage | 77/75/3.2 | 100/95/1.4 | 100/100/0.9 | 100/100/0.6 | 100/100/0.5 |
| dragon | 100/100/0.3 | 100/100/0.2 | 100/100/0.2 | 100/100/0.2 | 100/100/0.2 |
| seraph | 100/96/2.4 | 100/100/0.9 | 100/100/0.7 | 100/100/0.5 | 100/100/0.5 |
| troll | 100/96/9.0 | 100/100/3.3 | 100/100/2.4 | 100/100/1.3 | 100/100/1.3 |

#### doom L500

| build | today | ×2.75 | ×4 | ×7 | ×8.5 |
|---|---|---|---|---|---|
| knight_sns | 84/58/2.3 | 100/96/1.1 | 100/100/0.9 | 100/100/0.5 | 100/100/0.5 |
| knight_2h | 70/52/1.6 | 100/89/0.9 | 100/96/0.9 | 100/100/0.9 | 100/100/0.9 |
| minotaur_dual | 92/63/1.8 | 100/92/1.0 | 100/96/0.9 | 100/100/0.9 | 100/100/0.9 |
| vamp_knight | 80/56/1.4 | 100/96/0.8 | 100/100/0.6 | 100/100/0.5 | 100/100/0.5 |
| dk_vampire | 55/47/1.9 | 100/89/1.2 | 100/96/1.2 | 100/100/1.1 | 100/100/1.1 |
| dk_minotaur_dual | 56/47/1.3 | 100/86/1.0 | 100/96/0.9 | 100/100/0.9 | 100/100/0.9 |
| archer | 56/47/1.3 | 100/92/0.6 | 100/100/0.5 | 100/100/0.5 | 100/100/0.5 |
| archmage | 22/18/2.8 | 66/55/1.5 | 92/68/1.3 | 100/76/1.0 | 100/77/0.9 |
| dragon | 100/98/0.5 | 100/100/0.3 | 100/100/0.3 | 100/100/0.3 | 100/100/0.3 |
| seraph | 97/84/2.8 | 100/100/1.1 | 100/100/0.8 | 100/100/0.6 | 100/100/0.6 |
| troll | 100/84/8.7 | 100/96/3.3 | 100/100/2.4 | 100/100/1.4 | 100/100/1.2 |

#### insanity L500

| build | today | ×2.75 | ×4 | ×7 | ×8.5 |
|---|---|---|---|---|---|
| knight_sns | 54/48/2.2 | 100/92/1.2 | 100/100/0.8 | 100/100/0.5 | 100/100/0.5 |
| knight_2h | 59/49/1.7 | 100/88/1.1 | 100/92/1.0 | 100/100/0.9 | 100/100/0.9 |
| minotaur_dual | 69/53/1.8 | 100/90/1.1 | 100/92/1.0 | 100/100/1.0 | 100/100/1.0 |
| vamp_knight | 61/50/1.7 | 100/92/0.9 | 100/100/0.7 | 100/100/0.5 | 100/100/0.5 |
| dk_vampire | 49/43/1.9 | 100/91/1.1 | 100/96/1.0 | 100/100/1.0 | 100/100/1.0 |
| dk_minotaur_dual | 44/39/1.4 | 100/83/1.1 | 100/92/1.0 | 100/100/1.0 | 100/100/1.0 |
| archer | 50/42/1.5 | 100/88/0.8 | 100/100/0.6 | 100/100/0.5 | 100/100/0.5 |
| archmage | 13/9/3.6 | 51/43/1.5 | 79/68/1.3 | 95/74/0.9 | 95/76/0.8 |
| dragon | 100/99/0.5 | 100/100/0.3 | 100/100/0.3 | 100/100/0.3 | 100/100/0.3 |
| seraph | 89/68/2.3 | 100/100/1.0 | 100/100/0.8 | 100/100/0.5 | 100/100/0.5 |
| troll | 100/77/9.0 | 100/92/3.6 | 100/100/2.6 | 100/100/1.5 | 100/100/1.4 |

#### madness L500

| build | today | ×2.75 | ×4 | ×7 | ×8.5 |
|---|---|---|---|---|---|
| knight_sns | 1/0/4.3 | 87/53/2.2 | 98/72/1.7 | 100/88/1.1 | 100/94/1.0 |
| knight_2h | 3/1/3.3 | 92/62/2.2 | 100/78/1.5 | 100/92/1.1 | 100/96/1.1 |
| minotaur_dual | 10/4/3.6 | 97/68/2.2 | 100/80/1.5 | 100/95/1.2 | 100/98/1.1 |
| vamp_knight | 6/3/3.2 | 95/69/1.7 | 100/82/1.3 | 100/96/0.8 | 100/100/0.7 |
| dk_vampire | 1/0/3.8 | 85/53/2.7 | 100/72/2.1 | 100/90/1.4 | 100/95/1.3 |
| dk_minotaur_dual | 3/1/2.4 | 90/52/1.6 | 100/74/1.2 | 100/91/1.0 | 100/98/1.0 |
| archer | 1/0/2.2 | 84/48/1.3 | 98/71/1.1 | 100/86/0.7 | 100/91/0.6 |
| archmage | 0/0/2.5 | 3/2/2.7 | 24/13/2.2 | 58/35/1.9 | 66/43/1.4 |
| dragon | 84/60/1.6 | 100/100/0.5 | 100/100/0.4 | 100/100/0.3 | 100/100/0.3 |
| seraph | 47/29/4.8 | 100/80/2.3 | 100/87/1.7 | 100/96/1.1 | 100/98/1.0 |
| troll | 57/26/17.2 | 99/71/6.4 | 100/79/4.7 | 100/89/2.9 | 100/94/2.6 |

#### nightmare L200

| build | today | ×2.75 | ×4 | ×7 | ×8.5 |
|---|---|---|---|---|---|
| knight_sns | 100/83/1.6 | 100/96/0.7 | 100/100/0.5 | 100/100/0.4 | 100/100/0.4 |
| knight_2h | 94/75/1.4 | 100/96/1.0 | 100/96/1.0 | 100/100/1.0 | 100/100/0.9 |
| minotaur_dual | 100/85/1.5 | 100/96/0.9 | 100/96/0.9 | 100/100/0.9 | 100/100/0.9 |
| vamp_knight | 100/85/1.3 | 100/96/0.6 | 100/100/0.5 | 100/100/0.5 | 100/100/0.5 |
| dk_vampire | 91/75/1.7 | 100/96/1.1 | 100/100/1.1 | 100/100/1.1 | 100/100/1.1 |
| dk_minotaur_dual | 92/78/1.4 | 100/96/0.9 | 100/96/0.9 | 100/100/0.9 | 100/100/0.9 |
| archer | 91/71/1.3 | 100/96/0.7 | 100/96/0.6 | 100/100/0.6 | 100/100/0.6 |
| archmage | 80/69/2.1 | 100/96/0.8 | 100/100/0.6 | 100/100/0.5 | 100/100/0.5 |
| dragon | 100/96/0.4 | 100/100/0.2 | 100/100/0.2 | 100/100/0.2 | 100/100/0.2 |
| seraph | 100/94/1.7 | 100/100/0.7 | 100/100/0.6 | 100/100/0.6 | 100/100/0.5 |
| troll | 100/94/3.5 | 100/96/1.4 | 100/100/1.2 | 100/100/0.9 | 100/100/0.9 |

#### madness L200

| build | today | ×2.75 | ×4 | ×7 | ×8.5 |
|---|---|---|---|---|---|
| knight_sns | 98/29/2.4 | 100/76/1.1 | 100/90/0.8 | 100/94/0.6 | 100/100/0.6 |
| knight_2h | 86/21/2.9 | 100/73/1.4 | 100/87/1.1 | 100/94/1.1 | 100/94/1.1 |
| minotaur_dual | 98/25/2.0 | 100/73/1.2 | 100/81/1.2 | 100/90/1.2 | 100/94/1.2 |
| vamp_knight | 99/35/2.1 | 100/87/1.0 | 100/94/0.7 | 100/100/0.7 | 100/100/0.7 |
| dk_vampire | 99/38/3.1 | 100/88/1.4 | 100/94/1.2 | 100/100/1.2 | 100/100/1.2 |
| dk_minotaur_dual | 99/34/2.1 | 100/90/1.2 | 100/94/1.2 | 100/100/1.2 | 100/100/1.2 |
| archer | 96/29/1.3 | 100/78/0.7 | 100/87/0.6 | 100/94/0.6 | 100/94/0.6 |
| archmage | 75/34/1.8 | 100/93/0.7 | 100/100/0.5 | 100/100/0.3 | 100/100/0.3 |
| dragon | 100/100/0.3 | 100/100/0.2 | 100/100/0.2 | 100/100/0.2 | 100/100/0.2 |
| seraph | 100/94/2.5 | 100/100/1.0 | 100/100/0.8 | 100/100/0.7 | 100/100/0.6 |
| troll | 99/42/4.6 | 100/73/1.9 | 100/83/1.5 | 100/94/1.2 | 100/94/1.1 |

- Nightmare L500: today 88–96 % whole groups at 1.2–2.2 s per monster; at ×2.75 every melee and bow build is
  100 %/100 % at 0.6–1.1 s per monster: mash play, nothing left to manage.
- Doom and Insanity L500: at ×2.75 ok4 = 100 % and whole groups 83–96 % at ~1 s per monster; at ×4 whole groups are
  92–100 %. These difficulties are today the "pull carefully" tier (ok4 44–92 %); a global ×2.75 removes that.
- Nightmare L200 likewise goes to 96–100 % whole groups at ×2.75.
- So a player-side buff can only be the fix if it scales with something that only Beyond Madness has (monster
  level above the character's, or a Beyond Madness flag); otherwise the fix belongs on the Beyond Madness monster
  scaling.

## Recommended target

A maxed melee solo at Beyond Madness L500 needs about **×14 effective power** (EHP × DPS) to clear by pulling four,
of which **magic mitigation ×2.75, HP ×2.75 and damage ×2.75**; to clear whole groups at a mash pace it needs about
**×120**, of which **magic mitigation ×7, HP ×7 and damage ×7**. Because mitigation sits at MAW's 10 % floor and
because a player-side buff of this size trivialises Nightmare to Insanity, the practical form is on the monster
side: Beyond Madness L500 monsters with about **÷3.75 HP and damage** (pull-four play; roughly Insanity's numbers)
or about ÷11 (whole groups). Casters (archmage) need ×14 even for pulls and are a separate problem.

## Caveats

- Expected-value model (realfight.py): every monster attacks at its average rate with its average damage mix;
  no variance, so the 90 % thresholds are sharper than real play. No crowd control, stuns, paralysis, kiting,
  ranged approach, line of sight, doors or terrain; every group starts its attack at once and stays in melee.
- Groups are the actors within 512 units of each other; real pulls may be larger or smaller. "Pulled four" assumes
  full rest between pulls and that four can always be separated.
- No potions in any number here (ok4p ≈ ok4 at Beyond Madness L500 today, so this changes little).
- Kill order is "most damage per HP first"; the solo picks the best attack each swing; AoE hits 75 % of the group.
- The HP lever scales leech heals with max HP (realfight heals a share of max HP) but keeps regeneration and
  potions absolute; the mitigation levers ignore the 10 % floor (they go below it), which is exactly why they
  would need a rules change.
- Five seeds per case; the median hides seeds that are much worse (some seeds of knight_2h, minotaur_dual and
  dk_vampire never reach the 1 s mash pace because one swing takes ≥ 0.95 s).
- Stage 200 Beyond Madness uses unpromoted classes in the harness data (as in data_real.json).

## Reproducing

[power_gap_sweep.py](power_gap_sweep.py) holds the harness path in `H` (2026-11-14: a private copy of the harness
work directory in a session scratchpad; point it at any copy of the solo-sim work directory with the files named
under Method). `python3 power_gap_sweep.py gap`, `sweep` (6160 bisections, about two minutes on 24 cores),
`PROBE='[["A2.75","comboA",2.75],["A4","comboA",4],["A7","comboA",7],["A8.5","comboA",8.5]]' python3
power_gap_sweep.py probe` (add `["base","hp",1]` for today's column), then `python3 power_gap_sweep.py tables`
prints every table above.
