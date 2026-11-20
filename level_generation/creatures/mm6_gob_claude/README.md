# MM6 goblin (gob) — 3D model, 2026-10-06

**Superseded 2026-10-10** by [mm6_gob2_claude](../mm6_gob2_claude/README.md) (bound in `actors.yml`); this model's
GLBs remain in `export/` only.

BGoblin A/B/C (550 Goblin, 551 Goblin Shaman, 552 Goblin King) from the reviewed
[stage-1 package](../mm6_goblin/stage1_20261006/README.md), made with the
[humanoid NPC playbook](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md). Opt-in (`debug.actor_models=true`).

![Skins A/B/C](review/lit4_abc_sheet.png)

In-game: [goblins in combat](review/ingame/fight_v2_crop.png), [standing](review/ingame/full.png),
[face](review/ingame/face.png). Launcher: `./tools/run_gob_3d_test.sh` (3 Goblins + Shaman + King, immortal party).

| Item | Value |
|---|---|
| Runtime GLB | `assets_dev/worlds/mm6/models/mm6_gob.glb` |
| Bindings | `actors.yml`: skins `gob_a/b/c`, scale 106.1 (256 px × 0.65); B/C `scale_reference: BGoblin A` (0.70/0.75 sprite scales) |
| Triangles LOD0/1/2/3 | **11,574** (incl. 642-triangle scimitar, subdivided fingers) / 5,786 / 2,066 / 643 |
| Skeleton | 57 joints: Mixamo with fingers + forearm twist + sword bone; ≤ 4 influences |
| Clips (revision 2) | Standing (sword low and forward, hands clear of the skirt), Walking (Meshy legs, authored arms), Attack (forehand diagonal cut, 0.75 s), Cast_FireBolt (left-hand gather/thrust, for Shaman/King spells), Hit (left forearm face guard, bow), Death (fold, left-hand brace, prone, sword drops), Dead, Fidget |
| Textures | 2048² base colour × 3 (skin only changes: olive / blue / red from palettes 745→746/747), 1024² normal + metal/roughness |
| Meshy credits | **64 / 100** (Smart Topology 5, three retextures 30 — two discarded, see below; rigging 5 for Meshy walk/run) |
| Regression | `mm6_gob_actor_models_bind_sorpigal_goblins` (A=76, B=6, C=30 in New Sorpigal) |

## What was cheapened

15,757 → 10,112 triangles before rigging: 24 spikes, ear hoops, teeth and buckle reduced hard, skirt strips and
greave straps decimated, skin under armour/leather decimated, eyeballs removed (painted by the retexture).
Face, hands with claws and silhouette armour kept.

## Process notes (what the self-check loop caught)

- Sword frame: the flexion-measured palm normal was nearly parallel to the blade axis on this rig, collapsing the
  blade to a needle. The hand frame is now orthogonal; the blade plane follows the forearm.
- Sword-hand poses: requested palm directions forced 110°+ wrist bends. `orient_blade` now picks the roll about the
  blade axis with the least wrist strain. The chest frame for poses is the body's canonical frame carried by the
  posed spine (the refitted hunched spine bones had tilted "forward" downward).
- UVs: retexture v1 was patchy on greaves/skirt (ABF fragmented the Meshy armour/leather shells into ~1,400
  islands) → armour/leather now use Smart UV Project. Retexture v2 then showed dark feet: feet UVs had collapsed
  to a line inside the torso region → legs and feet are separate UV regions (seam along the sole), wrists map to
  the forearm. Retexture v3 is the delivered one.
- Shaman/King cast Fire Bolt, so the engine requires a distinct cast clip — `Cast_FireBolt` was added.
- Armour metallic lowered (0.5) after in-game captures showed sky reflections turning iron blue.

## Revision 2: animation review fixes (2026-10-07)

User review in the [viewer](review/viewer/) flagged hands inside the body, a sloped-shoulder walk and warped wrists.
Causes and fixes:

- Hand targets were chest-local from the Spine2 joint, which sits 10 cm behind the shoulders on this hunched body;
  hands landed 5-8 cm inside the thighs/chest. Arms now use a mirrored shoulder frame (`'sh': True`: out, up, forward).
- An attached action re-evaluated over poses being built (the right clavicle was silently reset). Poses are now built
  with no action and written directly (`author_clips.key_clip`/`write_action`).
- The walk copied the female peasant's clavicle drop and tight arms. It keeps the Meshy legs/spine; arms are
  re-posed per frame with clavicles at rest and a counter-swing phased from the feet (`author_gob.build_walk`).
- Requested blade directions near the forearm axis forced 70-degree wrist bends; blades are now kept roughly
  perpendicular to the forearm, and the grip roll penalises forearm twist and stays continuous between keys.
- Raised arms lift the clavicle automatically; the corpse drops the sword flat beside the hand.
- `scripts/pose_audit.py` checks every frame for arm/sword penetration (ray-parity inside test), wrist bend, forearm
  twist and arm elevation; `scripts/review_frames.py` renders labelled multi-view sheets with the audit per row
  ([attack](review/anim_v2/attack.png), [hit](review/anim_v2/hit.png), [cast](review/anim_v2/cast.png),
  [walk](review/anim_v2/walk.png), [close-ups](review/anim_v2/close.png)). All clips pass except a 101-degree
  forearm twist at the attack wind-up (limit 100).

## Revision 3: rig repair and native attack (2026-10-07)

Second viewer review: mangled sword fist, twisting upper arm, odd left-hand fingers, attack unlike the original.
Root causes were in the rig, not only the poses. `scripts/rebuild_anim_v3.sh` replays everything from
`work/final_v1_before_hand_refit.blend`:

- `refit_hands.py`: the proxy fit had stacked all finger chains on one or two real fingers (two left bones 9-14 mm
  long). Fingers are now found on the mesh (surface distance from the wrist, one region per fingertip, split at the
  webs); chains follow each finger (thumb + three fingers, the unused fourth chain is parked), rolls curl toward the
  palm, and finger weights are rebuilt along the chains.
- `fit_sword_grip.py`: the grip is moved into the closed fist (axis through the curled finger loops, 30-degree
  diagonal toward the knuckles); the thumb wraps over the fingers when the hand is closed.
- `tuck_shoulders.py` + `fix_arm_bleed.py`: upper-arm weight had bled onto chest, back, lats and neck (~18 %);
  torso-side skin now follows the clavicle/spine, the armpit boundary is smoothed, hidden shoulder skin sits 18 mm
  under the pauldrons, and shoulder armour copies the weights of the skin beneath it.
- Arm solving keeps the requested elbow unless the upper arm would roll more than 40 degrees, then searches elbow
  directions that stay outside the shoulder line. The blade aim may tilt up to 35 degrees to spare the wrist.
- Attack follows native gobata a-f: low sword across the belly, lift across to the left shoulder with the open left
  hand beside it, blade high, diagonal cut to the right hip, arm out to the right with the blade level, sword hanging.
- `scripts/viewer_shots.mjs` captures the review viewer itself (clip, time, camera, focus) for self-checks.

Audit maxima: penetration 4 cm (inner arm against the chest in the Hit face guard, hidden by the arm), wrist 66,
forearm twist 64, upper-arm roll 75 (corpse sword arm).

## Revision 4: hands and Corsair scimitar (2026-10-07)

- `subdivide_hands.py`: one smooth subdivision of the fingers/thumbs (~70 triangles per finger was faceted when
  curled); corners outside the hands keep their custom normals. +960 triangles.
- `replace_sword.py`: Corsair-style scimitar (MM7 artifact icon `7item220`, native goblin sword): curved blade
  widening to a clipped point, two back notches, diamond bevel, octagonal leather grip, round crossguard, D-shaped
  knuckle bow, scroll quillon, round-cut red jewels at guard and pommel (642 triangles). The atlas has no room for a
  sword texture, so faces map to swatches in free atlas space (`paint_sword_swatches.py`: steel gradient strip with a
  fuller line, gold, leather, jewel); steel is metal 0.6 / rough 0.34-0.48 so it does not mirror dark scenes black.
- Grip: the grip axis runs through the curled finger loops (no diagonal offset); per key each finger's spread,
  knuckle curl and distal curl are solved so its phalanges lie on the handle surface within the handle length.
- Claws: compose paints horn only on the last ~2 cm of each fingertip (tips from `work/hand_fit.json`), blended into
  the skin; the rest of the finger takes the forearm skin tone.

Rebuild: `scripts/rebuild_anim_v3.sh`, promote `work/rig_v2.blend` to `work/final_v1.blend`, `compose_gob.py`,
`paint_sword_swatches.py work/sword_swatches.json`, `build_runtime.sh --install`.

## Revision 5: colour grade (2026-10-07)

The textures looked washed out in game next to the graded demon. `compose_gob.py` now grades toward the native
sprite medians (skin H65 S0.64, leather H25 S0.69, neutral iron), using the demon's approach: saturation scaled
around luminance, then channel gains (skin x1.35 sat, gains 0.86/0.98/0.85; leather x1.25, 0.85; plates x0.40,
0.86/0.86/0.88). Skin/leather roughness 0.72/0.78 (less white sheen), normal strength 0.75. Goblin A skin median
moved from H52 S0.49 V0.42 to H64 S0.66 V0.37; B/C follow through the palette fits.
[Before/after in game](review/ingame/grade_before_after.png).

## Revision 6: cast socket and Meshy walk/run (2026-10-07)

- Spell glow: the engine places the cast glow halfway between the bound palm sockets. With both palms bound it
  floated in front of the chest (left hand gathering, right fist low with the sword), and the sockets themselves sat
  5 cm toward the back of the wrist. `fix_palm_sockets.py` puts each socket 2 cm off the palm centre; the goblin
  bindings now list only `palm_left`, so the glow forms at the casting hand.
- Meshy rigging job `rig_v1` (5 credits) on the retextured mesh supplied its walk and run. `retarget.py` maps them
  onto the fitted rig; `author_gob.build_locomotion` keeps Meshy's hips/legs/spine/head, returns the clavicles to
  rest, keeps the wrists' swing (damped 30 % for the run) but holds hands and elbows outside the body, puts the sword
  in the solved fist and relaxes the left hand. Bindings: `walking: Walking`, `run: Running`.
  Audit: walk contact ≤ 3.5 cm (inner forearm at the skirt), run ≤ 6 cm where the pumping left upper arm meets
  the chest side under the pauldron.

## Revision 7: locomotion posture (2026-10-07)

The Meshy walk/run leaned the torso 4-7 degrees (walk) and 12 degrees (run) further forward than Standing, with the
head following and straight hanging arms, so the goblin looked slumped. `build_locomotion` now pulls the hips->neck
lean back to Standing's 10.5 degrees (15 for the run) and the neck to 18, lifts the clavicles 5-7 degrees, keeps the
wrists at Standing height and points the elbows outward. Audit: deepest contact ~3 cm (walk), ~2.7 cm (run).
[Posture sheet](review/anim_v5/loco_posture_v2.png).
The elbow direction copied from Meshy rolled the right upper arm through ~50 degrees per cycle; with no upper-arm
twist bone the skin under the pauldron wrung. `author_clips.solve_arm_low_roll` now picks, per frame, the elbow
direction that keeps the upper-arm roll near rest (walk right arm -17..5 degrees, run constant).

## Locomotion binding (2026-10-07)

At the user's request the goblins use the Meshy run for walking as well (`walking: Running`, `run: Running`).
Goblins move at 160 units/s (~1.5 m/s); the run covers ~3 m per 0.625 s cycle, so a true stride would play it at a
third of its speed. `stride_length: 1.25` keeps a quick ~0.83 s cycle at the cost of some foot sliding.
`Walking` stays in the GLB.
Run sword arm (follow-up): the blade was aimed forward while the pumping forearm also pointed forward, so the sword
lay along the forearm with the wrist cocked, and the elbow was pushed out sideways (chicken wing). In the
locomotion clips the blade is now held across the forearm (up+forward minus the forearm component; ~90 degrees), and
the run's elbow drives down and back with the fist allowed in front of the shoulder (Meshy's own swing).

## Revision 8: form contrast (2026-10-07)

In game the graded skin was about as flat as the grass behind it (p90/p10 luminance ~2.1 vs the demon's ~3.1),
so the goblins blended into the background. `compose_gob.py` now boosts the large-scale painted shading on skin
(x1.8) and leather (x1.5) within each material, AO strength 0.75, skin roughness 0.58 (highlights back), leather
0.70; normal strength back to 1.0 in `export_glb.py`. Skin texture contrast 2.4 → 4.8.
[In-game before/after](review/ingame/contrast_before_after.png). User: "now it looks better".

## Revision 9: Meshy auto-rig (2026-10-07)

Root cause of the recurring arm/shoulder/wrist/neck warping: our MakeHuman-proxy rig. Its joints sat in the wrong
places for this body (shoulders ~6 cm and elbows ~8 cm too high, neck/head too high) and its transferred weights
mixed chest and arm skin, so moving arms stretched narrow bands 6-9x. The same frames on Meshy's own auto-rig
(rig_v1 job) deform cleanly ([comparison](review/meshy_library/meshy_own_rig_same_frames.png)).
`scripts/switch_to_meshy_rig.py` moves the rig onto Meshy's joints and axes (bone names unchanged), takes Meshy's
weights for everything except the hands, keeps our fingers, twist bones, sword and sockets, re-applies our clips
rest-relative, and plays Meshy library clips (anim_lib_v1, 24 credits: M_* candidates) and walk/run directly.
Worst stretch at the user's flagged frames: 6-9x -> ~2.5-3x. Meshy credits: 64 / 100.
Open: arm/body contact up to 5-8 cm in some Meshy clips (human proportions on a bulky goblin), forearm twist up to
122 deg in M_SwordSlash/M_ChargedSlash, and the Meshy clips' length versus the native 0.75 s actions.

## Revision 14: fixed hands + Meshy clips (2026-10-07)

`scripts/finalize_v14.py` on the Meshy rig: one fixed right fist around the sword (solved once at rest) and one
relaxed left hand in every frame; Meshy motion copied as world rotations; forearm twist clamped at 90 deg; arms
swung outward from the shoulder where they enter the torso; head tilts away from a raised arm; walk/run lean
matched to Standing. Attack = Meshy 219 (frames 2-33, x1.5, 0.875 s), Hit = Meshy 179 (x1.4, 0.83 s),
Death = Meshy 184 (frames 0-44, x1.5, 1.21 s), Dead = its last frame; Standing/Fidget/Cast are ours.
Audit: no sword in the body, twist <= 90 deg, contact <= 5.8 cm (armpit folding, inside the body).
In-game combat tour at play distance: [sheet](review/ingame_v14/ingame_v14_sheet.png),
[crops](review/ingame_v14/ingame_v14_crops.png). Also fixed an endless loop in `posing.two_bone_ik_hinge` on ties.

## Death clip runs to the end (2026-10-07)

The AI switches Dying -> Dead after the native sprite death length (0.625 s), which cut the 1.2 s Meshy fall in
half. `WorldFxSystem` now keeps playing a model's death clip after the switch until it ends, then holds the dead
clip (visual only; not for disintegrating deaths such as the demon). [In-game sequence](review/ingame_v16/death_sheet.png).

## Known flaws

- The ring finger's base touches the grip ~1 cm deep near the pommel; the curled fist is still somewhat lumpy close up.
- Atlas utilisation is ~46% (many small armour islands); texel density is lower than the peasants.
- User artistic acceptance not yet recorded.

## Head texture set pilot (2026-10-08)

Head-only retexture of the same mesh ([creature textures](../CLAUDE_CREATURE_TEXTURES.md), "Head detail"):
1. `references_head/`: Codex head turnaround (1254², brief `CODEX_BRIEF.md`, from the accepted body references).
2. `scripts/head_split.py` on `work/final_v1.blend` (backup `final_v1_pre_head.blend`). Head = Body/Teeth/Hoops faces
   weighted mostly to `mixamorig:Head`, 2,231 of 11,203; face attribute `head`; own UV layout; exports
   `texturing/gob_head_upload.glb`.
3. Meshy `head_retexture_v1` (10 credits; 87/100 used) from `00_front`, `02_left`, `03_back`, `04_right`.
4. `scripts/compose_head.py`: 1K head maps, graded like the body, skin luminance matched to the body (median 0.1085
   vs 0.1084). The head reuses the body's skin ramps, so head and neck match in every tier.
5. `export_glb.py` assigns `GoblinHead_A` from the `head` attribute; `gob_ramps.json` has Goblin + GoblinHead entries.
Result: same triangle count, head and body as two primitives per LOD, GLB 9.8 → 12.4 MB. Captures:
`review/head_set_gobclose_20261008.png` and `head_set_gob_20261008.png`. The body base colour stays 2K for now.
`export/mm6_gob_prehead.glb` is the previous build.

## Clip timing (2026-10-10)

The engine's action events let a clip keep its own speed ([audit](../CLIP_TIMING_AUDIT_20261010.md)).
`GOB_ONLY=Attack,Death blender work/final_v1.blend --python scripts/finalize_v14.py` rebuilds only those clips in
place (backup `work/final_v1_pre_clip_timing.blend`): Attack = 0.3 s ready pause (ease from Standing into the
slash's first pose) + Meshy 219 frames 2-33 at source speed (1.58 s, was x1.5 in 0.875 s); blow (peak Sword-tip
speed) 0.729 s -> actors.yml `events: attack_melee: {impact: 0.729}`. Death = Meshy 184 frames 0-44 at source speed
(1.83 s; the engine finishes a long death). Sheet: `review/timing_attack_sheet.png`.
