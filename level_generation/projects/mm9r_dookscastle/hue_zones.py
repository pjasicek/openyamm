"""Zones of DOOKSCASTLE.dat for ../mm9r_common/hue_vs_lightmaps.py: boxes in MM9's own units (x0, y0, z0, x1, y1, z1),
y up. The castle storey (floor 160 LT, the gate hall 0-176), the caves under it (-100 to -1400), the lake (bed -1920)."""
ZONES = {
    "gate_hall": (-450, -20, 400, 450, 700, 1300),
    "corridors": (-1100, 140, 1300, 260, 700, 3700),
    "throne_room": (-1560, 140, 3150, -420, 700, 4300),
    "west_rooms": (-2450, 140, 1500, -150, 700, 2420),
    "east_rooms": (140, 140, 2100, 1300, 700, 3700),
    "upper_tunnels": (100, -700, 1000, 2800, -20, 4000),
    "lake_cavern": (2550, -2000, 800, 5300, -400, 2700),
    "north_caves": (2800, -1500, 2700, 5800, -400, 4700),
}
