"""Zones of THJORADMINE.dat for ../mm9r_common/hue_vs_lightmaps.py: boxes in MM9's own units (x0, y0, z0, x1, y1, z1),
y up. The entrance and the refinery in the middle, the old halls and caves west (floors 0-500), the cave-in over the
flooded cavern, the east mine network (floors about -550), Ebora's chamber, the abandoned mine south."""
ZONES = {
    "entrance": (600, -500, -1400, 2300, 0, 900),
    "refinery": (-700, -400, -700, 700, 700, 700),
    "west_halls": (-3200, -100, -2000, -700, 700, 1000),
    "northwest": (-5400, 0, 1000, -1500, 700, 3700),
    "north_tunnels": (-1500, -400, 1800, 3000, 700, 3700),
    "cavein_deep": (1600, -1500, 300, 3500, -450, 3000),
    "east_mines": (3500, -800, -3000, 12300, -300, 1800),
    "ebora": (9300, -700, -900, 10300, -300, -300),
    "abandoned": (1500, -900, -7600, 12300, -300, -4000),
}
