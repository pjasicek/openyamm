# MM6 Male Peasant (PeasantM1 A/B/C) reduction (2026-10-13)

User: optimise the New Sorpigal goblin, female/male peasant, guard and mage. `../reduce_installed.sh pman_v2 Peasant "<title>"`
(texture-aware reduction of the installed `assets_source/worlds/mm6/models/mm6_pman_v2.glb`, no retexture). Limits scaled to
the model's height: p99 5.61 mm, max 28.04 mm. Pick r45: auto-pick.

| step | triangles | p99 / max mm | IoU min | SSIM | |
|---|---:|---|---|---|---|
| source | 10,554 | | | | |
| 70 % | 7,386 | 2.69 / 14.65 | 0.9954 | 0.9968 | pass |
| 55 % | 5,804 | 3.99 / 15.92 | 0.9912 | 0.9941 | pass |
| 45 % | 4,748 | 4.97 / 20.56 | 0.988 | 0.9919 | **pick** |
| 40 % | 4,220 | 5.99 / 20.98 | 0.985 | 0.9902 | fail |
| 35 % | 3,692 | 6.53 / 20.98 | 0.983 | 0.9885 | fail |
| 30 % | 3,166 | 7.8 / 32.98 | 0.9785 | 0.9858 | fail |
| 25 % | 2,638 | 8.74 / 33.15 | 0.9747 | 0.9835 | fail |

`export/mm6_pman_v2.glb`: LODs 4,748 / 2,374 / 853 / 284, variants carried to every LOD and shadow mesh.
Viewer `review/viewer/` (installed vs pick, every variant and clip; passes `check_viewer.mjs`), close renders
`review/close/sheet_*.png`. Not installed yet.

## Retexture of head and body (2026-10-13, not installed)

User: "male peasant same regeenrate head and body textures" (head of good quality, not fighting the body skin).
Accepted source: `../mm6_pman_claude_20261013/` (master `work/textured_uv.blend`, pre-runtime `export/mm6_pman_v2_lod0.glb`).

- `scripts/build_master.py`: Cand_45 pieces by component majority (each source piece is one component); the face/neck
  skin (piece 1) is kept at source density with its source weights (`REA_SOURCE_PIECES=1`): at 45 % the lips collapsed
  into a notch (`review/r45/face_compare*.png`). **6,116 triangles** (2,989 head set: face 2,202 + 45 % hair).
  Fresh UVs: UVMap over the whole figure (body return), HeadUV over the head faces; smart-project charts re-unwrapped
  angle-based, overlapping triangles cut into their own charts until no texel is shared (41 % / 43 % fill).
- Meshy `body_texture_r45`, `head_texture_r45` (`requests/`, accepted references, `enable_original_uv`, 2k): 20 credits,
  both back in ~2 min; UV parity exact (0 unmatched/changed corners).
- `scripts/tex_chain.sh` (~30 s): parity, rasters, AO, `tex_compose.py`, export, `swap_lod0.py` into the accepted
  pre-runtime GLB, `tex_images.py`, prepare, LODs **6,116 / 3,057 / 1,099 / 366**, shadow LODs, region variants
  (tunic ramps 798 -> 799/800), head merge, KHR specular stripped -> `export/mm6_pman_v2.glb`.
- Compose repairs: skin match, face (piece 1) and forearms/hands (4, 5) both moved to their per-channel geometric
  mean (returns disagreed: arms linear 0.82/0.40/0.22, face 0.53/0.21/0.11 -> both 0.66/0.29/0.16, measured on
  mid-luminance skin); 6,413 skin/cream texels Meshy painted on the collar rim and tunic hem replaced from nearby
  tunic texels; the tier region is the whole tunic except its dark leather bands (a green test left green flecks on B/C).
- Review: `review/retex/face_sheet.png` (installed vs new), `neck_hands_sheet.png`, `tiers_sheet.png`, `poses_sheet.png`;
  viewer models `pman_{a,b,c}_r45t` (54 loads pass `check_viewer.mjs`).

### Review fixes (2026-10-14, user via coordinator; no new Meshy job)

- **Arms** (band-brown smudges under the cuffs; flat, low-definition arms): the first body layout gave each arm ~18k
  texels (installed ~170k). `tex_relayout.py` keeps the Meshy layout as `UVMeshy` and re-packs the same charts
  without rotation, arms x2.6 linear, unused head charts x0.15 (arms now ~83k texels each at 1K).
  `tex_resample.py` (Blender lookup) + `tex_sample.py` resample the Meshy body maps into it per triangle and take the
  arm/hand albedo from the installed model by 3D surface lookup (its covered texels only), colour-matched as before;
  arm normals flat, no second AO, constant roughness. The resampled 2K maps are now nearest-padded before compose
  downsizes them: Lanczos ringing at black chart borders had drawn light seam lines on the skin.
- **Hairline** (painted hairline not matching the hair mesh, pale gap, step): `tex_hairmask.py` finds face skin
  under the hair mesh (ray along the skin normal) and its distance to it; covered skin takes the nearby hair colour
  with darker roots, a 4 mm band outside the mesh edge blends into it. Painted hair farther out (temples, sideburns,
  nape) is kept: erasing it cut a hard light curve.
- **Definition**: the new maps carry as much or more normal/albedo detail per texel than the installed ones; the loss
  was arm texel density (above). Tunic unchanged.
- Skin guard on skin meeting cloth (arms above the wrists, neck below the jaw): nothing left to repair after the arm
  transfer. `tex_chain.sh` now stops on Blender script errors (`--python-exit-code 1`) and resumes with `FROM=<step>`.
- Review sheets: `review/fix/arms_after.png`, `hair_after.png`, `tunic_after.png` (rows: installed / first retexture /
  fixed), `tiers_after.png`; viewer models `pman_*_r45t` updated, 54 loads pass `check_viewer.mjs`.

## Installed (2026-10-14)

User: "male peasant ok". `export/mm6_pman_v2.glb` (6,116 tris, LODs 3,057 / 1,099 / 366, variants on every LOD and
shadow mesh) installed as `mm6_pman_v2.glb`; previous source in `work/mm6_pman_v2_source_pre_reduce.glb`.
`mm6_pman_actor_models_bind_town_peasants` passes.
