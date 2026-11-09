# MM6 peasant restoration — complete

[New Sorpigal original/enhanced playtest](PLAYTEST.md): isolated drop-in appearances for the town's existing
`pfem` and `pman` residents plus restored `pmn2` mages and `gob` goblins, with matching starting saves and separate `play.sh` modes.
Enhanced mode also includes the complete 134-texture MM6 x2 terrain pack (all outdoor maps), ESRGAN building surfaces in the default snapshot,
and the imagegen x2 fair-weather sky. See the playtest guide for preparation and refresh commands.

Goal: [restore all eight families](../MM6_PEASANTS_RESTORATION_GOAL.md), with all native actions/views and
three selective palette appearances per family. All eight families are complete: seven new staged packages and the accepted `pmn2` package reused unchanged.

| Family | Pattern | Palettes | Status | Package |
| --- | --- | --- | --- | --- |
| Female 1 | `pfem*.bmp` | 786–788 | Complete, staged and reviewed | [README](../mm6_pfem/README.md) · [viewer](../mm6_pfem/review.html) · [validation](../mm6_pfem/validation.json) |
| Female 2 | `fmp*.bmp` | 789–791 | Complete, staged and reviewed | [README](../mm6_fmp/README.md) · [viewer](../mm6_fmp/review.html) · [validation](../mm6_fmp/validation.json) |
| Female 3 | `mfp*.bmp` | 792–794 | Complete, staged and reviewed | [README](../mm6_mfp/README.md) · [viewer](../mm6_mfp/review.html) · [validation](../mm6_mfp/validation.json) |
| Female 4 | `natf*.bmp` | 795–797 | Complete, staged and reviewed | [README](../mm6_natf/README.md) · [viewer](../mm6_natf/review.html) · [validation](../mm6_natf/validation.json) |
| Male 1 | `pman*.bmp` | 798–800 | Complete, staged and reviewed | [README](../mm6_pman/README.md) · [viewer](../mm6_pman/review.html) · [validation](../mm6_pman/validation.json) |
| Male 2 | `pmn2*.bmp` | 801–803 | Complete, reused and verified | [README](../mm6_pmn2/README.md) · [viewer](../mm6_pmn2/review.html) · [validation](../mm6_pmn2/validation.json) |
| Male 3 | `mep*.bmp` | 804–806 | Complete, staged and reviewed; four-channel masks | [README](../mm6_mep/README.md) · [viewer](../mm6_mep/review.html) · [validation](../mm6_mep/validation.json) |
| Male 4 | `natm*.bmp` | 795–797 | Complete, staged and reviewed | [README](../mm6_natm/README.md) · [viewer](../mm6_natm/review.html) · [validation](../mm6_natm/validation.json) |

[Native family/palette contact](native_families.png) · [Native inventory](inventory.json) ·
[pmn2 reuse verification](pmn2_reuse_check.json) · [Final file audit](completion_audit.json).

Every family has 59 source filenames, but native dimensions, unused images, duplicate images and sequence reuse
differ. `pmn2` already has a separate runtime installation as custom monsters 904–906; this goal leaves that intact.
New families are staged only. Guards are outside this goal.

[All eight families × three appearances](all_family_variants.png) compares native and enhanced art at matching
logical size, with sufficient space for the spear and staff silhouettes. Each family viewer supplies all actions,
stored/mirrored directions, palette controls, masks and native/enhanced placement comparison.

## Coverage and review

**472 native filenames, 468 unique enhanced tiles, 24 palette appearances.** All source files are retained,
including six unused artworks, without inserting unused frames into playback. Exact native pixel aliases share
atlas tiles. Standing/walking retain five stored directions and eight native view aliases; single-view actions
retain their original behavior. Attack2 bindings are preserved; reused `pmn2` stores attack once because its
native second-attack group is identical for all three palettes, as recorded in the reuse check.

Each package includes base/mask pages, versioned placement and animation JSON, aligned masters, tight crops,
full action review sheets, deterministic variant previews, exact submitted prompts and generation/source hashes.
All use two physical pixels per logical pixel while retaining native timing, frame scale and bottom placement.
Actual AI output dimensions are recorded separately in each README and generation checkpoint.

All-frame crop reconstruction, atlas extraction, source/provenance, palette alpha, base bypass and protected-mask
checks pass. The cleaned and final atlas-extracted frames pass residual-matte scans, followed by visual review
of light/dark contour patches. All base frames and masks were reviewed in contacts, with native pose comparisons
and representative offline viewer captures. The final aggregate verifies every palette/action/view sequence against
the native inventory, including timing, mirrors and scale. Current descriptors and animation groups were checked
against that inventory at completion.

## Shared footprint

MiB = 1,048,576 bytes. [Exact byte totals and page hashes](footprint.json).

| Family | RGBA8 base | Masks | Shared decoded total | Shipping PNGs + JSON |
| --- | ---: | ---: | ---: | ---: |
| pfem | 26.97 | 6.74 | 33.71 | 7.93 |
| fmp | 30.02 | 7.51 | 37.53 | 9.51 |
| mfp | 26.55 | 6.64 | 33.18 | 7.64 |
| natf | 34.25 | 8.56 | 42.81 | 10.34 |
| pman | 26.30 | 6.57 | 32.87 | 7.52 |
| pmn2, reused | 36.91 | 9.23 | 46.14 | 9.75 |
| mep | 34.57 | 34.57 | 69.14 | 11.88 |
| natm | 53.00 | 13.25 | 66.26 | 11.42 |
| **All eight** | **268.56** | **93.07** | **361.63** | **75.99** |

The seven newly staged families total **315.49 MiB decoded** and **66.25 MiB shipping**. Decoded totals include
atlas packing and transparent padding; each validation also reports unique tight-base bytes. Seven families use
one R8 mask; `mep` uses four RGBA8 data channels. All appearances and actors share the pages. Shipping excludes raw
AI sheets, prompts, aligned masters, baked variant previews, viewers and review images. No FPS claim follows from
these byte counts; this goal performs no engine build, gameplay scenario or installation.

## Runtime compatibility and limitations

`pfem`, `fmp`, `mfp`, `natf`, `pman` and `natm` use the supported single-mask `masked_luminance_rgb_v1` operation.
Their staged manifests still require explicit registration and loader validation before installation. `pmn2` has
its prior separate custom-monster installation (904–906), which this goal does not modify.

`mep` requires a future **four-channel mask / four-vector shader and loader extension**. Mask alpha is a fourth
coverage channel, not opacity; base alpha remains separate. Its README and manifest specify the encoded-RGB
luminance sum and exact base bypass. The viewer uses deterministic previews of this operation.

Remaining visual approximations are recorded per family: reconstructed faces, fabric/feather details and small
accessories vary slightly between poses; lighting is generally softer and some midtones warmer/brighter than the
native art. Palette vectors approximate native ramps, with some desaturated wear/highlights retained. Alpha is
estimated from a matte. These are accepted offline restoration limits, not claims of exact recovery of lost detail.

## Resume or reproduce

Use the [creature-restore skill](../../../.agents/skills/creature-restore/SKILL.md) and each package's saved
checkpoints. No additional AI generation is needed for the completed scope. Goal-scoped preparation, processing,
packaging and viewer helpers live beside this index; material settings and local repairs live in each family's
`config.json`. Keep accepted `pmn2` on its existing workflow rather than running the new family helpers over it.

```sh
python3 level_generation/creatures/mm6_peasants/aggregate.py
```

This rebuilds the labeled comparison and footprint report only after checking all eight completed packages.
For offline browser screenshots use the [approved capture helper](../../../tools/CAPTURE_LOCAL_HTML.md).
