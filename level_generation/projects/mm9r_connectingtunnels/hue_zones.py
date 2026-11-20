"""Zones of CONNECTINGTUNNELS.dat for ../mm9r_common/hue_vs_lightmaps.py: boxes in MM9's own units (x0, y0, z0, x1, y1,
z1), y up. The coffin hall (blue fills, the glowing pillars) in the south, the tunnels round it, the central junctions,
the north-east loop and chamber, the spiral to Thronheim in the east, the south-west tunnel to Yorwick's lower exit and
the north-west climb to Yorwick's upper exit."""
ZONES = {
    "coffin_hall": (4800, -900, -6100, 7800, 400, -3800),
    "south_tunnels": (3000, -900, -3800, 9500, 400, -1500),
    "centre": (2000, -900, -1500, 9000, 1600, 1500),
    "northeast": (9000, -900, -1000, 12400, 2900, 4700),
    "east_spiral": (12400, -900, -3500, 14600, 2900, 1000),
    "southwest": (-1300, -900, -6100, 2000, 1600, -1500),
    "northwest": (-1300, -900, -1500, 2000, 2900, 4700),
}
