# MM6–MM8 terrain decorations

Implemented and installed in `assets_dev/worlds/mm*/terrain_decorations/` on 2026-09-13.
All 42 inventoried outdoor maps have explicit decisions: **24 enabled, 18 disabled**.
New Sorpigal retains its accepted version-1 grass rules, artwork, seed and grass placements; its dirt stones are removed.

Run the ordinary `./build/game/openyamm`. Enable in the console:

```text
config set terrain_decorations true
```

Or set `[video] terrain_decorations=true` in top-level `settings.ini`.
The toggle applies immediately; reload the map or restart after editing YAML or artwork.
Terrain decorations are separate from `[video_quality] terrain=x2`; either terrain resolution works.

## Content and controls

- [Map choices, density multipliers and rationale](map_design.yml), [map table](MAPS.md).
- [Reusable family dimensions and weights](families.yml).
- [Runtime family schema/example](runtime/worlds/mm8/terrain_decorations/families_v2.yml).
- [Installed MM6](../../../assets_dev/worlds/mm6/terrain_decorations),
  [MM7](../../../assets_dev/worlds/mm7/terrain_decorations),
  [MM8](../../../assets_dev/worlds/mm8/terrain_decorations).
- [Original design inspection](DESIGN_REVIEW.md), [installed terrain inventory](tiles.json).
- [Validation and resumable state](WORK_STATE.json), [actual map scatter audit](runtime_audit.yml).

Only **grass, tropical and swamp terrain** receives added cover. Sand, cracked/waste ground, dirt,
snow, volcanic/mineral surfaces and liquid/road overlays remain bare. This is a material rule: Dragonsand
still has cover on its isolated grass patches. Ironsand, Sweet Water and Paradise Valley are fully disabled.

Swamp reeds retain their original density, width and dry-footprint masks but use height 100 instead of 40
(**2.5× taller**). All 28 swamp base/transition masks were reviewed: accepted foreground coverage excludes
the dirt side, while an additional dry mask excludes blue channels painted into the swamp. Full-footprint
clearance keeps roots away from those edges. MM6 and MM7 transition captures are recorded in WORK_STATE.

Unused reed/dead/mineral family definitions and source artwork remain available for future authoring;
unselected families place no instances. The atlas layout stays stable. Four specialized maps were already
disabled; another fourteen now have no selected grass/tropical/swamp cover.

Version-2 maps reference one world-local `families_v2.yml`. Each rule selects a family and can override
candidates, width, height, tint, mask, wind strength and full-footprint clearance. Unlisted textures stay bare.
Family variant layers select the existing instance texture-array field; the shader and 64-byte instance
layout are unchanged. The 1024×576 atlas contains twelve 256×192 cells (ten used, two transparent).
Different worlds share silhouettes but use material-specific tints. Typical plant range is 4096 world units;
New Sorpigal keeps 6144. Stones retain their shorter renderer range.

## Artwork provenance

Imagegen produced the three paired families using accepted terrain/grass references. At the user's direction,
all accepted source sheets use **magenta, followed by offline alpha repair**. No checkerboard is baked in.
[Exact prompts](art/magenta_prompts.json), [raw sheets](art/raw), [processing](process_art.py),
[processing settings/hashes](art/processing.json), [light/dark edge review](art/edge_review.png) are retained.
The earlier transparent outputs are provenance only; runtime cells come from the magenta versions.

Repair estimates edge coverage against magenta, unmattes color, removes isolated background fragments,
resizes with premultiplied alpha and repairs residual magenta fringes. Each pair uses a common scale and a
shared ground row. All six cells passed the alpha-bound and magenta-spill checks and were visually inspected.

## Rebuild and install

```sh
python3 level_generation/terrain/decoration_rollout/build_catalogue.py
python3 level_generation/terrain/decoration_rollout/process_art.py
python3 level_generation/terrain/decoration_rollout/export_runtime.py
# Explicit installation after reviewing staged output:
python3 level_generation/terrain/decoration_rollout/export_runtime.py --install
cmake --build build --target openyamm -j25
```

`build_catalogue.py` checks all 489 accepted terrain PNGs and effective map inventories. `export_runtime.py`
records exact transition sources, exports staged runtime files and checks installation ownership/hashes.
It preserves only the files referenced by accepted New Sorpigal content, not arbitrary similarly named masks.
Installation does not change settings, original terrain, bmodel textures or creature sprites.
Update WORK_STATE after reviewing regenerated content; exporting alone does not confer visual acceptance.

## Verification

The focused Terrain-decoration suite passes 15 cases / 135,949 assertions, including version-2 family loading,
invalid references/layers, disabled maps, per-rule variants, deterministic placements and strict water-channel
footprints. The actual scene/loader/scatter audit covers all 42 maps and verifies referenced terrain names.
New Sorpigal's retained grass configuration exactly equals its original baseline after filtering out stones
(70,266 grass instances). The largest current map has 129,329 instances; this is map-wide storage, not the
visible count or a per-frame allocation. The height validator now accepts up to 128 authored units to support
100-unit reeds; culling bounds already include the actual scaled instance height.

Native captures and their poses/logs live in [review](review), with the all-map jobs in [capture_jobs.json](capture_jobs.json).
They are sampled visual checks, not exhaustive exploration of every courtyard. Several ordinary actors and
native trees obscure parts of frames; the retained screenshots make that limitation explicit. Xvfb timings
are software-renderer measurements. Real-GPU and Android evidence is recorded separately in WORK_STATE.

Before the material restriction/taller-reed revision, the RTX 3060 Ti Murmurwoods comparison reported median loop FPS 2244.95 on / 2286.04 off
(about 1.8% difference in this short view, not a GPU timer benchmark). The release x86_64 Android emulator
rendered Bootleg Bay with all 82,382 map instances prepared; its screenshot confirms the same tropical atlas
and exclusions. The original emulator settings were restored. Physical-device performance remains unmeasured.

Live console off/on and ordinary walking were checked; [tropical motion frames](review/deco_tropical_wind_wind_frames.json)
show restrained wind with grounded stems and clean edges. The existing distance-fade shader was unchanged.

Current policy supersedes the original broad-material design review and initial all-map screenshots.
No current rule scatters stones, sand tufts or dead stalks. Older Android/performance checks are historical;
the current desktop build and native map/mask validation are recorded in WORK_STATE.
