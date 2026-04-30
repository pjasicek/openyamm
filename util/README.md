# Export Utilities

These scripts export OpenYAMM-relevant binary data files into JSON for inspection or downstream import tooling.

Usage examples:

```bash
python3 util/dmonlist_export.py assets_dev/_legacy/bin_tables/dmonlist.bin -o /tmp/dmonlist.json
python3 util/dtile_export.py assets_dev/_legacy/tile_tables/dtile.bin -o /tmp/dtile.json
python3 util/ddm_export.py assets_dev/Data/games/out01.ddm -o /tmp/out01.ddm.json
```

Available exporters:

- `dchest_export.py`
- `ddeclist_export.py`
- `dift_export.py`
- `dmonlist_export.py`
- `dobjlist_export.py`
- `doverlay_export.py`
- `dpft_export.py`
- `dsft_export.py`
- `dsounds_export.py`
- `dtft_export.py`
- `dtile_export.py`
- `dtile2_export.py`
- `dtile3_export.py`
- `ddm_export.py`
- `odm_export.py`
- `blv_export.py`
- `dlv_export.py`

There is also a shared generic entry point:

```bash
python3 util/mm_bin_export.py dmonlist assets_dev/_legacy/bin_tables/dmonlist.bin -o /tmp/dmonlist.json
python3 util/map_export.py odm assets_dev/Data/games/out01.odm -o /tmp/out01.odm.json
```
