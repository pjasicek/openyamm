# Hesper Kreegan Troopers (hkr)

Kreegan Trooper A/B/C: 10010 Trooper, 10011 Veteran Trooper (x1.05), 10012 Spire Guard (x1.1)
([MONSTERS](../../../design/kreegan_world/MONSTERS.md), `design/kreegan_world/data/make_monster_tables.py`). Concept
`design/kreegan_world/concepts/monsters/fam_troopers.png` (`references_hd/concept.png`), castes
`concepts/07_kreegan_castes.png` (`references_hd/castes.png`).

User direction: one Kreegan body reused consistently, castes differing only by add-ons (armour, scale, weapons); the
body is the MM6 Demon, the winged castes the MM6 flying demon. **No Meshy credits** (0 of the 80-credit cap): the body
is the installed MM6 Demon, every add-on and the carbine are built locally. Not installed: the Hesper stage integrates
the exports; `integration/actors.yml` is the binding draft.

Review: [viewer](http://127.0.0.1:8912/level_generation/creatures/hes_kreegan_claude/review/viewer/) (tiers A/B/C, every
clip; `python3 tools/run_creature_review.py --project level_generation/creatures/hes_kreegan_claude check`),
`review/tiers_abc.jpg`, `review/tiers_before_after.jpg`, `review/attack_vs_concept.jpg`, `review/clips_v3.jpg`,
`review/shots/` (captures before the armour work in `review/before/`).

## Reusing the Kreegan body

| Body | Source (copied into `source/`, the MM6 projects and installed models untouched) | Castes |
|---|---|---|
| ground | `assets_source/worlds/mm6/models/mm6_demon.glb` (`mm6_demon_reduce_claude/`) -> `source/mm6_demon_source.glb` | Drudge, Brute, Hulk, Hatchling, Trooper, Veteran, Spire Guard, Lancer ranks |
| winged | `mm6_wdm.glb` (`mm6_wdm_claude/`, `mm6_wdm_reduce_claude/`) -> `source/mm6_wdm_source.glb` | Overseer ranks, winged bosses (not built yet) |

The shared body (`export/hes_kreegan.glb`, mesh node `HKR`) is the demon's LOD0 (9,060 triangles, its own 2K
materials and UVs) plus two ivory horns rigid on the head (`add_horns.py`, concept), on a source-frame `B_*` rig built
on the demon's own joints and weights (`build_rig_hkr.py`, fingers by connectivity, torso weights, curled fists with
grip tunnels). It carries the carbine clips (`Carbine_*`) and the demon's own clips on the same rig (`Demon_*`). Tier
colours are `KHR_materials_variants` (`hkr_a/b/c`) from the demon's region mask (R skin, G harness) with authored
ramps (`tier_ramps_hkr.py`, no native palette): A violet, B slate blue, C black crimson (since 2026-10-24, see
"Tier colours").

A caste is either
- **the bare body + rigid add-ons**: `export/hes_kreegan.glb` with attachments, one GLB per joint
  (`export/hes_kreegan_<part>.glb`, `split_attachments_hkr.py`), each with the same three variants so it inherits the
  carrier's tier by name (Drudge bare; Brute, Hulk later); or
- **a caste GLB with a skinned shell**: the same skeleton, bone names, head and clip sets, the body mesh bulked for the
  caste (`bulk_body.py`; the bare GLB keeps the thin Demon), a skinned armour shell in its skinned mesh with the skin
  under it removed, plus rigid add-ons for the small parts. Trooper now (`export/hes_kreegan_trooper.glb`), Lancer
  ranks later (their own bulk and shell spec on the same route).

| Caste | Model | Add-ons (per-descriptor `attachments:`) | State |
|---|---|---|---|
| Drudge | `hes_kreegan.glb` | none (bare) | body + `Demon_*` clips ready; needs its own skin variants |
| Brute | `hes_kreegan.glb`, x1.15 | scrap-plate shoulder | to build |
| Hulk | `hes_kreegan.glb`, x1.3 | grafted slab armour | to build |
| Trooper (A) | `hes_kreegan_trooper.glb` (bulked body) | shell (barrel cuirass, abdomen and back lames, belt, two tassets, full thigh plates, knee caps, greaves, upper-arm plates, forearm guards) + rigid crest, pauldron caps, spikes, buckler emitter, pulse carbine | **done** (bulky v4 2026-10-22) |
| Veteran Trooper (B) | `hes_kreegan_trooper.glb`, x1.05 | as A with the black carapace caps (`carapace_l/r`) in place of the ivory caps | **done** |
| Spire Guard (C) | `hes_kreegan_trooper.glb`, x1.1 | as A; gilded shell and caps, white-gold glow | **done** |
| Lancer ranks | a caste GLB with a heavier shell | + ion lance | to build |
| Overseer ranks | winged body | pistol (+ rod, sash for the higher ranks) | to build on the winged body |

Armour material: ivory chitin-ceramic, gold edges, orange-glowing seams (`make_armour.py` from
`scripts/armour_trooper.json`, written by `armour_spec_v3.py`; atlas `armour_texture.py`): `HKR_Plate` with the
armour region mask and ramps (A ivory, B scorched ivory + bronze, C gilded), seams and studs `HKR_Glow` with a per-tier
`emissiveFactor` only (`glow_variants.py`: orange A/B, white-gold C; no emissive texture, which the cook does not
accept). Carbine: bone stock, amber resin receiver, orange glow core, lens and bore (`make_carbine.py`,
`carbine_texture.py`), joint `Rifle` (child of `B_R_Hand`), muzzle socket `Socket_Muzzle`.

**Engine needs (listed only, no engine work):** none (skinned meshes with material variants, rigid attachments and
sockets exist; the seam glow uses `emissiveFactor`, so the coming emissive support for skinned actors is not needed).

## Bulky Trooper caste (v4, 2026-10-22, user-approved)

History: v1 rigid plates (`review/before/`), the rigid armour pass (v2, `armour_spec_v2.py`), the first skinned shell
(v3, `armour_spec_v3.py`; it still read as a thin Demon in light bands). v4 makes the concept's bulky soldier on the
same skeleton, bone names, clips and head (`rebuild.sh tail`):
1. `leg_limit.py`: Running's knee drive soft-limited (hip flexion above 60 deg continues at 30 %: 88 -> 68 deg).
   At 88 deg the raised thigh's front rose above the belt, so no tasset or thigh plate could clear it; an armoured
   run with a lower knee drive. The other clips stay under 47 deg and are untouched.
2. `bulk_body.py` (Trooper only; the thin rest shape kept as `thin_co`, restored by `export_hkr.py MODE=base`): the
   rest mesh inflated along its normals by per-bone amounts blended with the skin's own weights and smoothed over the
   mesh: upper chest 2.4, clavicles 2.2, lower spine 1.2-2.0, pelvis 1.6, neck base 1.2, upper arms 2.6, forearms 1.4
   fading to the wrist, thighs 3.2, calves 2.0 fading to the ankle (cm); the arms bulk outward, 35 % on their
   body-facing side (the supporting arm crosses the cuirass); head, hands, feet, tail untouched; loose pieces ride
   their skin. Weights, joints and fists unchanged.
3. `armour_spec_v4.py` -> `make_armour.py` -> `skin_shell.py` (as v3: constant weights per piece, the skin under each
   piece removed in the Trooper export): a barrel cuirass (chest and back plates on one Spine2/Spine1 weight set,
   2-2.8 cm off the bulked chest, rounded lower edge; cut back on the supporting-arm side), two abdomen lames on the
   spine, a lower back lame, a centre belt, **two tassets riding their thighs** (over the upper thigh front and side;
   a central tasset met the raised thigh plate, a belt-hung hinged tasset could not clear the thigh's front), **full
   thigh plates** over the front and sides below them, knee caps, greaves, upper-arm plates, forearm guards (the
   right one with the stock gap). Larger caps (7.5 cm off, wider) and spikes (x1.12), tier B's carapace to match.
4. Pose fixes: `armour_clear.py` (the held gun pushed forward out of the cuirass, belt, lames and leg plates; the hand
   test now also catches a plate inside the fist when the belly is the nearest skin), `death_unfold.py`.
5. Emission (`claude_shared/emission.py`, last runtime step): the seam, stud and carbine-core glow materials emit with
   bloom, colour per tier in the factor (orange A/B, white-gold C; strength 1: a larger strength clipped the colour).

Silhouette (`silhouette_ratio.py`, Standing): shoulders across the pauldrons / hips with the leg plates, the arms
left out of the hip band. Concept front and back views: 1.15 (169 / 147 px). Trooper v3 1.50 (0.75 / 0.50 m),
v4 1.39 (0.81 / 0.58 m): the hips grew most (thighs, tassets, thigh plates); the concept's 1.15 comes from its wide
stance and very broad thigh armour, which the clip's stance does not reach.

Iteration: `armour_iter.sh` (bulk + plates on the final clips, the gun push, every gate in about two minutes),
`gate_worst.py`, `hip_flex_probe.py`, `dbg_plate_in_skin.py`.

## Clips (two-handed carbine on the demon rig)

The demon's claw clips cannot hold a gun, so the carbine clips are retargeted (world-rotation copy) from the local
humanoid set `anim_library/humanoid_set/2Hand Shooting.glb` and the Mixamo library: Standing (2HandShootingIdle, low
ready), Walking, Running (RunForward), Attack (FireRifle1; the shot at 0.367 s), Hit (GetHitF1, feet pinned), Fidget
(IdleAlt: raises and sights, lowers), Death (Mixamo Dying Backwards, travel halved), Dead (last Death frame held 1 s).

Chain (`TOK=<lease> scripts/rebuild.sh [rig|anim|tail]`, about 10 min): retarget -> fists -> carbine fit/seat -> timing
-> carbine drive (level in roll) -> left fist on the handguard (`support_hand.py`) -> reach fix -> pauldron/buckler
helper bones -> plates -> clearance (`armour_clear.py`, carbine and both forearms out of the plates/body) -> ground and
feet -> corpse floor -> Running's knee drive limited -> helper bones -> caste bulk -> plates -> shell weights and hidden skin -> clearance ->
ground and feet -> death spine eased out of the cuirass ->
corpse floor -> twist bones -> shell weights again -> locomotion foot floor -> tail motion -> armour, shell stretch and
shell leak gates.

Corrections of 2026-10-22 (resume after the interrupted run):
- **Left wrist 106-120 deg -> 2-28 deg.** The support fist's grip tunnel took the source hand's direction along the
  barrel; on the demon's long hand that pointed the tunnel the wrong way and locked the arm straight. The tunnel now
  runs toward the stock (`BAR_SIGN=-1`, thumb forward), with the roll searched over the full circle (circular
  smoothing) and the elbow plane +-60 deg; the elbow bends (reach 0.87 instead of 1.0) and the left arm's jerk fell
  from 54 to under 9 deg per frame.
- **Run foot through the floor (-9.8 cm between keys) -> -1.4 cm.** `foot_floor.py` chose each frame's pitch alone
  (heel-down and toe-up alternated, 78 deg in one frame at the loop seam); the pitch is now one Viterbi choice over the
  clip (depth, lift-off and pitch change; the loop closed, `CYCLIC=1`).
- **Corpse 45 cm in the air -> on the floor.** `death_floor.py` counted the stiff source tail and the held gun; it now
  rests the body without them, `tail_anim.py` drapes the tail (`FLOOR=0.07`), and `death_carbine_floor.py` (from
  `hes_guard_reduce_claude`) turns the carbine out of the hands onto the floor from the moment the pelvis has fallen
  halfway (Death 1.65-2.15 s, laid in Dead).
- Hit: the left forearm guard went 4 cm through the belt and thigh; `armour_clear.py LEFT=1` moves the gun and both
  hands together. Buckler moved toward the elbow (v 0.38, R 0.12: the bent fist pierced it by 2.9 cm).
- `armour_gate.py`: plate-in-body parity with 1.2 m rays (0.5 m rays ended inside the arms held in front of the chest:
  false 4-6 cm hits on the chest plate).

## Gates (`work/rig_v3t.blend`, every frame; `scripts/gates_hkr.sh`, `review/gates_final.json`)

| Gate | Result |
|---|---|
| shell leak (`shell_leak.py`, `review/shell_leak_final.json`) | PASS every clip incl. Death: no kept skin in front of a shell piece (0.5 cm) |
| shell stretch (`shell_stretch.py`, `review/shell_stretch_final.json`) | PASS: living p99 / max <= 1.074 / 1.084 (limits 1.10 / 1.25) |
| armour clearance (`armour_gate.py`, `review/armour_gate_a3.json`; hidden skin and hidden loose pieces not counted, five-ray parity) | living clips <= 0.09 cm (belt / right tasset / thigh plate at the Running knee drive); Death <= 2.6 cm (a falling forearm at the left tasset, the slumped head at the caps and spikes 1.5-1.8); the belly under the cuirass in Death is gone |
| arm stretch p99 (max) | living <= 1.93 (R max 3.5 at the back of the shoulder, under the cap); Death 2.05 (4.45) |
| hand stretch | <= 2.24 |
| wrist swing (<= 60) | L 13-41, R 22-45 (living clips); Death 37 / 49 |
| hands in body | <= 0.08 cm |
| carbine up / roll (`rifle_up_check.py`) | PASS every held clip |
| soles (`sole_probe.py`, half frames) | Standing/Attack/Fidget -0.1, Walking -0.3..2.3, Running -1.9 (flight phase up), Hit -0.6 cm |
| hip flexion (`hip_flex_probe.py`) | Running 69 / 75 deg after the limit (88 in the source) |
| silhouette (`silhouette_ratio.py`) | shoulders / hips 0.81 / 0.58 m = 1.40 (v3 1.50; concept 1.15) |
| floor / death | plates over the floor; corpse lowest -0.15 cm; the carbine leaves the hands and lies on the floor (the blend's held gun dips 4.4 cm at Death 0.27 s, the export lifts it) |
| key times | PASS: both exports and the three viewer GLBs |
| winding | 0 inverted closed parts in all 29 GLBs |
| far LODs | bare body r30_16 pass; Trooper body r42_20 pass (`LODREP_LADDER`: the plates' outline needs LOD2 at 42 %); attachments `lod_atlas_check.py` PASS |
| viewer (`tools/run_creature_review.py ... check`) | every tier and clip, no console errors |

## Runtime (`TOK=<lease> LOD_REPAIR_PYTHON=<venv> scripts/build_runtime_hkr.sh`)

Both from `work/rig_v3t.blend` (`export_hkr.py`, same skeleton and `Carbine_*` / `Demon_*` clips):
- `export/hes_kreegan.glb` (bare, MODE=base): prepare -> LODs -> skin variants -> shrunk shadow LODs -> far LODs
  (`lodrep/`) -> key times;
- `export/hes_kreegan_trooper.glb` (MODE=trooper): the bulked body + shell, skin under it removed -> prepare -> LODs -> variants (skin,
  `HKR_Plate`, carbine) -> glow variants -> rigid parts split out (`scripts/attachments_trooper.json`; a far level
  below 8 triangles keeps the previous one, per-item `lod_from` for levels that sampled across UV islands) -> shadows
  rebuilt and shrunk -> far LODs (`LODREP_LADDER=0.42:0.2`) -> carbine drop -> emission (glow materials, bloom) -> key
  times.

| LOD0 triangles | |
|---|---:|
| bare body (Demon_Body_A 7,770, claws 1,492, eyes 146) | 9,408 |
| Trooper body + shell (skin 8,993 after removing 415 faces; shell 4,448 + glow 526 minus the caps' share) | 12,225 |
| rigid attachments, tier A/C (crest 70, caps 2 x 318, spikes 2 x 128, buckler 168, carbine 780) | 1,910 |
| **per tier LOD0** | **14,135 (A/C) / 14,111 (B)** |
| Trooper body LODs (after the split, far LODs repaired) | 12,225 / 6,106 / 4,515 / 2,205 |
| bare body LODs | 9,408 / 4,684 / 2,788 / 1,486 |

Exports: `export/hes_kreegan.glb`, `export/hes_kreegan_trooper.glb` and `export/hes_kreegan_<part>.glb` (crest,
pauldron_l/r, carapace_l/r, spikes_l/r, buckler, carbine). The glow materials carry emission with bloom. Viewer GLBs (`viewer_tiers_hkr.py` from the Trooper
export: ramps baked, tier B with the carapace instead of the ivory caps, then the carbine drop) in `review/viewer/`.

## Tier colours (2026-10-24)

The user decided that castes and tiers stop sharing one violet / plum / rose skin
([MONSTERS](../../../design/kreegan_world/MONSTERS.md) "Kreegan skin colours"). The table lives in
`../claude_shared/kreegan_skin.py` (`SKIN`, `BOSS`), with `recolour()`: a ramp keeps its range and its stops'
luminance spread, hits the table colour at 70 % of the ramp, and lifts the highlights of dark tiers (top stop at
least 0.07 linear luminance). Every caste's ramp script calls it: here `tier_ramps_hkr.py` (Trooper skins; harness
unchanged). The Drudge, Lancer, Harrower and Overseer projects use it from their own scripts.

- Rebuilt with `scripts/build_runtime_hkr.sh`. Every export (bare body, Trooper, all eight attachments) has the same
  geometry, skin, clips, nodes and images as before; only the skin ramps changed. Rerunning the script also refit the
  plate ramps to the current v4 armour texture (the old JSON predated it): mean 0.8, p95 3 of 255 on A, invisible.
- `export/hes_kreegan.glb` is now SHA-256 `38cc3345…`; the Drudge and Lancer pins were updated.
- Gates (`gates_hkr.sh`) identical to before, winding 0 in every GLB, key times PASS, viewer 3 tiers x 16 clips with
  no console errors. Sheet: `review/tier_colours_20261024.jpg`. The previous exports are in
  `work/before_tiercolours_20261024/`.

## Doubts

- Silhouette 1.40 against the concept's 1.15: the concept's hips read wide from its stance and very broad thigh
  armour; ours grew from 1.50 but the clip's stance is narrower. Wider thigh plates would need the legs apart.
- Running's knee drive is limited (88 -> 68-75 deg) for the armour; the run reads a little heavier than the source.
- Far LODs of the Trooper body are dense (LOD2 4.5k, LOD3 2.2k: 74 % / 49 % of the level above) to keep the plates'
  outline within the gate.
- The shell texture is procedural (ivory chitin cells, gold trim, groove, glowing seam strips and studs as
  geometry). No Meshy retexture was spent this pass; one (<= 20 credits) could add sculpted chitin detail.
- Right-arm stretch max 3.5 at the back of the shoulder under the cap (p99 1.5): the bulked shoulder's lever.
- Hit's head snaps 27 deg in one frame at 0.08 s (the source GetHitF1's own jolt).
- Not checked in game (nothing installed); the Hesper stage should spawn the three ranks and look at LOD switches.
