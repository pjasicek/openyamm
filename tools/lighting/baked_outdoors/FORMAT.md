# Outdoor lighting versions 3, 4 and 5

All integers and IEEE float32 values are little endian. Magic remains `OYMLIT1\0`; versions 3, 4 and 5 are
accepted. Version 4 adds explicit model sunlight data; version 5 adds direct-only surface illumination.
File lengths/section offsets/counts, geometry
hash, face identities, finite values, page references, page dimensions, paired dimensions and dependency
paths are validated before use. Trailing data is rejected.

## Header (96 bytes)

| Offset | Type | Meaning |
| --- | --- | --- |
| 0 | 8 bytes | Magic |
| 8 | u32 | Version: 3, 4 or 5 |
| 12 | u32 | Header bytes: 96 |
| 16 | u64 | FNV-1a of native ODM bytes |
| 24, 28 | u32 each | Source BModel and face counts |
| 32, 36, 40, 44 | u32 each | Page, face, vertex, authored-light counts |
| 48, 52, 56, 60, 64 | u32 each | Page/face/vertex/light records and pixel data offsets |
| 68 | u32 | Entire file length, including extension |
| 72 | u32 | Legacy ambient; producer writes zero |
| 76 | u32 | Flags: bit 0 selects paired baked sun/sky pages |
| 80, 84 | f32 each | Terrain first sample world X/Y |
| 88, 92 | f32 each | Terrain sample-to-sample world X/Y extent |

For paired baked pages, the terrain sun page is page zero and the sky page is page one. Current terrain
coverage is `(-32768,32768)` plus extent `(65024,-65024)`. Runtime adds the half-texel
edge adjustment so the first and last native terrain vertices address the first/last texel centers.

## Shared records

- Page: width, height, absolute pixel offset, compressed byte count (four u32 values, 16 bytes).
  Pages are adjacent sun/sky pairs, matching dimensions; face indices reference even sun pages.
- Face: source key `(u64(model)<<32)|face`, model u32, face u32, page u16, flags u16,
  first lighting vertex u32 (24 bytes). Flag bit 0 means a lightmap is present; `0xffff` means absent.
  Invisible/degenerate faces still have records to retain exact native identity.
- Vertex: lightmap U/V float32 and legacy ABGR color u32 (12 bytes), in native face vertex order.
  New producer writes white vertex color. No base material UV changes.
- Authored lights retain the 80-byte version-1 layout; new producer emits zero (runtime local lights stay live).

Each pixel is stored B,G,R,M. Decode linear illumination as `RGB * M * 4`, with normalized byte components.
M is the upward-rounded maximum channel divided by four (minimum 1/255). Values above four or nonfinite
samples reject the bake. Files contain no display tone mapping, receiving albedo or mipmaps.

Version 3 compresses each page independently over four-byte BGRM texels. A one-byte span tag stores the
length minus one in its low seven bits. A set high bit repeats the following texel; a clear high bit is
followed by that many literal texels. Spans contain 1–128 texels. The decoder requires the compressed span
to end exactly at the recorded byte count and produce exactly `width * height` texels.

Files without the paired-source flag contain a single combined lightmap set, as produced by the MM9
importer. Their compressed page payload must end at the file boundary. Paired-source files carry the
extension below after their compressed pages.

## Extension after the last page

Version 4 and 5 paired-source files first store six float32 values: the normalized direction toward the baked sun
in OpenYAMM world coordinates and RGB white Lambertian response at normal incidence (`sun_energy / pi`).
The direction has positive Z. All values must be finite and the response positive and within RGBM4 range.
Version 3 paired-source files start directly at the counts below.

1. Probe count u32, dependency count u32.
2. Each probe: position XYZ, sun RGB, sky RGB (nine float32 values, 36 bytes in version 3).
   Versions 4 and 5 append indirect-sun RGB and direct-sun visibility (four float32 values; 52 bytes total).
   Indirect sun is measured in an indirect-only bake. Visibility is measured in a direct-only bake and
   normalized against the known horizontal receiver response, then bounded to `[0,1]`. It is not derived
   from total sun RGB, which includes bounced illumination.
3. Each dependency: UTF-8 path byte length u32, FNV-1a u64, then path bytes without a terminator.
   Paths are rooted at `engine/` or `worlds/` in the mounted asset filesystem. No parent traversal,
   backslashes, embedded NULs or absolute paths are accepted. At least one dependency is required.
4. Version 5 then stores direct-sun page count u32, equal to half the original page count. Each page stores
   width u32, height u32, compressed byte count u32, then the same BGRM/RLE payload as ordinary pages.
   Direct page `i` uses the dimensions and UV placement of original sun page `2*i`. Its illumination is
   measured with only the direct diffuse sun pass enabled; static occlusion is already included.
   The loader validates spans and retains compressed bytes. GPU receivers decode/upload only pages they need.

Dynamic actor shadow visibility multiplies the direct-only contribution. The existing total-sun page retains
its bounced contribution; sky and local lights remain independent. Never multiply a second static occlusion
term into the already baked sun response or darken all bounced light using actor shadow visibility.

The recipe records the complete profile, Blender version and producer SHA-256. The sidecar hashes that
recipe alongside its source inputs. This catches mismatched installation and changed runtime inputs;
it does not introspect authoring scripts or profiles from the game executable.
Map event Lua files are excluded from dependency records. Script edits that change baked decoration
shadow states require a manual rebake; gameplay-only edits do not invalidate lighting.

The existing sun/sky pages and total-sun/sky probe values keep their original meaning and bytes when migrating.
Models use visibility to modulate directional direct light and use indirect-sun/sky RGB for fill. Sprite and
world-surface paths keep their existing total sun/sky lighting. A version-3 bake remains valid for those consumers;
binding a 3D model to a paired-source version-3 map requires explicit migration first.
Version 4 remains valid for model lighting and self-shadow sampling. Baked world surfaces need the version-5
direct-only pages to receive actor mesh shadows without suppressing bounced illumination.

For an installed version-4 bake, use `bake_outdoor.py --sun-direct-only <installed.lighting>` with its exact
recipe profile, or `bake_all_outdoors.py --sun-direct-only --install`. Migration preserves the existing page,
face/vertex and model/sprite probe bytes, validates every installed dependency, and adds producer provenance.
Atlas placement or dimension mismatches reject migration instead of silently misaligning the new contribution.
