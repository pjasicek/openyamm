"""Zones of BEETHOVEN.dat for ../mm9r_common/hue_vs_lightmaps.py: boxes in MM9's own units (x0, y0, z0, x1, y1, z1), y up.
Storeys from the README (sewers y 0..300, catacombs and baths -736..-500, lower sewers -1216..-1100, maze hall -1392); the
x/z limits come from the DAT lightmaps' own colour (a 1500-unit grid of the polygons' mean RGB) and the water volumes
("frigidarium water" x -2128..-1648 z -1058..-66, "Caldarium water" x -2088..-968 z 2432..3472)."""
ZONES = {
    "sewers": (-7600, -100, -1500, 2200, 350, 7400),
    "sewers_neutral": (-7600, -100, 4400, -6000, 350, 6100),
    "catacombs": (-7600, -850, -3100, -2300, -450, 3700),
    "baths": (-2300, -900, -1600, -300, -450, 3700),
    "lower_sewers": (-6200, -1300, -1600, -2900, -1100, 100),
    "maze_hall": (-7600, -1500, -12100, -3000, -1300, -8000),
    # added 2026-10-30 (re-light): the flooded cavern under the hub (GrandEntrance Water's box, below the catacombs'
    # floor) and the south arrival's tunnel (ExitS / SewerS, x -4400..-3000 round z 212)
    "cavern": (-1600, -1300, -1300, 450, -790, -560),
    "south_arrival": (-4400, -100, -300, -3000, 700, 700),
    # the lower storey east and south of the lower_sewers box (the manuscript's channels) and the catacomb-level
    # corridors south of the catacombs and baths, towards the maze hall
    "lower_rest": (-3400, -1300, -3100, -1600, -1100, 100),
    "south_corridors": (-7600, -900, -8000, 2200, -450, -3100),
}
