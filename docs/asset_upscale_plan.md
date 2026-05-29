# Asset Upscale Plan

## Goal

Support three mutually exclusive asset tiers:

- `x1` as the default
- `x2` as an optional upscale tier
- `x4` as an optional upscale tier

At all tiers, the game must preserve:

- identical gameplay behavior
- identical UI logical layout semantics in `640x480` style units
- identical save/load behavior

The hard preservation rule for this plan is UI logical space.
World rendering scale and texture-coordinate handling may be recalculated in later slices as long as tiers are not mixed.

## Scope

Target tiered asset folders such as:

- `Data/bitmaps`
- `Data/bitmaps_x2`
- `Data/bitmaps_x4`
- `Data/sprites`
- `Data/sprites_x2`
- `Data/sprites_x4`
- `Data/icons`
- `Data/icons_x2`
- `Data/icons_x4`

Only one tier is active for a run. No mixing between tiers.

Current asset organization assumptions:

- visual assets previously taken from `Data/EnglishD` now live under `Data/icons`
- `Data/EnglishD` is treated as sound-only for this feature
- HUD and menu fonts remain out of upscale scope for now and may continue loading from `Data/EnglishT`

## Core Rule

The engine must distinguish between canonical virtual paths and selected physical asset roots.

Canonical game requests should remain:

- `Data/bitmaps/foo.bmp`
- `Data/sprites/bar.bmp`
- `Data/icons/baz.bmp`

The asset system should resolve those requests to the selected tier:

- `Data/bitmaps` -> `Data/bitmaps_x2` or `Data/bitmaps_x4`
- `Data/sprites` -> `Data/sprites_x2` or `Data/sprites_x4`
- `Data/icons` -> `Data/icons_x2` or `Data/icons_x4`

## Architectural Direction

Use canonical virtual asset paths everywhere in game code.

This keeps tier awareness centralized in the asset layer instead of scattering suffix logic across gameplay and rendering code.

The first implementation slice should stop there:

- select `x1`, `x2`, or `x4`
- remap canonical asset roots to the chosen physical folders
- fail fast if a selected tier is incomplete

UI logical-size preservation remains the next major slice after that.

## Phase 1: Asset Tier Configuration

### Goal

Add global selection of `x1`, `x2`, or `x4`, with `x1` as default.

### Work

- Extend application configuration to carry the selected asset tier.
- Extend the asset filesystem to resolve canonical virtual paths to the selected physical folder set.
- Ensure `x1` continues to mount and resolve exactly as it does now.
- Ensure `x2` and `x4` can transparently remap:
  - `Data/bitmaps` to `Data/bitmaps_x2` or `Data/bitmaps_x4`
  - `Data/sprites` to `Data/sprites_x2` or `Data/sprites_x4`
  - `Data/icons` to `Data/icons_x2` or `Data/icons_x4`

### Acceptance

- `x1` is behaviorally identical to current code.
- `x2` and `x4` are selectable globally.
- No rendering or gameplay code directly refers to `_x2` or `_x4`.

## Phase 2: Texture Metadata Split

### Goal

Introduce a shared notion of logical size versus physical size.

### Work

Add texture metadata that carries:

- `physicalWidth`
- `physicalHeight`
- `logicalWidth`
- `logicalHeight`
- `scaleTier`

Apply this first in loaders and cached texture handles.

### Acceptance

- `x1` uses identical logical and physical dimensions.
- `x2` and `x4` preserve current logical dimensions while exposing larger physical textures to the renderer.

## Phase 3: Icons, Inventory, UI, and Menus

### Goal

Prevent larger UI textures from changing gameplay-facing layout or inventory semantics.

### Work

- Stop deriving inventory slot size from raw icon bitmap size.
- Make item footprint remain based on logical dimensions only.
- Make HUD and equipment rendering use logical dimensions for placement and layout.
- Make menu and source-rect based rendering interpret rectangles in logical coordinates and scale sampling to the active tier.
- Audit icons, fonts, and menu atlases for tier-safe sampling.

### Acceptance

- Inventory slot usage is unchanged across `x1`, `x2`, and `x4`.
- Equipment placement is unchanged.
- HUD and menu layout is unchanged.
- Only sharpness improves.

## Phase 4: Sprites and Billboards

### Goal

Keep monsters, decorations, projectiles, and world items at their current world size.

### Work

- Replace any world-space sizing derived from texture pixel size with logical size.
- Keep sprite frame selection, animation timing, mirroring, and palette logic unchanged.
- Apply the same rule to indoor and outdoor billboard rendering.

### Acceptance

- Billboarded content has the same apparent size across all tiers.
- Only visual fidelity changes.

## Phase 5: BModels, Indoor Faces, and Sky

### Goal

Keep textured geometry visually identical while allowing higher-resolution source textures.

### Work

- Normalize UVs against logical texture size rather than physical texture size.
- Ensure higher-resolution replacements do not alter texture tiling or scaling on geometry.
- Make sky rendering tier-safe without changing coverage or framing.

### Acceptance

- Outdoor BModels render the same at all tiers.
- Indoor textured faces render the same at all tiers.
- Sky appearance and coverage remain unchanged.

## Phase 6: Terrain

### Goal

Support sharper terrain textures without changing terrain layout or world scale.

### Work

- Refactor terrain atlas generation to separate logical tile size from physical tile size.
- Keep logical terrain tile size fixed to current `x1` meaning.
- Let physical terrain tile size scale by tier.
- Recompute atlas UVs using physical atlas dimensions.
- Update animated water and shoreline atlas update logic to be scale-aware.

### Acceptance

- Terrain placement and coverage are unchanged.
- Terrain texture sharpness improves with tier.
- Water animation remains correct.
- `x2` is the baseline supported upscale terrain tier.
- `x4` must be validated against texture-size and VRAM limits.

## Phase 7: Validation and Failure Handling

### Goal

Make tier pack problems explicit and easy to diagnose.

### Work

- Add validation for selected tier completeness at startup.
- Check for missing required files.
- Check for invalid dimensions where strict integer scaling is required.
- Check for non-integer or inconsistent scaling in tiered assets.
- Log active asset tier and resolved tiered roots clearly.

### Acceptance

- Broken `x2` or `x4` packs fail fast with actionable diagnostics.
- The game does not silently mix incompatible dimensions.

## Phase 8: Testing and Verification

### Goal

Prove that upscale tiers preserve behavior and scale.

### Test Matrix

Verify across `x1`, `x2`, and `x4`:

- same save/load behavior
- same inventory slot usage
- same equipment placement
- same HUD and menu alignment
- same terrain tiling
- same world-space size of monsters, decorations, projectiles, and items
- same camera framing and sky presentation
- same event and gameplay behavior

### Verification Approach

- use fixed-camera screenshot comparisons
- use identical save states for before/after checks
- verify selected representative outdoor and indoor scenes
- verify representative UI-heavy flows such as inventory, equipment, chest, shops, and menus

## Rollout Order

1. Land asset tier configuration and canonical path remapping.
2. Land logical versus physical texture metadata.
3. Land icon, inventory, HUD, and menu fixes.
4. Land sprite and billboard logical sizing fixes.
5. Land BModel, indoor face, and sky UV fixes.
6. Land terrain atlas refactor.
7. Enable and validate `x2`.
8. Enable and validate `x4` after atlas and memory checks pass.

## Risk Notes

- `x4` terrain atlases may become very large and must be checked against hardware limits.
- VRAM usage and load time will rise significantly at `x4`.
- Source-rect based atlases and fonts are easy to overlook.
- Tiered assets must be exact integer upscales with matching content extents.
- The engine should treat `x2` as the primary first supported upscale tier and `x4` as the second.

## Success Criteria

The work is complete when:

- `x1` remains 1:1 with current behavior and presentation
- `x2` works end-to-end with canonical path remapping
- `x4` works under the same remapping model where hardware allows
- UI continues to operate in logical `640x480`-style units
- gameplay and save/load behavior are unchanged
