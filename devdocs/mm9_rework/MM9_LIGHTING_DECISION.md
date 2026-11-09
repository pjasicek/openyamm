# MM9 lighting: findings and the deferred plan (2026-10-31)

**User decision (2026-10-31):** replacing the dungeons' static lighting with MM9's own lightmaps is deferred to the very
end of the MM9 integration. It changes no geometry and no gameplay, so it can be dropped in later. Until then the
dungeons keep our Cycles bakes, re-baked after every map rebuild.

## What we established
- **MM9's formula.** MM9 (LithTech) draws a world polygon as texture × its stored lightmap value, ×1: two-pass, no
  MODULATE2X, no gamma ramp, no brightness term (`MM9_RENDER_LIGHTING_RE.md`). Vertex colour on lightmapped polygons
  is white. Detail textures, the GOG `ddraw.dll` wrapper and the `Brightness` cvar do not change brightness.
- **Proven on this PC.** The user's own Wine screenshot of Boot Camp's first view (`overnight/real_mm9/bootcamp_wine_A.png`)
  measures 61.1 against a predicted 61.4–64.7, hue matching, walls and ceiling within 5–10 %. Doubling the light and
  treating the lightmap as linear light are both ruled out (`MM9_LIGHTING_GLOBAL_MODEL.md`).
- **Our shaders are not the problem.** They multiply the texture by the lightmap value the same way, and our textures
  equal MM9's (339 checked). The whole difference is our Cycles bake: 0.56–1.66× MM9's lightmaps per zone, with hue
  drift both ways (Yanmir's Fort brighter and paler, Dungeon of Secrets redder), plus Cycles noise where many small
  lights overlap.
- **The real screenshots** (`overnight/real_mm9/`, `MEASUREMENTS.md`) fit texture × lightmap where nothing lights the
  camera's surroundings (Yanmir's Fort 1: 1.00). The extra in other shots is local: torches and candles (Klusos
  1.44–1.66), the Torch Light spell in the video (Dungeon of Secrets 4: 3.77, icon on the HUD), a uniform 2× in the
  Dragon Stadium video (most likely a setting there). Unexplained: Dungeon of Secrets 1 (3×, no source found) and its
  purple room (darker than predicted).
- **The party light.** `PlayerLightOn` is a grey (191,191,191) light of radius 36 LT with no visible effect; Torch Light
  enlarges it (12 × power). So real MM9 rooms are as dark as their lightmaps until Torch Light is cast. The overnight
  "no pitch-black rooms" floor (a stand-in for the party light) is therefore not MM9 behaviour; keep it as an explicit
  choice, not a correction.
- **No per-map fudge.** Calibrating each map to screenshots was the wrong approach (user, 2026-10-31); the per-map
  factors added overnight only compensate the Cycles bake and go away with the transfer.

## The plan for later (probable best approach)
1. **Transfer MM9's own lightmaps onto our faces** (`MM9_LIGHTMAP_TRANSFER.md`, tool
   `level_generation/projects/mm9r_common/lightmap_transfer.py`): keep our bake's page layout and face UVs, fill each
   texel from the coplanar MM9 polygon's lightmap at the same world position, stored as MM9 byte / 255. Prototype on
   Yanmir's Fort: 99.7 % of texels transferred; mean of 4 real-shot views real 75 / our bake 100 / transfer 67, hue
   close; smooth, no visible blocks or seams. It is a post-process: rerun it whenever a BLV changes.
2. **Fallback for faces MM9 has no polygon for** (restored floor holes, welded cracks, glass, some movers): our bake,
   matched per surface to the neighbouring transferred texels, never a per-map factor. Open: MM9's movable brushes
   (Yanmir's basement plank tops came out almost black from MM9's data).
3. **Resolution.** MM9 stores 20, 32 or 64 LT per texel depending on the map (32 = 5× coarser than our bake); at 32 it
   reads soft, not blocky. The four 64-LT maps may look too soft: there, re-cook at our resolution with MM9's rule
   (direct light only, its falloff, shadows, ambient, texture lights, DirLights), calibrated per surface against the
   transferred texels. A full re-cook of every map is 3–5 days and only worth it if MM9-resolution light is rejected.
4. **Local runtime light** for the glow near torches, fires and candles (Klusos): MM9's dynamic lights as runtime
   lights. Size their contribution first with a Wine shot with `"DynamicLight" "0"` in `autoexec.cfg` (shot B, not
   taken yet).
5. **Props** keep MM9's model lighting (`devdocs/INDOOR_MODEL_LIGHTING.md`): ambient + full-colour lights + ModelAdd 30.
6. **Outdoor maps** need the same idea on their own path (terrain and BModel lightmaps); the tool is indoor-only.
7. Decide then: pure MM9 darkness or keep the "no pitch-black" floor.

## Until then
- **No re-bakes until then (user, 2026-10-31).** A map whose `.lighting` sidecar goes stale (a rebuild, or a
  `scene.yml` change such as the water work) has the sidecar removed from the review root (a copy stays in the map
  project's `work/lighting_stale_<date>/`) and renders with the classic MM6–MM8 lighting path (static lights in vertex
  colours, sector ambient, dynamic lights), as every MM6–MM8 dungeon does. `tools/lighting/stale_bakes.py --assets
  output/mm9_rework/assets_dev --check` must list no MM9 map. Maps already transferred during the 2026-10-31 rollout
  keep the transfer while it is valid (listed in `MM9_LIGHTMAP_TRANSFER.md`).
- Real-screenshot tooling for later checks: `level_generation/projects/mm9r_common/real_shots.py`, `real_context.py`,
  `real_measure.py`, each map's `make_real_tour.py`.
- Starting MM9 under Wine straight into a dungeon (untested): `wine lithtech.exe +runworld worlds\klusoshouse
  +windowed 1`; a game copy with its own prefix is in `output/mm9_rework/mm9_wine/` (1.1 GB, never launched).

## Files
`MM9_RENDER_LIGHTING_RE.md` (renderer RE, open points updated), `MM9_LIGHTING_GLOBAL_MODEL.md` (the model and its
fit), `MM9_LIGHTMAP_TRANSFER.md` and `lightmap_transfer/` (prototype, sheets), `overnight/real_mm9/` (real shots,
`MEASUREMENTS.md`, comparison sheets).
