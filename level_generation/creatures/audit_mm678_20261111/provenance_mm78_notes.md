# MM7/MM8 installed 3D monsters: provenance notes (2026-11-11)

126 GLBs (`provenance_mm78.csv`, one row each). Paths are relative to `level_generation/creatures/`; `file:N` is the
line carrying the claim. Sources are READMEs only; no GLB was measured.

## Currency and the rollback
- Rolled back 2026-10-16, restored 2026-10-18 (`assets_legacy/rollback_3d_20261016/README.md`): MM8 centaur,
  lizardman_peasant, m412, m424, m432, m444, m456, m484, ratman, wolf. Other MM8 models built from 2026-10-18; MM7
  never rolled back (A–L installed 2026-10-20/21, M 2026-10-21; `mm7_batches/BATCH_*.md`). All 126 are current.
- Later passes: floor 2026-10-21, far-LOD repair 2026-10-22, head bob 2026-10-22 (a few), gait rollout 2026-10-31.
- `bound_models.json` says mm7-only for mm8_m508, m496, m528, m492, m612; both worlds bind them (CSV: `mm7+mm8`).

## Routes (counts over 126)
- Mesh: 116 Meshy Smart Topology / image-to-3D from Codex HD masters (playbook route); 4 MM7 copies of an MM8 GLB
  with MM7 palettes (m390 = m552 Thunderbird, m210 = m500, m461 = m480, m434 = m560); 2 MPFB effect bodies (Air m508,
  Fire m496); 1 Blender-built shell (Wisp m528); 2 reused MM6 bodies (mm7_m182 = MM6 cdr1 body/rig/clips + grafted
  MM7 head; mm8_m464 = mm6_mfp_codex re-dressed); 1 older Meshy image-to-3D "standard" body (mm8_lizardman_peasant,
  meshy-7.1, 2026-10-06).
- Rig: 73 source-frame rig with gates (the 5-credit Meshy auto-rig used only for joint estimates); 43 own rigs
  (heat or rule weights); 5 copies; 2 MPFB; 2 reused MM6 (m182 cdr1, m540 on the MM6 Ogre rig); 1 Meshy auto-rig
  skeleton (lizardman peasant, 24 joints + 8 digit bones: `mm8_m400/3d_20261006/claude_20261015/README.md:5`).
- Clips: no model uses paid or Meshy-library animation, except the lizardman peasant: Walk "adapts Meshy's walking
  preset", both attack slots play Walk once (`mm8_m400/3d_20261006/README.md:39-40`), gait Run is library
  "Relax-Run-Forward" (`gait_rollout_20261031/h16/README.md:14`).
  - 85 humanoid-shaped: local library clips (Mixamo Standard/Sword And Shield/Mutant/Zombie/Orc sets, humanoid set
    Relax*/Unarmed*/Armed*) with authored fixes. 41 procedural/authored only: every non-humanoid, plus m182 on cdr1's
    clips ("Motion is procedural and an interpretation of the native frames": `mm7_m258_claude/README.md:75`).
  - One Fly loop covers standing/walk/run/fidget on Wyvern m560/m434 (`mm8_m560_claude/README.md:61`), Bone Dragon
    m616 (`mm8_m616_claude/README.md:31`), Thunderbird m552/Roc m390. Near-identical "Mixamo soldier" set on MM8
    m412, m444, m456, m604, m656 and the MM7 batch A fighters.
- Textures: almost all on the older Meshy route (humanoids 1K body + 1K head set in 2080x1024; non-humanoids 2K base
  on Smart UV + 1K maps; tier ramps from native palettes). 4K texture-quality pass done on 10 only: m616, m500 +
  mm7_m210, m480 + mm7_m461, mm7_m274, m322, m342, m362, m372 (`claude_shared/texpass_mm678/HANDOFF.md:11-18`).
  Queued, not done: 30 in group A, 24 in group B (HANDOFF:57-78). Non-Meshy: m508, m496, m528, m596 (procedural).
- Acceptance: many READMEs still read "User artistic acceptance is not recorded" or "pending user review" (batches
  D, G, L; m492, m564, m572, m286). Batch C was accepted 2026-10-20 (`mm7_batches/BATCH_C_stage/README.md:3`). MM8
  reductions mostly carry a one-word user "ok". Verdicts are quoted per row.

## Older/cheaper routes vs the later playbooks
- Pre-playbook: only mm8_lizardman_peasant (image-to-3D standard, Meshy auto-rig, Meshy walk preset,
  Walk-as-attack): the clearest rework candidate on provenance. Outside the Claude lineage: Codex projects (m548,
  m608) and MM6-body copies (m182, m464).
- Batch-era shortcuts inside the playbook route: rigid hands on casters/robes/monsters (`mm7_batches/BATCH_B.md:84`,
  `mm7_m470_claude/README.md:54`, `mm7_m418_claude/README.md:50`, `mm7_m178_claude/README.md:140`,
  `mm7_m242_claude/README.md:96`); robe deaths kneel onto the side where the native falls back
  (`mm7_batches/BATCH_B.md:81`); Mixamo deaths end knee-up (`mm7_batches/BATCH_K.md:117`); peasants have no attack
  clip (`mm7_batches/BATCH_K.md:109`); Dog/Cat/Chicken attack/hit/fidget are "inventions"
  (`mm7_m509_claude/README.md:97`, `mm7_7m500_claude/README.md:94`, `mm7_7m504_claude/README.md:105`).

## Models whose READMEs admit problems (main claims; full per-row list in the CSV)
- Mesh / Smart Topology fusion: m470 overalls painted on skin (`mm7_m470_claude/README.md:55`); m238 vortex a solid
  spiral (`mm7_m238_claude/README.md:75`); m282 armpits fused (`mm7_m282_claude/README.md:211`); m442 vest fused
  (`mm7_m442_claude/README.md:137`); m504 stone plates only in texture (`mm8_m504_claude/README.md:148`); m234 torn
  membrane faces (`mm7_m234_claude/README.md:88`); m174 hem split (`mm7_m174_claude/README.md:64`); 7m504 wings
  cannot spread (`mm7_7m504_claude/README.md:103`); m432, m624 hair holes (`mm8_m432_reduce_claude/README.md:140`,
  `mm8_m624_reduce_claude/README.md:81`); m430 human face under skull paint (`mm7_m430_claude/README.md:58`); m414
  crumbling death not modelled (`mm7_m414_claude/README.md:143`); m398 falls whole, no bone heap
  (`mm7_m398_claude/README.md:77`); m479 Treant 1155 units tall vs collision 199 (`mm7_m479_claude/README.md:134`).
- Rig / weights: m190 138 vertices on clavicle and thigh (`gait_rollout_20261031/h10/README.md:140`); m596
  claw-to-shin strand (`mm8_m596_v2_claude/README.md:389`); m592 inner-thigh web
  (`gait_rollout_20261031/h22/README.md:117`); centaur hind crease, wrist 70–104° (`gait_rollout_20261031/q4/
  README.md:183`, `mm8_centaur_reduce_claude/README.md:157`); m382 Rat 11.8x hock stretch
  (`mm7_m382_claude/README.md:53`); m230 plates bend (`mm7_m230_claude/README.md:93`); m430 robe armpit 8x
  (`mm7_m430_claude/README.md:43`); m456 anatomy audit FAIL, 356 rows (`mm8_m456_claude/review/ASSESSMENT.md:3`);
  m412 checker FAIL, 488 rows (`mm8_m412_claude/README.md:86`); m418 Meshy auto-rig unusable
  (`mm7_batches/BATCH_D.md:74`).
- Clips / animation:
  - m162 Behemoth: Attack claw into the floor, left open (`claude_shared/floor/README.md:120`,
    `mm7_m162_reduce_claude/README.md:140`); walk bob 8.9 % vs 4.5 % target (`head_bob_claude/README.md:42`).
  - m182: corpse belly-down; motion fits the MM7 frames worse (`mm7_m182_claude/README.md:191-192`).
  - m438 dragging-foot slide (`mm7_m438_claude/README.md:108`); m656 attack unlike the native overhead cut, left
    unchanged (`mm8_m656_reduce_claude/README.md:82`); m420 Walking rises 7.3 cm, not fixed
    (`mm8_m420_reduce_claude/README.md:75`); m472 robe shuffle with no planted phase
    (`mm8_m472_reduce_claude/README.md:147`); m432 sprint limps (`gait_rollout_20261031/h18/README.md:115`); m424,
    m604 Running half a loop out of phase (`gait_rollout_20261031/h18/README.md:124`); m452 Attack hind-leg snap
    left (`mm8_m452_reduce_claude/README.md:112`); m612 Gog chases on its walk at x2.08–2.70, awaiting the user
    (`gait_rollout_20261031/STATUS.md:45`); wolf toe-out 13–22° (`gait_rollout_20261031/q2/README.md:170`); m516
    feet 9–10° (`gait_rollout_20261031/q3/README.md:215`); m294 violent death fall
    (`mm7_m294_claude/README.md:163`); m234 death legs kick up (`mm7_m234_claude/README.md:87`).
  - Open user questions: 7m452 one-handed billhook (`mm7_batches/BATCH_J.md:70`); m422 belt flaps
    (`mm7_batches/BATCH_F.md:130`).
- Fixes that live only in reduce exports (a re-export from production reverts them): m556
  (`mm8_m556_reduce_claude/README.md:82`), m632 (`mm8_m632_reduce_claude/README.md:90`).
- Textures: m386 spotted brass is Meshy paint (`mm7_m386_v2_claude/README.md:260`); m426 skin "clean rather than
  detailed" (`mm7_m426_claude/README.md:121`); m230 hammered stipple (`mm7_m230_claude/README.md:94`); m222 tier
  ramp spill on the neck (`mm7_m222_reduce_claude/README.md:114`); m508 pale in dark interiors
  (`mm8_m508_claude/README.md:48`); m496 layered flame cards, no glow (`mm8_m496_claude/README.md:85`); m616 10
  zero-area UV triangles (`mm8_m616_claude/README.md:131`); m258 atlas 33 %, m278 28 %
  (`mm7_m258_claude/README.md:78`, `mm7_m278_claude/README.md:70`); m352, m332 "probably share the face issues"
  (`claude_shared/texpass_mm678/HANDOFF.md:45`); m342, m372 skirt stretch and knee poke-through (same line); m372
  lip slit is geometry (`mm7_m372_texpass_claude/README.md:298`); m464, m468 darker head textures
  (`mm8_m464_reduce_claude/README.md:92`, `mm8_m468_reduce_claude/README.md:92`).
- Reductions/LODs under gate: Beholder m166 and Robot m386 (`mm7_batches/BATCH_H.md:82`, `:98`); Wisp m528 far-LOD
  notch (`lod_repair_claude/README.md:75`); m624 saved only 9.6 % (`mm8_m624_reduce_claude/README.md:79`); crude
  LOD3 on m218, m230, m479 (`mm7_m218_reduce_claude/README.md:139`, `mm7_m230_reduce_claude/README.md:112`,
  `mm7_m479_reduce_claude/README.md:155`).
- Stale README text: m412 says round 3 awaits review though installed (`mm8_m412_reduce_claude/README.md:185` vs
  `:183`); m394 says LOD0 is 12.6k though halved (`mm7_m394_claude/README.md:124` vs `:15`).
Confidence: 122 rows high; 4 medium (m432, m544, m584, m616: clip sources only partly stated, m616 none recorded).
