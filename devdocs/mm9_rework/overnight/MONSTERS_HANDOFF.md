# MM9 monsters: handoff (2026-10-31)

Run stopped by the user at 91 % of the weekly limit, with all work in progress finished. Start here to pick it up.

- Review page: http://127.0.0.1:8912/level_generation/creatures/claude_shared/mm9_overview/index.html
  (serve with `python3 -m http.server 8912 --bind 127.0.0.1` from the repo root)
- Details per body: [ledger](monsters_ledger.md), `status/monster_<body>.md`, each project's README.
- Rules for agents, with every lesson of the run: [MONSTER_AGENT_BRIEF.md](MONSTER_AGENT_BRIEF.md). Queue and rules: [../OVERNIGHT_MONSTERS.md](../OVERNIGHT_MONSTERS.md).
- State at the end: 23 of 30 bodies installed, binding regression 143 descriptors on 58 models, 0 failed. Meshy 710 of 1,000 credits,
  backup balance 4,075. No leases, Blender or orphan Chromes of this run left.

## 1. Bodies
| State | Bodies |
|---|---|
| Accepted by the user (23) | dwarf, nosferatu, lizardorc (r15), trellborg (r10 cuffs, "fine I guess"), skeleton, banshee, thrall, evilsorcerer, ghoul, gezzampt, monk, mummy, ghost, honk male, honk female, guard, troglodyte, highwayman, clansoldier, nobleman, dookmilitia, bigfoot, zombie |
| Not started (7) | giant, yanmir, lichking, colloidalwarrior, stage1demon, njam, ebora |

## 2. Known defects by body
Not finished, gates failed, mostly because the agents stopped at the limit:
- **lizardorc:** r15 took the skin off the breastplate (`plate_fix.py`): top edge is a plain cut, wavy stripes under the neck-side patch, pale streaks on the neck hide, orange flecks in the chest mail. Read in Standing only. r13 fixed the neck, doubled body density (693 -> 1386 texels/m, two 2K pages, +7 MB colour; the right side now mirrors the left's paint) and the grip. Plates still in thighs: Walking 1.7, Running 3.3, AttackMelee 6.1 cm. Rectangular chest plate edge not clipped. Fidget R fist 5.5 cm into its tasset, AttackMelee 2.5 cm. Blade against thigh not rerun. Crease under the chin. 5 jitter flags, 3 detached flags unread. Floor -9 is the cutlass tip, all three bindings still flagged by the audit. Strips and in-game are from r12.
- **bigfoot:** hands in the body in Fidget2, Taunt, attacks, Hit2 (up to 6 cm, capped). 19 jitter flags. Got one gate run. Check the hard-edged saddle on tier B's back
  (the compare sheet shows it; r6 softened it, seen in one shot) and the Yeti's blue chest patch.
- **dookmilitia:** cheek bar flagged 5.0 cm; Cower hilt through the head 5.6 cm; floor Running -4.5 against 2.5. No in-game run at all. Strips and close-ups not read.
- **dwarf:** r14 fixed the fan and the beard stretch. Upper skirt bunches into a shiny roll under the belt in Running and AttackMelee. Thighs through it: AttackMelee2 2.5 cm, Death2 2.4 cm. Axe in upper arm 6 cm+ in Fidget; helmet rim in shoulders. Collapse, arm, jitter, grip and in-game checks not rerun on r14; arm corrections may now be too big.

Open after fixes, judge by eye:
- **guard:** red-brown shards in the outer eye-window corners, cheek plate streaks, dark patch under the chin. Fist fingers wrap but read straight across in places. L hand in AttackMelee2 4.0 cm, AttackMelee 3.2 cm.
- **clansoldier:** skirt hangs, but thighs pass it: Running 4.0 cm, Walking 1.4 cm, Death 7.5 cm. Other gates not rerun on r22, older sheets show the old skirt. Shoulder holds in Walking may be too big now.
- **honk female:** right cuff sliver, right forearm reads as a pointed tip from below, left cuff spike, dark lining lines on the robe.
- **highwayman:** cheeks smoother than the face front, hair ripples and a collar of hair under the jaw. Floor Running -2.7 against 2.5.
- **nobleman:** forehead crease, jaw corner nicks, Viscount's smile wider than the mesh mouth, shoulder folds, reptile scale paint under the arm.
- **troglodyte:** neck folds with the head thrown back (96 faces), small nub on the jaw rear rim. Most gates not rerun on r13.
- **nosferatu:** r16 redraws the sleeve from shoulder to elbow as a straight tube, like MM9's (`scripts/tuck_sleeves.py`, run after finish_nos.py; it keeps its input as `work/*_pre_tuck.npz`). Cloth, collapse and in-game checks not rerun. Pale wrist patch at the cuff edge with the arm raised (AttackRanged), seen, not fixed. The baked AO still holds the old puff's crease.
- **trellborg:** r10 cuffs: the hand passes the lip at extreme wrist bends (R AttackMelee2 12.6 cm, L Fidget 10.4 cm, L Running 5.2 cm), paint steps at chart seams, 13 and 9 open edges hidden under the cuff, cuffs not seen in game. r5 wrists and fists. Finger webbing runs 1.9 cm inside the handle (hidden). Fidget2 L hand 6.0 cm, club in skin 5.7 cm. Collapse, floor, club gate and in-game not rerun on r5. Forehead smudge on tier C, flat orange skin, smeared wedges at the neck. Tone not compared with MM9.

Every body: nobody watched playback at normal speed (agents cannot watch video). LOD1-3 were barely looked at. Few ran on a map that places them.
My own reads of contact sheets missed doubled faces on three bodies. The user catches what small sheets hide, so read heads at full size.

**Snapped joint offsets (found 2026-10-31 on the dwarf, Standing frames 19-21):** every project's copy of `clips_mm9.py` cuts small joint offsets with `np.where(np.abs(off) > 0.004, off * k, 0.0)`, so a slow drift crossing 4 mm pops by 0.4 cm x k in a frame or two. Fixed in the dwarf's copy only, with a soft threshold. 23 copies carry it. A scan of translation channels flags pops on many bodies, but it also catches real fast moves: worst Clavicle or Thigh entries are nobleman AttackMelee 0.68 cm, thrall AttackMelee3 1.08 cm, guard AttackMelee2 0.84 cm, yrsa Hit 0.83 cm. Use the soft line in new bodies, and rebuild an accepted body only if the user sees a pop.

## 3. Follow-up work, in suggested order
1. Done: zombie head graft (r15).
2. **Head audit.** Silhouette-fit projection doubled faces on guard, highwayman, gezzampt and nobleman. Read every remaining head at full size, front on.
3. **Dropped clips.** Clips are basically free (0.8-5 MB of a 17-63 MB GLB). Add the rest as `script_clips`, with no gate polish on clips nothing drives. Source/installed:
   honk male and female 21/10, clansoldier 23/19, mummy 22/18, banshee 17/14, skeleton 17/15, zombie 18/16, troglodyte 18/16, gezzampt 17/15, highwayman 21/20, nobleman 15/14, bigfoot (5 left out).
   Counts include a bind pose, and installed counts include an added Dead, so trust the Honks most. Later bodies were told to carry everything.
4. **Finish lizardorc, bigfoot, dookmilitia, dwarf** (section 2).
5. **The 7 unstarted bodies.** Use the brief; 20-30 credits each is normal on one texture set.
6. **Sleeping guards in Kluso's House.** `sleep` is on the guard now (a nap on his feet). `KlusosSleeper.scr` loops it on UpperSleep0-7 from map start, with waking on the Blackheart or damage already done (`dormant`). Add a small actor behaviour that loops the clip until woken.

## 4. Decisions
Made by the user or on the user's word, 2026-10-31:
- **Tiers where MM9 has one look** (dwarf, lizardorc B and C): keep ours, decided by the orchestrator on the user's word: distinct rows read better in play, and it is ramps only, so it reverts cheaply.
- **Sleeping guards in Kluso's House:** leave alone for now; house scripting is separate.
- **Blended order, engine:** done in part. `ModelRenderer` now sorts a blended skinned primitive by where its main joint carries it this frame (`anchorJoint`), which covers ghost and banshee limbs and the ghost's flying head. Not looked at in game. A primitive still sorts as one piece, so a blended depth prepass would be the fuller fix. Blended geometry still casts no shadow.
- **Upload only the tiers on a map:** not done. The user said do it if easy, and it is not: `prepare()` builds every material's textures per asset ahead of draws, off-thread preparation included, so it needs a variant list from both world loaders plus late spawns, or an upload hitch at first draw. In ModelRenderer.cpp's `prepare()`, near `textureFor`.
- **Bone audit, checked against MM9's raw clips:** native on guard, mummy, lich, honk male, gezzampt, nobleman. **Ours on thrall, skeleton, skeleton warrior** (raw 0 stretching), hips sliding 2-5 cm from `mirror_source.py`. All three are accepted and look fine; rebuild only if a hip reads wrong.

Done on the user's OK, 2026-10-31:
- **Banshee flies:** `SCRIPT_FLYING_SOURCES` in the table generator. MM9's row has Fly 0, but her script flies her.
- **Banshee decay:** tiers stay, no skin switch.
- **Clan Soldier melee only:** `MELEE_ONLY_SOURCES`. MM9's rows do list Axe and FireAr; basemelee.scr with AttackRange 60 never throws them, and the model has no throw clip. `attack_ranged` is still bound to Hattack2 in actors.yml, unused now.
- **Town Guards bound:** rows 107-110 as `MM9 10x Town Guard`, on the guard A and C, Half Orc A and Horde B bodies. No converted map places them yet (policeman.scr).

## 5. What to reuse
- Faces: `mm9_highwayman_claude/scripts/project_head.py` and `mm9_nobleman_claude` (landmark placement, one source per feature). `mm9_guard_claude` (layered paint with a z-buffer).
- `claude_shared/bone_length_audit.py`, every build. Never `mirror_source.py` on an asymmetric bind: use `mirror_glb.py`; `mm9_highwayman_claude/scripts/rerest.py` for a frozen rig.
- `mm9_evilsorcerer_claude/scripts/collapse_gate.py` reads all primitives. The cat's reads only the first.
- Grips: `mm9_highwayman_claude`. Child models: `merge_child.py` (HIGHWAYMAN, DOOKMILITIA and PHANTOM link FIGHTERBASE.abc). Hip pivot: `ORBIT` in `mm9_ghoul_claude/scripts/`.
- `viewer_shots.mjs` now kills its Chrome on a signal. Those leaks took the load past 300.
- Agents: kill literal verified PIDs only. A stalled agent looks "running": compare file times per project. Run at most 6.
