"""Zones of TASARACADEMY.dat for ../mm9r_common/hue_vs_lightmaps.py: boxes in MM9's own units (x0, y0, z0, x1, y1, z1),
y up. Halls at 0, the south wing 128-136, the library's tower floors 208 and 416, the pit -256."""
ZONES = {
    "entry_halls": (0, -50, -400, 2200, 400, 450),
    "arena": (600, -50, -1750, 1600, 340, -450),
    "west_wing": (-1100, -50, -1600, 600, 300, -400),
    "east_wing": (1780, -50, -2050, 3300, 300, -400),
    "store_room": (2060, -50, -450, 3100, 300, 200),
    "library": (100, -50, -3400, 800, 720, -2450),
    "pit_tower": (300, -300, -2400, 700, 300, -1800),
    "south_halls": (1300, -50, -3400, 2100, 300, -1800),
    "south_hall": (-120, 50, -4600, 1500, 450, -3550),
    "rules_room": (-700, 50, -3950, -100, 450, -3450),
    "octagon_east": (1750, 50, -4400, 2800, 450, -3550),
    "barn": (1500, 50, -4850, 2500, 450, -4400),
}
