# MM6 Female Peasant (PeasantF1 A/B/C) reduction (2026-10-13)

User: optimise the New Sorpigal goblin, female/male peasant, guard and mage. `../reduce_installed.sh pfem Peasant "<title>"`
(texture-aware reduction of the installed `assets_source/worlds/mm6/models/mm6_pfem.glb`, no retexture). Limits scaled to
the model's height: p99 4.69 mm, max 23.43 mm. Pick r45: auto-pick.

| step | triangles | p99 / max mm | IoU min | SSIM | |
|---|---:|---|---|---|---|
| source | 12,781 | | | | |
| 70 % | 8,945 | 1.92 / 11.36 | 0.9966 | 0.9981 | pass |
| 55 % | 7,029 | 3.2 / 16.66 | 0.994 | 0.9964 | pass |
| 45 % | 5,751 | 4.38 / 17.48 | 0.9925 | 0.9946 | **pick** |
| 40 % | 5,111 | 4.94 / 19.59 | 0.9904 | 0.993 | fail |
| 35 % | 4,473 | 5.93 / 25.05 | 0.9874 | 0.9904 | fail |
| 30 % | 3,833 | 7.0 / 34.32 | 0.985 | 0.9885 | fail |
| 25 % | 3,195 | 8.42 / 34.32 | 0.979 | 0.9851 | fail |

`export/mm6_pfem.glb`: LODs 5,751 / 2,874 / 1,032 / 342, variants carried to every LOD and shadow mesh.
Viewer `review/viewer/` (installed vs pick, every variant and clip; passes `check_viewer.mjs`), close renders
`review/close/sheet_*.png`. Not installed yet.

## Retextured 45 % (2026-10-14, not installed)

User: regenerate the head texture (good quality, no tone fight with the body skin) and the body texture; black
triangle on the back of the clasped hands. Result: `export/mm6_pfem.glb` (5,751 / 2,873 / 1,030 / 339 triangles,
pfem_a/b/c, head merged into the body atlas); the earlier untextured-change 45 % export is
`export/mm6_pfem_r45_noretex.glb`. Meshy: `retexture_r45` (body) + `head_retexture_v1` (head), 20 credits, ~2 min.

Black quad cause: one hand vertex of the reduced mesh carried a full Knife weight (data-transfer weights); with the
knife bone scaled to zero outside Attack its 5 skin faces stretched into the knife's collapse point (three.js viewer
only; Blender drew it correctly). `scripts/knife_fix.py` reweights such vertices from the nearest non-knife master
vertex. Not UV-related, though the reduced mesh's carried UVs also had large UV-degenerate triangles (fresh UVs below).
Other reduced creatures can have the same stray weights on hidden props (bone scaled to zero) and degenerate UVs.

Pipeline (scripts/): `prep_master.py` (original master with the reduced mesh; part/head by nearest master face,
majority per piece; softened custom normals) -> `uv_r45.py` (pfem's `uv_atlas_v2.py` for the body set without the
head faces, twist bones mapped to their arm, folded tube regions re-projected at 80 degrees, overlap gate; head set
smart-projected at 85 degrees, face skin 1.8x density; gate: no triangle below 5 % of its set's median UV density;
coverage 67 % body / 70 % head) -> `knife_fix.py` -> `uploads_r45.py` -> Meshy (UV parity exact) -> `bake_ao_r45.py`
-> `texture_r45.sh` (`dump_uv3d_r45.py`, `compose_r45.py` = pfem's compose_textures_v2 + nape repair and no nape AO,
`tier_ramps_r45.py`, `compose_head_set.py`, `compose_head_r45.py`) -> `runtime_r45.sh`.

`compose_head_r45.py`: skin colour met halfway at the neck (head x sqrt(gain), body skin / sqrt(gain); full match made
the face sallow), surface-space blend within 1.5 cm of the seam, normal maps flattened within 1 cm of it, face-island
low frequencies from a 3D surface average (eyes, brows, nose, lips protected), spill/pale/hair-shadow patches and the
nape repaired by 3D fills (UV inpaint left whole small islands black), braid recoloured to the hair, brass circlet.
Neck seam skin (linear, within 5 cm): head 0.591 / 0.296 / 0.171, body 0.604 / 0.296 / 0.171 (`textures_r45/pfem_head_match.json`).

Review: `review/final/sheet_a.png`, `sheet_bc.png` (three.js viewer captures), `review/hands/`, viewer models
`*_r45t` (63 loads pass `check_viewer.mjs`). Remaining: small pale wedge at the left temple under the circlet (the
installed model has a pale strip there too), slightly warmer chin than cheeks, circlet edges jagged up close.

## Round 2 (orchestrator review, 2026-10-14)

- Hairline: `hair_cover_r45.py` (after the male peasant's `tex_hairmask.py`): skin under the hair/circlet mesh (ray
  along the skin normal) takes the nearby hair colour with darker roots, an 8 mm band outside the mesh edge blends in.
- Chin and mouth corners: low frequencies matched to the cheeks (lip-red kept). Face islands: 3D smoothing at 10 mm,
  skin normal map half flat.
- Nape: skin under the braid takes the neck skin; uncovered nape skin takes the local body neck colour; body nape AO
  fades instead of a hard no-AO region (the hard edge was a pale band).
- Circlet: `circlet_r45.py` rebuilds it as a clean 48-segment ribbon (the reduced band had flaps on the temples), UVs
  in a dedicated square of the head atlas (inside an old island it mipmapped brown); gold bleed on hair/skin removed.
  Total 5,823 triangles (LODs 2,909 / 1,043 / 344).
- Dark spot between the clasped fingers: custom normals transferred from the master faced away from their faces on
  thin parts (173 corners); `normals_fix.py` keeps them only on head skin where they agree with the face. Dark hand
  texels and hand AO also reduced.
- Captures `review/final2/` (sheet_a: hands, clasp, nape, face front/3-4 both sides, neck, whole, fidget, top, both
  sides; sheet_bc), 63 viewer loads pass. Remaining: a narrow pale strip at the right temple hairline in the left 3/4
  view, the chin slightly warmer than the cheeks, the back of the neck a little lighter than the front in side light.

## Round 3: one skin over head and body (2026-10-14, orchestrator, not installed)

User: "looks like a mask over her original skin ... make the body + head uniform, not jagged transitions, not the
weird triangle artifacts". `scripts/unify_skin.py` runs after `texture_r45.sh`, before `runtime_r45.sh` (inputs kept
as `textures_r45/*_pre_unify.png`; idempotent):
- Shared tone: a 3D skin field (1 cm voxels, Gaussian 2 cm) from both sets, head and body toned to meet halfway at the
  neck; every skin texel = its colour x shared / its UV island's own low frequencies (per island: a 3D blur across
  islands left the left/right face halves different, a split down the chin).
- Visible skin from `scripts/exposure_r45.py` (camera-like rays from every 3rd head texel; full-sphere rays called the
  forehead under the circlet hidden): enclosed scalp keeps the hair paint, visible skin starts from the graded Meshy
  head (the round-2 hair band beside the mesh, rays reaching hair up to 4 cm in front of the temples, had painted
  brown strips on visible skin).
- Outside eyes/brows, nose and lip-coloured texels only fine detail (Gaussian 4 texels) rides on the shared tone
  (Meshy's projection seam across the forehead and patches go); features blend in over ~10 texels; the neck and upper
  chest (within 12 cm of the head) the same. Outliers filled from 3D neighbours; scalp seen under the jagged hair edge
  takes hair colour weighted by exposure and hair distance.
- Normal maps flat within 2 cm of the head/body seam and 70 % flat within 5 texels of face UV island borders.
Seam bands (linear, `textures_r45/pfem_unify_report.json`): head 0.526 / 0.245 / 0.141, body 0.547 / 0.256 / 0.146.
Captures `review/final3/` (front, both 3/4, the user's framing, chin, neck, back, torso); viewer loads pass.
Remaining: a thin pale sliver where the jagged hair-mesh edge meets one temple, the lips (reduced geometry) and the
shading under the chin.

## Round 4: head at source density (2026-10-14, orchestrator, not installed)

User agreed to keep the head at full detail (the 45 % face lost its lips, an eye corner and left a forehead crease).
- `scripts/head_protect.py`: source faces nearest the master's head-set face skin and hair (2,859) stay untouched;
  `decimate_tex.py` (REA_PROTECT_HEAD=1, ratio 0.573) reduces the rest to 45 %; the kept boundary welds back exactly
  (open edges 429 = source). Candidate `work_head_proj/work/ladder.blend` Cand_57 (7,323; p99 4.35 mm, max 17.5 mm).
- `prep_master.py` (LADDER/CAND env) -> `uv_r45.py work/r45_master.blend` -> knife_fix -> circlet_r45 -> normals_fix
  -> uploads: 7,393 triangles.
- Body texture carried, no new body job: `scripts/bake_body_transfer.py` bakes the Meshy body return from the round-3
  body (`backup_round3/`) onto the new body UVs (emission for colour/metal/rough, tangent normal with Meshy's DirectX
  green) -> `meshy/retexture_r45_baked/`, used with RETEX_JOB=retexture_r45_baked.
- Head: Meshy `head_retexture_v2` (10 credits; 30 for this model). `claude_shared/compose_head_set.py` takes
  HEAD_RETEX_JOB (default head_retexture_v1).
- Chain: bake_ao -> hair_cover -> exposure -> texture_r45.sh -> unify_skin.py -> runtime_r45.sh.
- Eye review: her left brow and eye washed out — not Meshy (both sides equal in the input) but unify's feature blend
  (a Gaussian of the zone diluted a brow on a smaller UV island into the ±10 % skin path). Features now count fully
  inside their zone and fade over 12 texels; skin-coloured texels inside a feature zone keep their brightness ratio
  with the shared skin colour (an island's warmer hue made an orange socket). Brow darkness left/right 44.5 / 43.3.
Captures `review/final4/`. Rollback of the round-3 state: `backup_round3/`.

## Installed (2026-10-14)

User: "ok good accept it". `export/mm6_pfem_retex.glb` (7,393 tris, LODs 3,695 / 1,326 / 440, variants on every LOD
and shadow mesh) installed as `mm6_pfem.glb`; previous source in `work/mm6_pfem_source_pre_reduce.glb`.
`mm6_pfem_actor_models_bind_town_peasants` passes.
