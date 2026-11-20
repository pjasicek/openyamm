"""Zones of TEMPLEOFHONK.dat for ../mm9r_common/hue_vs_lightmaps.py and ../mm9r_common/relight_fit.py (re-light,
2026-10-31): a k-d split of MM9's lightmapped polygons by area into eight boxes tiling the temple (MM9 units, y up),
from `../mm9r_common/relight_zones.py TEMPLEOFHONK.dat 8`. The temple is one storey band (y -352..704); x runs west
(-2400) to east (2304), z south (-416) to north (3232). Comments: MM9's mean lightmap RGB (0-255) per box."""
ZONES = {
    "z1_west_south": (-2400, -352, -416, -1184, 704, 1248),     # 115, 115, 105
    "z2_west_north": (-2400, -352, 1248, -1344, 704, 3232),     # 125, 125, 117
    "z3_midwest_north": (-1344, -352, 1248, 2, 704, 3232),      # 142, 142, 134
    "z4_midwest_south": (-1184, -352, -416, 2, 704, 1248),      # 116, 116, 106
    "z5_mideast_south": (2, -352, -416, 1089, 704, 1472),       # 122, 122, 113
    "z6_mideast_north": (2, -352, 1472, 1152, 704, 3232),       # 123, 123, 112
    "z7_east_south": (1089, -352, -416, 2304, 704, 1472),       # 123, 123, 112
    "z8_east_north": (1152, -352, 1472, 2304, 704, 3232),       # 127, 127, 118
}
