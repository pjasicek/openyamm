# MM7 3D batch F: Humanoid monsters and casters

Five MM7 creatures for one Claude session, built one after another in the order below. Other sessions work on the
other batches at the same time; each touches only its own projects. The full batch list is in [README.md](README.md).

## The five models

| # | Creature | Native sprite project | Your project | Monster ids (three tiers) | Status |
|---|---|---|---|---|---|
| 1 | Devil | `mm7_m178` | `mm7_m178_claude` | 220 Devil Worker, 221 Devil Warrior, 222 Devil Captain | installed 2026-10-21 (reduced, `mm7_m178_reduce_claude`) |
| 2 | Goblin | `mm7_m246` | `mm7_m246_claude` | 271 Goblin, 272 Hobgoblin, 273 Goblin Lord | installed 2026-10-21 (reduced, `mm7_m246_reduce_claude`) |
| 3 | Necromancer | `mm7_m294` | `mm7_m294_claude` | 307 Necromancer, 308 Speaker for the Dead, 309 Queen of the Dead | installed 2026-10-21 (reduced, `mm7_m294_reduce_claude`) (covered-outfit deviation, see Open issues) |
| 4 | Vampire | `mm7_m422` | `mm7_m422_claude` | 415 Minion Vampire, 416 Vampire, 417 Elder Vampire | installed 2026-10-21 (reduced, `mm7_m422_reduce_claude`) |
| 5 | Zombie | `mm7_m438` | `mm7_m438_claude` | 427 Rotted Corpse, 428 Walking Dead, 429 Zombie | installed 2026-10-21 (reduced, `mm7_m438_reduce_claude`) |

All projects live under `level_generation/creatures/`. The native projects hold the original frames and the
validated sprite restorations; read from them, do not change them.

Keep the **Status** column of this table up to date (`not started`, `in progress: <stage>`, `exported`, `blocked:
<reason>`). It is the resume point for this batch if the session is restarted.

## How to build each model

Run the creature-to-3d workflow (`.agents/skills/creature-to-3d/SKILL.md`, `CREATURE_TO_3D`) for each creature, one
at a time, and follow the **Claude humanoid NPC playbook** fully (read it before the first model; humanoid:
`level_generation/creatures/CLAUDE_HUMANOID_NPC_PLAYBOOK.md`, quadruped:
`level_generation/creatures/CLAUDE_QUADRUPED_PLAYBOOK.md`). Also follow
`level_generation/creatures/CLAUDE_HD_MASTER_REFERENCES.md` (five HD masters from the native bitmaps before any
Meshy job), `level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md` (one shared texture set, region mask and
per-tier colour ramps from the MM7 palettes, separate 1K head set) and
`level_generation/GAME_ASSET_MODELLING_GUIDELINES.md`. Reference projects: mm6_bar1_claude/, mm6_gob2_claude/
(non-human body) and mm6_pfem_claude/ (cloth skirt).

Devil and Goblin are two-armed non-human bodies: use the mm6_gob2_claude/ rig-first route. Necromancer has a long
split skirt and Vampire a long coat and cape: solve the cloth with the mm6_pfem_claude/ or mm6_gob2_claude/ skirt
approach. Held weapons and staffs are separate attachment GLBs. Necromancer, Vampire and Zombie were blocked by
image-service refusals during sprite restoration, so expect the same risk for their HD masters. If the image service
refuses an HD master or texture request, do not rephrase it to get around the refusal: mark that model `blocked:
refusal` in the table, note the request under **Open issues** and continue with the next model.

Finish one model completely (all clips, gates, textures, LODs, exports, viewer check) before starting the next. Before
any paid Meshy animation, check the animation library first (`anim_library/README.md`) and ingest every paid result.

## Do not install: keep everything in the projects

The user will decide later when these go into the game. Until then:

- Do not run `tools/install_model.py`, and do not write anything under `assets_dev/` or `assets_source/`.
- Do not edit `actors.yml`, model manifests, monster tables or any other runtime binding or table.
- Do not change shared tools, playbooks or skills. If one needs a fix, note it under **Open issues** below.
- Each model stops at accepted project exports: the final GLB, any attachment GLBs, LODs and textures in the project's
  export folder. The project README lists the exact `tools/install_model.py --world mm7 ...` command(s) and the
  `actors.yml` binding you would add, ready to apply later.
- Check visually with `python3 tools/run_creature_review.py --project level_generation/creatures/<project>` (the
  project viewer), including the playbook's gates on every clip.
- An in-game check is optional and only in a private asset root under `output/`, launched with
  `./tools/run_game.sh --isolated <name> --world mm7 ... --assets <that root>`. If that root uses hard links, delete
  the link and write a new file before changing anything, so the real `assets_dev/` is never modified. Note in the
  project README how it was checked.

## When the batch is done

Report per model: export paths, gate results, Meshy spend, and anything left for the user to review. Collect
problems that need the user's decision here:

## Open issues

- **Devil** (`mm7_m178_claude/README.md`, "For the user to review"): hide brighter/more saturated than the sprites
  (ramp gain); tiers A/B walk at 1.42x/1.78x the Mutant walk's natural speed; residual contacts attack 4.5 cm (off hand
  vs tail root) and death 6.1 cm. Not checked in game. User review 2026-10-20 (rolled feet) fixed with batch A's
  `foot_level.py` + `walk_bob.py` (README "Feet and walk fix"): Standing sole roll 6.4/-8.9 -> 0.2/-0.1 deg, walk head
  second difference 1.64 -> 0.83 cm; the walk keeps its heel-up (toe-pad) stance; pending re-review. User review
  2026-10-20 (static attack feet) fixed with an authored lower body (`attack_legs.py`: weight back, lunge step and
  deep crouch into the swipe, rear heel peel, step back; README "Attack feet"); blow 0.750 s; new contact: swiping
  claws 3.9 cm over the stepped foot; pending re-review.
- **Model origin on tailed bodies (affects m418 too):** the Smart Topology import centres the bounding box, tail
  included, so the m178 pelvis sat 0.53 m in front of the origin; the m178 export now moves it back
  (`export_runtime.py`, origin between soles and pelvis). The exported `mm7_m418.glb` (Batch D) still has its pelvis
  0.42 m in front of the origin, so the troglodyte would stand ahead of its actor position in game; worth checking
  before it is installed.
- **Meshy auto-rig on a long-tailed upright body:** limbs usable, but the shoulders came out 22 cm behind the back and
  the spine/neck/head on the chest surface (5 credits, joints used only as a second estimate), as with m418.
- **Tool notes (no shared tool changed):** `tools/run_creature_review.py` shots with focus `head` framed the tail on
  this model; the project's G6 copy counts the tail as body skin (useful here, it found the attack's hand-tail touch).
- **Necromancer (m294): exported with a design deviation.** The first, faithful HD-master request was refused by the
  image service (`moderation_blocked`, output stage, `sexual`, request ID `6bdd504a-b1bf-4362-8462-a83f05029be6`). The
  user overrode the no-rewording rule for this model: the reworded brief (`mm7_m294_claude/references_hd/
  CODEX_BRIEF_v2_primary.md`, a dignified sorceress in a fully covered outfit) passed at the first attempt. The model
  therefore wears an opaque long-sleeved purple tunic with black panels where the native has cut-outs, and black
  leggings; the tier region and texture pattern differ from the sprite. The authorised fallback to the restored
  sheets was not needed. Tier colours re-fitted to the native frames (ramp gains 0.85/0.8/0.2). Attack removed (user review): attacks and spells play the Cast. Review
  items: hands brushing the hanging cape panels; details in `mm7_m294_claude/README.md`. Not checked in game.
- **Zombie (m438)** (`mm7_m438_claude/README.md`, "For the user to review"): built under the user decision of
  2026-10-20 that allows benign rewording after an image-service refusal: `00_three_quarter` corrective regeneration
  refused (violence; the first return was selected by orchestrator override), `02_back` refused twice and taken from
  rewording variant R2 (stains/patches instead of wounds); all prompts and refusals in
  `references_hd/generation_runs.json`. The restored-art fallback was allowed but not needed. Design deviations for
  review: the wounds are Meshy's shapes, re-graded to the native crimson after the coordinator's texture review (tier-B
  white halos around the trouser holes and the headband specks fixed the same day; after the user review the stump's
  four hand-like rods became two broken bone shafts and the held forearm got a ragged rounded wound end with the same
  bones); tier A trousers read greener than
  the sprite's olive;
  the right shin was rebuilt as a lathe (Smart Topology returned only bone rods there); the held severed forearm is
  built from the model's own left forearm, mirrored, and is rigid. Tier C (palette 123) trousers/headband are
  near-black as in the native palette. Walk stride 2.03 m (right foot; the drunk walk drags the left). Not checked in
  game. Tool notes (project copies only): `prop_attach.py`/`make_forearm.py` had to drop mesh deform data copied from
  the body (stale vertex-group indices otherwise skinned the prop to arm bones); `g6_prop.py`/`arm_clear.py` count the
  closed trousers as body.
- **Vampire** (`mm7_m422_claude/README.md`, "Known limits / for review"): the image service refused the corrective
  primary and the front/back/right views at the output stage (`moderation_blocked`, category `other`). Under the
  coordinator-relayed user decision (2026-10-20: benign rewording, at most three variants; restored-art fallback
  allowed) all five views and the head turnaround were obtained (front on the third variant); every prompt/refusal is
  in `references_hd/generation_runs.json`. Design deviation: closed calm mouth in the masters, fangs only as painted
  tips. Also for review: tier C's pure-black cape uses a neutral near-black ramp to keep folds; the death's cape
  crumples under the body for ~0.3 s (cape p99 6.1 lying); Meshy's knees sat on the coat front (moved onto the leg
  mesh, `legs_fix.py`). Not checked in game. Tool notes (project copies only): `robe_sim.py` gained neighbour-midpoint
  and post-smoothing collision passes (`MID_COLLIDE`, `NB_FINAL`), `weights_robe.py` a `hem_z` for coats that end
  above the floor, `caster_timing.py` tolerates a missing Cast clip.
  User review 1 (2026-10-20, README "Revision 2026-10-20"): attack now Mixamo "Standing Melee Attack Downward" (G1 of
  four candidates, impact 0.917 s, no cast); walk-coat light patches fixed (hidden inner coat layer deleted at the
  source, cloth bend limit); raised-arm stretch reduced (attack armpit p99 3.56 -> 2.46, still above the ~2 target at
  the wind-up peak); clasps/buckle copy the coat skin under them (seat drift <= 8 mm). Still open: the belt-end
  'winglike scroll' flaps are Smart Topology geometry (need a remodel), and a few small UV-carry specks on the sleeves
  and lower coat (a fresh 10-credit body retexture of the final mesh would remove them). No new credits.
  User review 2 (attack legs): authored lunge step, hip-led drive and rear heel peel on the claw rake
  (`attack_legs.py`, from the Devil); blow 0.917 -> 0.975 s (binding updated); coat poke at the lunge 2 vertices /
  0.6 cm; armpit p99 2.464 -> 2.467. Pre-change masters kept as `*_preattackfeet`. No new credits.
  Body retexture v2 (user-approved, 10 credits, project total 40/100): Meshy retexture of the final mesh removed the
  UV carry-over specks; tier gains refitted with tier_match (luminance within 5 % of the natives). Head set unchanged.
  Still open: the belt-end flaps (not remodelled), tier C coat less saturated than the native.
- **Installed 2026-10-21 at the user's request** (all five, reduced in `mm7_m{178,246,294,422,438}_reduce_claude/`,
  no retexture, no credits): LOD0 Devil 9,977 -> 6,981, Goblin 10,431 -> 8,603 (sword 630 unchanged), Necromancer
  12,015 -> 9,125, Vampire 10,329 -> 8,093, Zombie 9,499 -> 7,407 (forearm 1,844 -> 1,458). check_winding 0 on all
  seven GLBs; installed with `tools/install_model.py --world mm7`; the staged bindings appended to
  `assets_dev/worlds/mm7/models/actors.yml` (Vampire B/C expanded to full entries). In game (7d16, `debug.actor_spawn_id`
  220/271/307/415/427): all render as 3D, no load errors. The MM6 boss mage demo bound to the shared Necromancer A
  descriptor was unbound the same day (user: a temporary test), so MM7's Necromancer A shows this model.
  Rollback: each reduce project's `work/*_source_pre_reduce.glb`.
