# Optional terrain decorations

MM6–MM8 rollout: [map/family configuration, new plant art and validation](../decoration_rollout/README.md).

For the proposed expansion to all MM6/MM7/MM8 terrain maps, see the
[42-map decoration catalogue](../decoration_rollout/README.md). It includes per-map density/family choices
and special-environment exclusions; it has not been installed into gameplay.

New Sorpigal now supports nearby instanced painted grass and small solid dirt stones. Enable in the settings.ini
used by the executable, then restart the game:

```ini
[video]
terrain_decorations=true
```

Default is false. The key is preserved when settings are saved; there is no menu control. Other maps require their
own world-local configuration. Maps started disabled/unconfigured load no decoration textures, meshes or instance buffers.

For an immediate performance comparison, open the in-game console with the backtick key (below Esc):

```text
config toggle terrain_decorations
config set terrain_decorations false
config set terrain_decorations true
config get terrain_decorations
```

This toggles both grass and dirt stones without reloading the map. The console reports `true`/`false` and saves
the preference to `settings.ini`, following the existing `config` commands. Close the console before comparing FPS
from the same viewpoint. Enabling after starting disabled performs a one-time load/scatter; let that finish before
measuring. Subsequent toggles reuse identical placements and GPU resources. Disabled skips decoration culling and
draw submission, but retains the allocated memory until map unload, so this compares frame cost, not memory use.
Only maps with decoration content show a visual change.

## Play the prepared trial

```sh
./level_generation/terrain/mm6_ground_cover/play.sh
```

Choose Load Game and **Terrain camera reference**. Walk onto the grass outside town to see the tufts. The isolated
stage is `/tmp/openyamm-sorpigal-ground-cover`, built from the accepted enhanced terrain/creature content, including
new dirt, directional land transitions and the newer water/shore pack. Its settings enable the feature. Restart an already running trial to load refreshed shaders/assets.
The peasants launcher retains its existing executable/settings; setting the key on an older executable is insufficient.

Rebuild and refresh this trial when changing the feature:

```sh
cmake --build build --target openyamm -j25
python3 level_generation/terrain/mm6_ground_cover/build_assets.py
python3 level_generation/terrain/mm6_ground_cover/prepare_trial.py
```

The trial snapshots the current enhanced assets on first preparation. Later preparation refreshes the decoration
assets and atomically replaces the binary, preserving trial preferences and existing saves.

## Content and renderer

Runtime content is [assets_dev/worlds/mm6/terrain_decorations](../../../assets_dev/worlds/mm6/terrain_decorations).
`oute3.yml` selects exact terrain texture names, grass/stone kind, deterministic seed, density, size, tint and masks.
White mask pixels allow placement; `invert_mask` selects the opposite material. Each rule's `candidates` is the
average number of random candidates per 512-unit terrain cell before exclusions and density controls. Grass/dirt masks come from the accepted
`connected_v4` pack, reduced to 64×64, preserving native NE/SW/etc. orientation. Unlisted surfaces receive no props.

### Height, density and transition coverage (v4)

The grayscale PNG masks were previously read from blue, but bimg decodes grayscale intensity into red only.
That suppressed all transition grass and made the inverted stone masks allow the entire tile. The loader now reads
red for both material masks and density masks. A regression test loads all twelve authored grass/dirt directions.
Short grass uses a four-unit root clearance and probabilistic thinning through the grassy blend; stones and taller
clumps retain full-width material clearance. Roots do not enter the dirt half of a blend.

New Sorpigal uses `candidates: 50` for grass, redistributed across pure grass and the newly enabled transitions.
The measured full-map total is **81,072 instances / 5,188,608 bytes**, versus 79,781 / 5,105,984 before this revision
(+1.6%). There are 3,416 occupied cell/kind patches. Instances are grouped by mesh kind at scatter time so mixed
tiles can still merge contiguous grass draws without intervening stone ranges. The same four tuft images are reused.

These controls live in `oute3.yml`; edit `build_assets.py` as well when changing the generated defaults:

| Control | Current value | Meaning |
| --- | --- | --- |
| `density_variation` | `0.8` | Smooth variation around the average, up to 0.2–1.8× before exclusions. |
| `patch_size` | `768` | World-space noise spacing, shared across cell boundaries. |
| `tall_grass_chance` | `0.08` | Taller-clump probability, modulated toward denser patches. |
| `tall_grass_scale` | `1.8` | Tall height relative to base height, retaining normal random size variation. |
| Rule `density` | `1` when omitted | Per-texture/kind multiplier from 0 to 2; zero disables placement. |
| Optional `density_mask` | Omitted | Path relative to the decoration directory to a 128×128 grayscale PNG. |

For a density mask, pixel `(x,y)` controls terrain cell `(x,y)`, north at the top. Black means zero density,
128 means roughly half, and white means the full configured density. Values interpolate between cell centres;
combine this with rule density to author sparse town lawns and fuller wilderness without hard cell boundaries.
It affects both grass and stones. The shipped map uses procedural variation, with no additional authored density mask.
Tall clumps use the same smooth patch field, retain full material clearance, and use 144-unit building clearance.
Existing nearby-entity exclusions remain in force. Ordinary short grass keeps the existing building checks.

All density, mask and height decisions happen once at load/first enable. No new frame-time calculation, shader,
texture, instance attribute or gameplay entity is added. Taller silhouettes can increase GPU pixel work; equal
instance counts alone do not guarantee equal FPS. Reload the map or restart after changing these content controls;
the console toggle reuses the existing scatter.

Visual checks and validation are recorded in [v4 review](review/v4/REPORT.md).

The source shapes are [broad](generated/grass_tuft.png), [fine](generated/grass_fine.png),
[wispy](generated/grass_wispy.png), and [dry](generated/grass_dry.png). Each was made with the built-in imagegen tool;
[prompts](generated/PROMPT.md), [fine prompt](generated/grass_fine_prompt.md),
[wispy prompt](generated/grass_wispy_prompt.md), [accepted dry prompt](generated/grass_dry_final_prompt.md) are retained.
The earlier dry checkerboard output was rejected and is not exported.

The runtime `grass_variants.png` is a 512×384 atlas of four 256×192 cells (broad/fine on top, wispy/dry below).
`tuft_atlas_grid` specifies the grid; `tuft_variants` selects positive weights and width/height scales in row-major order.
Current weights are **45/35/15/5**; the wispy type is taller and dry tufts are sparse. Width scales cannot exceed 1,
so the existing material/building footprint remains conservative. Variant choice uses a separate deterministic
random stream, preserving original placement, rotation and stone geometry. The layer index uses an existing spare
instance float, adding no instance bytes or draw batches.

All selected masters have real alpha. Export follows the existing
[direct sprite workflow](../../creatures/DIRECT_SPRITE_WORKFLOW.md): preserve delivered alpha, resize premultiplied
RGB/alpha, audit partially transparent and opaque contour pixels before and after export, and inspect on light/dark
backgrounds. No significant magenta spill was found; no colour-key or despill correction was necessary. Magenta plus
soft matting/edge-colour unmixing remains the documented route for outputs lacking alpha, not a required extra pass
on these transparent images. [Edge audit](review/v3/edge_audit.json), [light/dark review](review/v3/edge_audit.png).

GPU upload extracts each atlas cell into an independent texture-array layer before colour bleeding and mip generation;
neighbouring variants cannot contaminate lower mips. One texture binding serves every grass shape. Grass texture
storage is approximately 1 MiB including mips (up from 256 KiB); variant selection adds no per-instance storage. Stones remain
an original small opaque mesh. These are world-sized props independent of the base terrain's x1/x2 setting.

`TerrainDecorationData` loads the map config and scatters once on first enable (at map load if already enabled).
It uses the rendered terrain triangles,
checks masks across cell boundaries, excludes steep slopes and conservative building/entity bounds, and stores
surface normals so roots follow slopes. There are no gameplay entities, save records, collision bodies or per-frame
scatter/raycast/upload operations.

`TerrainDecorationRenderer` holds persistent instance data and one mesh per kind. CPU distance/frustum checks select
cell batches; the vertex shader bends grass tips while keeping full mesh dimensions. Grass coverage fades over a
broad, per-clump staggered band: approximately 2,458–6,144 world units. Object-space cutout noise is fixed across
frames; it does not depend on the screen or wind. Grass mips preserve alpha-test coverage to keep fine blades from
disappearing prematurely. Stones retain a shorter 2,048-unit maximum range. Roots remain anchored. Stones receive no wind. Rendering uses cutout depth writes, mipmaps, transparent-edge colour
bleeding, and the same outdoor fog/ambient/local light shader as terrain. No grass shadows or interaction simulation.
Instancing support is required; an unsupported backend logs a clear message and leaves base terrain usable.

Visible cells with contiguous instance ranges, the same mesh kind and identical light uniforms now share a draw.
At the profiled New Sorpigal camera this reduced decoration draws from 148 to 14 with all 8,714 visible instances
preserved. Placement, density and draw distance are unchanged. See the
[desktop GPU profiling report](review/performance/REPORT.md) for measurements and before/after visual checks.
Visible ranges and light uniforms are cached at 20 Hz while stationary. Movement, turning, projection changes and
added/removed lights refresh immediately; wind, fog and draws continue every frame. Existing moving/flickering
light uniforms can lag by at most 50 ms while stationary. Frustum constants are computed only when the view changes.

Additional worlds/maps can supply `worlds/<world>/terrain_decorations/<map-stem>.yml` and local assets with this schema.
Current mesh kinds are grass and stone; new shapes need another mesh kind, not a new gameplay system. Ship the
world's decoration folder and the two compiled `terrain_decoration` shaders with an updated executable.

## Validation

- Batching/cache optimization: ten focused cases (38,508 assertions) passed; adjacent-range, mesh and light-uniform
  boundaries and camera/projection/shutdown invalidation are covered. Desktop GPU profiling and native before/after
  visuals are recorded in the report above.
- Console toggle: desktop game/test targets rebuilt and the eight focused cases still pass. A native capture started
  disabled, queried the setting, toggled on, set off, then set on. Reviewed the
  [console results](review/console/grass_console_reenabled_console.png),
  [disabled view](review/console/grass_console_disabled.png) and
  [re-enabled view](review/console/grass_console_reenabled.png). Logs show exactly one decoration initialization
  across these changes; final enabled preference was verified in the isolated settings file.
- Desktop game and unit-test targets built. Eight focused cases (38,489 assertions) passed: deterministic triangle-height
  placement, directional masks, footprint/building/slope exclusions, frustum/distance culling, strict config loading,
  missing assets, settings on/off round-trip, cutout mip alpha coverage, weighted variant choice and unchanged placements/batch counts.
- Revision after `test_img/1282.png`: grass changed from 32×19 to 40×30 world units, candidates from 48 to 64,
  and tint from `[0.68, 0.88, 0.65]` to `[0.82, 0.98, 0.78]`. Grass range is 6,144 rather than 2,048 units.
  The old size-to-zero fade caused visible growth while approaching; it has been replaced by distant coverage fading.
- Four-shape revision: [current mix](review/v3/grass_v3_mix_start.png),
  [walking](review/v3/grass_v3_mix_walk_1.png), and [town paths](review/v3/grass_v3_town.png). The v2 distance behaviour
  remains active; all 79,781 placements and 2,740 batches remain unchanged.
- [Previous single-shape grass at the comparison camera](review/v2/grass_v2_same_view.png),
  [running start](review/v2/grass_v2_run_start.png), and [running through grass](review/v2/grass_v2_run_run_01.png)
  were checked in the native renderer. The eight-step run is retained in `review/v2/` with its actions and metadata.
  Earlier, overly faint grass and its disabled baseline remain in `review/` for comparison.
- Current map allocation: 79,781 instances, 2,740 spatial batches, 5,105,984 instance bytes (~4.87 MiB), plus a small
  texture/meshes and CPU batch bounds. These are full-map allocation counts, not per-frame visible counts. The longer
  grass range submits more distant instances; stones keep the shorter range to avoid unnecessary extra work.
- Xvfb software-rendered captures validate appearance and operation, not hardware GPU performance or sustained
  Android cost. Daylight town/hill views and an eight-step run were reviewed; extended motion, night/weather and device
  profiling remain useful follow-up checks before changing the default.

Use the reusable, prefix-approved wrapper for visual checks:

```sh
./tools/capture_gameplay.sh ground_cover_check --world mm6 --map oute3.odm \
  --stage /tmp/openyamm-sorpigal-ground-cover \
  --review-directory level_generation/terrain/mm6_ground_cover/review \
  --start-save level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/references/Dirt_View.oysav \
  --pose -10000 -12200 161 0 -0.35 --binary /tmp/openyamm-sorpigal-ground-cover/openyamm \
  --warmup 1 --seconds 2
```
