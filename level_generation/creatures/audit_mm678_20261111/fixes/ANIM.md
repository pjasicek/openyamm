# Stream: clip and weight fixes, then the blandest attacks

One agent (`anim`). Read [COMMON.md](COMMON.md) first, then the humanoid playbook
([CLAUDE_HUMANOID_NPC_PLAYBOOK.md](../../CLAUDE_HUMANOID_NPC_PLAYBOOK.md); its arm and hand gate is mandatory) or the
quadruped playbook for non-humanoids. The texture-pass agents may help with part 4 once their queue is done.

Measure with `claude_shared/motion_audit.py` before and after, and check with `claude_shared/motion_frames.py
<glb> <clip> <out.png> --highlight [--joint J --zoom 0.3]`. The audit's `sheet.py` puts several moments side by side.
A fix is done when:
- the flagged region's bad share beyond Standing is under 12 % (cloth under 15 %);
- the frames show no balloon, hole or tear;
- no other clip got worse;
- the arm and hand gate, floor and gait checks and the regression pass.

## 1. Robes and skirts in the run clips

The 2026-10-31 gait rollout added Jog, Run2 and Sprint (and on some models Walk2), and the cloth chains do not
survive them. Its per-batch READMEs are in `gait_rollout_20261031/hNN/`; find each model's batch there, and read how
the clips were made. Known good repairs:
- m342 and m372: arms out 6° with no hand push on the skirt chains (`mm7_m342_texpass_claude`, round 2);
- the batch-B robe chains;
- `meshy-cloth-lining` (an exact offset inner copy).

Re-bake or re-solve the cloth for the affected clips. Where a clip is too fast for the cloth, damp it, limit the
chains, or narrow the stride. Measured (cloth region, % bad beyond Standing):

| Model | Clips | Worst |
|---|---|---|
| mm6_mfp PeasantF3 | Jog 47.6, Sprint 59.6 | skirt balloons into an egg |
| mm8_m484 Minotaur | Jog 39.9, Running 42.4, Sprint 38.9 | holes in the kilt |
| mm7_m430 Wight | **Walking** 38.9 | robe pulled into long sheets; plays all the time: do first |
| mm6_sor1 Sorcerer | Jog 36.8, Walking 21.2 | |
| mm8_m472 Necromancer | Run2 39.3 | |
| mm7_m290 Monk | Jog 31.5, Sprint 32.0 | |
| mm6_mnk1 BMonk | Run2 29.3 | |
| mm7_m170 Cleric Moon | Jog 24.2 | |
| mm7_m294 Necromancer | Jog 23.1 | also in part 2 |
| mm8_m460 Cleric | Jog 22.0 | |

(mm6_thf belongs to the rebuild stream.)

## 2. Hit reactions that fold torsos

On these bipeds the Hit clip folds or stretches the spine, head or arm region by 18–42 % beyond Standing. Many share
one library Hit (the humanoid set's `Unarmed get-hit`; check each model's clip sources in
`../provenance_mm6.csv` or `../provenance_mm78.csv`). First find out whether the fault is the clip (too much spine
bend and twist on bodies with long torsos and armour), the weights (chest and back skin over too few spine joints),
or both. Then choose one fix per cause and apply it to the whole group. Options: a gentler library hit, scaling the
spine keys, or smoothing spine weights. Keep a readable flinch.

| Model | Region, % | Model | Region, % |
|---|---|---|---|
| mm7_m294 Necromancer | spine 42.2, head 20.5 | mm6_wdm DemonFly | spine 23.9 |
| mm7_m190 Dwarf | spine 36.7, arm 20.8 | mm7_m290 Monk | spine 23.3 |
| mm6_kni KnightPlate | spine 28.4 | mm8_m476 Troll | spine 23.0 |
| mm7_m342 Peasant Human1 F | head 28.4 | mm7_m475 zBlasterGuy | arm 23.0 |
| mm7_m302 Peasant Dwarf M | spine 26.2, arm 21.5 | mm7_m262 Harpy | head 22.1, spine 20.8 |
| mm6_pman_v2 PeasantM1 | spine 20.9 | mm6_gob2 BGoblin | spine 20.1 |
| mm8_m472 Necromancer | head 19.6 | mm8_m444 | spine 19.1 |
| mm7_m214 | arm 18.1 | mm7_m254 Golem | arm 18.1 |
| mm8_m480 Troll Peasant (+ mm7_m461) | arm 18.0 | | |

## 3. Single faults

- **mm8_m456 Dragon Hunter, Walking:** the left hand is inside the thigh (62 % of hand vertices; plays all the time).
  Add arm clearance as the playbook's arm-clear correction does: solve on keys, low-pass, and keep the gesture.
- **mm8_m464 Vampire Female Peasant, Running** (bound run): the loop jumps ten times its normal frame step at the
  seam. Close the seam.
- **mm7_m242 Ghost, Walking:** the loop seam jumps about twice its normal frame step. Close it.
- **mm8_m544 Unicorn:** Hit equals Standing (no reaction). Author or adapt a hit (MM9 GOAT/COW wince, or the
  quadruped playbook's route).
- **Attack and Cast are one clip** on mm8_m540 Ogre Mage, mm6_mep, mm6_lzd, mm7_m182 and mm8_m544. Give the casters
  (m540 at least) a real cast. For the others, decide from the native sprite whether a separate cast exists.
- **mm7_m162 Behemoth:** Attack sinks 17–21 units into the floor (known, `claude_shared/floor/README.md`). Fix with
  `floor_fix.py` or by re-solving the claw.

## 4. Blandest attacks: re-animate from donors

These melee attacks reach under 45 % of the MM9 median for their body type, measured as the mean of reach, moving
share and peak speed (`../score.py`). The goal is an attack that moves legs and torso, has a clear wind-up and a
fast strike, and stays true to the native sprite's action. Gate: the score's motion ratio at least 0.75, unless the
native sprite shows a restrained move (record why). Then:
- move `events.impact` (and the `attack_ranged` and `cast` impacts) in `actors.yml` to the new contact frame, and
  keep the sockets;
- the arm and hand gate passes, the floor passes, and no new deformation appears;
- held props still meet the grip: weapons are separate GLBs, so check them in the viewer.

**Donors.** See [options_mm9_lomm.md](../options_mm9_lomm.md). The user's rule (2026-11-11): use any MM9 or Legends
of Might and Magic donor, **except the MM9 Dragon**, whose clips do not fit.
- MM9 ABCs: `mm9/extracted/MODELS/MODELS/*.abc`, read with `tools/mm9_import_discovery/convert_abc_model.py`.
  `claude_shared/mm9_clip_census.py` lists their clips; the MM9 projects' `clips_mm9.py` resample them (PCHIP,
  30 fps).
- LoMM: `reference/legends_of_mm/Data/MODELS.REZ`, extracted with `tools/mm9_import_discovery/extract_rez.py`.
- Retarget onto our skeletons by world-rotation copy, as the MM6–MM8 projects do (`mm6_ttn1_claude`'s
  `retarget_fbx.py`, the humanoid playbook).
- Otherwise use `anim_library` (humanoid set, the full local Mixamo library; query `index.json` first), choosing
  clips that use the whole body.

Start with one model per donor family and look at it in the viewer before repeating the route on its siblings.

**Owners (from 2026-11-11 16:10):** two dedicated agents take this part, so `anim` stops after parts 1–3.
- `attacks-1` takes the people: mfp, m475, m174, m426, m540 (with its Cast), m274, m536, m416.
- `attacks-2` takes the other bodies: m386, m608, wyrm, m524, m568, m282, m500 (+ m210), m600.
Record these in `LEDGER_attacks.md`. The texture-pass agents help with whatever is still free when their queue ends.

| Model | Name | Ratio | Suggested donor |
|---|---|---|---|
| mm6_mfp | PeasantF3 | 0.32 | MM9 PEASANTFEMALE hattack1 |
| mm7_m475 | zBlasterGuy | 0.30 | LoMM player set (wand, crossbow) or a Mixamo pistol or rifle shot with the body |
| mm7_m386 | Robot (scorpion) | 0.22 | none: author a whole-body tail strike |
| mm8_m608 | Juggernaut | 0.41 | LoMM GOLEMSTONE HAttack; MM9 GIANT or TRELLBORG smash |
| mm6_wyrm | DragonLand | 0.27 | not the MM9 Dragon; MM9 BASILISK RAttack or bite lunge, or author a whole-body lunge |
| mm7_m174 | Cleric Sun | 0.32 | MM9 MONK / EVILSORCERER cast; LoMM player staff or wand |
| mm7_m426 | Warlock | 0.27 | MM9 EVILSORCERER rAttack, LICH |
| mm8_m540 | Ogre Mage | 0.28 | LoMM TROLL or ORC attack; MM9 GIANT; plus a real Cast (part 3) |
| mm7_m274 | Mage | 0.39 | MM9 SCHOLAR / EVILSORCERER |
| mm8_m524 | Serpentmen | 0.26 | none for the body; upper body from an MM9 fighter, tail authored |
| mm8_m536 | Efreeti | 0.41 | MM9 BANSHEE attacks |
| mm8_m416 | Pirate Crossbowman (F) | 0.26 | LoMM player Wattack_Crossbow1 |
| mm8_m568 | Salamander | 0.36 | MM9 BASILISK, or author |
| mm7_m282 | Medusa | 0.28 | upper body from an MM9 caster; tail authored |
| mm8_m500 (+ mm7_m210) | Water Elemental | 0.19 | effect body: author a bigger surge and strike |
| mm8_m600 | Nightmare | 0.24 | MM9 GOAT HAttack1 / RunAttack, adapted to a horse |

(PeasantF1, Merchant and Guard belong to the rebuild stream.)
