# MM9 Bjarni Thorvaldssen (`mm9_bjarni`) see-through linings: candidate v5 ready for review (2026-11-05; not installed; lease released)

Brief: [LINING_BRIEF_20261105.md](../../../devdocs/mm9_rework/overnight/LINING_BRIEF_20261105.md) (user 2026-11-05: line the four worst
bodies of the 2026-11-02 sweep). Lease `mm9lining:bjarni` (owner bjarni-lining-20261105); `mm9:bjarni` and `mm9reduce:bjarni` were free.
Source: the installed `assets_source/worlds/mm9/models/mm9_bjarni.glb` (sha256 ef96e332ec88, the reduced b60 of
`../mm9_bjarni_reduce_claude/`), copied to `before/` (rollback). No Meshy, no repaint, no new texture, no engine/game edits. **Not installed.**

**Candidate: `export/mm9_bjarni.glb` (= `export/mm9_bjarni_v5.glb`, sha256 12ac4a30c3ac)**, lining triangle centres in
`export/mm9_bjarni_v5_lining.npz`.

**v5 (coordinator review of v4, 2026-11-05):** v4's yoke underside, a single dark texel, read as a large flat dark slab around the
shoulder in the side view and in Applause (`sheet_close_v4_6.png`, `sheet_close_v4_1.png`). v5 lines the yoke with twins that keep the
yoke's **own UVs** (olive-brown cloth and patterned orange border, Tryggva's fur-cape route: `own_uv` in line.py), 1.5 mm under the yoke
instead of 3 mm; the rim strips keep the yoke body-colour texel (0.22, 0.16, 0.00) and read as the cloth's edge. Everything else is v4.
Re-rendered and read at full size: `review/sheet_close_v5_{1..6}.png` (yoke_side in `_6`, applause_yoke in `_1`), `review/sheet_body_v5_{1,2}.png`:
the underside now reads as the same cloth seen from below (border pattern included). The v4 sections below still hold for v5 unless a v5
number is given.

| | LOD0 | body `Bjarni` | head `BjarniHead` | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed (reduced) | 6,841 | 3,849 | 2,992 | 3,413 | 1,219 | 399 |
| **lined v5** | **8,359 (+1,518)** | 5,254 (+1,405) | 3,105 (+113) | 3,918 | 1,402 | 461 |

Every installed LOD0 vertex row (position, normal, UV, joints, weights) and triangle is byte-identical; lining rows and triangles are
appended (`review/gates_v4/same_lod0.txt`: LOD0 EXACT + APPENDED). Clips (18), skin, nodes, materials, textures and the 6 images are the
installed ones (`same_clips.txt`). New vertices copy the joints/weights of the vertex they line (cap centre: the rim's mean, 4 largest).

## Measured first (installed GLB, sweep settings: step 4, 4 mm pixels, 16 views, every clip; `review/st_before/`)
Per-face hole map (`scripts/hole_faces.py`): **88 % of all hole pixels are the yoke** (piece 277, 231 tris: a single-sided cape over
the shoulders whose back panel and front flaps stand off the body; its underside is what the sweep's torso, collar and sleeve zones
counted), 9 % the tunic skirt underside (piece 1741), 2.5 % the boot tops / knee backs (piece 166), the rest the necklace beads, buckle and
studs (open cups, 21 small pieces), the head shell's nape and the neck band. The tunic has no open cuffs (the hands are grafted stubs
inside closed sleeves).

## Linings (`scripts/ops_v4.json`, `scripts/line.py`: PeasantM1d's GLB-level line.py, adapted: no region mask on Bjarni, `dark_from: band`,
`uniform`, `pct`, multi-map `holes` with a bone filter)
| op | kind | faces | texel |
|---|---|---|---|
| yoke (outer edge 51 v + neck 38 v loops) | band (whole yoke, **v5: own-UV twins 1.5 mm inside**; 44 inner-layer faces at 0.5 mm) + rim strip | 231 + 182 | **v5: the yoke's own paint**; strips: yoke body colour (0.22, 0.16, 0.00) |
| skirt (hem 31 v + waist 30 v) | band + rim | 171 + 122 | skirt dark (0.32, 0.24, 0.07) |
| boot tops R/L (calf loops) | band 15 cm, Calf faces + rim | 119 + 36, 97 + 28 | boot leather (0.16, 0.04, 0.02) |
| neck cap (head shell's 25 v neck opening) | cap | 25 | head-set dark (0.19, 0.12, 0.06) |
| neck band, trinkets (beads/buckle/studs), legs, nape | exact reversed copies (own UVs) of faces with hole pixels (before + v1 maps, `min_px` 3/3/5/20) | 13, 203, 216, 75 | own paint |

Rejected on the way: v1 foot/sole caps (dark lines at the sole junction in the soles-up Speak16 and corpse views: they sat in front of
the sole; replaced by the legs reversed copies), the v3 yoke texel (darkest patch 0.11, 0.08, 0.00: a black slab in every side view,
`review/sheet_close_v3_6.png`; v4 differs from v3 only in that texel, same geometry).

## See-through (DM2 zones, max hole px over every clip; `review/st_before/`, `review/st_v5/` on the candidate itself; v4's `st_final/` gave the same maxima)
| zone | installed (worst clip) | lined v5 |
|---|---:|---:|
| torso | 2,522 (Death) | 2 |
| collar | 793 (Death) | 6 |
| sleeve R / L | 647 / 630 (Running) | 4 / 3 |
| boot R / L | 54 (Speak16) / 43 (Running) | 3 / 4 |
| head | 21 (Death) | 5 |
| trousers L / R | 21 / 8 | 3 / 0 |
No zone worse in any clip (`python3 scripts/st_table.py before final`).

## Other gates (installed numbers: `../mm9_bjarni_reduce_claude/review/gates_b60/`, the same file; lined: `review/gates_v4/`)
- **UV audit** (`reduction_uv_audit.py` vs `before/`, v5 `review/gates_v5/uv_audit.txt`): **0 escaping LOD0 faces** both primitives.
  LOD1-3 (rebuilt): body/head 151/138, 124/136, 66/90 (v4 144/138, 115/136, 56/90) vs the installed file's own 147/137, 107/139, 62/90.
- **Winding** 0 inverted closed parts (v5). v5 LOD0 rows exact + appended, clips/skin/nodes/materials/images identical (`review/gates_v5/`).
  LOD heights/floor v5 (`review/lod_compare_v5.txt`): same as v4 below (LOD3 461 tris). The remaining gates (jitter, arm/hand, sleeve
  poke, detached, bones, beard, shading) were run on v4 (`review/gates_v4/`; v5 changes only the yoke lining's UVs and offset) and the
  coordinator accepted their flags. **Sleeve poke** identical. **Bones** identical (the two thigh notes). **Beard** equal (gaps
  within 0.03 cm). Flat shading body 0.0 -> 0.4 % (the rim strips), head 0.1 % both. Texture quality: atlas 59.9 % / 44.7 % both
  (density p10 reads 0 and the spread explodes because the lining faces are one texel; islands 136 -> 145).
- **LODs** (`scripts/build_lods.py`, the reduction's: 31 of 31 protected points snapped; DM2's `shrink_shadow_lods.py` drops 970/356/149/...
  one-texel triangles from the shadow meshes; fix_winding 0): height 1.799 m LOD0-2, 1.8014 LOD3 (installed the same); lowest point per
  clip within 0.6 mm of the installed LOD at every level, LOD1-3 within 0.8 mm of LOD0; 0 stretched faces (`review/lod_compare_v4.txt`).
- **Lining poke, render, v5** (`review/st_v5/`): max 30 px/clip (Death), own-piece max 28 (Applause), and those now show the yoke's own
  paint; geometric (`review/lining_gate_v5.txt`): yoke twins at most 1.44 mm past the yoke (v4 2.9), the rest as v4.
- **Lining poke, render, v4** (gate with `lining=`): visible lining faces with any front face within 2 cm behind them max 34 px/clip; of those,
  "own-piece" pokes (the face behind belongs to the lined garment itself, `scripts/see_through_gate.py` addition) max 34 px (Applause),
  all on the yoke's front flaps at the shoulders. Close-ups of every such worst view (`review/sheet_poke_v4_{1,2}.png`) show the dark
  lining only where the installed model showed the tunic or background through the flap (the flap seen from its back, at folds); no dark
  speck on the yoke's outer paint. **Geometric** (`scripts/lining_gate.py`, 10 fps): yoke twins up to 2.9 mm past the nearest outer yoke
  triangle at folds in arm-raising clips (Applause, Shot1A, Fidget), boot twins 1.6-3.0 mm against the trousers inside the boot (another
  layer, not visible), neck cap centre 30.7 mm in Shot1A (inside the collar; measured against the head shell); the renders above are the check.
- **Jitter**: AttackMelee L shoulder skin 5.34 mm/f2 FAIL (installed 0.14). Statistic artefact, as Hanndl's lined Hit: the gate's p95 over
  Clavicle/UpperArm-dominant vertices now includes the yoke lining rows. `scripts/jitter_split.py`: installed rows identical; lining rows
  never move more than the installed rows (AttackMelee max 247 vs 318 L, 243 vs 386 R; Hit 81.1 vs 85.2; Death 92.8 vs 93.3).
- **Arm and hand** (hands unchanged everywhere): forearm-in-body Fidget R 5.9 -> 0.0 cm, Applause L 1.1 -> 6.0, R 0.2 -> 4.9 (with
  `--outer-only` L equal). The arm and hand vertices are byte-identical; the sign test now meets the reversed copies of the beads and
  buckle (two coincident faces, either normal). Close-ups at those frames (`review/sheet_arms_v4_1.png`) are identical apart from lining edges.
- **Detached**: 1 part "detached" (the 4-triangle belt stud at the R hip, 6.5 mm in Death frame 18). The installed stud floats the same
  6.7 mm at that frame (nearest other face); the installed audit did not flag it, the lined skirt's closed rim changes the audit's
  open-tube rule. Same 46 components, nothing moved.
- Viewer: `run_creature_review.py check` 36 switches, 0 failed, 0 console errors (`review/viewer_check_v4.txt`).

## Sheets read (full size; installed | lined | |diff| x4)
`review/sheet_close_v4_{1..6}.png` (yoke front/back/side/low front/low back, beads, nape, hem front/back/low, boot tops front/back both
legs, Running knees, Speak16 soles, Shot1A/Fidget/Applause yoke), `review/sheet_worst_v4_{1..3}.png` (the sweep's worst view per zone),
`review/sheet_body_v4_{1,2}.png` (front, 3/4, back, party, walk, talk, sit, death), `review/sheet_poke_v4_{1,2}.png`,
`review/sheet_arms_v4_1.png`, and the gate images in `review/st_before/`, `review/st_v1/`, `review/st_v3/` (identical geometry to v4) and `review/st_final/`.
The face is not touched (no head-shell vertex changed; the nape copies and the neck cap sit behind the hair and inside the collar).
Viewer: `http://127.0.0.1:<port>/level_generation/creatures/mm9_bjarni_lining_claude/review/viewer/` (installed vs lined, 18 clips).

## What to look at
The yoke from the side and from below (v5: its underside shows its own cloth and orange border where the installed showed the tunic
or the background through it: `sheet_close_v5_6.png`, `sheet_close_v5_1.png`, the Death view in `sheet_body_v5_1.png`); the shoulder flaps in Applause/Shot1A/Talk (lining visible
behind the shoulder); the skirt from below (brown lining).

## Not checked
In game (not installed; the orchestrator's binding regression); motion at normal speed by eye; LOD1-3 and shadow meshes by eye (numbers only).

## Build (project folder)
```sh
scripts/st.sh before/mm9_bjarni.glb before                          # baseline see-through (+ per-face map)
G=../claude_shared/gltf_venv/bin/python; $G scripts/hole_faces.py before/mm9_bjarni.glb review/st_before/see_through_faces.npz
scripts/build.sh scripts/ops_v1.json v1; scripts/st.sh work/b_v1_lod0.glb v1 lining=$PWD/work/b_v1_lod0_lining.npz
$G scripts/hole_faces.py work/b_v1_lod0.glb review/st_v1/see_through_faces.npz   # the v1 map the legs/nape ops read
scripts/build.sh scripts/ops_v5.json v5    # line.py -> build_lods -> shrink_shadow_lods (DM2) -> carry_variants -> fix_winding -> restore_materials -> check_winding
scripts/st.sh export/mm9_bjarni_v5.glb v5 lining=$PWD/export/mm9_bjarni_v5_lining.npz; scripts/gates.sh export/mm9_bjarni_v5.glb v5
scripts/shots.sh close|worst|body|poke|arms inst lin; $G scripts/pair_sheet.py <set> inst lin sheet_<set>_v4 4
```
Install (orchestrator, on the OK): `check_winding.py` + `tools/install_model.py level_generation/creatures/mm9_bjarni_lining_claude/export/mm9_bjarni.glb
--world mm9 --name mm9_bjarni.glb`, then the post-install note in `../mm9_bjarni_claude/README.md` (a rebuild from the creature master
must re-run the reduction and these linings) and the binding regression. Rollback: `before/mm9_bjarni.glb`.
