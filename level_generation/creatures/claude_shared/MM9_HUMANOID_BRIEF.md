# MM9 humanoid monster 3D models: common brief (2026-10-30)

Build complete, installed 3D models for MM9 humanoid monsters: Meshy work, rig, MM9 clips, textures, LODs, runtime
binding, viewer, checks. Quality is key: the user reviews every creature closely in the viewer and has rejected warped
hands, poor faces, flat shading, detached parts, smudged textures, stretched mouths and jittering clips. Pass the gates
before you report.

**Read [MM9_ANIMAL_BRIEF.md](MM9_ANIMAL_BRIEF.md) in full first.** Its gates, data and runtime steps, rules and
deliverables all apply here, except for the differences below. These monsters are `MONSTERS.txt` rows, so most already
have a world descriptor: check before adding anything to `mm9_npc_actor_rows.tsv`.

## Route: the approved Yrsa route
- **MM9 skeleton and MM9 clips, never Mixamo.** The user: "we want the MM9 animations on the model". Humanoids stay on the
  original ABC skeleton (`tools/mm9_import_discovery/convert_abc_model.py`) with MM9's own clips and clip events.
- **Hands:** MM9 hands have one finger chain, which warped Forad's first model. Graft five-finger MPFB hands with 15 finger
  bones per side, driven from MM9's finger curl (`finger_alias`). A body whose design has claws, bone fingers or fewer
  fingers keeps that design: build the fingers from the mesh on the same principle (see `mm6_gob2_claude/` for weights by
  connectivity and `mm6_ske_claude/` for bones). Compare with the MM9 model and say what you chose.
- **Head:** a separate 1K head texture set for every body with a face, and a real anatomy check of the chin and jaw (the
  Winged Mutant's chin was rejected).
- **Arms:** hands must not enter the body. Fix with `arm_clear.py`, keep the gesture intent, and run the arm and hand gate.
  Corrections are solved on keys or low-passed, with `hand_rest.py` and `jitter_gate.py` against MM9's clip. Forad's Talk
  was rejected for a constantly jiggling hand and shoulder.
- **Shared scripts and references:**
  - `level_generation/creatures/mm9_yrsa_claude/v2/scripts/` and its README (the approved route);
  - `mm9_forad_claude/` and `mm9_annud_claude/` (the route on male bodies, the face and shoulder lessons);
  - `mm9_imp_claude/` (approved monster on the route: limb fit `fit_imp.py`, fingers from the mesh, held trident with
    `trident_clear.py`, tier parts, and `mirror_glb.py` for true handedness: check your body's handedness against MM9);
  - `level_generation/creatures/CLAUDE_HUMANOID_NPC_PLAYBOOK.md`: read it for the arm and hand gate, cloth, faces and
    pitfalls, but its clip selection is replaced by MM9's clips here.
- **Skins and tiers:** every monster row on the body gets a tier by region mask and colour ramps from the MM9 skins, with
  no per-tier baked base colours. A skin with a different design may need its own region or part. `MONSTERS.txt`
  `Transparent 1` means "use the skin's alpha", not a ghost.
- **Equipment:** weapons held in MM9 are separate rigid parts in the right hand, with the hand solved round the grip (see
  `mm6_bar1_claude/`). Blades follow the swing with no pass through the body or head.
- **Ranged and spell clips:** carry MM9's events to sockets and contact times (see `charge-sockets` in `actors.yml`).
- **Sharp textures from the start:** `uv_atlas.py`, Meshy 4K downsampled once, gentle grade, `texture_quality.py` targets. If a
  fresh paint drifts from the MM9 look, see the look-matching notes in `TEXTURE_QUALITY_PASS.md`.
- Check `devdocs/mm9_rework/MM9_VISUAL_PROPERTIES.md`: glow masks, skin alpha and animated skins are match or gain.

## Budget and limits
- Meshy: up to 40 credits per body without asking, 60 for a pair sharing one agent, only through `tools/creature_meshy.py`.
- Triangle budgets follow the modelling guidelines: reduce LOD0 until visuals or rig suffer; 15k is a ceiling.
- Shared tools change under you: `uv_atlas.py` broke briefly when two agents edited it at once. Add options, default them
  off, and re-read before editing.

## Report
Per body: route and deviations, gate numbers, credits, sheet paths from viewer shots, viewer URL, and anything you looked
at and are unsure of. State plainly what you did not check.
