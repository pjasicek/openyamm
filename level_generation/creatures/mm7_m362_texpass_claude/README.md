# MM7 Peasant Human2 Male `mm7_m362`: texture quality pass

Separate project for the [texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md) on the installed nine-skin
peasant (palettes 363–371, sheathed rapier in the body mesh), following the
[MM6–MM8 handoff](../claude_shared/texpass_mm678/HANDOFF.md) and the Troll's route
([mm8_m480_texpass_claude](../mm8_m480_texpass_claude/README.md)). Own lease `mm7:m362-texpass` (token in
`work/LEASE.txt`). Production: [mm7_m362_claude](../mm7_m362_claude/README.md) (HD masters, head views, rig);
reduction: [mm7_m362_reduce_claude](../mm7_m362_reduce_claude/README.md); gait clips:
`mm7_m362_gait_h14_claude`.

## Texture quality pass (2026-11-01)

**Installed 2026-11-01.** User feedback (in-game, brown-haired skin with green/purple sleeves, i.e. `m362_ab`):
textures terrible on body and head; a grey stubble-coloured patch around the mouth and chin that does not match the
face; the face must be one continuous skin tone with no seam at the neck. Coordinator follow-up (found on the other
MM7 peasants): shattered, blocky irises and pale shards at the eyes, pale shards in the mouth slit, a hard dark spike
in the nostrils.

### Cause of the face mismatch

Three things, all in the installed build (see `review/texpass_closeups.png`, top rows):
- **The beard region (mask B) was a box, not a beard.** `compose_m362.py` made the "jaw stubble" region a 3D box under
  the nose (from the eye height down to the chin) at a flat 0.7 weight, over the lips too. Every skin recolours it
  through its B ramp: on the bearded skins (ab grey, ac black, ba white, bb olive, cb ginger, as the native sprites) it
  drew a flat semi-transparent colour slab with a straight top edge across the cheeks and over the lips; on the four
  clean-shaven skins (aa, bc, ca, cc) the ramp is the native palette's skin tones, tan-brown against the pink paint,
  so even they showed a brownish box. Measured as the engine shows it (ramps applied, same surface points): mouth
  corners and jaw sides 13.6–21.2 dE from the cheeks on the bearded skins, 5.0–5.3 on the shaven ones.
- **Two paints in two skin tones.** The body set and the separate 1K head set were separate Meshy paints with
  different skin tones and a straight cut at the head-set boundary; the head paint's own neck is a dull grey-beige.
- **Low resolution and fragments:** 1K body + 1K head sets, 575 islands, 9.1 % of the surface on fragments.

### Route (`scripts/`)

1. `dump_lod0.py` (installed LOD0 -> `work/lod0_before.npz`, head set = right half of the old 2080×1024 atlas),
   `dump_pieces.py` (Smart Topology piece/garment per LOD0 face from the read-only production master;
   `python3 dump_pieces.py map` for the mapping step).
2. `uv_texpass.py` (Blender, `claude_shared/uv_atlas.py`, head set ×1.8, hands ×1.3, fast packer `fine=250 steps=0`):
   **`work/uv_fine.npz`, 60.4 %, the paid layout. Never re-run** (hashes in `work/layout_hashes.txt`).
3. Meshy `meshy-7` 4K retextures on that layout (`requests/`): body with the four HD masters, head-set faces with the
   four close head views. Both returns report the same layout (60.4 %, 227 islands).
4. `resample_approved.py` (installed maps at the same surface points), `bake_ao.py` (2K AO on the layout, reach 0.035).
5. `compose.py` (docstring has the details): 4K gutters and island rims padded before the single 4K -> 2K
   downsample; the head paint's skin mapped onto the body paint's tone (one quantile curve fitted on the front of the
   face where both paints exist; head paint 176/116/92 -> 198/142/120); the head paint replaces the body paint above
   the jaw line only, crossfaded over ~1.6 cm; one broad skin tone measured on the welded mesh (continuous across UV
   seams, so no seam lines) and pulled towards the face colour (face 0.5, neck/jaw/chest 0.95, hands 0.6); per-texel
   chroma fixes for the head paint's grey-green shading (face), the body paint's yellow-brown neck cast, the forehead
   strip under the hair fringe and pale strokes on the ears; gentle grade; region mask at 2048 (R doublet incl. stray
   violet paint, G hair incl. scalp above the hairline, B the new beard); ramps.
6. `face_features.py`: procedural eyes, lid rims, under-eye crescents, mouth interior and lip slit, nostrils; writes
   `work/uv_final.npz` (paid layout with only the 388 eyeball triangles moved to new charts).
7. `apply_layout.py` -> runtime GLB (LOD0/LOD1 UVs with vertex splits, images, ramps; LOD2/3 maps transferred again
   with `lod_repair_claude/scripts/transfer_textures.py` at 512/256).

**The fix of the chin/face mismatch** (first install; the beard parts are superseded by "No beard; undershirt"
below, which removes the beard from every skin):
- **Beard (mask B) rebuilt in 3D at rest:** the native short full beard (moustache under the nose tapering round the
  mouth corners into the chin, jaw to the sideburns, under the chin; lips, cheeks, ears and neck clear) with a fine
  downward strand pattern that thins out at the edge instead of fading as a slab. Bearded skins take their native
  beard colours (window 0.08–0.72 of the native beard pixels, so the bright chin skin does not turn the beard grey).
- **Clean-shaven skins show no trace of it:** their B ramp is least-squares fitted to the skin under the beard shape,
  and the base colour there takes that same fit (twice refitted), so the ramp reproduces the base (error 0.21 mean,
  0.52 p95 levels).
- **One skin tone:** the head paint is mapped to the body paint's tone and the broad tone evened on the mesh, so face,
  neck, chest and hands are one tone.

### Results

| `texture_quality.py`, LOD0 | Installed | Texture pass |
|---|---|---|
| Texture | 2080×1024 (1K body \| 1K head) | 2048² |
| Atlas use | 41.6 % | **60.5 %** |
| Equivalent square | 1,341 px | 1,593 px |
| Density p10 / p50 / p90 | 334 / 496 / 1,584 | 1,226 / 1,283 / 1,693 |
| Median per bone: head, neck, thigh, hands | 1,899, 639, 426, 1,416–1,518 | 2,299, 1,278, 1,279, 1,660 |
| Spread p90/p10 | 4.75 | 1.38 (head ×1.8 by design) |
| Islands / fragments | 575 / 9.1 % | 220 / 0.9 % |
| Stretch p90 | 1.84 | 1.12 |
| Meshy source | 2 × 2K on 1K sets | 2 × 4K, downsampled once |

Runtime maps: colour, normal and region mask 2048², metal/roughness 1024². The mask is 2048 (installed 2080×1024)
so the beard strands stay sharp. LOD2/3 sizes unchanged.

**Face as the engine shows it** (`face_seam.py`, ramps applied, CIE76 dE against the cheeks at the same surface points,
`review/quality/face_seam_{before,after}.txt`). Every skin now has the same face (the beard is outside these zones on
the bearded skins):

| Zone | Installed (shaven / bearded skins) | Texture pass (every skin) |
|---|---|---|
| forehead | 2.3 / 3.9–12.0 | 2.2 |
| nose | 2.3 / 2.4–8.6 | 4.0 |
| mouth corners | 5.3 / 9.2–21.2 | 3.3–3.5 |
| chin (shaven skins) | 4.9 | 2.6 |
| jaw sides | 5.0 / 10.3–19.5 | 4.6–5.2 |
| throat | 0.9 / 1.6–2.9 | 1.9 |
| neck across the head/body crossfade | 1.4–6.1 | **2.0 (shaven) / 2.7 (bearded)** |

The neck below the jaw stays 7.5–7.7 dE darker than the cheeks (lightness, its AO shading), not a hue step.

**Doublet and hair tiers** (`region_tone.py`, `review/quality/region_tone.txt`): hair means within 4 levels of the
installed in every skin (luminance sd +5–10 %). The new paint's cloth came out ~20 % brighter through the native rank
matching, so each doublet ramp is pinned to the installed engine colour (linear gain 0.62–0.66, spread capped at 1.2×):
means within 1–6 levels except **AC red** (101/38/61 -> 114/25/37: a purer red, less magenta), luminance sd ×1.0–1.4.

**Eyes** (`work/eyes.json`): eyeball spheres r 11.5/11.8 mm; forward axes from the head paint's pupils (the installed
paint's darkest eye texels sit in the corners, so it gave no usable pupil), made mirror-symmetric: 5° outward, 3° up,
as the HD head views (straight ahead). Iris 26° half-angle in the head views' blue-grey with radial fibres, collarette,
limbal ring; round pupil 0.36 of the iris; small highlight; lid occlusion from the layout's AO. Eye charts: azimuthal
discs (radius 40.6 px) in the two largest free atlas spaces, ~34 texels/cm on the visible cap, about 2.5× the head's
13.5 (3–4× did not fit: the largest free discs are 41 px). Pupils centred, irises intact in every skin
(`review/texpass_closeups.png`).

**Other checks** (all on `export/mm7_m362_tp.glb`):
- `glb_diff.py` against the installed GLB: OK. Only UVs, vertex splits (LOD0 7,470 -> 9,246, LOD1 4,365 -> 5,572),
  images and ramp values differ. Nodes, skin, inverse binds, every clip sampler (Dead, Death, Fidget, Hit, Standing,
  Walking, Jog), materials, variants, LOD lists, per-corner position/normal/joints/weights are unchanged.
- `check_winding.py`: 0 inverted closed parts. `flat_shading_check.py`: flat 0.00.
- `lod1_check.py`: LOD1 vs LOD0 colour error mean 2.7 -> 2.0, p99 53.5 -> 39.8.
- Viewer `check`: 18 models × 7 clips, 126 switches, no console errors.
- Installed with `flock output/creature_3d_locks/texpass_install.lock tools/install_model.py ... --world mm7`;
  all 12 cooked texture URIs exist; `cmake --build build --target openyamm`;
  `mm6_mm7_mm8_actor_models_build_every_binding` PASS (647 descriptors, 0 failed). No regression case names m362.
- Not done: an in-game look, the Android cook.

**Meshy: 20 credits** (body and head retexture, 10 each, backup account; balance 3,740 after).

### No beard; undershirt (2026-11-01, installed)

User follow-up through the coordinator, overriding the native-sprite beard reading:
- **No beard or moustache on any skin** ("PLEASE remove the human2 gray mustache, he shouldn't have any"). The beard
  channel (mask B) keeps its ramps in every material (no `actors.yml` or variant change) but its coverage is zero
  everywhere. The former beard area (moustache, chin, jaw, sideburns) and the chin's underside take the cheeks'
  chroma, and texels darker than the cheeks are lifted half way (`face_features.py`, `LOWER_CHROMA`). The
  shaven-ramp bake of the first version is gone, so the paint's own clean-shaven skin shows.
- **Undershirt in the chest opening** ("make the undertunic fit these ones"). The chest skin below the collar (rest
  height under `SHIRT_TOP` 1.396; the neck above the collar stays skin) is painted as the off-white undershirt: the
  sleeves' median colour, a sleeve's own weave (luminance detail of a patch cut from a sleeve, mirrored tiles laid by
  rest position at the same density), soft vertical folds and AO, normalised so its median is the sleeves' colour.
  It has a flat normal (the painted lace drawing and its relief are gone), the sleeves' metal/roughness, and no
  region: the shirt, sleeves and collar are not recoloured on any skin, so every skin's undershirt matches its own
  sleeves and collar. The four tie bars (pieces 41–44) are dark leather all round (64/45/34 with a little grain and
  AO, the belt's metal/roughness, no region): no white tips, no brass.

Measured (`face_seam.py`, engine colours, every zone on every skin; `review/quality/face_seam_{before,after}.txt`):
**all nine skins now give identical numbers**: upper lip 4.1, mouth corners 2.4, chin 1.2, jaw sides 1.8, forehead 2.2,
nose 4.0, throat 0.3 dE from the cheeks; neck crossfade 2.1. Installed: upper lip 10.2–20.3, mouth corners 5.3–21.0,
chin 4.9–19.7, jaw sides 5.0–18.3. Undershirt median 189/178/174 against the sleeves' 184/173/169 (collar 174/154/139);
tie bars 52/36/28.

Checks on the reinstalled `export/mm7_m362_tp.glb`: `glb_diff.py` OK against both the pre-pass GLB and the first
install (only UVs, vertex splits, images, ramp values); winding 0; flat shading 0.00; LOD1 error mean 2.1, p99 42.7;
`texture_quality.py` unchanged (60.5 %); installed under the lock, 12 cooked textures present; build;
`mm6_mm7_mm8_actor_models_build_every_binding` PASS; viewer `check` 126 switches, no errors. Meshy: 0 credits.
Rollback copy of the first install: `work/before_nobeard/mm7_m362.glb`.

### Review

- Viewer: [review/viewer/](http://127.0.0.1:8912/level_generation/creatures/mm7_m362_texpass_claude/review/viewer/)
  (revision `texpass-20261101-nb`; ids `m362_<skin>_before`, `m362_<skin>_nb`; focus "Face close-up" is this
  creature's close camera).
- Sheets (identical cameras, installed | texture pass, every skin): `review/texpass_sheet_{a,b,c}.png` (columns face
  front, 3/4 and right close-ups, head front and 3/4, shoulders 3/4, body 3/4 and back), `review/texpass_closeups.png`
  (eyes, nose and mouth, front and 3/4, all nine skins), `review/texpass_chest.png` (chest opening, shoulders front
  and 3/4, all nine skins). Shots in `review/shots/` (`before_<skin>_<view>.png`, `nb_<skin>_<view>.png`; views
  ff/fq/fr face close-ups, hf/hq head, sf/sq shoulders front and 3/4, bq/bk body).

### Drift and known limits

- The faces follow the head views more closely: darker, heavier brown brows on every skin (the installed brows were
  pale). No skin has a beard any more (user decision, against the native sprites' beards on ab, ac, ba, bb, cb).
- A faint darker crescent remains under the left lower lid.
- AC doublet a purer red than installed (see above).
- Eye charts ~2.5× the head density, not 3–4× (free atlas space).

### Rebuild and rollback

```sh
# no paid step: compose, features, apply to the pre-pass GLB, diff against it and the installed GLB, checks;
# --install installs under the lock
level_generation/creatures/mm7_m362_texpass_claude/scripts/build_install.sh [--install]
```

Preparatory steps, already done: `dump_lod0.py`, `dump_pieces.py` (Blender, then `map`), `resample_approved.py
work/uv_fine.npz work/approved_fine 2048 1024`, `bake_ao.py work/uv_fine.npz textures/m362_tp_ao_2k.png` (Blender via
`tools/run_creature_blender.sh`). Review: `scripts/review_round.sh <tag>` (build, viewer variants, manifest, head
shots), `texpass_sheet.py`, `closeup_sheet.py`, `face_seam.py`, `region_tone.py`.

Rollback: `flock output/creature_3d_locks/texpass_install.lock python3 tools/install_model.py
level_generation/creatures/mm7_m362_texpass_claude/work/before_texpass/mm7_m362.glb --world mm7` (before the pass), or
`work/before_nobeard/mm7_m362.glb` (the first install, with beards and the skin chest).
