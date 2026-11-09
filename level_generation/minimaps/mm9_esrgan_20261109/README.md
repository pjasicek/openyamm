# MM9 painted maps at 2× (2026-11-09)

MM9's 54 map screens (`mm9/extracted/ART/ART/INTERFACESCREENS/MAPSCREENS/MAPS/*.pcx`; the archive's unused
`KLUSOHOUSEA/B` duplicates left out) upscaled by the recipe the user approved for the MM7/MM8 minimaps on 2026-09-28
([study](../esrgan_study_20260928/README.md)): `realesr-animevideov3`, direct 2×, full strength, no blend, a
16-pixel reflected border removed after inference. The user asked for "x2 (or x4?)"; 2× was kept because the source
maps are already 573–1140 px wide and the minimap shows them at their native logical size (the catalog's width and
height), so a 2× texture is pixel for pixel at a 2× HUD scale, and the MM7/MM8 study found 4× reduced to 2× no better.

```sh
python3 -B level_generation/minimaps/mm9_esrgan_20261109/upscale.py prepare   # original/ and padded input/
python3 -B level_generation/minimaps/mm9_esrgan_20261109/upscale.py run       # raw/ (about 20 s on the RTX 3060 Ti)
python3 -B level_generation/minimaps/mm9_esrgan_20261109/upscale.py finish    # x2/, contacts/, results.json
python3 -B level_generation/minimaps/mm9_esrgan_20261109/upscale.py install   # worlds/mm9/ui/maps/<map>.png
```

`finish` reduces each result to native size and checks its registration against the original at shifts of ±2 px:
all 54 are best at zero shift. `contacts/<map>.png` shows a native crop at nearest 2× beside the result. `install`
writes the PNGs into `assets_dev` and both MM9 review roots and removes the native PCX copies there (the catalog names
the PNGs; the originals stay in `mm9/extracted`). The catalog itself is written by the converters
(`level_generation/projects/mm9r_common/dungeon/tables.py`); how the maps are placed and checked is in the
[dungeon playbook](../../projects/mm9r_common/DUNGEON_PLAYBOOK.md#painted-maps-2026-11-09).
