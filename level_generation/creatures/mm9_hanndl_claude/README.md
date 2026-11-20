# MM9 Hanndl, the Gate Keeper (mm9_hanndl) — 3D actor variant, 2026-11-02

MM9 `HANNDL.abc` + `HANNDL.dtx`, `MONSTERS.txt` row **260 Hanndl** "Gate Keeper" (basemelee.scr, PeasantMale library, Move 0).
Placed in Arslegard City (`Hanndl1`, NPC334.scr; `Hanndl`, Hanndl.scr), the Great Gate (`Hanndl`, Hanndl.scr) and the Hall of the
Gods (`Hanndl`, WG_NPC334.scr). Batch: `devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md` (shared-mesh variants; no new body).
Owner variants-b. Progress and Meshy receipts: `creature_3d_progress.json`. (`HANNDLSCULPT.dtx`, a statue skin, is named by no
MONSTERS.txt row: not built.)

**Same mesh as PeasantM6 = Annud's body** (`meshcmp.py hanndl:peasantm6`: head max 2.0 cm on 1 % of samples, torso 0.4, legs 0.6,
arms p90 0.8, 3 % over 1.5 cm, max 6.9 cm). **The "small arm piece" is PeasantM6's, not Hanndl's**: vertex-level (`vdiff.py`),
Hanndl has 343 vertices, PeasantM6 365; the 22 extra are 11 per forearm (10 on the cuff, up to 11 cm out from Hanndl's surface):
the BELL CUFF FLARE of Annud's wide sleeves (plus one skirt-front vertex on Bone06, 5 cm, and one head vertex, 2 cm). Hanndl's
sleeves are fitted to the wrist. So this model is **Annud's approved body, MM9 skeleton, weights and clip choice**
(`../mm9_annud_claude/`, never written to) with the sleeves narrowed onto the forearm, and his own paint (old white-haired,
white-bearded man; dark brown tunic, fur mantle, chain-mail chest panel, studded belt, leather-lattice sleeves, fur-topped boots).

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_hanndl.glb` (`tools/install_model.py --world mm9 --name mm9_hanndl.glb`), identical to `v2/export/mm9_hanndl.glb` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` `MM9 260 Hanndl` (block `scripts/binding.yml`, `scripts/bind_under_lock.sh` under the flock): Annud's values (scale 100, yaw -1.5708, stride 1.1 / 2.8, look Neck/Head, impact 0.533 s = hattack2 Rattack); script clips `talk`, `cower` and his scene clips under their MM9 names (`sc3_hanndl07` ... `hanndl06`) |
| Descriptor | row 260 added to `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback 555, the stand-in the maps use), tables regenerated: 9260 |
| Triangles LOD0/1/2/3 | 8,560 / 4,279 / 1,536 / 509 (Annud's mesh: no faces added or removed) |
| Clips (30 fps, soft offset line) | PeasantMale (`source/mm9_lib/pmale.glb`): Standing stand1, Walking walk3 (also WG_NPC334's `Walkto`), Running run, Fidget fidget4, Talk conv2, AttackMelee hattack2, Hit wince1, Death die1, Dead, Cower cower (basemelee.scr -> BaseRun.inc `LoopAnim Cower`). His own HANNDL.abc clips (`source/mm9/hanndl.glb`) that his scripts play: Hanndl.scr (lose-game, writ-of-fate and present-writ cinemas) Sc3_hanndl07, sc3_Hanndl08, sc4_hanndl09-15, sc5_Hanndl16-17; WG_NPC334.scr (win-game scene) Hanndl01-06. NPC334.scr plays none. Left out: `Hanndl` (bind clip), `Hanndlshot17(no voice)`, `Hanndlshot19` (no script plays them) |
| Textures | body 2K colour + 1K normal + 1K ORM on Annud's texture-pass UVs (repainted); head + hands set on Annud's head UVs (repainted head, Annud's hand texels toned to Hanndl's cheeks) |
| Meshy credits | **20 / 20**: body retexture 4K 10, head retexture 4K 10 (backup account; balance 3245 before the first job, 3235 before the second) |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_hanndl_claude/review/viewer/ |

## Route (project folder unless noted; nothing written into mm9_annud_claude)
0. Sources `source/mm9/hanndl.glb` (`convert_abc_model.py --id hanndl --scale 0.0256 --texture 0=HANNDL.dtx`); MM9 renders
   `scripts/ref_sheets.sh` -> `references_hd/mm9_views.png`, `mm9_head_views.png`, `mm9_skin_x4.png`.
1. **HD masters** (Codex via `codex_slot.sh`, `scripts/codex_masters.sh <project> 1|2` with `SHAPE=mm9_annud_claude`, brief
   `references_hd/CODEX_BRIEF.md`): design from the MM9 renders (calm expression asked for: MM9's face grimaces), pose and body
   from Annud's HD masters except the sleeves (fitted, no bell). Head turnaround `references_head/` (`scripts/codex_head.sh`).
   `scripts/clean_alpha.py` -> `*_clean.png` (the Meshy inputs).
2. **Sleeves** `scripts/narrow_sleeves.py master ../mm9_annud_claude/v2/work/sleeves_v2.blend work/master_v1.blend
   work/narrow.json` (vertex moves only): per arm, the forearm centre line and radius are fitted to Annud's forearm stub inside the
   sleeve; every sleeve vertex's distance beyond the stub is mapped through e*(1-exp(-d/e)) (monotone, so the inner and outer
   layers keep their order), ease e 2.4 cm below the elbow to 1.3 cm at the cuff, blended in from 0.15 above the elbow to 0.25 down
   the forearm. Outer radius at the cuff 11.4 -> 5.0 cm (L), 10.7 -> 5.1 cm (R); max move 6.4 cm. The same displacement on
   Annud's body upload (`narrow_sleeves.py upload`, exact rest-position match): `v2/texturing/hanndl_body_upload.glb`, UV set
   identical (`scripts/upload_check.py`: 25,212 corners, 287 moved, UVs equal). Head: Annud's head upload unchanged.
3. **Paint**: `v2/requests/retexture_body.json`, `retexture_head.json` (4K, meshy-7, our UVs); `bake_ao_texpass.py` on
   `work/master_v1.blend`, `compose_texpass.py hanndl`, gentle grade, `compose_head_texpass.py annud_tp hanndl`, then
   `scripts/fix_beard_net.py hanndl work/texpos_head.npz` (Meshy drew the beard's sides as a net of crossing white strands on skin;
   in the beard zone by rest position the strands are thickened and mixed with the local beard colour, weighted by the smooth beard
   density) and `scripts/hand_tone.py hanndl 1.0 work/texpos_head.npz -0.009`.
4. **Clips**: `v2/scripts/roles_hanndl.json` (Annud's roles + Cower + 17 own clips, `soft_offsets`). `v2/scripts/clips_mm9.py`
   gained an opt-in role key `fingers_from` ([source, clip]): 13 of the HANNDL.abc clips key the mitten `Finger1` turned 180 deg
   (with `Finger11` bent 88 deg), a broken five-finger hand (finger stretch 5.45); their finger channels take stand1's first key.
5. **Runtime**: `ARMCLEAR_CLIPS=Standing,Walking,Running,Fidget,Talk,AttackMelee,Hit,Death PYGLTF_PYTHON=../claude_shared/gltf_venv/bin/python
   TOKEN=<lease> HEADTEX=hanndl BODYTEX=hanndl BLEND=work/master_v1.blend v2/scripts/build_runtime_v2.sh hanndl Hanndl
   v2/scripts/roles_hanndl.json` (this project's copy: `ARMCLEAR_CLIPS` keeps Annud's accepted `arm_clear.py` passes on his base
   clips only; then `v2/scripts/hand_rest_hanndl.txt` (Hanndl04) and `v2/scripts/abduct_hanndl.txt` (`scripts/arm_abduct.py`: a
   constant 5-8 deg right upper-arm abduction, eased over 0.3 s at the clip ends, in Hanndl02/03/04/06, where MM9's hand at the
   thin MM9 hip dips into the HD tunic skirt; hand_rest.py and arm_clear.py do not see the skirt). Then `check_winding.py`, install,
   binding, viewer (`make_viewer_v2.py`).

5b. **Stub tuck** `scripts/sleeve_tuck.py work/master_v1.blend work/master_v2.blend 0.74 0.004` (PeasantM7's script): after the
   narrowing, Annud's forearm stub came through the right sleeve (sleeve_poke_gate 5.2 mm at rest, 7.8-12.5 mm in Fidget,
   AttackMelee, Cower); the narrowing also clamps every sleeve vertex 1.6 cm outside the stub in its own direction (the chord sag
   of the low-poly sleeve ring). The tuck draws the stub in and gives its upper part the sleeve's weights. AO re-baked on
   `work/master_v2.blend`, body maps recomposed from the same Meshy maps.
5c. **Linings** `scripts/linings.sh` (PeasantDM2's `neck_cap.py` and `rim_lining.py`, copied): the head shell's open neck capped,
   the collar loops lined (band 30 cm) and the belt band's two rims lined (band 12 cm; a one-region mask
   `textures/hanndl_lining_mask.png` stands in for DM2's tier mask) -> **`work/master_v3.blend` (the master)**. Annud's body has no
   open rim at the cuffs or the tunic hem. The lining faces would change what arm_clear.py sees inside the body (Fidget's
   accepted correction grew from 6 to 19 deg), so the build takes the clips of the accepted master_v2 build
   (`v2/work/clips_accepted_lod0.glb`, grafted by `claude_shared/graft_clips.py`: `CLIPS_FROM` in this project's build script;
   posed difference 0.1 mm). DM2's `shrink_shadow_lods.py` (drops the one-texel lining triangles from the shadow meshes) and
   pm1d's `fix_winding.py` (two near-zero-volume lining remnants in LOD1/LOD2 turned outward) are in the build.
   Final build: `CLIPS_FROM=v2/work/clips_accepted_lod0.glb ... BLEND=work/master_v3.blend v2/scripts/build_runtime_v2.sh hanndl
   Hanndl v2/scripts/roles_hanndl.json`; to rebuild the clips themselves, build master_v2 with `ARMCLEAR_CLIPS` (step 5) first.

## Checks (final GLB, sha256 99c719f1...)

| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only --exact`, 48 fps, `v2/review/gates/arm.txt`; Hanndl06 rerun after its last change) | base clips as Annud's installed GLB with the same options (Talk R 3.2 cm / 26 frames vs Annud 3.1 / 26: MM9's conv2 hand; forearms in the sleeves lower than Annud's: Talk 3.7 vs 5.0 cm); all 17 own clips and Cower: hands 0; Hanndl04 R forearm 6.0 cm at frame 506 (sleeve against the tunic: cloth on cloth, as Annud's accepted forearms); finger stretch max 3.35 (Fidget, Annud's value; own clips 1.67 after `fingers_from`, were 5.45); 19 chains per hand |
| Jitter (`jitter_gate.py` vs MM9's untouched clips) | before the linings: the same 7 side-fails in the same base clips as Annud's accepted GLB (Walking/Death shoulder skin, Fidget R arm_clear, Talk L); 0 fails in Cower and the 17 own clips (the abduction eases add at most 0.78 deg/f over MM9). Lined GLB: the same plus Hit R shoulder-skin p95 2.37 mm/f2 (limit 2.0) with 0 arm excess: the lining vertices weighted to the clavicle join the shoulder-skin sample; the clips are identical |
| Sleeve poke (`sleeve_poke_gate.py`, 48 fps, every clip) | rest 0 mm both sides (5.2 mm before the clamp and tuck); Fidget R 7.7 mm on 6 frames (3 vertices: the wrist meets the cuff lip as MM9's fidget bends the wrist 68 deg) and AttackMelee L 1.2 mm on 9 frames; every other clip 0 |
| Detached parts (`detached_parts_audit.py`) | before the linings: the right hand part (870 triangles) opens up to 2.5 cm from the body cluster in 25 of 3,161 poses (Talk, Fidget, AttackMelee, Hanndl04); Annud's GLB: none in those clips. A consequence of the narrowed sleeve (the stub no longer touches the old wide cuff wall); the see-through gate is the visual check (no hole at the right cuff in those clips). Lined GLB: the right hand part in 16 poses (Talk 2.1 cm, Hanndl04 2.5 cm); the components' 'root lift' notes are the linings (DM2 saw the same artifact) |
| Floor (`floor_audit.py --world mm9 --match 'MM9 260 *'`) | ok: stand 0, walk -0.0..+0.0, living 0, dead 0 (Annud's row the same) |
| Winding | 0 inverted closed parts |
| `texture_quality.py` | lined GLB: body p10 density 0 and huge spread come from the one-texel lining triangles (as DM2's); before the linings: body atlas 59.4 % (Annud's layout), density p10/p50/p90 1354/1402/1496, spread 1.10, fragments 0.1 %, stretch p90 1.16; head set: the same numbers as Annud's installed head (40.9 %; its p10 0 and huge stretch come from the export_fix hole/mouth patches that sample one texel: inherited) |
| Viewer `run_creature_review.py check` (revision `v4-lined-20261102`) | 27 switches, 0 failed, 0 console errors |
| Regression `--world mm9 --headless-run-regression-suite actors` | passed 192, failed 1 (the known `out05_event_clearance_completes_from_monster_killed_hook` "could not load gameplay data"; `review/regression_actors.log`); after the final (lined) install `mm9_actor_models_build_every_binding` PASS, 204 descriptors on 90 models (`review/regression_binding_final.log`) |
| See-through (`scripts/see_through_gate.py` step 4, 8 azimuths x 0/20 deg) | unlined, every clip (`v2/review/gates/see_through/`): worst corpse views (Death, from the feet) torso 72 px, sleeve R 28, collar 23; standing clips sleeve L 3-10, torso 4-13, collar 1-3. Annud's installed GLB on Standing/Talk/Death: torso 67, sleeve R 26, collar 20, sleeve L 6-17: inherited. Lined (`see_through_lined/`, 12 clips incl. Hanndl04, Sc4Hanndl12): collar 0 (Fidget 1), torso 3-8 standing / 16 corpse, sleeve R 17 corpse only, sleeve L 3-10 (thin slivers at the left cuff opening), trousers 2; images read: single-pixel slivers along the belt band and the cuff lip, a thin arc at the corpse's back hem |

Sheets (read): `review/sheet_mm9_vs_ours.png` (MM9 Hanndl vs ours, five views), `review/final/head.png` (bind and Talk 60),
`review/final/ears.png` (ears, under the jaw, party view), `review/r3/ears.png` (beard net before/after), `review/r3/hands.png`
(finger fix: Sc4Hanndl09 before), `review/r4/c.png` (hands at the skirt before the abduction), `review/r5/sleeves.png`,
`review/r6/f.png` (fitted sleeves and cuffs in Fidget/AttackMelee/bind), `review/sheet_viewer_shots.png` (viewer: Standing, face,
Talk, Walking, Sc4Hanndl12, Hanndl04).

## Approved model untouched
`mm9_annud_claude/` was only read (master blend, uploads, head set, scripts and sources copied). `assets_source` and `assets_dev`
`mm9_annud.glb` sha256 are the same before and after; the `MM9 54 Shopkeeper` binding was not edited.

## Open points / not checked
- Sleeve length: Annud's Meshy sleeves end at mid-forearm (his bell sleeves), so Hanndl's fitted sleeves show ~6-8 cm of bare
  forearm above the hand; MM9's and the HD master's sleeves (lattice and gold cuff) reach the wrist. Lengthening them needs new
  sleeve geometry and paint (no budget left).
- The fur mantle is paint only (Annud's tunic shoulders have no fur volume) and reads as spiky quills up close.
- The throat: looking up from under the jaw the V of the collar shows the background (Annud's installed GLB the same).
- Annud's rope-belt tassels hang below Hanndl's painted buckle (geometry kept).
- The beard fix leaves a soft, slightly flat patch where the sideburn meets the cheek.
- No in-game run; LOD1-3 and shadow meshes not looked at; normal-speed playback not watched; the scene clips' sync with
  the cinema scripts (cameras, Krohn) not checked.
- Map placement (row 260 still placed as legacy 555) is the orchestrator's.

User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_hanndl_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_hanndl_reduce_claude/before/`.
