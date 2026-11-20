# Spell Reaver sprite restoration

Restored 2026-09-22 under the [MM9 FXF guide](../README.md). **Discarded at user request; original textures are active.**
This package contains all 22 texture frames referenced by the four sprite components of `mm9:spell_reaver`.
All 22 runtime PNGs have been restored byte-for-byte to their retained native originals. The active importer
overlay is empty, so future imports keep the originals. Generated artwork and earlier checks are archived here.
Native descriptor dimensions and timing remain unchanged.
These resources also belong to other effects. Original artwork is retained and explicitly selectable.

Open [the interactive comparison](review.html) for synchronized 15 fps playback, frame stepping, normal/quarter speed,
light/dark backgrounds, alpha/additive blending and equal logical-size comparisons. The preview shows individual
sprite animations, not the engine's complete particle simulation or Reaver's animated tint/scale recipes.

| Family | Frames | Native canvas | Export canvas | Selected master |
| --- | ---: | --- | --- | --- |
| `spells/bluering` | 1 | 64×64 | 128×128 | Continuous native-profile reconstruction |
| `flareparticle` | 10 | 32×32 | 64×64 | Built-in imagegen attempt 02 |
| `weapons/ringexplodeblue` | 1 | 64×64 | 128×128 | Built-in imagegen attempt 02 |
| `smoke/smokenoise` | 10 | 64×64 | 128×128 | Built-in imagegen attempt 02 |

All descriptors retain 15 fps, their original resource IDs, frame ordering and native logical dimensions.
The [export manifest](export_manifest.yml) maps each resource to its restored PNG and original engine PNG.
Exports are under each family's `export/`; `masters/` retains the larger graded RGBA canvases, and `native/` retains
byte-identical comparison copies. AI sheets are 1254×1254; animated cells are 313/314 pixels wide and high, safely
above the required 2× native sampling. Crops use rounded equal-cell boundaries, never visible-content bounds.

## Generation and processing

Used the built-in `image_gen` tool, eight calls total, two per family. All raw returns and exact submitted prompts
are retained beside their references. Selected AI prompt files are
[flareparticle/prompt_02.txt](flareparticle/prompt_02.txt),
[ringexplodeblue/prompt_02.txt](ringexplodeblue/prompt_02.txt), and
[smokenoise/prompt_02.txt](smokenoise/prompt_02.txt).
For expanding-ring attempt 01, the exact submitted prompt is `prompt_submitted.txt`.

Both generated blue-ring attempts were rejected for profile/opacity drift. The guide explicitly prefers deterministic
reconstruction for analytic effects: `bluering/analytic_fit.json` records a nonnegative continuous radial Gaussian
basis fit to native premultiplied RGB and alpha, using a fitted rounded-ring radius and the native alpha center.
Its 1024×1024 master removes coarse steps without painting extra detail or changing the interior opacity.

For the other three families, generation reconstructs the artwork. Export applies one shared color/opacity grade
to each complete family, never a separate normalization per frame. Flare and expanding-ring curves preserve bright
cores while matching sequence-average alpha and premultiplied RGB. Native smoke has white RGB with detail in alpha;
generated neutral shading is folded into its delivered alpha, followed by one shared opacity gain, retaining both
the generated cloud structure and soft transparency. There is no chroma key, hard mask, opaque-pixel clamp or erosion.
Resizing uses premultiplied alpha. Processing is reproducible with:

```sh
python3 level_generation/sprites/mm9_fxf_effects/spell_reaver/export.py
```

Review status is retained only for export hashes recorded in [review.json](review.json). Changed exports return to
`pending_visual_review`. [ledger.yml](ledger.yml) retains the original binding records, selected masters, attempts
and rejection observations.

## Review and validation

- All 22 PNGs are true RGBA at exactly 2× their native canvas; all 22 resource IDs are unique.
- Original PNGs remain in `native/`, and original decoded DTX mips remain under the engine import directory.
  The importer replaces only the 22 selected runtime PNGs and records restoration provenance beside the native mips.
  SPR descriptors and effect recipes are unchanged.
- Full-resolution composites and all phases were inspected; first/last-frame HTML captures are retained as
  [dark](review_dark.png) and [light](review_light.png) proofs. Per-family contact sheets retain native, enlarged
  restored and actual exported-size comparisons on both backgrounds.
- The simple ring keeps its translucent center on light backgrounds; the expanding ring keeps its bright central
  flash; flare cores are smooth rather than enlarged squares; smoke keeps phase-specific flowing openings.
- Family-average premultiplied RGB and alpha are within approximately 1% of native. This is an energy check, not proof
  of pixel identity. Flare frame energy varies approximately −13% to +14% against corresponding native frames;
  smoke varies approximately −6% to +5%. These remaining differences are recorded, not independently normalized away.
- Maximum alpha-centroid difference is under one native pixel per family (simple ring: 0.17 px). Full native canvases,
  emitter registration and descriptor sizes are retained; the centroid measurement includes changed internal shading.
- Raw RGBA texture storage grows from 232 KiB to 928 KiB before mipmaps/compression, a 696 KiB increase. This is a
  calculated asset cost, not measured GPU memory or performance.

[checks.json](checks.json) records per-frame hashes, sizes, energy, opacity and centroid measurements.
The HTML viewer provides playback for review. The experiment also passed the focused desktop check below before being discarded;
exhaustive camera/update-rate and other-effect-consumer certification is not claimed.

## Archived installation procedure

The former overlay is retained as [archived_overlay.yml](archived_overlay.yml), outside the active importer manifest.
The commands below document the previous experiment; with the active manifest now empty they select zero textures.
Re-enabling this discarded experiment would require deliberately restoring its manifest.

Historical implementation:
Normal MM9 FX imports apply it after native DTX conversion, so regeneration preserves reviewed artwork. Artwork,
review and original DTX hashes are checked before installation. Texture provenance records the overlay separately
from the native conversion; original decoded mips remain intact.

```sh
# Install/reinstall these 22 textures without rebuilding or changing the effect library:
python3 tools/mm9_import_discovery/import_mm9_effect_assets.py --restorations-only

# Explicitly switch these textures back to original DTX-derived artwork:
python3 tools/mm9_import_discovery/import_mm9_effect_assets.py --restorations-only --native-textures
```

The original selection is now active in `assets_dev`. Runtime ZIP packages were not rebuilt.
The exporter reads retained `native/` source snapshots, so rerunning it after installation cannot accidentally
restore already-restored textures or overwrite original evidence.

## Desktop verification

Matching isolated normal desktop runs used MM6 New Sorpigal, one `mm9:spell_reaver`, identical camera/settings and
a 0.75-second screenshot/diagnostic delay. [Native](runtime_native.png) and [restored](runtime_restored.png) captures
show the same effect placement, soft smoke, purple rings and green/yellow flare trail. OpenGL 3.3 was active;
the logs do not identify the physical GPU, so these runs are visual checks, not a hardware performance benchmark.

Both snapshots report 51 particles, one fixed sprite, 52 visible quads, 45 draw submissions, 45 texture switches,
22 textures, 30,138 transient bytes and the same world-quad area. Estimated effect texture storage including
mipmaps rises from 316,750 to 1,267,022 bytes. No FX simulation, attachment, duration, tint or blend recipe changed.
[runtime_review.json](runtime_review.json) and `runtime/` retain measurements, logs, settings and run records.

`python3 tools/mm9_import_discovery/test_effect_asset_pipeline.py` passes. Coverage checks native conversion,
all packaged SPR dimensions/order, reimport preservation, explicit native rollback and rejection of artwork that
does not match its reviewed hash.
