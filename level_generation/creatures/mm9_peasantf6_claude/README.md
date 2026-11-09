# MM9 PeasantF6, the elf townswoman with a braid (mm9_peasantf6) — 3D actor variant, 2026-11-02

Variants batch (`devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md`). MM9 `MONSTERS.txt` rows naming `PEASANTF6.abc` (only these two):
**17 Town** "Peasant Elf FemaleB A" (skin PEASANTF6A, DAT class `TownElfFemaleA`, 7 objects) and **19 Shopkeeper** "Peasant Elf
FemaleC A" (skin PEASANTF6B, DAT class `ShopkeeperElfFemaleA`, 5 objects). Two skins = two tiers of one model. Scripts on the objects:
NPCbase.scr, shopkeeper.scr, retainer.scr, Pledge.scr, NPC50.scr (ScriptParams empty: no library clip) -> PeasantF5's clip set.
Status log: `devdocs/mm9_rework/overnight/status/variants_peasantf6.md`. Lease identity `mm9:peasantf6`.

## Decision: variant route on PeasantF5 (frozen, user-approved)
`scripts/abc_compare.py PEASANTF6.abc PEASANTF5.abc`: **identical skeletons** (all 73 bind matrices equal, max diff 0.0), similar topology
(276 vs 253 vertices); legs a rigid 0.47 cm shift; torso/arms within 2 cm (paint-level differences: MM9 paints F5's bare forearms and F6's
sleeves on the same arm geometry); the real difference is the **head**: no coif but a rounded bob of hair, a braid on `FHP Ponytail11` and
elf ears (head up to 7 cm, Ponytail11 up to 8.9 cm). Sheets: `references_hd/mm9_body_f5_vs_f6.png`, `references_hd/mm9_head_f5_vs_f6.png`.
So F6 = PeasantF5's body, rig, weights and clips (bit-identical: `scripts/anim_diff.py ../mm9_peasantf5_claude/work/half.glb work/half.glb`,
max 9.6e-8 on all 216 channels of all 11 clips) + new hair, braid and ears, a new gown paint and two new faces. Own GLB `mm9_peasantf6.glb`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantf6.glb` (`tools/install_model.py --world mm9` from `export/mm9_peasantf6.glb`) |
| Variants | `pf6_a` (row 17 Town, blonde ~25), `pf6_b` (row 19 Shopkeeper, auburn ~45) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block from `scripts/binding.yml` (`scripts/bind_under_lock.sh` under the flock): `MM9 17 Town` (pf6_a), `MM9 19 Shopkeeper` (pf6_b); PeasantF5's values (scale 100, yaw -1.570796327, stride 1.0 / 1.6, look Neck/Head, attacks play Fidget) |
| Descriptors | rows 17 (stand-in 334) and 19 (337) in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`, tables regenerated |
| Triangles LOD0/1/2/3 | 14,556 / 7,247 / 2,607 / 867 (F5's 12,992 - coif 568 - brooches 256 - 84 degenerate fins - 274 needle/zero-UV slivers + hair 900 + braid 800 + ears 588 + caps/collar lining 444) |
| Clips | PeasantF5's: Standing, Walking, Running, Fidget, Talk (conv2), Conv1, Conv3, Hit, Death, Dead, Cower |
| Textures | body 2K colour, 1K normal/ORM, 1K region mask (R gown, G vest + belt) + ramps per tier; head set (head, hair, braid, ears) 1K colour per tier, 1K normal (Meshy's, unmodified) and ORM |
| Meshy credits | **20 / 20**: head 4K retexture A 10 (backup 2950 before), body 4K retexture 10 (backup 2940 before); 2930 after both |
| Codex | body masters (2 runs), head turnaround A (1 run), face repaint A + B (1 run), all through `codex_slot.sh` |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasantf6_claude/review/viewer/ |

## Route (`scripts/`; PeasantF5's scripts copied, F5's project only read)
0. `abc_compare.py`, `mm9_f6_head.py` (MM9 F6/F5 head-region dump), `convert_abc_model.py` -> `source/mm9/pf6a|pf6b.glb`; reference renders
   `ref_renders.py` -> `references_hd/mm9_*`.
1. **Geometry** `make_f6_geom.py work/f5_final_asm.npz work/mm9_f6_head.npz work/f6_geom_v2.npz $(cat scripts/geom_args.txt)`, then the
   84 zero-area fins dropped -> **`work/asm_f6.npz`** (frozen). Start = F5's final geometry (asm positions after F5's `tweak_pf.py`,
   from F5's `work/uv_tex2.npz` via `orig`). Coif and brooches removed. F5's human ears pressed onto the skull (238 vertices, press box
   y -0.052..0.045, z 0.615..0.775, 25 relax passes). The forehead's midline crease (hidden under the coif before) relaxed by Taubin
   passes (no shrink). **Hair**: the skull's hair-region faces (hairline by azimuth round the head) offset outward along smoothed normals
   by MM9 PeasantF6's own hair volume (ray from the head centre to MM9's head mesh, x1.2, 14-60 mm), tapered at the face opening, thinned
   round the ear roots, hairline relaxed along the boundary, a rim strip to 2 mm inside the skull (closed underside). **Ears**: PeasantF8 /
   M7d / M2d cupped leaf, root (0.066, 0.008, 0.668) inside the skull, tip (0.128, 0.042, 0.760) from MM9's, oriented outward by signed
   volume. **Braid**: tube with alternating lobes along MM9's braid line pulled toward the back (2.3 cm off the dress).
   Clay: `review/clay/head_v2d.png`, silhouette vs MM9 `review/clay/sil_f6v2d.png`.
2. **UVs** `uv_pf.py` (adapted; never re-run: the paid paints belong to `work/uv.npz`): body square (hands 1.5x, legs 0.5x, lining 0.3x),
   head square (head + hair + braid + ears, face 1.6x); 17 needle faces and 257 zero-UV-area slivers (< 0.1 mm²) dropped before the upload
   (`work/uv_orig.npz` kept). Uploads `make_upload_pf.py` -> `texturing/pf6_body_upload.glb`, `pf6_head_upload.glb`.
3. **HD masters** (`references_hd/CODEX_BRIEF.md`, skin A design, F5's masters as pose authority, `shape_head_clay.png` as head shape
   authority), halos removed (`clean_alpha.py`), put on F5's landscape canvas and aligned (`align_masters.py`, IoU 0.82-0.93 -> 0.86-0.95),
   front/back arms rotated 7-10 deg to F5's arm angle (`arm_rotate.py`) -> `references_hd/aligned/`. Head turnaround A
   (`references_head/CODEX_BRIEF.md`).
4. **Meshy**: `requests/retexture_body_v1.json`, `requests/retexture_head_a.json` (4K, original UVs).
5. **Maps**: `compose_pf.py` (4K -> 2K/1K once), AO `texpass_bake_ao.py` + `pad_ao.py`, gentle grade (`finish_pf.py`; head graded the same,
   then `sym_paint.py`).
6. **Tiers** `tiers_pf6.py`: R gown (ochre wool by hue on dress/arms/skirt/lining, apron charts and linen left out), G vest + belt (dark
   bodice front panels and the black belt; the floral borders left out); tier A ramps fitted to our own paint, tier B mapped onto MM9 B's
   texels (gown: skirt+sleeve, vest: bodice; a touch more green, `B_GREEN` 1.15: MM9's orange read crimson under the viewer's light). Also
   the lining darkened, shins to stockings, and F5's standing collar (bodice shell above z 0.525) given the neck's skin tone (it was
   painted a greyish skin). Fit error tier A: gown 1.9, vest 11.6 (8-bit; the vest's pattern hues).
7. **Heads** `head_build.sh`: `hair_fill.py` (the bob's lowest band beside the jaw had plain pale paint: strands carried down from 4.5 cm
   above) -> `hair_tier_b.py` (B: hair shell, braid and the skull's front hair texels recoloured onto MM9 B's auburn by luminance
   quantile; pale spill under the bob's edge to skin) -> **`project_face_pf6.py`** (Codex repaint of the flat front render projected:
   A fixed (natural lips instead of Meshy's lipstick mouth, no cheek crease), B a broad warm ~45-year-old face; soft window, the hair
   shell/braid/ears keep their paint; nose underside painted on the geometry as F5's; A window |x| < 6.2 cm, B 8 cm) -> `head_polish.py`
   (the hairline rim's dark arc over the forehead, the neck's sides pulled to the front-of-neck tone). **Meshy's head normal map is
   used unmodified** (coordinator lesson 2026-11-02: never flatten it over the nose and mouth).
8. **Linings** `line_rims.py work/uv_tex.npz work/uv_lined.npz ...`: fans over the head's open neck, the bare arms' open tops inside the
   puffs, the hand stubs' ends and two 4-edge holes; the collar band (278 dress faces within 10 cm of the neck opening) lined 3 mm in, rim
   strip to the neck edge, on one dark gown texel (region R).
9. **Rig and runtime** `rebuild.sh <rev> [--install]` = finish -> tiers -> finish -> line_rims -> `rig.sh work/uv_lined.npz`
   (`fit_rig_pf.py`: Ponytail1/11 at MM9's joints, as F5's rig; `weights_pf6.py`: hair copies the skull weights under it, ears rigid
   Head, braid Ponytail11 with its first 3-8 cm blending to Head) -> `build_runtime.sh` (F5's chain) -> `viewer_update.sh`.

## Approved PeasantF5 unchanged
`work/f5_unchanged.txt`: `assets_source/worlds/mm9/models/mm9_peasantf5.glb` sha256 `cc15d105b676...` = F5's `export/mm9_peasantf5.glb`;
no file in `../mm9_peasantf5_claude/` newer than this project's lease (14:04); F5's actors.yml block untouched (rows 17/19 are a new block).

## Checks (installed r10, sha256 `b5a735ff...`; `review/gates/`)
| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py --outer-only --exact`, 48 fps) | = PeasantF5 (same clips/arms): hands 0 frames over 1 cm in every clip; forearm Cower R 1.0 cm in frame 0 (F5's known coif-free brush); finger stretch max 2.36 |
| Jitter (vs the same clips uncorrected) | 0 fails |
| Skin poke (stub, sleeve) | 0.0 mm every clip |
| Robe (legs through skirt) | 0 frames, all 11 clips |
| See-through (`see_through_gate.py`, step 3, 8 az x 0/20 deg) | r7 all clips: torso 1168 / sleeve L 2201 / collar 731 px (Death/Dead, a view up the skirt of the corpse into the open waist), sleeve R 28, head 3 (pre-linings head 314). r9 after the waist cap (Death, Dead, Hit): torso 57, sleeve L 24, sleeve R 23, collar 9, head 3 (single slivers at silhouette edges) |
| Detached | legs/shoes free inside the skirt by design (as F5/F8); forearm/bracelet lifts <= 1.8 cm in <= 9 poses (as F5); braid rooted (shallow -3.8 mm) |
| Collapse | as F5 (Death waist 80, Hit waist 66 / armpit R 47 face-frames) |
| Winding / bones / flat shading | 0 inverted / 0 stretching / body 0.00, head 0.03 |
| Texture quality | body atlas 63.3 %, fragments 0.5 %, stretch p90 1.05, spread 3.37 (hands 1.5x, legs 0.5x, lining 0.3x by design); head atlas 55.7 %, spread 1.68 (face 1.6x), fragments 0.1 %, stretch 1.07 |
| Floor (`floor_audit.py --match 'MM9 1[79] *'`) | both ok: stand -0.2, walk -0.1..+1.2, living -0.5, dead 0 |
| LOD0 | 14,584 triangles (ceiling 15k) |
| Viewer check | 22 switches, 0 failed, 0 console errors |
| Binding regression `mm9_actor_models_build_every_binding` | PASS, 216 descriptors on 93 models (`regression_binding.log`) |

Sheets read: `review/sheet_mm9_vs_ours.png` (MM9 vs ours both tiers, front/3-4/back/side), `review/sheet_face_vs_mm9.png` (MM9 face
front/3-4/side, ours front/3-4/profile/party 22 deg/64 px party simulation, both tiers), `review/faces_r9.png` (both tiers: front, 3/4,
both true profiles, party, low 3/4, from below, mouth, eyes, nose; viewer-like lighting), `review/sheet_ears_r9.png` (ears front/sides/
backs, from below, both neck sides, bind + Fidget, both tiers), `review/flat_faces_r13.png` (B profiles after the jaw fix), `review/strips_a.png`
(all 11 clips, six frames), `review/clay/head_v2d.png`, `review/clay/sil_f6v2d.png`, `references_hd/mm9_*_f5_vs_f6.png`.

## Deviations and open points
- Hair, braid and ears are our geometry on F5's skull (MM9's bob is a low-poly shell); the bob reads fuller/taller than MM9's from the front.
- Tier A's temples show Codex's paler blond "curtain" strands over the shell's honey blond (front view); B's hair is a recolour of A's
  paint (auburn by quantile) with a Codex-painted face window.
- Tier B: MM9 B has no vest; ours keeps A's laced vest panels (recoloured orange-brown) and the chemise front; no pendant.
- Both faces keep the lips closed (MM9 smiles with teeth). The nose underside shades a little darker under top light (F5's geometry, not
  smoothed: coordinator lesson). Meshy head normal map unmodified.
- Under-chin/jaw: slightly pointed chin in profile (F5's geometry, unchanged); no slab seen in the profiles.
- Map placement (rows still placed as legacy 334/337) is the orchestrator's.

## Not checked
No in-game run (map placement not switched). Strips viewed for tier A only (tier B is the same mesh and clips). Motion at normal speed not
watched. LOD1-3 not looked at. Full see-through rerun on all clips after the waist cap: only Death/Dead/Hit (the cap only affects views up
the skirt). User artistic acceptance not recorded.

## Hair reshape r13 (coordinator review 2026-11-02: "a huge flared bell/helmet"; MM9's hair is pulled back close to the head)
0 Meshy credits. Rollback of r10 in `work/rollback_r10/` (GLB, asm_f6, uv, uv_tex, uv_lined).
- **Geometry** (`make_f6_geom.py`, args `scripts/geom_args.txt`): close cap: hair K 0.75 of MM9's hair volume, 9-30 mm, and a whole-rim taper to
  1.5 mm over 3 cm (`rim_w`, `rim_t`) so the lower edge tucks under onto the skull (no hard horizontal step, no skin gap at the nape);
  `clear=0.004` pushes shell vertices back out to at least 4 mm (or their thickness) above the skull (the relaxation had sunk the thin shell
  into the skull and the skull's paint showed through as a dark arc over the forehead). Same topology as r10, so the paid UV layout holds:
  `scripts/swap_geom.py` replaces the positions in `work/asm_f6.npz` and `work/uv.npz` (hair moved up to 25 mm inward). Silhouettes
  `review/clay/sil_cap2.png` (front, side, top vs MM9), clay before/after `review/clay/cap_cmp2.png`.
- **Paint**: `head_polish.py`: the elf ears (now fully clear of the hair; Meshy had painted hair strands on their backs) repainted as plain
  skin with the paint's fine detail, darker toward the root; the rim strip found exactly (the last 136 hair faces); `hair_tier_b.py`: the
  temple hair recolour fades out downward (no hard edge). `project_face_pf6.py`: nostrils softer (shadow 0.70 of the skin, smaller, softer
  edge).
- Gates on r13 (installed sha256 `2374f7aa...`): see-through (Standing, Fidget, Talk, Hit, Death, Dead, Cower) torso 57, sleeves 23/25, collar 10,
  head 13 px (edge specks); winding 0; LOD0 14,584; binding regression PASS (216 / 93); floor ok; viewer 22 switches 0 failed. Body, rig
  and clips unchanged (hair rigid on the head, so arm/hand, poke, robe and jitter results stand).
- Sheets read: `review/faces_r13.png` (both tiers: front, 3/4, both profiles, back, party, low 3/4, below, nose, ear), `review/crown4.png`,
  `review/sheet_hair_vs_mm9.png` (MM9 vs ours in the viewer: front, 3/4, both sides, back, both tiers).
- Open: MM9's low-poly hair reads wider (an octagonal hull, ears lower at cheek height); ours is now the pulled-back cap the review asked
  for, ears higher and larger. Tier A's temples keep Codex's paler strands.

## Hair and ears to MM9's silhouette r15 (coordinator review of r13: the cap read smaller than MM9; ears too large and high)
0 Meshy credits. Rollback of r13 in `work/rollback_r13/`.
- **Hair** (`make_f6_geom.py`, args `scripts/geom_args.txt` = `geom_args_d.txt`): a rounded bob fitted to MM9 PeasantF6's own head outline:
  thickness = 1.4 x (MM9's head mesh - our skull) along rays from the head centre, 16-60 mm, the lower edge curled under over 1.5 cm (rim
  1.5 mm), 4 mm minimum clearance, braid as before. Silhouettes vs MM9 at the same scale (front, side, top): `review/clay/sil_d.png`,
  clay `review/clay/cand_d.png` (candidates `cand_c.png`, `sil_ab_cmp.png`, `sil_k_cmp.png`). Same topology: `swap_geom.py`.
- **Ears**: 7.7 cm long (was 11.6), 3.2 cm wide, root (0.070, -0.036, 0.698) at the temple just in front of the hair, tip (0.122, -0.008,
  0.748), as MM9's (small, at cheek/temple height); hair thinned round the root (r 1.4-3.0 cm). Still outward-facing; skin-painted.
- **Mouth**: the lip slit is open into the head, so the nape's inside showed through it as pale/gold specks: a small backing plate
  8 mm behind the lips on a lip-shadow texel (`line_rims.py` "mouth backing", 36 faces); slit texels take the nearest front lip texels;
  pale outliers in the lower face take their 3D-neighbour median; the V under the lower lip (F5's chin notch, geometry kept) gets a soft
  3D-weighted lift on its down-facing texels (`head_polish.py`).
- Gates r15 (installed sha256 `1297f605...`): see-through (Standing, Fidget, Talk, Hit, Death, Dead, Cower) head 2 px (13 before the mouth
  backing), collar 10, torso 57, sleeves 23/25; winding 0; LOD0 14,620; binding regression PASS (217 / 94); floor ok; viewer 22/0.
- Sheets read: `review/faces_r15.png` (both tiers: front, 3/4, both profiles, back, party, low 3/4, below, mouth, nose; viewer-like light),
  `review/sheet_hair_vs_mm9_r15.png` (viewer: MM9 / r13 cap / r15 bob, front, 3/4, both sides, back, both tiers), `review/clay/cand_d.png`.
- Open: a faint darker strand streak on the hair just in front of each ear (shell paint); the bob's lower sides stay ~0.5-1 cm inside MM9's
  faceted outline; the chin notch still shades slightly under top light.

## Nose, lip edge and chin r17 (user review: "isnt it a double nose or something?", `review/user_notes/double_nose_front_a.png`)
0 Meshy credits (one paint pass made it read as one nose; no fresh head job). Rollback of r15 in `work/rollback_r15/`.
- Diagnosis: the Codex repaint's nose (alae, tip shading, nostrils) is wider (half-width ~65 px vs the geometry's ~30 px at the alae
  rows) and lower than the geometry's nose, so its outline ringed the real nose; Meshy's head normal map is untouched (lesson).
- `head_polish.py`: the nose zone (an ellipse |x| 2.7 cm, z 0.611-0.661, soft edge) takes plain skin from the surrounding skin at low
  frequency with only pore grain kept, so the geometry's own nose is the only nose; small soft nostril shadows on the real down-facing
  openings (x +-6 mm); the down-facing nose underside lifted 10 %; lip highlight/gold specks to the local lip median; the V under the
  lower lip lifted 28 % on its down-facing facets (geometry kept). `line_rims.py`: the 44 lip-slit sliver faces, whose UVs lay in another
  chart (the gold line in the slit), get their own vertex copies on a lip-shadow texel (positions, weights unchanged).
- Gates r17 (installed sha256 `cd121970...`): binding PASS (229 / 100); floor ok; viewer 22/0; winding 0; see-through (Standing, Talk,
  Hit, Death) collar 10, sleeves 22/24, edge specks.
- Sheets read: `review/sheet_nose_before_after.png` (viewer, both tiers, front/3-4/profile before r15 and after r17),
  `review/faces_r17.png` (front, 3/4, both profiles, below, party, low 3/4, mouth, nose), `review/nose_geo_vs_paint.png`.
- Open: a soft grey shade remains under the nose tip from top light (geometry faces down); a faint chin crease under the lower lip.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_peasantf6_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantf6_reduce_claude/before/`.
