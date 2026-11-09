# MM9 ground items in 3D (2026-11-05)

[PLAN.md](PLAN.md) is the plan the user approved (Meshy for body armour, a 635-credit ceiling, MM9's own binding
file). This README records what is built and how.

## Status

**All 245 designs built, textured and installed (2026-11-05)**: 391 MM9 items bound in
`assets_dev/worlds/mm9/world_items/items.yml`, 245 models in `assets_source/worlds/mm9/world_items/models/`
(`ledger.json`), all with 0 inverted closed parts. In game (New Sorpigal, 48 items of every family dropped): no
placeholder, no load error (`review/ingame/`); an MM8 boot is unaffected. The eight pilots (d10115, d10369, d10124,
d10229, d10009, d10084, d10145, d10153) were reviewed first; the rest followed in waves through `pipeline.py`.

Meshy: 107 Smart Topology jobs (whole armour, misc and hybrid parts), 535 of the 635-credit ceiling, no failures
(receipts in `meshy/creature_3d_progress.json`; the workspace claim is released).

Known compromises: ring settings are a generic round mount and stone (not each icon's setting); an amulet with an
open centre (d10161) is a solid disc; the jar's glass is opaque; d10067 and d10188 carry `icon_paint.py` textures.

Review: `review/final/<d>_{above,three_quarter,low}.png` per design; `scripts/sheet.py <out> final <d>...` builds
a contact sheet with the icon and painting.

Viewer: `review/viewer/` (three.js, the installed source GLBs beside their icon and painting; lighting presets,
texture channels, wireframe, review flags kept in the browser). `scripts/viewer_manifest.py` rewrites its
`manifest.json`; serve the repository with `python3 -m http.server 8912 --bind 127.0.0.1` from its root and open
`http://127.0.0.1:8912/level_generation/props/items_mm9_claude/review/viewer/`.

### Lessons of the full pass

- **OpenAI's image filter** refused about 30 weapon paintings as "violence" (input or output stage, also a plow,
  a scroll and an amulet). `mm9item.py neutral-brief <d>` writes the brief with a neutral title and every weapon
  word replaced; with retries all but two passed. Those two (d10067 Crude Mace, d10188 Blackpowder) are painted by
  `icon_paint.py` from the HD icon painting (top view = the icon, side views sampled per row, mask by a per-design
  rule); only for icon-silhouette builds.
- **Codex rate limits** (429, reconnects) slowed one wave to 2-3 paintings per 10 minutes for about two hours;
  sessions that ran out of reconnects are simply rerun (`pipeline.py` paints whatever has no raw).
- **Rings were solid discs**: `ring_band` revolved an open profile and capped it; it is a closed loop now.
- **Shields had a dark groove** down the face: `curved_plate` cut only across X, so the face was full-height strips
  baked as slivers; it cuts across Y as well now.
- **Hybrid crumbs**: `meshy_part` drops islands under 1 % of the faces; Mjulnir's cage head is all small islands
  (`crumbs: 0` in `design_overrides.yml`).
- **Dark metal**: paintings copy the icons' shaded steel (base colour 0.2-0.3), which renders black as a metal. The
  bake lifts the metal texels' median luminance to 0.5 (at most x2), keeping hue and detail.
- **Texel density** (2026-11-06): Smart UV left Meshy armour and cage builds at 11-30 % of the atlas (hundreds of
  loose islands, each with its margin), so armour had about 1 texel per world unit against a median 3.3.
  `codex_texture.py repack <d>` re-packs the prepared mesh (same geometry and guides, so the paintings stay valid):
  the same islands at one density with a 2-texel concave pack, or `claude_shared/uv_atlas.py` charts when those cover
  5 points more. The 30 designs under 1.5 texels per unit went to 39-56 % coverage (median 1.66, lowest 1.17, Scaled
  Leather) and were baked again; their pre-repack blends and exports are in `work/codex_tex/pre_repack/`.
- **Bake tolerance**: a view whose painting does not register is left out when the other views cover the model (at
  most two); masks may miss the guide by 10 % and carry up to 3 % antialias outliers; edge-on sliver views are
  skipped unless every view is thin.

## Engine and tools (done for this pass)

- `GameDataLoader` reads `worlds/<mounted world>/world_items/items.yml` after the engine's bindings; an icon bound
  twice fails (unit test in `tests/EffectDefinitionLoaderTests.cpp`, `*Item model*`).
- `tools/install_model.py --world-items --world mm9` installs into `worlds/mm9/world_items/models/`.
- `tools/cook/model_textures.yml`: class `worlds/*/world_items/models/*.glb` with the ground-item caps (colour 512,
  normal and roughness 256), before the creature class.

## Pipeline (scripts/)

The MAW route (paint + material-mask atlas, registration, mask-driven PBR) for every design; Hesper's component kit
for the Blender geometry.

1. `classify.py` (routes.tsv, classification.json from the icon project), `designs.py` (designs.json, with family
   defaults and `design_overrides.yml`).
2. `mm9item.py reference <d>`: the icon project's HD painting keyed; it is the Meshy master for armour and misc.
   `mm9item.py master <d>`: a Codex three-quarter master (helms, boots, gauntlets, hybrid heads).
3. Meshy: `meshy_submit.sh <token> <d>...`, `meshy_fetch.sh <token> <d>...` (Smart Topology, untextured, 5 credits).
4. `build_mm9.py <d>`: Blender geometry for blender, plate and hybrid designs (work/procedural/<d>.glb).
5. `pipeline.py [--no-paint] [--rebake] [<d>...]` runs everything whose inputs are ready: `codex_texture.py prep`
   (re-prepped when the model is newer than its guides; old paintings move to `superseded/`), `mm9item.py
   paint-brief`, `mm9item.py codex` (16 at once), then `register_views.py`, `codex_texture.py bake` and
   `review_render.py`; `pipeline_status.json` records each design's step. `mm9item.py neutral-brief <d>` and
   `icon_paint.py <d>` are the image-filter fallbacks.
6. `install_mm9.py <d>...`: winding check, install, bindings (one line per MM9 item), bounds.

Changes from MAW: metal roughness 0.45 (dark steel at 0.35 mirrored a dark world into black) and the metal albedo
floor; the interior takes the dominant painted material when the declared one is not painted; `skip_views` per
design; sliver views and view rejection as above.
