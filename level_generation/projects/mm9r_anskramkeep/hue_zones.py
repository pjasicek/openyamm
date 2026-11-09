"""Zones of ANSKRAMKEEP.dat for ../mm9r_common/hue_vs_lightmaps.py and ../mm9r_common/relight_fit.py (re-light,
2026-10-31): a k-d split of MM9's lightmapped polygons by area into ten boxes tiling the keep (MM9 units, y up), from
`../mm9r_common/relight_zones.py ANSKRAMKEEP.dat 10`. One storey band (y -512..320); x west (-2816) to east (2752), z
south (-384) to north (6336). Comments: MM9's mean lightmap RGB (0-255) per box."""
ZONES = {
    "z01_sw": (-2816, -512, -384, -1408, 320, 1472),           # 113, 105, 80
    "z02_w_mid": (-2816, -512, 1472, -448, 320, 2368),         # 122, 115, 91
    "z03_w_north": (-2816, -512, 2368, -384, 320, 3448),       # 120, 113, 90
    "z04_nw": (-2816, -512, 3448, -384, 320, 6336),            # 112, 106, 81
    "z05_s_midwest": (-1408, -512, -384, -448, 320, 1472),     # 113, 106, 83
    "z06_centre_south": (-448, -512, -384, 832, 320, 2368),    # 119, 112, 87
    "z07_centre_north": (-384, -512, 2368, 1229, 320, 3520),   # 117, 111, 87
    "z08_ne": (-384, -512, 3520, 2752, 320, 6336),             # 106, 100, 78
    "z09_se": (832, -512, -384, 2752, 320, 2368),              # 110, 102, 79
    "z10_e_mid": (1229, -512, 2368, 2752, 320, 3520),          # 128, 120, 90
}
