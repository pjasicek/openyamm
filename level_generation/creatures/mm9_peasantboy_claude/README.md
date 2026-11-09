# MM9 human boy family (PeasantBoy1 / PeasantBoy2 / PeasantBoy1e) — 3D actors, 2026-11-02

Variants batch (`devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md`): ONE new Meshy body on the full MM9 humanoid route for the
three MM9 boy models, which share one mesh (`meshcmp.py`: Boy1 vs Boy2 body 0.3 cm, head up to 4.0 cm on 5 % of head vertices;
Boy1 vs Boy1e body identical + the 14-vertex ear piece `Boy_1a`; PEASANTCHILDBOY = Boy1 + `Boy_1a`). Progress, hashes and
Meshy receipts: `creature_3d_progress.json`. The dwarf boy (PeasantDBoy1, rows 67/68) is a different mesh and not here.

| Item | Value |
|---|---|
| Rows | 69 Commoner Child (PEASANTBOY1.abc, skin PEASANTBOY1; DAT `CommonerChildHumanChildA`, 5 objects), 70 Townsfolk Child (PEASANTBOY2.abc, skin PEASANTBOY3; no placed object), 73 Commoner Child elf (PEASANTBOY1E.abc, skin PEASANTBOY2; DAT `CommonerChildElfChildA`, 5 objects) |
| Runtime GLBs | `assets_source/worlds/mm9/models/mm9_peasantboy.glb` (from `export/mm9_pboy.glb`, sha256 d17ac68220a2...), variants `pboy_a` (69), `pboy_b` (70), `pboy_e` (73); `mm9_peasantboy_elfears.glb` (from `export/mm9_pboy_elfears.glb`, 771f2d5f5bda...): row 73's elf ears, an attachment on joint `Bip01 ElfEars` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantboy_claude`: `MM9 69 Commoner Child`, `MM9 70 Townsfolk Child`, `MM9 73 Commoner Child` (+ attachment); scale 100 (MM9 Scale 1, our body is MM9's 1.36 m), `yaw_offset -1.570796327`, stride walk 0.45 / run 1.3 (`stride.py`), look Neck/Head, impact 0.7 s (hattack1 `Rattack`) |
| Rows table | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`: 69 -> 166, 70 -> 167, 73 -> 340 (the old stand-ins); tables regenerated, descriptors 9069 / 9070 / 9073 |
| Triangles LOD0/1/2/3 | 10,189 / 5,092 / 1,830 / 607 (Smart Topology 15,066 -> 8,443 after reduction + mirror; MPFB hands 2 x 700; linings ~1,700, one texel each, left out of the shadow meshes; elf ears 672 in the attachment) |
| Clips (30 fps, `source/mm9_lib/pchildboy.glb`) | Standing (stand), Walking (walk), Running (run), Fidget (Fidget1), Talk (conv1), AttackMelee (hattack1), Hit (wince), Death (die1), Dead (die1 end), Cower (cower) |
| Textures | body 2K colour + 1K normal/ORM, region mask (R vest, G sleeves, B trousers, A belt) + ramps per tier; head + hands set 2K colour + 1K normal/ORM with a head colour per tier (three different boys); specular 0, metallic 0 |
| Meshy credits | **45 / 60**: Smart Topology 5, body 4K retexture 10, head 4K retextures a / b / e 10 + 10 + 10 (backup account 3290 before the first job -> 3050 after; other agents spend from it too) |

## Fifth pass (2026-11-02, orchestrator: the pass-4 mouth read as a flat pink sticker, no lips in profile; 0 credits)
- **Lips sculpted** into the face shell (`lip_sculpt.py`, NEW; **`work/face_v10.blend`, the build default**), positions only,
  head weights unchanged: upper lip +1.0 mm (centre 2.2 mm above the line), lower lip +1.8 mm with a rounded underside (3 mm
  below), a groove where they meet, the mentolabial dip (-0.6 mm, 8 mm below), a faint philtrum groove, corners tucked back,
  all scaled across the mouth. Subdividing the patch first (`SUBDIV=2`) and depth smoothing (`SMOOTH`) were tried and dropped:
  creases at the patch border and dented oblique cheeks; the existing vertices carry the profile.
- **Lip paint** (`face_paint_fix.py` step 4): a thin upper lip with a cupid's bow, a fuller lower lip (5.2 mm) with a soft
  centre highlight, colour deepest at the inner lips (rose of the skin's own hue) fading to skin at the edges, a darker parting
  line fading at the corners.
- **Glabella** (`face_paint_fix.py` step 6): texels between the brows darker than 0.94 x the forehead take the surrounding
  skin's own low-pass (dark texels excluded) at their fine detail (a 476, b 147, e 539 texels): no smudge, no plate.
- Sheet read: `review/sheet_faces_p5.png` (viewer lighting; per tier MM9 front/3-4/profile, before = pass 4 and after at front,
  3/4, profile, low 3/4, party, 128 px; zoomed after-front row brows to chin).
- Left: in profile the lips are a modest relief (a child's), not MM9's painted-on lip line; boy a's nostrils read a little red.

## Fourth pass (2026-11-02, user: "look at his mouth", all three boys; 0 credits)
User screenshot `review/user_notes/mouth_front_tiera.png`: a painted smile line above a pale lumpy lower-lip bulge, tooth
specks at the centre, almost no lip colour; a bright stripe and a dark diamond on the nose bridge; reddish eye rims.
- **Cause (mouth)**: the face shell is closed at the mouth (its lips meet in a shallow dent at rest z 0.6936); Meshy's lips were
  three LOOSE pieces floating in front of it (two 18-vertex lip pieces and a 24-vertex plate): their rims were the two "slits"
  the export capped, the lower piece was the pale lumpy bulge, the plate's edges were the specks. `mouth_close.py` (NEW) deletes
  them (42 vertices; `work/face_v8.blend`), `export_fix.mouth_cap` is dropped, `mouth_paint.py` is out of the head chain.
- **Paint** (`face_paint_fix.py` step 4, rewritten): ONE mouth on the geometry's own lip line (glTF y 1.1761, corners 2 mm up
  at |x| 2.35 cm), upper lip 3.2 mm and lower lip 4.8 mm at the centre, rose lips (skin moved 68 % toward a rose of its own hue),
  a soft line where they meet, corner shadows fading into the cheeks, no Meshy lip wrinkles in the box.
- **Nose**: `bridge_weld.py` (NEW) welds the unwelded midline vertex pairs at the top of the bridge (11 welds; the needle slivers
  that opened into the dark diamond) and the bridge is smoothed (`nose_round.py 5`, coincident vertices moved together):
  **`work/face_v9.blend`, the build default**. The stripe and the diamond are gone in the viewer's front light.
- **Eyes**: `face_paint_fix.py` step 5: texels around each eye redder than the cheek (r/g above the cheek's x 1.08) move 75 %
  toward the cheek's hue at their own brightness (a 3389, b 3763, e 1862 texels).
- Viewer shots `scripts/face_shots.sh <prefix>` (the viewer's own lights; explicit cameras: front close-up, 3/4, true profile,
  low 3/4, party view); before = the pass-3 viewer GLBs (`review/viewer_before_p4/`). Sheet read: `review/sheet_faces_p4.png`
  (per tier: MM9 front / 3/4 / profile, before x 5 views + 128 px, after x 5 views + 128 px).
- Gates (installed export 0fc10119d33b...): arm/hand 0 frames > 1 cm, jitter 0, sleeve poke 0, detached 0, winding 0, flat 0.00, bones 0;
  head set 43.8 %; floor ok; binding test PASS (214 descriptors on 92 models). See-through not rerun (head-only changes; the
  waist tube's quads are now triangles, same surface).
- Left: the lips are a soft uniform rose band (no cupid's bow modelled); the mouth geometry carries no lip relief of its own.

## Third pass (2026-11-02, orchestrator review of the second pass; 0 credits)
1. **Mouths** (pass 2 read as a pinched pout): the cause was the geometry: Meshy's narrow lips stood 3 mm proud of the face
   around a 2 cm slit. `mouth_relax.py` (NEW) relaxes the depth of the face shell in an ellipse round the mouth (2.8 x 1.7 cm,
   never forward), lifts the corners up to 1.2 mm, and moves the small inner mouth pieces back with the lips
   (**`work/face_v6.blend`, the build default**). The paint (`face_paint_fix.py` step 4, rewritten) is a wide relaxed closed
   smile: lip line 4.8 cm wide with the corners curving up 2 mm, upper lip 1.8 mm and lower lip 2.8 mm, lip colour the skin
   moved 35 % toward red, a soft line where they meet, corner shadows fading into the cheeks.
2. **Elf ears**: the binding was already right: only `MM9 73 Commoner Child` carries `mm9_peasantboy_elfears.glb`; 69 and 70 have no
   attachment, and the body GLB has no ear triangles (split out; it keeps the `Bip01 ElfEars` joint as the socket). The ears in
   `tiers_p2.png` rows a/b came from the preview renderer drawing the unsplit export; `tier_preview_render.py` now drops them for
   a/b (`NOEARS=1`). Re-rendered `review/tiers_p2.png`.
3. **Boy b's nose bridge**: not paint (a flat-light render of the head paint is clean); it is the bridge geometry's shading
   under side light. `nose_round.py` (bridge smoothing) removes the stripe but opens the degenerate midline slivers at the
   bridge top into a dark notch, so it is not applied; the stripe is left.
Installed export sha256 f11d12d36d38...; elf ears unchanged. Binding test PASS; arm/hand 0, jitter 0, detached 0, winding 0,
flat 0.00; viewer p4 30 switches, 0 errors. See-through not rerun (only the head shell moved; its numbers are the second pass's).
Sheet read: `review/sheet_faces_p3.png` (per tier: MM9 front + 3/4, before front/3-4/party/128 px, after the same), `review/tiers_p2.png`.

## Second pass (2026-11-02, orchestrator review of r8; 0 Meshy credits, no Codex run)
Rollback: the r8 export is not kept separately; the r8 blend chain is intact (`work/face_v3.blend`), and every step below is a
script on top of it.
1. **Back of the head**: no split. The skin-coloured "slit" in `review/sheet_ears.png` columns 3-5 was the two side views
   (`rside`, `lside`, mirror images) placed next to each other at a tight 0.6 scale: the two face profiles met in the middle of
   the sheet. The bob is one closed shell (geometry `review/faces/back_check.png`). Proof: `review/sheet_back_of_head.png`
   (all tiers: 3/4 back both sides, side, back, top, Cower from behind and above, Death from above). Pale diamonds on the vest
   in its `p_*` columns are lining back faces drawn by that renderer without back-face culling; the viewer and game cull
   them (viewer back shots `review/shots/p2_*_back.png` are clean).
2. **Nose**: `face_paint_fix.py` step 3 mirrors the lighter half of the mid-face (|x| < 4.5 cm, nose to mouth) onto the darker
   half (the geometry is symmetric, so the nostrils still fit it); `head_texel_pos.py` now skips the midline needle triangles
   (they stamped a streak of mirrored positions across boy b's cheek). What remains under side light is the bridge's own
   shading (geometry); `nose_round.py` (bridge smoothing) was tried and dropped: it pulled the bridge texels into a dark notch.
3. **Mouths**: a closed, calm mouth painted on every tier (`face_paint_fix.py` step 4, from `work/mouth_slit.json`,
   `mouth_slit.py`): one lip line 4 mm above the inner slit, upper lip 3 mm, lower lip 5.2 mm, the lips' own red, a soft dark
   line where they meet; the inner slit stays capped (`export_fix.mouth_cap`). No teeth, no parted gap, no second lip layer.
4. **Hands**: `hand_clean.py` with `HAND_REF` = each tier's own cheek skin (written by `face_paint_fix.py` to
   `work/hand_ref_<prefix>.txt`): a 211/134/111, b 234/152/125, e 231/144/121 (was a grey-white 228/159/127 graded bake).
5. **See-through** at the belt: `waist_backstop.py` (NEW) puts a dark closed tube inside the trunk from rest z 0.12 to 0.40 at
   0.86 of the innermost cloth radius, each ring weighted as the nearest cloth (bends with the trunk), on one dark vest texel,
   `lined` (out of the shadow meshes): through any gap that opens at the belt the eye meets it (`work/face_v4.blend`, 736
   faces). Knee rims (trouser end over the boot top, rest -0.143) lined with `rim_lining.py bones=Calf,Thigh
   band_bones=Calf,Thigh,Foot depth=0.25 region=B zmin=-0.2 zmax=-0.08 min_edges=10 mid_ok=1 inner_offset=0.0005`
   (**`work/face_v5.blend`, the build default**).
6. **Tiers b and e**: plain brown trousers (`tiers_boy.py`: one MM9 brown per tier on a 0.85-1.05 slope; the check reads as a
   faint weave). Boy b's open vest: a per-tier region mask (`textures/pboy_region_mask_b.png`, NEW `mask_variant.py` in the
   runtime build) moves a panel down the front (1.2 cm half width at the belt to 4 cm at the collar) from the vest channel to
   the shirt channel, and b's shirt ramp is widened so the dark vest texels there turn cream. No Meshy job.
7. **Descriptor heights** (for the orchestrator): MM9's rule (`mm9_monster_bodies.py`: height = 2 x vertical half extent x scale
   x 2.56, radius = larger horizontal half extent x scale x 2.56) with PEASANTBOY1/2/1E's animation extents (10, 26, 10 LT,
   Scale 1) gives **Height 133, Radius 26** for 9069, 9070 and 9073 (now 160/160/106 from the stand-ins). Not written here.
   See-through after the second pass (`review/gates/see_through_p3/`, all clips every 2nd frame + Running 15; worst px level /
   party 20 deg): torso 95 -> **21 / 4** (AttackMelee 14 from the front-left: the ray enters the belt gap and grazes between the
   vest and the tube onto the vest's back faces at rest z 0.355; not closed), trousers 78 -> **0 / 1**, boots **0**, sleeves
   7 / 4, collar 7 (the lying corpse's open collar), head 12 (mouth corners, eye corners: not cloth). Triangles LOD0/1/2/3
   11,945 / 5,970 / 2,145 / 711 (the tube and new linings are one-texel faces, dropped from the shadow meshes).
   Installed export sha256 ebcae1094819...; elf ears unchanged (cf923380686a...).
Sheets read: `review/sheet_before_after_p2.png` (faces front/3-4 before, after front/3-4, party view 22 deg, 128 px sim; hands;
back), `review/sheet_back_of_head.png`, `review/sheet_viewer_p2.png` (viewer: front, 3/4, back, AttackMelee from behind, Hit,
Cower from behind, Death; all tiers), `review/tiers_p2.png` (MM9 vs ours, three tiers), `review/tiers_p2/bz.png` (b's panel).

## Which clips the boys play
`dat_objects.py "Child"`: `CommonerChildHumanChildA` 3 objects without a script (NPCbase: wander, converse, `LoopAnim Cower` in
BaseRun.inc) and 2 with `scripts\YanmirChild.scr` (follow the party, run to the exit); `CommonerChildElfChildA` 3 without a
script, 1 `NPC93.scr` (Rude only, no animation), 1 YanmirChild. All three rows are `NPCbase.scr` in MONSTERS.txt. The library is
PEASANTCHILDBOY.abc (the boy models carry only a 1.4 s bind clip). hattack1 is kept as AttackMelee (the rows have attacks);
hattack2, cowerstart and cowerstop are not carried.

## Route (scripts/, repo root unless noted)
0. `convert_sources.sh` (MM9 models with their row skins + the library), `ref_renders.py` -> `review/mm9/`, sheets
   `references_hd/mm9_views_{a,b,e}.png`, `mm9_head_views_{a,b,e}.png`, `mm9_skin_x4_{a,b,e}.png` (`review/mm9_views_all.png`).
1. HD masters (boy a's design): `codex_masters.sh 1|2` (brief `references_hd/CODEX_BRIEF.md`; both runs' halo removed with
   `from_pdm2/clean_alpha.py 200`, originals in `references_hd/raw/selected_*`); head turnarounds `codex_head.sh a|b|e`
   (b and e: different boys on a's silhouette; e's ears are not drawn, they are geometry). Sheets `review/masters_check2.png`,
   `review/heads_abe_check.png`.
2. Meshy Smart Topology 15k from `00_three_quarter.png`.
3. **NEW** `add_left_hand.py`: MM9's child skeleton has no `Bip01 L Hand` (the left fingers hang off the forearm, so MM9's left
   wrist never bends). A static joint is inserted at the mirror of the right hand with the forearm's rotation (identity local),
   the left fingers re-parented, the file's own keys and inverse bind matrix adjusted (`source/mm9/pboy1_lh.glb`). No clip
   animates it: the left hand stays rigid on the forearm as in MM9; the shared hand scripts find a hand joint on both sides.
4. **NEW** `sym_meshy.py`: the Meshy body made exactly symmetric (+X half mirrored; MM9's mesh is symmetric; Meshy had a hole
   in one thigh), `fit_rig.py fit_config.json` (pelvis-rooted child chain), `reduce_uv.py`, **`sym_rigged.py`** (symmetric
   again after the decimation, weights swapped L/R), `graft_hands.py graft_boy.json` (MPFB child hands, age 0.17, 0.128 m:
   MM9's hand is 0.119 m and our arms 1.078x MM9's), `head_split.py head_boy.json` (neck cut 0.58 rest, the shirt/neck part
   spans), `eye_fill.py` 5,6 + `drop_parts.py` 5,6 (eyeball cups), `head_split.py` again (`work/eyes_v1.blend`).
5. UVs `uv_pass.sh` (body atlas 63.4 %; head with `method=ANGLE_BASED`: the default SLIM merge collapsed 284 faces to zero UV
   area). Never re-run (the paid paints are on these layouts).
6. Paint (project folder): `bake_ao_texpass.py`, `compose_texpass.py pboy_tp ...`, gentle grade (`grade_basecolor.py --fine 1.0
   --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15`), `bake_hands.py work/texpass_head.blend
   young_caucasian_male/...`; tiers `mm9_skin_labels_boy.py` + `tiers_boy.py` (below).
7. Geometry on the painted master (positions/faces/weights only): `sleeve_tuck.py 0.75 0.003 1`, `cuff_trim.py 0.01`
   (`trim_v1`) -> **NEW** `add_elf_ears.py` (`ears_v1`) -> **`linings.sh`** (neck cap, belt, boot, sleeve-top and cuff linings;
   `linings_v1`) -> **NEW** `face_smooth.py 5 0.022 0.725 0` (the mirrored face's midline crease, knife-edged nose ridge and
   V chin softened below the brows; `face_v1`) -> **NEW** `root_buttons.py` (the vest's toggles rigid on the cloth, floating
   ones set down; `face_v1r`) -> **NEW** `relayout_head.py face_factor=1.4 method=ANGLE_BASED fine=250 steps=0` (`face_v2`,
   below) -> `root_buttons.py` (`face_v2r`) -> **NEW** `stub_despike.py` (stub spikes out of the cuffs; `face_v2s`) -> `rim_lining.py bones=Thigh,Pelvis,Spine
   band_bones=Thigh,Pelvis,Spine depth=0.15 region=B zmin=0.12 zmax=0.2 min_edges=20 mid_ok=1 inner_offset=0.0005` (the
   trousers' waist rim inside the vest, which `linings.sh` had missed; **`face_v3`**, the build default).
8. Head set paint `scripts/head_paint.sh` (project folder): `compose_headhand.py --ref-head --ref-lum-min 150 --hand-gain 1.12`
   per head job -> pad the old layout -> `transfer_head_paint.py` + `transfer_head_merge.py` (one supersampled resample into
   the new head layout) -> `head_normal_flat.py` -> `elf_ear_paint.py` -> `mouth_paint.py` -> `face_paint_fix.py` ->
   `hand_clean.py <p> 1.1` -> `pad_head_boy.py`. Needs `work/mouth_uv.json` (`mouth_mask.py` on face_v2) and
   `work/head_texel_pos{,_old}.npz` (`head_texel_pos.py` on exports of face_v2 / face_v1r).
9. Runtime `TOKEN=<lease> scripts/build_runtime_pboy.sh [--install]` (export with `export_fix.mouth_cap`, clips, hand rest
   `hand_rest_pboy.txt`: Fidget L, LODs, shadow fix, region variants, **split of the elf ears** (`tools/split_attachment.py
   --joint "Bip01 ElfEars"`, before `tier_head.py` because the tool keeps only ramp-only variants), tier heads b/e, extras,
   floor fix, `mirror_glb.py` on body and ears, winding, install with `--name mm9_peasantboy.glb` / `mm9_peasantboy_elfears.glb`).
   Viewer `scripts/viewer.sh <rev>` (project folder; tier e from an unsplit copy so the viewer shows the ears). Binding:
   `flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
   level_generation/creatures/mm9_peasantboy_claude/scripts/bind_actors.py && python3
   tools/mm9_import_discovery/generate_mm9_monster_tables.py'`. Gates `scripts/gates.sh` (project folder) +
   `sleeve_poke_gate.py` + `see_through_gate.py`.

## Tiers
One body paint (boy a's design) with region ramps: R vest, G shirt sleeves, B trousers, A belt (boots are the same in all
three skins and in no region). Each MM9 skin is labelled from its OWN model's UVs and joints (`mm9_skin_labels_boy.py`:
PEASANTBOY1E maps its green tunic block onto the sleeves), light outliers dropped from vest/sleeve/trouser pixels (b's
cream shirt panel, e's trim) and every tier, a included, takes its skin's region colours at our texel's luminance quantile
(gain MM9 a -> our paint): our Meshy vest was orange-brown, MM9's is dark brown. Fit mean / p95 (8-bit): vest a 2.3/6.0,
b 2.7/9.8, e 6.3/19.5; sleeves 4.3/15.4, 4.3/15.5, 3.4/10.1; trousers 2.3/6.6, 2.7/7.4, 2.6/7.2; belt 5.2/16.6, 4.8/16.1,
5.9/23.5. Heads: one Meshy head retexture per boy (a: long chestnut bob; b: darker wavy fringe, round smiling face; e: auburn
bob with a straight fringe, freckles), so three head colour images on one head mesh (`tier_head.py`).

## Elf ears (row 73)
MM9's `Boy_1a` is two pointed ears through the hair. `add_elf_ears.py` builds them procedurally after its shape (a 8.6 cm
leaf from inside the hair at the ear, out, up and slightly back, dished front, tapering thickness, rim strip), weighted 100 %
to a new joint `Bip01 ElfEars` (child of `Bip01 Head`), on head-set texels in the free band above the head square, painted with
boy e's cheek skin, a darker dished concha and a light rim (`elf_ear_paint.py`). The runtime build splits them into
`mm9_peasantboy_elfears.glb`; only `MM9 73 Commoner Child` carries the attachment. Sheets `review/ears_geo.png`,
`review/sheet_ears.png`, `review/sheet_ears_sides.png`.

## Head layout (face as one chart)
The viewer at party distance showed a dark "goatee" and a spot between the brows on every boy: the head layout split the
mirrored face down its midline and around the chin, and coarse mip levels blended the hair islands packed beside those seams
into the face (reproduced by rendering with the head set downsampled to 128 px). `relayout_head.py` unwraps the face (front
head-shell faces, nostril undersides excluded: they folded over the cheek) as one angle-based island, feeds it to
`uv_atlas.py` as a ready chart (xatlas's `charts` result wrapped in the script only; the shared tool is unchanged) with 1.4x
density, and packs the rest; the elf ear islands and hands keep their texels. The paid paint is carried over once
(`transfer_head_paint.py`, Cycles emission bake at 2x, box-downsampled; degenerate midline slivers whose new UVs are needles
are not baked: they drew a streak across boy b's cheek), head normals flat (Meshy's were near flat). Head-set use 43.8 %
(was 46.0 %), fragments 2.1 %, spread 1.55, stretch p90 1.16. Sheets `review/head_charts_ff.png`, `review/faces_zoom_r10.png`
(includes the 128 px mip simulation).

## Checks (final build, `review/gates/`)

| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only`, 10 clips, 48 fps) | **0 frames over 1 cm, both hands, every clip** (before the Fidget rest: L 1.8 cm, 5 frames; `hand_rest.py` need 3.1 -> 0.0 cm). Finger stretch max 3.03 (Talk L); 19 chains per hand; left wrist 0 deg in every clip (MM9 has no left wrist) |
| Jitter (`jitter_gate.py` vs MM9's untouched clips) | **0 fails** (Hit failed at 5.4 mm/f2 shoulder skin with `--ground-loop Hit` in the floor pass; dropped, floor still ok) |
| Sleeve poke (`sleeve_poke_gate.py`) | **0 mm, 0 frames, both sides, every clip** |
| See-through (`see_through_gate.py`) | see "See-through" below |
| Floor (`floor_audit.py --world mm9`) | MM9 69 / 70 / 73: stand 0.0, walk -0.1..+1.2, living -1.7, dead -0.0: ok |
| Detached (`detached_parts_audit.py`) | **0 detached** (before `root_buttons.py`: a vest toggle 7.9 mm off at rest, the collar toggle up to 8.6 mm in Death) |
| Winding / bones / flat | 0 inverted (body and ears); 12 checked, 0 stretching; flat 0.00 on both materials |
| Texture quality | body atlas **63.3 %** (uv sum 64.1 %), density p50 1576 (pre-lining spread 1.04, fragments 0.0 %), stretch p90 1.07; the linings' one-texel faces make the reported spread infinite (as PeasantDM2's). Head set 43.8 %, spread 1.55 (hands half density by design), fragments 2.1 %, stretch 1.16 |
| Viewer (`run_creature_review.py check`) | 30 switches, 0 failed, 0 console errors |
| Regression `mm9_actor_models_build_every_binding` (`--world mm9`) | **PASS** (201 descriptors on 88 models, 0 failed; `review/gates/regression_binding_final.log`) |

### See-through
Rims lined by `linings.sh` and the trouser-waist run. Worst background pixels per zone (3 mm pixels, 8 azimuths x level / 20 deg
down): r1 (no linings, all clips, every 4th frame) -> r3 (`linings.sh`, all clips, every 2nd frame + Running 15) -> r4 (+ trouser
waist; Death, AttackMelee, Running, Cower, Hit, every 4th frame): sleeve L 49 -> 7 -> 7, sleeve R 36 -> 7 -> 4, boots 1 -> 2 -> 1,
collar 7 -> 7 -> 6, trousers L 78 -> 78 -> 25 (level 20 / party 25), trousers R 28 -> 29 -> 17, torso 157 -> 95 -> 95 (party view 35),
head (mouth, eye corners; not cloth) 10 -> 12 -> 10. Reports `review/gates/see_through_r{1,2,3,4}/`. **Not passed**: the torso
slit at the belt line, seen from behind/side when the trunk bends (AttackMelee 24, Cower, Death, Hit; `hole_probe.py`: the view
meets the back faces of the vest above the belt, part 4119, Spine1-weighted, 0.84-0.89 m) and the trouser tops seen up under
the vest hem in Death. Both open only in bent poses; the belt lining band (12 cm) does not reach the vest faces behind the gap.
Not fixed: a bridge between the vest's lower rim (34 edges) and the skirt's top rim (30 edges) under the belt would close it.

## Sheets read
`review/sheet_mm9_vs_ours.png` (MM9 front/3-4 vs viewer, three tiers), `review/sheet_viewer_final.png` (every clip, three tiers),
`review/faces_zoom_r10.png` (faces a/b/e front + 3/4, mip-128 simulation), `review/faces/chin4.png` (mouth, jaw, neck),
`review/sheet_ears.png` + `review/sheet_ears_sides.png` (ears, sides, under the jaw, back), `review/sheet_hands.png` (before) and
`review/faces/hand3R_front.png` (after the despike and hand clean), `review/tiers_preview_vs_mm9.png`, `review/graft_hands.png`,
`review/xray_v2.png`, `review/fit_v2_sheet.png`, `review/see_through_r1_sheet.png`, `review/see_through_r2_sheet.png`.
The viewer's `head` focus misframes this small rig; faces, hands and ears are judged on Blender renders of the textured export.

## Deviations and open points
- **Pattern differences not reproduced** (ramps recolour one paint): b's open vest showing the cream shirt, e's embroidered
  trim; our trousers keep a woven check on b and e (MM9's are plain brown); the belt of b/e is the braid recoloured brown.
- **Faces**: three different boys from Meshy head retextures (Codex head turnarounds), checked against MM9's faces (no doubled
  nostrils, one brow, no plate under the eyes, closed mouth: the mouth slit capped and painted as lip shadow, teeth texels
  between the lips none left). Boy a still reads slightly parted-lipped; the nose bridge carries Meshy's baked side shading.
  The face is a mirrored copy of one half (symmetric like MM9's).
- **Left hand**: rigid on the forearm in every clip, as MM9 (no left wrist joint in MM9's child skeleton).
- **Elf ears** are procedural (not a Meshy/Codex piece): MM9-like proportion and placement, simple painted shading.
- **Heights** of descriptors 9069/9070/9073 come from their legacy stand-ins (160 / 160 / 106); MM9's boy is 1.36 m. The body
  override table (`mm9_monster_body_overrides.tsv`) is written by `mm9_monster_bodies.py --write-overrides` (shared import
  code); not run here.
- Hands 0.128 m (MM9 0.119 m), MPFB child hands with five fingers driven from MM9's mitten curl.
- Not looked at in game (placement still uses the legacy stand-ins: the orchestrator's switch); LOD1-3 and shadow meshes not
  looked at; motion judged on strips and gates, not watched at speed in the viewer; sounds; Android cook.

## Binding plan (map placement)
`CommonerChildHumanChildA` / `CommonerChildElfChildA` objects are placed with legacy ids 166 / 340 by
`transcode_mm9_dat_to_odm.py`; they should place 9069 / 9073 (row 70 has no placed object). Per the brief, that switch is the
orchestrator's.

User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantboy_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantboy_reduce_claude/before/`.
