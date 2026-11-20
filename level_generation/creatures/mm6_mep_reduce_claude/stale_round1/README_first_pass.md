# MM6 Mep / PeasantM3 A/B/C reduction and face retexture (2026-10-14, not installed)

User: "3D tris count reduction playbook - do mm6_mep". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md))
on the installed `assets_source/worlds/mm6/models/mm6_mep.glb` (10,066 body tris, 8 influences, one texture set: body
left 1024 px, head set right) and `mm6_mep_staff.glb` (1,616 tris). Started with
`../reduce_installed.sh mep Mep "MM6 Mep"`; weld 7,354 -> 904 open edges; limits for the 1.692 m height p99 5.08 mm,
max 25.38 mm. Region scripts copied from `../mm6_natf_reduce_claude/` (`run_ladder.sh`, `build_pick.sh`, drift check,
prop chain), close views from `../mm6_nobl_reduce_claude/`. Meshy: 10 credits (face retexture below).

## Body ladder

| config | step | tris | p99 / max mm | IoU | SSIM | visual |
|---|---|---:|---|---|---|---|
| source | | 10,066 | | | | |
| uniform | 70 % | 7,046 | 3.0 / 33.3 | 0.995 | 0.993 | fails max (upper back, Death) |
| uniform | 55 % | 5,536 | 4.6 / 38.1 | 0.989 | 0.990 | fail |
| regions g1 | 62 % | 6,276 | 4.4 / 23.8 | 0.989 | 0.990 | passes; dark slits on the turban top |
| **regions g3** | **62 %** | **6,274** | 4.4 / 23.8 | 0.988 | 0.990 | **pick**, turban matches |
| regions g3 | 57 % | 5,872 | 5.3 / 23.8 | 0.986 | 0.989 | fails p99 |

Regions (`scripts/mep_regions.py`, colour classes of the head set from `work/basecolor.png`): kept exactly = face skin
plus one ring (642), eyes (43), buttons (141) and, in g3, the separate turban-top piece (component 22, 346 faces;
at 60 % it sank into the turban wrap and showed dark slits). Group ratios: hands 50 %, turban wrap 60 %, beard 70 %,
belt + sash ends 70 %; the rest takes the ladder budget. Texture drift: 2 faces over 40 (1.2 cm2 at the sandal
soles), so no lock round.

## Staff

Prop chain (`prop_dump.py` -> `prop_ladder.py` -> `prop_build.py` -> `prop_swap_glb.py`): every step passes; r25 =
404 tris (max 0.28 % / 3.9 mm of 1.41 m), close-ups identical to installed and r35 (`review/props/staff_close.png`).
LOD chain 404 / 352 / 160 (the old 528 LOD1 is dropped as no longer coarser).

Grip gate (`scripts/grip_gate_mep.py`, staff at the Staff joint as at runtime, every 2nd frame of every clip, Death
before the release): hand-to-shaft gap max 0.33 mm (installed 0.18 mm), no hand vertex inside the staff, all clips.
Renders `review/grip/grip_sheet.png` (rows installed / pick: Standing, Attack, Cast).

## First result (superseded by the face retexture below)

`export/mm6_mep_g3r62.glb`: **6,274 tris**, LODs 6,274 / 3,134 / 1,127 / 372 (installed 10,066 /
4,494 / 3,594 / 3,494); variants on every LOD and shadow primitive; LOD texture sizes kept (2080/2080/1056/544).
`export/mm6_mep_staff.glb` (= `mm6_mep_staff_r25.glb`): **404 tris**.
Renders: `review/close/sheet1_*.png` (standing whole/head/hand), `sheet2_whole.png`, `sheet2_back.png`,
`sheet2_head.png` (rows installed / pick: Standing 0, Death 30, Attack 20, Cast 20), `work/turban.png`.
Viewer `review/viewer/` (installed vs pick, all variants and clips; `check_viewer.mjs` 54 switches, no errors).
The torn chest/beard look in Attack and Cast is in the installed model too.

## Face retexture (2026-10-14)

User on the pick: "face needs retexture" (screenshot: smeared eyes, dark nose streak, ragged mouth). The face is the
installed one (kept exactly in the reduction), so the defects are in the installed texture. One Meshy head retexture,
10 credits (lease `mm6:mep-reduce`, budget 10, held for the install).
- `scripts/head_uv.py` (on `work/ladder_g3.blend`, Cand_62): head-set faces (atlas u > 0.5) are split by the installed
  colour into turban (pale blue, 717 faces, island shapes kept) and face part (661: skin, eyes, brows, beard, neck
  cloth), which is unwrapped again as whole charts; skin and eye islands at 1.6x; the whole head set is packed again
  without overlaps (the installed head layout overlapped 325 faces). Skin 18.6 texels/cm (installed 12.1), beard and
  cloth 11.6 (11.9). `texturing/head_upload.glb` (all head faces), `texturing/head_uv_layout.png`,
  `work/head_uv.npz` (new and installed UVs and rest positions per head triangle). The layout is deterministic:
  reruns reproduce the uploaded one byte for byte (checked).
- Meshy `head_retexture_r62` (`requests/`, the accepted HD head references from `../mm6_mep_codex/references_head/`,
  `enable_original_uv`): UV parity exact, per vertex.
- `scripts/compose_head.py` (6 s): turban texels copied per triangle from the installed maps at their installed UVs,
  normals rotated with each triangle's UV frame; seven "turban" triangles whose installed mask is partly skin are
  forehead faces and take Meshy texels (copied, they showed as a skin wedge between the brows); the ears keep the
  installed texels (Meshy painted them grey); Meshy skin in the white head band above z 1.576 m takes the nearest
  band texel. Meshy white is quantile-matched per channel to the installed white; skin luminance half quantile-matched,
  half mean-shifted (the full match brought back dark veins); mask and specular/roughness per class from the installed
  medians (skin A, white B); normal convention measured (Meshy +y down, flipped).
- `scripts/head_atlas.py`: the head half of all four LOD atlases (2080 / 2080 / 1056 / 544 px), body half untouched;
  then the usual `build_pick.sh r62 head` chain (LODs 6,274 / 3,134 / 1,127 / 372).

`export/mm6_mep.glb` (= `mm6_mep_headr62.glb`): **6,274 tris**, new face, turban/body as installed.
Renders: `review/faces/face_sheet.png` (rows installed / new: front, three-quarter, side), `review/faces/tiers_sheet.png`
(tiers A/B/C, installed / new). Viewer: installed / final / pick before the retexture, all variants and clips;
`check_viewer.mjs` 81 switches, no errors. Known: a small grey notch at the upper right of the head band (a turban
triangle with the installed band colour); tier C beard slightly less green than installed.

Install after review: back up the installed sources to `work/mm6_mep_source_pre_reduce.glb` and
`work/mm6_mep_staff_source_pre_reduce.glb`, then `tools/install_model.py export/mm6_mep.glb --world mm6` and the same for
the staff, run the actor regression, add the ledger row.
