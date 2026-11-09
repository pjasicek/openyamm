"""Zones of DARKPASSAGEWAY.dat for ../mm9r_common/hue_vs_lightmaps.py: boxes in MM9's own units (x0, y0, z0, x1, y1, z1),
y up. Along the passage: the start room, the bridge lake, the canyon corridor and canyon, the mountain room and forest
corridor, the forest, the winding path, the tube room, the ocean hall, the pillared room, the desert, the spike-trap
corridor, the exit room, the curved corridor and the Wyrde's room."""
ZONES = {
    "start": (-7700, -100, -120, -7100, 900, 900),
    "lake": (-8600, -1200, -3900, -6100, 0, -512),
    "canyon_corridor": (-8700, -600, -6300, -7500, -200, -3950),
    "canyon": (-9400, -2600, -8450, -7300, 700, -6350),
    "mountain": (-7600, -300, -8800, -6000, 300, -7600),
    "forest": (-6400, -300, -6800, -5600, 600, -4400),
    "path_north": (-6400, -500, -4400, -3900, 600, -2800),
    "path_south": (-5400, -500, -7700, -4300, 600, -4400),
    "tube_room": (-5300, -1000, -8800, -3600, 300, -7700),
    "ocean": (-4100, -1700, -9300, -1900, -900, -7600),
    "pillar_room": (-3300, -400, -7600, -2800, 0, -6250),
    "desert": (-4100, -400, -6250, 300, 600, -2080),
    "spike": (-2400, -400, -2080, -1700, 100, -600),
    "exit_room": (-2300, -500, -600, -1700, 0, 1050),
    "curve": (-2100, -300, 1050, -500, 1000, 2900),
    "wyrde": (-500, -300, 2150, 300, 600, 2900),
}
