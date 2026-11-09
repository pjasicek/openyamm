# Townsfolk PeasantDM4 (dwarf man, cap and red beard) — status

- Project `level_generation/creatures/mm9_peasantdm4_claude/`, lease `mm9:peasantdm4` (owner peasantdm4-agent), budget 50.
- Rows naming PeasantDM4.abc: only **10 Town** (Peasant Dwarf MaleB A, PeasantDM4a). Skin PEASANTDM4B is used by no row (not built).

## Log
- 13:00 UTC lease claimed (backup 2975). Sources converted. Skeleton = DM1/DM2/library bind exactly (41 joints).
  Rigid-shift test (`scripts/rigid_cmp.py`, translation ICP): best shift < 1 cm, torso stays p50 2.8-2.9 / p90 5.2-5.5 cm vs
  DM1/DM2 -> not a shifted copy. Renders (`review/sheet_mm9_dm4_vs_dm1_dm2.png`): own design (skullcap with emblem, red hair
  and beard, laced vest, puffed shoulders, flared tunic). Route: new body on the full MM9 humanoid route with DM1/DM2's
  retarget, linings and fixes. Credits 0.
- 13:20 UTC clips for row 10 (DAT class TownDwarfMaleA, 11 objects, stand-in 325): core roles + Cower (NPCbase -> BaseRun),
  RubBeard and X (NPC7.scr Refinery); randverretainer.scr's `sitting` is not in the dwarf library. Codex master 00: first
  return selected (arms 20 deg down as MM9; Codex's correction had them horizontal), halo removed.
- 13:35 UTC Smart Topology body_smart_v1 (5; backup 2975 before). Fit to the dwarf skeleton (arms within 2 %), reduce
  14,519 -> 7,609, MPFB hands at 0.205 m (Meshy 0.195/0.181, MM9 0.21), head split (cap + hair + beard + face one head set),
  head shell centred (Meshy put it 1.3 cm off the midline: scripts/head_shift.py), eye cups filled/removed, eye plate relaxed
  0.4 before the UV pass. UV pass running; Codex run 2 (views 01-04) running. Credits 5.
- 14:20 UTC HD masters 01-04 and head turnaround accepted (halos removed); body atlas 55.2 %, head 58.0 %; body 4K
  retexture (10, backup 2970 before) and head 4K retexture (10, backup 2960 before). Credits 25.
- 14:30-15:05 UTC first builds: cap faces flipped (cap_normals.py), the cap's silver medallion projected from the head
  master (Meshy painted a cap-coloured blob: emblem_project.py), hands to the face tone, sleeves tucked/trimmed, linings
  (collar, boots, sleeves, skirt hem and belt rims, cap inner lining; black interior texels excluded), rigid head
  (Bone03 chin 24-38 deg in AttackMelee/Hit and Ponytail1 49 deg in Talk would shear the face: head_rigid.py), relaxed
  fingers (Kira's finger_pose.py adapted to the two-segment dwarf mitten), arm clearance (arm_clear.py --exact, sigma 8:
  0 jitter excess) + hand rest. Exact arm/hand gate < 1 cm everywhere on the trial.
- 15:10 UTC PC reboot killed the see-through gate run (no output written; Meshy jobs all SUCCEEDED before, none pending;
  lease still valid). Resuming: right-cuff poke 2.1 mm (re-tuck), body blotch fix, final build and gates.
- (second restart, OOM elsewhere) resumed: lease valid, no Meshy job pending, no Blender of mine left; every Blender/heavy job
  now under `systemd-run ... MemoryMax=12G`, one Blender at a time.
- Jitter: arm_clear.py's neighbour falloff failed the jitter gate on its 5 clips (20-37 deg/f); NEW --smooth-keys Gaussian per
  clip (Talk 4, RubBeard/Fidget 14, Running/AttackMelee 8 + 7 cm margin): jitter 0 fails; exact arm/hand gate hands 0 cm,
  forearms <= 0.6 cm in all 13 clips. Right-cuff poke fixed (sleeve_tuck 0.7): rest 0 mm both sides.
- Paint: dark patches on the puffed sleeves were AO islands baked 0.1-0.3 + a faint Meshy smear: AO specks filled and floored at
  0.5 before the grade, then a surface-neighbourhood lift (blotch_fix3d.py). Faint traces remain on the sleeves.
- Face pre-screen r4 (front, 3/4, both profiles, low 3/4, party 22 deg, 128 px; Standing and Talk): irises visible from party
  height, one brow, one lip line under the moustache, clean nose underside, solid chin under the beard; ears hidden by hair as MM9.
- Viewer r4-20261102: 13 switches, 0 failed. Final see-through gate running.
- See-through fixes after the full gate: elbow rims of the puffed outer sleeves lined (rim_lining max_edges), hand-stub caps,
  toothed cuff flaps trimmed (cuff_trim -1.5 cm both sides: the thin wrist band went with them), inner-layer twins in the
  cuffs (skip_inner had left the trimmed cuff's bottom wall unlined), shoulder-top twins (twin_patch.py).
- Installed r9 (assets_source/worlds/mm9/models/mm9_peasantdm4.glb, sha256 037786978f46...). Bound under the flock: row 10 ->
  325 in mm9_npc_actor_rows.tsv, tables regenerated (217 rows), actors.yml block mm9_peasantdm4_claude (MM9 10 Town, no skin).
  Gates: exact arm/hand hands 0 cm (forearm <= 1.2), jitter 0 fails, sleeve poke rest 0 (Death R 1 vertex checked), floor ok,
  winding 0, bones 0, flat 0.00, body atlas 54.6 % (0.4 short), LOD0 12,262; viewer r9 13 switches 0 failed;
  mm9_actor_models_build_every_binding PASS (217 descriptors on 94 models).
  **See-through gate NOT fully passed**: right sleeve 74 px (X) / 110 px (Death), torso 97 (Running 12, 20 deg above behind),
  boots 14-18 in every clip, head 28 (Death); collar/trousers 0. Details in the README.
- Phase: **done (with the see-through residual)**. Credits **25 / 50** (backup 2975 at start; 2815 seen later, other agents
  spend too). Map placement left to the orchestrator (README "Binding plan"). Lease released.
- 16:22 UTC lease re-claimed (coordinator: cap reshape toward MM9's flat-topped skullcap, see-through to <= ~10 px, left wrist stub). 0 credits planned.
- 16:30-19:30 UTC (0 credits): cap reshaped to MM9's tall flat-topped skullcap (cap_reshape.py, positions only; band and
  medallion kept; review/sheet_cap_before_after.png, review/cap_overlay_s1.png). See-through: right shoulder top/upper back,
  skirt sides and boot cuff undersides twin-patched (twin_patch.py), cuff lining in shaded linen (the dark stub round the
  wrist in the front T-pose), all chained in scripts/geom_chain.sh. Final see-through r11 worst px: torso 9, right sleeve 9,
  left sleeve 17 (Talk; <= 11 elsewhere), boots 11/12, head 18 (cap silhouette slivers), collar/trousers 0 (r9: 97/146/18/
  14-18/28). Arm/hand hands 0 cm (forearm <= 1.2), jitter 0 fails, sleeve poke rest 0, floor ok, winding 0, bones 0, flat 0.00.
  Reinstalled r11 (sha256 ba125d9d90a8...), mm9_actor_models_build_every_binding PASS (229 on 100 models), viewer r11 13
  switches 0 failed.
- Phase: **done**. Credits **25 / 50**. Lease released.
- lease re-claimed (user note: Talk twists the clothing on the breast/collarbones). 0 credits.
- Talk chest twist (user note): body cloth near the beard carried MM9's head-only bones (Ponytail1 22 % on the upper chest,
  swung 49 deg in Talk; Bone03; Head 44 % on the collar) and upper-arm shares ran to the sternum. body_reweight.py (geometry
  chain): those shares -> Neck/Spine2, arm/clavicle shares fade toward the midline (as DM2). Chest shear p95 (chest_shear.py):
  Talk 5.64 -> 2.15 cm, X 7.38 -> 4.02, AttackMelee 8.49 -> 6.39. Meshy's beard paint on the shirt under the beard then showed
  (orange patch) -> under_beard_paint.py; the neck cap seen through the collar gap -> two-sided (twin_patch heads=1).
  Reinstalled r14 (sha256 70dcc8ca8a02...). Gates: arm/hand hands 0 cm (forearm <= 1.0), jitter 0 fails, sleeve poke rest 0,
  see-through torso 10 / sleeves 10 & 17 / boots 11-12 / head 16 / collar 8, floor ok, winding 0, bones 0, flat 0.00, binding
  test PASS (230 on 101 models), viewer r14 13 switches 0 failed. Sheets review/sheet_talk_chest_before_after_{a,b}.png.
- Phase: **done**. Credits **25 / 50**. Lease released.
- lease re-claimed (coordinator: under-beard fill reads as a smudge; clone real collar band / shirt texture, remove orange flecks). 0 credits.
- Under-beard cloth (coordinator: the smooth fill read as a smudge): under_beard_paint.py now clones real texel patches (linen
  shirt, navy collar band with gold knots, ochre vest weave; class by nearest clear cloth in 3D, mirrored tiling, local shading),
  catches the orange flecks and Meshy's featureless paint, pads the gutters. Sheets review/sheet_under_beard_{a,b}.png (Talk 77,
  X 63, AttackMelee 27, RubBeard 45; r14 vs r15). r15 = r14 mesh and clips (glb_diff 0.000 mm), only the body colour changed, so
  the r14 geometry gates stand. Reinstalled r15 (sha256 d07208ac9f2e...), binding test PASS (232 on 102 models), floor ok,
  viewer r15 13 switches 0 failed.
- Phase: **done**. Credits **25 / 50**. Lease released.
