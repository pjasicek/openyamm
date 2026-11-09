"""Zones of THEARENA.dat for ../mm9r_common/hue_vs_lightmaps.py: boxes in MM9's own units (x0, y0, z0, x1, y1, z1),
y up. The hall and the arena floor at 0, the stands from 192 up, Sven's box at 192-224, the open sky over the bowl."""
ZONES = {
    "hall": (-256, -10, -1536, 256, 170, -610),
    "arena_floor": (-600, -10, -590, 600, 180, 590),
    "east_pen": (600, -10, -100, 1000, 170, 100),
    "west_pen": (-1000, -10, -100, -600, 170, 100),
    "south_stand": (-256, 185, -1110, 256, 520, -600),
    "east_stand": (600, 185, -256, 1120, 520, 256),
    "north_box": (-256, 185, 590, 256, 420, 870),
}
