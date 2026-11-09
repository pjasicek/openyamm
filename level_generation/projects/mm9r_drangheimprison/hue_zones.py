"""Zones of DRANGHEIMPRISON.dat for ../mm9r_common/hue_vs_lightmaps.py and ../mm9r_common/relight_fit.py (re-light,
2026-10-31): a k-d split of MM9's lightmapped polygons by area into ten boxes tiling the prison (MM9 units, y up), from
`../mm9r_common/relight_zones.py DRANGHEIMPRISON.dat 10`: the low storey (y -1868..-1248), the middle band and the
upper levels (y -616..256) west of x -64. Comments: MM9's mean lightmap RGB (0-255) per box."""
ZONES = {
    "z01_low_west_s": (-2752, -1868, -3776, -64, -616, -1536),   # 62, 74, 79
    "z02_low_west_n": (-2752, -1868, -1536, -64, -616, 928),     # 67, 72, 69
    "z03_low_mid_s": (-64, -1868, -3776, 1120, -1248, -960),     # 41, 61, 75
    "z04_low_mid_n": (-64, -1868, -960, 1120, -1248, 928),       # 41, 64, 79
    "z05_low_east_s": (1120, -1868, -3776, 3634, -1248, -1216),  # 41, 66, 84
    "z06_low_east_n": (1120, -1868, -1216, 3634, -1248, 928),    # 41, 64, 79
    "z07_upper_east_s": (-64, -1248, -3776, 3634, 256, -256),    # 61, 74, 79
    "z08_upper_east_n": (-64, -1248, -256, 3634, 256, 928),      # 67, 72, 70
    "z09_upper_west_s": (-2752, -616, -3776, -64, 256, -32),     # 65, 69, 64
    "z10_upper_west_n": (-2752, -616, -32, -64, 256, 928),       # 67, 70, 66
}
