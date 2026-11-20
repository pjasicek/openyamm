# Hesper Harrowers — review revision r2, 2026-10-23

The integrator's loader blocker and six visual fixes are addressed. The four-tier viewer is ready, rows 10240–10242
and 10147 are restaged, the scenario-only sweep passes **73/73**, and the requested **hes_d13 desktop smoke passes**
with no `Actor model load failed` or invalid LOD reference in its game log. Artistic acceptance remains with the
integrator under `CREATURE_BUILDS.md` rule 9.

## Assets and review changes

One shared body plus ten rigid attachment GLBs. `integration/actors.yml` retains the four bindings and eleven clips
(twelve since the library attacks of 2026-10-24, below, which replace Attack and Attack2).

| ID | Entry | Scale | Assembled LOD0 triangles |
|---|---|---|---|
| 10240 | Harrower A | 1.0 | 13,016 |
| 10241 | Harrower B | 1.05 | 13,334 |
| 10242 | Harrower C | 1.1 | 13,212 |
| 10147 | Huntmaster Vreth | 1.35 | 14,448 |

Counts include 240 boss-only body triangles hidden on A–C. All 9,408 native body triangles, original weights,
80 native bone frames, tail and sculpted harness remain. Harness mask G uses the skin palette. The source project
and installed MM6 assets were not changed. There are 117 bones including the equipment and cloth chains.

- Solved closed fists against the actual native finger mesh. Handles stay centred in the palm in every clip;
  ivory blade guards form the fist rings at the ends of the segmented gauntlets.
- Blades span about 58.1% of body height for A–C and 62.1% for Vreth. The full convex edge has a 34 mm emissive strip.
- A/C edges are red-orange, B gold-orange, Vreth orange-white. Scalar emission uses strength 3.5 and bloom on the
  blade/plate glow material; cloth cracks use 0.65. No emissive textures.
- Three ivory forearm segments per arm, knee/shin plates and clear wrist/elbow/ankle hinges.
- Thin folded cloth, ragged alpha edges and holes, torn ends and faint cracks; Vreth has alternating ivory/black
  mantle strips. Far-LOD base-colour alpha is preserved.
- Darker, less saturated magenta A and darker crimson B/C/Vreth, using shared textures and four region-ramp variants.

The 18 original `Carbine_*` / `Demon_*` clips retain byte-identical sampler data and remain unbound. The bound clips
are Standing, Walking, Running, Attack, Attack2, Hit, Death, Dead, Fidget, Roar/frenzy and Spent. The accepted native
body motion and Mixamo Standard Run remain. Local library provenance is in the viewer manifest. Walk/run sole-based
strides remain 1.2005 / 2.8114 m; impact times remain 0.525 / 0.425 s. Cloth correctives are baked at 120 Hz.

## Verification and evidence

All eleven clips pass grip, arm/hand, armour, shell, floor and blade-clearance checks. Quarter-frame contact checks
have zero blade/body/head/opposing-blade/cloth crossings and zero hand/other-body crossings. Maximum arm p99 stretch
is 1.7237, hand stretch 3.440, wrist swing 49.234 degrees; body floor penetration is at most 1.438 mm.
Cloth p99 stretch reaches 2.289 during the fall. Actual finger contact has at most 3.065 mm skin/handle penetration,
7.887 mm p10 surface gap and under 0.001 mm handle-centre drift. Evidence: `review/r2/grip_gate.json`,
`review/gates_r2.json`, `review/geometry_r2.json`, `review/armour_gate_r2.json`, `review/shell_leak_r2.json`.
The inherited signed `hand_in_body` diagnostic is not a closed-skin contact test; the triangle audit is authoritative.

`review/validation.json` verifies source anatomy/weights/frames, original clips, variants, texture alpha at every LOD,
loader-valid LOD references and the 15k ceiling. `review/winding.txt`: zero inverted closed parts in all eleven GLBs.
`runtime_finish.py` omits the body's `openyamm_shadow_lods`, so shadows use the normal LOD chain and variant alpha.
The old self-reference is preserved only in the rejected baseline under `work/review_v1/`.

Body LOD counts: **11,244 / 5,598 / 4,460 / 2,777**. The shared repair helpers reduce, unwrap and transfer textures.
The body also uses the same method at LOD1 (50%) to fix the measured LOD1→2 outline pop; far ratios remain 40% / 25%.
A local copy of `transfer_textures.py` keeps RGBA base colour as well as RGBA region masks. Two inverted tetrahedra
created by far-LOD collapse were removed (four triangles each), with LOD0 untouched. `repair_far_winding.py` refuses
larger or near-LOD defects. All four assembled actors pass the normal image limits: worst LOD2 outline 3.5%, colour
6.4; LOD3 outline 7.4%, colour 7.8. See `review/lod_audit.json` and `work/lod_repair/assembly_*/audit/`.

`review/regression.json` / `review/regression.log` record the fresh 73/73 sweep. `review/r2/desktop_smoke.json` and
`review/r2/desktop_smoke/game.log` record the completed D13 run. The authorized launcher ran directly with the requested
arguments while both shared locks were held separately; the outer-flock invocation had no video device. The initial blocker-only restage log is `review/r2/blocker_stage.log`.
Background Blender material reviews are `review/r2/material_*.png`; these are separate from integrator viewer playback.

## Tier colours (2026-10-24)

Skins follow the user's caste table (`design/kreegan_world/MONSTERS.md`, "Kreegan skin colours"):
`prepare_materials.py` takes them from `claude_shared/kreegan_skin.py`, A dusk red `#7b4556`, B bone ash `#a69c88`,
C black `#262024` (highlights lifted), Vreth bone white `#cfc6b0`, measured at 70 % of each ramp on the Trooper A
skin's spread. The harness still uses the skin ramp. Plate, mantle, cloth and glow ramps are otherwise unchanged; they
inherit hes_kreegan_claude's plate refit (at most 5/255, mean ≤ 1.6/255).

Re-run from `prepare_materials.py` through `prepare_viewer.py` (steps 1–4 below) on the existing assembly LOD0s with
the same LOD plan. Every export keeps identical geometry, skins, clips, nodes and images (only ramp extras differ;
pre-change copies in `work/before_tiercolours_20261024/`). The assembled LOD audit scores match the previous run
exactly, `validate_exports.py` passes, winding is 0 inverted closed parts in all 11 GLBs, and the viewer check passes
every tier and clip. `prepare_repair.py finish` now gates only levels 2 and 3; the body's LOD1 rebuild had made it
look up a level-1 threshold that never existed.

## Library attacks (2026-10-24)

The user picked three of the library candidates (FIX_PROMPTS "Harrower attacks from the library"; candidate package,
sheets and viewer in `output/harrower_attack_candidates/`, git-ignored): **A1** for Attack, **B1** for Attack2 and
**C** as a charge strike. Each plays the local humanoid set clip's whole body and both arms (the bound clips before kept
20 % of the mocap upper body and authored the arm paths):

| Role | Source (window) | Duration | Impact (`events`) | Cuts, game s (tips > 25 m/s) |
|---|---|---|---|---|
| `attack_melee` Harrower_Attack | Armed-Attack-Dual2, f0-30 | 1.0 s | 0.5 s (was 0.525) | 0.13, 0.40 (both), 0.50 |
| `attack_ranged` Harrower_Attack2 | Armed-Attack-Dual3, f4-30 | 0.87 s | 0.4 s (was 0.425) | 0.08 (both), 0.17, 0.50 |
| script clip `charge_strike` Harrower_ChargeStrike | Armed-Run-Attack-Dual, f0-24 | 0.8 s | none | weak swing (tips under 14 m/s) |

The engine fits the wind-up [0, impact] to Demon A's contact at 0.5 s, so `harrower_slash`'s cracks (about 0.12 and
0.55 s) fall on the first and the last cut of both attacks. Attack2 starts at source frame 4 because the set clip
begins mid-swing: from frame 0 the ease from Standing snapped the hands at 50 m/s. The charge strike is bound but
unused: the engine plays Walking in a charge dash (`GameplayActorModifiers.cpp`, an engine task).

Chain (`scripts/run_cands.sh`, config `work/cand_config.json`, retargeted sources `work/cand_raw.blend`): `cand_fit.py`
(window, heading, ground, eases, solved grip, helpers, clearance limits), `cand_footlock.py` (planted feet, and a step
where an ease still slides a foot), `cand_armclear.py`, `cand_blade_clear.py` (half frames), `cand_polish.py`,
`cand_contacts.py` (the last armour contacts, measured as `armour_gate.py` does: the upper arm blends toward Standing in
the cross-body follow-through, head roll/pitch, thigh out, spine bend moved to the lower joint), `cand_finish.py`
(floor, tail, skirt and mantle with crescent capsules from tip to tip, cloth fit, root lift), then
`cand_blade_clear.py` again with the simulated cloth as an obstacle. `scripts/run_cand_gates.sh` runs the gates.
`scripts/install_attacks.py` puts the three into `work/final.blend`; `scripts/run_install_attacks.sh` does that and
README steps 1-4 (the previous master, exports, binding and audits: `work/before_attacks_20261024/`).

Gates (`review/*_cand.json`): armour plates pass at 0.3 cm, shell leak none, grip (skin 3.06 mm), zero blade crossings
of body, head, the other blade and cloth on both halves at half frames, floor (body at most 1.3 mm under), arm p99
1.86/2.21 (A1), 1.92/1.74 (B1), 1.71/1.41 (C), wrist swing at most 55 degrees, jerk at 48 fps within the source except
B1's feet (its steps). Left as they are: A1's mantle strip 4 grazes the left thigh 4.6 mm on one frame (Vreth only);
B1's right foot slides 6 cm on frame 3 inside the engine's 0.12 s blend from the previous clip; C slides its leading
foot by design (`footlock: false`, it is played while the actor dashes). At the blows the crescents mostly lead with
their flat (edge cosine -0.4 to 0.1): the set swings a sword edge-first and that edge is our fist-held crescent's flat,
so the convex edge would need a 90-110 degree forearm roll, outside the wrist range.

Exports: only `hes_harrower.glb` changed (30 animations; geometry, nodes, skins and materials identical); the ten
attachments are byte-identical and the four assembled LOD audits score exactly as before. `review/validation.json`
passes, the viewer (`harrowers_attacks_20261024`, twelve clips) passes the headless check on every tier and clip.

## Warglaives (2026-10-24)

The user replaced the fist-held crescents with **warglaives** (FIX_PROMPTS "Harrower warglaives and Vreth's relic
pair"): a twin-bladed glaive held at a centre grip, our own Kreegan design. Concepts
`design/kreegan_world/concepts/monsters/warglaive_{harrower,vreth}.png` (the user picked candidate 1 of both, the
bow and the stepped bow; brief `CODEX_BRIEF_WARGLAIVES.md`). Vreth's pair also drops as the relics **Vreth's First
Cut** and **Vreth's Last Cut** (11438, 11439).

- **Model:** Codex HD masters (`warglaives/<key>/references_hd/`, five views), Meshy Smart Topology on the backup
  account, 5 credits each, **10 of the 20-credit cap** (`meshy/warglaive_<key>_st_v1/`); both shapes right first time.
- **Texture:** `scripts/warglaive_texture.py` (a Harrower-local copy of the ground items' codex_texture.py):
  `prep` puts the mesh in the glaive frame (centre grip at the origin, long axis Z, the glowing concave edge +X),
  scales it to 1.10 / 1.18 m (58 / 62 % of the body, as the crescents), reduces it to 1 420 / 1 190 triangles (the
  family assembly, every tier's gear at once, and Vreth's stay under 15 000) and renders the guides; Codex paints five
  views per glaive (`warglaives/<key>/paint/`); `bake` projects them into base colour, normal, metal-roughness and a
  region mask (ivory, gold, glow); `warglaive_seams.py` finds the painted energy seams and `glow` lays them on the
  surface as ribbons of their own material (the shared HHW glow, scalar emission coloured per tier): 116 / 72
  triangles. `scripts/warglaive_atlas.py` pastes the bakes into two free rects of the shared armour atlas
  (`warglaives/atlas_rects.json`), so the tiers recolour them as the plates.
- **In the hand:** `scripts/install_warglaives.py` puts them on Blade_L/R (the left mirrored through its face), the grip
  on the solved handle centre and axis, and the glowing edge toward the knuckles along the forearm, where the set's
  sword blows move the blade; the grip JSONs carry the glaive frame for the gates.
- **Refit:** `scripts/run_install_warglaives.sh` (backup in `work/before_warglaives_20261024/`, atlas, glaives into
  `work/glaive_base.blend` and the chain's sources, then `run_cands.sh`); `BASE=work/glaive_base.blend
  scripts/run_install_attacks.sh` installs the clips and rebuilds the exports (`run_rebuild_exports.sh`).
- **Gates:** grip (skin 3.06 mm, the grip centre carried by the Blade bone), zero crossings of either glaive through
  body, head, the other glaive and cloth at half frames, armour within 0.3 cm, floor, arm p99 at most 2.21, jerk as
  before. The blows now lead with the glowing edge: edge cosine at the impact 0.78 / 0.80 (A1, was 0.40 / -0.11),
  0.66 / 0.62 (B1, was -0.04 / -0.40), 0.82 on C's right; backhand moments still lead with the spine (the bow is
  one-sided).
- **Exports:** assembled LOD0 14 424 / 14 742 / 14 620 / 14 972 (A, B, C, Vreth); the four actor LOD audits pass;
  validation and winding (0) pass; the viewer passes on every tier and clip.
- **Relic items:** icons from Vreth's front master (`design/kreegan_world/art/item_icons`), ground models
  `warglaives/ground/` (`scripts/warglaive_ground.py`, 160 units, winding 0), grips in `hesper_paperdoll/grips.yml`.

## Reproduction and handoff

The selected editable master is `work/final.blend`; hashes live in `creature_3d_progress.json`. Use a workspace lease
for writes and `tools/run_creature_blender.sh` for Blender. From the preserved v1 master, the review fitting sequence
is `probe_hand_r2.py`, `solve_fists.py`, `apply_grip_r2.py`, `revise_r2.py`, `cloth_fit.py` (revised_r2 → fitted_r2),
`finish_r2.py`, then `polish_r2.py`; copy final_r2 to final. Copy the solved grip JSONs to `work/grip_pose_L/R.json`
before auditing. `armour_texture.py` generates the atlas, including the final torn alpha masks.

1. `export_harrower.py work/final.blend`, `prepare_materials.py`, Blender `build_lods.py`, then `split_models.py`.
2. `prepare_repair.py prepare <stem> <step>` for `review/lod_plan.json`; this includes RGBA transfer and winding cleanup.
3. `assemble_lod_audit.py`, Blender `lod_audit.py assembly_<a|b|c|boss> repaired`, then `check_lods.py`.
4. `runtime_finish.py`, `validate_exports.py`, `viewer_tiers.py`, `prepare_viewer.py`.
5. `stage_registration.py` under the exclusive stage lock; `rebuild_all.sh --scenarios-only`; the D13 desktop command
   in `review/r2/desktop_smoke.json` under shared build/stage locks.

The viewer at `review/viewer/` has four choices (`hhw_a`, `hhw_b`, `hhw_c`, `hhw_boss`), eleven clips, cache-busted
hashes and preserved feedback. The integrator still owns full viewer playback, indoor/outdoor visual acceptance
and showing the revision to the user. No engine/map build, engine code, `assets_dev` installation or git staging.

## Meshy jobs for the integrator

None. Cap **0**, used **0**. All parts are local and the shared body is reused.
