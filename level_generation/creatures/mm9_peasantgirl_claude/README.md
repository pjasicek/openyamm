# MM9 peasant girls (PeasantGirl2 / PeasantGirl3 / PeasantGirl1e) — 3D actors, 2026-11-02

MM9 `PEASANTGIRL2.abc`, `PEASANTGIRL3.abc` and `PEASANTGIRL1E.abc` share one body (`meshcmp.py` re-run: Girl3 vs Girl2 head up to 2.4 cm,
hair only; Girl1e vs Girl2 head up to 2.3 cm, the elf ears; torso, arms and legs identical; `PEASANTCHILDGIRL.abc`, the clip library, is the
same mesh). Skeleton: MM9's 60-joint child girl rig (`Bip01`, no thighs: the calves hang off `Bip01 Spine` and MM9 moves the knees by
translation; eight skirt chains). `MONSTERS.txt` rows (all `NPCbase.scr`, BaseName `PeasantGirl`, Scale 1):

| Row | Name | Model / skin | DAT placements (rebuilt maps) | Our GLB, tier |
|---|---|---|---|---|
| 71 | Commoner Child, Peasant Human2 Child A | PeasantGirl2 / Peasantgirl2 | `CommonerChildHuman2ChildA`: 4 (2 `YanmirChild.scr`, 1 `NPC312.scr`, 1 none) | `mm9_peasantgirl`, `pg_g2` |
| 72 | Townsfolk Child, Peasant Human2 Child B | PeasantGirl3 / Peasantgirl3 | none | `mm9_peasantgirl`, `pg_g3` |
| 74 | Townsfolk Child, Peasant Elf Child B | PeasantGirl1e / Peasantgirl1 | none (`CommonerChildElfChildA` is row 73, the elf boy) | `mm9_peasantgirl1e`, `pg_g1e` |

| Item | Value |
|---|---|
| Runtime GLBs | `assets_source/worlds/mm9/models/mm9_peasantgirl.glb` (no ears; variants `pg_g2`, `pg_g3`) and `mm9_peasantgirl1e.glb` (procedural elf ears; variant `pg_g1e`), installed with `tools/install_model.py --world mm9`, identical to `export/`. The body textures are the same images in both: the cook shares them (the elf install cooked 3 new textures, the head set) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_peasantgirl_claude`: `MM9 71 Commoner Child`, `MM9 72 Townsfolk Child`, `MM9 74 Townsfolk Child`; scale 100 (MM9's size: 1.29 m), `yaw_offset` -1.570796327, stride walk 0.62 / run 1.55 (`stride.py`), look Neck + Head |
| Descriptors | rows 71, 72, 74 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visuals 595, 596, 331 = the existing stand-ins), tables regenerated: ids 9071, 9072, 9074 (`scripts/bind_under_lock.sh` under the flock). Map placement not switched (orchestrator's step) |
| Triangles LOD0/1/2/3 | human 13,776 / 6,884 / 2,475 / 824; elf 14,364 / 7,178 / 2,581 / 858. LOD0 (elf): head with eyeballs 5,326, dress (bodice, sleeves) 1,962, skirt + apron 1,440, skirt lining 1,604 (+ waist cap 32), hair 1,298, hands 1,464, ears 588, legs + shoes 560, buttons 92 |
| Skeleton | 95 joints: MM9's 60 + 30 finger bones (MPFB hands) + 5 half-joint helpers |
| Clips (30 fps, `source/mm9_lib/pchildgirl/pchildgirl.glb`) | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget`, Talk `conv`, Hit `wince`, Death `die1`, Dead, Cower `cower` |
| Textures | body colour 2K, normal and ORM 1K, region mask 1K (R dress cloth + lining, G vest / trims / belt, B skin of the neck, chest and hands); head colour 1K per girl (3), head normal + ORM 1K (g2's in the human GLB, g1e's in the elf GLB) |
| Meshy credits | **105** (cap raised by the coordinator for the r27 repaint): head repaints r27 g2 / g3 / g1e 10 each (jobs pg_head3_*, backup 2510 / 2500 / 2490 before, 2475 after); **75** before (45 for the family + 30 for the face repaint, user / coordinator decision 2026-11-02): head repaints r24 g2 / g3 / g1e 10 each (jobs pg_head2_*, backup 2815 / 2805 / 2795 before); first round **45 / 60**: Smart Topology 5, body retexture 4K 10, head retextures 4K g2 10, g3 10, g1e 10 (backup account: 3295 before the first job, 3095 before the last); no retries |
| Codex | 3 runs through `codex_slot.sh`: three-quarter master, four views, twelve head views (`references_hd/`, `references_head/`) |
| Height | 1.294 m soles to crown in the bind (MM9's PEASANTGIRL2 1.294 m, Scale 1): **129.4 world units** at scale 100 for all three descriptors (standing clip 129.5 units, measured on the export; the elf ear tips stay under the crown). **Descriptor height to record: 130, radius 21** (the hem's widest half-width 0.21 m). The tables now carry 151 / 51 (inherited); MM9's own rule (`mm9_monster_bodies.py`, read-only run) gives 82 / 328 because the girl models' animation-0 dims (128, 16, 16) lie on the wrong axis: not usable. Overrides not written (orchestrator's step) |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasantgirl_claude/review/viewer/ revision `r24`, tiers `pg_g2`, `pg_g3`, `pg_g1e` (focus presets at child scale) |

## Clips

NPCbase.scr -> NPCBase.inc `Converse -1` (the library has one `conv`) and BaseRun.inc `LoopAnim Cower`; `YanmirChild.scr` (follow the
player, run to the exit) and `NPC312.scr` play no animation by name. Bound: standing, walking, run, fidget, hit, dying, dead; attacks play
Fidget (children flee); script clips `talk` / `conv` (Talk), `cower`, `stand`. Left out: `hattack1`, `cowerstart`, `cowerend`
(`ALL=1 scripts/pg_roles.py` adds them). Retarget: PeasantF5's `clips_pf.py` (MM9's local rotations on MM9's joints, the soft line for
translations), `root_lift` Pelvis 0.102 (the library keys the pelvis relative to standing; without it every living clip stood 10 cm under the
floor, floor audit -10.4). Fingers: `finger_alias` from MM9's two two-bone chains + `finger_rest_pg.py`. Corrections:
- `pony_hang.py`: MM9's Ponytail chain turns rigidly with the bowed head (Hit 76 deg from down); our hair is 10 cm longer than MM9's and
  stuck out behind like a horn. The chain's angle from down is soft-clamped above 35 deg (x0.3) except in Death / Dead.
- `pony_floor.py`: in Death / Dead the hair tip went up to 23 cm under the floor; Ponytail1 turns until it lies on the floor.
- `skirt_gather.py`: the A-line hem (0.4 m) stood round the feet of the corpse as a flower (MM9's skirt is a tube); Death (ramped from
  35 %) and Dead turn each chain's first link 0.6 x its rest flare toward the legs.

## Route (`scripts/`)

0. **Sources**: `convert_abc_model.py --scale 0.0256` (pg2, pg3, pg1e, pg3e, PEASANTCHILDGIRL; run with the gltf venv's site-packages on
   `PYTHONPATH`, the system Python lacks pygltflib), `mm9_dump.py`, `mm9_regions_pg.py`, `ref_renders.py` -> `references_hd/mm9_*`.
1. **HD masters** (Codex, `references_hd/CODEX_BRIEF.md`, `codex_masters.sh` runs 1 and 2; skin g2, the placed row), `clean_alpha.py`.
   Head turnarounds (`references_head/CODEX_BRIEF.md`, `codex_heads.sh`): g2, g3 (fringe), g1e (elf ears); profiles mirrored to face left.
2. **Smart Topology** 15k from `00_three_quarter_clean.png`. Meshy returned the face, bodice, sleeves (bell cuffs closed by a recessed cap),
   apron and skirt as ONE shell, a hair helmet with a scalp cap, hands, shins, shoes, eyeballs, braid ties and belt buttons.
   `step1_clean.py ... 1.294` (MM9's height).
3. **`assemble_pg.py`**: the head sat 5.5 mm off the body midline (eyes, nose): shifted with a neck feather; every shell mirrored from +x;
   a needle strip Meshy hung from the lips to the chest dropped; the body shell reduced outside the head, then split on a **level neck
   seam** (z 1.05 over the soles) into head / dress / skirt; the braid ties dropped (they hung beside the jaw like earrings); sleeves pulled
   to MM9's arm length (x1.23) and turned 10 deg onto MM9's direction, radially limited so the torso side stays; MPFB hands 135 mm with a
   3 cm stub inside the cuff; shins and shoes; skirt lining with rims at the hem and the apron's edge; **procedural elf ears** (F8's leaf,
   8 cm, out and up through the hair as MM9's Girl1e) as their own part `ears`.
4. **Rig** (`rig.sh`): `fit_rig_pg.py` (arms on the sleeve axis with MM9's lengths, MPFB fingers, Ponytail chain 2 cm inside the hair's back,
   head pivot at the skull base), `weights_pg.py` (from F5: skirt over the eight chains, torso by spine heights, sleeves by the arm axis,
   head rigid above a jaw plane and all Neck at the seam, hair on Head then Ponytail1 -> 11 behind the ears, ears rigid on Head, hand stubs
   rigid on the forearm), `build_glb_pg.py` (`DROP_PARTS=ears` for the human GLB), `clips_pf.py`, `finger_rest_pg.py`, `pony_hang.py`,
   `pony_floor.py`, `skirt_gather.py`, `half_keys_pg.py`.
5. **UVs** (`uv_pg.py`, never re-run: the paid paints belong to `work/uv_orig.npz`): body square (hands 1.5x, lining 0.3x, shins 0.5x),
   head square (head, hair, ears; face 1.6x, long hair 0.6x). `fix_needles_pg.py` dropped 2 needle faces at the nose tip before the upload.
   Uploads `make_upload_pg.py`: body, head without ears (g2, g3), head with ears (g1e).
6. **Paint**: `compose_pg.py` (4K -> 2K / 1K once), AO (`texpass_bake_ao.py` + `pad_ao.py`), gentle grade (`finish_pg.py`), `sym_paint.py`
   on the heads, `head_fix_pg.py` per girl, `tiers_pg.py`, `add_cap.py`, `tweak_pg.py`; `rebuild.sh <rev> [--install]` replays
   head fix -> tiers -> (human, elf: finish -> cap -> tweak -> rig -> runtime) -> viewer from the paid paints.
7. **Runtime** (`build_runtime.sh human|elf`): prepare, LODs, shadow fix, `region_variants.py` (ramps split per GLB), `tier_images_pg.py`
   (head colour per girl), winding, floor (skirt lift 0.14 in Death / Dead, ground), `mirror_glb.py` (true handedness), winding.

## Faces, hands and cloth fixes (pre-screen against MM9's faces)

- **Eyes**: Meshy set the eyeballs 7 mm behind the lids and the lower lid opening ran 6 mm under the eye centre: from the party's height a
  stare (white under the iris), and once the ball was painted, a skin-coloured lump under it. `tweak_pg.py` (positions only): eyeballs
  3 mm forward, the lower half of each lid opening compressed toward the eye centre (x0.55) and 1 mm forward. `head_fix_pg.py`: the ball
  under the iris takes the lower lid's own skin (sampled under each eye), a soft lid shadow and lash line at the top, Meshy's red lid rims
  toward the skin, the white inner rim of the lower lid to skin. Head normal map flattened on the eyes and lips (`*_normal_fix.png`: its
  baked eye relief drew a dark crescent under each eye in the viewer).
- **Mouth**: closed-lip smile (Codex); the lips' inner faces under the upper lip were painted skin (pale specks in the slit): plain lip tone.
- **Midline cracks**: `fix_needles_pg.py` first dropped every face under 0.2 mm2 too, which opened ~1 mm holes on the nose, lips and chin
  (dark dots): restored; only the two needles stay out. `fix_tjunctions.py` checks for T-junction cracks (none left).
- **Neck seam / skin**: the head is per girl, the body paint shared; region B (neck, chest, hands) takes each girl's chin skin by ramp.
- **Cuffs**: Meshy painted skin wedges on the undersleeves beside the hands: repainted cream (`tiers_pg.py`).
- **See-through**: the dress is one-sided and has no torso inside: from the feet of the falling body the view up the skirt met the inside of
  the bodice (1,477 px). `add_cap.py`: a disc across the inside of the dress at the waist, facing down, on a lining texel (new faces only).
- **Hairline arc** (coordinator review of the boys): the hair helmet's front edge stands off the scalp as a ledge, and Meshy painted a dark band where the hair shell's front edge lies on the scalp
  cap (a hairband at 128 px on g3 / g1e): hair texels within 1.2 cm of the shell's open edges take their neighbourhood's luminance, and `tweak_pg.py` sinks hair vertices within 1.5 cm of the shell's front edges
  up to 2.5 mm toward the head. A soft ridge remains at the hairline under top light (geometry of the helmet; not corrected further).
- **Chest specks**: dark flecks inside the neckline skin (the needle strip's paint, vest flecks; navy dots on g3) take the skin.
- **Holes** (`fill_holes.py`): the needle filter had also dropped long thin faces of the vest edge (a 9 cm slit each side of the vest
  front), plus gaps at the apron sides, the mouth corners and the nose tip: 11 loops filled with new faces.
- **Shins**: their knee ends touched the skirt's folds when MM9 translates the knees: narrowed 30 % and 4 cm lower (`tweak_pg.py`).

## Tiers

MM9's three skins are three different girls and three dress colours: one body paint (g2's rust dress with a black gold-embroidered vest)
with ramps: R dress cloth (g2 rust, g3 navy, g1e teal; from MM9's skirt texels), G vest (g2 from MM9's vest texels; g3 / g1e from their dress
cloth: they have no vest), B skin (each head's chin skin). A head colour per girl (`KHR_materials_variants`). Coordinator review (patterns MM9 does not have): g3 / g1e take a narrow G ramp round their own dress cloth, so their
bodice reads plain like MM9's (no gold embroidery pattern). Deviations: g1e's lacing and white sash and g3's belt are not painted; the
belt stays the g2 paint.

## Checks (final GLBs, `review/gates/`)

| Gate | Result |
|---|---|
| `arm_hand_gate.py --outer-only --exact` (48 fps) | 0 frames over 1 cm in every clip, both hands; hand depth max 0.7 cm (Cower L); forearm max 0.6 cm (Talk R); finger stretch max 1.76 |
| `sleeve_poke_pg.py` (hands inside the cuffs, 48 fps) | 0 mm in every clip except Hit L 2.6 mm in 16 frames, 2 vertices (wrist bent under the bell cuff; not visible in close-ups) |
| `robe_gate.py` (legs through the skirt) | living clips: Standing 3/25 frames 1.1 cm, Walking 2/50 0.9, Running 1/44 0.7, Talk 11/105 1.4, Hit 8/49 1.3, Fidget and Cower 0; Death 28/45 2.5 cm, Dead 25/25 1.7 cm: the knee ends of the shins against the gathered skirt of the corpse (see open points) |
| `see_through_gate.py` (every 3rd 30 fps frame, 8 azimuths x level / 20 deg, 2 mm px) | before the waist cap: torso 1,477 / sleeve 1,730 / collar 1,224 px (Death, from the feet). r12: living clips (Standing, Walking, Running, Talk, Fidget, Hit, Cower) at most 15-19 px torso (1-px slivers at the belt / silhouette), sleeves at most 10, head 6; Death / Dead from the feet at floor level torso 47, sleeve L 88, collar 65 (the cap rim and the bodice seen from under the fallen skirt); at the party's 20 deg at most 13 px. `review/gates/see_through_h/`, `see_through_e/` |
| `jitter_gate.py` | 0 fails (no arm corrections: MM9's arms clear this body) |
| `flat_shading_check.py` | 0.00 body and head, both GLBs |
| `detached_parts_audit.py` | 4 parts: shins and shoes, free inside the skirt by design (as F5 / MM9) |
| `bone_length_audit.py` | 2 "stretching": both Calf bones (MM9 translates the knees: 0.32 -> 0.36 m, its own design) |
| `check_winding.py` | 0 inverted closed parts, both |
| `floor_audit.py --world mm9 --match 'MM9 7[124] *'` | 3 bindings ok: stand -0.2, walk -0.2..+1.9, living -1.3, dead 0.0 |
| `texture_quality.py` | body atlas 57.5 %, fragments 1.9 %, stretch p90 1.06, spread 3.39 (hands 1.5x, lining 0.3x, shins 0.5x by design); head atlas 61.4 % (elf 62.3 %), fragments 1.5 %, stretch p90 1.13, spread 2.56 (face 1.6x, long hair 0.6x) |
| Regression `mm9_actor_models_build_every_binding` | PASS, 201 descriptors on 88 models, 0 failed |
| Viewer `run_creature_review.py check` | 27 switches, 0 failed, 0 console errors |

## Coordinator pass 2 (r14, 0 credits)

Before / after sheet: `review/sheet_before_after_r14.png` (r13 vs r14, g2 and g1e: face front / party / 128 px, back of the head, neck, hairline).
1. **Gloss**: the engine already draws these materials with specular 0 and metallic 0 (as F1 / F8); the sheen was Blender's studio
   specular in my sheets. ORM roughness floor raised 0.6 -> 0.88 (`finish_pg.py`, `RMIN`), and sheets are now rendered with the specular
   highlight off (`ref_renders.py NOSPEC=1`), matching the engine.
2. **Neck dots**: Meshy painted the dress neckline as brown blobs on the head's neck strip above the level seam: the neck under the jaw takes
   each girl's chin skin with broad shading only (head-skin faces only; hair beside the neck untouched), the chin's midline tick blurred.
   A first try moved the seam's own vertices (chin smoothing feather) and opened a dark gap: the seam is now fixed in place.
3. **Hairline ridge**: the hair shell rose from 2 mm to 12 mm off the forehead within 1.3 cm: hair vertices within 3.5 cm of the shell's front
   edges blend toward the head surface + 1.5 mm (90 % at the edge), computed on welded positions (`tweak_pg.py`); plus the paint lift.
4. **Chin**: head vertices under the mouth Laplacian-smoothed (12 passes, feathered, max 4.2 mm, the neck seam fixed); weights unchanged.
5. **Lip specks**: also light texels on the slit line within the lips (`head_fix_pg.py`).
6. **Eyes at 128 px**: the skin round each lid opening lifted up to 16 %, the lid shadow on the ball softened (0.30 -> 0.18), the head normal
   map flattened 9 mm round each eye (was 4).
7. **Legs through the skirt**: the shin knee ends shortened to 0.26 m over the floor and narrowed 40 %. `robe_gate.py` (nearest-face plane)
   still flags Standing 0.8, Walking 1.2, Talk 1.1, Hit 2.0, Death 1.8, Dead 0.7 cm: its plane sign is unreliable in the skirt's deep folds
   (the flagged shins are 4-7 cm inside the cloth). `scripts/robe_ray_check.py` re-tests every flag with rays out from the body axis (living
   clips) or straight up (Death, Dead): **0 really outside in every clip except Death, 2 vertex-frames at 1.8 cm during the fall**; Dead 0.
   The corpse hem was not changed (gather 0.6).
   See-through on r14 (both GLBs, every clip): living clips at most 15 px torso (Hit; 1-px slivers at the belt and silhouette), sleeves 6,
   head 5; Death / Dead from the feet at floor level torso 47, sleeve L 88, collar 71; at the party's 20 deg at most 14 px.
   Viewer check r14: 27 switches, 0 errors.
8. MM9 vs ours: `review/sheet_mm9_vs_ours_r14.png` (each girl: MM9's own model and skin | ours, front / 3/4 / back); final faces
   `review/sheet_face_128_r14.png`.

## Coordinator pass 3 (r15, 0 credits)

Sheets: `review/sheet_before_after_r15.png` (rows: the r14 sheet's "after" from an intermediate, never-installed build; installed r14 re-rendered;
r15; mouth r14 / r15), `review/sheet_viewer_faces_r15.png` (viewer shots, all three girls: face front, 3/4, true profile, low 3/4 from below,
party view, party view of the upper body, 128 px simulation of the party view; the party and low views by temporarily remapping two viewer
view buttons, restored after the shots).
1. **Neck line**: the black line and brown band came from the intermediate render (the chin smoothing had moved the seam vertices; fixed
   before install). Installed r14 and r15 show no line in front, party or 128 px views.
2. **Ghost flaps**: also only in that intermediate render; not present in the installed r14 or r15, nor in the viewer shots.
3. **Lip specks**: the cause was `fill_holes.py`'s fans in the lip slit, whose single-point UV sat on a skin texel: they now take a dark
   lip texel next to the slit. The head paint's gutter fill is chart-aware (`chart_pad` in `head_fix_pg.py`: each UV chart pads its own ring),
   the lip speck pass works only inside the lips' own outline. A few tiny light wedges remain at the very mouth corners in extreme
   close-ups (not visible in the viewer's head preset or at party distance).

## User note r15 (neck seam, ghost nose; r20, 0 credits)

`review/user_notes/neck_seam_nose_front_g2.png`. Sheets (viewer): `review/sheet_user_note_before_after_r20.png` (front close-up r15 | r20, all
three girls), `review/sheet_viewer_faces_r20.png` (front, 3/4, profile, low 3/4, party view; party / low via a temporary view remap, restored).
- **Neck seam**: positions were already welded and normals averaged across the seam (0.02 deg); the line was a colour step and a crease.
  Now: the head's neck within 2.5 cm of the seam blends to each tier's ramped body skin at the seam (`tiers_pg.py` writes
  `textures/body_neck.json`), head and body normal maps flattened 2-3 cm either side, the crease Laplacian-smoothed on welded positions
  (rims pinned, at most 3 mm, `tweak_pg.py`).
- **Ghost nose**: paint outside the geometry's nose (protrusion < 1.6 mm over a smoothed head) takes the surrounding skin; the nose base
  repainted with the nose's own skin and two soft nostril shadows on down-facing texels; the nose-tip hole fill re-textured (dark dot).
  Nose geometry smoothing was tried and turned off (lumpy alae).
- Lower-lid wedges (lid opening compressed further, lighter paint under the iris), dark lip outline / corners softened, dark blobs on the
  chin and lip corners cleaned (lip-red texels protected).
- Remaining: a faint row of light specks on the neck below the jaw in the low / party views, and Meshy's nostril holes still read slightly
  pinched in the lit low 3/4 view.
- After two session kills (reboot, OOM): installed GLBs verified = r15 before each restart; every rebuild since runs under
  `systemd-run ... MemoryMax=12G`.

## Coordinator r20 follow-up (r23, 0 credits)

`review/sheet_before_after_r23.png`, `review/sheet_before_after_r23_zoom.png` (viewer front close-ups r20 | r23, all three girls).
- Bridge: no open edges at the top of the bridge (checked), but 18 vertex pairs closer than 0.5 mm: micro-facets smoothed (at most 1 mm);
  dark paint between the brows takes the surrounding skin; normal map flattened there. The dark diamond is much lighter.
- Chin dimple: dark paint under the lower lip cleaned and the down-facing lip underside lifted, feathered (a first hard box drew a pale
  rectangle, r22, fixed). A soft V shadow remains: it is the lower lip's own geometry.
- Neck specks: a texel pass drew colour across a UV chart edge (a dark triangle on the neck, r21) and was dropped; the faint specks remain.

## Face repaint (r24, 30 credits)

User / coordinator: patching the first paint had hit its limit (nose smear, lip outline, specks, seams, dark marks); a fresh 4K head paint on
the current mesh. Rollback of r23 in `work/rollback_r23/` (GLBs, head textures), the old head UVs in `work/uv_v1.npz`.
- **Head UVs re-laid** (`scripts/uv_head_pg.py`): the face is now ONE chart (was 50 small charts, with the midline, nose and lips on chart
  borders); body UVs and paint unchanged. Topology for the disc: the mirror's midline micro-cluster under the chin welded, duplicate sliver
  pairs dropped, the mouth-corner holes fan-filled. Head atlas 63.7 %, 16 islands, fragments 0.8 %, stretch p90 1.6.
- **Forms** (clay sheet `review/sheet_clay_head_v2.png`): the midline V crease (light line down lips and chin) by depth-only smoothing of
  the lower-face midline (`tweak_pg.py`, at most 2 mm) and the face's shading normals fading their sideways part to 0 at the midline
  (`build_glb_pg.py`); a folded triangle pair under the chin collapsed. Nothing else reshaped.
- **Masters** (`references_head2/`, one Codex run): paint-overs of viewer-lit renders of the current head of each girl, with the earlier HD
  portraits and MM9's girls as reference. Codex reported that exact landmark registration drifted; Meshy's retexture fitted them to the mesh.
- **Retexture** 4K per girl (`requests/retexture_head2_*.json`): front, three-quarter, profile, plus the earlier back views.
- **`head_fix2_pg.py`** (light touch): nose underside (and cavity walls) repainted with the nose's own skin and two small soft nostril
  shadows centred on the geometry's openings (found on the mesh), the down-facing underside paint lifted to counter the top light; dark
  brown paint on the nose tip, small dark / light marks (chin dimple, bridge, forehead strands) from the skin round them; Meshy's thin pale
  lines along the face chart's cuts (top-hat filter) and 3 px seam halos removed; mouth slit a soft lip shadow, dark corners to skin; neck
  blended to the body skin at the seam; normal map flattened on the face skin (its relief drew ridges up the bridge), per-chart padding.
- Sheets (viewer, read zoomed): `review/sheet_before_after_r24.png` (front close-up, r20-23 paint | r24, all girls),
  `review/sheet_viewer_faces_r24.png` (front, 3/4, profile, low view from below, party), `review/sheet_zoom_front_below_r24.png`.
- Gates r24: arm/hand 0 frames > 1 cm; robe ray check 0 outside except Death 2 vertex-frames 1.8 cm; sleeve poke Hit L 2.6 mm (2 v); flat 0.01; see-through (h living max 15 corpse max 88 party 20deg max 14; e living max 15 corpse max 88 party 20deg max 14; ; [exited with code 0]); binding test PASS 222 / 97; floor 3 ok; viewer 0 errors.
- **Remaining marks** (viewer, user's zoom): faint pale lines from the inner eye corners up the sides of the bridge; the nose base reads a
  little dark under top light and the nostrils from below as a soft dark V (geometry shading); a thin dark mouth slit with small dark
  corners; a small dark dot in the chin dimple under the lower lip and a faint light line down the chin's midline; the dark area under the
  chin from below is lighting; g2's cheeks are paler than before.

## Paint pass on r24 (r25, 0 credits)

Coordinator review of r24: forehead / bridge marks, a wan look, a pursed mouth, earlobe specks, nostrils from below. Rollback of r24 in
`work/rollback_r24/`. No new Meshy or Codex work; the r24 paints and UVs are unchanged.
- **Forehead midline and bridge**: the texture was clean there; the stitch-like kites were the per-vertex shading of Meshy's small midline
  facets. `build_glb_pg.py` averages the face normals within 1.8 cm of the midline from the bridge to the hairline (8 passes, feathered;
  positions unchanged); `tweak_pg.py`'s depth-only midline smoothing now reaches up the forehead; `head_fix2_pg.py` blends a 4 mm paint
  band on the midline (forehead, chin) into the skin round it.
- **Warmth** (`head_fix2_pg.py`): a soft cheek blush per girl (g2 0.30, g3 0.16, g1e 0.20), lips 35 % toward a rose (no outline).
- **Mouth**: corners lifted to the skin (paint below 0.97 of the local skin round the corner notches) and the corner notches' normals
  averaged like the midline (`build_glb_pg.py`); the slit line fades out toward the corners.
- **Earlobe specks**: a few crumpled head-shell triangles of the ear root poked out sideways between the jaw and the hair;
  `tweak_pg.py` draws the shell behind the jaw's front edge at ear height in to 6.3 cm off the midline so the hair covers it (the elf ear
  part keeps its place); the head side under the hair takes the jaw's skin.
- **Nostrils from below**: smaller painted nostril shadows (radii 1.6 / 2.2 / 1.6 mm, darkness 0.42) and the nose underside's normals lean
  55 % toward the face's forward direction (the remaining dark V was the top light on down-facing faces).
- Sheets (viewer, read zoomed): `review/sheet_before_after_r25.png` (front close-up and low view from below, r24 | r25 per girl),
  `review/sheet_viewer_faces_r25.png` (front, 3/4, profile, low, party).
- Gates r25: winding 0 inverted (both); binding test PASS 229 / 100; floor 3 ok; flat 0.01 / head 0.00; see-through living clips
  (Standing, Walking, Running, Talk, Fidget; both GLBs) torso max 8 px, head 3, sleeves 2 (`review/gates/see_through_r25_*.json`).
- **Remaining**: a small dark V in the chin dimple under the lower lip; from below, the nose underside is still a soft brownish triangle
  (lighter, no dark pits); a thin crack of background pixels on the side of the neck at the head-body seam in profile (also in r24).

## Mouth, muzzle and hairline (r26, 0 credits)

User review of r25 ("whats wrong with the mouth?", `review/user_notes/mouth_front_g2_r25.png`): a lighter oval round the mouth with an
edge, a tight pursed bud with dark wedge corners, a dark dot under the lower lip, a sawtooth hairline. Rollback of r25 in
`work/rollback_r25/` (GLBs, head textures, the three scripts). No Meshy or Codex work; paints and UVs unchanged.
- **Sources found** (unlit and clay renders): the oval is in Meshy's paint (a duller, browner disc with a rim; not the shading); the bud is
  geometry (lower lip 2-3 mm proud, a recessed slit with corner notches); the chin dot was the dimple notch plus r23's lift (a light blob);
  the sawtooth is the head shell's face chart (skin) meeting its scalp chart (hair colour) along triangle edges under the hair's edge.
  No loose lip pieces (head shell + two eyeballs only).
- **Relaxed mouth** (`tweak_pg.py`, like the boys' `lip_sculpt.py`): the mouth patch's front surface (|x| < 3.1 cm, 2.6 cm below to 1.35 cm
  above the lip line 0.6272) is replaced by a smooth base (a low-order surface fitted to the face round it: rms 2 mm) plus subtle lips
  sculpted into it (upper +0.8 mm, lower +1.2 mm, 0.3 mm groove, 0.5 mm mentolabial dip, faint philtrum, corners tucked 0.6 mm); depth only,
  at most 2.9 mm; the slit's inner faces follow their nearest front vertex. The chin dimple notch is gone with it.
- **Paint** (`head_fix2_pg.py`): the muzzle's colour field (front view, 0.5 mm grid, 2 mm blur) is replaced inside an ellipse by a
  harmonic fill from the face round it, each texel scaled by fill / field (detail kept), and the rim's thin line removed by a dark
  top-hat; the slit's inner faces take a soft rose line fading to skin at the corners; pale specks on the lips' inner edges take the lip
  colour; the chin-dimple lift dropped. Hairline: a band from 2.6 cm under the hair's front edge to it takes the skin carried up from
  below (front-view grid) and the hair-root colour in the last 5 mm, with ±3 % detail, on both charts.
- **Normals** (`build_glb_pg.py`): the mouth's inner faces (more than 2.5 mm behind the front) take the front's normal.
- Tried and dropped: a bilaplacian base (overshot to 6 mm), closing the slit pocket to the front (cavity paint poked through), corner
  rules at 1.2 mm depth (pale / grey boxes at the corners).
- Sheets: `review/sheet_before_after_r26.png` (rows front close-up, 3/4, profile, from below, party; r25 | r26 per girl),
  `review/sheet_mouth_zoom_r26.png`.
- Gates r26: winding 0 (both); installed = export; binding test PASS 230 / 101; floor 3 ok; see-through (human, Standing / Talk / Fidget)
  torso max 8 px, head 3, sleeves 2 (`review/gates/see_through_r26_h.json`).
- **Remaining**: small dark ticks at the mouth corners (the corner notch geometry, much smaller than r25's wedges); the slit is a thin
  slightly jagged line; a faint trace of the oval's rim at its far sides on g2; the soft brownish triangle under the nose from below.

## Final mouth and fresh head paint (r27, 30 credits)

Coordinator review of r26: pale specks along the slit, dark corner ticks and a jagged line remained because the r24 paint was made for the
old mouth. As on PeasantM3: finalise the geometry, paint fresh on it, no geometry moves afterwards. Rollback of r26 in `work/rollback_r26/`
(GLBs, head textures, scripts).
- **Geometry, final** (`tweak_pg.py`, positions only): the lip edges along the slit follow one smooth symmetric curve (a closed line at
  0.6270 rising 1.4 mm to the corners), 0.3 mm either side of it and closing to nothing at the corners; the slit's pocket (inner vertices
  within 8 mm behind the front) drawn onto the line just behind the edges, so the corners flow into the cheeks; the rows beside the line
  relaxed in height and (within 4 mm) depth. The midline's sub-millimetre facets on the line share one normal (`build_glb_pg.py`, a light
  tick before). Clay check front / 3/4 / profile / from below. The upload (`texturing/pg_head3_upload*.glb`) is `work/uv_geo3.npz`, the
  build's own `uv_tex2.npz`, so the paint and the runtime mesh are the same geometry; AO re-baked (`textures/pg_head3_ao.png`).
- **Masters** (`references_head3/`, one Codex run, `scripts/codex_heads3.sh`): paint-overs of viewer renders of the current heads, the MM9
  girls as identity; the brief points the mouth at the render's thin mouth line (the old lip paint no longer fitted) and asks for calm,
  warm, closed relaxed mouths, rosy cheeks, no makeup, the skin round the mouth the cheeks' tone. Codex reported registration was not exact.
- **Retexture** 4K per girl (`requests/retexture_head3_*.json`, jobs `pg_head3_*`), compose + `sym_paint.py` as before.
- **Paint fixes only** (`head_fix3_pg.py`, replaces `head_fix2_pg.py` in `rebuild.sh`): nostril shadows on the openings with the underside
  lifted, neck blend to the tier's body skin, hairline gradient band, seam halos and thin pale lines (Meshy drew pale strands across the
  forehead and fringe again), normal map flattened on the face skin; hand tone stays in `tiers_pg.py`.
- Sheets (viewer, read zoomed): `review/sheet_before_after_r27.png` (rows front close-up, 3/4, profile, from below, party; r26 | r27 per
  girl), `review/sheet_mouth_zoom_r27.png`.
- Gates r27: winding 0 (both); installed = export; binding test PASS 238 / 104; floor 3 ok; see-through, every clip, both GLBs
  (`review/gates/see_through_r27_{h,e}.json`): head at most 3 px, living clips at most 8 px, Death from the feet sleeve 41 / collar 30 /
  torso 19 (r24: 88), party 20 deg at most 8.
- **Remaining** (read zoomed): a faint greyish smudge with fine vertical streaks under the lower lip (all three); a lighter pink patch in the
  middle of the upper lip (g2, g3); the nostrils read a little darker from the front; g2's cheek warmth runs as a broad brownish-rose patch
  down to the jaw in 3/4; g1e has heavy dark lashes and upper lid line (mascara-like); from below the soft brownish triangle under the nose
  and the dark area under the chin (lighting); the pale ear-stub triangle at the hair edge in profile; the neck-seam crack in profile was
  not re-checked.

## Upper-lip patch (r28, 0 credits)

User review of r27 (g2, `review/user_notes/upper_lip_patch_g2_r27.png`): a pale, blurry rectangle over the upper lip / philtrum with hard
side edges at the mouth corners. Rollback of r27 in `work/rollback_r27/`. No Meshy, no geometry moves.
- **Source** (unlit / clay renders): in the paint, not the shading. `head_fix3_pg.py` built its masks from `work/headmap.npz`, the texel
  positions of the r24 geometry: the slit's former pocket faces (now on the lip line after r27) were still taken to lie behind the mouth,
  and the nose-underside mask (z 0.624-0.646) reached down over the upper lip, whose lift (up to 1.6x) painted the pale band.
- **Fix**: `headmap_final_pg.py` (NEW) maps the texels on the final painted geometry (`work/uv_geo3.npz`) -> `work/headmap_final.npz`,
  which `head_fix3_pg.py` now uses; the nose underside starts above the lip (z > 0.6345) and is lifted only where it truly faces down; the
  r26 muzzle fill (front-view harmonic fill from the cheeks, lips kept) runs on this paint; any remaining pale band between the line and
  7 mm above it takes the front-view colour field round it; the grey vertical streaks under the lower lip take the field round them, and
  their normals are averaged (`build_glb_pg.py`, positions unchanged).
- Sheets (viewer, read zoomed): `review/sheet_before_after_r28.png` (rows front close-up, 3/4, from below; r27 | r28 per girl),
  `review/sheet_mouth_zoom_r28.png`.
- Gates r28: winding 0 (both); installed = export; binding test PASS 240 / 105; floor 3 ok. Geometry is unchanged from r27, so its
  see-through results stand.
- **Remaining**: a faint darker shadow line along the mouth line at the corners; soft vertical shading at the philtrum's sides; from
  below, the brownish triangle under the nose and the chin's underside shadow (lighting); g1e's heavy lashes.

## Sheets (read by me)

`review/sheet_tiers_head_r4.png` (viewer heads, 3 tiers x front / 3/4 / side / rear), `review/sheet_tiers_body_r4.png` (bodies, shoulders,
arms), `review/sheet_ears_r11.png` (ears and under the jaw, both GLBs), `review/sheet_back_of_head_r11.png` (back of the head in Standing,
Cower, Hit, Death, Dead), `review/sheet_face_128_r12.png` (each girl front / party / party 3/4 at full size next to a 128 px simulation),
`review/sheet_hands_face_r11.png` (hands beside the face, Cower and Talk, g3), `review/strips_tex_g2.png` (every clip, six frames),
`review/strips_clay_a.png` / `_b.png` (MM9's own mesh vs ours, same clips), `review/clay_dead4.png` (corpse skirt), `review/face_g2_fix.png`,
`review/face_g3_fix.png` (face fix iterations), `review/sheet_asm.png` (assembly), `review/mm9_refs.png`, `review/mm9_heads.png` (MM9).

## Deviations and open points

- **Two GLBs**: the elf ears are geometry, so the elf girl is its own GLB from the same project (same mesh, rig, clips, UVs and body paint;
  the cook shares the body textures). The boy family carries its elf ears as an attachment instead; that would be the next step here too.
- **Hands**: MPFB five-finger child hands (MM9: two chains); relaxed curl.
- **Corpse**: the gathered skirt still crumples at the feet end, and the shin knee ends touch it (robe gate Death / Dead).
- **Hair**: one long helmet; in Cower (head bowed into the hands) the crown stands up behind as in MM9's own silhouette.
- **Braids**: painted on the hair, not modelled (MM9 has them painted too); their gold ties are paint only.
- Map placement not switched (orchestrator's step): the rebuilt maps still place 595 for `CommonerChildHuman2ChildA`.

## 2026-11-04: gold embroidery on g3 / g1e (user review)
User: "variants b/c are losing the texture detail like these patterns on the fabric; initial variant has it" (screenshots in
`review/user_20261104/`). The 2026-11-02 coordinator choice (plain tone-on-tone bodice for g3 / g1e, as MM9's skins) is reversed:
`tiers_pg.py` now gives g3 / g1e a vest ramp whose dark end is their own dress cloth and whose bright end blends to g2's gold, so the
bodice, cuff and belt embroidery reads gold on navy / teal. Only the g3 and g1e vest ramps changed (body tone, mask, classes and g2's
ramps byte-identical, backup in `work/backup_20261104/`); `build_runtime.sh human|elf` rebuilt from the unchanged `work/half_*.glb`,
installed, viewer r28-20261104. Binding regression PASS (248 descriptors on 110 models). Sheet: `review/sheet_bodice_gold_r28.png`.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantgirl_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantgirl_reduce_claude/before/`.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantgirl_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantgirl_reduce_claude/before/`.
