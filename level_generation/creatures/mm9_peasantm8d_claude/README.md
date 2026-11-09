# MM9 PeasantM8d, the old elf commoner (mm9_peasantm8d) — 3D actor variant, 2026-11-02

MM9 `PEASANTM8D.abc` + `PEASANTM8D.dtx`, the only `MONSTERS.txt` row naming it: **23 Commoner** "Peasant Elf MaleA B"
(NPCbase.scr, PeasantMale library; DAT class `CommonerElfMaleB`, 8 placements in Arslegard City, Yorwick, Lindisfarne and
Thjorgard City, all with an empty ScriptName, so NPCbase.scr). Batch: `devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md`
(shared-mesh variants; no new body). Owner variants-b. Progress and Meshy receipts: `creature_3d_progress.json`.

**Same mesh as ForadDarre** (re-run of the orchestrator's comparison, `meshcmp.py peasantm8d:foraddarre`): torso, arms and legs
p90 0.3 cm (max 0.3 / 1.3 / 0.3 cm), head 6 % of the samples over 1.5 cm, max 4.2 cm. Vertex-level (`vdiff.py`): 7 head
vertices per side differ, the MM9 elf ear fan (tip at 11.8 cm out, 83.3 cm up, 3.5 cm back; Forad's ear vertex at 8.3 cm out),
and the hands are 1.4-1.9 cm larger (irrelevant: our hands are grafted MPFB hands). So this model is **Forad's approved v3.4 body,
MM9 skeleton, weights and clip choice** (`../mm9_forad_claude/`, never written to) with elf ears, no necklace and its own paint.
Different person and clothes from Forad (old white-haired elf with a walrus moustache, green flecked tweed tunic over cream linen
sleeves, brown belt, torn brown ribbed breeches, cuffed boots), so a new body paint and a new head paint (20 credits).

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantm8d.glb` (`tools/install_model.py --world mm9 --name mm9_peasantm8d.glb`), identical to `v2/export/mm9_pm8d.glb` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` `MM9 23 Commoner` (block `scripts/binding.yml`, `scripts/bind_under_lock.sh` under the flock): Forad's values (scale 100, yaw -1.5708, stride 1.05 / 3.8, look Neck/Head, impact 0.5 s = hattack1 Rattack); script clips `talk` Talk, `cower` Cower |
| Descriptor | row 23 added to `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback 341, the stand-in the maps use), tables regenerated: 9023 |
| Triangles LOD0/1/2/3 | 7,834 / 3,916 / 1,408 / 465 (Forad 8,397: 39 necklace beads and the two eyeball cups gone) |
| Clips (30 fps, PeasantMale `source/mm9_lib/pmale.glb`, soft offset line) | Standing stand1, Walking walk3, Running run, Fidget fidget1, Talk conv1 (Forad's hand rest), AttackMelee hattack1, Hit wince1, Death die1, Dead, Cower cower (NPCBase.inc -> BaseRun.inc `LoopAnim Cower`). Forad's story clips (bow, sit, agree, applause, argument scenes) are not played by this commoner and are left out |
| Textures | body 2K colour + 1K normal + 1K ORM on Forad's texture-pass UVs (repainted); head + hands set 2K colour + 1K normal/ORM on new head UVs (ears changed shape) |
| Meshy credits | **20 / 20**: body retexture 4K 10, head retexture 4K 10 (backup account; balance 3285 before the first job, 3275 before the second) |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm8d_claude/review/viewer/ revision `v1-20261102` |

## Route (project folder unless noted; nothing written into mm9_forad_claude)
0. Sources `source/mm9/pm8d.glb` (`convert_abc_model.py --id pm8d --scale 0.0256 --texture 0=PEASANTM8D.dtx`); MM9 renders
   `scripts/ref_sheets.sh` -> `references_hd/mm9_views.png`, `mm9_head_views.png`, `mm9_skin_x4.png`.
1. **HD masters** (Codex via `codex_slot.sh`, `scripts/codex_masters.sh <project> 1|2` with `SHAPE=mm9_forad_claude`; brief
   `references_hd/CODEX_BRIEF.md`): design from the MM9 renders, pose/body/hair-volume authority from Forad's own HD masters (so
   the paint projects onto Forad's mesh: same arm angle, ponytail volume). Head turnaround `references_head/` (`scripts/codex_head.sh`,
   shape authority Forad's head sheet). Alpha halo removed: `scripts/clean_alpha.py` -> `*_clean.png` (the Meshy inputs).
2. **Geometry** `scripts/elf_ears.py master ../mm9_forad_claude/v2/work/sleeves_v2.blend work/master_v1.blend work/elf_ears.json`
   (vertex moves only on Forad's ear vertices: the lateral HeadUV ear islands, the right ear completed by mirroring the left;
   tip (2.2 out, 1.8 back, 3.2 up) cm x smoothstep of the height in the ear x a root fade over 2 edges, upper ear narrowed; max
   move 4.5 cm, the MM9 difference is 4.2-4.9 cm), and in the same pass the 39 necklace bead parts and Meshy's two eyeball cups
   deleted (Forad's export dropped the cups by part number; `v2/scripts/head_pm8d.json` drops nothing). Clay before/after: the
   `ears_cmp` sheet in the session scratchpad (not kept); textured ear close-ups below.
3. **Head UVs** `v2/scripts/texpass_head_uv.py work/master_v1.blend v2/work/head_uv.blend v2/texturing/pm8d_head_upload.glb`
   (new layout: the ears changed; hands keep Forad's HeadUV squares). **Never re-run**: the paid head paint belongs to it.
   Body: Forad's texture-pass UVs and his upload `v2/texturing/forad_body_texpass_upload.glb` (copied) unchanged.
4. **Paint**: `v2/requests/retexture_body.json`, `retexture_head.json` (4K, meshy-7, our UVs); `v2/scripts/bake_ao_texpass.py`
   on `work/master_v1.blend`, `compose_texpass.py pm8d`, `grade_basecolor.py` gentle (`--fine 1.0 --local 0.3 --ao-strength 0.5
   --contrast 1.06 --saturation 1.15`), `compose_head_texpass.py forad_tp pm8d` (Forad's hand texels kept), then
   `scripts/hand_tone.py pm8d 1.0 work/texpos_head.npz -0.017` (hands toned to the new cheeks: Forad's tanned hands read dark
   brown against the old elf's rosy face; `scripts/texel_pos.py` gives the texel positions).
5. **Lining texel** `scripts/lining_texel.py v2/work/head_uv.blend v2/work/master_v2.blend textures/pm8d_basecolor_graded.png`:
   Forad's bracer lining and cuff-rim faces (sleeve_lining.py) sampled one black texel; on cream cuffs that was a black fin at the
   wrist, so they point at the cuffs' median texel. **`v2/work/master_v2.blend` is the master.**
6. **Runtime**: `PYGLTF_PYTHON=../claude_shared/gltf_venv/bin/python TOKEN=<lease> HEADTEX=pm8d BODYTEX=pm8d
   BLEND=v2/work/master_v2.blend v2/scripts/build_runtime_v2.sh pm8d PeasantM8d v2/scripts/roles_pm8d.json` (Forad's shared
   script; `v2/scripts/hand_rest_pm8d.txt` = Forad's Talk line; `scripts/floor_ops.txt` without Bow, with Cower), then
   `check_winding.py`, `tools/install_model.py ... --name mm9_peasantm8d.glb`, binding under the flock, viewer `make_viewer_v2.py`.

## Checks (final GLB)

| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only --exact`, 48 fps, `v2/review/gates/arm.txt`) | identical to Forad's installed GLB run with the same options: hands 0 in every clip except **Talk L 3.5 cm, 40 frames** (MM9's hand on the heart: Forad's accepted Talk, same 3.5 cm / 40 frames on `mm9_forad.glb`); Fidget R forearm 1.2 cm; finger stretch max 2.91; 19 chains per hand |
| Jitter (`jitter_gate.py` vs MM9's untouched clips, `v2/review/gates/jitter.txt`) | the same fails as Forad's accepted clips, same numbers (Talk L upper arm 9.07 vs Forad 9.09 deg/f; Walking and Death shoulder-skin p95): no new fail; Cower passes |
| See-through (`scripts/see_through_gate.py` step 3, 8 azimuths x 0/20 deg, `v2/review/gates/see_through/`) | head 0, torso 0, boots 0, trousers 0; sleeves: single-frame slivers at the bracer rim (R 10 px Running 6, 9 px AttackMelee 15; L 4 px Talk 33), images read: thin edge slivers |
| Sleeve poke (`sleeve_poke_gate.py`, every clip, `v2/review/gates/sleeve_poke.txt`) | rest 0; the hand meets the bracer/cuff when MM9 bends the wrist (Talk L 17.2 mm, Hit R 22.5, Death/Dead R 24.1, Fidget L 6.7, Running L 8.5): identical to Forad's installed GLB (Talk L 17.4, Hit R 22.5, Death R 24.1, Fidget L 6.7). Close-ups `review/r4/p.png`: the back of the hand slides into the cuff, no skin shows through the cream sleeve |
| Floor (`floor_audit.py --world mm9 --match 'MM9 23 *'`) | ok: stand 0, walk -0.0..+0.0, living 0, dead 0 (Forad's row the same) |
| Detached (`detached_parts_audit.py`) | 0 detached (6 components) |
| Winding | 0 inverted closed parts |
| `texture_quality.py` | body atlas 53.3 % (Forad 53.5 %, same layout less the beads), density p10/p50/p90 1502/1553/1598, spread 1.06, fragments 0.0 %, stretch p90 1.09; head set atlas 45.1 % (Forad 43.9 %), fragments 2.4 %, stretch p90 1.23 |
| Viewer `run_creature_review.py check` | 10 switches, 0 failed, 0 console errors |
| Regression `--world mm9 --headless-run-regression-suite actors` (after both variants' installs) | passed 192, failed 1 (the known `out05_event_clearance_completes_from_monster_killed_hook`); `mm9_actor_models_build_every_binding` PASS, 198 descriptors on 86 models (`../mm9_hanndl_claude/review/regression_actors.log`, `regression_binding_final.log`) |

Sheets (read): `review/sheet_mm9_vs_ours_r1.png` (MM9 PeasantM8d vs ours, five views), `review/r1/head.png` (bind and Talk 60:
front, profiles, 3/4, eyes, mouth, both neck sides), `review/r1/ears.png` (both ears, close-ups, 3/4 backs, under the jaw,
party view), `review/r3/hands_sheet.png` (hands after the tone and lining fixes), `review/sheet_viewer_shots.png` (viewer:
Standing, face, Talk, Walking, Cower, AttackMelee).

## Approved model untouched
`mm9_forad_claude/` was only read (its master blend, uploads, head set, scripts and sources copied in). `assets_source` and
`assets_dev` `mm9_forad.glb` sha256 are the same before and after this work (see the status file); the `MM9 252 Forad Darre`
binding was not edited.

## Open points / not checked
- Elf ears are Forad's human ears drawn into a point (no new geometry): the right ear of Forad's mesh is flatter, so it stands
  out less from the side than the left. A few white hair strands are painted across the front of each ear (sideburn locks).
- Forad's open-vest geometry (standing lapels, the chest between them) is painted as a closed tunic; the lapel edge shows as a
  faint vertical fold. The tunic's short cap sleeves are paint on Forad's vest shoulders.
- The hand texture carries Forad's faint zig-zag graft seam on the back of each hand (Forad's installed hands show it too).
- No in-game run; LOD1-3 and shadow meshes not looked at; normal-speed playback not watched (motion = Forad's accepted clips).
- Map placement (rows still placed as legacy 341) is the orchestrator's (see `../mm9_peasantm1d_claude/README.md`, "Binding plan").

User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantm8d_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantm8d_reduce_claude/before/`.
