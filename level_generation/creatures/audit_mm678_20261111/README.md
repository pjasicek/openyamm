# MM6–MM8 3D monster audit (2026-11-11)

Every installed MM6–MM8 monster model (185 GLBs bound in the three worlds' `models/actors.yml`) measured for texture,
mesh, rig deformation, hand contact and animation energy, against the 114 installed MM9 models as the reference.
Nothing was changed in any model or binding. The user asked for the audit after noting that MM9's LOD0 models,
textures, rigs and clips look much better, and that the MM6 female peasant's hands and the MM6 Titan's attack hand
are bad.

Ranked table: `scores.csv` (and `scores.json`); measurements per model: `motion/<stem>.json`, `texq/<stem>.json`;
history per model: `provenance_mm6.csv`, `provenance_mm78.csv` with their `*_notes.md`; donor options:
`options_mm9_lomm.md`. MM9 reference: `motion_mm9/`, `texq_mm9/`. The CSV and JSON files are git-ignored
(`level_generation/.gitignore`); rebuild them with the commands under Method.

## Findings

1. **Textures are the largest and cheapest gap.** Atlas use (largest body set) median 41.8 % against MM9's 57.7 %;
   surface on UV fragments 9.8 % against 0.85 %; only 27 of 185 reach 55 %. By the texpass group rule
   (`claude_shared/texpass_mm678/HANDOFF.md`) 47 models are group A and 35 group B; the pass has been done on 10.
   Cause and recipe as MM9: 2K paints on Meshy or Smart UV layouts with the old grade, against 4K paints on
   `uv_atlas.py` layouts with the gentle grade ([TEXTURE_QUALITY_PASS.md](../claude_shared/TEXTURE_QUALITY_PASS.md)).
2. **Attacks are slower and stiffer than MM9's.** Bound melee attack, medians: bipeds peak speed 3.6 against 5.9
   heights/s, torso turn 48 against 63 degrees, clip 1.5 against 1.0 s; other bodies reach 0.24 against 0.33 heights,
   moving share 74 against 96 %, speed 2.9 against 4.5. 47 of 157 attacks are under 60 % of the MM9 median of their
   body type, 20 under 45 % (pfem, mer1, mfp, gua, m475, m386 Robot, m608, wyrm, m174, m426, m540, m274, m524, m536,
   m416, m568, m282, m500 / m210, m600). Frame strips confirm it: MM6 Guard and MM8 Ogre Mage swing one arm on
   straight legs where MM9's Guard and Dwarf lean, bend and lunge. 17 peasants play Standing or Walking as their
   attack (the native peasant attack reuses the walk frames, `mm7_batches/BATCH_K.md`).
3. **Robes and skirts tear in the gait clips** added on 2026-10-31 (cloth region over 20 % bad beyond Standing):
   mfp Jog/Sprint (the skirt balloons into an egg), m484 Minotaur Jog/Running/Sprint (holes in the kilt), m430 Wight
   **Walking** (long stretched robe sheets), sor1 Jog and Walking, m472 Run2, m290 Jog/Sprint, mnk1 Run2, thf Sprint,
   m170, m294, m460 Jog.
4. **Hit reactions stretch torsos** (spine/head/arm region 18–42 % bad beyond Standing) on about 20 bipeds: m294
   Necromancer, m190 Dwarf (chest and beard crumple), kni (neck tears), m342, m302, m476, m475, wdm, pman_v2, gob2,
   m290, m262, m444 and others.
5. **Hands.** Hand vertices inside the body: m456 Dragon Hunter **Walking** (62 %: left hand inside the thigh), pfem
   Hit (46 %), ratman Running (8 %, chest crushed), m488 Attack (7 %). Rigid hands without finger bones: Guard,
   Titan, Thief, Werewolf, Cleric, PeasantF2. Weak at rest (`handsheet.py` sheets): pmn2 (right hand a lump), thf
   (mittens), gob2 (blobby, four fingers), lizardman peasant (spiky), m475, lzd bow hand, fists that crumple on
   m484, m540, m190, m154. The Titan's Cast collapses the left shoulder and armpit at 1.6–2.05 s and the hand then
   sinks into the belly; the README records rigid open hands (`mm6_ttn1_claude/README.md:101`), Discord OY-27.
6. **Clip faults:** Running loop jumps 10x its frame step on m464 (Vampire Female Peasant), Walking loop jumps 2x
   on m242 Ghost; Attack and Cast are one clip on m540 Ogre Mage, mep, lzd, m182, m544; the Unicorn m544's Hit equals
   its Standing (no hit reaction); one loop for standing/walk/run on m182, wyrm, gst, m548. Floor: only the Behemoth
   attack sinks (known). Gait: only Fighter Leather (user's choice) and Gog (open).
7. **Legacy routes still installed:** Meshy auto-rig on demon, pmn2, gua, cle, thf, ttn, wwf (MM6, Oct 6–9); the
   lizardman peasant (image-to-3D standard body, Walk as attack); Codex installs with failing gates or QA hold:
   lch, mer1, min1, kni, arc1, figc, mep; placeholder status: wwf, ske, gob2, cle, dru1. LODs are fine apart from
   the effect bodies (fie1, aie1, m528, m508).

## Recommended focus

1. **Texture pass**, group A then B, from the queue in `texpass_mm678/HANDOFF.md`. No rig work, 10–20 credits each.
2. **In-place clip and weight fixes** for findings 3–6 (cloth chains in gait clips, Hit spine weights or a gentler
   Hit, m456 Walking arm clearance, pfem Hit, the two loop pops, Titan Cast shoulder).
3. **Re-animate the blandest attacks** (finding 2) from donors: MM9 clips where the anatomy matches, LoMM clips
   (`options_mm9_lomm.md`), else more energetic library clips with legs and torso.
4. **Rebuild** where model, rig and history all fail: pfem (user rejected), lizardman peasant, mer1, thf, gua, wwf,
   and the Titan's hands (LoMM TITAN is a donor).
5. **Pilot the donor route** on one MM9 skeleton (Wyvern for m434 = m560) and one LoMM skeleton (Bat or Harpy) before
   queueing families.

## Method

Run from the repository root; every step needs only Python (numpy, scipy, PIL, yaml), no Blender.

```sh
A=level_generation/creatures/audit_mm678_20261111
T=level_generation/creatures/claude_shared
cat $A/glbs.txt | xargs -P 12 -I{} python3 $T/motion_audit.py {} --out $A/motion          # 3-4 min
cat $A/glbs.txt | xargs -P 16 -I{} sh -c "python3 $T/texture_quality.py {} --by-bone --json $A/texq/\$(basename {} .glb).json"
python3 $A/aggregate.py && python3 $A/score.py
```

- `claude_shared/motion_audit.py`: per clip on LOD0, linear-blend skinned at 30 fps. **Deformation**: per triangle
  the singular values of the in-plane map from the bind triangle (stretch > 1.6, squash < 0.55) and folds (normal
  turned over 90 degrees from the dominant joint's rigid motion); the share of each body region (from joint names)
  bad in its worst frame, compared with the same model's Standing. **Hand contact**: hand vertices more than 0.02 H
  behind the nearest torso, head and leg surfaces. **Motion** from the first frame: p90 reach, moving share
  (> 0.05 H), peak p95 vertex speed, torso joint turn; loop gap; near-identical clip pairs.
- `claude_shared/motion_frames.py` and `sheet.py` render flat-shaded frames with the bad triangles red;
  `handsheet.py` renders both hands of every biped at rest. About twenty flagged moments were checked this way
  before they went into the findings; the Reactor's unfolding arms (scale-animated) were a false positive and are
  now skipped.
- `score.py`: severities 0–3 per dimension (thresholds in its docstring), priority = sum (known issues x 0.8).
- Not covered: the look of the paint itself (only its layout), faces, held weapons (separate GLBs), in-game
  lighting. The motion ratio compares with MM9 medians, not with each native sprite; slow is sometimes intended
  (a robed caster). A region percentage can overstate a few large triangles on a small region; read the frames.

## Fixes and re-measurement (2026-11-11)

The findings were fixed the same day by agent streams. Their briefs and ledgers are in [fixes/](fixes/COMMON.md), and
each change has a one-copy revert in its project's `work/before_*`. `aggregate.py after && score.py after` scores the
re-measurement in `after/` (motion and texture of all 185 models after the fixes).

| Measure | Before | After |
|---|---|---|
| Atlas used, median | 41 % | 53 % |
| Models at 55 % or more | 23 | 68 |
| Fragments, median | 9.9 % | 4.9 % |
| Texture group A/B | 82 | 17 |
| Attacks under 45 % of MM9 | 20 | 1 |
| Deformation severity 2–3 | 18 | 9 |

- **Texture:** 66 retextured, 9 skipped (900 credits).
- **Clips:** cloth on 8 models, Hit folds on 17, loop hitches, Behemoth, Unicorn, the m190 reweight.
- **Attacks:** the 16 blandest re-animated.
- **Rebuilds on MM9 donor skeletons and clips:** Guard, PeasantF1, Thief, Merchant, lizardman peasant, Werewolf; the
  Titan got five-finger hands.
- **Actors suite:** 191 passed, 2 failures not caused by this work (MM9 map actors, the out05 quest event).
- **Still open:**
  - m472 and mnk1 Run2 robes (re-author in their own projects);
  - the Guard's Walk2 skirt (17 %);
  - the Demon Queen and zUltra Dragon textures (left on purpose);
  - user review of the PeasantF1 and Merchant faces and the Guard coif.
