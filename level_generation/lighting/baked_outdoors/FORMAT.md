# Outdoor lighting version 3

All integers and IEEE float32 values are little endian. Magic remains `OYMLIT1\0`; only version 3 is
accepted. File lengths/section offsets/counts, geometry
hash, face identities, finite values, page references, page dimensions, paired dimensions and dependency
paths are validated before use. Trailing data is rejected.

## Header (96 bytes)

| Offset | Type | Meaning |
| --- | --- | --- |
| 0 | 8 bytes | Magic |
| 8 | u32 | Version: 3 |
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

1. Probe count u32, dependency count u32.
2. Each probe: position XYZ, sun RGB, sky RGB (nine float32 values, 36 bytes).
3. Each dependency: UTF-8 path byte length u32, FNV-1a u64, then path bytes without a terminator.
   Paths are rooted at `engine/` or `worlds/` in the mounted asset filesystem. No parent traversal,
   backslashes, embedded NULs or absolute paths are accepted. At least one dependency is required.

The recipe records the complete profile, Blender version and producer SHA-256. The sidecar hashes that
recipe alongside its source inputs. This catches mismatched installation and changed runtime inputs;
it does not introspect authoring scripts or profiles from the game executable.
