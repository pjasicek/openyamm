# Stream: texture pass on the worst MM6–MM8 textures

Three agents (`texpass-1`, `texpass-2` and, from 16:10, `texpass-3`) work one shared queue. Read [COMMON.md](COMMON.md) first. The recipe and its
lessons are fixed:

- [TEXTURE_QUALITY_PASS.md](../../claude_shared/TEXTURE_QUALITY_PASS.md)
- [texpass_mm678/HANDOFF.md](../../claude_shared/texpass_mm678/HANDOFF.md): read it fully. It covers what the trial
  settled, starting from the installed GLB, LOD1 projection, LOD2/3 refill, the head-only 4K paint, eyes and faces,
  drift, and region ramps.
- The Troll project `mm8_m480_texpass_claude/` has the most reusable scripts. The MM7 peasants (`mm7_m342_texpass_claude`
  and its siblings) show the face rules.

**How to take an item:** go down the queue in order. Skip anything marked in progress or done in `LEDGER_texpass.md`.
Claim the lease; if the claim fails, take the next item. Add the ledger row, do the pass, install, run the checks,
write the result, then release. Two agents may finish one item each in parallel; never more than one model per agent.

**Acceptance per model:**
- atlas at least 48 % (aim 55 %);
- fragments under 5 %;
- stretch p90 under 1.6;
- the same look as before in every tier, with no colour drift and no new blotches;
- faces and eyes checked close up, front and three-quarter, in every tier;
- every check in COMMON.md passed.

Per the handoff, report credits, the `texture_quality.py` before and after, and the sheet paths. Do not touch clips,
weights or `actors.yml`.

## Queue, phase A (worst first: atlas %, fragments %, stretch p90 of the worst body set)

Special cases come first in each note. The rebuild stream owns PeasantF1, the lizardman peasant, Merchant, Thief, Guard,
Werewolf and Titan: never take those.

| Model | Name | Atlas | Frag | Stretch | Note |
|---|---|---|---|---|---|
| mm6_demon | Demon | 3.2 | 75.4 | 2.03 | Claws set uses a whole 2K texture at 3 %: repack or merge into the body; body set 33 %, normal pass |
| mm8_m496 | Fire Elemental | 7.2 | 53.5 | 2.01 | MPFB effect body with flame cards. If it has no Meshy paint, repack only, or skip with a reason |
| mm7_m186 | Dragonfly | 9.0 | 31.8 | 1.71 | |
| mm8_m508 | Air Elemental | 10.8 | 34.4 | 1.71 | MPFB effect body: as m496 |
| mm7_m158 | Bat | 12.4 | 29.2 | 1.89 | |
| mm8_m552 | Thunderbird (+ mm7_m390 Roc) | 13.2 | 25.8 | 1.49 | Shared layout: claim both |
| mm6_lch | BLich | 15.3 | 14.3 | 2.27 | |
| mm8_m564 | Gorgon | 15.6 | 26.8 | 1.94 | |
| mm6_lzd | LizardArch | 17.2 | 13.7 | 1.78 | Bow set LizardBow_A 1.9 % at 1K: repack |
| mm8_m548 | Crystal Dragon | 18.4 | 22.0 | 1.46 | |
| mm7_m266 | Hydra | 18.9 | 48.8 | 1.88 | |
| mm8_m572 | Phoenix | 19.9 | 39.1 | 1.19 | |
| mm8_m436 | Ogre Peasant Male | 20.4 | 23.9 | 1.71 | |
| mm6_drg1 | BDragonFly | 20.7 | 19.9 | 1.94 | |
| mm7_m166 | Beholder | 21.2 | 21.9 | 2.01 | |
| mm6_ckt | Cockatrice | 22.0 | 21.9 | 1.91 | |
| mm8_ratman | Wererat Ratman | 22.6 | 16.1 | 1.79 | |
| mm8_m476 | Troll | 23.9 | 21.3 | 1.66 | The animation stream also fixes its Hit: coordinate through the lease |
| mm8_m492 | zUltra Dragon | 24.1 | 35.4 | 1.69 | |
| mm8_m560 | Wyvern (+ mm7_m434) | 24.6 | 5.2 | 1.31 | Shared layout: claim both |
| mm8_m576 | Triton | 24.6 | 6.6 | 2.12 | |
| mm7_m386 | Robot | 26.9 | 36.1 | 1.69 | Spotted brass is Meshy paint (README); a new paint may fix it |
| mm6_djn | BGenie | 26.9 | 10.4 | 4.61 | User accepted the left bracer texture "for now"; fix it in this pass |
| mm6_gar | BGargoyle | 28.7 | 28.7 | 1.88 | |
| mm7_m182 | ADragon | 28.8 | 36.1 | 3.43 | Stale lease (see COMMON); MM6 cdr1 body with a grafted head |
| mm6_seas | SeaSerpent | 29.1 | 30.9 | 1.75 | |
| mm7_m162 | Behemoth | 31.7 | 50.9 | 2.58 | |
| mm6_ske | Skeleton | 33.1 | 42.5 | 1.87 | |
| mm6_qfi | zDemonQueen | 35.0 | 31.5 | 3.47 | Hive and queen |
| mm8_m556 | Wasp Warrior | 35.4 | 45.4 | 1.75 | Its clip fixes live only in the reduce export (provenance notes): start from the installed GLB |
| mm6_wdm | DemonFly | 38.6 | 58.1 | 3.07 | |
| mm6_dru1 | Druidess | 39.0 | 36.7 | 3.12 | |
| mm7_m238 | Genie | 40.6 | 43.4 | 2.02 | |
| mm6_gob2 | BGoblin | 44.2 | 14.4 | 4.52 | |
| mm8_centaur | Centaur | 46.4 | 33.9 | 2.20 | |
| mm8_m588 | Malevolent Boulder | 46.4 | 43.9 | 1.49 | |
| mm7_7m500 | zcat | 48.6 | 36.7 | 1.48 | |
| mm7_m242 | Ghost | 49.6 | 45.6 | 1.60 | |
| mm8_m584 | Raven Man | 54.2 | 37.6 | 2.66 | |
| mm6_natm | PeasantM4 | 58.6 | 50.7 | 1.76 | Fragments, not atlas |
| mm6_fie1 | ElemFire | 60.7 | 0.0 | 1.90 | Effect atlas; probably nothing to do: check and skip with a reason |
| mm6_rea | zReactor | 69.9 | 9.7 | 7.91 | Find what is broken in its UVs first (handoff) |

Also listed in the handoff as "not a retexture first": `mm6_nobl` (stretch p90 8.25). Investigate its UVs when you
reach this point in the queue.

## Queue, phase B (after phase A, while the 900-credit cap allows)

mm6_mfp, mm6_med, mm7_m278, mm7_m382, mm6_bh, mm8_m540, mm8_m596, mm8_m472, mm7_m218, mm8_m604, mm8_m608, mm7_m258,
mm8_m440, mm8_m516, mm6_gst, mm6_cdr1, mm8_wolf, mm7_m479, mm8_m408, mm6_mep, mm8_m620, mm6_figc, mm7_m302, mm6_cob,
mm7_m270, mm6_wyrm, mm8_m628, mm8_m484, mm8_m524, mm6_hyd, mm7_m246, mm6_natf, mm7_m398, mm7_m170 (worst atlas
first). Several also have animation work queued; the lease keeps the two streams apart.

## When both queues are empty or the cap is reached

Take items from the attack queue in [ANIM.md](ANIM.md) (section "Blandest attacks"), using `LEDGER_anim.md` to see
what is free. Follow that brief for those items.
