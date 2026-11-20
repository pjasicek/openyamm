"""Zones of LICHLAB.dat for ../mm9r_common/hue_vs_lightmaps.py and ../mm9r_common/relight_fit.py (re-light, 2026-10-31):
a k-d split of MM9's lightmapped polygons by area into ten boxes tiling the laboratory (MM9 units, y up), from
`../mm9r_common/relight_zones.py LICHLAB.dat 10`: the lower floors (y -576..512) and the upper floors (y 480/512..1536),
x west (-3808) to east (3136), z south (-2161) to north (4960). Comments: MM9's mean lightmap RGB (0-255) per box."""
ZONES = {
    "z01_low_west_s": (-3808, -576, -2161, -704, 512, 1632),    # 84, 86, 80
    "z02_low_west_mid": (-3808, -576, 1632, -576, 512, 3360),   # 91, 110, 104 (the teal pods)
    "z03_low_west_n": (-3808, -576, 3360, -576, 512, 4960),     # 83, 86, 80
    "z04_low_east_s": (-704, -576, -2161, 3136, 512, 256),      # 76, 79, 74
    "z05_low_east_mid": (-704, -576, 256, 3136, 512, 1632),     # 80, 81, 75
    "z06_low_east_n": (-576, -576, 1632, 3136, 480, 4960),      # 81, 83, 78
    "z07_up_west_s": (-3808, 512, -2161, -704, 1536, 1632),     # 75, 78, 73
    "z08_up_west_n": (-3808, 512, 1632, -576, 1536, 4960),      # 73, 87, 84
    "z09_up_east_s": (-704, 512, -2161, 3136, 1536, 1632),      # 77, 79, 75
    "z10_up_east_n": (-576, 480, 1632, 3136, 1536, 4960),       # 80, 83, 78
}
