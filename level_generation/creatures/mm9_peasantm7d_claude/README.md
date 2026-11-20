# MM9 elf townsman PeasantM7d (mm9_peasantm7d) — 3D actor, 2026-11-02

Variants batch (`devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md`). MM9 `MONSTERS.txt` rows naming `PeasantM7d.abc`: **25 Town**
"Peasant Elf MaleB B" (skin PEASANTM7D, DAT class `TownElfMaleB`, 3 objects) and **27 Shopkeeper** "Peasant Elf MaleC B" (skin
PEASANTM7C, DAT class `ShopkeeperElfMaleB`, 4 objects). Mesh comparison (`meshcmp.py peasantm7:peasantm7d`, re-run): body
identical (0.2 cm), head 4 % of vertices over 1.5 cm, max 5.3 cm = the elf ear tips (54 MM9 vertices, all on `Bip01 Head`).
So this is **PeasantM7's approved body** (`../mm9_peasantm7_claude/`, rows 51/53: mesh, rig, weights, MM9 PeasantMale clips,
hands, sleeve fixes) **plus two elf ears**, two new faces and two body tiers, installed as its own GLB.
Progress and Meshy receipts: `creature_3d_progress.json` (lease identity `mm9:peasantm7d`).

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantm7d.glb` (`tools/install_model.py --world mm9 --name mm9_peasantm7d.glb` from `export/mm9_pm7d.glb`), sha256 `07e75223bfe1caf2...` (v2: ear normals fixed, linings); v1 `b5c57394...` kept as `work/installed_v1_prelinings.glb` |
| Variants | `pm7d_d` (row 25), `pm7d_c` (row 27) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` (`scripts/binding.yml`, `scripts/bind_under_lock.sh` under the flock): `MM9 25 Town` (pm7d_d), `MM9 27 Shopkeeper` (pm7d_c); PeasantM7's scale 100, `yaw_offset -1.570796327`, stride 1.1 / 2.8, look Neck/Head, impact 0.533 s |
| Descriptors | rows 25 (stand-in 344) and 27 (347) in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`, tables regenerated: 9025 / 9027 |
| Triangles LOD0/1/2/3 | 9,630 / 4,813 / 1,733 / 577 (PeasantM7's 7,313 + 588 ear triangles + 1,729 lining triangles at the boot tops and the belt) |
| Clips | PeasantM7's: Standing stand1, Walking walk3, Running run, Fidget fidget4, Talk conv2, AttackMelee hattack2, Hit wince1, Death die1, Dead, Cower cower |
| Textures | body = PeasantM7's paint (2K colour + 1K normal/ORM) + new 1K region mask (R tunic, G collar/placket/hem, B breeches, A sleeves) + ramps per tier; head + hands set 2K colour + 1K normal/ORM per tier (D the base head material, C its own colour + normal via `tier_head.py`) |
| Meshy credits | **20** (two 4K head retextures, D and C; backup 3195 before the first, 3175 after the second; other agents spending too). No body job: the body paint is PeasantM7's |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm7d_claude/review/viewer/ revision `v2-20261102`, tiers pm7d_d, pm7d_c |

## Clips the rows play
DAT objects (`scripts/dat_objects.py "(Town|Shopkeeper)ElfMaleB"`): 2 without a script (NPCbase.scr -> BaseRun.inc `LoopAnim
Cower`), Shopkeeper.scr (BaseWander: marker animations, none named), Arena.scr, NPC185.scr, NPC196.scr, NPC209.scr (animation from
ScriptParams, empty). So PeasantM7's core roles + Cower; its Conv1/Conv4/Conv5 (NPC110/NPC213/Ralof) are not carried
(`scripts/roles_pm7d.json`, `hand_rest_pm7d.txt`, `floor_ops_pm7d.txt` = PeasantM7's without those clips).

## Route (scripts/, repo root for Blender via `scripts/bl.sh`, else project folder)
PeasantM7's scripts are copied into `scripts/` unchanged unless named here. PeasantM7's files are read only.
1. **Ears** `scripts/add_ears.py <M7 master work/texpass_head_tuck.blend> work/ears_v3.blend texturing/... root=0.075,0.004,0.779
   tip=0.141,0.042,0.863 width=0.046 press=1` -> **master `work/ears_v3.blend`**: PeasantF8's procedural cupped elf ear (leaf with
   a rolled rim), one per side, mirrored about the face midline (the eye shells' mean x, -0.0111), 11.3 cm long, root inside the
   skull where Meshy's human ear was, tip out, back and up through the hair as MM9's; rigid on `Bip01 Head`; faces appended
   (PeasantM7's vertices, faces, weights and UVs untouched, ids kept); HeadUV islands in the free band above the head islands
   (v 0.81-0.88, head density). `press=1`: Meshy's small human ears (on the face shell under the elf ear roots) pressed onto the
   skull (50 vertices, at most the cheek's distance from the midline + 2 mm): with them, each side showed two ears.
   **v4** (`work/ears_v4.blend`): the hand-built ear winding was inside out on both ears (all 588 faces; the first see-through
   gate saw their back faces from outside: in game they would have shown their inside); `bmesh.ops.recalc_face_normals` now
   orients them outward. Positions and UVs as v3.
1b. **Linings** `scripts/linings.sh` (repo root; PeasantDM2's `rim_lining.py` unchanged) -> **master `work/linings_v1.blend`**:
   boot tops (both rims at each knee, band 30 cm, region B) and the belt seam where the upper tunic meets the skirt (band 12 cm,
   region R). Geometry added only (+1,729 triangles). A collar lining was tried and dropped (no collar holes; it made four
   near-zero-volume shells that check_winding counts as inverted). `shrink_shadow_lods.py` is PeasantDM2's newer copy (drops the
   linings' one-texel triangles from the shadow meshes).
   The head upload (`texturing/pm7d_head_upload.glb`, head faces + ears, UV = HeadUV) came from the first run (v2, ear root 2.6 cm
   further back): PeasantM7's head UVs are the same in v2 and v3; the ear islands differ by under 0.5 % in size (v3: 0.1547 x
   0.0587), which does not matter because `ear_paint.py` repaints the ear islands from v3's own UVs.
   Clay checks `review/ears_v2_sheet.png`, `review/skull_sheet.png` (v2: two ears) -> `review/skull_sheet3.png` (v3).
2. **Head masters** (Codex, `scripts/codex_head.sh d|c`, brief `references_head/CODEX_BRIEF.md`; resume `codex_head_back.sh`
   after a "model at capacity" stop): edits of PeasantM7's four accepted head views with the ears from `references_head/
   ear_shape_views.png` (red clay renders of our ears). Halo removed, then `scripts/align_masters.py` (silhouette affine, IoU
   0.75-0.83 -> 0.90-0.96) and for C's front `scripts/align_face.py` (feature alignment: the silhouette fit had left the eyes
   ~12 px high) -> `references_head/clean/` (D), `references_head_c/clean/` (C). Calm, warm expressions.
3. **Head retextures** (4K) on that upload: `requests/retexture_head_d.json`, `retexture_head_c.json`.
4. **Head maps**: `compose_headhand.py pm7d_tp|pm7dc_tp ... --ref-head --hand-gain 1.12 --head-scale 1.0` (the upload is HeadUV
   1:1), `hand_clean.py 0.95 <head colour>` (PeasantM7's, with blond hair kept out of the skin reference by hue), then
   **`scripts/ear_paint.py pm7d_tp pm7dc_tp`** (reads `*_preear.png`; needs `work/ear_faces.npz` from `ear_dump.py`,
   `work/press_faces*.npz` from `press_dump.py`):
   - ear islands: the retextures painted blond strands (D) or half hair (C) on them; MM9's elf ears are plain skin: procedural
     skin from the tier's own cheek skin x cup/rim/root shading x fine noise, flat normal, skin roughness;
   - pressed human ears: their faces take the surrounding skin (normalised convolution) by a press weight;
   - hair shell near the ear roots: skin-hued texels (the views put the elf ear's base on the hair's side edge) take hair texels
     mirrored across the nearest hair border;
   - neck: the views' high gold brocade collar painted on the neck skin below z 0.715 -> surrounding skin (20 px normalised
     convolution);
   - throat panel: PeasantM7's undershirt collar piece in the tunic's V (head set) was painted as skin (a pale flat plate under the
     chin): it takes PeasantM7's own approved paint there (its non-skin texels below z 0.70).
   Then `scripts/eye_rims.py pm7dc_tp` (0.7) and `pm7d_tp 0.5`: the saturated red ring round the eyes (wave-1 lesson) moved toward
   the cheek skin's hue (needs `work/head_faces.npz`, `head_dump.py`).
5. **Body tiers** `scripts/tier_pm7d.py work/mm9_t7_unmirrored.glb PeasantM7` (PeasantM7's tier_pm7.py method on PeasantM7's
   paint `textures/pm7d_tp_basecolor_graded.png` = `pm7_tp_basecolor_graded.png`; target per texel = MM9 skin X's colour at the
   texel's luminance quantile in the region x our luminance / MM9 skin B's): R tunic, G collar/placket/hem band, B breeches,
   A **sleeves** (new: the tunic class beyond a plane 3 cm inside each shoulder joint, within 11 cm of the arm axis; C's sleeves
   are gold, its tunic plum). `work/mm9_t7_*` is a byte-identical rebuild of PeasantM7's installed GLB from its master (sha256
   `35e99c36...` = installed), used for texel positions only.
6. **Runtime** `TOKEN=<lease> BLEND=work/ears_v3.blend scripts/build_runtime_pm7d.sh [--install]` (PeasantM7's chain: export,
   `clips_mm9.py` soft offsets, `hand_rest.py`, prepare, LODs, shadow LODs, extras, `region_variants.py`, `tier_head.py`
   (pm7d_c=pm7dc_tp), `floor_fix.py`, `mirror_glb.py`, winding). Viewer: `scripts/viewer_variant.py export/mm9_pm7d.glb
   review/viewer/<tier>.glb <tier>` (ramps baked), `scripts/make_viewer_pm7d.py <rev>`.

Texture chain when a head paint changes: compose_headhand -> hand_clean -> (delete `*_preear.png`) ear_paint -> eye_rims -> build.

## Approved PeasantM7 unchanged (proof)
`assets_source/worlds/mm9/models/mm9_peasantm7.glb` sha256 `35e99c36e8e14a1f...` before and after (= its `export/mm9_pm7.glb`);
no file in `../mm9_peasantm7_claude/` is newer than this lease; PeasantM7's master was only opened read-only (outputs went to
this project). Its binding block in actors.yml is untouched (rows 25/27 are a new block).

## Checks (`review/gates/`, final build)
| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only`, 48 fps) | hands 0 frames over 1 cm in every clip except **Fidget R 2.2 cm, 10 frames** (MM9's chin scratch; PeasantM7's installed GLB measures the same 2.2 cm / 10 frames with today's gate script); forearms 0; finger stretch max 3.14; wrist max 119 deg (MM9's limp death hand); 19 chains per hand |
| Jitter (`jitter_gate.py` vs MM9's untouched clips) | **0 fails** (PeasantM7's two fails were Conv1/Conv5, not carried) |
| Sleeve poke (`sleeve_poke_gate.py`) | 0 mm, 0 frames, all 10 clips, both sides |
| Floor (`floor_audit.py --world mm9 --match 'MM9 2[57] *'`) | both ok: stand 0, walk -0.1..+2.4, living -0.1, dead 0 |
| Winding | 0 inverted closed parts |
| Bones | 12 checked, 0 stretching |
| Detached | 0 detached (23 components); notes only (the boot linings' root-lift/concealed notes, the hair shell rigid on the head) |
| Flat shading | 0.00 on both materials |
| Texture quality | body atlas 55.7 % (PeasantM7's layout; the linings' one-texel UVs make the density spread and fragments meaningless: 1.08 and 0.0 % without them); head set 43.7 % (41.2 + the ear islands), spread 2.88, fragments 2.5 %, stretch p90 1.31 |
| Tier ramp fit (8-bit mean / p95) | tunic D 0.22/0.42, C 0.13/0.22; collar D 0.97/2.33, C 0.98/2.25; breeches 0.12/0.30; sleeves D 0.34/0.76, C 0.18/0.33 |
| Viewer check | 20 switches, 0 failed, 0 console errors |
| Binding regression `mm9_actor_models_build_every_binding` | **PASS** on the final install, 198 descriptors on 86 models (`review/gates/regression_binding.log`); full `actors --world mm9` suite (on the v1 install): 192 pass, 1 known fail (out05 "could not load gameplay data"), `review/gates/regression_actors_full.log` |
| See-through (`scripts/see_through_gate.py`, PeasantDM2's; every 3rd 30 fps frame of all 10 clips, 8 azimuths x level/20 deg, 3 mm pixels; `review/gates/see_through/`, before in `see_through_before/`) | worst background pixels per zone, v1 -> v2 (ears outward + linings): boot L 48 -> 4, boot R 19 -> 10, trousers R 42 -> 8, trousers L 2 -> 0, sleeve R 7 -> 7, sleeve L 4 -> 4, torso 19 -> 19 (Hit 18 from 135 deg: a sliver at the tunic's side slit), head 14 -> 14 (Death 15: a few px at the crown seen from below; specks at the open ear roots from behind in Death 3). Frames with boot holes 56/55 -> 1/3. Remaining are single slivers at silhouette edges; not chased further |

Sheets read: `review/sheet_mm9_vs_ours.png` (MM9 D/C vs ours, front, q34, back), `review/first_body_pm7d_{d,c}.png`,
`review/sheet_face.png` (both tiers, Standing/Talk: face, q34, eyes, mouth; after eye_rims), `review/sheet_ears_big8.png` (both
ears, close ears, 3/4 back, party view), `review/sheet_throat.png` (front, party, under the jaw), `review/neck_both.png`,
`review/skull_sheet3.png`, `review/head_blend_m7.png` (aligned views on PeasantM7's), `review/sheet_ears_final.png` (v2: outward
ears), `review/sheet_linings.png` (knees in Running/Cower from behind and the front, the belt from 135 deg and the front, a red-twin
knee view; both tiers), `review/see_through_worst.png` (v1 gate's worst frames).

## Deviations and open points
- **Ears are procedural** (PeasantF8's generator), skin-painted procedurally; MM9's are flat cards. From some angles the
  cupped front reads a little darker than the cheek.
- The hair shell's side edge next to the ear roots was repainted from mirrored hair texels: up close a slightly repeated strand
  pattern there.
- Hair is PeasantM7's hair shell (volume and outline) with blond paint; MM9's elves have a slightly longer, lighter mop.
- The faint jaw/under-chin line is PeasantM7's geometry (same there).
- Row 27's tunic front braid (MM9 C: gold braid down the plum front) is the collar/placket band in gold, not a separate braid.

## Not checked
No in-game run (map placement is the orchestrator's: the maps still place stand-ins 344/347); motion at normal speed not watched
(PeasantM7's approved clips); LOD1-3 not looked at; user artistic acceptance not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantm7d_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantm7d_reduce_claude/before/`.
