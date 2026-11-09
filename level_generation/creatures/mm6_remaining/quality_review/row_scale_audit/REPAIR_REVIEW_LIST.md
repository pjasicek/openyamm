# MM6 scale repair and review list

Snapshot: 2026-09-24. Scope: the row-scale investigation, not every possible art, anchor, or animation defect.

**Cleric is ready for a production-quality rebuild of its liked trial. The other entries are a prioritized diagnosis/trial queue; none is an instruction to blindly resize every listed sprite.**

The complete list has **131 candidate sheets across 47 families**, covering **315 distinct later-row frame names** and **654 frame names including comparison rows**. Reused native pixel aliases can have separate frame names; these counts are not counts of independent drawings.

All 60 current manifest and registration hashes match the saved audit. Bindings below were read from every palette in those manifests, including reused poses and mirrored views.

Sources: [diagnosis and correction method](../../../SPRITE_SCALE_DIAGNOSIS.md), [audit and visual evidence](SUMMARY.md), [machine measurements](audit.json).

## How to read the list

- Frame positions `#` are **1-based**, matching positions in the exported animation sequence. The filename is the authoritative art identifier. A sequence can repeat one sprite in several positions.
- Views: `v0` front; `v1/v7` front-quarter pair; `v2/v6` side pair; `v3/v5` rear-quarter pair; `v4` rear. `mirrored` records actual manifest reuse. Single-view actions can reuse the same artwork for v0–7.
- `Master only` means there is no animation binding in these manifests. Review it through the viewer Master selector; do not assume it needs an in-game animation repair.
- Each detailed table contains every frame on the candidate sheet. **Focus** marks the later row that crossed the screen; **Compare** includes the baseline and other context rows. The first row can also be wrong, so inspect both before assigning responsibility.
- Per-frame percentages describe a saved landmark span, or silhouette height when landmarks are unavailable, relative to that exact original pose after accounting for the 2× export tier. Negative means shorter; positive means taller. These percentages are not verified uniform scale errors or repair multipliers.
- The displayed row difference compares row medians of these native-normalized ratios. It is not a raw height comparison between different poses.
- A correction to one master must propagate to its masks and palette appearances; mirrored/reused bindings do not require separately redrawn frames.

## Start here

| Creature | Actual action/view and positions | Frame names | Next action |
| --- | --- | --- | --- |
| Cleric A | walk v0 #4–6/6 | `clewald0`, `clewale0`, `clewalf0` | Rebuild the existing three-frame trial from retained high-resolution art; recheck placement, masks and sampling before adoption. |
| BDwarf A | standing v3–4 #1/1<br>standing v5 mirrored #1/1 | `dwa1sta3`, `dwa1sta4` | Measure body width/independent anatomy, then try uniform scale and placement on the shorter views. |
| BDwarf A | fidget v0–7 #4–6/6 | `dwa1fid0`, `dwa1fie0`, `dwa1fif0` | Prioritize a reversible scale/placement trial for d/e/f after independent body measurements. |
| PeasantM4 A | walk v4 #3–4/6 | `natmwac4`, `natmwad4` | Prioritize body-feature fitting and a reversible trial for c/d; compare both rows against native absolute scale. |
| PeasantM3 A | hit v0–7 #4–6/6 | `mepwind0`, `mepwine0`, `mepwinf0` | Check body measurements through the recoil pose, then trial corrections for d/e/f. |
| BThief A | walk v2 #4–6/6<br>walk v6 mirrored #4–6/6 | `thfwald2`, `thfwale2`, `thfwalf2` | The later row is taller but silhouette width trends narrower. Check body proportions before choosing uniform reduction. |
| ElemFire A | fidget v3 #5–6/6<br>fidget v5 mirrored #5–6/6<br>walk v3 #5–6/6<br>walk v5 mirrored #5–6/6 | `fie1fle3`, `fie1flf3` | Shorter flame extent is visible; determine whether whole-effect scaling preserves the native structure and motion. |

Cleric trial factors: `clewald0` ×1.0256477123, `clewale0` ×1.0148258066, `clewalf0` ×1.0247703541, with the trial landmark-based translations replacing previous compensating nudges. Use the retained high-resolution source for adoption; preserve the previous package/checkpoint.

## All candidate families

| Family | Candidate sheets | Landmark / silhouette basis | Focus actions and views |
| --- | ---: | --- | --- |
| [BArcher A](#mm6-arc1) | 1 | 0 / 1 | corpse v0–7<br>death v0–7 |
| [Barbarian A](#mm6-bar1) | 2 | 0 / 2 | corpse v0–7<br>death v0–7<br>hit v0–7 |
| [BBat A](#mm6-bat) | 3 | 0 / 3 | fidget v2–3<br>fidget v5–6 mirrored<br>hit v0–7<br>standing v2–3<br>standing v5–6 mirrored<br>walk v2–3<br>walk v5–6 mirrored<br>Master only: `batstd3`, `batstd4` |
| [Bloodsucker A](#mm6-bld) | 5 | 0 / 5 | death v0–7<br>fidget v0–7<br>hit v4<br>standing v4<br>walk v4<br>Master only: `bldfib1`, `bldfib2`, `bldfic3`, `bldfic4`, `bldfid1`, `bldfid2` |
| [Cleric A](#mm6-cle) | 1 | 1 / 0 | walk v0 |
| [Cobra A](#mm6-cob) | 3 | 2 / 1 | attack v0–7<br>attack2 v0–7<br>death v0–7<br>fidget v0–7 |
| [DragonCave A](#mm6-drag) | 1 | 1 / 0 | walk v4 |
| [DragonLand A](#mm6-drr1) | 2 | 2 / 0 | hit v0–7<br>Master only: `drr1bid0`, `drr1bie0`, `drr1fib0` |
| [Druidess A](#mm6-dru1) | 1 | 0 / 1 | corpse v0–7<br>death v0–7 |
| [BDwarf A](#mm6-dwa1) | 6 | 5 / 1 | corpse v0–7<br>death v0–7<br>fidget v0–7<br>standing v3–4<br>standing v5 mirrored<br>walk v1–3<br>walk v5–7 mirrored |
| [ElemAir A](#mm6-aie1) | 1 | 0 / 1 | hit v0–7 |
| [ElemEarth A](#mm6-ert) | 4 | 4 / 0 | attack v0–7<br>attack2 v0–7<br>death v0–7<br>walk v0,4 |
| [ElemFire A](#mm6-fie1) | 6 | 5 / 1 | death v0–7<br>fidget v0–3<br>fidget v5–7 mirrored<br>hit v0–7<br>walk v0–3<br>walk v5–7 mirrored |
| [ElemWater A](#mm6-wel) | 5 | 5 / 0 | death v0–7<br>fidget v0–7<br>walk v0<br>Master only: `welfic2`, `welfid1`, `welfif1`, `welfif2` |
| [FighterChain A](#mm6-figc) | 3 | 3 / 0 | attack v0–7<br>attack2 v0–7<br>standing v3–4<br>standing v5 mirrored<br>walk v3<br>walk v5 mirrored |
| [FighterLeath A](#mm6-fgt) | 2 | 1 / 1 | death v0–7<br>walk v3<br>walk v5 mirrored |
| [BGenie A](#mm6-djn) | 6 | 6 / 0 | attack v0–7<br>attack2 v0–7<br>death v0–7<br>fidget v0–7<br>walk v0–2<br>walk v6–7 mirrored |
| [BGhost A](#mm6-gst) | 4 | 1 / 3 | attack v0–7<br>attack2 v0–7<br>fidget v2–3<br>fidget v5–6 mirrored<br>hit v0–7<br>standing v2–3<br>standing v5–6 mirrored<br>walk v2–3<br>walk v5–6 mirrored |
| [BGoblin A](#mm6-goblin) | 3 | 0 / 3 | corpse v0–7<br>death v0–7<br>hit v0–7<br>standing v3–4<br>standing v5 mirrored |
| [Guard A](#mm6-gua) | 1 | 1 / 0 | hit v0–7 |
| [BHarpy A](#mm6-hrp) | 1 | 1 / 0 | fidget v2<br>fidget v6 mirrored<br>standing v2<br>standing v6 mirrored<br>walk v2<br>walk v6 mirrored |
| [BHydra A](#mm6-hyd) | 5 | 5 / 0 | death v0–7<br>hit v0–7<br>walk v0,2–3<br>walk v5–6 mirrored<br>Master only: `hydstaa2`, `hydstaa3` |
| [Jackalman A](#mm6-jak1) | 3 | 1 / 2 | death v0–7<br>hit v0–7<br>standing v3–4<br>standing v5 mirrored |
| [KnightPlate A](#mm6-kni) | 2 | 1 / 1 | death v0–7<br>walk v2<br>walk v6 mirrored |
| [BLich A](#mm6-lch) | 2 | 0 / 2 | death v0–7<br>hit v0–7 |
| [LizardArch A](#mm6-lzd) | 5 | 5 / 0 | attack v0–7<br>attack2 v0–7<br>death v0–7<br>fidget v0–7<br>walk v1,4<br>walk v7 mirrored |
| [BMedusa A](#mm6-med) | 2 | 2 / 0 | death v0–7<br>walk v1<br>walk v7 mirrored |
| [BMinotaur A](#mm6-min1) | 3 | 3 / 0 | standing v2–3<br>standing v5–6 mirrored<br>walk v1–3<br>walk v5–7 mirrored |
| [Nobleman A](#mm6-nobl) | 1 | 1 / 0 | walk v2<br>walk v6 mirrored |
| [BOoze A](#mm6-ooz) | 3 | 1 / 2 | attack v0–7<br>attack2 v0–7<br>death v0–7<br>walk v3<br>walk v5 mirrored |
| [Ogre A](#mm6-ogr) | 3 | 0 / 3 | fidget v0–7<br>hit v0–7<br>walk v2<br>walk v6 mirrored |
| [PeasantF1 A](#mm6-pfem) | 1 | 0 / 1 | corpse v0–7<br>death v0–7 |
| [PeasantF2 A](#mm6-fmp) | 5 | 5 / 0 | corpse v0–7<br>death v0–7<br>hit v0–7<br>standing v3–4<br>standing v5 mirrored<br>walk v0,3<br>walk v5 mirrored |
| [PeasantF4 A](#mm6-natf) | 1 | 1 / 0 | walk v1<br>walk v7 mirrored |
| [PeasantM1 A](#mm6-pman) | 1 | 1 / 0 | walk v1<br>walk v7 mirrored |
| [PeasantM2 A](#mm6-pmn2) | 3 | 3 / 0 | attack v0–7<br>attack2 v0–7<br>hit v0–7<br>walk v1<br>walk v7 mirrored |
| [PeasantM3 A](#mm6-mep) | 6 | 5 / 1 | attack v0–7<br>attack2 v0–7<br>death v0–7<br>hit v0–7<br>walk v0,2–3<br>walk v5–6 mirrored |
| [PeasantM4 A](#mm6-natm) | 1 | 1 / 0 | walk v4 |
| [BRobot A](#mm6-rob1) | 4 | 0 / 4 | death v0–7<br>fidget v0–7<br>hit v0–7<br>standing v3–4<br>standing v5 mirrored<br>walk v3–4<br>walk v5 mirrored |
| [SeaSerpent A](#mm6-seas) | 4 | 4 / 0 | walk v0–1,3–4<br>walk v5,7 mirrored |
| [Sorcerer A](#mm6-sor1) | 2 | 2 / 0 | walk v0,4 |
| [BThief A](#mm6-thf) | 3 | 3 / 0 | hit v0–7<br>walk v0,2<br>walk v6 mirrored |
| [Werewolf A](#mm6-wfigt1) | 1 | 0 / 1 | corpse v0–7<br>death v0–7 |
| [Cactus A](#mm6-mcac) | 3 | 2 / 1 | attack v0–7<br>attack2 v0–7<br>death v0–7<br>hit v0–7<br>Master only: `mcacau0` |
| [BMonk A](#mm6-mnk1) | 1 | 0 / 1 | corpse v0–7<br>death v0–7 |
| [BRat A](#mm6-rat) | 2 | 0 / 2 | standing v3–4<br>standing v5 mirrored<br>walk v4 |
| [BSpider A](#mm6-spi1) | 3 | 0 / 3 | walk v1–3<br>walk v5–7 mirrored |

## Exact sheet and frame list

<a id="mm6-arc1"></a>

### BArcher A — `mm6:arc1`

Viewer family: `#mm6_arc1`. Package: `level_generation/creatures/mm6_arc1/redo_2x`.

#### 001. death_corpse_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +2.57%**, using silhouette height only. Source: `level_generation/creatures/mm6_arc1/redo_2x/raw/death_corpse_redo_01_v2.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `arc1diq` -0.39%<br>`arc1dir` +1.00%<br>`arc1dis` +0.59% | death v0–7 #1–3/5 |
| 2 | Focus | `arc1dit` -1.18%<br>`arc1diu` +7.20%<br>`arc1div` +3.17% | corpse v0–7 #1/1<br>death v0–7 #4–5/5 |

<a id="mm6-bar1"></a>

### Barbarian A — `mm6:bar1`

Viewer family: `#mm6_bar1`. Package: `level_generation/creatures/mm6_bar1/redo_2x`.

#### 002. death_corpse_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +2.46%**, using silhouette height only. Source: `level_generation/creatures/mm6_bar1/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `bar1dea0` +0.00%<br>`bar1deb0` +0.47%<br>`bar1dec0` -1.58% | death v0–7 #1–3/5 |
| 2 | Focus | `bar1ded0` +0.32%<br>`bar1dee0` +3.12%<br>`bar1def0` +2.46% | corpse v0–7 #1/1<br>death v0–7 #4–5/5 |

#### 003. hit_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -3.20%**, using silhouette height only. Source: `level_generation/creatures/mm6_bar1/redo_2x/raw/hit_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `bar1wib0` +0.21%<br>`bar1wic0` +0.65%<br>`bar1wid0` +0.44% | hit v0–7 #2–4/6 |
| 2 | Focus | `bar1wie0` -2.16%<br>`bar1wif0` -3.39% | hit v0–7 #5–6/6 |

<a id="mm6-bat"></a>

### BBat A — `mm6:bat`

Viewer family: `#mm6_bat`. Package: `level_generation/creatures/mm6_bat/redo_2x`.

#### 004. standing_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -4.79%**, using silhouette height only. Source: `level_generation/creatures/mm6_bat/redo_2x/raw/standing_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `batwaa0` +1.27%<br>`batwaa1` -1.13% | fidget v0–1 #1/6<br>fidget v7 mirrored #1/6<br>standing v0–1 #1/6<br>standing v7 mirrored #1/6<br>walk v0–1 #1/6<br>walk v7 mirrored #1/6 |
| 2 | Focus | `batwaa2` -5.41%<br>`batwaa3` -4.05% | fidget v2–3 #1/6<br>fidget v5–6 mirrored #1/6<br>standing v2–3 #1/6<br>standing v5–6 mirrored #1/6<br>walk v2–3 #1/6<br>walk v5–6 mirrored #1/6 |

#### 005. hit_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -2.16%**, using silhouette height only. Source: `level_generation/creatures/mm6_bat/redo_2x/raw/hit_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `batwia0` -2.23%<br>`batwib0` -5.06% | hit v0–7 #1–2/6 |
| 2 | Focus | `batwic0` -5.78%<br>`batwid0` -5.66% | hit v0–7 #3–4/6 |

#### 006. unused_native_2_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -5.89%**, using silhouette height only. Source: `level_generation/creatures/mm6_bat/redo_2x/raw/unused_native_2_redo_01_v2.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `batstd1` -8.21%<br>`batstd2` -6.75% | Master only: `batstd1`, `batstd2` |
| 2 | Focus | `batstd3` -6.57%<br>`batstd4` -19.29% | Master only: `batstd3`, `batstd4` |

<a id="mm6-bld"></a>

### Bloodsucker A — `mm6:bld`

Viewer family: `#mm6_bld`. Package: `level_generation/creatures/mm6_bld/redo_2x`.

#### 007. walk_4_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +2.92%**, using silhouette height only. Source: `level_generation/creatures/mm6_bld/redo_2x/raw/walk_4_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `bldflyb4` -8.70%<br>`bldflyc4` -4.88% | hit v4 #2–3/6<br>standing v4 #2–3/6<br>walk v4 #2–3/6 |
| 2 | Focus | `bldflyd4` -3.36%<br>`bldflye4` -4.76% | hit v4 #4–5/6<br>standing v4 #4–5/6<br>walk v4 #4–5/6 |

#### 008. fidget_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +2.66%**, using silhouette height only. Source: `level_generation/creatures/mm6_bld/redo_2x/raw/fidget_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `bldfia0` +18.70%<br>`bldfib0` +27.73% | fidget v0–7 #1–2/6 |
| 2 | Focus | `bldfic0` +27.98%<br>`bldfid0` +25.00% | fidget v0–7 #3–4/6 |

#### 009. death_corpse_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +2.25%**, using silhouette height only. Source: `level_generation/creatures/mm6_bld/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `blddyia0` +2.67%<br>`blddyib0` +4.71% | death v0–7 #1–2/5 |
| 2 | Focus | `blddyic0` +4.87%<br>`blddyid0` +7.18% | death v0–7 #3–4/5 |

#### 010. unused_native_0_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 3: +6.58%**, using silhouette height only. Source: `level_generation/creatures/mm6_bld/redo_2x/raw/unused_native_0_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `bldfia1` +1.53%<br>`bldfia2` +3.08% | Master only: `bldfia1`, `bldfia2` |
| 2 | Compare | `bldfia3` +5.00%<br>`bldfia4` -4.23% | Master only: `bldfia3`, `bldfia4` |
| 3 | Focus | `bldfib1` +8.82%<br>`bldfib2` +9.24% | Master only: `bldfib1`, `bldfib2` |

#### 011. unused_native_1_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -2.46%; row 1 → 3: -5.02%**, using silhouette height only. Source: `level_generation/creatures/mm6_bld/redo_2x/raw/unused_native_1_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `bldfic1` +0.00%<br>`bldfic2` -3.12% | Master only: `bldfic1`, `bldfic2` |
| 2 | Focus | `bldfic3` -2.21%<br>`bldfic4` -5.75% | Master only: `bldfic3`, `bldfic4` |
| 3 | Focus | `bldfid1` -5.51%<br>`bldfid2` -7.50% | Master only: `bldfid1`, `bldfid2` |
| 4 | Compare | `bldfid3` -2.87%<br>`bldfid4` -3.25% | Master only: `bldfid3`, `bldfid4` |

<a id="mm6-cle"></a>

### Cleric A — `mm6:cle`

Viewer family: `#mm6_cle`. Package: `level_generation/creatures/mm6_cle/redo_2x`.

#### 012. walk_0_redo_01

**Trial liked by user.** Rebuild the existing three-frame trial from retained high-resolution art; recheck placement, masks and sampling before adoption.

Screen: **row 1 → 2: -3.08%**, using head / sole_height. Source: `level_generation/creatures/mm6_cle/redo_2x/raw/walk_0_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `clewala0` +0.06%<br>`clewalb0` +0.69%<br>`clewalc0` +0.76% | walk v0 #1–3/6 |
| 2 | Focus | `clewald0` -2.50%<br>`clewale0` -1.46%<br>`clewalf0` -2.42% | walk v0 #4–6/6 |

<a id="mm6-cob"></a>

### Cobra A — `mm6:cob`

Viewer family: `#mm6_cob`. Package: `level_generation/creatures/mm6_cob/redo_2x`.

#### 013. attack_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -11.11%**, using head_top_candidate / lower_jaw. Source: `level_generation/creatures/mm6_cob/redo_2x/raw/attack_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `cobatta0` +12.22%<br>`cobattb0` -14.80% | attack v0–7 #1–2/6<br>attack2 v0–7 #1–2/6 |
| 2 | Focus | `cobattc0` -15.92%<br>`cobattd0` -8.60% | attack v0–7 #3–4/6<br>attack2 v0–7 #3–4/6 |

#### 014. fidget_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.11%**, using head_top_candidate / lower_jaw. Source: `level_generation/creatures/mm6_cob/redo_2x/raw/fidget_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `cobfida0` -11.86%<br>`cobfidb0` -13.34%<br>`cobfidc0` -15.54% | fidget v0–7 #1–3/6 |
| 2 | Focus | `cobfidd0` -19.66%<br>`cobfide0` -15.17%<br>`cobfidf0` -11.67% | fidget v0–7 #4–6/6 |

#### 015. death_corpse_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -4.11%**, using silhouette height only. Source: `level_generation/creatures/mm6_cob/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `cobdeta0` +0.00%<br>`cobdetb0` -0.65% | death v0–7 #1–2/6 |
| 2 | Focus | `cobdetc0` -4.56%<br>`cobdetd0` -4.28% | death v0–7 #3–4/6 |

<a id="mm6-drag"></a>

### DragonCave A — `mm6:drag`

Viewer family: `#mm6_drag`. Package: `level_generation/creatures/mm6_drag/redo_2x`.

#### 016. walk_4_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.26%**, using head_back / planted_sole. Source: `level_generation/creatures/mm6_drag/redo_2x/raw/walk_4_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `dragwaa4` -0.19%<br>`dragwab4` +0.88% | walk v4 #1–2/6 |
| 2 | Focus | `dragwac4` -0.61%<br>`dragwad4` -3.23% | walk v4 #3–4/6 |

<a id="mm6-drr1"></a>

### DragonLand A — `mm6:drr1`

Viewer family: `#mm6_drr1`. Package: `level_generation/creatures/mm6_drr1/redo_2x`.

#### 017. hit_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -5.87%**, using foot_or_remnant_anchor / head_or_remnant_feature. Source: `level_generation/creatures/mm6_drr1/redo_2x/raw/hit_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `drr1wia0` +0.71%<br>`drr1wib0` +11.34%<br>`drr1wic0` +1.35% | hit v0–7 #1–3/5 |
| 2 | Focus | `drr1wid0` -2.39%<br>`drr1wie0` -6.81% | hit v0–7 #4–5/5 |

#### 018. unused_native_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -4.19%**, using foot_or_remnant_anchor / independent_body_feature. Source: `level_generation/creatures/mm6_drr1/redo_2x/raw/unused_native_redo_01_v2.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `drr1bia0` +8.28%<br>`drr1bib0` +2.85%<br>`drr1bic0` +1.75% | Master only: `drr1bia0`, `drr1bib0`, `drr1bic0` |
| 2 | Focus | `drr1bid0` -1.46%<br>`drr1bie0` -0.45%<br>`drr1fib0` -1.69% | Master only: `drr1bid0`, `drr1bie0`, `drr1fib0` |

<a id="mm6-dru1"></a>

### Druidess A — `mm6:dru1`

Viewer family: `#mm6_dru1`. Package: `level_generation/creatures/mm6_dru1/redo_2x`.

#### 019. death_corpse_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -3.04%**, using silhouette height only. Source: `level_generation/creatures/mm6_dru1/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `dru1dya0` +0.00%<br>`dru1dyb0` -0.20%<br>`dru1dyc0` +0.00% | death v0–7 #1–3/5 |
| 2 | Focus | `dru1dyd0` -3.04%<br>`dru1dye0` -3.72%<br>`dru1dyf0` -0.88% | corpse v0–7 #1/1<br>death v0–7 #4–5/5 |

<a id="mm6-dwa1"></a>

### BDwarf A — `mm6:dwa1`

Viewer family: `#mm6_dwa1`. Package: `level_generation/creatures/mm6_dwa1/redo_2x`.

#### 020. standing_redo_01

**Visually supported; fit pending.** Measure body width/independent anatomy, then try uniform scale and placement on the shorter views.

Screen: **row 1 → 2: -3.21%**, using helmet_spike / sole. Source: `level_generation/creatures/mm6_dwa1/redo_2x/raw/standing_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `dwa1sta0` +0.07%<br>`dwa1sta1` +0.23%<br>`dwa1sta2` +0.88% | standing v0–2 #1/1<br>standing v6–7 mirrored #1/1 |
| 2 | Focus | `dwa1sta3` -2.60%<br>`dwa1sta4` -3.36% | standing v3–4 #1/1<br>standing v5 mirrored #1/1 |

#### 021. walk_1_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.20%**, using helmet_spike / sole. Source: `level_generation/creatures/mm6_dwa1/redo_2x/raw/walk_1_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `dwa1wka1` +0.10%<br>`dwa1wkb1` -0.04%<br>`dwa1wkc1` -0.04% | walk v1 #1–3/6<br>walk v7 mirrored #1–3/6 |
| 2 | Focus | `dwa1wkd1` -3.12%<br>`dwa1wke1` -2.24%<br>`dwa1wkf1` -1.34% | walk v1 #4–6/6<br>walk v7 mirrored #4–6/6 |

#### 022. walk_2_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.76%**, using helmet_spike / sole. Source: `level_generation/creatures/mm6_dwa1/redo_2x/raw/walk_2_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `dwa1wka2` -0.28%<br>`dwa1wkb2` -1.06%<br>`dwa1wkc2` -0.73% | walk v2 #1–3/6<br>walk v6 mirrored #1–3/6 |
| 2 | Focus | `dwa1wkd2` -3.47%<br>`dwa1wke2` -3.73%<br>`dwa1wkf2` -2.26% | walk v2 #4–6/6<br>walk v6 mirrored #4–6/6 |

#### 023. walk_3_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.02%**, using helmet_spike / sole. Source: `level_generation/creatures/mm6_dwa1/redo_2x/raw/walk_3_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `dwa1wka3` +0.87%<br>`dwa1wkb3` +1.40%<br>`dwa1wkc3` +1.86% | walk v3 #1–3/6<br>walk v5 mirrored #1–3/6 |
| 2 | Focus | `dwa1wkd3` +0.01%<br>`dwa1wke3` -0.65%<br>`dwa1wkf3` -0.79% | walk v3 #4–6/6<br>walk v5 mirrored #4–6/6 |

#### 024. fidget_redo_01

**Visually supported; fit pending.** Prioritize a reversible scale/placement trial for d/e/f after independent body measurements.

Screen: **row 1 → 2: -4.08%**, using crown / sole. Source: `level_generation/creatures/mm6_dwa1/redo_2x/raw/fidget_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `dwa1fia0` +0.11%<br>`dwa1fib0` +0.28%<br>`dwa1fic0` +0.28% | fidget v0–7 #1–3/6<br>Master only: `dwa1fib0` |
| 2 | Focus | `dwa1fid0` -4.41%<br>`dwa1fie0` -3.65%<br>`dwa1fif0` -3.81% | fidget v0–7 #4–6/6 |

#### 025. death_corpse_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -2.46%**, using silhouette height only. Source: `level_generation/creatures/mm6_dwa1/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `dwa1dya0` -0.23%<br>`dwa1dyb0` +1.45%<br>`dwa1dyc0` +0.49% | death v0–7 #1–3/6 |
| 2 | Focus | `dwa1dyd0` -2.23%<br>`dwa1dye0` -1.99%<br>`dwa1dyf0` +0.68% | corpse v0–7 #1/1<br>death v0–7 #4–6/6 |

<a id="mm6-aie1"></a>

### ElemAir A — `mm6:aie1`

Viewer family: `#mm6_aie1`. Package: `level_generation/creatures/mm6_aie1/redo_2x`.

#### 026. hit_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -6.20%**, using silhouette height only. Source: `level_generation/creatures/mm6_aie1/redo_2x/raw/hit_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `aie1wia` -2.13%<br>`aie1wib` -7.24%<br>`aie1wic` -5.07% | hit v0–7 #1–3/6 |
| 2 | Focus | `aie1wid` -7.71%<br>`aie1wie` -10.95%<br>`aie1wif` -13.20% | hit v0–7 #4–6/6 |

<a id="mm6-ert"></a>

### ElemEarth A — `mm6:ert`

Viewer family: `#mm6_ert`. Package: `level_generation/creatures/mm6_ert/redo_2x`.

#### 027. walk_0_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.50%**, using crown / feet. Source: `level_generation/creatures/mm6_ert/redo_2x/raw/walk_0_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `ertwaa0` -0.09%<br>`ertwab0` -1.04%<br>`ertwac0` -1.04% | walk v0 #1–3/6 |
| 2 | Focus | `ertwad0` -1.61%<br>`ertwae0` -3.51%<br>`ertwaf0` -3.91% | walk v0 #4–6/6 |

#### 028. walk_4_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.63%**, using crown / feet. Source: `level_generation/creatures/mm6_ert/redo_2x/raw/walk_4_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `ertwaa4` -0.09%<br>`ertwab4` -1.03%<br>`ertwac4` -1.21% | walk v4 #1–3/6 |
| 2 | Focus | `ertwad4` -1.92%<br>`ertwae4` -3.63%<br>`ertwaf4` -4.03% | walk v4 #4–6/6 |

#### 029. attack_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.50%**, using crown / feet. Source: `level_generation/creatures/mm6_ert/redo_2x/raw/attack_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `ertata` +0.04%<br>`ertatb` -0.11% | attack v0–7 #1–2/6<br>attack2 v0–7 #1–2/6 |
| 2 | Focus | `ertatc` -1.04%<br>`ertatd` -4.03% | attack v0–7 #3–4/6<br>attack2 v0–7 #3–4/6 |

#### 030. death_corpse_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -3.48%**, using base / upper_extent. Source: `level_generation/creatures/mm6_ert/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `ertdya` -0.32%<br>`ertdyb` +1.79% | death v0–7 #1–2/5 |
| 2 | Focus | `ertdyc` -4.18%<br>`ertdyd` -1.37% | death v0–7 #3–4/5 |

<a id="mm6-fie1"></a>

### ElemFire A — `mm6:fie1`

Viewer family: `#mm6_fie1`. Package: `level_generation/creatures/mm6_fie1/redo_2x`.

#### 031. walk_0_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.38%**, using tail / tip. Source: `level_generation/creatures/mm6_fie1/redo_2x/raw/walk_0_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `fie1flb0` -0.05%<br>`fie1flc0` +1.02%<br>`fie1fld0` +0.07% | fidget v0 #2–4/6<br>walk v0 #2–4/6 |
| 2 | Focus | `fie1fle0` -2.26%<br>`fie1flf0` -2.37% | fidget v0 #5–6/6<br>walk v0 #5–6/6 |

#### 032. walk_1_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -5.96%**, using tail / tip. Source: `level_generation/creatures/mm6_fie1/redo_2x/raw/walk_1_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `fie1flb1` +0.21%<br>`fie1flc1` -0.24%<br>`fie1fld1` -0.45% | fidget v1 #2–4/6<br>fidget v7 mirrored #2–4/6<br>walk v1 #2–4/6<br>walk v7 mirrored #2–4/6 |
| 2 | Focus | `fie1fle1` -5.80%<br>`fie1flf1` -6.57% | fidget v1 #5–6/6<br>fidget v7 mirrored #5–6/6<br>walk v1 #5–6/6<br>walk v7 mirrored #5–6/6 |

#### 033. walk_2_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -5.36%**, using tail / tip. Source: `level_generation/creatures/mm6_fie1/redo_2x/raw/walk_2_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `fie1flb2` -0.32%<br>`fie1flc2` -0.63%<br>`fie1fld2` +0.03% | fidget v2 #2–4/6<br>fidget v6 mirrored #2–4/6<br>walk v2 #2–4/6<br>walk v6 mirrored #2–4/6 |
| 2 | Focus | `fie1fle2` -5.74%<br>`fie1flf2` -5.57% | fidget v2 #5–6/6<br>fidget v6 mirrored #5–6/6<br>walk v2 #5–6/6<br>walk v6 mirrored #5–6/6 |

#### 034. walk_3_redo_01

**Visual extent mismatch; effect geometry.** Shorter flame extent is visible; determine whether whole-effect scaling preserves the native structure and motion.

Screen: **row 1 → 2: -7.06%**, using tail / tip. Source: `level_generation/creatures/mm6_fie1/redo_2x/raw/walk_3_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `fie1flb3` +0.48%<br>`fie1flc3` +0.76%<br>`fie1fld3` +0.91% | fidget v3 #2–4/6<br>fidget v5 mirrored #2–4/6<br>walk v3 #2–4/6<br>walk v5 mirrored #2–4/6 |
| 2 | Focus | `fie1fle3` -6.13%<br>`fie1flf3` -6.58% | fidget v3 #5–6/6<br>fidget v5 mirrored #5–6/6<br>walk v3 #5–6/6<br>walk v5 mirrored #5–6/6 |

#### 035. hit_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -5.22%**, using tail / tip. Source: `level_generation/creatures/mm6_fie1/redo_2x/raw/hit_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `fie1wib0` -0.05%<br>`fie1wic0` +1.06%<br>`fie1wid0` +3.05% | hit v0–7 #2–4/6 |
| 2 | Focus | `fie1wie0` -1.30%<br>`fie1wif0` -7.13% | hit v0–7 #5–6/6 |

#### 036. death_corpse_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -2.06%**, using silhouette height only. Source: `level_generation/creatures/mm6_fie1/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `fie1dea0` -1.42%<br>`fie1deb0` -4.60% | death v0–7 #1–2/6 |
| 2 | Focus | `fie1dec0` -3.73%<br>`fie1ded0` -6.30% | death v0–7 #3–4/6 |

<a id="mm6-wel"></a>

### ElemWater A — `mm6:wel`

Viewer family: `#mm6_wel`. Package: `level_generation/creatures/mm6_wel/redo_2x`.

#### 037. walk_0_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.08%**, using hand_check / head_anchor. Source: `level_generation/creatures/mm6_wel/redo_2x/raw/walk_0_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `welwka0` -0.24%<br>`welwkb0` -7.36% | walk v0 #1–2/6 |
| 2 | Focus | `welwkc0` -8.21%<br>`welwkd0` -3.40% | walk v0 #3–4/6 |

#### 038. fidget_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -3.69%**, using hand_check / head_anchor. Source: `level_generation/creatures/mm6_wel/redo_2x/raw/fidget_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `welfia0` +7.69%<br>`welfib0` +5.35%<br>`welfic0` +3.65% | fidget v0–7 #1–3/6 |
| 2 | Focus | `welfid0` +0.36%<br>`welfie0` +3.53%<br>`welfif0` +1.46% | fidget v0–7 #4–6/6 |

#### 039. death_corpse_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: +7.62%**, using head_anchor / waist_calibration. Source: `level_generation/creatures/mm6_wel/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `weldya0` -0.03%<br>`weldyb0` -1.61% | death v0–7 #1–2/6 |
| 2 | Focus | `weldyc0` +12.34%<br>`weldyd0` +1.15% | death v0–7 #3–4/6 |

#### 040. unused_native_0_redo_02

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -3.53%**, using hand_check / head_anchor. Source: `level_generation/creatures/mm6_wel/redo_2x/raw/unused_native_0_redo_02_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `welfib2` +0.14%<br>`welfic1` +3.90% | Master only: `welfib2`, `welfic1` |
| 2 | Focus | `welfic2` -3.50%<br>`welfid1` +0.34% | Master only: `welfic2`, `welfid1` |

#### 041. unused_native_1_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: +2.63%**, using hand_check / head_anchor. Source: `level_generation/creatures/mm6_wel/redo_2x/raw/unused_native_1_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `welfie1` +1.97%<br>`welfie2` -5.10% | Master only: `welfie1`, `welfie2` |
| 2 | Focus | `welfif1` -1.29%<br>`welfif2` +3.33% | Master only: `welfif1`, `welfif2` |

<a id="mm6-figc"></a>

### FighterChain A — `mm6:figc`

Viewer family: `#mm6_figc`. Package: `level_generation/creatures/mm6_figc/redo_2x`.

#### 042. standing_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.27%**, using crown / sole. Source: `level_generation/creatures/mm6_figc/redo_2x/raw/standing_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `figcsta0` -0.03%<br>`figcsta1` -0.18%<br>`figcsta2` -0.34% | standing v0–2 #1/1<br>standing v6–7 mirrored #1/1 |
| 2 | Focus | `figcsta3` -2.30%<br>`figcsta4` -2.61% | standing v3–4 #1/1<br>standing v5 mirrored #1/1 |

#### 043. walk_3_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: +2.33%**, using crown / sole. Source: `level_generation/creatures/mm6_figc/redo_2x/raw/walk_3_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `figcwaa3` -0.32%<br>`figcwab3` -0.78%<br>`figcwac3` -0.75% | walk v3 #1–3/6<br>walk v5 mirrored #1–3/6 |
| 2 | Focus | `figcwad3` +1.56%<br>`figcwae3` +2.27%<br>`figcwaf3` +1.50% | walk v3 #4–6/6<br>walk v5 mirrored #4–6/6 |

#### 044. attack_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.05%**, using crown / sole. Source: `level_generation/creatures/mm6_figc/redo_2x/raw/attack_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `figcata0` -0.04%<br>`figcatb0` -0.11%<br>`figcatc0` -0.50% | attack v0–7 #1–3/6<br>attack2 v0–7 #1–3/6 |
| 2 | Focus | `figcatd0` -1.03%<br>`figcate0` -2.24%<br>`figcatf0` -2.16% | attack v0–7 #4–6/6<br>attack2 v0–7 #4–6/6 |

<a id="mm6-fgt"></a>

### FighterLeath A — `mm6:fgt`

Viewer family: `#mm6_fgt`. Package: `level_generation/creatures/mm6_fgt/redo_2x`.

#### 045. walk_3_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.79%**, using crown / sole. Source: `level_generation/creatures/mm6_fgt/redo_2x/raw/walk_3_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `fgtwlka3` +0.00%<br>`fgtwlkb3` -0.69%<br>`fgtwlkc3` -1.57% | walk v3 #1–3/6<br>walk v5 mirrored #1–3/6 |
| 2 | Focus | `fgtwlkd3` -3.46%<br>`fgtwlke3` -3.40%<br>`fgtwlkf3` -4.18% | walk v3 #4–6/6<br>walk v5 mirrored #4–6/6 |

#### 046. death_corpse_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -4.77%**, using silhouette height only. Source: `level_generation/creatures/mm6_fgt/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `fgtdeta0` -0.21%<br>`fgtdetb0` -0.80% | death v0–7 #1–2/5 |
| 2 | Focus | `fgtdetc0` -6.42%<br>`fgtdetd0` -4.09% | death v0–7 #3–4/5 |

<a id="mm6-djn"></a>

### BGenie A — `mm6:djn`

Viewer family: `#mm6_djn`. Package: `level_generation/creatures/mm6_djn/redo_2x`.

#### 047. walk_0_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.74%**, using crown / vortex_tip. Source: `level_generation/creatures/mm6_djn/redo_2x/raw/walk_0_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `djnwala0` -0.10%<br>`djnwalb0` -0.54%<br>`djnwalc0` -2.02% | walk v0 #1–3/6 |
| 2 | Focus | `djnwald0` -2.68%<br>`djnwale0` -3.27%<br>`djnwalf0` -3.75% | walk v0 #4–6/6 |

#### 048. walk_1_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.60%**, using crown / vortex_tip. Source: `level_generation/creatures/mm6_djn/redo_2x/raw/walk_1_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `djnwala1` -0.46%<br>`djnwalb1` +0.09%<br>`djnwalc1` -0.34% | walk v1 #1–3/6<br>walk v7 mirrored #1–3/6 |
| 2 | Focus | `djnwald1` -1.80%<br>`djnwale1` -2.93%<br>`djnwalf1` -4.10% | walk v1 #4–6/6<br>walk v7 mirrored #4–6/6 |

#### 049. walk_2_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.56%**, using crown / vortex_tip. Source: `level_generation/creatures/mm6_djn/redo_2x/raw/walk_2_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `djnwala2` +2.00%<br>`djnwalb2` +2.47%<br>`djnwalc2` +2.47% | walk v2 #1–3/6<br>walk v6 mirrored #1–3/6 |
| 2 | Focus | `djnwald2` +0.41%<br>`djnwale2` -0.15%<br>`djnwalf2` -0.97% | walk v2 #4–6/6<br>walk v6 mirrored #4–6/6 |

#### 050. attack_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.31%**, using crown / vortex_tip. Source: `level_generation/creatures/mm6_djn/redo_2x/raw/attack_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `djnatta0` -0.04%<br>`djnattb0` +4.50% | attack v0–7 #1–2/6<br>attack2 v0–7 #1–2/6 |
| 2 | Focus | `djnattc0` +0.52%<br>`djnattd0` -0.78% | attack v0–7 #3–4/6<br>attack2 v0–7 #3–4/6 |

#### 051. fidget_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -3.29%**, using crown / vortex_tip. Source: `level_generation/creatures/mm6_djn/redo_2x/raw/fidget_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `djnfida0` +0.16%<br>`djnfidb0` -0.71%<br>`djnfidc0` -1.21% | fidget v0–7 #1–3/6 |
| 2 | Focus | `djnfidd0` -3.64%<br>`djnfide0` -4.83%<br>`djnfidf0` -3.98% | fidget v0–7 #4–6/6 |

#### 052. death_corpse_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -11.11%**, using extent_max / extent_min. Source: `level_generation/creatures/mm6_djn/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `djndyia0` +0.35%<br>`djndyib0` +3.45%<br>`djndyic0` +5.22% | death v0–7 #1–3/6 |
| 2 | Focus | `djndyid0` -8.05%<br>`djndyie0` -7.93%<br>`djndyif0` -10.34% | death v0–7 #4–6/6 |

<a id="mm6-gst"></a>

### BGhost A — `mm6:gst`

Viewer family: `#mm6_gst`. Package: `level_generation/creatures/mm6_gst/redo_2x`.

#### 053. standing_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -4.93%**, using silhouette height only. Source: `level_generation/creatures/mm6_gst/redo_2x/raw/standing_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `gstflya0` -0.62%<br>`gstflya1` -0.41% | fidget v0–1 #1/6<br>fidget v7 mirrored #1/6<br>standing v0–1 #1/6<br>standing v7 mirrored #1/6<br>walk v0–1 #1/6<br>walk v7 mirrored #1/6 |
| 2 | Focus | `gstflya2` -5.04%<br>`gstflya3` -5.80% | fidget v2–3 #1/6<br>fidget v5–6 mirrored #1/6<br>standing v2–3 #1/6<br>standing v5–6 mirrored #1/6<br>walk v2–3 #1/6<br>walk v5–6 mirrored #1/6 |

#### 054. walk_3_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: +4.14%**, using hood / visible_hand_exit. Source: `level_generation/creatures/mm6_gst/redo_2x/raw/walk_3_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `gstflyb3` -5.33%<br>`gstflyc3` +2.83% | fidget v3 #2–3/6<br>fidget v5 mirrored #2–3/6<br>standing v3 #2–3/6<br>standing v5 mirrored #2–3/6<br>walk v3 #2–3/6<br>walk v5 mirrored #2–3/6 |
| 2 | Focus | `gstflyd3` +1.85%<br>`gstflye3` +3.84% | fidget v3 #4–5/6<br>fidget v5 mirrored #4–5/6<br>standing v3 #4–5/6<br>standing v5 mirrored #4–5/6<br>walk v3 #4–5/6<br>walk v5 mirrored #4–5/6 |

#### 055. attack_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -2.31%**, using silhouette height only. Source: `level_generation/creatures/mm6_gst/redo_2x/raw/attack_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `gstatka0` -0.56%<br>`gstatkb0` -1.91% | attack v0–7 #1–2/6<br>attack2 v0–7 #1–2/6 |
| 2 | Focus | `gstatkc0` -4.46%<br>`gstatkd0` -2.57% | attack v0–7 #3–4/6<br>attack2 v0–7 #3–4/6 |

#### 056. hit_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -3.38%**, using silhouette height only. Source: `level_generation/creatures/mm6_gst/redo_2x/raw/hit_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `gstwnca0` -0.60%<br>`gstwncb0` -2.43% | hit v0–7 #1–2/6 |
| 2 | Focus | `gstwncc0` -5.19%<br>`gstwncd0` -4.49% | hit v0–7 #3–4/6 |

<a id="mm6-goblin"></a>

### BGoblin A — `mm6:goblin`

Viewer family: `#mm6_goblin`. Package: `level_generation/creatures/mm6_goblin/direct_complete/redo_2x`.

#### 057. accepted_front_death_corpse_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +5.46%**, using silhouette height only. Source: `level_generation/creatures/mm6_goblin/direct_complete/redo_2x/raw/accepted_front_death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `gobdya0` -0.21%<br>`gobdyb0` +0.00% | death v0–7 #1–2/5 |
| 2 | Focus | `gobdyc0` +3.42%<br>`gobdyd0` +7.27%<br>`gobdyf0` +7.27% | corpse v0–7 #1/1<br>death v0–7 #3–4/5 |

#### 058. standing_sides_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -2.44%**, using silhouette height only. Source: `level_generation/creatures/mm6_goblin/direct_complete/redo_2x/raw/standing_sides_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `gobsta1` +0.19%<br>`gobsta2` +0.39% | standing v1–2 #1/1<br>standing v6–7 mirrored #1/1 |
| 2 | Focus | `gobsta3` -2.15%<br>`gobsta4` -2.16% | standing v3–4 #1/1<br>standing v5 mirrored #1/1 |

#### 059. accepted_front_hit_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -4.81%**, using silhouette height only. Source: `level_generation/creatures/mm6_goblin/direct_complete/redo_2x/raw/accepted_front_hit_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `gobwia0` +0.80%<br>`gobwib0` -0.62% | hit v0–7 #1–2/6 |
| 2 | Focus | `gobwic0` -2.74%<br>`gobwid0` -6.70% | hit v0–7 #3–4/6 |

<a id="mm6-gua"></a>

### Guard A — `mm6:gua`

Viewer family: `#mm6_gua`. Package: `level_generation/creatures/mm6_gua/redo_2x`.

#### 060. hit_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.85%**, using crown / sole. Source: `level_generation/creatures/mm6_gua/redo_2x/raw/hit_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `guawina0` -0.01%<br>`guawinb0` +0.77% | hit v0–7 #1–2/6 |
| 2 | Focus | `guawinc0` -2.90%<br>`guawind0` -2.06% | hit v0–7 #3–4/6 |

<a id="mm6-hrp"></a>

### BHarpy A — `mm6:hrp`

Viewer family: `#mm6_hrp`. Package: `level_generation/creatures/mm6_hrp/redo_2x`.

#### 061. walk_2_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.13%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_hrp/redo_2x/raw/walk_2_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `hrpflyb2` +5.61%<br>`hrpflyc2` -0.87% | fidget v2 #2–3/6<br>fidget v6 mirrored #2–3/6<br>standing v2 #2–3/6<br>standing v6 mirrored #2–3/6<br>walk v2 #2–3/6<br>walk v6 mirrored #2–3/6 |
| 2 | Focus | `hrpflyd2` -0.12%<br>`hrpflye2` +0.50% | fidget v2 #4–5/6<br>fidget v6 mirrored #4–5/6<br>standing v2 #4–5/6<br>standing v6 mirrored #4–5/6<br>walk v2 #4–5/6<br>walk v6 mirrored #4–5/6 |

<a id="mm6-hyd"></a>

### BHydra A — `mm6:hyd`

Viewer family: `#mm6_hyd`. Package: `level_generation/creatures/mm6_hyd/redo_2x`.

#### 062. standing_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: +4.50%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_hyd/redo_2x/raw/standing_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `hydwala0` -1.64%<br>`hydwala1` -1.00% | walk v0–1 #1/6<br>walk v7 mirrored #1/6 |
| 2 | Focus | `hydwala2` +4.53%<br>`hydwala3` +1.72% | walk v2–3 #1/6<br>walk v5–6 mirrored #1/6 |

#### 063. walk_0_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.13%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_hyd/redo_2x/raw/walk_0_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `hydwalb0` +0.39%<br>`hydwalc0` +1.84%<br>`hydwald0` +0.59% | walk v0 #2–4/6 |
| 2 | Focus | `hydwale0` -0.50%<br>`hydwalf0` -2.60% | walk v0 #5–6/6 |

#### 064. hit_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: +2.48%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_hyd/redo_2x/raw/hit_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `hydwina0` -2.87%<br>`hydwinb0` +0.11% | hit v0–7 #1–2/6 |
| 2 | Focus | `hydwinc0` +0.64%<br>`hydwind0` +1.49% | hit v0–7 #3–4/6 |

#### 065. death_corpse_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: +3.27%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_hyd/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `hyddyia0` -0.91%<br>`hyddyib0` -0.84% | death v0–7 #1–2/5 |
| 2 | Focus | `hyddyic0` +1.52%<br>`hyddyid0` +3.21% | death v0–7 #3–4/5 |

#### 066. unused_native_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.33%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_hyd/redo_2x/raw/unused_native_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `hydstaa0` +1.34%<br>`hydstaa1` +1.56% | Master only: `hydstaa0`, `hydstaa1` |
| 2 | Focus | `hydstaa2` -1.17%<br>`hydstaa3` -0.67% | Master only: `hydstaa2`, `hydstaa3` |

<a id="mm6-jak1"></a>

### Jackalman A — `mm6:jak1`

Viewer family: `#mm6_jak1`. Package: `level_generation/creatures/mm6_jak1/redo_2x`.

#### 067. standing_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.01%**, using crown / sole. Source: `level_generation/creatures/mm6_jak1/redo_2x/raw/standing_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `jak1sta0` +0.00%<br>`jak1sta1` -0.27%<br>`jak1sta2` -0.20% | standing v0–2 #1/1<br>standing v6–7 mirrored #1/1 |
| 2 | Focus | `jak1sta3` -2.34%<br>`jak1sta4` -2.07% | standing v3–4 #1/1<br>standing v5 mirrored #1/1 |

#### 068. hit_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -2.07%**, using silhouette height only. Source: `level_generation/creatures/mm6_jak1/redo_2x/raw/hit_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `jak1wia0` -0.17%<br>`jak1wib0` -0.50%<br>`jak1wic0` -0.16% | hit v0–7 #1–3/6 |
| 2 | Focus | `jak1wid0` -2.10%<br>`jak1wie0` -2.23%<br>`jak1wif0` -2.94% | hit v0–7 #4–6/6 |

#### 069. death_corpse_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +4.36%**, using silhouette height only. Source: `level_generation/creatures/mm6_jak1/redo_2x/raw/death_corpse_redo_01_v2.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `jak1dya0` -1.01%<br>`jak1dyb0` -3.04% | death v0–7 #1–2/5 |
| 2 | Focus | `jak1dyc0` +1.73%<br>`jak1dyd0` +2.75% | death v0–7 #3–4/5 |

<a id="mm6-kni"></a>

### KnightPlate A — `mm6:kni`

Viewer family: `#mm6_kni`. Package: `level_generation/creatures/mm6_kni/redo_2x`.

#### 070. walk_2_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.88%**, using crown / sole. Source: `level_generation/creatures/mm6_kni/redo_2x/raw/walk_2_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `kniwala2` +0.07%<br>`kniwalb2` +0.13%<br>`kniwalc2` +0.36% | walk v2 #1–3/6<br>walk v6 mirrored #1–3/6 |
| 2 | Focus | `kniwald2` -2.83%<br>`kniwale2` -2.75%<br>`kniwalf2` -1.81% | walk v2 #4–6/6<br>walk v6 mirrored #4–6/6 |

#### 071. death_corpse_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -2.97%**, using silhouette height only. Source: `level_generation/creatures/mm6_kni/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `knideta0` +0.00%<br>`knidetb0` -0.40% | death v0–7 #1–2/5 |
| 2 | Focus | `knidetc0` -2.90%<br>`knidetd0` -3.43% | death v0–7 #3–4/5 |

<a id="mm6-lch"></a>

### BLich A — `mm6:lch`

Viewer family: `#mm6_lch`. Package: `level_generation/creatures/mm6_lch/redo_2x`.

#### 072. hit_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -4.44%**, using silhouette height only. Source: `level_generation/creatures/mm6_lch/redo_2x/raw/hit_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `lchwnca0` +0.00%<br>`lchwncb0` +0.53% | hit v0–7 #1–2/6 |
| 2 | Focus | `lchwncc0` -4.83%<br>`lchwncd0` -3.55% | hit v0–7 #3–4/6 |

#### 073. death_corpse_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +4.03%**, using silhouette height only. Source: `level_generation/creatures/mm6_lch/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `lchdtha0` -0.18%<br>`lchdthb0` -1.06% | death v0–7 #1–2/5 |
| 2 | Focus | `lchdthc0` +4.25%<br>`lchdthd0` +2.53% | death v0–7 #3–4/5 |

<a id="mm6-lzd"></a>

### LizardArch A — `mm6:lzd`

Viewer family: `#mm6_lzd`. Package: `level_generation/creatures/mm6_lzd/redo_2x`.

#### 074. walk_1_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -3.95%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_lzd/redo_2x/raw/walk_1_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `lzdwala1` +1.63%<br>`lzdwalb1` +2.09%<br>`lzdwalc1` +1.80% | walk v1 #1–3/6<br>walk v7 mirrored #1–3/6 |
| 2 | Focus | `lzdwald1` -3.00%<br>`lzdwale1` -1.21%<br>`lzdwalf1` -2.22% | walk v1 #4–6/6<br>walk v7 mirrored #4–6/6 |

#### 075. walk_4_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -3.67%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_lzd/redo_2x/raw/walk_4_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `lzdwala4` +1.62%<br>`lzdwalb4` +2.27%<br>`lzdwalc4` +1.62% | walk v4 #1–3/6 |
| 2 | Focus | `lzdwald4` -3.57%<br>`lzdwale4` -1.27%<br>`lzdwalf4` -2.10% | walk v4 #4–6/6 |

#### 076. attack_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.85%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_lzd/redo_2x/raw/attack_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `lzdatka0` +1.11%<br>`lzdatkb0` +3.44%<br>`lzdatkc0` +1.11% | attack v0–7 #1–3/6<br>attack2 v0–7 #1–3/6 |
| 2 | Focus | `lzdatkd0` -2.89%<br>`lzdatke0` -0.65% | attack v0–7 #4–5/6<br>attack2 v0–7 #4–5/6 |

#### 077. fidget_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.84%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_lzd/redo_2x/raw/fidget_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `lzdfidb0` +0.16%<br>`lzdfidc0` +0.39%<br>`lzdfidd0` +0.39% | fidget v0–7 #2–4/6 |
| 2 | Focus | `lzdfide0` -2.27%<br>`lzdfidf0` -2.66% | fidget v0–7 #5–6/6 |

#### 078. death_corpse_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: +4.26%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_lzd/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `lzddtha0` -0.81%<br>`lzddthb0` -1.67% | death v0–7 #1–2/5 |
| 2 | Focus | `lzddthc0` +1.56%<br>`lzddthd0` +4.37% | death v0–7 #3–4/5 |

<a id="mm6-med"></a>

### BMedusa A — `mm6:med`

Viewer family: `#mm6_med`. Package: `level_generation/creatures/mm6_med/redo_2x`.

#### 079. walk_1_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.80%**, using coil_baseline / neck_ring. Source: `level_generation/creatures/mm6_med/redo_2x/raw/walk_1_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `medwala1` +0.09%<br>`medwalb1` +0.46% | walk v1 #1–2/6<br>walk v7 mirrored #1–2/6 |
| 2 | Focus | `medwalc1` -2.74%<br>`medwald1` -2.32% | walk v1 #3–4/6<br>walk v7 mirrored #3–4/6 |

#### 080. death_corpse_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -3.93%**, using grounded_coil / independent_wrist_or_neck. Source: `level_generation/creatures/mm6_med/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `meddyia0` +3.82%<br>`meddyib0` +4.89% | death v0–7 #1–2/5 |
| 2 | Focus | `meddyic0` +3.48%<br>`meddyid0` -2.96% | death v0–7 #3–4/5 |

<a id="mm6-min1"></a>

### BMinotaur A — `mm6:min1`

Viewer family: `#mm6_min1`. Package: `level_generation/creatures/mm6_min1/redo_2x`.

#### 081. standing_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.70%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_min1/redo_2x/raw/standing_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `min1wkc0` +1.90%<br>`min1wkc1` +1.51% | standing v0–1 #1/1<br>standing v7 mirrored #1/1<br>walk v0–1 #3/6<br>walk v7 mirrored #3/6 |
| 2 | Focus | `min1wkc2` -1.00%<br>`min1wkc3` -1.08% | standing v2–3 #1/1<br>standing v5–6 mirrored #1/1<br>walk v2–3 #3/6<br>walk v5–6 mirrored #3/6 |

#### 082. walk_1_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.13%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_min1/redo_2x/raw/walk_1_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `min1wka1` +1.13%<br>`min1wkb1` +1.57% | walk v1 #1–2/6<br>walk v7 mirrored #1–2/6 |
| 2 | Focus | `min1wkd1` -1.03%<br>`min1wke1` -0.60% | walk v1 #4–5/6<br>walk v7 mirrored #4–5/6 |

#### 083. walk_2_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.33%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_min1/redo_2x/raw/walk_2_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `min1wka2` +0.78%<br>`min1wkb2` +0.31%<br>`min1wkd2` +0.56% | walk v2 #1–2,4/6<br>walk v6 mirrored #1–2,4/6 |
| 2 | Focus | `min1wke2` -0.87%<br>`min1wkf2` -2.71% | walk v2 #5–6/6<br>walk v6 mirrored #5–6/6 |

<a id="mm6-nobl"></a>

### Nobleman A — `mm6:nobl`

Viewer family: `#mm6_nobl`. Package: `level_generation/creatures/mm6_nobl/redo_2x`.

#### 084. walk_2_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -3.60%**, using crown / sole. Source: `level_generation/creatures/mm6_nobl/redo_2x/raw/walk_2_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `noblwaa2` -0.07%<br>`noblwab2` +0.47% | walk v2 #1–2/6<br>walk v6 mirrored #1–2/6 |
| 2 | Focus | `noblwac2` -2.61%<br>`noblwad2` -4.21% | walk v2 #3–4/6<br>walk v6 mirrored #3–4/6 |

<a id="mm6-ooz"></a>

### BOoze A — `mm6:ooz`

Viewer family: `#mm6_ooz`. Package: `level_generation/creatures/mm6_ooz/redo_2x`.

#### 085. walk_3_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +3.47%**, using silhouette height only. Source: `level_generation/creatures/mm6_ooz/redo_2x/raw/walk_3_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `oozwab3` -0.92%<br>`oozwac3` -3.09% | walk v3 #2–3/6<br>walk v5 mirrored #2–3/6 |
| 2 | Focus | `oozwad3` +0.41%<br>`oozwae3` +2.38% | walk v3 #4–5/6<br>walk v5 mirrored #4–5/6 |
| 3 | Compare | `oozwaf3` +0.00% | walk v3 #6/6<br>walk v5 mirrored #6/6 |

#### 086. attack_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -3.86%**, using silhouette height only. Source: `level_generation/creatures/mm6_ooz/redo_2x/raw/attack_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `oozata` +2.08%<br>`oozatb` +5.14% | attack v0–7 #1–2/6<br>attack2 v0–7 #1–2/6 |
| 2 | Focus | `oozatc` +1.22%<br>`oozatd` -2.00% | attack v0–7 #3–4/6<br>attack2 v0–7 #3–4/6 |

#### 087. death_corpse_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -8.75%**, using crest / right. Source: `level_generation/creatures/mm6_ooz/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `oozdya` +4.81%<br>`oozdyb` +0.18% | death v0–7 #1–2/5 |
| 2 | Focus | `oozdyc` -5.76%<br>`oozdyd` -7.19% | death v0–7 #3–4/5 |

<a id="mm6-ogr"></a>

### Ogre A — `mm6:ogr`

Viewer family: `#mm6_ogr`. Package: `level_generation/creatures/mm6_ogr/redo_2x`.

#### 088. walk_2_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +2.30%**, using silhouette height only. Source: `level_generation/creatures/mm6_ogr/redo_2x/raw/walk_2_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `ogrwlka2` -0.40%<br>`ogrwlkb2` +0.60% | walk v2 #1–2/6<br>walk v6 mirrored #1–2/6 |
| 2 | Focus | `ogrwlkc2` +2.40%<br>`ogrwlkd2` +2.42% | walk v2 #3–4/6<br>walk v6 mirrored #3–4/6 |

#### 089. hit_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -2.72%**, using silhouette height only. Source: `level_generation/creatures/mm6_ogr/redo_2x/raw/hit_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `ogrwnca0` -0.40%<br>`ogrwncb0` +4.37% | hit v0–7 #1–2/6 |
| 2 | Focus | `ogrwncc0` -1.58%<br>`ogrwncd0` +0.00% | hit v0–7 #3–4/6 |

#### 090. fidget_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -2.93%**, using silhouette height only. Source: `level_generation/creatures/mm6_ogr/redo_2x/raw/fidget_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `ogrfgta0` -0.20%<br>`ogrfgtb0` -0.75% | fidget v0–7 #1–2/6 |
| 2 | Focus | `ogrfgtc0` -3.62%<br>`ogrfgtd0` -3.16% | fidget v0–7 #3–4/6 |

<a id="mm6-pfem"></a>

### PeasantF1 A — `mm6:pfem`

Viewer family: `#mm6_pfem`. Package: `level_generation/creatures/mm6_pfem/redo_2x`.

#### 091. death_corpse_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +3.71%**, using silhouette height only. Source: `level_generation/creatures/mm6_pfem/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `pfemdea0` -0.24%<br>`pfemdeb0` +0.30%<br>`pfemdec0` +0.97% | death v0–7 #1–3/5 |
| 2 | Focus | `pfemded0` -3.96%<br>`pfemdee0` +4.02%<br>`pfemdef0` +11.21% | corpse v0–7 #1/1<br>death v0–7 #4–5/5 |

<a id="mm6-fmp"></a>

### PeasantF2 A — `mm6:fmp`

Viewer family: `#mm6_fmp`. Package: `level_generation/creatures/mm6_fmp/redo_2x`.

#### 092. standing_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.50%**, using crown / sole. Source: `level_generation/creatures/mm6_fmp/redo_2x/raw/standing_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `fmpstaa0` +0.11%<br>`fmpstaa1` +0.11%<br>`fmpstaa2` +0.11% | standing v0–2 #1/1<br>standing v6–7 mirrored #1/1 |
| 2 | Focus | `fmpstaa3` -2.25%<br>`fmpstaa4` -2.53% | standing v3–4 #1/1<br>standing v5 mirrored #1/1 |

#### 093. walk_0_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.80%**, using crown / sole. Source: `level_generation/creatures/mm6_fmp/redo_2x/raw/walk_0_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `fmpwala0` -0.13%<br>`fmpwalb0` +1.57%<br>`fmpwalc0` +1.72% | walk v0 #1–3/6 |
| 2 | Focus | `fmpwald0` -1.96%<br>`fmpwale0` -1.27%<br>`fmpwalf0` -0.61% | walk v0 #4–6/6 |

#### 094. walk_3_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.02%**, using crown / sole. Source: `level_generation/creatures/mm6_fmp/redo_2x/raw/walk_3_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `fmpwala3` +0.10%<br>`fmpwalb3` +0.22%<br>`fmpwalc3` +0.22% | walk v3 #1–3/6<br>walk v5 mirrored #1–3/6 |
| 2 | Focus | `fmpwald3` -1.49%<br>`fmpwale3` -1.81%<br>`fmpwalf3` -1.96% | walk v3 #4–6/6<br>walk v5 mirrored #4–6/6 |

#### 095. hit_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.51%**, using crown / sole. Source: `level_generation/creatures/mm6_fmp/redo_2x/raw/hit_redo_01_v2.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `fmpwina0` +0.01%<br>`fmpwinb0` +0.01%<br>`fmpwinc0` -0.69% | hit v0–7 #1–3/6 |
| 2 | Focus | `fmpwind0` -2.50%<br>`fmpwine0` -2.50%<br>`fmpwinf0` -2.50% | hit v0–7 #4–6/6 |

#### 096. death_corpse_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: +4.38%**, using crown / sole. Source: `level_generation/creatures/mm6_fmp/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `fmpdyia0` +0.03%<br>`fmpdyib0` -1.70%<br>`fmpdyic0` -0.03% | death v0–7 #1–3/5 |
| 2 | Focus | `fmpdyid0` +1.10%<br>`fmpdyie0` +4.34%<br>`fmpdyif0` +16.61% | corpse v0–7 #1/1<br>death v0–7 #4–5/5 |

<a id="mm6-natf"></a>

### PeasantF4 A — `mm6:natf`

Viewer family: `#mm6_natf`. Package: `level_generation/creatures/mm6_natf/redo_2x`.

#### 097. walk_1_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.18%**, using crown / sole. Source: `level_generation/creatures/mm6_natf/redo_2x/raw/walk_1_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `natfwaa1` -0.06%<br>`natfwab1` -2.11%<br>`natfwac1` -1.02% | walk v1 #1–3/6<br>walk v7 mirrored #1–3/6 |
| 2 | Focus | `natfwad1` -2.70%<br>`natfwae1` -3.63%<br>`natfwaf1` -3.17% | walk v1 #4–6/6<br>walk v7 mirrored #4–6/6 |

<a id="mm6-pman"></a>

### PeasantM1 A — `mm6:pman`

Viewer family: `#mm6_pman`. Package: `level_generation/creatures/mm6_pman/redo_2x`.

#### 098. walk_1_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.04%**, using crown / sole. Source: `level_generation/creatures/mm6_pman/redo_2x/raw/walk_1_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `pmanwaa1` -0.05%<br>`pmanwab1` -1.32%<br>`pmanwac1` -1.19% | walk v1 #1–3/6<br>walk v7 mirrored #1–3/6 |
| 2 | Focus | `pmanwad1` -2.08%<br>`pmanwae1` -3.38%<br>`pmanwaf1` -3.20% | walk v1 #4–6/6<br>walk v7 mirrored #4–6/6 |

<a id="mm6-pmn2"></a>

### PeasantM2 A — `mm6:pmn2`

Viewer family: `#mm6_pmn2`. Package: `level_generation/creatures/mm6_pmn2/redo_2x`.

#### 099. walk_1_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.42%**, using crown / sole. Source: `level_generation/creatures/mm6_pmn2/redo_2x/raw/walk_1_redo_01_v4.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `pmn2waa1` -0.02%<br>`pmn2wab1` +0.53%<br>`pmn2wac1` -0.18% | walk v1 #1–3/6<br>walk v7 mirrored #1–3/6 |
| 2 | Focus | `pmn2wad1` -2.75%<br>`pmn2wae1` -2.08%<br>`pmn2waf1` -2.44% | walk v1 #4–6/6<br>walk v7 mirrored #4–6/6 |

#### 100. attack_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -3.24%**, using crown / sole. Source: `level_generation/creatures/mm6_pmn2/redo_2x/raw/attack_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `pmn2ata0` -0.02%<br>`pmn2atb0` +0.48% | attack v0–7 #1–2/6<br>attack2 v0–7 #1–2/6 |
| 2 | Focus | `pmn2atc0` -5.67%<br>`pmn2atd0` -0.38% | attack v0–7 #3–4/6<br>attack2 v0–7 #3–4/6 |

#### 101. hit_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: +2.80%**, using crown / sole. Source: `level_generation/creatures/mm6_pmn2/redo_2x/raw/hit_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `pmn2wia0` -0.03%<br>`pmn2wib0` +0.40% | hit v0–7 #1–2/6 |
| 2 | Focus | `pmn2wic0` +0.61%<br>`pmn2wid0` +5.36% | hit v0–7 #3–4/6 |

<a id="mm6-mep"></a>

### PeasantM3 A — `mm6:mep`

Viewer family: `#mm6_mep`. Package: `level_generation/creatures/mm6_mep/redo_2x`.

#### 102. walk_0_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: +2.16%**, using crown / sole. Source: `level_generation/creatures/mm6_mep/redo_2x/raw/walk_0_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `mepwala0` +0.06%<br>`mepwalb0` -2.20%<br>`mepwalc0` -2.18% | walk v0 #1–3/6 |
| 2 | Focus | `mepwald0` -1.25%<br>`mepwale0` -0.06%<br>`mepwalf0` +0.13% | walk v0 #4–6/6 |

#### 103. walk_2_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: +2.76%**, using crown / sole. Source: `level_generation/creatures/mm6_mep/redo_2x/raw/walk_2_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `mepwala2` +0.00%<br>`mepwalb2` -2.83% | walk v2 #1–2/6<br>walk v6 mirrored #1–2/6 |
| 2 | Focus | `mepwalc2` -0.29%<br>`mepwald2` +2.91% | walk v2 #3–4/6<br>walk v6 mirrored #3–4/6 |

#### 104. walk_3_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -3.33%**, using crown / sole. Source: `level_generation/creatures/mm6_mep/redo_2x/raw/walk_3_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `mepwala3` -0.03%<br>`mepwalb3` -1.65% | walk v3 #1–2/6<br>walk v5 mirrored #1–2/6 |
| 2 | Focus | `mepwalc3` -4.06%<br>`mepwald3` -4.21% | walk v3 #3–4/6<br>walk v5 mirrored #3–4/6 |

#### 105. attack_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -3.39%**, using crown / sole. Source: `level_generation/creatures/mm6_mep/redo_2x/raw/attack_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `mepatta0` +0.31%<br>`mepattb0` +1.54% | attack v0–7 #1–2/6<br>attack2 v0–7 #1–2/6 |
| 2 | Focus | `mepattc0` -0.86%<br>`mepattd0` -4.13% | attack v0–7 #3–4/6<br>attack2 v0–7 #3–4/6 |

#### 106. hit_redo_01

**Visually supported; fit pending.** Check body measurements through the recoil pose, then trial corrections for d/e/f.

Screen: **row 1 → 2: -3.64%**, using crown / sole. Source: `level_generation/creatures/mm6_mep/redo_2x/raw/hit_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `mepwina0` +0.07%<br>`mepwinb0` -0.26%<br>`mepwinc0` +0.69% | hit v0–7 #1–3/6 |
| 2 | Focus | `mepwind0` -2.57%<br>`mepwine0` -3.57%<br>`mepwinf0` -5.34% | hit v0–7 #4–6/6 |

#### 107. death_corpse_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +2.92%**, using silhouette height only. Source: `level_generation/creatures/mm6_mep/redo_2x/raw/death_corpse_redo_01_v2.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `mepdyia0` +0.82%<br>`mepdyib0` +0.87% | death v0–7 #1–2/5 |
| 2 | Focus | `mepdyic0` +3.92%<br>`mepdyid0` +3.66% | death v0–7 #3–4/5 |

<a id="mm6-natm"></a>

### PeasantM4 A — `mm6:natm`

Viewer family: `#mm6_natm`. Package: `level_generation/creatures/mm6_natm/redo_2x`.

#### 108. walk_4_redo_01

**Visually supported; fit pending.** Prioritize body-feature fitting and a reversible trial for c/d; compare both rows against native absolute scale.

Screen: **row 1 → 2: -4.50%**, using crown / sole. Source: `level_generation/creatures/mm6_natm/redo_2x/raw/walk_4_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `natmwaa4` +1.98%<br>`natmwab4` +2.08% | walk v4 #1–2/6 |
| 2 | Focus | `natmwac4` -2.90%<br>`natmwad4` -2.22% | walk v4 #3–4/6 |

<a id="mm6-rob1"></a>

### BRobot A — `mm6:rob1`

Viewer family: `#mm6_rob1`. Package: `level_generation/creatures/mm6_rob1/redo_2x`.

#### 109. standing_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -2.20%**, using silhouette height only. Source: `level_generation/creatures/mm6_rob1/redo_2x/raw/standing_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `rob1fla0` -1.47%<br>`rob1fla1` -1.46%<br>`rob1fla2` -2.62% | standing v0–2 #1/6<br>standing v6–7 mirrored #1/6<br>walk v0–2 #1/6<br>walk v6–7 mirrored #1/6 |
| 2 | Focus | `rob1fla3` -3.49%<br>`rob1fla4` -3.78% | standing v3–4 #1/6<br>standing v5 mirrored #1/6<br>walk v3–4 #1/6<br>walk v5 mirrored #1/6 |

#### 110. hit_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +3.47%**, using silhouette height only. Source: `level_generation/creatures/mm6_rob1/redo_2x/raw/hit_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `rob1wia0` -0.89%<br>`rob1wib0` +3.48% | hit v0–7 #1–2/6 |
| 2 | Focus | `rob1wid0` +6.60%<br>`rob1wie0` +4.81%<br>`rob1wif0` +0.63% | hit v0–7 #4–6/6 |

#### 111. fidget_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -2.19%**, using silhouette height only. Source: `level_generation/creatures/mm6_rob1/redo_2x/raw/fidget_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `rob1fia0` -0.29%<br>`rob1fic0` -0.29%<br>`rob1fid0` +0.59% | fidget v0–7 #1–4/6 |
| 2 | Focus | `rob1fie0` -2.63%<br>`rob1fif0` -2.33% | fidget v0–7 #5–6/6 |

#### 112. death_corpse_redo_01

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -16.03%**, using silhouette height only. Source: `level_generation/creatures/mm6_rob1/redo_2x/raw/death_corpse_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `rob1dea0` +0.30%<br>`rob1deb0` +5.70% | death v0–7 #1–2/6 |
| 2 | Focus | `rob1dec0` -12.45%<br>`rob1ded0` -14.57% | death v0–7 #3–4/6 |

<a id="mm6-seas"></a>

### SeaSerpent A — `mm6:seas`

Viewer family: `#mm6_seas`. Package: `level_generation/creatures/mm6_seas/redo_2x`.

#### 113. walk_0_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: +2.78%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_seas/redo_2x/raw/walk_0_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `seaswaa0` -1.85%<br>`seaswab0` -1.13%<br>`seaswac0` +0.09% | walk v0 #1–3/6 |
| 2 | Focus | `seaswad0` +0.32%<br>`seaswae0` +1.62%<br>`seaswaf0` +2.46% | walk v0 #4–6/6 |

#### 114. walk_1_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -5.00%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_seas/redo_2x/raw/walk_1_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `seaswaa1` +2.38%<br>`seaswab1` +2.59% | walk v1 #1–2/6<br>walk v7 mirrored #1–2/6 |
| 2 | Focus | `seaswac1` -3.35%<br>`seaswad1` -1.92% | walk v1 #3–4/6<br>walk v7 mirrored #3–4/6 |

#### 115. walk_3_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -6.79%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_seas/redo_2x/raw/walk_3_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `seaswaa3` +4.88%<br>`seaswab3` +2.06% | walk v3 #1–2/6<br>walk v5 mirrored #1–2/6 |
| 2 | Focus | `seaswac3` -5.59%<br>`seaswad3` -1.51% | walk v3 #3–4/6<br>walk v5 mirrored #3–4/6 |

#### 116. walk_4_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -4.74%**, using floor_contact / top_silhouette. Source: `level_generation/creatures/mm6_seas/redo_2x/raw/walk_4_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `seaswaa4` +4.05%<br>`seaswab4` +2.01%<br>`seaswac4` +1.19% | walk v4 #1–3/6 |
| 2 | Focus | `seaswad4` -3.65%<br>`seaswae4` -2.82%<br>`seaswaf4` -0.82% | walk v4 #4–6/6 |

<a id="mm6-sor1"></a>

### Sorcerer A — `mm6:sor1`

Viewer family: `#mm6_sor1`. Package: `level_generation/creatures/mm6_sor1/redo_2x`.

#### 117. walk_0_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.00%**, using crown / sole. Source: `level_generation/creatures/mm6_sor1/redo_2x/raw/walk_0_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `sor1wka0` +0.04%<br>`sor1wkb0` -1.14%<br>`sor1wkc0` -1.45% | walk v0 #1–3/6 |
| 2 | Focus | `sor1wkd0` -2.36%<br>`sor1wke0` -3.12%<br>`sor1wkf0` -3.62% | walk v0 #4–6/6 |

#### 118. walk_4_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: +2.99%**, using crown / sole. Source: `level_generation/creatures/mm6_sor1/redo_2x/raw/walk_4_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `sor1wka4` -0.10%<br>`sor1wkb4` -1.28%<br>`sor1wkc4` -2.08% | walk v4 #1–3/6 |
| 2 | Focus | `sor1wkd4` +1.67%<br>`sor1wke4` +0.33%<br>`sor1wkf4` +1.70% | walk v4 #4–6/6 |

<a id="mm6-thf"></a>

### BThief A — `mm6:thf`

Viewer family: `#mm6_thf`. Package: `level_generation/creatures/mm6_thf/redo_2x`.

#### 119. walk_0_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.02%**, using crown / sole. Source: `level_generation/creatures/mm6_thf/redo_2x/raw/walk_0_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `thfwala0` -0.06%<br>`thfwalb0` +1.04%<br>`thfwalc0` +0.35% | walk v0 #1–3/6 |
| 2 | Focus | `thfwald0` -2.66%<br>`thfwale0` -0.89%<br>`thfwalf0` -1.68% | walk v0 #4–6/6 |

#### 120. walk_2_redo_01

**Visual mismatch; proportions uncertain.** The later row is taller but silhouette width trends narrower. Check body proportions before choosing uniform reduction.

Screen: **row 1 → 2: +3.58%**, using crown / sole. Source: `level_generation/creatures/mm6_thf/redo_2x/raw/walk_2_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `thfwala2` -0.03%<br>`thfwalb2` +1.60%<br>`thfwalc2` +0.61% | walk v2 #1–3/6<br>walk v6 mirrored #1–3/6 |
| 2 | Focus | `thfwald2` +4.07%<br>`thfwale2` +4.21%<br>`thfwalf2` +4.66% | walk v2 #4–6/6<br>walk v6 mirrored #4–6/6 |

#### 121. hit_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -2.29%**, using crown / sole. Source: `level_generation/creatures/mm6_thf/redo_2x/raw/hit_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `thfwina0` +0.12%<br>`thfwinb0` +0.12%<br>`thfwinc0` -0.43% | hit v0–7 #1–3/6 |
| 2 | Focus | `thfwind0` -2.17%<br>`thfwine0` -2.17%<br>`thfwinf0` -2.31% | hit v0–7 #4–6/6 |

<a id="mm6-wfigt1"></a>

### Werewolf A — `mm6:wfigt1`

Viewer family: `#mm6_wfigt1`. Package: `level_generation/creatures/mm6_wfigt1/redo_2x`.

#### 122. death_corpse

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +3.39%**, using silhouette height only. Source: `level_generation/creatures/mm6_wfigt1/raw/death_corpse.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `wdead1a0` +0.00%<br>`wdead1b0` -0.22%<br>`wdead1c0` -0.27% | death v0–7 #1–3/4 |
| 2 | Focus | `wdead1d0` +4.87%<br>`wdead1e0` +1.47% | corpse v0–7 #1/1<br>death v0–7 #4/4 |

<a id="mm6-mcac"></a>

### Cactus A — `mm6:mcac`

Viewer family: `#mm6_mcac`. Package: `level_generation/creatures/mm6_mcac/redo_2x`.

#### 123. attack_0_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: -5.83%**, using lower_spine_envelope / upper_spine_envelope. Source: `level_generation/creatures/mm6_mcac/redo_2x/raw/attack_0_redo_01_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `mcacaa0` +3.48%<br>`mcacab0` +3.48%<br>`mcacac0` +2.70%<br>`mcacad0` +0.05% | attack v0–7 #1–4/17<br>attack2 v0–7 #1–4/17 |
| 2 | Focus | `mcacae0` -1.64%<br>`mcacaf0` -4.94% | attack v0–7 #5–6/17<br>attack2 v0–7 #5–6/17 |

#### 124. death_corpse_redo_02

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +3.71%**, using silhouette height only. Source: `level_generation/creatures/mm6_mcac/redo_2x/raw/death_corpse_redo_02_v1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `mcacdi0` -22.05%<br>`mcacdj0` -21.82% | death v0–7 #9–10/15 |
| 2 | Focus | `mcacdk0` -21.76%<br>`mcacdl0` -16.32% | death v0–7 #11–12/15 |

#### 125. adequate_redo_01

**Landmark candidate; unverified.** Verify corresponding body dimensions and absolute scale in both rows before proposing any adjustment.

Screen: **row 1 → 2: +2.65%**, using lower_spine_envelope / upper_spine_envelope. Source: `level_generation/creatures/mm6_mcac/redo_2x/raw/adequate_redo_01_v2.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `mcacsa0` -0.22%<br>`mcacsb0` -0.22%<br>`mcacas0` -4.84%<br>`mcacat0` -2.68% | standing v0–7 #1–2/17<br>Master only: `mcacas0`, `mcacat0` |
| 2 | Focus | `mcacau0` +0.09%<br>`mcacza0` -0.29% | hit v0–7 #1/1<br>Master only: `mcacau0` |

<a id="mm6-mnk1"></a>

### BMonk A — `mm6:mnk1`

Viewer family: `#mm6_mnk1`. Package: `level_generation/creatures/mm6_mnk1`.

#### 126. death_corpse

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: -3.45%**, using silhouette height only. Source: `level_generation/creatures/mm6_mnk1/raw/death_corpse.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `mnk1dea0` +0.00%<br>`mnk1deb0` -0.25%<br>`mnk1dec0` +0.00% | death v0–7 #1–3/5<br>death v0–7 #1–3/6 |
| 2 | Focus | `mnk1ded0` -3.45%<br>`mnk1dee0` -4.79%<br>`mnk1def0` +5.10% | corpse v0–7 #1/1<br>death v0–7 #4–5/5<br>death v0–7 #4–6/6 |

<a id="mm6-rat"></a>

### BRat A — `mm6:rat`

Viewer family: `#mm6_rat`. Package: `level_generation/creatures/mm6_rat`.

#### 127. standing

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +10.67%**, using silhouette height only. Source: `level_generation/creatures/mm6_rat/raw/standing.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `ratsta0` +0.00%<br>`ratsta1` -1.32%<br>`ratsta2` -1.32% | standing v0–2 #1/1<br>standing v6–7 mirrored #1/1 |
| 2 | Focus | `ratsta3` +7.24%<br>`ratsta4` +11.18% | standing v3–4 #1/1<br>standing v5 mirrored #1/1 |

#### 128. walk_4

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +2.30%**, using silhouette height only. Source: `level_generation/creatures/mm6_rat/raw/walk_4.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `ratwala4` +0.00%<br>`ratwalb4` -1.14%<br>`ratwalc4` -1.69% | walk v4 #1–3/6 |
| 2 | Focus | `ratwald4` +2.38%<br>`ratwale4` +1.14%<br>`ratwalf4` -0.54% | walk v4 #4–6/6 |

<a id="mm6-spi1"></a>

### BSpider A — `mm6:spi1`

Viewer family: `#mm6_spi1`. Package: `level_generation/creatures/mm6_spi1`.

#### 129. walk_1

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +4.92%**, using silhouette height only. Source: `level_generation/creatures/mm6_spi1/raw/walk_1.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `spi1waa1` -4.84%<br>`spi1wab1` -2.15%<br>`spi1wac1` -1.10% | walk v1 #1–3/6<br>walk v7 mirrored #1–3/6 |
| 2 | Focus | `spi1wad1` +2.72%<br>`spi1wae1` +1.61%<br>`spi1waf1` +2.66% | walk v1 #4–6/6<br>walk v7 mirrored #4–6/6 |

#### 130. walk_2

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +3.78%**, using silhouette height only. Source: `level_generation/creatures/mm6_spi1/raw/walk_2.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `spi1waa2` -4.26%<br>`spi1wab2` -1.06%<br>`spi1wac2` -1.61% | walk v2 #1–3/6<br>walk v6 mirrored #1–3/6 |
| 2 | Focus | `spi1wad2` +2.66%<br>`spi1wae2` +0.53%<br>`spi1waf2` +2.11% | walk v2 #4–6/6<br>walk v6 mirrored #4–6/6 |

#### 131. walk_3

**Silhouette candidate; unverified.** Identify reliable body/effect landmarks first; equipment or pose changes may explain the screen.

Screen: **row 1 → 2: +3.16%**, using silhouette height only. Source: `level_generation/creatures/mm6_spi1/raw/walk_3.png`.

| Source row | Review role | Exact frames: measured span vs original | Animation bindings |
| ---: | --- | --- | --- |
| 1 | Compare | `spi1waa3` -1.04%<br>`spi1wab3` -1.58%<br>`spi1wac3` +0.53% | walk v3 #1–3/6<br>walk v5 mirrored #1–3/6 |
| 2 | Focus | `spi1wad3` +2.11%<br>`spi1wae3` +2.08%<br>`spi1waf3` -0.52% | walk v3 #4–6/6<br>walk v5 mirrored #4–6/6 |

## Families without a candidate from this screen

BBeholder A, Cockatrice A, DemonFly A, Demon A, BDragonFly A, DragonCover A, BGargoyle A, PeasantF3 A, Skeleton A, BTitan A, zDemonQueen, zReactor, Merchant A.

This is not a clean bill of health: single-row sheets, sheets without sufficient distinct cells per row, smaller discrepancies, and body-proportion errors can escape this screen. It also does not replace the user’s existing acceptance flags or saved frame notes. No artwork or acceptance state was changed to build this list.

Audit SHA-256: `783ea5d6fb684c994128534fe8ac57f4373c25df6e7c883c9efa2ef6ea241846`.
