# Hesper Nobles and the Court (Round 4, Claude D)

Rows (design/kreegan_world/MONSTERS.md, `data/make_monster_tables.py`): **10040-10042** Noble A, Noble Duellist B (x1.05),
Court Noble C (x1.1); **10112** the Gatekeeper (x1.2); **10113** Lady Ssekh, **10114** Lord Mraal (grounded), **10115**
Lord Xith (x1.15). Work package: `design/kreegan_world/WORK_PACKAGES/CREATURE_BUILDS.md`, "Round 4". Report:
`requests/P3.md`, "Creature report: Nobles and the Court".

Concepts: `concepts/monsters/fam_nobles.png`, `boss_court_nobles.png` (approved), **`boss_gatekeeper.png`** (made
here, `CODEX_BRIEF_GATEKEEPER.md`; the user approved the pale-gold sheet on 2026-10-24).

## Route

One model for all seven rows, `export/hes_noble.glb` (mesh node `NOBLE`), on the Overseers' published winged Kreegan
body (`source/hes_kreegan_winged.glb`, copied from `hes_overseer_codex/export/`; that project is not modified): the
83-joint rig, native horns and wings, **no tail, no harness**.

| Part | How |
|---|---|
| Carapace | Projected plates on the body (`carapace_spec.py` -> `make_carapace.py`, the Trooper's plate builder; the body's ivory spurs/claws masked out of the projection, `mark_ivory.py`), skinned as a shell (`skin_shell.py`: each plate the mean of the skin weights under it; tabards 0.6 pelvis + 0.2 each thigh), the skin under the plates removed at export. V breastplate, spine plate, belt, front/back tabards, hip leaves, thigh plates, knee shields, greaves, pauldrons with two ivory spikes, upper-arm plates, bracers (the native forearm spurs pass through, the sheet's spiked bracers). Procedural gold/ivory atlas (`carapace_texture.py`), seams as `NB_Glow` geometry |
| Weapons and gear | Codex HD masters (`references_hd/weapons/`) -> Meshy Smart Topology (5 credits each, untextured) -> `weapon_prep.py` (flat side in XZ, scaled, exact orthographic guides) -> Codex paints over the guides -> `register_paint.py` (bounding-box registration, nearest fill) -> `weapon_texture.py` (collapse reduction, front/back planar UVs, orange faces to a per-weapon glow material). Noble fang + holstered sidearm, Ssekh's crescent fangs (one mesh, mirrored for the left hand), Mraal's phase cleaver, Xith's storm caster, the Gatekeeper's Lancer carbine, Bastion Emitter (left forearm; `emitter_search.py`: scale 0.6, turned 15 deg about the forearm, off the carbine and the body) and gorget with the gate seal |
| Rig sockets | `add_sockets.py`: `Grip_R` (the Overseer's fitted round-handle fist, its finger pose in `work/grips.json`), `Grip_L` (its mirror), `Holster_L`, `Palm_L` (spell/bolt release), `Emitter_L`, `Gorget`; release sockets on the weapons (`Tip_Ssekh_R`, `Blade_Mraal`, `Muzzle_Xith`, `Muzzle_Gate`) added by `assemble.py` from `weapons.json` |
| Clips | `build_clips.py` (`clips_lib.py`): the local humanoid set's trunk and arms copied as world rotations onto the source-frame rig over the flying demon's native wings, legs and pelvis (the Overseer clips); arms relative to the chest. Clips chosen in G1 (`review/g1/*.png`). Two-handed weapons: the handle is laid on the library's own right-to-left grip line (`grip_line.py` -> `grip_lines.json`), the left fist put on it by two-bone IK with the minimal hand turn (`support_grip`), released where the library's own left hand leaves (a one-handed sweep). Guns: the gun hand lifted off the carapace (`build_clips.py` `lift`: the wrist pushed along the skin normal until every gun point is 3.5 cm out, recorded in the dry pass, dilated and averaged over +-4 frames, applied by two-bone IK with the hand's rotation kept) Mraal is grounded: the 2Hand Axe set full body, pelvis path scaled to our legs, the lowest toe kept on the floor, both cleaver ends kept above it, wings at rest with a third of the flight's motion |
| Colours | Seven `KHR_materials_variants` (`tier_ramps.py`, user-approved 2026-10-24, `review/proposal/sheet.png`): `nb_a` jade, `nb_b` garnet, `nb_c` midnight sapphire, `nb_ssekh` rose tourmaline, `nb_mraal` obsidian iron, `nb_xith` amethyst, `nb_gatekeeper` steel turquoise (MONSTERS.md "Kreegan skin colours": no caste tier colour reused). Carapace: A antique gold, B bronze gold with scorched ivory, C and the named rows pale gold; seams amber/hot orange (A/B), white-gold (C and the named rows) |
| Death | Burn-away (`death_effect: burn`): burn maps baked for every material from the LOD GLB (`claude_shared/bake_burn_maps.py`; wing rims open and fast, ignition at the head, hands and wing tips) and embedded before the variants; `check_burn.py` gates every variant and LOD |

## Clip sets (one GLB)

| Rows | Prefix | Clips |
|---|---|---|
| 10040-10042 | `Noble_` | Flight (ArmedIdle carry), AttackMelee (SwordAttackR1), AttackRanged (ArmedCastLAttackHand2, palm bolt), Cast (ArmedCastLAOE1), Hit, Death, Dead |
| 10113 | `Ssekh_` | Flight, AttackMelee (ArmedAttackDual1), AttackRanged (ArmedCastRAttack1, a fang flick released at the right tip), Cast, Dive (`script_clips: dive`), Hit, Death, Dead |
| 10114 | `Mraal_` | Standing, Walking, Running (2Hand Axe idle/walk/run), AttackMelee (Attack2), AttackRanged (Attack3 sweep), Cast (Activate), Cleave (`script_clips: cleave`, Attack1), Hit, Death, Dead |
| 10115 | `Xith_` | Flight (2Hand Shooting idle), AttackRanged (FireRifle1), AttackMelee (Attack1 bash), Cast (Activate), ChargedShot (`script_clips: charged_shot`), Hit, Death, Dead |
| 10112 | `Gate_` | as Xith with the carbine (no charged shot) |

Events (`probe_events.py`, `work/events.json`): blows at the fastest tip motion in front of the chest, bolts at the
release socket's furthest forward point, casts at its highest, rifle shots at the library's fire time.

## State and checks (2026-10-24)

Staged in `hesper_stage/monsters.yml` (rows 10040-10042, 10112-10115; height/radius kept at 218/60 so no built map's
placements go stale). `stage.py` exit 0. Desktop smoke (`scripts/desktop_smoke.py`, `review/desktop_smoke.json`):
D6, D7, D8, D11, D12, D16, Out4 load with 0 actor-model errors. `scripts/validate.py` (stage's model rules, clips,
sockets, look keys, loadouts <= 15k: 14.0-14.8k), model cook in a scratch tree, `check_burn.py` (burn image by name on
every variant/LOD), key times, winding (0 inverted), viewer check (7 models x 40 clips, no errors;
`review/viewer_sheet.png`).

**Numeric gates FAIL**, 496 LOD0 rows (658 at the first report; `review/gates/gates.md`, config `gates.json` from
`gates_config.py`). The 2026-10-24 gate round fixed Xith's hit wrist roll (forearm twist 60 % of the hand roll), Mraal's
death under the floor (mesh floor through the fall) and the Gatekeeper's bash (86 -> 49 deg/frame). It also lifted the
guns off the carapace (`lift` in `build_clips.py`, not in the bash) and shrank the Bastion Emitter off the carbine
(`emitter_search.py`), and the support fist now turns at most 24 deg a frame. Left: the library's fast attacks
(rotation steps, accelerations), the six-claw hand stretch, the open-shell arm/prop estimates, upper-arm roll in the
hits and deaths, and Mraal's digitigrade feet against the gate's sole/yaw rules. Tried and dropped: a constant gun turn
against the plates (it aims 40 deg off), elbow-plane continuity in the support IK, and a slower grip blend; none
lowered the bash peak.

Pitfalls met: `merge_head_material.compact` drops textures referenced only from `extras.openyamm_burn_map` (the copied
glow/split/shadow steps use `region_variants._compact`); split attachments carried burn extras without their textures
and crashed the stage's model cook (`strip_attachment_burn.py`); `animation.look` needs `max_yaw_degrees` and
`max_pitch_degrees`.

## Rebuild

From the project folder, inside the lease (`tools/creature_workspace.py claim --project
level_generation/creatures/hes_nobles_claude --identity hesper:nobles ...`):

```sh
LOD_REPAIR_PYTHON=<python with pymeshlab, xatlas, scipy> scripts/rebuild_all.sh clips   # sockets .. bindings
python3 scripts/viewer_tiers.py                                                        # review/viewer/
python3 scripts/stage_rows.py                                                           # hesper_stage rows
```

`rebuild_all.sh` without `clips` reuses the clip blends. Weapons: `weapon_prep.py` -> Codex paint -> `register_paint.py`
-> `weapon_texture.py <name> <triangles>` (see the scripts' headers).

## Meshy (cap 60 credits)

| Job | Kind | Credits |
|---|---|---|
| noble_fang_st_v1, noble_sidearm_st_v1, ssekh_fang_st_v1, phase_cleaver_st_v1, storm_rifle_st_v1 | Smart Topology, untextured | 5 each |
| lancer_carbine_st_v1, bastion_emitter_st_v1, gorget_seal_st_v1 | Smart Topology, untextured | 5 each |
| **total** | | **40** |

Receipts in `creature_3d_progress.json`; returns in `meshy/`. No retexture, rigging or animation jobs.
