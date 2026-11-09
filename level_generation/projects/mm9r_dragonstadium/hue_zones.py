"""Zones of DRAGONSTADIUM.dat for ../mm9r_common/hue_vs_lightmaps.py: boxes in MM9's own units (x0, y0, z0, x1, y1, z1),
y up. The arena's floor (the bowl's bottom, under the sky opening), the arena's walls (the bowl's sides up to the sky
box), the entrance tunnel from the start to the arena's mouth (its three blue lights), the winding side tunnel."""
ZONES = {
    "floor_centre": (0, -200, -1000, 1100, 40, 1200),        # under the sky box's ceiling (the sun's patch)
    "floor_west": (-1600, -200, -1500, -200, 40, 2500),      # the bowl's floor outside it
    "floor_east": (1500, -200, -1500, 3400, 40, 2500),
    "arena_floor": (-1600, -200, -1500, 3400, 40, 2500),
    "arena_walls": (-1600, 40, -1700, 3400, 2500, 2500),
    "entrance_tunnel": (400, -200, -2750, 1100, 400, -1750),
    "side_tunnel": (1100, -200, -3200, 3000, 900, -2300),
}
