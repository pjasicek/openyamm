# MM7 Zombie (m438) — Claude humanoid project

Batch F, model 5 ([batch file](../mm7_batches/BATCH_F.md)). Descriptors 427 Rotted Corpse (palette 118, olive
trousers and headband), 428 Walking Dead (119, pale grey) and 429 Zombie (123, black). **Exported, not installed**
(batch rule). Technically complete; user artistic acceptance pending. Not checked in game.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_m438_claude/review/viewer/`) ·
[clay clips](review/clips_three_quarter.png) · [textured actions](review/actions_viewer.png) ·
[tiers](review/tiers_viewer.png) · [tier close-ups: chest, trouser holes, shin, head](review/tiers_closeups.png) · [stump and held forearm end, front and 3/4, all tiers](review/stump_prop_closeups.png) · [gates](review/gates_final.txt) · [G1 candidates](review/g1_idle_walk.png),
[actions](review/g1_actions.png), [walks](review/g1_walks.png) ·
[HD masters](references_hd/selected_views_review.png) · [head masters](references_head/selected_views_review.png)

| Item | Value |
|---|---|
| Exports | `export/mm7_m438.glb` (body, 4 colour LODs + shadow LODs, 3 tier variants, head merged into a 2080x1024 atlas), `export/mm7_m438_forearm.glb` (the held severed forearm, attachment on node `Sword`), `export/mm7_m438_lod0.glb` (portable LOD0 incl. the prop); editable master `work/rig_v7.blend` (`rig_v6.blend` + the stump bones) |
| Triangles | body LOD0/1/2/3 9,499 / 4,748 / 1,708 / 562; forearm 1,844 / 922 / 330 / 108 (combined 11,343 / 5,670 / 2,038 / 670) |
| Mesh | Smart Topology (15k) of the HD three-quarter master: skin shell (head, torso, arms; the right arm ends 9 cm below the elbow), closed trousers, two feet, rope belt and ends, four stump bone tips, three shin bone rods, teeth, eyes. Repairs (`step1_clean.py`): a 5-edge flank hole filled; **the right shin had no volume** (only the three bone rods between the trouser cuff and the foot), so a closed 240-triangle lathe restores the leg with the rods half embedded as the visible bone |
| Rig | 52 `B_*` bones + twist bones; Meshy auto-rig for the axial joints, clavicles, shoulders, hips, knees and the left elbow; left wrist at the narrowest arm ring; **right arm (stump)**: elbow at the left upper-arm length along the stump axis, the hand/finger bones continue the forearm in the air and carry no weight (Meshy's "hand" share on the stump moved to the forearm); ankles from the foot-shell ring at 9 cm; left fingers by connectivity (the short curled pinky needed the finger-pieces direction, not the forearm's) |
| Weights | `weights_fix.py`: skin = Meshy + shoulder fade + neck free of the shoulders; trousers Meshy without arm share; rope copies the trousers/skin; stump bones rigid on the right forearm; shin rods copy the shin/foot; teeth and eyes rigid on the head. Reduced after weighting 16.2k -> 9.8k (head and hands protected) |
| Stump (user review 2026-10-20) | Smart Topology's four rods below the stump (P06-P09) read as a small hand growing from the wound. `stump_bone.py` replaces them on the textured master with two broken bone shafts (radius and ulna, `bone_stub.py`: 6-sided, 1.1 / 0.95 cm radius, 3.4 / 2.6 cm out of the stump, jagged broken tips, side by side across the arm as `m438sa0/sa1` draw them), skinned 100 % to `B_R_Forearm`, bone class, UVs in a 40-texel ivory patch painted into free atlas texels (`bone_patch.py`; colour from the native sprites' pale bone pixels x 1.15, sRGB 215/179/145), zeroed in the region mask |
| Prop | The severed right forearm is built from our own mesh (`make_forearm.py`: the left forearm + hand mirrored and cut by a plane 4.5 cm below the elbow; the cut end is a ragged rounded wound - a torn rim, three inner rings bulging out, the same two bone shafts as the stump - instead of the first flat fan, which read as a faceted red block (user review 2026-10-20); the grip zone squeezed to the 3 cm fist), held by the wrist in the **left** fist with the bloody elbow end forward as the club head (native `m438sa*`, `m438a*`). Own 512 texture set copied triangle by triangle from the body set (`forearm_textures.py`; normals turned with the UV frame); the wound end takes the native wound ramp through a smooth noise field (the same crimson as the stump), the bones the stump's ivory |
| Clips (30 fps) | see below |
| Textures | body 1K + head 1K (Meshy retextures from the HD masters / head turnaround); skin repainted to one albedo from the native sprite's grey-green (x1.4) times Meshy's fine shading (Meshy painted salmon patches); **wounds re-graded** (review 2026-10-20) to the native wound colours (the crimson pixels of `m438sa*`/`w*`, median sRGB 69/9/9), histogram-matched to Meshy's wound luminance so its flesh detail stays, 1-texel feather; the red Meshy painted on the bone rods counts as wound; AO graded; ORM red = per-class specular mask; material class maps. One recolour region (R): trousers in the body set, headband in the head set; ramps histogram-matched to the native trouser/headband pixels of each palette. **Torn hole rims**: trouser texels within 7 UV texels or 3 cm (3D) of a wound are darkened to the cloth's 25th-percentile luminance and wound texels + a 2-texel border stay out of the mask (they were white halos on tier B); the darkened rims stay out of the ramp histogram. Trouser mean sRGB A 41/52/32 (native 43/46/31, x1.35 58/62/42), B 111/115/120 (114/116/118), C 7/16/20 (6/11/13) |
| Meshy credits | **30 of 100**: Smart Topology 5, auto-rig 5 (joint estimates), body retexture 10, head retexture 10; no paid animation |

## Clips

| Clip | s | Source and adaptation |
|---|---:|---|
| Standing | 4.23 | Mixamo Zombie Idle; authored carry (`carry_L.json`): the arm nearly straight 15 deg out, the forearm level and pointing forward at the hip like `m438sa0/sa2` |
| Walking | 1.73 | Mixamo Walking (5), a staggering shamble; the carry arm held from the idle with a 14 deg swing against the stump arm (`arm_hold.py`, mm7_m214); per-frame floor pass (the drunk walk sank -7.5 cm on our legs) |
| Running | 0.73 | Mixamo Standard Run fitted + carry (prop pitched 35 deg up); spare, the tiers never reach the run threshold |
| Attack | 1.80 | Mixamo Sword And Shield Slash (2) **mirrored onto the left hand** (`retarget_mixamo.py :mirror`, from mm7_m154): the forearm raised overhead and chopped down and across (native `m438aa..ag`); planted + 20 % of its legs, 0.3 s ready pause, **blow 0.95 s** (fastest club-head motion while pointing forward) |
| Hit | 0.50 | Humanoid set Unarmed get-hit front 1, blends 0.2 s |
| Death | 3.63 | Mixamo Standing React Death Backward (falls onto the back like `m438da..dd`), travel halved, floor pass; the forearm kept in hand and cleared of the floor |
| Dead | 1.00 | last Death pose held |
| Fidget | 2.80 | Mixamo Zombie Scream (planted): a sideways lurch with the arms out (native `m438nb`-like) |

G1 (`review/g1_*.png`): idles Zombie Idle (1)/(2)/(3) crouch or hunch; walks: Walker Walk 0.18 m/s and Walking (12)
0.57 m/s would play 3-9x, Zombie Walk raises both arms, Mixamo Walk 1.9 m/s is not a zombie; hits from the zombie
pack lunge a step; Zombie Death/Dying travel far.

## Gates (final rig, `review/gates_final.txt`)

- G3: frame error 0; left finger chains inside the fingers (`hand_look.py`).
- G4 arm stretch p99 <= 1.87 (death, both arms), edge max 2.9; hand twist vs forearm <= 92 deg (left, fidget).
- G5 left hand stretch <= 1.83x (fidget); the solved fist (handle radius 3 cm, thumb capped at 30 deg) wraps the
  severed wrist.
- G6 (closed skin AND the closed trousers, half frames, with the exported prop on `rig_v7`, i.e. the new stump bones
  and the new forearm end): prop, both forearms and the left hand 0 cm inside in every clip except Running 0.1 cm. `prop_clear.py` turned the hand <= 15 deg in Walking/Fidget/Death
  (<= 45 deg in the unused `AttackFull`/`FidgetFull` helpers); `arm_clear.py` swung the stump out <= 4 deg in the attack
  and the carrying arm <= 6 deg in the run.
- Soles: grounded within -1.3..+2.0 cm (walk), -0.9..+1.9 cm in the other planted clips; Running airborne by design.
- Jerk: the mirrored chop keeps the source's whip (left upper arm 32 deg per 1/48 s at the blow, as m190's 50);
  the set's hit snaps the head 16 deg per 1/48 s (source motion); the spare run's loop seam steps the neck/spine 7 deg.
- Viewer: 3 tiers x 8 clips, no console errors (`run_creature_review.py check`, `check_viewer.mjs`); textured shots
  of all tiers in `review/shots/` inspected.

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m438_claude/export/mm7_m438.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m438_claude/export/mm7_m438_forearm.glb --world mm7
```

Then add [actors_m438_binding.yml](actors_m438_binding.yml) to `assets_dev/worlds/mm7/models/actors.yml`: scale 125.1
= native stand 216 px x 1.0 over the 1.726 m Standing pose (all tiers); stride 2.03 m (the right foot's stance speed
1.17 m/s in Walking (5); the left foot drags, `stride.py`'s median of both feet gives 1.42 m); blow 0.95 s; head look;
forearm attachment on node `Sword`. Tier speeds 160/180/200 stay under the run threshold (300), so every tier walks, at
1.09x / 1.23x / 1.37x the walk's natural speed. Winding check: 0 inverted closed parts in both GLBs.

## Replay

Claim the project, then `CREATURE_3D_TOKEN=<token> scripts/rebuild.sh` (STAGE=rig, then STAGE=anim twice on a fresh
project: the prop clearance needs the solved grip). Texture chain once: `export_uploads.py`, Meshy
`body_retexture_v1` / `head_retexture_v1` (`requests/`), `transfer_uv.py -- work/rig_v5h.blend
meshy/body_retexture_v1 work/rig_v6.blend`, then `... work/rig_v6.blend meshy/head_retexture_v1 work/rig_v6.blend
HeadUV`; then `scripts/build_runtime.sh` (rasters, AO, the bone patch and stump bones -> `work/rig_v7.blend`, `compose_m438.py`,
the forearm prop and its textures, export,
LODs, variants, split, head merge), `viewer_tiers.py`, `update_viewer_manifest.py`. Gates: `prop_attach.py` +
`g6_prop.py` (PROP_HAND=L), `g4_weights.py`, `g5_hand_stretch.py`, `sole_probe.py`, `jerk_probe.py`, `stride.py`,
`stand_height.py`.

## HD masters and the refusal record

- `00_three_quarter.png`: orchestrator override of Codex's first return (Codex rejected it for a front-LEFT camera
  and enlarged red accents; its one corrective regeneration was refused by the image service: violence). Accepted on
  the Claude gate (alpha, canvas, identity, stump, empty left hand, palette).
- `01`-`04`: original wording except `02_back.png`, which came from the benign rewording variant R2 after two refusals
  (original wording, then R1). **User decision 2026-10-20** (relayed by the coordinator) overrides BATCH_F's
  no-rewording rule: rewording after a refusal is allowed (stains instead of open wounds); every prompt and refusal is
  in `references_hd/generation_runs.json`. The back view's stains are therefore described as stains/patches; the
  model's wounds come from Meshy's paint of all four views.
- A second user decision allowed a fallback to the restored sprite art if the HD route failed. **Not needed; not used.**
- Head turnaround: no refusals; Codex returned 1254x1254 instead of the 1024x1024 asked.

## Known limits / for the user to review

- The wounds are Meshy's paint re-graded to the native crimson; their shapes (chest spots, flank, stump, right shin,
  trouser holes, a band at the left wrist from the HD masters) are Meshy's and larger than the sprite's.
- Tier A trousers read greener than the sprite's olive-brown at the viewer light (the native palette's shadow entries
  are true greens; the mean matches the native mean, not the x1.35 sprite gain, because the darkened hole rims pull
  it down).
- Tier C trousers and headband are near-black: palette 123 maps the lit olive-brown entries to (1..4) grey and only the
  green shadow entries to dark teal, as the native sprite does. The head mask is eroded by one texel (white specks
  beside the tier-B band); a few dark flecks remain inside the white band.
- The walk is a drunk stagger with a dragging left foot; that foot slides at the chosen stride. The tiers play it
  1.1-1.4x.
- The held forearm is rigid (the severed hand does not dangle); its texture is the body's left forearm, mirrored.
- The bone shafts are simple 6-sided low-poly sticks (72 triangles per pair); at close range their facets show.
- The right-arm stump twists with the forearm twist bone (the source's hand roll x 0.6), which the short stump shows
  only slightly.
- Hand twist reaches 92 deg against the forearm in the fidget (left hand).
- Not checked in game (optional for batch F; other agents were building in parallel).
